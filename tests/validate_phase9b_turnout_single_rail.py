"""Check the finite TO-001 single-rail route without FreeCAD.

Invented host and catalogue doubles test binding and lifecycle contracts.
The retained independent Pascal oracle supplies rail calculations; this
does not prove native shapes, GUI state, physical fit or production use.
Templot-informed metadata is GPL-3.0-or-later; see NOTICE.md.
"""

import copy
import importlib
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

import single_rail_source_oracle as oracle  # noqa: E402
from validate_phase9b_turnout_central_cc import (  # noqa: E402
    source_case as cc_source_case,
)

RAILS = {2: "curved switch and closure rail", 4: "turnout-side stock rail"}
MODELS = {family: digest for family, _path, digest in oracle.MODEL_INPUTS}
SELECTED = tuple((name, rail) for name in ("S13", "T1", "T2", "T14")
                 for rail in ((2,) if name == "T14" else (2, 4)))
SENTINEL = "Phase 9B TO-001 single-rail standalone validation passed"


def identity(name, rail):
    return f"TO-001:chair:to-001-timber-{name.lower()}:{RAILS[rail].replace(' ', '-')}"


def selection(_path, family, *, run):
    return SimpleNamespace(
        label=family, run=run, model_sha256=MODELS[family],
        components=tuple(range(23 if family == "L1" else 17)),
    )


def source_case():
    source = cc_source_case()
    module = source.module
    geometry = oracle._source_geometry(oracle.SOURCE_PARAMETERS)
    dimensions = {
        "gauge": 16.5, "k3": math.atan2(1, 10),
        "switch_curve_end_x": float(
            geometry["centre_x_mm"] + geometry["closure_radius_mm"]
            / (geometry["crossing_ratio"] ** 2 + 1).sqrt()
        ),
    }
    module.rea_c10_dimensions = lambda *_args: dimensions

    def inner(_dimensions, station):
        pose = oracle.source_rail_pose(oracle.SOURCE_PARAMETERS, station, 2)
        return station, pose["y_mm"], pose["k_rad"]

    def outer(_dimensions, station):
        pose = oracle.source_rail_pose(oracle.SOURCE_PARAMETERS, station, 4)
        return station, pose["y_mm"] - 8.25, pose["k_rad"]

    module._rea_c10_inner_gauge_face = inner
    module._rea_c10_turnout_outer_gauge_point_at_x = outer
    analysis, rails, timbers = source.context[2], source.context[4], source.context[5]
    templates = {name: dict(identifier=name, x=station, near_y=-16.0,
                            far_y=20.0, length_prototype_inches=108.0)
                 for name, station in oracle.NOMINAL_STATIONS[:4]}
    source.layout.extend(templates.values())
    for rail_name in RAILS.values():
        rail_record = next((r for r in rails if r["name"] == rail_name), None)
        if rail_record is None:
            rail_record = {}
            rails.append(rail_record)
        rail_record.update({
            "stable_identity": "TO-001:rail:" + rail_name.replace(" ", "-"),
            "name": rail_name,
            "rail_role": "stock rail" if rail_name == RAILS[4] else rail_name,
            "parent_turnout_identity": "TO-001", "parent_crossover_identity": "",
            "source_configuration": {
                "gauge_face": rail_name + " gauge face",
                "outer_face": rail_name + " outer face",
                "gauge_orientation_source": "mapped named turnout rail faces",
                "rail_geometry_revision": 2,
            },
        })
    template_record = copy.deepcopy(next(
        p for p in analysis["positions"] if p.get("chair_code_label") == "XN"
    ))
    for name, nominal in templates.items():
        station = 746.298 + nominal["x"]
        point, heading = module.interpolate_alignment_station(None, station)
        timbers.append({
            "stable_identity": "TO-001:timber:" + name,
            "identifier": name, "parent_turnout_identity": "TO-001",
            "crossover_identity": "", "host_chainage": station,
            "local_rail_heading_radians": heading,
            "centre": [point.x - 2 * math.sin(heading),
                       point.y + 2 * math.cos(heading)],
            "source_configuration": {
                "local_x": nominal["x"], "local_near_y": -16.0,
                "local_far_y": 20.0, "length_prototype_inches": 108.0,
                "turnout_geometry_revision": 2,
            },
        })
    for index, (name, rail_code) in enumerate(SELECTED):
        rail = next(r for r in rails if r["name"] == RAILS[rail_code])
        timber = next(t for t in timbers if t["identifier"] == name)
        record = copy.deepcopy(template_record)
        record.update(
            stable_chair_position_identity=identity(name, rail_code),
            rail_identity=rail["stable_identity"], rail_name=rail["name"],
            rail_role=rail["rail_role"], timber_identity=timber["stable_identity"],
            prototype_timber_identifier=name, timber_identifier=name,
            chair_code=5, chair_code_label="L1", chair_family="bridge chair",
            handedness="not applicable", assignment_complete_in_current_stage=True,
            key_orientation="requires confirmation from the final bridge-chair "
            "subtype and keying arrangement",
            source_configuration={"rail": copy.deepcopy(rail["source_configuration"]),
                                  "timber": copy.deepcopy(timber["source_configuration"])},
        )
        old_id = f"invented-unselected-{index:03d}"
        old = next(p for p in analysis["positions"]
                   if p["stable_chair_position_identity"] == old_id)
        analysis["positions"][analysis["positions"].index(old)] = record
        excluded = next(p for p in source.plan["analytical_only"]
                        if p["chair_position_identity"] == old_id)
        excluded.update(chair_position_identity=record["stable_chair_position_identity"],
                        rail_identity=record["rail_identity"],
                        timber_identity=record["timber_identity"],
                        chair_label="L1", chair_family="bridge chair",
                        reason="special chair assignment remains analytical",
                        unresolved_special=True, deliberate_omission=False)
    return source


