"""Observe one first Core Generate using the unchanged baseline witnesses."""

import copy
import importlib.util
import json
from pathlib import Path
import sys
import traceback
import types

import FreeCAD as App
import FreeCADGui as Gui

from tools import core_generate_attribution as attribution
from tracktemplate.adapters.export.core_layout_set import (
    CoreLayoutExportSetFiles,
)
from tracktemplate.adapters.freecad.core_export_document import (
    CoreExportDocument,
)
from tracktemplate.application.core_export_set import (
    run_atomic_core_layout_export,
)
from tracktemplate.application.core_dependency_manifest import (
    build_core_dependency_manifest,
)
from tracktemplate.compatibility.core_dependency_inventory import (
    prepare_core_dependency_manifest,
)


def _load_baseline(root):
    path = root / "tools/freecad_bridge/probes/core_generate_baseline.py"
    module = types.ModuleType("core_generate_attribution_witnesses")
    module.__dict__.update(globals())
    exec(
        attribution.baseline_definitions(path.read_text(), str(path)),
        module.__dict__,
    )
    return module


def _targets(module, witnesses):
    """Select coarse live boundaries; no product or routing replacement."""
    targets = []

    def add(name, function, classification="nested component"):
        targets.append(
            (name, classification, attribution.callable_code(function))
        )

    add("run_macro", module.run_macro, "operator action")
    add("input_dialog_construction", module.CurveInputDialog.__init__)
    for name in (
        "dialog_exec",
        "main_circle_centre",
        "build_concentric_core",
        "prepare_track_alignment",
        "create_template_plan_face",
        "create_template_shape",
        "_document_recompute",
        "run_production_preflight",
        "run_production_export",
        "show_production_export_summary",
        "dispatch_freecad_export",
    ):
        add(name, getattr(module, name))
    add("atomic_export", run_atomic_core_layout_export)
    add("export_document", CoreExportDocument.__call__)
    add("dependency_inventory", prepare_core_dependency_manifest)
    add("dependency_manifest", build_core_dependency_manifest)
    for name in (
        "open",
        "stage",
        "artifact_inventory",
        "stage_dependency_manifest",
        "validate",
        "publish",
        "cleanup",
    ):
        add("export_set_" + name, getattr(CoreLayoutExportSetFiles, name))
    monitors = [
        code
        for code in witnesses._measure_action.__code__.co_consts
        if isinstance(code, types.CodeType) and code.co_name == "monitor"
    ]
    if len(monitors) != 1:
        raise ValueError("Baseline dialog monitor code is ambiguous")
    targets.append(("dialog_monitor", "harness enclosing", monitors[0]))
    return targets


