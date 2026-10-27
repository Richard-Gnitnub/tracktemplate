#!/usr/bin/env python3
"""Check the finite crossing/exit supplement and independent source rules."""

from collections import Counter
import copy
import hashlib
import inspect
import json
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.compatibility import (  # noqa: E402
    chair_catalogue_placement,
    transition_workflow,
)
import crossing_exit_source_oracle as oracle  # noqa: E402


class CrossingExitOptionTests(unittest.TestCase):
    def test_default_remains_absent_and_explicit_path_is_forwarded(self):
        method = transition_workflow.ModularCoreLayoutWorkflowSession.preview_private_catalogue_crossover_chairs
        self.assertIn(
            "crossing_contexts_path", inspect.signature(method).parameters
        )
        self.assertIsNone(
            inspect.signature(method)
            .parameters["crossing_contexts_path"]
            .default
        )
        session = SimpleNamespace(
            module=object(),
            _private_catalogue_crossover_preview_factory=object(),
            routing_record=Mock(),
        )
        operation = Mock(return_value="receipt")
        options = dict(
            paired_contexts_path="paired",
            include_central_cc=True,
            include_check_ends=True,
            include_single_rail=True,
            crossing_contexts_path="crossing",
        )
        with patch.object(
            chair_catalogue_placement,
            "preview_private_catalogue_crossover_chairs",
            operation,
        ):
            result = method(
                session, "document", "XO-001", "catalogue", **options
            )
        self.assertEqual(result, "receipt")
        operation.assert_called_once_with(
            session.module,
            "document",
            "XO-001",
            "catalogue",
            session._private_catalogue_crossover_preview_factory,
            **options,
        )

    def test_all_existing_supplements_required_before_source_access(self):
        operation = chair_catalogue_placement.preview_private_catalogue_crossover_chairs
        complete = dict(
            paired_contexts_path="paired",
            include_central_cc=True,
            include_check_ends=True,
            include_single_rail=True,
        )
        for missing in complete:
            with self.subTest(missing=missing):
                options = {
                    key: value
                    for key, value in complete.items()
                    if key != missing
                }
                create = Mock()
                with self.assertRaisesRegex(ValueError, "requires"):
                    operation(
                        object(),
                        object(),
                        "XO-001",
                        "unused",
                        create,
                        crossing_contexts_path="crossing",
                        **options,
                    )
                create.assert_not_called()


class CrossingSourceRulesTests(unittest.TestCase):
    def test_actual_source_families_not_canonical_labels(self):
        decisions = [oracle.source_decision(t) for t in oracle.TIMBERS]
        self.assertEqual(
            tuple(d["family"] for d in decisions),
            ("ZY", "ZY", "XA", "AA", "BB", "CD", "DD", "EF"),
        )
        self.assertEqual(decisions[0]["source_rail_2_branch"], "radcurve")
        self.assertTrue(
            all(
                d["source_rail_2_branch"] == "turnoutst_main"
                for d in decisions[1:]
            )
        )

    def test_continued_exit_context_and_joint_override(self):
        self.assertEqual(
            [
                oracle.exit_family(t, r)[0]
                for t in ("R1", "R2")
                for r in (2, 3)
            ],
            ["L1", "S1J", "S1", "S1"],
        )


