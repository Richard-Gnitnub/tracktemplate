#!/usr/bin/env python3
"""Check four opt-in R2 exit chairs without constructing native geometry.

Source-informed Templot 556b calculations, GPL-3.0-or-later; see NOTICE.md
and reference/PROVENANCE.md. Reuse the independent decimal rail and source
component-frame oracles. Their reuse is an explicit independence limit.
Synthetic host and adapter fixtures do not qualify physical fit or GUI.
"""

from collections import Counter
from contextlib import ExitStack
import copy
from fractions import Fraction
import hashlib
import inspect
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility import (  # noqa: E402
    chair_catalogue_placement as binding,
    chair_check_end_placement,
    chair_check_placement,
    chair_pair_placement,
    chair_single_rail_placement as singles,
    transition_workflow,
)
from tracktemplate.domain.chair_placement import S1Placement  # noqa: E402
import single_rail_source_oracle as oracle  # noqa: E402
from validate_phase9b_catalogue_heel_adapter import (  # noqa: E402
    RoutingBoundary,
    fixture as adapter_fixture,
    single,
)
from validate_phase9b_catalogue_heel_l1 import (  # noqa: E402
    ARCHIVE,
    ARCHIVE_SHA256,
    CORRECTED_IDS,
    SOURCE_HASHES,
    UNCHANGED_HEEL_IDS,
    heel_source,
    selection,
)

RAILS = {2: "vee splice rail", 3: "vee point rail"}
TIMBERS = {"A": "XO-001:INHERITED-LONG:A:004",
           "B": "XO-001:INHERITED-LONG:B:010"}
S1_SHA256 = oracle.MODEL_INPUTS[0][2]
R2_STATION = oracle.a_timber(oracle.SOURCE_PARAMETERS) + 205 / 3


def chair_identity(owner, rail):
    """Use the existing extended timber and named source rail identities."""
    return ("XO-001:chair:" + TIMBERS[owner].lower().replace(":", "-")
            + ":" + RAILS[rail].replace(" ", "-"))


R2_IDS = {chair_identity(owner, rail)
          for owner in ("A", "B") for rail in RAILS}


def r2_source():
    """Add only the four fixed R2 records to the retained heel fixture."""
    source = heel_source()
    module, _document, signature, positions, timbers, _hosts = source
    layout = module.rea_c10_timber_layout
    module.rea_c10_timber_layout = lambda *args: [
        *layout(*args), {"identifier": "R2", "x": R2_STATION},
    ]
    config = json.loads(signature)
    for owner, timber_id in TIMBERS.items():
        config["configuration"]["turnout_" + owner.lower() + "_config"][
            "module_end_x"
        ] = oracle.a_timber(oracle.SOURCE_PARAMETERS) + 445 / 6
        timber_source = {
            "extended_source_timber_identity": f"XO-001:{owner}:R2",
            "path_station": R2_STATION,
        }
        timbers.append({"stable_identity": timber_id,
                        "source_configuration": timber_source})
        for rail, name in RAILS.items():
            identity = chair_identity(owner, rail)
            positions[identity] = {
                "stable_chair_position_identity": identity,
                "prototype_timber_identifier": "R2", "rail_name": name,
                "parent_turnout_identity": f"XO-001-{owner}001",
                "timber_identity": timber_id,
                "rail_identity": f"XO-001-{owner}001:rail:"
                + name.replace(" ", "-"),
                "special_assignment_deferred": True,
                "chair_code": 25 if rail == 2 else 26,
                "chair_code_label": "AB" if rail == 2 else "BB/BC",
                "source_configuration": {
                    "timber": copy.deepcopy(timber_source),
                },
            }
    return (
        module, source[1], json.dumps(config), positions, timbers, source[-1],
    )


def prepare(source, **options):
    """Retain actual binding and mathematics; stand in for model loading."""
    def catalogue(path, family, **kwargs):
        result = selection(path, family, **kwargs)
        if family == "S1":
            result.model_sha256 = S1_SHA256
        return result

    with patch.object(
        singles, "prepare_catalogue_chair", side_effect=catalogue,
    ):
        return singles.prepare_single_rails(
            *source[:5], 0.8, "unused", **options,
        )


