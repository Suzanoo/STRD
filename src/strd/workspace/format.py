"""Versioned draft document. Storage validation is not engineering acceptance."""
from copy import deepcopy
from hashlib import sha256
import json
import math
from uuid import uuid4
from strd import __version__
from strd.assessment import ASSESSMENT_VERSION, SCHEMA_VERSION
from strd.catalog import catalog_snapshot, CATALOG_REVISION, MATERIAL_ID
from strd.desktop.model import MemberSession, FLAGS
from strd.engineering.dpt.basis import MS2_BASIS_ID, MS2_CALCULATOR_VERSION, SOURCE_SHA256

FORMAT = 'STRD-PROJECT-1'
MAX_BYTES = 16 * 1024 * 1024
MAX_MEMBERS = 100
MAX_ITEMS = 100

class ProjectError(ValueError):
    """Operation rejected; caller must retain the current workspace."""

class CompatibilityError(ProjectError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')


def digest(raw):
    return sha256(raw).hexdigest()


def basis():
    return dict(basis_id=MS2_BASIS_ID, source_sha256=SOURCE_SHA256,
                calculator_version=MS2_CALCULATOR_VERSION, assessment_version=ASSESSMENT_VERSION)


def entry(session=None):
    s = session or MemberSession()
    return dict(key=str(uuid4()), demonstration=s.demonstration, draft=deepcopy(s.draft))


def new_document():
    return dict(format=FORMAT, project_id=str(uuid4()), title='Untitled project',
                written_by=__version__, engineering=basis(), catalog=catalog_snapshot(),
                result_policy='RECALCULATE_ON_OPEN', members=[entry()])


def shape(value, keys, where):
    if type(value) is not dict or set(value) != set(keys):
        raise ProjectError(where + ': missing or unknown fields; file left unchanged.')


def text(value, where, nonempty=False):
    if type(value) is not str or len(value)>4096 or '\x00' in value or (nonempty and not value.strip()):
        raise ProjectError(where + ': invalid text.')
    try:value.encode('utf-8')
    except UnicodeError:raise ProjectError(where + ': invalid Unicode.') from None


def identity(value):
    from uuid import UUID
    try:
        if str(UUID(value)) != value:raise ValueError()
    except (ValueError, TypeError, AttributeError):raise ProjectError('Invalid project/member identity.') from None


def numeric_draft(value):
    if type(value) is str:text(value, 'Draft number')
    elif type(value) not in (int, float) or not math.isfinite(value):
        raise ProjectError('Draft numeric field must be finite number or editable text.')


def items(value, where):
    if type(value) is not list or not 1 <= len(value) <= MAX_ITEMS:
        raise ProjectError(where + ': expected 1-100 items.')


def validate_draft(d):
    shape(d, ('schema_version','basis_id','catalog_revision','member_id','section_id','material_id','length_mm','assumptions','segments','cases'), 'Member')
    for k,v in [('schema_version',SCHEMA_VERSION),('basis_id',MS2_BASIS_ID),('catalog_revision',CATALOG_REVISION),('material_id',MATERIAL_ID)]:
        if d[k]!=v:raise CompatibilityError('Unsupported member '+k+'; no automatic substitution.')
    if d['section_id'] not in [s['section_id'] for s in catalog_snapshot()['sections']]:
        raise CompatibilityError('Section is outside the verified catalog.')
    text(d['member_id'],'Member ID');numeric_draft(d['length_mm'])
    shape(d['assumptions'],FLAGS,'Assumptions')
    if any(type(v) is not bool for v in d['assumptions'].values()):raise ProjectError('Assumptions must be boolean.')
    items(d['segments'],'Segments');items(d['cases'],'Cases')
    ids=[]
    for s in d['segments']:
        shape(s,('segment_id','start_mm','end_mm','continuous_restraint'),'Segment')
        text(s['segment_id'],'Segment ID',True);ids.append(s['segment_id'])
        numeric_draft(s['start_mm']);numeric_draft(s['end_mm'])
        if type(s['continuous_restraint']) is not bool:raise ProjectError('Restraint must be boolean.')
    if len(ids)!=len(set(ids)):raise ProjectError('Duplicate segment identities.')
    for c in d['cases']:
        shape(c,('case_id','method','action_source','segments'),'Case')
        for key in ('case_id','method','action_source'):text(c[key],key)
        items(c['segments'],'Case actions')
        if len(c['segments'])!=len(ids):raise ProjectError('Case/segment structure mismatch.')
        for i,a in enumerate(c['segments']):
            shape(a,('segment_id','moment_knm','shear_kn','cb','cb_source','cb_reference'),'Action')
            if a['segment_id']!=ids[i]:raise ProjectError('Case/segment identity mismatch.')
            for key in ('moment_knm','shear_kn','cb'):numeric_draft(a[key])
            for key in ('cb_source','cb_reference'):text(a[key],key)


def validate(doc):
    shape(doc,('format','project_id','title','written_by','engineering','catalog','result_policy','members'),'Project')
    if doc['format']!=FORMAT:raise CompatibilityError('Unsupported project format; use its compatible application. No migration performed.')
    if canonical(doc['engineering'])!=canonical(basis()):raise CompatibilityError('Engineering basis/version differs; automatic migration is not supported.')
    if canonical(doc['catalog'])!=canonical(catalog_snapshot()):raise CompatibilityError('Catalog snapshot differs; no property replacement or recalculation permitted.')
    if doc['result_policy']!='RECALCULATE_ON_OPEN':raise CompatibilityError('Unsupported result policy.')
    identity(doc['project_id']);text(doc['title'],'Project title');text(doc['written_by'],'Writer version',True)
    if type(doc['members']) is not list or not 1<=len(doc['members'])<=MAX_MEMBERS:raise ProjectError('Project requires 1-100 members.')
    keys=[]
    for m in doc['members']:
        shape(m,('key','demonstration','draft'),'Member entry');identity(m['key']);keys.append(m['key'])
        if type(m['demonstration']) is not bool:raise ProjectError('Invalid demonstration flag.')
        validate_draft(m['draft'])
    if len(keys)!=len(set(keys)):raise ProjectError('Duplicate workspace member identities.')
    return doc


def encode(doc):
    validate(doc)
    payload=deepcopy(doc);payload['written_by']=__version__
    raw=canonical(dict(payload=payload,sha256=digest(canonical(payload))))+b'\n'
    if len(raw)>MAX_BYTES:raise ProjectError('Project exceeds 16 MiB limit.')
    return raw


def decode(raw):
    if len(raw)>MAX_BYTES:raise ProjectError('Project exceeds 16 MiB limit.')
    def pairs(values):
        d={}
        for k,v in values:
            if k in d:raise ProjectError('Duplicate JSON key: '+k)
            d[k]=v
        return d
    def bad(_):raise ProjectError('Nonfinite JSON number.')
    try:
        env=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=bad)
        shape(env,('payload','sha256'),'Envelope')
        if env['sha256']!=digest(canonical(env['payload'])):raise ProjectError('Project integrity checksum mismatch.')
        return validate(env['payload'])
    except ProjectError:raise
    except (ValueError,TypeError,UnicodeError,OverflowError,RecursionError) as exc:
        raise ProjectError('Invalid project document: '+str(exc)) from None
