#!/usr/bin/env python3
"""Check independent raw-source P placement and stale-result controls."""

import argparse
import copy
from dataclasses import replace
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from p_curvature_source_oracle import (  # noqa: E402
    assert_recalculated,
    expected_p_frames,
    validate_p_frames,
)

SENTINEL = "Phase 9B P curvature source validation passed"


def source_records(cosine=1.0, sine=0.0, offset=(0.0, 0.0)):
    """Make an independently calculable 3:4:5 rigid-source example."""
    def point(x, y):
        return (offset[0] + cosine * x - sine * y,
                offset[1] + sine * x + cosine * y)

    rail = {
        "stable_identity": "A:stock", "parent_turnout_identity": "A",
        "name": "main-side stock rail", "rail_role": "stock rail",
        "points": [point(-10, 0), point(10, 0)],
        "gauge_face_points": [point(-10, -1), point(10, -1)],
        "outer_face_points": [point(-10, 1), point(10, 1)],
    }
    timber = {
        "stable_identity": "A:S1", "parent_turnout_identity": "A",
        "identifier": "S1", "prototype_reference": "S1",
        "section": "switch", "centre": point(3, 2),
    }
    binding = {"position_id": "P1", "rail_id": "A:stock",
               "timber_id": "A:S1", "parent_id": "A"}
    return [rail], [timber], [binding]


def frames(records):
    return expected_p_frames(*records, base_z_mm=0.8)


def negative_control(kind):
    """Expose a deliberate stale result; the command must exit with FAIL."""
    before = frames(source_records())
    after = frames(source_records(0.6, 0.8, (100.0, -50.0)))
    if kind == "stale-centres":
        actual = (replace(after[0], origin_mm=before[0].origin_mm),)
    elif kind == "stale-axes":
        actual = (replace(after[0], x_axis=before[0].x_axis,
                          y_axis=before[0].y_axis),)
    else:
        return assert_recalculated(before, before)
    return validate_p_frames(actual, after)


