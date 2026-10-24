"""Prove twelve central CC additions in native and real-GUI hosts.

The accepted paired receipt owns the unchanged 183 placements. Every one
of their 3555 components is compared with its copied native model. The
396 added components use an independent source and canonical-host oracle.
Focused rollback repeats the new CC preparation and shared lifecycle;
it does not repeat the already accepted complete baseline failure suite.
Private source agreement provides no physical-fit or production approval.
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
from types import SimpleNamespace
from unittest.mock import patch

import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]


def _load_paired():
    spec = importlib.util.spec_from_file_location(
        "_central_check_paired",
        ROOT / "tests/freecad_validate_phase9b_catalogue_paired_crossover.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


paired = _load_paired()
p, xo, whole = paired.p, paired.xo, paired.whole
adapter, lifecycle = paired.adapter, paired.lifecycle
catalogue, combined = paired.catalogue, paired.combined

import central_check_source_oracle as oracle  # noqa: E402
from tracktemplate.application import chair_catalogue as reader  # noqa: E402
from tracktemplate.domain.central_check_placement import (  # noqa: E402
    CentralCheckPlacement,
)

SENTINEL = "Phase 9B central check catalogue FreeCAD validation passed"
BASELINE_SHA256 = (
    "e914317c36662d439c94034ee274646ea06468f70be49dc5466f94ed4ea2dbaa"
)
MODEL_SHA256 = (
    "b28b574a517e677c86fc35e26cab9a966e41504cb2242968db45e7c07ac81637"
)
POSITION_FIELDS = ("position_id", "rail_id", "timber_id")
FRAME_FIELDS = ("origin_mm", "x_axis", "y_axis")


def _read_baseline(path):
    assert catalogue._hash(path) == BASELINE_SHA256
    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["status"] == "PASS" and not result["gui"]
    assert result["profile"] == p.PROFILE
    assert result["fixture_sha256"] == xo.FIXTURE_SHA256
    assert result["component_comparisons"] == 3555
    assert result["preview"]["placement_count"] == 183
    return result


def _references(path, supplement, run_dir):
    references, prepared = paired._references(path, supplement, run_dir)
    selected = reader.prepare_catalogue_chair(
        path, "CC", run="context-native-02",
    )
    assert selected.model_sha256 == MODEL_SHA256
    native = catalogue._reference(("CC", {
        "run": selected.run,
        "model": {"path": selected.model_path, "sha256": MODEL_SHA256},
    }), run_dir / "native-copies")
    references["CC"] = {name: shape for name, _label, shape, _matrix in native}
    prepared["CC"] = selected
    assert len(native) == len(selected.components) == 33
    assert tuple(references["CC"]) == tuple(c.name for c in selected.components)
    return references, prepared


def _frame(record):
    return SimpleNamespace(**{
        **{name: record[name] for name in POSITION_FIELDS},
        **{name: tuple(record[name]) for name in FRAME_FIELDS},
    })


def _near_frame(actual, expected):
    """Compare lengths in mm separately from dimensionless unit axes."""
    assert math.dist(actual["origin_mm"], expected.origin_mm) <= p.EPSILON_MM
    for name in ("x_axis", "y_axis"):
        assert math.dist(actual[name], getattr(expected, name)) <= 1e-12


def _world_point(common, point):
    return tuple(common["origin_mm"][axis]
                 + point[0] * common["x_axis"][axis]
                 + point[1] * common["y_axis"][axis] for axis in (0, 1))


def _world_frame(position, local, common, rail_top_z):
    origin = _world_point(common, [local[0][3], local[1][3]])
    axes = [tuple(
        local[0][column] * common["x_axis"][axis]
        + local[1][column] * common["y_axis"][axis]
        for axis in (0, 1)
    ) for column in (0, 1)]
    return SimpleNamespace(
        position_id=position["stable_chair_position_identity"],
        rail_id=position["rail_identity"], timber_id=position["timber_identity"],
        origin_mm=tuple(origin) + (rail_top_z + local[2][3],),
        x_axis=axes[0], y_axis=axes[1],
    )


def _witnesses(module, source, context, supplement, data):
    """Read actual host arrays and compose independent source matrices."""
    binding = json.loads(supplement.read_text())["canonical_hosts"]
    host_path = Path(binding["path"])
    assert catalogue._hash(host_path) == binding["sha256"]
    captured = json.loads(host_path.read_text())
    assert captured["fixture_sha256"] == xo.FIXTURE_SHA256
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
    positions = {item["stable_chair_position_identity"]: item
                 for item in context[1]["positions"]}
    checks = {}
    for context_id, target in data["contexts"].items():
        for identity in target["source_position_ids"]:
            position = positions[identity]
            if not position["rail_name"].endswith("stock rail"):
                continue
            side = {"XO-001-A001": "A", "XO-001-B001": "B"}[
                position["parent_turnout_identity"]]
            host = hosts[side]
            common = oracle.expected_world_frame(
                host, toe_chainage_mm=host["toe_chainage"],
                direction=1 if side == "A" else -1, hand=-1,
                station_mm=target["station_mm"], gauge_mm=16.5,
            )
            components, expected_points = {}, {}
            for part_id, part in data["parts"].items():
                name = part["native_object"]
                components[name] = _world_frame(
                    position, oracle.native_to_target(data, context_id, part_id),
                    common, base_z + 149 / 60,
                )
                expected_points[name] = [
                    _world_point(common, point)
                    + (base_z + 149 / 60 + point[2],)
                    for point in oracle.source_target_vertices(
                        data, context_id, part_id,
                    )
                ]
            mates = [value for value in target["source_position_ids"]
                     if positions[value]["parent_turnout_identity"]
                     == position["parent_turnout_identity"] and value != identity]
            mate, = mates
            assert positions[mate]["rail_name"].endswith("check rail")
            points = expected_points["base_plinth"]
            centre = tuple((min(p[i] for p in points)
                            + max(p[i] for p in points)) / 2 for i in range(3))
            checks[identity] = {
                "context_id": context_id, "side": side,
                "mate_position_id": mate, "components": components,
                "source_vertices": expected_points, "centre_mm": centre,
            }
    assert len(checks) == 12
    return checks


def _coverage(receipt, context, baseline, witnesses):
    """Keep canonical deferred records while deriving bounded support."""
    old = baseline["preview"]["source_receipt"]
    positions = {item["stable_chair_position_identity"]: item
                 for item in context[1]["positions"]}
    selected = {item["position_id"]: item for item in receipt["selected_positions"]}
    excluded = {item["position_id"]: item for item in receipt["excluded_positions"]}
    assert len(selected) == receipt["placement_count"] == 195
    assert len(excluded) == receipt["excluded_position_count"] == 160
    assert len(positions) == receipt["analysis_position_count"] == 355
    assert not selected.keys() & excluded.keys()
    assert selected.keys() | excluded.keys() == positions.keys()
    assert receipt["selected_counts"] == dict(paired.COUNTS, CC=12)
    assert Counter(item["exclusion_kind"] for item in excluded.values()) == {
        "source-assignment-deferred": 100,
        "confirmed-no-separate-chair": 48,
        "source-paired-reference-support": 12,
    }
    assert receipt["represented_source_position_count"] == 255
    assert receipt["unrepresented_source_position_count"] == 100
    assert receipt["existing_shared_support_count"] == 48
    assert receipt["source_paired_check_support_count"] == 12
    assert receipt["canonical_deferred_assignment_count"] == 124
    assert sum(bool(p["special_assignment_deferred"])
               for p in positions.values()) == 124
    for name in ("source_context_signature", "source_analysis_signature",
                 "original_analytical_exclusions"):
        assert receipt[name] == old[name]
    assert receipt["original_analytical_exclusions"] == context[3]["analytical_only"]
    assert not receipt["source_document_mutation"]
    assert not receipt["model_support_adjustments_applied"]
    for item in old["selected_positions"]:
        assert selected[item["position_id"]] == item
    for item in old["excluded_positions"]:
        identity = item["position_id"]
        if identity not in witnesses and identity not in {
                w["mate_position_id"] for w in witnesses.values()}:
            assert excluded[identity] == item
    for identity, witness in witnesses.items():
        item = selected[identity]
        assert item["family"] == "CC"
        assert item["context_id"] == witness["context_id"]
        assert item["mate_position_id"] == witness["mate_position_id"]
        mate = excluded[witness["mate_position_id"]]
        assert mate["supporting_position_id"] == identity
        assert mate["supporting_assembly_placed"] is True
        assert mate["exclusion_kind"] == "source-paired-reference-support"
        for position_id in (identity, witness["mate_position_id"]):
            position = positions[position_id]
            assert position["special_assignment_deferred"]
            assert position["timber_identity"] == positions[identity]["timber_identity"]
        for name in ("rail_id", "timber_id"):
            assert item[name] == getattr(witness["components"]["base_plinth"], name)


def _source_vertices(shape, expected):
    observed = [tuple(vertex.Point) for vertex in shape.Vertexes]
    assert len(observed) == len(expected)
    residuals = [min(math.dist(a, b) for b in expected) for a in observed]
    residuals += [min(math.dist(a, b) for b in observed) for a in expected]
    maximum = max(residuals)
    assert maximum <= p.EPSILON_MM, maximum
    return maximum


def _assert_cc(result, document, references, witnesses):
    record = result["families"]["CC"]
    assert record["source_model_sha256"] == MODEL_SHA256
    assert record["run"] == "context-native-02"
    assert record["placement"] == "source-central-check-component-frames.v1"
    assert record["component_count"] == 33 and record["placement_count"] == 12
    names = tuple(references["CC"])
    assert tuple(c["source_name"] for c in record["components"]) == names
    checks = []
    for index, placement in enumerate(record["placements"]):
        identity = placement["position_id"]
        witness = witnesses[identity]
        _near_frame(placement, witness["components"]["base_plinth"])
        assert len(placement["components"]) == 33
        for name, component in zip(names, placement["components"]):
            frame = witness["components"][name]
            _near_frame(component, frame)
            assert tuple(component["placement_identity"]) == (
                identity, MODEL_SHA256, name,
            )
            obj = document.getObject("CC_" + name)
            children = obj.Shape.childShapes()
            assert len(children) == 12
            child = children[index]
            checks.append(dict(
                p._compare_component(child, references["CC"][name], frame),
                source_vertex_residual_mm=_source_vertices(
                    child, witness["source_vertices"][name],
                ), position_id=identity, component=name,
            ))
    assert len(checks) == 396
    assert {p["position_id"] for p in record["placements"]} == witnesses.keys()
    return checks


def _assert_preview(result, document, references, baseline, witnesses):
    catalogue.helpers._active_document_state(document)
    assert not document.FileName and not document.Temporary
    assert result["contract_id"] == "tracktemplate.private-catalogue-crossover.v3"
    assert result["placement_count"] == result["track_placements_added"] == 195
    assert result["family_count"] == 9 and result["assembly_group_count"] == 14
    assert result["component_count"] == 411 and result["layer_count"] == 413
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["geometry_rebuilt"] is False
    assert result["length_basis"] == "model" and result["length_unit"] == "mm"
    assert result["scale_denominator"] == "76.2"
    names = paired.LAYER_NAMES + tuple("CC_" + name for name in references["CC"])
    assert tuple(obj.Name for obj in document.Objects) == names
    assert tuple(layer["name"] for layer in result["layers"]) == names
    for obj in document.Objects:
        assert obj.TypeId == "Part::Feature"
        assert "GeneratedBy" not in obj.PropertiesList
    for obj in document.Objects[:2]:
        assert not obj.Shape.Faces and not obj.Shape.Solids
    baseline_checks = []
    for group, old in baseline["preview"]["families"].items():
        actual = result["families"][group]
        for name in ("run", "source_model_sha256", "source_bindings",
                     "context", "placement_count", "component_count"):
            assert json.loads(json.dumps(actual[name])) == old[name]
        assert len(actual["placements"]) == len(old["placements"])
        for index, (current, accepted) in enumerate(zip(
                actual["placements"], old["placements"])):
            for name in POSITION_FIELDS + FRAME_FIELDS:
                assert json.loads(json.dumps(current[name])) == accepted[name]
            frame = _frame(accepted)
            assert len(current["components"]) == len(accepted["components"])
            for component, previous in zip(current["components"], accepted["components"]):
                name = component["source_name"]
                assert name == previous["source_name"]
                assert component["source_identity"] == tuple(previous["source_identity"])
                assert tuple(component["placement_identity"]) == tuple(previous["placement_identity"])
                assert not any(key in component for key in FRAME_FIELDS)
                children = document.getObject(
                    group.replace("-", "_") + "_" + name,
                ).Shape.childShapes()
                assert len(children) == len(old["placements"])
                baseline_checks.append(dict(
                    p._compare_component(children[index], references[group][name], frame),
                    position_id=frame.position_id, group=group, component=name,
                ))
    assert len(baseline_checks) == 3555
    assert result["solid_count"] == sum(len(obj.Shape.Solids)
                                        for obj in document.Objects)
    return {"baseline": baseline_checks,
            "central_cc": _assert_cc(result, document, references, witnesses)}


def _inspection_frames(baseline, witnesses):
    groups = {group: tuple(_frame(item) for item in record["placements"])
              for group, record in baseline["preview"]["families"].items()}
    for identity, witness in witnesses.items():
        label = witness["context_id"]
        groups.setdefault(label, [])
        groups[label].append(SimpleNamespace(
            position_id=identity, origin_mm=witness["centre_mm"],
        ))
    return groups


def _check_factory_inputs(arguments, baseline, witnesses):
    """Check the complete command's analytical boundary before geometry."""
    assert len(arguments) == 5
    groups, _context, receipt, _verify = arguments[1:]
    assert set(groups) == set(paired.COUNTS) | {"CC"}
    for group, old in baseline["preview"]["families"].items():
        assert len(groups[group]) == len(old["placements"])
        for placement, accepted in zip(groups[group], old["placements"]):
            for name in POSITION_FIELDS + FRAME_FIELDS:
                assert json.loads(json.dumps(getattr(placement, name))) == accepted[name]
    assert len(groups["CC"]) == 12
    for placement in groups["CC"]:
        witness = witnesses[placement.position_id]
        _near_frame(vars(placement), witness["components"]["base_plinth"])
        for index, fixing in enumerate(placement.fixing_frames):
            name = "SourceFixing" + (f"{index * 4:03d}" if index else "")
            _near_frame(vars(fixing), witness["components"][name])
    return receipt


