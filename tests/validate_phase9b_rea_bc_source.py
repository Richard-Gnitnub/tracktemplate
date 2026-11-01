#!/usr/bin/env python3
"""Compare the B/C successor with independently frozen source summaries.

Source-informed calculations, Copyright (C) 2024 Martin Wynne and
OpenTemplot contributors, GPL-3.0-or-later. See NOTICE.md and
reference/PROVENANCE.md. These numerical comparisons do not establish
physical fit, rights, native/GUI qualification or production acceptance.
"""

import dataclasses
from decimal import Decimal
from decimal import localcontext
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import validate_phase1_turnout as baseline  # noqa: E402


FIXTURE = ROOT / "tests/fixtures/phase9b-rea-bc-source.json"
FIXTURE_SHA256 = (
    "d8c356a8cd84be1de0f6535abc09090a12dd82ecbb6083bd3ca65e19f43694f4"
)
CONTEXT = "templot-556b-rea-bh-regular-auto-fit-square-on"
SENTINEL = "Phase 9B independent REA B/C source comparisons passed"
MENU = (4, 4.5, 4.75, 5, 5.25, 5.5, 5.75, 6, 6.25, 6.5,
        7, 7.5, 8, 9, 10, 12)


class ReaSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.subject = importlib.import_module(
            "tracktemplate.domain.rea_turnout"
        )
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.specification = cls.subject.ReaTurnoutSpecification

    def test_independent_fixture_identity_and_provenance(self):
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
                         FIXTURE_SHA256)
        self.assertEqual(self.fixture["source_context"], CONTEXT)
        self.assertEqual(self.fixture["archive_sha256"],
                         "2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f"
                         "3404259cbf262f7309cf3")
        self.assertEqual(self.fixture["case_count"], 88)
        for row in self.fixture["cases"]:
            self.assertEqual(len(row["dimensions"]), 85)

    def test_all_menu_combinations_and_continuous_source_boundaries(self):
        rows = self.fixture["cases"]
        self.assertEqual(self.fixture["case_count"], len(rows))
        menu = {(r["switch"], float(r["crossing_ratio"]))
                for r in rows if r["is_menu"]}
        self.assertEqual(menu, {(s, n) for s in ("B", "C") for n in MENU})
        self.assertTrue(any(not r["is_menu"] for r in rows))
        for row in rows:
            with self.subTest(size=row["switch"], n=row["crossing_ratio"]):
                spec = self.specification(
                    row["switch"], float(row["crossing_ratio"])
                )
                result = self.subject.rea_turnout_dimensions(spec)
                for name, expected in row["dimensions"].items():
                    # Reuse the retained Phase 1 scalar arithmetic budget.
                    # This is not a fit or railway acceptance tolerance.
                    baseline._close(result[name], expected)
                self.assertEqual(
                    result["check_turnout_working_mode"],
                    row["check_turnout_working_mode"],
                )
                for key in ("wing_front_count", "vee_timber_count",
                            "wing_chair_span", "crossing_seat"):
                    self.assertEqual(result[key], row["metadata"][key])
                self.assertEqual(result["source_status"],
                                 "transient-unqualified")
                self.assertFalse(row["source_check_approximation"])
                self.assertGreater(result["turnout_radius"], 0)
                self.assertGreater(result["curved_stock_radius"], 0)
                self.assertLessEqual(
                    result["turnout_radius"], result["switch_radius"]
                )
                self.assertEqual(result, self.subject.rea_turnout_dimensions(
                    spec
                ))

    def test_source_timber_counts_stations_and_literal_suffixes(self):
        for row in self.fixture["cases"]:
            with self.subTest(size=row["switch"], n=row["crossing_ratio"]):
                spec = self.specification(
                    row["switch"], float(row["crossing_ratio"])
                )
                actual = self.subject.rea_turnout_timber_stations(spec)
                expected = row["timbers"]
                self.assertEqual(len(actual), len(expected))
                for found, wanted in zip(actual, expected):
                    for key in ("identifier", "section", "crossing_suffix"):
                        self.assertEqual(found[key], wanted[key])
                    baseline._close(found["x"], wanted["x"])
                    self.assertEqual(found["angle_radians"], 0.0)
                    # B/C front_timbered=True: J1/J2 also use 12-inch
                    # timber width (switch_select:1770,1825; math:23140).
                    baseline._close(found["width"], wanted["width"])
                self.assertEqual(
                    len({r["identifier"] for r in actual}), len(actual)
                )

    def test_strict_invalid_and_unqualified_inputs(self):
        invalid_ratios = (
            None, True, False, "10", math.nan, math.inf, -math.inf,
            -1, 0, 0.5, 1.49, 1.5, math.nextafter(4, -math.inf),
            10 ** 400,
            20.125, 24, 100,
        )
        for size in ("B", "C"):
            for value in invalid_ratios:
                with self.subTest(size=size, ratio=value):
                    with self.assertRaises((ValueError, TypeError)):
                        self.subject.rea_turnout_dimensions(
                            self.specification(size, value)
                        )
        for size in (None, True, 2, "A", "D", "b", "REA B", ""):
            with self.subTest(size=size):
                with self.assertRaises((ValueError, TypeError)):
                    self.subject.rea_turnout_dimensions(
                        self.specification(size, 10)
                    )
        for values in ({"schema_version": 2}, {"schema_version": True},
                       {"source_context": ""},
                       {"source_context": "clip-fit"},
                       {"source_context": "curviform"},
                       {"source_context": None}):
            with self.subTest(options=values):
                with self.assertRaises((ValueError, TypeError)):
                    self.subject.rea_turnout_dimensions(
                        self.specification("C", 10, **values)
                    )

    def test_straight_sentinel_and_irregular_source_regions_reject(self):
        heels = {"B": 18.417941404842995, "C": 22.70237204880366}
        for size, heel in heels.items():
            for n in (heel - 1.0e-10, math.nextafter(heel, 0), heel,
                      math.nextafter(heel, math.inf), heel + 0.01):
                with self.subTest(size=size, n=n):
                    with self.assertRaises(ValueError):
                        self.subject.rea_turnout_dimensions(
                            self.specification(size, n)
                        )

    def test_denominator_sentinel_still_reaches_source_auto_fit(self):
        # Distinct source predicates: math3357 versus3373-3375. A nonstraight
        # denominator sentinel proceeds to the3401 auto-fit radius cap.
        n = 18.417941403843
        with localcontext() as context:
            context.prec = 70
            d = Decimal
            inch = d(1) / 3
            planing_ratio = d(32)
            norm = (planing_ratio ** 2 + 1).sqrt()
            sine = 1 / norm
            cosine = planing_ratio / norm
            radius = d(7356) * inch
            heel_sine = (d(257) * inch - d(88) * inch * cosine) / radius
            heel_sine += sine
            heel_cosine = (1 - heel_sine ** 2).sqrt()
            offset = (d(88) * inch * cosine / planing_ratio
                      + radius * (cosine - heel_cosine))
            ratio = d(str(n))
            crossing_norm = (ratio ** 2 + 1).sqrt()
            crossing_sine = 1 / crossing_norm
            crossing_cosine = ratio / crossing_norm
            denominator = heel_cosine - crossing_cosine
            self.assertLess(abs(denominator), d("1e-12"))
            self.assertGreater(abs(math.asin(float(heel_sine))
                                   - math.atan(1 / n)), 1.0e-12)
            entry = (d("16.5") - offset - radius * denominator) * ratio
            span = radius * (crossing_sine - heel_sine)
        self.assertGreater(span, 0)
        result = self.subject.rea_turnout_dimensions(
            self.specification("B", n)
        )
        self.assertTrue(result["auto_fit_cap"])
        baseline._close(result["turnout_radius"], radius)
        baseline._close(result["entry_straight"], entry)
        baseline._close(result["turnout_curve_length"], span)
        self.assertGreater(result["turnout_curve_length"], 0)
        # Above the heel the sentinel cap must not admit a negative span.
        with self.assertRaises(ValueError):
            self.subject.rea_turnout_dimensions(
                self.specification("B", 18.417941405843)
            )

    def test_actual_source_consumer_rail_anchors(self):
        # Use the real retained rail consumers and new adapter. Only host
        # access is doubled; expected anchors come from frozen source data.
        from types import SimpleNamespace
        import validate_phase9b_rea_bc_consumers as consumers
        from tracktemplate.compatibility.rea_turnout import (
            ReaTurnoutGeometryAdapter,
        )

        module = consumers.railway_module()
        adapter = ReaTurnoutGeometryAdapter(module)
        source_host = consumers.host(module)
        document = SimpleNamespace(turnouts=[], crossovers=[])
        for size, n in (("B", 5.5), ("C", 10), ("C", 12)):
            row = next(r for r in self.fixture["cases"]
                       if r["switch"] == size
                       and float(r["crossing_ratio"]) == n)
            expected = {k: float(v) for k, v in row["dimensions"].items()}
            result = adapter.turnout(
                document, source_host, 2000,
                module.TURNOUT_HAND_LEFT, module.TURNOUT_ORIENTATION_FACING,
                self.specification(size, n),
            )
            rails = {rail["name"]: rail["local_points"]
                     for rail in result["rails"]}
            anchors = {
                "turnout-side wing flare gauge face": (
                    expected["wing_flare_turnout_x"],
                    expected["wing_end_turnout_x"],
                ),
                "turnout-side wing flare outer face": (
                    expected["wing_flare_turnout_outer_x"],
                    expected["wing_end_turnout_outer_x"],
                ),
                "main-side wing flare gauge face": (
                    expected["wing_flare_main_x"],
                    expected["wing_end_main_x"],
                ),
                "main-side wing flare outer face": (
                    expected["wing_flare_main_outer_x"],
                    expected["wing_end_main_outer_x"],
                ),
                "main-side check rail gauge face": (
                    expected["check_main_start_x"],
                    expected["check_main_end_x"],
                ),
                "main-side check rail outer face": (
                    expected["check_main_outer_start_x"],
                    expected["check_main_outer_end_x"],
                ),
                "turnout-side check rail gauge face": (
                    expected["check_turnout_start_x"],
                    expected["check_turnout_end_x"],
                ),
            }
            # math_unit.pas:4443,4467,4475,4505-4511, bent flares.
            k = expected["k3"]
            flare = expected["flare_angle"]
            width = expected["rail_head_width"]
            angle = k
            if row["check_turnout_working_mode"] != "straight crossing leg":
                angle -= (
                    expected["check_turnout_length_before_fp"]
                    - expected["entry_straight"] / math.cos(k)
                    + expected["flare_length"]
                ) / expected["check_turnout_radius"]
            outer_start = (expected["check_turnout_start_x"]
                           + width * math.sin(angle + flare))
            outer_end = (expected["check_turnout_end_x"]
                         + width * math.sin(k - flare))
            anchors["turnout-side check rail outer face"] = (
                outer_start, outer_end,
            )
            for name, (start, end) in anchors.items():
                for index, wanted in ((0, start), (-1, end)):
                    with self.subTest(size=size, n=n, rail=name, end=index):
                        baseline._close(rails[name][index][0], wanted)

            # Source docrossing8608-8611 always uses turnoutst_wing/check,
            # then aq2/aq3offset plus a vertical offset divided by cos(k).
            # This independently checks all retained samples, not just X.
            inner_corner_angle = k
            if row["check_turnout_working_mode"] != "straight crossing leg":
                inner_corner_angle -= (
                    expected["check_turnout_length_before_fp"]
                    - expected["entry_straight"] / math.cos(k)
                ) / expected["check_turnout_radius"]
            check_outer_in = (expected["check_turnout_flare_in_x"]
                              + expected["rail_bend_width"]
                              * math.sin(inner_corner_angle + flare / 2))
            check_outer_out = (expected["check_turnout_flare_out_x"]
                               + expected["rail_bend_width"]
                               * math.sin(k - flare / 2))
            for name in (
                "turnout-side wing rail gauge face",
                "turnout-side wing rail outer face",
                "turnout-side wing flare gauge face",
                "turnout-side wing flare outer face",
                "turnout-side check rail gauge face",
                "turnout-side check rail outer face",
            ):
                outer = name.endswith("outer face")
                wing = "wing" in name
                residuals = []
                for x, y in rails[name]:
                    if wing:
                        left = expected["wing_flare_turnout_outer_x"
                                        if outer else "wing_flare_turnout_x"]
                        right = expected["wing_end_turnout_outer_x"
                                         if outer else "wing_end_turnout_x"]
                        fraction = max(0.0, (x - left) / (right - left))
                        running_y = (expected["gauge"]
                                     + (x - expected["fine_point_x"]) / n)
                        rail_angle = k
                    else:
                        start, end = anchors[name]
                        inner = check_outer_in if outer else expected[
                            "check_turnout_flare_in_x"]
                        finish = check_outer_out if outer else expected[
                            "check_turnout_flare_out_x"]
                        fraction = (
                            (inner - x) / (inner - start) if x < inner
                            else (x - finish) / (end - finish)
                            if x > finish else 0.0
                        )
                        radius = expected["curved_stock_radius"]
                        centre = expected["turnout_origin_x"]
                        join = centre + radius * math.sin(k)
                        if x < join:
                            dx = x - centre
                            running_y = expected["turnout_origin_y"] - (
                                radius * radius - dx * dx
                            ) ** 0.5
                            rail_angle = math.asin(dx / radius)
                        else:
                            running_y = (
                                expected["turnout_origin_y"]
                                - radius * math.cos(k) + (x - join) / n
                            )
                            rail_angle = k
                    gap = (expected["flangeway"] + (width if outer else 0)
                           + fraction * expected["flare_length"]
                           * math.sin(flare))
                    wanted = (running_y + (gap if wing else -gap)
                              / math.cos(rail_angle)
                              - expected["gauge"] / 2)
                    residuals.append(abs(y - wanted))
                with self.subTest(size=size, n=n, source_y_path=name):
                    baseline._close(max(residuals), 0)

    def test_specification_frozen_and_context_explicit(self):
        spec = self.specification("C", 10)
        self.assertTrue(dataclasses.is_dataclass(spec))
        self.assertEqual(spec.schema_version, 1)
        self.assertEqual(spec.source_context, CONTEXT)
        fields = self.subject.rea_turnout_dimensions(spec)
        flags = fields["source_context_flags"]
        self.assertEqual(flags, {
            "xing_type_i": 0, "entry_straight_code": 0,
            "half_diamond": False, "plain_track": False, "gaunt": False,
            "retpar_i": 0, "timbers_equalized": False,
            "square_on_angled": False, "equalizing_fixed": False,
            "force_eq": False, "randangle": 0, "ccd_end_adjustments": 0,
            "ftimbspmax_inches": 30,
        })
        self.assertTrue(fields["source_gaps"])
        self.assertEqual(fields["source_specification"], spec.to_record())
        with self.assertRaises(TypeError):
            self.specification("C", 10, track_gauge=25)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            spec.crossing_ratio = 12
        with self.assertRaises((ValueError, TypeError)):
            self.subject.rea_turnout_dimensions({"switch_size": "C"})


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ReaSourceTests)
    )
    print("Frozen source fixture SHA256:", hashlib.sha256(
        FIXTURE.read_bytes()
    ).hexdigest())
    if result.wasSuccessful():
        print(SENTINEL)
    raise SystemExit(0 if result.wasSuccessful() else 1)
