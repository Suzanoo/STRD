"""Bounded MS2 request validation and response orchestration; no fixture globals."""
from strd.domain.properties import HSection, ReferenceSection, ReferenceMaterial
from strd.domain.contracts import StrengthResult
from dataclasses import asdict
from strd.domain.validation import _number
from .basis import MS2_BASIS_ID as BASIS_ID, MS2_CALCULATOR_VERSION as CALCULATOR_VERSION, SOURCE_SHA256
from .validation import _positive, _Unsupported, _geometry
from .flexure import _flexural_strength
from .shear import _web_shear_strength

_COMMON = {"basis_id", "section_id", "material_id", "method", "prismatic_undamaged"}
_FLEXURE = _COMMON | {"moment_knm", "unbraced_length_mm", "cb", "cb_source",
                      "cb_reference", "support_twist_restrained", "segment_ends_braced",
                      "major_axis_only"}
_SHEAR = _COMMON | {"shear_kn", "web_plane_only", "unstiffened_web"}
_EXCLUSIONS = (
    "axial/minor-axis/combined actions/torsion", "deflection/serviceability",
    "connections/net-section rupture", "local bearing/web crippling/concentrated forces",
    "global stability", "bracing strength and stiffness", "fatigue/seismic/fire",
)


def _result(check, status, message, **details):
    excluded = ["web shear"] if check == "FLEXURE" else ["major-axis bending/LTB"]
    if check == "SHEAR":
        excluded += ["stiffener design", "tension-field action"]
    return dict(status=status, message=message, check=check,
                scope="Individual conditional strength check; not whole-member acceptance",
                basis_id=BASIS_ID, calculator_version=CALCULATOR_VERSION,
                not_checked=excluded + list(_EXCLUSIONS), **details)


def _validate(request, check, required, flags, scalars, section, material):
    if type(request) is not dict:
        return _result(check, "INVALID_INPUT", "Request must be a dictionary.")
    missing, extra = required - request.keys(), request.keys() - required
    if missing or extra:
        return _result(check, "INVALID_INPUT", "Fields do not match the documented schema.",
                       missing=sorted(missing), unexpected=sorted(map(str, extra)))
    for key in ("basis_id", "section_id", "material_id", "method"):
        if type(request[key]) is not str or not request[key].strip():
            return _result(check, "INVALID_INPUT", f"{key} must be a nonempty string.")
    for key in flags:
        if type(request[key]) is not bool:
            return _result(check, "INVALID_INPUT", f"{key} must be an explicit boolean.")
    for key in scalars:
        if not _number(request[key]) or request[key] < 0:
            return _result(check, "INVALID_INPUT", f"{key} must be a finite nonnegative number.")
    for key, allowed in (("basis_id", (BASIS_ID,)), ("section_id", (section.section_id,)),
                         ("material_id", (material.material_id,)), ("method", ("ASD", "LRFD"))):
        if request[key] not in allowed:
            return _result(check, "UNSUPPORTED", f"Unsupported {key}; no catalog fallback.")
    if not all(request[key] for key in flags):
        return _result(check, "UNSUPPORTED", "Required applicability/restraint assumptions are not satisfied.")
    return None


def _trace(section, material, clauses, pages):
    return dict(section=asdict(section), material=asdict(material),
                source_sha256=SOURCE_SHA256, clauses=clauses, printed_pages=pages,
                data_status="Book example inputs only; not an authoritative manufacturer catalog")


