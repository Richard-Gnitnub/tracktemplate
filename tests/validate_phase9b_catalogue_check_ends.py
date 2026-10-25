#!/usr/bin/env python3
"""Test check-end ownership and proper component frames without private data."""

import cmath
import copy
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.compatibility.chair_catalogue_placement import (  # noqa: E402
    preview_private_catalogue_crossover_chairs,
)
from tracktemplate.domain.check_end_placement import (  # noqa: E402
    CheckEndPlacement,
    place_check_end,
    prepare_check_end_placements,
)
from tracktemplate.domain import alignment, crossover  # noqa: E402
from check_end_source_oracle import (  # noqa: E402
    source_rail_geometry,
    source_rail_pose,
    source_check_selection,
)
from validate_phase9b_catalogue_central_check import central_source  # noqa: E402


SOURCE_PARAMETERS = {
    "scale_mm_per_inch": 1 / 3, "gauge_mm": 16.5,
    "flangeway_mm": 1.0, "crossing_ratio": 10,
    "switch": {"planing": 110, "heel_lead_inches": 329,
               "planing_angle": 40, "switch_radius_inchormax": 11520},
}
# Permanent fixed XO-001 regression stations; model mm, not fit limits.
END_STATIONS = (("X1-Z", 257.23290043721454),
                ("X5-B", 297.23290043721454))


def end_source():
    """Use actual source poses on disposable synthetic A/B hosts.

    The independent direct circle/line oracle replaces the former constant
    crossing-angle mock. Native proof uses the accepted product resolver.
    """
    source = central_source()
    module = source[0]
    geometry = source_rail_geometry(SOURCE_PARAMETERS)
    crossing_angle = float(geometry["crossing_angle_rad"])
    module.rea_c10_dimensions = lambda *_args: {
        "a_timber_x": END_STATIONS[0][1] + 30,
        "gauge": 16.5, "k3": crossing_angle,
        "switch_curve_end_x": (
            float(geometry["curve_end_station_mm"])
            + 16.5 * math.sin(crossing_angle)
        ),
    }

    def source_point(_dimensions, station):
        pose = source_rail_pose(SOURCE_PARAMETERS, station, "TS")
        return station, pose["y_mm"] - 8.25, pose["k_rad"]

    module._rea_c10_turnout_outer_gauge_point_at_x = source_point
    module.TURNOUT_ORIENTATION_FACING = "facing"
    module.TURNOUT_ORIENTATION_TRAILING = "trailing"
    positions, timbers = {}, []
    for owner in ("A", "B"):
        for timber, station in END_STATIONS:
            timber_id = owner + ":" + timber
            timbers.append({
                "stable_identity": timber_id,
                "source_configuration": {"local_x": station},
            })
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
    return (*source[:3], positions, timbers, source[-1])


def prepare_ends(source):
    from tracktemplate.compatibility import chair_check_end_placement as ends

    def selection(_path, family, **_kwargs):
        return SimpleNamespace(
            label=family, model_sha256="invented-" + family,
            context={"context_sha256": "invented"},
        )

    with patch.object(ends, "prepare_catalogue_chair", side_effect=selection):
        return ends.prepare_check_ends(*source[:5], 0.8, "unused")


