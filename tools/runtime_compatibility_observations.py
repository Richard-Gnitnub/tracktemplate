"""Extract the fixed matrix's public observations from original run evidence.

The caller supplies its verified assessment manifest. This module executes no
fixture, FreeCAD command or geometry operation. It checks original invocation
and cleanup evidence, reads only source-specific result fields, and delegates
the final public boundary to compatibility_evidence_output. Rejected original
diagnostics and partially prepared projection files stay in owned scratch.
Readiness is a separate group; this matrix contributes at most 23 results and
159 images. A matrix result never admits a runtime or authorises ZY.
"""

import hashlib
import io
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from tools import compatibility_evidence_output as output
from tools import prepare_runtime_assessment as assessment
from tools import runtime_compatibility_diagnostics as diagnostics


MAX_PRIVATE_BYTES = 16 * 1024 * 1024
ENTRY_MARKER = "TRACKTEMPLATE_MATRIX_ENTRY="
DONE_MARKER = "TRACKTEMPLATE_MATRIX_ENTRY_COMPLETE"
BASE_IDENTITY = {"bytes": output.BASE_BYTES, "sha256": output.BASE_SHA256}
RECEIPT_PREFIXES = {
    "straight-generation": "Straight/station evidence: ",
    "phase3-four-routes": "Phase 3 routed workflow series: ",
    "phase7-export-pair": "Phase 7 core-layout export workflow pair: ",
    "phase8-turnout_toe": "Phase 8 turnout toe GUI evidence: ",
    "phase8-crossover_preflight": "Phase 8 crossover GUI evidence: ",
    "phase8-crossover_b4_recovery": "Phase 8 crossover B4 GUI evidence: ",
    "phase8-crossover_edit_recovery": "Phase 8 crossover edit GUI evidence: ",
    "phase8-crossover_host_integration_recovery": (
        "Phase 8 crossover integration GUI evidence: "
    ),
    "phase8-turnout_host_integration_recovery": (
        "Phase 8 turnout integration GUI evidence: "
    ),
    "phase8-straight_host_turnout": (
        "Phase 8 straight-host turnout GUI evidence: "
    ),
    "phase8-straight_host_crossover": "Phase 8 straight-host GUI evidence: ",
    "phase8-straight_crossover_b4": "Phase 8 straight B4 GUI evidence: ",
    "selected-export-document": "SELECTED_EXPORT_DOCUMENT_GUI_EVIDENCE=",
    "selected-export-set": "SELECTED_EXPORT_SET_GUI_EVIDENCE=",
    "selected-export-rollback": "SELECTED_EXPORT_ROLLBACK_GUI_EVIDENCE=",
}
for _group in ("direct", "main-button"):
    RECEIPT_PREFIXES["phase8-turnout-selected-" + _group] = (
        "Phase 8 turnout selected export GUI evidence: "
    )
for _selection in ("highlighted", "preselected"):
    for _group in ("direct", "main-button"):
        RECEIPT_PREFIXES[
            "phase8-crossover-selected-" + _selection + "-" + _group
        ] = "Phase 8 crossover selected export GUI evidence: "

PHASE5_IMAGES = {
    "edited-transition-editor.png": (
        "representative_multi_object_result/editor_edited_image"
    ),
    "selected-transition-editor.png": (
        "representative_multi_object_result/editor_selected_image"
    ),
    "representative-entry-exit-reopened.png": (
        "representative_multi_object_result/reopened_attachment/reopened_image"
    ),
    "explicit-lifecycle-editor.png": (
        "transition_editing_lifecycle_result/editor_image"
    ),
    "explicit-lifecycle-scene.png": (
        "transition_editing_lifecycle_result/scene_image"
    ),
    **{
        name + ".png": "result/screenshots/" + name.replace("-", "_")
        for name in (
            "change-back", "change-back-redo", "change-back-undo", "edited",
            "hidden", "recovered", "redo", "reopened", "undo", "visible",
        )
    },
}