class R2SourceTests(unittest.TestCase):
    @unittest.skipUnless(ARCHIVE.is_file(), "private 556b archive unavailable")
    def test_frozen_source_sequence_and_clearance_predicates(self):
        self.assertEqual(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
                         ARCHIVE_SHA256)
        with zipfile.ZipFile(ARCHIVE) as archive:
            name, = [n for n in archive.namelist()
                     if n.rsplit("/", 1)[-1] == "math_unit.pas"]
            raw = archive.read(name)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         SOURCE_HASHES["math_unit.pas"])
        lines = raw.decode("latin-1").splitlines()
        continuation = "\n".join(lines[22759:22820])
        self.assertIn("1: tb_xing_end:=turnoutx", continuation)
        self.assertIn("xtb:=mvjp_nx+mvj_sp*inscale", continuation)
        self.assertIn("xtb:=xtb+xingtb_v", continuation)
        joint = "\n".join(lines[29654:29665])
        self.assertIn("(timb_str='X')", joint)
        self.assertIn("xtb>(mvjp_nx-(mvj_sp+1)*inscale)", joint)
        self.assertIn("xtb<(mvjp_nx+(mvj_sp+1)*inscale)", joint)
        vee = "\n".join(lines[29759:29804])
        self.assertIn("aq2offset(xtimbcl-S1_chair_halfwide*inscale", vee)
        self.assertIn("S1_chair_outlong*inscale*2+inscale/2", vee)
        self.assertIn("chairing_dims2:=L1_chairing_dims", vee)

    def test_r2_source_selects_s1_after_joint_without_extrapolation(self):
        low, high = oracle.joint_window(oracle.SOURCE_PARAMETERS)
        self.assertGreater(R2_STATION, high)
        self.assertGreater(high, low)
        gap = oracle.source_rail_pose(
            oracle.SOURCE_PARAMETERS, R2_STATION - 4 / 3, 2,
        )["y_mm"] - 16.5
        self.assertGreater(gap, float(Fraction(19, 3)))
        self.assertEqual(len(oracle.dimensions("S1")["fixing_centres_mm"]), 3)
        end = oracle.a_timber(oracle.SOURCE_PARAMETERS) + 445 / 6
        self.assertGreater(end, R2_STATION)
        for rail, branch in ((2, "turnoutst_main"), (3, "main_straight")):
            pose = oracle.source_rail_pose(
                oracle.SOURCE_PARAMETERS, R2_STATION, rail,
            )
            self.assertEqual(pose["source_branch"], branch)
            self.assertEqual(
                pose["k_rad"], math.atan2(1, 10) if rail == 2 else 0,
            )


