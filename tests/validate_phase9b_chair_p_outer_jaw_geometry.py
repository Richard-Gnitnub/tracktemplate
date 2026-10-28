#!/usr/bin/env python3
"""Check the finite P jaw with invented exact geometry, without a host.

The hand-calculated input is not a prototype or retained source package.
It protects the source face relationships, both closed boundaries and
their proper chair frame; it supplies no physical-fit acceptance.
"""

from collections import Counter
from dataclasses import FrozenInstanceError, fields, replace
from fractions import Fraction
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.domain.chair_p_outer_jaw import (  # noqa: E402
    ChairPOuterJawParameters,
    construct_chair_p_outer_jaw,
)


SENTINEL = "Phase 9B P outer-jaw geometry validation passed"


def synthetic_parameters():
    """Use invented lengths that give hand-checkable rational sections."""
    return ChairPOuterJawParameters(**{
        name: Fraction(value) for name, value in {
            "jaw_top_half_width_mm": 2,
            "jaw_bottom_half_width_mm": 4,
            "jaw_top_depth_mm": 2,
            "jaw_bottom_depth_mm": 6,
            "jaw_top_slope_mm": 1,
            "plinth_thickness_mm": 1,
            "seat_thickness_mm": 3,
            "rail_depth_mm": 20,
            "rail_head_width_mm": 8,
            "rail_foot_width_mm": 10,
            "rail_web_width_mm": 2,
            "rail_web_top_from_top_mm": Fraction(7, 2),
            "rail_web_bottom_from_top_mm": Fraction(25, 2),
            "rail_fish_ratio": 2,
        }.items()
    })


def hand_source_faces():
    """Return 21 hand-calculated polygons in the source rail-top frame.

    Widths at the four spacer levels are 2, 16/7, 26/7 and 4.
    The groove has a one-unit half width, two-unit depth and twelve-unit
    vertical extent at its middle. No product calculation is called.
    """
    p = {
        "a": (2, -9, -1), "b": (Fraction(16, 7), -5, -3),
        "c": (Fraction(26, 7), -5, -13), "d": (4, -9, -15),
        "e": (1, -5, -3), "f": (1, -5, -13),
        "g": (1, -9, -1), "h": (1, -9, -15),
        "i": (0, -7, -2), "j": (0, -7, -14),
        "k": (0, -9, -1), "l": (0, -9, -15),
        "m": (5, -9, -22), "n": (5, -15, -22),
        "o": (2, -11, -2),
    }
    p = {name: tuple(Fraction(value) for value in point)
         for name, point in p.items()}
    p.update({name.upper(): (-point[0], point[1], point[2])
              for name, point in tuple(p.items()) if point[0] != 0})
    orders = (
        "ABCD", "abcd", "adDA", "bcfe", "BCFE",
        "efji", "EFji", "abeg", "ABEG", "eikg", "EikG",
        "dcfh", "DCFH", "fjlh", "FjlH", "AMNO", "amno",
        "aAOo", "mMNn", "amMA", "onNO",
    )
    return tuple(tuple(p[name] for name in order) for order in orders)