def binding():
    return importlib.import_module(
        "tracktemplate.compatibility.chair_turnout_single_rail_placement",
    )


def preview(source, factory=None, *, select=selection):
    adapter = binding()
    with (patch.dict(sys.modules, {"FreeCAD": source.app}),
          patch.object(adapter, "prepare_catalogue_chair", side_effect=select),
          patch.object(adapter, "verify_catalogue_sources")):
        return adapter.preview_private_catalogue_turnout_single_rail_chairs(
            source.module, source.document, "TO-001", "catalogue.json",
            factory or (lambda *args: args),
        )


class TurnoutSingleRailTests(unittest.TestCase):
    def test_seven_source_choices_and_canonical_inputs_preserved(self):
        source = source_case()
        before = copy.deepcopy((source.context, source.plan))
        _path, placements, _shapes, receipt, verify = preview(source)
        self.assertEqual(len(placements), 7)
        self.assertEqual([p.position_id for p in placements],
                         sorted(identity(*item) for item in SELECTED))
        for p in placements:
            self.assertEqual(p.family, "S1" if p.position_id == identity("T2", 4) else "L1")
        self.assertEqual(receipt["selected_family_counts"], {"L1": 6, "S1": 1})
        self.assertEqual(receipt["represented_source_position_count"], 7)
        self.assertEqual(len(receipt["remaining_positions"]), 161)
        self.assertEqual(receipt["original_analytical_exclusions"], before[1]["analytical_only"])
        with (patch.dict(sys.modules, {"FreeCAD": source.app}),
              patch.object(binding(), "verify_catalogue_sources")):
            verify()
        self.assertEqual((source.context, source.plan), before)
        source.context[2]["positions"].reverse()
        source.plan["analytical_only"].reverse()
        self.assertEqual(preview(source)[1], placements)

    def assert_refused(self, source, **kwargs):
        factory = Mock(side_effect=AssertionError("preview must not start"))
        with self.assertRaises(ValueError):
            preview(source, factory, **kwargs)
        factory.assert_not_called()

    def test_fixed_source_and_profile_guards(self):
        for field, value in (("handing", "Right-hand"), ("toe_chainage", 746.299),
                             ("template_width", 33), ("track_gauge", 18.83),
                             ("chair_analysis_signature", "changed")):
            with self.subTest(field=field):
                source = source_case()
                source.context[1][field] = value
                self.assert_refused(source)
        source = source_case()
        source.plan["rail_profile"]["rail_depth_mm"] += 1e-9
        self.assert_refused(source)

    def test_identity_label_and_assignment_guards(self):
        for field, value in (("chair_code_label", "S1"), ("chair_code", 5.0),
                             ("rail_identity", "wrong"), ("handedness", "Left-hand"),
                             ("assignment_complete_in_current_stage", False),
                             ("special_assignment_deferred", False),
                             ("deliberate_omission", True),
                             ("key_direction_sign", 1), ("stale_signature_state", True)):
            with self.subTest(field=field):
                source = source_case()
                record = next(p for p in source.context[2]["positions"]
                              if p["stable_chair_position_identity"] == identity("S13", 2))
                record[field] = value
                self.assert_refused(source)

    def test_missing_duplicate_and_partition_guards(self):
        for change in ("missing", "duplicate", "overlap", "unowned"):
            source = source_case()
            records = source.context[2]["positions"]
            record = next(p for p in records
                          if p["stable_chair_position_identity"] == identity("S13", 2))
            if change == "missing":
                records.remove(record)
            elif change == "duplicate":
                records.append(copy.deepcopy(record))
            elif change == "overlap":
                source.plan["instances"].append({"chair_position_identity": identity("S13", 2)})
            else:
                source.plan["analytical_only"].pop()
            self.assert_refused(source)

    def test_nominal_station_and_mounting_guards(self):
        for change in ("station", "centre", "heading", "datum", "extended"):
            source = source_case()
            timber = next(t for t in source.context[5] if t["identifier"] == "S13")
            if change == "station":
                timber["source_configuration"]["local_x"] += 1e-6
            elif change == "centre":
                timber["centre"][0] += 1e-6
            elif change == "heading":
                timber["local_rail_heading_radians"] += 1e-6
            elif change == "extended":
                timber["source_configuration"]["extended_source_timber_identity"] = "other"
            else:
                source.plan["instances"][0]["base_z"] = math.nan
            self.assert_refused(source)

    def test_family_selection_and_catalogue_substitution_guards(self):
        source = source_case()
        source.module._rea_c10_turnout_outer_gauge_point_at_x = (
            lambda _dimensions, station: (station, 12.0, .05)
        )
        self.assert_refused(source)
        for field, value in (("model_sha256", "wrong"), ("run", "other"),
                             ("label", "P"), ("components", (1,))):
            def changed(path, family, *, run):
                result = selection(path, family, run=run)
                setattr(result, field, value)
                return result
            self.assert_refused(source_case(), select=changed)

    def test_late_source_and_host_changes_are_rejected(self):
        for change in ("source", "host"):
            source = source_case()
            def factory(_path, _placements, _shapes, _receipt, verify):
                if change == "source":
                    source.context[2]["positions"][-1]["stale_signature_state"] = True
                else:
                    source.host_data["points"][-1].x += 1e-6
                verify()
            with self.assertRaises(ValueError):
                preview(source, factory)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TurnoutSingleRailTests),
    )
    if result.wasSuccessful():
        print(SENTINEL)
    raise SystemExit(0 if result.wasSuccessful() else 1)
