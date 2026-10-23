"""Prove the private catalogue import and preview boundary in FreeCAD.

The explicit local catalogue supplies retained models, not constructors.
Native mode compares all 30 contexts with copied FCStd restoration. GUI
mode inspects complete P and the largest contextual model through the
same command. Source geometry and all previous documents remain unchanged.
"""

import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import runpy
import sys
import traceback
from unittest.mock import patch

import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.adapters.freecad import (  # noqa: E402
    chair_catalogue_preview as adapter,
    chair_reference_preview as lifecycle,
)
from tracktemplate.application import chair_catalogue  # noqa: E402


SENTINEL = "Phase 9B private chair catalogue FreeCAD validation passed"
PROFILE = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-"
    "qt6.11.2-coin4.0.10"
)
EPSILON_MM = 1.0e-7


def _helpers():
    """Reuse settled native/view snapshots without running an old proof."""
    spec = importlib.util.spec_from_file_location(
        "_catalogue_lifecycle_helpers",
        ROOT / "tests/freecad_validate_phase9b_chair_l1_model.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


helpers = _helpers()


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _cases(path):
    """Use every selected model and the separate retained C10 CC context."""
    index = json.loads(path.read_text())
    cases = [(entry["label"], entry["selected_model"])
             for entry in index["entries"]]
    cc = next(entry for entry in index["entries"] if entry["label"] == "CC")
    extra = next(item for item in cc["attempts"]
                 if item["run"] == "context-native-02")
    cases.append(("CC", extra))
    assert len(cases) == 30 and len({label for label, _item in cases}) == 29
    cases.sort(key=lambda item: (item[0] != "P", item[0], item[1]["run"]))
    return cases


def _reference(case, directory):
    """Restore only a verified disposable copy before protected state exists."""
    label, selected = case
    model = selected["model"]
    content = Path(model["path"]).read_bytes()
    assert hashlib.sha256(content).hexdigest() == model["sha256"]
    copied = directory / (label + "-" + selected["run"] + ".FCStd")
    with copied.open("xb") as stream:
        stream.write(content)
    before = dict(App.listDocuments())
    document = App.openDocument(str(copied))
    try:
        assert document is not None and document.Objects
        objects = tuple((obj.Name, obj.Label, Part.Shape(obj.Shape),
                         tuple(obj.Placement.toMatrix().A))
                        for obj in document.Objects)
        assert all(obj.TypeId == "Part::Feature" for obj in document.Objects)
    finally:
        App.closeDocument(document.Name)
    helpers._settle()
    assert App.listDocuments() == before
    assert copied.read_bytes() == content
    assert Path(model["path"]).read_bytes() == content
    return objects


def _compare(actual, expected):
    """Compare the new import with the independent copied native restore."""
    assert not actual.isNull() and actual.isValid()
    counts = lambda shape: tuple(len(getattr(shape, field)) for field in (
        "Solids", "Shells", "Faces", "Wires", "Edges", "Vertexes",
    ))
    assert counts(actual) == counts(expected)
    assert actual.ShapeType == expected.ShapeType
    assert actual.Orientation == expected.Orientation
    matrix_error = max(abs(a - b) for a, b in zip(
        actual.Placement.toMatrix().A, expected.Placement.toMatrix().A,
    ))
    assert matrix_error <= 1.0e-14
    observed = [tuple(v.Point) for v in actual.Vertexes]
    original = [tuple(v.Point) for v in expected.Vertexes]
    assert observed and len(observed) == len(original)
    residual = max(
        max(min(math.dist(p, q) for q in original) for p in observed),
        max(min(math.dist(p, q) for q in observed) for p in original),
    )
    assert residual <= EPSILON_MM
    for field in ("XMin", "YMin", "ZMin", "XMax", "YMax", "ZMax"):
        assert abs(getattr(actual.BoundBox, field)
                   - getattr(expected.BoundBox, field)) <= EPSILON_MM
    assert abs(actual.Volume - expected.Volume) <= max(
        expected.Area * EPSILON_MM, abs(expected.Volume) * 1.0e-12,
    )
    assert abs(actual.Area - expected.Area) <= max(
        expected.Length * EPSILON_MM, expected.Area * 1.0e-12,
    )
    assert tuple(face.Orientation for face in actual.Faces) == tuple(
        face.Orientation for face in expected.Faces
    )
    assert tuple(type(face.Surface).__name__ for face in actual.Faces) == tuple(
        type(face.Surface).__name__ for face in expected.Faces
    )
    return {"topology": counts(actual), "matrix_residual": matrix_error,
            "vertex_residual_mm": residual}


def _assert_preview(result, document, case, reference):
    label, selected = case
    assert result["contract_id"] == (
        "tracktemplate.private-chair-catalogue-preview.v1"
    )
    assert result["label"] == label and result["run"] == selected["run"]
    assert result["source_model_sha256"] == selected["model"]["sha256"]
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["geometry_rebuilt"] is False
    assert result["track_placements_added"] == 0
    assert result["component_count"] == result["layer_count"] == len(reference)
    assert result["scale_denominator"] == "76.2"
    assert result["length_unit"] == "mm" and result["length_basis"] == "model"
    assert result["placement"] == "unchanged-retained-model-coordinates"
    assert not document.FileName and not document.Temporary
    assert "catalogue inspection" in document.Label
    assert "central keys" not in document.Label
    assert tuple(obj.Name for obj in document.Objects) == tuple(
        name for name, _label, _shape, _placement in reference
    )
    measurements = []
    for obj, metadata, (name, source_label, shape, object_matrix) in zip(
        document.Objects, result["components"], reference,
    ):
        assert obj.TypeId == "Part::Feature"
        assert "GeneratedBy" not in obj.PropertiesList
        assert obj.Label.endswith(source_label)
        assert metadata["source_name"] == name
        assert metadata["source_label"] == source_label
        assert tuple(metadata["source_identity"]) == (
            selected["model"]["sha256"], name,
        )
        values = metadata["xml_placement"]
        xml_matrix = App.Placement(
            App.Vector(*values[:3]), App.Rotation(*values[3:]),
        ).toMatrix().A
        xml_error = max(abs(a - b) for a, b in zip(xml_matrix, object_matrix))
        assert xml_error <= 1.0e-14
        assert math.isfinite(metadata["xml_placement_matrix_residual"])
        measurements.append(dict(
            name=name, xml_object_placement_residual=xml_error,
            **_compare(obj.Shape, shape),
        ))
    assert result["solid_count"] == sum(len(shape.Solids)
                                        for _name, _label, shape, _placement
                                        in reference)
    return measurements


def _capture(document, directory):
    """Reuse the qualified settled-buffer capture method for fitted views."""
    from PySide6 import QtWidgets
    from PySide6.QtOpenGLWidgets import QOpenGLWidget

    directory.mkdir()
    view = Gui.getDocument(document.Name).activeView()
    window = Gui.getMainWindow()
    records = []
    for name, orientation in (("top.png", view.viewTop),
                              ("axonometric.png", view.viewAxonometric)):
        orientation()
        helpers._settle()
        view.fitAll()
        helpers._settle()
        helpers._active_document_state(document)
        area = window.findChild(QtWidgets.QMdiArea)
        subwindow = area.activeSubWindow()
        assert subwindow is not None and subwindow.isVisible()
        widgets = [widget for widget in subwindow.findChildren(QOpenGLWidget)
                   if widget.isVisible()]
        assert len(widgets) == 1
        widget = widgets[0]
        previous = widget.updateBehavior()
        camera = view.getCamera()
        try:
            widget.setUpdateBehavior(QOpenGLWidget.PartialUpdate)
            image = window.grab()
        finally:
            widget.setUpdateBehavior(previous)
        path = directory / name
        assert not image.isNull() and image.save(str(path))
        assert view.getCamera() == camera
        records.append({"file": str(path), "sha256": _hash(path),
                        "document": document.Name, "camera": camera,
                        "visible_objects": [obj.Name for obj in
                                            document.Objects
                                            if obj.ViewObject.Visibility]})
    return records


def _mutation_controls(shape):
    """Reject actual geometric changes despite shared native topology."""
    result = []
    for name in ("translation", "rotation", "small-translation",
                 "small-rotation", "orientation"):
        changed = Part.Shape(shape)
        assert adapter._same_presented_shape(changed, shape)
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
        assert not adapter._same_presented_shape(changed, shape), name
        result.append(name)
    assert not adapter._same_presented_shape(Part.makeBox(2, 3, 4), shape)
    return result + ["different-body"]


def _reject(operation, error_type):
    try:
        operation()
    except error_type as error:
        return str(error)
    raise AssertionError("Expected refusal did not occur")


def validate():
    """Retain complete success/failure evidence for this new import route."""
    assert not App.listDocuments(), "Use an isolated empty FreeCAD host"
    path = Path(os.environ["TRACKTEMPLATE_CHAIR_CATALOGUE"]).resolve()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    run_dir = Path(os.environ.get(
        "TRACKTEMPLATE_CHAIR_CATALOGUE_RUN_DIR",
        ROOT / "benchmark-output/private-chair-catalogue" / stamp,
    )).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    copies = run_dir / "native-copies"
    copies.mkdir()
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp), "cases": []}
    initial = helpers._document_state()
    try:
        cases = _cases(path)
        preparations = [chair_catalogue.prepare_catalogue_chair(
            path, label, run=selected["run"],
        ) for label, selected in cases]
        assert len(preparations) == 30
        receipt["routing"] = [{"label": item.label, "run": item.run,
                               "component_count": len(item.components)}
                              for item in preparations]
        chosen = list(range(30))
        if App.GuiUp:
            largest = max(range(1, 30),
                          key=lambda i: len(preparations[i].components))
            chosen = [0, largest]
        references = {i: _reference(cases[i], copies) for i in chosen}
        assert not App.listDocuments()
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        api, bootstrap = launcher["_load_foundation"](ROOT)
        session, routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, bootstrap,
        )
        assert launcher["FOUNDATION_RESULT"]["matched_profile_id"] == PROFILE
        receipt.update(profile=PROFILE, session_routing=routing)
        source = App.newDocument("CatalogueProtectedSource")
        source.addObject("Part::Feature", "Keep").Shape = Part.makeBox(2, 3, 4)
        foreign = App.newDocument("CatalogueUnrelatedDocument")
        foreign.addObject("Part::Feature", "Other").Shape = Part.makeBox(5, 6, 7)
        source.recompute()
        foreign.recompute()
        App.setActiveDocument(source.Name)
        gui = Gui if App.GuiUp else None
        if gui:
            gui.getMainWindow().resize(1600, 1000)
            gui.Selection.addSelection(source.Keep)
        helpers._settle()
        helpers._document_state()
        helpers._settle()
        baseline = helpers._document_state()
        assert helpers._document_state() == baseline
        registry = dict(App.listDocuments())
        identities = {(d.Name, o.Name): o for d in registry.values()
                      for o in d.Objects}
        shapes = {key: obj.Shape for key, obj in identities.items()}
        selection = lifecycle._selection_snapshot(App, gui)
        preselection = lifecycle._preselection_snapshot(App, gui)
        receipt["protected_before"] = baseline

        def unchanged(stage, active):
            current = helpers._document_state()
            protected = [d for d in current["documents"]
                         if d["name"] in registry]
            assert protected == baseline["documents"], stage
            for name, document in registry.items():
                assert App.getDocument(name) is document, stage
            for (name, obj_name), obj in identities.items():
                assert App.getDocument(name).getObject(obj_name) is obj
                assert adapter._same_presented_shape(obj.Shape,
                                                     shapes[name, obj_name])
            assert lifecycle._selection_snapshot(App, gui) == selection
            assert lifecycle._preselection_snapshot(App, gui) == preselection
            helpers._active_document_state(active)
            receipt["last_preservation_stage"] = stage

        command = session.preview_private_catalogue_chair
        for index in chosen:
            label, selected = cases[index]
            with patch.object(App, "openDocument", side_effect=AssertionError(
                "Product restored an external document",
            )):
                result = command(path, label, run=selected["run"])
            preview = App.getDocument(result["document_name"])
            assert App.listDocuments() == dict(registry, **{preview.Name: preview})
            checks = _assert_preview(result, preview, cases[index],
                                     references[index])
            unchanged("created " + label, preview)
            case_result = {"label": label, "run": selected["run"],
                           "receipt": result, "comparisons": checks}
            if index == 0:
                assert label == "P" and len(preview.Objects) == 23
                receipt["mutation_controls"] = _mutation_controls(
                    preview.Objects[0].Shape,
                )
                before_shapes = tuple(obj.Shape for obj in preview.Objects)
                assert preview.UndoCount == 1
                preview.undo()
                assert not preview.Objects
                preview.redo()
                _assert_preview(result, preview, cases[index], references[index])
                assert all(adapter._same_presented_shape(obj.Shape, shape)
                           for obj, shape in zip(preview.Objects, before_shapes))
                unchanged("P Undo/Redo", preview)
                receipt["undo_redo"] = "PASS"
            if gui:
                for obj in preview.Objects:
                    gui.Selection.clearSelection()
                    gui.Selection.addSelection(obj)
                    assert gui.Selection.getSelection() == [obj]
                    obj.ViewObject.Visibility = False
                    helpers._settle()
                    assert not obj.ViewObject.Visibility
                    obj.ViewObject.Visibility = True
                helpers._settle()
                gui.Selection.clearSelection()
                case_result["images"] = _capture(
                    preview, run_dir / (label + "-views"),
                )
                lifecycle._restore_selection(App, gui, selection)
                lifecycle._restore_preselection(App, gui, preselection)
                unchanged("inspected " + label, preview)
            App.closeDocument(preview.Name)
            App.setActiveDocument(source.Name)
            # Test-owned closure clears selection. Restore the fixture as in
            # the existing L1 and combined-preview lifecycle proofs.
            lifecycle._restore_selection(App, gui, selection)
            lifecycle._restore_preselection(App, gui, preselection)
            helpers._settle()
            assert App.listDocuments() == registry
            unchanged("closed " + label, source)
            receipt["cases"].append(case_result)
            print("CATALOGUE_PREVIEW_CASE_PASS", label, selected["run"],
                  len(checks), flush=True)

        invalid = run_dir / "changed-catalogue.json"
        invalid.write_bytes(path.read_bytes() + b"\n")
        receipt["refusals"] = {}
        with patch.object(App, "newDocument", side_effect=AssertionError(
            "Invalid input created a document",
        )):
            receipt["refusals"]["changed-catalogue"] = _reject(
                lambda: command(invalid, "P"), ValueError,
            )
            for label, run in (("M1", None), ("P", "basic-03"),
                               ("CC", "unbound-context")):
                receipt["refusals"][label + str(run)] = _reject(
                    lambda: command(path, label, run=run), ValueError,
                )
        unchanged("early refusals", source)
        with patch.object(adapter, "_same_presented_shape", return_value=False):
            receipt["refusals"]["stored-geometry"] = _reject(
                lambda: command(path, "P"), ValueError,
            )
        helpers._settle()
        assert App.listDocuments() == registry
        unchanged("stored-geometry rollback", source)
        changing = run_dir / "late-change-catalogue.json"
        changing.write_bytes(path.read_bytes())
        original_import = adapter._import_components

        def mutate_copy(prepared):
            result = original_import(prepared)
            changing.write_bytes(changing.read_bytes() + b"\n")
            return result

        with patch.object(adapter, "_import_components", mutate_copy):
            receipt["refusals"]["late-input-change"] = _reject(
                lambda: command(changing, "P"), ValueError,
            )
        helpers._settle()
        assert App.listDocuments() == registry
        unchanged("late-input rollback", source)
        for prepared in preparations:
            chair_catalogue.verify_catalogue_sources(prepared)
        receipt.update(source_bindings_unchanged=True,
                       protected_after=helpers._document_state(),
                       transaction_rollback="PASS", track_placements_added=0,
                       production_geometry_authorized=False)
    except BaseException:
        receipt.update(status="FAIL", traceback=traceback.format_exc())
        raise
    finally:
        for name in tuple(App.listDocuments()):
            App.closeDocument(name)
        helpers._settle()
        receipt["owned_documents_closed"] = not App.listDocuments()
        (run_dir / "result.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
        )
    assert helpers._document_state() == initial
    receipt["status"] = "PASS"
    (run_dir / "result.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
    )
    print(SENTINEL, flush=True)


if __name__ in ("__main__", Path(__file__).stem):
    validate()
