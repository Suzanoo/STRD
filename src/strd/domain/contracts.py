"""Typed JSON-compatible contracts. Runtime validation, not hints, enforces inputs."""
from typing import Literal, TypedDict
Method = Literal['ASD', 'LRFD']
StrengthStatus = Literal['INVALID_INPUT', 'UNSUPPORTED', 'PASS', 'FAIL']

class Identity(TypedDict):
    basis_id: str
    section_id: str
    material_id: str
    method: Method

class BendingRequest(Identity):
    moment_knm: float
    continuously_braced: bool
    support_twist_restrained: bool
    major_axis_only: bool

class FlexureRequest(Identity):
    prismatic_undamaged: bool
    moment_knm: float
    unbraced_length_mm: float
    cb: float
    cb_source: Literal['CONSERVATIVE', 'VERIFIED_MOMENT_DIAGRAM']
    cb_reference: str
    support_twist_restrained: bool
    segment_ends_braced: bool
    major_axis_only: bool

class ShearRequest(Identity):
    prismatic_undamaged: bool
    shear_kn: float
    web_plane_only: bool
    unstiffened_web: bool

class MomentGradientRequest(TypedDict):
    maximum_knm: float
    quarter_knm: float
    midpoint_knm: float
    three_quarter_knm: float

class StrengthResultBase(TypedDict):
    status: StrengthStatus
    message: str
    scope: str
    basis_id: str
    calculator_version: str
    not_checked: list[str]

class StrengthResult(StrengthResultBase, total=False):
    check: Literal['FLEXURE', 'SHEAR']
    inputs: dict[str, object]
    reference: dict[str, object]
    intermediates: dict[str, object]
    capacity_knm: float
    capacity_kn: float
    utilization: float
    governing_limit_state: str
    lateral_torsional_buckling: str
    formulas: dict[str, str]
    assumptions: list[str]
    warnings: list[str]
    missing: list[str]
    unexpected: list[str]

class MomentGradientResultBase(TypedDict):
    status: Literal['INVALID_INPUT', 'CALCULATED']
    basis_id: str
    reference: str
    message: str

class MomentGradientResult(MomentGradientResultBase, total=False):
    cb: float
    inputs: dict[str, object]
    formula: str
