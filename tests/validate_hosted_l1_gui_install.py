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

    def released_exit(self, unit, deadline, *, remove_group=False):
        row = self.show(unit, deadline)
        if self.state in ('exited', 'inactive'):
            group = installer.CGROUP_ROOT / row['ControlGroup'].lstrip('/')
            row['ControlGroup'] = ''
            if remove_group:
                for item in group.iterdir():
                    item.unlink()
                group.rmdir()
        return row

    def test_successful_exit_can_release_group_before_explicit_stop(self):
        # Hosted run 41286458961 reported active/exited, zero PIDs, exit 0
        # and an empty ControlGroup after the installation command ended.
        with patch.object(installer, '_show', self.released_exit):
            self.assertEqual(installer.run(self.work), 0)
        result = self.result()
        self.assertEqual(result['exit_status'], 0)
        self.assertEqual(result['terminal_unit']['ControlGroup'], '')
        self.assertEqual(result['terminal_unit']['SubState'], 'exited')
        self.assertTrue(result['cleanup'])
        self.assertGreater(result['resources']['samples'], 0)
        self.assertEqual(sum('systemd-run' in row for row in self.commands), 1)
        self.assertEqual(sum('stop' in row for row in self.commands), 1)

    def test_successful_exit_with_removed_group_keeps_prior_measurements(self):
        def removed(unit, deadline):
            return self.released_exit(unit, deadline, remove_group=True)

        with patch.object(installer, '_show', removed):
            self.assertEqual(installer.run(self.work), 0)
        result = self.result()
        self.assertTrue(result['cleanup'])
        self.assertTrue(result['finalization']['cgroup_removed'])
        self.assertEqual(result['resources']['memory_peak_bytes'], 2048)

    def test_released_exit_does_not_replace_empty_process_proof(self):
        self.residual = True
        with patch.object(installer, '_show', self.released_exit):
            self.assertEqual(installer.run(self.work), 1)
        self.assertEqual(self.result()['status'], 'FAIL')
        self.assertFalse(self.result()['cleanup'])
        self.assertFalse(Path(os.environ['GITHUB_ENV']).exists())

    def test_released_exit_requires_known_owner_and_successful_terminal_state(self):
        intent = installer._identity(self.work)
        self.state = 'exited'
        row = self.released_exit(intent['unit'], 5)
        owner = {'intent': intent, 'invocation': 'a' * 32,
                 'cgroup': '/system.slice/' + intent['unit']}
        self.assertEqual(installer._owned(row, intent, owner), owner)
        with self.assertRaises(ValueError):
            installer._owned(row, intent)
        invalid = {
            'MainPID': ['100'], 'ControlPID': ['100'],
            'SubState': ['running'], 'ActiveState': ['activating'],
            'ExecMainCode': ['0', '2'], 'ExecMainStatus': ['1'],
            'Result': ['exit-code', 'timeout'],
            'ExecMainExitTimestampMonotonic': ['', '0', '-1', 'invalid', None],
            'InvocationID': ['b' * 32], 'User': ['0'],
            'KillMode': ['process'], 'RuntimeMaxUSec': ['10min'],
            'ExecStart': ['{ argv[]=/bin/bash /foreign.sh ; }'],
        }
        for name, values in invalid.items():
            for value in values:
                with self.subTest(property=name, value=value):
                    with self.assertRaises(ValueError):
                        installer._owned(dict(row, **{name: value}),
                                         intent, owner)

    def test_local_workspace_cannot_write_cleanup_evidence(self):
        os.environ['RUNNER_ENVIRONMENT'] = 'self-hosted'
        self.assertEqual(installer.run(self.work), 1)
        self.assertFalse((self.work / 'evidence/installer-result.json').exists())
        self.assertFalse(self.commands)

    def completion_race(self, *, during_sample=False, first=False,
                        fresh=None, malformed_sample=False, deadline=False,
                        partial_fields=None):
        """Finish between a live unit read and its resource observation."""
        self.complete_after = 10**9
        trigger = 1 if first else 2
        raced = False
        sample_reads = 0
        original_sample = installer.guard._sample

        def remove_group(group):
            for item in group.iterdir():
                item.unlink()
            group.rmdir()

        def finish(group):
            nonlocal raced
            raced = True
            self.state = 'exited'
            remove_group(group)
            if deadline:
                self.clock = 575

        def show(unit, limit):
            row = self.show(unit, limit)
            group = installer.CGROUP_ROOT / row['ControlGroup'].lstrip('/')
            if not raced and not during_sample and self.reads == trigger:
                finish(group)
                return row  # The observation predates the actual exit.
            if raced and self.state in ('exited', 'inactive'):
                if not self.residual:
                    remove_group(group)
                    row['ControlGroup'] = ''
                if self.state == 'exited':
                    row.update(fresh or {})
            return row

        def sample(group):
            nonlocal sample_reads
            sample_reads += 1
            row = original_sample(group)
            if during_sample and not raced and sample_reads == trigger:
                finish(group)
                row['memory.peak'] = 'invalid' if malformed_sample else None
                row.update(partial_fields or {})
            return row

        with (
            patch.object(installer, '_show', show),
            patch.object(installer.guard, '_sample', sample),
        ):
            return installer.run(self.work)

    def test_completion_between_live_read_and_group_check(self):
        self.assertEqual(self.completion_race(), 0)
        result = self.result()
        self.assertEqual(result['resources']['samples'], 1)
        self.assertEqual(result['exit_status'], 0)
        self.assertTrue(result['cleanup'])
        evidence = result['completion_recheck']
        self.assertEqual(evidence['before']['SubState'], 'running')
        self.assertEqual(evidence['after']['SubState'], 'exited')
        self.assertEqual(sum('systemd-run' in row for row in self.commands), 1)
        self.assertEqual(sum('stop' in row for row in self.commands), 1)

    def test_completion_during_resource_read_keeps_only_complete_samples(self):
        self.assertEqual(self.completion_race(during_sample=True), 0)
        result = self.result()
        self.assertEqual(result['resources']['samples'], 1)
        self.assertEqual(result['resources']['memory_peak_bytes'], 2048)
        self.assertTrue(result['cleanup'])
        self.assertIn('completion_recheck', result)

    def test_completion_recheck_cannot_accept_a_live_unit(self):
        fresh = {'SubState': 'running', 'MainPID': '100',
                 'ExecMainExitTimestampMonotonic': '0',
                 'ControlGroup': ('/system.slice/'
                                  'tracktemplate-l1-install-42.service')}
        self.assertEqual(self.completion_race(fresh=fresh), 1)
        self.assertIn('Live installer cgroup disappeared',
                      self.result()['errors'][0])
        self.assertFalse(Path(os.environ['GITHUB_ENV']).exists())

    def test_completion_recheck_cannot_acquire_a_foreign_invocation(self):
        self.assertEqual(self.completion_race(
            fresh={'InvocationID': 'b' * 32}), 1)
        self.assertFalse(self.result()['cleanup'])
        self.assertFalse(any('stop' in row for row in self.commands))

    def test_completion_recheck_keeps_failed_exit(self):
        self.assertEqual(self.completion_race(fresh={
            'ActiveState': 'failed', 'SubState': 'failed',
            'ExecMainStatus': '100', 'Result': 'exit-code',
        }), 1)
        self.assertEqual(self.result()['exit_status'], 100)
        self.assertTrue(self.result()['cleanup'])

    def test_completion_recheck_requires_prior_complete_measurements(self):
        self.assertEqual(self.completion_race(first=True), 1)
        self.assertEqual(self.result()['resources'], {})
        self.assertFalse(Path(os.environ['GITHUB_ENV']).exists())

    def test_malformed_complete_sample_is_not_an_exit_race(self):
        self.assertEqual(self.completion_race(
            during_sample=True, malformed_sample=True), 1)
        self.assertNotIn('completion_recheck', self.result())
        self.assertIn('invalid', self.result()['errors'][0])

    def test_missing_final_field_does_not_hide_malformed_numeric_data(self):
        self.assertEqual(self.completion_race(
            during_sample=True, partial_fields={'memory.current': 'invalid'}),
            1)
        self.assertNotIn('completion_recheck', self.result())
        self.assertIn('invalid', self.result()['errors'][0])
        self.assertTrue(self.result()['cleanup'])
        self.assertFalse(Path(os.environ['GITHUB_ENV']).exists())

    def test_missing_final_field_does_not_hide_malformed_cpu_data(self):
        self.assertEqual(self.completion_race(
            during_sample=True, partial_fields={'cpu.stat': 'usage_usec -1'}),
            1)
        self.assertNotIn('completion_recheck', self.result())
        self.assertIn('Invalid installer CPU sample', self.result()['errors'][0])
        self.assertTrue(self.result()['cleanup'])
        self.assertFalse(Path(os.environ['GITHUB_ENV']).exists())

    def test_completion_recheck_keeps_original_deadline(self):
        self.assertEqual(self.completion_race(deadline=True), 1)
        self.assertIn('deadline', self.result()['errors'][0])
        self.assertTrue(self.result()['cleanup'])

    def test_completion_recheck_does_not_replace_process_cleanup(self):
        self.residual = True
        self.assertEqual(self.completion_race(), 1)
        self.assertFalse(self.result()['cleanup'])
        self.assertFalse(Path(os.environ['GITHUB_ENV']).exists())

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
