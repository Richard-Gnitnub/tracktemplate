"""Exercise fixed ZY generation controls with inert process/file doubles."""

from copy import deepcopy
import hashlib
import importlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def identity(raw):
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def member(archive, name, raw, *, kind=tarfile.REGTYPE):
    item = tarfile.TarInfo(name)
    item.size, item.mode, item.type = len(raw), 0o600, kind
    archive.addfile(item, io.BytesIO(raw))


class ZyGenerationControls(unittest.TestCase):
    """No compiler, subprocess, network, FreeCAD or Qt runs in these cases."""

    def setUp(self):
        self.generation = importlib.import_module(
            "tools.hosted_to_zy_generation"
        )
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        (self.work / "evidence").mkdir()

    def input_archive(self, changes=(), *, linked=False):
        files = {"source/a.py": b"source\n", "x2/build_x2_zy.py": b"entry\n"}
        manifest = {
            "file_count": 2,
            "total_bytes": sum(map(len, files.values())),
            "files": [
                {"member": name, **identity(raw)}
                for name, raw in files.items()
            ],
        }
        raw = encoded(manifest)
        archive = self.work / "inputs.tar"
        with tarfile.open(archive, "x", format=tarfile.USTAR_FORMAT) as stream:
            member(stream, "known-input-manifest.json", raw)
            for name, data in files.items():
                member(
                    stream,
                    name,
                    data,
                    kind=tarfile.SYMTYPE if linked else tarfile.REGTYPE,
                )
            for name, data in changes:
                member(stream, name, data)
        return archive, raw, files

    def test_fixed_scope_and_old_selectors(self):
        g = self.generation
        self.assertEqual(
            g.MANIFEST_SHA256,
            "3ff851541917e251809a5512348ae234b7499adca203bf4bde4263359d74667d",
        )
        self.assertEqual(
            g.ENTRY_SHA256,
            "e4fc8566f07651bc931b36d553a21e78eae40dd4b4f20d7b39b478034ec7c190",
        )
        self.assertEqual(g.INPUT_COUNT, 71)
        self.assertEqual(g.INPUT_BYTES, 4009495)
        self.assertEqual(g.ARCHIVE_BYTES, 4085760)
        from tools import hosted_l1_private_validation as native

        for value in ("l1", "to-single", "to-crossing", "to-zy-generation"):
            self.assertEqual(
                native.selected_workload(
                    {"TRACKTEMPLATE_NATIVE_WORKLOAD": value}
                ),
                value,
            )
        with self.assertRaises(ValueError):
            native.selected_workload({"TRACKTEMPLATE_NATIVE_WORKLOAD": "zy"})

    def test_exact_archive_and_exclusive_inputs(self):
        archive, raw, files = self.input_archive()
        g = self.generation
        with patch.multiple(
            g,
            MANIFEST_SHA256=identity(raw)["sha256"],
            INPUT_COUNT=2,
            INPUT_BYTES=sum(map(len, files.values())),
            ARCHIVE_BYTES=archive.stat().st_size,
        ):
            result = g.extract_inputs(archive, self.work / "approved")
            self.assertEqual(result, json.loads(raw))
            for name, data in files.items():
                self.assertEqual(
                    (self.work / "approved" / name).read_bytes(), data
                )
            with self.assertRaises((ValueError, FileExistsError)):
                g.extract_inputs(archive, self.work / "approved")

    def test_archive_refuses_extra_duplicate_traversal_and_links(self):
        cases = (
            ("extra", b"x"),
            ("source/a.py", b"source\n"),
            ("../escaped", b"x"),
            ("/absolute", b"x"),
            ("source//other", b"x"),
        )
        for index, change in enumerate(cases):
            with self.subTest(change=change):
                directory = self.work / str(index)
                directory.mkdir()
                previous = self.work
                self.work = directory
                archive, raw, files = self.input_archive((change,))
                self.work = previous
                with patch.multiple(
                    self.generation,
                    MANIFEST_SHA256=identity(raw)["sha256"],
                    INPUT_COUNT=2,
                    INPUT_BYTES=sum(map(len, files.values())),
                    ARCHIVE_BYTES=archive.stat().st_size,
                ):
                    with self.assertRaises(ValueError):
                        self.generation.extract_inputs(
                            archive, directory / "out"
                        )
                    self.assertFalse((directory / "out").exists())
        directory = self.work / "linked"
        directory.mkdir()
        previous, self.work = self.work, directory
        archive, raw, files = self.input_archive(linked=True)
        self.work = previous
        with patch.multiple(
            self.generation,
            MANIFEST_SHA256=identity(raw)["sha256"],
            INPUT_COUNT=2,
            INPUT_BYTES=sum(map(len, files.values())),
            ARCHIVE_BYTES=archive.stat().st_size,
        ):
            with self.assertRaises(ValueError):
                self.generation.extract_inputs(archive, directory / "out")

    def test_archive_changed_member_and_manifest_fail_before_extract(self):
        archive, raw, files = self.input_archive()
        data = archive.read_bytes()
        archive.write_bytes(data.replace(b"source\n", b"SOURCE\n"))
        with patch.multiple(
            self.generation,
            MANIFEST_SHA256=identity(raw)["sha256"],
            INPUT_COUNT=2,
            INPUT_BYTES=sum(map(len, files.values())),
            ARCHIVE_BYTES=archive.stat().st_size,
        ):
            with self.assertRaises(ValueError):
                self.generation.extract_inputs(archive, self.work / "out")
        self.assertFalse((self.work / "out").exists())

    def test_compiler_identity_is_actual_and_complete(self):
        g = self.generation
        driver = self.work / "fpc"
        backend = self.work / "ppcx64"
        config = self.work / "fpc.cfg"
        rtl = self.work / "system.ppu"
        for path in (driver, backend, config, rtl):
            path.write_bytes(path.name.encode())
        record = {
            "status": "PASS_COMPILER_READINESS",
            "version": "3.2.2",
            "package_version": "3.2.2+dfsg-32",
            "architecture": "x86_64",
            "compiler_path": str(driver),
            "binary_identity": identity(driver.read_bytes()),
            "package_provenance": {"packages": ["fixture-only"]},
            "toolchain_aliases": [
                {"path": str(driver), "resolved": str(driver)}
            ],
            "toolchain_files": [
                {
                    "path": str(path),
                    "role": role,
                    **identity(path.read_bytes()),
                }
                for path, role in (
                    (driver, "driver"),
                    (backend, "backend"),
                    (config, "config"),
                    (rtl, "rtl"),
                )
            ],
        }
        self.assertEqual(g.validate_compiler(record), driver)
        for field, value in (
            ("compiler_path", "fpc"),
            ("package_version", "3.2.2"),
            ("package_provenance", {}),
            ("toolchain_files", record["toolchain_files"][:-1]),
        ):
            with self.subTest(field=field):
                changed = deepcopy(record)
                changed[field] = value
                with self.assertRaises(ValueError):
                    g.validate_compiler(changed)
        backend.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            g.validate_compiler(record)

    def test_compiler_link_and_changed_ancestor_are_rejected(self):
        target = self.work / "target"
        target.write_bytes(b"compiler")
        link = self.work / "fpc"
        link.symlink_to(target)
        with self.assertRaises(ValueError):
            self.generation.compiler_path(link)
        parent = self.work / "alias"
        parent.symlink_to(self.work, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.generation.compiler_path(parent / "target")

    def test_deadline_only_decreases_and_host_limits_are_exact(self):
        g = self.generation
        self.assertEqual(g.remaining_seconds(7300.0, 100.1), 7199)
        self.assertEqual(g.remaining_seconds(7300.0, 7000.9), 299)
        for now in (7299.1, 7300, 8000):
            with self.assertRaises(ValueError):
                g.remaining_seconds(7300, now)
        properties = g.preparation_properties(7199)
        for name, value in {
            "MemoryMax": str(4096 * 1024**2),
            "MemoryHigh": str(4096 * 1024**2),
            "MemorySwapMax": "0",
            "CPUQuota": "100%",
            "TasksMax": "128",
            "RuntimeMaxSec": "7199",
            "KillMode": "control-group",
            "Restart": "no",
            "LimitCORE": "0",
        }.items():
            self.assertEqual(properties[name], value)

    def test_live_resource_failures_stop_before_handoff(self):
        sample = {
            "memory.current": "100",
            "memory.peak": "100",
            "memory.swap.current": "0",
            "pids.current": "3",
            "memory.events": "high 0\nmax 0\noom 0\noom_kill 0\n",
            "cpu.stat": "usage_usec 10\n",
            "memory.pressure": "some avg10=0.00 avg60=0.00 avg300=0.00 total=0\nfull avg10=0.00 avg60=0.00 avg300=0.00 total=0\n",
            "cgroup.events": "populated 1\n",
            "cgroup.procs": "1\n2\n3\n",
        }
        host = {
            "MemAvailable": 13 * 1024**3,
            "SwapTotal": 0,
            "SwapFree": 0,
            "memory_pressure": sample["memory.pressure"],
        }
        self.generation.validate_sample(sample, host)
        for field, value in (
            ("memory.swap.current", "1"),
            ("memory.events", "high 1\nmax 0\noom 0\noom_kill 0\n"),
            ("pids.current", "129"),
            ("memory.peak", str(4096 * 1024**2 + 1)),
            ("cpu.stat", None),
            ("memory.pressure", "bad"),
        ):
            with self.subTest(field=field):
                changed = dict(sample, **{field: value})
                with self.assertRaises(ValueError):
                    self.generation.validate_sample(changed, host)
        with self.assertRaises(ValueError):
            self.generation.validate_sample(
                sample, dict(host, MemAvailable=8192 * 1024**2 - 1)
            )

    def test_native_never_starts_after_failed_or_unclean_preparation(self):
        g = self.generation
        for prep in (
            {"status": "FAIL", "cleanup": True},
            {"status": "PASS", "cleanup": False},
        ):
            with (
                self.subTest(prep=prep),
                patch.object(g, "run_preparation", return_value=prep),
                patch.object(g, "run_native") as native,
            ):
                with self.assertRaises(ValueError):
                    g.generation_sequence(self.work, {}, object(), 7200.0)
                native.assert_not_called()

    def test_native_receives_remaining_budget_and_same_lease(self):
        g = self.generation
        lease = object()
        with (
            patch.object(
                g,
                "run_preparation",
                return_value={
                    "status": "PASS",
                    "cleanup": True,
                },
            ),
            patch.object(g.time, "monotonic", return_value=7000.25),
            patch.object(
                g, "run_native", return_value={"status": "PASS"}
            ) as native,
        ):
            result = g.generation_sequence(self.work, {}, lease, 7300.0)
            self.assertEqual(result["native"], {"status": "PASS"})
            self.assertEqual(native.call_args.kwargs["seconds"], 299)
            self.assertIs(native.call_args.kwargs["lease"], lease)

    def test_readiness_cannot_generate_or_auto_admit_model(self):
        g = self.generation
        record = {
            "status": "PASS",
            "stage": "readiness",
            "run_id": 21,
            "source_commit": "a" * 40,
            "manifest_sha256": g.MANIFEST_SHA256,
            "compiler": {"fixture": "actual reviewed identities"},
            "cleanup": True,
            "independent_review": "PASS",
            "evidence_sha256": "b" * 64,
            "native_tests": 1,
            "skips": 0,
            "input_integrity": True,
            "runtime_profile_id": g.pilot.EXPECTED_PROFILE,
        }
        control = {"source_commit": "a" * 40, "compiler": record["compiler"]}
        g.validate_readiness(record, control, 22)
        for field, value in (
            ("source_commit", "c" * 40),
            ("run_id", 22),
            ("cleanup", False),
            ("stage", "native"),
            ("compiler", {}),
            ("evidence_sha256", "0" * 64),
        ):
            with self.subTest(field=field):
                changed = dict(record, **{field: value})
                with self.assertRaises(ValueError):
                    g.validate_readiness(changed, control, 22)

    def test_failure_projection_preserves_only_first_failed_raw_request(self):
        g = self.generation
        generated = self.work / "generated"
        (generated / "generated-raw").mkdir(parents=True)
        rows = []
        for index, name in enumerate(("first", "second", "third")):
            rows.append(
                {"name": name, "request_identity": identity(name.encode())}
            )
            if index == 2:
                continue
            out = generated / "generated-raw" / (name + ".faces.json")
            err = generated / "generated-raw" / (name + ".stderr")
            out.write_bytes(
                b'{"status":"PASS","marker":"raw-success"}'
                if not index
                else b"original-partial"
            )
            err.write_bytes(b"" if not index else b"original-error")
            if not index:
                Path(str(out) + ".process.json").write_bytes(
                    encoded({"returncode": 0})
                )
        record = g.preserve_generation_failure(
            generated, rows, self.work / "evidence"
        )
        self.assertEqual(record["request"], "second")
        self.assertEqual(
            (self.work / "evidence/failed-request.stdout").read_bytes(),
            b"original-partial",
        )
        self.assertEqual(
            (self.work / "evidence/failed-request.stderr").read_bytes(),
            b"original-error",
        )
        self.assertFalse(
            any(
                b"raw-success" in p.read_bytes()
                for p in (self.work / "evidence").iterdir()
            )
        )

    def test_native_first_cause_allowlist_excludes_full_result(self):
        g = self.generation
        generated = self.work / "generated"
        (generated / "native-x2/components").mkdir(parents=True)
        for name, data in (
            (
                "native-x2/components/component-results.json",
                b'{"cause":"original"}',
            ),
            ("native-x2/ZY.failure.txt", b"original normalization traceback"),
            ("native-x2/result.json", b"private recipe and vertices"),
        ):
            (generated / name).write_bytes(data)
        result = g.preserve_native_failure(generated, self.work / "evidence")
        self.assertEqual(
            set(result), {"component-results.json", "ZY.failure.txt"}
        )
        self.assertEqual(
            (self.work / "evidence/ZY.failure.txt").read_bytes(),
            b"original normalization traceback",
        )
        self.assertFalse((self.work / "evidence/result.json").exists())

    def control(self):
        g = self.generation
        return {
            "schema": 1,
            "workload": g.WORKLOAD,
            "stage": "readiness",
            "scope_id": g.SCOPE,
            "source_commit": "a" * 40,
            "workflow_commit": "a" * 40,
            "manifest_sha256": g.MANIFEST_SHA256,
            "entry_sha256": g.ENTRY_SHA256,
            "execution_enabled": True,
            "independent_review": "PASS",
            "independent_review_sha256": "b" * 64,
            "dispatch_nonce": "c" * 32,
            "limits": g.resource_contract("readiness"),
            "handling_decision": {
                "status": "APPROVED",
                "sha256": g.OWNER_DECISION_SHA256,
                "manifest_sha256": g.MANIFEST_SHA256,
                "independent_review_sha256": "d" * 64,
            },
            "access_review": {
                "status": "PASS",
                "audited_at_utc": "2026-11-13T00:00:00Z",
                "owner": "Richard-Gnitnub",
                "environment": "l1-private-validation",
                "branches": ["main"],
                "tags": [],
                "input_repository": "Richard-Gnitnub/tracktemplate",
                "repository_public": True,
                "active_runs": 0,
                "queued_runs": 0,
                "waiting_runs": 0,
            },
            "recovery": {
                "status": "PASS",
                "manifest_sha256": g.MANIFEST_SHA256,
                "independent_review_sha256": "e" * 64,
                "source_commit": "a" * 40,
            },
            "source_publication": {
                "status": "PASS",
                "manifest_sha256": g.MANIFEST_SHA256,
                "independent_review_sha256": "f" * 64,
            },
            "input_archive": {
                "asset_id": 1,
                "sha256": g.ARCHIVE_SHA256,
                "bytes": g.ARCHIVE_BYTES,
            },
            "control_files_sha256": {
                name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                for name in g.CONTROL_FILES
            },
            "compiler": None,
            "compiler_record_asset": None,
            "readiness_review": None,
        }

    def test_exact_owner_source_archive_and_serial_contract(self):
        g, control = self.generation, self.control()
        environment = {"GITHUB_SHA": "a" * 40, "GITHUB_RUN_ID": "22"}
        g.validate_control(control, "readiness", environment)
        cases = (
            (("execution_enabled",), 1),
            (("source_commit",), "0" * 40),
            (("independent_review_sha256",), "0" * 64),
            (("manifest_sha256",), "1" * 64),
            (("entry_sha256",), "2" * 64),
            (("handling_decision", "sha256"), "3" * 64),
            (("input_archive", "sha256"), "4" * 64),
            (("input_archive", "bytes"), g.ARCHIVE_BYTES + 1),
            (("recovery", "source_commit"), "5" * 40),
            (("source_publication", "status"), "PENDING"),
            (("access_review", "repository_public"), False),
            (("access_review", "branches"), ["main", "other"]),
            (("access_review", "waiting_runs"), 1),
            (("access_review", "active_runs"), False),
            (("limits", "swap_bytes"), False),
            (("limits", "timeout_seconds"), 7200),
            (("compiler",), {"sha256": "7" * 64, "bytes": 4}),
        )
        for keys, value in cases:
            with self.subTest(keys=keys):
                changed = deepcopy(control)
                row = changed
                for key in keys[:-1]:
                    row = row[key]
                row[keys[-1]] = value
                with self.assertRaises(ValueError):
                    g.validate_control(changed, "readiness", environment)
        changed = deepcopy(control)
        changed["control_files_sha256"].pop(g.CONTROL_FILES[-1])
        with self.assertRaises(ValueError):
            g.validate_control(changed, "readiness", environment)

    def test_source_owner_rejects_identity_command_and_deadline_changes(self):
        g = self.generation
        intent = {
            "unit": "tracktemplate-zy-source-123.service",
            "seconds": 33,
            "command": ["/usr/bin/python3", "/fixed/entry.py"],
        }
        group = (
            f"/user.slice/user-{g.os.getuid()}.slice/user@{g.os.getuid()}.service/"
            "app.slice/" + intent["unit"]
        )
        state = {
            "Id": intent["unit"],
            "ControlGroup": group,
            "InvocationID": "a" * 32,
            "KillMode": "control-group",
            "Restart": "no",
            "SendSIGKILL": "yes",
            "RuntimeMaxUSec": "33s",
            "TimeoutStopUSec": "5s",
            "ExecStart": "{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /fixed/entry.py ; }",
        }
        owner = g.source_owner(state, intent)
        for key, value in (
            ("InvocationID", "b" * 32),
            ("ControlGroup", "/foreign"),
            ("RuntimeMaxUSec", "7200s"),
            ("KillMode", "process"),
            ("ExecStart", "{ argv[]=/bin/other ; }"),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                g.source_owner(dict(state, **{key: value}), intent, owner)

    def test_output_allowlist_and_same_run_primary_readback(self):
        g = self.generation
        for name in (
            "guard/control.json",
            "compiler-readiness.json",
            "failed-request.stdout",
            "component-results.json",
            "ZY.failure.txt",
            "x2-native-summary.json",
            "ZY-X2-Y.FCStd",
        ):
            g.evidence_name(name)
        for name in (
            "native-x2/result.json",
            "generated-raw/a.faces.json",
            "source/secret.py",
            "unexpected.txt",
            "../escape",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                g.evidence_name(name)
        (self.work / "evidence/assessment.json").write_bytes(
            b'{"status":"FAIL"}'
        )
        g.evidence_archive(self.work, self.work / "evidence.tar")
        with tarfile.open(self.work / "evidence.tar") as archive:
            self.assertEqual(
                set(archive.getnames()),
                {"evidence/assessment.json", "evidence-manifest.json"},
            )
        (self.work / "readback-primary").mkdir()
        (self.work / "readback-primary/evidence.tar").write_bytes(b"wrong")
        with (
            patch.dict(
                g.os.environ,
                {
                    "L1_PRIMARY_UPLOAD": "success",
                    "L1_PRIMARY_DOWNLOAD": "success",
                    "L1_PRIMARY_ID": "123",
                },
            ),
            patch.object(g, "cleanup_owned") as cleanup,
        ):
            self.assertEqual(g.publish(self.work), 1)
            cleanup.assert_not_called()

    def test_import_safe_native_suite_and_readiness_has_no_construction(self):
        entry = importlib.import_module("tests.hosted_to_zy_generation_suite")
        self.assertTrue(hasattr(entry.ZyGeneration, "test_readiness"))
        self.assertTrue(hasattr(entry.ZyGeneration, "test_native"))
        self.assertNotIn("FreeCAD", sys.modules)
        self.assertNotIn("Part", sys.modules)
        self.assertNotIn("PySide6", sys.modules)


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False).result
    if not result.wasSuccessful():
        raise SystemExit(1)
    print("Hosted fixed ZY generation controls passed")
