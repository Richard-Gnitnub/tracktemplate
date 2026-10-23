"""Prove private P catalogue placement on a copied C10 turnout.

Compare every placed component with copied native source geometry and
independently evaluated analytical frames. Reuse the existing complete
source-state and GUI lifecycle witnesses without changing their oracles.
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
from types import SimpleNamespace
from unittest.mock import patch

import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.adapters.freecad import (  # noqa: E402
    chair_catalogue_placement_preview as adapter,
    chair_catalogue_preview as catalogue_adapter,
    chair_reference_preview as lifecycle,
)
from tracktemplate.application.chair_catalogue import (  # noqa: E402
    prepare_catalogue_chair,
    verify_catalogue_sources,
)
from tracktemplate.compatibility import (  # noqa: E402
    chair_reference_preview as existing_binding,
)


SENTINEL = "Phase 9B catalogue P placement FreeCAD validation passed"
PROFILE = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-"
    "qt6.11.2-coin4.0.10"
)
EPSILON_MM = 1.0e-7
COMPONENT_NAMES = (
    "base_plinth", "slide_seat", "outer", "SourceFixing",
    *("SourceFixing" + str(index).zfill(3) for index in range(1, 19)),
)
LAYER_NAMES = ("ReferenceRails", "ReferenceTimbers", *COMPONENT_NAMES)


def _load_helper(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ROOT == ROOT
    return module


combined = _load_helper(
    "_catalogue_p_combined", "freecad_validate_phase9b_s1_s1j_reference_preview.py",
)
catalogue = _load_helper(
    "_catalogue_p_import", "freecad_validate_phase9b_chair_catalogue.py",
)
helpers = combined.helpers


def _expected_frames(module, context):
    """Solve sections using the independent tangent-dot-product witness."""
    _signature, analysis, _settings, plan, rails, _timbers = context
    positions = sorted(
        (position for position in analysis["positions"]
         if type(position["chair_code"]) is int
         and position["chair_code"] == 2),
        key=lambda position: position["stable_chair_position_identity"],
    )
    assert len(analysis["positions"]) == 168 and len(positions) == 14
    datums = {instance["base_z"] for instance in plan["instances"]}
    assert datums == {0.8}
    rail_map = {rail["stable_identity"]: rail for rail in rails}
    frames = []
    for position in positions:
        assert position["assignment_status"] == module.CHAIR_ASSIGNMENT_CONFIRMED
        assert not position["deliberate_omission"]
        assert not position["special_assignment_deferred"]
        assert position["key_direction_sign"] == 0
        centre, tangent = position["centre_point"], position["local_rail_tangent"]
        rail = rail_map[position["rail_identity"]]
        sides = []
        for face in ("gauge_face_points", "outer_face_points"):
            _index, _fraction, point = helpers._face_crossing(
                centre, tangent, rail[face],
            )
            sides.append(
                -Fraction(tangent[1]) * (point[0] - Fraction(centre[0]))
                + Fraction(tangent[0]) * (point[1] - Fraction(centre[1]))
            )
        assert sides[0] * sides[1] < 0
        sign = 1 if sides[0] > 0 else -1
        magnitude = math.hypot(*tangent)
        y_axis = (sign * tangent[1] / magnitude,
                  -sign * tangent[0] / magnitude)
        frames.append(SimpleNamespace(
            position_id=position["stable_chair_position_identity"],
            rail_id=position["rail_identity"],
            timber_id=position["timber_identity"],
            origin_mm=(*centre, next(iter(datums))),
            x_axis=(y_axis[1], -y_axis[0]), y_axis=y_axis,
        ))
    assert any(abs(frame.x_axis[1]) > 0.001 for frame in frames)
    return tuple(frames)


def _point(frame, point):
    x, y, z = point
    return (
        frame.origin_mm[0] + x * frame.x_axis[0] + y * frame.y_axis[0],
        frame.origin_mm[1] + x * frame.x_axis[1] + y * frame.y_axis[1],
        frame.origin_mm[2] + z,
    )


def _legacy_partition(module, context):
    """Retain the existing combined route's positions and exclusions."""
    _signature, analysis, _settings, plan, rails, timbers = context
    first, second, excluded = existing_binding._select_s1_s1j_positions(
        module, analysis, plan,
    )
    selected = []
    for code, placements in ((1, first), (7, second)):
        placements, excluded, _records = existing_binding._recover_positions(
            module, analysis, plan, rails, timbers, placements, excluded, code,
        )
        selected.extend(placements)
    assert len(selected) == 59 and len(excluded) == 109
    return tuple(selected), excluded


