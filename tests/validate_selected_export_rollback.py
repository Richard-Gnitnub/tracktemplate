#!/usr/bin/env python3
"""Check selected-export preservation with disposable real files.

Synthetic bytes prove transaction and diagnostic behaviour. They do not
qualify CAD formats, durability, restart recovery, or production use.
"""

import ast
import copy
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.application.selected_export import (  # noqa: E402
    run_selected_production_export,
)
from tracktemplate.adapters.export.selected_export_files import (  # noqa: E402
    SelectedExportFiles,
)


SENTINEL = "Selected export rollback validation passed"
LEGACY = ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
LEGACY_SHA256 = (
    "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848"
)
FIELDS = ("record_id", "format", "path", "status")


def payload(task):
    return ("synthetic-new-" + Path(task["path"]).name).encode("ascii")


def regular_files(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def inputs(root, *, manifest=True, existing=True, overwrite=True):
    tasks = [
        {"path": str(root / name), "format": name.rsplit(".", 1)[1],
         "records": [{"record_id": "record-" + name}], "combined": False}
        for name in ("first.step", "second.svg")
    ]
    plan = {"tasks": tasks, "manifest_path": str(root / "selected.csv")
            if manifest else "", "skipped": []}
    config = {"output_directory": str(root), "create_manifest": manifest,
              "overwrite_existing": overwrite}
    if existing:
        for final in [task["path"] for task in tasks] + (
            [plan["manifest_path"]] if manifest else []
        ):
            path = Path(final)
            path.write_bytes(("original-" + path.name).encode("ascii"))
    (root / "unrelated.txt").write_bytes(b"foreign evidence stays")
    return plan, config


class Collaborators:
    """Observe staging through caller-visible bytes and paths."""

    def __init__(self, document, plan, root, fault=None):
        self.document = document
        self.plan = plan
        self.root = root
        self.fault = fault
        self.before = regular_files(root)
        self.dispatched = []
        self.staging = None

    def unchanged(self):
        observed = regular_files(self.root)
        for name, value in self.before.items():
            assert observed.get(name) == value, name
        for task in self.plan["tasks"]:
            if Path(task["path"]).name not in self.before:
                assert not Path(task["path"]).exists()

    def dispatch(self, document, task, path):
        self.unchanged()
        assert document is self.document
        assert task is self.plan["tasks"][len(self.dispatched)]
        assert str(path) != task["path"]
        assert Path(path).suffix == Path(task["path"]).suffix
        self.staging = Path(path).parent
        self.dispatched.append(task)
        if self.fault == "unknown-staging":
            (self.staging / "foreign.dat").write_bytes(b"uncertain evidence")
            raise OSError("controlled generation with unknown staging")
        if self.fault == "generation" and len(self.dispatched) == 2:
            Path(path).write_bytes(b"incomplete")
            raise OSError("controlled generation failure")
        Path(path).write_bytes(payload(task))

    def rows(self, results, skipped, set_id, *configs):
        self.unchanged()
        assert set_id == "SET-SELECTED" and len(configs) == 4
        assert skipped == self.plan["skipped"]
        assert [item["task"] for item in results] == self.plan["tasks"]
        assert all(item["success"] for item in results)
        if self.fault == "manifest-build":
            raise OSError("controlled manifest construction failure")
        return [
            {"record_id": item["task"]["records"][0]["record_id"],
             "format": item["task"]["format"],
             "path": item["task"]["path"], "status": "Success"}
            for item in results
        ]

    def write(self, path, rows):
        self.unchanged()
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        if self.fault == "manifest-write":
            raise OSError("controlled manifest write failure")

    @staticmethod
    def failed(item):
        detail = str(item["error"])
        return "Task failed: " + detail, detail

    @staticmethod
    def skipped(item):
        return "Skipped: " + item["reason"], item["reason"]

    def keywords(self):
        return {
            "dispatch_export_task": self.dispatch,
            "build_manifest_rows": self.rows,
            "write_export_manifest": self.write,
            "failed_export_report": self.failed,
            "skipped_export_report": self.skipped,
        }


def legacy_namespace(collaborators, namespace=None):
    """Use frozen function bodies, never a rewritten comparison oracle."""
    source = LEGACY.read_bytes()
    assert hashlib.sha256(source).hexdigest() == LEGACY_SHA256
    parsed = ast.parse(source, filename=str(LEGACY))
    names = {
        "_selected_export_stage_path", "commit_staged_export_entries",
        "_selected_export_summary_failure", "run_selected_production_export",
    }
    nodes = [node for node in parsed.body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in nodes} == names
    namespace = {} if namespace is None else namespace
    namespace.update({
        "os": os, "shutil": shutil, "tempfile": tempfile,
        "safe_filename_component": lambda value, fallback: value or fallback,
        "build_manifest_rows": collaborators.rows,
        "write_export_manifest": collaborators.write,
        "_failed_export_report": collaborators.failed,
        "_skipped_export_report": collaborators.skipped,
        "dispatch_freecad_export": collaborators.dispatch,
    })
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(LEGACY), "exec"),
         namespace)
    return namespace


