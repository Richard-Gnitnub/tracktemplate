#!/usr/bin/env python3
"""Independent source arithmetic for the REA B straight closure branch.

Source-informed equations: Templot 556b, Martin Wynne and OpenTemplot
contributors, GPL-3.0-or-later. No Pascal or FreeCAD execution is required.
The retained Phase 1 absolute arithmetic budget is not a fit tolerance.
"""

from decimal import Decimal, localcontext
import math
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate.domain import rea_turnout as source  # noqa: E402
from validate_phase1_turnout import _close  # noqa: E402


HEEL_N = 18.417941404842995


def independent_line(ratio=HEEL_N):
    """Derive mm values from literal source inches using Decimal algebra."""
    with localcontext() as context:
        context.prec = 70
        d = Decimal
        inch = d(1) / 3
        norm = d(1025).sqrt()
        sin1, cos1 = 1 / norm, 32 / norm
        planing = 88 * inch * cos1
        heel, radius = 257 * inch, 7356 * inch
        sin2 = (heel - planing) / radius + sin1
        cos2 = (1 - sin2 * sin2).sqrt()
        offset = planing / 32 + radius * (cos1 - cos2)
        n = d.from_float(float(ratio))
        entry = 2 * n
        span = (d("14.5") - offset) * n
        return {key: float(value) for key, value in {
            "planing_x": planing, "heel_lead": heel,
            "heel_offset": offset, "switch_radius": radius,
            "entry_straight": entry, "turnout_curve_length": span,
            "switch_curve_end_x": heel + span,
            "fine_point_x": heel + span + entry,
            "curve_end_offset": d("14.5"),
        }.items()}


def expected_inner(x, ratio=HEEL_N):
    values = independent_line(ratio)
    return x, (values["heel_offset"]
               + (x - values["heel_lead"]) / ratio), math.atan(1 / ratio)


