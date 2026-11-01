"""One import-safe L1 GUI journey; execution needs reviewed hosted authority.

The generated, hash-recorded FreeCAD macro calls ``start``. Importing this
module starts no Qt application, document, geometry or external process.
The host coordinator owns containment, deadlines and evidence preservation.
This test supplements the retained native proof; it does not repeat its
component comparisons, rollback construction or full crossover preview.
"""

from contextlib import ExitStack
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import struct
import sys
import time
import traceback
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCOPE = "L1-QUALIFICATION-001-hosted-gui-v1"
BASE = "ad554906172df31008d3a16672f392cdc6473325"
SENTINEL = "L1 current-source hosted GUI validation passed"
READINESS_SENTINEL = "L1 current-source hosted GUI readiness passed"
NATIVE_ENTRY_SHA256 = (
    "20cd1694979830099e1e6988300c1c8bc9ea1dbc59ad7a5cef1832a0fe4bcc71"
)
GUI_HELPERS = {
    "images": (
        "tests/freecad_validate_phase9b_s1_reference_preview.py",
        "caeb23ae8a01407b636ceafe2d5ec0aed647cc9c479f762824a2291e0c2494f6",
    ),
    "state": (
        "tests/freecad_validate_phase9b_chair_l1_model.py",
        "257fd6dc196e9d8a51ccc277a7c8b698ff7a66c1f241225d981d6a01651b22c6",
    ),
}
FREECAD_LIMITS = {
    "memory_max_mib": 4096, "timeout_seconds": 7200,
    "cpu_percent": 100, "tasks_max": 128,
}
DISPLAY_LIMITS = {
    "memory_max_mib": 256, "timeout_seconds": 7300,
    "cpu_percent": 25, "tasks_max": 16,
}


def validate_authority(authority, config, entry_sha256):
    """Check the recorded scope; a record itself does not grant consent."""
    stage = os.environ.get("L1_GUI_STAGE")
    assert stage in ("readiness", "gui")
    freecad_limits = dict(FREECAD_LIMITS)
    display_limits = dict(DISPLAY_LIMITS)
    if stage == "readiness":
        freecad_limits["timeout_seconds"] = 90
        display_limits["timeout_seconds"] = 190
    expected = {
        "schema": 1, "scope_id": SCOPE, "source_base_commit": BASE,
        "stage": stage,
        "owner": "Richard-Gnitnub", "execution_authorized": True,
        "independent_review": "PASS", "run_attempt": 1,
        "gui_entry_sha256": entry_sha256,
        "handling_decision": config["handling_decision"],
        "input_hashes": {
            item["id"]: item["sha256"] for item in config["inputs"]
        },
        "freecad_limits": freecad_limits, "display_limits": display_limits,
        "initial_reserve_mib": 8192, "software_renderer": "llvmpipe",
    }
    assert authority.get("execution_authorized") is True
    assert type(authority.get("run_attempt")) is int
    assert all(authority.get(key) == value for key, value in expected.items())
    assert isinstance(authority.get("decision_id"), str)
    assert authority["decision_id"].strip()
    assert authority.get("source_commit") == os.environ.get("GITHUB_SHA")
    assert os.environ.get("GITHUB_RUN_ATTEMPT") == "1"
    assert os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"


def validate_gl(record):
    """Require an actual xcb OpenGL context using the approved renderer."""
    assert record["gui_up"] is True and record["widget_valid"] is True
    assert record["platform"] == "xcb"
    assert all(isinstance(record[key], str) and record[key].strip()
               for key in ("vendor", "renderer", "version"))
    assert "llvmpipe" in record["renderer"].lower()


def check_structure(result, names, child_counts, expected_ids):
    """Reject missing, duplicate or foreign identities and display layers."""
    assert result["placement_count"] == 10
    assert result["component_count"] == 23 and result["layer_count"] == 25
    assert len(expected_ids) == len(set(expected_ids)) == 10
    observed = [item["position_id"] for item in result["placements"]]
    assert observed == sorted(expected_ids)
    components = (
        *(f"Part_{index:02d}" for index in range(7)),
        "SourceFixing", *(f"SourceFixing{index:03d}" for index in range(1, 16)),
    )
    assert tuple(names) == ("ReferenceRails", "ReferenceTimbers", *components)
    assert set(child_counts) == set(components)
    assert all(type(count) is int and count == 10
               for count in child_counts.values())
    assert result["project_status"] == "reference-only"
    assert result["production_geometry_authorized"] is False
    assert result["geometry_rebuilt"] is False
    assert result["excluded_source_components"] == []
    assert result["source_receipt"]["source_document_mutation"] is False


