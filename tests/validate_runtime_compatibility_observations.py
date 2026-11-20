"""Offline counterexamples for source-bound matrix observation extraction."""

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import compatibility_evidence_output as output  # noqa: E402
from tools import hosted_runtime_compatibility as matrix  # noqa: E402
from tools import runtime_compatibility_observations as observation  # noqa: E402
from tools import runtime_compatibility_diagnostics as diagnostics  # noqa: E402

SPEC = importlib.util.spec_from_file_location(
    "output_fixture", ROOT / "tests/validate_compatibility_evidence_output.py"
)
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False) + "\n")


class ObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capsule = matrix.load_execution_capsule(ROOT / matrix.CAPSULE, ROOT)
        cls.entries = matrix.entries(cls.capsule)
        cls.scope = output.load_scope_capsule(FIXTURE.CAPSULE, ROOT)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="matrix-observations-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.work = self.root / "work"
        self.tree = self.work / "assessment"
        self.tree.mkdir(parents=True)
        self.destination = self.root / "public"
        self.manifest = {"source_files": []}
        self.runtime = copy.deepcopy(output.RUNTIME)
        self.entry = copy.deepcopy(self.capsule["gui_entries"][0])

    def source(self, relative):
        path = self.tree / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
            self.manifest["source_files"].append({
                "path": relative, "assessment": output._identity(path.read_bytes()),
            })
        return output._identity(path.read_bytes())["sha256"]

    def session(self, entry, directory=None):
        directory = directory or self.work / "entries" / entry["id"]
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        directory.chmod(0o700)
        digest = self.source(entry["path"])
        write(directory / "invocation.json", {
            "id": entry["id"], "entry_path": str(self.tree / entry["path"]),
            "entry_sha256": digest, "kind": entry["kind"],
            "assessment": str(self.tree), "session_directory": str(directory),
        })
        write(directory / "guard/result.json", {
            "status": "completed", "process_exit": 0,
            "cleanup_proved": True, "failure_reason": None,
            "deadline_cancellation_exit": 0,
            "before_cleanup": {"cgroup.procs": "41001\n41002\n"},
        })
        write(directory / "clearance.json", {"complete": True})
        write(directory / "runtime-observation.json", self.runtime)
        for name in ("input-before.json", "input-after.json"):
            write(directory / name, observation.BASE_IDENTITY)
        text = observation.ENTRY_MARKER + json.dumps({
            "id": entry["id"], "sha256": digest, "run_name": "__main__",
        }) + "\n" + entry["sentinel"] + "\n" + observation.DONE_MARKER + "\n"
        parent_text = (text.replace(entry["sentinel"] + "\n", "", 1)
                       if entry["kind"] == "gui-client" else text)
        (directory / "guard/stdout").write_text(parent_text)
        (directory / "client.stdout").write_text(text)
        return directory

    def run_session(self, directory=None, entry=None):
        entry = entry or self.entry
        directory = directory or self.work / "entries" / entry["id"]
        return observation._session(directory, entry, self.tree, self.manifest,
                                    self.runtime)

    def rows(self):
        return [{
            "id": entry["id"], "status": "PASS",
            "sessions": entry["sessions"], "assessment_entry": {},
            "elapsed_seconds": 1,
            "originals_directory": str(self.work / "entries" / entry["id"]),
        } for entry in self.entries]

    def test_complete_order_and_first_failure(self):
        rows = self.rows()
        self.assertEqual(len(observation._entry_rows(rows, self.entries)), 80)
        for index, entry in enumerate(self.entries[3:], 3):
            rows[index] = {"id": entry["id"],
                           "status": "FAIL" if index == 3 else "NOT_RUN"}
        self.assertEqual(len(observation._entry_rows(rows, self.entries)), 4)
        rows[4] = self.rows()[4]
        with self.assertRaises(output.EvidenceError):
            observation._entry_rows(rows, self.entries)

    def test_entry_absence_duplicates_types_and_extra_fields_rejected(self):
        mutations = [lambda rows: rows.pop(),
                     lambda rows: rows.__setitem__(1, rows[0]),
                     lambda rows: rows[0].update(sessions=True),
                     lambda rows: rows[0].update(elapsed_seconds=float("nan")),
                     lambda rows: rows[0].update(elapsed_seconds=float("inf")),
                     lambda rows: rows[0].update(elapsed_seconds=True),
                     lambda rows: rows[0].update(private="PRIVATE_VALUE")]
        for mutate in mutations:
            rows = self.rows()
            mutate(rows)
            with self.subTest(mutation=mutate), self.assertRaises(output.EvidenceError):
                observation._entry_rows(rows, self.entries)

    def test_session_requires_actual_main_and_cleanup(self):
        directory = self.session(self.entry)
        text, pids = self.run_session()
        self.assertIn(self.entry["sentinel"], text)
        self.assertEqual(pids, [41001, 41002])
        path = directory / "guard/stdout"
        original = path.read_text()
        for replacement in (original.replace("__main__", "__fixture__"),
                            original.replace(observation.DONE_MARKER, ""),
                            original.replace(self.entry["sentinel"], ""),
                            original + observation.DONE_MARKER + "\n"):
            path.write_text(replacement)
            with self.assertRaises(output.EvidenceError):
                self.run_session()
        path.write_text(original)
        guard = json.loads((directory / "guard/result.json").read_text())
        for change in ({"process_exit": True}, {"cleanup_proved": False},
                       {"deadline_cancellation_exit": 1}):
            write(directory / "guard/result.json", dict(guard, **change))
            with self.assertRaises(output.EvidenceError):
                self.run_session()

    def test_session_does_not_accept_inferred_runtime_or_source_identity(self):
        directory = self.session(self.entry)
        write(directory / "runtime-observation.json", dict(self.runtime, qt="6.0"))
        with self.assertRaises(output.EvidenceError):
            self.run_session()
        write(directory / "runtime-observation.json", self.runtime)
        write(directory / "input-after.json", dict(observation.BASE_IDENTITY,
                                                    sha256="f" * 64))
        with self.assertRaises(output.EvidenceError):
            self.run_session()
        write(directory / "input-after.json", observation.BASE_IDENTITY)
        (self.tree / self.entry["path"]).write_text("print('fake')\n")
        with self.assertRaises(output.EvidenceError):
            self.run_session()

    def test_gui_client_requires_parent_completion(self):
        entry = self.capsule["generation"]
        directory = self.session(entry)
        (directory / "guard/stdout").write_text("parent failed\n")
        with self.assertRaises(output.EvidenceError):
            self.run_session(directory, entry)

    def test_symlink_file_and_ancestor_rejected(self):
        path = self.tree / "record.json"
        write(path, {"status": "PASS"})
        linked = self.root / "linked.json"
        linked.symlink_to(path)
        with self.assertRaises(output.EvidenceError):
            observation._read_json(linked)
        parent = self.root / "linked-parent"
        parent.symlink_to(self.tree, target_is_directory=True)
        with self.assertRaises(output.EvidenceError):
            observation._read_json(parent / path.name)

    def test_json_rejects_duplicate_fields_and_nested_nonfinite(self):
        path = self.tree / "record.json"
        for raw in ('{"status":"PASS","status":"FAIL"}',
                    '{"raw":{"geometry":[NaN]}}'):
            path.write_text(raw)
            with self.assertRaises(output.EvidenceError):
                observation._read_json(path)

    def image_record(self, group_id="selected-export-set"):
        group = self.scope.groups[group_id]
        directory = self.tree / "benchmark-output/run"
        receipt = directory / "run.json"
        value = {"visual_sha256": {}, "private": {"token": "PRIVATE_SECRET"}}
        for member in group.images:
            relative = member.removeprefix("gui/" + group_id + "/")
            path = directory / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(FIXTURE.png())
            value["visual_sha256"][relative] = hashlib.sha256(FIXTURE.png()).hexdigest()
        return group, value, receipt

    def test_exact_images_preserve_bytes_without_raw_nested_fields(self):
        group, value, receipt = self.image_record()
        images = observation._image_sources(group, value, receipt, self.tree)
        self.assertEqual(set(images), set(group.images))
        self.assertEqual(len(images), 10)
        self.assertTrue(all(raw == FIXTURE.png() for raw in images.values()))
        self.assertNotIn(b"PRIVATE_SECRET", b"".join(images.values()))

    def test_image_missing_extra_modified_or_linked_rejected(self):
        group, value, receipt = self.image_record()
        original = copy.deepcopy(value)
        value["visual_sha256"]["private.png"] = "a" * 64
        with self.assertRaises(output.EvidenceError):
            observation._image_sources(group, value, receipt, self.tree)
        value = copy.deepcopy(original)
        member = next(iter(value["visual_sha256"]))
        value["visual_sha256"][member] = "a" * 64
        with self.assertRaises(output.EvidenceError):
            observation._image_sources(group, value, receipt, self.tree)
        value = original
        image = receipt.parent / member
        renamed = image.with_suffix(".kept")
        image.rename(renamed)
        with self.assertRaises(output.EvidenceError):
            observation._image_sources(group, value, receipt, self.tree)
        image.symlink_to(renamed)
        with self.assertRaises(output.EvidenceError):
            observation._image_sources(group, value, receipt, self.tree)

    def test_original_path_cannot_escape_tree(self):
        for value in (str(self.root / "private/run"), "relative/run",
                      str(self.tree / "../private/run"), True):
            with self.assertRaises(output.EvidenceError):
                observation._inside(value, self.tree)

    def test_lifecycle_requires_source_specific_observations(self):
        value = {"result": {"undo_restored_initial": True,
                            "redo_restored_edit": True,
                            "reopened_canonical_state_equal": True},
                 "transition_editing_lifecycle_result": {
                     "undo_redo_preserved": True},
                 "private": {"record": "PRIVATE_SECRET"}}
        self.assertEqual(observation._lifecycle("phase5-view-edit-lifecycle", value),
                         ("PASS", "PASS", "PASS"))
        value["result"]["undo_restored_initial"] = 1
        with self.assertRaises(output.EvidenceError):
            observation._lifecycle("phase5-view-edit-lifecycle", value)
        with self.assertRaises((KeyError, output.EvidenceError)):
            observation._lifecycle("phase5-view-edit-lifecycle", {})

    def test_original_comparison_false_or_boolean_count_rejected(self):
        for comparison in ({"equal": False, "difference_count": 0},
                           {"equal": True, "difference_count": False}):
            with self.assertRaises(output.EvidenceError):
                observation._lifecycle("phase7-export-pair",
                                       {"comparison": comparison})

    def test_unapproved_fcstd_is_not_parsed(self):
        with self.assertRaises(output.EvidenceError):
            observation._base_object_count(b"not the approved input")

    def safe_failure(self):
        path = self.tree / "reviewed.py"
        path.write_bytes(FIXTURE.ASSESSMENT_BYTES)
        scope = output.bind_assessment_source(
            self.scope, "phase4-migration", FIXTURE.ASSESSMENT, path,
            FIXTURE.ASSESSMENT_SHA256,
        )
        directory = self.work / "entries/phase4-migration"
        directory.mkdir(parents=True)
        raw = (
            'Traceback (most recent call last):\n'
            f'  File "{FIXTURE.ASSESSMENT}", line 2, in run\n'
            '    assert False, "source assertion failed"\n'
            'AssertionError: source assertion failed\n'
        ).encode()
        path = directory / "client.stderr"
        path.write_bytes(raw)
        staging = self.root / "projection"
        staging.mkdir()
        return scope, directory, path, raw, staging

    def test_safe_original_failure_is_byte_exact(self):
        scope, directory, path, raw, staging = self.safe_failure()
        group = scope.groups["phase4-migration"]
        value = observation._failure(scope, group, directory,
                                     self.work / "evidence", staging)
        self.assertEqual(value["reason_code"], "ASSERTION_FAILED")
        self.assertEqual((staging / group.failure).read_bytes(), raw)
        self.assertEqual(path.read_bytes(), raw)

    def test_unsafe_original_failure_is_kept_and_not_sanitized(self):
        scope, directory, path, raw, staging = self.safe_failure()
        raw = raw.replace(b"in run", b"in PRIVATE_CREDENTIAL_VALUE")
        path.write_bytes(raw)
        group = scope.groups["phase4-migration"]
        with self.assertRaises(output.EvidenceError):
            observation._failure(scope, group, directory,
                                 self.work / "evidence", staging)
        self.assertEqual(path.read_bytes(), raw)
        self.assertFalse((staging / group.failure).exists())
        self.assertFalse(self.destination.exists())

    def test_missing_failure_is_not_replaced_with_summary(self):
        scope, directory, path, raw, staging = self.safe_failure()
        path.write_bytes(b"")
        with self.assertRaises(output.EvidenceError):
            observation._failure(scope, scope.groups["phase4-migration"],
                                 directory, self.work / "evidence", staging)
        self.assertEqual(path.read_bytes(), b"")

    def test_original_receipt_cannot_claim_success_after_source_change(self):
        directory = self.tree / "benchmark-output/run"
        write(directory / "run.json", {
            "status": "PASS", "source_fixture_sha256": "a" * 64,
            "source_fixture_sha256_after": "b" * 64,
        })
        text = observation.RECEIPT_PREFIXES["phase8-turnout_toe"] + str(directory)
        with self.assertRaises(output.EvidenceError):
            observation._original("phase8-turnout_toe", text, self.tree)

    def test_failed_matrix_cannot_claim_57_native_entries(self):
        rows = [{"id": entry["id"],
                 "status": "FAIL" if index == 0 else "NOT_RUN"}
                for index, entry in enumerate(self.entries)]
        self.assertEqual(len(observation._entry_rows(rows, self.entries)), 1)
        rows[1] = self.rows()[1]
        with self.assertRaises(output.EvidenceError):
            observation._entry_rows(rows, self.entries)

    def original_fixture(self, group_id):
        """Synthetic source records; never evidence of a native execution."""
        directory = self.tree / "benchmark-output" / group_id
        directory.mkdir(parents=True, exist_ok=True)
        value = {
            "status": "PASS", "source_fixture_sha256": output.BASE_SHA256,
            "source_fixture_sha256_after": output.BASE_SHA256,
            "cleanup": {"remaining": []},
            "private": {"source": "PRIVATE_SECRET", "vertices": [1, 2, 3]},
        }
        if group_id == "straight-generation":
            generated = directory / "b14-long-straight-generated.FCStd"
            generated.write_bytes(b"synthetic generated working document")
            self.generated = generated
            generated_hash = hashlib.sha256(generated.read_bytes()).hexdigest()
            initial, created = "a" * 64, "b" * 64
            edited = "496a64e43033a5b742d4c82b686ad1bc622508cc4eb6ce8ecadf4d7b9796944d"
            self.source("AdvancedTurnout.FCMacro")
            value.update({
                "status": "completed", "recipe_id": "phase8-b14-straight-host-source-v1",
                "scenario": "phase8-straight-host", "run_document": str(generated),
                "run_document_sha256": generated_hash,
                "macro_sha256": self.source("AdvancedTurnout.FCMacro"),
                "comparison_witness_sha256": edited,
                "recipe_orchestrator_elapsed_seconds": 4.5,
                "recipe": {
                    "initial_document": {"semantic_sha256": initial},
                    "scenarios": [
                        {"snapshot": {"semantic_sha256": created}},
                        {"target_lengths_mm": [1500.0, 450.0],
                         "snapshot": {"semantic_sha256": edited}},
                    ],
                    "history_cycles": [
                        {"undo_semantic_sha256": initial, "redo_semantic_sha256": created},
                        {"undo_semantic_sha256": created, "redo_semantic_sha256": edited},
                    ],
                    "curve_geometry_preserved": True,
                    "save_reopen": {"semantic_sha256": edited, "wall_ms": 125.0},
                },
            })
        elif group_id == "phase4-migration":
            return None, None
        elif group_id == "phase5-view-edit-lifecycle":
            value.update({
                "result": {"undo_restored_initial": True,
                           "redo_restored_edit": True,
                           "reopened_canonical_state_equal": True},
                "transition_editing_lifecycle_result": {"undo_redo_preserved": True},
            })
            for name, pointer in observation.PHASE5_IMAGES.items():
                path = directory / name
                path.write_bytes(FIXTURE.png())
                target = value
                parts = pointer.split("/")
                for part in parts[:-1]:
                    target = target.setdefault(part, {})
                target[parts[-1]] = str(path)
            return value, None
        elif group_id == "phase3-four-routes":
            value.update(status="completed", workflows={
                name: {"comparison": {"equal": True, "difference_count": 0}}
                for name in ("plain-line-edit", "connected-straight")
            })
        elif group_id == "phase7-export-pair":
            value.update(status="completed",
                         comparison={"equal": True, "difference_count": 0})
        elif group_id.startswith("selected-export-"):
            value.update(source_unchanged=True, proof={
                "save_reopen_unchanged": True,
                "crossover": {"save_reopen_unchanged": True},
                "cases": {name: {"editable_state_and_save_reopen_unchanged": True}
                          for name in ("full", "partial")},
            })
        else:
            stage = {"object_count": 9,
                     "history": {"undo_count": 0, "redo_count": 0}}
            value["probe"] = {
                "positive": copy.deepcopy(stage),
                "export_history_before": {"undo_count": 0},
                "export_history_after": {"undo_count": 0},
                "reopened_history": {"undo_count": 0},
                **{name + "_history": {"undo_count": 1, "redo_count": 0}
                   for name in ("created", "edited", "removed")},
                "created_semantic_sha256": "b" * 64,
                "reopened_semantic_sha256": "c" * 64,
                "edited_semantic_sha256": "c" * 64,
                "removed_semantic_sha256": "d" * 64,
                "removed_reopened_semantic_sha256": "d" * 64,
                "edit_proof": {
                    "undo_semantic_sha256": "b" * 64,
                    "redo_semantic_sha256": "c" * 64,
                    "created_semantic_sha256": "b" * 64,
                    "edited_semantic_sha256": "c" * 64,
                    "save_reopen": {"semantic_sha256": "c" * 64},
                },
                **{name: copy.deepcopy(stage) for name in (
                    "undo", "redo", "save_reopen", "integration_undo",
                    "integration_redo", "reopened_integrated", "create_undo",
                    "create_redo", "edit_undo", "edit_redo", "edit_save_reopen",
                )},
            }
            if "straight" in group_id:
                digest = hashlib.sha256(self.generated.read_bytes()).hexdigest()
                value.update(source_fixture_sha256=digest,
                             source_fixture_sha256_after=digest)
        group = self.scope.groups[group_id]
        value["visual_sha256"], value["visual_evidence"] = {}, {}
        for member in group.images:
            relative = member.removeprefix("gui/" + group_id + "/")
            path = directory / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(FIXTURE.png())
            identity = output._identity(path.read_bytes())
            value["visual_sha256"][relative] = identity["sha256"]
            value["visual_evidence"][relative] = {"path": str(path), **identity}
        receipt = directory / ("comparison.json" if group_id in (
            "phase3-four-routes", "phase7-export-pair") else "run.json")
        write(receipt, value)
        return value, receipt

    def full_matrix_fixture(self):
        write(self.work / "execution.json", self.capsule)
        base = self.tree / observation.assessment.BASE_PATH
        base.parent.mkdir(parents=True)
        base.write_bytes(b"test double for excluded approved base")
        rows = self.rows()
        originals = {}
        for entry in [self.capsule["generation"], *self.capsule["gui_entries"]]:
            originals[entry["id"]] = self.original_fixture(entry["id"])
        generation, generation_receipt = originals["straight-generation"]
        for row, entry in zip(rows, self.entries):
            directory = self.work / "entries" / entry["id"]
            digest = self.source(entry["path"])
            row["assessment_entry"] = output._identity((self.tree / entry["path"]).read_bytes())
            if entry["kind"] == "series":
                calls, parts = [], []
                for index in range(1, entry["sessions"] + 1):
                    name = entry["id"] + "-route-" + str(index)
                    child = dict(entry, id=name, kind="gui-client", sessions=1,
                                 sentinel="Original child route complete")
                    if entry["id"] == "phase3-four-routes":
                        child["path"] = "tools/freecad_bridge/run_phase3_transition_workflow.py"
                    child_directory = self.session(child, directory / name)
                    original = self.tree / "benchmark-output" / name / "run.json"
                    write(original, {
                        "status": "completed", "cleanup": {"remaining": []},
                        "workflow": {"recipe": {"save_reopen": {
                            "objects": 9, "normalised_semantic_sha256": "d" * 64,
                        }}},
                    })
                    calls.append({"id": name,
                                  "guard": str(child_directory / "guard/result.json"),
                                  "original": str(original)})
                    parts.append((child_directory / "client.stdout").read_text())
                _, receipt = originals[entry["id"]]
                write(directory / "sessions.json", calls)
                parts.append(entry["sentinel"] + str(receipt.parent) + "\n")
                parts.append(observation.DONE_MARKER + "\n")
                (directory / "series.stdout").write_text("".join(parts))
            else:
                self.session(entry, directory)
                file = directory / ("client.stdout" if entry["kind"] == "gui-client" else "guard/stdout")
                text = file.read_text()
                if entry["id"] in originals:
                    value, receipt = originals[entry["id"]]
                    if entry["id"] == "phase5-view-edit-lifecycle":
                        namespace = {}
                        exec(diagnostics._helper_source(diagnostics.SOURCES[
                            entry["path"]]), namespace)
                        public = io.StringIO()
                        with patch.dict(os.environ, {
                            diagnostics.SESSION_ENV: str(directory),
                        }), contextlib.redirect_stdout(public):
                            namespace["_tt_diagnostic_report"](
                                "g05-report",
                                entry["sentinel"] + json.dumps(value))
                        text = text.replace(entry["sentinel"] + "\n",
                                            public.getvalue())
                    elif receipt is not None:
                        marker = observation.RECEIPT_PREFIXES[entry["id"]]
                        if marker == entry["sentinel"]:
                            text = text.replace(marker + "\n", marker + str(receipt.parent) + "\n")
                        else:
                            text += marker + str(receipt.parent) + "\n"
                if entry["path"].endswith("/freecad_validate_phase8_straight_crossover_b4.py"):
                    receipt = self.tree / "benchmark-output/native-b4.json"
                    write(receipt, {
                        "status": "PASS", "sentinel": entry["sentinel"],
                        "source_receipt": str(generation_receipt),
                        "source_receipt_sha256": output._identity(generation_receipt.read_bytes())["sha256"],
                        "source_fixture": generation["run_document"],
                        "source_fixture_sha256": generation["run_document_sha256"],
                        "source_fixture_sha256_after": generation["run_document_sha256"],
                        "source_document_semantic_sha256": "80b80168f012ddb0fb2f7d4a0a747f40db57243eceb698345e196996ac8281c5",
                    })
                    text += "PHASE8_STRAIGHT_CROSSOVER_B4_RECEIPT=" + str(receipt) + "\n"
                file.write_text(text)
        write(self.work / "evidence/matrix-entries.json", rows)

    def extract_fixture(self):
        # Source-entry bytes, receipts, sessions and publication validation are
        # real here. Only excluded base acquisition is doubled; its producer
        # has a separate exact-byte suite and read-only author check.
        with patch.object(matrix, "verify_source_members"), patch.object(
            observation, "_base_object_count", return_value=9
        ):
            return observation.extract_matrix_payload(
                ROOT, self.work, self.manifest, self.destination,
                runtime_observation=self.work / "entries/straight-generation/runtime-observation.json",
            )

    def test_full_matrix_seals_23_typed_results_and_159_actual_pngs(self):
        self.full_matrix_fixture()
        result = self.extract_fixture()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["native_entries_verified"], 57)
        self.assertEqual(len(result["started_groups"]), 23)
        self.assertEqual(sum(path.endswith(".png") for path in result["members"]), 159)
        self.assertEqual(sum(path.endswith("result.json") for path in result["members"]), 23)
        self.assertFalse(result["runtime_admission"])
        for path in result["members"]:
            raw = (self.destination / path).read_bytes()
            self.assertNotIn(b"PRIVATE_SECRET", raw)
            self.assertNotIn(str(self.work).encode(), raw)
        generated = json.loads((self.destination / "fixture-generation/straight/result.json").read_text())
        self.assertNotEqual(generated["source_document_semantic_sha256"], "a" * 64)
        self.assertEqual(generated["timings"]["save_reopen"], 0.125)

    def test_straight_turnout_projects_actual_history_and_persistence(self):
        self.full_matrix_fixture()
        path = self.tree / "benchmark-output/phase8-straight_host_turnout/run.json"
        original = json.loads(path.read_text())
        self.assertEqual(observation._lifecycle(
            "phase8-straight_host_turnout", original), ("PASS", "PASS", "PASS"))
        for field, value in (("created_history", {"undo_count": True, "redo_count": 0}),
                             ("removed_reopened_semantic_sha256", "f" * 64)):
            changed = copy.deepcopy(original)
            changed["probe"][field] = value
            with self.subTest(field=field), self.assertRaises(output.EvidenceError):
                observation._lifecycle("phase8-straight_host_turnout", changed)

    def test_phase7_requires_actual_original_save_reopen(self):
        self.full_matrix_fixture()
        entry = next(row for row in self.entries if row["id"] == "phase7-export-pair")
        directory = self.work / "entries" / entry["id"]
        original = self.tree / "benchmark-output/phase7-export-pair-route-1/run.json"
        value = json.loads(original.read_text())
        del value["workflow"]["recipe"]["save_reopen"]
        write(original, value)
        with self.assertRaises(output.EvidenceError):
            observation._series(directory, entry, self.tree, self.manifest, self.runtime)

    def test_full_matrix_rejects_native_without_actual_invocation(self):
        self.full_matrix_fixture()
        entry = self.capsule["native_entries"][12]
        path = self.work / "entries" / entry["id"] / "guard/stdout"
        path.write_text(entry["sentinel"] + "\n")
        with self.assertRaises(output.EvidenceError):
            self.extract_fixture()
        self.assertFalse(self.destination.exists())

    def test_generation_semantic_must_be_same_run_actual_native_receipt(self):
        self.full_matrix_fixture()
        path = self.tree / "benchmark-output/native-b4.json"
        value = json.loads(path.read_text())
        value["source_receipt_sha256"] = "a" * 64
        write(path, value)
        with self.assertRaises(output.EvidenceError):
            self.extract_fixture()
        self.assertFalse(self.destination.exists())

    def test_later_native_failure_cannot_seal_without_original_diagnostic(self):
        self.full_matrix_fixture()
        path = self.work / "evidence/matrix-entries.json"
        rows = json.loads(path.read_text())
        failed = False
        for row in rows:
            if row["id"] == "native-57":
                failed = True
                row.clear()
                row.update(id="native-57", status="FAIL")
            elif failed:
                identifier = row["id"]
                row.clear()
                row.update(id=identifier, status="NOT_RUN")
        write(path, rows)
        failure = self.work / "entries/native-57/guard/stderr"
        failure.write_bytes(b"original failure retained privately\n")
        with self.assertRaisesRegex(output.EvidenceError, "native failure"):
            self.extract_fixture()
        self.assertEqual(failure.read_bytes(), b"original failure retained privately\n")
        self.assertFalse(self.destination.exists())

    def phase5_private_fixture(self):
        entry = next(item for item in self.entries
                     if item["id"] == "phase5-view-edit-lifecycle")
        directory = self.session(entry)
        value = {"proof": "original", "excluded_raw_points": [[1, 2, 3]]}
        namespace = {}
        exec(diagnostics._helper_source(diagnostics.SOURCES[entry["path"]]),
             namespace)
        public = io.StringIO()
        with patch.dict(os.environ, {
            diagnostics.SESSION_ENV: str(directory),
        }), contextlib.redirect_stdout(public):
            namespace["_tt_diagnostic_report"](
                "g05-report", entry["sentinel"] + json.dumps(value))
        path = directory / "client.stdout"
        path.write_text(path.read_text().replace(
            entry["sentinel"] + "\n", public.getvalue()))
        return directory, value

    def test_phase5_reads_exact_private_original_after_witness_verification(self):
        directory, value = self.phase5_private_fixture()
        public = (directory / "client.stdout").read_text()
        actual, receipt = observation._original(
            "phase5-view-edit-lifecycle", public, self.tree,
            directory=directory)
        self.assertEqual(actual, value)
        self.assertIsNone(receipt)
        self.assertNotIn("excluded_raw_points", public)
        with self.assertRaises(output.EvidenceError):
            observation._original("phase5-view-edit-lifecycle", public,
                                  self.tree)

    def test_phase5_missing_changed_or_unwitnessed_original_is_retained(self):
        directory, _ = self.phase5_private_fixture()
        public = (directory / "client.stdout").read_text()
        original = directory / "diagnostic-private/g05-report.txt"
        retained = original.read_bytes()
        original.write_bytes(retained + b"changed")
        with self.assertRaises(output.EvidenceError):
            observation._original("phase5-view-edit-lifecycle", public,
                                  self.tree, directory=directory)
        self.assertEqual(original.read_bytes(), retained + b"changed")
        original.write_bytes(retained)
        sidecar = directory / "diagnostic-witnesses.jsonl"
        sidecar.rename(directory / "retained-private-witness.jsonl")
        with self.assertRaises(output.EvidenceError):
            observation._original("phase5-view-edit-lifecycle", public,
                                  self.tree, directory=directory)
        self.assertEqual(original.read_bytes(), retained)

    def test_phase5_extra_or_linked_original_fails_closed(self):
        directory, _ = self.phase5_private_fixture()
        public = (directory / "client.stdout").read_text()
        extra = directory / "diagnostic-private/unlisted.txt"
        extra.write_bytes(b"retained")
        with self.assertRaises(output.EvidenceError):
            observation._original("phase5-view-edit-lifecycle", public,
                                  self.tree, directory=directory)
        extra.rename(directory / "retained-unlisted.txt")
        original = directory / "diagnostic-private/g05-report.txt"
        retained = directory / "retained-report.txt"
        original.rename(retained)
        original.symlink_to(retained)
        with self.assertRaises(output.EvidenceError):
            observation._original("phase5-view-edit-lifecycle", public,
                                  self.tree, directory=directory)
        self.assertTrue(retained.is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