class StraightSourceTests(unittest.TestCase):
    def dimensions(self, ratio=HEEL_N):
        return source.rea_turnout_dimensions(
            source.ReaTurnoutSpecification("B", ratio),
        )

    def test_source_line_dimensions_on_both_sides_of_heel(self):
        for ratio in (HEEL_N - 1e-10, HEEL_N, HEEL_N + 1e-10):
            with self.subTest(ratio=ratio):
                actual = self.dimensions(ratio)
                self.assertEqual(actual["source_closure_kind"], "line")
                self.assertFalse(actual["auto_fit_cap"])
                for name, value in independent_line(ratio).items():
                    _close(actual[name], value)
                self.assertEqual(actual["turnout_radius"], 99995008.25)
                self.assertEqual(actual["turnout_origin_x"], 0.0)
                self.assertEqual(actual["turnout_origin_y"], 0.0)
                self.assertEqual(actual["check_turnout_working_mode"],
                                 "straight crossing leg")

    def test_source_angle_band_is_distinct_from_denominator_cap(self):
        below = self.dimensions(18.417941403843)
        self.assertNotIn("source_closure_kind", below)
        self.assertTrue(below["auto_fit_cap"])
        self.assertEqual(below["turnout_radius"], below["switch_radius"])
        self.assertGreater(below["turnout_curve_length"], 0)
        for size, ratio in (("B", 18.417941405843), ("B", 3.999),
                            ("B", 20.125), ("C", 22.70237204880366)):
            with self.subTest(size=size, ratio=ratio):
                with self.assertRaises(source.ReaTurnoutError):
                    source.rea_turnout_dimensions(
                        source.ReaTurnoutSpecification(size, ratio),
                    )

    def test_line_point_and_actual_x_stock_faces(self):
        dims = self.dimensions()
        for x in (dims["heel_lead"], 100, dims["switch_curve_end_x"],
                  dims["fine_point_x"], dims["module_end_x"]):
            actual = source.rea_turnout_straight_point(dims, x)
            for found, expected in zip(actual, expected_inner(x)):
                _close(found, expected)
        for bad in (math.nan, math.inf, -math.inf, True, "100", 10 ** 400):
            with self.subTest(bad=bad):
                with self.assertRaises(source.ReaTurnoutError):
                    source.rea_turnout_straight_point(dims, bad)

    def test_marker_is_not_a_radius_heuristic_or_unchecked_override(self):
        dims = self.dimensions()
        for key, value in (("source_closure_kind", "circle"),
                           ("source_status", "accepted"),
                           ("turnout_origin_y", 1.0),
                           ("k3", 0.1), ("heel_offset", 0.0),
                           ("source_specification", {})):
            corrupted = dict(dims, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                source.rea_turnout_straight_point(corrupted, 100.0)
        missing = dict(dims)
        missing.pop("source_closure_kind")
        with self.assertRaises(ValueError):
            source.rea_turnout_straight_point(missing, 100.0)

    def test_all_six_source_wing_check_paths_use_actual_x_line(self):
        dims = self.dimensions()
        k = math.atan(1 / HEEL_N)
        width = 11 / 12
        flare = math.asin((1.75 / 3) / 12)
        for kind in ("wing", "check"):
            for outer in (False, True):
                suffix = "outer_" if outer else ""
                if kind == "wing":
                    a = dims["wing_flare_turnout_" + suffix + "x"]
                    b = dims["wing_end_turnout_" + suffix + "x"]
                    probes = ((a - 1, 0), (a, 0),
                              ((a + b) / 2, 0.5), (b, 1))
                else:
                    prefix = "check_turnout_" + suffix
                    a, b, c, end = (dims[prefix + name] for name in
                                   ("start_x", "flare_in_x",
                                    "flare_out_x", "end_x"))
                    probes = ((a, 1), ((a + b) / 2, 0.5), (b, 0),
                              (c, 0), ((c + end) / 2, 0.5), (end, 1))
                for x, fraction in probes:
                    running = expected_inner(x)[1]
                    if kind == "check":
                        running += 16.5 / math.cos(k)
                    offset = (1 + (width if outer else 0)
                              + fraction * 12 * math.sin(flare))
                    expected = running + (
                        1 if kind == "wing" else -1
                    ) * offset / math.cos(k) - 8.25
                    actual = source.rea_turnout_source_rail_point(
                        dims, x, kind, outer,
                    )
                    _close(actual[0], x)
                    _close(actual[1], expected)

    def test_straight_check_anchors_are_independently_linear(self):
        dims = self.dimensions()
        fine = independent_line()["fine_point_x"]
        k = math.atan(1 / HEEL_N)
        flare = math.asin((1.75 / 3) / 12)
        blunt = fine + (0.125 / math.sin(k / 2))
        a_timber = blunt + 4 / 3
        check_fp = fine - 15.5 * math.sin(k)
        after = (a_timber - check_fp) / math.cos(k) + 26 - 12
        before = 72 - after - 24
        inner = check_fp - before * math.cos(k)
        start = inner - 12 / math.cos(flare) * math.cos(k + flare)
        out = check_fp + after * math.cos(k)
        end = out + 12 / math.cos(flare) * math.cos(k - flare)
        expected = (start, inner, out, end)
        bend = (11 / 12) / math.cos(flare / 2)
        shifts = ((11 / 12) * math.sin(k + flare),
                  bend * math.sin(k + flare / 2),
                  bend * math.sin(k - flare / 2),
                  (11 / 12) * math.sin(k - flare))
        for index, key in enumerate(("start_x", "flare_in_x",
                                     "flare_out_x", "end_x")):
            _close(dims["check_turnout_" + key], expected[index])
            _close(dims["check_turnout_outer_" + key],
                   expected[index] + shifts[index])

    def test_source_invalid_circle_placeholders_are_not_geometry(self):
        # Independent source audit356a, math_unit3365-3371 and4355-4439:
        # csradius=0, so the unused check radii are fw and flare_end_gap.
        dims = self.dimensions()
        self.assertEqual(dims["curved_stock_radius"], 0.0)
        self.assertEqual(dims["check_turnout_radius"], 1.0)
        _close(dims["check_turnout_flare_radius"], 19 / 12)
        for x in (100, 150, 200, 300):
            self.assertEqual(source.rea_turnout_straight_point(dims, x)[0], x)

    def test_independent_45_timber_roster_and_selected_exit(self):
        # Independent90-digit audit50a1f7d9: 14fixed+18closure+13crossing.
        # Expected spacing below starts from the literal switch schedule;
        # it consumes no product dimension or station as its oracle.
        intervals = (3.5, 28, 28, 28, 28, 28, 28, 28.5, 28.5,
                     28.5, 26, 24)
        for ratio in (HEEL_N - 1e-10, HEEL_N, HEEL_N + 1e-10):
            spec = source.ReaTurnoutSpecification("B", ratio)
            k = math.atan(1 / ratio)
            fine = independent_line(ratio)["fine_point_x"]
            blunt = fine + 0.125 / math.sin(k / 2)
            a_timber = blunt + 4 / 3
            first_crossing = a_timber - 50
            fixed = [("J2", -17.5), ("J1", -24.5 / 3)]
            station = 0.0
            for index, interval in enumerate(intervals, 1):
                station += interval / 3
                fixed.append(("T1" if index == 12 else "S" + str(index),
                              station))
            closure = [("T" + str(index + 1), station + index * (
                first_crossing - 25 / 3 - station) / 18)
                       for index in range(1, 19)]
            suffixes = ("", "", "Z", "Y", "X", "A", "B", "C", "D",
                        "", "", "", "")
            crossing = [("X" + str(index + 1) + ("-" + suffix if suffix else ""),
                         first_crossing + 10 * index)
                        for index, suffix in enumerate(suffixes)]
            expected = fixed + closure + crossing
            actual = source.rea_turnout_timber_stations(spec)
            self.assertEqual(len(actual), 45)
            for index, (row, (identifier, x)) in enumerate(zip(actual, expected), 1):
                self.assertEqual(row["identifier"], identifier)
                self.assertEqual(row["sequence"], index)
                _close(row["x"], x)
                _close(row["width"], 4)
                self.assertEqual(row["angle_radians"], 0)
            exits = source.rea_turnout_exit_sleepers(
                spec, source.ReaExitSleeperProfile(
                    "templot-556b-00-D0GAF-32mm-full-exit",
                ),
            )
            for row, offset in zip(exits, (12, 38.5)):
                _close(row["x"], blunt + 75.5 + offset / 3)
                self.assertEqual((row["near_y"], row["far_y"]), (-16, 16))
                _close(row["width"], 10 / 3)

    def test_binary64_source_predicate_adjacent_float_boundaries(self):
        # Independent90-digit audit50a1f7d9 separately records the exact
        # algebraic band. These are its binary64-trig transition witnesses,
        # not a claim of Pascal Extended execution or a widened epsilon.
        lower_out = float.fromhex("0x1.26afe3537fbd6p+4")
        lower_in = float.fromhex("0x1.26afe3537fbd7p+4")
        upper_in = float.fromhex("0x1.26afe353ae7fdp+4")
        upper_out = float.fromhex("0x1.26afe353ae7fep+4")
        self.assertEqual(math.nextafter(lower_out, math.inf), lower_in)
        self.assertEqual(math.nextafter(upper_in, math.inf), upper_out)
        self.assertNotIn("source_closure_kind", self.dimensions(lower_out))
        for ratio in (lower_in, upper_in):
            self.assertEqual(self.dimensions(ratio)["source_closure_kind"], "line")
        with self.assertRaises(source.ReaTurnoutError):
            self.dimensions(upper_out)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(StraightSourceTests),
    )
    if result.wasSuccessful() and not result.skipped:
        print("REA B straight closure source arithmetic passed")
    raise SystemExit(not result.wasSuccessful() or bool(result.skipped))
