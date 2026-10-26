"""Prove supplemental S1/S1J/L1 placements using retained chair geometry.

The accepted check-end receipt owns the unchanged 203 assemblies and
4215 component results. New placements need independent source witnesses.
One complete preview and focused new-family lifecycle failures preserve
that baseline. Source agreement supplies no physical-fit acceptance.
"""

from collections import Counter
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
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "tests" / filename,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ROOT == ROOT
    return module


previous = _load_helper(
    "_single_rail_previous", "freecad_validate_phase9b_catalogue_check_ends.py",
)
guard = _load_helper(
    "_single_rail_guard", "freecad_validate_phase9b_p_curvature_recalculation.py",
)
central, p, xo = previous.central, previous.p, previous.xo
adapter, lifecycle = previous.adapter, previous.lifecycle
catalogue, combined, reader = (
    previous.catalogue, previous.combined, previous.reader,
)

import single_rail_source_oracle as oracle  # noqa: E402

SENTINEL = "Phase 9B single-rail catalogue FreeCAD validation passed"
BASELINE_SHA256 = (
    "38adadeec8bcdb6fdc5bcdfa21f1097973870021154863d2f2ee68d70924a77f"
)
MODEL_SHA256 = {
    "S1": "a3c8c99a67d9f18b0ee5668400a8bf94f9f39fa641a22da7477141b74cc120eb",
    "S1J": "fd5cb5ffa9fa2004ef2930ab9280b4e906175b9233364448d07d8ef63c212c4b",
    "L1": "a0289c046b6ae8cb1e2df88a8f6a1f3f0dc79f7a0ae1870d0b3b13154e0eb042",
}
GROUP_FAMILY = {
    "SupplementS1": "S1", "SupplementS1J": "S1J", "L1": "L1",
}
COUNTS = {"SupplementS1": 14, "SupplementS1J": 4, "L1": 16}
RUNS = {"S1": "existing-02", "S1J": "basic-04", "L1": "existing-02"}
SOURCE_CONTEXTS = {
    "S1": "retained-S1-L1-reference-package",
    "S1J": "fixed-basic-source-context",
    "L1": "retained-S1-L1-reference-package",
}
COMPONENT_NAMES = {
    "S1": (*(f"Part_{index:02d}" for index in range(5)),
           "SourceFixing", *(f"SourceFixing{index:03d}"
                             for index in range(1, 12))),
    "S1J": ("base_plinth", "seat", "outer", "inner", "key",
            "SourceFixing", *(f"SourceFixing{index:03d}"
                              for index in range(1, 12))),
    "L1": (*(f"Part_{index:02d}" for index in range(7)),
           "SourceFixing", *(f"SourceFixing{index:03d}"
                             for index in range(1, 16))),
}


def _read_baseline(path):
    """Bind the complete accepted fixed-XO result, including exclusions."""
    assert catalogue._hash(path) == BASELINE_SHA256
    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["status"] == "PASS" and not result["gui"]
    assert result["profile"] == p.PROFILE
    assert result["fixture_sha256"] == xo.FIXTURE_SHA256
    assert result["owned_documents_closed"]
    assert result["source_bindings_unchanged"]
    assert result["baseline_component_comparisons"] == 3951
    assert result["check_end_component_comparisons"] == 264
    assert result["preview"]["placement_count"] == 203
    assert result["preview"]["layer_count"] == 479
    source = result["preview"]["source_receipt"]
    assert source["unrepresented_source_position_count"] == 84
    assert source["existing_shared_support_count"] == 48
    return result


def _references(path, supplement, run_dir):
    """Read copied native shapes through the accepted catalogue helpers."""
    references, prepared = previous._references(path, supplement, run_dir)
    assert tuple(references["S1"]) == COMPONENT_NAMES["S1"]
    assert tuple(references["S1J"]) == COMPONENT_NAMES["S1J"]
    selected = reader.prepare_catalogue_chair(path, "L1", run="existing-02")
    assert selected.model_sha256 == MODEL_SHA256["L1"]
    assert selected.context == "retained-S1-L1-reference-package"
    native = catalogue._reference(("L1", {
        "run": selected.run,
        "model": {"path": selected.model_path,
                  "sha256": selected.model_sha256},
    }), run_dir / "native-copies")
    references["L1"] = {
        name: shape for name, _label, shape, _matrix in native
    }
    prepared["L1"] = selected
    assert tuple(references["L1"]) == COMPONENT_NAMES["L1"]
    assert tuple(c.name for c in selected.components) == COMPONENT_NAMES["L1"]
    assert len(native) == 23
    return references, prepared