def _compare_component(actual, reference, frame):
    """Compare transformed coordinates without calling the product transform."""
    assert actual.isValid() and not actual.isNull()
    assert actual.ShapeType == reference.ShapeType
    assert actual.Orientation == reference.Orientation
    counts = tuple(len(getattr(reference, name)) for name in (
        "Solids", "Shells", "Faces", "Wires", "Edges", "Vertexes",
    ))
    assert counts == tuple(len(getattr(actual, name)) for name in (
        "Solids", "Shells", "Faces", "Wires", "Edges", "Vertexes",
    ))
    assert all(solid.isClosed() and solid.isValid() and solid.Volume > 0
               for solid in actual.Solids)
    assert actual.getTolerance(1) == reference.getTolerance(1)
    assert tuple(face.Orientation for face in actual.Faces) == tuple(
        face.Orientation for face in reference.Faces
    )
    expected = [_point(frame, vertex.Point) for vertex in reference.Vertexes]
    observed = [tuple(vertex.Point) for vertex in actual.Vertexes]
    residual = max(math.dist(a, b) for a, b in zip(observed, expected))
    assert residual <= EPSILON_MM, residual
    assert abs(actual.Volume - reference.Volume) <= max(
        reference.Area * EPSILON_MM, reference.Volume * 1.0e-12,
    )
    assert abs(actual.Area - reference.Area) <= max(
        reference.Length * EPSILON_MM, reference.Area * 1.0e-12,
    )
    return {"counts": counts, "vertex_residual_mm": residual}


def _assert_preview(result, document, reference, frames, context):
    """Prove the complete component/position product and retained limits."""
    catalogue.helpers._active_document_state(document)
    assert not document.FileName and not document.Temporary
    assert tuple(obj.Name for obj in document.Objects) == LAYER_NAMES
    assert result["component_count"] == 22
    assert result["placement_count"] == 14 and result["layer_count"] == 24
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["geometry_rebuilt"] is False
    assert result["scale_denominator"] == "76.2"
    assert result["length_basis"] == "model" and result["length_unit"] == "mm"
    excluded = result["excluded_source_components"]
    assert len(excluded) == 1 and excluded[0]["source_name"] == "display_rail"
    _signature, analysis, _settings, plan, _rails, _timbers = context
    source = result["source_receipt"]
    assert source["analysis_position_count"] == len(analysis["positions"])
    assert source["selected_p_count"] == len(source["selected_positions"]) == 14
    assert len(source["remaining_positions"]) == 154
    assert source["original_analytical_exclusions"] == plan["analytical_only"]
    selected_ids = {item["position_id"] for item in source["selected_positions"]}
    remaining_ids = {item["position_id"] for item in source["remaining_positions"]}
    assert not selected_ids & remaining_ids
    assert selected_ids | remaining_ids == {
        item["stable_chair_position_identity"] for item in analysis["positions"]
    }
    assert selected_ids == {frame.position_id for frame in frames}
    for item in source["selected_positions"]:
        assert item["key_direction_sign"] == 0
        assert item["key_orientation"] == (
            "requires a configurable key-direction policy"
        )
        assert item["original_exclusion"] in plan["analytical_only"]
    assert source["source_context_signature"] == "sha256:" + hashlib.sha256(
        context[0].encode("utf-8"),
    ).hexdigest()
    assert source["source_document_mutation"] is False
    assert source["model_support_adjustments_applied"] is False
    measured = []
    for obj in document.Objects[:2]:
        assert not obj.Shape.Solids and not obj.Shape.Faces
    for index, (obj, component) in enumerate(zip(
        document.Objects[2:], result["components"],
    )):
        assert obj.TypeId == "Part::Feature"
        assert "GeneratedBy" not in obj.PropertiesList
        assert component["source_name"] == obj.Name == COMPONENT_NAMES[index]
        assert tuple(component["source_identity"]) == (
            result["source_model_sha256"], obj.Name,
        )
        ref = reference[obj.Name]
        children = obj.Shape.childShapes()
        assert len(children) == len(frames)
        measured.append({
            "name": obj.Name,
            "positions": [_compare_component(child, ref, frame)
                          for child, frame in zip(children, frames)],
        })
    for actual, frame in zip(result["placements"], frames):
        for field in ("position_id", "rail_id", "timber_id"):
            assert actual[field] == getattr(frame, field)
        for field in ("origin_mm", "x_axis", "y_axis"):
            assert tuple(actual[field]) == getattr(frame, field)
        assert len(actual["components"]) == 22
    assert result["solid_count"] == sum(len(obj.Shape.Solids)
                                        for obj in document.Objects)
    # Physical generation retains its historical rejection of every P.
    assert all(item["chair_code"] != 2 for item in plan["instances"])
    return measured


