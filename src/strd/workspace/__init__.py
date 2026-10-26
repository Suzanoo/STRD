"""Project workspace orchestration, independent of Tk and engineering formulas."""
from copy import deepcopy
from uuid import uuid4
from . import storage
from .format import new_document, validate, canonical, entry, ProjectError, MAX_MEMBERS
from strd.desktop.model import MemberSession


class ProjectWorkspace:
    def __init__(self):
        self._adopt(new_document(),None,None)
        self.saved=None  # New project is unsaved even before editing.

    def _adopt(self,doc,path,token):
        validate(doc)
        sessions=[]
        for m in doc['members']:
            s=MemberSession();s.draft=deepcopy(m['draft']);s.demonstration=m['demonstration'];s.invalidate()
            # Allocate fresh generated identities beyond existing names; the editable
            # case labels can be arbitrary, and must not cause a generated collision.
            def next_id(values,prefix):
                n=1
                while prefix+str(n) in values:n+=1
                return n
            s._next_segment=next_id([v['segment_id'] for v in s.draft['segments']],'S')
            s._next_case=next_id([v['case_id'] for v in s.draft['cases']],'C')
            sessions.append(s)
        self.doc=deepcopy(doc);self.sessions=sessions;self.index=0
        self.path=path;self.token=token;self.saved=canonical(self.document()) if path else None

    @property
    def session(self):return self.sessions[self.index]

    def document(self):
        doc=deepcopy(self.doc)
        for m,s in zip(doc['members'],self.sessions):
            m['draft']=deepcopy(s.draft);m['demonstration']=s.demonstration
        return doc

    @property
    def dirty(self):return self.saved is None or canonical(self.document())!=self.saved

    def add(self,duplicate=False):
        if len(self.sessions)>=MAX_MEMBERS:raise ProjectError('Maximum 100 members per project.')
        s=MemberSession()
        if duplicate:
            s.draft=deepcopy(self.session.draft);s.demonstration=self.session.demonstration
            s._next_case=self.session._next_case;s._next_segment=self.session._next_segment
            s.draft['member_id']+=' copy';s.invalidate()
        else:s.draft['member_id']='B'+str(len(self.sessions)+1)
        self.sessions.append(s);self.doc['members'].append(entry(s));self.index=len(self.sessions)-1

    def remove(self):
        if len(self.sessions)==1:raise ProjectError('Keep at least one member.')
        self.sessions.pop(self.index);self.doc['members'].pop(self.index);self.index=max(0,self.index-1)

    def open(self,path):
        doc,token,p=storage.load(path)
        self._adopt(doc,p,token)  # Validate/read fully before replacing live state.

    def recover(self,path):
        doc=storage.recover(path)
        self._adopt(doc,None,None)  # Must Save As a new file; damaged original retained.

    def save(self,path=None):
        if path is None and self.path is None:raise ProjectError('Choose Save As for this unsaved project.')
        dest=storage.location(path) if path is not None else self.path
        expected=self.token if dest==self.path else None
        doc=self.document();token,p=storage.save(dest,doc,expected)
        self.path=p;self.token=token;self.saved=canonical(doc)
