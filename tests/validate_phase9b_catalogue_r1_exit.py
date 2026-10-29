#!/usr/bin/env python3
"""Check four opt-in R1 exit chairs without constructing native geometry.

Source-informed Templot 556b calculations, GPL-3.0-or-later; see NOTICE.md
and reference/PROVENANCE.md. Reuse the independently derived decimal rail
and component-frame oracles and existing routing fixtures. This reuse is
an independence limit. Native geometry, physical fit and GUI are not proved.
"""

from collections import Counter
from contextlib import ExitStack
import copy
from fractions import Fraction
import hashlib
import inspect
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
)
from validate_phase9b_catalogue_r2_exit import (  # noqa: E402
    R2_IDS,
    R2_STATION,
    r2_source,
)

RAILS = {2: "vee splice rail", 3: "vee point rail"}
FAMILIES = {2: "L1", 3: "S1J"}
TIMBERS = {"A": "XO-001:INHERITED-LONG:A:003",
           "B": "XO-001:INHERITED-LONG:B:009"}
R1_STATION = oracle.a_timber(oracle.SOURCE_PARAMETERS) + 175 / 3
MODEL_HASHES = {family: digest
                for family, _path, digest in oracle.MODEL_INPUTS}


def chair_identity(owner, rail):
    """Preserve the inherited timber and source rail identities."""
    return ("XO-001:chair:" + TIMBERS[owner].lower().replace(":", "-")
            + ":" + RAILS[rail].replace(" ", "-"))


R1_IDS = {chair_identity(owner, rail)
          for owner in ("A", "B") for rail in RAILS}


def r1_source():
    """Extend the retained R2 fixture by the four source-qualified records."""
    source = r2_source()
    layout = source[0].rea_c10_timber_layout
    source[0].rea_c10_timber_layout = lambda *args: [
        *layout(*args), {"identifier": "R1", "x": R1_STATION},
    ]
    for owner, timber_id in TIMBERS.items():
        timber = {"extended_source_timber_identity": f"XO-001:{owner}:R1",
                  "path_station": R1_STATION}
        source[4].append({"stable_identity": timber_id,
                          "source_configuration": timber})
        for rail, name in RAILS.items():
            identity = chair_identity(owner, rail)
            source[3][identity] = {
                "stable_chair_position_identity": identity,
                "prototype_timber_identifier": "R1", "rail_name": name,
                "parent_turnout_identity": f"XO-001-{owner}001",
                "timber_identity": timber_id,
                "rail_identity": f"XO-001-{owner}001:rail:"
                + name.replace(" ", "-"),
                "special_assignment_deferred": True,
                "chair_code": 25 if rail == 2 else 26,
                "chair_code_label": "AB" if rail == 2 else "BB/BC",
                "source_configuration": {"timber": copy.deepcopy(timber)},
            }
    return source


def catalogue(_path, family, **_kwargs):
    """Keep retained model identities while stubbing native model loading."""
    return SimpleNamespace(label=family, model_sha256=MODEL_HASHES[family],
                           context="retained-S1-L1-reference-package")


def prepare_r1(source, **options):
    with patch.object(singles, "prepare_catalogue_chair",
                      side_effect=catalogue):
        return singles.prepare_single_rails(*source[:5], 0.8, "unused",
                                            **options)


def r1_adapter_fixture(*, corrected=False, include_r2=False):
    groups = adapter_fixture(corrected=corrected)
    if include_r2:
        groups["SupplementS1"] += tuple(
            single(i, "S1") for i in sorted(R2_IDS)
        )
    for rail, group in ((2, "L1"), (3, "SupplementS1J")):
        groups[group] += tuple(
            single(chair_identity(owner, rail), FAMILIES[rail])
            for owner in ("A", "B")
        )
    return groups


