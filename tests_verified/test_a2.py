"""A2 source transcription, independent arithmetic and service verification."""
import copy
from dataclasses import FrozenInstanceError, replace
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
from strd.catalog import catalog_snapshot, _resolve, MATERIAL_ID
from strd.assessment import assess_member, REQUIRED_PROPERTIES
from strd.engineering.dpt.checks import _check_flexure
from strd.reference.ms2 import SECTION
from verification.a2_reference_calculations import reference_values
ROOT=Path(__file__).resolve().parents[1]
def request():return json.loads((ROOT/'examples/a2_member.json').read_text(encoding='utf-8'))

class A2Tests(unittest.TestCase):
    def close(self,a,b):self.assertTrue(math.isclose(a,b,rel_tol=2e-12,abs_tol=1e-9),(a,b))
    def test_source_rows_units_and_identity(self):
        # Independently transcribed rendered SYS pp15/16; not generated from resource.
        rows=[(450,200,9,14,18,1680,1490,4.40,1870,56.9,889000),(500,200,10,16,20,2180,1910,4.33,2140,85.9,1250000)]
        keys=['depth_mm','width_mm','web_mm','flange_mm','root_radius_mm','plastic_modulus_x_mm3','elastic_modulus_x_mm3','radius_y_mm','inertia_y_mm4','torsion_j_mm4','warping_cw_mm6']
        snap=catalog_snapshot();self.assertEqual(len(snap['sections']),2)
        for row,got in zip(rows,snap['sections']):
            for k,v,f in zip(keys,row,[1,1,1,1,1,1000,1000,10,10000,10000,1000000]):self.close(got[k],v*f)
        self.assertEqual(snap['material'],dict(material_id=MATERIAL_ID,fy_mpa=245,elastic_modulus_mpa=200000))
        self.assertEqual(snap['sources'][0]['sha256'],'b60c8c729cefa31075cfd9836af77dc1f644ddd89bd853b8dd09419b984a0458')
        self.assertEqual(snap['sources'][1]['sha256'],'8d55c8575a1c744e919e6e7affef934f9afb5b347331d4724db6fba238a7c59a')
    def test_geometry_and_table_rounding(self):
        for row,ref in zip(catalog_snapshot()['sections'],reference_values()):
            for k,r,t in [('plastic_modulus_x_mm3','plastic_with_fillets_mm3',5000),('torsion_j_mm4','j_derived_mm4',500),('warping_cw_mm6','cw_derived_mm6',5e8 if row['depth_mm']==450 else 5e9)]:self.assertLessEqual(abs(row[k]-ref[r]),t)
        self.close(reference_values()[0]['plastic_without_fillets_mm3'],1621489)
        self.assertEqual(SECTION.plastic_modulus_x_mm3,1621000);self.assertEqual(SECTION.torsion_j_mm4,472000)
    def test_independent_sections_methods_regions(self):
        for entry,oracle in zip(catalog_snapshot()['sections'],reference_values()):
            for method in ('ASD','LRFD'):
                for lb,region in [(1000,'LB_LE_LP'),(4000,'LP_LT_LB_LE_LR'),(10000,'LB_GT_LR')]:
                    q=request();q.update(section_id=entry['section_id'],length_mm=lb)
                    q['segments']=[dict(segment_id='S1',start_mm=0,end_mm=lb,continuous_restraint=False)]
                    q['cases']=q['cases'][:1];q['cases'][0]['method']=method;q['cases'][0]['segments']=q['cases'][0]['segments'][:1];q['cases'][0]['segments'][0].update(moment_knm=1,shear_kn=1)
                    r=assess_member(q);self.assertEqual(r['status'],'CHECKS_PASS');f=r['records'][0]['flexure'];s=r['records'][0]['shear']
                    self.assertEqual(f['intermediates']['region'],region)
                    for key in ('lp_mm','lr_mm','rts_mm'):self.close(f['intermediates'][key],oracle[key])
                    mn=oracle[f'nominal_{lb}_nmm'];self.close(f['intermediates']['nominal_moment_nmm'],mn)
                    self.close(f['capacity_knm'],(mn*.9 if method=='LRFD' else mn/1.67)/1e6)
                    self.close(s['capacity_kn'],oracle['shear_'+method.lower()+'_kn'])
    def test_boundaries_cb_continuous(self):
        for entry in catalog_snapshot()['sections']:
            q=request();q['section_id']=entry['section_id'];f=assess_member(q)['records'][0]['flexure'];sec,mat,_=_resolve(entry['section_id'],MATERIAL_ID)
            for bound,before,after in [('lp_mm','LB_LE_LP','LP_LT_LB_LE_LR'),('lr_mm','LP_LT_LB_LE_LR','LB_GT_LR')]:
                value=f['intermediates'][bound]
                for lb,region in [(math.nextafter(value,0),before),(value,before),(math.nextafter(value,math.inf),after)]:self.assertEqual(_check_flexure(dict(f['inputs'],unbraced_length_mm=lb),sec,mat)['intermediates']['region'],region)
            high=_check_flexure(dict(f['inputs'],cb=5,cb_source='VERIFIED_MOMENT_DIAGRAM'),sec,mat);self.assertEqual(high['governing_limit_state'],'YIELDING')
            q['segments'][0]['continuous_restraint']=True;self.assertEqual(assess_member(q)['records'][0]['flexure']['intermediates']['region'],'LB_LE_LP')
    def test_governing_case_identity_and_ties(self):
        q=request();q['cases'][0]['segments'][0]['moment_knm']=500;q['cases'][1]['segments'][1]['shear_kn']=1000;r=assess_member(q)
        self.assertEqual(r['status'],'CHECKS_FAIL');self.assertTrue(r['coverage']['complete'])
        self.assertEqual(r['governing']['flexure']['cases'],[dict(case_id='ASD-1',method='ASD',segment_id='S1')])
        self.assertEqual(r['governing']['shear']['cases'],[dict(case_id='LRFD-1',method='LRFD',segment_id='S2')])
        self.assertEqual(len(assess_member(request())['governing']['flexure']['cases']),2)
    def test_zero_equality_and_next_float(self):
        for kind,key,cap in [('flexure','moment_knm','capacity_knm'),('shear','shear_kn','capacity_kn')]:
            q=request();value=assess_member(q)['records'][0][kind][cap]
            for v,status in [(0,'PASS'),(value,'PASS'),(math.nextafter(value,math.inf),'FAIL')]:
                q['cases'][0]['segments'][0][key]=v;self.assertEqual(assess_member(q)['records'][0][kind]['status'],status)
    def test_every_required_field_and_unknown_fields(self):
        for path in [(),('assumptions',),('segments',0),('cases',0),('cases',0,'segments',0)]:
            q=request();item=q
            for part in path:item=item[part]
            for key in list(item)+['axial_kn']:
                bad=copy.deepcopy(q);target=bad
                for part in path:target=target[part]
                if key=='axial_kn':target[key]=0
                else:del target[key]
                self.assertEqual(assess_member(bad)['status'],'INVALID_INPUT')
        for v in [None,True,1,'x',[]]:self.assertEqual(assess_member(v)['status'],'INVALID_INPUT')
    def test_invalid_scalars(self):
        for val in [None,True,'1',-1,math.nan,math.inf,-math.inf,10**1000]:
            for path in [('length_mm',),('segments',0,'start_mm'),('segments',0,'end_mm'),('cases',0,'segments',0,'moment_knm'),('cases',0,'segments',0,'shear_kn'),('cases',0,'segments',0,'cb')]:
                q=request();target=q
                for p in path[:-1]:target=target[p]
                target[path[-1]]=val;self.assertEqual(assess_member(q)['status'],'INVALID_INPUT')
    def test_coverage_rejections(self):
        bad=[]
        for key in ('segments','cases'):
            q=request();q[key]=[];bad.append(q)
        for field,val in [('start_mm',4001),('start_mm',3999),('end_mm',7999),('segment_id','S1')]:
            q=request();q['segments'][1][field]=val;bad.append(q)
        q=request();q['cases'].append(copy.deepcopy(q['cases'][0]));bad.append(q)
        q=request();q['cases'][0]['segments'].pop();bad.append(q)
        for name in ('unknown','S1'):
            q=request();q['cases'][0]['segments'][1]['segment_id']=name;bad.append(q)
        for q in bad:self.assertEqual(assess_member(q)['status'],'INVALID_INPUT')
    def test_unsupported_and_flags(self):
        for key in ('schema_version','basis_id','catalog_revision','section_id','material_id'):
            q=request();q[key]='unknown';self.assertEqual(assess_member(q)['status'],'UNSUPPORTED')
        q=request();q['cases'][0]['method']='ULS';self.assertEqual(assess_member(q)['status'],'UNSUPPORTED')
        for flag in request()['assumptions']:
            for value,status in [(False,'UNSUPPORTED'),(1,'INVALID_INPUT')]:
                q=request();q['assumptions'][flag]=value;self.assertEqual(assess_member(q)['status'],status)
    def test_incomplete_retains_failed_check(self):
        q=request();q['cases'][0]['segments'][0]['cb']=6;q['cases'][1]['segments'][0]['shear_kn']=1e5;r=assess_member(q)
        self.assertEqual(r['status'],'INCOMPLETE');self.assertTrue(r['has_strength_failure']);self.assertFalse(r['coverage']['complete']);self.assertTrue(r['governing']['shear']['partial'])
    def test_property_requirements_per_check(self):
        q=request();sec,mat,evidence=_resolve(q['section_id'],q['material_id'])
        for key in REQUIRED_PROPERTIES['FLEXURE']:
            with patch('strd.assessment._resolve',return_value=(replace(sec,**{key:None}),mat,evidence)):
                r=assess_member(q);self.assertEqual(r['status'],'INCOMPLETE');f=r['records'][0]['flexure'];self.assertEqual(f['status'],'INVALID_INPUT');self.assertNotIn('capacity_knm',f)
                if key not in REQUIRED_PROPERTIES['SHEAR']:self.assertEqual(r['records'][0]['shear']['status'],'PASS')
    def test_noncompact_rejected(self):
        q=request();sec,mat,evidence=_resolve(q['section_id'],q['material_id'])
        with patch('strd.assessment._resolve',return_value=(replace(sec,width_mm=1000),mat,evidence)):
            r=assess_member(q);self.assertEqual(r['status'],'INCOMPLETE');self.assertEqual(r['records'][0]['flexure']['status'],'UNSUPPORTED')
    def test_catalog_integrity_and_thickness(self):
        from strd import catalog
        mock=MagicMock();mock.joinpath.return_value.read_bytes.return_value=b'{}'
        with patch.object(catalog,'files',return_value=mock):self.assertEqual(assess_member(request())['status'],'INVALID_INPUT')
        for change in ({'material_max_thickness_mm':17},{'material':dict(material_id=MATERIAL_ID,fy_mpa=235,elastic_modulus_mpa=200000)}):
            raw=catalog_snapshot();raw.update(change)
            with patch.object(catalog,'_read',return_value=(raw,'test')):self.assertEqual(assess_member(request())['status'],'INVALID_INPUT')
        raw=catalog_snapshot();raw['sections'][0]['flange_mm']=17
        with patch.object(catalog,'_read',return_value=(raw,'test')):self.assertEqual(assess_member(request())['status'],'UNSUPPORTED')
    def test_frozen_records_and_snapshot_isolation(self):
        q=request();before=copy.deepcopy(q);a=assess_member(q);b=assess_member(q);self.assertEqual(a,b);self.assertEqual(q,before);json.dumps(a,allow_nan=False)
        a['data_snapshot']['section']['depth_mm']=1;a['inputs']['cases'].clear();self.assertEqual(b,assess_member(q))
        snap=catalog_snapshot();snap['sections'].clear();self.assertEqual(len(catalog_snapshot()['sections']),2)
        sec,_,_=_resolve(q['section_id'],q['material_id'])
        with self.assertRaises(FrozenInstanceError):sec.depth_mm=1
        q['cases'][0]['segments'][0]['moment_knm']+=1;self.assertNotEqual(b['snapshot_sha256'],assess_member(q)['snapshot_sha256'])
    def test_trace_scope_and_counts(self):
        r=assess_member(request());self.assertEqual(r['coverage']['expected'],8);self.assertEqual(r['coverage']['completed'],8);self.assertEqual(r['status'],'CHECKS_PASS')
        self.assertIn('not whole-member',r['scope']);self.assertIn('bracing strength and stiffness',r['not_checked'])
        for rec in r['records']:
            for kind in ('flexure','shear'):
                ref=rec[kind]['reference'];self.assertIn('manufacturer',ref['data_status']);self.assertFalse(any(c.startswith('Example') for c in ref['clauses']));self.assertEqual(ref['section'],r['data_snapshot']['section'])
    def test_overflow_fails_closed(self):
        q=request();q['length_mm']=1e308;q['segments'][1]['end_mm']=1e308;r=assess_member(q)
        self.assertEqual(r['status'],'INCOMPLETE');self.assertEqual(r['records'][1]['flexure']['status'],'INVALID_INPUT');self.assertNotIn('capacity_knm',r['records'][1]['flexure']);json.dumps(r,allow_nan=False)