def _run_attribution():
    root = Path(globals()["_PHASE3_REPOSITORY_ROOT"])
    module = sys.modules[globals()["TRACKTEMPLATE_WORKFLOW_MODULE_NAME"]]
    witnesses = _load_baseline(root)
    require = witnesses._require
    mode = globals()["TRACKTEMPLATE_ATTRIBUTION_MODE"]
    require(mode in ("control", "observed"), "Unknown observation mode")
    directory = (
        Path(globals()["TRACKTEMPLATE_ATTRIBUTION_DIRECTORY"]) / "probe"
    )
    directory.mkdir()
    document = App.ActiveDocument
    require(
        document is not None and document.FileName,
        "Open the saved copied fixture first",
    )
    require(globals()["_PHASE3_PRODUCT_COMPOSITION"], "Normal route required")
    qualification = globals()["_PHASE3_QUALIFICATION"]
    host = qualification["compatibility_evaluation"]["matched_profile_id"]
    require(host == witnesses.HOST_PROFILE_ID, "Unexpected host profile")
    session = globals()["_PHASE3_SESSION"]
    routing = globals()["_PHASE3_ROUTING"]
    bindings = {
        name: module.__dict__[name] for name in routing["function_names"]
    }
    spec = importlib.util.spec_from_file_location(
        "core_generate_attribution_export_witness",
        root / "tests/freecad_validate_core_export_atomic.py",
    )
    export_witness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(export_witness)
    group = App.ParamGet(module.LAST_INPUTS_PARAMETER_PATH)
    preferences = witnesses._preferences(group)
    pending = copy.deepcopy(module._PENDING_IMPORTED_CONFIGURATION)
    registry = dict(App.listDocuments())
    original_profiler = sys.getprofile()
    observer = attribution.Observer(_targets(module, witnesses))
    action = {"label": "first-generate", "status": "incomplete"}
    report = {
        "schema_version": 1,
        "profile_id": attribution.PROFILE,
        "host_profile_id": host,
        "host_qualification": qualification,
        "mode": mode,
        "status": "incomplete",
        "checks": {},
        "action": action,
        "routing": routing,
        "attribution": None,
        "measurement_boundary": "baseline _measure_action: one run_macro call",
        "limitations": [
            "Fresh GUI process, first Generate; startup and fixture load "
            "excluded.",
            "Dialog construction, configuration and 25ms polling "
            "are included.",
            "Deep output/geometry checks, capture and disposal are excluded.",
            "Selected Python frames on the GUI thread only; native work "
            "is enclosed or unobserved.",
            "Process CPU is accumulated across all threads during "
            "each interval.",
            "Each remainder includes unobserved work and observer cost; "
            "it is not a named product stage.",
            "External baseline float milliseconds are rounded to ns "
            "for reconciliation.",
            "Observer differences are matched timing differences, "
            "not corrected product costs.",
            "No cold OS-cache, warm-reuse, budget, improvement "
            "or acceptance claim.",
        ],
    }
    try:
        witnesses.ordinary_track_snapshot(
            module,
            document,
            enforce_expected_hash=False,
            expected_macro_version="10.2A8A7B15",
        )
        initial = witnesses.ordinary_track_document_snapshot(module, document)
        parent = directory / "outputs"
        parent.mkdir()
        (parent / "previous-output.txt").write_text(
            "preserve previous output\n"
        )
        previous = witnesses._file_state(parent)
        for key in (
            module.LAST_INPUTS_PARAMETER_KEY,
            module.LAST_INPUTS_DOCUMENT_MAP_KEY,
        ):
            group.RemString(key)
        module._PENDING_IMPORTED_CONFIGURATION = None
        children = set(parent.iterdir())
        if mode == "observed":
            try:
                with observer:
                    witnesses._measure_action(module, document, parent, action)
            finally:
                report["observer_raw"] = {
                    "spans": observer.spans,
                    "errors": observer.errors,
                    "mapping": observer.mapping,
                    "restored": observer.restored,
                }
            report["attribution"] = observer.result(action)
        else:
            require(original_profiler is None, "Existing profiler in control")
            witnesses._measure_action(module, document, parent, action)
        additions = set(parent.iterdir()) - children
        require(
            len(additions) == 1 and next(iter(additions)).is_dir(),
            "Expected exactly one published directory",
        )
        child = next(iter(additions))
        require(not child.name.startswith("."), "Unpublished staging path")
        require(
            dict(App.listDocuments()) == registry
            and App.ActiveDocument is document,
            "Document registry changed",
        )
        after = witnesses.ordinary_track_document_snapshot(module, document)
        witnesses.compare_create_time_document_to_base(
            *[
                witnesses.normalise_version_migration_snapshot(
                    value,
                    ("10.2A8A7B14", "10.2A8A7B15"),
                )
                for value in (initial, after)
            ]
        )
        contract = witnesses.create_time_export_document_snapshot(
            after,
            enforce_expected_hash=False,
        )
        require(len(document.Objects) == 9, "Object count differs")
        proof = witnesses._validate_outputs(
            module, document, child, export_witness
        )
        require(
            dict(App.listDocuments()) == registry
            and App.ActiveDocument is document,
            "Deep validation leaked documents",
        )
        current = witnesses._file_state(parent)
        require(
            all(
                current.get(name) == value for name, value in previous.items()
            ),
            "Previous output changed",
        )
        digest = witnesses._digest(
            {
                "document": contract["semantic_sha256"],
                "logical_output": proof["logical_output_sha256"],
                "geometry": proof["export_metrics_sha256"],
            }
        )
        action.update(
            proof,
            status="completed",
            output_dir=str(child),
            payload_count=witnesses.EXPECTED_TASK_COUNT,
            output_contract_sha256=digest,
            document_semantic_sha256=contract["semantic_sha256"],
            previous_outputs_preserved=True,
        )
        require(
            all(
                module.__dict__[name] is value
                for name, value in bindings.items()
            )
            and session.routing_record() == routing,
            "Product routing changed",
        )
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.activeDocument().activeView().fitAll()
        Gui.updateGui()
        capture = directory / "completed-product.png"
        Gui.activeDocument().activeView().saveImage(str(capture), 1280, 900)
        require(
            capture.is_file() and capture.stat().st_size > 0, "Capture absent"
        )
        report.update(
            capture=str(capture),
            capture_sha256=attribution.baseline._hash(capture),
        )
        report["checks"].update(
            previous_outputs_preserved=True,
            actual_export_geometry_verified=True,
            document_registry_preserved=True,
            routing_preserved=True,
            dependency_classification_verified=True,
        )
        report.update(status="completed", sentinel=attribution.SENTINEL)
    except BaseException:
        report.update(status="failed", traceback=traceback.format_exc())
        raise
    finally:
        try:
            try:
                witnesses._restore_preferences(group, preferences)
            finally:
                module._PENDING_IMPORTED_CONFIGURATION = pending
            report["checks"].update(
                preferences_restored=witnesses._preferences(group)
                == preferences,
                pending_configuration_restored=(
                    module._PENDING_IMPORTED_CONFIGURATION == pending
                ),
                observer_restored=sys.getprofile() is original_profiler,
            )
            require(
                all(
                    report["checks"][key]
                    for key in (
                        "preferences_restored",
                        "pending_configuration_restored",
                        "observer_restored",
                    )
                ),
                "State restoration failed",
            )
        except BaseException:
            report.update(
                status="failed", restoration_traceback=traceback.format_exc()
            )
            report.pop("sentinel", None)
            raise
        finally:
            attribution.baseline._write(directory / "probe.json", report)
    attribution.validate_probe(report, mode)
    print(json.dumps(report, sort_keys=True))


_run_attribution()