class CheckEndBoundaryTests(unittest.TestCase):
    def test_old_straight_pose_is_refused_at_curved_source_station(self):
        source = end_source()
        source[0]._rea_c10_turnout_outer_gauge_point_at_x = (
            lambda _dimensions, x: (x, 10.0, math.atan(0.1))
        )
        with self.assertRaisesRegex(ValueError, "source branch"):
            prepare_ends(source)

    def test_session_forwards_only_explicit_check_end_option(self):
        from tracktemplate.compatibility import (
            chair_catalogue_placement,
            transition_workflow,
        )

        session = SimpleNamespace(
            module=object(), _private_catalogue_crossover_preview_factory=object(),
            routing_record=Mock(),
        )
        operation = Mock(return_value="receipt")
        with patch.object(chair_catalogue_placement,
                          "preview_private_catalogue_crossover_chairs", operation):
            session_type = transition_workflow.ModularCoreLayoutWorkflowSession
            session_type.preview_private_catalogue_crossover_chairs(
                session, "document", "XO-001", "catalogue",
                paired_contexts_path="supplement", include_central_cc=True,
                include_check_ends=True,
            )
        operation.assert_called_once_with(
            session.module, "document", "XO-001", "catalogue",
            session._private_catalogue_crossover_preview_factory,
            paired_contexts_path="supplement", include_central_cc=True,
            include_check_ends=True,
        )

    def test_complete_source_pairing_and_late_verification(self):
        from tracktemplate.compatibility import chair_check_end_placement as ends

        source = end_source()
        before = json.dumps(source[3:5], sort_keys=True)
        groups, witnesses, companions, verify = prepare_ends(source)
        self.assertEqual({k: len(v) for k, v in groups.items()},
                         {"CCL": 4, "CCR": 4})
        ids = {p.position_id for group in groups.values() for p in group}
        self.assertEqual(set(witnesses), ids)
        self.assertEqual(set(companions.values()), ids)
        self.assertEqual(len(companions), 8)
        self.assertEqual(ids | set(companions), set(source[3]))
        for identity, witness in witnesses.items():
            working = "x1-z" in identity
            main = "main-side" in identity
            expected = "CCR" if working == main else "CCL"
            self.assertEqual(witness["family"], expected)
        self.assertEqual(before, json.dumps(source[3:5], sort_keys=True))
        with patch.object(ends, "verify_catalogue_sources"):
            verify()
            source[-1]["HostB"]["points"][0].x += 1
            with self.assertRaisesRegex(ValueError, "host changed"):
                verify()

    def test_incomplete_or_changed_source_is_refused(self):
        for change in ("missing", "owner", "station", "deferred", "extra"):
            with self.subTest(change=change), self.assertRaises(ValueError):
                source = end_source()
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
                    source[3]["extra"] = copy.deepcopy(source[3][identity])
                prepare_ends(source)

    def test_invalid_orientation_and_outside_host_are_refused(self):
        for value in ("unknown", None, 1):
            source = end_source()
            payload = json.loads(source[2])
            payload["configuration"]["turnout_a_config"]["orientation"] = value
            changed = (*source[:2], json.dumps(payload), *source[3:])
            with self.subTest(value=value), self.assertRaises(ValueError):
                prepare_ends(changed)
        for toe in (-1000.0, 1000.0, math.nan, math.inf):
            source = end_source()
            payload = json.loads(source[2])
            payload["configuration"]["turnout_a_config"]["toe_chainage"] = toe
            changed = (*source[:2], json.dumps(payload), *source[3:])
            with self.subTest(toe=toe), self.assertRaises(ValueError):
                prepare_ends(changed)

    def test_option_refuses_invalid_values_before_source_access(self):
        for value in (1, 0, None, "yes", (), []):
            with self.subTest(value=value):
                create = Mock()
                with self.assertRaisesRegex(ValueError, "actual Boolean"):
                    preview_private_catalogue_crossover_chairs(
                        object(), object(), "XO-001", "unused", create,
                        include_check_ends=value,
                    )
                create.assert_not_called()

    def test_option_requires_complete_existing_preview(self):
        for options in ({}, {"paired_contexts_path": "unused"},
                        {"include_central_cc": True}):
            with self.subTest(options=options):
                create = Mock()
                with self.assertRaisesRegex(ValueError, "requires"):
                    preview_private_catalogue_crossover_chairs(
                        object(), object(), "XO-001", "unused", create,
                        include_check_ends=True, **options,
                    )
                create.assert_not_called()


