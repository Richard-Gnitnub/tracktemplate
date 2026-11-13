"""Import-safe GUI proof of four fixed crossing assemblies.

The controller owns authority and process guards. This entry checks one
preview, its visibility, a retained plinth interior, rollback and disposal.
It supplements the native comparison without rebuilding source geometry.
"""

from contextlib import ExitStack
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import traceback
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCOPE = "TO-001-fixed-crossing-gui-v1"
BASE = "a801f4444bec2f6799e7d2ad1fa2da3aac78db95"
PREFIX = "TRACKTEMPLATE_TO_CROSSING_GUI="
NATIVE_PATH = "tests/freecad_validate_to_crossing_chairs.py"
NATIVE_SHA256 = (
    "583f3d37d658e0e8a339ccb7ba58191ebb2d0e38b039ea0486126b3b1496b5ab"
)
LEGACY_GUI_PATH = "tests/freecad_validate_to_single_rail_gui.py"
LEGACY_GUI_SHA256 = (
    "b5ac9a3c9bd139b4d67420134cd59400a90ced848e885b83919defb2dea85488"
)


def native():
    path = ROOT / NATIVE_PATH
    assert hashlib.sha256(path.read_bytes()).hexdigest() == NATIVE_SHA256
    import freecad_validate_to_crossing_chairs as module

    assert Path(module.__file__).resolve() == path
    return module


def legacy_gui():
    path = ROOT / LEGACY_GUI_PATH
    assert hashlib.sha256(path.read_bytes()).hexdigest() == LEGACY_GUI_SHA256
    import freecad_validate_to_single_rail_gui as helper

    assert Path(helper.__file__).resolve() == path
    return helper


def gui_helpers():
    return legacy_gui().gui_helpers()


def runtime():
    return legacy_gui().runtime()


def limits(stage):
    return legacy_gui().limits(stage)


def check_image(directory, record, name):
    return legacy_gui().check_image(directory, record, name)


def sentinel(stage):
    assert stage in ("readiness", "gui")
    return (
        "Fixed TO crossing GUI readiness passed"
        if stage == "readiness"
        else "Fixed TO crossing GUI validation passed"
    )


def image_names(stage):
    assert stage in ("readiness", "gui")
    if stage == "readiness":
        return ("to-crossing-readiness.png",)
    return (
        "to-crossing-overview.png",
        "to-crossing-XA-AA.png",
        "to-crossing-CD-DD.png",
        "to-crossing-selected-chair.png",
        "to-crossing-layer-hidden.png",
        "to-crossing-rollback-restored.png",
    )


def compare_frames(placements, fixture):
    return native().compare_frames(placements, fixture)


def interior_target(part, child):
    """Find a native face interior on the retained source-named plinth.

    Native minimum distances establish membership and separation from the
    boundary. No source coordinate, face ordinal or geometric tolerance is
    invented here. No candidate means refusal before a synthetic click.
    """
    choices = []
    for index, face in enumerate(child.Faces, 1):
        if (
            not face.isValid()
            or not math.isfinite(face.Area)
            or face.Area <= 0
        ):
            continue
        normal = face.normalAt(0, 0)
        if normal.z <= 0 or not face.Edges:
            continue
        point = face.CenterOfMass
        vertex = part.Vertex(point)
        distance = face.distToShape(vertex)[0]
        clearance = min(edge.distToShape(vertex)[0] for edge in face.Edges)
        if distance == 0 and math.isfinite(clearance) and clearance > 0:
            choices.append((face.Area, index, point))
    assert choices, "TO_CROSSING_NO_INTERIOR_TARGET"
    # Stable source order breaks equal-area ties; no face number is fixed.
    _area, index, point = max(choices, key=lambda row: (row[0], -row[1]))
    return index, point


def check_pick(rows, document, obj, face_index):
    assert len(rows) == 1, "TO_CROSSING_PICK_COUNT"
    row = rows[0]
    assert (row.DocumentName, row.ObjectName) == (document, obj), (
        "TO_CROSSING_PICK_IDENTITY"
    )
    assert tuple(row.SubElementNames) == ("Face" + str(face_index),), (
        "TO_CROSSING_PICK_FACE"
    )