def fault_factory(fault, instances):
    class FaultFiles(SelectedExportFiles):
        def __init__(self):
            super().__init__()
            instances.append(self)
            self.events = []

        def _replace(self, source, destination, *, source_directory_fd,
                     destination_directory_fd):
            source_parent = Path(os.readlink(
                "/proc/self/fd/" + str(source_directory_fd)
            )).name
            self.events.append((source_parent, source, destination))
            if (fault in {"publish", "restore", "all-restores"}
                    and source_parent != ".backups"
                    and str(source).startswith("0002_")):
                raise OSError("controlled publication failure")
            if (source_parent == ".backups"
                    and (fault == "all-restores"
                         or (fault == "restore"
                             and str(source).startswith("0001_")))):
                raise OSError("controlled backup restoration failure")
            return super()._replace(
                source, destination,
                source_directory_fd=source_directory_fd,
                destination_directory_fd=destination_directory_fd,
            )

    return FaultFiles


def run_case(root, *, manifest=True, existing=True, overwrite=True,
             fault=None, factory=None, legacy=False):
    plan, config = inputs(root, manifest=manifest, existing=existing,
                          overwrite=overwrite)
    saved_plan, saved_config = copy.deepcopy(plan), copy.deepcopy(config)
    document = object()
    collaborators = Collaborators(document, plan, root, fault)
    instances = []
    arguments = (document, plan, config, "SET-SELECTED", {}, {}, {}, {})
    if legacy:
        namespace = legacy_namespace(collaborators)
        result = namespace["run_selected_production_export"](*arguments)
    else:
        result = run_selected_production_export(
            *arguments,
            export_files_factory=factory or fault_factory(fault, instances),
            **collaborators.keywords(),
        )
    assert plan == saved_plan and config == saved_config
    assert (root / "unrelated.txt").read_bytes() == b"foreign evidence stays"
    return result, plan, collaborators, instances


def diagnostics(result):
    return "\n".join(result["failures"] + result["failure_details"])


def validate_success(base):
    cases = 0
    for manifest in (True, False):
        for existing in (True, False):
            root = base / ("success-{}-{}".format(manifest, existing))
            root.mkdir()
            result, plan, _, instances = run_case(
                root, manifest=manifest, existing=existing,
            )
            assert result["successful_files"] == 2 + int(manifest)
            assert result["failed_files"] == 0
            assert result["output_directory"] == str(root)
            assert result["manifest_path"] == plan["manifest_path"]
            assert result["manifest_requested"] is manifest
            assert result["formats"] == ["STEP", "SVG"]
            assert instances[0].state == "published"
            assert not instances[0].retained_staging_directory
            for task in plan["tasks"]:
                assert Path(task["path"]).read_bytes() == payload(task)
            expected = {"first.step", "second.svg", "unrelated.txt"}
            if manifest:
                expected.add("selected.csv")
                with open(plan["manifest_path"], newline="") as handle:
                    rows = list(csv.DictReader(handle))
                assert [row["path"] for row in rows] == [
                    task["path"] for task in plan["tasks"]
                ]
            assert {path.name for path in root.iterdir()} == expected

            # Reuse the same destination so no normalisation hides a change.
            expected_bytes = regular_files(root)
            old_result, _, _, _ = run_case(
                root, manifest=manifest, existing=existing, legacy=True,
            )
            assert old_result == result
            assert regular_files(root) == expected_bytes
            cases += 1
    return cases


