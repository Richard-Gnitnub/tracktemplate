#!/usr/bin/env python3
"""Prove the Core staging barrier against real filesystem observations.

Synthetic payloads exercise the inherited nonempty regular-file boundary.
They do not claim CAD format, railway, or whole-set publication acceptance.
"""

import ast
import copy
from contextlib import ExitStack
import csv
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys
import subprocess
import types
import tempfile
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api  # noqa: E402
from tracktemplate.application import core_layout_export as exports  # noqa: E402
from tracktemplate.adapters.export import core_layout_files as files  # noqa: E402
from tracktemplate.adapters.export import core_layout_set as atomic_files  # noqa: E402
from tracktemplate.adapters.freecad import core_export_document as documents  # noqa: E402


SENTINEL = "Core export staging validation passed"
FORMATS = ("dxf", "svg", "stl", "step")
FIELDS = ("record_id", "format", "path", "status")


class ControlledInterruption(BaseException):
    """An explicit callback interruption, not a bytecode-window probe."""


def payload(task):
    return ("synthetic-" + task["format"] + "\n").encode("ascii")


def file_witness(root):
    """Retain bytes and identity so identical-byte replacement cannot pass."""
    result = {}
    for path in sorted(Path(root).rglob("*")):
        stat = path.lstat()
        item = (stat.st_mode, stat.st_ino, stat.st_size, stat.st_mtime_ns)
        if path.is_symlink():
            item += ("symlink", os.readlink(path))
        elif path.is_file():
            item += ("file", hashlib.sha256(path.read_bytes()).hexdigest())
        else:
            item += ("directory",)
        result[path.relative_to(root).as_posix()] = item
    return result


def inputs(root, *, existing=False, overwrite=True):
    tasks = [
        {
            "format": name,
            "path": str(root / ("core." + name)),
            "records": [{"record_id": "record-" + name, "role": "Template"}],
            "combined": False,
        }
        for name in FORMATS
    ]
    plan = {
        "tasks": tasks,
        "manifest_path": str(root / "core.csv"),
        "skipped": [
            {
                "format": "svg",
                "reason": "unsupported",
                "record": {"record_id": "skipped", "role": "Skip"},
            }
        ],
    }
    config = {"output_directory": str(root), "overwrite_existing": overwrite}
    if existing:
        for path in [item["path"] for item in tasks] + [plan["manifest_path"]]:
            Path(path).write_bytes(("preserve-" + Path(path).name).encode())
    (root / "foreign-evidence.tmp").write_bytes(b"never owned by this call")
    return plan, config


class Collaborators:
    """Observe the barrier independently of application staging helpers."""

    def __init__(self, document, plan, root, fault=None, interruption=None):
        self.document = document
        self.plan = plan
        self.root = root
        self.before = file_witness(root)
        self.fault = fault
        self.interruption = interruption
        self.dispatched = []
        self.manifest_written = False
        self.rows = None

    def dispatch(self, document, task, staged_path):
        assert document is self.document
        index = len(self.dispatched)
        assert task is self.plan["tasks"][index]
        assert str(staged_path) != task["path"]
        assert Path(staged_path).suffix == Path(task["path"]).suffix
        self.assert_finals_unchanged()
        self.dispatched.append(task)
        path = Path(staged_path)
        if self.fault == ("generation", index):
            path.write_bytes(b"partial")
            raise RuntimeError("controlled generation " + str(index))
        if self.fault == ("interrupt", index):
            path.write_bytes(b"partial")
            raise self.interruption
        if self.fault == ("missing", index):
            return
        if self.fault == ("empty", index):
            path.write_bytes(b"")
            return
        if self.fault == ("directory", index):
            path.mkdir()
            return
        if self.fault == ("symlink", index):
            path.symlink_to(self.root / "foreign-evidence.tmp")
            return
        path.write_bytes(payload(task))

    def assert_finals_unchanged(self):
        for relative, witness in self.before.items():
            assert file_witness(self.root)[relative] == witness, relative
        for task in self.plan["tasks"]:
            relative = Path(task["path"]).relative_to(self.root).as_posix()
            if relative not in self.before:
                assert not Path(task["path"]).exists(), relative
        manifest = Path(self.plan["manifest_path"])
        if manifest.name not in self.before:
            assert not manifest.exists()

    def build_rows(self, results, skipped, set_id, *configs):
        self.assert_finals_unchanged()
        assert skipped is self.plan["skipped"] and set_id == "SET-STAGING"
        assert len(configs) == 4
        assert len(results) == len(self.plan["tasks"])
        for result, original in zip(results, self.plan["tasks"]):
            assert result["task"] is original and result["success"] is True
        if self.fault == ("manifest-build", None):
            raise RuntimeError("controlled manifest construction")
        self.rows = [
            {
                "record_id": item["task"]["records"][0]["record_id"],
                "format": item["task"]["format"],
                "path": item["task"]["path"],
                "status": "Success",
            }
            for item in results
        ]
        return self.rows

    def write_rows(self, path, rows):
        self.assert_finals_unchanged()
        assert rows is self.rows
        assert str(path) != self.plan["manifest_path"]
        if self.fault == ("manifest-write", None):
            Path(path).write_bytes(b"partial CSV")
            raise OSError("controlled manifest write")
        if self.fault == ("manifest-interrupt", None):
            raise self.interruption
        if self.fault == ("manifest-empty", None):
            Path(path).write_bytes(b"")
            return
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=FIELDS, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
        self.manifest_written = True

    def keywords(self):
        return {
            "dispatch_export_task": self.dispatch,
            "build_manifest_rows": self.build_rows,
            "write_export_manifest": self.write_rows,
            "failed_export_report": lambda item: (
                item["task"]["format"] + ": " + item["error"],
                item["task"]["path"] + "\n" + item["error"],
            ),
            "skipped_export_report": lambda item: (
                item["reason"],
                item["record"]["record_id"],
            ),
        }


