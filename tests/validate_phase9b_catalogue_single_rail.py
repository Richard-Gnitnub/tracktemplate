#!/usr/bin/env python3
"""Check opt-in single-rail coverage without changing accepted defaults."""

import copy
import inspect
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.compatibility import (  # noqa: E402
    chair_catalogue_placement,
    transition_workflow,
)
import single_rail_source_oracle as oracle  # noqa: E402
from validate_phase9b_catalogue_central_check import central_source  # noqa: E402


def selected_contexts():
    """Only authorised positions; families come from source predicates."""
    for timber, station in oracle.NOMINAL_STATIONS:
        rails = (
            (2, 4)
            if timber in ("S13", "T1", "T2")
            else (2,)
            if timber == "T14"
            else (1, 2, 3, 4)
            if timber == "X9-F"
            else (1, 4)
        )
        for rail in rails:
            family = oracle.selected_family(
                oracle.SOURCE_PARAMETERS, timber, station, rail
            )
            pose = oracle.source_rail_pose(
                oracle.SOURCE_PARAMETERS, station, rail
            )
            yield timber, station, rail, family, pose


def single_source():
    """Invent records with independently derived source rail samples.

    Actual source identities and extended timber conventions are retained.
    The separate native proof compares the real accepted B15 resolvers.
    """
    source = central_source()
    module = source[0]
    geometry = oracle._source_geometry(oracle.SOURCE_PARAMETERS)
    angle = math.atan2(1, 10)
    module.rea_c10_dimensions = lambda *_args: {
        "a_timber_x": oracle.a_timber(oracle.SOURCE_PARAMETERS),
        "gauge": 16.5,
        "k3": angle,
        "inch": 1 / 3,
        "switch_curve_end_x": float(
            geometry["centre_x_mm"]
            + geometry["closure_radius_mm"]
            / (geometry["crossing_ratio"] ** 2 + 1).sqrt()
        ),
    }
    module.rea_c10_timber_layout = lambda *_args: [
        {"identifier": timber, "x": station}
        for timber, station in oracle.NOMINAL_STATIONS
    ]

    def inner(_dimensions, station):
        pose = oracle.source_rail_pose(oracle.SOURCE_PARAMETERS, station, 2)
        return station, pose["y_mm"], pose["k_rad"]

    def outer(_dimensions, station):
        pose = oracle.source_rail_pose(oracle.SOURCE_PARAMETERS, station, 4)
        return station, pose["y_mm"] - 8.25, pose["k_rad"]

    module._rea_c10_inner_gauge_face = inner
    module._rea_c10_turnout_outer_gauge_point_at_x = outer
    module.TURNOUT_ORIENTATION_FACING = "facing"
    module.TURNOUT_ORIENTATION_TRAILING = "trailing"
    configuration = json.loads(source[2])
    positions, timbers = {}, []
    names = {1: "main-side stock rail", 4: "turnout-side stock rail"}
    extended = {
        ("A", "X8-E"): 1,
        ("A", "X9-F"): 2,
        ("B", "X6-C"): 5,
        ("B", "X7-D"): 6,
        ("B", "X8-E"): 7,
        ("B", "X9-F"): 8,
    }
    for owner in ("A", "B"):
        config = configuration["configuration"]
        config["turnout_" + owner.lower() + "_id"] = f"XO-001-{owner}001"
        config["turnout_" + owner.lower() + "_config"]["template_width"] = 54
        for timber, station, rail, _family, _pose in selected_contexts():
            number = extended.get((owner, timber))
            if number is None:
                timber_id = f"XO-001:{owner}:{timber}"
                source_config = {"local_x": station}
            else:
                timber_id = f"XO-001:INHERITED-LONG:{owner}:{number:03d}"
                source_config = {
                    "path_station": station,
                    "extended_source_timber_identity": f"XO-001:{owner}:{timber}",
                }
            if not any(t["stable_identity"] == timber_id for t in timbers):
                timbers.append(
                    {
                        "stable_identity": timber_id,
                        "source_configuration": source_config,
                    }
                )
            name = names.get(rail, "curved switch and closure rail")
            if timber == "X9-F" and rail in (2, 3):
                name = "vee splice rail" if rail == 2 else "vee point rail"
            identity = (
                "XO-001:chair:"
                + timber_id.lower().replace(":", "-")
                + ":"
                + name.replace(" ", "-")
            )
            positions[identity] = {
                "stable_chair_position_identity": identity,
                "prototype_timber_identifier": timber,
                "rail_name": name,
                "parent_turnout_identity": f"XO-001-{owner}001",
                "timber_identity": timber_id,
                "rail_identity": owner + ":" + name,
                "special_assignment_deferred": True,
                "source_configuration": {
                    "timber": copy.deepcopy(source_config)
                },
            }
    return (
        module,
        source[1],
        json.dumps(configuration),
        positions,
        timbers,
        source[-1],
    )