def _witnesses(module, source, context, supplement, data, references):
    """Compose source matrices using independently bound canonical hosts.

    Only identities are taken from chair analysis. The oracle reads
    nominal stations and source selections from its frozen inputs; its
    host interpolation reads actual canonical arrays, never a product
    placement. The retained mounting plane is Z=0 for all three families.
    """
    binding = json.loads(supplement.read_text())["canonical_hosts"]
    host_path = Path(binding["path"])
    assert catalogue._hash(host_path) == binding["sha256"]
    captured = json.loads(host_path.read_text())
    assert captured["fixture_sha256"] == xo.FIXTURE_SHA256
    data["bindings"][str(host_path)] = binding["sha256"]
    configuration = json.loads(context[0])["configuration"]
    hosts = {}
    for side in ("A", "B"):
        config = configuration["turnout_" + side.lower() + "_config"]
        obj = source.getObject(config["host_object"])
        host = module.turnout_host_alignment(obj)
        hosts[side] = {
            "object_name": obj.Name,
            "points": [[point.x, point.y] for point in host["points"]],
            "headings": host["headings"], "stations": host["stations"],
            "total": host["total"], "toe_chainage": config["toe_chainage"],
            "orientation": config["orientation"], "handing": config["handing"],
        }
        assert hosts[side] == captured["hosts"][side]
    base_z, = {instance["base_z"] for instance in context[3]["instances"]}
    geometry = oracle._source_geometry(data["parameters"])
    arithmetic_scale = max(
        1.0, *(abs(float(geometry[field])) for field in (
            "centre_y_mm", "closure_radius_mm", "stock_radius_mm",
        )),
    )
    positions = {item["stable_chair_position_identity"]: item
                 for item in context[1]["positions"]}
    witnesses = {}
    for context_id, target in data["contexts"].items():
        family = target["family"]
        for identity in target["source_position_ids"]:
            assert identity not in witnesses
            position = positions[identity]
            side = {"XO-001-A001": "A", "XO-001-B001": "B"}[
                position["parent_turnout_identity"]]
            host = hosts[side]
            common = oracle.expected_world_frame(
                host, toe_chainage_mm=host["toe_chainage"],
                direction=1 if side == "A" else -1, hand=-1,
                station_mm=target["station_mm"], gauge_mm=16.5,
            )
            components = {
                part["native_object"]: central._world_frame(
                    position, oracle.native_to_target(data, context_id, part_id),
                    common, base_z,
                )
                for part_id, part in data["parts_by_family"][family].items()
            }
            assert tuple(components) == tuple(references[family])
            body = components[COMPONENT_NAMES[family][0]]
            witnesses[identity] = {
                "context_id": context_id, "side": side, "family": family,
                "components": components, "inspection_frame": body,
                "source_decision": {
                    "source_rail_code": target["source_rail_code"],
                    "source_branch": target["source_branch"],
                    "source_station_mm": target["station_mm"],
                    "source_angle_rad": target["source_angle_rad"],
                    "source_gauge_y_mm": target["source_gauge_y_mm"],
                },
                "source_gauge_arithmetic_scale_mm": arithmetic_scale,
                "expected_component_frames": {
                    name: vars(frame) for name, frame in components.items()
                },
            }
    assert len(witnesses) == 34
    assert Counter(item["family"] for item in witnesses.values()) == {
        "S1": 14, "S1J": 4, "L1": 16,
    }
    assert Counter(item["side"] for item in witnesses.values()) == {
        "A": 17, "B": 17,
    }
    return witnesses


def _assert_baseline(result, document, references, baseline):
    """Compare every accepted component using its unchanged recorded frame."""
    checks = []
    for group, accepted in baseline["preview"]["families"].items():
        current = result["families"][group]
        for field in ("run", "source_model_sha256", "source_bindings",
                      "context", "placement_count", "component_count",
                      "components", "placements"):
            assert json.loads(json.dumps(current[field])) == accepted[field], (
                group, field,
            )
        for index, placement in enumerate(accepted["placements"]):
            for component in placement["components"]:
                name = component["source_name"]
                frame_record = dict(placement)
                for field in previous.FRAME_FIELDS:
                    if field in component:
                        frame_record[field] = component[field]
                frame = central._frame(frame_record)
                children = document.getObject(
                    group.replace("-", "_") + "_" + name,
                ).Shape.childShapes()
                assert len(children) == len(accepted["placements"])
                checks.append(dict(
                    p._compare_component(
                        children[index], references[group][name], frame,
                    ),
                    group=group, position_id=frame.position_id, component=name,
                ))
        print("SINGLE_RAIL_BASELINE_GROUP_PASS", group, flush=True)
    assert len(checks) == 4215
    return checks