def run_case(
    root,
    *,
    existing=False,
    fault=None,
    overwrite=True,
    publish_fault=None,
    cleanup_fault=False,
    interruption=None,
    plan_change=None,
    final_kind=None,
):
    plan, config = inputs(root, existing=existing, overwrite=overwrite)
    if plan_change is not None:
        plan_change(plan)
    if final_kind == "symlink":
        Path(plan["tasks"][0]["path"]).symlink_to(
            root / "foreign-evidence.tmp"
        )
    elif final_kind == "directory":
        Path(plan["tasks"][0]["path"]).mkdir()
    document = {"canonical": "unchanged", "history": ("Generate",)}
    before_inputs = copy.deepcopy((document, plan, config))
    collaborators = Collaborators(document, plan, root, fault, interruption)
    published = []
    original_publish = files._publish_staged_file

    def publish(source, target, allow_overwrite, **kwargs):
        assert len(collaborators.dispatched) == len(plan["tasks"])
        assert collaborators.manifest_written
        assert [row["path"] for row in collaborators.rows] == [
            task["path"] for task in plan["tasks"]
        ]
        if len(published) == publish_fault:
            raise OSError("controlled final publication")
        original_publish(source, target, allow_overwrite, **kwargs)
        published.append(str(target))

    keywords = collaborators.keywords()
    with ExitStack() as stack:
        stack.enter_context(
            mock.patch.object(
                files,
                "_publish_staged_file",
                publish,
            )
        )
        cleanup = (
            mock.patch.object(
                files,
                "_cleanup_staging",
                side_effect=OSError("controlled cleanup"),
            )
            if cleanup_fault
            else mock.patch.object(
                files,
                "_cleanup_staging",
                wraps=files._cleanup_staging,
            )
        )
        stack.enter_context(cleanup)
        try:
            result = api.run_staged_core_layout_export(
                document,
                plan,
                config,
                "SET-STAGING",
                {},
                {},
                {},
                {},
                export_files_factory=files.CoreLayoutExportFiles,
                **keywords,
            )
        finally:
            assert (document, plan, config) == before_inputs
    assert [item["task"] for item in result["results"]] == plan["tasks"]
    assert all(
        item["task"] is task
        for item, task in zip(result["results"], plan["tasks"])
    )
    assert result["successful_files"] == len(published)
    assert result["manifest_requested"] is True
    assert bool(result["manifest_path"]) == (
        plan["manifest_path"] in published
    )
    assert result["skipped_objects"] == 1
    assert result["skipped_outputs"] == ["unsupported"]
    return result, plan, collaborators, published


def assert_aborted(result, collaborators):
    assert result["successful_files"] == 0
    assert result["failed_files"] > 0
    assert result["formats"] == [] and result["manifest_path"] == ""
    assert all(
        not item["success"] and item["error"] for item in result["results"]
    )
    after = file_witness(collaborators.root)
    for name in (
        "core.dxf",
        "core.svg",
        "core.stl",
        "core.step",
        "core.csv",
        "foreign-evidence.tmp",
    ):
        assert after.get(name) == collaborators.before.get(name), name
    if collaborators.fault and collaborators.fault[0] in (
        "directory",
        "symlink",
    ):
        assert "Unremoved staging entries preserved:" in "\n".join(
            result["failure_details"]
        )
    else:
        assert after == collaborators.before


def assert_legacy_success_bytes(result, plan, collaborators):
    """Compare the retained API at identical final paths and CSV inputs."""
    paths = [Path(task["path"]) for task in plan["tasks"]] + [
        Path(plan["manifest_path"])
    ]
    before = {str(path): path.read_bytes() for path in paths}

    def execute(_document, same_plan, _config, _override):
        assert same_plan is plan
        for task in same_plan["tasks"]:
            Path(task["path"]).write_bytes(payload(task))
        return [
            {"task": task, "success": True, "error": ""}
            for task in same_plan["tasks"]
        ]

    def write_rows(path, rows):
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=FIELDS, lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)

    keywords = collaborators.keywords()
    keywords.pop("dispatch_export_task")
    keywords.update(
        {
            "execute_export_tasks": execute,
            "build_manifest_rows": lambda *_args: collaborators.rows,
            "write_export_manifest": write_rows,
        }
    )
    legacy = api.run_core_layout_export(
        collaborators.document,
        plan,
        {
            "output_directory": str(collaborators.root),
            "overwrite_existing": True,
        },
        "SET-STAGING",
        {},
        {},
        {},
        {},
        **keywords,
    )
    assert legacy == result
    assert {str(path): path.read_bytes() for path in paths} == before