def _require(condition, message):
    if not condition:
        raise output.EvidenceError(message)


def _at(value, pointer):
    """Read a fixed source field; never use a data-supplied field path."""
    try:
        for part in pointer.split("/"):
            value = value[int(part)] if isinstance(value, list) else value[part]
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise output.EvidenceError("original source field missing") from error
    return value


def _read_json(path):
    return output._json(output._read(Path(path), MAX_PRIVATE_BYTES))


def _read_text(path):
    try:
        return output._read(Path(path), MAX_PRIVATE_BYTES).decode("utf-8")
    except UnicodeError as error:
        raise output.EvidenceError("original text encoding differs") from error


def _inside(value, root):
    _require(type(value) is str, "original path type differs")
    path = Path(value)
    _require(
        path.is_absolute() and ".." not in path.parts
        and path.is_relative_to(root),
        "original path escaped owned assessment",
    )
    # _read additionally rejects symlink ancestors, hardlinks and special files.
    return path


def _one_line(text, prefix):
    values = [line[len(prefix):] for line in text.splitlines()
              if line.startswith(prefix)]
    _require(len(values) == 1, "original sentinel missing or repeated")
    return values[0]


def _source_digest(tree, manifest, relative):
    rows = [row for row in manifest["source_files"]
            if row["path"] == relative]
    _require(len(rows) == 1, "assessment source binding missing or repeated")
    content = output._read(tree / output._relative(relative), 2 * 1024 * 1024)
    _require(output._identity(content) == rows[0]["assessment"],
             "assessment source changed")
    return rows[0]["assessment"]["sha256"]


def _base_object_count(content):
    """Measure source objects in the exact approved archive, without FreeCAD."""
    _require(output._identity(content) == BASE_IDENTITY,
             "approved base identity differs")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = [item for item in archive.infolist()
                       if item.filename == "Document.xml"]
            _require(len(entries) == 1
                     and entries[0].file_size <= 4 * 1024 * 1024,
                     "approved document XML differs")
            raw = archive.read(entries[0])
        _require(b"<!DOCTYPE" not in raw and b"<!ENTITY" not in raw,
                 "document XML declaration refused")
        root = ET.fromstring(raw)
        objects = root.find("Objects")
        _require(objects is not None, "source object inventory missing")
        count = len(objects.findall("Object"))
        _require(objects.get("Count") == str(count),
                 "source object inventory differs")
        return count
    except (zipfile.BadZipFile, ET.ParseError, KeyError) as error:
        raise output.EvidenceError("approved document inventory differs") from error


def _entry_rows(value, entries):
    from tools.hosted_runtime_compatibility import HEAVY_SECONDS

    _require(type(value) is list and len(value) == len(entries) == 80,
             "matrix entry count differs")
    failed = False
    started = []
    for row, entry in zip(value, entries):
        _require(type(row) is dict and row.get("id") == entry["id"],
                 "matrix entry order differs")
        status = row.get("status")
        if failed:
            _require(row == {"id": entry["id"], "status": "NOT_RUN"},
                     "matrix continued after failure")
        elif status == "PASS":
            output._exact(row, (
                "id", "status", "sessions", "assessment_entry",
                "elapsed_seconds", "originals_directory",
            ), "entry result fields differ")
            _require(type(row["sessions"]) is int
                     and row["sessions"] == entry["sessions"],
                     "entry session count differs")
            output._integer(row["sessions"])
            elapsed = row["elapsed_seconds"]
            ceiling = entry["timeout_seconds"]
            if ceiling is None:
                ceiling = HEAVY_SECONDS
            _require(type(elapsed) in (int, float)
                     and 0 <= elapsed <= ceiling,
                     "entry elapsed time differs")
            started.append((entry, row))
        else:
            _require(row == {"id": entry["id"], "status": "FAIL"},
                     "matrix omitted entry before failure")
            failed = True
            started.append((entry, row))
    return started