class R1SourceTests(unittest.TestCase):
    @unittest.skipUnless(ARCHIVE.is_file(), "private 556b archive unavailable")
    def test_frozen_source_joint_before_asymmetric_vee_override(self):
        self.assertEqual(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
                         ARCHIVE_SHA256)
        with zipfile.ZipFile(ARCHIVE) as archive:
            name, = [n for n in archive.namelist()
                     if n.rsplit("/", 1)[-1] == "math_unit.pas"]
            raw = archive.read(name)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         SOURCE_HASHES["math_unit.pas"])
        lines = raw.decode("latin-1").splitlines()
        joint = "\n".join(lines[29656:29665])
        for token in ("(timb_str='X')", "xtb>(mvjp_nx-(mvj_sp+1)*inscale)",
                      "xtb<(mvjp_nx+(mvj_sp+1)*inscale)",
                      "chairing_dims2:=S1J_chairing_dims",
                      "chairing_dims3:=S1J_chairing_dims"):
            self.assertIn(token, joint)
        vee = "\n".join(lines[29759:29804])
        self.assertIn("aq2offset(xtimbcl-S1_chair_halfwide*inscale", vee)
        self.assertIn("chair_space_y<(S1_chair_outlong*inscale*2+inscale/2)",
                      vee)
        self.assertLess(vee.index("chairing_dims2:=L1_chairing_dims"),
                        vee.index("chair_space_y<(S1_chair_outlong*inscale+"
                                  "L1_chair_outlong*inscale+inscale/2)"))
        self.assertIn("chairing_dims3:=L1_chairing_dims", vee)

    def test_source_station_gap_and_retained_fixing_inventory(self):
        # Frozen B15 stations and the decimal source oracle differ only
        # within the already accepted finite-arithmetic comparison budget.
        budget = 128 * sys.float_info.epsilon * 1000
        self.assertLessEqual(abs(R1_STATION - 345.5662337705479), budget)
        self.assertEqual(R2_STATION - R1_STATION, 10.0)
        low, high = oracle.joint_window(oracle.SOURCE_PARAMETERS)
        self.assertLess(low, R1_STATION)
        self.assertLess(R1_STATION, high)
        gap = oracle.source_rail_pose(
            oracle.SOURCE_PARAMETERS, R1_STATION - 4 / 3, 2,
        )["y_mm"] - 16.5
        self.assertLessEqual(abs(gap - 6.084268307611648), budget)
        self.assertGreater(gap, float(Fraction(67, 12)))
        self.assertLess(gap, float(Fraction(19, 3)))
        self.assertEqual(len(R1_IDS), 4)
        for rail, count in ((2, 4), (3, 3)):
            self.assertEqual(len(oracle.dimensions(FAMILIES[rail])[
                "fixing_centres_mm"]), count)


