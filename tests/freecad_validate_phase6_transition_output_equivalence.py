#!/usr/bin/env python3
"""Prove bounded legacy equivalence through actual Part and DXF output.

Run in the qualified FreeCAD runtime. Optional GUI capture observes owned
DXF imports only; it does not introduce or qualify a product GUI command.
"""

import hashlib
import json
import math
import os
import pathlib
import sys
import tempfile
import uuid

import FreeCAD as App
import Part


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests import phase6_transition_output_equivalence as proof  # noqa: E402
from tools import validate_dependency_manifest  # noqa: E402
from tracktemplate import api, bootstrap  # noqa: E402
from tracktemplate.adapters.export import transition_dxf as exporter  # noqa: E402
from tracktemplate.adapters.freecad import transition_exact  # noqa: E402


def _application_snapshot():
    return (
        App.ActiveDocument,
        App.getActiveTransaction(),
        tuple(
            (
                name, document, str(document.Label), str(document.FileName),
                bool(document.Temporary), int(document.UndoCount),
                int(document.RedoCount),
                tuple(
                    (obj, str(obj.Name), str(obj.TypeId), tuple(
                        (prop, repr(getattr(obj, prop)))
                        for prop in obj.PropertiesList
                    ))
                    for obj in document.Objects
                ),
            )
            for name, document in sorted(App.listDocuments().items())
        ),
    )


def _new_editable_document(name, temporary=False):
    document = App.newDocument(name, name, temporary, temporary)
    document.UndoMode = 1
    document.openTransaction("Create owned equivalence baseline")
    obj = document.addObject("App::FeaturePython", "PreservedObject")
    obj.addProperty("App::PropertyString", "PreservedData")
    obj.PreservedData = "must remain unchanged"
    document.commitTransaction()
    document.recompute()
    return document


def _directory_snapshot(path):
    return tuple(sorted((item.name, item.read_bytes())
                        for item in path.iterdir()))


def _shape_coordinates(shape, point_count, tolerance_mm):
    """Observe ordered open linear topology without sorting its vertices."""
    assert not shape.isNull() and shape.isValid()
    assert len(shape.Edges) == max(0, point_count - 1)
    if point_count == 1:
        assert str(shape.ShapeType) == "Vertex"
        vertices = tuple(shape.Vertexes)
    else:
        wire = shape if str(shape.ShapeType) == "Wire" else Part.Wire(
            shape.Edges
        )
        assert wire.isValid() and not wire.isClosed()
        vertices = tuple(wire.OrderedVertexes)
        # A curved edge with the correct endpoints is not equivalent to
        # the signed centreline polyline.
        for edge in shape.Edges:
            assert isinstance(edge.Curve, Part.Line), "non-linear edge"
            assert len(edge.Vertexes) == 2
            first, last = (vertex.Point for vertex in edge.Vertexes)
            assert math.isclose(
                float(edge.Length), (last - first).Length,
                rel_tol=0.0, abs_tol=tolerance_mm,
            )
    assert len(vertices) == point_count
    assert len(shape.Vertexes) == point_count
    return tuple(
        (float(vertex.Point.x), float(vertex.Point.y), float(vertex.Point.z))
        for vertex in vertices
    )


def _observe_exact_geometry(artifact):
    result = api.transition_exact_result_from_artifact(artifact)
    baseline = _application_snapshot()
    names = set(App.listDocuments())
    observations = []

    def observe():
        for name, document in App.listDocuments().items():
            if name in names:
                continue
            for obj in document.Objects:
                if "Shape" in obj.PropertiesList and not obj.Shape.isNull():
                    observations.append(_shape_coordinates(
                        obj.Shape, len(result.centreline.points),
                        proof.NUMERICAL_TOLERANCE_MM,
                    ))
        return False

    receipt = transition_exact.build_transition_exact_geometry(
        artifact, cancellation_requested=observe,
    )
    assert observations, "The proof did not observe actual exact geometry"
    assert all(item == observations[0] for item in observations)
    assert receipt.domain_id == result.centreline.domain_id
    assert receipt.exact_artifact_signature == result.artifact_signature
    assert _application_snapshot() == baseline
    return observations[0]