def validate_api_route():
    """Bind the successor API without changing the retained v1 default."""
    from tracktemplate.compatibility import transition_workflow as workflow

    expected = (
        "doc",
        "plan",
        "config",
        "set_id",
        "platform_config",
        "formation_config",
        "registration_config",
        "template_assembly_config",
        "exporter_override",
        "dispatch_export_task",
        "build_manifest_rows",
        "write_export_manifest",
        "failed_export_report",
        "skipped_export_report",
        "export_files_factory",
    )
    signature = inspect.signature(api.run_staged_core_layout_export)
    assert tuple(signature.parameters) == expected
    assert all(
        signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        for name in expected[9:]
    )
    assert "run_staged_core_layout_export" in api.__all__
    contract = json.loads(
        (
            ROOT / "reference/contracts/core-layout-export-staging.json"
        ).read_text()
    )
    assert (
        contract["application_command"]
        == "tracktemplate.api.run_staged_core_layout_export"
    )
    assert (
        contract["retained_comparison_command"]
        == "tracktemplate.api.run_core_layout_export"
    )
    assert contract["input_mutation"] is False
    assert contract["file_operations"] == {
        "factory_keyword": "export_files_factory",
        "implementation": (
            "tracktemplate.adapters.export.core_layout_files.CoreLayoutExportFiles"
        ),
        "methods": ["open", "stage", "validate", "publish", "cleanup"],
    }
    assert (
        contract["host_operations"]["dispatch_export_task"]
        == "dispatch_freecad_export"
    )
    assert contract["serializer_isolation"]["factory_keyword"] == (
        "export_dispatcher_factory"
    )
    assert contract["serializer_isolation"]["implementation"] == (
        "tracktemplate.adapters.freecad.core_export_document.CoreExportDocument"
    )

    module = types.ModuleType("_staging_route_fixture")
    namespace = module.__dict__
    for name in (
        "execute_export_tasks",
        "dispatch_freecad_export",
        "build_manifest_rows",
        "write_export_manifest",
        "_failed_export_report",
        "_skipped_export_report",
        "run_production_export",
    ):
        exec(
            "def " + name + "(*args, **kwargs):\n    return None\n", namespace
        )
    exec("def run_macro():\n    return run_production_export\n", namespace)
    base = types.SimpleNamespace(
        module=module,
        _host=types.SimpleNamespace(source_sha256="host-fixture"),
        routing_record=lambda: {"schema_version": 16, "route": "modular"},
        launch_workflow=lambda: module.run_macro(),
    )
    old = workflow.ModularCoreLayoutWorkflowSession(
        base, api.run_core_layout_export
    )
    assert old.core_layout_export_routing_record()["contract_id"] == (
        "tracktemplate:phase7:core-layout-export:1"
    )
    with mock.patch.object(
        workflow, "load_b15_workflow_host", return_value=base._host
    ):
        with mock.patch.object(
            workflow, "ModularTransitionWorkflowSession", return_value=base
        ):
            session = workflow.load_modular_transition_workflow_session(
                ROOT,
                api,
                {},
                atomic=False,  # Retained comparison under D-P9-013.
                export_files_factory=files.CoreLayoutExportFiles,
                export_dispatcher_factory=documents.CoreExportDocument,
            )
    record = session.core_layout_export_routing_record()
    assert record["contract_id"] == contract["contract_id"]
    for name, expected_value in contract["product_routing"].items():
        field = "schema_version" if name == "record_schema_version" else name
        assert record[field] == expected_value
    adapter = module.run_production_export
    assert adapter.calculation is api.run_staged_core_layout_export
    assert adapter.export_files_factory is files.CoreLayoutExportFiles
    assert adapter.export_dispatcher_factory is documents.CoreExportDocument
    assert tuple(inspect.signature(adapter).parameters) == expected[:9]
    for name in ("run_production_export", "dispatch_freecad_export"):
        with mock.patch.object(module, name, lambda: None):
            try:
                session.core_layout_export_routing_record()
            except workflow.TransitionWorkflowError:
                pass
            else:
                raise AssertionError(
                    "A replaced route binding passed: " + name
                )
    object.__setattr__(adapter, "export_files_factory", lambda: None)
    try:
        try:
            session.core_layout_export_routing_record()
        except workflow.TransitionWorkflowError:
            pass
        else:
            raise AssertionError("A replaced filesystem factory passed")
    finally:
        object.__setattr__(
            adapter, "export_files_factory", files.CoreLayoutExportFiles
        )
    object.__setattr__(adapter, "export_dispatcher_factory", lambda: None)
    try:
        try:
            session.core_layout_export_routing_record()
        except workflow.TransitionWorkflowError:
            pass
        else:
            raise AssertionError("A replaced document factory passed")
    finally:
        object.__setattr__(
            adapter, "export_dispatcher_factory", documents.CoreExportDocument
        )
    for invalid_factory in (None, 42):
        previous = module.run_production_export
        try:
            workflow.ModularCoreLayoutWorkflowSession(
                base,
                api.run_staged_core_layout_export,
                staged=True,
                export_files_factory=files.CoreLayoutExportFiles,
                export_dispatcher_factory=invalid_factory,
            )
        except workflow.TransitionWorkflowError:
            pass
        else:
            raise AssertionError("An invalid document factory passed")
        assert module.run_production_export is previous
    for invalid_factory in (None, 42):
        previous = module.run_production_export
        try:
            workflow.ModularCoreLayoutWorkflowSession(
                base,
                api.run_staged_core_layout_export,
                staged=True,
                export_files_factory=invalid_factory,
                export_dispatcher_factory=documents.CoreExportDocument,
            )
        except workflow.TransitionWorkflowError:
            pass
        else:
            raise AssertionError("A missing or non-callable factory passed")
        assert module.run_production_export is previous
    module.run_production_export = object()
    assert session.launch_workflow() is adapter
    previous = module.run_production_export
    with mock.patch.object(
        workflow.ModularCoreLayoutWorkflowSession,
        "_validate_core_layout_export_binding",
        side_effect=RuntimeError("controlled binding failure"),
    ):
        try:
            workflow.ModularCoreLayoutWorkflowSession(
                base,
                api.run_staged_core_layout_export,
                staged=True,
                export_files_factory=files.CoreLayoutExportFiles,
                export_dispatcher_factory=documents.CoreExportDocument,
            )
        except RuntimeError as error:
            assert str(error) == "controlled binding failure"
        else:
            raise AssertionError("Setup failure was absorbed")
    assert module.run_production_export is previous

    script = """
import builtins, sys
sys.path.insert(0, sys.argv[1])
original = builtins.__import__
forbidden = {'FreeCAD', 'FreeCADGui', 'Part', 'PySide', 'PySide2', 'PySide6', 'pivy'}
concrete = 'tracktemplate.adapters.export.core_layout_files'
def guarded(name, *args, **kwargs):
    assert name.split('.')[0] not in forbidden, name
    assert name != concrete, name
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from tracktemplate import api
from tracktemplate.application import core_layout_export
assert api.run_staged_core_layout_export is core_layout_export.run_staged_core_layout_export
assert not (set(sys.modules) & forbidden)
assert concrete not in sys.modules
assert not any(
    name in core_layout_export.run_staged_core_layout_export.__code__.co_names
    for name in ("os", "stat", "tempfile", "pathlib", "shutil",
                 "CoreLayoutExportFiles")
)
"""
    subprocess.run([sys.executable, "-c", script, str(ROOT)], check=True)

    script = """
import builtins, sys
sys.path.insert(0, sys.argv[1])
original = builtins.__import__
def guarded(name, *args, **kwargs):
    assert name.split('.')[0] not in {'FreeCAD', 'FreeCADGui'}, name
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from tracktemplate.adapters.freecad.core_export_document import CoreExportDocument
CoreExportDocument(lambda *args: None)
assert 'FreeCAD' not in sys.modules and 'FreeCADGui' not in sys.modules
"""
    subprocess.run([sys.executable, "-c", script, str(ROOT)], check=True)


