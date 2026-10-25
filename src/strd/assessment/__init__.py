"""Headless A2 service; supplied actions only, no project storage or force generation."""
from copy import deepcopy
from hashlib import sha256
import json

from strd.catalog import CATALOG_REVISION, _resolve
from strd.domain.validation import _number
from strd.engineering.dpt.basis import MS2_BASIS_ID
from strd.engineering.dpt.checks import _check_flexure, _check_web_shear, _EXCLUSIONS

SCHEMA_VERSION = 'STRD-MEMBER-1'
ASSESSMENT_VERSION = 'A2-1'
GEOMETRY_PROPERTIES = ('depth_mm', 'width_mm', 'web_mm', 'flange_mm', 'root_radius_mm')
REQUIRED_PROPERTIES = {
    'FLEXURE': GEOMETRY_PROPERTIES + ('plastic_modulus_x_mm3', 'elastic_modulus_x_mm3',
        'radius_y_mm', 'inertia_y_mm4', 'torsion_j_mm4', 'warping_cw_mm6'),
    'SHEAR': GEOMETRY_PROPERTIES,
}
_FLAGS = {'prismatic_undamaged', 'support_twist_restrained', 'segment_ends_braced',
          'major_axis_only', 'web_plane_only', 'unstiffened_web'}
_TOP = {'schema_version', 'basis_id', 'catalog_revision', 'member_id', 'section_id',
        'material_id', 'length_mm', 'assumptions', 'segments', 'cases'}
_SEGMENT = {'segment_id', 'start_mm', 'end_mm', 'continuous_restraint'}
_CASE = {'case_id', 'method', 'action_source', 'segments'}
_ACTION = {'segment_id', 'moment_knm', 'shear_kn', 'cb', 'cb_source', 'cb_reference'}


class _InputError(ValueError):
    pass


class _ScopeError(ValueError):
    pass


def _shape(value, keys, path):
    if type(value) is not dict:
        raise _InputError(path + ' must be a dictionary.')
    if set(value) != keys:
        raise _InputError(path + ': missing=' + str(sorted(keys - value.keys())) +
                          '; unexpected=' + str(sorted(map(str, value.keys() - keys))))


def _text(value, path):
    if type(value) is not str or not value.strip():
        raise _InputError(path + ' must be a nonempty string.')


def _scalar(value, path, positive=False):
    if not _number(value) or value < 0 or (positive and value == 0):
        raise _InputError(path + ' must be finite and ' + ('positive.' if positive else 'nonnegative.'))


def _list(value, path):
    if type(value) is not list or not value:
        raise _InputError(path + ' must be a nonempty list.')


def _validate(req):
    _shape(req, _TOP, 'member')
    for key in ('schema_version', 'basis_id', 'catalog_revision', 'member_id', 'section_id', 'material_id'):
        _text(req[key], key)
    _scalar(req['length_mm'], 'length_mm', positive=True)
    _shape(req['assumptions'], _FLAGS, 'assumptions')
    for key, value in req['assumptions'].items():
        if type(value) is not bool:
            raise _InputError(key + ' must be an explicit boolean.')
    _list(req['segments'], 'segments')
    previous = 0
    segment_ids = set()
    for segment in req['segments']:
        _shape(segment, _SEGMENT, 'segment')
        _text(segment['segment_id'], 'segment_id')
        if segment['segment_id'] in segment_ids:
            raise _InputError('Duplicate segment_id.')
        segment_ids.add(segment['segment_id'])
        for key in ('start_mm', 'end_mm'):
            _scalar(segment[key], key)
        if segment['start_mm'] != previous or segment['end_mm'] <= previous:
            raise _InputError('Segments must be ordered, contiguous, nonoverlapping and positive length.')
        previous = segment['end_mm']
        if type(segment['continuous_restraint']) is not bool:
            raise _InputError('continuous_restraint must be an explicit boolean.')
    if previous != req['length_mm']:
        raise _InputError('Segments must cover exactly the declared member length.')
    _list(req['cases'], 'cases')
    case_ids = set()
    for case in req['cases']:
        _shape(case, _CASE, 'case')
        for key in ('case_id', 'method', 'action_source'):
            _text(case[key], key)
        if case['case_id'] in case_ids:
            raise _InputError('Duplicate case_id.')
        case_ids.add(case['case_id'])
        _list(case['segments'], 'case.segments')
        seen = set()
        for action in case['segments']:
            _shape(action, _ACTION, 'case.segment')
            for key in ('segment_id', 'cb_source', 'cb_reference'):
                _text(action[key], key)
            if action['segment_id'] in seen:
                raise _InputError('Duplicate case/segment action.')
            seen.add(action['segment_id'])
            for key in ('moment_knm', 'shear_kn', 'cb'):
                _scalar(action[key], key)
        if seen != segment_ids:
            raise _InputError('Each case must provide exactly one action record for every member segment.')
    for key, expected in (('schema_version', SCHEMA_VERSION), ('basis_id', MS2_BASIS_ID),
                          ('catalog_revision', CATALOG_REVISION)):
        if req[key] != expected:
            raise _ScopeError('Unsupported ' + key + '; explicit migration required.')
    if not all(req['assumptions'].values()):
        raise _ScopeError('Member assumptions are outside the supported envelope.')
    for case in req['cases']:
        if case['method'] not in ('ASD', 'LRFD'):
            raise _ScopeError('Unsupported design method.')