class CrossingCommonFrameTests(unittest.TestCase):
    def test_all_source_components_on_signed_curvature_and_both_directions(
        self,
    ):
        from paired_switch_source_oracle import (
            expected_world_frame,
            world_point,
        )
        from tracktemplate.domain.chair_placement import place_paired_chair

        for radius in (None, -900.0, -600.0, 600.0, 900.0):
            stations = (0.0, 500.0, 1000.0)
            points = [
                (s, 0.0)
                if radius is None
                else (
                    radius * math.sin(s / radius),
                    radius * (1 - math.cos(s / radius)),
                )
                for s in stations
            ]
            headings = [
                0.0 if radius is None else s / radius for s in stations
            ]
            host = dict(stations=stations, points=points, headings=headings)
            for direction in (-1, 1):
                for timber in oracle.TIMBERS:
                    context = oracle.crossing_context(timber)
                    source_x = context["station_mm"]
                    # Includes both source host endpoints and an interior point.
                    for target in (0.0, 500.0 + direction * source_x, 1000.0):
                        with self.subTest(
                            radius=radius,
                            direction=direction,
                            timber=timber,
                            target=target,
                        ):
                            toe = target - direction * source_x
                            expected = expected_world_frame(
                                host,
                                toe_chainage_mm=toe,
                                direction=direction,
                                hand=-1,
                                station_mm=source_x,
                                gauge_mm=16.5,
                            )
                            index = 0 if target < 500 else 1
                            fraction = (target - stations[index]) / 500
                            centre = tuple(
                                points[index][axis]
                                + fraction
                                * (
                                    points[index + 1][axis]
                                    - points[index][axis]
                                )
                                for axis in (0, 1)
                            )
                            heading = headings[index] + fraction * (
                                headings[index + 1] - headings[index]
                            )
                            if direction == -1:
                                heading += math.pi
                            placement = place_paired_chair(
                                "position",
                                "rail",
                                "timber",
                                centre,
                                heading,
                                0.8,
                                8.25,
                                0.45,
                            )
                            source_points = [
                                (
                                    c["insertion"]["x_mm"],
                                    c["insertion"]["y_mm"],
                                    -1.9,
                                )
                                for c in context["components"]
                            ] + [
                                (x, y, -2.0)
                                for x, y in context["base"][
                                    "bolt_centres_source_mm"
                                ]
                            ]
                            for source in source_points:
                                actual = placement.transform_point(
                                    oracle.source_to_native(source)
                                )
                                wanted = (
                                    *world_point(expected, source),
                                    source[2] + 149 / 60 + 0.8,
                                )
                                for first, second in zip(actual, wanted):
                                    budget = (
                                        128
                                        * sys.float_info.epsilon
                                        * max(
                                            1,
                                            abs(first),
                                            abs(second),
                                            1000,
                                        )
                                    )
                                    self.assertLessEqual(
                                        abs(first - second), budget
                                    )

    def test_invalid_common_frame_values_refuse(self):
        from tracktemplate.domain.chair_placement import place_paired_chair

        for value in (True, float("nan"), float("inf"), -float("inf")):
            for field in ("heading", "base_z", "centre"):
                with self.subTest(value=value, field=field):
                    with self.assertRaises(ValueError):
                        place_paired_chair(
                            "p",
                            "r",
                            "t",
                            (value, 0) if field == "centre" else (0, 0),
                            value if field == "heading" else 0,
                            value if field == "base_z" else 0.8,
                            8.25,
                            0.45,
                        )


