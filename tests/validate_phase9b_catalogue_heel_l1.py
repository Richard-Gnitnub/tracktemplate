#!/usr/bin/env python3
"""Check the ten opt-in heel corrections without native geometry.

Source-informed tests for Templot 556b, copyright Martin Wynne and
OpenTemplot contributors, GPL-3.0-or-later. See NOTICE.md and
reference/PROVENANCE.md. Existing decimal rail calculations are reused;
the straight-rail component frames below are independently hand-derived.
This is no native, physical-fit, rights or whole-host qualification.
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
import re
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
from paired_switch_source_oracle import SOURCE_HASHES  # noqa: E402
from validate_phase9b_catalogue_single_rail import (  # noqa: E402
    single_source,
)

ARCHIVE = ROOT / "reference/t5_files_556b_06_feb_2025.zip"
ARCHIVE_SHA256 = (
    "2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3"
)
L1_SHA256 = (
    "a0289c046b6ae8cb1e2df88a8f6a1f3f0dc79f7a0ae1870d0b3b13154e0eb042"
)
RAIL_NAMES = {
    1: "main-side stock rail",
    3: "straight switch and closure rail",
}
HEEL_CONTEXTS = (("S13", 1), ("S13", 3), ("T1", 1), ("T1", 3), ("T2", 3))


def identity(owner, timber, rail):
    """Return the preserved canonical chair identity."""
    return (
        f"XO-001:chair:xo-001-{owner.lower()}-{timber.lower()}:"
        + RAIL_NAMES[rail].replace(" ", "-")
    )


CORRECTED_IDS = {
    identity(owner, timber, rail)
    for owner in ("A", "B")
    for timber, rail in HEEL_CONTEXTS
}
UNCHANGED_HEEL_IDS = {identity(owner, "T2", 1) for owner in ("A", "B")}


def heel_source():
    """Extend the old invented fixture with accepted heel identities.

    The two T2 rail-1 records are deliberate negative controls. All twelve
    records retain their original S1 assignment; only ten are eligible for
    the new derived preview. The original 34 records are unchanged.
    """
    source = single_source()
    for owner in ("A", "B"):
        for timber in ("S13", "T1", "T2"):
            for rail, name in RAIL_NAMES.items():
                timber_id = f"XO-001:{owner}:{timber}"
                source_config = {
                    "local_x": dict(oracle.NOMINAL_STATIONS)[timber]
                }
                chair_id = identity(owner, timber, rail)
                source[3][chair_id] = {
                    "stable_chair_position_identity": chair_id,
                    "prototype_timber_identifier": timber,
                    "rail_name": name,
                    "parent_turnout_identity": f"XO-001-{owner}001",
                    "timber_identity": timber_id,
                    "rail_identity": owner + ":" + name,
                    "special_assignment_deferred": False,
                    "chair_code": 1,
                    "chair_code_label": "S1",
                    "source_configuration": {"timber": source_config},
                }
    return source


def selection(_path, family, **_kwargs):
    """Use a catalogue stand-in; geometry admission remains a host duty."""
    return SimpleNamespace(
        label=family,
        model_sha256=L1_SHA256 if family == "L1" else "invented-" + family,
        context="retained-S1-L1-reference-package",
    )


def corrected(source):
    with patch.object(singles, "prepare_catalogue_chair", side_effect=selection):
        return singles.prepare_single_rails(
            *source[:5], 0.8, "unused", correct_heel_l1=True,
        )


def source_heel_choices(gap):
    """Evaluate the frozen Pascal inequalities using exact rational inputs.

    Return rails 1 and 3 only. This oracle does not qualify arbitrary
    timber stations or replace the subsequent closure-rail predicates.
    """
    if gap < Fraction(43, 12):
        return "PLR3", None
    if gap < 5:
        return ("L1" if gap < Fraction(53, 12) else "S1"), "L1"
    return "S1", "S1"


class HeelSourceTests(unittest.TestCase):
    @unittest.skipUnless(ARCHIVE.is_file(), "private 556b archive unavailable")
    def test_frozen_source_identity_dimensions_and_predicate_order(self):
        self.assertEqual(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
                         ARCHIVE_SHA256)
        with zipfile.ZipFile(ARCHIVE) as archive:
            texts = {}
            for name, digest in (
                ("math_unit.pas", SOURCE_HASHES["math_unit.pas"]),
                ("chairs_unit.pas", SOURCE_HASHES["chairs_unit.pas"]),
            ):
                matches = [n for n in archive.namelist()
                           if n.rsplit("/", 1)[-1] == name]
                self.assertEqual(len(matches), 1)
                raw = archive.read(matches[0])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                texts[name] = raw.decode("latin-1")
        math_lines = texts["math_unit.pas"].splitlines()
        heel = "\n".join(math_lines[29550:29585])
        self.assertIn("tbn>(csi.num_slide_chairs+", heel)
        self.assertIn("aq3offset(xtimbcl-S1_chair_halfwide*inscale", heel)
        for expression in (
            "L1_chair_outlong*inscale+L1_chair_inlong*inscale+inscale/4",
            "S1_chair_outlong*inscale+S1_chair_inlong*inscale+inscale/2",
            "S1_chair_outlong*inscale+L1_chair_inlong*inscale+inscale/2",
        ):
            self.assertIn("chair_space_y<(" + expression + ")", heel)
        self.assertLess(heel.index("chairing_dims3:=L1_chairing_dims"),
                        heel.index("chairing_dims1:=L1_chairing_dims"))
        closure = "\n".join(math_lines[29589:29642])
        self.assertIn("g-aq2offset(xtimbcl+S1_chair_halfwide*inscale", closure)
        self.assertIn("S1_chair_inlong*inscale*2+inscale/2", closure)
        dimensions = texts["chairs_unit.pas"].split("implementation", 1)[1]
        dimensions = dimensions.split("procedure init_3d_rea", 1)[0]
        dimensions = re.sub(r"\{.*?\}", "", dimensions, flags=re.DOTALL)
        for name, expected in (
            ("S1_chair_outlong", Fraction(37, 4)),
            ("S1_chair_inlong", Fraction(21, 4)),
            ("S1_chair_halfwide", Fraction(4)),
            ("L1_chair_outlong", Fraction(7)),
            ("L1_chair_inlong", Fraction(7, 2)),
            ("L1_inbolt_1x", Fraction(-15, 4)),
            ("L1_inbolt_2x", Fraction(15, 4)),
            ("L1_outbolt_1x", Fraction(-15, 4)),
            ("L1_outbolt_2x", Fraction(15, 4)),
            ("L1_bolts_from_end", Fraction(7, 4)),
        ):
            self.assertEqual(oracle._assignment(dimensions, name), expected)

    def test_source_boundaries_and_nominal_ten_identity_set(self):
        step = Fraction(1, 10**9)
        for boundary, before, exact, after in (
            (Fraction(43, 12), ("PLR3", None), ("L1", "L1"), ("L1", "L1")),
            (Fraction(53, 12), ("L1", "L1"), ("S1", "L1"), ("S1", "L1")),
            (Fraction(5), ("S1", "L1"), ("S1", "S1"), ("S1", "S1")),
        ):
            self.assertEqual(source_heel_choices(boundary - step), before)
            self.assertEqual(source_heel_choices(boundary), exact)
            self.assertEqual(source_heel_choices(boundary + step), after)
        found = set()
        for timber, station in oracle.NOMINAL_STATIONS[:3]:
            gap = oracle.source_rail_pose(
                oracle.SOURCE_PARAMETERS, station - 4 / 3, 4,
            )["y_mm"] - 16.5
            for rail, family in zip((1, 3), source_heel_choices(gap)):
                if family == "L1":
                    found.update(identity(owner, timber, rail)
                                 for owner in ("A", "B"))
            if timber.startswith("T"):
                closure_gap = 16.5 - oracle.source_rail_pose(
                    oracle.SOURCE_PARAMETERS, station + 4 / 3, 2,
                )["y_mm"]
                self.assertGreater(closure_gap, 11 / 3)
        self.assertEqual(found, CORRECTED_IDS)
        self.assertEqual(len(found), 10)


class HeelBindingTests(unittest.TestCase):
    def test_default_keeps_original_34_and_explicit_option_replaces_ten(self):
        source = heel_source()
        before = copy.deepcopy(source[3:5])
        with patch.object(singles, "prepare_catalogue_chair", side_effect=selection):
            baseline, baseline_witnesses, _verify = singles.prepare_single_rails(
                *source[:5], 0.8, "unused",
            )
        groups, witnesses, _verify = corrected(source)
        self.assertEqual({name: len(items) for name, items in groups.items()},
                         {"SupplementS1": 14, "SupplementS1J": 4, "L1": 26})
        self.assertEqual(set(witnesses) - set(baseline_witnesses), CORRECTED_IDS)
        self.assertFalse(set(witnesses) & UNCHANGED_HEEL_IDS)
        for name, old in baseline.items():
            self.assertEqual(
                tuple(p for p in groups[name] if p.position_id not in CORRECTED_IDS),
                old,
            )
        for chair_id in baseline_witnesses:
            self.assertEqual(witnesses[chair_id], baseline_witnesses[chair_id])
        for chair_id in CORRECTED_IDS:
            witness = witnesses[chair_id]
            self.assertEqual(witness["original_family"], "S1")
            self.assertEqual(witness["family"], "L1")
            self.assertEqual(witness["source_model_sha256"], L1_SHA256)
            self.assertEqual(witness["source_branch"], "main_straight")
            self.assertEqual(witness["source_angle_rad"], 0)
            self.assertEqual(witness["physical_fit"], "NOT_PROVED")
        self.assertEqual(source[3:5], before)

    def test_changed_or_partial_accepted_identity_is_rejected(self):
        for change in ("missing", "duplicate", "owner", "rail", "label",
                       "code", "deferred", "station", "nonfinite"):
            with self.subTest(change=change):
                source = heel_source()
                chair_id = identity("A", "T1", 3)
                record = source[3][chair_id]
                if change == "missing":
                    del source[3][chair_id]
                elif change == "duplicate":
                    source[3]["duplicate"] = copy.deepcopy(record)
                elif change == "owner":
                    record["parent_turnout_identity"] = "Other"
                elif change == "rail":
                    record["rail_name"] = RAIL_NAMES[1]
                elif change == "label":
                    record["chair_code_label"] = "S1J"
                elif change == "code":
                    record["chair_code"] = 7
                elif change == "deferred":
                    record["special_assignment_deferred"] = True
                else:
                    record["source_configuration"]["timber"]["local_x"] = (
                        math.nan if change == "nonfinite" else 999
                    )
                with self.assertRaises(ValueError):
                    corrected(source)

    def test_original_catalogue_and_host_are_reverified(self):
        source = heel_source()
        _groups, _witnesses, verify = corrected(source)
        with patch.object(singles, "verify_catalogue_sources") as verify_model:
            verify()
            self.assertEqual(Counter(call.args[0].label
                                     for call in verify_model.call_args_list),
                             {"S1": 1, "S1J": 1, "L1": 1})
        with patch.object(singles, "verify_catalogue_sources",
                          side_effect=ValueError("catalogue changed")):
            with self.assertRaisesRegex(ValueError, "catalogue changed"):
                verify()
        source[-1]["HostB"]["points"][0].x += 1
        with patch.object(singles, "verify_catalogue_sources"):
            with self.assertRaisesRegex(ValueError, "host changed"):
                verify()

    def test_all_ten_body_and_fixing_frames_against_hand_derived_marks(self):
        # This reuses the accepted finite arithmetic comparison budget.
        # It is not a physical-fit tolerance or whole-host admission.
        def near(actual, expected):
            budget = 128 * sys.float_info.epsilon * max(
                1000, abs(actual), abs(expected),
            )
            self.assertLessEqual(abs(actual - expected), budget)

        for radius in (None, 600, 900, 1800, -600, -900, -1800):
            source = heel_source()

            def host(_data, station):
                if radius is None:
                    return SimpleNamespace(x=station, y=0.0), 0.0
                angle = station / radius
                return SimpleNamespace(
                    x=radius * math.sin(angle),
                    y=radius * (1 - math.cos(angle)),
                ), angle

            source[0].interpolate_alignment_station = host
            groups, witnesses, _verify = corrected(source)
            frames = {p.position_id: p for p in groups["L1"]}
            for chair_id in sorted(CORRECTED_IDS):
                placement = frames[chair_id]
                witness = witnesses[chair_id]
                position = source[3][chair_id]
                rail = 1 if position["rail_name"] == RAIL_NAMES[1] else 3
                self.assertEqual(witness["source_rail_code"], rail)
                station = dict(oracle.NOMINAL_STATIONS)[
                    position["prototype_timber_identifier"]
                ]
                reverse = position["parent_turnout_identity"] == "XO-001-B001"
                chainage = 500 - station if reverse else 500 + station
                self.assertEqual(witness["source_station_mm"], station)
                self.assertEqual(witness["host_station_mm"], chainage)
                self.assertEqual(witness["source_gauge_y_mm"],
                                 0 if rail == 1 else 16.5)
                point, heading = host(None, chainage)
                if reverse:
                    heading += math.pi
                tangent = (math.cos(heading), math.sin(heading))
                normal = (-tangent[1], tangent[0])
                body_y = 0.45 if rail == 1 else -16.95
                local_y = (body_y, -97 / 60, -97 / 60, 61 / 20, 61 / 20)
                if rail == 3:
                    local_y = (body_y,) * 5
                signs = ((1,) if rail == 1 else (-1,)) + (-1,) * 4
                self.assertEqual(len(placement.fixing_frames), 4)
                for frame, y, sign in zip(
                    (placement, *placement.fixing_frames), local_y, signs,
                ):
                    self.assertEqual(frame.position_id, chair_id)
                    self.assertEqual(frame.rail_id, placement.rail_id)
                    self.assertEqual(frame.timber_id, placement.timber_id)
                    near(frame.origin_mm[0], point.x + (y + 8.25) * normal[0])
                    near(frame.origin_mm[1], point.y + (y + 8.25) * normal[1])
                    near(frame.origin_mm[2], 0.8)
                    for axis in (0, 1):
                        near(frame.x_axis[axis], sign * tangent[axis])
                        near(frame.y_axis[axis], sign * normal[axis])


class HeelRoutingTests(unittest.TestCase):
    def test_defaults_are_false_and_session_forwards_explicit_option(self):
        method = (
            transition_workflow.ModularCoreLayoutWorkflowSession
            .preview_private_catalogue_crossover_chairs
        )
        for operation in (method, binding.preview_private_catalogue_crossover_chairs,
                          singles.prepare_single_rails):
            self.assertIs(inspect.signature(operation).parameters[
                "correct_heel_l1"].default, False)
        session = SimpleNamespace(
            module=object(), _private_catalogue_crossover_preview_factory=object(),
            routing_record=Mock(),
        )
        with patch.object(binding, "preview_private_catalogue_crossover_chairs",
                          return_value="receipt") as operation:
            self.assertEqual(method(
                session, "document", "XO-001", "catalogue",
                paired_contexts_path="pairs", include_central_cc=True,
                include_check_ends=True, include_single_rail=True,
                correct_heel_l1=True,
            ), "receipt")
        self.assertIs(operation.call_args.kwargs["correct_heel_l1"], True)
        self.assertIs(operation.call_args.kwargs["include_single_rail"], True)

    def test_option_rejects_non_boolean_and_missing_supplement_before_source(self):
        create = Mock()
        with patch.object(binding, "_open_source_context") as opened:
            for value in (1, 0, None, "yes", (), []):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    binding.preview_private_catalogue_crossover_chairs(
                        object(), object(), "XO-001", "unused", create,
                        correct_heel_l1=value,
                    )
            with self.assertRaises(ValueError):
                binding.preview_private_catalogue_crossover_chairs(
                    object(), object(), "XO-001", "unused", create,
                    paired_contexts_path="pairs", include_central_cc=True,
                    include_check_ends=True, correct_heel_l1=True,
                )
        opened.assert_not_called()
        create.assert_not_called()

    def test_whole_routing_removes_only_ten_s1_and_preserves_canonical_records(self):
        source = heel_source()
        module, document, signature, positions, timbers, _data = source
        document.Name = "Invented"
        originals = []
        instances = []
        old_s1 = []
        for chair_id, position in positions.items():
            accepted = chair_id in CORRECTED_IDS | UNCHANGED_HEEL_IDS
            position.update(
                chair_code=1 if accepted else 5,
                chair_code_label="S1" if accepted else "L1",
                deliberate_omission=False, key_direction_sign=0,
                key_orientation="retained", key_orientation_classification="source",
                centre_point=[0, 0],
            )
            record = {"chair_position_identity": chair_id,
                      "centre_point": [0, 0]}
            (instances if accepted else originals).append(record)
            if accepted:
                old_s1.append(S1Placement(
                    chair_id, position["rail_identity"], position["timber_identity"],
                    (0, 0, 0.8), (1, 0), (0, 1),
                ))
        plan = {"instances": instances, "analytical_only": originals}
        before = copy.deepcopy((positions, timbers, plan))
        context = (signature, {"geometry_signature": "invented"},
                   {"future_chair_embed_depth": 0.2}, plan, [], timbers)
        create = Mock(side_effect=lambda _path, groups, _shapes, receipt,
                      _verify, **options: (groups, receipt, options))
        with ExitStack() as stack:
            for name, result in (
                ("_open_source_context", context),
                ("_require_p_crossover_context", {}),
                ("_whole_crossover_records", positions),
                ("_select_s1_s1j_positions", (tuple(old_s1), (), [])),
                ("_select_p_positions", ((), [], [], 0.8)),
                ("_context_shapes_and_verifier", ((), Mock())),
            ):
                stack.enter_context(patch.object(binding, name, return_value=result))
            stack.enter_context(patch.object(
                binding, "_recover_positions",
                side_effect=lambda _m, _a, _p, _r, _t, values, remaining, _c:
                (values, remaining, []),
            ))
            for module_to_patch, name, result in (
                (chair_pair_placement, "prepare_crossover_pairs", ({}, {}, Mock())),
                (chair_check_placement, "prepare_central_checks", ((), {}, {}, Mock())),
                (chair_check_end_placement, "prepare_check_ends", ({}, {}, {}, Mock())),
            ):
                stack.enter_context(patch.object(module_to_patch, name,
                                                return_value=result))
            stack.enter_context(patch.object(singles, "prepare_catalogue_chair",
                                            side_effect=selection))
            groups, receipt, options = binding.preview_private_catalogue_crossover_chairs(
                module, document, "XO-001", "unused", create,
                paired_contexts_path="pairs", include_central_cc=True,
                include_check_ends=True, include_single_rail=True,
                correct_heel_l1=True,
            )
        self.assertEqual({p.position_id for p in groups["S1"]}, UNCHANGED_HEEL_IDS)
        self.assertEqual(groups["S1"], tuple(p for p in old_s1
                                           if p.position_id in UNCHANGED_HEEL_IDS))
        self.assertEqual(len(groups["L1"]), 26)
        placed = [p.position_id for values in groups.values() for p in values]
        self.assertEqual(len(placed), len(set(placed)))
        self.assertEqual(set(placed), set(positions))
        self.assertEqual(receipt["placement_count"], 46)
        self.assertEqual(receipt["excluded_position_count"], 0)
        self.assertEqual(receipt["source_document_mutation"], False)
        selected = {p["position_id"]: p for p in receipt["selected_positions"]}
        for chair_id in CORRECTED_IDS:
            self.assertEqual(selected[chair_id]["family"], "L1")
            self.assertEqual(selected[chair_id]["original_family"], "S1")
            self.assertEqual(selected[chair_id]["chair_code"], 1)
            self.assertEqual(selected[chair_id]["original_instance"],
                             next(p for p in instances
                                  if p["chair_position_identity"] == chair_id))
        self.assertIs(options["correct_heel_l1"], True)
        self.assertEqual((positions, timbers, plan), before)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("PASS: ten source-qualified heel L1 corrections")