def _validate_curve_rejection():
    """Reject an arc that passes endpoint and chord-length observations."""
    edge = Part.Arc(
        App.Vector(0.0, 0.0, 0.0), App.Vector(7.5, 0.0001, 0.0),
        App.Vector(15.0, 0.0, 0.0),
    ).toShape()
    assert abs(edge.Length - 15.0) < proof.NUMERICAL_TOLERANCE_MM
    try:
        _shape_coordinates(Part.Wire([edge]), 2,
                           proof.NUMERICAL_TOLERANCE_MM)
    except AssertionError as error:
        assert "linear" in str(error)
    else:
        raise AssertionError("The proof accepted a shallow curved edge")


def _dxf_coordinates(path, point_count):
    """Read the published entity independently of the exporter's parser."""
    lines = path.read_text(encoding="ascii").splitlines()
    assert len(lines) % 2 == 0
    pairs = tuple(
        (int(code), value.strip())
        for code, value in zip(lines[::2], lines[1::2])
    )
    assert pairs[-1] == (0, "EOF")
    for name, value in (("$INSUNITS", "4"), ("$MEASUREMENT", "1")):
        index = pairs.index((9, name))
        assert pairs[index + 1] == (70, value)
    start = pairs.index((2, "ENTITIES")) + 1
    end = pairs.index((0, "ENDSEC"), start)
    entity = pairs[start:end]
    entity_type = "POINT" if point_count == 1 else "LWPOLYLINE"
    assert entity[0] == (0, entity_type)
    assert sum(code == 0 for code, _value in entity) == 1
    assert [value for code, value in entity if code == 8] == [
        "TRACKTEMPLATE_TRANSITION_CENTRELINE"
    ]
    if point_count == 1:
        return (tuple(
            float(next(value for item, value in entity if item == code))
            for code in (10, 20, 30)
        ),)
    assert (90, str(point_count)) in entity and (70, "0") in entity
    assert [float(v) for c, v in entity if c == 38] == [0.0]
    assert not any(code in (40, 41, 42, 43, 210, 220, 230)
                   for code, _value in entity)
    coordinates = []
    for index, (code, value) in enumerate(entity):
        if code == 10:
            assert entity[index + 1][0] == 20
            coordinates.append((float(value), float(entity[index + 1][1]),
                                0.0))
    assert len(coordinates) == point_count
    return tuple(coordinates)


def _capture_import(document, case_id, directory):
    import FreeCADGui as Gui
    from PySide6 import QtGui, QtWidgets

    assert Gui.getMainWindow().isVisible()
    assert Gui.ActiveDocument is not None
    App.setActiveDocument(document.Name)
    for obj in document.Objects:
        if "Shape" in obj.PropertiesList:
            obj.ViewObject.Visibility = True
    view = Gui.activeDocument().activeView()
    view.viewTop()
    view.fitAll()
    view.redraw()
    for _iteration in range(5):
        Gui.updateGui()
        QtWidgets.QApplication.processEvents()
    path = pathlib.Path(directory) / (case_id + ".png")
    view.saveImage(str(path), 1600, 1000, "Current")
    assert path.is_file() and path.stat().st_size > 0
    picture = QtGui.QImage(str(path))
    assert not picture.isNull()
    return str(path)


def _import_coordinates(path, point_count, capture_directory, case_id):
    import importDXF

    baseline = _application_snapshot()
    active = App.ActiveDocument
    assert App.getActiveTransaction() is None
    name = "Phase6EquivalenceImport_" + uuid.uuid4().hex
    assert name not in App.listDocuments()
    document = None
    try:
        document = App.newDocument(name)
        importDXF.insert(str(path), name)
        document.recompute()
        # The native GUI importer can leave its application transaction
        # active after committing the document. Close only this newly
        # created import group, before restoring the previous document.
        transaction = App.getActiveTransaction()
        if transaction is not None:
            assert transaction[0] == "DXF Post-processing"
            assert App.ActiveDocument is document
            App.closeActiveTransaction(False, transaction[1])
        assert App.getActiveTransaction() is None
        objects = tuple(
            obj for obj in document.Objects
            if "Shape" in obj.PropertiesList and not obj.Shape.isNull()
        )
        assert len(objects) == 1, "Expected one imported centreline entity"
        coordinates = _shape_coordinates(
            objects[0].Shape, point_count,
            proof.IMPORT_TRANSPORT_TOLERANCE_MM,
        )
        capture = None
        if capture_directory is not None and case_id in (
            "recorded-outside-entry", "recorded-inside-exit",
        ):
            capture = _capture_import(document, case_id, capture_directory)
    finally:
        if document is not None and App.listDocuments().get(name) is document:
            App.closeDocument(name)
        if active is not None:
            App.setActiveDocument(active.Name)
        else:
            App.setActiveDocument("")
    assert _application_snapshot() == baseline
    return coordinates, capture


