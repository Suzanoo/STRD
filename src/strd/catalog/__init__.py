"""Curated offline SYS subset. No arbitrary catalog or property override API."""
from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib.resources import files
import json

from strd.domain.properties import ReferenceSection, ReferenceMaterial
from strd.domain.validation import _number

CATALOG_REVISION = 'SYS-TIS-H-ED6-A2-1'
MATERIAL_ID = 'SYS-SS400-TLE16-DPT-E200000-v1'


@dataclass(frozen=True)
class CatalogSection(ReferenceSection):
    elastic_modulus_x_mm3: float
    radius_y_mm: float
    inertia_y_mm4: float
    torsion_j_mm4: float
    warping_cw_mm6: float


def _read():
    raw = files(__package__).joinpath('sys_h_ed6.json').read_bytes()
    if sha256(raw).hexdigest() != 'b6486d0109ae73f88f9b12f7aa03ff734e5ac20eca75072dc84cabbf634416dd':
        raise ValueError('Catalog content checksum mismatch; unreviewed edits are not supported.')
    data = json.loads(raw)
    if data['catalog_revision'] != CATALOG_REVISION:
        raise ValueError('Catalog revision mismatch.')
    ids = [s['section_id'] for s in data['sections']]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError('Catalog identities must be unique and nonempty.')
    # Hash identifies the exact shipped input snapshot; it is not a signature.
    return data, sha256(raw).hexdigest()


def catalog_snapshot() -> dict:
    """Return a fresh JSON-compatible inventory with explicit SI property names."""
    data, digest = _read()
    return dict(data, content_sha256=digest)


def _resolve(section_id, material_id):
    data, digest = _read()
    if material_id != MATERIAL_ID or data['material']['material_id'] != MATERIAL_ID:
        raise LookupError('Unsupported material_id; no grade substitution.')
    selected = next((s for s in data['sections'] if s['section_id'] == section_id), None)
    if selected is None:
        raise LookupError('Unsupported section_id; no nominal-size fallback.')
    section = CatalogSection(**selected)
    material = ReferenceMaterial(**data['material'])
    thickness = data['material_max_thickness_mm']
    if thickness != 16 or material.fy_mpa != 245 or material.elastic_modulus_mpa != 200000:
        raise ValueError('Material record differs from the verified applicability envelope.')
    for value in (section.web_mm, section.flange_mm):
        if not _number(value) or value <= 0:
            raise ValueError('Invalid material thickness.')
        if value > thickness:
            raise LookupError('Only SS400 web/flange thickness <=16 mm is supported.')
    evidence = dict(catalog_revision=CATALOG_REVISION, content_sha256=digest,
                    section=asdict(section), material=asdict(material), sources=data['sources'],
                    material_max_thickness_mm=thickness,
                    data_status='Curated manufacturer nominal properties; not a mill certificate')
    return section, material, evidence