def validate_rollback(base):
    cases = 0
    for manifest in (True, False):
        for fault in ("publish", "restore", "all-restores"):
            root = base / ("rollback-{}-{}".format(manifest, fault))
            root.mkdir()
            result, plan, collaborators, instances = run_case(
                root, manifest=manifest, fault=fault,
            )
            files = instances[0]
            assert result["successful_files"] == 0
            assert result["failed_files"] >= 1
            assert result["manifest_path"] == ""
            observed = regular_files(root)
            for value in collaborators.before.values():
                assert value in observed.values(), (fault, value)
            assert "controlled publication failure" in diagnostics(result)
            if fault == "publish":
                assert files.state == "rolled_back"
                assert observed == collaborators.before
                assert not files.retained_staging_directory
                assert not collaborators.staging.exists()
            else:
                assert files.state == "rollback_incomplete"
                retained = Path(files.retained_staging_directory)
                assert retained.is_dir() and retained == collaborators.staging
                assert str(retained) in diagnostics(result)
                assert "controlled backup restoration failure" in (
                    diagnostics(result)
                )
                assert "No destination export file was changed" not in (
                    diagnostics(result)
                )
                first_backup = retained / ".backups" / "0001_first.step"
                assert first_backup.read_bytes() == (
                    collaborators.before["first.step"]
                )
                assert not Path(plan["tasks"][0]["path"]).exists()
                if fault == "all-restores":
                    second_backup = retained / ".backups" / "0002_second.svg"
                    assert second_backup.read_bytes() == (
                        collaborators.before["second.svg"]
                    )
                else:
                    assert Path(plan["tasks"][1]["path"]).read_bytes() == (
                        collaborators.before["second.svg"]
                    )
                before_cleanup = regular_files(root)
                files.cleanup()
                assert regular_files(root) == before_cleanup
            cases += 1
    return cases


def validate_prepublication_failures(base):
    cases = 0
    for fault in ("generation", "manifest-build", "manifest-write"):
        root = base / fault
        root.mkdir()
        result, _, collaborators, instances = run_case(root, fault=fault)
        assert result["successful_files"] == 0 and result["failed_files"] >= 1
        assert regular_files(root) == collaborators.before
        assert not collaborators.staging.exists()
        assert not instances[0].retained_staging_directory
        cases += 1

    root = base / "collision"
    root.mkdir()
    result, _, collaborators, _ = run_case(root, overwrite=False)
    assert result["successful_files"] == 0 and result["failed_files"] >= 1
    assert regular_files(root) == collaborators.before
    cases += 1
    return cases


