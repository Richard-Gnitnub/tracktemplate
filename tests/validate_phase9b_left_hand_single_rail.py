#!/usr/bin/env python3
"""Check finite LH single-rail frames against independent source marks.

Source-informed expected values: Templot 556b, GPL-3.0-or-later.
Copyright (C) 2024 Martin Wynne and OpenTemplot contributors.
See NOTICE.md and reference/PROVENANCE.md. No native runtime is used.
The seven frozen frames preceded implementation; they are numerical source
evidence, not independent prototype or physical-fit evidence.
"""

import cmath
from dataclasses import FrozenInstanceError
from fractions import Fraction
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.domain import single_rail_placement as placement  # noqa: E402


# Frozen independent assessment c943c79d1310244b355237be4cc3780eaaf3bf9e4a355
# bd82cedeb9d5f836214. Entries are timber, rail, family, host XY/heading,
# source angle/gauge Y, expected body XY/X-axis, and indexed fixing origins.
FROZEN = (
    ("S13", 2, "L1", (782.4231673258731, 271.41776324438456),
     0.9411728206336331, 0.0471519486871401, 3.8321603999269604,
     (786.3545556698531, 268.54585871571425),
     (-0.5500896263736563, -0.835105623832154),
     ((786.3752426848703, 268.4722456932465),
      (786.2783655037641, 268.53938660180086),
      (786.4379075328544, 268.5626643956123),
      (786.3410303517483, 268.6298053041666))),
    ("S13", 4, "L1", (782.4231673258731, 271.41776324438456),
     0.9411728206336331, 0.04743472383843949, 20.35062988922664,
     (772.2821835341795, 278.8136414631995),
     (0.5498534572645989, 0.8352611421191386),
     ((774.0292114187328, 277.6032261897802),
      (773.931743814854, 277.670755894052),
      (770.1943538128306, 280.26017875396855),
      (770.0968862089517, 280.32770845824035))),
    ("T1", 2, "L1", (787.0918306863207, 277.91410748188457),
     0.954111023120015, 0.05004356801003937, 4.221248823793925,
     (790.7424906271006, 275.3179627536359),
     (-0.536801685063849, -0.8437084513696733),
     ((790.7655674896827, 275.2401601647026),
      (790.6617361684102, 275.3099314503174),
      (790.8306873562565, 275.33706939789016),
      (790.726856034984, 275.406840683505))),
    ("T1", 4, "L1", (787.0918306863207, 277.91410748188457),
     0.954111023120015, 0.0503437129064263, 20.742055541991235,
     (776.536821522889, 285.40490898093447),
     (0.5365484261025186, 0.843869531649834),
     ((778.3040455416262, 284.2177765934457),
      (778.1995810729505, 284.2879505797609),
      (774.4314834478213, 286.8191694193548),
      (774.3270189791455, 286.88934340567))),
    ("T14", 2, "L1", (847.3390056666443, 384.4124347329628),
     1.1548261727687286, 0.09441242237198981, 13.089388883807876,
     (843.3218518958695, 386.1735294662196),
     (-0.31604483242394105, -0.9487442563189108),
     ((843.3967392788577, 386.04003792718856),
      (843.1766574991971, 386.1250867340645),
      (843.4761181652754, 386.24544758820514),
      (843.2560363856147, 386.330496395081))),
    ("T2", 2, "L1", (792.4818152273718, 285.64951105212725),
     0.9704698813696341, 0.05345194303580648, 4.709571514187278,
     (795.7713668462657, 283.3888518236457),
     (-0.5200201169177483, -0.8541540130449844),
     ((795.7975120120806, 283.30621021961645),
      (795.6852826285249, 283.3787171372689),
      (795.8651851352229, 283.4109576442684),
      (795.7529557516672, 283.4834645619209))),
    ("T2", 4, "S1", (792.4818152273718, 285.64951105212725),
     0.9704698813696341, 0.05377256833304834, 21.233312493992784,
     (781.4027975125163, 293.248435453558),
     (0.5197462268089328, 0.8543207007429221),
     ((784.1480542554121, 291.4754585599946),
      (784.0878333973707, 291.5143511663398),
      (777.9598800217261, 295.47198455271337))),
)


def arguments(row):
    """Bind the exact finite source identities to their numerical poses."""
    timber, rail, family, host, heading, angle, gauge = row[:7]
    name = ("curved-switch-and-closure-rail" if rail == 2
            else "turnout-side-stock-rail")
    return dict(
        position_id=f"TO-001:chair:to-001-timber-{timber.lower()}:{name}",
        rail_id="TO-001:rail:" + name, timber_id="TO-001:timber:" + timber,
        host_point_mm=host, travel_heading_rad=heading, base_z_mm=0.8,
        family=family, source_rail_code=rail, source_angle_rad=angle,
        source_gauge_y_mm=gauge,
    )