def _subtract(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _area_vector(points):
    products = [_cross(a, b) for a, b in
                zip(points, points[1:] + points[:1])]
    return tuple(sum(point[axis] for point in products) for axis in range(3))


def _signed_volume(points, faces):
    return sum(
        _dot(points[ids[0]], _cross(points[ids[index]],
                                  points[ids[index + 1]])) / 6
        for _name, ids in faces for index in range(1, len(ids) - 1)
    )


class POuterJawGeometryTests(unittest.TestCase):
    def setUp(self):
        self.parameters = synthetic_parameters()
        self.geometry = construct_chair_p_outer_jaw(self.parameters)

    def test_hand_coordinates_source_faces_and_nonplanar_partition(self):
        source = hand_source_faces()
        expected_points = {
            (-x, -y - 4, z + 23) for polygon in source for x, y, z in polygon
        }
        actual_points = {tuple(row[1:]) for _role, part in self.geometry.parts
                         for row in part.vertices}
        self.assertEqual(actual_points, expected_points)
        self.assertEqual(tuple(role for role, _part in self.geometry.parts),
                         ("spacer", "body"))
        for role, part in self.geometry.parts:
            points = {row[0]: tuple(row[1:]) for row in part.vertices}
            indices = range(15) if role == "spacer" else range(15, 21)
            self.assertEqual(tuple(name for name, _ids in part.source_faces),
                             tuple(f"{role}-source-{i:02d}" for i in indices))
            for name, ids in part.source_faces:
                index = int(name.rsplit("-", 1)[1])
                polygon = source[index]
                expected = tuple((-x, -y - 4, z + 23)
                                 for x, y, z in polygon)
                self.assertEqual(tuple(points[key] for key in ids), expected)
                observed = [(face, vertices) for face, vertices in part.faces
                            if face == name or face.startswith(name + "-")]
                if index in (15, 16):
                    self.assertEqual(len(observed), 2)
                    self.assertEqual(
                        {frozenset(points[key] for key in vertices)
                         for _face, vertices in observed},
                        {frozenset(expected[:3]),
                         frozenset((expected[0], expected[2], expected[3]))},
                    )
                    self.assertNotEqual(_dot(
                        _cross(_subtract(expected[1], expected[0]),
                               _subtract(expected[2], expected[0])),
                        _subtract(expected[3], expected[0]),
                    ), 0)
                else:
                    self.assertEqual(len(observed), 1)
                    actual = tuple(points[key] for key in observed[0][1])
                    self.assertEqual(
                        tuple(abs(x) for x in _area_vector(actual)),
                        tuple(abs(x) for x in _area_vector(expected)),
                    )
                    self.assertTrue(set(expected).issubset(actual))
        self.assertEqual(tuple(len(part.faces) for _role, part
                               in self.geometry.parts), (15, 8))

    def test_closed_boundaries_planarity_and_exact_volumes(self):
        for _role, part in self.geometry.parts:
            points = {row[0]: tuple(row[1:]) for row in part.vertices}
            uses = Counter((a, b) for _name, ids in part.faces
                           for a, b in zip(ids, ids[1:] + ids[:1]))
            self.assertTrue(all(count == 1 and uses[b, a] == 1
                                for (a, b), count in uses.items()))
            self.assertEqual(len(points) - len(uses) // 2 + len(part.faces), 2)
            for _name, ids in part.faces:
                polygon = tuple(points[key] for key in ids)
                normal = _area_vector(polygon)
                self.assertNotEqual(normal, (0, 0, 0))
                self.assertTrue(all(_dot(normal, _subtract(p, polygon[0])) == 0
                                    for p in polygon))
            self.assertEqual(_signed_volume(points, part.faces),
                             part.volume_mm3)
            self.assertGreater(part.volume_mm3, 0)
        # Without the groove: integral 6*(5-y), y=-9..-5 = 288.
        # Groove: integral (y+7)*(5-y), y=-7..-5 = 64/3.
        self.assertEqual(self.geometry.parts[0][1].volume_mm3,
                         Fraction(800, 3))
        self.assertEqual(self.geometry.volume_mm3,
                         sum(part.volume_mm3 for _role, part
                             in self.geometry.parts))
        self.assertEqual(self.geometry.bounds_mm, (-5, 1, 1, 5, 11, 22))

    def test_scaling_change_back_and_immutable_results(self):
        for factor in (Fraction(1, 1000), Fraction(7, 3), Fraction(10**30)):
            scaled = replace(self.parameters, **{
                field.name: getattr(self.parameters, field.name) * factor
                for field in fields(self.parameters)
                if field.name != "rail_fish_ratio"
            })
            result = construct_chair_p_outer_jaw(scaled)
            self.assertEqual(result.volume_mm3,
                             self.geometry.volume_mm3 * factor**3)
            self.assertEqual(result.bounds_mm,
                             tuple(value * factor for value
                                   in self.geometry.bounds_mm))
            for (_role, part), (_old_role, old) in zip(result.parts,
                                                     self.geometry.parts):
                self.assertEqual(part.faces, old.faces)
                self.assertEqual(part.source_faces, old.source_faces)
                self.assertEqual(part.vertices, tuple(
                    (name, *(value * factor for value in point))
                    for name, *point in old.vertices
                ))
        changed = replace(self.parameters, rail_head_width_mm=Fraction(10))
        translated = construct_chair_p_outer_jaw(changed)
        self.assertEqual(translated.volume_mm3, self.geometry.volume_mm3)
        # Gauge datum moves with the head width; the chair-centred material
        # stays at the same coordinates for this isolated datum change.
        self.assertEqual(
            tuple(part.vertices for _r, part in translated.parts),
            tuple(part.vertices for _r, part in self.geometry.parts),
        )
        self.assertEqual(construct_chair_p_outer_jaw(self.parameters),
                         self.geometry)
        with self.assertRaises(FrozenInstanceError):
            self.geometry.parts = ()
        with self.assertRaises(FrozenInstanceError):
            self.geometry.parts[0][1].faces = ()
        self.assertEqual(self.parameters.source_to_chair(
            (Fraction(2), Fraction(3), Fraction(5))), (-2, -7, 28))

    def test_invalid_types_and_topology_changes_are_refused(self):
        for field in fields(self.parameters):
            for value in (True, 1, 1.0, float("nan"), float("inf"), "1"):
                with self.subTest(field=field.name, value=value):
                    with self.assertRaises(TypeError):
                        replace(self.parameters, **{field.name: value})
            for value in (Fraction(0), Fraction(-1)):
                with self.subTest(field=field.name, value=value):
                    with self.assertRaises(ValueError):
                        replace(self.parameters, **{field.name: value})
        for changes in (
            {"jaw_bottom_half_width_mm": Fraction(2)},
            {"jaw_bottom_depth_mm": Fraction(2)},
            {"rail_web_width_mm": Fraction(10)},
            {"rail_web_bottom_from_top_mm":
             self.parameters.rail_web_top_from_top_mm},
            {"rail_depth_mm": Fraction(12)},
            {"rail_depth_mm": Fraction(13)},
            {"seat_thickness_mm": Fraction(1)},
            {"jaw_top_slope_mm": Fraction(21)},
            {"plinth_thickness_mm": Fraction(9)},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                construct_chair_p_outer_jaw(replace(self.parameters,
                                                  **changes))
        for value in (None, {}, self.geometry):
            with self.assertRaises(TypeError):
                construct_chair_p_outer_jaw(value)
        for point in ((1, 2, 3), (Fraction(1),), "bad", None):
            with self.assertRaises((TypeError, ValueError)):
                self.parameters.source_to_chair(point)
        corrupted = synthetic_parameters()
        object.__setattr__(corrupted, "rail_fish_ratio", Fraction(0))
        with self.assertRaises(ValueError):
            construct_chair_p_outer_jaw(corrupted)
        # The former numerical negative input has a positive web span
        # after correction of the invented fixture's top datum.
        narrow = construct_chair_p_outer_jaw(replace(
            self.parameters, rail_web_bottom_from_top_mm=Fraction(4),
        ))
        self.assertTrue(all(part.volume_mm3 > 0
                            for _role, part in narrow.parts))

    def test_domain_imports_no_host(self):
        self.assertFalse({"FreeCAD", "Part", "FreeCADGui", "PySide", "pivy"}
                         .intersection(sys.modules))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        POuterJawGeometryTests
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