def _session(directory, entry, tree, manifest, runtime, *, paired=False):
    invocation = _read_json(directory / "invocation.json")
    digest = _source_digest(tree, manifest, entry["path"])
    _require(
        invocation["id"] == entry["id"]
        and invocation["entry_path"] == str(tree / entry["path"])
        and invocation["entry_sha256"] == digest
        and invocation["kind"] == entry["kind"]
        and invocation["assessment"] == str(tree)
        and invocation["session_directory"] == str(directory),
        "original invocation binding differs",
    )
    guard = _read_json(directory / "guard/result.json")
    _require(
        guard["status"] == "completed"
        and type(guard["process_exit"]) is int and guard["process_exit"] == 0
        and guard["cleanup_proved"] is True
        and guard["failure_reason"] is None
        and type(guard["deadline_cancellation_exit"]) is int
        and guard["deadline_cancellation_exit"] == 0
        and _read_json(directory / "clearance.json") == {"complete": True},
        "original process or timer cleanup incomplete",
    )
    text = _read_text(directory / (
        "client.stdout" if entry["kind"] == "gui-client" else "guard/stdout"
    ))
    _require(output._json(_one_line(text, ENTRY_MARKER)) == {
        "id": entry["id"], "sha256": digest, "run_name": "__main__",
    }, "actual source main invocation differs")
    _require(text.splitlines().count(DONE_MARKER) == 1,
             "actual source completion missing or repeated")
    if entry["kind"] == "gui-client":
        parent_text = _read_text(directory / "guard/stdout")
        _require(parent_text.splitlines().count(DONE_MARKER) == 1,
                 "GUI parent completion missing or repeated")
    if not paired:
        _one_line(text, entry["sentinel"])
    for name in ("input-before.json", "input-after.json"):
        _require(_read_json(directory / name) == BASE_IDENTITY,
                 "same-run source preservation differs")
    if entry["kind"] != "native":
        _require(output._runtime(_read_json(
            directory / "runtime-observation.json")) == runtime,
            "same-run runtime observation differs")
    sample = guard.get("before_cleanup", {})
    _require("cgroup.procs" in sample
             and type(sample["cgroup.procs"]) in (str, type(None)),
             "owned process sample missing")
    owned = (sample["cgroup.procs"] or "").splitlines()
    _require(all(re.fullmatch(r"[1-9][0-9]*", value) for value in owned),
             "owned process observation differs")
    # Empty or removed cgroups have no sampled PID. The separate clearance and
    # guard cleanup proofs are mandatory; no PID is guessed from process names.
    return text, [int(value) for value in owned]


def _series(directory, entry, tree, manifest, runtime):
    calls = _read_json(directory / "sessions.json")
    _require(type(calls) is list and len(calls) == entry["sessions"],
             "original series sessions differ")
    owned = []
    for index, row in enumerate(calls, 1):
        output._exact(row, ("id", "guard", "original"),
                      "series session fields differ")
        name = entry["id"] + "-route-" + str(index)
        child = dict(entry, id=name, kind="gui-client", sessions=1)
        if entry["id"] == "phase3-four-routes":
            child["path"] = (
                "tools/freecad_bridge/run_phase3_transition_workflow.py"
            )
        _require(row["id"] == name
                 and row["guard"] == str(directory / name / "guard/result.json"),
                 "series child binding differs")
        _, pids = _session(directory / name, child, tree, manifest,
                           runtime, paired=True)
        owned.extend(pids)
        original = _read_json(_inside(row["original"], tree))
        _require(original["status"] == "completed"
                 and original["cleanup"]["remaining"] == [],
                 "original route or document cleanup incomplete")
        if entry["id"] == "phase7-export-pair":
            persisted = _at(original, "workflow/recipe/save_reopen")
            output._integer(_at(persisted, "objects"))
            output._digest(_at(persisted, "normalised_semantic_sha256"))
    text = _read_text(directory / "series.stdout")
    _one_line(text, entry["sentinel"])
    # Each child prints its completion and the parent adds its own.
    _require(text.splitlines().count(DONE_MARKER) == entry["sessions"] + 1,
             "series completion count differs")
    return text, owned


