"""Pure calculation API for the continuously braced example envelope only.

No UI, filesystem, legacy imports or load-analysis side effects.
All reported capacities are conditional on the explicitly supplied assumptions.
"""

import math
from dataclasses import asdict

from .reference import (
    BASIS_ID, CALCULATOR_VERSION, SOURCE_SHA256, SECTION, MATERIAL, PHI_B, OMEGA_B,
)

_REQUIRED = frozenset({
    "basis_id", "section_id", "material_id", "method", "moment_knm",
    "continuously_braced", "support_twist_restrained", "major_axis_only",
})
_FLAGS = ("continuously_braced", "support_twist_restrained", "major_axis_only")
_NOT_CHECKED = (
    "shear", "deflection/serviceability", "connections/local bearing",
    "axial/combined actions/torsion", "global stability", "bracing adequacy",
)


def _result(status, message, **details):
    return {
        "status": status,
        "message": message,
        "scope": "MS-1 major-axis bending proof only",
        "basis_id": BASIS_ID,
        "calculator_version": CALCULATOR_VERSION,
        "not_checked": list(_NOT_CHECKED),
        **details,
    }


def _number(value):
    # bool is an int in Python, but is not an engineering scalar input.
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, ValueError):
        return False


def _reference_valid():
    values = [v for k, v in asdict(SECTION).items() if k != "section_id"]
    values += [MATERIAL.fy_mpa, MATERIAL.elastic_modulus_mpa, PHI_B, OMEGA_B]
    if not all(_number(v) and v > 0 for v in values):
        return False
    return (
        SECTION.web_mm < SECTION.width_mm
        and SECTION.depth_mm > 2 * (SECTION.flange_mm + SECTION.root_radius_mm)
        and 0 < PHI_B <= 1 <= OMEGA_B
        and MATERIAL.fy_mpa < MATERIAL.elastic_modulus_mpa
    )


def check_bending(request):
    """Return a fresh JSON-compatible result; never read console input.

    Request must contain exactly the documented fields. Moment is a nonnegative
    magnitude in kN-m, already on the selected ASD or LRFD demand basis.
    Missing/invalid data returns INVALID_INPUT; valid but unavailable cases
    return UNSUPPORTED. Neither includes a capacity or utilization ratio.
    PASS/FAIL applies solely to the supported bending check, not the member.
    """
    if type(request) is not dict:
        return _result("INVALID_INPUT", "Request must be a dictionary.")
    missing = _REQUIRED - request.keys()
    extra = request.keys() - _REQUIRED
    if missing or extra:
        return _result("INVALID_INPUT", "Request fields do not match the proof schema.",
                       missing=sorted(missing), unexpected=sorted(map(str, extra)))
    for key in ("basis_id", "section_id", "material_id", "method"):
        if type(request[key]) is not str or not request[key]:
            return _result("INVALID_INPUT", f"{key} must be a nonempty string.")
    for key in _FLAGS:
        if type(request[key]) is not bool:
            return _result("INVALID_INPUT", f"{key} must be an explicit boolean.")
    moment = request["moment_knm"]
    if not _number(moment) or moment < 0:
        return _result("INVALID_INPUT", "moment_knm must be a finite nonnegative magnitude.")
    try:
        demand_nmm = moment * 1e6
    except OverflowError:
        return _result("INVALID_INPUT", "Moment overflows the internal unit conversion.")
    if not math.isfinite(demand_nmm):
        return _result("INVALID_INPUT", "Moment overflows the internal unit conversion.")
    supported = {
        "basis_id": (BASIS_ID,), "section_id": (SECTION.section_id,),
        "material_id": (MATERIAL.material_id,), "method": ("ASD", "LRFD"),
    }
    for key, allowed in supported.items():
        if request[key] not in allowed:
            return _result("UNSUPPORTED", f"Unsupported {key}; see the MS-1 scope.")
    if not all(request[key] for key in _FLAGS):
        return _result("UNSUPPORTED", "Requires continuous bracing, support twist restraint and major-axis-only loading.")
    if not _reference_valid():
        return _result("INVALID_INPUT", "Internal reference data failed integrity validation.")

    flange_ratio = SECTION.width_mm / (2 * SECTION.flange_mm)
    web_clear_mm = SECTION.depth_mm - 2 * (SECTION.flange_mm + SECTION.root_radius_mm)
    web_ratio = web_clear_mm / SECTION.web_mm
    modulus_ratio = MATERIAL.elastic_modulus_mpa / MATERIAL.fy_mpa
    flange_limit = 0.38 * math.sqrt(modulus_ratio)
    web_limit = 3.76 * math.sqrt(modulus_ratio)
    if flange_ratio > flange_limit or web_ratio > web_limit:
        return _result("UNSUPPORTED", "Proof is limited to compact flange and web.")

    nominal_nmm = MATERIAL.fy_mpa * SECTION.plastic_modulus_x_mm3
    lrfd_nmm = PHI_B * nominal_nmm
    asd_nmm = nominal_nmm / OMEGA_B
    capacity_nmm = lrfd_nmm if request["method"] == "LRFD" else asd_nmm
    ratio = demand_nmm / capacity_nmm
    status = "PASS" if demand_nmm <= capacity_nmm else "FAIL"
    return _result(
        status, "Supported bending check passed." if status == "PASS" else "Bending demand exceeds the supported capacity.",
        inputs=dict(request),
        reference={
            "section": asdict(SECTION), "material": asdict(MATERIAL),
            "source_sha256": SOURCE_SHA256,
            "printed_pages": [28, 29, 74, 90, 91],
            "clauses": ["2.4 / Table 1(b)", "5.1", "5.2.1 Eq.(10)", "Example 10.3.1"],
        },
        intermediates={
            "flange_width_thickness": flange_ratio,
            "flange_compact_limit": flange_limit,
            "clear_web_mm": web_clear_mm,
            "web_width_thickness": web_ratio,
            "web_compact_limit": web_limit,
            "flange_class": "COMPACT", "web_class": "COMPACT",
            "plastic_modulus_x_mm3": SECTION.plastic_modulus_x_mm3,
            "nominal_moment_nmm": nominal_nmm,
            "phi_b": PHI_B, "omega_b": OMEGA_B,
            "lrfd_capacity_nmm": lrfd_nmm, "asd_capacity_nmm": asd_nmm,
            "demand_nmm": demand_nmm,
        },
        capacity_knm=capacity_nmm / 1e6, utilization=ratio,
        governing_limit_state="YIELDING",
        lateral_torsional_buckling="Not governing under the asserted continuous-bracing assumption of Example 10.3.1; bracing adequacy not designed.",
        formulas={
            "classification": "b/tf = B/(2tf); h/tw = [H-2(tf+r)]/tw; limits 0.38sqrt(E/Fy), 3.76sqrt(E/Fy)",
            "nominal": "Mn = Mp = Fy * Zx_plastic",
            "design": "LRFD: phi_b * Mn; ASD: Mn / omega_b",
            "comparison": "demand <= capacity; ratio = demand / capacity",
            "units": "1 kN-m = 1,000,000 N-mm; MPa = N/mm^2",
        },
    )
