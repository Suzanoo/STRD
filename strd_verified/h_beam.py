"""Pure bounded MS-2 checks. No analysis, catalog import or presentation I/O.

Only the evidence fixture in h_reference is public. Private kernels accept
explicit properties for independent equation/boundary tests, not catalog entry.
"""
import math
from dataclasses import asdict

from .bending import _number  # reuse MS-1 strict finite-scalar validation
from .reference import PHI_B, OMEGA_B
from .h_reference import BASIS_ID, CALCULATOR_VERSION, SOURCE_SHA256, SECTION, MATERIAL

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


class _Unsupported(ValueError):
    pass


def _result(check, status, message, **details):
    excluded = ["web shear"] if check == "FLEXURE" else ["major-axis bending/LTB"]
    if check == "SHEAR":
        excluded += ["stiffener design", "tension-field action"]
    return dict(status=status, message=message, check=check,
                scope="Individual conditional strength check; not whole-member acceptance",
                basis_id=BASIS_ID, calculator_version=CALCULATOR_VERSION,
                not_checked=excluded + list(_EXCLUSIONS), **details)


def _validate(request, check, required, flags, scalars):
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
    for key, allowed in (("basis_id", (BASIS_ID,)), ("section_id", (SECTION.section_id,)),
                         ("material_id", (MATERIAL.material_id,)), ("method", ("ASD", "LRFD"))):
        if request[key] not in allowed:
            return _result(check, "UNSUPPORTED", f"Unsupported {key}; no catalog fallback.")
    if not all(request[key] for key in flags):
        return _result(check, "UNSUPPORTED", "Required applicability/restraint assumptions are not satisfied.")
    return None


def _positive(*values):
    if not all(_number(v) and v > 0 for v in values):
        raise ValueError("Nonpositive or nonfinite engineering intermediate/reference value.")


def _geometry(section, material):
    _positive(*(v for k, v in asdict(section).items() if k != "section_id"),
              material.fy_mpa, material.elastic_modulus_mpa)
    if not (section.web_mm < section.width_mm and
            section.plastic_modulus_x_mm3 >= section.elastic_modulus_x_mm3 and
            material.fy_mpa < material.elastic_modulus_mpa):
        raise ValueError("Inconsistent section/material reference data.")
    clear = section.depth_mm - 2 * (section.flange_mm + section.root_radius_mm)
    _positive(clear)
    return clear


def _classify(section, material):
    clear = _geometry(section, material)
    root = math.sqrt(material.elastic_modulus_mpa / material.fy_mpa)
    flange, web = section.width_mm / (2 * section.flange_mm), clear / section.web_mm
    def label(ratio, compact, slender):
        return "COMPACT" if ratio <= compact else ("NONCOMPACT" if ratio <= slender else "SLENDER")
    return dict(clear_web_mm=clear, flange_width_thickness=flange, web_width_thickness=web,
                flange_compact_limit=0.38 * root, flange_noncompact_limit=root,
                web_compact_limit=3.76 * root, web_noncompact_limit=5.70 * root,
                flange_class=label(flange, 0.38 * root, root),
                web_class=label(web, 3.76 * root, 5.70 * root))


def _flexural_strength(section, material, lb, cb):
    """Book 5.2 only. Caller validates Lb/Cb; reject noncompact sections here."""
    classification = _classify(section, material)
    if classification["flange_class"] != "COMPACT" or classification["web_class"] != "COMPACT":
        raise _Unsupported("Section 5.2 requires compact flange AND web; 5.3-5.5 are not implemented.")
    e, fy = material.elastic_modulus_mpa, material.fy_mpa
    sx, zx = section.elastic_modulus_x_mm3, section.plastic_modulus_x_mm3
    h0 = section.depth_mm - section.flange_mm
    rts = math.sqrt(math.sqrt(section.inertia_y_mm4 * section.warping_cw_mm6) / sx)
    a = section.torsion_j_mm4 / (sx * h0)  # c=1 for doubly symmetric H
    lp = 1.76 * section.radius_y_mm * math.sqrt(e / fy)
    lr = 1.95 * rts * e / (0.7 * fy) * math.sqrt(a + math.sqrt(a*a + 6.76*(0.7*fy/e)**2))
    _positive(rts, lp, lr, lr - lp)
    mp = fy * zx
    fcr = None
    if lb <= lp:
        region, raw, governing = "LB_LE_LP", mp, "YIELDING"
    elif lb <= lr:  # equality belongs to Eq.(11) in the accepted book
        region = "LP_LT_LB_LE_LR"
        raw = cb * (mp - (mp - 0.7 * fy * sx) * (lb - lp) / (lr - lp))
        governing = "YIELDING" if raw >= mp else "INELASTIC_LTB"
    else:
        region = "LB_GT_LR"
        slenderness = lb / rts
        fcr = cb * math.pi**2 * e / slenderness**2 * math.sqrt(1 + 0.078*a*slenderness**2)
        raw = fcr * sx
        governing = "YIELDING" if raw >= mp else "ELASTIC_LTB"
    mn = min(mp, raw)
    _positive(mp, raw, mn)
    return dict(**classification, flange_centroid_distance_mm=h0, c=1.0, rts_mm=rts,
                j_over_sx_h0=a, lp_mm=lp, lr_mm=lr, region=region,
                cb=cb, elastic_critical_stress_mpa=fcr,
                plastic_moment_nmm=mp, ltb_candidate_nmm=raw,
                nominal_moment_nmm=mn, governing_limit_state=governing,
                phi_b=PHI_B, omega_b=OMEGA_B,
                lrfd_capacity_nmm=PHI_B*mn, asd_capacity_nmm=mn/OMEGA_B)


