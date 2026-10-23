"""Prove the finite P slide-seat with qualified native and GUI evidence.

Optional private inputs supply an independently retained source comparison.
The product reconstructs its parameters without reading that source. A GUI
witness is disposable, full-size and explicitly reference-only.
"""

from collections import Counter
import copy
import datetime
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import traceback
from unittest.mock import patch

import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate import bootstrap  # noqa: E402
from tracktemplate.adapters.freecad import chair_p_seat_exact  # noqa: E402
from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
)
from tracktemplate.application.chair_research import (  # noqa: E402
    prepare_chair_p_seat_research,
)
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
)
from validate_phase9b_chair_p_seat import (  # noqa: E402
    load_package,
    synthetic_p_seat_package_records,
)


SENTINEL = "Phase 9B P slide-seat FreeCAD validation passed"
PROFILE_ID = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-"
    "qt6.11.2-coin4.0.10"
)
EPSILON_MM = 1.0e-7


def _lifecycle_helpers():
    """Reuse state/settling controls without entering an old proof."""
    spec = importlib.util.spec_from_file_location(
        "_p_seat_lifecycle_helpers",
        ROOT / "tests/freecad_validate_phase9b_chair_l1_model.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_lifecycle = _lifecycle_helpers()
_state = _lifecycle._document_state
_settle = _lifecycle._settle
_active = _lifecycle._active_document_state


def _inputs():
    package_path = os.environ.get("TRACKTEMPLATE_P_SEAT_PACKAGE")
    manifest_path = os.environ.get("TRACKTEMPLATE_P_SEAT_MANIFEST")
    if package_path or manifest_path:
        assert package_path and manifest_path
        paths = tuple(Path(p).resolve() for p in (package_path, manifest_path))
        content = tuple(path.read_bytes() for path in paths)
        record, manifest = (json.loads(data) for data in content)
        text = content[1].decode("utf-8")
        package = definitions.chair_definition_package_from_json(
            content[0].decode("utf-8"), text,
        )
        identities = {str(path): hashlib.sha256(data).hexdigest()
                      for path, data in zip(paths, content)}
        return record, manifest, package, text, identities
    record, manifest = synthetic_p_seat_package_records()
    package, text = load_package(record, manifest)
    return record, manifest, package, text, {}


def _partition_edges(group):
    """Split raw edges at exact retained vertices before cancellation.

    Source cap fans meet a whole trunk edge at their central vertex.
    Fractions preserve each supplied coordinate exactly. No point moves,
    no tolerance snaps a nearby point onto an edge, and no face is removed.
    """
    points = {point for _index, polygon, _area in group for point in polygon}
    exact = {
        point: tuple(Fraction(value) for value in point) for point in points
    }
    edges = Counter()
    for _index, polygon, _area in group:
        for start, end in zip(polygon, polygon[1:] + polygon[:1]):
            a, b = exact[start], exact[end]
            direction = tuple(y - x for x, y in zip(a, b))
            length_squared = sum(value * value for value in direction)
            assert length_squared > 0
            cuts = [(Fraction(0), start), (Fraction(1), end)]
            for point in points - {start, end}:
                delta = tuple(y - x for x, y in zip(a, exact[point]))
                cross = (
                    direction[1] * delta[2] - direction[2] * delta[1],
                    direction[2] * delta[0] - direction[0] * delta[2],
                    direction[0] * delta[1] - direction[1] * delta[0],
                )
                along = sum(x * y for x, y in zip(direction, delta))
                if not any(cross) and 0 < along < length_squared:
                    cuts.append((along / length_squared, point))
            cuts.sort()
            edges.update(frozenset((a[1], b[1])) for a, b in
                         zip(cuts, cuts[1:]))
    return edges


def _check_source_coverage(research, shape, source):
    """Cover every source point, plane, area and complete outer edge."""
    assert source["status"] == "PASS" and source["units"] == "mm"
    assert source["coordinate_origin"] == "rail top / gauge face"
    assert source["face_count"] == len(source["faces"]) == 85, (
        "source face count"
    )
    scale = 304.8 / source["scale_mm_per_foot"]
    assert math.isfinite(scale) and scale > 0
    p = research.geometry.parameters
    for name in ("rail_head_width_mm", "rail_foot_width_mm", "rail_depth_mm"):
        assert abs(source["parameters"]["rail"][name] * scale
                   - float(getattr(p, name))) <= EPSILON_MM
    for name, source_name in (("seat_thickness_mm", "seat_thickness"),
                              ("edge_thickness_mm", "chair_edge_thick")):
        assert abs(source["parameters"]["3d"][source_name] * 25.4
                   - float(getattr(p, name))) <= EPSILON_MM
    head = float(p.rail_head_width_mm)
    height = float(p.rail_depth_mm + p.seat_thickness_mm)
    groups = [[] for _face in shape.Faces]
    seen = set()
    for index, face in enumerate(source["faces"]):
        assert face["block"] == "PSEAT"
        points = []
        for x, y, z in face["vertices"]:
            point = (-x * scale, -y * scale - head / 2, z * scale + height)
            assert all(math.isfinite(v) for v in point)
            if not points or point != points[-1]:
                points.append(point)
        if points[0] == points[-1]:
            points.pop()
        assert len(points) in (3, 4) and len(set(points)) == len(points)
        identity = frozenset(points)
        assert identity not in seen, "duplicated source face"
        seen.add(identity)
        vectors = [App.Vector(*point) for point in points]
        mids = [(first + second) / 2
                for first, second in zip(vectors, vectors[1:] + vectors[:1])]
        centre = sum(vectors, App.Vector(0, 0, 0)) / len(vectors)
        matches = [i for i, native in enumerate(shape.Faces) if all(
            native.isInside(point, EPSILON_MM, True)
            for point in vectors + mids + [centre]
        )]
        assert len(matches) == 1, (index, matches)
        normal = App.Vector(0, 0, 0)
        for first, second in zip(vectors, vectors[1:] + vectors[:1]):
            normal += first.cross(second)
        area = normal.Length / 2
        assert area > 0
        normal.normalize()
        native = shape.Faces[matches[0]]
        assert abs(abs(normal.dot(native.normalAt(0, 0))) - 1) < 1e-12
        assert max(abs((point - vectors[0]).dot(normal))
                   for point in vectors) <= EPSILON_MM
        groups[matches[0]].append((index, points, area))
    coverage = []
    for native, group in zip(shape.Faces, groups):
        assert group, "native face has no source coverage"
        edges = _partition_edges(group)
        assert set(edges.values()) <= {1, 2}, "source edge multiplicity"
        boundary = [tuple(edge) for edge, count in edges.items() if count == 1]
        assert len(boundary) == len(native.Edges)
        for edge in native.Edges:
            actual = [tuple(vertex.Point) for vertex in edge.Vertexes]
            assert len(actual) == 2
            matches = [pair for pair in boundary if all(
                any(math.dist(point, candidate) <= EPSILON_MM
                    for candidate in pair) for point in actual
            )]
            assert len(matches) == 1
            boundary.remove(matches[0])
        assert not boundary
        area = sum(item[2] for item in group)
        budget = max(native.Length * EPSILON_MM, native.Area * 1e-12)
        assert abs(area - native.Area) <= budget
        coverage.append({
            "source_faces": [item[0] for item in group],
            "area_mm2": area, "native_area_mm2": native.Area,
            "area_residual_mm2": abs(area - native.Area),
            "boundary_edge_count": len(native.Edges),
        })
    assert sum(len(group) for group in groups) == 85
    return {
        "source_face_count": 85, "native_face_count": 33,
        "scale_denominator": scale, "faces": coverage,
        "complete_point_plane_area_boundary_coverage": True,
    }


def _source_coverage(research, shape, identities):
    """Compare retained bytes and reject three detached source mutations."""
    source_path = os.environ.get("TRACKTEMPLATE_P_SEAT_SOURCE_FACES")
    if not source_path:
        return None
    path = Path(source_path).resolve()
    content = path.read_bytes()
    identities[str(path)] = hashlib.sha256(content).hexdigest()
    source = json.loads(content)
    result = _check_source_coverage(research, shape, source)
    rejections = {}
    for name, expected in (
        ("missing-face", "source face count"),
        ("duplicate-face", "duplicated source face"),
        ("shifted-vertex", "source edge multiplicity"),
    ):
        changed = copy.deepcopy(source)
        if name == "missing-face":
            del changed["faces"][35]
            changed["face_count"] = len(changed["faces"])
        elif name == "duplicate-face":
            changed["faces"][35] = copy.deepcopy(changed["faces"][36])
        else:
            # Keep the repeated triangle endpoint and planar face intact;
            # only the source fan centre moves within the native cap.
            for index in (2, 3):
                changed["faces"][35]["vertices"][index][0] += 0.001
        try:
            _check_source_coverage(research, shape, changed)
        except AssertionError as error:
            assert str(error) == expected, (name, str(error))
            rejections[name] = str(error)
        else:
            raise AssertionError(name + ": source mutation accepted")
    assert json.loads(content) == source
    result["source_mutations_rejected"] = rejections
    return result


def _failures(package, text, record, manifest):
    """Reject bad requests before native work and retain failure state."""
    operation = chair_p_seat_exact.validate_chair_p_seat_exact_geometry
    observed = {}
    before = _state()

    def forbidden(_geometry):
        raise AssertionError("invalid research request reached native work")

    with patch.object(chair_p_seat_exact, "_make_shape", forbidden):
        mutations = (
            ("schema", lambda r: r.update(schema_version=999)),
            ("frame", lambda r: r["definition"]["frame"].update(
                handedness="left",
            )),
            ("lineage", lambda r: r["lineage"][0].update(
                evidence_state="unresolved",
            )),
            ("rule", lambda r: r["definition"]["procedures"][1].update(
                rule_id="unsupported-p-seat-rule",
            )),
        )
        for name, mutate in mutations:
            changed, related = copy.deepcopy((record, manifest))
            mutate(changed)
            resign_package(changed, related)
            try:
                candidate, candidate_text = load_package(changed, related)
                operation(candidate, candidate_text)
            except definitions.ChairDefinitionError as error:
                observed[name] = error.code
            else:
                raise AssertionError(name + ": invalid request accepted")
        tampered = copy.deepcopy(manifest)
        tampered["dependencies"][0]["name"] += " changed"
        try:
            operation(package, canonical_json(tampered))
        except definitions.ChairDefinitionError as error:
            assert error.code == "dependency-manifest-mismatch"
            observed["manifest"] = error.code
        else:
            raise AssertionError("changed manifest accepted")
    assert _state() == before
    injections = (
        ("kernel", Part.OCCError("injected P seat failure"),
         "p-seat-kernel-construction-failed"),
        ("null", Part.Shape(), "invalid-p-seat-solid"),
        ("wrong-solid", Part.makeBox(2, 3, 4), "unexpected-p-seat-topology"),
    )
    for name, injected, code in injections:
        arguments = (
            {"side_effect": injected} if isinstance(injected, Exception)
            else {"return_value": injected}
        )
        with patch.object(chair_p_seat_exact, "_make_shape", **arguments):
            try:
                operation(package, text)
            except chair_p_seat_exact.ChairPSeatExactGeometryError as error:
                assert error.code == code, (name, error.code)
                assert error.diagnostic()["document_mutation"] is False
                assert error.diagnostic()["filesystem_mutation"] is False
                observed[name] = error.code
            else:
                raise AssertionError(name + ": native failure accepted")
        assert _state() == before
    return observed


def _same_presented_shape(actual, expected):
    """Keep native topology, exact placement and orientation unchanged.

    Recompute can replace a TopLoc location with an equivalent transform.
    Compare that transform rather than its transient datum identity.
    """
    return (
        actual.isPartner(expected)
        and actual.Placement.toMatrix().A == expected.Placement.toMatrix().A
        and actual.Orientation == expected.Orientation
    )


def _presentation_rejections(shape):
    """Reject genuine changes even when the native topology is shared."""
    observed = []
    for name in ("translation", "rotation", "orientation"):
        changed = Part.Shape(shape)
        assert _same_presented_shape(changed, shape)
        if name == "translation":
            changed.translate(App.Vector(1, 0, 0))
        elif name == "rotation":
            changed.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 90)
        else:
            changed.reverse()
            assert changed.isSame(shape)
        assert changed.isPartner(shape)
        assert not _same_presented_shape(changed, shape), name
        observed.append(name)
    assert not _same_presented_shape(Part.makeBox(2, 3, 4), shape)
    observed.append("different-body")
    return observed


