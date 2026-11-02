#!/usr/bin/env python3
"""Exercise the bounded TO GUI entry without FreeCAD, Part or Qt."""

import ast
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

import freecad_validate_to_single_rail_gui as entry  # noqa: E402


SENTINEL = "Fixed TO single-rail GUI entry offline checks passed"


def authority(stage="readiness"):
    record = dict(
        schema=1,
        scope_id=entry.SCOPE,
        stage=stage,
        source_base_commit=entry.BASE,
        source_commit="1" * 40,
        owner="Richard-Gnitnub",
        execution_authorized=True,
        independent_review="PASS",
        run_attempt=1,
        gui_entry_sha256="2" * 64,
        native_entry_sha256=entry.NATIVE_SHA256,
        handling_decision="reviewed-handling",
        input_hashes=dict(entry.native().INPUT_HASHES),
        freecad_limits=entry.limits(stage)[0],
        display_limits=entry.limits(stage)[1],
        initial_reserve_mib=8192,
        software_renderer="llvmpipe",
        decision_id="reviewed-decision",
    )
    record["publication_review"] = dict(
        status="PASS",
        independent_review="PASS",
        input_hashes=record["input_hashes"],
        handling_decision=record["handling_decision"],
        evidence_sha256="3" * 64,
        publication_basis="reviewed-basis",
    )
    record["prior_native_evidence"] = dict(
        status="PASS",
        independent_review="PASS",
        source_commit=record["source_commit"],
        entry_sha256=entry.NATIVE_SHA256,
        input_hashes=record["input_hashes"],
        cleanup=True,
        independent_preservation=True,
        evidence_sha256="4" * 64,
        scope_id=entry.native().SCOPE,
        tests=1,
        skips=0,
        run_attempt=1,
        evidence_verified=True,
        run_id=123,
        source_frame_comparisons=59,
        component_comparisons=270,
        successful_components=270,
        rolled_back_components=270,
    )
    record["gui_readiness_review"] = dict(
        status="PASS",
        independent_review="PASS",
        source_commit=record["source_commit"],
        gui_entry_sha256="2" * 64,
        input_hashes=record["input_hashes"],
        tests=1,
        skips=0,
        cleanup=True,
        independent_preservation=True,
        run_id=124,
    )
    return record