def _shear_coefficients(ratio, e, fy):
    """Book coefficient branches, separated for exact boundary verification."""
    _positive(ratio, e, fy)
    if ratio >= 260:
        raise _Unsupported("Unstiffened kv=5 provision requires h/tw < 260.")
    kv = 5.0
    rolled_limit = 2.24 * math.sqrt(e / fy)
    first = 1.10 * math.sqrt(kv * e / fy)
    second = 1.37 * math.sqrt(kv * e / fy)
    if ratio <= rolled_limit:
        cv, phi, omega, region = 1.0, 1.0, 1.50, "ROLLED_WEB_YIELDING"
    else:
        phi, omega = 0.90, 1.67
        if ratio <= first:
            cv, region = 1.0, "WEB_YIELDING"
        elif ratio <= second:
            cv, region = first / ratio, "INELASTIC_SHEAR_BUCKLING"
        else:
            cv, region = 1.51 * kv * e / (ratio**2 * fy), "ELASTIC_SHEAR_BUCKLING"
    return dict(rolled_web_limit=rolled_limit, cv_yield_limit=first,
                cv_inelastic_limit=second, unstiffened_web_limit=260.0,
                kv=kv, cv=cv, phi_v=phi, omega_v=omega,
                governing_limit_state=region)


def _web_shear_strength(section, material):
    """Book 6.2, unstiffened rolled H, kv=5, no tension-field action."""
    clear = _geometry(section, material)
    ratio = clear / section.web_mm
    coefficients = _shear_coefficients(ratio, material.elastic_modulus_mpa, material.fy_mpa)
    area = section.depth_mm * section.web_mm  # Aw=d*tw, NOT clear h*tw
    vn = 0.6 * material.fy_mpa * area * coefficients["cv"]
    _positive(area, coefficients["cv"], vn)
    return dict(**coefficients, clear_web_mm=clear, web_width_thickness=ratio,
                web_area_mm2=area, nominal_shear_n=vn,
                lrfd_capacity_n=coefficients["phi_v"]*vn,
                asd_capacity_n=vn/coefficients["omega_v"],
                stiffener_slenderness_limit=2.46*math.sqrt(material.elastic_modulus_mpa/material.fy_mpa))


def _trace(clauses, pages):
    return dict(section=asdict(SECTION), material=asdict(MATERIAL),
                source_sha256=SOURCE_SHA256, clauses=clauses, printed_pages=pages,
                data_status="Book example inputs only; not an authoritative manufacturer catalog")


def check_flexure(request):
    """Check one braced segment of the verified H section; Lb in mm, M in kN-m.

    Cb is supplied with its provenance, 1 <= Cb <= 5. Both segment ends must
    have the required restraint. Cb=1 is the supported conservative option.
    Lb=0 explicitly represents continuous restraint; bracing is not designed.
    """
    check = "FLEXURE"
    error = _validate(request, check, _FLEXURE,
                      ("prismatic_undamaged", "support_twist_restrained", "segment_ends_braced", "major_axis_only"),
                      ("moment_knm", "unbraced_length_mm", "cb"))
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
        mid = _flexural_strength(SECTION, MATERIAL, request["unbraced_length_mm"], request["cb"])
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
                   inputs=dict(request), reference=_trace(["Table 1(b), rows 10/15", "5.1", "5.2 Eqs.(10)-(17a)", "Examples 10.3.1/10.3.2"], [9,10,28,29,30,90,91,92,93,94,95]),
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


def check_web_shear(request):
    """Check web-plane shear alone, unstiffened rolled H, demand in kN."""
    check = "SHEAR"
    error = _validate(request, check, _SHEAR,
                      ("prismatic_undamaged", "web_plane_only", "unstiffened_web"), ("shear_kn",))
    if error: return error
    try:
        mid = _web_shear_strength(SECTION, MATERIAL)
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
                   inputs=dict(request), reference=_trace(["6.1", "6.2.1 Eqs.(94)-(98)", "6.2.2", "Example 10.4.1"], [51,52,53,119,120]),
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


def moment_gradient_factor(request):
    """Eq.(9) from absolute kN-m at max/quarter/mid/three-quarter points.

    No force generation. All points must refer to the same doubly-end-braced
    segment and demand basis. Zero diagram conservatively returns Cb=1.
    """
    keys = {"maximum_knm", "quarter_knm", "midpoint_knm", "three_quarter_knm"}
    base = dict(basis_id=BASIS_ID, reference="5.1 Eq.(9), printed p.28; braced at both ends")
    if type(request) is not dict or request.keys() != keys:
        return dict(base, status="INVALID_INPUT", message="Four documented moment magnitudes required.")
    if not all(_number(v) and v >= 0 for v in request.values()):
        return dict(base, status="INVALID_INPUT", message="Moments must be finite nonnegative magnitudes.")
    maximum = request["maximum_knm"]
    points = [request[k] for k in ("quarter_knm", "midpoint_knm", "three_quarter_knm")]
    if any(v > maximum for v in points):
        return dict(base, status="INVALID_INPUT", message="Quarter-point value exceeds stated maximum.")
    if maximum == 0:
        cb = 1.0
    else:
        # Normalize first to avoid overflow and preserve scale invariance.
        a, b, c = [v / maximum for v in points]
        cb = 12.5 / (2.5 + 3*a + 4*b + 3*c)
    return dict(base, status="CALCULATED", cb=cb, inputs=dict(request),
                formula="12.5*Mmax/(2.5*Mmax+3*MA+4*MB+3*MC)",
                message="Moment-gradient factor only; no strength or bracing acceptance.")
