"""Book-based bounded strength checks; not whole-member certification."""
from .bending import check_bending  # accepted MS-1 interface unchanged
from .h_beam import check_flexure, check_web_shear, moment_gradient_factor

__all__ = ["check_bending", "check_flexure", "check_web_shear", "moment_gradient_factor"]