def _presentation(shape, run_dir, witness):
    """Capture a full-size seat in an owned unsaved presentation document."""
    from PySide6 import QtWidgets
    from PySide6.QtOpenGLWidgets import QOpenGLWidget

    before = _state()
    document = App.newDocument("PSlideSeatPresentation")
    captures = []
    try:
        _active(document)
        document.Label = "P slide-seat — reference-only, full-size mm"
        obj = document.addObject("Part::Feature", "SlideSeat")
        obj.Label = "P slide-seat; no placement or production acceptance"
        obj.Shape = shape
        obj.ViewObject.ShapeColor = (0.70, 0.58, 0.35)
        obj.ViewObject.LineColor = (0.15, 0.13, 0.10)
        obj.ViewObject.DisplayMode = "Flat Lines"
        document.recompute()
        assert not document.FileName and len(document.Objects) == 1
        assert _same_presented_shape(obj.Shape, shape)
        window = Gui.getMainWindow()
        view = Gui.getDocument(document.Name).activeView()
        for name, orientation in (("top.png", view.viewTop),
                                  ("axonometric.png", view.viewAxonometric)):
            orientation()
            _settle()
            view.fitAll()
            _settle()
            _active(document)
            area = window.findChild(QtWidgets.QMdiArea)
            subwindow = area.activeSubWindow()
            assert subwindow is not None and subwindow.isVisible()
            widgets = [
                widget for widget in subwindow.findChildren(QOpenGLWidget)
                if widget.isVisible()
            ]
            assert len(widgets) == 1
            widget = widgets[0]
            behaviour = widget.updateBehavior()
            camera = view.getCamera()
            try:
                widget.setUpdateBehavior(QOpenGLWidget.PartialUpdate)
                image = window.grab()
            finally:
                widget.setUpdateBehavior(behaviour)
            assert not image.isNull() and image.save(str(run_dir / name))
            assert view.getCamera() == camera
            assert widget.updateBehavior() == behaviour
            _active(document)
            captures.append({
                "file": name, "camera": camera,
                "document": document.Name, "full_size_mm": True,
                "unsaved": not document.FileName,
            })
        assert captures[0]["camera"] != captures[1]["camera"]
    finally:
        App.closeDocument(document.Name)
        App.setActiveDocument(witness.Name)
        _settle()
        _active(witness)
    assert _state() == before
    (run_dir / "capture-state.json").write_text(
        json.dumps(captures, indent=2) + "\n", encoding="utf-8",
    )
    return captures


