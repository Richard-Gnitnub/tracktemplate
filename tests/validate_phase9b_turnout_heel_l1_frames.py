#!/usr/bin/env python3
"""Check the five LH heel-chair frames against straight source marks.

Source-informed calculations from Templot 556b, GPL-3.0-or-later.
Copyright (C) 2024 Martin Wynne and OpenTemplot contributors.
See NOTICE.md and reference/PROVENANCE.md. No native runtime is used.
These checks give no physical-fit or production acceptance.
"""

import cmath
from fractions import Fraction
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.domain import single_rail_placement as placement  # noqa: E402


# Fixed TO-001 source host samples, retained with the seven curved-rail
# frames in validate_phase9b_left_hand_single_rail.py. Main rails have
# zero source angle; source gauge Y is 0 mm or 16.5 mm.
FROZEN = (
    ("S13", 1, (782.4231673258731, 271.41776324438456),
     0.9411728206336331),
    ("S13", 3, (782.4231673258731, 271.41776324438456),
     0.9411728206336331),
    ("T1", 1, (787.0918306863207, 277.91410748188457),
     0.954111023120015),
    ("T1", 3, (787.0918306863207, 277.91410748188457),
     0.954111023120015),
    ("T2", 3, (792.4818152273718, 285.64951105212725),
     0.9704698813696341),
)

# Independent source review frozen before implementation, SHA-256
# 5f2cb7f0dbaf480890eb00ca68ec67ad087ad6a9a3a0fd0693e1a38bfbaedeae.
# Body XY, body X-axis, and inner/outer-row fixing origins for each row.
EXPECTED = (
    ((789.4549358914437, 266.2948509046843),
     (-0.5888404988161171, -0.8082492604104172),
     ((789.4549358914437, 266.2948509046843),) * 2),
    ((775.3913987603025, 276.5406755840848),
     (0.5888404988161171, 0.8082492604104172),
     ((777.0617805651507, 275.32373855319815),
      (773.2899506832354, 278.07166088100666))),
    ((794.1892901392973, 272.8825998238011),
     (-0.5783342135728109, -0.8157999371237524),
     ((794.1892901392973, 272.8825998238011),) * 2),
    ((779.994371233344, 282.945615139968),
     (0.5783342135728109, 0.8157999371237524),
     ((781.6803577700665, 281.7503910985842),
      (777.8732913968223, 284.4492840952573))),
    ((785.3029993873112, 290.56424432408545),
     (0.5649118703400251, 0.8251512459839921),
     ((787.0083119623447, 289.3967597920494),
      (783.1576061477527, 292.0330151869695))),
)

# chairs_unit.pas:952-966: exact source inches at 4 mm/ft.
CENTRES = (
    (-Fraction(5, 4), Fraction(7, 12)),
    (Fraction(5, 4), Fraction(7, 12)),
    (-Fraction(5, 4), -Fraction(7, 4)),
    (Fraction(5, 4), -Fraction(7, 4)),
)


def arguments(row):
    """Keep the five canonical identities and model-mm source poses."""
    timber, rail, point, heading = row
    name = ("main-side-stock-rail" if rail == 1
            else "straight-switch-and-closure-rail")
    return dict(
        position_id=f"TO-001:chair:to-001-timber-{timber.lower()}:{name}",
        rail_id="TO-001:rail:" + name, timber_id="TO-001:timber:" + timber,
        host_point_mm=point, travel_heading_rad=heading, base_z_mm=0.8,
        family="L1", source_rail_code=rail, source_angle_rad=0.0,
        source_gauge_y_mm=0.0 if rail == 1 else 16.5,
    )


def expected_source_point(values, source_point, fixing_index=None):
    """Apply source insertions without consuming product frame results.

    math_unit.pas:31377-31479,31685-31736 supplies zero midpoint shift
    and indexed fixing centres. dxf_unit.pas:11902-11905 reverses rail 3.
    Source fixing heads keep zero local angle on either rail.
    """
    rail = values["source_rail_code"]
    point = complex(source_point[0], source_point[1])
    if fixing_index is None:
        local = point if rail == 1 else -point + 16.5j
    else:
        x, y = map(float, CENTRES[fixing_index])
        centre = complex(x, y if rail == 1 else 16.5 - y)
        local = centre + point
    world = (complex(*values["host_point_mm"])
             + (local - 8.25j)
             * cmath.rect(1, values["travel_heading_rad"]))
    return (world.real, world.imag,
            source_point[2] + 149 / 60 + values["base_z_mm"])