def _check_flexure(request: object, section: HSection, material: ReferenceMaterial) -> StrengthResult:
    """Check one braced segment of the verified H section; Lb in mm, M in kN-m.

    Cb is supplied with its provenance, 1 <= Cb <= 5. Both segment ends must
    have the required restraint. Cb=1 is the supported conservative option.
    Lb=0 explicitly represents continuous restraint; bracing is not designed.
    """
    check = "FLEXURE"
    error = _validate(request, check, _FLEXURE,
                      ("prismatic_undamaged", "support_twist_restrained", "segment_ends_braced", "major_axis_only"),
                      ("moment_knm", "unbraced_length_mm", "cb"), section, material)
    if error: return error
    for key in ("cb_source", "cb_reference"):
        if type(request[key]) is not str or not request[key].strip():
            return _result(check, "INVALID_INPUT", f"{key} requires a nonempty string.")
    if request["cb_source"] not in ("CONSERVATIVE", "VERIFIED_MOMENT_DIAGRAM"):
        return _result(check, "UNSUPPORTED", "Unsupported Cb provenance mode.")
    if request["cb"] < 1 or request["cb"] > 5:
        return _result(check, "UNSUPPORTED", "Cb must be within the Eq.(9) magnitude envelope [1,5].")
    if request["cb_source"] == "CONSERVATIVE" and request["cb"] != 1:
        return _result(check, "INVALID_INPUT", "CONSERVATIVE mode requires Cb=1.")
    try:
        mid = _flexural_strength(section, material, request["unbraced_length_mm"], request["cb"])
        demand = request["moment_knm"] * 1e6
        capacity = mid["lrfd_capacity_nmm"] if request["method"] == "LRFD" else mid["asd_capacity_nmm"]
        _positive(capacity)
        if not _number(demand) or not _number(demand / capacity):
            raise ValueError("Demand conversion/utilization exceeds numerical range.")
    except _Unsupported as exc:
        return _result(check, "UNSUPPORTED", str(exc))
    except (ValueError, OverflowError, ZeroDivisionError) as exc:
        return _result(check, "INVALID_INPUT", f"Calculation integrity failure: {exc}")
    # Compare in the public unit so feeding an exact reported capacity is equality.
    capacity_knm = capacity / 1e6
    status = "PASS" if request["moment_knm"] <= capacity_knm else "FAIL"
    return _result(check, status, "Conditional major-axis flexural strength comparison completed.",
                   inputs=dict(request), reference=_trace(section, material, ["Table 1(b), rows 10/15", "5.1", "5.2 Eqs.(10)-(17a)", "Examples 10.3.1/10.3.2"], [9,10,28,29,30,90,91,92,93,94,95]),
                   intermediates=dict(mid, demand_nmm=demand), capacity_knm=capacity_knm,
                   utilization=request["moment_knm"]/capacity_knm,
                   governing_limit_state=mid["governing_limit_state"],
                   assumptions=["Rolled doubly symmetric compact prismatic H; no holes/copes/damage",
                                "Restraint and moment-diagram assertions are caller evidence, not brace design",
                                "Moment is maximum absolute segment demand on selected ASD/LRFD basis"],
                   formulas={"nominal":"min(Fy*Zx, LTB strength); book Eqs.(10)-(17a)",
                             "units":"MPa=N/mm^2; 1 kN-m=1e6 N-mm",
                             "boundary":"Lb=Lp: yielding; Lb=Lr: Eq.(11); Lb>Lr: Eqs.(12)-(13)",
                             "design":"LRFD=0.9*Mn; ASD=Mn/1.67"})


def _check_web_shear(request: object, section: HSection, material: ReferenceMaterial,
                     *, full_reference_integrity=True) -> StrengthResult:
    """Check web-plane shear alone, unstiffened rolled H, demand in kN."""
    check = "SHEAR"
    error = _validate(request, check, _SHEAR,
                      ("prismatic_undamaged", "web_plane_only", "unstiffened_web"), ("shear_kn",), section, material)
    if error: return error
    try:
        if full_reference_integrity:
            _geometry(section, material)  # Retain accepted fixed-fixture API validation.
        mid = _web_shear_strength(section, material)
        demand = request["shear_kn"] * 1000
        capacity = mid["lrfd_capacity_n"] if request["method"] == "LRFD" else mid["asd_capacity_n"]
        _positive(capacity)
        if not _number(demand) or not _number(demand / capacity):
            raise ValueError("Demand conversion/utilization exceeds numerical range.")
    except _Unsupported as exc:
        return _result(check, "UNSUPPORTED", str(exc))
    except (ValueError, OverflowError, ZeroDivisionError) as exc:
        return _result(check, "INVALID_INPUT", f"Calculation integrity failure: {exc}")
    capacity_kn = capacity / 1000
    status = "PASS" if request["shear_kn"] <= capacity_kn else "FAIL"
    # 6.2.2 uses 'greater than' for the strength alternative; retain strict >.
    exemption = (mid["web_width_thickness"] <= mid["stiffener_slenderness_limit"] or
                 request["shear_kn"] < capacity_kn)
    if status == "PASS" and not exemption:
        return _result(check, "UNSUPPORTED", "Strength equality does not establish the strict 6.2.2 exemption for this slender web; stiffener assessment required.")
    mid["transverse_stiffener_exemption_6_2_2"] = exemption
    return _result(check, status, "Conditional web shear strength comparison completed.",
                   inputs=dict(request), reference=_trace(section, material, ["6.1", "6.2.1 Eqs.(94)-(98)", "6.2.2", "Example 10.4.1"], [51,52,53,119,120]),
                   intermediates=dict(mid, demand_n=demand), capacity_kn=capacity_kn,
                   utilization=request["shear_kn"]/capacity_kn,
                   governing_limit_state=mid["governing_limit_state"],
                   assumptions=["Unstiffened rolled doubly symmetric H; no holes/copes/damage",
                                "No tension-field action or transverse-stiffener strength credit",
                                "Shear magnitude supplied on selected ASD/LRFD basis"],
                   warnings=[] if exemption else ["6.2.2 exemption not established; stiffener assessment required outside this check"],
                   formulas={"nominal":"Vn=0.6*Fy*(d*tw)*Cv", "units":"1 kN=1000 N; MPa=N/mm^2",
                             "slenderness":"h/tw=[d-2(tf+r)]/tw; Aw=d*tw",
                             "factors":"6.2.1(a): phi=1, omega=1.5; otherwise phi=.9, omega=1.67"})