def validate_composition_boundary():
    """Keep concrete adapters in the existing runtime composition root."""
    from tools import modular_structure

    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    parsed = ast.parse((ROOT / "TrackTemplate.FCMacro").read_text())
    function = next(
        node
        for node in parsed.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_load_modular_transition_workflow"
    )
    calls = []
    marker = object()
    runtime_reader = lambda: {"runtime": "synthetic"}
    preview_factory = lambda *args: None
    joint_preview_factory = lambda *args: None
    combined_preview_factory = lambda *args: None
    l1_preview_factory = lambda *args: None
    routing = {"route": "modular"}
    session = types.SimpleNamespace(routing_record=lambda: routing)

    def load(*args, **kwargs):
        assert args == (ROOT, api, marker)
        assert kwargs == {
            "export_files_factory": atomic_files.CoreLayoutExportSetFiles,
            "export_dispatcher_factory": documents.CoreExportDocument,
            "selected_export_files_factory": atomic_files.CoreLayoutExportSetFiles,
            "selected_export_atomic": True,
            "runtime_record": runtime_reader,
            "s1_reference_preview_factory": preview_factory,
            "s1j_reference_preview_factory": joint_preview_factory,
            "s1_s1j_reference_preview_factory": combined_preview_factory,
            "l1_reference_preview_factory": l1_preview_factory,
        }
        return session

    modules = {
        "tracktemplate.compatibility": types.SimpleNamespace(
            load_modular_transition_workflow_session=load,
        ),
        "tracktemplate.adapters.export.core_layout_set": atomic_files,
        "tracktemplate.adapters.freecad.core_export_document": documents,
        "tracktemplate.adapters.freecad.chair_reference_preview": (
            types.SimpleNamespace(
                create_s1_reference_preview=preview_factory,
                create_s1j_reference_preview=joint_preview_factory,
                create_s1_s1j_reference_preview=combined_preview_factory,
                create_l1_reference_preview=l1_preview_factory,
            )
        ),
    }

    def resolve(name):
        calls.append(name)
        return modules[name]

    namespace = {"importlib": types.SimpleNamespace(import_module=resolve)}
    exec(
        compile(
            ast.Module(body=[function], type_ignores=[]),
            "<composition boundary>",
            "exec",
        ),
        namespace,
    )
    result = namespace[function.name](
        ROOT,
        api,
        types.SimpleNamespace(load_contract=lambda _path: marker,
                              runtime_record=runtime_reader),
    )
    assert result == (session, routing)
    assert set(calls) == set(modules)