def validate_uncertain_cleanup(base):
    cases = 0
    for published in (False, True):
        name = "uncertain-published" if published else "uncertain-stage"
        root = base / name
        root.mkdir()
        instances = []

        class UnknownCleanup(SelectedExportFiles):
            def __init__(self):
                super().__init__()
                instances.append(self)

            def publish(self, overwrite_existing):
                super().publish(overwrite_existing)
                stage = next(
                    path for path in root.iterdir()
                    if path.name.startswith(".railway_selected_export_")
                )
                (stage / "foreign.dat").write_bytes(b"uncertain evidence")

        result, plan, collaborators, _ = run_case(
            root, fault=None if published else "unknown-staging",
            factory=UnknownCleanup,
        )
        files = instances[0]
        retained = Path(files.retained_staging_directory)
        assert retained.is_dir()
        assert str(retained) in diagnostics(result)
        assert (retained / "foreign.dat").read_bytes() == b"uncertain evidence"
        assert result["failed_files"] >= 1
        if published:
            assert files.state == "published"
            assert result["successful_files"] == 3
            assert result["manifest_path"] == plan["manifest_path"]
            for task in plan["tasks"]:
                assert Path(task["path"]).read_bytes() == payload(task)
            assert "No destination export file was changed" not in (
                diagnostics(result)
            )
        else:
            assert result["successful_files"] == 0
            observed = regular_files(root)
            assert all(observed[name] == value
                       for name, value in collaborators.before.items())
        cases += 1

    for published in (False, True):
        name = "substituted-published" if published else "substituted-stage"
        root = base / name
        root.mkdir()
        instances = []
        moved = root / "moved-staging"
        observed = {}

        def substitute(stage):
            stage.rename(moved)
            observed["moved"] = regular_files(moved)
            observed["last_known"] = stage
            stage.mkdir()
            (stage / "foreign.dat").write_bytes(b"foreign replacement")

        class SubstitutedCleanup(SelectedExportFiles):
            def __init__(self):
                super().__init__()
                instances.append(self)

            def stage(self, final_path, writer, *, manifest=False):
                def replacing_writer(path):
                    writer(path)
                    if not published:
                        substitute(Path(path).parent)
                return super().stage(final_path, replacing_writer,
                                     manifest=manifest)

            def publish(self, overwrite_existing):
                super().publish(overwrite_existing)
                stage = next(
                    path for path in root.iterdir()
                    if path.name.startswith(".railway_selected_export_")
                )
                substitute(stage)

        result, _plan, collaborators, _ = run_case(
            root, factory=SubstitutedCleanup,
        )
        assert result["failed_files"] >= 1
        assert result["successful_files"] == (3 if published else 0)
        assert instances[0].retained_staging_directory == ""
        assert regular_files(moved) == observed["moved"]
        assert regular_files(observed["last_known"]) == {
            "foreign.dat": b"foreign replacement",
        }
        remaining = regular_files(root)
        assert all(value in remaining.values()
                   for value in collaborators.before.values())
        detail = diagnostics(result)
        assert "staging location is uncertain" in detail
        assert "Last-known path: " + str(observed["last_known"]) in detail
        assert "Retained selected-export staging:" not in detail
        cases += 1
    return cases


def validate_plan_rejection(base):
    cases = 0
    for fault in ("duplicate", "outside", "late-collision"):
        root = base / ("plan-" + fault)
        root.mkdir()
        plan, config = inputs(root, existing=False, overwrite=False)
        if fault == "duplicate":
            plan["tasks"][1]["path"] = plan["tasks"][0]["path"]
        elif fault == "outside":
            plan["tasks"][1]["path"] = str(base / "outside.svg")
        document = object()
        collaborators = Collaborators(document, plan, root)
        before = regular_files(base)

        class LateCollision(SelectedExportFiles):
            def publish(self, overwrite_existing):
                destination = Path(plan["tasks"][0]["path"])
                destination.write_bytes(b"late foreign file")
                return super().publish(overwrite_existing)

        result = run_selected_production_export(
            document, plan, config, "SET-SELECTED", {}, {}, {}, {},
            export_files_factory=(LateCollision if fault == "late-collision"
                                  else SelectedExportFiles),
            **collaborators.keywords(),
        )
        assert result["successful_files"] == 0 and result["failed_files"] >= 1
        after = regular_files(base)
        if fault == "late-collision":
            expected = dict(before)
            expected[root.name + "/first.step"] = b"late foreign file"
            assert after == expected
        else:
            assert not collaborators.dispatched
            assert after == before
        cases += 1
    return cases