def _prototype_controls(prepared):
    """Separate display meshing from genuine native source changes."""
    stable = []
    first = None
    for component in prepared.components:
        if component.name == "display_rail":
            continue
        shape = Part.Shape()
        shape.importBrepFromString(component.brep_text)
        before = adapter._prototype_state(shape)
        assert set(before) == set(catalogue_adapter._measure_shape(shape))
        vertices = tuple(tuple(vertex.Point) for vertex in shape.Vertexes)
        # This is a display-mesh witness, not a geometric or fit tolerance.
        points, triangles = shape.tessellate(0.1)
        assert points and triangles
        assert adapter._prototype_state(shape) == before, component.name
        assert tuple(tuple(vertex.Point) for vertex in shape.Vertexes) == vertices
        stable.append(component.name)
        if first is None:
            first = shape
    assert tuple(stable) == COMPONENT_NAMES
    baseline = adapter._prototype_state(first)
    rejected = []
    for name in ("translation", "rotation", "small-translation",
                 "small-rotation", "orientation"):
        changed = Part.Shape(first)
        assert adapter._prototype_state(changed) == baseline
        if name == "translation":
            changed.translate(App.Vector(1, 0, 0))
        elif name == "rotation":
            changed.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
        elif name == "small-translation":
            changed.translate(App.Vector(1.0e-12, 0, 0))
        elif name == "small-rotation":
            changed.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 1.0e-10)
        else:
            changed.reverse()
        if name == "orientation":
            message = catalogue._reject(
                lambda: adapter._prototype_state(changed), ValueError,
            )
            assert message == (
                "Private chair catalogue preview: "
                "component contains invalid or open solid material"
            )
        else:
            assert adapter._prototype_state(changed) != baseline, name
        rejected.append(name)
    assert adapter._prototype_state(Part.makeBox(2, 3, 4)) != baseline
    rejected.append("geometry-replacement")
    assert adapter._prototype_state(first) == baseline
    return {"meshing_stable": stable, "mutations_rejected": rejected}