def _coverage(receipt, context, baseline, witnesses):
    """Preserve the complete partition and every non-selected source record."""
    old = baseline["preview"]["source_receipt"]
    positions = {item["stable_chair_position_identity"]: item
                 for item in context[1]["positions"]}
    selected = {item["position_id"]: item
                for item in receipt["selected_positions"]}
    excluded = {item["position_id"]: item
                for item in receipt["excluded_positions"]}
    assert len(selected) == receipt["placement_count"] == 237
    assert len(excluded) == receipt["excluded_position_count"] == 118
    assert len(positions) == receipt["analysis_position_count"] == 355
    assert not selected.keys() & excluded.keys()
    assert selected.keys() | excluded.keys() == positions.keys()
    assert len(witnesses) == 34
    assert Counter(item["exclusion_kind"] for item in excluded.values()) == {
        "source-assignment-deferred": 50,
        "confirmed-no-separate-chair": 48,
        "source-paired-reference-support": 12,
        "source-paired-check-end-support": 8,
    }
    assert receipt["represented_source_position_count"] == 305
    assert receipt["unrepresented_source_position_count"] == 50
    assert receipt["existing_shared_support_count"] == 48
    assert receipt["source_paired_check_support_count"] == 12
    assert receipt["source_paired_check_end_support_count"] == 8
    assert receipt["canonical_deferred_assignment_count"] == 124
    assert sum(bool(item["special_assignment_deferred"])
               for item in positions.values()) == 124
    for field in ("source_context_signature", "source_analysis_signature",
                  "original_analytical_exclusions"):
        assert receipt[field] == old[field]
    assert receipt["original_analytical_exclusions"] == context[3]["analytical_only"]
    assert not receipt["source_document_mutation"]
    assert not receipt["model_support_adjustments_applied"]
    accepted_ids = set()
    for item in old["selected_positions"]:
        identity = item["position_id"]
        assert selected[identity] == item
        accepted_ids.add(identity)
    assert selected.keys() - accepted_ids == witnesses.keys()
    for item in old["excluded_positions"]:
        identity = item["position_id"]
        if identity not in witnesses:
            assert excluded[identity] == item
        else:
            assert item["exclusion_kind"] == "source-assignment-deferred"
            for field in previous.POSITION_FIELDS + (
                    "chair_code", "chair_label", "original_exclusion",
                    "key_direction_sign", "key_orientation",
                    "key_orientation_classification"):
                assert selected[identity][field] == item[field]
            witness = witnesses[identity]
            assert selected[identity]["family"] == witness["family"]
            assert selected[identity]["physical_fit"] == "NOT_PROVED"
            for field, value in witness["source_decision"].items():
                if field in ("source_rail_code", "source_branch",
                             "source_station_mm"):
                    assert selected[identity][field] == value
                    continue
                # Reuse the accepted check-end arithmetic bound. Circle
                # subtraction uses its operands, not the small result;
                # these budgets qualify arithmetic, never physical fit.
                scale = (witness["source_gauge_arithmetic_scale_mm"]
                         if field == "source_gauge_y_mm" else
                         max(1.0, abs(value)))
                budget = 64 * sys.float_info.epsilon * scale
                assert math.isfinite(selected[identity][field])
                assert abs(selected[identity][field] - value) <= budget


def _close_preview(document, source, gui, selection, preselection, unchanged):
    """Restore only selection affected by test-owned document closure."""
    App.closeDocument(document.Name)
    App.setActiveDocument(source.Name)
    lifecycle._restore_selection(App, gui, selection)
    lifecycle._restore_preselection(App, gui, preselection)
    combined._settle(source)
    unchanged("test-owned preview close", source)