def source_centres(family):
    """Read the frozen inch relationships as exact model-mm fractions."""
    # chairs_unit.pas:920-935,952-966. Scale is one model mm per 3 inches.
    if family == "L1":
        return ((-Fraction(5, 4), Fraction(7, 12)),
                (Fraction(5, 4), Fraction(7, 12)),
                (-Fraction(5, 4), -Fraction(7, 4)),
                (Fraction(5, 4), -Fraction(7, 4)))
    return ((-Fraction(2, 3), Fraction(7, 6)),
            (Fraction(2, 3), Fraction(7, 6)),
            (Fraction(0), -Fraction(5, 2)))


def expected_source_point(values, source_point, fixing_index=None):
    """Apply LH Pascal insertion marks before native normalisation.

    math_unit.pas:31377-31479,31685-31736 supplies midpoint and centres.
    dxf_unit.pas:11902-11905 supplies the opposite-rail rotation without
    the RH half turn. Fixing heads retain zero local source angle.
    This complex-number path does not consume product frames.
    """
    rail = values["source_rail_code"]
    family = values["family"]
    angle = values["source_angle_rad"]
    turn = cmath.rect(1, angle)
    midpoint = Fraction(7, 12) if family == "L1" else Fraction(2, 3)
    shift = float(midpoint) * math.sin(angle) * (-1 if rail == 2 else 1)
    marks = [complex(shift + x, 0) * turn for x in (-1, 1)]
    insertion = sum(marks) / 2 + complex(0, values["source_gauge_y_mm"])
    point = complex(source_point[0], source_point[1])
    if fixing_index is None:
        direction = (marks[1] - marks[0]) / 2
        if rail == 4:
            direction = -direction
        local = insertion + point * direction
    else:
        cx, cy = map(float, source_centres(family)[fixing_index])
        centre = complex(cx + shift, cy if rail == 2 else -cy) * turn
        local = centre + complex(0, values["source_gauge_y_mm"]) + point
    world = (complex(*values["host_point_mm"])
             + (local - complex(0, 8.25))
             * cmath.rect(1, values["travel_heading_rad"]))
    return (world.real, world.imag,
            source_point[2] + 149 / 60 + values["base_z_mm"])