def validate_retained_native_composition():
    """Exercise retained loader prefixes without claiming historical host proof."""
    from tracktemplate.compatibility import transition_workflow as workflow
    from tracktemplate.application import turnout_edit
    from tracktemplate.domain import turnout

    names = (
        "phase7_platform_transitions",
        "phase8_crossover_b4_recovery",
        "phase8_crossover_edit_recovery",
        "phase8_crossover_host_integration_recovery",
        "phase8_crossover_preflight",
        "phase8_crossover_selected_export",
        "phase8_straight_host_crossover",
        "phase8_straight_host_turnout",
        "phase8_turnout_host_integration_recovery",
        "phase8_turnout_selected_export",
        "phase8_turnout_toe_range",
    )
    for name in names:
        path = ROOT / "tests" / ("freecad_validate_" + name + ".py")
        parsed = ast.parse(path.read_text())
        matches = [
            (function, index)
            for function in parsed.body
            if isinstance(function, ast.FunctionDef)
            for index, node in enumerate(function.body)
            if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Subscript)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "launcher"
            and isinstance(node.value.func.slice, ast.Constant)
            and node.value.func.slice.value
            == "_load_modular_transition_workflow"
        ]
        assert len(matches) == 1, name
        function, index = matches[0]
        profile = next(
            (
                ast.literal_eval(node.value)
                for node in parsed.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "PROFILE"
                    for target in node.targets
                )
            ),
            "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-qt6.11.2-coin4.0.10",
        )
        bootstrap = object()
        module = object()
        calls = []

        def compose(root, modular_api, supplied_bootstrap):
            assert root == ROOT and modular_api is api
            assert supplied_bootstrap is bootstrap
            calls.append(name)
            return types.SimpleNamespace(module=module), {"route": "modular"}

        launcher = {
            "FOUNDATION_RESULT": {
                "status": "modular-foundation-ready",
                "matched_profile_id": profile,
            },
            "_load_foundation": lambda root: (api, bootstrap),
            "_load_modular_transition_workflow": compose,
        }
        namespace = {
            "ROOT": ROOT,
            "SOURCE_ROOT": ROOT,
            "PROFILE": profile,
            "api": api,
            "bootstrap": bootstrap,
            "os": os,
            "pathlib": types.SimpleNamespace(Path=Path),
            "transition_workflow": workflow,
            "turnout_edit": turnout_edit,
            "turnout": turnout,
            "document_state": lambda: {},
            "runpy": types.SimpleNamespace(run_path=lambda path: launcher),
        }
        prefix = copy.deepcopy(function.body[: index + 1])
        tree = ast.Module(body=prefix, type_ignores=[])
        exec(compile(tree, str(path), "exec"), namespace)
        assert namespace["session"].module is module and calls == [name]
        assert any(
            isinstance(node, ast.Attribute)
            and node.attr == "module"
            and isinstance(node.value, ast.Name)
            and node.value.id == "session"
            for node in ast.walk(function)
        ), name


