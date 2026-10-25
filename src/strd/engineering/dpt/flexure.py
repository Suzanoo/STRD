"""Retained Section 5.2 equations; explicit-property internal kernel."""
from strd.domain.properties import HSection, ReferenceSection, ReferenceMaterial
from strd.domain.contracts import StrengthResult
import math
from .basis import PHI_B, OMEGA_B
from .classification import _classify
from .validation import _positive, _Unsupported

def _flexural_strength(section: HSection, material: ReferenceMaterial, lb: float, cb: float) -> dict:
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