class LeftHandSingleRailTests(unittest.TestCase):
    def near(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for left, right in zip(actual, expected):
            budget = 128 * sys.float_info.epsilon * max(
                1000, abs(left), abs(right),
            )
            self.assertLessEqual(abs(left - right), budget)

    def place(self, values):
        return placement.place_left_hand_single_rail(**values)

    def test_all_seven_frozen_body_and_indexed_fixing_frames(self):
        for row in FROZEN:
            with self.subTest(timber=row[0], rail=row[1]):
                values = arguments(row)
                result = self.place(values)
                self.assertIs(type(result), placement.SingleRailPlacement)
                self.assertEqual(result.family, row[2])
                self.near(result.origin_mm, (*row[7], 0.8))
                self.near(result.x_axis, row[8])
                self.near(result.y_axis, (-row[8][1], row[8][0]))
                self.assertEqual(len(result.fixing_frames), len(row[9]))
                for fixing, origin in zip(result.fixing_frames, row[9]):
                    self.near(fixing.origin_mm, (*origin, 0.8))
                    self.near(fixing.x_axis,
                              (-math.cos(row[4]), -math.sin(row[4])))
                    self.near(fixing.y_axis,
                              (math.sin(row[4]), -math.cos(row[4])))
                for frame in (result, *result.fixing_frames):
                    for field in ("position_id", "rail_id", "timber_id"):
                        self.assertEqual(getattr(frame, field), values[field])

    def test_body_and_fixing_points_follow_source_insertions(self):
        points = ((0.0, 0.0, 0.0), (0.7, -1.3, -0.4),
                  (-2.1, 1.9, 1.2))
        for row in FROZEN:
            for heading in (0, math.pi, -0.83, 1.47):
                values = arguments(row)
                values.update(host_point_mm=(12.5, -37.25),
                              travel_heading_rad=heading, base_z_mm=-0.2)
                result = self.place(values)
                for point in points:
                    native = (-point[0], -point[1] - 0.45,
                              point[2] + 149 / 60)
                    self.near(result.transform_point(native),
                              expected_source_point(values, point))
                    for index, centre in enumerate(source_centres(row[2])):
                        native_fixing = (
                            -point[0] - float(centre[0]),
                            -point[1] - float(centre[1]) - 0.45,
                            point[2] + 149 / 60,
                        )
                        self.near(
                            result.fixing_frames[index].transform_point(
                                native_fixing,
                            ), expected_source_point(values, point, index),
                        )

    def test_wrong_hand_and_common_fixing_frame_are_detectable(self):
        for row in FROZEN:
            values = arguments(row)
            result = self.place(values)
            right_hand = placement.place_single_rail(**values)
            native = (-0.7, 1.3 - 0.45, 149 / 60)
            self.assertGreater(math.dist(result.transform_point(native),
                                         right_hand.transform_point(native)),
                               0.1)
            cx, cy = map(float, source_centres(row[2])[0])
            # Rail-2 centres coincide; an offset also observes head angle.
            point = (-cx + 3, -cy - 0.45 + 4, 149 / 60)
            self.assertGreater(math.dist(result.transform_point(point),
                                         result.fixing_frames[0].transform_point(
                                             point,
                                         )), 0.1)

    def test_source_midpoint_and_fixing_index_are_not_interchangeable(self):
        for row in FROZEN:
            values = arguments(row)
            result = self.place(values)
            origin = expected_source_point(values, (0, 0, -149 / 60))
            nominal = (complex(*values["host_point_mm"])
                       + complex(0, values["source_gauge_y_mm"] - 8.25)
                       * cmath.rect(1, values["travel_heading_rad"]))
            self.assertGreater(math.dist(origin[:2],
                                         (nominal.real, nominal.imag)), 0.01)
            cx, cy = map(float, source_centres(row[2])[0])
            native = (-cx, -cy - 0.45, 149 / 60)
            self.assertGreater(math.dist(
                result.fixing_frames[0].transform_point(native),
                result.fixing_frames[1].transform_point(native),
            ), 0.01)

    def test_rigid_host_change_and_mounting_height(self):
        for row in FROZEN:
            values = arguments(row)
            result = self.place(values)
            angle, shift, rise = 0.73, complex(-45, 29), 3.75
            rotation = cmath.rect(1, angle)
            host = complex(*values["host_point_mm"]) * rotation + shift
            moved = self.place(dict(
                values, host_point_mm=(host.real, host.imag),
                travel_heading_rad=values["travel_heading_rad"] + angle,
                base_z_mm=values["base_z_mm"] + rise,
            ))
            for before, after in zip((result, *result.fixing_frames),
                                     (moved, *moved.fixing_frames)):
                point = before.transform_point((0.3, -0.8, 0.4))
                expected = complex(*point[:2]) * rotation + shift
                self.near(after.transform_point((0.3, -0.8, 0.4)),
                          (expected.real, expected.imag, point[2] + rise))

    def test_invalid_source_family_rail_and_pose_rejected(self):
        values = arguments(FROZEN[0])
        invalid = {
            "family": (None, "S1J", "P", "l1", []),
            "source_rail_code": (True, False, 1, 3, 2.0, "2", None),
            "source_angle_rad": (0, -0.1, math.pi / 2, math.pi),
            "source_gauge_y_mm": (0, -1),
            "host_point_mm": (None, (), (1,), (1, 2, 3), "12"),
            "position_id": ("", " ", None),
            "rail_id": ("", " ", None),
            "timber_id": ("", " ", None),
        }
        for field, bad_values in invalid.items():
            for value in bad_values:
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        self.place(dict(values, **{field: value}))

    def test_nonfinite_and_nonreal_values_rejected(self):
        values = arguments(FROZEN[0])
        bad = (math.nan, math.inf, -math.inf, True, None, "1", 1j)
        for value in bad:
            for field in ("travel_heading_rad", "base_z_mm",
                          "source_angle_rad", "source_gauge_y_mm"):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        self.place(dict(values, **{field: value}))
            for host in ((value, 1), (1, value)):
                with self.assertRaises(ValueError):
                    self.place(dict(values, host_point_mm=host))

    def test_result_is_immutable_and_preserves_existing_preparation(self):
        result = self.place(arguments(FROZEN[0]))
        self.assertEqual(placement.prepare_single_rail_placements((result,)),
                         (result,))
        with self.assertRaises(FrozenInstanceError):
            result.family = "S1"
        with self.assertRaises(FrozenInstanceError):
            result.fixing_frames[0].origin_mm = (0, 0, 0)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: seven source-qualified left-hand single-rail frames")