class CheckEndFrameTests(unittest.TestCase):
    def test_unsupported_or_nonfinite_source_pose_is_refused(self):
        arguments = dict(side="TS", family="CCL",
                         source_angle_rad=math.atan(0.1),
                         source_gauge_y_mm=30.0)
        for key, value in (("side", "other"), ("family", "CC"),
                           ("source_angle_rad", 0.0),
                           ("source_angle_rad", -0.01),
                           ("source_angle_rad", math.pi / 2),
                           ("source_angle_rad", float("nan")),
                           ("source_gauge_y_mm", float("inf")),
                           ("source_gauge_y_mm", True),
                           ("source_gauge_y_mm", 0.0)):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                place_check_end(
                    "owner", "rail", "timber", (0.0, 0.0), 0.0, 0.8,
                    **dict(arguments, **{key: value}),
                )

    def test_nonfinite_host_frames_are_refused(self):
        for value in (math.nan, math.inf, -math.inf, True):
            for field in ("point", "heading", "base"):
                with self.subTest(value=value, field=field):
                    with self.assertRaises(ValueError):
                        place_check_end(
                            "owner", "rail", "timber",
                            (value, 0) if field == "point" else (0, 0),
                            value if field == "heading" else 0,
                            value if field == "base" else 0,
                            side="MS", family="CCR", source_angle_rad=0,
                            source_gauge_y_mm=0,
                        )

    def make(self, *, side="TS", family="CCL", heading=0.0):
        return place_check_end(
            "owner", "rail", "timber", (0.0, 0.0), heading, 0.8,
            side=side, family=family,
            source_angle_rad=0.0 if side == "MS" else math.atan(0.1),
            source_gauge_y_mm=0.0 if side == "MS" else 30.0,
        )

    def test_source_seat_translation_and_enlarged_base_anchor(self):
        alpha, k = math.atan(1 / 18), math.atan(0.1)
        flare = 49 / 192
        chair_mod = -(1 + flare + 4 / 3 * math.sin(alpha)) / 2
        shift = chair_mod * math.sin(k)
        for family, direction in (("CCL", -1), ("CCR", 1)):
            with self.subTest(family=family):
                frame = self.make(family=family)
                self.assertAlmostEqual(
                    frame.origin_mm[0], shift * math.cos(k)
                    - 0.45 * math.sin(k), places=12,
                )
                dx = -direction * flare * math.cos(alpha) / 2
                dy = -flare * math.sin(alpha) / 2
                self.assertAlmostEqual(
                    frame.check_frame.origin_mm[0] - frame.origin_mm[0],
                    dx * math.cos(k) + dy * math.sin(k), places=12,
                )
                self.assertAlmostEqual(
                    frame.check_frame.origin_mm[1] - frame.origin_mm[1],
                    -dx * math.sin(k) + dy * math.cos(k), places=12,
                )
                self.assertEqual(frame.check_frame.x_axis, frame.x_axis)
                self.assertNotEqual(frame.check_frame.origin_mm, frame.origin_mm)
                main = self.make(side="MS", family=family)
                self.assertEqual(main.check_frame.origin_mm, main.origin_mm)

    def test_nested_frames_survive_validation_and_cannot_be_forged(self):
        frame = self.make()
        prepared = prepare_check_end_placements((frame,))
        self.assertIsInstance(prepared[0], CheckEndPlacement)
        self.assertEqual(prepared[0], frame)
        self.assertIsNot(prepared[0], frame)
        self.assertEqual(len(frame.fixing_frames), 4)
        with self.assertRaises(ValueError):
            prepare_check_end_placements((frame, frame))
        forged = copy.deepcopy(frame)
        object.__setattr__(forged.check_frame, "position_id", "other")
        with self.assertRaises(ValueError):
            prepare_check_end_placements((forged,))
        with self.assertRaises(ValueError):
            self.make(family="CC")

    def test_component_frames_rotate_together_in_host_frame(self):
        original = self.make()
        angle = 0.37
        rotated = self.make(heading=angle)
        for first, second in zip(
            (original, original.check_frame, *original.fixing_frames),
            (rotated, rotated.check_frame, *rotated.fixing_frames),
        ):
            for old, new in ((first.origin_mm, second.origin_mm),
                             (first.x_axis, second.x_axis),
                             (first.y_axis, second.y_axis)):
                self.assertAlmostEqual(new[0], old[0] * math.cos(angle)
                                       - old[1] * math.sin(angle), places=12)
                self.assertAlmostEqual(new[1], old[0] * math.sin(angle)
                                       + old[1] * math.cos(angle), places=12)


