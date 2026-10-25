"""Book Eq.(9), arithmetic only, no analysis or brace design."""
from strd.domain.contracts import MomentGradientResult
from strd.domain.validation import _number
from .basis import MS2_BASIS_ID as BASIS_ID

def moment_gradient_factor(request: object) -> MomentGradientResult:
    """Eq.(9) from absolute kN-m at max/quarter/mid/three-quarter points.

    No force generation. All points must refer to the same doubly-end-braced
    segment and demand basis. Zero diagram conservatively returns Cb=1.
    """
    keys = {"maximum_knm", "quarter_knm", "midpoint_knm", "three_quarter_knm"}
    base = dict(basis_id=BASIS_ID, reference="5.1 Eq.(9), printed p.28; braced at both ends")
    if type(request) is not dict or request.keys() != keys:
        return dict(base, status="INVALID_INPUT", message="Four documented moment magnitudes required.")
    if not all(_number(v) and v >= 0 for v in request.values()):
        return dict(base, status="INVALID_INPUT", message="Moments must be finite nonnegative magnitudes.")
    maximum = request["maximum_knm"]
    points = [request[k] for k in ("quarter_knm", "midpoint_knm", "three_quarter_knm")]
    if any(v > maximum for v in points):
        return dict(base, status="INVALID_INPUT", message="Quarter-point value exceeds stated maximum.")
    if maximum == 0:
        cb = 1.0
    else:
        # Normalize first to avoid overflow and preserve scale invariance.
        a, b, c = [v / maximum for v in points]
        cb = 12.5 / (2.5 + 3*a + 4*b + 3*c)
    return dict(base, status="CALCULATED", cb=cb, inputs=dict(request),
                formula="12.5*Mmax/(2.5*Mmax+3*MA+4*MB+3*MC)",
                message="Moment-gradient factor only; no strength or bracing acceptance.")
