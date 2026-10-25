"""Migration preservation and boundaries, separate from independent book proofs."""
import ast
import contextlib
import copy
import errno
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import strd
import strd_verified
from contract_cases import cases
ROOT=Path(__file__).resolve().parents[1]

# Only these existing corpus cases exercise platform ERANGE wording from float pow.
# Keep the immutable Linux snapshot; never broadly drop/normalize result messages.
_OVERFLOW_CASES = frozenset(
    f"{i:04d}-check_flexure" for i in (*range(370, 379), *range(439, 448))
)
_OVERFLOW_MESSAGES = frozenset({
    "Calculation integrity failure: (34, 'Numerical result out of range')",
    "Calculation integrity failure: (34, 'Result too large')",
})


class MigrationTests(unittest.TestCase):
    def assert_baseline_response(self, key, actual, expected):
        if key in _OVERFLOW_CASES:
            # Require an exact known diagnostic, preserving the prefix and errno.
            # The final full-dictionary comparison still checks status, omissions,
            # exclusions, versions and all other result fields. No numerical slack.
            self.assertEqual(expected['status'], 'INVALID_INPUT')
            self.assertIn(expected['message'], _OVERFLOW_MESSAGES)
            self.assertIn(actual.get('message'), _OVERFLOW_MESSAGES)
            expected = dict(expected, message=actual['message'])
        self.assertEqual(actual, expected)

    def test_exact_baseline_responses_both_apis(self):
        frozen=json.loads((ROOT/'tests_verified/fixtures/ms2_accepted_contracts.json').read_text(encoding='utf-8'))
        self.assertEqual(frozen['baseline'],'8cee711c0d16584eb811dfaaf96af4a4ed530f72')
        corpus=cases();self.assertEqual(len(corpus),len(frozen['cases']))
        for (key,api,req),expected in zip(corpus,frozen['cases']):
            self.assertEqual(key,expected['id'])
            for package in (strd,strd_verified):
                with self.subTest(case=key,package=package.__name__):
                    actual=getattr(package,api)(req)
                    self.assert_baseline_response(key,actual,expected['result']);json.dumps(actual,allow_nan=False)

    def test_canonical_faults_fail_closed(self):
        from strd.reference import ms1,ms2
        for api,mod,key in [('check_bending',ms1,'plastic_modulus_x_mm3'),('check_flexure',ms2,'torsion_j_mm4'),('check_web_shear',ms2,'web_mm')]:
            req=next(r for _,a,r in cases() if a==api)
            with patch.object(mod,'SECTION',replace(mod.SECTION,**{key:0})):
                result=getattr(strd,api)(req)
                self.assertEqual(result['status'],'INVALID_INPUT');self.assertNotIn('utilization',result)

    def test_canonical_purity_and_mutation_isolation(self):
        for api in strd.__all__:
            req=next(r for _,a,r in cases() if a==api);before=dict(req);out=io.StringIO()
            with contextlib.redirect_stdout(out),patch('builtins.input',side_effect=AssertionError('I/O')),patch('builtins.open',side_effect=AssertionError('I/O')):
                a=getattr(strd,api)(req);b=getattr(strd,api)(req)
            self.assertEqual(a,b);self.assertEqual(req,before);self.assertEqual(out.getvalue(),'')
            a['inputs']['method']='changed';self.assertEqual(b,getattr(strd,api)(req))

    def test_dependency_boundaries(self):
        import strd.engineering.dpt
        folder=Path(strd.engineering.dpt.__file__).parent
        for file in folder.glob('*.py'):
            for node in ast.walk(ast.parse(file.read_text(encoding='utf-8'))):
                if isinstance(node,ast.Import):names=[n.name for n in node.names]
                elif isinstance(node,ast.ImportFrom):names=[node.module or '']
                else:continue
                for name in names:
                    self.assertFalse(any(x in name.split('.') for x in ('reference','strd_verified','numpy','pandas','app','applications','adapters','desktop','tkinter')))
                    if isinstance(node,ast.Import) or not node.level:self.assertIn(name.split('.')[0],{'strd','math','dataclasses','typing'})

    def test_archive_origin_hashes(self):
        manifest=json.loads((ROOT/'archive/legacy/ORIGIN.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest['files']),45)
        for item in manifest['files']:
            raw=(ROOT/item['destination']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),item['sha256'])
            self.assertEqual(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),item['git_blob_sha'])

    def test_typed_contract_fields_match_schema(self):
        from strd.domain import contracts as c
        for api,cls in [('check_bending',c.BendingRequest),('check_flexure',c.FlexureRequest),('check_web_shear',c.ShearRequest),('moment_gradient_factor',c.MomentGradientRequest)]:
            req=next(r for _,a,r in cases() if a==api)
            self.assertEqual(set(cls.__required_keys__),set(req));self.assertFalse(cls.__optional_keys__)

    def test_overflow_cases_reach_native_erange(self):
        # Verify the exceptional case inventory against the actual arithmetic,
        # rather than allowing a diagnostic exception to conceal a new code path.
        from strd.engineering.dpt.flexure import _flexural_strength
        from strd.reference.ms2 import SECTION, MATERIAL
        affected = [(key, api, req) for key, api, req in cases() if key in _OVERFLOW_CASES]
        self.assertEqual(len(affected), 18)
        for key, api, req in affected:
            with self.subTest(case=key):
                self.assertEqual(api, 'check_flexure')
                self.assertGreater(req['unbraced_length_mm'], 1e307)
                with self.assertRaises(OverflowError) as raised:
                    _flexural_strength(SECTION, MATERIAL, req['unbraced_length_mm'], req['cb'])
                self.assertEqual(raised.exception.args[0], errno.ERANGE)

    def test_both_overflow_diagnostics_preserve_full_rejection(self):
        import strd.engineering.dpt.checks as checks
        native = checks._flexural_strength
        frozen = json.loads((ROOT/'tests_verified/fixtures/ms2_accepted_contracts.json').read_text(encoding='utf-8'))
        expected = {item['id']: item['result'] for item in frozen['cases']}
        for wording in ('Numerical result out of range', 'Result too large'):
            def platform_kernel(*args, **kwargs):
                try:
                    return native(*args, **kwargs)
                except OverflowError as exc:
                    if len(exc.args) == 2 and exc.args[0] == errno.ERANGE:
                        raise OverflowError(errno.ERANGE, wording) from exc
                    raise
            # Exercise actual overflow first; only substitute OS-owned diagnostic.
            with patch.object(checks, '_flexural_strength', side_effect=platform_kernel):
                for key, api, req in cases():
                    if key not in _OVERFLOW_CASES:
                        continue
                    for package in (strd, strd_verified):
                        with self.subTest(wording=wording, case=key, api=package.__name__):
                            actual = getattr(package, api)(req)
                            self.assertEqual(actual['status'], 'INVALID_INPUT')
                            self.assertNotIn('capacity_knm', actual)
                            self.assertNotIn('utilization', actual)
                            self.assert_baseline_response(key, actual, expected[key])

    def test_portability_comparison_rejects_material_and_unknown_differences(self):
        frozen = json.loads((ROOT/'tests_verified/fixtures/ms2_accepted_contracts.json').read_text(encoding='utf-8'))
        expected = {item['id']: item['result'] for item in frozen['cases']}
        key = '0370-check_flexure'
        before = copy.deepcopy(expected[key])
        mutations = [
            {'status': 'PASS'}, {'status': 'UNSUPPORTED'}, {'capacity_knm': 1.0},
            {'utilization': 0.0}, {'not_checked': []}, {'calculator_version': 'other'},
            {'message': "Calculation integrity failure: (33, 'Result too large')"},
            {'message': 'Calculation integrity failure: division by zero'},
            {'message': 'Result too large'}, {'message': 'unexpected diagnostic'},
        ]
        for changes in mutations:
            with self.subTest(changes=changes), self.assertRaises(AssertionError):
                self.assert_baseline_response(key, dict(before, **changes), before)
        missing = dict(before); del missing['scope']
        with self.assertRaises(AssertionError):
            self.assert_baseline_response(key, missing, before)
        # Even a recognized overflow spelling is not waived for other case IDs.
        alternate = dict(before, message="Calculation integrity failure: (34, 'Result too large')")
        with self.assertRaises(AssertionError):
            self.assert_baseline_response('not-an-overflow-case', alternate, before)
        valid = next(item for item in frozen['cases'] if item['result']['status'] == 'PASS')
        import math
        changed = copy.deepcopy(valid['result'])
        changed['capacity_knm'] = math.nextafter(changed['capacity_knm'], math.inf)
        with self.assertRaises(AssertionError):
            self.assert_baseline_response(valid['id'], changed, valid['result'])
        changed = copy.deepcopy(valid['result'])
        changed['intermediates']['nominal_moment_nmm'] += 1
        with self.assertRaises(AssertionError):
            self.assert_baseline_response(valid['id'], changed, valid['result'])
        self.assertEqual(before, expected[key])  # comparator never mutates oracle
