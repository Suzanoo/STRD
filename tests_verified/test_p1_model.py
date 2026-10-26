"""P1 draft/session tests; engine correctness remains in existing independent tests."""
import copy
import json
import unittest
from unittest.mock import patch
from strd.desktop.model import MemberSession, DraftError, FLAGS
from strd.assessment import assess_member

class SessionTests(unittest.TestCase):
    def ready(self):
        s=MemberSession();s.load_example();return s
    def test_initial_empty_and_explicit_assumptions(self):
        s=MemberSession();self.assertEqual(s.state,'EMPTY');self.assertIsNone(s.result)
        self.assertFalse(any(s.draft['assumptions'].values()));self.assertEqual(s.calculate()['status'],'INVALID_INPUT')
    def test_example_exact_engine_result(self):
        s=self.ready();req=s.request();self.assertEqual(s.calculate(),assess_member(req));self.assertTrue(s.demonstration)
        self.assertEqual(s.result['status'],'CHECKS_PASS');self.assertEqual(s.state,'CURRENT')
    def test_every_edit_invalidates_immediately(self):
        paths=[('member_id',),('section_id',),('length_mm',)]
        paths += [('assumptions',k) for k in FLAGS]
        paths += [('segments',0,k) for k in ('start_mm','end_mm','continuous_restraint')]
        paths += [('cases',0,k) for k in ('case_id','method','action_source')]
        paths += [('cases',0,'segments',0,k) for k in ('moment_knm','shear_kn','cb','cb_source','cb_reference')]
        for path in paths:
            with self.subTest(path=path):
                s=self.ready();s.calculate();target=s.draft
                for k in path:target=target[k]
                s.set_value(path,not target if type(target) is bool else 'changed')
                self.assertEqual(s.state,'STALE');self.assertIsNone(s.result)
    def test_selection_does_not_mutate_inputs(self):
        s=self.ready();s.calculate();before=copy.deepcopy(s.draft);s.request()
        self.assertEqual(s.draft,before);self.assertEqual(s.state,'CURRENT')
    def test_invalid_numeric_forms(self):
        for value in ('','NaN','Infinity','1,000','12 mm',True,None):
            s=self.ready();s.set_value(('cases',0,'segments',0,'moment_knm'),value)
            r=s.calculate();self.assertEqual(r['status'],'INVALID_INPUT');self.assertNotIn('records',r)
    def test_negative_is_rejected_by_engine(self):
        s=self.ready();s.set_value(('cases',0,'segments',0,'moment_knm'),'-1')
        self.assertEqual(s.calculate()['status'],'INVALID_INPUT')
    def test_failure_and_recalculation(self):
        s=self.ready();s.set_value(('cases',0,'segments',0,'moment_knm'),'9000');self.assertEqual(s.calculate()['status'],'CHECKS_FAIL')
        s.set_value(('cases',0,'segments',0,'moment_knm'),'200');self.assertIsNone(s.result);self.assertEqual(s.calculate()['status'],'CHECKS_PASS')
    def test_missing_assumption_unsupported(self):
        s=self.ready();s.set_value(('assumptions','segment_ends_braced'),False)
        self.assertEqual(s.calculate()['status'],'UNSUPPORTED')
    def test_incomplete_and_failure_visible(self):
        s=self.ready();s.set_value(('cases',0,'segments',0,'cb'),'6');s.set_value(('cases',1,'segments',1,'shear_kn'),'10000')
        r=s.calculate();self.assertEqual(r['status'],'INCOMPLETE');self.assertTrue(r['has_strength_failure'])
    def test_add_remove_case_segment_synchronization(self):
        s=self.ready();s.calculate();s.add_case();s.add_segment();self.assertIsNone(s.result)
        ids=[x['segment_id'] for x in s.draft['segments']]
        self.assertEqual(len(s.draft['cases']),3)
        for c in s.draft['cases']:self.assertEqual([a['segment_id'] for a in c['segments']],ids)
        s.remove_segment(1);s.remove_case(0)
        ids=[x['segment_id'] for x in s.draft['segments']]
        for c in s.draft['cases']:self.assertEqual([a['segment_id'] for a in c['segments']],ids)
    def test_no_deletion_of_last_items(self):
        s=MemberSession()
        with self.assertRaises(DraftError):s.remove_case(0)
        with self.assertRaises(DraftError):s.remove_segment(0)
    def test_load_example_resets_results_and_new_identity_counters(self):
        s=self.ready();s.calculate();s.add_segment();s.load_example();self.assertIsNone(s.result)
        s.add_segment();self.assertEqual(s.draft['segments'][-1]['segment_id'],'S3')
    def test_result_copy_and_request_isolation(self):
        s=self.ready();r=s.calculate();r['records'].clear();self.assertEqual(len(s.result['records']),4)
        q=s.request();q['cases'].clear();self.assertEqual(len(s.draft['cases']),2)
    def test_error_clears_previous_result(self):
        s=self.ready();s.calculate()
        with patch('strd.desktop.model.assess_member',side_effect=RuntimeError('injected')):
            with self.assertRaises(RuntimeError):s.calculate()
        self.assertIsNone(s.result)
    def test_no_case_mixing_in_editor_model(self):
        s=self.ready();other=copy.deepcopy(s.draft['cases'][1]);s.set_value(('cases',0,'segments',0,'moment_knm'),'999')
        self.assertEqual(s.draft['cases'][1],other)
