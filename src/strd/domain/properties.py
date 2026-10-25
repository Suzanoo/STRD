"""SI property records; construction alone does not establish verification."""
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class ReferenceSection:
    section_id: str
    depth_mm: float
    width_mm: float
    web_mm: float
    flange_mm: float
    root_radius_mm: float
    plastic_modulus_x_mm3: float


@dataclass(frozen=True)
class ReferenceMaterial:
    material_id: str
    fy_mpa: float
    elastic_modulus_mpa: float


class HSection(Protocol):
    """Read-only structural type for kernels, not catalog authorization."""
    @property
    def section_id(self) -> str: ...

    @property
    def depth_mm(self) -> float: ...

    @property
    def width_mm(self) -> float: ...

    @property
    def web_mm(self) -> float: ...

    @property
    def flange_mm(self) -> float: ...

    @property
    def root_radius_mm(self) -> float: ...

    @property
    def plastic_modulus_x_mm3(self) -> float: ...

    @property
    def elastic_modulus_x_mm3(self) -> float: ...

    @property
    def radius_y_mm(self) -> float: ...

    @property
    def inertia_y_mm4(self) -> float: ...

    @property
    def torsion_j_mm4(self) -> float: ...

    @property
    def warping_cw_mm6(self) -> float: ...