def dialog_host(root, document=None):
    """Load the real selected dialog callback above synthetic host services."""
    from types import ModuleType, SimpleNamespace

    plan, config = inputs(root)
    document = object() if document is None else document
    collaborators = Collaborators(document, plan, root)
    module = ModuleType("selected_export_binding_fixture")
    namespace = module.__dict__
    legacy_namespace(collaborators, namespace)
    namespace.update({"collaborators": collaborators, "fixture_plan": plan,
                      "fixture_config": config, "shown": []})
    exec("""
def dispatch_freecad_export(*args):
    return collaborators.dispatch(*args)
def build_manifest_rows(*args):
    return collaborators.rows(*args)
def write_export_manifest(*args):
    return collaborators.write(*args)
def _failed_export_report(*args):
    return collaborators.failed(*args)
def _skipped_export_report(*args):
    return collaborators.skipped(*args)
def execute_export_tasks(*args):
    raise AssertionError('Core serialization was not requested')
def run_production_export(*args):
    raise AssertionError('Core export was not requested')
def run_macro():
    return run_production_export
def selected_export_selection_snapshot(doc, set_id):
    return []
class SelectedProductionExportDialog:
    def _current_scope(self):
        return {'selected_objects': selected_export_selection_snapshot(
            self.doc, self.current_set_id())}
class CurveInputDialog:
    def _update_production_export_controls(self, *args):
        pass
    def _production_export_values(self):
        return fixture_config
def plan_production_export(*args):
    return fixture_plan
def run_production_preflight(doc, catalogue, records, config, set_id,
                             *args, **kwargs):
    return []
def preflight_blocking_report(issues):
    return ''
def confirm_selected_export_operation(*args):
    return True
def ensure_production_export_directory(config):
    assert config is fixture_config
def plan_selected_production_export(*args):
    return fixture_plan
def selected_export_filename_issues(*args):
    return []
def settings_for_template_set(*args):
    return None
def selected_export_validation_records(*args):
    return []
def selected_export_preflight_config(config, plan):
    return config
def read_section_config(*args):
    return {}
read_registration_config = read_section_config
read_template_assembly_config = read_section_config
read_formation_config = read_section_config
def read_platform_configs(*args):
    return [{}]
def show_production_export_summary(summary):
    shown.append(summary)
""", namespace)
    parsed = ast.parse(LEGACY.read_bytes(), filename=str(LEGACY))
    dialog_node = next(node for node in parsed.body
                       if isinstance(node, ast.ClassDef)
                       and node.name == "SelectedProductionExportDialog")
    callback = next(node for node in dialog_node.body
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "export_selected")
    exec(compile(ast.Module(body=[callback], type_ignores=[]), str(LEGACY),
                 "exec"), namespace)
    namespace["SelectedProductionExportDialog"].export_selected = (
        namespace["export_selected"]
    )

    def unexpected_dialog(*args):
        raise AssertionError("Handled export failure escaped into GUI error")

    namespace.update({
        "PRODUCTION_PREFLIGHT_SEVERITY_WARNING": "warning",
        "versioned_dialog_title": lambda value: value,
        "QtWidgets": SimpleNamespace(QMessageBox=SimpleNamespace(
            critical=unexpected_dialog,
        )),
    })
    dialog = SimpleNamespace(
        doc=document, plan=plan, issues=[], scope={}, matching_records=[],
        export_records=[], preliminary_skipped=[], catalogue_records=[],
        refresh_preview=lambda: None, _current_config=lambda: config,
        current_set_id=lambda: "SET-SELECTED",
    )
    host = SimpleNamespace(
        module=module,
        _host=SimpleNamespace(source_sha256=LEGACY_SHA256),
        routing_record=lambda: {"route": "modular", "schema_version": 16},
        launch_workflow=lambda: module.run_macro(),
    )
    return host, dialog, collaborators