def expected_checks(stage):
    assert stage in ("readiness", "gui")
    checks = dict(
        binding_checks=1,
        catalogue_contracts=4,
        source_frame_inputs=50,
        source_frame_comparisons=50,
        successful_previews=1,
        assemblies=4,
        layers=137,
        successful_components=135,
        layer_visibility_checks=137,
        viewport_picks=1,
        late_verifier_failures=1,
        rolled_back_components=135,
        source_preservation_checks=4,
        preview_disposals=1,
        screenshots=6,
        readiness_empty_documents=0,
    )
    if stage == "readiness":
        checks = dict.fromkeys(checks, 0)
        checks.update(
            binding_checks=1,
            catalogue_contracts=4,
            source_frame_inputs=50,
            screenshots=1,
            readiness_empty_documents=1,
        )
    return checks


def check_counts(checks, stage):
    expected = expected_checks(stage)
    assert type(checks) is dict and set(checks) == set(expected)
    assert all(
        type(checks[key]) is int and checks[key] == value
        for key, value in expected.items()
    )


def _matches(record, expected):
    assert type(record) is dict
    assert all(
        type(record.get(key)) is type(value) and record[key] == value
        for key, value in expected.items()
    )


def _hash(value):
    return (
        type(value) is str
        and re.fullmatch("[0-9a-f]{64}", value)
        and value != "0" * 64
    )


def validate_authority(authority, config, entry_sha256):
    """Check GUI bindings; the hosted controller owns the complete gate."""
    assert type(authority) is dict
    stage = authority.get("stage")
    freecad, display = limits(stage)
    expected = dict(
        schema=1,
        scope_id=SCOPE,
        stage=stage,
        source_base_commit=BASE,
        source_commit=config.source_commit,
        owner="Richard-Gnitnub",
        execution_authorized=True,
        independent_review="PASS",
        run_attempt=1,
        gui_entry_sha256=entry_sha256,
        native_entry_sha256=NATIVE_SHA256,
        input_hashes=dict(native().INPUT_HASHES),
        freecad_limits=freecad,
        display_limits=display,
        initial_reserve_mib=8192,
        software_renderer="llvmpipe",
    )
    _matches(authority, expected)
    assert re.fullmatch("[0-9a-f]{40}", config.source_commit)
    assert os.environ.get("GITHUB_SHA") == config.source_commit
    assert os.environ.get("GITHUB_ACTIONS") == "true"
    assert os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
    assert os.environ.get("GITHUB_RUN_ATTEMPT") == "1"
    assert os.environ.get("GITHUB_RUN_ID", "").isdigit()
    assert all(
        type(authority.get(key)) is str and authority[key].strip()
        for key in ("decision_id", "handling_decision")
    )
    publication = authority.get("publication_review")
    _matches(
        publication,
        dict(
            status="PASS",
            independent_review="PASS",
            input_hashes=expected["input_hashes"],
            handling_decision=authority["handling_decision"],
        ),
    )
    assert _hash(publication.get("evidence_sha256"))
    assert type(publication.get("publication_basis")) is str
    assert publication["publication_basis"].strip()
    proof = authority.get("prior_native_evidence")
    _matches(
        proof,
        dict(
            status="PASS",
            independent_review="PASS",
            entry_sha256=NATIVE_SHA256,
            input_hashes=expected["input_hashes"],
            scope_id=native().SCOPE,
            tests=1,
            skips=0,
            run_attempt=1,
            cleanup=True,
            evidence_verified=True,
            independent_preservation=True,
            source_frame_comparisons=50,
            component_comparisons=135,
            stored_compound_checks=135,
            stored_child_checks=135,
            successful_components=135,
            rolled_back_components=135,
        ),
    )
    assert type(proof.get("run_id")) is int and proof["run_id"] > 0
    assert str(proof["run_id"]) != os.environ["GITHUB_RUN_ID"]
    assert _hash(proof.get("evidence_sha256"))
    assert proof.get("source_commit") == config.source_commit
    assert authority.get("native_source_reuse") is None
    if stage == "gui":
        ready = authority.get("gui_readiness_review")
        _matches(
            ready,
            dict(
                status="PASS",
                independent_review="PASS",
                source_commit=config.source_commit,
                gui_entry_sha256=entry_sha256,
                input_hashes=expected["input_hashes"],
                tests=1,
                skips=0,
                cleanup=True,
                independent_preservation=True,
            ),
        )
        assert type(ready.get("run_id")) is int and ready["run_id"] > 0
        assert ready["run_id"] != proof["run_id"]
        assert str(ready["run_id"]) != os.environ["GITHUB_RUN_ID"]


