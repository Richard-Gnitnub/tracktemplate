"""Import-safe, separately authorised GUI proof of the fixed TO chair preview.

The reviewed macro calls start once. The external hosted coordinator owns
limits, recovery, input handling and process cleanup. This entry supplements
the native proof; it does not repeat native component comparisons or expose
a new operator command.
"""

from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import sys
import time
import traceback
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCOPE = "TO-001-fixed-single-rail-gui-v1"
BASE = "7fa2a5a1bd637cf2c3847ec5e35dc35bd04eed77"
PREFIX = "TRACKTEMPLATE_TO_SINGLE_GUI="
NATIVE_PATH = "tests/freecad_validate_to_single_rail.py"
NATIVE_SHA256 = (
    "6288286b9b7c45ec26df4cf3d2b891ae59548bab4cc5b3ab92a103fa54d627c0"
)
GUI_HELPER = "tests/hosted_l1_gui_suite.py"
GUI_HELPER_SHA256 = (
    "1150aab0a68d75a9048bbfd096f60f270d8f452c7333ab692ba063fd878e7012"
)


def native():
    path = ROOT / NATIVE_PATH
    assert hashlib.sha256(path.read_bytes()).hexdigest() == NATIVE_SHA256
    import freecad_validate_to_single_rail as module

    assert Path(module.__file__).resolve() == path
    return module


def gui_helpers():
    path = ROOT / GUI_HELPER
    assert hashlib.sha256(path.read_bytes()).hexdigest() == GUI_HELPER_SHA256
    import hosted_l1_gui_suite as module

    assert Path(module.__file__).resolve() == path
    return module


def sentinel(stage):
    assert stage in ("readiness", "gui")
    return (
        "Fixed TO single-rail hosted GUI readiness passed"
        if stage == "readiness"
        else "Fixed TO single-rail hosted GUI validation passed"
    )


def image_names(stage):
    assert stage in ("readiness", "gui")
    if stage == "readiness":
        return ("to-single-readiness.png",)
    return (
        "to-single-overview.png",
        "to-corrected-heels.png",
        "to-retained-placements.png",
        "to-selected-chair.png",
        "to-chair-layer-hidden.png",
        "to-rollback-restored.png",
    )


def limits(stage):
    assert stage in ("readiness", "gui")
    return (
        dict(
            memory_max_mib=4096,
            timeout_seconds=(90 if stage == "readiness" else 7200),
            cpu_percent=100,
            tasks_max=128,
        ),
        dict(
            memory_max_mib=256,
            timeout_seconds=(190 if stage == "readiness" else 7300),
            cpu_percent=25,
            tasks_max=16,
        ),
    )


def expected_checks(stage):
    assert stage in ("readiness", "gui")
    checks = dict(
        binding_checks=1,
        catalogue_contracts=2,
        source_frame_inputs=59,
        source_frame_comparisons=59,
        successful_previews=1,
        assemblies=12,
        layers=42,
        successful_components=270,
        layer_visibility_checks=42,
        viewport_picks=1,
        late_verifier_failures=1,
        rolled_back_components=270,
        source_preservation_checks=4,
        preview_disposals=1,
        screenshots=6,
        readiness_empty_documents=0,
    )
    if stage == "readiness":
        checks = dict.fromkeys(checks, 0)
        checks.update(
            binding_checks=1,
            catalogue_contracts=2,
            source_frame_inputs=59,
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
    return type(value) is str and re.fullmatch("[0-9a-f]{64}", value)


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
            source_commit=config.source_commit,
            entry_sha256=NATIVE_SHA256,
            input_hashes=expected["input_hashes"],
            scope_id=native().SCOPE,
            tests=1,
            skips=0,
            run_attempt=1,
            cleanup=True,
            evidence_verified=True,
            independent_preservation=True,
            source_frame_comparisons=59,
            component_comparisons=270,
            successful_components=270,
            rolled_back_components=270,
        ),
    )
    assert type(proof.get("run_id")) is int and proof["run_id"] > 0
    assert str(proof["run_id"]) != os.environ["GITHUB_RUN_ID"]
    assert _hash(proof.get("evidence_sha256"))
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