def validate_binding(base):
    from unittest import mock

    from tracktemplate import api
    from tracktemplate.compatibility import transition_workflow as workflow
    from tracktemplate.compatibility.selected_export_workflow import (
        SelectedExportBinding,
    )

    from tracktemplate.adapters.freecad import core_export_document as documents
    from validate_core_export_staging import DocumentHost

    app = DocumentHost()
    editable = app.documents["Editable"]
    root = base / "retained-comparison-loader"
    root.mkdir()
    host, dialog, collaborators = dialog_host(root, editable)
    original_dispatch = collaborators.dispatch
    isolated_calls = []

    def isolated_dispatch(document, task, path):
        assert document is not editable
        assert app.listDocuments().get(document.Name) is document
        isolated_calls.append(document)
        collaborators.document = document
        try:
            original_dispatch(document, task, path)
        finally:
            collaborators.document = editable

    collaborators.dispatch = isolated_dispatch
    isolation = documents.CoreExportDocument

    def document_factory(serializer):
        return isolation(serializer, app=app, gui=app.gui)
    namespace = host.module.__dict__
    original = namespace["run_selected_production_export"]
    with mock.patch.object(workflow, "load_b15_workflow_host",
                           return_value=host._host):
        with mock.patch.object(workflow, "ModularTransitionWorkflowSession",
                               return_value=host):
            from tracktemplate.adapters.export.core_layout_set import (
                CoreLayoutExportSetFiles,
            )
            session = workflow.load_modular_transition_workflow_session(
                ROOT, api, {},
                export_files_factory=CoreLayoutExportSetFiles,
                export_dispatcher_factory=document_factory,
                selected_export_files_factory=SelectedExportFiles,
                selected_export_atomic=False,
            )
    binding = namespace["run_selected_production_export"]
    assert isinstance(binding, SelectedExportBinding)
    assert binding.original_command is original
    assert binding.export_dispatcher_factory is document_factory
    session.core_layout_export_routing_record()
    factory = binding.export_files_factory
    binding.export_files_factory = None
    try:
        session.core_layout_export_routing_record()
    except RuntimeError:
        pass
    else:
        raise AssertionError("A missing selected-export factory was accepted")
    finally:
        binding.export_files_factory = factory
    session.core_layout_export_routing_record()
    instances = []
    try:
        binding.export_files_factory = fault_factory("restore", instances)
        namespace["SelectedProductionExportDialog"].export_selected(dialog)
    finally:
        binding.export_files_factory = factory
    result, = namespace["shown"]
    assert len(isolated_calls) == len(dialog.plan["tasks"])
    assert set(app.documents) == {"Editable", "Other"}
    assert result["successful_files"] == 0 and result["failed_files"] >= 1
    observed = regular_files(root)
    assert all(value in observed.values()
               for value in collaborators.before.values())
    assert str(instances[0].retained_staging_directory) in diagnostics(result)
    assert "No destination export file was changed" not in diagnostics(result)
    session.core_layout_export_routing_record()
    namespace["run_selected_production_export"] = original
    try:
        session.core_layout_export_routing_record()
    except RuntimeError:
        pass
    else:
        raise AssertionError("A mixed selected-export command was accepted")
    namespace["run_selected_production_export"] = binding
    session.core_layout_export_routing_record()

    root = base / "comparison-constructor"
    root.mkdir()
    host, _dialog, _collaborators = dialog_host(root)
    original = host.module.run_selected_production_export
    workflow.ModularCoreLayoutWorkflowSession(host, api.run_core_layout_export)
    assert host.module.run_selected_production_export is original
    assert hashlib.sha256(LEGACY.read_bytes()).hexdigest() == LEGACY_SHA256
    return 2