class ParametricCheckEndTests(unittest.TestCase):
    """Mathematical foundations; no broader preview or rail-fit admission."""

    def near(self, actual, expected, scale=1.0):
        # Conservative operation-count roundoff for finite frame sums.
        # This is not a railway dimension or a physical-fit tolerance.
        budget = 128 * sys.float_info.epsilon * max(
            1.0, abs(actual), abs(expected), scale,
        )
        self.assertLessEqual(abs(actual - expected), budget)

    def test_actual_source_branches_and_join(self):
        geometry = source_rail_geometry(SOURCE_PARAMETERS)
        join = float(geometry["curve_end_station_mm"])
        before, at, after = [source_rail_pose(SOURCE_PARAMETERS, x, "TS")
                             for x in (math.nextafter(join, -math.inf), join,
                                       math.nextafter(join, math.inf))]
        self.assertEqual([p["source_branch"] for p in (before, at, after)],
                         ["radcurve", "turnoutst_main", "turnoutst_main"])
        for pose in (before, after):
            self.near(pose["y_mm"], at["y_mm"],
                      float(geometry["stock_radius_mm"]))
            self.near(pose["k_rad"], at["k_rad"])
        working = source_rail_pose(SOURCE_PARAMETERS, END_STATIONS[0][1], "TS")
        extension = source_rail_pose(SOURCE_PARAMETERS, END_STATIONS[1][1], "TS")
        self.assertLess(working["k_rad"], math.atan(0.1))
        self.near(extension["k_rad"], math.atan(0.1))
        self.assertEqual(working["source_rail_code"], 4)
        for _timber, station in END_STATIONS:
            main = source_rail_pose(SOURCE_PARAMETERS, station, "MS")
            self.assertEqual((main["source_rail_code"], main["y_mm"],
                              main["k_rad"]), (1, 0.0, 0.0))
        for station in (math.nan, math.inf, -math.inf, -1.0, True):
            with self.subTest(station=station), self.assertRaises(ValueError):
                source_rail_pose(SOURCE_PARAMETERS, station, "TS")

    def test_selector_boundaries_and_one_call_per_support(self):
        # Distinct, ordered interval endpoints isolate the Pascal predicates.
        bounds = (250.0, 260.0, 290.0, 300.0)
        for x, expected in ((250.0, 0), (260.0, 1), (290.0, 2), (300.0, 3)):
            self.assertEqual(source_check_selection(bounds, x)["check_chair"],
                             expected)
        self.assertEqual(source_check_selection(
            bounds, math.nextafter(250.0, math.inf),
        )["check_chair"], 1)
        self.assertEqual(source_check_selection(
            bounds, math.nextafter(300.0, math.inf),
        )["check_chair"], 0)
        state = (None, None)
        observed = []
        for station in (255.0, 265.0, 295.0):
            result = source_check_selection(bounds, station, state)
            observed.append(result["check_chair"])
            state = result["state"]
        self.assertEqual(observed, [1, 2, 3])
        self.assertEqual(source_check_selection(bounds, 255.0, state)[
            "check_chair"], 2)

    def test_component_frames_at_independent_source_join(self):
        geometry = source_rail_geometry(SOURCE_PARAMETERS)
        join = float(geometry["curve_end_station_mm"])
        for station in (math.nextafter(join, -math.inf), join,
                        math.nextafter(join, math.inf)):
            pose = source_rail_pose(SOURCE_PARAMETERS, station, "TS")
            for family in ("CCL", "CCR"):
                for direction in (1, -1):
                    heading = 2.7 + (0 if direction > 0 else math.pi)
                    host = complex(314, -271)
                    placed = place_check_end(
                        "owner", "rail", "timber", (host.real, host.imag),
                        heading, 2.75, side="TS", family=family,
                        source_angle_rad=pose["k_rad"],
                        source_gauge_y_mm=pose["y_mm"],
                    )
                    frames = (placed, placed.check_frame, *placed.fixing_frames)
                    for role, frame in zip(("body", "check", 0, 1, 2, 3), frames):
                        for native in ((0, 0, 0), (2, -3, 1), (-1, 4, 0.5)):
                            source = self.source_point(
                                native, role, "TS", family, pose,
                            )
                            expected = host + cmath.exp(1j * heading) * (
                                source + 8.25j
                            )
                            actual = frame.transform_point(native)
                            self.near(actual[0], expected.real, abs(host))
                            self.near(actual[1], expected.imag, abs(host))
                            self.near(actual[2], 2.75 + native[2])

    @staticmethod
    def circle(station, curvature):
        direction = cmath.exp(0.37j)
        advance = (station if curvature == 0 else
                   (cmath.exp(1j * curvature * station) - 1)
                   / (1j * curvature))
        return complex(314, -271) + direction * advance

    @staticmethod
    def source_point(native, role, side, family, pose):
        """Invert the native datum, then use source insertion geometry."""
        point = complex(-native[0], -native[1] - 0.45)
        angle = pose["k_rad"]
        turn = cmath.exp(-1j * angle)
        alpha = math.atan(1 / 18)
        flare = 49 / 192
        outer = 9.25 / 3
        inner = outer + 1 + flare + 4 / 3 * math.sin(alpha)
        shift = (outer - inner) * math.sin(angle) / 2
        anchor = complex(shift * math.cos(angle),
                         -pose["y_mm"] - shift * math.sin(angle))
        if isinstance(role, int):
            centres = (complex(-2 / 3, inner - 1.75 / 3),
                       complex(2 / 3, inner - 1.75 / 3),
                       complex(-2 / 3, -outer + 1.75 / 3),
                       complex(2 / 3, -outer + 1.75 / 3))
            centre = centres[role]
            target = (centre.conjugate() if side == "MS"
                      else anchor + turn * centre)
            return point + target - centre
        if side == "MS":
            return -point
        if role == "check":
            sign = -1 if family == "CCL" else 1
            point -= complex(sign * flare * math.cos(alpha) / 2,
                             flare * math.sin(alpha) / 2)
        return anchor + turn * point

    def test_signed_curvature_and_both_travel_directions(self):
        for curvature in (0.0, 1 / 600, -1 / 600, 1 / 1200, -1 / 1200,
                          1 / 2400, -1 / 2400):
            for travel_sign in (1, -1):
                source = end_source()
                payload = json.loads(source[2])
                for owner, sign in (("A", travel_sign), ("B", -travel_sign)):
                    config = payload["configuration"]["turnout_" + owner.lower()
                                                       + "_config"]
                    config["orientation"] = "facing" if sign > 0 else "trailing"
                    data = source[-1]["Host" + owner]
                    stations = (0.0, 250.0, 500.0, 750.0, 1000.0)
                    points = [self.circle(x, curvature) for x in stations]
                    data.update(points=[SimpleNamespace(x=p.real, y=p.imag)
                                        for p in points], stations=list(stations),
                                headings=[0.37 + curvature * x for x in stations])

                def interpolate(data, station):
                    neutral = dict(data, points=[
                        (p.x, p.y) for p in data["points"]
                    ])
                    result = alignment.interpolate_alignment_station(
                        neutral, station,
                    )
                    return SimpleNamespace(x=result.point[0],
                                           y=result.point[1]), result.heading

                source[0].interpolate_alignment_station = interpolate
                source = (*source[:2], json.dumps(payload), *source[3:])
                groups, witnesses, companions, _verify = prepare_ends(source)
                self.assertEqual(len(companions), 8)
                for family, placements in groups.items():
                    for placement in placements:
                        witness = witnesses[placement.position_id]
                        side = ("MS" if "main-side" in placement.position_id
                                else "TS")
                        pose = source_rail_pose(
                            SOURCE_PARAMETERS, witness["source_station_mm"], side,
                        )
                        station = witness["host_station_mm"]
                        left = min(int(station // 250), 3) * 250
                        fraction = (station - left) / 250
                        host = (self.circle(left, curvature) * (1 - fraction)
                                + self.circle(left + 250, curvature) * fraction)
                        owner_sign = (
                            travel_sign if "xo-001-a-" in placement.position_id
                            else -travel_sign
                        )
                        heading = 0.37 + curvature * station
                        if owner_sign < 0:
                            heading += math.pi
                        turn = cmath.exp(1j * heading)
                        frames = (placement, placement.check_frame,
                                  *placement.fixing_frames)
                        roles = ("body", "check", 0, 1, 2, 3)
                        for role, frame in zip(roles, frames):
                            for native in ((0, 0, 0), (2, -3, 1), (-1, 4, 0.5)):
                                local = self.source_point(
                                    native, role, side, family, pose,
                                )
                                expected = host + turn * (local + 8.25j)
                                actual = frame.transform_point(native)
                                self.near(actual[0], expected.real, abs(host))
                                self.near(actual[1], expected.imag, abs(host))
                                self.near(actual[2], 0.8 + native[2])
                        self.assertEqual(witness["physical_fit"], "NOT_PROVED")

    def test_varying_curvature_nodes_endpoints_and_unwrapped_heading(self):
        # Analytical parabolas supply varying signed curvature. Exact arc
        # stations and headings label the samples; the accepted host
        # contract interpolates between them. Sampling error is not fit.
        for bend in (1 / 2400, -1 / 2400):
            parameters = (0.0, 200.0, 400.0, 600.0, 800.0)
            stations, points, headings = [], [], []
            for u in parameters:
                slope = 2 * bend * u
                stations.append(
                    u * math.sqrt(1 + slope * slope) / 2
                    + math.asinh(slope) / (4 * bend)
                )
                points.append(complex(314, -271)
                              + cmath.exp(3.1j) * complex(u, bend * u * u))
                headings.append(3.1 + math.atan(slope))
            data = dict(points=[(p.real, p.imag) for p in points],
                        stations=stations, headings=headings,
                        total=stations[-1])
            probes = list(stations)
            probes += [(a + b) / 2 for a, b in zip(stations, stations[1:])]
            for station in stations[1:-1]:
                probes.extend((math.nextafter(station, -math.inf),
                               math.nextafter(station, math.inf)))
            for station in probes:
                # Independent interval search and affine reconstruction.
                interval = next((i for i in range(len(stations) - 1)
                                 if station <= stations[i + 1]), 3)
                fraction = ((station - stations[interval])
                            / (stations[interval + 1] - stations[interval]))
                host = (points[interval] * (1 - fraction)
                        + points[interval + 1] * fraction)
                heading = (headings[interval] * (1 - fraction)
                           + headings[interval + 1] * fraction)
                sampled = alignment.interpolate_alignment_station(data, station)
                for direction in (1, -1):
                    reverse = 0 if direction > 0 else math.pi
                    for identifier, source_station in END_STATIONS:
                        for side in ("MS", "TS"):
                            family = ("CCR" if (identifier == "X1-Z")
                                      == (side == "MS") else "CCL")
                            pose = source_rail_pose(
                                SOURCE_PARAMETERS, source_station, side,
                            )
                            placed = place_check_end(
                                "owner", "rail", "timber", sampled.point,
                                sampled.heading + reverse, 2.75,
                                side=side, family=family,
                                source_angle_rad=pose["k_rad"],
                                source_gauge_y_mm=pose["y_mm"],
                            )
                            frames = (placed, placed.check_frame,
                                      *placed.fixing_frames)
                            for role, frame in zip(
                                ("body", "check", 0, 1, 2, 3), frames,
                            ):
                                native = (2.0, -3.0, 1.25)
                                local = self.source_point(
                                    native, role, side, family, pose,
                                )
                                expected = host + cmath.exp(
                                    1j * (heading + reverse)
                                ) * (local + 8.25j)
                                actual = frame.transform_point(native)
                                self.near(actual[0], expected.real, abs(host))
                                self.near(actual[1], expected.imag, abs(host))
                                self.near(actual[2], 4.0)

    def test_complete_radius_decision_is_separate_from_frame_fit(self):
        # These are configured test inputs, not new railway limits.
        for requested in (600.0, 1200.0, 2400.0):
            for limiting in range(3):
                cases = ((math.nextafter(requested, -math.inf), False),
                         (requested, True),
                         (math.nextafter(requested, math.inf), True))
                for radius, expected in cases:
                    values = [requested * 2] * 3
                    values[limiting] = radius
                    self.assertEqual(crossover.complete_radius_decision(
                        *values, requested,
                    )["accepted"], expected)
        self.assertTrue(crossover.complete_radius_decision(
            None, None, None, 600,
        )["accepted"])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    )
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("Phase 9B check-end standalone validation passed")