def _original(group_id, text, tree, *, directory=None):
    if group_id == "phase4-migration":
        return None, None
    if group_id == "phase5-view-edit-lifecycle":
        _require(directory is not None,
                 "Phase 5 private original session is missing")
        directory = Path(directory).absolute()
        channels = [_read_text(directory / name) for name in (
            "guard/stdout", "guard/stderr", "client.stdout", "client.stderr")
            if (directory / name).exists() or (directory / name).is_symlink()]
        try:
            diagnostics.verify_private_reports(
                directory, group_id, channels, completed=True)
        except ValueError as error:
            raise output.EvidenceError(
                "Phase 5 private original verification failed") from error
        private_text = _read_text(
            directory / "diagnostic-private/g05-report.txt")
        return output._json(_one_line(
            private_text, "TRACKTEMPLATE_PHASE5_VIEWPROVIDER_GUI=")), None
    path = _inside(_one_line(text, RECEIPT_PREFIXES[group_id]), tree)
    filename = ("comparison.json" if group_id in (
        "phase3-four-routes", "phase7-export-pair") else "run.json")
    path = path / filename
    value = _read_json(path)
    _require(value["status"] in ("PASS", "completed"),
             "original source result failed")
    if "source_fixture_sha256" in value:
        # Straight consumers can report the generated fixture here; their base
        # preservation is separately measured by the controller each session.
        _require(value["source_fixture_sha256_after"]
                 == value["source_fixture_sha256"],
                 "original fixture changed")
    if "source_sha256_after" in value:
        _require(value["source_sha256_after"] == value["source_sha256"],
                 "original source map changed")
    if "cleanup" in value:
        _require(value["cleanup"]["remaining"] == [],
                 "original documents remain open")
    return value, path