def _assert_new(result, document, references, witnesses):
    """Compare every new component with an independent source transform."""
    checks = []
    seen = set()
    for group, family in GROUP_FAMILY.items():
        record = result["families"][group]
        names = COMPONENT_NAMES[family]
        assert record["source_model_sha256"] == MODEL_SHA256[family]
        assert record["run"] == RUNS[family]
        assert record["context"] == SOURCE_CONTEXTS[family]
        assert record["component_count"] == len(names)
        assert record["placement_count"] == COUNTS[group]
        assert record["placement"] == "source-single-rail-component-frames.v1"
        assert record["fixing_head_rotation_rad"] == 0.0
        assert not record["random_export_parity"]
        assert not record["templot_global_fixing_angle_parity"]
        assert tuple(c["source_name"] for c in record["components"]) == names
        for index, placement in enumerate(record["placements"]):
            identity = placement["position_id"]
            assert identity not in seen
            seen.add(identity)
            witness = witnesses[identity]
            assert witness["family"] == family
            central._near_frame(placement, witness["components"][names[0]])
            assert len(placement["components"]) == len(names)
            for name, component in zip(names, placement["components"]):
                assert component["source_name"] == name
                assert tuple(component["placement_identity"]) == (
                    identity, MODEL_SHA256[family], name,
                )
                frame = witness["components"][name]
                central._near_frame(component, frame)
                layer = document.getObject(group + "_" + name)
                children = layer.Shape.childShapes()
                assert len(children) == COUNTS[group]
                checks.append(dict(
                    p._compare_component(
                        children[index], references[family][name], frame,
                    ),
                    group=group, position_id=identity, component=name,
                ))
    assert seen == witnesses.keys()
    assert len(checks) == 674
    return checks


def _assert_preview(result, document, references, baseline, witnesses):
    """Keep the complete old assembly while proving the added components."""
    catalogue.helpers._active_document_state(document)
    assert not document.FileName and not document.Temporary
    assert result["contract_id"] == "tracktemplate.private-catalogue-crossover.v5"
    assert result["placement_count"] == result["track_placements_added"] == 237
    assert result["family_count"] == 12 and result["assembly_group_count"] == 19
    assert result["component_count"] == 534 and result["layer_count"] == 536
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["geometry_rebuilt"] is False
    assert result["length_basis"] == "model" and result["length_unit"] == "mm"
    assert result["scale_denominator"] == "76.2"
    names = tuple(item["name"] for item in baseline["preview"]["layers"])
    names += tuple(group + "_" + name
                   for group, family in GROUP_FAMILY.items()
                   for name in COMPONENT_NAMES[family])
    assert tuple(obj.Name for obj in document.Objects) == names
    assert tuple(item["name"] for item in result["layers"]) == names
    for obj in document.Objects:
        assert obj.TypeId == "Part::Feature"
        assert "GeneratedBy" not in obj.PropertiesList
    for obj in document.Objects[:2]:
        assert not obj.Shape.Faces and not obj.Shape.Solids
    baseline_checks = _assert_baseline(result, document, references, baseline)
    new_checks = _assert_new(result, document, references, witnesses)
    expected_solids = baseline["preview"]["solid_count"] + sum(
        COUNTS[group] * sum(len(shape.Solids)
                            for shape in references[family].values())
        for group, family in GROUP_FAMILY.items()
    )
    assert result["solid_count"] == expected_solids == sum(
        len(obj.Shape.Solids) for obj in document.Objects
    )
    return {"baseline": baseline_checks, "single_rail": new_checks}


def _gui_inspection(document, witnesses, run_dir):
    """Exercise every layer and capture each newly qualified position."""
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
    view = Gui.getDocument(document.Name).activeView()
    animation = view.isAnimationEnabled()
    images = {}
    try:
        view.setAnimationEnabled(False)
        assert not view.isAnimationEnabled()
        for index, (identity, witness) in enumerate(sorted(witnesses.items())):
            directory = run_dir / "views" / f"position-{index:02d}"
            directory.mkdir(parents=True)
            filenames = previous.whole.helpers._images(
                document, (witness["inspection_frame"],), directory,
            )
            images[identity] = {
                "family": witness["family"],
                "files": [{"path": str(directory / name),
                           "sha256": catalogue._hash(directory / name)}
                          for name in filenames],
                "capture_state": str(directory / "capture-state.json"),
            }
    finally:
        view.setAnimationEnabled(animation)
    assert view.isAnimationEnabled() == animation
    assert len(images) == 34
    manifest = run_dir / "image-manifest.json"
    manifest.write_text(json.dumps(images, indent=2) + "\n", encoding="utf-8")
    print("SINGLE_RAIL_IMAGES_READY", str(manifest), flush=True)
    return images


