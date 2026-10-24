#!/usr/bin/env python3
"""Check the finite central CC preview boundary without private source data."""

from pathlib import Path
import json
import math
import copy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.compatibility.chair_catalogue_placement import (  # noqa: E402
    preview_private_catalogue_crossover_chairs,
)
from tracktemplate.compatibility import chair_check_placement  # noqa: E402
from validate_phase9b_catalogue_paired_crossover import (  # noqa: E402
    invented_source,
)


def central_source():
    """Use invented stations on the established synthetic pair hosts."""
    module, document, signature, _positions, _timbers, _selections, data = (
        invented_source()
    )
    module.rea_c10_dimensions = lambda *_args: {"a_timber_x": 40.0}
    module._rea_c10_turnout_outer_gauge_point_at_x = (
        lambda _dimensions, x: (x, 10.0, math.atan(0.1))
    )
    positions, timbers = {}, []
    for owner in ("A", "B"):
        for index, timber in enumerate(("X2-Y", "X3-X", "X4-A")):
            timber_id = owner + ":" + timber
            timbers.append({"stable_identity": timber_id,
                            "source_configuration": {"local_x": 20.0 + 10 * index}})
            for side in ("main-side", "turnout-side"):
                for rail in ("stock-rail", "check-rail"):
                    identity = (f"XO-001:chair:xo-001-{owner.lower()}-"
                                f"{timber.lower()}:{side}-{rail}")
                    positions[identity] = {
                        "prototype_timber_identifier": timber,
                        "rail_name": side + " " + rail.replace("-", " "),
                        "parent_turnout_identity": "Owner" + owner,
                        "timber_identity": timber_id,
                        "rail_identity": owner + ":" + side + ":" + rail,
                        "special_assignment_deferred": True,
                    }
    return module, document, signature, positions, timbers, data


def prepare_central(source):
    prepared = SimpleNamespace(model_sha256="invented",
                               context={"context_sha256": "invented"})
    with patch.object(chair_check_placement, "prepare_catalogue_chair",
                      return_value=prepared):
        return chair_check_placement.prepare_central_checks(
            *source[:5], 0.8, "unused",
        )


class CentralCheckBoundaryTests(unittest.TestCase):
    def test_complete_pairing_preserves_source_records_and_detects_late_change(self):
        source = central_source()
        before = json.dumps(source[3:5], sort_keys=True)
        placements, witnesses, companions, verify = prepare_central(source)
        self.assertEqual(len(placements), 12)
        self.assertEqual(len(companions), 12)
        self.assertEqual(set(witnesses), {p.position_id for p in placements})
        self.assertEqual(set(companions.values()), set(witnesses))
        self.assertEqual(set(witnesses) | set(companions), set(source[3]))
        self.assertEqual(before, json.dumps(source[3:5], sort_keys=True))
        with patch.object(chair_check_placement, "verify_catalogue_sources"):
            verify()
            source[-1]["HostB"]["points"][0].x += 1
            with self.assertRaisesRegex(ValueError, "host changed"):
                verify()

    def test_partial_or_altered_source_ownership_is_refused(self):
        for change in ("missing", "owner", "station", "deferred", "extra"):
            with self.subTest(change=change), self.assertRaises(ValueError):
                source = central_source()
                identity = next(iter(source[3]))
                if change == "missing":
                    source[3].pop(identity)
                elif change == "owner":
                    source[3][identity]["parent_turnout_identity"] = "Other"
                elif change == "station":
                    source[4][0]["source_configuration"]["local_x"] += 1
                elif change == "deferred":
                    source[3][identity]["special_assignment_deferred"] = False
                else:
                    source[3]["extra"] = dict(source[3][identity])
                prepare_central(source)

    def test_central_check_option_requires_a_boolean_before_source_access(self):
        for value in (1, 0, None, "yes", (), []):
            with self.subTest(value=value):
                create = Mock()
                with self.assertRaisesRegex(ValueError, "actual Boolean"):
                    preview_private_catalogue_crossover_chairs(
                        object(), object(), "XO-001", "unused", create,
                        paired_contexts_path="unused",
                        include_central_cc=value,
                    )
                create.assert_not_called()

    def test_central_checks_cannot_replace_the_paired_baseline(self):
        create = Mock()
        with self.assertRaisesRegex(ValueError, "paired supplement"):
            preview_private_catalogue_crossover_chairs(
                object(), object(), "XO-001", "unused", create,
                include_central_cc=True,
            )
        create.assert_not_called()