def validate():
    """Run one bounded proof; preserve failures and close only owned data."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    run_dir = Path(os.environ.get(
        "TRACKTEMPLATE_P_SEAT_OUTPUT_DIR",
        ROOT / "benchmark-output" / "p-slide-seat" / stamp,
    )).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp)}
    initial = _state()
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
        retained = copy.deepcopy((record, manifest))
        encoded = definitions.chair_definition_package_to_json(package)
        research = prepare_chair_p_seat_research(package, text)
        original = copy.deepcopy(research)
        witness = App.newDocument("PSlideSeatWitness")
        marker = witness.addObject("Part::Feature", "ResearchWitness")
        marker.Shape = Part.makeBox(2, 3, 4)
        marker.addProperty("App::PropertyString", "Evidence")
        marker.Evidence = "P slide-seat success and failure preserve state"
        witness.recompute()
        if App.GuiUp:
            Gui.getMainWindow().resize(1600, 1000)
        _settle()
        _active(witness)
        before = _state()
        reopened = definitions.chair_definition_package_from_json(
            encoded, text,
        )
        operation = chair_p_seat_exact.validate_chair_p_seat_exact_geometry
        forbidden_source = AssertionError("source access")
        with patch("builtins.open", side_effect=forbidden_source):
            first = operation(reopened, text)
            second = operation(package, text)
        assert first == second
        assert first["solid_count"] == first["shell_count"] == 1
        assert tuple(first[name] for name in (
            "vertex_count", "edge_count", "face_count",
        )) == (
            62, 93, 33,
        )
        assert first["valid"] and first["closed"]
        assert first["project_status"] == "reference-only"
        assert first["intended_uses"] == ["private-development"]
        assert first["production_geometry_authorized"] is False
        assert first["length_unit"] == "mm"
        assert first["length_basis"] == "full-size"
        assert first["component_id"] == research.component_id
        assert first["procedure_id"] == research.procedure_id
        assert first["package_signature"] == package.content_signature
        assert first["manifest_signature"] == research.manifest_signature
        assert _state() == before
        if identities:
            synthetic_record, synthetic_manifest = (
                synthetic_p_seat_package_records()
            )
            synthetic_package, synthetic_text = load_package(
                synthetic_record, synthetic_manifest,
            )
            synthetic = operation(synthetic_package, synthetic_text)
        else:
            synthetic = first
        assert synthetic["bounds_mm"] == (-8.0, -17.0, 1.0, 8.0, 3.0, 5.0)
        # Independent strip/trapezoid/rectangle and 24-triangle fan sum.
        expected_volume = 688 + 432 * math.sin(math.pi / 24)
        assert abs(synthetic["volume_mm3"] - expected_volume) <= EPSILON_MM
        assert _state() == before
        receipt["synthetic_native"] = synthetic
        shape = chair_p_seat_exact.construct_chair_p_seat_shape(
            research.geometry,
        )
        receipt["native"] = first
        receipt["source_coverage"] = _source_coverage(
            research, shape, identities,
        )
        receipt["rejections"] = _failures(package, text, record, manifest)
        assert _state() == before
        if App.GuiUp:
            receipt["presentation_mutations_rejected"] = (
                _presentation_rejections(shape)
            )
            receipt["captures"] = _presentation(shape, run_dir, witness)
        assert research == original
        assert definitions.chair_definition_package_to_json(package) == encoded
        assert (record, manifest) == retained
        assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == value
                   for path, value in identities.items())
        assert _state() == before
        receipt.update(
            input_sha256=identities, source_unchanged=True,
            document_state_unchanged=True, deterministic_repeat=True,
            source_free_roundtrip=True, production_geometry_authorized=False,
            placement_claimed=False, full_chair_claimed=False,
        )
    except BaseException:
        receipt.update(status="FAIL", traceback=traceback.format_exc())
        raise
    finally:
        if witness is not None and witness.Name in App.listDocuments():
            App.closeDocument(witness.Name)
        _settle()
        receipt["owned_documents_closed"] = not App.listDocuments()
        (run_dir / "result.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
        )
    try:
        _active(None)
        assert _state() == initial
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
