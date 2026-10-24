"""Independent book-literal/Decimal verification; synthetic data is not a catalog."""
import ast
import contextlib
from dataclasses import asdict, replace, FrozenInstanceError
import io
import json
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from strd_verified import check_bending, check_flexure, check_web_shear, moment_gradient_factor
from strd_verified.h_reference import BASIS_ID, SECTION, MATERIAL
from strd_verified.h_beam import _flexural_strength, _shear_coefficients, _web_shear_strength, _classify, _Unsupported
from strd_verified.ms2_examples import examples
from verification.ms2_reference_calculations import reference_values


def common():
    return dict(basis_id=BASIS_ID, section_id=SECTION.section_id, material_id=MATERIAL.material_id,
                method='LRFD', prismatic_undamaged=True)


def flex(**changes):
    req=dict(common(), moment_knm=310., unbraced_length_mm=3333., cb=1.01,
             cb_source='VERIFIED_MOMENT_DIAGRAM', cb_reference='Example 10.3.2 p.94',
             support_twist_restrained=True, segment_ends_braced=True, major_axis_only=True)
    req.update(changes)
    return req


def shear(**changes):
    req=dict(common(), shear_kn=542.5, web_plane_only=True, unstiffened_web=True)
    req.update(changes)
    return req


def profile(**changes):
    req=dict(maximum_knm=1., quarter_knm=.972, midpoint_knm=1., three_quarter_knm=.972)
    req.update(changes)
    return req


class HBeamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle={k:float(v) for k,v in reference_values().items()}

    def close(self, actual, expected):
        self.assertTrue(math.isclose(actual,expected,rel_tol=2e-12,abs_tol=1e-9),(actual,expected))

    def test_fixture_provenance_values(self):
        self.assertEqual(asdict(SECTION),dict(section_id='EX10.3.1-H450x200x9x14',
            depth_mm=450.,width_mm=200.,web_mm=9.,flange_mm=14.,root_radius_mm=18.,
            plastic_modulus_x_mm3=1621000.,elastic_modulus_x_mm3=1490000.,radius_y_mm=44.,
            inertia_y_mm4=18700000.,torsion_j_mm4=472000.,warping_cw_mm6=890000000000.))
        self.assertEqual((MATERIAL.fy_mpa,MATERIAL.elastic_modulus_mpa),(245,200000))
        with self.assertRaises(FrozenInstanceError):SECTION.radius_y_mm=1

    def test_continuous_bracing_matches_ms1(self):
        from strd_verified.reference import BASIS_ID as old_basis
        for method,demand in [('LRFD',310),('ASD',200)]:
            old=check_bending(dict(basis_id=old_basis,section_id=SECTION.section_id,
                material_id=MATERIAL.material_id,method=method,moment_knm=demand,
                continuously_braced=True,support_twist_restrained=True,major_axis_only=True))
            new=check_flexure(flex(method=method,moment_knm=demand,unbraced_length_mm=0,cb=1,cb_source='CONSERVATIVE'))
            self.assertEqual(new['capacity_knm'],old['capacity_knm'])
            self.assertEqual(new['status'],old['status'])
            self.assertEqual(new['intermediates']['nominal_moment_nmm'],397145000)

    def test_example_10_3_2_independent_intermediates(self):
        r=check_flexure(flex());m=r['intermediates']
        for k in ('rts_mm','lp_mm','lr_mm'):self.close(m[k],self.oracle[k])
        self.close(m['nominal_moment_nmm'],self.oracle['example_10_3_2_mn_nmm'])
        self.close(r['capacity_knm'],328.0917358995603)
        self.assertEqual(m['clear_web_mm'],386)
        self.assertEqual(m['flange_centroid_distance_mm'],436)
        self.assertEqual(m['demand_nmm'],310000000)
        self.assertEqual((r['status'],r['governing_limit_state']),('PASS','INELASTIC_LTB'))

    def test_example_10_3_2_asd_and_rounding(self):
        r=check_flexure(flex(method='ASD',moment_knm=200));m=r['intermediates']
        self.close(r['capacity_knm'],self.oracle['example_10_3_2_asd_knm'])
        for actual,expected in [(m['nominal_moment_nmm']/1e6,364.5),(m['lrfd_capacity_nmm']/1e6,328.1),(r['capacity_knm'],218.3)]:
            self.assertLess(abs(actual-expected),.05)
        self.assertLess(abs(self.oracle['book_staged_mn_nmm']/1e6-364.5),.05)
        self.assertTrue(3 < m['lr_mm']-6591 < 4)

    def test_exact_ltb_boundary_ownership(self):
        m=check_flexure(flex())['intermediates'];lp,lr=m['lp_mm'],m['lr_mm']
        for boundary,left,right in [(lp,'LB_LE_LP','LP_LT_LB_LE_LR'),(lr,'LP_LT_LB_LE_LR','LB_GT_LR')]:
            for lb,expected in [(math.nextafter(boundary,0),left),(boundary,left),(math.nextafter(boundary,math.inf),right)]:
                r=check_flexure(flex(unbraced_length_mm=lb,cb=1))
                self.assertEqual(r['intermediates']['region'],expected)
        at=check_flexure(flex(unbraced_length_mm=lr,cb=1))['intermediates']['nominal_moment_nmm']
        after=check_flexure(flex(unbraced_length_mm=math.nextafter(lr,math.inf),cb=1))['intermediates']['nominal_moment_nmm']
        self.close(at,255535000);self.close(after,self.oracle['at_lr_elastic_limit_nmm'])
        self.assertTrue(.001 < (at-after)/at < .0012)  # published coefficient step

    def test_elastic_ltb_and_design_factors(self):
        for cb in (1,1.5,2):
            r=check_flexure(flex(unbraced_length_mm=10000,cb=cb))
            self.close(r['intermediates']['nominal_moment_nmm'],self.oracle['elastic_10000_nmm']*cb)
            self.assertEqual(r['governing_limit_state'],'ELASTIC_LTB')
        r=check_flexure(flex(unbraced_length_mm=10000,cb=1,method='ASD'))
        self.close(r['capacity_knm'],self.oracle['elastic_10000_nmm']/1.67/1e6)
        self.assertEqual(r['status'],'FAIL')

    def test_plastic_cap_governs_both_ltb_regions(self):
        for lb in (3333,10000):
            r=check_flexure(flex(unbraced_length_mm=lb,cb=5));m=r['intermediates']
            self.assertEqual(r['governing_limit_state'],'YIELDING')
            self.assertEqual(m['nominal_moment_nmm'],397145000)
            self.assertGreater(m['ltb_candidate_nmm'],m['plastic_moment_nmm'])
        for cb in (1,1.01,5):
            self.assertEqual(check_flexure(flex(unbraced_length_mm=1000,cb=cb))['capacity_knm'],357.4305)

    def test_cb_inner_outer_and_segment_governing(self):
        inner=moment_gradient_factor(profile());outer=moment_gradient_factor(profile(maximum_knm=.889,quarter_knm=.306,midpoint_knm=.556,three_quarter_knm=.750))
        self.close(inner['cb'],self.oracle['cb_inner']);self.close(outer['cb'],self.oracle['cb_outer'])
        self.assertEqual(inner['status'],'CALCULATED')
        a=check_flexure(flex(cb=inner['cb']));b=check_flexure(flex(moment_knm=310*.889,cb=outer['cb']))
        self.close(a['intermediates']['nominal_moment_nmm'],self.oracle['unrounded_cb_mn_nmm'])
        self.assertGreater(a['utilization'],b['utilization'])

    def test_cb_scale_uniform_zero_and_upper_bound(self):
        for magnitude in (0,1e-250,1,1e300):
            self.assertEqual(moment_gradient_factor({k:magnitude for k in profile()})['cb'],1)
        self.assertEqual(moment_gradient_factor(profile(quarter_knm=0,midpoint_knm=0,three_quarter_knm=0))['cb'],5)
        a=moment_gradient_factor(profile())['cb']
        for scale in (1e-100,1e100):
            self.close(moment_gradient_factor({k:v*scale for k,v in profile().items()})['cb'],a)

    def test_cb_invalid_diagrams_and_provenance(self):
        for req in (None,[],{},dict(profile(),extra=1),profile(quarter_knm=2)):
            self.assertEqual(moment_gradient_factor(req)['status'],'INVALID_INPUT')
        for key in profile():
            for value in (True,None,'1',-1,float('nan'),float('inf'),10**1000):
                r=moment_gradient_factor(profile(**{key:value}))
                self.assertEqual(r['status'],'INVALID_INPUT');self.assertNotIn('cb',r)
        for changes,status in [({'cb':.99},'UNSUPPORTED'),({'cb':5.1},'UNSUPPORTED'),
                ({'cb_source':'CONSERVATIVE'},'INVALID_INPUT'),({'cb_source':'guess'},'UNSUPPORTED'),
                ({'cb_reference':' '},'INVALID_INPUT'),({'cb_reference':1},'INVALID_INPUT')]:
            self.assertEqual(check_flexure(flex(**changes))['status'],status)

    def test_example_10_4_1(self):
        for method,demand,cap in [('LRFD',542.5,595.35),('ASD',350,396.9)]:
            r=check_web_shear(shear(method=method,shear_kn=demand));m=r['intermediates']
            self.assertEqual(r['status'],'PASS');self.close(r['capacity_kn'],cap)
            self.assertEqual((m['phi_v'],m['omega_v'],m['cv']),(1,1.5,1))
            self.assertEqual(m['web_area_mm2'],4050);self.assertEqual(m['clear_web_mm'],386)
            self.assertEqual(m['nominal_shear_n'],595350);self.assertEqual(m['demand_n'],demand*1000)
            self.close(m['web_width_thickness'],386/9)
            self.assertTrue(m['transverse_stiffener_exemption_6_2_2'])
            self.assertLessEqual(abs(m['nominal_shear_n']/1000-595.4),.050000001)

    def test_shear_regions_and_whole_internal_path(self):
        for ratio,cv,phi,omega,state in [(40,1,1,1.5,'ROLLED_WEB_YIELDING'),(65,1,.9,1.67,'WEB_YIELDING'),
            (80,self.oracle['cv_at_80'],.9,1.67,'INELASTIC_SHEAR_BUCKLING'),(100,self.oracle['cv_at_100'],.9,1.67,'ELASTIC_SHEAR_BUCKLING')]:
            m=_shear_coefficients(ratio,200000,245)
            self.close(m['cv'],cv);self.assertEqual((m['phi_v'],m['omega_v']),(phi,omega))
            self.assertEqual(m['governing_limit_state'],state)
            n=_web_shear_strength(replace(SECTION,web_mm=386/ratio),MATERIAL)
            expected=.6*245*450*(386/ratio)*cv
            self.close(n['nominal_shear_n'],expected)
            self.close(n['lrfd_capacity_n'],phi*expected);self.close(n['asd_capacity_n'],expected/omega)

    def test_shear_exact_boundaries_and_rounding_step(self):
        m=_shear_coefficients(40,200000,245)
        for key,left,right in [('rolled_web_limit','ROLLED_WEB_YIELDING','WEB_YIELDING'),
                ('cv_yield_limit','WEB_YIELDING','INELASTIC_SHEAR_BUCKLING'),
                ('cv_inelastic_limit','INELASTIC_SHEAR_BUCKLING','ELASTIC_SHEAR_BUCKLING')]:
            b=m[key]
            for x,state in [(math.nextafter(b,0),left),(b,left),(math.nextafter(b,math.inf),right)]:
                self.assertEqual(_shear_coefficients(x,200000,245)['governing_limit_state'],state)
        b=m['cv_inelastic_limit']
        low=_shear_coefficients(b,200000,245)['cv'];high=_shear_coefficients(math.nextafter(b,math.inf),200000,245)['cv']
        self.close(low,1.1/1.37);self.close(high,1.51/1.37**2)
        self.assertTrue(0 < high/low-1 < .002)
        self.assertEqual(_shear_coefficients(math.nextafter(260,0),200000,245)['governing_limit_state'],'ELASTIC_SHEAR_BUCKLING')
        for x in (260,261):
            with self.assertRaises(_Unsupported):_shear_coefficients(x,200000,245)

    def test_compactness_classes_reject_unsupported(self):
        self.assertEqual(_classify(SECTION,MATERIAL)['flange_class'],'COMPACT')
        for section,key,expected in [(replace(SECTION,flange_mm=8),'flange_class','NONCOMPACT'),
                (replace(SECTION,flange_mm=3),'flange_class','SLENDER'),
                (replace(SECTION,web_mm=3),'web_class','NONCOMPACT'),(replace(SECTION,web_mm=2),'web_class','SLENDER')]:
            self.assertEqual(_classify(section,MATERIAL)[key],expected)
            with self.assertRaises(_Unsupported):_flexural_strength(section,MATERIAL,0,1)
            with patch('strd_verified.h_beam.SECTION',section):
                r=check_flexure(flex());self.assertEqual(r['status'],'UNSUPPORTED');self.assertNotIn('capacity_knm',r)

    def test_compactness_boundary(self):
        flange_limit=.38*math.sqrt(200000/245);web_limit=3.76*math.sqrt(200000/245)
        for scale,expected in [(1-1e-10,'COMPACT'),(1,'COMPACT'),(1+1e-10,'NONCOMPACT')]:
            self.assertEqual(_classify(replace(SECTION,width_mm=28*flange_limit*scale),MATERIAL)['flange_class'],expected)
            self.assertEqual(_classify(replace(SECTION,web_mm=386/(web_limit*scale)),MATERIAL)['web_class'],expected)

    def test_missing_extra_and_non_dictionary(self):
        for fn,make in [(check_flexure,flex),(check_web_shear,shear)]:
            for bad in (None,[],0,'request'):self.assertEqual(fn(bad)['status'],'INVALID_INPUT')
            for key in make():
                req=make();del req[key];self.assertEqual(fn(req)['status'],'INVALID_INPUT')
            for key in ('axial_kn','minor_moment_knm','temperature','fy_mpa','custom_section'):
                self.assertEqual(fn(make(**{key:1}))['status'],'INVALID_INPUT')

    def test_invalid_scalars_and_overflow(self):
        for fn,make,keys in [(check_flexure,flex,('moment_knm','unbraced_length_mm','cb')),(check_web_shear,shear,('shear_kn',))]:
            for key in keys:
                for value in (None,True,'1',[],{},-1,float('nan'),float('inf'),-float('inf'),10**1000):
                    with self.subTest(key=key,value=str(value)[:10]):
                        r=fn(make(**{key:value}));self.assertEqual(r['status'],'INVALID_INPUT');self.assertNotIn('utilization',r)
            self.assertEqual(fn(make(**{keys[0]:1e308}))['status'],'INVALID_INPUT')
        self.assertEqual(check_flexure(flex(unbraced_length_mm=1e308))['status'],'INVALID_INPUT')

    def test_identifiers_and_assumptions(self):
        for fn,make,flags in [(check_flexure,flex,('prismatic_undamaged','support_twist_restrained','segment_ends_braced','major_axis_only')),
                              (check_web_shear,shear,('prismatic_undamaged','web_plane_only','unstiffened_web'))]:
            for key in ('basis_id','section_id','material_id','method'):
                self.assertEqual(fn(make(**{key:'unknown'}))['status'],'UNSUPPORTED')
                for value in (None,0,'',[]):self.assertEqual(fn(make(**{key:value}))['status'],'INVALID_INPUT')
            for key in flags:
                r=fn(make(**{key:False}));self.assertEqual(r['status'],'UNSUPPORTED');self.assertNotIn('utilization',r)
                for value in (None,0,1,'true'):self.assertEqual(fn(make(**{key:value}))['status'],'INVALID_INPUT')

    def test_reference_faults_do_not_pass_zero_demand(self):
        for key in asdict(SECTION):
            if key=='section_id':continue
            for value in (0,-1,float('nan')):
                with patch('strd_verified.h_beam.SECTION',replace(SECTION,**{key:value})):
                    for fn,req in [(check_flexure,flex(moment_knm=0)),(check_web_shear,shear(shear_kn=0))]:
                        r=fn(req);self.assertEqual(r['status'],'INVALID_INPUT');self.assertNotIn('utilization',r)
        for section in (replace(SECTION,depth_mm=40),replace(SECTION,elastic_modulus_x_mm3=2e6)):
            with patch('strd_verified.h_beam.SECTION',section):self.assertEqual(check_flexure(flex())['status'],'INVALID_INPUT')
        with patch('strd_verified.h_beam.MATERIAL',replace(MATERIAL,fy_mpa=0)):
            self.assertEqual(check_web_shear(shear())['status'],'INVALID_INPUT')

    def test_shear_limit_and_stiffener_exemption(self):
        with patch('strd_verified.h_beam.SECTION',replace(SECTION,web_mm=1)):
            self.assertEqual(check_web_shear(shear())['status'],'UNSUPPORTED')
        with patch('strd_verified.h_beam.SECTION',replace(SECTION,web_mm=386/100)):
            low=check_web_shear(shear(shear_kn=0));cap=low['capacity_kn']
            self.assertTrue(low['intermediates']['transverse_stiffener_exemption_6_2_2'])
            self.assertEqual(check_web_shear(shear(shear_kn=cap))['status'],'UNSUPPORTED')
            high=check_web_shear(shear(shear_kn=cap*1.01))
            self.assertEqual(high['status'],'FAIL');self.assertTrue(high['warnings'])

    def test_zero_equality_and_next_float_over_capacity(self):
        for fn,make,key,capkey in [(check_flexure,flex,'moment_knm','capacity_knm'),(check_web_shear,shear,'shear_kn','capacity_kn')]:
            for method in ('LRFD','ASD'):
                cap=fn(make(method=method))[capkey]
                for value,status in [(0,'PASS'),(math.nextafter(cap,0),'PASS'),(cap,'PASS'),(math.nextafter(cap,math.inf),'FAIL'),(cap*2,'FAIL')]:
                    self.assertEqual(fn(make(method=method,**{key:value}))['status'],status)

    def test_units(self):
        f=check_flexure(flex(moment_knm=1.234,unbraced_length_mm=10000));s=check_web_shear(shear(shear_kn=1.234))
        self.assertEqual(f['intermediates']['demand_nmm'],1234000)
        self.assertEqual(s['intermediates']['demand_n'],1234)
        self.assertEqual(f['intermediates']['region'],'LB_GT_LR')

    def test_deterministic_pure_fresh_results(self):
        for fn,make in [(check_flexure,flex),(check_web_shear,shear)]:
            req=make();before=dict(req);out=io.StringIO()
            with contextlib.redirect_stdout(out),patch('builtins.input',side_effect=AssertionError('I/O')),patch('builtins.open',side_effect=AssertionError('I/O')):
                first=fn(req);second=fn(req)
            self.assertEqual(out.getvalue(),'');self.assertEqual(req,before);self.assertEqual(first,second)
            json.dumps(first,allow_nan=False)
            first['reference']['section']['depth_mm']=1;first['not_checked'].clear()
            self.assertEqual(second,fn(req))

    def test_trace_exclusions_and_smoke(self):
        results=examples();json.dumps(results,allow_nan=False)
        self.assertEqual(len(results),7)
        for name,r in results.items():
            self.assertEqual(r['status'],'CALCULATED' if name.endswith('unrounded') else 'PASS')
            if name.endswith('unrounded'):continue
            self.assertEqual(r['basis_id'],BASIS_ID);self.assertEqual(r['calculator_version'],'MS2-1')
            self.assertTrue(r['reference']['clauses']);self.assertTrue(r['formulas']);self.assertTrue(r['assumptions'])
            self.assertIn('bracing strength and stiffness',r['not_checked'])
            self.assertEqual(len(r['reference']['source_sha256']),64)
        self.assertIn('web shear',check_flexure(flex())['not_checked'])
        self.assertIn('major-axis bending/LTB',check_web_shear(shear())['not_checked'])

    def test_legacy_short_lb_defect_and_verified_replacement(self):
        path=Path(__file__).resolve().parents[1]/'applications/flexural.py'
        tree=ast.parse(path.read_text(encoding='utf-8'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='LTB')
        scope={'np':SimpleNamespace(sqrt=math.sqrt,pi=math.pi)}
        exec(compile(ast.Module(body=[cls],type_ignores=[]),str(path),'exec'),scope)
        mat=SimpleNamespace(Fy=245,Es=200000);sec=SimpleNamespace(ry=4.4,Iy=1870,H=450,tf=14,Sx=1490)
        with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(UnboundLocalError):
            scope['LTB'](mat).hc_major(mat,sec,397145000,1,1,472000,890000000000)
        self.assertEqual(check_flexure(flex(unbraced_length_mm=1000,cb=1))['capacity_knm'],357.4305)


if __name__=='__main__':unittest.main()