def _lifecycle(group_id, value):
    """Project only lifecycle stages actually witnessed by each fixed source.

    The original source's completed main invocation proves its assertions ran.
    Named result stages below must also be present; their raw geometry and
    object state never cross the public boundary. NOT_APPLICABLE means that
    this source does not exercise that operation, not that evidence is absent.
    """
    if group_id == "phase4-migration":
        # This fixture emits no JSON. Its main calls the copied-target proof
        # with actual undo, redo and save/reopen assertions before its sentinel.
        return ("PASS", "PASS", "PASS")
    if group_id == "phase5-view-edit-lifecycle":
        for field in ("undo_restored_initial", "redo_restored_edit",
                      "reopened_canonical_state_equal"):
            _require(_at(value, "result/" + field) is True,
                     "original Phase 5 lifecycle failed")
        _require(_at(value,
            "transition_editing_lifecycle_result/undo_redo_preserved") is True,
            "original editing lifecycle failed")
        return ("PASS", "PASS", "PASS")
    if group_id in ("phase3-four-routes", "phase7-export-pair"):
        comparisons = (
            [row["comparison"] for row in value["workflows"].values()]
            if group_id == "phase3-four-routes" else [value["comparison"]]
        )
        _require(len(comparisons) == (2 if group_id == "phase3-four-routes" else 1)
                 and all(row["equal"] is True
                         and type(row["difference_count"]) is int
                         and row["difference_count"] == 0
                         for row in comparisons),
                 "original routed comparison failed")
        # Phase 3 recipes exercise histories and persistence. Phase 7 proves
        # persistence in each route; it does not perform Undo or Redo.
        return (("PASS", "PASS", "PASS") if group_id == "phase3-four-routes"
                else ("NOT_APPLICABLE", "NOT_APPLICABLE", "PASS"))
    if group_id.startswith("selected-export-"):
        proof = value["proof"]
        _require(value["source_unchanged"] is True,
                 "selected export source changed")
        if group_id == "selected-export-rollback":
            cases = proof["cases"]
            _require(len(cases) == 2 and all(
                case["editable_state_and_save_reopen_unchanged"] is True
                for case in cases.values()), "original rollback proof failed")
        else:
            _require(proof["save_reopen_unchanged"] is True,
                     "original selected export persistence failed")
            if group_id == "selected-export-set":
                _require(proof["crossover"]["save_reopen_unchanged"] is True,
                         "original crossover persistence failed")
        return ("NOT_APPLICABLE", "NOT_APPLICABLE", "PASS")
    probe = value["probe"]
    if group_id == "phase8-crossover_preflight":
        _require(type(probe["positive"]["history"]["undo_count"]) is int,
                 "original preflight stage missing")
        return ("NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE")
    if "-selected-" in group_id:
        _require(probe["export_history_before"] == probe["export_history_after"],
                 "original export changed history")
        _require(type(probe["reopened_history"]["undo_count"]) is int,
                 "original reopen history missing")
        return ("NOT_APPLICABLE", "NOT_APPLICABLE", "PASS")
    pointers = {
        "phase8-turnout_toe": (
            "edit_proof/undo_semantic_sha256", "edit_proof/redo_semantic_sha256",
            "edit_proof/save_reopen/semantic_sha256",
        ),
        "phase8-crossover_b4_recovery": ("undo", "redo", "save_reopen"),
        "phase8-crossover_edit_recovery": ("undo", "redo", "save_reopen"),
        "phase8-crossover_host_integration_recovery": (
            "integration_undo", "integration_redo", "reopened_integrated",
        ),
        "phase8-turnout_host_integration_recovery": (
            "create_undo", "create_redo", "reopened_integrated",
        ),
        "phase8-straight_host_crossover": (
            "edit_undo", "edit_redo", "edit_save_reopen",
        ),
        "phase8-straight_crossover_b4": ("undo", "redo", "save_reopen"),
    }
    if group_id == "phase8-straight_host_turnout":
        for name in ("created", "edited", "removed"):
            for operation in ("undo_count", "redo_count"):
                output._integer(_at(probe, name + "_history/" + operation))
        for name in ("created", "edited", "reopened", "removed",
                     "removed_reopened"):
            output._digest(_at(probe, name + "_semantic_sha256"))
        _require(probe["reopened_semantic_sha256"]
                 == probe["edited_semantic_sha256"]
                 != probe["created_semantic_sha256"]
                 and probe["removed_semantic_sha256"]
                 == probe["removed_reopened_semantic_sha256"],
                 "original straight turnout persistence failed")
        # The bound original source asserts edit and removal Undo/Redo before
        # emitting these stages and its completed sentinel.
        return ("PASS", "PASS", "PASS")
    _require(group_id in pointers, "lifecycle source not implemented")
    for pointer in pointers[group_id]:
        stage = _at(probe, pointer)
        if type(stage) is str:
            output._digest(stage)
        else:
            _require(type(stage) is dict, "original lifecycle stage absent")
            count = "record_count" if "record_count" in stage else "object_count"
            output._integer(_at(stage, count))
            if "history" in stage:
                history = stage["history"]
                for name in ("undo_count", "redo_count"):
                    output._integer(_at(history, name))
    if group_id == "phase8-turnout_toe":
        edit = probe["edit_proof"]
        _require(edit["undo_semantic_sha256"] == edit["created_semantic_sha256"]
                 and edit["redo_semantic_sha256"]
                 == edit["save_reopen"]["semantic_sha256"]
                 == edit["edited_semantic_sha256"],
                 "original turnout history witnesses differ")
    return ("PASS", "PASS", "PASS")


