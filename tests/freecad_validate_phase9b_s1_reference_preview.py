"""Exercise private S1 and S1J placement and recovery on one copied C10 fixture.

Use an empty qualified host. Optional local package and manifest paths
select the retained private reference; otherwise use invented geometry.
No production, fit, persistence or Phase 9B acceptance follows.
"""

import copy
import datetime
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import runpy
import shutil
import struct
import sys
import time
import traceback
from unittest.mock import patch
import zipfile
import zlib

import FreeCAD as App

if App.GuiUp:
    # FreeCAD document callbacks resolve Gui in the script's main namespace.
    import FreeCADGui as Gui


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.adapters.freecad import (  # noqa: E402
    chair_reference_preview as preview_adapter,
)
from tracktemplate.application.chair_definition import (  # noqa: E402
    chair_definition_package_from_json,
)
from tracktemplate.application.chair_model_research import (  # noqa: E402
    prepare_chair_model_research,
    prepare_chair_s1j_model_research,
)
from tracktemplate.compatibility.chair_reference_preview import (  # noqa: E402
    _recover_positions,
    _select_positions,
    _select_s1j_positions,
    _source_context,
)
import validate_phase9a_chair_assembly as assembly_tests  # noqa: E402
from validate_phase9a_chair_model_scale import REQUEST  # noqa: E402


SENTINEL = "Phase 9B S1 reference preview FreeCAD validation passed"


