"""Reference integrity and unsupported applicability; internal only."""
from strd.domain.properties import HSection, ReferenceSection, ReferenceMaterial
from strd.domain.contracts import StrengthResult
from dataclasses import asdict
from strd.domain.validation import _number

class _Unsupported(ValueError):
    pass


def _positive(*values):
    if not all(_number(v) and v > 0 for v in values):
        raise ValueError("Nonpositive or nonfinite engineering intermediate/reference value.")


def _geometry(section: HSection, material: ReferenceMaterial) -> float:
    _positive(*(v for k, v in asdict(section).items() if k != "section_id"),
              material.fy_mpa, material.elastic_modulus_mpa)
    if not (section.web_mm < section.width_mm and
            section.plastic_modulus_x_mm3 >= section.elastic_modulus_x_mm3 and
            material.fy_mpa < material.elastic_modulus_mpa):
        raise ValueError("Inconsistent section/material reference data.")
    clear = section.depth_mm - 2 * (section.flange_mm + section.root_radius_mm)
    _positive(clear)
    return clear
