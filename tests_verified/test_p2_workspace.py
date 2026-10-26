"""P2 disk integrity, drift rejection and real process failure/concurrency evidence."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from strd.workspace import ProjectWorkspace
from strd.workspace import storage
from strd.workspace.format import (ProjectError,CompatibilityError,canonical,digest,encode,decode,MAX_BYTES)
from strd.assessment import assess_member


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'โครงการ beam.strd';self.w=ProjectWorkspace()
    def sample(self):self.w.session.load_example()
    def saved(self):self.sample();self.w.save(self.path)
    def assert_rejected(self,doc):
        raw=canonical(dict(payload=doc,sha256=digest(canonical(doc))))
        with self.assertRaises(ProjectError):decode(raw)
    def test_incomplete_draft_roundtrip(self):
        self.w.session.set_value(('length_mm',),'not ready');self.w.doc['title']='โครงการ ทดสอบ'
        self.w.save(self.path);v=ProjectWorkspace();v.open(self.path)
        self.assertEqual(v.document(),self.w.document());self.assertFalse(v.dirty)
        self.assertEqual(v.session.calculate()['status'],'INVALID_INPUT')
    def test_multiple_members_roundtrip_engine_agreement_and_no_saved_results(self):
        self.sample();expected=assess_member(self.w.session.request());self.w.session.calculate();self.w.add(True)
        self.w.session.set_value(('cases',0,'segments',0,'moment_knm'),'9000');self.w.session.calculate()
        self.w.save(self.path);raw=self.path.read_bytes();self.assertNotIn(b'CHECKS_PASS',raw)
        v=ProjectWorkspace();v.open(self.path);self.assertEqual(len(v.sessions),2)
        self.assertTrue(all(s.result is None for s in v.sessions));self.assertEqual(v.session.calculate(),expected)
        v.index=1;self.assertEqual(v.session.calculate()['status'],'CHECKS_FAIL')
    def test_calculation_not_dirty_and_edits_are_dirty(self):
        self.saved();self.w.session.calculate();self.assertFalse(self.w.dirty)
        self.w.session.set_value(('member_id',),'new');self.assertTrue(self.w.dirty);self.assertIsNone(self.w.session.result)
    def test_member_duplicate_is_independent_and_keys_unique(self):
        self.sample();self.w.add(True);self.w.session.set_value(('length_mm',),'99')
        self.assertEqual(self.w.sessions[0].draft['length_mm'],8000)
        self.assertEqual(len({m['key'] for m in self.w.doc['members']}),2)
        self.w.remove();self.assertEqual(len(self.w.sessions),1)
        with self.assertRaises(ProjectError):self.w.remove()
    def test_restore_then_generated_case_ids_do_not_collide(self):
        self.sample();self.w.session.draft['cases'][0]['case_id']='C2';self.w.save(self.path)
        self.w.open(self.path);self.w.session.add_case();self.w.session.add_case()
        ids=[x['case_id'] for x in self.w.session.draft['cases']];self.assertEqual(len(ids),len(set(ids)))
        self.w.session.add_segment();self.assertEqual(self.w.session.draft['segments'][-1]['segment_id'],'S3')
    def test_corrupt_open_retains_current_workspace(self):
        self.sample();before=self.w.document();self.path.write_bytes(b'{broken')
        with self.assertRaises(ProjectError):self.w.open(self.path)
        self.assertEqual(self.w.document(),before);self.assertIsNone(self.w.path)
    def test_checksum_duplicate_keys_nonfinite_and_truncated_rejected(self):
        raw=encode(self.w.document())
        for bad in [raw[:-10],raw.replace(b'Untitled',b'Corrupt'),b'{"payload":1,"payload":2}',b'{"payload":NaN}',b'\xff']:
            with self.subTest(bad=bad[:40]),self.assertRaises(ProjectError):decode(bad)
    def test_versions_catalog_and_unknown_fields_fail_closed(self):
        doc=self.w.document()
        for field,value in [('format','STRD-PROJECT-2'),('format','STRD-PROJECT-0'),('result_policy','TRUST_RESULTS'),('engineering',{}),('catalog',{})]:
            d=copy.deepcopy(doc);d[field]=value;self.assert_rejected(d)
        d=copy.deepcopy(doc);d['catalog']['sections'][0]['depth_mm']+=1;self.assert_rejected(d)
        d=copy.deepcopy(doc);d['members'][0]['result']={'status':'CHECKS_PASS'};self.assert_rejected(d)
        d=copy.deepcopy(doc);d['members'][0]['draft']['assumptions']['major_axis_only']=1;self.assert_rejected(d)
    def test_catalog_bool_number_equality_cannot_bypass_snapshot(self):
        d=self.w.document();d['catalog']['sections'][0]['depth_mm']=True;self.assert_rejected(d)
    def test_malformed_shapes_are_rejected_before_ui(self):
        d=self.w.document()
        for mutate in [lambda x:x.update(members=[]),lambda x:x['members'].append(copy.deepcopy(x['members'][0])),lambda x:x['members'][0]['draft'].update(segments=[]),lambda x:x['members'][0]['draft']['cases'][0].update(segments=[]),lambda x:x['members'][0]['draft'].update(length_mm=True),lambda x:x['members'][0]['draft'].update(section_id='legacy')]:
            other=copy.deepcopy(d);mutate(other);self.assert_rejected(other)
    def test_size_limits(self):
        with self.assertRaises(ProjectError):decode(b' '*(MAX_BYTES+1))
        d=self.w.document();d['title']='x'*4097
        with self.assertRaises(ProjectError):encode(d)
    def test_save_as_never_overwrites_existing(self):
        self.path.write_bytes(b'unrelated');before=self.w.document()
        with self.assertRaises(storage.ConflictError):self.w.save(self.path)
        self.assertEqual(self.path.read_bytes(),b'unrelated');self.assertEqual(self.w.document(),before);self.assertIsNone(self.w.path)
    def test_save_as_changes_binding_without_touching_original(self):
        self.saved();old=self.path.read_bytes();self.w.doc['title']='copy';dest=self.path.parent/'copy.strd'
        self.w.save(dest);self.assertEqual(self.path.read_bytes(),old);self.assertEqual(self.w.path,dest.resolve(strict=True));self.assertTrue(self.w.path.samefile(dest));self.assertFalse(self.w.dirty)
    def test_stale_writer_and_deleted_target_rejected(self):
        self.saved();other=ProjectWorkspace();other.open(self.path);self.w.doc['title']='first';self.w.save();raw=self.path.read_bytes()
        other.doc['title']='second'
        with self.assertRaises(storage.ConflictError):other.save()
        self.assertEqual(self.path.read_bytes(),raw);self.assertTrue(other.dirty)
        self.path.unlink()
        with self.assertRaises(storage.ConflictError):self.w.save()
    def test_backup_and_explicit_recovery_do_not_modify_original(self):
        self.saved();previous=self.path.read_bytes();self.w.doc['title']='new';self.w.save()
        backup=Path(str(self.path)+'.bak');self.assertEqual(backup.read_bytes(),previous)
        self.path.write_bytes(b'damaged');other=ProjectWorkspace();other.recover(backup)
        self.assertEqual(other.doc['title'],'Untitled project');self.assertIsNone(other.path);self.assertTrue(other.dirty)
        self.assertIsNone(other.session.result);self.assertEqual(self.path.read_bytes(),b'damaged')
        with self.assertRaises(storage.ConflictError):other.save(self.path)
        other.save(self.path.parent/'recovered.strd')
    def test_corrupt_backup_rejected_without_replacing_memory(self):
        self.saved();Path(str(self.path)+'.bak').write_bytes(b'bad');before=self.w.document()
        with self.assertRaises(ProjectError):self.w.recover(self.path)
        self.assertEqual(self.w.document(),before)
    def test_write_fsync_backup_and_replace_faults_preserve_original(self):
        for target in ['stage','os.fsync','os.replace']:
            with self.subTest(target=target):
                self.w=ProjectWorkspace();self.path.unlink(missing_ok=True);self.saved();raw=self.path.read_bytes();token=self.w.token
                self.w.doc['title']='edit'
                with patch('strd.workspace.storage.'+target,side_effect=OSError('injected disk failure')):
                    with self.assertRaises(ProjectError):self.w.save()
                self.assertEqual(self.path.read_bytes(),raw);self.assertEqual(self.w.token,token);self.assertTrue(self.w.dirty)
                self.assertFalse(list(self.path.parent.glob('*.pending-*')))
    def test_primary_replace_failure_preserves_previous_revision(self):
        self.saved();raw=self.path.read_bytes();real=os.replace
        primary=self.path.resolve(strict=True);token=self.w.token;destinations=[]
        def fail_primary(a,b):
            destinations.append(Path(b))
            if Path(b)==primary:raise OSError('primary blocked')
            return real(a,b)
        self.w.doc['title']='edit'
        with patch('strd.workspace.storage.os.replace',side_effect=fail_primary),self.assertRaisesRegex(ProjectError,'primary blocked'):self.w.save()
        self.assertEqual(destinations,[Path(str(primary)+'.bak'),primary])
        self.assertEqual(self.path.read_bytes(),raw);self.assertEqual(Path(str(self.path)+'.bak').read_bytes(),raw)
        self.assertEqual(self.w.token,token);self.assertEqual(self.w.path,primary);self.assertTrue(self.w.dirty)
    def test_post_commit_sync_failure_is_not_reported_saved(self):
        self.saved();self.w.doc['title']='edit';real=storage.sync_directory;calls=[]
        def fail_second(p):
            calls.append(p)
            if len(calls)==2:raise OSError('sync failure')
            real(p)
        with patch('strd.workspace.storage.sync_directory',side_effect=fail_second),self.assertRaisesRegex(ProjectError,'may have been committed'):self.w.save()
        self.assertTrue(self.w.dirty);self.assertEqual(decode(self.path.read_bytes())['title'],'edit')
        with self.assertRaises(storage.ConflictError):self.w.save()
    def test_symlink_hardlink_directory_and_lock_rejected(self):
        other=self.path.parent/'other';other.write_bytes(b'untouched')
        self.path.symlink_to(other)
        with self.assertRaises((ProjectError,OSError)):self.w.save(self.path)
        self.assertEqual(other.read_bytes(),b'untouched');self.path.unlink();os.link(other,self.path)
        with self.assertRaises((ProjectError,OSError)):self.w.save(self.path)
        self.path.unlink();self.path.mkdir()
        with self.assertRaises((ProjectError,OSError)):self.w.save(self.path)
        self.path.rmdir();lock=Path(str(self.path)+'.lock');lock.unlink(missing_ok=True);lock.symlink_to(other)
        with self.assertRaises((ProjectError,OSError)):self.w.save(self.path)
        self.assertEqual(other.read_bytes(),b'untouched')
    def test_held_lock_rejected_then_released(self):
        self.saved()
        with storage.locked(self.path):
            with self.assertRaises(storage.ConflictError):self.w.save()
        self.w.save()
    def test_real_process_simultaneous_writers_one_success(self):
        self.saved()
        code='''import sys
from pathlib import Path
from strd.workspace import ProjectWorkspace
from strd.workspace.format import ProjectError
w=ProjectWorkspace();w.open(sys.argv[1]);print('READY',flush=True);sys.stdin.readline();w.doc['title']=sys.argv[2]
try:w.save();print('SAVED',flush=True)
except ProjectError:print('REJECTED',flush=True)
'''
        env=dict(os.environ,PYTHONPATH=str(Path(__import__('strd').__file__).resolve().parent.parent))
        alias=self.path.parent/'process-alias';alias.symlink_to(self.path.parent,target_is_directory=True)
        paths=[self.path.resolve(strict=True),alias/self.path.name]
        procs=[subprocess.Popen([sys.executable,'-c',code,str(paths[i]),str(i)],env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for i in range(2)]
        try:
            for p in procs:self.assertEqual(p.stdout.readline().strip(),'READY')
            for p in procs:p.stdin.write('go\n');p.stdin.flush()
            outcomes=[p.communicate(timeout=10)[0].strip() for p in procs]
            self.assertEqual(sorted(outcomes),['REJECTED','SAVED']);decode(self.path.read_bytes())
        finally:
            for p in procs:
                if p.poll() is None:p.kill();p.wait()
    def test_process_exit_before_and_after_commit_preserves_recoverability(self):
        self.saved();old=self.path.read_bytes()
        code='''import sys,os
from pathlib import Path
from strd.workspace import ProjectWorkspace,storage
w=ProjectWorkspace();w.open(sys.argv[1]);w.doc['title']='crash candidate'
real=os.replace
def crash(a,b):
 if Path(b)==w.path:
  if sys.argv[2]=='after':real(a,b)
  os._exit(77)
 return real(a,b)
storage.os.replace=crash
w.save()
'''
        env=dict(os.environ,PYTHONPATH=str(Path(__import__('strd').__file__).resolve().parent.parent))
        for phase in ['before','after']:
            p=subprocess.run([sys.executable,'-c',code,str(self.path),phase],env=env,timeout=10);self.assertEqual(p.returncode,77)
            self.assertEqual(Path(str(self.path)+'.bak').read_bytes(),old);decode(self.path.read_bytes())
            if phase=='before':self.assertEqual(self.path.read_bytes(),old)
        # The OS releases advisory locks even after abrupt process death.
        other=ProjectWorkspace();other.open(self.path);other.save()

    def test_unchanged_save_does_not_rotate_previous_revision(self):
        self.saved();old=self.path.read_bytes();self.w.doc['title']='new';self.w.save()
        self.w.save();self.assertEqual(Path(str(self.path)+'.bak').read_bytes(),old)

    def test_delivered_sample_is_valid_and_bounded(self):
        root=Path(__file__).resolve().parents[1]
        w=ProjectWorkspace();w.open(root/'examples/p2_two_members.strd')
        self.assertEqual(len(w.sessions),2)
        self.assertEqual(w.sessions[0].calculate()['status'],'CHECKS_PASS')
        self.assertEqual(w.sessions[1].calculate()['status'],'CHECKS_FAIL')
        self.assertTrue(all(s.demonstration for s in w.sessions))

    def directory_alias(self,name):
        alias=self.path.parent/name
        alias.symlink_to(self.path.parent,target_is_directory=True)
        return alias/self.path.name

    def test_corrected_safety_assertions_through_directory_alias(self):
        # Explicitly exercise both former failures even when /tmp is not aliased.
        original=self.path
        alias=self.directory_alias('assertion-alias').parent
        for i,method in enumerate((self.test_primary_replace_failure_preserves_previous_revision,
                                  self.test_save_as_changes_binding_without_touching_original)):
            with self.subTest(method=method.__name__):
                self.path=alias/('case-'+str(i)+'.strd');self.w=ProjectWorkspace()
                self.assertNotEqual(self.path,self.path.parent.resolve()/self.path.name)
                method()
        self.path=original

    def test_alias_save_stale_writer_and_backup_recovery_share_identity(self):
        alias=self.directory_alias('recovery-alias');self.sample();self.w.save(alias)
        canonical_path=self.path.resolve(strict=True)
        self.assertEqual(self.w.path,canonical_path)
        other=ProjectWorkspace();other.open(self.path)
        before=self.path.read_bytes();self.w.doc['title']='saved through alias';self.w.save(alias)
        self.assertEqual(Path(str(alias)+'.bak').read_bytes(),before)
        other.doc['title']='stale edit'
        with self.assertRaises(storage.ConflictError):other.save(alias)
        self.assertTrue(other.dirty)
        current=self.path.read_bytes();recovery=ProjectWorkspace();recovery.recover(str(alias)+'.bak')
        self.assertEqual(recovery.doc['title'],'Untitled project');self.assertIsNone(recovery.path)
        self.assertTrue(recovery.dirty);self.assertEqual(self.path.read_bytes(),current)

    def test_directory_alias_cannot_bypass_held_save_lock(self):
        alias=self.directory_alias('lock-alias');self.saved();before=self.path.read_bytes()
        self.w.doc['title']='blocked edit'
        with storage.locked(self.path.resolve(strict=True)):
            with self.assertRaises(storage.ConflictError):self.w.save(alias)
        self.assertEqual(self.path.read_bytes(),before);self.assertTrue(self.w.dirty)
        self.w.save(alias);self.assertFalse(self.w.dirty)