def crossing_source():
    """Invent finite records using the independent source mathematics.

    Synthetic records test binding and refusal, not native geometry or
    admission of a different host. Native validation uses actual XO-001.
    """
    from validate_phase9b_catalogue_single_rail import single_source
    from tracktemplate.compatibility.chair_pair_placement import _host_context

    previous = single_source()
    module, document, signature = previous[:3]
    configuration = json.loads(signature)["configuration"]
    positions, timbers, rails = {}, {}, {}
    layout = {
        item["identifier"]: item["x"]
        for item in module.rea_c10_timber_layout(None, None)
    }
    layout.update(
        {t: oracle.source_decision(t)["station_mm"] for t in oracle.TIMBERS}
    )
    layout.update({t: oracle.exit_family(t, 2)[1] for t in ("R1", "R2")})
    module.rea_c10_timber_layout = lambda *_args: [
        {"identifier": t, "x": x} for t, x in layout.items()
    ]
    crossing_names = (
        ("straight switch and closure rail", "curved switch and closure rail"),
        ("straight switch and closure rail", "curved switch and closure rail"),
        (
            "turnout-side wing rail",
            "main-side wing rail",
            "turnout-side wing knuckle",
            "main-side wing knuckle",
        ),
        ("turnout-side wing rail", "main-side wing rail"),
        (
            "vee point rail",
            "vee splice rail",
            "turnout-side wing flare",
            "main-side wing flare",
        ),
        *(("vee point rail", "vee splice rail"),) * 3,
    )
    expected_primary, expected_companions = set(), {}
    for side in ("A", "B"):
        for timber, names in [
            *zip(oracle.TIMBERS, crossing_names),
            ("R1", ("vee point rail", "vee splice rail")),
            ("R2", ("vee point rail", "vee splice rail")),
        ]:
            # Exercise both nominal and inherited long-timber identity forms.
            timber_id = f"XO-001:{side}:{timber}"
            source = {"local_x": layout[timber]}
            if side == "B" and timber == "X8-E":
                timber_id = "XO-001:INHERITED-LONG:B:007"
                source = {
                    "path_station": layout[timber],
                    "extended_source_timber_identity": "XO-001:B:X8-E",
                }
            timbers[timber_id] = {
                "stable_identity": timber_id,
                "source_configuration": source,
            }
            identities = []
            for name in names:
                identity = (
                    "XO-001:chair:"
                    + timber_id.lower().replace(":", "-")
                    + ":"
                    + name.replace(" ", "-")
                )
                rail_id = side + ":" + name
                positions[identity] = {
                    "stable_chair_position_identity": identity,
                    "prototype_timber_identifier": timber,
                    "rail_name": name,
                    "parent_turnout_identity": f"XO-001-{side}001",
                    "timber_identity": timber_id,
                    "rail_identity": rail_id,
                    "special_assignment_deferred": True,
                    # Deliberately misleading labels must not select geometry.
                    "chair_code": 22,
                    "chair_code_label": "XN",
                    "source_configuration": {"timber": copy.deepcopy(source)},
                }
                rails[rail_id] = {
                    "stable_identity": rail_id,
                    "points": [(0.0, 3.0), (1.0, 1.1)],
                }
                identities.append(identity)
            if timber in oracle.TIMBERS:
                expected_primary.add(identities[0])
                expected_companions.update(
                    {i: identities[0] for i in identities[1:]}
                )
            else:
                expected_primary.update(identities)
        for timber in ("S13", "T1", "T2"):
            for name in (
                "main-side stock rail",
                "straight switch and closure rail",
            ):
                identity = (
                    f"XO-001:chair:xo-001-{side.lower()}-{timber.lower()}:"
                    + name.replace(" ", "-")
                )
                positions[identity] = {
                    "stable_chair_position_identity": identity,
                    "prototype_timber_identifier": timber,
                    "rail_name": name,
                    "chair_code": 1,
                    "chair_code_label": "S1",
                }
    timber_id = "XO-001:ENVELOPE:001"
    timbers[timber_id] = {
        "stable_identity": timber_id,
        "centre": (0.0, 0.0),
        "width": 2.0,
        "width_axis": (0.0, 1.0),
        "source_configuration": {"envelope": 1},
        "polygon": [(-2.0, -1.0), (2.0, -1.0), (2.0, 1.0), (-2.0, 1.0)],
    }
    for name, end_y in (("vee point rail", 1.1), ("vee splice rail", 1.15)):
        rail_id = "A:" + name
        rails[rail_id]["points"] = [(0.0, 3.0), (1.0, end_y)]
        identity = "XO-001:chair:xo-001-envelope-001:" + name.replace(" ", "-")
        positions[identity] = {
            "stable_chair_position_identity": identity,
            "prototype_timber_identifier": "E001",
            "rail_name": name,
            "parent_turnout_identity": "XO-001-A001",
            "timber_identity": timber_id,
            "rail_identity": rail_id,
            "centre_point": rails[rail_id]["points"][-1],
            "source_configuration": {"timber": {"envelope": 1}},
        }
    hosts, _, _ = _host_context(module, document, configuration)
    metadata = {
        "source_context_sha256": hashlib.sha256(
            signature.encode()
        ).hexdigest(),
        "host_context_sha256": hashlib.sha256(
            json.dumps(hosts, sort_keys=True, allow_nan=False).encode()
        ).hexdigest(),
    }
    selections = tuple(
        SimpleNamespace(
            run="RH-" + timber,
            label=oracle.source_decision(timber)["family"],
            model_sha256="invented-" + timber,
            metadata=copy.deepcopy(metadata),
            context={
                "station_mm": layout[timber],
                "timber_id": timber,
                "context_sha256": "invented-context-" + timber,
                "native_frame": {"common_timber_curving_applied": False},
            },
        )
        for timber in oracle.TIMBERS
    )
    return dict(
        module=module,
        document=document,
        signature=signature,
        positions=positions,
        rails=list(rails.values()),
        timbers=list(timbers.values()),
        selections=selections,
        hosts=previous[-1],
        primary=expected_primary,
        companions=expected_companions,
    )


