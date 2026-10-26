"""P2 project shell reuses the accepted member editor and result presentation."""
from tkinter import ttk, messagebox, filedialog
from .ui import StrengthApp
from .model import MemberSession
from strd.workspace import ProjectWorkspace
from strd.workspace.format import ProjectError, MAX_ITEMS


class ProjectApp(StrengthApp):
    def __init__(self,root):
        self.workspace=ProjectWorkspace()
        self.project_ready=False
        super().__init__(root,self.workspace.session)
        root.geometry('1180x940');root.minsize(960,760)
        self.scope_label.configure(text='Conditional strength checks only. Save stores inputs; reopening requires recalculation. Local files only.')
        bar=ttk.Frame(self.tabs.master);bar.pack(fill='x',pady=(0,8),before=self.tabs)
        self.project_buttons={}
        for label,fn in [('New',self.new_project),('Open',self.open_project),('Save',self.save_project),('Save As',lambda:self.save_project(True)),('Recover backup',self.recover_project)]:
            b=ttk.Button(bar,text=label,command=fn);b.pack(side='left',padx=(0,5));self.project_buttons[label]=b
        self.file_status=ttk.Label(bar);self.file_status.pack(side='left',padx=6)
        row=ttk.Frame(self.tabs.master);row.pack(fill='x',pady=(0,10),before=self.tabs)
        ttk.Label(row,text='Project').pack(side='left')
        import tkinter as tk
        self.title_var=tk.StringVar(value=self.workspace.doc['title'])
        self.title_entry=ttk.Entry(row,textvariable=self.title_var,width=22);self.title_entry.pack(side='left',padx=6)
        self.title_var.trace_add('write',self.title_changed)
        self.member_picker=ttk.Combobox(row,state='readonly',width=30);self.member_picker.pack(side='left',padx=6)
        self.member_picker.bind('<<ComboboxSelected>>',self.select_member)
        for label,fn in [('+ Member',self.add_member),('Duplicate',lambda:self.add_member(True)),('Remove',self.remove_member)]:
            b=ttk.Button(row,text=label,command=fn);b.pack(side='left',padx=3);self.project_buttons[label]=b
        self.project_ready=True;self.refresh_state()
        root.bind('<Command-s>',lambda _:self.save_project())
        root.bind('<Control-s>',lambda _:self.save_project())

    def title_changed(self,*_):
        if self.loading:return
        self.workspace.doc['title']=self.title_var.get();self.refresh_project()

    def refresh_project(self):
        if not self.project_ready:return
        w=self.workspace
        self.member_picker.configure(values=[f"{i+1}: {s.draft['member_id'] or '(unnamed)'}" for i,s in enumerate(w.sessions)])
        self.member_picker.current(w.index)
        dirty='Unsaved changes' if w.dirty else 'Saved'
        self.file_status.configure(text=dirty)
        self.root.title('STRD - '+w.doc['title']+(' *' if w.dirty else '')+' | '+(str(w.path) if w.path else 'New project'))

    def refresh_state(self):
        super().refresh_state()
        if self.project_ready:
            if not self.session.demonstration:self.banner.configure(text='Project member | Confirm applicability before calculating. Reopening requires recalculation.')
            self.refresh_project()

    def bind_member(self):
        self.session=self.workspace.session;self.ci=self.si=0
        self.load_forms();self.refresh_state()
        if self.session.result is not None:self.show_result(self.session.result)
        else:self.tabs.select(self.member_tab)

    def select_member(self,_=None):
        index=self.member_picker.current()
        if index>=0 and index!=self.workspace.index:self.workspace.index=index;self.bind_member()

    def add_member(self,duplicate=False):
        try:self.workspace.add(duplicate);self.bind_member()
        except ProjectError as exc:self.error(exc)

    def remove_member(self):
        if not messagebox.askyesno('Remove member?', 'Remove the selected member and its inputs from this project?',parent=self.root):return
        try:self.workspace.remove();self.bind_member()
        except ProjectError as exc:self.error(exc)

    def mutate(self,operation):
        key='segments' if operation=='add_segment' else 'cases' if operation=='add_case' else None
        if key and len(self.session.draft[key])>=MAX_ITEMS:
            self.error('P2 supports at most 100 '+key+' per member.');return
        super().mutate(operation)

    def error(self,exc):
        messagebox.showerror('Project operation not completed',str(exc),parent=self.root)
        self.refresh_project()

    def save_project(self,save_as=False):
        w=self.workspace;path=None
        if save_as or w.path is None:
            path=filedialog.asksaveasfilename(parent=self.root,title='Save project as a new filename',defaultextension='.strd',filetypes=[('STRD project','*.strd')])
            if not path:return False
        try:w.save(path)
        except (ProjectError,OSError) as exc:self.error(exc);return False
        self.refresh_project();return True

    def may_leave(self):
        if not self.workspace.dirty:return True
        choice=messagebox.askyesnocancel('Unsaved project', 'Save changes before leaving this project?\nYes: save. No: discard. Cancel: keep editing.',parent=self.root)
        if choice is None:return False
        return self.save_project() if choice else True

    def new_project(self):
        if not self.may_leave():return
        self.workspace=ProjectWorkspace();self.install_project()

    def install_project(self):
        self.loading=True
        try:self.title_var.set(self.workspace.doc['title'])
        finally:self.loading=False
        self.bind_member()

    def open_project(self):
        path=filedialog.askopenfilename(parent=self.root,title='Open STRD project',filetypes=[('STRD project','*.strd'),('All files','*')])
        if not path:return
        # Read/validate candidate BEFORE discard/save prompt or live replacement.
        candidate=ProjectWorkspace()
        try:candidate.open(path)
        except (ProjectError,OSError) as exc:self.error(exc);return
        if not self.may_leave():return
        # Saving the current file might have changed this same candidate. Re-read.
        try:candidate.open(path)
        except (ProjectError,OSError) as exc:self.error(exc);return
        self.workspace=candidate;self.install_project()

    def recover_project(self):
        path=filedialog.askopenfilename(parent=self.root,title='Select project or its .bak recovery file',filetypes=[('Recovery backup','*.bak'),('STRD project','*.strd'),('All files','*')])
        if not path:return
        candidate=ProjectWorkspace()
        try:candidate.recover(path)
        except (ProjectError,OSError) as exc:self.error(exc);return
        if not self.may_leave():return
        self.workspace=candidate;self.install_project()
        messagebox.showinfo('Backup recovered', 'Loaded the previous successful revision. Recalculate and Save As a NEW filename. Original file was not modified.',parent=self.root)

    def reset(self):
        if not messagebox.askyesno('Clear selected member?', 'Replace only this member with blank inputs? Save the project to keep this change.',parent=self.root):return
        self.workspace.sessions[self.workspace.index]=MemberSession();self.bind_member()

    def close(self):
        if self.may_leave():self.root.destroy()