def configuration():
    helper = native().shared()
    path = helper.regular_path(os.environ["TRACKTEMPLATE_TO_GUI_AUTHORITY"])
    assert (
        helper.sha256(path)
        == os.environ["TRACKTEMPLATE_TO_GUI_AUTHORITY_SHA256"]
    )
    authority = native().strict_json(path.read_bytes())
    assert authority.get("stage") in ("readiness", "gui")
    config = native().configuration(
        "readiness" if authority["stage"] == "readiness" else "native"
    )
    validate_authority(authority, config, helper.sha256(Path(__file__)))
    config_path = helper.regular_path(
        os.environ["TRACKTEMPLATE_TO_RUN_CONFIG"]
    )
    raw = native().strict_json(config_path.read_bytes())
    assert raw["handling_decision"] == authority["handling_decision"]
    return config, authority


def preflight(rt, config, receipt):
    with ExitStack() as guards:
        for owner, name in (
            (rt.app, "newDocument"),
            (rt.app, "openDocument"),
            (rt.part, "Shape"),
            (rt.part, "makeCompound"),
        ):
            guards.enter_context(
                patch.object(
                    owner,
                    name,
                    side_effect=(
                        AssertionError(
                            "Readiness constructed document or geometry"
                        )
                    ),
                )
            )
        rt.session.routing_record()
        receipt["checks"]["binding_checks"] = 1
        native().source_contract()
        selected = native().catalogues(config.inputs)
        assert set(selected) == set(native().FAMILIES)
        receipt["checks"]["catalogue_contracts"] = len(selected)
        receipt["checks"]["source_frame_inputs"] = native().validate_fixture(
            config.fixture
        )
    assert not rt.app.listDocuments() and rt.app.ActiveDocument is None
    return selected


def finish(rt, config, owned, receipt):
    """Attempt owned cleanup even when input preservation has failed."""
    errors = []
    try:
        native().verify_inputs(config.inputs)
        receipt["input_bindings_unchanged"] = True
    except BaseException as error:
        receipt["input_bindings_unchanged"] = False
        native().record_failure(config, receipt, "input", error)
        errors.append(error)
    try:
        assert rt is not None, "No runtime cleanup evidence"
        rt.gui.Selection.clearSelection()
        native().cleanup(rt.app, owned)
        assert rt.gui.activeDocument() is None
        assert rt.gui.ActiveDocument is None
        receipt["remaining_documents"] = len(rt.app.listDocuments())
        receipt["owned_documents_closed"] = True
    except BaseException as error:
        receipt["owned_documents_closed"] = False
        native().record_failure(config, receipt, "cleanup", error)
        errors.append(error)
    receipt["cleanup_errors"] = [
        "TO_CROSSING_CLEANUP_FAILED" for _error in errors
    ]
    return errors


