"""Book Table 1(b), rolled H flange and web."""
from strd.domain.properties import HSection, ReferenceSection, ReferenceMaterial
from strd.domain.contracts import StrengthResult
import math
from .validation import _geometry

def _classify(section: HSection, material: ReferenceMaterial) -> dict:
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
