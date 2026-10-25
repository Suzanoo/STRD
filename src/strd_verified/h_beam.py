"""MS2 facade. Private aliases retain regression seams, not extension APIs."""
from .h_reference import SECTION, MATERIAL
from strd.engineering.dpt.checks import _check_flexure, _check_web_shear
from strd.engineering.dpt.moment_gradient import moment_gradient_factor
from strd.engineering.dpt.flexure import _flexural_strength
from strd.engineering.dpt.shear import _shear_coefficients, _web_shear_strength
from strd.engineering.dpt.classification import _classify
from strd.engineering.dpt.validation import _Unsupported


def check_flexure(request):
    return _check_flexure(request, SECTION, MATERIAL)


def check_web_shear(request):
    return _check_web_shear(request, SECTION, MATERIAL)