class ToCrossingGui(unittest.TestCase):
    def test_authorised_gui_stage(self):
        config, authority = configuration()
        stage, started = authority["stage"], time.monotonic()
        receipt = dict(
            status="RUNNING",
            stage=stage,
            scope_id=SCOPE,
            test_id=self.id(),
            source_commit=config.source_commit,
            fixture_sha256=native().FIXTURE_SHA256,
            profile=native().shared().PROFILE,
            gui=True,
            visual_review="REQUIRED",
            physical_fit="NOT_PROVED",
            native_evidence_reused={
                key: authority["prior_native_evidence"][key]
                for key in (
                    "run_id",
                    "source_commit",
                    "entry_sha256",
                    "evidence_sha256",
                )
            },
            checks=dict.fromkeys(expected_checks(stage), 0),
            input_sha256=dict(native().INPUT_HASHES),
            stage_timings={},
            screenshots=[],
            failures=[],
        )
        self.receipt = receipt
        rt, owned, failure = None, {}, None
        try:
            rt = runtime()
            selected = preflight(rt, config, receipt)
            receipt["stage_timings"]["readiness_seconds"] = (
                time.monotonic() - started
            )
            if stage == "readiness":
                self._readiness(rt, config, owned, receipt)
            else:
                begin = time.monotonic()
                self._journey(rt, config, selected, owned, receipt)
                receipt["stage_timings"]["gui_seconds"] = (
                    time.monotonic() - begin
                )
            check_counts(receipt["checks"], stage)
            assert [item["path"] for item in receipt["screenshots"]] == list(
                image_names(stage)
            )
        except BaseException as error:
            failure = error
            native().record_failure(config, receipt, "gui", error)
        finally:
            begin = time.monotonic()
            errors = finish(rt, config, owned, receipt)
            if errors and failure is None:
                failure = errors[0]
            receipt["stage_timings"]["cleanup_seconds"] = (
                time.monotonic() - begin
            )
            receipt["stage_timings"]["total_seconds"] = (
                time.monotonic() - started
            )
            receipt["status"] = "PASS" if failure is None else "FAIL"
            if failure is None:
                receipt["sentinel"] = sentinel(stage)
            native().write_result(config, receipt)
        if failure is not None:
            raise AssertionError("TO_CROSSING_GUI_FAILED") from None

    def _capture(self, rt, config, receipt, name):
        assert name in image_names(receipt["stage"])
        assert name not in [row["path"] for row in receipt["screenshots"]]
        path = config.evidence / name
        assert not path.exists() and not path.is_symlink()
        rt.helpers.settle()
        active = rt.app.ActiveDocument
        camera = rt.gui.activeDocument().activeView().getCamera()
        selection = rt.helpers.state()["selection"]
        record = gui_helpers()._readiness_image(rt.gui, rt.qtwidgets, path)
        check_image(config.evidence, record, name)
        assert rt.app.ActiveDocument is active
        assert rt.gui.activeDocument().activeView().getCamera() == camera
        assert rt.helpers.state()["selection"] == selection
        receipt["screenshots"].append(record)
        receipt["checks"]["screenshots"] += 1

    def _readiness(self, rt, config, owned, receipt):
        with (
            patch.object(
                rt.part,
                "Shape",
                side_effect=AssertionError("Readiness constructed shape"),
            ),
            patch.object(
                rt.part,
                "makeCompound",
                side_effect=AssertionError("Readiness constructed compound"),
            ),
        ):
            document = rt.app.newDocument("TOGuiReadiness")
            owned[document.Name] = document
            rt.helpers.settle()
            assert not document.Objects
            assert rt.app.listDocuments() == {document.Name: document}
            receipt["renderer"] = gui_helpers()._gl_record(
                rt.app, rt.gui, rt.qtgui, rt.qtwidgets
            )
            self._capture(rt, config, receipt, image_names("readiness")[0])
            assert not document.Objects
            receipt["checks"]["readiness_empty_documents"] = 1

    def _structure(self, result, preview, captured, fixture, receipt):
        checks = receipt["checks"]
        checks["successful_components"] = native().check_structure(
            result, preview, fixture
        )
        checks["source_frame_comparisons"] = compare_frames(captured, fixture)
        checks.update(successful_previews=1, assemblies=4, layers=137)

    def _source_preserved(self, rt, baseline, source, context, receipt):
        from tracktemplate.compatibility.chair_reference_preview import (
            _open_source_context,
        )

        rt.helpers.settle()
        state = rt.helpers.state()
        names = {row["name"] for row in baseline["documents"]}
        assert [row for row in state["documents"] if row["name"] in names] == (
            baseline["documents"]
        )
        assert (
            _open_source_context(
                rt.session.module, source, "TO-001", "Crossings"
            )
            == context
        )
        receipt["checks"]["source_preservation_checks"] += 1

    def _focus(self, rt, rows):
        view = rt.gui.activeDocument().activeView()
        view.viewTop()
        rt.helpers.settle()
        points = [row["body"]["origin_mm"] for row in rows]
        low = [min(point[index] for point in points) for index in range(3)]
        high = [max(point[index] for point in points) for index in range(3)]
        centre = rt.app.Vector(*((a + b) / 2 for a, b in zip(low, high)))
        orientation = view.getCameraOrientation()
        node = view.getCameraNode()
        # Retained 18 mm/30 mm framing, enlarged only for a displayed group.
        intended = tuple(centre + orientation.multVec(rt.app.Vector(0, 0, 30)))
        node.position.setValue(intended)
        node.height.setValue(
            max(18.0, 2 * max(b - a for a, b in zip(low, high)))
        )
        rounding_bound = max(1.0, *(abs(value) for value in intended)) * 2**-23
        assert (
            max(abs(a - b) for a, b in zip(node.position.getValue(), intended))
            <= rounding_bound
        )
        view.redraw()
        rt.helpers.settle()

    def _pick(self, rt, preview, fixture):
        from PySide6.QtOpenGLWidgets import QOpenGLWidget

        row = fixture["positions"][0]
        assert row["family"] == "XA"
        self._focus(rt, [row])
        obj = preview.getObject("XA_base_plinth")
        assert obj is not None
        visibility = [
            (layer, layer.ViewObject.Visibility) for layer in preview.Objects
        ]
        try:
            for layer, _visible in visibility:
                layer.ViewObject.Visibility = layer is obj
            rt.helpers.settle()
            (child,) = obj.Shape.childShapes()
            face_index, point = interior_target(rt.part, child)
            view = rt.gui.activeDocument().activeView()
            area = rt.gui.getMainWindow().findChild(rt.qtwidgets.QMdiArea)
            widgets = [
                item
                for item in area.activeSubWindow().findChildren(QOpenGLWidget)
                if item.isVisible()
            ]
            assert len(widgets) == 1 and widgets[0].isValid()
            widget = widgets[0]
            x, y = view.getPointOnScreen(point)
            ratio = widget.devicePixelRatioF()
            assert math.isfinite(ratio) and ratio > 0
            target = rt.qtcore.QPoint(
                round(x / ratio),
                round((widget.height() * ratio - y - 1) / ratio),
            )
            assert widget.rect().contains(target)
            rt.gui.Selection.clearSelection()
            widget.setFocus()
            rt.qttest.QTest.mouseMove(widget, target)
            rt.helpers.settle()
            rt.qttest.QTest.mouseClick(
                widget,
                rt.qtcore.Qt.LeftButton,
                rt.qtcore.Qt.NoModifier,
                target,
            )
            rt.helpers.settle()
            check_pick(
                rt.gui.Selection.getSelectionEx("*"),
                preview.Name,
                obj.Name,
                face_index,
            )
            self.receipt["pick_witness"] = dict(
                family="XA",
                component="base_plinth",
                face_index=face_index,
                native_interior=True,
                selection_matches=True,
            )
        finally:
            for layer, visible in visibility:
                layer.ViewObject.Visibility = visible
            rt.helpers.settle()
        return obj

    def _journey(self, rt, config, selected, owned, receipt):
        from tracktemplate.compatibility.chair_reference_preview import (
            _open_source_context,
        )

        source = native().prepare_source(
            rt.app, rt.session.module, config, owned
        )
        foreign = rt.app.newDocument("TOGuiUnrelatedWitness")
        owned[foreign.Name] = foreign
        marker = foreign.addObject("App::FeaturePython", "Keep")
        marker.addProperty("App::PropertyString", "ProofValue")
        marker.ProofValue = "Preserve unrelated document"
        foreign.recompute()
        rt.app.setActiveDocument(source.Name)
        rt.gui.activeDocument().activeView().viewTop()
        rt.gui.activeDocument().activeView().fitAll()
        for document in rt.app.listDocuments().values():
            for obj in document.Objects:
                if obj.TypeId == "App::DocumentObjectGroup":
                    getattr(obj, "Shape", None)
        rt.gui.Selection.clearSelection()
        rt.gui.Selection.addSelection(marker)
        baseline = gui_helpers()._witness_baseline(rt.helpers, rt.gui, marker)
        context = _open_source_context(
            rt.session.module, source, "TO-001", "Crossings"
        )
        assert len(context[1]["positions"]) == 168
        assert (
            context[1]["geometry_signature"] == native().SOURCE_ANALYSIS_SHA256
        )
        captured = {}
        factory_name = "_private_catalogue_turnout_crossing_preview_factory"
        original = getattr(rt.session, factory_name)

        def capture(*args):
            captured.update(args[1])
            return original(*args)

        begin = time.monotonic()
        with (
            patch.object(rt.session, factory_name, capture),
            patch.object(
                rt.app,
                "openDocument",
                side_effect=AssertionError(
                    "Product reopened an external document"
                ),
            ),
        ):
            result = (
                rt.session.preview_private_catalogue_turnout_crossing_chairs(
                    source, "TO-001", config.inputs["catalogue"]["path"]
                )
            )
        receipt["stage_timings"]["successful_preview_seconds"] = (
            time.monotonic() - begin
        )
        preview = rt.app.getDocument(result["document_name"])
        assert preview is not None and preview.Name not in owned
        owned[preview.Name] = preview
        self._structure(result, preview, captured, config.fixture, receipt)
        self._source_preserved(rt, baseline, source, context, receipt)
        assert rt.helpers.state()["selection"] == baseline["selection"]
        rt.helpers.active(preview)
        receipt["renderer"] = gui_helpers()._gl_record(
            rt.app, rt.gui, rt.qtgui, rt.qtwidgets
        )
        view = rt.gui.activeDocument().activeView()
        view.viewTop()
        view.fitAll()
        self._capture(rt, config, receipt, "to-crossing-overview.png")
        for families, name in (
            (("XA", "AA"), "to-crossing-XA-AA.png"),
            (("CD", "DD"), "to-crossing-CD-DD.png"),
        ):
            rows = [
                row
                for row in config.fixture["positions"]
                if row["family"] in families
            ]
            assert len(rows) == 2
            self._focus(rt, rows)
            self._capture(rt, config, receipt, name)
        for obj in preview.Objects:
            visible = obj.ViewObject.Visibility
            assert visible is True
            obj.ViewObject.Visibility = False
            rt.helpers.settle()
            assert obj.ViewObject.Visibility is False
            obj.ViewObject.Visibility = visible
            rt.helpers.settle()
            assert obj.ViewObject.Visibility is visible
            receipt["checks"]["layer_visibility_checks"] += 1
        selected_obj = self._pick(rt, preview, config.fixture)
        receipt["checks"]["viewport_picks"] = 1
        self._capture(rt, config, receipt, "to-crossing-selected-chair.png")
        selected_obj.ViewObject.Visibility = False
        try:
            self._capture(rt, config, receipt, "to-crossing-layer-hidden.png")
            assert selected_obj.ViewObject.Visibility is False
        finally:
            selected_obj.ViewObject.Visibility = True
            rt.helpers.settle()
        self._source_preserved(rt, baseline, source, context, receipt)
        begin = time.monotonic()
        native().ToCrossingChairs._rollback(
            self,
            rt.app,
            rt.session,
            source,
            selected,
            config,
            rt.helpers.state,
            receipt,
        )
        receipt["stage_timings"]["late_rollback_seconds"] = (
            time.monotonic() - begin
        )
        receipt["checks"]["late_verifier_failures"] = 1
        self._source_preserved(rt, baseline, source, context, receipt)
        self._capture(rt, config, receipt, "to-crossing-rollback-restored.png")
        # Picking and rollback retain their own selection assertions above.
        # Establish the unrelated witness before testing preview disposal.
        rt.gui.Selection.clearSelection()
        rt.gui.Selection.addSelection(marker)
        gui_helpers()._witness_baseline(rt.helpers, rt.gui, marker)
        name = preview.Name
        rt.app.closeDocument(name)
        assert name not in rt.app.listDocuments()
        # FreeCAD 1.1.4 slotDeleteDocument clears global selection, including
        # other documents. Check that host effect and the surviving documents
        # before deliberately restoring the fixture's selection witness.
        selection = rt.helpers.state()["selection"]
        assert selection == (), selection
        self._source_preserved(rt, baseline, source, context, receipt)
        rt.app.setActiveDocument(source.Name)
        rt.gui.Selection.addSelection(marker)
        gui_helpers()._witness_baseline(rt.helpers, rt.gui, marker)
        assert rt.helpers.state()["selection"] == baseline["selection"]
        receipt["checks"]["preview_disposals"] = 1


def start():
    """Schedule one named unittest on the existing, qualified Qt event loop."""
    from PySide6 import QtCore

    def execute():
        code = 1
        test = ToCrossingGui("test_authorised_gui_stage")
        try:
            result = unittest.TextTestRunner(verbosity=2).run(
                unittest.TestSuite([test])
            )
            if (
                result.wasSuccessful()
                and result.testsRun == 1
                and not result.skipped
            ):
                receipt = test.receipt
                assert receipt["status"] == "PASS"
                print(
                    "\n"
                    + PREFIX
                    + json.dumps(receipt, sort_keys=True, allow_nan=False)
                )
                print(receipt["sentinel"])
                code = 0
        except BaseException:
            traceback.print_exc()
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            QtCore.QCoreApplication.exit(code)

    QtCore.QTimer.singleShot(0, execute)
