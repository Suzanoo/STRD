"""MS-2 evidence fixture, not a general section/material catalog.

The MS-1 record is extended, not replaced. Values are the stated book inputs;
see docs/MS2_REFERENCE.md for property-by-property provenance and rounding.
"""
from dataclasses import dataclass
from .reference import ReferenceSection, MATERIAL, SOURCE_SHA256

BASIS_ID = "DPT-STEEL-MANUAL-ISBN9789744585974-H-BENDING-SHEAR-v1"
CALCULATOR_VERSION = "MS2-1"


@dataclass(frozen=True)
class HReferenceSection(ReferenceSection):
    elastic_modulus_x_mm3: float = 1490000.0  # Sx, not plastic Zx
    radius_y_mm: float = 44.0
    inertia_y_mm4: float = 18700000.0
    torsion_j_mm4: float = 472000.0
    warping_cw_mm6: float = 890000000000.0


SECTION = HReferenceSection()