def validate_selected_isolation(base):
    """Exercise normal and override serializers through the selected binding."""
    from tracktemplate import api
    from tracktemplate.adapters.freecad.core_export_document import (
        CoreExportDocument,
    )
    from tracktemplate.compatibility import transition_workflow as workflow
    from validate_core_export_staging import DocumentHost

    cases = 0
    for mode in ("normal", "override", "falsy-override", "serialize", "close",
                 "interrupt"):
        root = base / ("isolated-" + mode)
        root.mkdir()
        app = DocumentHost()
        editable = app.documents["Editable"]
        registry = app.listDocuments()
        objects = dict(editable.objects)
        active = app.ActiveDocument
        selection = list(app.gui.Selection.entries)
        hover = app.gui.Selection.hover
        host, dialog, collaborators = dialog_host(root, editable)
        calls = []

        def serializer(document, task, path):
            assert all(document is not item for item in registry.values())
            assert document.Temporary is True and not document.FileName
            assert app.documents.get(document.Name) is document
            assert task is dialog.plan["tasks"][len(calls)]
            collaborators.unchanged()
            calls.append(document)
            document.addObject("App::FeaturePython", "UnremovedExportObject")
            if mode == "serialize":
                raise OSError("controlled selected serializer failure")
            if mode == "interrupt":
                raise KeyboardInterrupt("controlled selected interruption")
            Path(path).write_bytes(payload(task))

        def factory(operation):
            return CoreExportDocument(operation, app=app, gui=app.gui)

        collaborators.dispatch = serializer
        if mode == "close":
            def close_failure(_name):
                raise RuntimeError("controlled selected document close failure")
            app.close_fault = close_failure
        session = workflow.ModularCoreLayoutWorkflowSession(
            host, api.run_core_layout_export,
            selected_export_files_factory=SelectedExportFiles,
            export_dispatcher_factory=factory,
        )
        binding = host.module.run_selected_production_export
        session.core_layout_export_routing_record()
        if mode == "normal":
            binding.export_dispatcher_factory = lambda operation: operation
            try:
                session.core_layout_export_routing_record()
            except RuntimeError:
                pass
            else:
                raise AssertionError("A replaced isolation factory passed")
            finally:
                binding.export_dispatcher_factory = factory
            session.core_layout_export_routing_record()
            cases += 1

        class FalsySerializer:
            def __bool__(self):
                return False

            def __call__(self, *args):
                return serializer(*args)

        override = None
        if mode in ("override", "falsy-override"):
            override = serializer if mode == "override" else FalsySerializer()

            def forbidden(*_args):
                raise AssertionError("Explicit override was ignored")

            collaborators.dispatch = forbidden
        try:
            summary = binding(
                editable, dialog.plan, dialog._current_config(),
                "SET-SELECTED", {}, {}, {}, {}, exporter_override=override,
            )
        except KeyboardInterrupt as error:
            assert mode == "interrupt"
            assert str(error) == "controlled selected interruption"
        else:
            assert mode != "interrupt"
            if mode in ("normal", "override", "falsy-override"):
                assert summary["successful_files"] == 3, summary
                assert summary["failed_files"] == 0, summary
                assert len(calls) == 2
                for task in dialog.plan["tasks"]:
                    assert Path(task["path"]).read_bytes() == payload(task)
            else:
                assert summary["successful_files"] == 0, summary
                assert summary["failed_files"] == 1, summary
                assert "controlled selected" in diagnostics(summary), summary
                if mode == "close":
                    assert app.created[0] in diagnostics(summary)
        assert editable.objects == objects
        assert all(app.documents[name] is value
                   for name, value in registry.items())
        assert app.ActiveDocument is active
        assert sorted(app.gui.Selection.entries) == sorted(selection)
        assert app.gui.Selection.hover == hover
        if mode == "close":
            assert set(app.documents) == set(registry) | {app.created[0]}
        else:
            assert app.documents == registry
        if mode in ("serialize", "close", "interrupt"):
            assert regular_files(root) == collaborators.before
        cases += 1

    for invalid in (None, object()):
        root = base / ("missing-isolation-" + str(cases))
        root.mkdir()
        host, _dialog, _collaborators = dialog_host(root)
        original = host.module.run_selected_production_export
        try:
            workflow.ModularCoreLayoutWorkflowSession(
                host, api.run_core_layout_export,
                selected_export_files_factory=SelectedExportFiles,
                export_dispatcher_factory=invalid,
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError("Selected export accepted no isolation")
        assert host.module.run_selected_production_export is original
        cases += 1
    return cases


def main():
    with tempfile.TemporaryDirectory(prefix="tt-selected-rollback-") as area:
        root = Path(area)
        counts = {
            "success_and_frozen_comparison": validate_success(root),
            "rollback": validate_rollback(root),
            "prepublication_failure": validate_prepublication_failures(root),
            "uncertain_cleanup": validate_uncertain_cleanup(root),
            "binding": validate_binding(root),
            "selected_isolation": validate_selected_isolation(root),
            "plan_rejection": validate_plan_rejection(root),
        }
    print(json.dumps(counts, sort_keys=True))
    print(SENTINEL)


if __name__ == "__main__":
    main()