class R1BindingTests(unittest.TestCase):
    def test_four_additions_preserve_all_previous_option_combinations(self):
        for corrected in (False, True):
            for r2 in (False, True):
                with self.subTest(corrected=corrected, r2=r2):
                    source = r1_source()
                    before = copy.deepcopy(source[3:5])
                    options = dict(correct_heel_l1=corrected,
                                   include_r2_exit=r2)
                    baseline, old_witnesses, _ = prepare_r1(source, **options)
                    groups, witnesses, _ = prepare_r1(
                        source, include_r1_exit=True, **options,
                    )
                    self.assertEqual({k: len(v) for k, v in groups.items()},
                                     {"SupplementS1": 18 if r2 else 14,
                                      "SupplementS1J": 6,
                                      "L1": 28 if corrected else 18})
                    self.assertEqual(set(witnesses) - set(old_witnesses),
                                     R1_IDS)
                    for name, old in baseline.items():
                        self.assertEqual(tuple(p for p in groups[name]
                                               if p.position_id not in R1_IDS),
                                         old)
                    for identity, witness in old_witnesses.items():
                        self.assertEqual(witnesses[identity], witness)
                    for owner in ("A", "B"):
                        for rail, family in FAMILIES.items():
                            witness = witnesses[chair_identity(owner, rail)]
                            self.assertEqual(witness["family"], family)
                            self.assertEqual(witness["source_model_sha256"],
                                             MODEL_HASHES[family])
                            self.assertEqual(witness["physical_fit"],
                                             "NOT_PROVED")
                    self.assertEqual(source[3:5], before)

    def test_invalid_source_records_are_rejected(self):
        for defect in (
            "missing", "duplicate", "identity", "owner", "rail-name",
            "rail-owner", "deferred", "station", "nonfinite", "source-owner",
            "literal-R", "endpoint", "local-source",
        ):
            with self.subTest(defect=defect):
                source = r1_source()
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
                        math.nan if defect == "nonfinite" else R1_STATION + 1
                    )
                elif defect == "source-owner":
                    timber["source_configuration"][
                        "extended_source_timber_identity"] = "XO-001:B:R1"
                elif defect == "literal-R":
                    record["prototype_timber_identifier"] = "R"
                elif defect == "endpoint":
                    record["timber_identity"] = "XO-001:ENVELOPE:001"
                else:
                    timber["source_configuration"] = {"local_x": R1_STATION}
                for position in source[3].values():
                    if position["timber_identity"] == TIMBERS["A"]:
                        position["source_configuration"]["timber"] = (
                            copy.deepcopy(timber["source_configuration"])
                        )
                with self.assertRaises(ValueError):
                    prepare_r1(source, include_r1_exit=True)

    def test_clearance_joint_and_source_branch_boundaries(self):
        dimensions = {"a_timber_x": oracle.a_timber(oracle.SOURCE_PARAMETERS)}

        def family(station, rail, gauge_y, branch="turnoutst_main"):
            with patch.object(singles, "_source_pose", return_value=(
                math.atan2(1, 10), gauge_y, branch,
            )) as pose:
                result = singles._family(None, dimensions, "R1", station, rail)
                pose.assert_called_once_with(None, dimensions,
                                             station - 4 / 3, 2)
                return result

        lower, upper = Fraction(67, 12), Fraction(19, 3)
        for threshold in (lower, upper):
            centre = float(Fraction(33, 2) + threshold)
            admitted_results = set()
            for y in (math.nextafter(centre, -math.inf), centre,
                      math.nextafter(centre, math.inf)):
                gap = Fraction.from_float(y) - Fraction(33, 2)
                admitted = lower <= gap < upper
                admitted_results.add(admitted)
                for rail, expected in FAMILIES.items():
                    with self.subTest(threshold=threshold, y=y, rail=rail):
                        if admitted:
                            self.assertEqual(family(R1_STATION, rail, y),
                                             expected)
                        else:
                            with self.assertRaises(ValueError):
                                family(R1_STATION, rail, y)
            self.assertEqual(admitted_results, {False, True})
        low, high = oracle.joint_window(oracle.SOURCE_PARAMETERS)
        for station, admitted in (
            (math.nextafter(low, -math.inf), False), (low, False),
            (math.nextafter(low, high), True), (R1_STATION, True),
            (math.nextafter(high, low), True), (high, False),
            (math.nextafter(high, math.inf), False),
        ):
            for rail, expected in FAMILIES.items():
                with self.subTest(station=station, rail=rail):
                    if admitted:
                        self.assertEqual(family(station, rail, 22.5), expected)
                    else:
                        with self.assertRaises(ValueError):
                            family(station, rail, 22.5)
        for rail, branch in ((2, "radcurve"), (3, "radcurve"),
                             (2, "main_straight"), (3, "unknown"),
                             (1, "turnoutst_main"), (4, "turnoutst_main")):
            with self.subTest(rail=rail, branch=branch):
                with self.assertRaises(ValueError):
                    family(R1_STATION, rail, 22.5, branch)

    def test_frames_for_both_directions_and_signed_curvature(self):
        def near(actual, expected):
            budget = 128 * sys.float_info.epsilon * max(
                1000, abs(actual), abs(expected),
            )
            self.assertLessEqual(abs(actual - expected), budget)

        for radius in (None, 600, 900, 1800, -600, -900, -1800):
            source = r1_source()

            def host(_data, station):
                angle = 0.0 if radius is None else station / radius
                point = (
                    (station, 0.0) if radius is None else
                    (radius * math.sin(angle), radius * (1 - math.cos(angle)))
                )
                return SimpleNamespace(x=point[0], y=point[1]), angle

            source[0].interpolate_alignment_station = host
            groups, witnesses, _ = prepare_r1(source, include_r1_exit=True)
            placements = {p.position_id: p
                          for group in groups.values() for p in group}
            for owner in ("A", "B"):
                direction = 1 if owner == "A" else -1
                chainage = 500 + direction * R1_STATION
                point, heading = host(None, chainage)
                heading += math.pi if direction == -1 else 0
                c, s = math.cos(heading), math.sin(heading)
                origin = (point.x - 8.25 * s, point.y + 8.25 * c)
                for rail, family_name in FAMILIES.items():
                    identity = chair_identity(owner, rail)
                    pose = oracle.source_rail_pose(
                        oracle.SOURCE_PARAMETERS, R1_STATION, rail,
                    )
                    matrices = oracle.local_frames(family_name, rail,
                                                   pose["k_rad"], pose["y_mm"])
                    witness = witnesses[identity]
                    placement = placements[identity]
                    self.assertEqual(witness["source_station_mm"], R1_STATION)
                    self.assertEqual(witness["host_station_mm"], chainage)
                    self.assertEqual(witness["source_rail_code"], rail)
                    self.assertEqual(witness["source_branch"],
                                     pose["source_branch"])
                    self.assertEqual(len(placement.fixing_frames),
                                     4 if rail == 2 else 3)
                    self.assertEqual(placement.rail_id,
                                     source[3][identity]["rail_identity"])
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

    def test_late_model_and_host_verification_remains_live(self):
        source = r1_source()
        _, _, verify = prepare_r1(source, include_r1_exit=True)
        with patch.object(singles, "verify_catalogue_sources") as checked:
            verify()
            self.assertEqual(Counter(c.args[0].label
                                     for c in checked.call_args_list),
                             {"S1": 1, "S1J": 1, "L1": 1})
        with patch.object(singles, "verify_catalogue_sources",
                          side_effect=ValueError("catalogue changed")):
            with self.assertRaisesRegex(ValueError, "catalogue changed"):
                verify()
        source[-1]["HostB"]["points"][0].x += 1
        with patch.object(singles, "verify_catalogue_sources"):
            with self.assertRaisesRegex(ValueError, "host changed"):
                verify()