def _continuity_helpers():
    """Import fixture helpers without invoking their historical test run."""
    spec = importlib.util.spec_from_file_location(
        "_s1_preview_continuity",
        ROOT / "tests/freecad_validate_chair_export_continuity.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


continuity = _continuity_helpers()


def _face_crossing(centre, tangent, points):
    """Solve raw face sections independently by tangent dot products."""
    centre = tuple(Fraction(value) for value in centre)
    tangent = tuple(Fraction(value) for value in tangent)
    roots = []
    for index, (a, b) in enumerate(zip(points, points[1:])):
        a, b = (tuple(Fraction(value) for value in point) for point in (a, b))
        ha = sum(t * (p - c) for t, p, c in zip(tangent, a, centre))
        hb = sum(t * (p - c) for t, p, c in zip(tangent, b, centre))
        assert not ha == hb == 0
        if ha == hb:
            continue
        fraction = -ha / (hb - ha)
        if 0 <= fraction <= 1:
            point = tuple(x + fraction * (y - x) for x, y in zip(a, b))
            roots.append((index, fraction, point))
    assert len(roots) == 1, roots
    return roots[0]


def _placement_recovery(module, analysis, plan, rails, timbers, family):
    """Prove retained frames and recovery against raw named face sections."""
    select = _select_positions if family == "S1" else _select_s1j_positions
    code, old_count, extra_count = (1, 37, 17) if family == "S1" else (7, 4, 1)
    raw_before = json.dumps((analysis, plan, rails, timbers), sort_keys=True)
    old, old_excluded = select(module, analysis, plan)
    assert len(old) == old_count
    placements, excluded, records = _recover_positions(
        module, analysis, plan, rails, timbers, old, old_excluded, code,
    )
    by_id = {item.position_id: item for item in placements}
    assert all(by_id[item.position_id] == item for item in old)
    assert all(by_id[item.position_id] is item for item in old)
    original_ids = {item.position_id for item in old}
    recovered_ids = set(by_id) - original_ids
    assert len(recovered_ids) == len(records) == extra_count
    assert recovered_ids == {item["position_id"] for item in records}
    positions = {item["stable_chair_position_identity"]: item
                 for item in analysis["positions"]}
    rail_map = {item["stable_identity"]: item for item in rails}
    reasons = {item["chair_position_identity"]: item["reason"]
               for item in plan["analytical_only"]}
    datums = {item["base_z"] for item in plan["instances"]}
    assert len(datums) == 1
    base_z = next(iter(datums))
    observations = []
    for record in records:
        identity = record["position_id"]
        placement, position = by_id[identity], positions[identity]
        centre = position["centre_point"]
        tangent = position["local_rail_tangent"]
        rail = rail_map[position["rail_identity"]]
        assert record["original_reason"] == reasons[identity]
        assert record["rail_id"] == placement.rail_id == (
            rail["stable_identity"]
        )
        assert record["timber_id"] == placement.timber_id == (
            position["timber_identity"]
        )
        assert record["chair_code"] == position["chair_code"] == code
        assert placement.origin_mm == (*centre, base_z)
        witness = record["frame_evidence"]
        assert witness["method"] == "accepted-tangent-normal-intersection-v1"
        assert tuple(witness["centre_point_mm"]) == tuple(centre)
        assert tuple(witness["local_rail_tangent"]) == tuple(tangent)
        sides = []
        for face in ("gauge", "outer"):
            index, fraction, point = _face_crossing(
                centre, tangent, rail[face + "_face_points"],
            )
            evidence = witness[face + "_face"]
            exact_point = tuple(Fraction(value)
                                for value in evidence["point_mm_exact"])
            assert point == exact_point
            assert len(evidence["segments"]) == 1
            segment = evidence["segments"][0]
            assert segment["index"] == index
            assert Fraction(segment["fraction_exact"]) == fraction
            side = (-Fraction(tangent[1]) * (point[0] - Fraction(centre[0]))
                    + Fraction(tangent[0]) * (point[1] - Fraction(centre[1])))
            assert side * Fraction(
                evidence["normal_parameter_mm_exact"],
            ) > 0
            sides.append(side)
        assert sides[0] * sides[1] < 0
        sign = 1 if sides[0] > 0 else -1
        length = math.hypot(*tangent)
        y_axis = (sign * tangent[1] / length, -sign * tangent[0] / length)
        x_axis = (y_axis[1], -y_axis[0])
        assert placement.x_axis == x_axis and placement.y_axis == y_axis
        observations.append({
            "position_id": identity, "centre_mm": centre, "base_z_mm": base_z,
            "face_sides_exact": [str(side) for side in sides],
        })
    assert json.dumps((analysis, plan, rails, timbers), sort_keys=True) == (
        raw_before
    )
    victim = positions[records[0]["position_id"]]
    rejected_faces = {}
    for case in ("missing", "ambiguous"):
        changed_rails = copy.deepcopy(rails)
        changed = next(item for item in changed_rails
                       if item["stable_identity"] == victim["rail_identity"])
        if case == "missing":
            changed.pop("gauge_face_points")
        else:
            centre = victim["centre_point"]
            tangent = victim["local_rail_tangent"]
            normal = (-tangent[1], tangent[0])
            changed["gauge_face_points"] = [
                tuple(c + along * t + across * n
                      for c, t, n in zip(centre, tangent, normal))
                for along, across in ((1, 1), (-1, 1), (1, 2))
            ]
        retained, refusals, recovered = _recover_positions(
            module, analysis, plan, changed_rails, timbers,
            old, old_excluded, code,
        )
        victim_id = victim["stable_chair_position_identity"]
        assert victim_id not in {item.position_id for item in retained}
        assert victim_id not in {item["position_id"] for item in recovered}
        refusal = next(item for item in refusals
                       if item["position_id"] == victim_id)
        assert refusal["reason"] == reasons[victim_id]
        assert all(item in retained for item in old)
        rejected_faces[case] = refusal
    assert json.dumps((analysis, plan, rails, timbers), sort_keys=True) == (
        raw_before
    )
    return placements, excluded, records, {
        "unchanged_legacy_count": old_count,
        "independent_recovery_count": extra_count,
        "positions": observations,
        "named_face_rejections": rejected_faces,
    }


def _inputs(family="S1"):
    package_path = os.environ.get(f"TRACKTEMPLATE_{family}_REFERENCE_PACKAGE")
    manifest_path = os.environ.get(f"TRACKTEMPLATE_{family}_REFERENCE_MANIFEST")
    if package_path or manifest_path:
        assert package_path and manifest_path
        text = Path(manifest_path).read_text(encoding="utf-8")
        package = chair_definition_package_from_json(
            Path(package_path).read_text(encoding="utf-8"), text,
        )
        return package, text
    if family == "S1J":
        from validate_phase9b_chair_s1j import synthetic_s1j_package_records

        record, manifest = synthetic_s1j_package_records()
        text = assembly_tests.seat_tests.canonical_json(manifest)
        package = chair_definition_package_from_json(
            assembly_tests.seat_tests.canonical_json(record), text,
        )
        return package, text
    record, manifest = assembly_tests.synthetic_assembly_package_records()
    package, text, _research = assembly_tests.load_research(record, manifest)
    return package, text


def _archive_state(content):
    """Compare every archive byte except verified ZIP DOS timestamps.

    FreeCAD stamps each fresh dump with wall time. Parse its classic ZIP
    layout before masking the four timestamp bytes in each local and
    central header. Reject unsupported layouts; retain payloads, ordering,
    extra fields, comments and every other header byte without alteration.
    """
    content = bytes(content)
    end = len(content) - 22
    footer = struct.unpack_from("<4s4H2LH", content, end)
    assert footer[0] == b"PK\x05\x06"
    assert footer[1:3] == (0, 0) and footer[3] == footer[4]
    assert 0 < footer[4] < 65535 and footer[7] == 0
    directory_size, directory_start = footer[5:7]
    assert directory_start + directory_size == end
    normalised = bytearray(content)
    local_position, central_position = 0, directory_start
    names = []
    for _index in range(footer[4]):
        central = struct.unpack_from(
            "<4s6H3L5H2L", content, central_position,
        )
        assert central[0] == b"PK\x01\x02"
        assert central[13] == 0 and central[16] == local_position
        local = struct.unpack_from("<4s5H3L2H", content, local_position)
        assert local[0] == b"PK\x03\x04"
        assert local[1:10] == central[2:11]
        assert local[1:4] == (20, 0, zipfile.ZIP_DEFLATED)
        local_name = local_position + 30
        central_name = central_position + 46
        name = content[local_name:local_name + local[9]]
        assert name and name not in names
        assert name == content[central_name:central_name + central[10]]
        names.append(name)
        local_end = local_name + local[9] + local[10] + local[7]
        central_end = central_name + sum(central[10:13])
        assert local_end <= directory_start and central_end <= end
        normalised[local_position + 10:local_position + 14] = b"\0" * 4
        normalised[central_position + 12:central_position + 16] = b"\0" * 4
        local_position, central_position = local_end, central_end
    assert local_position == directory_start and central_position == end
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        assert len(archive.infolist()) == len(names)
        for member in archive.infolist():
            archive.read(member)  # Validate each complete payload and CRC.
    return hashlib.sha256(normalised).hexdigest()


def _archive_controls():
    """Reject valid content changes and every single-byte corruption."""
    def example(records, date=(2020, 1, 2, 3, 4, 6), comment=b""):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            for name, payload in records:
                member = zipfile.ZipInfo(name, date)
                member.compress_type = zipfile.ZIP_DEFLATED
                member.comment = comment
                archive.writestr(member, payload)
        return stream.getvalue()

    records = [("first.bin", b"native state"), ("second.bin", b"geometry")]
    baseline = example(records)
    expected = _archive_state(baseline)
    later = example(records, date=(2026, 10, 20, 22, 30, 8))
    assert baseline != later and _archive_state(later) == expected
    witnesses = {
        "valid-payload-and-crc": example([
            ("first.bin", b"changed state"), records[1],
        ]),
        "member-identity": example([("other.bin", records[0][1]), records[1]]),
        "member-order": example(list(reversed(records))),
        "member-metadata": example(records, comment=b"changed metadata"),
    }
    for label, changed in witnesses.items():
        assert _archive_state(changed) != expected, label
    rejected = 0
    for index in range(len(baseline)):
        changed = bytearray(baseline)
        changed[index] ^= 1
        try:
            observed = _archive_state(changed)
        except (AssertionError, struct.error, zipfile.BadZipFile, zlib.error):
            rejected += 1
        else:
            assert observed != expected, index
            rejected += 1
    return {"timestamp_only": "PASS", "valid_mutations": list(witnesses),
            "single_byte_mutations_rejected": rejected}


def _source_state_controls(module, document, run_dir):
    """Prove stable observation and native mutation rejection on a copy."""
    if App.GuiUp:
        import FreeCADGui as Gui
        from PySide import QtWidgets

        # Finish initial rendering before guarding the complete camera state.
        Gui.getDocument(document.Name).activeView().redraw()
        Gui.updateGui()
        QtWidgets.QApplication.processEvents()
    baseline = _state(module, document)
    time.sleep(2.2)
    assert _state(module, document) == baseline
    target = run_dir / "state-mutation.FCStd"
    shutil.copy2(document.FileName, target)
    witness = App.openDocument(str(target))
    try:
        before = _state(module, witness)
        witness.Objects[0].Label += " mutation witness"
        assert _state(module, witness) != before
        shape_object = next(obj for obj in witness.Objects
                            if "Shape" in obj.PropertiesList
                            and not obj.Shape.isNull())
        before_shape = _archive_state(shape_object.dumpContent())
        changed_shape = shape_object.Shape.copy()
        changed_shape.translate(App.Vector(0.01, 0, 0))
        shape_object.Shape = changed_shape
        assert _archive_state(shape_object.dumpContent()) != before_shape
    finally:
        App.closeDocument(witness.Name)
        App.setActiveDocument(document.Name)
    assert _state(module, document) == baseline
    return {"delayed_noop": "PASS", "label_mutation_rejected": True,
            "shape_mutation_rejected": True, "original_unchanged": True}


def _state(module, document, entity_kind="turnout", entity_id="TO-001"):
    """Retain exact decision, editable, native and visible source state."""
    result = {
        "decisions": continuity._decision_state(module, document, entity_kind),
        "editable": continuity.SIGNATURE._document_state(
            module, document, entity_kind, entity_id,
        ),
        "filename": document.FileName,
        "undo": document.UndoCount, "redo": document.RedoCount,
        "objects": tuple((obj.Name, obj.TypeId) for obj in document.Objects),
        "content": tuple((obj.Name, _archive_state(
            obj.dumpContent(),
        )) for obj in document.Objects),
    }
    if App.GuiUp:
        import FreeCADGui as Gui

        result["gui_modified"] = Gui.getDocument(document.Name).Modified
        result["camera"] = Gui.getDocument(
            document.Name,
        ).activeView().getCamera()
        result["views"] = tuple((obj.Name, _archive_state(
            obj.ViewObject.dumpContent(),
        )) for obj in document.Objects)
    return result


def _reject(operation, expected):
    try:
        operation()
    except (ValueError, RuntimeError) as error:
        assert expected in str(error), str(error)
        assert not getattr(error, "__notes__", ()), error.__notes__
        return str(error)
    raise AssertionError("Invalid preview was accepted: " + expected)


def _images(document, placements, run_dir):
    """Capture the rendered preview without invalidating its GL buffer."""
    from PySide6 import QtWidgets
    from PySide6.QtOpenGLWidgets import QOpenGLWidget

    view = Gui.getDocument(document.Name).activeView()
    window = Gui.getMainWindow()
    captures = []

    def capture(name, *, target=None):
        view.redraw()
        for _iteration in range(5):
            Gui.updateGui()
            QtWidgets.QApplication.processEvents()
        if target is not None:
            assert tuple(view.getCameraNode().position.getValue()) == (
                target["stored_camera_position_mm"]
            )
            assert tuple(view.getCameraOrientation().Q) == (
                target["orientation_q"]
            )
        assert App.ActiveDocument is document
        assert Gui.activeDocument().Document is document
        area = window.findChild(QtWidgets.QMdiArea)
        subwindow = area.activeSubWindow()
        assert subwindow is not None and subwindow.isVisible()
        widgets = [widget for widget in subwindow.findChildren(QOpenGLWidget)
                   if widget.isVisible()]
        assert len(widgets) == 1
        widget = widgets[0]
        behaviour = widget.updateBehavior()
        camera = view.getCamera()
        try:
            # Qt grab renders again; FreeCAD's paintGL queues its redraw.
            # Preserve the settled buffer only during this synchronous read.
            widget.setUpdateBehavior(QOpenGLWidget.PartialUpdate)
            image = window.grab()
        finally:
            widget.setUpdateBehavior(behaviour)
        assert widget.updateBehavior() == behaviour
        assert view.getCamera() == camera
        assert App.ActiveDocument is document
        assert Gui.activeDocument().Document is document
        assert area.activeSubWindow() is subwindow
        assert not image.isNull() and image.save(str(run_dir / name))
        captures.append({
            "file": name, "document": document.Name,
            "mdi_title": subwindow.windowTitle(), "camera": camera,
            "original_update_behaviour": str(behaviour),
            "restored_update_behaviour": str(widget.updateBehavior()),
            "target": target,
        })

    view.viewTop()
    view.fitAll()
    capture("overview.png")
    view.viewAxonometric()
    # The view command queues its rotation. Finish it before placing the
    # camera, or the pending rotation will move the selected chair away.
    view.redraw()
    for _iteration in range(5):
        Gui.updateGui()
        QtWidgets.QApplication.processEvents()
    camera = view.getCameraOrientation()
    placement = placements[len(placements) // 2]
    centre = App.Vector(*placement.origin_mm)
    node = view.getCameraNode()
    intended = tuple(centre + camera.multVec(App.Vector(0, 0, 30)))
    node.position.setValue(intended)
    node.height.setValue(18.0)
    stored = tuple(node.position.getValue())
    # Coin camera coordinates use single precision. This is a rounding
    # bound for the view only; it changes no geometry or source comparison.
    rounding_bound = max(1.0, *(abs(value) for value in intended)) * 2**-23
    assert max(abs(a - b) for a, b in zip(stored, intended)) <= rounding_bound
    capture("chair-closeup.png", target={
        "position_id": placement.position_id,
        "point_mm": tuple(centre),
        "intended_camera_position_mm": intended,
        "stored_camera_position_mm": stored,
        "orientation_q": tuple(camera.Q),
        "camera_rounding_bound_mm": rounding_bound,
    })
    assert captures[0]["camera"] != captures[1]["camera"]
    (run_dir / "capture-state.json").write_text(
        json.dumps(captures, indent=2) + "\n", encoding="utf-8",
    )
    return [item["file"] for item in captures]


def validate(family="S1"):
    """Run one isolated proof and retain raw receipts, including failures."""
    assert family in {"S1", "S1J"}, "Unsupported proof family"
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    selected, excluded_count, confirmed, unresolved = (
        (54, 114, 54, 0) if family == "S1" else (5, 163, 5, 0)
    )
    prepare_model = (prepare_chair_model_research if family == "S1"
                     else prepare_chair_s1j_model_research)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    run_dir = Path(os.environ.get(
        f"TRACKTEMPLATE_{family}_PREVIEW_RUN_DIR",
        ROOT / "benchmark-output" / (family.lower() + "-reference-preview")
        / stamp,
    )).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp), "family": family}
    try:
        receipt["archive_controls"] = _archive_controls()
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        api, bootstrap = launcher["_load_foundation"](ROOT)
        session, routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, bootstrap,
        )
        module = session.module
        preview_chairs = getattr(
            session, "preview_" + family.lower() + "_reference_chairs",
        )
        receipt["profile"] = launcher["FOUNDATION_RESULT"][
            "matched_profile_id"
        ]
        receipt["routing"] = routing
        document = continuity._prepare_case(module, run_dir, "turnout")
        receipt["source_state_controls"] = _source_state_controls(
            module, document, run_dir,
        )
        foreign = App.newDocument("UnrelatedWitness")
        foreign.addObject("App::FeaturePython", "Keep").Label = "Keep me"
        App.setActiveDocument(document.Name)
        if App.GuiUp:
            import FreeCADGui as Gui
            from PySide import QtWidgets

            Gui.getMainWindow().resize(1600, 1000)
            Gui.Selection.addSelection(document.Objects[0])
            QtWidgets.QApplication.processEvents()
        original = _state(module, document)
        source_objects = {obj.Name: obj for obj in document.Objects}
        source_shapes = {obj.Name: obj.Shape for obj in document.Objects
                         if "Shape" in obj.PropertiesList}
        package, text = _inputs(family)
        model = prepare_model(package, text, REQUEST)
        _binding, analysis, _settings, plan, rails, timbers = _source_context(
            module, document, "TO-001", family,
        )
        placements, excluded, recovered, proof = _placement_recovery(
            module, analysis, plan, rails, timbers, family,
        )
        receipt["placement_recovery"] = proof
        started = time.perf_counter()
        result = preview_chairs(
            document, "TO-001", package, text, REQUEST,
        )
        receipt["construction_seconds"] = time.perf_counter() - started
        receipt["preview"] = result
        assert result["source_receipt"]["recovered_positions"] == recovered
        preview = App.getDocument(result["document_name"])
        assert App.ActiveDocument is preview
        assert not preview.FileName and len(preview.Objects) == 7
        assert result["package_signature"] == model.package.content_signature
        assert result["manifest_signature"] == model.manifest_signature
        assert result["request_signature"] == model.request_signature
        assert len(placements) + len(excluded) == 168
        assert len(placements) == selected and len(excluded) == excluded_count
        assert result["source_receipt"][
            "confirmed_" + family.lower() + "_count"
        ] == confirmed
        assert result["source_receipt"][
            "unresolved_confirmed_" + family.lower() + "_count"
        ] == unresolved
        assert (
            f"{selected}/{confirmed} {family}; {unresolved} unresolved"
        ) in preview.Label
        assert all(len(obj.Shape.Solids) == len(placements)
                   for obj in preview.Objects[2:])
        assert all("GeneratedBy" not in obj.PropertiesList
                   for obj in preview.Objects)
        assert _state(module, document) == original
        for name, obj in source_objects.items():
            assert document.getObject(name) is obj
        for name, shape in source_shapes.items():
            assert document.getObject(name).Shape.isSame(shape), name
        assert App.getDocument(foreign.Name) is foreign
        assert foreign.getObject("Keep").Label == "Keep me"
        shapes_before = [obj.Shape for obj in preview.Objects]
        preview.undo()
        assert not preview.Objects
        preview.redo()
        assert len(preview.Objects) == 7
        assert all(obj.Shape.isSame(shape) for obj, shape in zip(
            preview.Objects, shapes_before,
        ))
        receipt["undo_redo"] = "PASS"
        if App.GuiUp:
            receipt["images"] = _images(preview, placements, run_dir)
        App.closeDocument(preview.Name)
        App.setActiveDocument(document.Name)
        if App.GuiUp:
            # Document closure clears selection; restore this test fixture.
            Gui.Selection.addSelection(document.Objects[0])
        assert _state(module, document) == original

        # A sub-micrometre source change aliases the legacy cache key, but
        # must invalidate the full-precision preview binding before commit.
        create = getattr(
            preview_adapter, "create_" + family.lower() + "_reference_preview",
        )
        other_family = "S1J" if family == "S1" else "S1"
        other_package, other_text = _inputs(other_family)
        before_rejection = App.listDocuments()
        try:
            preview_chairs(document, "TO-001", other_package, other_text, REQUEST)
        except ValueError as error:
            receipt["other_family_package_rejected"] = str(error)
        else:
            raise AssertionError("Another family's package was accepted")
        other_select = (_select_s1j_positions if family == "S1"
                        else _select_positions)
        other_placements, _other_excluded = other_select(module, analysis, plan)
        roles = module._turnout_objects_by_role(document, "TO-001")
        context_shapes = tuple(roles[role].Shape.copy() for role in (
            module.TURNOUT_RAIL_ROLE, module.TURNOUT_TIMBER_ROLE,
        ))
        try:
            create(package, text, REQUEST, other_placements, context_shapes,
                   result["source_receipt"], lambda: None)
        except TypeError as error:
            assert family + "Placement" in str(error), str(error)
            receipt["other_family_placements_rejected"] = str(error)
        else:
            raise AssertionError("Another family's placements were accepted")
        assert App.listDocuments() == before_rejection
        assert App.ActiveDocument is document
        assert _state(module, document) == original
        original_top = module._chair_physical_top_z
        registry = App.listDocuments()

        def stale_during_build(*args):
            def changed_source():
                with patch.object(
                    module, "_chair_physical_top_z",
                    side_effect=lambda *values: original_top(*values) + 1e-8,
                ):
                    args[-1]()

            return create(*args[:-1], changed_source)

        with patch.object(
            session, "_" + family.lower() + "_reference_preview_factory",
            side_effect=stale_during_build,
        ):
            receipt["subprecision_rejection"] = _reject(lambda: (
                preview_chairs(
                    document, "TO-001", package, text, REQUEST,
                )
            ), "source changed")
        assert App.listDocuments() == registry
        assert App.ActiveDocument is document
        assert _state(module, document) == original
        receipt["transaction_failure_cleanup"] = "PASS"

        # Each negative fixture is copied from the already saved C10 case.
        # No original fixture or live operator document is modified.
        receipt["analysis_rejections"] = {}
        for case in ("missing", "stale"):
            target = run_dir / (case + ".FCStd")
            shutil.copy2(document.FileName, target)
            negative = App.openDocument(str(target))
            if case == "missing":
                settings_object = module._chair_settings_object(
                    negative, "turnout", "TO-001",
                )
                setattr(settings_object, module.CHAIR_ANALYSIS_RESULT_PROPERTY,
                        "")
            else:
                module.invalidate_chair_analysis(
                    negative, "turnout", "TO-001", remove_display=True,
                )
            before_documents = App.listDocuments()
            try:
                preview_chairs(
                    negative, "TO-001", package, text, REQUEST,
                )
            except ValueError as error:
                receipt["analysis_rejections"][case] = str(error)
            else:
                raise AssertionError("Invalid analysis accepted: " + case)
            assert App.listDocuments() == before_documents
            App.closeDocument(negative.Name)
        App.setActiveDocument(document.Name)
        if App.GuiUp:
            Gui.Selection.addSelection(document.Objects[0])
        assert App.ActiveDocument is document
        assert _state(module, document) == original
        receipt["source_unchanged"] = True
        receipt["status"] = "PASS"
    except BaseException:
        receipt["status"] = "FAIL"
        receipt["traceback"] = traceback.format_exc()
        raise
    finally:
        (run_dir / "result.json").write_text(
            json.dumps(receipt, allow_nan=False, indent=2) + "\n",
            encoding="utf-8",
        )
        for name in tuple(App.listDocuments()):
            App.closeDocument(name)
    print(SENTINEL if family == "S1" else
          "Phase 9B S1J reference preview FreeCAD validation passed")
    return receipt


if __name__ in {"__main__", "freecad_validate_phase9b_s1_reference_preview"}:
    validate(os.environ.get("TRACKTEMPLATE_REFERENCE_PROOF_FAMILY", "S1"))
