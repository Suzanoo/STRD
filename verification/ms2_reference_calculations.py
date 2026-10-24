"""Independent Decimal worksheet using book literals, no production imports.

Run from repo root: python verification/ms2_reference_calculations.py
This is verification evidence, not an alternative product calculator.
"""
import json
from decimal import Decimal, localcontext


def reference_values():
    with localcontext() as context:
        context.prec = 50
        d = Decimal
        e, fy = d('200000'), d('245')
        sx, zx, ry = d('1490000'), d('1621000'), d('44')
        iy, cw, j, h0 = d('18700000'), d('890000000000'), d('472000'), d('436')
        rts_squared = (iy*cw).sqrt()/sx
        rts = rts_squared.sqrt()
        lp = d('1.76')*ry*(e/fy).sqrt()
        a = j/(sx*h0)
        lr = d('1.95')*rts*e/(d('.7')*fy)*(a+(a*a+d('6.76')*(d('.7')*fy/e)**2).sqrt()).sqrt()
        mp, residual = fy*zx, d('.7')*fy*sx
        # Weighted endpoint interpolation is independent of production expression.
        def inelastic(lb, cb):
            return min(mp, cb*((lr-lb)*mp+(lb-lp)*residual)/(lr-lp))
        pi = d('3.1415926535897932384626433832795028841971693993751')
        def elastic(lb, cb):
            # Algebraic alternative: no squared slenderness denominator.
            factor = cb*pi*pi*e*rts/(lb*lb)
            return min(mp, sx*factor*(rts_squared+d('.078')*a*lb*lb).sqrt())
        cb_inner = d('12.5')/(d('2.5')+d(6)*d('.972')+d(4))
        cb_outer = d('12.5')*d('.889')/(d('2.5')*d('.889')+d(3)*d('.306')+d(4)*d('.556')+d(3)*d('.750'))
        nominal = inelastic(d(3333), d('1.01'))
        book_staged = d('1.01')*(d('397.1e6')-(d('397.1e6')-residual)*d(1120)/d(4378))
        vn = d('.6')*fy*d(450)*d(9)
        values = dict(rts_mm=rts, lp_mm=lp, lr_mm=lr, mp_nmm=mp,
                      cb_inner=cb_inner, cb_outer=cb_outer,
                      book_staged_mn_nmm=book_staged,
                      example_10_3_2_mn_nmm=nominal,
                      example_10_3_2_lrfd_knm=nominal*d('.9')/d('1e6'),
                      example_10_3_2_asd_knm=nominal/d('1.67')/d('1e6'),
                      unrounded_cb_mn_nmm=inelastic(d(3333),cb_inner),
                      at_lp_nmm=mp, at_lr_inelastic_nmm=residual,
                      at_lr_elastic_limit_nmm=elastic(lr,d(1)),
                      elastic_10000_nmm=elastic(d(10000),d(1)),
                      shear_vn_n=vn, shear_lrfd_kn=vn/d(1000),
                      shear_asd_kn=vn/d('1.5')/d(1000),
                      shear_rolled_limit=d('2.24')*(e/fy).sqrt(),
                      shear_first_limit=d('1.1')*(d(5)*e/fy).sqrt(),
                      shear_second_limit=d('1.37')*(d(5)*e/fy).sqrt(),
                      cv_at_80=d('1.1')*(d(5)*e/fy).sqrt()/d(80),
                      cv_at_100=d('1.51')*d(5)*e/(d(100)**2*fy))
        return {k: str(v) for k,v in values.items()}


if __name__ == '__main__':
    print(json.dumps(reference_values(), indent=2, allow_nan=False))