class SourceProjectionTests(unittest.TestCase):
    def test_hand_calculated_projection_and_orientation(self):
        for cosine, sine in ((1, 0), (0, 1), (-1, 0), (0, -1), (0.6, 0.8)):
            source = source_records(cosine, sine, (100, -50))
            before = copy.deepcopy(source)
            frame, = frames(source)
            self.assertEqual(source, before)
            expected = replace(
                frame, origin_mm=(100 + 3 * cosine, -50 + 3 * sine, 0.8),
                x_axis=(cosine, sine), y_axis=(-sine, cosine),
            )
            validate_p_frames((frame,), (expected,))
            self.assertEqual(frame.parent_id, "A")

    def test_varied_segment_headings_are_recalculated(self):
        rail, timber, bindings = source_records()
        rail[0].update(
            points=[(0, 0), (10, 0), (10, 10)],
            gauge_face_points=[(0, -1), (11, -1), (11, 10)],
            outer_face_points=[(0, 1), (9, 1), (9, 10)],
        )
        timber[0]["centre"] = (7, 2)
        first, = frames((rail, timber, bindings))
        self.assertEqual(first.origin_mm, (7.0, 0.0, 0.8))
        self.assertEqual(first.x_axis, (1.0, 0.0))
        timber[0]["centre"] = (12, 7)
        second, = frames((rail, timber, bindings))
        self.assertEqual(second.origin_mm, (10.0, 7.0, 0.8))
        self.assertEqual(second.x_axis, (0.0, 1.0))
        self.assertEqual(assert_recalculated((first,), (second,))[
            "changed_axis_ids"], ["P1"])

    def test_equal_minimum_at_shared_vertex_uses_first_source_segment(self):
        rail, timber, bindings = source_records()
        rail[0]["points"] = [(-10, 0), (3, 0), (10, 0)]
        frame, = frames((rail, timber, bindings))
        self.assertEqual(frame.origin_mm[:2], (3.0, 0.0))
        self.assertEqual(
            frame.evidence["projection"]["equal_minimum_segments"], [0, 1],
        )
        self.assertEqual(frame.evidence["projection"]["segment_index"], 0)

    def test_distinct_equidistant_supports_are_not_guessed(self):
        rail, timber, bindings = source_records()
        rail[0]["points"] = [(-10, -1), (10, -1), (10, 1), (-10, 1)]
        timber[0]["centre"] = (0, 0)
        with self.assertRaisesRegex(ValueError, "distinct equal minima"):
            frames((rail, timber, bindings))

    def test_named_face_reversal_and_shared_endpoint(self):
        source = source_records()
        expected = frames(source)
        for key in ("points", "gauge_face_points", "outer_face_points"):
            source[0][0][key].reverse()
        validate_p_frames(frames(source), expected)
        source[0][0]["gauge_face_points"] = [(-10, -1), (3, -1), (10, -1)]
        validate_p_frames(frames(source), expected)

    def test_invalid_geometry_identity_and_assignment_are_refused(self):
        changes = (
            ("rail", "points", [(0, 0), (0, 0)]),
            ("rail", "points", [(0, 0), (math.nan, 1)]),
            ("rail", "gauge_face_points", [(3, -1), (3, 1)]),
            ("rail", "outer_face_points", [(-10, -2), (10, -2)]),
            ("rail", "parent_turnout_identity", "other"),
            ("rail", "rail_role", "check rail"),
            ("timber", "centre", (True, 0)),
            ("timber", "centre", (math.inf, 0)),
            ("timber", "identifier", "S8"),
            ("binding", "rail_id", "absent"),
            ("binding", "parent_id", "other"),
            ("binding", "centre_point", (999, 999)),
        )
        for kind, key, value in changes:
            with self.subTest(kind=kind, key=key):
                source = source_records()
                record_index = {"rail": 0, "timber": 1, "binding": 2}[kind]
                source[record_index][0][key] = value
                with self.assertRaises(ValueError):
                    frames(source)
        for datum in (True, math.nan, math.inf, -math.inf):
            with self.subTest(datum=datum), self.assertRaises(ValueError):
                expected_p_frames(*source_records(), base_z_mm=datum)
        source = source_records()
        source[2].append(dict(source[2][0]))
        with self.assertRaises(ValueError):
            frames(source)

    def test_all_stale_negative_controls_fail(self):
        for kind in ("stale-centres", "stale-axes", "unchanged"):
            with self.subTest(kind=kind), self.assertRaises(AssertionError):
                negative_control(kind)

    def test_nonfinite_or_malformed_observed_frames_cannot_pass(self):
        expected = frames(source_records())
        for name in ("origin_mm", "x_axis", "y_axis"):
            for value in (math.nan, math.inf, True):
                with self.subTest(name=name, value=value):
                    damaged = list(getattr(expected[0], name))
                    damaged[-1] = value
                    actual = (replace(expected[0], **{name: tuple(damaged)}),)
                    with self.assertRaises(AssertionError):
                        validate_p_frames(actual, expected)
        with self.assertRaises(AssertionError):
            validate_p_frames((replace(expected[0], y_axis=(0,)),), expected)

    def test_changed_record_is_bound_to_matching_ids(self):
        before = frames(source_records())
        after = frames(source_records(0.6, 0.8, (100, -50)))
        receipt = assert_recalculated(before, after)
        self.assertEqual(receipt["changed_centre_ids"], ["P1"])
        with self.assertRaises(AssertionError):
            validate_p_frames(before, (replace(before[0], rail_id="other"),))
        with self.assertRaises(AssertionError):
            assert_recalculated(
                before, (replace(after[0], position_id="other"),),
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--negative-control", choices=(
        "stale-centres", "stale-axes", "unchanged",
    ))
    arguments = parser.parse_args()
    if arguments.negative_control:
        negative_control(arguments.negative_control)
        raise AssertionError("The deliberate fault escaped its control")
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)


if __name__ == "__main__":
    main()