def check_dialog(record):
    """Require one real input, Replace confirmation and success dialog."""
    assert record["control"] == "real-GUI" and record["cancel"] is False
    assert not record["errors"] and len(record["inputs"]) == 1
    messages = record["messages"]
    assert len(messages) == 2
    assert sum(item["kind"] == "question" for item in messages) == 1
    assert sum(item["kind"] == "information" and
               "Curve and straight-track outputs created successfully"
               in item["text"] for item in messages) == 1


def _write(path, record):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _helpers(native, app, gui, qtcore, qtwidgets):
    namespace = {
        "App": app, "Gui": gui, "json": json, "hashlib": hashlib,
        "io": io, "struct": struct, "zipfile": zipfile,
    }
    with patch.dict(native.HELPERS, GUI_HELPERS):
        image_helpers = native.extract_helper(
            ROOT, "images", ("_images", "_archive_state"),
            namespace=namespace,
        )
        states = native.extract_helper(
            ROOT, "state",
            ("_settle", "_document_state", "_active_document_state"),
            namespace={**namespace,
                       "_archive_state": image_helpers["_archive_state"]},
        )
    generate = native.extract_helper(
        ROOT, "generate", ("_gui_generate",), namespace={
            "App": app, "QtCore": qtcore, "QtWidgets": qtwidgets,
            "copy": copy, "traceback": traceback,
            "old": SimpleNamespace(_write=_write),
        },
    )["_gui_generate"]

    def state():
        # Preview activation must not hide the unrelated selection witness.
        result = states["_document_state"]()
        result["selection"] = tuple(
            (item.DocumentName, item.ObjectName, tuple(item.SubElementNames))
            for item in gui.Selection.getSelectionEx("*")
        )
        return result

    return SimpleNamespace(
        images=image_helpers["_images"], generate=generate,
        settle=states["_settle"], state=state,
        active=states["_active_document_state"],
    )


def _gl_record(app, gui, qtgui, qtwidgets):
    from PySide6.QtOpenGLWidgets import QOpenGLWidget

    area = gui.getMainWindow().findChild(qtwidgets.QMdiArea)
    subwindow = area.activeSubWindow()
    assert subwindow is not None and subwindow.isVisible()
    widgets = [item for item in subwindow.findChildren(QOpenGLWidget)
               if item.isVisible()]
    assert len(widgets) == 1 and widgets[0].isValid()
    widget = widgets[0]
    widget.makeCurrent()
    try:
        context = widget.context()
        assert qtgui.QOpenGLContext.currentContext() is context
        functions = context.functions()
        record = {
            "gui_up": bool(app.GuiUp), "widget_valid": widget.isValid(),
            "platform": qtgui.QGuiApplication.platformName(),
            "vendor": functions.glGetString(0x1F00),
            "renderer": functions.glGetString(0x1F01),
            "version": functions.glGetString(0x1F02),
        }
    finally:
        widget.doneCurrent()
    validate_gl(record)
    return record