class R1RoutingTests(unittest.TestCase):
    def test_defaults_false_and_explicit_session_routing(self):
        method = (transition_workflow.ModularCoreLayoutWorkflowSession
                  .preview_private_catalogue_crossover_chairs)
        for operation in (
            method, binding.preview_private_catalogue_crossover_chairs,
            singles.prepare_single_rails, RoutingBoundary().operation,
        ):
            self.assertIs(inspect.signature(operation).parameters[
                "include_r1_exit"].default, False)
        session = SimpleNamespace(
            module=object(), routing_record=Mock(),
            _private_catalogue_crossover_preview_factory=object(),
        )
        for corrected in (False, True):
            for r2 in (False, True):
                with patch.object(
                    binding, "preview_private_catalogue_crossover_chairs",
                    return_value="receipt",
                ) as operation:
                    self.assertEqual(method(
                        session, "document", "XO-001", "catalogue",
                        paired_contexts_path="pairs", include_central_cc=True,
                        include_check_ends=True, include_single_rail=True,
                        include_r1_exit=True, include_r2_exit=r2,
                        correct_heel_l1=corrected,
                    ), "receipt")
                options = operation.call_args.kwargs
                self.assertIs(options["include_r1_exit"], True)
                self.assertEqual("include_r2_exit" in options, r2)
                self.assertEqual("correct_heel_l1" in options, corrected)
                self.assertIs(options.get("include_r2_exit", False), r2)
                self.assertIs(options.get("correct_heel_l1", False), corrected)

    def test_invalid_options_stop_before_source_or_materialisation(self):
        for options in (
            *({"include_r1_exit": value} for value in (None, 0, 1, "true")),
            {"include_r1_exit": True, "include_single_rail": False},
            {"include_r1_exit": True, "include_check_ends": False},
            {"include_r1_exit": True, "include_central_cc": False},
            {"include_r1_exit": True, "paired_contexts_path": None},
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
                prepare_r1(r1_source(), include_r1_exit=value)

    def test_adapter_counts_all_options_and_reverifies_sources(self):
        for corrected in (False, True):
            for r2 in (False, True):
                boundary = RoutingBoundary()
                result = boundary.run(r1_adapter_fixture(corrected=corrected,
                                                          include_r2=r2),
                                      include_r1_exit=True, include_r2_exit=r2,
                                      correct_heel_l1=corrected)
                identities = {p.position_id for group, _ in boundary.selections
                              for p in group}
                self.assertEqual(len(identities), 245 if r2 else 241)
                self.assertTrue(R1_IDS <= identities)
                for rail, family_name in FAMILIES.items():
                    group, specification = next(
                        (group, spec) for group, spec in boundary.selections
                        if chair_identity("A", rail)
                        in {p.position_id for p in group}
                    )
                    self.assertEqual(len(group), (28 if corrected else 18)
                                     if rail == 2 else 6)
                    self.assertEqual(specification["model_sha256"],
                                     MODEL_HASHES[family_name])
                result.verify()
                boundary.source_check.assert_called_once_with()
                boundary.paired_checks.assert_called_once()
                boundary.source_check.side_effect = ValueError(
                    "source changed",
                )
                with self.assertRaisesRegex(ValueError, "source changed"):
                    result.verify()

    def test_adapter_rejects_incomplete_duplicate_or_implicit_groups(self):
        for defect in (
            "missing-L1", "missing-S1J", "duplicate", "overlap", "implicit",
        ):
            boundary = RoutingBoundary()
            groups = r1_adapter_fixture()
            if defect.startswith("missing"):
                name = "L1" if defect == "missing-L1" else "SupplementS1J"
                groups[name] = groups[name][:-1]
            elif defect == "duplicate":
                groups["L1"] = groups["L1"][:-1] + groups["L1"][-2:-1]
            elif defect == "overlap":
                groups["L1"] = groups["L1"][:-1] + (single("base:0", "L1"),)
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                boundary.run(groups, include_r1_exit=defect != "implicit")
            boundary.materialise.assert_not_called()

    def test_public_preview_accounts_only_four_new_source_identities(self):
        source = r1_source()
        module, document, signature, positions, timbers, _ = source
        document.Name = "Invented"
        originals, instances, previous = [], [], []
        for identity, record in positions.items():
            accepted = identity in CORRECTED_IDS | UNCHANGED_HEEL_IDS
            record.update(deliberate_omission=False, key_direction_sign=0,
                          key_orientation="retained", centre_point=[0, 0],
                          key_orientation_classification="source")
            record.setdefault("chair_code", 1 if accepted else 5)
            record.setdefault("chair_code_label", "S1" if accepted else "L1")
            (instances if accepted else originals).append({
                "chair_position_identity": identity, "centre_point": [0, 0],
            })
            if accepted:
                previous.append(S1Placement(identity, record["rail_identity"],
                                            record["timber_identity"],
                                            (0, 0, 0.8), (1, 0), (0, 1)))
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
                stack.enter_context(patch.object(binding, name,
                                                 return_value=result))
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
                stack.enter_context(patch.object(target, name,
                                                 return_value=result))
            stack.enter_context(patch.object(
                singles, "prepare_catalogue_chair", side_effect=catalogue,
            ))
            groups, receipt, verify, options = (
                binding.preview_private_catalogue_crossover_chairs(
                    module, document, "XO-001", "unused", create,
                    paired_contexts_path="pairs", include_central_cc=True,
                    include_check_ends=True, include_single_rail=True,
                    include_r1_exit=True, include_r2_exit=True,
                    correct_heel_l1=True,
                )
            )
        self.assertEqual(len(groups["SupplementS1J"]), 6)
        self.assertEqual(len(groups["L1"]), 28)
        self.assertEqual(receipt["placement_count"], 54)
        self.assertEqual(receipt["represented_source_position_count"], 54)
        self.assertEqual(receipt["unrepresented_source_position_count"], 0)
        self.assertIs(options["include_r1_exit"], True)
        selected = {r["position_id"]: r for r in receipt["selected_positions"]}
        for owner in ("A", "B"):
            for rail, family_name in FAMILIES.items():
                identity = chair_identity(owner, rail)
                self.assertEqual(selected[identity]["family"], family_name)
                self.assertEqual(selected[identity]["chair_code"],
                                 positions[identity]["chair_code"])
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
    print("PASS: four source-qualified R1 exit L1/S1J chairs")