def _focused_failures(create, captured, module, path, prepared, registry,
                      source, unchanged):
    """Repeat only the new preparation paths and shared rollback boundary."""
    from tracktemplate.domain.single_rail_placement import SingleRailPlacement

    groups, context_shapes, source_receipt, verify_source = captured["args"][1:]
    failures = {}
    for prerequisite, value in (
            ("paired_contexts_path", None), ("include_central_cc", False),
            ("include_check_ends", False)):
        with patch.object(App, "newDocument", side_effect=AssertionError(
                "Missing single-rail prerequisite created a document")):
            failures[prerequisite] = catalogue._reject(
                lambda: create(**{prerequisite: value}), ValueError,
            )
        unchanged("early " + prerequisite + " refusal", source)

    original_read = reader._read
    original_host = module.turnout_host_alignment
    original_check = adapter._same_presented_shape
    for group, family in GROUP_FAMILY.items():
        selected = prepared[family]
        layer_count = 2 + len(COMPONENT_NAMES[family])

        def changed_bytes(filename):
            content = original_read(filename)
            return (content + b"\n" if str(filename) == selected.model_path
                    else content)

        checks = {}
        with patch.object(reader, "_read", changed_bytes), patch.object(
                App, "newDocument", side_effect=AssertionError(
                    "Changed single-rail geometry created a document")):
            checks["early_model_refusal"] = catalogue._reject(create, ValueError)
        unchanged(group + " early model refusal", source)

        def focused(verify=verify_source):
            choice, specs, prepare = adapter._prepare_catalogue_family(
                path, groups[group], context_shapes, source_receipt,
                family=family, placement_type=SingleRailPlacement,
                model_sha256=MODEL_SHA256[family],
                source_names=tuple(item.name for item in selected.components),
                run=RUNS[family], source_context=SOURCE_CONTEXTS[family],
            )

            def verify_inputs():
                verify()
                reader.verify_catalogue_sources(choice)

            return adapter._materialise_preview(
                family, source_receipt, specs, prepare, verify_inputs,
            )

        def late_bytes(filename):
            if App.ActiveDocument not in registry.values():
                assert len(App.ActiveDocument.Objects) == layer_count
                return changed_bytes(filename)
            return original_read(filename)

        with patch.object(reader, "_read", late_bytes):
            checks["late_model_refusal"] = catalogue._reject(focused, ValueError)
        unchanged(group + " late model rollback", source)

        def stale_source():
            assert App.ActiveDocument not in registry.values()
            assert len(App.ActiveDocument.Objects) == layer_count

            def changed_host(obj):
                host = dict(original_host(obj))
                headings = list(host["headings"])
                headings[0] += 1e-8
                return dict(host, headings=headings)

            with patch.object(module, "turnout_host_alignment", changed_host):
                verify_source()

        checks["late_host_refusal"] = previous.paired.helpers._reject(
            lambda: focused(stale_source), "changed",
        )
        unchanged(group + " late host rollback", source)

        def reject_stored(actual, expected):
            if App.ActiveDocument not in registry.values():
                assert len(App.ActiveDocument.Objects) == layer_count
                return False
            return original_check(actual, expected)

        with patch.object(adapter, "_same_presented_shape", reject_stored):
            checks["stored_shape_refusal"] = catalogue._reject(focused, ValueError)
        unchanged(group + " stored shape rollback", source)
        failures[group] = checks
        print("SINGLE_RAIL_FOCUSED_ROLLBACK_PASS", group, flush=True)
    return failures