class GuiEntryTests(unittest.TestCase):
    def test_import_and_named_discovery_are_host_free(self):
        for name in ("FreeCAD", "FreeCADGui", "Part", "PySide6"):
            self.assertNotIn(name, sys.modules)
        self.assertEqual(
            unittest.defaultTestLoader.getTestCaseNames(entry.ToSingleRailGui),
            ["test_authorised_gui_stage"],
        )
        suite = unittest.defaultTestLoader.loadTestsFromName(
            "ToSingleRailGui.test_authorised_gui_stage", entry
        )
        self.assertEqual(suite.countTestCases(), 1)

    def test_frozen_native_fixture_and_gui_helpers(self):
        self.assertEqual(
            entry.native().validate_fixture(entry.native().read_fixture()), 59
        )
        self.assertEqual(
            Path(entry.gui_helpers().__file__).resolve(),
            ROOT / entry.GUI_HELPER,
        )
        self.assertEqual(
            hashlib.sha256(
                (ROOT / entry.NATIVE_PATH).read_bytes()
            ).hexdigest(),
            entry.NATIVE_SHA256,
        )

    def test_authority_requires_exact_source_proof_scope_and_limits(self):
        config = SimpleNamespace(source_commit="1" * 40)
        environment = dict(
            GITHUB_SHA="1" * 40,
            GITHUB_RUN_ATTEMPT="1",
            GITHUB_RUN_ID="125",
            GITHUB_ACTIONS="true",
            RUNNER_ENVIRONMENT="github-hosted",
        )
        for stage in ("readiness", "gui"):
            with patch.dict(entry.os.environ, environment):
                entry.validate_authority(authority(stage), config, "2" * 64)
                for key, value in (
                    ("scope_id", entry.native().SCOPE),
                    ("source_commit", None),
                    ("gui_entry_sha256", "x" * 64),
                    ("native_entry_sha256", "x" * 64),
                    ("run_attempt", True),
                    ("execution_authorized", False),
                    ("independent_review", "PENDING"),
                    ("stage", "native"),
                    ("freecad_limits", {}),
                    ("display_limits", {}),
                    ("input_hashes", {}),
                    ("prior_native_evidence", {}),
                    ("publication_review", {}),
                ):
                    candidate = copy.deepcopy(authority(stage))
                    candidate[key] = value
                    with self.subTest(stage=stage, key=key):
                        with self.assertRaises((AssertionError, ValueError)):
                            entry.validate_authority(
                                candidate, config, "2" * 64
                            )
                if stage == "gui":
                    candidate = authority(stage)
                    candidate["gui_readiness_review"] = {}
                    with self.assertRaises(AssertionError):
                        entry.validate_authority(candidate, config, "2" * 64)

    def test_exact_counts_and_image_scopes(self):
        self.assertEqual(len(entry.expected_checks("gui")), 16)
        self.assertEqual(
            entry.expected_checks("gui")["successful_components"], 270
        )
        self.assertEqual(
            entry.expected_checks("gui")["rolled_back_components"], 270
        )
        for stage, number in (("readiness", 1), ("gui", 6)):
            checks = entry.expected_checks(stage)
            entry.check_counts(checks, stage)
            self.assertEqual(len(entry.image_names(stage)), number)
            for key in checks:
                changed = dict(checks, **{key: True})
                with self.subTest(key=key), self.assertRaises(AssertionError):
                    entry.check_counts(changed, stage)
        with self.assertRaises(AssertionError):
            entry.expected_checks("native")

    def test_images_reject_unknown_paths_symlinks_or_invalid_png(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            name = entry.image_names("readiness")[0]
            path = root / name
            path.write_bytes(b"\x89PNG\r\n\x1a\nactual-capture")
            record = dict(
                path=name,
                bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            entry.check_image(root, record, name)
            for key, value in (
                ("path", "../" + name),
                ("bytes", True),
                ("sha256", "0" * 64),
            ):
                with self.subTest(key=key), self.assertRaises(AssertionError):
                    entry.check_image(root, dict(record, **{key: value}), name)
            other = root / "link.png"
            other.symlink_to(path)
            with self.assertRaises(AssertionError):
                entry.check_image(
                    root, dict(record, path="link.png"), "link.png"
                )
            path.write_bytes(b"not a PNG")
            record.update(
                bytes=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            with self.assertRaises(AssertionError):
                entry.check_image(root, record, name)

    def test_independent_frames_reject_changed_identity_or_frame(self):
        fixture = entry.native().read_fixture()
        placements = []
        for row in fixture["positions"]:
            placements.append(
                SimpleNamespace(
                    position_id=row["position_id"],
                    family=row["family"],
                    rail_id=row["rail_id"],
                    timber_id=row["timber_id"],
                    **row["body"],
                    fixing_frames=tuple(
                        SimpleNamespace(**frame)
                        for frame in row["fixing_frames"]
                    ),
                )
            )
        self.assertEqual(entry.compare_frames(placements, fixture), 59)
        changed = copy.deepcopy(placements)
        changed[0].origin_mm[0] += 1
        with self.assertRaises(AssertionError):
            entry.compare_frames(changed, fixture)
        with self.assertRaises(AssertionError):
            entry.compare_frames(placements[::-1], fixture)

    def test_actual_pick_rejects_wrong_object_face_and_ambiguity(self):
        def picked(doc="Preview", obj="L1_Part_00", sub=("Face5",)):
            return SimpleNamespace(
                DocumentName=doc, ObjectName=obj, SubElementNames=sub
            )

        entry.check_pick([picked()], "Preview", "L1_Part_00", 4, 9)
        for rows in (
            [],
            [picked(), picked()],
            [picked(doc="Source")],
            [picked(obj="ReferenceRails")],
            [picked(sub=("Face3",))],
            [picked(sub=("Edge5",))],
            [picked(sub=())],
            [picked(sub=("Face5", "Face6"))],
        ):
            with self.subTest(rows=rows), self.assertRaises(AssertionError):
                entry.check_pick(rows, "Preview", "L1_Part_00", 4, 9)

    def test_readiness_uses_real_public_composition_without_geometry(self):
        from validate_to_single_rail_native_entry import composed_session
        from tracktemplate.compatibility.transition_workflow import (
            TransitionWorkflowError,
        )

        def run_ready(session):
            documents, receipts = {}, []
            app = SimpleNamespace(
                openDocument=Mock(),
                listDocuments=lambda: dict(documents),
                ActiveDocument=None,
            )

            def create(name):
                document = SimpleNamespace(Name=name, Objects=[])
                documents[name] = document
                app.ActiveDocument = document
                return document

            def close(name):
                documents.pop(name)
                app.ActiveDocument = None

            app.newDocument, app.closeDocument = (
                Mock(side_effect=create),
                close,
            )
            gui = SimpleNamespace(
                activeDocument=lambda: None,
                ActiveDocument=None,
                Selection=SimpleNamespace(clearSelection=Mock()),
            )
            part = SimpleNamespace(Shape=Mock(), makeCompound=Mock())
            rt = SimpleNamespace(
                app=app,
                gui=gui,
                part=part,
                session=session,
                qtgui=object(),
                qtwidgets=object(),
                helpers=SimpleNamespace(settle=lambda: None),
            )
            config = SimpleNamespace(
                inputs={},
                fixture=entry.native().read_fixture(),
                source_commit="1" * 40,
            )
            case = entry.ToSingleRailGui("test_authorised_gui_stage")

            def capture(_rt, _config, receipt, name):
                receipt["screenshots"].append(dict(path=name))
                receipt["checks"]["screenshots"] += 1

            with (
                patch.object(
                    entry, "configuration", return_value=(config, authority())
                ),
                patch.object(entry, "runtime", return_value=rt),
                patch.object(
                    entry.native(),
                    "catalogues",
                    return_value={"L1": object(), "S1": object()},
                ),
                patch.object(entry.native(), "verify_inputs"),
                patch.object(
                    entry.native(),
                    "write_result",
                    side_effect=lambda _, value: receipts.append(
                        copy.deepcopy(value)
                    ),
                ),
                patch.object(
                    entry.gui_helpers(),
                    "_gl_record",
                    return_value={"renderer": "llvmpipe"},
                ),
                patch.object(case, "_capture", side_effect=capture),
            ):
                try:
                    case.test_authorised_gui_stage()
                finally:
                    self.assertFalse(documents)
                    self.assertEqual(len(receipts), 1)
                    self.assertTrue(receipts[0]["owned_documents_closed"])
                    app.openDocument.assert_not_called()
                    part.Shape.assert_not_called()
                    part.makeCompound.assert_not_called()
            self.assertEqual(app.newDocument.call_count, 1)
            self.assertEqual(
                receipts[0]["checks"], entry.expected_checks("readiness")
            )
            self.assertEqual(receipts[0]["status"], "PASS")
            return receipts[0]

        with composed_session() as session:
            run_ready(session)
        for name in ("build_concentric_core", "run_production_export"):
            with self.subTest(name=name), composed_session() as session:
                setattr(session.module, name, lambda *_: None)
                with self.assertRaises(TransitionWorkflowError):
                    run_ready(session)

    def test_cleanup_is_attempted_even_after_input_failure(self):
        app = SimpleNamespace(listDocuments=lambda: {}, ActiveDocument=None)
        gui = SimpleNamespace(
            activeDocument=lambda: None,
            ActiveDocument=None,
            Selection=SimpleNamespace(clearSelection=Mock()),
        )
        rt = SimpleNamespace(app=app, gui=gui)
        native = entry.native()
        for input_failure, cleanup_failure in ((True, False), (False, True)):
            receipt = {}
            with (
                patch.object(
                    native,
                    "verify_inputs",
                    side_effect=(
                        RuntimeError("input changed")
                        if input_failure
                        else None
                    ),
                ),
                patch.object(
                    native,
                    "cleanup",
                    side_effect=(
                        RuntimeError("cleanup uncertain")
                        if cleanup_failure
                        else None
                    ),
                ) as close,
            ):
                errors = entry.finish(
                    rt, SimpleNamespace(inputs={}), {}, receipt
                )
            close.assert_called_once()
            self.assertTrue(errors)
            self.assertTrue(receipt["cleanup_errors"])

    def test_actual_journey_prefix_establishes_unrelated_selection(self):
        from tracktemplate.compatibility import chair_reference_preview

        class PrefixComplete(Exception):
            pass

        selected, calls = [], []
        source = SimpleNamespace(Name="Source", Objects=[])
        foreign = SimpleNamespace(
            Name="Foreign", Objects=[], recompute=lambda: None
        )
        marker = SimpleNamespace(
            Name="Keep", Document=foreign, addProperty=lambda *_: None
        )
        foreign.addObject = lambda *_: marker

        def clear():
            calls.append("clear")
            selected.clear()

        def add(obj):
            calls.append(("add", obj.Name))
            selected.append(obj)

        view = SimpleNamespace(viewTop=lambda: None, fitAll=lambda: None)
        gui = SimpleNamespace(
            activeDocument=lambda: SimpleNamespace(activeView=lambda: view),
            Selection=SimpleNamespace(
                clearSelection=clear,
                addSelection=add,
                getSelection=lambda *_: list(selected),
            ),
        )
        app = SimpleNamespace(
            newDocument=lambda *_: foreign,
            setActiveDocument=lambda *_: None,
            listDocuments=lambda: {"Source": source, "Foreign": foreign},
        )
        helpers = SimpleNamespace(
            settle=lambda: None,
            state=lambda: dict(
                selection=tuple(
                    (item.Document.Name, item.Name, ()) for item in selected
                )
            ),
        )
        rt = SimpleNamespace(
            app=app,
            gui=gui,
            helpers=helpers,
            session=SimpleNamespace(module=object()),
        )
        case = entry.ToSingleRailGui("test_authorised_gui_stage")
        with (
            patch.object(
                entry.native(), "prepare_source", return_value=source
            ),
            patch.object(
                chair_reference_preview,
                "_open_source_context",
                side_effect=PrefixComplete,
            ) as reached,
        ):
            with self.assertRaises(PrefixComplete):
                case._journey(rt, object(), {}, {}, {})
        reached.assert_called_once()
        self.assertEqual(selected, [marker])
        self.assertEqual(calls, ["clear", ("add", "Keep")])

    def test_actual_disposal_tail_establishes_then_preserves_witness(self):
        tree = ast.parse(Path(entry.__file__).read_text())
        cls = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "ToSingleRailGui"
        )
        journey = next(
            node
            for node in cls.body
            if isinstance(node, ast.FunctionDef) and node.name == "_journey"
        )
        index = next(
            index
            for index, node in enumerate(journey.body)
            if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and any(
                isinstance(arg, ast.Constant)
                and arg.value == "to-rollback-restored.png"
                for arg in node.value.args
            )
        )
        # Execute the unchanged actual disposal suffix, after picking and the
        # separately checked rollback; host close supplies only its boundary.
        suffix = compile(
            ast.Module(body=journey.body[index + 1 :], type_ignores=[]),
            entry.__file__,
            "exec",
        )
        for corrupt_close in (False, True):
            with self.subTest(corrupt_close=corrupt_close):
                source = SimpleNamespace(Name="Source")
                foreign = SimpleNamespace(Name="Foreign")
                marker = SimpleNamespace(Name="Keep", Document=foreign)
                preview = SimpleNamespace(Name="Preview")
                registry = {
                    "Source": source,
                    "Foreign": foreign,
                    "Preview": preview,
                }
                selected = [(preview, "Face5")]
                events = []

                def clear():
                    events.append("clear")
                    selected.clear()

                def add(obj):
                    events.append(("add", obj.Name))
                    selected.append((obj, ""))

                def state():
                    return dict(
                        selection=tuple(
                            (obj.Document.Name, obj.Name, ())
                            for obj, _ in selected
                            if obj is marker
                        )
                    )

                def close(name):
                    events.append("close")
                    self.assertEqual(selected, [(marker, "")])
                    registry.pop(name)
                    if corrupt_close:
                        selected.clear()

                helpers = SimpleNamespace(settle=lambda: None, state=state)
                gui = SimpleNamespace(
                    Selection=SimpleNamespace(
                        clearSelection=clear,
                        addSelection=add,
                        getSelection=lambda *_: [obj for obj, _ in selected],
                    )
                )
                rt = SimpleNamespace(
                    app=SimpleNamespace(
                        closeDocument=close,
                        listDocuments=lambda: dict(registry),
                        setActiveDocument=lambda *_: None,
                    ),
                    gui=gui,
                    helpers=helpers,
                )
                case = SimpleNamespace(_source_preserved=Mock())
                receipt = dict(checks={"preview_disposals": 0})
                baseline = dict(selection=(("Foreign", "Keep", ()),))
                namespace = dict(
                    entry.__dict__,
                    rt=rt,
                    preview=preview,
                    source=source,
                    marker=marker,
                    baseline=baseline,
                    receipt=receipt,
                    context=object(),
                    self=case,
                )
                if corrupt_close:
                    with self.assertRaises(AssertionError):
                        exec(suffix, namespace)
                    self.assertEqual(receipt["checks"]["preview_disposals"], 0)
                else:
                    exec(suffix, namespace)
                    self.assertEqual(receipt["checks"]["preview_disposals"], 1)
                    case._source_preserved.assert_called_once()
                self.assertEqual(events, ["clear", ("add", "Keep"), "close"])

    def test_start_refuses_skips_wrong_count_errors_and_cleanup_failure(self):
        exits, scheduled = [], []
        qt = SimpleNamespace(
            QTimer=SimpleNamespace(
                singleShot=lambda _, fn: scheduled.append(fn)
            ),
            QCoreApplication=SimpleNamespace(exit=exits.append),
        )
        for success, count, skipped, status in (
            (False, 1, [], "FAIL"),
            (True, 0, [], "PASS"),
            (True, 2, [], "PASS"),
            (True, 1, ["skip"], "PASS"),
            (True, 1, [], "FAIL"),
            (True, 1, [], "PASS"),
        ):
            result = SimpleNamespace(
                wasSuccessful=lambda: success, testsRun=count, skipped=skipped
            )
            case = SimpleNamespace(
                receipt=dict(status=status, sentinel="passed")
            )
            output = io.StringIO()
            with ExitStack() as stack:
                stack.enter_context(
                    patch.dict(
                        sys.modules, {"PySide6": SimpleNamespace(QtCore=qt)}
                    )
                )
                stack.enter_context(
                    patch.object(entry, "ToSingleRailGui", return_value=case)
                )
                stack.enter_context(
                    patch.object(
                        entry.unittest, "TestSuite", return_value=object()
                    )
                )
                stack.enter_context(
                    patch.object(
                        entry.unittest,
                        "TextTestRunner",
                        return_value=SimpleNamespace(run=lambda _: result),
                    )
                )
                stack.enter_context(redirect_stdout(output))
                stack.enter_context(redirect_stderr(io.StringIO()))
                entry.start()
                scheduled.pop()()
            valid = success and count == 1 and not skipped and status == "PASS"
            self.assertEqual(exits.pop(), 0 if valid else 1)
            self.assertEqual(entry.PREFIX in output.getvalue(), valid)


if __name__ == "__main__":
    outcome = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(GuiEntryTests)
    )
    if (
        outcome.wasSuccessful()
        and outcome.testsRun == 12
        and not outcome.skipped
    ):
        print(SENTINEL)
        raise SystemExit(0)
    raise SystemExit(1)