class TurnoutHeelL1FrameTests(unittest.TestCase):
    def near(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for left, right in zip(actual, expected):
            # Same arithmetic roundoff budget as the retained LH proof.
            budget = 128 * sys.float_info.epsilon * max(
                1000, abs(left), abs(right),
            )
            self.assertLessEqual(abs(left - right), budget)

    def place(self, values):
        return placement.place_left_hand_single_rail(**values)

    def test_independently_frozen_world_frames(self):
        for row, expected in zip(FROZEN, EXPECTED):
            with self.subTest(timber=row[0], rail=row[1]):
                result = self.place(arguments(row))
                self.near(result.origin_mm, (*expected[0], 0.8))
                self.near(result.x_axis, expected[1])
                for index, frame in enumerate(result.fixing_frames):
                    self.near(frame.origin_mm,
                              (*expected[2][index // 2], 0.8))

    def test_five_body_and_indexed_fixing_frames(self):
        for row in FROZEN:
            values = arguments(row)
            with self.subTest(timber=row[0], rail=row[1]):
                result = self.place(values)
                self.assertEqual(result.family, "L1")
                self.assertEqual(len(result.fixing_frames), 4)
                self.near(result.origin_mm, expected_source_point(
                    values, (0, -0.45, -149 / 60),
                ))
                tangent = (math.cos(row[3]), math.sin(row[3]))
                sign = -1 if row[1] == 1 else 1
                self.near(result.x_axis,
                          tuple(sign * value for value in tangent))
                for index, (frame, centre) in enumerate(zip(
                    result.fixing_frames, CENTRES,
                )):
                    self.near(frame.origin_mm, expected_source_point(
                        values, (-float(centre[0]),
                                 -float(centre[1]) - 0.45, -149 / 60),
                        index,
                    ))
                    self.near(frame.x_axis, tuple(-v for v in tangent))
                for frame in (result, *result.fixing_frames):
                    self.near(frame.y_axis,
                              (-frame.x_axis[1], frame.x_axis[0]))
                    for field in ("position_id", "rail_id", "timber_id"):
                        self.assertEqual(getattr(frame, field), values[field])

    def test_source_marks_in_both_travel_directions(self):
        for row in FROZEN:
            for heading in (0, math.pi, -0.83, 1.47):
                values = dict(arguments(row), host_point_mm=(12.5, -37.25),
                              travel_heading_rad=heading, base_z_mm=-0.2)
                result = self.place(values)
                for point in ((0, 0, 0), (0.7, -1.3, -0.4), (-2.1, 1.9, 1.2)):
                    self.near(result.transform_point(
                        (-point[0], -point[1] - 0.45, point[2] + 149 / 60),
                    ), expected_source_point(values, point))
                    for index, centre in enumerate(CENTRES):
                        native = (-point[0] - float(centre[0]),
                                  -point[1] - float(centre[1]) - 0.45,
                                  point[2] + 149 / 60)
                        self.near(result.fixing_frames[index].transform_point(
                            native,
                        ), expected_source_point(values, point, index))

    def test_rigid_host_changes_preserve_all_component_frames(self):
        for row in FROZEN:
            values = arguments(row)
            result = self.place(values)
            rotation, translation = cmath.rect(1, 0.73), complex(-45, 29)
            host = complex(*values["host_point_mm"]) * rotation + translation
            moved = self.place(dict(
                values, host_point_mm=(host.real, host.imag),
                travel_heading_rad=values["travel_heading_rad"] + 0.73,
                base_z_mm=values["base_z_mm"] + 3.75,
            ))
            for before, after in zip((result, *result.fixing_frames),
                                     (moved, *moved.fixing_frames)):
                point = before.transform_point((0.3, -0.8, 0.4))
                target = complex(*point[:2]) * rotation + translation
                self.near(after.transform_point((0.3, -0.8, 0.4)),
                          (target.real, target.imag, point[2] + 3.75))

    def test_wrong_handing_and_rail_three_fixing_rows_are_detectable(self):
        point = (-0.7, 0.85, 149 / 60)
        for row in FROZEN:
            values = arguments(row)
            result = self.place(values)
            wrong = placement.place_single_rail(**values)
            self.assertGreater(math.dist(result.transform_point(point),
                                         wrong.transform_point(point)), 0.1)
            if row[1] == 3:
                self.assertGreater(math.dist(
                    result.fixing_frames[0].transform_point(point),
                    result.fixing_frames[2].transform_point(point),
                ), 0.1)

    def test_exact_straight_source_pose_required(self):
        for row in FROZEN:
            values = arguments(row)
            gauge = values["source_gauge_y_mm"]
            invalid = {
                "source_angle_rad": (-0.1, 0.1, math.nextafter(0, 1)),
                "source_gauge_y_mm": (
                    math.nextafter(gauge, -math.inf),
                    math.nextafter(gauge, math.inf), 16.5 - gauge,
                ),
                "source_rail_code": (True, False, 0, 2, 4, 5, 1.0, "1"),
                "family": ("S1J", "P", None, [], "l1"),
            }
            for field, bad_values in invalid.items():
                for value in bad_values:
                    with self.subTest(row=row[:2], field=field, value=value):
                        with self.assertRaises(ValueError):
                            self.place(dict(values, **{field: value}))

    def test_nonfinite_nonreal_and_boolean_inputs_rejected(self):
        for row in FROZEN:
            values = arguments(row)
            for value in (math.nan, math.inf, -math.inf, True, False,
                          None, "1", 1j):
                for field in ("travel_heading_rad", "base_z_mm",
                              "source_angle_rad", "source_gauge_y_mm"):
                    with self.subTest(row=row[:2], field=field, value=value):
                        with self.assertRaises(ValueError):
                            self.place(dict(values, **{field: value}))
                for host in ((value, 1), (1, value)):
                    with self.assertRaises(ValueError):
                        self.place(dict(values, host_point_mm=host))

    def test_invalid_owners_and_host_coordinates_rejected(self):
        values = arguments(FROZEN[0])
        for field in ("position_id", "rail_id", "timber_id"):
            for value in ("", " ", None):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        self.place(dict(values, **{field: value}))
        for host in (None, (), (1,), (1, 2, 3), "12"):
            with self.assertRaises(ValueError):
                self.place(dict(values, host_point_mm=host))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TurnoutHeelL1FrameTests),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: five source-qualified left-hand L1 heel-chair frames")