def runtime():
    import FreeCAD as app
    import FreeCADGui as gui
    import Part
    from PySide6 import QtCore, QtGui, QtWidgets, QtTest

    assert app.GuiUp and not app.listDocuments()
    assert app.ActiveDocument is None
    assert QtGui.QGuiApplication.platformName() == "xcb"
    assert gui.getMainWindow().isVisible()
    with ExitStack() as guards:
        for owner, name in (
            (app, "newDocument"),
            (app, "openDocument"),
            (Part, "Shape"),
            (Part, "makeCompound"),
        ):
            guards.enter_context(
                patch.object(
                    owner,
                    name,
                    side_effect=(
                        AssertionError(
                            "Foundation constructed document or geometry"
                        )
                    ),
                )
            )
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        assert launcher["FOUNDATION_RESULT"]["matched_profile_id"] == (
            native().shared().PROFILE
        )
        api, bootstrap = launcher["_load_foundation"](ROOT)
        session, _routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, bootstrap
        )
        helpers = gui_helpers()._helpers(
            native().shared(), app, gui, QtCore, QtWidgets
        )
    return SimpleNamespace(
        app=app,
        gui=gui,
        part=Part,
        qtcore=QtCore,
        qtgui=QtGui,
        qtwidgets=QtWidgets,
        qttest=QtTest,
        session=session,
        helpers=helpers,
    )


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
        assert set(selected) == {"L1", "S1"}
        receipt["checks"]["catalogue_contracts"] = len(selected)
        receipt["checks"]["source_frame_inputs"] = native().validate_fixture(
            config.fixture
        )
    assert not rt.app.listDocuments() and rt.app.ActiveDocument is None
    return selected


def check_image(directory, record, name):
    assert type(record) is dict and set(record) == {"path", "bytes", "sha256"}
    assert record["path"] == name and Path(name).name == name
    path = directory / name
    assert path.is_file() and not path.is_symlink()
    assert type(record["bytes"]) is int and record["bytes"] > 8
    content = path.read_bytes()
    assert (
        len(content) == record["bytes"] and content[:8] == b"\x89PNG\r\n\x1a\n"
    )
    assert hashlib.sha256(content).hexdigest() == record["sha256"]


def compare_frames(placements, fixture):
    expected = {row["position_id"]: row for row in fixture["positions"]}
    assert [value.position_id for value in placements] == sorted(expected)
    count = 0
    for actual in placements:
        row = expected[actual.position_id]
        assert (actual.family, actual.rail_id, actual.timber_id) == (
            row["family"],
            row["rail_id"],
            row["timber_id"],
        )
        assert len(actual.fixing_frames) == len(row["fixing_frames"])
        for frame, target in zip(
            (actual, *actual.fixing_frames),
            (row["body"], *row["fixing_frames"]),
        ):
            native().shared().compare_frame(frame, target)
            count += 1
    assert count == 59
    return count


def check_pick(rows, document, obj, first_face, last_face):
    assert len(rows) == 1
    row = rows[0]
    assert (row.DocumentName, row.ObjectName) == (document, obj)
    assert len(row.SubElementNames) == 1
    match = re.fullmatch(r"Face([1-9][0-9]*)", row.SubElementNames[0])
    assert match and first_face <= int(match.group(1)) <= last_face


def finish(rt, config, owned, receipt):
    """Attempt owned cleanup even when input preservation has failed."""
    errors = []
    try:
        native().verify_inputs(config.inputs)
        receipt["input_bindings_unchanged"] = True
    except BaseException as error:
        receipt["input_bindings_unchanged"] = False
        receipt["input_traceback"] = traceback.format_exc()
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
        receipt["cleanup_traceback"] = traceback.format_exc()
        errors.append(error)
    receipt["cleanup_errors"] = [
        type(error).__name__ + ": " + str(error) for error in errors
    ]
    return errors


