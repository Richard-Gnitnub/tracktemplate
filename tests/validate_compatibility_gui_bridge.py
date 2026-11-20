#!/usr/bin/env python3
"""Offline proofs for the fixed, contained compatibility bridge adapter."""

import hashlib
import json
from pathlib import Path
import stat
import sys
import tempfile
import types
import unittest
from unittest import mock
import xmlrpc.client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import compatibility_gui_bridge as bridge  # noqa: E402


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.contents = {name: (name + "\n").encode()
                         for name in bridge.SOURCE_FILES}
        pins = {name: bridge._identity(data)
                for name, data in self.contents.items()}
        self.pins = mock.patch.object(bridge, "SOURCE_FILES", pins)
        self.pins.start()
        self.addCleanup(self.pins.stop)
        self.wheel_bytes = b"controlled offline wheel witness"
        for name, value in (
                ("CLICK_WHEEL_BYTES", len(self.wheel_bytes)),
                ("CLICK_WHEEL_SHA256", hashlib.sha256(
                    self.wheel_bytes).hexdigest())):
            patcher = mock.patch.object(bridge, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.wheel = self.root / bridge.CLICK_WHEEL
        self.wheel.write_bytes(self.wheel_bytes)
        self.checkout = self.root / "checkout"
        self.checkout.mkdir()
        self.staged = self.root / "bridge"
        with mock.patch.object(bridge, "verify_checkout",
                               return_value=self.contents):
            self.record = bridge.prepare_bridge(
                self.checkout, self.staged, click_wheel=self.wheel)
        self.assessment = self.root / "assessment"
        (self.assessment / "benchmark-output/freecad-bridge").mkdir(
            parents=True)
        self.authority = self.root / "Xauthority"
        self.authority.write_bytes(b"private display cookie fixture")
        self.environment = {
            "DISPLAY": ":99", "QT_QPA_PLATFORM": "xcb",
            "XAUTHORITY": str(self.authority), "GITHUB_ACTIONS": "true",
            "GITHUB_RUN_ATTEMPT": "1", "PATH": "/untrusted/search/path",
        }

    def test_exact_staging_keeps_licenses_and_token_private(self):
        self.assertEqual(bridge.verify_bridge(self.staged), self.staged)
        self.assertEqual(stat.S_IMODE(self.staged.stat().st_mode), 0o700)
        token = self.staged / "rpc-token"
        self.assertEqual(stat.S_IMODE(token.stat().st_mode), 0o600)
        self.assertNotIn(token.read_text().strip(), json.dumps(self.record))
        self.assertEqual((self.staged / "LICENSE").read_bytes(),
                         self.contents["LICENSE"])
        self.assertEqual((self.staged / bridge.CLICK_WHEEL).read_bytes(),
                         self.wheel_bytes)

    def test_existing_destination_is_never_replaced(self):
        before = (self.staged / "rpc-token").read_bytes()
        with mock.patch.object(bridge, "verify_checkout",
                               return_value=self.contents):
            with self.assertRaisesRegex(ValueError, "Fresh bridge"):
                bridge.prepare_bridge(self.checkout, self.staged,
                                      click_wheel=self.wheel)
        self.assertEqual((self.staged / "rpc-token").read_bytes(), before)

    def test_wrong_wheel_is_refused_before_destination_creation(self):
        self.wheel.write_bytes(b"wrong wheel")
        target = self.root / "new-bridge"
        with mock.patch.object(bridge, "verify_checkout",
                               return_value=self.contents):
            with self.assertRaisesRegex(ValueError, "Click wheel"):
                bridge.prepare_bridge(self.checkout, target,
                                      click_wheel=self.wheel)
        self.assertFalse(target.exists())

    def test_modified_source_and_extra_import_are_rejected(self):
        client = self.staged / "src/freecad_cli/client.py"
        client.write_bytes(b"unreviewed import")
        with self.assertRaisesRegex(ValueError, "Pinned bridge bytes"):
            bridge.verify_bridge(self.staged)
        client.write_bytes(self.contents["src/freecad_cli/client.py"])
        (client.parent / "sitecustomize.py").write_text("secret = True")
        with self.assertRaisesRegex(ValueError, "inventory"):
            bridge.verify_bridge(self.staged)

    def test_symlink_and_readable_token_are_rejected(self):
        token = self.staged / "rpc-token"
        token.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "Private bridge token"):
            bridge.verify_bridge(self.staged)
        token.chmod(0o600)
        (self.root / "alias").symlink_to(self.staged, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            bridge.verify_bridge(self.root / "alias")

    def test_driver_token_is_exact_idempotent_and_never_overwritten(self):
        path = bridge.install_driver_token(self.staged, self.assessment)
        self.assertEqual(path.read_bytes(),
                         (self.staged / "rpc-token").read_bytes())
        self.assertEqual(bridge.install_driver_token(
            self.staged, self.assessment), path)
        path.write_bytes(b"existing private data")
        with self.assertRaisesRegex(ValueError, "Existing driver token"):
            bridge.install_driver_token(self.staged, self.assessment)
        self.assertEqual(path.read_bytes(), b"existing private data")

    def test_session_command_uses_exact_source_and_token_file_only(self):
        macro = self.root / "readiness.FCMacro"
        macro.write_text("# reviewed macro fixture\n")
        argv, env = bridge.session_command(
            self.staged, self.assessment, self.environment,
            execution_seconds=90, macro=macro)
        self.assertEqual(argv[:3], ["flatpak", "run", "--command=FreeCAD"])
        self.assertEqual(argv[-1], str(macro))
        self.assertIn(str(self.staged / "addon/FreecadCli"), argv)
        self.assertEqual(env["PATH"], "/usr/bin:/bin")
        self.assertEqual(env["FREECAD_CLI_EXECUTION_TIMEOUT"], "90")
        self.assertNotIn((self.staged / "rpc-token").read_text().strip(),
                         json.dumps([argv, env]))
        self.assertNotIn("PYTHONPATH", env)

    def test_credential_environment_and_extended_budget_refused(self):
        env = dict(self.environment, GITHUB_TOKEN="PRIVATE_CREDENTIAL_VALUE")
        with self.assertRaisesRegex(ValueError, "Unreviewed child"):
            bridge.session_command(self.staged, self.assessment, env,
                                   execution_seconds=90)
        for seconds in (True, 0, 7201, 90.0):
            with self.subTest(seconds=seconds):
                with self.assertRaisesRegex(ValueError, "timeout"):
                    bridge.session_command(
                        self.staged, self.assessment, self.environment,
                        execution_seconds=seconds)

    def test_probe_command_is_isolated_and_has_no_token_contents(self):
        argv, env = bridge.readiness_probe_command(
            self.staged, self.root / "bridge-readiness.json", deadline=100.0)
        self.assertEqual(argv[:4], ["/usr/bin/python3", "-I", "-S", "-B"])
        self.assertEqual(env, bridge.BASE_ENV)
        self.assertNotIn((self.staged / "rpc-token").read_text().strip(),
                         json.dumps([argv, env]))
        self.assertNotIn("HOME", env)

    def _launch(self, groups):
        evidence = self.root / "guard"
        evidence.mkdir()
        expected = "/user.slice/user-1000.slice/test.scope"
        (evidence / "ownership.json").write_text(json.dumps({
            "cgroup": expected}))
        child = mock.Mock(pid=123)
        with mock.patch.dict(sys.modules, {"FreeCAD": types.SimpleNamespace(
                GuiUp=True)}):
            with mock.patch.object(bridge, "_process_cgroup",
                                   side_effect=groups):
                with mock.patch.object(bridge.subprocess, "Popen",
                                       return_value=child) as popen:
                    result = bridge.launch_readiness_probe(
                        self.staged, self.root / "bridge-readiness.json",
                        deadline=bridge.time.monotonic() + 20,
                        guard_evidence=evidence)
        return child, popen, result

    def test_probe_is_child_of_exact_guarded_gui_cgroup(self):
        group = "/user.slice/user-1000.slice/test.scope"
        child, popen, result = self._launch([group, group])
        self.assertIs(result, child)
        self.assertEqual(popen.call_args.kwargs["env"], bridge.BASE_ENV)
        self.assertNotIn("stdout", popen.call_args.kwargs)
        self.assertNotIn("stderr", popen.call_args.kwargs)
        self.assertFalse((self.root / "bridge-client.stdout").exists())
        self.assertFalse((self.root / "bridge-client.stderr").exists())
        child.kill.assert_not_called()

    def test_uncontained_probe_is_refused_before_launch(self):
        evidence = self.root / "guard"
        evidence.mkdir()
        (evidence / "ownership.json").write_text(json.dumps({
            "cgroup": "/user.slice/user-1000.slice/test.scope"}))
        with mock.patch.dict(sys.modules, {
                "FreeCAD": types.SimpleNamespace(GuiUp=True)}), \
                mock.patch.object(bridge, "_process_cgroup",
                                  return_value="/unrelated.scope"), \
                mock.patch.object(bridge.subprocess, "Popen") as popen:
            with self.assertRaisesRegex(ValueError, "outside the guarded"):
                bridge.launch_readiness_probe(
                    self.staged, self.root / "bridge-readiness.json",
                    deadline=bridge.time.monotonic() + 20,
                    guard_evidence=evidence)
        popen.assert_not_called()

    def test_changed_child_cgroup_kills_only_owned_child(self):
        child = mock.Mock(pid=456)
        with mock.patch.object(bridge.subprocess, "Popen", return_value=child):
            evidence = self.root / "guard"
            evidence.mkdir()
            group = "/user.slice/user-1000.slice/test.scope"
            (evidence / "ownership.json").write_text(json.dumps({
                "cgroup": group}))
            with mock.patch.dict(sys.modules, {
                    "FreeCAD": types.SimpleNamespace(GuiUp=True)}):
                with mock.patch.object(bridge, "_process_cgroup",
                                       side_effect=[group, "/other.scope"]):
                    with self.assertRaisesRegex(ValueError, "escaped"):
                        bridge.launch_readiness_probe(
                            self.staged, self.root / "bridge-readiness.json",
                            deadline=bridge.time.monotonic() + 20,
                            guard_evidence=evidence)
        child.kill.assert_called_once_with()
        child.wait.assert_called_once_with(timeout=5)


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.report = {"gui_up": True, "documents": 0, "main_thread": True,
                       "name_present": False, "file_present": False,
                       "pid": 1234}
        self.calls = []
        self.async_report = dict(self.report)
        self.job_status = "completed"
        self.auth_refused = True
        self.delayed = False
        outer = self

        class Proxy:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def ping(self, token):
                if token == "invalid-readiness-token" and outer.auth_refused:
                    raise xmlrpc.client.Fault(
                        1, "Invalid FreeCAD CLI authentication token")
                return True

        class Client:
            def __init__(self, **kwargs):
                outer.calls.append(kwargs)

            def ping(self):
                return True

            def execute_code(self, code):
                outer.assertEqual(code, bridge.PROBE_CODE)
                return {"error": "", "output": json.dumps(outer.report)}

            def submit_code(self, code):
                outer.assertEqual(code, bridge.PROBE_CODE)
                return {"job_id": "a" * 32, "status": "queued"}

            def get_job(self, job_id):
                if outer.delayed:
                    outer.clock.now = 1000.0
                return {"job_id": job_id, "status": outer.job_status,
                        "error": "", "output": json.dumps(outer.async_report)}

        self.proxy = lambda deadline, clock: Proxy()
        self.loader = lambda root: Client

    def run_probe(self):
        with mock.patch.object(bridge, "_token", return_value="a" * 64):
            return bridge._probe(
                Path("/bounded/bridge"), 20.0, clock=self.clock,
                sleep=self.clock.sleep, proxy_factory=self.proxy,
                client_loader=self.loader)

    def test_original_client_sync_async_auth_and_same_process(self):
        result = self.run_probe()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["synchronous"], result["asynchronous"])
        self.assertEqual(result["geometry_builds"], 0)
        self.assertNotIn("a" * 64, json.dumps(result))
        self.assertTrue(all(call["host"] == "127.0.0.1"
                            and call["port"] == 19875
                            and 0 < call["timeout"] <= 2
                            for call in self.calls))

    def test_wrong_token_accepted_refuses_proof(self):
        self.auth_refused = False
        with self.assertRaisesRegex(ValueError, "Unauthenticated"):
            self.run_probe()
        self.assertEqual(self.calls, [])

    def test_nonempty_document_or_wrong_namespace_refuses_proof(self):
        for name, value in (("documents", 1), ("main_thread", False),
                            ("name_present", True), ("file_present", True)):
            before = self.report[name]
            self.report[name] = value
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "witness differs"):
                    self.run_probe()
            self.report[name] = before

    def test_process_change_and_failed_async_job_refuse_proof(self):
        self.async_report["pid"] = 9876
        with self.assertRaisesRegex(ValueError, "process or witness changed"):
            self.run_probe()
        self.async_report["pid"] = self.report["pid"]
        self.job_status = "failed"
        with self.assertRaisesRegex(ValueError, "async execution failed"):
            self.run_probe()

    def test_no_timeout_reset_after_rpc_or_poll(self):
        self.delayed = True
        with self.assertRaisesRegex(ValueError, "deadline exhausted"):
            self.run_probe()
        self.delayed = False
        self.clock.now = 10.0
        self.job_status = "running"
        with self.assertRaisesRegex(ValueError, "deadline exhausted"):
            self.run_probe()
        self.assertGreaterEqual(self.clock.now, 20.0)

    def test_non_loopback_endpoint_rejected(self):
        transport = bridge._DeadlineTransport(20.0, self.clock)
        with self.assertRaisesRegex(ValueError, "Loopback endpoint"):
            transport.make_connection("example.com:19875")


if __name__ == "__main__":
    unittest.main()
