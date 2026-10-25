"""Strict finite scalar policy shared by accepted checks."""
import math

def _number(value):
    # bool is an int in Python, but is not an engineering scalar input.
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, ValueError):
        return False
