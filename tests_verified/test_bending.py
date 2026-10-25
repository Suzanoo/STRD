import ast
import contextlib
import io
import json
import math
from decimal import Decimal
from pathlib import Path
import unittest
from unittest.mock import patch
from dataclasses import replace

from strd_verified import check_bending
from strd_verified.reference import BASIS_ID, SECTION, MATERIAL


def request(**changes):
    value = dict(basis_id=BASIS_ID, section_id=SECTION.section_id,
                 material_id=MATERIAL.material_id, method="LRFD", moment_knm=310.0,
                 continuously_braced=True, support_twist_restrained=True,
                 major_axis_only=True)
    value.update(changes)
    return value


class BendingProofTests(unittest.TestCase):
    def test_reference_properties_are_exact_book_fixture(self):
        from dataclasses import asdict, FrozenInstanceError
        self.assertEqual(asdict(SECTION), {
            "section_id": "EX10.3.1-H450x200x9x14",
            "depth_mm": 450, "width_mm": 200, "web_mm": 9,
            "flange_mm": 14, "root_radius_mm": 18,
            "plastic_modulus_x_mm3": 1621000,
        })
        self.assertEqual(MATERIAL.fy_mpa, 245)
        self.assertEqual(MATERIAL.elastic_modulus_mpa, 200000)
        with self.assertRaises(FrozenInstanceError):
            SECTION.depth_mm = 500

    def test_independent_decimal_nominal_and_design_values(self):
        # Source literals from book pp.90-91, NOT production constants.
        nominal = Decimal("245") * Decimal("1621") * Decimal("1000")
        lrfd = nominal * Decimal("0.90")
        asd = nominal / Decimal("1.67")
        r = check_bending(request())
        mid = r["intermediates"]
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(mid["nominal_moment_nmm"], float(nominal))
        self.assertEqual(mid["lrfd_capacity_nmm"], float(lrfd))
        self.assertAlmostEqual(mid["asd_capacity_nmm"], float(asd), places=6)
        self.assertEqual(r["capacity_knm"], 357.4305)
        self.assertAlmostEqual(r["utilization"], 310 / 357.4305, places=14)

    def test_book_rounded_values(self):
        mid = check_bending(request())["intermediates"]
        for key, expected in (("nominal_moment_nmm", 397.1),
                              ("lrfd_capacity_nmm", 357.4),
                              ("asd_capacity_nmm", 237.8)):
            with self.subTest(key=key):
                self.assertLessEqual(abs(mid[key] / 1e6 - expected), 0.05)

    def test_intermediate_geometry_and_limits(self):
        mid = check_bending(request())["intermediates"]
        self.assertEqual(mid["clear_web_mm"], 386)
        self.assertAlmostEqual(mid["flange_width_thickness"], 100 / 14)
        self.assertAlmostEqual(mid["web_width_thickness"], 386 / 9)
        self.assertAlmostEqual(mid["flange_compact_limit"], 10.857142857142858)
        self.assertAlmostEqual(mid["web_compact_limit"], 107.42857142857143)
        self.assertEqual(mid["flange_class"], "COMPACT")
        self.assertEqual(mid["web_class"], "COMPACT")

    def test_asd_demand_is_independent(self):
        r = check_bending(request(method="ASD", moment_knm=200))
        self.assertEqual(r["status"], "PASS")
        self.assertEqual(r["intermediates"]["demand_nmm"], 200000000)
        self.assertAlmostEqual(r["capacity_knm"], 237.81137724550898)
        self.assertAlmostEqual(r["utilization"], 200 / 237.81137724550898)

    def test_demand_unit_conversion(self):
        r = check_bending(request(moment_knm=1.234))
        self.assertEqual(r["intermediates"]["demand_nmm"], 1234000)

    def test_capacity_boundary_and_overload(self):
        for method, cap in (("LRFD", 357.4305), ("ASD", 237.81137724550898)):
            for demand, status in ((0, "PASS"), (cap * (1-1e-9), "PASS"),
                                   (cap, "PASS"), (cap * (1+1e-9), "FAIL"),
                                   (500, "FAIL")):
                with self.subTest(method=method, demand=demand):
                    self.assertEqual(check_bending(request(method=method, moment_knm=demand))["status"], status)

    def test_non_numeric_and_nonfinite_moments(self):
        for value in (None, True, "310", [], float("nan"), float("inf"),
                      -float("inf"), -1, 1e308, 10**1000):
            with self.subTest(type=type(value), value=str(value)[:30]):
                r = check_bending(request(moment_knm=value))
                self.assertEqual(r["status"], "INVALID_INPUT")
                self.assertNotIn("capacity_knm", r)
                self.assertNotIn("utilization", r)

    def test_every_required_field_missing(self):
        for key in request():
            with self.subTest(key=key):
                value = request(); del value[key]
                self.assertEqual(check_bending(value)["status"], "INVALID_INPUT")

    def test_extra_fields_cannot_silently_drop_other_actions(self):
        for key in ("axial_kn", "shear_kn", "minor_moment_knm", "fy_mpa", "Lb", "capacity"):
            with self.subTest(key=key):
                self.assertEqual(check_bending(request(**{key: 1}))["status"], "INVALID_INPUT")

    def test_wrong_request_type(self):
        for value in (None, [], 1, "example"):
            self.assertEqual(check_bending(value)["status"], "INVALID_INPUT")

    def test_unsupported_ids_and_method(self):
        for key in ("basis_id", "section_id", "material_id", "method"):
            with self.subTest(key=key):
                r = check_bending(request(**{key: "other"}))
                self.assertEqual(r["status"], "UNSUPPORTED")
                self.assertNotIn("capacity_knm", r)

    def test_malformed_identifiers(self):
        for key in ("basis_id", "section_id", "material_id", "method"):
            for value in (None, "", 1, []):
                with self.subTest(key=key, value=value):
                    self.assertEqual(check_bending(request(**{key: value}))["status"], "INVALID_INPUT")

    def test_assumptions_must_be_explicit_boolean(self):
        for key in ("continuously_braced", "support_twist_restrained", "major_axis_only"):
            for value in (None, 1, "yes"):
                with self.subTest(key=key, value=value):
                    self.assertEqual(check_bending(request(**{key: value}))["status"], "INVALID_INPUT")

    def test_outside_assumptions_unsupported(self):
        for key in ("continuously_braced", "support_twist_restrained", "major_axis_only"):
            with self.subTest(key=key):
                self.assertEqual(check_bending(request(**{key: False}))["status"], "UNSUPPORTED")

    def test_reference_data_integrity(self):
        for changes in ({"plastic_modulus_x_mm3": 0}, {"web_mm": -1},
                        {"depth_mm": 20}, {"root_radius_mm": float("nan")}):
            with self.subTest(changes=changes), patch("strd_verified.bending.SECTION", replace(SECTION, **changes)):
                self.assertEqual(check_bending(request())["status"], "INVALID_INPUT")

    def test_noncompact_data_never_success(self):
        # Fault injection in internal reference only, not a supported catalog API.
        with patch("strd_verified.bending.SECTION", replace(SECTION, flange_mm=5)):
            self.assertEqual(check_bending(request())["status"], "UNSUPPORTED")
        with patch("strd_verified.bending.SECTION", replace(SECTION, web_mm=2)):
            self.assertEqual(check_bending(request())["status"], "UNSUPPORTED")

    def test_zero_reference_capacity_not_replaced_with_one(self):
        with patch("strd_verified.bending.SECTION", replace(SECTION, plastic_modulus_x_mm3=0)):
            r = check_bending(request(moment_knm=0))
            self.assertEqual(r["status"], "INVALID_INPUT")
            self.assertNotIn("utilization", r)

    def test_deterministic_fresh_results_no_console_io(self):
        value = request(); before = dict(value)
        output = io.StringIO()
        with contextlib.redirect_stdout(output), patch("builtins.input", side_effect=AssertionError("interactive call")):
            first = check_bending(value); second = check_bending(value)
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(value, before)
        self.assertEqual(first, second)
        json.dumps(first, allow_nan=False)
        first["inputs"]["method"] = "changed"
        first["not_checked"].clear()
        self.assertEqual(second, check_bending(value))

    def test_trace_and_scope_are_present(self):
        r = check_bending(request())
        self.assertEqual(r["basis_id"], BASIS_ID)
        self.assertIn("5.2.1 Eq.(10)", r["reference"]["clauses"])
        self.assertIn("shear", r["not_checked"])
        self.assertIn("bracing adequacy", r["not_checked"])
        self.assertEqual(r["governing_limit_state"], "YIELDING")

    def test_reused_legacy_yield_arithmetic_is_verified_in_isolation(self):
        # Reuse-first evidence: extract only the legacy class; no numpy needed.
        path = Path(__file__).resolve().parents[1] / "archive/legacy/applications/flexural.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Yeild")
        namespace = {}
        exec(compile(ast.Module(body=[cls], type_ignores=[]), str(path), "exec"), namespace)
        with contextlib.redirect_stdout(io.StringIO()):
            actual = namespace["Yeild"](MATERIAL_COMPAT()).major_axis(1621)
        self.assertAlmostEqual(actual, 357.4305)
        self.assertAlmostEqual(actual, check_bending(request())["capacity_knm"])
        # This verifies yielding arithmetic ONLY, not legacy routing, data or LTB.


class MATERIAL_COMPAT:
    Fy = 245
    Es = 200000


if __name__ == "__main__":
    unittest.main()
