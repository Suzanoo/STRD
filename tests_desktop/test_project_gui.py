"""P2 real widgets with deterministic native-dialog responses and real disk writes."""
import tempfile
from pathlib import Path
import tkinter as tk
import unittest
from unittest.mock import patch
from strd.desktop.project_ui import ProjectApp
from strd.workspace import ProjectWorkspace
from strd.workspace import storage

P='strd.desktop.project_ui.'
class ProjectGuiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'ไทย project.strd'
        self.root=tk.Tk();self.app=ProjectApp(self.root);self.errors=[]
        self.root.report_callback_exception=lambda *a:self.errors.append(a)
        self.root.update()
    def tearDown(self):
        try:self.root.destroy()
        except tk.TclError:pass
        self.assertEqual(self.errors,[])
    def sample(self):
        with patch('strd.desktop.ui.messagebox.askyesno',return_value=True):self.app.load_example()
        self.root.update()
    def save(self):
        with patch(P+'filedialog.asksaveasfilename',return_value=str(self.path)):self.assertTrue(self.app.save_project())
        self.root.update()
    def test_project_create_save_open_recalculate(self):
        self.sample();self.app.calculate();self.save()
        self.assertEqual(self.app.file_status.cget('text'),'Saved')
        with patch(P+'filedialog.askopenfilename',return_value=str(self.path)):self.app.open_project()
        self.root.update();self.assertIsNone(self.app.session.result);self.assertFalse(self.app.result_tree.get_children())
        self.app.calculate();self.assertEqual(self.app.session.result['status'],'CHECKS_PASS')
    def test_switch_members_never_shows_other_member_result(self):
        self.sample();self.app.calculate();self.app.add_member();self.root.update()
        self.assertFalse(self.app.result_tree.get_children());self.app.vars['member_id'].set('Second')
        self.app.member_picker.current(0);self.app.select_member();self.root.update()
        self.assertEqual(self.app.session.result['status'],'CHECKS_PASS');self.assertEqual(len(self.app.result_tree.get_children()),4)
        self.app.member_picker.current(1);self.app.select_member();self.root.update()
        self.assertFalse(self.app.result_tree.get_children());self.assertEqual(self.app.vars['member_id'].get(),'Second')
    def test_save_failure_blocks_new_and_keeps_inputs(self):
        self.sample();before=self.app.session.draft.copy()
        with patch(P+'messagebox.askyesnocancel',return_value=True),patch(P+'filedialog.asksaveasfilename',return_value=str(self.path)),patch('strd.workspace.storage.stage',side_effect=OSError('disk full')),patch(P+'messagebox.showerror') as error:
            self.app.new_project();error.assert_called_once()
        self.assertEqual(self.app.session.draft,before);self.assertTrue(self.app.workspace.dirty)
    def test_cancel_save_dialog_blocks_close(self):
        with patch(P+'messagebox.askyesnocancel',return_value=True),patch(P+'filedialog.asksaveasfilename',return_value=''):self.app.close()
        self.assertTrue(self.root.winfo_exists())
    def test_new_cancel_then_discard(self):
        self.sample();before=self.app.workspace
        with patch(P+'messagebox.askyesnocancel',return_value=None):self.app.new_project()
        self.assertIs(self.app.workspace,before)
        with patch(P+'messagebox.askyesnocancel',return_value=False):self.app.new_project()
        self.assertIsNot(self.app.workspace,before);self.assertEqual(self.app.vars['length_mm'].get(),'')
    def test_open_corrupt_does_not_prompt_discard_or_destroy_result(self):
        self.sample();self.app.calculate();self.path.write_bytes(b'bad');before=self.app.workspace
        with patch(P+'filedialog.askopenfilename',return_value=str(self.path)),patch(P+'messagebox.askyesnocancel') as prompt,patch(P+'messagebox.showerror') as error:self.app.open_project()
        prompt.assert_not_called();error.assert_called_once();self.assertIs(self.app.workspace,before)
        self.assertEqual(self.app.session.result['status'],'CHECKS_PASS')
    def test_save_as_existing_destination_rejected_visibly(self):
        self.path.write_bytes(b'other')
        with patch(P+'filedialog.asksaveasfilename',return_value=str(self.path)),patch(P+'messagebox.showerror') as error:self.assertFalse(self.app.save_project(True))
        error.assert_called_once();self.assertEqual(self.path.read_bytes(),b'other')
    def test_open_same_file_after_save_prompt_reads_newest(self):
        self.sample();self.save();self.app.vars['member_id'].set('Newest')
        with patch(P+'filedialog.askopenfilename',return_value=str(self.path)),patch(P+'messagebox.askyesnocancel',return_value=True):self.app.open_project()
        self.assertEqual(self.app.vars['member_id'].get(),'Newest');self.assertFalse(self.app.workspace.dirty)
    def test_recovery_is_unsaved_and_damaged_original_retained(self):
        self.sample();self.save();self.app.vars['member_id'].set('second');self.save();self.path.write_bytes(b'bad')
        with patch(P+'filedialog.askopenfilename',return_value=str(self.path)+'.bak'),patch(P+'messagebox.showinfo'):self.app.recover_project()
        self.assertIsNone(self.app.workspace.path);self.assertTrue(self.app.workspace.dirty);self.assertIsNone(self.app.session.result)
        self.assertEqual(self.path.read_bytes(),b'bad')
    def test_remove_cancel_and_duplicate_are_isolated(self):
        self.sample();self.app.add_member(True);self.app.vars['length_mm'].set('1')
        self.assertEqual(self.app.workspace.sessions[0].draft['length_mm'],8000)
        with patch(P+'messagebox.askyesno',return_value=False):self.app.remove_member()
        self.assertEqual(len(self.app.workspace.sessions),2)
        with patch(P+'messagebox.askyesno',return_value=True):self.app.remove_member()
        self.assertEqual(len(self.app.workspace.sessions),1)
    def test_rename_title_and_clear_selected_member_dirty(self):
        self.sample();self.save();self.app.title_var.set('ชื่อโครงการ');self.assertTrue(self.app.workspace.dirty)
        with patch(P+'messagebox.askyesno',return_value=True):self.app.reset()
        self.assertEqual(self.app.session.draft['length_mm'],'');self.assertIs(self.app.workspace.session,self.app.session)
    def test_stale_instance_conflict_keeps_ui_and_save_as_available(self):
        self.sample();self.save();other=ProjectWorkspace();other.open(self.path);other.doc['title']='other';other.save()
        self.app.vars['member_id'].set('my work')
        with patch(P+'messagebox.showerror') as error:self.assertFalse(self.app.save_project())
        error.assert_called_once();self.assertEqual(self.app.vars['member_id'].get(),'my work');self.assertTrue(self.app.workspace.dirty)
        with patch(P+'filedialog.asksaveasfilename',return_value=str(self.path.parent/'copy.strd')):self.assertTrue(self.app.save_project(True))
    def test_small_window_controls_and_scroll_accessible(self):
        self.root.geometry('960x760');self.root.update();self.app.tabs.select(self.app.actions_tab);self.root.update();self.app.actions_canvas.yview_moveto(1);self.root.update()
        for w in [*self.app.project_buttons.values(),self.app.widgets['cb_reference'],self.app.calculate_button]:
            self.assertLessEqual(w.winfo_rootx()+w.winfo_width(),self.root.winfo_rootx()+self.root.winfo_width())
            self.assertLessEqual(w.winfo_rooty()+w.winfo_height(),self.root.winfo_rooty()+self.root.winfo_height())