def prepare_singles(source):
    from tracktemplate.compatibility import (
        chair_single_rail_placement as singles,
    )

    def selection(_path, family, **_kwargs):
        return SimpleNamespace(
            label=family,
            model_sha256="invented-" + family,
            context="retained-S1-L1-reference-package",
        )

    with patch.object(
        singles, "prepare_catalogue_chair", side_effect=selection
    ):
        return singles.prepare_single_rails(*source[:5], 0.8, "unused")


class SingleRailBindingTests(unittest.TestCase):
    def test_complete_identity_family_selection_and_late_verification(self):
        from collections import Counter
        from tracktemplate.compatibility import (
            chair_single_rail_placement as singles,
        )

        source = single_source()
        before = json.dumps(source[3:5], sort_keys=True)
        groups, witnesses, verify = prepare_singles(source)
        self.assertEqual(
            {name: len(values) for name, values in groups.items()},
            {"SupplementS1": 14, "SupplementS1J": 4, "L1": 16},
        )
        self.assertEqual(set(witnesses), set(source[3]))
        self.assertEqual(
            Counter(item["family"] for item in witnesses.values()),
            {"S1": 14, "S1J": 4, "L1": 16},
        )
        self.assertEqual(before, json.dumps(source[3:5], sort_keys=True))
        with patch.object(singles, "verify_catalogue_sources"):
            verify()
            source[-1]["HostB"]["points"][0].x += 1
            with self.assertRaisesRegex(ValueError, "host changed"):
                verify()

    def test_incomplete_or_changed_source_is_refused(self):
        for change in (
            "missing",
            "owner",
            "station",
            "deferred",
            "extra",
            "extended-owner",
            "extended-station",
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                source = single_source()
                identity = next(iter(source[3]))
                if change == "missing":
                    source[3].pop(identity)
                elif change == "owner":
                    source[3][identity]["parent_turnout_identity"] = "Other"
                elif change == "station":
                    source[4][0]["source_configuration"]["local_x"] += 1
                elif change == "deferred":
                    source[3][identity]["special_assignment_deferred"] = False
                elif change == "extra":
                    source[3]["extra"] = copy.deepcopy(source[3][identity])
                else:
                    timber = next(
                        t
                        for t in source[4]
                        if "path_station" in t["source_configuration"]
                    )
                    if change == "extended-owner":
                        timber["source_configuration"][
                            "extended_source_timber_identity"
                        ] = "XO-001:E001"
                    else:
                        timber["source_configuration"]["path_station"] += 1
                prepare_singles(source)

    def test_wrong_branch_or_stationary_tangent_is_refused(self):
        for resolver in (
            "_rea_c10_inner_gauge_face",
            "_rea_c10_turnout_outer_gauge_point_at_x",
        ):
            source = single_source()
            original = getattr(source[0], resolver)

            def wrong(dimensions, station):
                x, y, _angle = original(dimensions, station)
                return x, y, dimensions["k3"]

            setattr(source[0], resolver, wrong)
            with (
                self.subTest(resolver=resolver),
                self.assertRaises(ValueError),
            ):
                prepare_singles(source)


class SingleRailMathematicsTests(unittest.TestCase):
    def near(self, actual, expected, scale=1):
        # Finite matrix-sum roundoff, not a fit or railway tolerance.
        budget = (
            128
            * sys.float_info.epsilon
            * max(1, abs(actual), abs(expected), scale)
        )
        self.assertLessEqual(abs(actual - expected), budget)

    def test_source_family_predicates_and_joint_override(self):
        from collections import Counter

        rows = list(selected_contexts())
        self.assertEqual(len(rows), 17)
        self.assertEqual(
            Counter(row[3] for row in rows), {"L1": 8, "S1": 7, "S1J": 2}
        )
        low, high = oracle.joint_window(oracle.SOURCE_PARAMETERS)
        x9 = dict(oracle.NOMINAL_STATIONS)["X9-F"]
        self.assertLess(low, x9)
        self.assertLess(x9, high)
        self.assertEqual(
            oracle.selected_family(
                oracle.SOURCE_PARAMETERS,
                "T2",
                dict(oracle.NOMINAL_STATIONS)["T2"],
                4,
            ),
            "S1",
        )
        for rail in (1, 4):
            for value, expected in (
                (low, "S1"),
                (high, "S1"),
                (math.nextafter(low, high), "S1J"),
                (math.nextafter(high, low), "S1J"),
            ):
                self.assertEqual(
                    oracle.selected_family(
                        oracle.SOURCE_PARAMETERS, "X9-F", value, rail
                    ),
                    expected,
                )

    def test_identified_extended_source_station_and_envelope_rejection(self):
        for owner in ("A", "B"):
            for timber in ("X6-C", "X7-D", "X8-E", "X9-F"):
                expected = dict(oracle.NOMINAL_STATIONS)[timber]
                position = {
                    "prototype_timber_identifier": timber,
                    "parent_turnout_identity": f"XO-001-{owner}001",
                    "source_configuration": {
                        "timber": {
                            "extended_source_timber_identity": f"XO-001:{owner}:{timber}",
                            "path_station": expected,
                        }
                    },
                }
                self.assertEqual(
                    oracle.station_from_position(position), expected
                )
                wrong = copy.deepcopy(position)
                wrong["source_configuration"]["timber"][
                    "extended_source_timber_identity"
                ] = "XO-001:E001"
                with self.assertRaises(ValueError):
                    oracle.station_from_position(wrong)
                envelope = copy.deepcopy(position)
                envelope["prototype_timber_identifier"] = "E001"
                with self.assertRaises(ValueError):
                    oracle.station_from_position(envelope)

    def test_source_fixing_index_and_gauge_datum_are_not_interchangeable(self):
        for family in ("S1", "S1J", "L1"):
            for rail, gauge in ((1, 0), (3, 16.5)):
                frames = oracle.local_frames(family, rail, 0, gauge)
                self.near(frames["body"][0][3], 0)
                self.near(frames["body"][1][3], 0.45 if rail == 1 else -16.95)
                centres = oracle.dimensions(family)["fixing_centres_mm"]
                for (cx, cy), frame in zip(centres, frames["fixings"]):
                    native = (-cx, -cy - 0.45)
                    target = tuple(
                        sum(frame[axis][j] * native[j] for j in (0, 1))
                        + frame[axis][3]
                        for axis in (0, 1)
                    )
                    self.near(target[0], cx)
                    self.near(target[1], -cy if rail == 1 else cy - gauge)
                # A common body transform swaps source fixing indices.
                cx, cy = centres[0]
                common_x = frames["body"][0][0] * -cx + frames["body"][0][
                    1
                ] * (-cy - 0.45)
                if rail == 1:
                    self.assertNotEqual(common_x, cx)

    def test_all_body_and_fixing_frames_against_source_marks(self):
        from tracktemplate.domain.single_rail_placement import (
            place_single_rail,
        )

        # Both travel directions and supported signed host curvatures.
        for timber, station, rail, family, pose in selected_contexts():
            expected = oracle.local_frames(
                family, rail, pose["k_rad"], pose["y_mm"]
            )
            for radius in (None, 600, 900, 1800, -600, -900, -1800):
                for direction in (-1, 1):
                    chainage = 500 + direction * station
                    angle = 0.0 if radius is None else chainage / radius
                    point = (
                        (chainage, 0)
                        if radius is None
                        else (
                            radius * math.sin(angle),
                            radius * (1 - math.cos(angle)),
                        )
                    )
                    heading = angle + (math.pi if direction == -1 else 0)
                    frame = place_single_rail(
                        "owner",
                        "rail",
                        timber,
                        point,
                        heading,
                        0.8,
                        family=family,
                        source_rail_code=rail,
                        source_angle_rad=pose["k_rad"],
                        source_gauge_y_mm=pose["y_mm"],
                    )
                    self.assertEqual(frame.family, family)
                    actual = (frame, *frame.fixing_frames)
                    matrices = (expected["body"], *expected["fixings"])
                    self.assertEqual(len(actual), len(matrices))
                    c, s = math.cos(heading), math.sin(heading)
                    gauge_origin = (point[0] - 8.25 * s, point[1] + 8.25 * c)
                    for placed, matrix in zip(actual, matrices):
                        self.assertEqual(placed.position_id, "owner")
                        self.assertEqual(placed.rail_id, "rail")
                        self.assertEqual(placed.timber_id, timber)
                        for field, column, translate in (
                            ("origin_mm", 3, True),
                            ("x_axis", 0, False),
                            ("y_axis", 1, False),
                        ):
                            vector = getattr(placed, field)
                            x, y = matrix[0][column], matrix[1][column]
                            self.near(
                                vector[0],
                                c * x
                                - s * y
                                + (gauge_origin[0] if translate else 0),
                                1000,
                            )
                            self.near(
                                vector[1],
                                s * x
                                + c * y
                                + (gauge_origin[1] if translate else 0),
                                1000,
                            )
                        self.near(placed.origin_mm[2], 0.8)
                        self.near(
                            placed.x_axis[0] * placed.y_axis[1]
                            - placed.x_axis[1] * placed.y_axis[0],
                            1,
                        )

    def test_source_branch_join_and_shifted_midpoint_counterexample(self):
        values = oracle._source_geometry(oracle.SOURCE_PARAMETERS)
        for rail, radius_key in (
            (2, "closure_radius_mm"),
            (4, "stock_radius_mm"),
        ):
            join = float(
                values["centre_x_mm"]
                + values[radius_key]
                / (values["crossing_ratio"] ** 2 + 1).sqrt()
            )
            poses = [
                oracle.source_rail_pose(oracle.SOURCE_PARAMETERS, x, rail)
                for x in (
                    math.nextafter(join, -math.inf),
                    join,
                    math.nextafter(join, math.inf),
                )
            ]
            self.assertEqual(
                [p["source_branch"] for p in poses],
                ["radcurve", "turnoutst_main", "turnoutst_main"],
            )
            self.near(
                poses[0]["y_mm"], poses[1]["y_mm"], float(values[radius_key])
            )
            self.near(
                poses[2]["y_mm"], poses[1]["y_mm"], float(values[radius_key])
            )
        station = dict(oracle.NOMINAL_STATIONS)["S13"]
        pose = oracle.source_rail_pose(oracle.SOURCE_PARAMETERS, station, 2)
        frames = oracle.local_frames("L1", 2, pose["k_rad"], pose["y_mm"])
        shifted = oracle.source_rail_pose(
            oracle.SOURCE_PARAMETERS, station + frames["midpoint_delta_mm"], 2
        )
        self.assertNotEqual(shifted["k_rad"], pose["k_rad"])
        self.assertNotEqual(
            frames["body"],
            oracle.local_frames("L1", 2, shifted["k_rad"], shifted["y_mm"])[
                "body"
            ],
        )
        self.assertNotEqual(frames["source_anchor_mm"][0], 0)

    def test_invalid_frames_and_forged_nested_identity_are_refused(self):
        from tracktemplate.domain.single_rail_placement import (
            place_single_rail,
            prepare_single_rail_placements,
        )

        arguments = {
            "family": "L1",
            "source_rail_code": 2,
            "source_angle_rad": 0.05,
            "source_gauge_y_mm": 4.0,
        }
        for key, value in (
            ("family", "CC"),
            ("source_rail_code", 0),
            ("source_rail_code", True),
            ("source_angle_rad", math.nan),
            ("source_angle_rad", math.pi / 2),
            ("source_angle_rad", -0.01),
            ("source_gauge_y_mm", math.inf),
            ("source_gauge_y_mm", True),
        ):
            with (
                self.subTest(key=key, value=value),
                self.assertRaises(ValueError),
            ):
                place_single_rail(
                    "p",
                    "r",
                    "t",
                    (0, 0),
                    0,
                    0.8,
                    **dict(arguments, **{key: value}),
                )
        for value in (math.nan, math.inf, -math.inf, True):
            for field in ("point", "heading", "base"):
                with (
                    self.subTest(value=value, field=field),
                    self.assertRaises(ValueError),
                ):
                    place_single_rail(
                        "p",
                        "r",
                        "t",
                        (value, 0) if field == "point" else (0, 0),
                        value if field == "heading" else 0,
                        value if field == "base" else 0.8,
                        **arguments,
                    )
        frame = place_single_rail("p", "r", "t", (0, 0), 0, 0.8, **arguments)
        self.assertEqual(prepare_single_rail_placements((frame,)), (frame,))
        with self.assertRaises(ValueError):
            prepare_single_rail_placements((frame, frame))
        forged = copy.deepcopy(frame)
        object.__setattr__(forged.fixing_frames[0], "position_id", "other")
        with self.assertRaises(ValueError):
            prepare_single_rail_placements((forged,))


class SingleRailOptionTests(unittest.TestCase):
    def test_session_preserves_default_and_forwards_explicit_option(self):
        method = transition_workflow.ModularCoreLayoutWorkflowSession.preview_private_catalogue_crossover_chairs
        self.assertIs(
            inspect.signature(method)
            .parameters["include_single_rail"]
            .default,
            False,
        )
        session = SimpleNamespace(
            module=object(),
            _private_catalogue_crossover_preview_factory=object(),
            routing_record=Mock(),
        )
        operation = Mock(return_value="receipt")
        with patch.object(
            chair_catalogue_placement,
            "preview_private_catalogue_crossover_chairs",
            operation,
        ):
            result = method(
                session,
                "document",
                "XO-001",
                "catalogue",
                paired_contexts_path="supplement",
                include_central_cc=True,
                include_check_ends=True,
                include_single_rail=True,
            )
        self.assertEqual(result, "receipt")
        operation.assert_called_once_with(
            session.module,
            "document",
            "XO-001",
            "catalogue",
            session._private_catalogue_crossover_preview_factory,
            paired_contexts_path="supplement",
            include_central_cc=True,
            include_check_ends=True,
            include_single_rail=True,
        )

    def test_option_rejects_non_boolean_before_source_access(self):
        operation = chair_catalogue_placement.preview_private_catalogue_crossover_chairs
        self.assertIs(
            inspect.signature(operation)
            .parameters["include_single_rail"]
            .default,
            False,
        )
        for value in (1, 0, None, "yes", (), []):
            with self.subTest(value=value):
                create = Mock()
                with self.assertRaisesRegex(ValueError, "actual Boolean"):
                    operation(
                        object(),
                        object(),
                        "XO-001",
                        "unused",
                        create,
                        include_single_rail=value,
                    )
                create.assert_not_called()

    def test_option_requires_every_existing_supplement(self):
        complete = {
            "paired_contexts_path": "unused",
            "include_central_cc": True,
            "include_check_ends": True,
        }
        operation = chair_catalogue_placement.preview_private_catalogue_crossover_chairs
        for missing in complete:
            with self.subTest(missing=missing):
                options = {k: v for k, v in complete.items() if k != missing}
                create = Mock()
                with self.assertRaisesRegex(ValueError, "requires"):
                    operation(
                        object(),
                        object(),
                        "XO-001",
                        "unused",
                        create,
                        include_single_rail=True,
                        **options,
                    )
                create.assert_not_called()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(
        sys.modules[__name__]
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: single-rail catalogue source placement")
