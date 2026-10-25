"""Supported fixed-fixture API; no public property override or catalog fallback."""
from .domain.contracts import StrengthResult
from .reference import ms1, ms2
from .engineering.dpt.continuous_bending import _check_bending
from .engineering.dpt.checks import _check_flexure, _check_web_shear
from .engineering.dpt.moment_gradient import moment_gradient_factor


def check_bending(request: object) -> StrengthResult:
    """Accepted MS1 continuous-bracing contract, including N-mm comparison."""
    return _check_bending(request, ms1.SECTION, ms1.MATERIAL)


def check_flexure(request: object) -> StrengthResult:
    """Accepted MS2 major-axis bending contract; all three LTB regions."""
    return _check_flexure(request, ms2.SECTION, ms2.MATERIAL)


def check_web_shear(request: object) -> StrengthResult:
    """Accepted MS2 unstiffened web shear contract."""
    return _check_web_shear(request, ms2.SECTION, ms2.MATERIAL)
