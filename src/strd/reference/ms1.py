"""Immutable example data, deliberately independent of the legacy CSV catalog."""

from dataclasses import dataclass

from strd.domain.properties import ReferenceSection as SectionProperties, ReferenceMaterial as MaterialProperties
from strd.engineering.dpt.basis import (MS1_BASIS_ID as BASIS_ID,
    MS1_CALCULATOR_VERSION as CALCULATOR_VERSION, SOURCE_SHA256, PHI_B, OMEGA_B)


@dataclass(frozen=True)
class ReferenceSection(SectionProperties):
    section_id: str = "EX10.3.1-H450x200x9x14"
    depth_mm: float = 450.0
    width_mm: float = 200.0
    web_mm: float = 9.0
    flange_mm: float = 14.0
    root_radius_mm: float = 18.0
    plastic_modulus_x_mm3: float = 1621000.0


@dataclass(frozen=True)
class ReferenceMaterial(MaterialProperties):
    material_id: str = "EX10.3.1-SS400-SM400"
    fy_mpa: float = 245.0
    elastic_modulus_mpa: float = 200000.0


SECTION = ReferenceSection()
MATERIAL = ReferenceMaterial()