def _straight(value, tree, semantic):
    recipe = value["recipe"]
    _require(value["recipe_id"] == "phase8-b14-straight-host-source-v1"
             and value["scenario"] == "phase8-straight-host",
             "original generation recipe differs")
    generated = _inside(value["run_document"], tree)
    _require(generated.name == "b14-long-straight-generated.FCStd",
             "generated document name differs")
    identity = output._identity(output._read(generated, MAX_PRIVATE_BYTES))
    _require(identity["sha256"] == value["run_document_sha256"],
             "same-run generated document changed")
    _require(value["macro_sha256"] == output._identity(output._read(
        tree / "AdvancedTurnout.FCMacro", MAX_PRIVATE_BYTES))["sha256"],
        "original generator macro changed")
    scenarios = recipe["scenarios"]
    cycles = recipe["history_cycles"]
    _require(len(scenarios) == len(cycles) == 2,
             "original generation lifecycle count differs")
    edited = scenarios[1]
    _require(edited["target_lengths_mm"] == [1500.0, 450.0]
             and all(type(v) in (int, float)
                     for v in edited["target_lengths_mm"]),
             "original straight lengths differ")
    _require(recipe["curve_geometry_preserved"] is True,
             "original curve preservation failed")
    initial = recipe["initial_document"]["semantic_sha256"]
    created = scenarios[0]["snapshot"]["semantic_sha256"]
    edited_hash = edited["snapshot"]["semantic_sha256"]
    _require([(row["undo_semantic_sha256"], row["redo_semantic_sha256"])
              for row in cycles] == [(initial, created), (created, edited_hash)]
             and recipe["save_reopen"]["semantic_sha256"] == edited_hash,
             "original generation history or persistence failed")
    elapsed = value["recipe_orchestrator_elapsed_seconds"]
    milliseconds = recipe["save_reopen"]["wall_ms"]
    _require(type(elapsed) in (int, float)
             and type(milliseconds) in (int, float),
             "original generation timing type differs")
    return {
        "macro_sha256": value["macro_sha256"],
        "generated_document": {
            "id": generated.name, **identity,
        },
        "comparison_witness_sha256": value["comparison_witness_sha256"],
        "source_document_semantic_sha256": semantic,
        "timings": {"generation": elapsed,
                    "save_reopen": milliseconds / 1000.0},
        "straight_checks": {
            "length_1500_mm": True, "length_450_mm": True,
            "curve_preserved": True, "history_preserved": True,
            "semantic_save_reopen": True,
        },
    }


def _generated_semantic(entries, verified, tree, generation, receipt):
    rows = [entry for entry in entries if entry["path"].endswith(
        "/freecad_validate_phase8_straight_crossover_b4.py")]
    _require(len(rows) == 1 and rows[0]["id"] in verified,
             "generated semantic observation not reached")
    text = verified[rows[0]["id"]][0]
    path = _inside(_one_line(text,
        "PHASE8_STRAIGHT_CROSSOVER_B4_RECEIPT="), tree)
    value = _read_json(path)
    _require(value["status"] == "PASS"
             and value["sentinel"] == rows[0]["sentinel"]
             and _inside(value["source_receipt"], tree) == receipt
             and value["source_receipt_sha256"] == output._identity(
                 output._read(receipt, MAX_PRIVATE_BYTES))["sha256"]
             and value["source_fixture"] == generation["run_document"]
             and value["source_fixture_sha256"]
             == value["source_fixture_sha256_after"]
             == generation["run_document_sha256"],
             "generated semantic witness is not paired with same-run source")
    return output._digest(value["source_document_semantic_sha256"])


def _image_sources(group, value, receipt, tree):
    bindings = {}
    for member in group.images:
        relative = member.removeprefix("gui/" + group.group_id + "/")
        if group.group_id == "phase5-view-edit-lifecycle":
            path = _inside(_at(value, PHASE5_IMAGES[relative]), tree)
            expected = None
        elif group.group_id.startswith("selected-export-"):
            _require(set(value["visual_sha256"]) == {
                item.removeprefix("gui/" + group.group_id + "/")
                for item in group.images}, "original image inventory differs")
            path = receipt.parent / output._relative(relative)
            expected = {"sha256": value["visual_sha256"][relative]}
        else:
            _require(set(value["visual_evidence"]) == {
                item.removeprefix("gui/" + group.group_id + "/")
                for item in group.images}, "original image inventory differs")
            item = value["visual_evidence"][relative]
            path = _inside(item["path"], receipt.parent)
            expected = {key: item[key] for key in ("sha256", "bytes")}
        _require(path.name == Path(relative).name,
                 "original image name differs")
        content = output._read(path, output.MAX_IMAGE_BYTES)
        measured = output._identity(content)
        _require(expected is None or all(measured[k] == v
                                         for k, v in expected.items()),
                 "original image identity differs")
        output._png(content)
        bindings[member] = content
    return bindings


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("xb") as stream:
        stream.write(data)


