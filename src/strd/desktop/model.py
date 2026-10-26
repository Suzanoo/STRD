"""One in-memory member, draft editing and result freshness. No engineering formulas."""
from copy import deepcopy
import json
from importlib.resources import files
import math
from strd.assessment import assess_member, SCHEMA_VERSION
from strd.catalog import catalog_snapshot, CATALOG_REVISION, MATERIAL_ID
from strd.engineering.dpt.basis import MS2_BASIS_ID

FLAGS = {
    'prismatic_undamaged': 'Prismatic, undamaged rolled H; no holes or copes',
    'major_axis_only': 'Major-axis bending only; no axial, minor-axis or torsional actions',
    'web_plane_only': 'Shear acts in the web plane',
    'unstiffened_web': 'Unstiffened web; no tension-field or stiffener strength credit',
    'support_twist_restrained': 'Supports have the required twist restraint',
    'segment_ends_braced': 'Every segment has the required end restraint',
}


class DraftError(ValueError):
    pass


class MemberSession:
    def __init__(self):
        self.inventory = catalog_snapshot()
        self._next_segment = 1
        self._next_case = 1
        self.draft = dict(schema_version=SCHEMA_VERSION, basis_id=MS2_BASIS_ID,
            catalog_revision=CATALOG_REVISION, member_id='B1',
            section_id=self.inventory['sections'][0]['section_id'], material_id=MATERIAL_ID,
            length_mm='', assumptions={k: False for k in FLAGS}, segments=[], cases=[])
        self.result = None
        self.state = 'EMPTY'
        self.demonstration = False
        self.add_segment(); self.add_case(); self.state = 'EMPTY'

    def invalidate(self):
        self.result = None  # Never expose old capacities as current after ANY edit.
        self.state = 'STALE'

    def set_value(self, path, value):
        target = self.draft
        for key in path[:-1]: target = target[key]
        if target[path[-1]] != value:
            target[path[-1]] = value
            self.invalidate()

    @staticmethod
    def _action(sid):
        return dict(segment_id=sid, moment_knm='', shear_kn='', cb='1',
                    cb_source='CONSERVATIVE', cb_reference='Cb=1 conservative assumption')

    def add_segment(self):
        while 'S'+str(self._next_segment) in {s['segment_id'] for s in self.draft['segments']}: self._next_segment += 1
        sid = 'S' + str(self._next_segment); self._next_segment += 1
        start = self.draft['segments'][-1]['end_mm'] if self.draft['segments'] else '0'
        self.draft['segments'].append(dict(segment_id=sid, start_mm=start, end_mm='', continuous_restraint=False))
        for case in self.draft['cases']: case['segments'].append(self._action(sid))
        self.invalidate()

    def remove_segment(self, index):
        if len(self.draft['segments']) <= 1: raise DraftError('Keep at least one segment.')
        self.draft['segments'].pop(index)
        for case in self.draft['cases']: case['segments'].pop(index)
        self.invalidate()

    def add_case(self):
        while 'C'+str(self._next_case) in {c['case_id'] for c in self.draft['cases']}: self._next_case += 1
        cid = 'C' + str(self._next_case); self._next_case += 1
        self.draft['cases'].append(dict(case_id=cid, method='ASD', action_source='',
            segments=[self._action(s['segment_id']) for s in self.draft['segments']]))
        self.invalidate()

    def remove_case(self, index):
        if len(self.draft['cases']) <= 1: raise DraftError('Keep at least one load case.')
        self.draft['cases'].pop(index); self.invalidate()

    def load_example(self):
        self.draft = json.loads(files('strd.desktop').joinpath('sample.json').read_text(encoding='utf-8'))
        self._next_segment = 3; self._next_case = 3
        self.demonstration = True; self.invalidate()

    def request(self):
        req = deepcopy(self.draft)
        def number(value, label):
            if type(value) is bool: raise DraftError(label + ': enter a finite number.')
            try: result = float(value)
            except (TypeError, ValueError, OverflowError): raise DraftError(label + ': enter a number (no units or comma separators).') from None
            if not math.isfinite(result): raise DraftError(label + ': enter a finite number.')
            return result
        req['length_mm'] = number(req['length_mm'], 'Member length [mm]')
        for s in req['segments']:
            for key in ('start_mm', 'end_mm'): s[key] = number(s[key], s['segment_id'] + ' ' + key)
        for case in req['cases']:
            for a in case['segments']:
                for key in ('moment_knm', 'shear_kn', 'cb'):
                    a[key] = number(a[key], case['case_id'] + '/' + a['segment_id'] + ' ' + key)
        return req

    def calculate(self):
        self.result = None
        try:
            req = self.request()
        except DraftError as exc:
            self.result = dict(status='INVALID_INPUT', message=str(exc), not_checked=[])
        else:
            self.result = assess_member(req)
        self.state = 'CURRENT'
        return deepcopy(self.result)