def validate():
    """Run one complete build and the focused CC lifecycle failures."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    path = Path(os.environ["TRACKTEMPLATE_CHAIR_CATALOGUE"]).resolve()
    supplement = Path(os.environ["TRACKTEMPLATE_PAIRED_CATALOGUE"]).resolve()
    fixture = Path(os.environ["TRACKTEMPLATE_CROSSOVER_REFERENCE_FIXTURE"])
    source_directory = Path(os.environ["TRACKTEMPLATE_TEMPLOT_SOURCE"])
    source_context = Path(os.environ["TRACKTEMPLATE_CC_SOURCE_CONTEXT"])
    baseline_path = Path(os.environ["TRACKTEMPLATE_PAIRED_BASELINE_RECEIPT"])
    run_dir = Path(os.environ["TRACKTEMPLATE_CC_PREVIEW_RUN_DIR"]).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp),
               "physical_fit": "NOT_PROVED", "baseline_sha256": BASELINE_SHA256}
    initial = catalogue.helpers._document_state()
    try:
        assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
        baseline = _read_baseline(baseline_path)
        data = oracle.load(source_directory, path.parent, source_context)
        receipt["source_analytical_admission"] = oracle.analytical_admission(data)
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
        foreign = App.newDocument("CentralCheckUnrelatedWitness")
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
        witnesses = _witnesses(module, source, context, supplement, data)
        receipt["source_bindings"] = data["bindings"]
        receipt["source_references"] = data["references"]
        receipt["source_witnesses"] = {
            identity: {key: value for key, value in witness.items()
                       if key not in ("components", "source_vertices")}
            for identity, witness in witnesses.items()
        }
        xo._state(module, source)
        combined._settle(source)
        source_state = xo._state(module, source)
        foreign_state = combined._foreign_state(foreign)
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
            assert all(identities[key].Shape.isSame(shape)
                       for key, shape in shapes.items()), stage
            assert lifecycle._selection_snapshot(App, gui) == selection, stage
            assert lifecycle._preselection_snapshot(App, gui) == preselection
            catalogue.helpers._active_document_state(active)

        def create(**options):
            kwargs = dict(paired_contexts_path=supplement, include_central_cc=True)
            kwargs.update(options)
            return command(source, "XO-001", path, **kwargs)

        captured = {}
        native_create = adapter.create_private_catalogue_crossover_preview

        def capture_factory(*args, **kwargs):
            captured.update(args=args, kwargs=kwargs)
            return native_create(*args, **kwargs)

        if os.environ.get("TRACKTEMPLATE_CC_PREFLIGHT_ONLY") == "1":
            def capture_only(*args, **kwargs):
                captured.update(args=args, kwargs=kwargs)
                return {"captured": True}

            with patch.object(
                    session, "_private_catalogue_crossover_preview_factory",
                    side_effect=capture_only):
                assert create() == {"captured": True}
            source_receipt = _check_factory_inputs(
                captured["args"], baseline, witnesses,
            )
            _coverage(source_receipt, context, baseline, witnesses)
            unchanged("analytical command preflight", source)
            receipt.update(status="PASS_ANALYTICAL_COMMAND_PREFLIGHT",
                           source_receipt=source_receipt)
            print("CENTRAL_CC_ANALYTICAL_COMMAND_PREFLIGHT_PASS", flush=True)
            return

        started = time.perf_counter()
        with patch.object(session, "_private_catalogue_crossover_preview_factory",
                          side_effect=capture_factory), patch.object(
                App, "openDocument", side_effect=AssertionError(
                    "Product restored an external source document")):
            result = create()
        _check_factory_inputs(captured["args"], baseline, witnesses)
        receipt["elapsed_creation_seconds"] = time.perf_counter() - started
        preview = App.getDocument(result["document_name"])
        receipt["preview"] = result
        _coverage(result["source_receipt"], context, baseline, witnesses)
        receipt["comparisons"] = _assert_preview(
            result, preview, references, baseline, witnesses,
        )
        unchanged("created", preview)
        print("CENTRAL_CC_COMPLETE_PREVIEW_PASS", flush=True)
        before = tuple(obj.Shape for obj in preview.Objects)
        assert preview.UndoCount == 1
        preview.undo()
        assert not preview.Objects
        preview.redo()
        assert len(preview.Objects) == len(before)
        assert all(p.catalogue_adapter._same_presented_shape(obj.Shape, shape)
                   for obj, shape in zip(preview.Objects, before))
        receipt["redo_cc_comparisons"] = _assert_cc(
            result, preview, references, witnesses,
        )
        unchanged("Undo/Redo", preview)
        receipt["undo_redo"] = "PASS"
        if gui:
            receipt["images"] = whole._gui_inspection(
                preview, _inspection_frames(baseline, witnesses), context, run_dir,
            )
            assert len(receipt["images"]) == 38
            lifecycle._restore_selection(App, gui, selection)
            lifecycle._restore_preselection(App, gui, preselection)
            unchanged("GUI inspection", preview)
            receipt["visibility_selection"] = "PASS"
            receipt["camera_animation_restored"] = True
        App.closeDocument(preview.Name)
        App.setActiveDocument(source.Name)
        lifecycle._restore_selection(App, gui, selection)
        lifecycle._restore_preselection(App, gui, preselection)
        combined._settle(source)
        unchanged("test-owned close", source)

        with patch.object(App, "newDocument", side_effect=AssertionError(
                "Missing paired prerequisite created a document")):
            receipt["paired_prerequisite_refusal"] = catalogue._reject(
                lambda: create(paired_contexts_path=None), ValueError,
            )
        unchanged("early prerequisite refusal", source)
        original_read = reader._read

        def changed_bytes(filename):
            content = original_read(filename)
            return (content + b"\n" if str(filename) == prepared["CC"].model_path
                    else content)

        with patch.object(reader, "_read", changed_bytes), patch.object(
                App, "newDocument", side_effect=AssertionError(
                    "Changed CC geometry created a document")):
            receipt["model_refusal"] = catalogue._reject(create, ValueError)
        unchanged("early CC model refusal", source)
        arguments = captured["args"]
        assert len(arguments) == 5
        placements, context_shapes, source_receipt, verify_source = arguments[1:]
        assert len(placements["CC"]) == 12
        selected = prepared["CC"]

        def focused(verify=verify_source):
            choice, specs, prepare = adapter._prepare_catalogue_family(
                path, placements["CC"], context_shapes, source_receipt,
                family="CC", placement_type=CentralCheckPlacement,
                model_sha256=MODEL_SHA256,
                source_names=tuple(item.name for item in selected.components),
                run=selected.run, source_context=selected.context,
            )

            def verify_inputs():
                verify()
                reader.verify_catalogue_sources(choice)

            return adapter._materialise_preview(
                "CC", source_receipt, specs, prepare, verify_inputs,
            )

        def late_bytes(filename):
            if App.ActiveDocument not in registry.values():
                assert len(App.ActiveDocument.Objects) == 35
                return changed_bytes(filename)
            return original_read(filename)

        with patch.object(reader, "_read", late_bytes):
            receipt["focused_late_model_refusal"] = catalogue._reject(
                focused, ValueError,
            )
        unchanged("focused late model rollback", source)
        original_host = module.turnout_host_alignment

        def stale_source():
            assert App.ActiveDocument not in registry.values()
            assert len(App.ActiveDocument.Objects) == 35

            def changed_host(obj):
                host = dict(original_host(obj))
                headings = list(host["headings"])
                headings[0] += 1e-8
                return dict(host, headings=headings)

            with patch.object(module, "turnout_host_alignment", changed_host):
                verify_source()

        receipt["focused_late_host_refusal"] = paired.helpers._reject(
            lambda: focused(stale_source), "changed",
        )
        unchanged("focused late host rollback", source)
        original_check = adapter._same_presented_shape

        def reject_stored(actual, expected):
            if App.ActiveDocument not in registry.values():
                assert len(App.ActiveDocument.Objects) == 35
                return False
            return original_check(actual, expected)

        with patch.object(adapter, "_same_presented_shape", reject_stored):
            receipt["focused_stored_shape_refusal"] = catalogue._reject(
                focused, ValueError,
            )
        unchanged("focused stored shape rollback", source)
        for group in (*whole.COUNTS, "CC"):
            reader.verify_catalogue_sources(prepared[group])
        paired.pairs.verify_paired_catalogue(tuple(
            prepared[group] for group in paired.PAIR_IDS
        ))
        for filename, digest in data["bindings"].items():
            assert catalogue._hash(Path(filename)) == digest
        assert catalogue._hash(source.FileName) == xo.FIXTURE_SHA256
        assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
        assert xo._context(module, source) == context
        receipt.update(
            source_after=xo._state(module, source),
            foreign_after=combined._foreign_state(foreign),
            fixture_sha256=xo.FIXTURE_SHA256, source_bindings_unchanged=True,
            baseline_component_comparisons=3555, cc_component_comparisons=396,
            redo_cc_component_comparisons=396, transaction_rollback="PASS",
            rollback_scope="new CC preparation and shared lifecycle",
            complete_baseline_failure_suite="reused accepted paired receipt",
            legacy_exclusions_unchanged=True,
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
