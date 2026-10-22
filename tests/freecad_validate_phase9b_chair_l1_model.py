"""Validate derived L1 model solids without changing source or documents.

Explicit local inputs select the retained private reference. Otherwise the
test uses invented geometry. GUI objects are task-owned presentation only;
the result accepts no source-scale fidelity, fit, output or production use.
"""

import copy
import datetime
import hashlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
import sys
import traceback
from types import SimpleNamespace
from unittest.mock import patch

import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate import bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import chair_model_exact  # noqa: E402
from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
    chair_model_research,
)
from validate_phase9a_chair_l1 import (  # noqa: E402
    EXPECTED_TOPOLOGY,
    edge_count,
    load_package,
    synthetic_l1_package_records,
    validate_rejections,
)
from validate_phase9a_chair_model_scale import (  # noqa: E402
    LENGTH_FACTOR,
    REQUEST,
    VOLUME_FACTOR,
    assert_diagnostic,
    request_rejections,
)
from validate_phase9a_chair_seat import canonical_json  # noqa: E402


SENTINEL = "Phase 9B L1 model FreeCAD validation passed"
PROFILE_ID = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-"
    "qt6.11.2-coin4.0.10"
)
NUMERICAL_BUDGET_MM = 1.0e-7
PART_NAMES = ("body", "bevel-negative", "bevel-positive")


