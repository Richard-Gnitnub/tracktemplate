"""Exercise fixed ZY generation controls with inert process/file doubles."""

from copy import deepcopy
import hashlib
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import Mock, patch


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
    """Only inert shell syntax runs; no service/compiler/native/network."""

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
            "MainPID": "31415",
            "ControlPID": "0",
            "ProcessCommandLine": intent["command"],
            "ProcessStart": "12345",
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

    def gate_state(self):
        g = self.generation
        command = [
            "/bin/sh",
            "-c",
            'kill -STOP "$$" || exit; exec "$@"',
            "zy-source",
            "/usr/bin/python3",
            "-B",
            "/fixed/entry.py",
        ]
        intent = {
            "unit": "tracktemplate-zy-source-123.service",
            "command": command,
            "seconds": 33,
            "lease_id": "lease",
        }
        state = {
            "Id": intent["unit"],
            "MainPID": "31415",
            "ControlPID": "0",
            "ControlGroup": (
                f"/user.slice/user-{g.os.getuid()}.slice/"
                f"user@{g.os.getuid()}.service/app.slice/" + intent["unit"]
            ),
            "InvocationID": "a" * 32,
            "KillMode": "control-group",
            "Restart": "no",
            "SendSIGKILL": "yes",
            "RuntimeMaxUSec": "33s",
            "TimeoutStopUSec": "5s",
            "ExecStart": (
                "{ path=/bin/sh ; argv[]=/bin/sh -c "
                'kill -STOP "$$" || exit; exec "$@" zy-source '
                "/usr/bin/python3 -B /fixed/entry.py ; "
                "ignore_errors=no ; start_time=[now] ; }"
            ),
            "ProcessCommandLine": command,
            "ProcessStart": "12345",
            "ProcessState": "T",
            "CgroupProcesses": ["31415"],
            "ActiveState": "active",
            "ExecMainExitTimestampMonotonic": "0",
        }
        return intent, state

    def test_real_service_gate_disables_expansion_and_stop_failure_refuses(
        self,
    ):
        g, launches = self.generation, []
        lease = Mock(lease_id="lease")
        lease.read.return_value = {}

        def capture(arguments, _deadline, **_kwargs):
            launches.append(arguments)
            raise ValueError("inert stop before any service execution")

        with (
            patch.object(g, "verify_inputs"),
            patch.object(g, "source_unit", return_value="unit.service"),
            patch.object(g, "remaining_seconds", return_value=33),
            patch.object(g, "show_unit", return_value={"MainPID": "0"}),
            patch.object(g, "bounded_command", side_effect=capture),
            patch.object(g, "source_cleanup", return_value={"cleanup": True}),
        ):
            result = g.run_preparation(
                self.work, {"stage": "readiness"}, lease, 999
            )
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(len(launches), 1)
        argv = launches[0]
        self.assertIn("--expand-environment=no", argv)
        script = argv[argv.index("/bin/sh") + 2]
        inert = subprocess.run(
            [
                "/bin/sh",
                "-c",
                "kill() { return 7; }; " + script,
                "zy-source",
                "/bin/sh",
                "-c",
                "printf UNAUTHORISED",
            ],
            capture_output=True,
            timeout=2,
            check=False,
        )
        self.assertNotEqual(inert.returncode, 0)
        self.assertEqual(inert.stdout, b"")

    def test_complete_gate_argv_and_cleanup_identity(self):
        g = self.generation
        intent, state = self.gate_state()
        properties = {
            key: value
            for key, value in state.items()
            if key
            not in (
                "ProcessCommandLine",
                "ProcessStart",
                "ProcessState",
                "CgroupProcesses",
            )
        }
        command = Mock(
            returncode=0,
            stdout="\n".join(
                key + "=" + value for key, value in properties.items()
            ),
        )
        raw = b"\0".join(arg.encode() for arg in intent["command"]) + b"\0"
        with (
            patch.object(g, "bounded_command", return_value=command),
            patch.object(g.guard, "_process_start", return_value="12345"),
            patch.object(Path, "read_bytes", return_value=raw),
            patch.object(
                Path,
                "read_text",
                side_effect=["State:\tT (stopped)", "31415\n"],
            ),
        ):
            observed = g.show_unit(intent["unit"], 105)
        self.assertEqual(observed["ProcessCommandLine"], intent["command"])
        self.assertEqual(observed["ProcessState"], "T")
        owner = g.source_owner(state, intent)
        for index, replacement in (
            (0, "/bin/other"),
            (2, "exec unwanted"),
            (6, "/different/entry.py"),
        ):
            changed = deepcopy(state)
            changed["ProcessCommandLine"][index] = replacement
            with self.subTest(index=index), self.assertRaises(ValueError):
                g.source_owner(changed, intent)
        ended = dict(
            state,
            MainPID="0",
            ControlGroup="",
            ProcessStart=None,
            ProcessCommandLine=None,
            ActiveState="inactive",
        )
        self.assertEqual(g.source_owner(ended, intent, owner), owner)
        with self.assertRaises(ValueError):
            g.source_owner(dict(ended, InvocationID="b" * 32), intent, owner)
        (self.work / "evidence/source-intent.json").write_bytes(
            encoded(intent)
        )
        (self.work / "evidence/source-ownership.json").write_bytes(
            encoded(owner)
        )
        with (
            patch.dict(g.os.environ, {"GITHUB_RUN_ID": "123"}),
            patch.object(g, "show_unit", side_effect=[state, ended]),
            patch.object(g, "bounded_command") as stop,
            patch.object(g.guard, "_empty", return_value=True),
        ):
            cleanup = g.source_cleanup(self.work)
        self.assertIs(cleanup["cleanup"], True)
        self.assertEqual(
            stop.call_args.args[0],
            ["systemctl", "--user", "stop", intent["unit"]],
        )
        # A command mismatch must not supply a cleanup owner.
        changed = dict(state, ProcessCommandLine=["/bin/other"])
        with self.assertRaises(ValueError):
            g.source_owner(changed, intent)

    def run_source_observation(
        self, name, *, terminal_changes=None, final_changes=None,
        host_changes=None, live_changes=None, no_live=False,
        final_group_present=False, deadline_expired=False,
    ):
        """Run the real monitor against inert service and kernel snapshots."""
        g = self.generation
        work = self.work / name
        (work / "evidence").mkdir(parents=True)
        lease = Mock(lease_id="lease")
        lease.read.return_value = {}
        sample = {
            "memory.current": "100", "memory.peak": "100",
            "memory.swap.current": "0", "pids.current": "1",
            "memory.events": "high 0\nmax 0\noom 0\noom_kill 0\n",
            "cpu.stat": "usage_usec 10\n",
            "memory.pressure": (
                "some avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
                "full avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
            ),
            "cgroup.events": "populated 1\n", "cgroup.procs": "31415\n",
        }
        host = {
            "MemAvailable": 13 * 1024**3, "SwapTotal": 0, "SwapFree": 0,
            "memory_pressure": sample["memory.pressure"],
        }
        final = dict.fromkeys(g.pilot.SAMPLE_FIELDS)
        final.update(final_changes or {})
        sample.update(live_changes or {})
        snapshots, present = {}, [True]
        clock = [100]
        samples = [final] if no_live else [sample, final]
        original_exists, original_read = Path.exists, Path.read_text
        limits = {
            "memory.max": str(4096 * 1024**2),
            "memory.high": str(4096 * 1024**2),
            "memory.swap.max": "0", "cpu.max": "100000 100000",
            "pids.max": "128",
        }

        def gate(_work, intent, _deadline):
            _, state = self.gate_state()
            state["ProcessCommandLine"] = intent["command"]
            state["ExecStart"] = (
                "{ argv[]=" + " ".join(intent["command"])
                + " ; ignore_errors=no ; }"
            )
            owner = g.source_owner(state, intent)
            snapshots["running"] = dict(state, ProcessState="S")
            snapshots["terminal"] = dict(
                state, MainPID="0", ControlGroup="", ProcessStart=None,
                ProcessCommandLine=None, ExecMainExitTimestampMonotonic="1",
                ExecMainCode="1", ExecMainStatus="0", Result="success",
                ActiveState="active", SubState="exited",
            )
            snapshots["terminal"].update(terminal_changes or {})
            return owner, state

        def show(_unit, _deadline):
            if not snapshots:
                return {"MainPID": "0"}
            return snapshots["terminal" if not present[0] else "running"]

        def measure(_group):
            value = samples.pop(0)
            if not samples:
                present[0] = final_group_present
                clock[0] = 134 if deadline_expired else 100
            return value

        def exists(path):
            if str(path).startswith("/sys/fs/cgroup/"):
                return present[0]
            return original_exists(path)

        def read_text(path, *args, **kwargs):
            if str(path).startswith("/sys/fs/cgroup/"):
                return limits[path.name]
            return original_read(path, *args, **kwargs)

        hosts = [dict(host, **(host_changes or {}))]
        if not no_live:
            hosts.insert(0, host)
        with (
            patch.dict(g.os.environ, {"GITHUB_RUN_ID": "123"}),
            patch.object(g, "verify_inputs"),
            patch.object(g, "wait_source_gate", side_effect=gate),
            patch.object(g, "show_unit", side_effect=show),
            patch.object(g, "bounded_command"),
            patch.object(g, "source_cleanup", return_value={"cleanup": True}),
            patch.object(g.guard, "_sample", side_effect=measure),
            patch.object(g, "host_sample", side_effect=hosts),
            patch.object(g.time, "monotonic", side_effect=lambda: clock[0]),
            patch.object(g.time, "sleep"),
            patch.object(Path, "exists", exists),
            patch.object(Path, "read_text", read_text),
        ):
            result = g.run_preparation(
                work, {"stage": "readiness"}, lease, 133
            )
        rows = [
            json.loads(line) for line in
            (work / "evidence/source-measurements.jsonl").read_text()
            .splitlines()
        ]
        self.assertEqual(rows[-1]["cgroup"], final if not samples else sample)
        return result, snapshots, rows

    def test_removed_source_group_refreshes_exact_terminal_evidence(self):
        _, live = self.gate_state()
        for index, group in enumerate(("", live["ControlGroup"])):
            with self.subTest(retained_group=group):
                result, states, rows = self.run_source_observation(
                    "race-" + str(index),
                    terminal_changes={"ControlGroup": group},
                )
                self.assertEqual(result["status"], "PASS", result["errors"])
                self.assertEqual(result["live_samples"], 1)
                self.assertEqual(
                    result["resource_accounting"], "sampled-lower-bound"
                )
                observed = result["removed_group_observation"]
                self.assertEqual(
                    observed["initial_state"], states["running"]
                )
                self.assertEqual(
                    observed["terminal_state"], states["terminal"]
                )
                self.assertEqual(observed["sample"], rows[-1]["cgroup"])
                self.assertIs(observed["group_removed"], True)

    def test_removed_group_requires_successful_unchanged_terminal_owner(self):
        changes = (
            {"InvocationID": "b" * 32}, {"MainPID": "991"},
            {"ControlPID": "991"}, {"ControlGroup": "/foreign"},
            {"ExecStart": "changed ; ignore_errors=no ; }"},
            {"RuntimeMaxUSec": "34s"},
            {"ExecMainExitTimestampMonotonic": "0"},
            {"ExecMainCode": "2"}, {"ExecMainStatus": "1"},
            {"Result": "timeout"},
        )
        for index, change in enumerate(changes):
            with self.subTest(change=change):
                result, _, _ = self.run_source_observation(
                    "terminal-" + str(index), terminal_changes=change
                )
                self.assertEqual(result["status"], "FAIL")
                self.assertTrue(result["errors"])

    def test_removed_group_never_excuses_telemetry_or_deadline_failures(self):
        cases = (
            {"no_live": True}, {"final_group_present": True},
            {"final_changes": {"memory.current": "1"}},
            {"host_changes": {"MemAvailable": 1}},
            {"host_changes": {"SwapTotal": 1}},
            {"host_changes": {"memory_pressure": "unavailable"}},
            {"live_changes": {"memory.events": "high 1\nmax 0\noom 0\n"}},
            {"deadline_expired": True},
        )
        for index, options in enumerate(cases):
            with self.subTest(options=options):
                result, _, _ = self.run_source_observation(
                    "resource-" + str(index), **options
                )
                self.assertEqual(result["status"], "FAIL")
                self.assertTrue(result["errors"])

    def cleanup_fixture(self, name):
        g = self.generation
        work = self.work / name
        (work / "evidence").mkdir(parents=True)
        intent, state = self.gate_state()
        owner = g.source_owner(state, intent)
        gone = dict(
            state, MainPID="0", ControlPID="0", ControlGroup="",
            InvocationID="", RuntimeMaxUSec="infinity", ExecStart="",
            ActiveState="inactive", SubState="dead", ProcessStart=None,
            ProcessCommandLine=None,
        )
        for filename, value in (
            ("source-intent.json", intent), ("source-ownership.json", owner),
        ):
            (work / "evidence" / filename).write_bytes(encoded(value))
        with (
            patch.dict(g.os.environ, {"GITHUB_RUN_ID": "123"}),
            patch.object(g, "show_unit", side_effect=[state, gone]),
            patch.object(g, "bounded_command") as stop,
            patch.object(g.guard, "_empty", return_value=True),
        ):
            first = g.source_cleanup(work)
        self.assertIs(first["cleanup"], True)
        self.assertIs(first["group_removed"], True)
        stop.assert_called_once()
        proof = {"status": "FAIL", "finalization": first}
        (work / "evidence/source-result.json").write_bytes(encoded(proof))
        return work, owner, gone, proof

    def test_repeated_cleanup_requires_prior_owned_removal_and_fresh_absence(
        self,
    ):
        g = self.generation
        work, owner, gone, _ = self.cleanup_fixture("repeat")
        original = (work / "evidence/source-result.json").read_bytes()
        with (
            patch.dict(g.os.environ, {"GITHUB_RUN_ID": "123"}),
            patch.object(g, "show_unit", return_value=gone),
            patch.object(g, "bounded_command") as stop,
            patch.object(g.guard, "_empty", return_value=True),
            patch.object(
                g.guard, "_process_start", side_effect=FileNotFoundError
            ),
        ):
            for _ in range(2):
                result = g.source_cleanup(work)
                self.assertIs(result["cleanup"], True, result["errors"])
                self.assertEqual(result["owner"], owner)
            stop.assert_not_called()
        self.assertEqual(
            (work / "evidence/source-result.json").read_bytes(), original
        )

    def test_repeated_cleanup_refuses_foreign_or_unproved_state(self):
        g = self.generation
        cases = (
            ("missing-proof", {}, None, True, None),
            ("changed-proof", {}, "owner", True, None),
            ("not-removed", {}, "group_removed", True, None),
            ("failed-proof", {}, "cleanup", True, None),
            ("foreign", {"InvocationID": "b" * 32}, None, True, None),
            ("pid", {"MainPID": "991"}, None, True, None),
            ("control", {"ControlPID": "991"}, None, True, None),
            ("group", {"ControlGroup": "/foreign"}, None, True, None),
            ("residue", {}, None, False, None),
            ("same-pid", {}, None, True, "12345"),
        )
        for name, change, corrupt, empty, process_start in cases:
            with self.subTest(name=name):
                work, _, gone, proof = self.cleanup_fixture(name)
                path = work / "evidence/source-result.json"
                if name == "missing-proof":
                    path.unlink()
                elif corrupt:
                    proof["finalization"][corrupt] = False
                    path.write_bytes(encoded(proof))
                with (
                    patch.dict(g.os.environ, {"GITHUB_RUN_ID": "123"}),
                    patch.object(
                        g, "show_unit", return_value=dict(gone, **change)
                    ),
                    patch.object(g, "bounded_command") as stop,
                    patch.object(g.guard, "_empty", return_value=empty),
                    patch.object(
                        g.guard, "_process_start", return_value=process_start
                    ),
                ):
                    result = g.source_cleanup(work)
                self.assertIs(result["cleanup"], False)
                self.assertTrue(result["errors"])
                stop.assert_not_called()

    def test_stop_gate_waits_for_same_pid_and_refuses_late_changes(self):
        g = self.generation
        intent, stopped = self.gate_state()
        running = dict(stopped, ProcessState="R")
        with (
            patch.object(g, "show_unit", side_effect=[running, stopped]),
            patch.object(g.time, "monotonic", return_value=100),
            patch.object(g.time, "sleep") as sleep,
            patch.object(g, "bounded_command") as command,
        ):
            owner, state = g.wait_source_gate(self.work, intent, 105)
        self.assertEqual(owner["pid"], 31415)
        self.assertEqual(state["ProcessState"], "T")
        sleep.assert_called_once()
        command.assert_not_called()
        for index, change in enumerate(
            (
                {"MainPID": "31416"},
                {"InvocationID": "b" * 32},
                {"ProcessStart": "changed"},
                {"CgroupProcesses": ["31415", "9"]},
                {"ExecMainExitTimestampMonotonic": "1"},
            )
        ):
            directory = self.work / str(index)
            (directory / "evidence").mkdir(parents=True)
            with (
                self.subTest(change=change),
                patch.object(
                    g,
                    "show_unit",
                    side_effect=[running, dict(stopped, **change)],
                ),
                patch.object(g.time, "monotonic", return_value=100),
                patch.object(g.time, "sleep"),
                patch.object(g, "bounded_command") as command,
                self.assertRaises(ValueError),
            ):
                g.wait_source_gate(directory, intent, 105)
            command.assert_not_called()
        directory = self.work / "timeout"
        (directory / "evidence").mkdir(parents=True)
        clock = [100]

        def late_wake(_seconds):
            clock[0] = 106

        with (
            patch.object(g, "show_unit", return_value=running),
            patch.object(g.time, "monotonic", side_effect=lambda: clock[0]),
            patch.object(g.time, "sleep", side_effect=late_wake),
            patch.object(g, "bounded_command") as command,
            self.assertRaises(ValueError),
        ):
            g.wait_source_gate(directory, intent, 105)
        command.assert_not_called()

    def test_partial_metadata_keeps_first_failure_bytes_before_cleanup(self):
        g = self.generation
        cases = (
            (b'{"returncode":', b'{"status":"FAIL"}'),
            (b"[]", b'{"status":"FAIL"}'),
            (b'{"returncode":0}', b"[]"),
            (None, b"original partial raw bytes"),
        )
        for index, (metadata, raw) in enumerate(cases):
            work = self.work / str(index)
            evidence = work / "evidence"
            evidence.mkdir(parents=True)
            generated = work / "generated"
            streams = generated / "generated-raw"
            streams.mkdir(parents=True)
            rows = [
                {
                    "name": name,
                    "request_identity": identity(name.encode()),
                    "historical_raw_identity": None,
                }
                for name in ("first", "second")
            ]
            (streams / "first.faces.json").write_bytes(b'{"status":"PASS"}')
            (streams / "first.faces.json.process.json").write_bytes(
                b'{"returncode":0}'
            )
            (streams / "first.stderr").write_bytes(b"")
            (streams / "second.faces.json").write_bytes(raw)
            (streams / "second.stderr").write_bytes(b"original stderr")
            if metadata is not None:
                (streams / "second.faces.json.process.json").write_bytes(
                    metadata
                )
            with self.subTest(metadata=metadata, raw=raw):
                result = g.preserve_generation_failure(
                    generated, rows, evidence
                )
                self.assertEqual(result["request"], "second")
                self.assertEqual(
                    (evidence / "failed-request.stdout").read_bytes(), raw
                )
                self.assertEqual(
                    (evidence / "failed-request.stderr").read_bytes(),
                    b"original stderr",
                )
                self.assertTrue(result["parse_limitations"])
                if metadata is not None:
                    self.assertEqual(
                        (
                            evidence / "failed-request.process.json"
                        ).read_bytes(),
                        metadata,
                    )
                self.assertNotIn(
                    "first.faces.json", [p.name for p in evidence.iterdir()]
                )

    def test_failed_stream_copy_blocks_staging_retirement(self):
        g = self.generation
        generated = self.work / "generated"
        streams = generated / "generated-raw"
        streams.mkdir(parents=True)
        (streams / "failed.faces.json").write_bytes(b"partial original")
        (streams / "failed.stderr").write_bytes(b"original error")
        rows = [
            {
                "name": "failed",
                "request_identity": identity(b"request"),
                "historical_raw_identity": None,
            }
        ]
        approved = self.work / "approved/x2"
        approved.mkdir(parents=True)
        (approved / "x2-generation-settings.json").write_bytes(
            encoded({"requests": rows})
        )
        (self.work / "evidence/process-finalization.json").write_bytes(
            encoded({"cleanup": True})
        )
        with patch.object(
            g, "preserve_copy", side_effect=OSError("copy failed")
        ):
            with self.assertRaises(OSError):
                g.preserve_generation_failure(
                    generated, rows, self.work / "evidence"
                )
        with (
            patch.object(g, "verify_inputs"),
            patch.object(g.shutil, "rmtree") as retire,
            self.assertRaises((ValueError, OSError)),
        ):
            g.cleanup_owned(self.work)
        retire.assert_not_called()
        self.assertEqual(
            (streams / "failed.faces.json").read_bytes(), b"partial original"
        )

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
