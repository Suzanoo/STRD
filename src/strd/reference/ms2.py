"""MS-2 evidence fixture, not a general section/material catalog.

The MS-1 record is extended, not replaced. Values are the stated book inputs;
see docs/MS2_REFERENCE.md for property-by-property provenance and rounding.
"""
from dataclasses import dataclass
from .ms1 import ReferenceSection, MATERIAL, SOURCE_SHA256

from strd.engineering.dpt.basis import (MS2_BASIS_ID as BASIS_ID,
    MS2_CALCULATOR_VERSION as CALCULATOR_VERSION)


@dataclass(frozen=True)
class HReferenceSection(ReferenceSection):
    elastic_modulus_x_mm3: float = 1490000.0  # Sx, not plastic Zx
    radius_y_mm: float = 44.0
    inertia_y_mm4: float = 18700000.0
    torsion_j_mm4: float = 472000.0
    warping_cw_mm6: float = 890000000000.0


SECTION = HReferenceSection()
