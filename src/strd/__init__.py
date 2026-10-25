"""Bounded book-based engineering engine; no whole-member certification."""
from .api import check_bending, check_flexure, check_web_shear, moment_gradient_factor
__version__ = '0.1.0'
__all__ = ['check_bending', 'check_flexure', 'check_web_shear', 'moment_gradient_factor']
