#!/usr/bin/env python3
"""Compare frozen core-layout export orchestration with the modular route."""

import ast
import copy
import hashlib
import importlib.util
import inspect
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import types
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
B14 = ROOT / "AdvancedTurnout.FCMacro"
B15 = ROOT / (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
LEGACY_NAME = "run_production_export"
LEGACY_DEFINITION_BYTES = 2542
LEGACY_DEFINITION_SHA256 = (
    "2de2b2283d550037c3ee0edecc5768ffc802f4c14870db1c326d6e3ff5c94a03"
)
SENTINEL = "Phase 7 core-layout export validation passed"
NORMALISER_SENTINEL = (
    "Phase 7 core-layout export recipe normaliser validation passed"
)
GUI_RUNNER = (
    ROOT
    / "tools"
    / "freecad_bridge"
    / "run_phase7_core_layout_export_workflow.py"
)
GUI_FINISHER = (
    ROOT
    / "tools"
    / "freecad_bridge"
    / "probes"
    / "finish_phase7_core_layout_export_workflow.py"
)


class ControlledInterruption(BaseException):
    """Represent one interruption outside the caught Exception boundary."""


def _expect_runtime_error(operation, message):
    try:
        operation()
    except RuntimeError as error:
        assert message in str(error)
    else:
        raise AssertionError("Expected RuntimeError containing {!r}".format(message))


def _routed_gui_report(harness, route):
    envelope = harness.ROUTE_ENVELOPES[route]
    export_routing = {
        "route": route,
        "comparison_route_available": True,
        "command_name": "run_production_export",
        "host_binding_name": "run_production_export",
        "mixed_route": False,
    }
    if route == harness.MODULAR_ROUTE:
        export_routing.update({
            "contract_id": "tracktemplate:phase7:core-layout-export:1",
            "comparison_route_available": False,
            "command_name": "run_core_layout_export",
        })
    return {
        "development_checkpoint": "10.2A8A7B16",
        "matched_profile_id": sorted(harness.QUALIFIED_PROFILE_IDS)[0],
        "routing": {
            "schema_version": envelope["schema_version"],
            "route": route,
            "function_names": list(envelope["function_names"]),
            "caller_names": list(envelope["caller_names"]),
        },
        "active_route_after_workflow": route,
        "workflow_version": "10.2A8A7B15",
        "binding_identity_preserved": True,
        "core_layout_export_binding_identity_preserved": True,
        "core_layout_export_routing": export_routing,
        "recipe_contract": {"stable": True},
    }


def _validate_gui_harness():
    spec = importlib.util.spec_from_file_location(
        "_phase7_core_layout_export_gui_harness",
        GUI_RUNNER,
    )
    assert spec is not None and spec.loader is not None
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)

    assert os.access(harness.WRAPPER_PATH, os.X_OK)
    wrapper_source = harness.WRAPPER_PATH.read_text(encoding="utf-8")
    assert "TRACKTEMPLATE_BRIDGE_PORT" in wrapper_source
    assert '"--port"' in inspect.getsource(harness._run_pair)
    expected_port_error = (
        "Phase 7 core-layout export requires bridge port 19875; "
        "nondefault ports are not isolated."
    )
    with tempfile.TemporaryDirectory() as wrapper_temporary:
        fake_bridge_dir = (
            pathlib.Path(wrapper_temporary) / "tools" / "freecad_bridge"
        )
        fake_bridge_dir.mkdir(parents=True)
        fake_wrapper = fake_bridge_dir / harness.WRAPPER_PATH.name
        fake_wrapper.write_text(wrapper_source, encoding="utf-8")
        fake_wrapper.chmod(0o755)
        launch_marker = fake_bridge_dir / "unexpected-launch"
        fake_isolated = fake_bridge_dir / "run-isolated"
        fake_isolated.write_text(
            "#!/usr/bin/env bash\ntouch \"{}\"\n".format(launch_marker),
            encoding="utf-8",
        )
        fake_isolated.chmod(0o755)
        for port_arguments in (("--port", "19876"), ("--port=19876",)):
            rejected = subprocess.run(
                [
                    str(fake_wrapper),
                    "--route",
                    harness.LEGACY_ROUTE,
                    *port_arguments,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            assert rejected.returncode == 2
            assert rejected.stderr.strip() == expected_port_error
            assert not launch_marker.exists()

    with (
        mock.patch.object(
            sys,
            "argv",
            [str(GUI_RUNNER), "--port", "19876"],
        ),
        mock.patch.object(harness, "_run_pair") as run_pair,
        mock.patch.object(harness, "_run_route") as run_route,
    ):
        try:
            harness.main()
        except SystemExit as error:
            assert str(error) == expected_port_error
        else:
            raise AssertionError("A nondefault bridge port passed")
        run_pair.assert_not_called()
        run_route.assert_not_called()
    for route in harness.ROUTES:
        compile(
            harness._embedded_workflow_source(
                route,
                pathlib.Path("/tmp/phase7-harness/workflow.FCStd"),
            ),
            "<phase7-core-layout-export-{}>".format(route),
            "exec",
        )

    with tempfile.TemporaryDirectory() as temporary:
        temporary_root = pathlib.Path(temporary)
        run_root = temporary_root / "runs"
        with mock.patch.object(harness, "RUN_ROOT", run_root):
            contained = harness._new_run_directory(
                run_root / "contained",
                "test",
            )
            assert contained == (run_root / "contained").resolve()
            assert contained.is_dir()
            try:
                harness._new_run_directory(contained, "test")
            except SystemExit as error:
                assert "already exists" in str(error)
            else:
                raise AssertionError("An existing GUI run directory passed")
            try:
                harness._new_run_directory(
                    temporary_root / "outside",
                    "test",
                )
            except SystemExit as error:
                assert "must remain under" in str(error)
            else:
                raise AssertionError("An outside GUI run directory passed")
            escape_target = temporary_root / "escape-target"
            escape_target.mkdir()
            escape_link = run_root / "escape-link"
            escape_link.symlink_to(escape_target, target_is_directory=True)
            try:
                harness._new_run_directory(
                    escape_link / "child",
                    "test",
                )
            except SystemExit as error:
                assert "must remain under" in str(error)
            else:
                raise AssertionError("A symlink-escaped GUI run directory passed")

        for route in harness.ROUTES:
            report = _routed_gui_report(harness, route)
            expected_envelope = harness.ROUTE_ENVELOPES[route]
            expected_shape = {
                harness.LEGACY_ROUTE: (1, 3, 3),
                harness.MODULAR_ROUTE: (16, 25, 40),
            }[route]
            assert (
                expected_envelope["schema_version"],
                len(expected_envelope["function_names"]),
                len(expected_envelope["caller_names"]),
            ) == expected_shape
            assert harness._validate_routed_report(report, route) == {
                "stable": True,
            }
            other_route = next(
                candidate for candidate in harness.ROUTES if candidate != route
            )
            other_envelope = harness.ROUTE_ENVELOPES[other_route]
            for key, value in (
                ("schema_version", other_envelope["schema_version"]),
                ("function_names", expected_envelope["function_names"][:-1]),
                (
                    "function_names",
                    expected_envelope["function_names"] + ["unexpected_function"],
                ),
                ("function_names", tuple(expected_envelope["function_names"])),
                ("function_names", other_envelope["function_names"]),
                ("caller_names", expected_envelope["caller_names"][:-1]),
                (
                    "caller_names",
                    expected_envelope["caller_names"] + ["unexpected_caller"],
                ),
                ("caller_names", tuple(expected_envelope["caller_names"])),
                ("caller_names", other_envelope["caller_names"]),
            ):
                changed = copy.deepcopy(report)
                changed["routing"][key] = value
                _expect_runtime_error(
                    lambda changed=changed, route=route: (
                        harness._validate_routed_report(changed, route)
                    ),
                    "evidence drifted",
                )

        clean_state = {"cleanup": {"closed": [], "remaining": []}}
        harness._validate_cleanup(clean_state, harness.LEGACY_ROUTE)
        for state in (
            {},
            {"cleanup_error": "controlled cleanup failure"},
            {"cleanup": {"remaining": []}},
            {"cleanup": {"closed": [], "remaining": ["Document"]}},
        ):
            _expect_runtime_error(
                lambda state=state: harness._validate_cleanup(
                    state,
                    harness.LEGACY_ROUTE,
                ),
                "route",
            )
        assert "_validate_cleanup(state, args.route)" in inspect.getsource(
            harness._run_route
        )
        route_source = inspect.getsource(harness._run_route)
        assert route_source.index('state["workflow"] = report') < route_source.index(
            "contract = _validate_routed_report(report, args.route)"
        )
        assert "_load_completed_route(" in route_source
        assert "result_path" in route_source

        completed_path = temporary_root / "completed.json"
        expected_sources = {"source.py": "a" * 64}
        completed = {
            "status": "completed",
            "route": harness.LEGACY_ROUTE,
            "workflow": _routed_gui_report(harness, harness.LEGACY_ROUTE),
            "source_sha256": expected_sources,
            "source_sha256_after": expected_sources,
        }
        for cleanup_state, message in (
            ({}, "shutdown evidence"),
            ({"cleanup_error": "controlled cleanup failure"}, "cleanup failed"),
            ({"cleanup": []}, "shutdown evidence"),
            ({"cleanup": {"remaining": []}}, "shutdown evidence"),
            ({"cleanup": {"closed": [], "remaining": ["Document"]}},
             "shutdown evidence"),
        ):
            candidate = copy.deepcopy(completed)
            candidate.update(cleanup_state)
            completed_path.write_text(json.dumps(candidate), encoding="utf-8")
            _expect_runtime_error(
                lambda: harness._load_completed_route(
                    completed_path,
                    harness.LEGACY_ROUTE,
                    expected_sources,
                ),
                message,
            )

        completed["cleanup"] = {"closed": ["Document"], "remaining": []}
        completed_path.write_text(json.dumps(completed), encoding="utf-8")
        assert harness._load_completed_route(
            completed_path,
            harness.LEGACY_ROUTE,
            expected_sources,
        )["cleanup"]["remaining"] == []
        for source_change in ("missing", "extra", "changed"):
            candidate = copy.deepcopy(completed)
            if source_change == "missing":
                candidate.pop("source_sha256")
            elif source_change == "extra":
                candidate["source_sha256_after"] = {
                    **expected_sources,
                    "extra.py": "b" * 64,
                }
            else:
                candidate["source_sha256_after"] = {
                    "source.py": "c" * 64,
                }
            completed_path.write_text(json.dumps(candidate), encoding="utf-8")
            _expect_runtime_error(
                lambda: harness._load_completed_route(
                    completed_path,
                    harness.LEGACY_ROUTE,
                    expected_sources,
                ),
                "source map drifted",
            )

    relative_source_paths = {
        str(path.relative_to(ROOT)) for path in harness.SOURCE_PATHS
    }
    required_source_paths = {
        "TrackTemplate.FCMacro",
        "tools/freecad_bridge/freecad-cli",
        "tools/freecad_bridge/freecad_export_metrics.py",
        "tools/freecad_bridge/launch-freecad",
        "tools/freecad_bridge/ordinary_track_edit_recipe.py",
        "tools/freecad_bridge/ordinary_track_export_recipe.py",
        "tools/freecad_bridge/ordinary_track_recipe.py",
        "tools/freecad_bridge/orchestration.py",
        "tools/freecad_bridge/phase3_transition_workflow_recipe.py",
        "tools/freecad_bridge/probes/b14_ordinary_create_export_driver.py",
        "tools/freecad_bridge/probes/finish_phase7_core_layout_export_workflow.py",
        "tools/freecad_bridge/probes/load_phase3_transition_workflow.py",
        "tools/freecad_bridge/run-phase7-core-layout-export-workflow",
        "tools/freecad_bridge/run-isolated",
        "tools/freecad_bridge/run_phase7_core_layout_export_workflow.py",
        "tools/semantic_compare.py",
        "tracktemplate/api.py",
        "tracktemplate/application/core_layout_export.py",
        "tracktemplate/compatibility/b15_workflow_host.py",
        "tracktemplate/compatibility/transition_workflow.py",
    }
    assert required_source_paths <= relative_source_paths
    source_hashes = harness._source_hashes()
    assert set(source_hashes) == relative_source_paths
    assert len(source_hashes) == len(harness.SOURCE_PATHS)
    assert all(
        len(digest) == 64 and set(digest) <= set("0123456789abcdef")
        for digest in source_hashes.values()
    )
    source_state = {
        "source_sha256": source_hashes,
        "source_sha256_after": source_hashes,
    }
    harness._validate_source_hashes(
        source_hashes,
        source_state,
        harness.LEGACY_ROUTE,
    )
    changed_sources = copy.deepcopy(source_state)
    changed_sources["source_sha256_after"] = dict(source_hashes)
    first_path = sorted(source_hashes)[0]
    changed_sources["source_sha256_after"][first_path] = "0" * 64
    _expect_runtime_error(
        lambda: harness._validate_source_hashes(
            source_hashes,
            changed_sources,
            harness.LEGACY_ROUTE,
        ),
        "source map drifted",
    )
    pair_source = inspect.getsource(harness._run_pair)
    assert "_load_completed_route(" in pair_source
    assert "source_hashes_before" in pair_source

    completed = subprocess.run(
        [sys.executable, str(GUI_FINISHER)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == NORMALISER_SENTINEL


def _legacy_functions():
    functions = []
    for path in (B14, B15):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        node = next(
            item for item in tree.body
            if isinstance(item, ast.FunctionDef) and item.name == LEGACY_NAME
        )
        definition = "".join(
            source.splitlines(keepends=True)[node.lineno - 1:node.end_lineno]
        )
        encoded = definition.encode("utf-8")
        assert len(encoded) == LEGACY_DEFINITION_BYTES
        assert hashlib.sha256(encoded).hexdigest() == LEGACY_DEFINITION_SHA256
        namespace = {"os": os}
        exec(
            compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"),
            namespace,
        )
        functions.append(namespace[LEGACY_NAME])
    assert inspect.getsource(functions[0]) == inspect.getsource(functions[1])
    return functions


class Collaborators:
    """Supply deterministic host operations to both orchestration routes."""

    def __init__(self, results, *, manifest_error=None):
        self.results = results
        self.manifest_error = manifest_error
        self.events = []

    def execute_export_tasks(self, document, plan, config, exporter_override=None):
        self.events.append((
            "execute",
            document,
            plan,
            config,
            exporter_override,
        ))
        return self.results

    def build_manifest_rows(
        self,
        results,
        skipped,
        set_id,
        platform_config,
        formation_config,
        registration_config,
        template_assembly_config,
    ):
        self.events.append((
            "manifest-rows",
            results,
            skipped,
            set_id,
            platform_config,
            formation_config,
            registration_config,
            template_assembly_config,
        ))
        return [{"set": set_id, "result_count": len(results)}]

    def write_export_manifest(self, path, rows):
        self.events.append(("write-manifest", path, rows))
        if self.manifest_error is not None:
            raise self.manifest_error

    def failed_export_report(self, item):
        self.events.append(("failed-report", item))
        task = item["task"]
        return (
            "{}:{}".format(task["format"], item["error"]),
            "{}|{}".format(task["path"], item["error"]),
        )

    def skipped_export_report(self, item):
        self.events.append(("skipped-report", item))
        return (
            "{}:{}".format(item.get("format", ""), item["reason"]),
            "{}|{}".format(item["record"]["role"], item["reason"]),
        )

    def legacy_namespace(self):
        return {
            "execute_export_tasks": self.execute_export_tasks,
            "build_manifest_rows": self.build_manifest_rows,
            "write_export_manifest": self.write_export_manifest,
            "_failed_export_report": self.failed_export_report,
            "_skipped_export_report": self.skipped_export_report,
        }

    def candidate_keywords(self):
        return {
            "execute_export_tasks": self.execute_export_tasks,
            "build_manifest_rows": self.build_manifest_rows,
            "write_export_manifest": self.write_export_manifest,
            "failed_export_report": self.failed_export_report,
            "skipped_export_report": self.skipped_export_report,
        }


def _inputs(manifest_path="/exports/core-layout.csv"):
    plan = {
        "tasks": [
            {
                "format": "dxf",
                "path": "/exports/layout.dxf",
                "records": [{"role": "Template"}],
            },
            {
                "format": "step",
                "path": "/exports/layout.step",
                "records": [{"role": "PlatformBody"}],
            },
        ],
        "skipped": [{
            "format": "svg",
            "reason": "no planar record",
            "record": {"role": "StraightTrackTemplate"},
        }],
        "manifest_path": manifest_path,
    }
    results = [
        {"task": plan["tasks"][0], "success": True, "error": ""},
        {
            "task": plan["tasks"][1],
            "success": False,
            "error": "controlled STEP failure",
        },
    ]
    return {
        "document": object(),
        "plan": plan,
        "config": {
            "output_directory": "/exports",
            "overwrite_existing": False,
        },
        "set_id": "SET-007",
        "platform_config": {"platform_height": 15.0},
        "formation_config": {"board_thickness": 3.0},
        "registration_config": {"joint_type": "Registration"},
        "template_assembly_config": {"joint_type": "Butt"},
        "exporter_override": object(),
        "results": results,
    }


def _call_arguments(inputs):
    return (
        inputs["document"],
        inputs["plan"],
        inputs["config"],
        inputs["set_id"],
        inputs["platform_config"],
        inputs["formation_config"],
        inputs["registration_config"],
        inputs["template_assembly_config"],
        inputs["exporter_override"],
    )


def _observe(function, inputs, collaborators, *, candidate):
    before = copy.deepcopy({
        key: value for key, value in inputs.items()
        if key not in {"document", "exporter_override", "results"}
    })
    if candidate:
        result = function(
            *_call_arguments(inputs),
            **collaborators.candidate_keywords(),
        )
    else:
        function.__globals__.update(collaborators.legacy_namespace())
        result = function(*_call_arguments(inputs))
    after = {
        key: value for key, value in inputs.items()
        if key not in {"document", "exporter_override", "results"}
    }
    assert after == before
    return result, collaborators.events


def _host_independent_import():
    script = """
import builtins
import pathlib
import sys
root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
original = builtins.__import__
def blocked(name, *args, **kwargs):
    if name.split('.')[0] in {'FreeCAD', 'FreeCADGui', 'Part', 'PySide', 'PySide2', 'PySide6', 'pivy'}:
        raise AssertionError('host import: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = blocked
from tracktemplate import api
from tracktemplate.application import core_layout_export
assert api.run_core_layout_export is core_layout_export.run_core_layout_export
assert not any(name.split('.')[0] in {'FreeCAD', 'FreeCADGui', 'Part', 'PySide', 'PySide2', 'PySide6', 'pivy'} for name in sys.modules)
"""
    subprocess.run(
        [sys.executable, "-c", script, str(ROOT)],
        cwd=ROOT,
        check=True,
    )


def _adapter_and_route(api, workflow):
    inputs = _inputs()
    collaborators = Collaborators(inputs["results"])
    module = types.ModuleType("_core_layout_export_fixture")
    namespace = module.__dict__
    namespace["COLLABORATORS"] = collaborators
    exec(
        "def execute_export_tasks(*args, **kwargs):\n"
        "    return COLLABORATORS.execute_export_tasks(*args, **kwargs)\n"
        "def build_manifest_rows(*args, **kwargs):\n"
        "    return COLLABORATORS.build_manifest_rows(*args, **kwargs)\n"
        "def write_export_manifest(*args, **kwargs):\n"
        "    return COLLABORATORS.write_export_manifest(*args, **kwargs)\n"
        "def _failed_export_report(*args, **kwargs):\n"
        "    return COLLABORATORS.failed_export_report(*args, **kwargs)\n"
        "def _skipped_export_report(*args, **kwargs):\n"
        "    return COLLABORATORS.skipped_export_report(*args, **kwargs)\n"
        "def run_production_export(*_args, **_kwargs):\n"
        "    raise AssertionError('the inherited orchestration remained active')\n"
        "def run_macro():\n"
        "    return run_production_export(*CALL_ARGUMENTS)\n",
        namespace,
    )
    namespace["CALL_ARGUMENTS"] = _call_arguments(inputs)
    original_export = namespace["run_production_export"]

    class BaseSession:
        def __init__(self):
            self.module = module
            self._host = types.SimpleNamespace(source_sha256="host-sha256")

        def routing_record(self):
            return {"schema_version": 16, "function_names": ["retained"]}

        def launch_workflow(self):
            return self.module.run_macro()

    session = workflow.ModularCoreLayoutWorkflowSession(
        BaseSession(), api.run_core_layout_export,
    )
    assert session.routing_record() == {
        "schema_version": 16,
        "function_names": ["retained"],
    }
    record = session.core_layout_export_routing_record()
    assert record == {
        "schema_version": 1,
        "contract_id": "tracktemplate:phase7:core-layout-export:1",
        "route": "modular",
        "comparison_route_available": False,
        "command_name": "run_core_layout_export",
        "host_binding_name": "run_production_export",
        "caller_name": "run_macro",
        "workflow_version": workflow.EXPECTED_WORKFLOW_VERSION,
        "workflow_source_sha256": "host-sha256",
        "mixed_route": False,
    }
    adapter = module.run_production_export
    assert type(adapter) is workflow._CoreLayoutExportAdapter
    signature = inspect.signature(adapter)
    assert tuple(signature.parameters) == (
        "doc", "plan", "config", "set_id", "platform_config",
        "formation_config", "registration_config",
        "template_assembly_config", "exporter_override",
    )
    result = session.launch_workflow()
    assert result["successful_files"] == 2
    assert result["failed_files"] == 1
    assert result["skipped_objects"] == 1

    module.run_production_export = original_export
    try:
        session.core_layout_export_routing_record()
    except workflow.TransitionWorkflowError as error:
        assert "mixed" in str(error)
    else:
        raise AssertionError("A mixed export orchestration route passed")
    assert session.launch_workflow() == result

    module.execute_export_tasks = lambda *_args, **_kwargs: []
    try:
        session.core_layout_export_routing_record()
    except workflow.TransitionWorkflowError as error:
        assert "operation" in str(error)
    else:
        raise AssertionError("A changed inherited export operation passed")


def validate():
    sys.path.insert(0, str(ROOT))
    from tracktemplate import api
    from tracktemplate.application import core_layout_export
    from tracktemplate.compatibility import transition_workflow as workflow

    legacy_b14, legacy_b15 = _legacy_functions()
    assert api.run_core_layout_export is core_layout_export.run_core_layout_export
    assert "run_core_layout_export" in api.__all__
    signature = inspect.signature(api.run_core_layout_export)
    assert tuple(signature.parameters) == (
        "doc", "plan", "config", "set_id", "platform_config",
        "formation_config", "registration_config",
        "template_assembly_config", "exporter_override",
        "execute_export_tasks", "build_manifest_rows",
        "write_export_manifest", "failed_export_report",
        "skipped_export_report",
    )
    assert all(
        signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        for name in (
            "execute_export_tasks", "build_manifest_rows",
            "write_export_manifest", "failed_export_report",
            "skipped_export_report",
        )
    )
    _host_independent_import()

    for manifest_path, manifest_error in (
        ("/exports/core-layout.csv", None),
        ("", None),
        ("/exports/core-layout.csv", OSError("controlled manifest failure")),
    ):
        inputs = _inputs(manifest_path)
        expected, expected_events = _observe(
            legacy_b14,
            inputs,
            Collaborators(inputs["results"], manifest_error=manifest_error),
            candidate=False,
        )
        observed, observed_events = _observe(
            api.run_core_layout_export,
            inputs,
            Collaborators(inputs["results"], manifest_error=manifest_error),
            candidate=True,
        )
        assert observed == expected
        assert observed_events == expected_events
        legacy_b15_result, legacy_b15_events = _observe(
            legacy_b15,
            inputs,
            Collaborators(inputs["results"], manifest_error=manifest_error),
            candidate=False,
        )
        assert legacy_b15_result == expected
        assert legacy_b15_events == expected_events

    inputs = _inputs()
    interruption = Collaborators(
        inputs["results"], manifest_error=ControlledInterruption("stop"),
    )
    try:
        _observe(
            api.run_core_layout_export,
            inputs,
            interruption,
            candidate=True,
        )
    except ControlledInterruption as error:
        assert str(error) == "stop"
    else:
        raise AssertionError("A BaseException at manifest write was absorbed")

    with mock.patch.object(
        workflow.ModularCoreLayoutWorkflowSession,
        "_validate_core_layout_export_binding",
        side_effect=RuntimeError("controlled route failure"),
    ):
        inputs = _inputs()
        collaborators = Collaborators(inputs["results"])
        module = types.ModuleType("_core_layout_export_rollback_fixture")
        namespace = module.__dict__
        namespace["COLLABORATORS"] = collaborators
        exec(
            "def execute_export_tasks(*args, **kwargs):\n"
            "    return COLLABORATORS.execute_export_tasks(*args, **kwargs)\n"
            "def build_manifest_rows(*args, **kwargs):\n"
            "    return COLLABORATORS.build_manifest_rows(*args, **kwargs)\n"
            "def write_export_manifest(*args, **kwargs):\n"
            "    return COLLABORATORS.write_export_manifest(*args, **kwargs)\n"
            "def _failed_export_report(*args, **kwargs):\n"
            "    return COLLABORATORS.failed_export_report(*args, **kwargs)\n"
            "def _skipped_export_report(*args, **kwargs):\n"
            "    return COLLABORATORS.skipped_export_report(*args, **kwargs)\n"
            "def run_macro():\n"
            "    return run_production_export\n",
            namespace,
        )
        original = object()
        namespace["run_production_export"] = original
        base = types.SimpleNamespace(
            module=module,
            _host=types.SimpleNamespace(source_sha256="host-sha256"),
        )
        try:
            workflow.ModularCoreLayoutWorkflowSession(
                base, api.run_core_layout_export,
            )
        except RuntimeError as error:
            assert str(error) == "controlled route failure"
        else:
            raise AssertionError("The controlled route failure was lost")
        assert module.run_production_export is original

    _adapter_and_route(api, workflow)
    _validate_gui_harness()
    print(SENTINEL)


if __name__ == "__main__":
    validate()