def _preview_helpers():
    """Load retained helpers under an alias that cannot enter the old proof."""
    spec = importlib.util.spec_from_file_location(
        "_l1_model_preview_helpers",
        ROOT / "tests/freecad_validate_phase9b_s1_reference_preview.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_preview = _preview_helpers()
_archive_state = _preview._archive_state
_images = _preview._images


def _inputs():
    package_path = os.environ.get("TRACKTEMPLATE_L1_MODEL_PACKAGE")
    manifest_path = os.environ.get("TRACKTEMPLATE_L1_MODEL_MANIFEST")
    if package_path or manifest_path:
        assert package_path and manifest_path
        paths = tuple(Path(p) for p in (package_path, manifest_path))
        content = tuple(p.read_bytes() for p in paths)
        record, manifest = (json.loads(data) for data in content)
        text = content[1].decode("utf-8")
        package = definitions.chair_definition_package_from_json(
            content[0].decode("utf-8"), text,
        )
        identities = {str(p): hashlib.sha256(data).hexdigest()
                      for p, data in zip(paths, content)}
        return record, manifest, package, text, identities
    record, manifest = synthetic_l1_package_records()
    package, text = load_package(record, manifest)
    return record, manifest, package, text, {}


def _settle():
    """Complete queued GUI work before an exact visible-state baseline."""
    if App.GuiUp:
        import FreeCADGui as Gui
        from PySide import QtWidgets

        for document in App.listDocuments().values():
            Gui.getDocument(document.Name).activeView().redraw()
        for _iteration in range(5):
            Gui.updateGui()
            QtWidgets.QApplication.processEvents()


def _document_state():
    """Retain complete native/view payloads, identities and registry state."""
    documents = []
    for name, document in sorted(App.listDocuments().items()):
        state = {
            "name": name, "label": document.Label,
            "filename": document.FileName,
            "undo": document.UndoCount, "redo": document.RedoCount,
            "objects": tuple((obj.Name, obj.TypeId, tuple(obj.State),
                              _archive_state(obj.dumpContent()))
                             for obj in document.Objects),
        }
        if App.GuiUp:
            import FreeCADGui as Gui

            gui = Gui.getDocument(name)
            state.update(
                gui_modified=gui.Modified,
                camera=gui.activeView().getCamera(),
                views=tuple((obj.Name, _archive_state(
                    obj.ViewObject.dumpContent(),
                )) for obj in document.Objects),
            )
        documents.append(state)
    result = {
        "active": App.ActiveDocument.Name if App.ActiveDocument else None,
        "documents": documents,
    }
    if App.GuiUp:
        import FreeCADGui as Gui

        result["active_documents"] = _active_document_state(App.ActiveDocument)
        result["selection"] = tuple(
            (item.DocumentName, item.ObjectName, tuple(item.SubElementNames))
            for item in Gui.Selection.getSelectionEx()
        )
    return result


def _active_document_state(expected):
    """Check native and Python GUI active-document references together."""
    assert App.ActiveDocument is expected
    state = {"app": expected.Name if expected is not None else None}
    if App.GuiUp:
        for name, document in (
            ("gui_method", Gui.activeDocument()),
            ("gui_attribute", Gui.ActiveDocument),
        ):
            if expected is None:
                assert document is None, (name, document)
                state[name] = None
            else:
                assert document is not None, name
                assert document.Document is expected, name
                state[name] = document.Document.Name
    return state


def _boundary(shape, projected, source, solid_count=1):
    """Measure native points against the exact full-size source projection."""
    assert shape.isValid() and not shape.isNull()
    assert len(shape.Solids) == len(shape.Shells) == solid_count
    assert all(solid.isClosed() for solid in shape.Solids)
    assert projected.faces == source.faces
    topology = (len(shape.Vertexes), len(shape.Edges), len(shape.Faces))
    assert topology == (
        len(source.vertices), edge_count(source), len(source.faces),
    )
    assert projected.vertices == tuple(
        (name, *(value * LENGTH_FACTOR for value in point))
        for name, *point in source.vertices
    )
    assert projected.bounds_mm == tuple(
        value * LENGTH_FACTOR for value in source.bounds_mm
    )
    assert projected.volume_mm3 == source.volume_mm3 * VOLUME_FACTOR
    assert projected.landmarks == tuple(
        (name, tuple(value * LENGTH_FACTOR for value in point))
        for name, point in source.landmarks
    )
    unmatched = [tuple(vertex.Point) for vertex in shape.Vertexes]
    residuals = {}
    for name, *point in source.vertices:
        expected = tuple(float(value * LENGTH_FACTOR) for value in point)
        nearest = min(unmatched, key=lambda p: math.dist(p, expected))
        residuals[name] = math.dist(nearest, expected)
        assert residuals[name] <= NUMERICAL_BUDGET_MM
        unmatched.remove(nearest)
    assert not unmatched
    box = shape.BoundBox
    bounds = (box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax)
    assert max(abs(observed - float(value * LENGTH_FACTOR))
               for observed, value in zip(bounds, source.bounds_mm)) <= (
        NUMERICAL_BUDGET_MM
    )
    expected_volume = float(source.volume_mm3 * VOLUME_FACTOR)
    volume_budget = max(
        shape.Area * NUMERICAL_BUDGET_MM, expected_volume * 1.0e-12,
    )
    assert abs(shape.Volume - expected_volume) <= volume_budget
    tolerance = shape.getTolerance(1)
    assert tolerance <= NUMERICAL_BUDGET_MM or math.isclose(
        tolerance, NUMERICAL_BUDGET_MM, rel_tol=1.0e-12, abs_tol=0.0,
    )
    return {
        "topology": topology, "vertex_count": len(residuals),
        "maximum_point_residual_mm": max(residuals.values()),
        "bounds_mm": bounds, "volume_mm3": shape.Volume,
        "expected_volume_mm3": expected_volume,
        "numerical_volume_budget_mm3": volume_budget,
    }


def _native_proof(model, receipt):
    """Keep five semantic components, including three named outer parts."""
    assert receipt["contract_id"] == (
        "tracktemplate.chair-l1-model-scale-exact-research.v1"
    )
    for name, expected in {
        "package_signature": model.package.content_signature,
        "manifest_signature": model.manifest_signature,
        "request_signature": model.request_signature,
        "length_basis": "model", "source_length_basis": "full-size",
        "length_unit": "mm", "scale_denominator": "76.2",
        "frame_id": REQUEST["source_frame_id"],
        "source_frame_id": REQUEST["source_frame_id"],
        "source_origin": REQUEST["origin_datum"],
        "placement": "same-chair-origin-and-axes-central-key",
        "project_status": "reference-only",
        "intended_uses": ["private-development"],
        "component_count": 5, "solid_count": 7, "valid": True,
        "fused": False, "document_mutation": False,
        "filesystem_mutation": False,
        "production_geometry_authorized": False,
        "manufacturing_compensation_applied": False,
        "numerical_length_budget_mm": NUMERICAL_BUDGET_MM,
    }.items():
        assert receipt[name] == expected, name
    shapes = chair_model_exact._construct_components(model, l1=True)
    assert len(shapes) == len(receipt["components"]) == 5
    compound = Part.makeCompound(shapes)
    assert compound.isValid() and len(compound.Solids) == 7
    children = compound.childShapes()
    assert len(children) == 5
    assert all(a.isSame(b) for a, b in zip(children, shapes))
    observed = []
    for shape, component, (full_role, _), full, item in zip(
        shapes, model.components, model.full_size_research.geometry.components,
        model.full_size_research.components, receipt["components"],
    ):
        role = component.role
        assert item["role"] == role == full_role
        assert item["component_id"] == component.component_id == (
            full.component_id
        )
        assert item["procedure_id"] == component.procedure_id == (
            full.procedure_id
        )
        count = 3 if role == "outer-jaw" else 1
        assert item["solid_count"] == item["shell_count"] == count
        proof = _boundary(shape, component.geometry, full.geometry, count)
        assert proof["topology"] == EXPECTED_TOPOLOGY[role]
        assert item["face_ids"] == tuple(n for n, _ in full.geometry.faces)
        assert item["volume_mm3"] == shape.Volume
        if role == "outer-jaw":
            assert tuple(n for n, _ in component.geometry.parts) == PART_NAMES
            assert tuple(n for n, _ in full.geometry.parts) == PART_NAMES
            assert tuple(p["piece_id"] for p in item["pieces"]) == PART_NAMES
            pieces = shape.childShapes()
            assert len(pieces) == 3
            proof["parts"] = [
                dict(name=name, **_boundary(child, projected, source))
                for child, (name, projected), (_, source) in zip(
                    pieces, component.geometry.parts, full.geometry.parts,
                )
            ]
            proof["contacts"] = []
            for bevel in pieces[1:]:
                common = pieces[0].common(bevel)
                distance = pieces[0].distToShape(bevel)[0]
                assert common.isValid() and common.Volume == 0
                assert not common.Solids and distance <= NUMERICAL_BUDGET_MM
                proof["contacts"].append({
                    "distance_mm": distance, "common_volume_mm3": 0,
                    "common_edge_count": len(common.Edges),
                })
        observed.append(dict(role=role, **proof))
    pairs = tuple(itertools.combinations(
        (component.component_id for component in model.components), 2,
    ))
    assert tuple(tuple(c["component_ids"]) for c in receipt["contacts"]) == (
        pairs
    )
    assert len(pairs) == 10
    for contact in receipt["contacts"]:
        assert math.isfinite(contact["distance_mm"])
        assert math.isfinite(contact["common_volume_mm3"])
        assert contact["distance_mm"] >= 0
        assert contact["common_volume_mm3"] >= 0
    assert receipt["landmarks_mm"] == {
        name: tuple(float(v * LENGTH_FACTOR) for v in point)
        for name, point in model.full_size_research.geometry.landmarks
    }
    return observed, shapes


def _failures(package, text, record, manifest):
    """Observe pre-construction rejection and unchanged failure state."""
    operation = chair_model_exact.validate_chair_l1_model_exact_geometry
    observed = {}

    def forbidden(*_args, **_kwargs):
        raise AssertionError("invalid input reached native construction")

    before = _document_state()
    with patch.object(chair_model_exact, "_construct_components", forbidden):
        for name, request, expected in request_rejections():
            retained = copy.deepcopy(request)
            try:
                operation(package, text, request)
            except definitions.ChairDefinitionError as error:
                assert_diagnostic(error, expected)
                observed[name] = error.code
            else:
                raise AssertionError(name + ": invalid request accepted")
            assert request == retained
        synthetic, related = synthetic_l1_package_records()
        observed.update(validate_rejections(
            synthetic, related, lambda p, t: operation(p, t, REQUEST),
        ))
        tampered = copy.deepcopy(record)
        tampered["definition"]["quantities"][0]["canonical_value"] = "999"
        try:
            definitions.chair_definition_package_from_json(
                canonical_json(tampered), text,
            )
        except definitions.ChairDefinitionError as error:
            assert_diagnostic(error, "content-signature-mismatch")
            observed["tampered-package"] = error.code
        else:
            raise AssertionError("unsigned package change accepted")
        altered = copy.deepcopy(manifest)
        altered["dependencies"][0]["name"] += " tampered"
        try:
            operation(package, canonical_json(altered), REQUEST)
        except definitions.ChairDefinitionError as error:
            assert_diagnostic(error, "dependency-manifest-mismatch")
            observed["tampered-manifest"] = error.code
        else:
            raise AssertionError("changed manifest accepted")
    assert _document_state() == before
    with patch.object(chair_model_exact, "_construct_components",
                      side_effect=ValueError("injected model failure")):
        try:
            operation(package, text, REQUEST)
        except chair_model_exact.ChairModelExactGeometryError as error:
            assert_diagnostic(error, "research-model-kernel-construction-failed")
            assert isinstance(error.__cause__, ValueError)
            observed["injected-construction-failure"] = error.code
        else:
            raise AssertionError("injected construction failure accepted")
    assert _document_state() == before
    return observed


def _presentation(model, shapes, run_dir, witness, active_states):
    """Present seven coloured solids in an owned, unsaved GUI document."""
    before = _document_state()
    document = App.newDocument("L1ModelPresentation")
    try:
        active_states.append(dict(
            stage="presentation-created", **_active_document_state(document),
        ))
        for component, shape in zip(model.components, shapes):
            if component.role == "outer-jaw":
                group = document.addObject("App::DocumentObjectGroup", "Outer")
                for index, ((name, _), child) in enumerate(zip(
                    component.geometry.parts, shape.childShapes(),
                )):
                    obj = document.addObject("Part::Feature", "OuterPart")
                    obj.Label = "outer-jaw: " + name
                    obj.Shape = child
                    obj.ViewObject.ShapeColor = (
                        (0.85, 0.55, 0.20), (0.85, 0.25, 0.30),
                        (0.70, 0.35, 0.85),
                    )[index]
                    group.addObject(obj)
            else:
                obj = document.addObject("Part::Feature", "Component")
                obj.Label = component.role
                obj.Shape = shape
                obj.ViewObject.ShapeColor = (0.55, 0.70, 0.80)
        document.recompute()
        assert len(document.Objects) == 8
        assert sum(len(obj.Shape.Solids) for obj in document.Objects
                   if "Shape" in obj.PropertiesList) == 7
        assert not document.FileName
        _settle()
        placement = SimpleNamespace(origin_mm=(0, 0, 0), position_id="L1")
        captures = _images(document, [placement], run_dir)
    finally:
        App.closeDocument(document.Name)
        active_states.append(dict(
            stage="presentation-closed", **_active_document_state(witness),
        ))
        App.setActiveDocument(witness.Name)
        _settle()
        active_states.append(dict(
            stage="witness-restored", **_active_document_state(witness),
        ))
    assert _document_state() == before
    return captures


def validate():
    """Run one bounded proof and preserve its raw result on either outcome."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    run_dir = Path(os.environ.get(
        "TRACKTEMPLATE_L1_MODEL_RUN_DIR",
        ROOT / "benchmark-output" / "l1-model" / stamp,
    )).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp)}
    initial = _document_state()
    receipt["active_documents"] = [dict(
        stage="initial", **_active_document_state(None),
    )]
    witness = None
    try:
        qualification = bootstrap.require_qualified_runtime(
            ROOT / "reference/contracts/phase1-compatibility.json",
        )
        receipt["profile"] = qualification["compatibility_evaluation"][
            "matched_profile_id"
        ]
        assert receipt["profile"] == PROFILE_ID
        record, manifest, package, text, identities = _inputs()
        retained = copy.deepcopy((record, manifest, REQUEST))
        encoded = definitions.chair_definition_package_to_json(package)
        model = chair_model_research.prepare_chair_l1_model_research(
            package, text, REQUEST,
        )
        source = copy.deepcopy(model.full_size_research)
        witness = App.newDocument("L1ModelWitness")
        receipt["active_documents"].append(dict(
            stage="witness-created", **_active_document_state(witness),
        ))
        marker = witness.addObject("Part::Feature", "ResearchWitness")
        marker.Shape = Part.makeBox(2, 3, 4)
        marker.addProperty("App::PropertyString", "Evidence")
        marker.Evidence = "L1 model success and failure preserve this state"
        witness.recompute()
        if App.GuiUp:
            import FreeCADGui as Gui

            Gui.getMainWindow().resize(1600, 1000)
        _settle()
        before = _document_state()
        reopened = definitions.chair_definition_package_from_json(encoded, text)
        operation = chair_model_exact.validate_chair_l1_model_exact_geometry
        with patch("builtins.open", side_effect=AssertionError("source access")):
            first = operation(reopened, text, REQUEST)
            repeated = operation(
                package, text, dict(reversed(tuple(REQUEST.items()))),
            )
        assert repeated == first
        assert _document_state() == before
        observations, shapes = _native_proof(model, first)
        receipt.update(native=first, independent_native_observations=observations)
        receipt["rejections"] = _failures(package, text, record, manifest)
        assert _document_state() == before
        if App.GuiUp:
            receipt["captures"] = _presentation(
                model, shapes, run_dir, witness, receipt["active_documents"],
            )
        assert model.full_size_research == source
        assert definitions.chair_definition_package_to_json(package) == encoded
        assert (record, manifest, REQUEST) == retained
        assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == value
                   for p, value in identities.items())
        assert _document_state() == before
        receipt.update(
            input_sha256=identities, source_unchanged=True,
            document_state_unchanged=True, deterministic_repeat=True,
            source_free_roundtrip=True, production_geometry_authorized=False,
            direct_four_mm_source_capture_claimed=False,
            historical_common_edge_limitation_preserved=True,
        )
    except BaseException:
        receipt.update(status="FAIL", traceback=traceback.format_exc())
        raise
    finally:
        if witness is not None and witness.Name in App.listDocuments():
            App.closeDocument(witness.Name)
        receipt["owned_documents_closed"] = not App.listDocuments()
        (run_dir / "result.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
        )
    try:
        receipt["active_documents"].append(dict(
            stage="witness-closed", **_active_document_state(None),
        ))
        assert _document_state() == initial
    except BaseException:
        receipt.update(status="FAIL", traceback=traceback.format_exc())
        (run_dir / "result.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
        )
        raise
    receipt["status"] = "PASS"
    (run_dir / "result.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
    )
    print(SENTINEL)


if __name__ in ("__main__", Path(__file__).stem):
    validate()