def validate_gui_route_guards():
    """Keep v1 and successor GUI reports distinct and fail closed."""
    import validate_phase7_core_layout_export as retained

    spec = importlib.util.spec_from_file_location(
        "_staging_gui_runner", retained.GUI_RUNNER
    )
    assert spec is not None and spec.loader is not None
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    old = retained._routed_gui_report(harness, harness.MODULAR_ROUTE)
    staged = copy.deepcopy(old)
    staged["core_layout_export_routing"].update(
        {
            "contract_id": "tracktemplate:phase9b:core-layout-export-staging:1",
            "command_name": "run_staged_core_layout_export",
        }
    )
    assert harness._validate_routed_report(
        staged, harness.MODULAR_ROUTE, staging_barrier=True
    ) == {"stable": True}
    assert harness._validate_routed_report(old, harness.MODULAR_ROUTE) == {
        "stable": True
    }
    for report, route, staged_mode in (
        (old, harness.MODULAR_ROUTE, True),
        (staged, harness.MODULAR_ROUTE, False),
        (
            retained._routed_gui_report(harness, harness.LEGACY_ROUTE),
            harness.LEGACY_ROUTE,
            True,
        ),
    ):
        try:
            harness._validate_routed_report(
                report, route, staging_barrier=staged_mode
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError("Mixed GUI route proof was accepted")
    compile(
        harness._embedded_workflow_source(
            harness.MODULAR_ROUTE,
            Path("/tmp/staging-test.FCStd"),
            staging_barrier=True,
        ),
        "<staging GUI recipe>",
        "exec",
    )


def validate_absent_manifest_and_falsy_override(root):
    """Retain no-manifest behaviour and honour an explicit falsy callback."""
    plan, config = inputs(root)
    plan["manifest_path"] = ""
    calls = []

    class FalsyExporter:
        def __bool__(self):
            return False

        def __call__(self, _document, task, path):
            calls.append(task)
            Path(path).write_bytes(payload(task))

    def forbidden(*_args):
        raise AssertionError("An unused dispatcher or CSV writer was called")

    result = api.run_staged_core_layout_export(
        object(),
        plan,
        config,
        "SET-STAGING",
        {},
        {},
        {},
        {},
        FalsyExporter(),
        dispatch_export_task=forbidden,
        build_manifest_rows=lambda *_args: [],
        write_export_manifest=forbidden,
        failed_export_report=lambda item: (item["error"], item["error"]),
        skipped_export_report=lambda item: (item["reason"], item["reason"]),
        export_files_factory=files.CoreLayoutExportFiles,
    )
    assert len(calls) == 4 and all(
        task is original for task, original in zip(calls, plan["tasks"])
    )
    assert result["successful_files"] == 4 and result["failed_files"] == 0
    assert (
        result["manifest_requested"] is False and result["manifest_path"] == ""
    )
    assert not any(path.suffix == ".csv" for path in root.iterdir())


class ExportDocumentFixture:
    """Keep label-only placeholders distinct from source feature witnesses."""

    def __init__(self, name):
        self.Name = name
        self.FileName = ""
        self.Temporary = True
        self.objects = {}

    @property
    def Objects(self):
        return tuple(self.objects.values())

    def getObject(self, name):
        return self.objects.get(name)

    def addObject(self, type_id, name):
        assert type_id == "App::FeaturePython"
        assert name not in self.objects
        obj = types.SimpleNamespace(Name=name, Label=name, TypeId=type_id)
        self.objects[name] = obj
        return obj


class DocumentHost:
    """Independent lifecycle model with observable global GUI side effects."""

    GuiUp = True

    def __init__(self):
        self.documents = {}
        for name in ("Editable", "Other"):
            document = self.make_document(name)
            document.objects["Shape"] = types.SimpleNamespace(
                Name="Shape", Label=name + " source", Document=document,
            )
            self.documents[name] = document
        self.ActiveDocument = self.documents["Other"]
        self.actual_active = self.ActiveDocument
        self.created = []
        self.closed = []
        self.creation_fault = None
        self.close_fault = None
        self.active_fault = None
        self.gui = types.SimpleNamespace(Selection=SelectionHost(self))

    @staticmethod
    def make_document(name):
        return ExportDocumentFixture(name)

    def listDocuments(self):
        return dict(self.documents)

    def activeDocument(self):
        return self.actual_active

    def newDocument(self, name, label, hidden, temporary):
        assert hidden is True and temporary is True
        assert name not in self.documents
        self.created.append(name)
        document = self.make_document(name)
        self.documents[name] = document
        self.ActiveDocument = self.actual_active = document
        if self.creation_fault is not None:
            return self.creation_fault(document)
        return document

    def closeDocument(self, name):
        self.closed.append(name)
        if self.close_fault is not None:
            self.close_fault(name)
        del self.documents[name]
        self.ActiveDocument = self.actual_active = None
        self.gui.Selection.clearSelection()
        self.gui.Selection.clearPreselection()

    def setActiveDocument(self, name):
        if self.active_fault is not None:
            self.active_fault(name)
        self.ActiveDocument = self.actual_active = self.documents.get(name)


class SelectionHost:
    """Model grouped subelements, whole membership and hover independently."""

    def __init__(self, app):
        self.app = app
        self.entries = [
            ("Editable", "Shape", "", (0.0, 0.0, 0.0)),
            ("Other", "Shape", "Edge2", (1.25, 2.5, 3.75)),
            ("Editable", "Shape", "Face1", (4.0, 5.0, 6.0)),
        ]
        self.hover = ("Other", "Shape", "Edge1", (7.0, 8.0, 9.0))
        self.read_fault = None
        self.write_fault = None
        self.hover_fault = None

    def item(self, document_name, object_name, names, points):
        document = self.app.documents[document_name]
        return types.SimpleNamespace(
            DocumentName=document_name, ObjectName=object_name,
            Object=document.getObject(object_name),
            SubElementNames=tuple(names),
            PickedPoints=tuple(
                types.SimpleNamespace(x=x, y=y, z=z) for x, y, z in points
            ),
        )

    def getSelectionEx(self, document, resolve):
        assert (document, resolve) == ("*", 0)
        if self.read_fault is not None:
            self.read_fault()
        groups = {}
        for doc, obj, subname, point in self.entries:
            group = groups.setdefault((doc, obj), ([], []))
            if subname:
                group[0].append(subname)
                group[1].append(point)
        return [self.item(*names, *values) for names, values in groups.items()]

    def isSelected(self, obj, subname, resolve):
        assert resolve == 0
        return any(
            (doc, name, sub) == (obj.Document.Name, obj.Name, subname)
            for doc, name, sub, _point in self.entries
        )

    def clearSelection(self):
        self.entries = []

    def addSelection(self, document, obj, subname, x, y, z, clear):
        assert clear is False
        if self.write_fault is not None:
            self.write_fault()
        self.entries.append((document, obj, subname, (x, y, z)))

    def getPreselection(self):
        if self.hover is None:
            return types.SimpleNamespace(DocumentName="", ObjectName="")
        doc, obj, subname, point = self.hover
        return self.item(doc, obj, (subname,), (point,))

    def clearPreselection(self):
        self.hover = None

    def setPreselection(self, obj, subname, x, y, z):
        if self.hover_fault is not None:
            self.hover_fault()
        self.hover = (obj.Document.Name, obj.Name, subname, (x, y, z))


def validate_document_isolation():
    """Disprove ownership, cleanup and callback-routing claims independently."""
    faults = (
        "success", "no-active", "headless", "serializer", "interrupt",
        "swallowed-removal", "close", "close-interrupt", "both",
        "new-raises", "new-returns-existing", "new-extra", "new-saved",
        "new-not-temporary", "scratch-replaced", "active", "selection",
        "preselection", "selection-read", "contradictory-active",
        "label-holder",
    )
    for fault in faults:
        app = DocumentHost()
        editable = app.documents["Editable"]
        previous = dict(app.documents)
        initial_selection = set(app.gui.Selection.entries)
        initial_hover = app.gui.Selection.hover
        if fault == "no-active":
            app.ActiveDocument = app.actual_active = None
        if fault == "headless":
            app.GuiUp = False
        if fault == "contradictory-active":
            app.actual_active = None
        active = app.ActiveDocument
        error = (
            ControlledInterruption("controlled serializer interruption")
            if fault in ("interrupt", "close-interrupt")
            else RuntimeError("controlled serializer failure")
        )
        cleanup_error = RuntimeError("controlled close failure")

        def fail(value):
            def operation(*_args):
                raise value
            return operation

        if fault == "new-raises":
            app.creation_fault = fail(error)
        elif fault == "new-returns-existing":
            app.creation_fault = lambda _doc: editable
        elif fault == "new-extra":
            def add_foreign(document):
                app.documents["Foreign"] = app.make_document("Foreign")
                return document
            app.creation_fault = add_foreign
        elif fault in ("new-saved", "new-not-temporary"):
            def invalid_document(document):
                if fault == "new-saved":
                    document.FileName = "/operator/retained.FCStd"
                else:
                    document.Temporary = False
                return document
            app.creation_fault = invalid_document
        elif fault == "label-holder":
            def fail_label_holder(document):
                document.addObject = fail(error)
                return document
            app.creation_fault = fail_label_holder
        if fault in ("close", "both", "close-interrupt"):
            app.close_fault = fail(
                error if fault == "close-interrupt" else cleanup_error
            )
        if fault == "active":
            app.active_fault = fail(RuntimeError("controlled active failure"))
        if fault == "selection":
            app.gui.Selection.write_fault = fail(
                RuntimeError("controlled selection failure")
            )
        if fault == "preselection":
            app.gui.Selection.hover_fault = fail(
                RuntimeError("controlled preselection failure")
            )
        if fault == "selection-read":
            app.gui.Selection.read_fault = fail(error)
        task = {"records": [object()], "format": "step"}
        calls = []

        def serializer(document, supplied_task, path):
            assert supplied_task is task and path == "/stage/payload.step"
            assert all(document is not item for item in previous.values())
            assert app.documents.get(document.Name) is document
            assert {obj.Label for obj in document.Objects} == {
                obj.Label for obj in editable.Objects
            }
            assert all(not hasattr(obj, "Shape") for obj in document.Objects)
            calls.append(document)
            document.objects["LeakedTemporaryObject"] = object()
            if fault in ("serializer", "interrupt", "both"):
                raise error
            if fault == "scratch-replaced":
                app.documents[document.Name] = app.make_document(document.Name)

        wrapped = documents.CoreExportDocument(
            serializer, app=app, gui=app.gui if app.GuiUp else None,
        )
        assert not app.created and not app.closed
        caught = None
        try:
            wrapped(editable, task, "/stage/payload.step")
        except BaseException as observed:
            caught = observed
        if fault in ("success", "no-active", "headless", "swallowed-removal"):
            assert caught is None, (fault, caught)
        else:
            assert caught is not None, fault
        if fault in (
            "serializer", "interrupt", "both", "close-interrupt",
            "new-raises", "selection-read", "label-holder",
        ):
            assert caught is error, fault
        if fault == "both":
            assert "controlled close failure" in " ".join(caught.__notes__)
        if fault in ("close", "both", "close-interrupt"):
            diagnostic = str(caught) + " ".join(
                getattr(caught, "__notes__", ())
            )
            assert app.created[0] in diagnostic
        assert all(name not in previous for name in app.closed)
        assert all(app.documents.get(name) is doc for name, doc in previous.items())
        assert editable.objects == {"Shape": editable.getObject("Shape")}
        if fault in ("new-raises", "new-returns-existing", "scratch-replaced"):
            assert not app.closed, fault
        if fault in ("new-extra", "new-saved", "new-not-temporary"):
            assert app.closed == app.created, fault
        if fault == "new-extra":
            assert set(app.documents) == set(previous) | {"Foreign"}
        if fault in ("selection-read", "contradictory-active"):
            assert not app.created and not calls, fault
        if fault not in (
            "new-raises", "new-returns-existing", "new-extra", "close",
            "both", "close-interrupt", "scratch-replaced",
        ):
            assert app.documents == previous, fault
        if fault not in ("active", "contradictory-active"):
            assert app.ActiveDocument is active and app.actual_active is active
        if app.GuiUp and fault != "selection":
            assert set(app.gui.Selection.entries) == initial_selection, fault
        if app.GuiUp and fault != "preselection":
            assert app.gui.Selection.hover == initial_hover, fault

    from tracktemplate.compatibility import transition_workflow as workflow

    raw = object()
    override = object()
    wrapped = object()
    calls = []

    def factory(serializer):
        calls.append(serializer)
        return wrapped

    def calculation(*args, **kwargs):
        assert args[8] is None
        assert kwargs["dispatch_export_task"] is wrapped
        return "isolated"

    adapter = workflow._StagedCoreLayoutExportAdapter(
        calculation, raw, None, None, None, None, None, factory,
    )
    arguments = (object(), {}, {}, "set", {}, {}, {}, {})
    assert adapter(*arguments) == "isolated"
    assert adapter(*arguments, exporter_override=override) == "isolated"
    assert calls == [raw, override]
    with tempfile.TemporaryDirectory(prefix="core-document-failure-") as tmp:
        root = Path(tmp)
        plan, config = inputs(root, existing=True)
        before = file_witness(root)
        app = DocumentHost()
        primary = RuntimeError("primary serializer failure")
        app.close_fault = fail(RuntimeError("secondary document close failure"))
        result = api.run_staged_core_layout_export(
            app.documents["Editable"], plan, config, "set", {}, {}, {}, {},
            dispatch_export_task=documents.CoreExportDocument(
                fail(primary), app=app, gui=app.gui,
            ),
            build_manifest_rows=lambda *_args: [],
            write_export_manifest=lambda *_args: None,
            failed_export_report=lambda item: (item["error"], item["error"]),
            skipped_export_report=lambda item: (item["reason"], item["reason"]),
            export_files_factory=files.CoreLayoutExportFiles,
        )
        assert result["successful_files"] == 0
        assert file_witness(root) == before
        details = "\n".join(result["failure_details"])
        assert "primary serializer failure" in details
        assert "secondary document close failure" in details
    print("CORE_EXPORT_DOCUMENT_CASES=" + str(len(faults)))


def validate_cleanup_observers():
    """Reject completed restoration whose observers change earlier state."""
    for mode in ("selection-active", "preselection-active", "preselection-selection"):
        with tempfile.TemporaryDirectory(prefix="core-observer-failure-") as tmp:
            root = Path(tmp)
            plan, config = inputs(root, existing=True)
            before = file_witness(root)
            app = DocumentHost()
            selection = app.gui.Selection
            original_add = selection.addSelection
            original_hover = selection.setPreselection

            def add_then_change_active(*args):
                original_add(*args)
                app.setActiveDocument("Editable")

            def hover_then_change_previous(*args):
                original_hover(*args)
                if mode == "preselection-active":
                    app.setActiveDocument("Editable")
                else:
                    selection.clearSelection()

            if mode == "selection-active":
                selection.addSelection = add_then_change_active
            else:
                selection.setPreselection = hover_then_change_previous

            def serialize(_document, _task, path):
                Path(path).write_bytes(b"complete staged payload")

            result = api.run_staged_core_layout_export(
                app.documents["Editable"], plan, config, "set", {}, {}, {}, {},
                dispatch_export_task=documents.CoreExportDocument(
                    serialize, app=app, gui=app.gui,
                ),
                build_manifest_rows=lambda *_args: [],
                write_export_manifest=lambda *_args: None,
                failed_export_report=lambda item: (item["error"], item["error"]),
                skipped_export_report=lambda item: (item["reason"], item["reason"]),
                export_files_factory=files.CoreLayoutExportFiles,
            )
            assert result["successful_files"] == 0, mode
            assert result["failed_files"] > 0, mode
            assert file_witness(root) == before, mode
            expected = "selection" if mode.endswith("-selection") else "active document"
            assert "Core export final " + expected + " changed." in "\n".join(
                result["failure_details"]
            ), mode
            assert set(app.documents) == {"Editable", "Other"}, mode
    print("CORE_EXPORT_OBSERVER_CASES=3")


def validate():
    validate_document_isolation()
    validate_cleanup_observers()
    validate_api_route()
    validate_composition_boundary()
    validate_retained_native_composition()
    validate_gui_route_guards()
    assert (
        api.run_staged_core_layout_export
        is exports.run_staged_core_layout_export
    )
    assert api.run_core_layout_export is exports.run_core_layout_export
    count = 0
    faults = (
        [("generation", index) for index in (0, 1, 3)]
        + [(name, 1) for name in ("missing", "empty", "directory", "symlink")]
        + [
            ("manifest-build", None),
            ("manifest-write", None),
            ("manifest-empty", None),
        ]
    )
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-staging-tests-"
    ) as tmp:
        base = Path(tmp)
        absent = base / "no-manifest"
        absent.mkdir()
        validate_absent_manifest_and_falsy_override(absent)
        count += 1
        for existing in (False, True):
            for fault in faults:
                root = base / str(count)
                root.mkdir()
                result, _plan, collaborators, _published = run_case(
                    root,
                    existing=existing,
                    fault=fault,
                )
                assert_aborted(result, collaborators)
                count += 1
            root = base / str(count)
            root.mkdir()
            result, plan, collaborators, published = run_case(
                root,
                existing=existing,
            )
            assert result["successful_files"] == 5
            assert result["failed_files"] == 0
            assert result["formats"] == sorted(
                name.upper() for name in FORMATS
            )
            assert published == [task["path"] for task in plan["tasks"]] + [
                plan["manifest_path"]
            ]
            for task in plan["tasks"]:
                assert Path(task["path"]).read_bytes() == payload(task)
            with open(
                plan["manifest_path"], newline="", encoding="utf-8"
            ) as handle:
                assert list(csv.DictReader(handle)) == collaborators.rows
            assert len(list(root.iterdir())) == 6
            assert_legacy_success_bytes(result, plan, collaborators)
            count += 1
            root = base / str(count)
            root.mkdir()
            result, plan, collaborators, published = run_case(
                root,
                existing=existing,
                publish_fault=1,
            )
            assert published == [plan["tasks"][0]["path"]]
            assert (
                result["successful_files"] == 1 and result["failed_files"] > 0
            )
            assert [item["success"] for item in result["results"]] == [
                True,
                False,
                False,
                False,
            ]
            assert result["manifest_path"] == ""
            after = file_witness(root)
            for name in ("core.svg", "core.stl", "core.step", "core.csv"):
                assert after.get(name) == collaborators.before.get(name)
            assert Path(published[0]).read_bytes() == payload(plan["tasks"][0])
            count += 1
        root = base / str(count)
        root.mkdir()
        result, _plan, collaborators, _published = run_case(
            root,
            existing=True,
            overwrite=False,
        )
        assert_aborted(result, collaborators)
        count += 1
        for final_kind in ("symlink", "directory"):
            root = base / str(count)
            root.mkdir()
            result, _plan, collaborators, _published = run_case(
                root,
                final_kind=final_kind,
            )
            assert_aborted(result, collaborators)
            count += 1
        for change in (
            lambda plan: plan["tasks"][1].update(
                path=plan["tasks"][0]["path"]
            ),
            lambda plan: plan.update(manifest_path=plan["tasks"][0]["path"]),
            lambda plan: plan["tasks"][0].update(
                path=str(base / "outside.dxf")
            ),
        ):
            root = base / str(count)
            root.mkdir()
            result, _plan, collaborators, _published = run_case(
                root,
                plan_change=change,
            )
            assert_aborted(result, collaborators)
            assert not collaborators.dispatched
            assert not (base / "outside.dxf").exists()
            count += 1
        for fault in (("interrupt", 1), ("manifest-interrupt", None)):
            root = base / str(count)
            root.mkdir()
            interruption = ControlledInterruption("controlled boundary")
            try:
                run_case(
                    root, existing=True, fault=fault, interruption=interruption
                )
            except ControlledInterruption as error:
                assert error is interruption
            else:
                raise AssertionError("The original interruption was absorbed")
            assert len(list(root.iterdir())) == 6
            for path in root.glob("core.*"):
                assert path.read_bytes() == ("preserve-" + path.name).encode()
            count += 1
        root = base / str(count)
        root.mkdir()
        result, _plan, _collaborators, _published = run_case(
            root,
            cleanup_fault=True,
        )
        assert result["successful_files"] == 5
        assert result["failed_files"] > 0
        assert "controlled cleanup" in "\n".join(result["failure_details"])
        count += 1
    print("CORE_EXPORT_STAGING_CASES=" + str(count))
    print(SENTINEL)


if __name__ == "__main__":
    validate()