def _failure(scope, group, directory, evidence, staging):
    candidates = [directory / "client.stderr", directory / "guard/stderr",
                  directory / "series.stderr", evidence / "matrix-failure.txt"]
    for path in candidates:
        if path.exists() or path.is_symlink():
            if not path.is_symlink() and path.stat().st_size == 0:
                continue
            raw = output._read(path, output.MAX_FAILURE_BYTES)
            # No substring extraction, redaction or reconstructed traceback.
            lines = raw.decode("utf-8").splitlines()
            frames = [output._FRAME.fullmatch(line) for line in lines]
            frames = [match for match in frames if match is not None]
            _require(bool(frames) and bool(lines),
                     "original failure is not safely projectable")
            frame = frames[-1]
            value = {
                "exception_type": lines[-1].split(":", 1)[0],
                "source_relative_file": frame[1], "line": int(frame[2]),
                "reason_code": (
                    "ASSERTION_FAILED" if lines[-1].startswith("AssertionError")
                    else "SOURCE_EXCEPTION"
                ),
            }
            output._safe_failure(scope, group, value, staging, original=raw)
            _write(staging / group.failure, raw)
            return value
    raise output.EvidenceError("started failure has no original diagnostic")


def extract_matrix_payload(
    source_root, work, manifest, destination, *, runtime_observation
):
    """Seal source-bound matrix evidence; preserve originals on every failure.

    ``manifest`` must be the caller's verified preparation, not an unchecked
    self-declared file. ``runtime_observation`` is this attempt's generation
    session file. The sibling ``destination.projection`` is private scratch;
    only the returned ``members`` belong to the public payload. A caller must
    preserve and classify exceptions before any retry or publication.
    """
    # The controller is imported here to share its exact execution capsule,
    # without constructing a runner or a second matrix definition.
    from tools import hosted_runtime_compatibility as matrix

    source_root, work = Path(source_root).absolute(), Path(work).absolute()
    destination = Path(destination).absolute()
    tree, evidence = work / "assessment", work / "evidence"
    descriptor = output._open_directory(work)
    os.close(descriptor)
    capsule = matrix.load_execution_capsule(source_root / matrix.CAPSULE,
                                            source_root)
    _require(_read_json(work / "execution.json") == capsule,
             "same-run execution capsule differs")
    entries = matrix.entries(capsule)
    started = _entry_rows(_read_json(evidence / "matrix-entries.json"), entries)
    _require(not any(entry["kind"] == "native" and row["status"] == "FAIL"
                     for entry, row in started),
             "native failure requires separately approved original transport")
    runtime_path = work / "entries/straight-generation/runtime-observation.json"
    _require(Path(runtime_observation).absolute() == runtime_path,
             "runtime witness is not from this attempt")
    runtime = (output._runtime(_read_json(runtime_path))
               if runtime_path.exists() or runtime_path.is_symlink() else None)
    _require(runtime is not None or started[0][1]["status"] == "FAIL",
             "completed generation has no observed runtime")
    matrix.verify_source_members(tree, manifest)
    scope = output.load_scope_capsule(
        source_root / "tests/fixtures/compatibility-evidence-scope.json",
        source_root,
    )
    base_count = _base_object_count(output._read(
        tree / assessment.BASE_PATH, output.BASE_BYTES))
    staging = destination.with_name(destination.name + ".projection")
    _require(not destination.exists() and not destination.is_symlink()
             and not staging.exists() and not staging.is_symlink(),
             "new projection and destination required")
    descriptor = output._open_directory(staging.parent)
    try:
        os.mkdir(staging.name, mode=0o700, dir_fd=descriptor)
    finally:
        os.close(descriptor)
    verified = {}
    native_count = 0
    for entry, row in started:
        group_id = entry["id"]
        directory = work / "entries" / group_id
        if row["status"] == "PASS":
            _require(row["originals_directory"] == str(directory)
                     and row["assessment_entry"] == output._identity(
                         output._read(tree / entry["path"], 2 * 1024 * 1024)),
                     "entry result source binding differs")
            if entry["kind"] == "series":
                text, owned = _series(directory, entry, tree, manifest, runtime)
            else:
                text, owned = _session(directory, entry, tree, manifest, runtime)
            if entry["kind"] == "native":
                native_count += 1
            verified[group_id] = (text, owned)
    observations = {}
    generated_input = None
    for entry, row in started:
        group_id = entry["id"]
        directory = work / "entries" / group_id
        if entry["kind"] == "native":
            # Native entries have no approved per-entry public result member.
            # Their original records remain separate operational evidence.
            continue
        group = scope.groups[group_id]
        digest = _source_digest(tree, manifest, entry["path"])
        scope = output.bind_assessment_source(
            scope, group_id, "assessment/" + entry["path"],
            tree / entry["path"], digest,
        )
        passed = row["status"] == "PASS"
        observation = {
            "status": row["status"], "assessment_entry_sha256": digest,
            "runtime": runtime, "sentinel": group.sentinel if passed else "",
            "returncode": 0 if passed else None,
            "sessions": row.get("sessions", 0),
            "inputs": [{"id": "approved-base", **BASE_IDENTITY}],
            "document_preservation": None, "cleanup": None, "failure": None,
        }
        if passed:
            text, owned = verified[group_id]
            original, receipt = _original(
                group_id, text, tree, directory=directory)
            if group_id == "straight-generation":
                semantic = _generated_semantic(
                    entries, verified, tree, original, receipt)
                observation.update(_straight(original, tree, semantic))
                generated_input = observation["generated_document"]
                lifecycle = ("PASS", "PASS", "PASS")
            else:
                lifecycle = _lifecycle(group_id, original)
                if "straight" in group_id:
                    _require(generated_input is not None
                             and original["source_fixture_sha256"]
                             == generated_input["sha256"],
                             "straight GUI input is not the same-run generation")
                    observation["inputs"].append(dict(generated_input))
            observation["document_preservation"] = {
                "source_sha256_before": output.BASE_SHA256,
                "source_sha256_after": output.BASE_SHA256,
                "original_unchanged": True, "copy_only": True,
                "object_count_before": base_count,
                "object_count_after": base_count,
                **dict(zip(("undo", "redo", "save_reopen"), lifecycle)),
            }
            observation["cleanup"] = {
                "owned_pids": sorted(set(owned)), "remaining_pids": [],
                "complete": True,
            }
            for member, content in _image_sources(
                group, original, receipt, tree
            ).items():
                _write(staging / member, content)
        else:
            if group_id == "straight-generation":
                observation.update({name: None for name in output._STRAIGHT_FIELDS})
            observation["failure"] = _failure(
                scope, group, directory, evidence, staging)
        observations[group_id] = observation
        result = output.build_result(scope, group_id, observation, staging)
        _write(staging / group.result, (
            json.dumps(result, sort_keys=True, allow_nan=False) + "\n"
        ).encode("utf-8"))
    _require(observations, "matrix has no started public group")
    matrix_pass = all(row["status"] == "PASS" for _, row in started)
    if matrix_pass:
        _require(len(started) == 80 and native_count == 57
                 and len(observations) == 23,
                 "complete matrix lacks actual per-entry evidence")
    matrix.verify_source_members(tree, manifest)
    members = output.seal_outputs(scope, staging, destination,
                                  list(observations), observations)
    return {"status": "PASS" if matrix_pass else "FAIL",
            "native_entries_verified": native_count,
            "started_groups": list(observations), "members": members,
            "runtime_admission": False, "zy_execution": False}
