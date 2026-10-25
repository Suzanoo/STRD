"""Literal migration corpus. Golden responses supplement independent book proofs."""
import math
import random

def cases():
    identity=dict(section_id='EX10.3.1-H450x200x9x14',material_id='EX10.3.1-SS400-SM400',method='LRFD')
    ms1=dict(identity,basis_id='DPT-STEEL-MANUAL-ISBN9789744585974-EX10.3.1-v1',moment_knm=310.,continuously_braced=True,support_twist_restrained=True,major_axis_only=True)
    common=dict(identity,basis_id='DPT-STEEL-MANUAL-ISBN9789744585974-H-BENDING-SHEAR-v1',prismatic_undamaged=True)
    flex=dict(common,moment_knm=310.,unbraced_length_mm=3333.,cb=1.01,cb_source='VERIFIED_MOMENT_DIAGRAM',cb_reference='Example 10.3.2 p.94',support_twist_restrained=True,segment_ends_braced=True,major_axis_only=True)
    shear=dict(common,shear_kn=542.5,web_plane_only=True,unstiffened_web=True)
    cb=dict(maximum_knm=1.,quarter_knm=.972,midpoint_knm=1.,three_quarter_knm=.972)
    seq=[]
    def add(api,req):seq.append((f'{len(seq):04d}-{api}',api,req))
    for api,base in [('check_bending',ms1),('check_flexure',flex),('check_web_shear',shear),('moment_gradient_factor',cb)]:
        add(api,dict(base))
        for value in (None,[],1,'example',{}):add(api,value)
        add(api,dict(base,extra=1))
        for key in base:
            req=dict(base);del req[key];add(api,req)
            for value in (None,False,'','unsupported',float('nan'),float('inf'),-1,10**1000):add(api,dict(base,**{key:value}))
    for method in ('ASD','LRFD'):
        for lb in (0.,1.,2212.571428571429,6594.583800917255,10000.,1e308):
            for length in (math.nextafter(lb,0),lb,math.nextafter(lb,math.inf)):
                for factor in (1.,1.01,5.):add('check_flexure',dict(flex,method=method,unbraced_length_mm=length,cb=factor))
        for api,base,key,cap in [('check_bending',ms1,'moment_knm',237.81137724550898 if method=='ASD' else 357.4305),('check_flexure',dict(flex,unbraced_length_mm=0),'moment_knm',237.81137724550898 if method=='ASD' else 357.4305),('check_web_shear',shear,'shear_kn',396.9 if method=='ASD' else 595.35)]:
            for demand in (0.,math.nextafter(cap,0),cap,math.nextafter(cap,math.inf),cap*2):add(api,dict(base,method=method,**{key:demand}))
    rng=random.Random(20261024)
    for _ in range(60):add('check_flexure',dict(flex,method=rng.choice(['ASD','LRFD']),unbraced_length_mm=rng.uniform(0,30000),cb=rng.uniform(1,5),moment_knm=rng.uniform(0,700)))
    for scale in (0.,1.,1e-300,1e300):add('moment_gradient_factor',{k:v*scale for k,v in cb.items()})
    return seq