def _readiness_image(gui, qtwidgets, path):
    """Use the retained partial-update capture convention on the source."""
    from PySide6.QtOpenGLWidgets import QOpenGLWidget

    window = gui.getMainWindow()
    area = window.findChild(qtwidgets.QMdiArea)
    subwindow = area.activeSubWindow()
    assert subwindow is not None and subwindow.isVisible()
    widgets = [item for item in subwindow.findChildren(QOpenGLWidget)
               if item.isVisible()]
    assert len(widgets) == 1 and widgets[0].isValid()
    widget = widgets[0]
    behaviour = widget.updateBehavior()
    try:
        widget.setUpdateBehavior(QOpenGLWidget.PartialUpdate)
        image = window.grab()
    finally:
        widget.setUpdateBehavior(behaviour)
    assert widget.updateBehavior() == behaviour
    assert not image.isNull() and image.save(str(path))
    return {"path": path.name, "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _preserved(before, after):
    """Compare every pre-existing document, including native/view archives."""
    current = {item["name"]: item for item in after["documents"]}
    assert all(current.get(item["name"]) == item
               for item in before["documents"])
    assert after["selection"] == before["selection"]


def _witness_baseline(helpers, gui, marker):
    """Capture the unrelated selection witness before chair preview."""
    helpers.settle()
    assert gui.Selection.getSelection("*") == [marker]
    baseline = helpers.state()
    assert baseline["selection"] == ((marker.Document.Name, marker.Name, ()),)
    return baseline


class L1Gui(unittest.TestCase):
    """Exercise the actual ten-chair command in one fresh GUI process."""

    def test_authorised_gui_stage(self):
        import hosted_l1_current_source_suite as native

        assert native.sha256(
            ROOT / "tests/hosted_l1_current_source_suite.py",
        ) == NATIVE_ENTRY_SHA256
        config, root, inputs, evidence, expected = native.load_configuration()
        assert root == ROOT
        authority_path = native.regular_path(
            os.environ["TRACKTEMPLATE_L1_GUI_AUTHORITY"],
        )
        assert native.sha256(authority_path) == os.environ[
            "TRACKTEMPLATE_L1_GUI_AUTHORITY_SHA256"
        ]
        authority = json.loads(authority_path.read_text())
        validate_authority(authority, config, native.sha256(Path(__file__)))
        stage = authority["stage"]
        sentinel = READINESS_SENTINEL if stage == "readiness" else SENTINEL
        directory = evidence / "gui"
        directory.mkdir(mode=0o700)
        started = time.monotonic()
        receipt = {
            "status": "RUNNING", "stage": stage, "scope_id": SCOPE,
            "profile": native.PROFILE, "gui": True, "cases": [],
            "visual_review": "REQUIRED", "physical_fit": "NOT_PROVED",
            "native_evidence_reused": authority["prior_native_evidence"],
            "source_commit": authority["source_commit"],
        }
        app = None
        owned = {}
        failure = None
        try:
            import FreeCAD as app
            import FreeCADGui as gui
            from PySide6 import QtCore, QtGui, QtWidgets

            assert app.GuiUp and not app.listDocuments()
            assert QtGui.QGuiApplication.platformName() == "xcb"
            assert gui.getMainWindow().isVisible()
            sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
            with (patch.object(app, "newDocument", side_effect=AssertionError(
                    "foundation opened a document")),
                  patch.object(app, "openDocument", side_effect=AssertionError(
                      "foundation restored a document"))):
                launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
                assert launcher["FOUNDATION_RESULT"]["matched_profile_id"] == (
                    native.PROFILE
                )
                api, bootstrap = launcher["_load_foundation"](ROOT)
                session, routing = launcher["_load_modular_transition_workflow"](
                    ROOT, api, bootstrap,
                )
                helpers = _helpers(native, app, gui, QtCore, QtWidgets)
                selected = native.catalogue_contract(inputs)
            receipt["routing"] = routing
            assert not app.listDocuments()
            receipt["pre_geometry_readiness_seconds"] = (
                time.monotonic() - started
            )
            self._journey(native, app, gui, QtGui, QtWidgets, session,
                          helpers, selected, inputs, expected, directory,
                          owned, receipt)
        except BaseException as error:
            failure = error
            receipt["traceback"] = traceback.format_exc()
        finally:
            cleanup_errors = []
            try:
                assert all(native.bound_file(record)
                           for record in inputs.values())
                receipt["input_bindings_unchanged"] = True
            except BaseException:
                receipt["input_bindings_unchanged"] = False
                cleanup_errors.append(traceback.format_exc())
            if app is not None:
                for name, document in reversed(tuple(owned.items())):
                    try:
                        current = app.listDocuments().get(name)
                        if current is not None:
                            assert current is document
                            app.closeDocument(name)
                        assert name not in app.listDocuments()
                    except BaseException:
                        cleanup_errors.append(traceback.format_exc())
                if app.listDocuments() or app.ActiveDocument is not None:
                    cleanup_errors.append("document registry not empty")
            receipt["cleanup_errors"] = cleanup_errors
            receipt["owned_documents_closed"] = (
                app is not None and not cleanup_errors
            )
            receipt["total_seconds"] = time.monotonic() - started
            if cleanup_errors and failure is None:
                failure = AssertionError("GUI document cleanup unproved")
            receipt["status"] = "PASS" if failure is None else "FAIL"
            if failure is None:
                receipt["sentinel"] = sentinel
            native.write_private_result(directory, receipt)
        if failure is not None:
            raise failure
        print("\n" + sentinel, flush=True)

    def _journey(self, native, app, gui, qtgui, qtwidgets, session, helpers,
                 selected, inputs, expected, directory, owned, receipt):
        from tracktemplate.adapters.freecad import chair_reference_preview

        module = session.module
        target = directory / "XO-001-copy.FCStd"
        assert not target.exists()
        shutil.copyfile(inputs["reference_document"]["path"], target)
        target.chmod(0o600)
        assert native.sha256(target) == inputs["reference_document"]["sha256"]
        source = app.openDocument(str(target))
        assert source is not None
        owned[source.Name] = source
        app.setActiveDocument(source.Name)
        helpers.settle()
        receipt["renderer"] = _gl_record(app, gui, qtgui, qtwidgets)
        if receipt["stage"] == "readiness":
            receipt["screenshots"] = [_readiness_image(
                gui, qtwidgets, directory / "readiness-source.png",
            )]
            receipt["successful_preview_component_placements"] = 0
            receipt["generate_operations"] = 0
            receipt["source_copy_only"] = True
            receipt["pre_geometry_readiness"] = True
            return
        original = copy.deepcopy(module.crossover_config_by_id(source, "XO-001"))
        foreign = app.newDocument("L1GuiUnrelatedWitness")
        owned[foreign.Name] = foreign
        marker = foreign.addObject("App::FeaturePython", "Keep")
        marker.addProperty("App::PropertyString", "ProofValue")
        marker.ProofValue = "Preserve unrelated document"
        foreign.recompute()
        previews = []
        for label, radius, _analysis_count in native.CASES:
            case_started = time.monotonic()
            case_dir = directory / label
            case_dir.mkdir(mode=0o700)
            item = {"case": label, "radius_mm": radius}
            receipt["cases"].append(item)
            helpers.settle()
            before_generate = helpers.state()
            registry = dict(app.listDocuments())
            with ExitStack() as stack:
                for name in vars(session):
                    if name.endswith("_preview_factory"):
                        stack.enter_context(patch.object(
                            session, name,
                            side_effect=AssertionError("eager chair creation"),
                        ))
                stack.enter_context(patch.object(
                    app, "newDocument",
                    side_effect=AssertionError("unexpected document"),
                ))
                item["generate"] = helpers.generate(
                    module, source, radius, case_dir,
                )
            check_dialog(item["generate"])
            assert dict(app.listDocuments()) == registry
            helpers.settle()
            after_generate = helpers.state()
            protected = {doc.Name for doc in (foreign, *previews)}
            assert [row for row in before_generate["documents"]
                    if row["name"] in protected] == [
                        row for row in after_generate["documents"]
                        if row["name"] in protected
                    ]
            config = module.crossover_config_by_id(source, "XO-001")
            for field in (
                "crossover_id", "host_a_object", "host_b_object",
                "reference_chainage", "arrangement", "handing",
                "track_gauge", "flangeway", "minimum_requested_radius",
                "toe_chainage_a", "template_set_id", "shared_timber_settings",
                "b3_settings", "b4_settings", "chair_analysis_settings",
            ):
                assert config[field] == original[field], field
            assert config["integration_active"] is True
            assert config["production_ready"] is False
            assert config["minimum_resulting_radius"] >= config[
                "minimum_requested_radius"
            ]
            assert module.quantity_value(
                module.latest_generated_settings(source), "CurveRadius", -1,
            ) == radius
            app.setActiveDocument(source.Name)
            gui.Selection.clearSelection()
            gui.Selection.addSelection(marker)
            baseline = _witness_baseline(helpers, gui, marker)
            preselection = chair_reference_preview._preselection_snapshot(
                app, gui,
            )
            captured = []
            create = session._private_catalogue_l1_preview_factory

            def capture(*args):
                captured.extend(args[1])
                return create(*args)

            with (patch.object(session, "_private_catalogue_l1_preview_factory",
                               capture),
                  patch.object(app, "openDocument", side_effect=AssertionError(
                      "product restored an external document"))):
                result = session.preview_private_catalogue_heel_l1_chairs(
                    source, "XO-001", inputs["catalogue"]["path"],
                )
            preview = app.getDocument(result["document_name"])
            assert preview is not None and preview.Name not in owned
            owned[preview.Name] = preview
            previews.append(preview)
            helpers.settle()
            item["active_document"] = helpers.active(preview)
            _preserved(baseline, helpers.state())
            assert chair_reference_preview._preselection_snapshot(
                app, gui,
            ) == preselection
            _write(case_dir / "before-preview.json", baseline)
            _write(case_dir / "after-preview.json", helpers.state())
            assert not preview.FileName and not preview.Temporary
            assert result["source_model_sha256"] == selected.model_sha256
            counts = {name: len(preview.getObject(name).Shape.childShapes())
                      for name in native.COMPONENT_NAMES}
            check_structure(result, [obj.Name for obj in preview.Objects],
                            counts, list(expected[label]))
            assert len(captured) == 10
            assert {p.position_id for p in captured} == set(expected[label])
            for placement in captured:
                record = expected[label][placement.position_id]
                assert (placement.rail_id, placement.timber_id) == (
                    record["rail_id"], record["timber_id"],
                )
                native.compare_frame(placement, record["body"])
            item["body_frame_comparisons"] = 10
            item["preview"] = result
            item["opengl"] = _gl_record(app, gui, qtgui, qtwidgets)
            for obj in preview.Objects:
                assert obj.ViewObject.Visibility
                gui.Selection.clearSelection()
                gui.Selection.addSelection(obj)
                assert gui.Selection.getSelection() == [obj]
                obj.ViewObject.Visibility = False
                helpers.settle()
                assert not obj.ViewObject.Visibility
                obj.ViewObject.Visibility = True
                helpers.settle()
                assert obj.ViewObject.Visibility
            gui.Selection.clearSelection()
            item["layer_visibility_selection_checks"] = 25
            view = gui.getDocument(preview.Name).activeView()
            animation = view.isAnimationEnabled()
            images = []
            try:
                view.setAnimationEnabled(False)
                for index, identity in enumerate(native.REPRESENTATIVES):
                    image_dir = case_dir / ("representative-" + str(index))
                    image_dir.mkdir(mode=0o700)
                    frame = SimpleNamespace(
                        position_id=identity, **expected[label][identity]["body"],
                    )
                    files = helpers.images(preview, (frame,), image_dir)
                    assert files == ["overview.png", "chair-closeup.png"]
                    for name in files:
                        image_path = image_dir / name
                        images.append({
                            "path": str(image_path.relative_to(directory)),
                            "sha256": native.sha256(image_path),
                            "bytes": image_path.stat().st_size,
                            "position_id": identity,
                        })
            finally:
                view.setAnimationEnabled(animation)
            assert view.isAnimationEnabled() == animation
            helpers.active(preview)
            # Inspection changes only preview state and selection deliberately.
            after_inspection = helpers.state()
            previous = {row["name"]: row
                        for row in after_inspection["documents"]}
            assert all(previous[row["name"]] == row
                       for row in baseline["documents"])
            item["images"] = images
            item["successful_preview_component_placements"] = sum(counts.values())
            item["seconds"] = time.monotonic() - case_started
        assert len(receipt["cases"]) == 3
        receipt["body_frame_comparisons"] = 30
        receipt["layer_visibility_selection_checks"] = 75
        receipt["successful_preview_component_placements"] = 690
        receipt["preview_image_count"] = 12
        receipt["dialog_image_count"] = 3
        receipt["generate_operations"] = 3
        receipt["screenshots"] = [
            image for item in receipt["cases"] for image in item["images"]
        ]
        for label, _radius, _count in native.CASES:
            image_path = directory / label / "radius-input.png"
            receipt["screenshots"].append({
                "path": str(image_path.relative_to(directory)),
                "sha256": native.sha256(image_path),
                "bytes": image_path.stat().st_size,
            })
        assert sum(len(item["images"]) for item in receipt["cases"]) == 12
        assert sum(item["successful_preview_component_placements"]
                   for item in receipt["cases"]) == 690
        assert all((directory / label / "radius-input.png").is_file()
                   for label, _radius, _count in native.CASES)
        helpers.settle()
        before_disposal = helpers.state()
        keep = {source.Name, foreign.Name}
        preserved = [row for row in before_disposal["documents"]
                     if row["name"] in keep]
        for preview in reversed(previews):
            app.closeDocument(preview.Name)
        helpers.settle()
        assert [row for row in helpers.state()["documents"]
                if row["name"] in keep] == preserved
        receipt["source_and_foreign_preserved"] = True
        receipt["no_eager_chairs"] = True


def start():
    """Schedule exactly one unittest after FreeCAD's GUI loop is running."""
    from PySide6 import QtCore

    def execute():
        code = 1
        try:
            suite = unittest.TestSuite([
                L1Gui("test_authorised_gui_stage"),
            ])
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            code = 0 if (result.wasSuccessful() and result.testsRun == 1
                         and not result.skipped) else 1
        except BaseException:
            traceback.print_exc()
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            QtCore.QCoreApplication.exit(code)

    QtCore.QTimer.singleShot(0, execute)
