"""Headless reference-example smoke command: python -m strd_verified."""

import json

from .bending import check_bending
from .reference import BASIS_ID, SECTION, MATERIAL


def main():
    outputs = []
    for method, moment in (("LRFD", 310.0), ("ASD", 200.0)):
        outputs.append(check_bending({
            "basis_id": BASIS_ID, "section_id": SECTION.section_id,
            "material_id": MATERIAL.material_id, "method": method,
            "moment_knm": moment, "continuously_braced": True,
            "support_twist_restrained": True, "major_axis_only": True,
        }))
    print(json.dumps(outputs, ensure_ascii=False, allow_nan=False, indent=2))


if __name__ == "__main__":
    main()