class R2BindingTests(unittest.TestCase):
    def test_four_additions_preserve_previous_records_and_heel_modes(self):
        for corrected in (False, True):
            source = r2_source()
            before = copy.deepcopy(source[3:5])
            baseline, old_witnesses, _ = prepare(
                source, correct_heel_l1=corrected,
            )
            groups, witnesses, _ = prepare(
                source, correct_heel_l1=corrected, include_r2_exit=True,
            )
            self.assertEqual({k: len(v) for k, v in groups.items()},
                             {"SupplementS1": 18, "SupplementS1J": 4,
                              "L1": 26 if corrected else 16})
            self.assertEqual(set(witnesses) - set(old_witnesses), R2_IDS)
            for name, old in baseline.items():
                self.assertEqual(tuple(p for p in groups[name]
                                       if p.position_id not in R2_IDS), old)
            for identity, witness in old_witnesses.items():
                self.assertEqual(witnesses[identity], witness)
            for identity in R2_IDS:
                witness = witnesses[identity]
                self.assertEqual(witness["family"], "S1")
                self.assertEqual(witness["source_model_sha256"], S1_SHA256)
                self.assertEqual(witness["physical_fit"], "NOT_PROVED")
            self.assertEqual(source[3:5], before)

    def test_invalid_source_and_endpoint_identities_are_rejected(self):
        for defect in (
            "missing", "duplicate", "identity", "owner", "rail-name",
            "rail-owner", "deferred", "station", "nonfinite", "source-owner",
            "literal-R", "endpoint", "local-source",
        ):
            with self.subTest(defect=defect):
                source = r2_source()
                identity = chair_identity("A", 2)
                record = source[3][identity]
                timber = next(t for t in source[4]
                              if t["stable_identity"] == TIMBERS["A"])
                if defect == "missing":
                    del source[3][identity]
                elif defect == "duplicate":
                    source[3]["duplicate"] = copy.deepcopy(record)
                elif defect == "identity":
                    record["stable_chair_position_identity"] = "wrong"
                elif defect == "owner":
                    record["parent_turnout_identity"] = "XO-001-B001"
                elif defect == "rail-name":
                    record["rail_name"] = "main-side stock rail"
                elif defect == "rail-owner":
                    record["rail_identity"] = (
                        "XO-001-B001:rail:vee-splice-rail"
                    )
                elif defect == "deferred":
                    record["special_assignment_deferred"] = False
                elif defect in ("station", "nonfinite"):
                    timber["source_configuration"]["path_station"] = (
                        math.nan if defect == "nonfinite" else R2_STATION + 1
                    )
                elif defect == "source-owner":
                    timber["source_configuration"][
                        "extended_source_timber_identity"
                    ] = "XO-001:B:R2"
                elif defect == "literal-R":
                    record["prototype_timber_identifier"] = "R"
                elif defect == "endpoint":
                    record["timber_identity"] = "XO-001:ENVELOPE:001"
                else:
                    timber["source_configuration"] = {"local_x": R2_STATION}
                for position in source[3].values():
                    if position["timber_identity"] == TIMBERS["A"]:
                        position["source_configuration"]["timber"] = (
                            copy.deepcopy(timber["source_configuration"])
                        )
                with self.assertRaises(ValueError):
                    prepare(source, include_r2_exit=True)

    def test_host_and_catalogue_verification_remain_live(self):
        source = r2_source()
        _groups, _witnesses, verify = prepare(source, include_r2_exit=True)
        with patch.object(singles, "verify_catalogue_sources") as checked:
            verify()
            self.assertEqual(
                Counter(c.args[0].label for c in checked.call_args_list),
                {"S1": 1, "L1": 1, "S1J": 1},
            )
        with patch.object(singles, "verify_catalogue_sources",
                          side_effect=ValueError("catalogue changed")):
            with self.assertRaisesRegex(ValueError, "catalogue changed"):
                verify()
        source[-1]["HostB"]["points"][0].x += 1
        with patch.object(singles, "verify_catalogue_sources"):
            with self.assertRaisesRegex(ValueError, "host changed"):
                verify()

    def test_r2_clearance_joint_and_source_branch_boundaries(self):
        # Mock only source rail evaluation. Exercise the actual admission
        # predicate; this does not admit other XO-001 hosts or stations.
        dimensions = {"a_timber_x": oracle.a_timber(oracle.SOURCE_PARAMETERS)}
        angle = math.atan2(1, 10)

        def family(station, rail, gauge_y, branch="turnoutst_main"):
            with patch.object(
                singles, "_source_pose", return_value=(angle, gauge_y, branch),
            ) as pose:
                try:
                    return singles._family(
                        None, dimensions, "R2", station, rail,
                    )
                finally:
                    pose.assert_called_once_with(
                        None, dimensions, station - 4 / 3, 2,
                    )

        threshold = Fraction(19, 3)
        gauge_threshold = Fraction(33, 2) + threshold
        centre = float(gauge_threshold)
        observed = set()
        for gauge_y in (
            math.nextafter(centre, -math.inf), centre,
            math.nextafter(centre, math.inf),
        ):
            # The exact 19/3 gap cannot occur after binary64 subtraction
            # at this gauge. Classify representable neighbours rationally.
            exact_gap = Fraction.from_float(gauge_y) - Fraction(33, 2)
            self.assertNotEqual(exact_gap, threshold)
            admitted = exact_gap >= threshold
            observed.add(admitted)
            for rail in (2, 3):
                with self.subTest(gauge_y=gauge_y, rail=rail):
                    if admitted:
                        self.assertEqual(
                            family(R2_STATION, rail, gauge_y), "S1",
                        )
                    else:
                        with self.assertRaisesRegex(ValueError, "two S1"):
                            family(R2_STATION, rail, gauge_y)
        self.assertEqual(observed, {False, True})

        joint = dimensions["a_timber_x"] + (12.5 + 5 * 30) / 3
        low, high = joint - 13.5 / 3, joint + 13.5 / 3
        for station, admitted in (
            (math.nextafter(low, -math.inf), True), (low, True),
            (math.nextafter(low, high), False), (joint, False),
            (math.nextafter(high, low), False), (high, True),
            (math.nextafter(high, math.inf), True),
        ):
            for rail in (2, 3):
                with self.subTest(station=station, rail=rail):
                    if admitted:
                        self.assertEqual(family(station, rail, 24.0), "S1")
                    else:
                        with self.assertRaisesRegex(ValueError, "joint-chair"):
                            family(station, rail, 24.0)
        for rail, branch in (
            (2, "radcurve"), (3, "radcurve"), (2, "main_straight"),
            (3, "unknown"), (1, "turnoutst_main"), (4, "turnoutst_main"),
        ):
            with self.subTest(rail=rail, branch=branch):
                with self.assertRaisesRegex(ValueError, "two S1"):
                    family(R2_STATION, rail, 24.0, branch)

    def test_body_and_fixings_for_directions_and_signed_host_curvature(self):
        def near(actual, expected):
            # Existing finite-arithmetic budget, never a physical-fit limit.
            budget = 128 * sys.float_info.epsilon * max(
                1000, abs(actual), abs(expected),
            )
            self.assertLessEqual(abs(actual - expected), budget)

        for radius in (None, 600, 900, 1800, -600, -900, -1800):
            source = r2_source()

            def host(_data, station):
                angle = 0.0 if radius is None else station / radius
                point = (
                    (station, 0.0) if radius is None else
                    (radius * math.sin(angle), radius * (1 - math.cos(angle)))
                )
                return SimpleNamespace(x=point[0], y=point[1]), angle

            source[0].interpolate_alignment_station = host
            groups, witnesses, _verify = prepare(source, include_r2_exit=True)
            actual = {p.position_id: p for p in groups["SupplementS1"]}
            for owner in ("A", "B"):
                direction = 1 if owner == "A" else -1
                chainage = 500 + direction * R2_STATION
                point, heading = host(None, chainage)
                heading += math.pi if direction == -1 else 0
                c, s = math.cos(heading), math.sin(heading)
                origin = (point.x - 8.25 * s, point.y + 8.25 * c)
                for rail in RAILS:
                    identity = chair_identity(owner, rail)
                    pose = oracle.source_rail_pose(
                        oracle.SOURCE_PARAMETERS, R2_STATION, rail,
                    )
                    matrices = oracle.local_frames(
                        "S1", rail, pose["k_rad"], pose["y_mm"],
                    )
                    witness, placement = witnesses[identity], actual[identity]
                    self.assertEqual(witness["source_station_mm"], R2_STATION)
                    self.assertEqual(witness["host_station_mm"], chainage)
                    self.assertEqual(witness["source_rail_code"], rail)
                    self.assertEqual(
                        witness["source_branch"], pose["source_branch"],
                    )
                    self.assertEqual(len(placement.fixing_frames), 3)
                    for frame, matrix in zip(
                        (placement, *placement.fixing_frames),
                        (matrices["body"], *matrices["fixings"]),
                    ):
                        self.assertEqual(frame.position_id, identity)
                        self.assertEqual(frame.rail_id, placement.rail_id)
                        self.assertEqual(frame.timber_id, TIMBERS[owner])
                        for field, column in (("origin_mm", 3), ("x_axis", 0),
                                              ("y_axis", 1)):
                            x, y = matrix[0][column], matrix[1][column]
                            vector = getattr(frame, field)
                            near(vector[0], c * x - s * y
                                 + (origin[0] if column == 3 else 0))
                            near(vector[1], s * x + c * y
                                 + (origin[1] if column == 3 else 0))
                        near(frame.origin_mm[2], 0.8)


