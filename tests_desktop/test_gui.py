"""Real Tk widget/event tests. Requires a desktop display; not a mock UI test."""
import tkinter as tk
import unittest
from unittest.mock import patch
from strd.desktop.ui import StrengthApp
from strd.assessment import assess_member

class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk();self.app=StrengthApp(self.root);self.errors=[]
        self.root.report_callback_exception=lambda *args:self.errors.append(args)
        self.root.update()
    def tearDown(self):
        self.root.destroy();self.assertEqual(self.errors,[])
    def sample(self):
        with patch('strd.desktop.ui.messagebox.askyesno',return_value=True):self.app.sample_button.invoke()
        self.root.update()
    def calculate(self):self.app.calculate_button.invoke();self.root.update()
    def test_launch_blank_form_and_no_pass(self):
        self.assertEqual(self.app.status.cget('text'),'Not calculated')
        self.assertFalse(self.app.result_tree.get_children());self.calculate()
        self.assertEqual(self.app.session.result['status'],'INVALID_INPUT')
    def test_widget_calculation_matches_engine_and_trace(self):
        self.sample();expected=assess_member(self.app.session.request());self.calculate()
        self.assertEqual(self.app.session.result,expected);self.assertEqual(len(self.app.result_tree.get_children()),4)
        self.assertIn('Conditional',self.app.trace.get('1.0','end'));self.assertIn('NOT CHECKED',self.app.detail.get('1.0','end'))
    def test_edit_clears_result_rows_and_trace_immediately(self):
        self.sample();self.calculate();self.app.vars['moment_knm'].set('9000');self.root.update()
        self.assertIsNone(self.app.session.result);self.assertFalse(self.app.result_tree.get_children())
        self.assertIn('No current',self.app.trace.get('1.0','end'));self.assertIn('recalculate',self.app.status.cget('text'))
        self.calculate();self.assertEqual(self.app.session.result['status'],'CHECKS_FAIL')
    def test_case_and_segment_selection_updates_correct_action(self):
        self.sample();self.app.cases_tree.selection_set('1');self.app.segments_tree.selection_set('1');self.root.update()
        self.assertEqual((self.app.ci,self.app.si),(1,1));self.assertEqual(float(self.app.vars['moment_knm'].get()),310)
        self.app.vars['moment_knm'].set('99');self.root.update()
        d=self.app.session.draft;self.assertEqual(d['cases'][1]['segments'][1]['moment_knm'],'99')
        self.assertEqual(d['cases'][0]['segments'][0]['moment_knm'],200)
    def test_selection_alone_preserves_current_results(self):
        self.sample();self.calculate();self.app.cases_tree.selection_set('1');self.root.update()
        self.assertEqual(self.app.session.state,'CURRENT');self.assertEqual(len(self.app.result_tree.get_children()),4)
    def test_incomplete_never_green_success(self):
        self.sample();self.app.vars['cb'].set('6');self.calculate()
        self.assertEqual(self.app.session.result['status'],'INCOMPLETE');self.assertIn('Incomplete',self.app.status.cget('text'))
        self.assertIn('UNSUPPORTED',str(self.app.result_tree.item('0','values')))
    def test_restraint_edit_unsupported(self):
        self.sample();self.calculate();self.app.vars['segment_ends_braced'].set(False);self.calculate()
        self.assertEqual(self.app.session.result['status'],'UNSUPPORTED');self.assertFalse(self.app.result_tree.get_children())
    def test_add_remove_rebinds_editors(self):
        self.sample();self.app.mutate('add_case');self.app.mutate('add_segment');self.root.update()
        self.assertEqual((self.app.ci,self.app.si),(2,2));self.app.vars['end_mm'].set('12000');self.root.update()
        self.assertEqual(self.app.session.draft['segments'][2]['end_mm'],'12000')
        self.app.mutate('remove_case');self.app.mutate('remove_segment');self.root.update()
        self.assertEqual(len(self.app.session.draft['cases']),2);self.assertEqual(len(self.app.session.draft['segments']),2)
    def test_reset_confirmation_and_fresh_state(self):
        self.sample();self.calculate()
        with patch('strd.desktop.ui.messagebox.askyesno',return_value=False):self.app.reset_button.invoke()
        self.assertIsNotNone(self.app.session.result)
        with patch('strd.desktop.ui.messagebox.askyesno',return_value=True):self.app.reset_button.invoke()
        self.root.update();self.assertIsNone(self.app.session.result);self.assertEqual(self.app.session.state,'EMPTY')
    def test_error_does_not_retain_success(self):
        self.sample();self.calculate()
        with patch('strd.desktop.model.assess_member',side_effect=RuntimeError('injected')):self.calculate()
        self.assertIsNone(self.app.session.result);self.assertFalse(self.app.result_tree.get_children())
        self.assertIn('Calculation error',self.app.status.cget('text'))
        self.calculate();self.assertEqual(self.app.session.result['status'],'CHECKS_PASS')
    def test_required_controls_fit_pilot_window(self):
        for geometry in ('1180x820','960x700'):
            self.root.geometry(geometry);self.root.update()
            self.app.tabs.select(self.app.actions_tab);self.root.update()
            self.app.actions_canvas.yview_moveto(1);self.root.update()
            for widget in (self.app.calculate_button,self.app.status,self.app.scope_label,self.app.widgets['cb_reference']):
                self.assertLessEqual(widget.winfo_rooty()+widget.winfo_height(),self.root.winfo_rooty()+self.root.winfo_height())
                self.assertLessEqual(widget.winfo_rootx()+widget.winfo_width(),self.root.winfo_rootx()+self.root.winfo_width())
    def test_close_confirmation_cancel(self):
        with patch('strd.desktop.ui.messagebox.askyesno',return_value=False):self.app.close()
        self.assertTrue(self.root.winfo_exists())
