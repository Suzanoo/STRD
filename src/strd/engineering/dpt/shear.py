"""Retained Section 6.2 equations; synthetic tests do not expand the catalog."""
from strd.domain.properties import HSection, ReferenceSection, ReferenceMaterial
from strd.domain.contracts import StrengthResult
import math
from .validation import _positive, _geometry, _Unsupported

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


def _web_shear_strength(section: HSection, material: ReferenceMaterial) -> dict:
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
