"""Prove one retained whole-crossover preview in native and real-GUI hosts.

Compare every component at every supported position with copied native
source shapes and the established independent placement witnesses. Keep
all 355 records visible in the coverage evidence, including exclusions.
This proof supplies no physical-fit, keying or production acceptance.
"""

from collections import Counter
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import runpy
import shutil
import sys
import time
import traceback
from unittest.mock import patch

import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]


def _load_helper(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ROOT == ROOT
    return module


px = _load_helper(
    "_whole_crossover_p", "freecad_validate_phase9b_catalogue_p_crossover.py",
)
p = px.p
xo = px.xo
adapter = p.adapter
lifecycle = p.lifecycle
catalogue = p.catalogue
combined = p.combined
helpers = p.helpers
SENTINEL = "Phase 9B whole crossover catalogue FreeCAD validation passed"
COUNTS = {"S1": 123, "S1J": 12, "P": 28}
RUNS = {"S1": "existing-02", "S1J": "basic-04", "P": "basic-04"}
MODEL_HASHES = {
    "S1": "a3c8c99a67d9f18b0ee5668400a8bf94f9f39fa641a22da7477141b74cc120eb",
    "S1J": "fd5cb5ffa9fa2004ef2930ab9280b4e906175b9233364448d07d8ef63c212c4b",
    "P": "939ddccacbea0605048277a6f207957a31fe76684a039a6c2bd0f41f3bc94ae7",
}
FIXINGS = (
    "SourceFixing",
    *("SourceFixing" + str(index).zfill(3) for index in range(1, 12)),
)
COMPONENT_NAMES = {
    "S1": (*(f"Part_{index:02d}" for index in range(5)), *FIXINGS),
    "S1J": ("base_plinth", "seat", "outer", "inner", "key", *FIXINGS),
    "P": p.COMPONENT_NAMES,
}
LAYER_NAMES = ("ReferenceRails", "ReferenceTimbers") + tuple(
    family + "_" + name
    for family, names in COMPONENT_NAMES.items() for name in names
)


def _references(path, run_dir):
    """Read exact retained inputs through disposable native copies."""
    directory = run_dir / "native-copies"
    directory.mkdir()
    cases = catalogue._cases(path)
    references, prepared = {}, {}
    for family in COUNTS:
        case = next(item for item in cases if item[0] == family)
        assert case[1]["run"] == RUNS[family]
        assert case[1]["model"]["sha256"] == MODEL_HASHES[family]
        original = catalogue._reference(case, directory)
        references[family] = {
            name: shape for name, _label, shape, _matrix in original
            if name != "display_rail"
        }
        assert tuple(references[family]) == COMPONENT_NAMES[family]
        prepared[family] = p.prepare_catalogue_chair(
            path, family, run=RUNS[family],
        )
    return references, prepared


def _coverage(source, context, frames):
    """Prove complete disjoint accounting without treating gaps as support."""
    _signature, analysis, _settings, plan, _rails, _timbers = context
    positions = {item["stable_chair_position_identity"]: item
                 for item in analysis["positions"]}
    selected = {item["position_id"]: item
                for item in source["selected_positions"]}
    excluded = {item["position_id"]: item
                for item in source["excluded_positions"]}
    assert len(positions) == source["analysis_position_count"] == 355
    assert len(selected) == len(source["selected_positions"]) == 163
    assert len(excluded) == len(source["excluded_positions"]) == 192
    assert source["placement_count"] == 163
    assert source["excluded_position_count"] == 192
    assert source["selected_counts"] == COUNTS
    assert not selected.keys() & excluded.keys()
    assert selected.keys() | excluded.keys() == positions.keys()
    assert Counter(item["exclusion_kind"] for item in excluded.values()) == {
        "source-assignment-deferred": 124,
        "paired-source-context-not-qualified": 20,
        "confirmed-no-separate-chair": 48,
    }
    assert source["original_analytical_exclusions"] == plan["analytical_only"]
    assert source["source_context_signature"] == "sha256:" + hashlib.sha256(
        context[0].encode("utf-8"),
    ).hexdigest()
    assert source["source_analysis_signature"] == analysis["geometry_signature"]
    assert source["source_document_mutation"] is False
    assert source["model_support_adjustments_applied"] is False
    assert source["source_kind"] == "crossover"
    assert source["crossover_id"] == "XO-001"
    assert source["timber_context"] == "current B4 resolved timbers"
    for family, values in frames.items():
        assert {item.position_id for item in values} == {
            identity for identity, item in selected.items()
            if item["family"] == family
        }
    shared_status = Counter()
    for identity, item in {**selected, **excluded}.items():
        position = positions[identity]
        for actual, original in (("rail_id", "rail_identity"),
                                 ("timber_id", "timber_identity")):
            assert item[actual] == position[original]
        assert item["chair_code"] == position["chair_code"]
        for field in ("key_direction_sign", "key_orientation",
                      "key_orientation_classification"):
            assert item[field] == position[field]
        if identity in selected:
            assert not position["deliberate_omission"]
            assert not position["special_assignment_deferred"]
            assert position["assignment_status"] == (
                "confirmed ordinary or turnout assignment"
            )
            assert item["key_direction_sign"] == 0
            continue
        assert item["reason"] and item["original_exclusion"] in (
            plan["analytical_only"]
        )
        kind = item["exclusion_kind"]
        if kind == "source-assignment-deferred":
            assert position["special_assignment_deferred"]
        elif kind == "paired-source-context-not-qualified":
            assert not position["special_assignment_deferred"]
            assert position["chair_code_label"] in ("1P/2P", "3P-11P")
            comparison = item["source_context_comparison"]
            mate = positions[comparison["mate_position_id"]]
            assert mate["timber_identity"] == position["timber_identity"]
            assert mate["deliberate_omission"]
            tangent = position["local_rail_tangent"]
            other = mate["local_rail_tangent"]
            assert comparison["target_sampled_world_midline_tangents"] == [
                tangent, other,
            ]
            assert math.isfinite(
                comparison["retained_uncurved_gauge_face_angle_rad"],
            )
            assert comparison["physical_fit"] == "NOT_PROVED"
            assert "angle_magnitude_difference_rad" not in comparison
        else:
            assert position["deliberate_omission"]
            owner_id = item["supporting_position_id"]
            owner = positions[owner_id]
            assert owner["timber_identity"] == position["timber_identity"]
            assert owner["rail_role"] == "stock rail"
            assert item["supporting_assembly_placed"] == (owner_id in selected)
            shared_status[item["supporting_assembly_placed"]] += 1
    assert shared_status == {True: 28, False: 20}


def _assert_preview(result, document, references, frames, context):
    """Compare all 2,911 component placements with independent sources."""
    catalogue.helpers._active_document_state(document)
    assert not document.FileName and not document.Temporary
    for text in ("163 placed", "192 excluded", "355 source positions"):
        assert text in document.Label
    assert tuple(obj.Name for obj in document.Objects) == LAYER_NAMES
    assert result["contract_id"] == "tracktemplate.private-catalogue-crossover.v2"
    assert result["family_count"] == 3
    assert result["placement_count"] == result["track_placements_added"] == 163
    assert result["component_count"] == 56 and result["layer_count"] == 58
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["geometry_rebuilt"] is False
    assert result["scale_denominator"] == "76.2"
    assert result["length_basis"] == "model" and result["length_unit"] == "mm"
    assert tuple(result["families"]) == tuple(COUNTS)
    assert tuple(item["name"] for item in result["layers"]) == LAYER_NAMES
    _coverage(result["source_receipt"], context, frames)
    for obj in document.Objects[:2]:
        assert not obj.Shape.Solids and not obj.Shape.Faces
    comparisons = {}
    solids = 0
    for family, values in frames.items():
        record = result["families"][family]
        assert record["family"] == record["label"] == family
        assert record["run"] == RUNS[family]
        assert record["source_model_sha256"] == MODEL_HASHES[family]
        assert record["placement_count"] == len(values) == COUNTS[family]
        names = COMPONENT_NAMES[family]
        assert record["component_count"] == len(names)
        assert len(record["placements"]) == len(values)
        assert len(record["components"]) == len(names)
        excluded_names = [item["source_name"]
                          for item in record["excluded_source_components"]]
        assert excluded_names == ([] if family == "S1" else ["display_rail"])
        family_checks = []
        for name, component in zip(names, record["components"]):
            obj = document.getObject(family + "_" + name)
            assert obj.TypeId == "Part::Feature"
            assert "GeneratedBy" not in obj.PropertiesList
            assert component["source_name"] == name
            assert tuple(component["source_identity"]) == (
                MODEL_HASHES[family], name,
            )
            children = obj.Shape.childShapes()
            assert len(children) == len(values)
            family_checks.append({
                "name": name,
                "positions": [
                    dict(p._compare_component(child, references[family][name],
                                              frame),
                         position_id=frame.position_id)
                    for child, frame in zip(children, values)
                ],
            })
            solids += len(references[family][name].Solids) * len(values)
        for actual, frame in zip(record["placements"], values):
            for field in ("position_id", "rail_id", "timber_id"):
                assert actual[field] == getattr(frame, field)
            for field in ("origin_mm", "x_axis", "y_axis"):
                assert tuple(actual[field]) == getattr(frame, field)
            assert len(actual["components"]) == len(names)
            for name, component in zip(names, actual["components"]):
                assert tuple(component["placement_identity"]) == (
                    frame.position_id, MODEL_HASHES[family], name,
                )
        comparisons[family] = family_checks
    assert sum(len(item["positions"]) for values in comparisons.values()
               for item in values) == 2911
    assert result["solid_count"] == solids == sum(
        len(obj.Shape.Solids) for obj in document.Objects
    )
    return comparisons


def _gui_inspection(document, frames, context, run_dir):
    """Inspect layers and capture each family on both constituent turnouts."""
    for obj in document.Objects:
        assert obj.ViewObject.Visibility
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(obj)
        assert Gui.Selection.getSelection() == [obj]
        obj.ViewObject.Visibility = False
        combined._settle(document)
        assert not obj.ViewObject.Visibility
        obj.ViewObject.Visibility = True
        combined._settle(document)
        assert obj.ViewObject.Visibility
    Gui.Selection.clearSelection()
    positions = {item["stable_chair_position_identity"]: item
                 for item in context[1]["positions"]}
    images = {}
    view = Gui.getDocument(document.Name).activeView()
    animation = view.isAnimationEnabled()
    try:
        view.setAnimationEnabled(False)
        assert not view.isAnimationEnabled()
        for family, values in frames.items():
            for side in ("A", "B"):
                label = family + "-" + side
                directory = run_dir / "views" / label
                directory.mkdir(parents=True)
                selected = tuple(
                    frame for frame in values
                    if positions[frame.position_id]["parent_turnout_identity"]
                    == "XO-001-" + side + "001"
                )
                assert selected
                images[label] = helpers._images(document, selected, directory)
    finally:
        view.setAnimationEnabled(animation)
    assert view.isAnimationEnabled() == animation
    return images


def validate():
    """Run the complete same proof in an isolated native or real-GUI host."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    path = Path(os.environ["TRACKTEMPLATE_CHAIR_CATALOGUE"]).resolve()
    fixture = Path(os.environ["TRACKTEMPLATE_CROSSOVER_REFERENCE_FIXTURE"])
    assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    run_dir = Path(os.environ.get(
        "TRACKTEMPLATE_WHOLE_CROSSOVER_RUN_DIR",
        ROOT / "benchmark-output/catalogue-whole-crossover" / stamp,
    )).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp)}
    initial = catalogue.helpers._document_state()
    try:
        references, prepared = _references(path, run_dir)
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        api, bootstrap = launcher["_load_foundation"](ROOT)
        session, routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, bootstrap,
        )
        assert launcher["FOUNDATION_RESULT"]["matched_profile_id"] == p.PROFILE
        receipt.update(profile=p.PROFILE, routing=routing)
        module = session.module
        command = session.preview_private_catalogue_crossover_chairs
        target = run_dir / "XO-001.FCStd"
        shutil.copy2(fixture, target)
        source = App.openDocument(str(target))
        source.UndoMode = 1
        receipt["analysis_refusals"] = px._analysis_refusals(
            module, command, source, fixture, path, run_dir,
        )
        foreign = App.newDocument("WholeCrossoverUnrelatedWitness")
        foreign.addObject("Part::Feature", "Keep").Shape = Part.makeBox(2, 3, 4)
        foreign.recompute()
        combined._settle(foreign)
        App.setActiveDocument(source.Name)
        gui = Gui if App.GuiUp else None
        if gui:
            gui.getMainWindow().resize(1600, 1000)
            gui.Selection.addSelection(source.Objects[0])
        combined._settle(source)
        context = xo._context(module, source)
        previous, excluded, recovered, observations = xo._expected_placements(
            module, context,
        )
        frames = {"S1": previous[0], "S1J": previous[1],
                  "P": px._expected_frames(module, context)}
        assert {family: len(values) for family, values in frames.items()} == (
            COUNTS
        )
        partition = px._legacy_partition(module, context)
        assert len(excluded) == 220
        receipt.update(frame_observations=observations,
                       recovered_positions=recovered)
        xo._state(module, source)
        combined._settle(source)
        source_state = xo._state(module, source)
        foreign_state = combined._foreign_state(foreign)
        combined._settle(source)
        assert xo._state(module, source) == source_state
        registry = dict(App.listDocuments())
        identities = {(doc.Name, obj.Name): obj for doc in registry.values()
                      for obj in doc.Objects}
        shapes = {key: obj.Shape for key, obj in identities.items()
                  if "Shape" in obj.PropertiesList}
        selection = lifecycle._selection_snapshot(App, gui)
        preselection = lifecycle._preselection_snapshot(App, gui)
        receipt.update(source_before=source_state, foreign_before=foreign_state)

        def unchanged(stage, active):
            receipt["last_preservation_stage"] = stage
            assert xo._state(module, source) == source_state, stage
            assert combined._foreign_state(foreign) == foreign_state, stage
            assert App.listDocuments() == dict(
                registry, **({active.Name: active}
                             if active.Name not in registry else {}),
            ), stage
            for name, document in registry.items():
                assert App.getDocument(name) is document, stage
            for (name, obj_name), obj in identities.items():
                assert App.getDocument(name).getObject(obj_name) is obj, stage
            for key, shape in shapes.items():
                assert identities[key].Shape.isSame(shape), stage
            assert lifecycle._selection_snapshot(App, gui) == selection, stage
            assert lifecycle._preselection_snapshot(App, gui) == preselection
            catalogue.helpers._active_document_state(active)

        arguments = (source, "XO-001", path)
        started = time.perf_counter()
        with patch.object(App, "openDocument", side_effect=AssertionError(
            "Product restored an external source document",
        )):
            result = command(*arguments)
        receipt["elapsed_seconds"] = time.perf_counter() - started
        preview = App.getDocument(result["document_name"])
        receipt["preview"] = result
        receipt["comparisons"] = _assert_preview(
            result, preview, references, frames, context,
        )
        unchanged("created", preview)
        before = tuple(obj.Shape for obj in preview.Objects)
        assert preview.UndoCount == 1
        preview.undo()
        assert not preview.Objects
        preview.redo()
        _assert_preview(result, preview, references, frames, context)
        assert all(p.catalogue_adapter._same_presented_shape(obj.Shape, shape)
                   for obj, shape in zip(preview.Objects, before))
        unchanged("Undo/Redo", preview)
        receipt["undo_redo"] = "PASS"
        if gui:
            receipt["images"] = _gui_inspection(
                preview, frames, context, run_dir,
            )
            receipt["camera_animation_restored"] = True
            lifecycle._restore_selection(App, gui, selection)
            lifecycle._restore_preselection(App, gui, preselection)
            unchanged("GUI inspection", preview)
            receipt["visibility_selection"] = "PASS"
        App.closeDocument(preview.Name)
        App.setActiveDocument(source.Name)
        lifecycle._restore_selection(App, gui, selection)
        lifecycle._restore_preselection(App, gui, preselection)
        combined._settle(source)
        unchanged("test-owned close", source)
        invalid = run_dir / "changed-catalogue.json"
        invalid.write_bytes(path.read_bytes() + b"\n")
        with patch.object(App, "newDocument", side_effect=AssertionError(
            "Invalid catalogue created a document",
        )):
            receipt["catalogue_refusal"] = catalogue._reject(
                lambda: command(source, "XO-001", invalid), ValueError,
            )
        unchanged("early refusal", source)
        original_top = module._chair_physical_top_z
        create = adapter.create_private_catalogue_crossover_preview

        def stale_during_build(*args):
            def changed_source():
                assert App.ActiveDocument not in (source, foreign)
                assert len(App.ActiveDocument.Objects) == 58
                with patch.object(
                    module, "_chair_physical_top_z",
                    side_effect=lambda *values: original_top(*values) + 1e-8,
                ):
                    args[-1]()
            return create(*args[:-1], changed_source)

        with patch.object(session, "_private_catalogue_crossover_preview_factory",
                          side_effect=stale_during_build):
            receipt["late_source_refusal"] = helpers._reject(
                lambda: command(*arguments), "source changed",
            )
        unchanged("late source rollback", source)
        original_check = adapter._same_presented_shape

        def reject_stored(actual, expected):
            if App.ActiveDocument not in registry.values():
                assert len(App.ActiveDocument.Objects) == 58
                return False
            return original_check(actual, expected)

        with patch.object(adapter, "_same_presented_shape", reject_stored):
            receipt["stored_shape_refusal"] = catalogue._reject(
                lambda: command(*arguments), ValueError,
            )
        unchanged("stored shape rollback", source)
        for value in prepared.values():
            p.verify_catalogue_sources(value)
        assert catalogue._hash(source.FileName) == xo.FIXTURE_SHA256
        assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
        assert xo._context(module, source) == context
        assert px._legacy_partition(module, context) == partition
        receipt.update(source_after=xo._state(module, source),
                       foreign_after=combined._foreign_state(foreign),
                       source_bindings_unchanged=True,
                       fixture_sha256=xo.FIXTURE_SHA256,
                       component_comparisons=2911,
                       transaction_rollback="PASS",
                       legacy_exclusions_unchanged=True)
    except BaseException:
        receipt.update(status="FAIL", traceback=traceback.format_exc())
        raise
    finally:
        # The asserted empty isolated host makes every remaining document
        # test-owned, including any document left by a failed rollback.
        for name in tuple(App.listDocuments()):
            App.closeDocument(name)
        catalogue.helpers._settle()
        receipt["owned_documents_closed"] = not App.listDocuments()
        (run_dir / "result.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
        )
    assert catalogue.helpers._document_state() == initial
    receipt["status"] = "PASS"
    (run_dir / "result.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
    )
    print(SENTINEL, flush=True)


if __name__ in ("__main__", Path(__file__).stem):
    validate()