def _validate_case(case, oracles, output, capture_directory):
    state, specification, artifact = proof.exact_fixture(case, oracles)
    result = api.transition_exact_result_from_artifact(artifact)
    point_count = len(result.centreline.points)
    reports = {}
    coordinates = _observe_exact_geometry(artifact)
    reports["part"] = proof.compare_output_coordinates(
        case, state, result, coordinates, oracles=oracles,
        transport_tolerance_mm=proof.NUMERICAL_TOLERANCE_MM,
    )
    baseline = _application_snapshot()
    request = api.TransitionDxfExportRequest(
        str(output), api.DEVELOPMENT_CHECKPOINT,
    )
    receipt = exporter.export_transition_dxf(
        state, artifact, specification, request,
    )
    assert receipt.disposition == "created"
    assert receipt.project_status == "unknown"
    assert _application_snapshot() == baseline
    dxf_path = output / receipt.dxf_filename
    manifest_path = output / receipt.manifest_filename
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert validate_dependency_manifest.validate_document(manifest) == []
    assert manifest["project_status"]["status"] == "unknown"
    assert manifest["intended_uses"] == ["private-development"]
    assert manifest["subject"]["artifacts"] == [{
        "path": receipt.dxf_filename,
        "format": "DXF",
        "sha256": hashlib.sha256(dxf_path.read_bytes()).hexdigest(),
    }]
    reports["dxf"] = proof.compare_output_coordinates(
        case, state, result, _dxf_coordinates(dxf_path, point_count),
        oracles=oracles, transport_tolerance_mm=proof.NUMERICAL_TOLERANCE_MM,
    )
    imported, capture = _import_coordinates(
        dxf_path, point_count, capture_directory, case.case_id,
    )
    reports["import"] = proof.compare_output_coordinates(
        case, state, result, imported, oracles=oracles,
        transport_tolerance_mm=proof.IMPORT_TRANSPORT_TOLERANCE_MM,
    )
    before = _directory_snapshot(output)
    reused = exporter.export_transition_dxf(
        state, artifact, specification, request,
    )
    assert reused.disposition == "reused"
    assert _directory_snapshot(output) == before
    assert _application_snapshot() == baseline
    reports["capture"] = capture
    return reports


def validate(capture_directory=None):
    """Validate eight owned examples and restore all pre-existing documents."""
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference" / "contracts" / "phase1-compatibility.json"
    )
    _validate_curve_rejection()
    assert App.getActiveTransaction() is None
    oracles = proof.load_legacy_oracles(ROOT)
    baseline = _application_snapshot()
    original_active = App.ActiveDocument
    owned = []
    reports = {}
    try:
        editable = _new_editable_document("Phase6EquivalenceEditable")
        owned.append(editable)
        owned.append(_new_editable_document(
            transition_exact.TRANSITION_EXACT_GEOMETRY_DOCUMENT_NAME, True,
        ))
        App.setActiveDocument(editable.Name)
        with tempfile.TemporaryDirectory(prefix="tt-exit1-equivalence-") as raw:
            directory = pathlib.Path(raw)
            for case in proof.equivalence_cases():
                output = directory / case.case_id
                output.mkdir()
                reports[case.case_id] = _validate_case(
                    case, oracles, output, capture_directory,
                )
    finally:
        for document in reversed(owned):
            if App.listDocuments().get(document.Name) is document:
                App.closeDocument(document.Name)
        if original_active is not None:
            App.setActiveDocument(original_active.Name)
        else:
            App.setActiveDocument("")
    assert _application_snapshot() == baseline
    print(json.dumps({
        "cases": reports,
        "source_hashes": proof.SOURCE_HASHES,
        "profile": qualification["compatibility_evaluation"][
            "matched_profile_id"
        ],
    }, sort_keys=True))
    print("Phase 6 transition output equivalence FreeCAD validation passed")


validate(os.environ.get("TRACKTEMPLATE_EQUIVALENCE_CAPTURE_DIRECTORY"))
