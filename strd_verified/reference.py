"""Immutable example data, deliberately independent of the legacy CSV catalog."""

from dataclasses import dataclass

BASIS_ID = "DPT-STEEL-MANUAL-ISBN9789744585974-EX10.3.1-v1"
CALCULATOR_VERSION = "MS1-1"
SOURCE_SHA256 = "8e7f8411228698cc3cffdb69ce50e284e4a95f535d48052cb61af0f5c47b95a9"


@dataclass(frozen=True)
class ReferenceSection:
    section_id: str = "EX10.3.1-H450x200x9x14"
    depth_mm: float = 450.0
    width_mm: float = 200.0
    web_mm: float = 9.0
    flange_mm: float = 14.0
    root_radius_mm: float = 18.0
    plastic_modulus_x_mm3: float = 1621000.0


@dataclass(frozen=True)
class ReferenceMaterial:
    material_id: str = "EX10.3.1-SS400-SM400"
    fy_mpa: float = 245.0
    elastic_modulus_mpa: float = 200000.0


SECTION = ReferenceSection()
MATERIAL = ReferenceMaterial()
PHI_B = 0.90
OMEGA_B = 1.67
