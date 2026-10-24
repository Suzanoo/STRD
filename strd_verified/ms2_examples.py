"""Headless MS-2 book examples; no file I/O, UI or load analysis."""
import json
from .h_reference import BASIS_ID, SECTION, MATERIAL
from .h_beam import check_flexure, check_web_shear, moment_gradient_factor


def examples():
    common = dict(basis_id=BASIS_ID, section_id=SECTION.section_id,
                  material_id=MATERIAL.material_id, prismatic_undamaged=True)
    results = {}
    for method, moment, shear in (("LRFD", 310., 542.5), ("ASD", 200., 350.)):
        flexure = dict(common, method=method, moment_knm=moment,
                       support_twist_restrained=True, segment_ends_braced=True,
                       major_axis_only=True)
        results[f"10.3.1_{method}"] = check_flexure(dict(flexure,
            unbraced_length_mm=0., cb=1., cb_source="CONSERVATIVE",
            cb_reference="Example 10.3.1 continuous restraint"))
        results[f"10.3.2_{method}"] = check_flexure(dict(flexure,
            unbraced_length_mm=3333., cb=1.01, cb_source="VERIFIED_MOMENT_DIAGRAM",
            cb_reference="Example 10.3.2 governing inner segment, printed Cb=1.01"))
        results[f"10.4.1_{method}"] = check_web_shear(dict(common, method=method,
            shear_kn=shear, web_plane_only=True, unstiffened_web=True))
    results['10.3.2_inner_cb_unrounded'] = moment_gradient_factor(dict(
        maximum_knm=1., quarter_knm=.972, midpoint_knm=1., three_quarter_knm=.972))
    return results


if __name__ == '__main__':
    print(json.dumps(examples(), indent=2, ensure_ascii=False, allow_nan=False))
