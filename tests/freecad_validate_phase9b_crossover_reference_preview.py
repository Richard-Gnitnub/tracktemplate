"""Prove private S1/S1J crossover placement in an isolated qualified host.

Copy the retained XO-001 input. Keep its decisions, unresolved positions and
all pre-existing native and GUI state. This proves no production, fit,
persistence, rights, performance or phase acceptance.
"""

import datetime
from fractions import Fraction
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

from tracktemplate.adapters.freecad import (  # noqa: E402
    chair_reference_preview as adapter,
)
from tracktemplate.application.chair_model_research import (  # noqa: E402
    prepare_chair_model_research,
    prepare_chair_s1j_model_research,
)
from tracktemplate.compatibility import (  # noqa: E402
    chair_reference_preview as binding,
)


SENTINEL = "Phase 9B crossover preview FreeCAD validation passed"
FIXTURE_SHA256 = (
    "d9e46e561b16f23813072d540d2829920ddaa83bd2bde36290bc465d920ee576"
)
PROFILE = "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10"


def _helpers():
    spec = importlib.util.spec_from_file_location(
        "_crossover_combined_preview_helpers",
        ROOT / "tests/freecad_validate_phase9b_s1_s1j_reference_preview.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ROOT == ROOT
    return module


combined = _helpers()
helpers = combined.helpers
LAYER_NAMES = combined.LAYER_NAMES


def _active(document):
    """Check both native and Python GUI active-document references."""
    assert App.ActiveDocument is document
    if App.GuiUp:
        assert Gui.activeDocument().Document is document
        assert Gui.ActiveDocument.Document is document


def _state(module, document):
    return helpers._state(module, document, "crossover", "XO-001")


def _context(module, document):
    return binding._source_context(
        module, document, "XO-001", "S1/S1J", entity_kind="crossover",
    )


def _expected_placements(module, context):
    """Check all retained and recovered frames against their raw sources."""
    _signature, analysis, _settings, plan, rails, timbers = context
    before = json.dumps(context, sort_keys=True)
    s1, s1j, excluded = binding._select_s1_s1j_positions(
        module, analysis, plan,
    )
    old = (s1, s1j)
    recovered = []
    prepared = []
    for code, placements in zip((1, 7), old):
        placements, excluded, records = binding._recover_positions(
            module, analysis, plan, rails, timbers, placements, excluded, code,
        )
        recovered.extend(records)
        prepared.append(placements)
    by_position = {p["stable_chair_position_identity"]: p
                   for p in analysis["positions"]}
    by_rail = {r["stable_identity"]: r for r in rails}
    instances = {p["chair_position_identity"]: p for p in plan["instances"]}
    witnesses = {p["position_id"]: p for p in recovered}
    datums = {p["base_z"] for p in plan["instances"]}
    assert len(datums) == 1
    base_z = next(iter(datums))
    observations = []
    for code, original, current in zip((1, 7), old, prepared):
        current_by_id = {p.position_id: p for p in current}
        assert all(current_by_id[p.position_id] is p for p in original)
        for placed in current:
            position = by_position[placed.position_id]
            assert position["chair_code"] == code
            assert position["assignment_status"] == (
                module.CHAIR_ASSIGNMENT_CONFIRMED
            )
            assert not position["special_assignment_deferred"]
            assert not position["deliberate_omission"]
            assert placed.rail_id == position["rail_identity"]
            assert placed.timber_id == position["timber_identity"]
            assert placed.origin_mm == (*position["centre_point"], base_z)
            if placed.position_id in instances:
                item = instances[placed.position_id]
                assert placed.x_axis == tuple(-v for v in item["local_y_axis"])
                assert placed.y_axis == tuple(item["outward_axis"])
                method = item["gauge_normal_source"]
                if method == "connector rail offset sign":
                    tangent = position["local_rail_tangent"]
                    length = math.hypot(*tangent)
                    sign = by_rail[placed.rail_id]["source_configuration"][
                        "gauge_normal_sign"
                    ]
                    expected_y = (sign * tangent[1] / length,
                                  -sign * tangent[0] / length)
                    assert placed.y_axis == expected_y
            else:
                record = witnesses[placed.position_id]
                tangent = position["local_rail_tangent"]
                centre = position["centre_point"]
                rail = by_rail[placed.rail_id]
                sides = []
                for face in ("gauge", "outer"):
                    index, fraction, point = helpers._face_crossing(
                        centre, tangent, rail[face + "_face_points"],
                    )
                    evidence = record["frame_evidence"][face + "_face"]
                    assert tuple(Fraction(v) for v in
                                 evidence["point_mm_exact"]) == point
                    assert evidence["segments"] == [{
                        "index": index, "fraction_exact": str(fraction),
                    }]
                    delta = tuple(p - Fraction(c)
                                  for p, c in zip(point, centre))
                    sides.append(-Fraction(tangent[1]) * delta[0]
                                 + Fraction(tangent[0]) * delta[1])
                assert sides[0] * sides[1] < 0
                sign = 1 if sides[0] > 0 else -1
                length = math.hypot(*tangent)
                expected_y = (sign * tangent[1] / length,
                              -sign * tangent[0] / length)
                assert placed.y_axis == expected_y
                assert placed.x_axis == (expected_y[1], -expected_y[0])
                method = "independent named-face section"
            observations.append({"position_id": placed.position_id,
                                 "frame_basis": method,
                                 "origin_mm": placed.origin_mm})
    assert json.dumps(context, sort_keys=True) == before
    return tuple(prepared), excluded, sorted(
        recovered, key=lambda item: item["position_id"],
    ), observations


def _stored_components(document, models, placements):
    """Compare every stored component with model vertices and volume."""
    tolerance = adapter.NUMERICAL_LENGTH_TOLERANCE_MM
    observations = []
    for family_index, (model, values) in enumerate(zip(models, placements)):
        layers = document.Objects[2 + family_index * 5:7 + family_index * 5]
        for component, obj in zip(model.components, layers):
            shapes = obj.Shape.childShapes()
            assert len(shapes) == len(values) == len(obj.Shape.Solids)
            total = 0.0
            total_budget = 0.0
            for shape, placed in zip(shapes, values):
                assert shape.isValid() and shape.isClosed()
                assert shape.ShapeType == "Solid" and len(shape.Solids) == 1
                points = []
                for _name, x, y, z in component.geometry.vertices:
                    points.append((
                        placed.origin_mm[0] + float(x) * placed.x_axis[0]
                        + float(y) * placed.y_axis[0],
                        placed.origin_mm[1] + float(x) * placed.x_axis[1]
                        + float(y) * placed.y_axis[1],
                        placed.origin_mm[2] + float(z),
                    ))
                bounds = tuple(min(p[i] for p in points) for i in range(3))
                bounds += tuple(max(p[i] for p in points) for i in range(3))
                assert max(abs(a - b) for a, b in zip(
                    adapter._bounds(shape), bounds,
                )) <= tolerance
                assert len(shape.Vertexes) == len(component.geometry.vertices)
                assert len(shape.Faces) == len(component.geometry.faces)
                expected = float(component.geometry.volume_mm3)
                budget = max(shape.Area * tolerance, expected * 1e-12)
                assert math.isfinite(shape.Volume) and shape.Volume > 0
                assert abs(shape.Volume - expected) <= budget
                total += shape.Volume
                total_budget += budget
            assert abs(obj.Shape.Volume - total) <= total_budget
            observations.append({
                "layer": obj.Name, "component_id": component.component_id,
                "solid_count": len(shapes), "volume_mm3": total,
            })
    return observations


def _assert_result(
    result, document, models, placements, context, exclusions, context_shapes,
):
    _active(document)
    assert not document.FileName and document.Temporary is False
    assert tuple(obj.Name for obj in document.Objects) == LAYER_NAMES
    assert result["layer_count"] == 12
    assert result["placement_count"] == sum(map(len, placements))
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["key_placement"] == "central-reference-only"
    assert result["length_unit"] == "mm" and result["length_basis"] == "model"
    assert tuple(item["name"] for item in result["layers"]) == LAYER_NAMES
    selected = set()
    for family, model, values, measured in zip(
        ("S1", "S1J"), models, placements, result["families"],
    ):
        assert measured["family"] == family
        assert measured["package_signature"] == model.package.content_signature
        assert measured["manifest_signature"] == model.manifest_signature
        assert measured["request_signature"] == model.request_signature
        assert measured["placement_count"] == len(values)
        combined._assert_placements(measured["placements"], values)
        ids = {p.position_id for p in values}
        assert selected.isdisjoint(ids)
        selected.update(ids)
        for observed in measured["placements"]:
            actual_ids = tuple(p["component_id"]
                               for p in observed["components"])
            assert actual_ids == tuple(
                p.component_id for p in model.components
            )
    source = result["source_receipt"]
    assert source["crossover_id"] == "XO-001" and "turnout_id" not in source
    assert source["source_kind"] == "crossover"
    assert source["timber_context"] == "current B4 resolved timbers"
    assert source["source_context_signature"] == "sha256:" + hashlib.sha256(
        context[0].encode("utf-8"),
    ).hexdigest()
    analysis = context[1]
    assert source["source_analysis_signature"] == (
        analysis["geometry_signature"]
    )
    assert len(analysis["positions"]) == 355
    assert source["analysis_position_count"] == 355
    assert len(context[-1]) == 86
    confirmed = {}
    for family, code, total, values in zip(
        ("s1", "s1j"), (1, 7), (123, 12), placements,
    ):
        confirmed[family] = {
            p["stable_chair_position_identity"] for p in analysis["positions"]
            if p["chair_code"] == code and p["assignment_status"] == (
                "confirmed ordinary or turnout assignment"
            )
        }
        assert len(confirmed[family]) == total
        assert source[f"confirmed_{family}_count"] == total
        assert source[f"selected_{family}_count"] == len(values) > 0
        assert source[f"unresolved_confirmed_{family}_count"] == (
            total - len(values)
        )
    assert source["confirmed_count"] == 135
    assert source["selected_count"] == len(selected)
    assert source["unresolved_confirmed_count"] == 135 - len(selected)
    assert source["excluded_positions"] == exclusions
    excluded = {p["position_id"] for p in exclusions}
    all_ids = {p["stable_chair_position_identity"]
               for p in analysis["positions"]}
    assert len(excluded) == len(exclusions) == 355 - len(selected)
    assert selected.isdisjoint(excluded) and selected | excluded == all_ids
    other = all_ids - set.union(*confirmed.values())
    assert len(other) == 220 and other <= excluded
    original_reasons = {p["chair_position_identity"]: p["reason"]
                        for p in context[3]["analytical_only"]}
    for item in exclusions:
        if item["position_id"] in original_reasons:
            assert item["reason"] == original_reasons[item["position_id"]]
    assert [p["position_id"] for p in exclusions] == sorted(excluded)
    assert all(obj.TypeId == "Part::Feature" for obj in document.Objects)
    assert all("GeneratedBy" not in obj.PropertiesList
               for obj in document.Objects)
    assert all(not obj.Shape.Faces and not obj.Shape.Solids
               for obj in document.Objects[:2])
    for obj, expected in zip(document.Objects[:2], context_shapes):
        assert len(obj.Shape.Edges) == len(expected.Edges)
        assert max(abs(a - b) for a, b in zip(
            adapter._bounds(obj.Shape), adapter._bounds(expected),
        )) <= adapter.NUMERICAL_LENGTH_TOLERANCE_MM
        for edge, original in zip(obj.Shape.Edges, expected.Edges):
            assert type(edge.Curve) is type(original.Curve)
            assert len(edge.Vertexes) == len(original.Vertexes)
            assert all(math.dist(tuple(a.Point), tuple(b.Point)) <= (
                adapter.NUMERICAL_LENGTH_TOLERANCE_MM
            ) for a, b in zip(edge.Vertexes, original.Vertexes))
    return _stored_components(document, models, placements)


def validate():
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    run_dir = Path(os.environ.get(
        "TRACKTEMPLATE_CROSSOVER_REFERENCE_PREVIEW_RUN_DIR",
        ROOT / "benchmark-output" / "crossover-reference-preview" / stamp,
    )).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp)}
    fixture = None
    try:
        fixture = Path(os.environ[
            "TRACKTEMPLATE_CROSSOVER_REFERENCE_FIXTURE"
        ]).resolve()
        source_hash = hashlib.sha256(fixture.read_bytes()).hexdigest()
        assert source_hash == FIXTURE_SHA256
        target = run_dir / "XO-001.FCStd"
        shutil.copy2(fixture, target)
        receipt["fixture"] = {"path": str(fixture), "sha256": FIXTURE_SHA256}
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        api, bootstrap = launcher["_load_foundation"](ROOT)
        session, routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, bootstrap,
        )
        receipt["profile"] = launcher["FOUNDATION_RESULT"][
            "matched_profile_id"
        ]
        assert receipt["profile"] == PROFILE
        receipt["routing"] = routing
        module = session.module
        command = session.preview_s1_s1j_crossover_reference_chairs
        source = App.openDocument(str(target))
        source.UndoMode = 1
        packages = (helpers._inputs("S1"), helpers._inputs("S1J"))
        models = (
            prepare_chair_model_research(*packages[0], helpers.REQUEST),
            prepare_chair_s1j_model_research(*packages[1], helpers.REQUEST),
        )
        arguments = (source, "XO-001", *packages[0], *packages[1],
                     helpers.REQUEST)
        receipt["analysis_rejections"] = {}
        for case in ("missing", "stale", "stale-b4"):
            negative_path = run_dir / (case + ".FCStd")
            shutil.copy2(fixture, negative_path)
            negative = App.openDocument(str(negative_path))
            if case == "missing":
                settings_object = module._chair_settings_object(
                    negative, "crossover", "XO-001",
                )
                setattr(settings_object, module.CHAIR_ANALYSIS_RESULT_PROPERTY,
                        "")
            elif case == "stale":
                module.invalidate_chair_analysis(
                    negative, "crossover", "XO-001", remove_display=True,
                )
            else:
                config = module.crossover_config_by_id(negative, "XO-001")
                config["b4_result"]["resolution_signature"] = (
                    "invalid-preview-test-witness"
                )
                settings_object = module._chair_settings_object(
                    negative, "crossover", "XO-001",
                )
                setattr(
                    settings_object, module.CROSSOVER_CONFIGURATION_PROPERTY,
                    json.dumps(config, sort_keys=True),
                )
                # Refresh only the disposable witness's fallback analysis.
                # The preview must reach its B4 guard, not stale-chair refusal.
                module.analyse_entity_chair_positions(
                    negative, "crossover", "XO-001",
                )
                current = module._chair_generation_context(
                    negative, "crossover", "XO-001",
                )
                config = current[1]
                inherited = module.crossover_inherited_timber_records(
                    negative, config,
                )
                assert not module._crossover_b4_result_is_current(
                    config, inherited, config["b4_result"],
                )
                receipt["stale_b4_fresh_analysis"] = {
                    "entity_id": config["crossover_id"],
                    "chair_position_count": len(current[2]["positions"]),
                    "current_b4": False,
                }
            registry = dict(App.listDocuments())
            try:
                command(negative, *arguments[1:])
            except ValueError as error:
                if case == "stale-b4":
                    assert "Current applied B4" in str(error), str(error)
                receipt["analysis_rejections"][case] = str(error)
            else:
                raise AssertionError("Invalid analysis accepted: " + case)
            assert App.listDocuments() == registry
            App.closeDocument(negative.Name)
        foreign = App.newDocument("UnrelatedCrossoverPreviewWitness")
        keep = foreign.addObject("Part::Feature", "Keep")
        keep.Shape = Part.makeBox(2, 3, 4)
        keep.Label = "Keep this unrelated document"
        foreign.recompute()
        combined._settle(foreign)
        App.setActiveDocument(source.Name)
        if App.GuiUp:
            Gui.getMainWindow().resize(1600, 1000)
            Gui.Selection.addSelection(source.Objects[0])
        combined._settle(source)
        gui = Gui if App.GuiUp else None
        # Finish lazy group Shape access before guarding native archives.
        _state(module, source)
        combined._settle(source)
        source_shapes = {o.Name: o.Shape for o in source.Objects
                         if "Shape" in o.PropertiesList}
        original = _state(module, source)
        combined._settle(source)
        original_foreign = combined._foreign_state(foreign)
        source_objects = {o.Name: o for o in source.Objects}
        registry = dict(App.listDocuments())
        selection = adapter._selection_snapshot(App, gui)
        preselection = adapter._preselection_snapshot(App, gui)
        assert _state(module, source) == original
        _active(source)
        receipt["source_before"] = original
        receipt["foreign_before"] = original_foreign

        def unchanged(stage, *, check_selection=True):
            receipt["state_check_stage"] = stage
            receipt["source_after"] = _state(module, source)
            receipt["foreign_after"] = combined._foreign_state(foreign)
            assert receipt["source_after"] == original, stage
            assert receipt["foreign_after"] == original_foreign, stage
            assert App.getDocument(source.Name) is source
            assert App.getDocument(foreign.Name) is foreign
            assert foreign.getObject(keep.Name) is keep
            for name, obj in source_objects.items():
                assert source.getObject(name) is obj, (stage, name)
            for name, shape in source_shapes.items():
                assert source.getObject(name).Shape.isSame(shape), (
                    stage, name,
                )
            if check_selection:
                assert adapter._selection_snapshot(App, gui) == selection
                assert adapter._preselection_snapshot(App, gui) == preselection

        context = _context(module, source)
        source_roles = {}
        for obj in module._crossover_objects(source, "XO-001"):
            role = module.object_string_property(obj, "GeneratedRole", "")
            source_roles.setdefault(role, []).append(obj)
        context_shapes = []
        for role in (module.CROSSOVER_RAIL_ROLE, module.CROSSOVER_B4_ROLE):
            assert len(source_roles[role]) == 1
            context_shapes.append(source_roles[role][0].Shape.copy())
        placements, excluded, recovered, frames = _expected_placements(
            module, context,
        )
        receipt["independent_frames"] = frames
        receipt["recovered_positions"] = recovered
        contexts = []
        read_context = binding._source_context

        def observed(*args, **kwargs):
            value = read_context(*args, **kwargs)
            contexts.append(value)
            return value

        started = time.perf_counter()
        with patch.object(binding, "_source_context", observed):
            result = command(*arguments)
        receipt["construction_seconds"] = time.perf_counter() - started
        receipt["preview"] = result
        assert len(contexts) == 2 and contexts[0] == contexts[1] == context
        assert result["source_receipt"]["recovered_positions"] == recovered
        preview = App.getDocument(result["document_name"])
        receipt["stored_components"] = _assert_result(
            result, preview, models, placements, context, excluded,
            context_shapes,
        )
        assert App.listDocuments() == dict(registry, **{preview.Name: preview})
        unchanged("successful creation")
        shapes = tuple(o.Shape for o in preview.Objects)
        assert preview.UndoCount == 1
        preview.undo()
        assert not preview.Objects
        preview.redo()
        assert tuple(o.Name for o in preview.Objects) == LAYER_NAMES
        assert all(o.Shape.isSame(shape) for o, shape in zip(
            preview.Objects, shapes,
        ))
        _assert_result(result, preview, models, placements, context, excluded,
                       context_shapes)
        unchanged("Undo and Redo")
        receipt["undo_redo"] = "PASS"
        if App.GuiUp:
            for obj in preview.Objects:
                assert obj.ViewObject.Visibility
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(obj)
                assert Gui.Selection.getSelection() == [obj]
                obj.ViewObject.Visibility = False
                combined._settle(preview)
                assert not obj.ViewObject.Visibility
                obj.ViewObject.Visibility = True
                combined._settle(preview)
                assert obj.ViewObject.Visibility
            Gui.Selection.clearSelection()
            receipt["images"] = {}
            for family, values in zip(("S1", "S1J"), placements):
                directory = run_dir / family.lower()
                directory.mkdir()
                receipt["images"][family] = [
                    str(Path(family.lower()) / name)
                    for name in helpers._images(preview, values, directory)
                ]
            adapter._restore_selection(App, gui, selection)
            adapter._restore_preselection(App, gui, preselection)
            unchanged("component inspection and viewport captures")
            receipt["visibility_selection"] = "PASS"
        App.closeDocument(preview.Name)
        App.setActiveDocument(source.Name)
        adapter._restore_selection(App, gui, selection)
        adapter._restore_preselection(App, gui, preselection)
        # Finish pending test-owned close and selection events.
        combined._settle(source)
        _active(source)
        unchanged("preview close")
        with patch.object(App, "newDocument", side_effect=AssertionError(
            "Invalid second family created a document",
        )):
            try:
                command(source, "XO-001", *packages[0], *packages[0],
                        helpers.REQUEST)
            except ValueError as error:
                receipt["package_rejection"] = str(error)
            else:
                raise AssertionError("S1 package accepted for S1J")
        assert App.listDocuments() == registry
        _active(source)
        unchanged("package rejection")
        original_top = module._chair_physical_top_z
        create = adapter.create_s1_s1j_reference_preview

        def fail_late(*args):
            def verify_changed_source():
                pending = App.ActiveDocument
                assert pending is not source and pending is not foreign
                assert tuple(o.Name for o in pending.Objects) == LAYER_NAMES
                receipt["rollback_owned_document"] = pending.Name
                with patch.object(
                    module, "_chair_physical_top_z",
                    side_effect=lambda *v: original_top(*v) + 1e-8,
                ):
                    args[-1]()
            return create(*args[:-1], verify_changed_source)

        with patch.object(session, "_s1_s1j_reference_preview_factory",
                          side_effect=fail_late):
            receipt["subprecision_rejection"] = helpers._reject(
                lambda: command(*arguments), "source changed",
            )
        assert App.listDocuments() == registry
        _active(source)
        unchanged("late source change rollback")
        receipt["transaction_failure_cleanup"] = "PASS"
        receipt["source_unchanged"] = True
        receipt["foreign_unchanged"] = True
        receipt["status"] = "PASS"
    except BaseException:
        receipt["status"] = "FAIL"
        receipt["traceback"] = traceback.format_exc()
        raise
    finally:
        if fixture is not None and fixture.is_file():
            final_hash = hashlib.sha256(fixture.read_bytes()).hexdigest()
            receipt["fixture_preserved"] = final_hash == FIXTURE_SHA256
            if not receipt["fixture_preserved"]:
                receipt["status"] = "FAIL"
        (run_dir / "result.json").write_text(
            json.dumps(receipt, allow_nan=False, indent=2) + "\n",
            encoding="utf-8",
        )
        for name in tuple(App.listDocuments()):
            App.closeDocument(name)
    assert receipt["status"] == "PASS" and receipt["fixture_preserved"]
    print(SENTINEL)
    return receipt


if __name__ in {
    "__main__", "freecad_validate_phase9b_crossover_reference_preview",
}:
    validate()