class CentralCheckFrameTests(unittest.TestCase):
    def test_admission_preserves_and_revalidates_all_fixing_frames(self):
        from tracktemplate.domain.central_check_placement import (
            place_central_check,
            prepare_central_check_placements,
        )

        frame = place_central_check(
            "p", "r", "t", (10, 20), 0.3, 0.8, side="TS",
            source_angle_rad=math.atan(0.1), source_gauge_y_mm=32.4,
        )
        copied, = prepare_central_check_placements((frame,))
        self.assertEqual(copied, frame)
        self.assertIsNot(copied, frame)
        for actual, original in zip(copied.fixing_frames, frame.fixing_frames):
            self.assertEqual(actual, original)
            self.assertIsNot(actual, original)
        for values in ((), [frame], (frame, frame)):
            with self.assertRaises(ValueError):
                prepare_central_check_placements(values)
        damaged = copy.deepcopy(frame)
        object.__setattr__(damaged.fixing_frames[0], "x_axis", (2.0, 0.0))
        with self.assertRaises(ValueError):
            prepare_central_check_placements((damaged,))

    def test_invalid_source_pose_is_refused(self):
        from tracktemplate.domain.central_check_placement import (
            place_central_check,
        )

        for side, angle, offset in (("MS", 0.1, 0), ("TS", 0, 20),
                                    ("LH", 0, 0), ("TS", math.nan, 20),
                                    ("MS", 0, math.inf), ("MS", True, 0)):
            with self.subTest(side=side, angle=angle, offset=offset):
                with self.assertRaises(ValueError):
                    place_central_check(
                        "p", "r", "t", (0, 0), 0, 0, side=side,
                        source_angle_rad=angle, source_gauge_y_mm=offset,
                    )

    def test_body_and_fixings_follow_distinct_source_frames(self):
        from tracktemplate.domain.central_check_placement import (
            place_central_check,
        )

        centres = ((-2 / 3, 3.5), (2 / 3, 3.5),
                   (-2 / 3, -2.5), (2 / 3, -2.5))
        primitive = (0.2, 0.3, -1.0)
        for heading in (0.0, math.pi / 2, -0.7):
            tangent = (math.cos(heading), math.sin(heading))
            normal = (-tangent[1], tangent[0])

            def world(point):
                return (100 + point[0] * tangent[0]
                        + (point[1] + 8.25) * normal[0],
                        200 + point[0] * tangent[1]
                        + (point[1] + 8.25) * normal[1],
                        0.8 + point[2] + 149 / 60)

            for side in ("MS", "TS"):
                angle = 0.0 if side == "MS" else math.atan(0.1)
                gauge_y = 0.0 if side == "MS" else 32.46656308246101
                frame = place_central_check(
                    "position", "rail", "timber", (100, 200), heading, 0.8,
                    side=side, source_angle_rad=angle,
                    source_gauge_y_mm=gauge_y,
                )
                c, s = math.cos(angle), math.sin(angle)
                d = -0.5 * s
                anchor = (d * c, -gauge_y - d * s)
                body = ((-primitive[0], -primitive[1], primitive[2])
                        if side == "MS" else
                        (c * primitive[0] + s * primitive[1] + anchor[0],
                         -s * primitive[0] + c * primitive[1] + anchor[1],
                         primitive[2]))
                native = (-primitive[0], -primitive[1] - 0.45,
                          primitive[2] + 149 / 60)
                for actual, expected in zip(frame.transform_point(native),
                                            world(body)):
                    self.assertAlmostEqual(actual, expected, places=12)
                self.assertEqual(len(frame.fixing_frames), 4)
                for (bx, by), fixing in zip(centres, frame.fixing_frames):
                    target = ((bx, -by) if side == "MS" else
                              (c * bx + s * by + anchor[0],
                               -s * bx + c * by + anchor[1]))
                    native = (-primitive[0] - bx,
                              -primitive[1] - by - 0.45,
                              primitive[2] + 149 / 60)
                    expected = world((primitive[0] + target[0],
                                      primitive[1] + target[1], primitive[2]))
                    for actual, wanted in zip(fixing.transform_point(native),
                                              expected):
                        self.assertAlmostEqual(actual, wanted, places=12)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("Phase 9B central check standalone validation passed")