def _base(status, message):
    return dict(status=status, message=message, schema_version=SCHEMA_VERSION,
                assessment_version=ASSESSMENT_VERSION, basis_id=MS2_BASIS_ID,
                scope='Conditional major-axis flexure and web shear only; not whole-member acceptance',
                not_checked=list(_EXCLUSIONS) + ['stiffener design', 'tension-field action',
                    'action generation/load combinations', 'interaction of simultaneous actions'],
                coverage={'requested_checks': ['FLEXURE', 'SHEAR'], 'complete': False})


def _check(check, request, section, material, evidence):
    missing = [p for p in REQUIRED_PROPERTIES[check]
               if not _number(getattr(section, p, None)) or getattr(section, p) <= 0]
    if missing:
        return dict(status='INVALID_INPUT', check=check,
                    message='Missing/invalid required section properties.', missing_properties=missing)
    if check == 'FLEXURE':
        result = _check_flexure(request, section, material)
    else:
        result = _check_web_shear(request, section, material, full_reference_integrity=False)
    if 'reference' in result:
        reference = result['reference']
        reference['data_status'] = evidence['data_status']
        reference['catalog_revision'] = evidence['catalog_revision']
        reference['catalog_content_sha256'] = evidence['content_sha256']
        reference['property_sources'] = deepcopy(evidence['sources'])
        reference['clauses'] = [c for c in reference['clauses'] if not c.startswith('Example')]
        reference['printed_pages'] = [9, 10, 28, 29, 30] if check == 'FLEXURE' else [51, 52, 53]
    return result


def assess_member(request: object) -> dict:
    """Validate complete case/segment coverage then perform independent strength checks.

    Moments/shears are supplied maximum absolute segment demands on each case's
    method basis. No sign inference, load combinations or interaction is performed.
    CHECKS_PASS means only that every requested conditional check passed.
    """
    try:
        _validate(request)
    except _InputError as exc:
        return _base('INVALID_INPUT', str(exc))
    except _ScopeError as exc:
        return _base('UNSUPPORTED', str(exc))
    req = deepcopy(request)
    try:
        section, material, evidence = _resolve(req['section_id'], req['material_id'])
    except LookupError as exc:
        return _base('UNSUPPORTED', str(exc))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return _base('INVALID_INPUT', 'Catalog integrity failure: ' + str(exc))
    records = []
    for case in req['cases']:
        by_segment = {a['segment_id']: a for a in case['segments']}
        for segment in req['segments']:
            action = by_segment[segment['segment_id']]
            common = {k: req[k] for k in ('basis_id', 'section_id', 'material_id')}
            common.update(method=case['method'], prismatic_undamaged=req['assumptions']['prismatic_undamaged'])
            flex = dict(common, **{k: action[k] for k in ('moment_knm', 'cb', 'cb_source', 'cb_reference')},
                        unbraced_length_mm=0 if segment['continuous_restraint'] else segment['end_mm']-segment['start_mm'],
                        **{k: req['assumptions'][k] for k in ('support_twist_restrained', 'segment_ends_braced', 'major_axis_only')})
            shear = dict(common, shear_kn=action['shear_kn'],
                         **{k: req['assumptions'][k] for k in ('web_plane_only', 'unstiffened_web')})
            records.append(dict(case_id=case['case_id'], method=case['method'],
                                action_source=case['action_source'], segment=deepcopy(segment),
                                flexure=_check('FLEXURE', flex, section, material, evidence),
                                shear=_check('SHEAR', shear, section, material, evidence)))
    checks = [r[k] for r in records for k in ('flexure', 'shear')]
    complete = all(c['status'] in ('PASS', 'FAIL') for c in checks)
    failed = any(c['status'] == 'FAIL' for c in checks)
    status = ('CHECKS_FAIL' if failed else 'CHECKS_PASS') if complete else 'INCOMPLETE'
    result = _base(status, 'Conditional strength checks completed.' if complete else 'One or more checks could not be completed; inspect per-check diagnostics.')
    governing = {}
    for kind in ('flexure', 'shear'):
        candidates = [r for r in records if r[kind]['status'] in ('PASS', 'FAIL')]
        if candidates:
            highest = max(r[kind]['utilization'] for r in candidates)
            governing[kind] = dict(utilization=highest, partial=not complete,
                cases=[dict(case_id=r['case_id'], method=r['method'], segment_id=r['segment']['segment_id'])
                       for r in candidates if r[kind]['utilization'] == highest])
    result.update(inputs=req, data_snapshot=evidence, records=records, governing=governing,
                  has_strength_failure=failed,
                  coverage={'requested_checks': ['FLEXURE', 'SHEAR'], 'complete': complete,
                            'expected': 2*len(req['cases'])*len(req['segments']),
                            'completed': sum(c['status'] in ('PASS', 'FAIL') for c in checks)})
    snapshot = {'inputs': req, 'data': evidence, 'assessment_version': ASSESSMENT_VERSION}
    result['snapshot_sha256'] = sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':'),
                                                ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    return result
