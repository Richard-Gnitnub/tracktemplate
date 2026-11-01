"""Offline installer ownership and cleanup regressions; no OS installation."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import hosted_l1_gui_install as installer  # noqa: E402


class InstallerControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.work = self.root / 'l1-gui-42'
        (self.work / 'evidence').mkdir(parents=True)
        self.environment = {
            'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted',
            'GITHUB_RUN_ID': '42', 'GITHUB_RUN_ATTEMPT': '1',
            'GITHUB_SHA': 'a' * 40, 'RUNNER_TEMP': str(self.root),
            'GITHUB_ENV': str(self.root / 'github-env'),
        }
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, self.environment, clear=True).start()
        patch.object(installer, 'CGROUP_ROOT', self.root / 'cgroup').start()
        self.state = 'absent'
        self.reads = 0
        self.exit_status = 0
        self.commands = []
        self.foreign = False
        self.incomplete = False
        self.residual = False
        self.clock = 0.0
        self.complete_after = 3
        self.released = False
        patch.object(installer.time, 'monotonic', self.now).start()
        patch.object(installer.time, 'sleep', self.sleep).start()
        patch.object(installer, '_command', self.command).start()
        patch.object(installer, '_show', self.show).start()

    def now(self):
        return self.clock

    def sleep(self, seconds):
        self.clock += seconds

    def command(self, arguments, deadline, *, check=True, timeout=5):
        if self.clock >= deadline:
            raise ValueError('Installer command deadline expired')
        self.commands.append(arguments)
        if 'systemd-run' in arguments:
            self.state = 'running'
        if 'stop' in arguments:
            self.state = 'inactive'
        return subprocess.CompletedProcess(arguments, 0, '', '')

    def show(self, unit, deadline):
        if self.clock >= deadline:
            raise ValueError('Installer query deadline expired')
        if self.state == 'absent':
            return {'Id': unit, 'LoadState': 'not-found',
                    'ActiveState': 'inactive', 'SubState': 'dead',
                    'MainPID': '0', 'ControlPID': '0', 'ControlGroup': '',
                    'InvocationID': ''}
        self.reads += 1
        if self.state == 'running' and self.reads >= self.complete_after:
            self.state = 'exited'
        row = {
            'Id': unit, 'LoadState': 'loaded',
            'InvocationID': ('b' if self.foreign else 'a') * 32,
            'ControlGroup': '/system.slice/' + unit,
            'MainPID': '100' if self.state == 'running' else '0',
            'ControlPID': '0',
            'ActiveState': 'inactive' if self.state == 'inactive' else 'active',
            'SubState': 'running' if self.state == 'running' else 'exited',
            'ExecMainCode': '1', 'ExecMainStatus': str(self.exit_status),
            'ExecMainExitTimestampMonotonic': '0' if self.state == 'running' else '100',
            'Result': 'success' if self.exit_status == 0 else 'exit-code',
            'User': str(os.getuid()), 'Group': str(os.getgid()),
            'RuntimeMaxUSec': '9min 30s', 'TimeoutStopUSec': '5s',
            'KillMode': 'control-group', 'Restart': 'no',
            'SendSIGKILL': 'yes', 'Type': 'exec', 'RemainAfterExit': 'yes',
            'ExecStart': ('{ path=/bin/bash ; argv[]=/bin/bash '
                          f'{self.work / "installer.sh"} ; ignore_errors=no ; }}'),
        }
        group = installer.CGROUP_ROOT / row['ControlGroup'].lstrip('/')
        group.mkdir(parents=True, exist_ok=True)
        active = self.state == 'running' or self.residual
        values = {
            'memory.current': '1024', 'memory.peak': '2048',
            'memory.events': 'low 0\nhigh 0\nmax 0\noom 0\noom_kill 0',
            'memory.swap.current': '0',
            'memory.pressure': ('some avg10=0.00 avg60=0.00 avg300=0.00 total=0\n'
                                'full avg10=0.00 avg60=0.00 avg300=0.00 total=0'),
            'cpu.stat': 'usage_usec 3000',
            'pids.current': '1' if active else '0',
            'cgroup.events': 'populated 1' if active else 'populated 0',
            'cgroup.procs': '100' if active else '',
        }
        if self.incomplete:
            values.pop('memory.peak')
        for name, value in values.items():
            (group / name).write_text(value)
        if self.released and self.state == 'inactive':
            row['ControlGroup'] = ''
        return row

    def result(self):
        return json.loads((self.work / 'evidence/installer-result.json').read_text())

    def test_success_requires_completed_command_resources_and_cleanup(self):
        self.assertEqual(installer.run(self.work), 0)
        result = self.result()
        self.assertEqual(result['status'], 'PASS')
        self.assertTrue(result['cleanup'])
        self.assertGreater(result['resources']['memory_peak_bytes'], 0)
        self.assertEqual(result['exit_status'], 0)
        self.assertIn('XDG_RUNTIME_DIR=', Path(os.environ['GITHUB_ENV']).read_text())
        self.assertTrue(installer.cleanup(self.work)['cleanup'])

    def test_install_failure_is_retained_and_cleaned_without_retry(self):
        self.exit_status = 100
        self.assertEqual(installer.run(self.work), 1)
        result = self.result()
        self.assertEqual(result['status'], 'FAIL')
        self.assertTrue(result['cleanup'])
        self.assertEqual(result['exit_status'], 100)
        self.assertEqual(sum('systemd-run' in row for row in self.commands), 1)
        self.assertFalse(Path(os.environ['GITHUB_ENV']).exists())

    def test_foreign_existing_unit_is_not_started_or_stopped(self):
        self.state = 'running'
        self.assertEqual(installer.run(self.work), 1)
        self.assertFalse(self.result()['cleanup'])
        self.assertFalse(self.commands)

    def test_changed_invocation_never_stops_foreign_unit(self):
        self.assertEqual(installer.run(self.work), 0)
        self.commands.clear()
        self.foreign = True
        self.assertFalse(installer.cleanup(self.work)['cleanup'])
        self.assertFalse(any('stop' in row for row in self.commands))

    def test_incomplete_telemetry_cannot_pass_install(self):
        self.incomplete = True
        self.assertEqual(installer.run(self.work), 1)
        self.assertEqual(self.result()['status'], 'FAIL')

    def test_populated_group_cannot_claim_cleanup(self):
        self.residual = True
        self.assertEqual(installer.run(self.work), 1)
        self.assertFalse(self.result()['cleanup'])

    def test_observation_deadline_stops_owned_hung_install_once(self):
        self.complete_after = 10**9
        self.assertEqual(installer.run(self.work), 1)
        result = self.result()
        self.assertEqual(result['status'], 'FAIL')
        self.assertTrue(result['cleanup'])
        self.assertEqual(sum('systemd-run' in row for row in self.commands), 1)
        self.assertIn('deadline', result['errors'][0])

    def test_stopped_unit_can_release_group_without_losing_ownership(self):
        self.released = True
        self.assertEqual(installer.run(self.work), 0)
        self.assertTrue(installer.cleanup(self.work)['cleanup'])

    def test_local_workspace_cannot_write_cleanup_evidence(self):
        os.environ['RUNNER_ENVIRONMENT'] = 'self-hosted'
        self.assertEqual(installer.run(self.work), 1)
        self.assertFalse((self.work / 'evidence/installer-result.json').exists())
        self.assertFalse(self.commands)

    def test_missing_or_malformed_ownership_is_not_clearance(self):
        self.assertFalse(installer.cleanup(self.work)['cleanup'])
        path = self.work / 'evidence/installer-ownership.json'
        path.write_text('{')
        self.assertFalse(installer.cleanup(self.work)['cleanup'])
        self.assertFalse(self.commands)

    def test_cleanup_after_wrapper_interruption_uses_retained_owner(self):
        self.assertEqual(installer.run(self.work), 0)
        (self.work / 'evidence/installer-result.json').unlink()
        self.state = 'running'
        self.assertTrue(installer.cleanup(self.work)['cleanup'])

    def test_tampered_script_is_not_owned_cleanup(self):
        self.assertEqual(installer.run(self.work), 0)
        (self.work / 'installer.sh').write_text('echo changed\n')
        self.commands.clear()
        self.assertFalse(installer.cleanup(self.work)['cleanup'])
        self.assertFalse(self.commands)

    def test_launch_is_nonroot_bounded_and_keeps_apt_failure_strict(self):
        self.assertEqual(installer.run(self.work), 0)
        launch = next(row for row in self.commands if 'systemd-run' in row)
        for setting in ('RuntimeMaxSec=570', 'TimeoutStopSec=5',
                        'KillMode=control-group', 'Restart=no',
                        f'User={os.getuid()}'):
            self.assertIn('--property=' + setting, launch)
        self.assertNotIn('--collect', launch)
        self.assertNotIn('--wait', launch)
        script = (self.work / 'installer.sh').read_text()
        self.assertIn('Acquire::Retries=0', script)
        self.assertIn('Acquire::http::Timeout=15', script)
        self.assertIn('Acquire::https::Timeout=15', script)
        self.assertIn('--error-on=any', script)
        self.assertNotIn('allow-unauthenticated', script)
        self.assertNotIn('sources.list', script)
        self.assertIn('e63d66825c4daf9adb09283488c2bc2ace92ed8b24bcf81666933226ed082fd4', script)
        self.assertIn('fe192771c0992ad873e6a9ccc6e4f087c76314ce5ced165650cc7ea045a6bbaa', script)


if __name__ == '__main__':
    unittest.main()
