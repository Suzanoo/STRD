"""MS1 compatibility facade; local bindings preserve accepted fault-test seams."""
from .reference import SECTION, MATERIAL
from strd.domain.validation import _number
from strd.engineering.dpt.continuous_bending import _check_bending


def check_bending(request):
    return _check_bending(request, SECTION, MATERIAL)