def validate():
    """Keep raw receipts for the isolated native and real-GUI proof."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    path = Path(os.environ["TRACKTEMPLATE_CHAIR_CATALOGUE"]).resolve()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    run_dir = Path(os.environ.get(
        "TRACKTEMPLATE_CATALOGUE_P_RUN_DIR",
        ROOT / "benchmark-output/catalogue-p-placement" / stamp,
    )).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp)}
    initial = catalogue.helpers._document_state()
    try:
        prepared = prepare_catalogue_chair(path, "P", run="basic-04")
        receipt["prototype_controls"] = _prototype_controls(prepared)
        case = next(item for item in catalogue._cases(path)
                    if item[0] == "P")
        copies = run_dir / "native-copies"
        copies.mkdir()
        original = catalogue._reference(case, copies)
        assert tuple(name for name, *_rest in original
                     if name != "display_rail") == COMPONENT_NAMES
        reference = {name: shape for name, _label, shape, _matrix in original
                     if name != "display_rail"}
        assert any(any(abs(value) > 0.01 for value in shape.Placement.Base)
                   for name, shape in reference.items()
                   if name.startswith("SourceFixing"))
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        api, bootstrap = launcher["_load_foundation"](ROOT)
        session, routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, bootstrap,
        )
        assert launcher["FOUNDATION_RESULT"]["matched_profile_id"] == PROFILE
        receipt.update(profile=PROFILE, session_routing=routing)
        module = session.module
        source = helpers.continuity._prepare_case(module, run_dir, "turnout")
        foreign = App.newDocument("CataloguePUnrelatedWitness")
        foreign.addObject("Part::Feature", "Keep").Shape = Part.makeBox(2, 3, 4)
        foreign.recompute()
        combined._settle(foreign)
        App.setActiveDocument(source.Name)
        gui = Gui if App.GuiUp else None
        if gui:
            gui.getMainWindow().resize(1600, 1000)
            gui.Selection.addSelection(source.Objects[0])
        combined._settle(source)
        context = existing_binding._source_context(module, source, "TO-001", "P")
        frames = _expected_frames(module, context)
        old_partition = _legacy_partition(module, context)
        source_state = helpers._state(module, source)
        source_file_sha256 = catalogue._hash(source.FileName)
        foreign_state = combined._foreign_state(foreign)
        combined._settle(source)
        assert helpers._state(module, source) == source_state
        registry = dict(App.listDocuments())
        identities = {(d.Name, obj.Name): obj for d in registry.values()
                      for obj in d.Objects}
        shapes = {key: obj.Shape for key, obj in identities.items()
                  if "Shape" in obj.PropertiesList}
        selection = lifecycle._selection_snapshot(App, gui)
        preselection = lifecycle._preselection_snapshot(App, gui)
        receipt.update(source_before=source_state, foreign_before=foreign_state)

        def unchanged(stage, active):
            receipt["last_preservation_stage"] = stage
            assert helpers._state(module, source) == source_state, stage
            assert combined._foreign_state(foreign) == foreign_state, stage
            for name, document in registry.items():
                assert App.getDocument(name) is document, stage
            for (name, obj_name), obj in identities.items():
                assert App.getDocument(name).getObject(obj_name) is obj, stage
            for key, shape in shapes.items():
                assert identities[key].Shape.isSame(shape), stage
            assert lifecycle._selection_snapshot(App, gui) == selection, stage
            assert lifecycle._preselection_snapshot(App, gui) == preselection
            catalogue.helpers._active_document_state(active)

        command = session.preview_private_catalogue_p_chairs
        arguments = (source, "TO-001", path)
        started = time.perf_counter()
        with patch.object(App, "openDocument", side_effect=AssertionError(
            "Product restored an external source document",
        )):
            result = command(*arguments)
        receipt["elapsed_seconds"] = time.perf_counter() - started
        preview = App.getDocument(result["document_name"])
        receipt["preview"] = result
        receipt["comparisons"] = _assert_preview(
            result, preview, reference, frames, context,
        )
        assert App.listDocuments() == dict(registry, **{preview.Name: preview})
        unchanged("created", preview)
        receipt["mutation_controls"] = catalogue._mutation_controls(
            preview.Objects[2].Shape.childShapes()[0],
        )
        before_shapes = tuple(obj.Shape for obj in preview.Objects)
        assert preview.UndoCount == 1
        preview.undo()
        assert not preview.Objects
        preview.redo()
        _assert_preview(result, preview, reference, frames, context)
        assert all(catalogue_adapter._same_presented_shape(obj.Shape, shape)
                   for obj, shape in zip(preview.Objects, before_shapes))
        unchanged("Undo/Redo", preview)
        receipt["undo_redo"] = "PASS"
        if gui:
            for obj in preview.Objects:
                gui.Selection.clearSelection()
                gui.Selection.addSelection(obj)
                assert gui.Selection.getSelection() == [obj]
                obj.ViewObject.Visibility = False
                catalogue.helpers._settle()
                assert not obj.ViewObject.Visibility
                obj.ViewObject.Visibility = True
            gui.Selection.clearSelection()
            views = run_dir / "views"
            views.mkdir()
            receipt["images"] = helpers._images(preview, frames, views)
            lifecycle._restore_selection(App, gui, selection)
            lifecycle._restore_preselection(App, gui, preselection)
            unchanged("GUI inspection", preview)
        App.closeDocument(preview.Name)
        App.setActiveDocument(source.Name)
        lifecycle._restore_selection(App, gui, selection)
        lifecycle._restore_preselection(App, gui, preselection)
        catalogue.helpers._settle()
        unchanged("test-owned close", source)
        receipt["refusals"] = {}
        invalid = run_dir / "changed-catalogue.json"
        invalid.write_bytes(path.read_bytes() + b"\n")
        with patch.object(App, "newDocument", side_effect=AssertionError(
            "Invalid input created a document",
        )):
            receipt["refusals"]["changed-catalogue"] = catalogue._reject(
                lambda: command(source, "TO-001", invalid), ValueError,
            )
        unchanged("early refusal", source)
        original_top = module._chair_physical_top_z
        create = adapter.create_private_catalogue_p_preview

        def stale_during_build(*args):
            def changed_source():
                assert App.ActiveDocument not in (source, foreign)
                assert len(App.ActiveDocument.Objects) == 24
                with patch.object(
                    module, "_chair_physical_top_z",
                    side_effect=lambda *values: original_top(*values) + 1e-8,
                ):
                    args[-1]()
            return create(*args[:-1], changed_source)

        with patch.object(session, "_private_catalogue_p_preview_factory",
                          side_effect=stale_during_build):
            receipt["refusals"]["late-source-datum"] = helpers._reject(
                lambda: command(*arguments), "source changed",
            )
        assert App.listDocuments() == registry
        unchanged("late source rollback", source)
        original_shape_check = adapter._same_presented_shape

        def reject_stored_shape(actual, expected):
            if App.ActiveDocument not in registry.values():
                assert len(App.ActiveDocument.Objects) == 24
                return False
            return original_shape_check(actual, expected)

        with patch.object(adapter, "_same_presented_shape", reject_stored_shape):
            receipt["refusals"]["stored-shape"] = catalogue._reject(
                lambda: command(*arguments), ValueError,
            )
        assert App.listDocuments() == registry
        unchanged("stored shape rollback", source)
        changing = run_dir / "late-change-catalogue.json"
        changing.write_bytes(path.read_bytes())
        original_import = adapter._import_components

        def change_catalogue(preparation):
            shapes = original_import(preparation)
            changing.write_bytes(changing.read_bytes() + b"\n")
            return shapes

        with patch.object(adapter, "_import_components", change_catalogue):
            receipt["refusals"]["late-catalogue-change"] = catalogue._reject(
                lambda: command(source, "TO-001", changing), ValueError,
            )
        assert App.listDocuments() == registry
        unchanged("late catalogue rollback", source)
        for case_name in ("missing", "stale"):
            target = run_dir / (case_name + ".FCStd")
            shutil.copy2(source.FileName, target)
            negative = App.openDocument(str(target))
            if case_name == "missing":
                settings_object = module._chair_settings_object(
                    negative, "turnout", "TO-001",
                )
                setattr(settings_object, module.CHAIR_ANALYSIS_RESULT_PROPERTY,
                        "")
            else:
                module.invalidate_chair_analysis(
                    negative, "turnout", "TO-001", remove_display=True,
                )
            before = dict(App.listDocuments())
            receipt["refusals"][case_name] = catalogue._reject(
                lambda: command(negative, "TO-001", path), ValueError,
            )
            assert App.listDocuments() == before
            App.closeDocument(negative.Name)
        App.setActiveDocument(source.Name)
        lifecycle._restore_selection(App, gui, selection)
        lifecycle._restore_preselection(App, gui, preselection)
        catalogue.helpers._settle()
        unchanged("negative witness closure", source)
        verify_catalogue_sources(prepared)
        assert catalogue._hash(source.FileName) == source_file_sha256
        context_after = existing_binding._source_context(
            module, source, "TO-001", "P",
        )
        assert context_after == context
        assert _legacy_partition(module, context_after) == old_partition
        receipt.update(source_after=helpers._state(module, source),
                       foreign_after=combined._foreign_state(foreign),
                       source_bindings_unchanged=True,
                       source_file_sha256=source_file_sha256,
                       transaction_rollback="PASS",
                       legacy_exclusions_unchanged=True)
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