class R2RoutingTests(unittest.TestCase):
    def test_defaults_false_and_session_routes_explicit_option(self):
        method = (transition_workflow.ModularCoreLayoutWorkflowSession
                  .preview_private_catalogue_crossover_chairs)
        for operation in (
            method, binding.preview_private_catalogue_crossover_chairs,
            singles.prepare_single_rails, RoutingBoundary().operation,
        ):
            self.assertIs(inspect.signature(operation).parameters[
                "include_r2_exit"].default, False)
        session = SimpleNamespace(
            module=object(),
            _private_catalogue_crossover_preview_factory=object(),
            routing_record=Mock(),
        )
        with patch.object(
            binding, "preview_private_catalogue_crossover_chairs",
            return_value="receipt",
        ) as operation:
            self.assertEqual(method(
                session, "document", "XO-001", "catalogue",
                paired_contexts_path="pairs", include_central_cc=True,
                include_check_ends=True, include_single_rail=True,
                include_r2_exit=True, correct_heel_l1=True,
            ), "receipt")
        self.assertIs(operation.call_args.kwargs["include_r2_exit"], True)
        self.assertIs(operation.call_args.kwargs["correct_heel_l1"], True)

    def test_invalid_options_stop_before_source_or_materialisation(self):
        for options in (
            *({"include_r2_exit": value} for value in (None, 0, 1, "true")),
            {"include_r2_exit": True, "include_single_rail": False},
            {"include_r2_exit": True, "include_check_ends": False},
            {"include_r2_exit": True, "include_central_cc": False},
            {"include_r2_exit": True, "paired_contexts_path": None},
        ):
            with self.subTest(options=options):
                boundary = RoutingBoundary()
                with self.assertRaises(ValueError):
                    boundary.run(adapter_fixture(), **options)
                boundary.materialise.assert_not_called()
                arguments = dict(
                    paired_contexts_path="pairs", include_central_cc=True,
                    include_check_ends=True, include_single_rail=True,
                )
                arguments.update(options)
                with patch.object(binding, "_open_source_context") as opened:
                    with self.assertRaises(ValueError):
                        binding.preview_private_catalogue_crossover_chairs(
                            object(), object(), "XO-001", "unused", Mock(),
                            **arguments,
                        )
                    opened.assert_not_called()
        for value in (None, 0, 1, "true"):
            with self.subTest(direct=value), self.assertRaises(ValueError):
                prepare(r2_source(), include_r2_exit=value)

    def test_adapter_routes_241_assemblies_and_keeps_heel_options(self):
        for corrected in (False, True):
            boundary = RoutingBoundary()
            groups = adapter_fixture(corrected=corrected)
            groups["SupplementS1"] += tuple(
                single(i, "S1") for i in sorted(R2_IDS)
            )
            result = boundary.run(groups, include_r2_exit=True,
                                  correct_heel_l1=corrected)
            identities = {
                p.position_id for placements, _spec in boundary.selections
                for p in placements
            }
            self.assertEqual(len(identities), 241)
            self.assertTrue(R2_IDS <= identities)
            supplement, = [
                (placements, spec) for placements, spec in boundary.selections
                if any(p.position_id in R2_IDS for p in placements)
            ]
            self.assertEqual(len(supplement[0]), 18)
            self.assertEqual(supplement[1]["model_sha256"], S1_SHA256)
            result.verify()
            boundary.source_check.assert_called_once_with()
            boundary.paired_checks.assert_called_once_with(
                boundary.paired_catalogue("pairs"),
            )

    def test_adapter_rejects_partial_duplicate_or_implicit_r2_groups(self):
        for defect in ("missing", "duplicate", "old-count", "implicit"):
            boundary = RoutingBoundary()
            groups = adapter_fixture()
            additions = tuple(single(i, "S1") for i in sorted(R2_IDS))
            if defect == "missing":
                additions = additions[:-1]
            elif defect == "duplicate":
                additions = additions[:-1] + additions[:1]
            elif defect == "old-count":
                additions = ()
            groups["SupplementS1"] += additions
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                boundary.run(groups, include_r2_exit=defect != "implicit")
            boundary.materialise.assert_not_called()

    def test_public_preview_accounts_only_four_new_identities(self):
        source = r2_source()
        module, document, signature, positions, timbers, _hosts = source
        document.Name = "Invented"
        accepted_ids = CORRECTED_IDS | UNCHANGED_HEEL_IDS
        originals, instances, previous = [], [], []
        for identity, record in positions.items():
            accepted = identity in accepted_ids
            record.update(deliberate_omission=False, key_direction_sign=0,
                          key_orientation="retained", centre_point=[0, 0],
                          key_orientation_classification="source")
            record.setdefault("chair_code", 1 if accepted else 5)
            record.setdefault("chair_code_label", "S1" if accepted else "L1")
            plan_record = {
                "chair_position_identity": identity, "centre_point": [0, 0],
            }
            (instances if accepted else originals).append(plan_record)
            if accepted:
                previous.append(S1Placement(
                    identity, record["rail_identity"],
                    record["timber_identity"],
                    (0, 0, 0.8), (1, 0), (0, 1),
                ))
        plan = {"instances": instances, "analytical_only": originals}
        before = copy.deepcopy((positions, timbers, plan))
        context = (signature, {"geometry_signature": "invented"},
                   {"future_chair_embed_depth": 0.2}, plan, [], timbers)
        create = Mock(side_effect=lambda _path, groups, _shapes, receipt,
                      verify, **options: (groups, receipt, verify, options))
        with ExitStack() as stack:
            for name, result in (
                ("_open_source_context", context),
                ("_require_p_crossover_context", {}),
                ("_whole_crossover_records", positions),
                ("_select_s1_s1j_positions", (tuple(previous), (), [])),
                ("_select_p_positions", ((), [], [], 0.8)),
                ("_context_shapes_and_verifier", ((), Mock())),
            ):
                stack.enter_context(patch.object(
                    binding, name, return_value=result,
                ))
            stack.enter_context(patch.object(
                binding, "_recover_positions",
                side_effect=lambda _m, _a, _p, _r, _t, values, remaining, _c:
                (values, remaining, []),
            ))
            for target, name, result in (
                (chair_pair_placement, "prepare_crossover_pairs",
                 ({}, {}, Mock())),
                (chair_check_placement, "prepare_central_checks",
                 ((), {}, {}, Mock())),
                (chair_check_end_placement, "prepare_check_ends",
                 ({}, {}, {}, Mock())),
            ):
                stack.enter_context(patch.object(
                    target, name, return_value=result,
                ))
            stack.enter_context(patch.object(
                singles, "prepare_catalogue_chair", side_effect=selection,
            ))
            preview = binding.preview_private_catalogue_crossover_chairs
            groups, receipt, verify, options = preview(
                module, document, "XO-001", "unused", create,
                paired_contexts_path="pairs", include_central_cc=True,
                include_check_ends=True, include_single_rail=True,
                include_r2_exit=True, correct_heel_l1=True,
            )
        self.assertEqual(len(groups["SupplementS1"]), 18)
        self.assertEqual(receipt["placement_count"], 50)
        self.assertEqual(receipt["represented_source_position_count"], 50)
        self.assertEqual(receipt["unrepresented_source_position_count"], 0)
        self.assertIs(options["include_r2_exit"], True)
        self.assertIs(options["correct_heel_l1"], True)
        selected = {r["position_id"]: r for r in receipt["selected_positions"]}
        for identity in R2_IDS:
            self.assertEqual(selected[identity]["family"], "S1")
            self.assertEqual(
                selected[identity]["chair_code"],
                positions[identity]["chair_code"],
            )
        self.assertEqual((positions, timbers, plan), before)
        with patch.object(singles, "verify_catalogue_sources"):
            verify()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(
        sys.modules[__name__],
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: four source-qualified R2 exit S1 chairs")