def validate():
    """Build one complete private preview in a qualified isolated host."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    path = Path(os.environ["TRACKTEMPLATE_CHAIR_CATALOGUE"]).resolve()
    supplement = Path(os.environ["TRACKTEMPLATE_PAIRED_CATALOGUE"]).resolve()
    fixture = Path(os.environ["TRACKTEMPLATE_CROSSOVER_REFERENCE_FIXTURE"])
    source_directory = Path(os.environ["TRACKTEMPLATE_TEMPLOT_SOURCE"])
    source_context = Path(os.environ["TRACKTEMPLATE_SINGLE_RAIL_SOURCE_CONTEXT"])
    baseline_path = Path(os.environ["TRACKTEMPLATE_CHECK_END_BASELINE_RECEIPT"])
    run_dir = Path(os.environ["TRACKTEMPLATE_SINGLE_RAIL_RUN_DIR"]).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp),
               "physical_fit": "NOT_PROVED", "baseline_sha256": BASELINE_SHA256,
               "source_agreement_scope": "34 newly qualified single-rail positions",
               "baseline_scope": "203 accepted assemblies preserved unchanged",
               "global_templot_equivalence": "NOT_CLAIMED"}
    initial = catalogue.helpers._document_state()
    try:
        assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
        baseline = _read_baseline(baseline_path)
        data = oracle.load(source_directory, path.parent, source_context)
        references, prepared = _references(path, supplement, run_dir)
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
        foreign = App.newDocument("SingleRailUnrelatedWitness")
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
        witnesses = _witnesses(
            module, source, context, supplement, data, references,
        )
        receipt["source_bindings"] = data["bindings"]
        receipt["source_references"] = data["references"]
        receipt["source_witnesses"] = {
            identity: {key: value for key, value in witness.items()
                       if key not in ("components", "inspection_frame")}
            for identity, witness in witnesses.items()
        }
        registry = dict(App.listDocuments())
        unchanged, selection, preselection, state_hash, negatives = guard._guard(
            module, source, foreign, gui, 355,
        )
        receipt["source_state_sha256"] = state_hash
        receipt["source_guard_negative_witnesses"] = negatives
        captured = {}
        native_create = adapter.create_private_catalogue_crossover_preview

        def capture_factory(*args, **kwargs):
            captured.update(args=args, kwargs=kwargs)
            return native_create(*args, **kwargs)

        def create(**options):
            kwargs = dict(
                paired_contexts_path=supplement, include_central_cc=True,
                include_check_ends=True, include_single_rail=True,
            )
            kwargs.update(options)
            return command(source, "XO-001", path, **kwargs)

        started = time.perf_counter()
        with patch.object(session, "_private_catalogue_crossover_preview_factory",
                          side_effect=capture_factory), patch.object(
                App, "openDocument", side_effect=AssertionError(
                    "Product restored an external source document")):
            result = create()
        receipt["elapsed_creation_seconds"] = time.perf_counter() - started
        preview = App.getDocument(result["document_name"])
        receipt["preview"] = result
        _coverage(result["source_receipt"], context, baseline, witnesses)
        receipt["comparisons"] = _assert_preview(
            result, preview, references, baseline, witnesses,
        )
        unchanged("created", preview)
        print("SINGLE_RAIL_COMPLETE_PREVIEW_PASS", flush=True)
        before = tuple(obj.Shape for obj in preview.Objects)
        assert preview.UndoCount == 1
        preview.undo()
        assert not preview.Objects
        preview.redo()
        assert len(preview.Objects) == len(before)
        assert all(p.catalogue_adapter._same_presented_shape(obj.Shape, shape)
                   for obj, shape in zip(preview.Objects, before))
        receipt["redo_new_comparisons"] = _assert_new(
            result, preview, references, witnesses,
        )
        unchanged("Undo/Redo", preview)
        receipt["undo_redo"] = "PASS"
        if gui:
            receipt["images"] = _gui_inspection(preview, witnesses, run_dir)
            lifecycle._restore_selection(App, gui, selection)
            lifecycle._restore_preselection(App, gui, preselection)
            unchanged("GUI inspection", preview)
            receipt["visibility_selection"] = "PASS"
            receipt["camera_animation_restored"] = True
        _close_preview(
            preview, source, gui, selection, preselection, unchanged,
        )
        receipt["focused_failures"] = _focused_failures(
            create, captured, module, path, prepared, registry, source, unchanged,
        )
        for family in (*previous.whole.COUNTS, "CC", "CCL", "CCR", "L1"):
            reader.verify_catalogue_sources(prepared[family])
        previous.paired.pairs.verify_paired_catalogue(tuple(
            prepared[group] for group in previous.paired.PAIR_IDS
        ))
        for filename, digest in data["bindings"].items():
            assert catalogue._hash(Path(filename)) == digest
        assert catalogue._hash(source.FileName) == xo.FIXTURE_SHA256
        assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
        assert xo._context(module, source) == context
        unchanged("complete proof", source)
        receipt.update(
            fixture_sha256=xo.FIXTURE_SHA256, source_bindings_unchanged=True,
            baseline_component_comparisons=4215, new_component_comparisons=674,
            redo_new_component_comparisons=674, transaction_rollback="PASS",
            rollback_scope="new single-rail preparation and shared lifecycle",
            complete_baseline_failure_suite="reused accepted check-end receipt",
            legacy_exclusions_unchanged_except_qualified_additions=True,
        )
    except BaseException:
        receipt.update(status="FAIL", traceback=traceback.format_exc())
        raise
    finally:
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