def prepare_crossings(source):
    from tracktemplate.compatibility import (
        chair_crossing_exit_placement as crossing,
    )

    with (
        patch.object(
            crossing,
            "prepare_crossing_catalogue",
            return_value=source["selections"],
        ),
        patch.object(
            crossing,
            "prepare_catalogue_chair",
            side_effect=lambda _path, family, **_kwargs: SimpleNamespace(
                label=family, model_sha256="invented-" + family
            ),
        ),
    ):
        return crossing.prepare_crossing_exit(
            *(
                source[key]
                for key in (
                    "module",
                    "document",
                    "signature",
                    "positions",
                    "rails",
                    "timbers",
                )
            ),
            0.8,
            "invented-catalogue",
            "invented-crossings",
        )


class CrossingExitBindingTests(unittest.TestCase):
    def test_complete_source_ownership_and_preserved_discrepancies(self):
        source = crossing_source()
        before = copy.deepcopy(
            (source["positions"], source["rails"], source["timbers"])
        )
        groups, witnesses, companions, excluded, heel, _verify = (
            prepare_crossings(source)
        )
        self.assertEqual(len(witnesses), 24)
        self.assertEqual(set(witnesses), source["primary"])
        self.assertEqual(companions, source["companions"])
        self.assertEqual(len(companions), 24)
        self.assertTrue(set(witnesses).isdisjoint(companions))
        self.assertEqual(
            Counter(w["family"] for w in witnesses.values()),
            {
                "ZY": 4,
                "XA": 2,
                "AA": 2,
                "BB": 2,
                "CD": 2,
                "DD": 2,
                "EF": 2,
                "S1": 4,
                "S1J": 2,
                "L1": 2,
            },
        )
        self.assertEqual(
            {k: len(v) for k, v in groups.items()},
            {
                **{"RH-" + t: 2 for t in oracle.TIMBERS},
                "ExitS1": 4,
                "ExitS1J": 2,
                "ExitL1": 2,
            },
        )
        placements = {
            p.position_id: p for values in groups.values() for p in values
        }
        for identity, witness in witnesses.items():
            position = source["positions"][identity]
            side = position["parent_turnout_identity"][-4]
            direction = 1 if side == "A" else -1
            local_x = witness["source_station_mm"]
            self.assertAlmostEqual(
                witness["host_station_mm"],
                500 + direction * local_x,
                places=12,
            )
            if position["prototype_timber_identifier"] in oracle.TIMBERS:
                actual = placements[identity].transform_point(
                    oracle.source_to_native((0, -16.5, 0))
                )
                expected = (
                    500 + direction * local_x,
                    -direction * 8.25,
                    0.8 + 149 / 60,
                )
                for first, second in zip(actual, expected):
                    self.assertAlmostEqual(first, second, places=12)
            else:
                pose = oracle.source_rail_pose(
                    oracle.SOURCE_PARAMETERS,
                    local_x,
                    witness["source_rail_code"],
                )
                self.assertEqual(
                    witness["source_branch"], pose["source_branch"]
                )
                self.assertAlmostEqual(
                    witness["source_angle_rad"], pose["k_rad"], places=12
                )
                self.assertAlmostEqual(
                    witness["source_gauge_y_mm"], pose["y_mm"], places=12
                )
        self.assertEqual(len(excluded), 2)
        self.assertEqual(len(heel), 10)
        self.assertEqual(
            Counter(h["timber"] for h in heel), {"S13": 4, "T1": 4, "T2": 2}
        )
        self.assertTrue(
            all(
                h["accepted_preview_family"] == "S1"
                and h["source_family"] == "L1"
                for h in heel
            )
        )
        self.assertEqual(
            before, (source["positions"], source["rails"], source["timbers"])
        )

    def test_source_ownership_station_and_recipe_mutation_refuse(self):
        for change in (
            "missing",
            "duplicate",
            "owner",
            "identity",
            "deferred",
            "station",
            "extended-owner",
            "recipe-station",
            "recipe-frame",
            "source-hash",
            "host-hash",
            "heel",
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                source = crossing_source()
                identity = next(iter(source["positions"]))
                position = source["positions"][identity]
                if change == "missing":
                    del source["positions"][identity]
                elif change == "duplicate":
                    source["positions"]["extra"] = copy.deepcopy(position)
                elif change == "owner":
                    position["parent_turnout_identity"] = "Other"
                elif change == "identity":
                    position["stable_chair_position_identity"] = "Other"
                elif change == "deferred":
                    position["special_assignment_deferred"] = False
                elif change == "station":
                    position["source_configuration"]["timber"]["local_x"] += 1
                elif change == "extended-owner":
                    next(
                        t
                        for t in source["timbers"]
                        if "path_station" in t["source_configuration"]
                    )["source_configuration"][
                        "extended_source_timber_identity"
                    ] = "XO-001:B:Other"
                elif change == "recipe-station":
                    source["selections"][0].context["station_mm"] += 1
                elif change == "recipe-frame":
                    source["selections"][0].context["native_frame"][
                        "common_timber_curving_applied"
                    ] = True
                elif change.endswith("hash"):
                    source["selections"][0].metadata[
                        "source_context_sha256"
                        if change == "source-hash"
                        else "host_context_sha256"
                    ] = "Other"
                else:
                    source["positions"][
                        "XO-001:chair:xo-001-a-s13:main-side-stock-rail"
                    ]["chair_code"] = 2
                prepare_crossings(source)

    def test_unsupported_hand_refuses_even_with_matching_fixture_binding(self):
        source = crossing_source()
        signature = json.loads(source["signature"])
        signature["configuration"]["turnout_a_config"]["handing"] = "Left-hand"
        source["signature"] = json.dumps(signature)
        from tracktemplate.compatibility.chair_pair_placement import (
            _host_context,
        )

        hosts, _, _ = _host_context(
            source["module"], source["document"], signature["configuration"]
        )
        for selection in source["selections"]:
            selection.metadata["source_context_sha256"] = hashlib.sha256(
                source["signature"].encode()
            ).hexdigest()
            selection.metadata["host_context_sha256"] = hashlib.sha256(
                json.dumps(hosts, sort_keys=True, allow_nan=False).encode()
            ).hexdigest()
        with self.assertRaisesRegex(ValueError, "right-hand"):
            prepare_crossings(source)

    def test_late_verification_checks_hosts_and_all_catalogues(self):
        from tracktemplate.compatibility import (
            chair_crossing_exit_placement as crossing,
        )

        source = crossing_source()
        verify = prepare_crossings(source)[-1]
        with (
            patch.object(crossing, "verify_crossing_catalogue") as contexts,
            patch.object(crossing, "verify_catalogue_sources") as singles,
        ):
            verify()
            contexts.assert_called_once_with(source["selections"])
            self.assertEqual(singles.call_count, 3)
            source["hosts"]["HostB"]["points"][0].x += 1
            with self.assertRaisesRegex(ValueError, "host changed"):
                verify()

    def test_finite_rail_exclusions_have_independent_polygon_separation(self):
        source = crossing_source()
        excluded = prepare_crossings(source)[3]
        timber = next(t for t in source["timbers"] if "polygon" in t)
        polygon = timber["polygon"]
        edge = tuple(polygon[1][i] - polygon[0][i] for i in (0, 1))
        length = math.hypot(*edge)
        normal = (-edge[1] / length, edge[0] / length)
        high = max(sum(v * n for v, n in zip(p, normal)) for p in polygon)
        rail_map = {r["stable_identity"]: r for r in source["rails"]}
        for identity, proof in excluded.items():
            points = rail_map[source["positions"][identity]["rail_identity"]][
                "points"
            ]
            gap = (
                min(sum(v * n for v, n in zip(p, normal)) for p in points)
                - high
            )
            self.assertGreater(gap, 0)
            self.assertLess(gap, 0.2)
            self.assertAlmostEqual(
                gap, proof["endpoint_outside_timber_mm"], places=12
            )
            self.assertEqual(proof["physical_fit"], "NOT_ASSESSED")
        for failure in ("missing", "endpoint", "intersects", "owner"):
            with self.subTest(failure=failure), self.assertRaises(ValueError):
                altered = crossing_source()
                identity = next(iter(excluded))
                position = altered["positions"][identity]
                if failure == "missing":
                    del altered["positions"][identity]
                elif failure == "endpoint":
                    position["centre_point"] = (1.0, 1.16)
                elif failure == "owner":
                    position["parent_turnout_identity"] = "XO-001-B001"
                else:
                    rail = next(
                        r
                        for r in altered["rails"]
                        if r["stable_identity"] == position["rail_identity"]
                    )
                    rail["points"][0] = (0.0, 0.0)
                prepare_crossings(altered)


class CrossingCatalogueRefusalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / "tmp").mkdir(exist_ok=True)

    def test_unknown_bytes_and_caller_hash_refuse(self):
        from tracktemplate.application import (
            chair_crossing_catalogue as reader,
        )
        from tracktemplate.application.chair_catalogue import (
            CatalogueChairError,
        )

        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as directory:
            path = Path(directory) / "unqualified.json"
            path.write_text("{}")
            with self.assertRaisesRegex(
                CatalogueChairError, "reviewed private evidence"
            ):
                reader.prepare_crossing_catalogue(path)
            with self.assertRaises(TypeError):
                reader.prepare_crossing_catalogue(
                    path, sha256="caller-supplied"
                )
            for value in ((), [], (SimpleNamespace(),) * 8):
                with self.assertRaises(CatalogueChairError):
                    reader.verify_crossing_catalogue(value)

    def test_malformed_duplicate_nonfinite_and_incomplete_evidence_refuse(
        self,
    ):
        from tracktemplate.application import (
            chair_crossing_catalogue as reader,
        )
        from tracktemplate.application.chair_catalogue import (
            CatalogueChairError,
        )

        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as directory:
            path = Path(directory) / "invented.json"
            for text in (
                "invalid",
                '{"a": 1, "a": 2}',
                '{"a": NaN}',
                "{}",
                "[]",
            ):
                with self.subTest(text=text):
                    path.write_text(text)
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    # Only the test fixture is hash-bound; the public API has no bypass.
                    with patch.object(
                        reader, "CROSSING_CATALOGUE_SHA256", digest
                    ):
                        with self.assertRaises(CatalogueChairError):
                            reader.prepare_crossing_catalogue(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