class ToSingleRailGui(unittest.TestCase):
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
            native_evidence_reused=authority["prior_native_evidence"],
            checks=dict.fromkeys(expected_checks(stage), 0),
            input_sha256=dict(native().INPUT_HASHES),
            stage_timings={},
            screenshots=[],
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
            receipt["traceback"] = traceback.format_exc()
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
            raise failure

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
        assert (
            result["placement_count"],
            result["component_count"],
            result["family_count"],
            result["layer_count"],
        ) == (12, 40, 2, 42)
        assert result["project_status"] == "reference-only"
        assert result["intended_uses"] == ["private-development"]
        assert result["production_geometry_authorized"] is False
        assert result["geometry_rebuilt"] is False
        assert not preview.FileName and not preview.Temporary
        source = result["source_receipt"]
        assert source["source_document_mutation"] is False
        assert source["model_support_adjustments_applied"] is False
        assert source["analysis_position_count"] == 168
        assert source["represented_source_position_count"] == 12
        assert source["selected_family_counts"] == {"L1": 11, "S1": 1}
        assert len(source["corrected_heel_positions"]) == 5
        assert len(source["remaining_positions"]) == 156
        counts = {}
        for family in ("L1", "S1"):
            family_receipt = result["families"][family]
            assert (
                family_receipt["source_model_sha256"]
                == fixture["model_sha256"][family]
            )
            assert family_receipt["excluded_source_components"] == []
            rows = [
                row for row in fixture["positions"] if row["family"] == family
            ]
            assert [
                row["position_id"] for row in family_receipt["placements"]
            ] == [row["position_id"] for row in rows]
            for name in native().component_names(family):
                layer = family + "_" + name
                counts[layer] = len(
                    preview.getObject(layer).Shape.childShapes()
                )
        checks = receipt["checks"]
        checks["successful_components"] = native().check_layers(
            [obj.Name for obj in preview.Objects], counts
        )
        checks["source_frame_comparisons"] = compare_frames(captured, fixture)
        checks.update(successful_previews=1, assemblies=12, layers=42)

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
            _open_source_context(rt.session.module, source, "TO-001", "L1/S1")
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

        rows = [row for row in fixture["positions"] if row["family"] == "L1"]
        index = next(
            index
            for index, row in enumerate(rows)
            if row["timber_id"] == "TO-001:timber:S13"
            and row["source_rail_code"] == 1
        )
        self._focus(rt, [rows[index]])
        obj = preview.getObject("L1_Part_00")
        visibility = [
            (layer, layer.ViewObject.Visibility) for layer in preview.Objects
        ]
        try:
            for layer, _ in visibility:
                layer.ViewObject.Visibility = layer is obj
            rt.helpers.settle()
            children = obj.Shape.childShapes()
            child = children[index]
            face = max(child.Faces, key=lambda value: value.CenterOfMass.z)
            point = face.CenterOfMass
            first = 1 + sum(len(shape.Faces) for shape in children[:index])
            last = first + len(child.Faces) - 1
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
                first,
                last,
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
            rt.session.module, source, "TO-001", "L1/S1"
        )
        assert len(context[1]["positions"]) == 168
        assert (
            context[1]["geometry_signature"]
            == config.fixture["source_analysis_sha256"]
        )
        captured = []
        factory_name = "_private_catalogue_turnout_single_rail_preview_factory"
        original = getattr(rt.session, factory_name)

        def capture(*args):
            captured.extend(args[1])
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
            result = rt.session.preview_private_catalogue_turnout_single_rail_chairs(
                source, "TO-001", config.inputs["catalogue"]["path"]
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
        self._capture(rt, config, receipt, "to-single-overview.png")
        corrected = config.fixture["source_receipt_sha256"]["corrected_five"]
        for corrected_group, name in (
            (True, "to-corrected-heels.png"),
            (False, "to-retained-placements.png"),
        ):
            rows = [
                row
                for row in config.fixture["positions"]
                if (row["source_receipt_sha256"] == corrected)
                is corrected_group
            ]
            assert len(rows) == (5 if corrected_group else 7)
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
        self._capture(rt, config, receipt, "to-selected-chair.png")
        selected_obj.ViewObject.Visibility = False
        try:
            self._capture(rt, config, receipt, "to-chair-layer-hidden.png")
            assert selected_obj.ViewObject.Visibility is False
        finally:
            selected_obj.ViewObject.Visibility = True
            rt.helpers.settle()
        self._source_preserved(rt, baseline, source, context, receipt)
        begin = time.monotonic()
        native().ToSingleRail._rollback(
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
        self._capture(rt, config, receipt, "to-rollback-restored.png")
        # Picking and rollback retain their own selection assertions above.
        # Establish the unrelated witness before testing preview disposal.
        rt.gui.Selection.clearSelection()
        rt.gui.Selection.addSelection(marker)
        disposal = gui_helpers()._witness_baseline(rt.helpers, rt.gui, marker)
        name = preview.Name
        rt.app.closeDocument(name)
        assert name not in rt.app.listDocuments()
        assert rt.helpers.state()["selection"] == disposal["selection"]
        rt.app.setActiveDocument(source.Name)
        gui_helpers()._witness_baseline(rt.helpers, rt.gui, marker)
        self._source_preserved(rt, baseline, source, context, receipt)
        assert rt.helpers.state()["selection"] == baseline["selection"]
        receipt["checks"]["preview_disposals"] = 1


def start():
    """Schedule one named unittest on the existing, qualified Qt event loop."""
    from PySide6 import QtCore

    def execute():
        code = 1
        test = ToSingleRailGui("test_authorised_gui_stage")
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
