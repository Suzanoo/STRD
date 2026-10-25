"""Independent 50-digit worksheet; transcribed source literals, no engine imports.

SYS Engineer Ed6 printed pp15-17; DPT equations docs/MS2_REFERENCE.md.
Geometric Z includes four square-minus-quarter-circle root fillets. J uses
SYS p17; these are audit calculations, not new product property-generation APIs.
"""
from decimal import Decimal, localcontext
import json


def reference_values():
    with localcontext() as ctx:
        ctx.prec = 50
        D = Decimal
        pi = D('3.1415926535897932384626433832795028841971693993751')
        rows = [('450', '200', '9', '14', '18', '1680', '1490', '4.40', '1870', '56.9', '889000'),
                ('500', '200', '10', '16', '20', '2180', '1910', '4.33', '2140', '85.9', '1250000')]
        result = []
        for row in rows:
            depth, width, tw, tf, r, zx, sx, ry, iy, j, cw = map(D, row)
            zx *= 1000; sx *= 1000; ry *= 10; iy *= 10000; j *= 10000; cw *= 1000000
            e, fy = D(200000), D(245)
            h0 = depth-tf
            fillet_area = r*r*(1-pi/4)
            fillet_centroid = r*(D(5)/6-pi/4)/(1-pi/4)
            area = 2*width*tf+(depth-2*tf)*tw+4*fillet_area
            z_plain = width*tf*h0+tw*(depth-2*tf)**2/4
            z_fillet = z_plain+4*fillet_area*(depth/2-tf-fillet_centroid)
            alpha = -D('.042')+D('.2204')*tw/tf+D('.1355')*r/tf-D('.0865')*tw*r/tf**2-D('.0725')*tw**2/tf**2
            d1 = ((tf+r)**2+tw*(r+tw/4))/(2*r+tf)
            j_derived = (2*width*tf**3+(depth-2*tf)*tw**3)/3+2*alpha*d1**4-D('.42')*tf**4
            cw_derived = iy*h0*h0/4
            rts2 = (iy*cw).sqrt()/sx
            lp = D('1.76')*ry*(e/fy).sqrt()
            a = j/(sx*h0)
            lr = D('1.95')*rts2.sqrt()*e/(D('.7')*fy)*(a+(a*a+D('6.76')*(D('.7')*fy/e)**2).sqrt()).sqrt()
            mp, residual = fy*zx, D('.7')*fy*sx
            def capacity(length):
                lb = D(length)
                if lb <= lp: return mp
                if lb <= lr: return ((lr-lb)*mp+(lb-lp)*residual)/(lr-lp)
                return min(mp, sx*pi*pi*e*rts2.sqrt()/(lb*lb)*(rts2+D('.078')*a*lb*lb).sqrt())
            values = dict(area_mm2=area, plastic_without_fillets_mm3=z_plain,
                          plastic_with_fillets_mm3=z_fillet, j_derived_mm4=j_derived,
                          cw_derived_mm6=cw_derived, lp_mm=lp, lr_mm=lr,
                          rts_mm=rts2.sqrt(), mp_nmm=mp,
                          nominal_1000_nmm=capacity(1000), nominal_4000_nmm=capacity(4000),
                          nominal_10000_nmm=capacity(10000),
                          shear_nominal_n=D('.6')*fy*depth*tw,
                          shear_asd_kn=D('.6')*fy*depth*tw/D('1.5')/1000,
                          shear_lrfd_kn=D('.6')*fy*depth*tw/1000)
            result.append({k: float(v) for k,v in values.items()})
        return result

if __name__ == '__main__':
    print(json.dumps(reference_values(), indent=2, allow_nan=False))
