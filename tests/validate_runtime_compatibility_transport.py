#!/usr/bin/env python3
"""Offline tests for matrix admission, cleanup and exact artifact transport."""

import copy
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import importlib.util
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import runtime_compatibility_transport as transport  # noqa: E402
from tools.compatibility_evidence_output import RUNTIME  # noqa: E402

JOB_CLOCK = transport.job_clock


def timestamp(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def http_date(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime(
        '%a, %d %b %Y %H:%M:%S GMT')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False) + '\n')


class TransportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='matrix-transport-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.commit = '1' * 40
        for name in transport.matrix.CONTROL_FILES:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Offline source identity fixture: ' + name + '\n')
        capsule = transport.matrix.load_execution_capsule(
            ROOT / transport.matrix.CAPSULE, ROOT)
        selected = [entry['path'] for entry in transport.matrix.entries(capsule)]
        for name in (*transport.CAPSULES.values(), *selected,
                     transport.matrix.assessment.CANONICAL_PATH):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / name).read_bytes())
        pins = {name: transport.digest(self.source / name)
                for name in transport.matrix.CONTROL_FILES}
        self.receipts = {
            'review': {'status': 'PASS', 'source_commit': self.commit,
                'source_files': pins, 'independent': True,
                'stage': 'qualification',
                'output_scope_sha256': transport.readiness.SCOPE_SHA256},
            'recovery': {'status': 'PASS', 'source_commit': self.commit,
                'source_files': pins, 'independent_preservation': True},
            'readiness': {'status': 'PASS', 'source_commit': '2' * 40,
                'source_files': {name: pins[name]
                    for name in transport.readiness.CONTROL_FILES},
                'independent': True, 'stage': 'readiness',
                'runtime': copy.deepcopy(RUNTIME),
                'base_sha256': transport.matrix.assessment.BASE_SHA256,
                'candidate_sha256': transport.matrix.assessment.CANDIDATE_SHA256,
                'artifact_sha256': 'a' * 64, 'run_id': '122'},
        }
        self.control = {
            'schema_version': 1, 'stage': 'qualification',
            'owner_decision': 'D-P9-024', 'owner_statement_sha256':
            'd193c34674fa4eb09de4ccaad6a6ddfbf1a930fdd50f369652f33204e2daa19a',
            'output_scope_sha256': transport.readiness.SCOPE_SHA256,
            'app_commit': transport.readiness.APP_COMMIT,
            'runtime_commit': transport.readiness.RUNTIME_COMMIT,
            'capsule_sha256': transport.matrix.CAPSULE_SHA256,
            'heavy_seconds': 7200, 'display_seconds': 7300,
            'outer_seconds': 8400, 'installer_seconds': 540,
            'readiness_seconds': 90, 'memory_mib': 4096, 'reserve_mib': 8192,
            'cpu_percent': 100, 'tasks': 128, 'swap_bytes': 0,
            'parallel': False, 'retry': False, 'runtime_admission': False,
            'zy_execution': False, 'source_commit': self.commit,
            'source_files': pins,
        }
        self.raw = {name: json.dumps(value, indent=3) + '\n'
                    for name, value in self.receipts.items()}
        self.inputs = {'workload': 'compatibility-qualification'}
        self.event = self.root / 'event.json'
        self.controls = self.root / 'compatibility-matrix-control'
        self.install_work = self.root / 'l1-gui-123'
        self.work = self.root / 'runtime-compatibility'
        self.environment = {
            'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted',
            'GITHUB_REPOSITORY': 'Richard-Gnitnub/tracktemplate',
            'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_RUN_ATTEMPT': '1',
            'GITHUB_RUN_ID': '123', 'GITHUB_SHA': self.commit,
            'RUNNER_OS': 'Linux', 'RUNNER_ARCH': 'X64',
            'RUNNER_TEMP': str(self.root), 'GITHUB_EVENT_PATH': str(self.event),
        }
        self.bind_inputs()
        for manager in (patch.object(transport, 'ROOT', self.source),
                        patch.dict(os.environ, self.environment, clear=True)):
            manager.start()
            self.addCleanup(manager.stop)
        manager = patch.object(transport, 'job_clock', side_effect=self.clock)
        self.clock_mock = manager.start()
        self.addCleanup(manager.stop)

    def clock(self, _controls, seed_started):
        now = transport.time.time()
        monotonic = transport.time.monotonic()
        return transport.clock_projection({
            'id': 456, 'run_id': 123, 'head_sha': self.commit,
            'name': transport.JOB_NAME, 'status': 'in_progress',
            'started_at': timestamp(now - 60),
        }, http_date(now), {
            'seed_monotonic': seed_started, 'request_monotonic': monotonic,
            'received_monotonic': monotonic,
            'request_utc': now, 'received_utc': now,
        })

    def bind_inputs(self):
        for name, raw in self.raw.items():
            self.control[name] = {'path': name + '.json',
                'sha256': transport.hashlib.sha256(raw.encode()).hexdigest()}
        self.inputs.update(
            readiness_control=json.dumps(self.control, indent=2) + '\n',
            readiness_recovery=self.raw['recovery'],
            readiness_review=json.dumps({name: self.raw[name]
                                        for name in ('review', 'readiness')}))
        self.save_event()

    def save_event(self):
        save(self.event, {'repository': {'private': False,
            'full_name': 'Richard-Gnitnub/tracktemplate'}, 'inputs': self.inputs})

    def prepare(self):
        transport.seed()
        with patch.object(transport.matrix.pilot, '_command',
                          side_effect=[self.commit, '']):
            return transport.prepare()

    def outcomes(self, values=('success', 'success', 'success', 'success')):
        os.environ.update(dict(zip(transport.OUTCOMES, values)))

    def finalized(self, success=True):
        self.outcomes()
        save(self.root / 'compatibility-matrix-finalization.json', {
            'cleanup': success, 'workflow_outcomes': {
                key: os.environ[key] for key in transport.OUTCOMES}})

    def readback(self, kind):
        path = self.root / ('compatibility-matrix-' + kind + '.tar')
        target = self.root / ('compatibility-matrix-' + kind + '-readback')
        target.mkdir()
        shutil.copyfile(path, target / path.name)
        prefix = 'L1_PRIMARY' if kind == 'primary' else 'L1_FINAL'
        os.environ.update({prefix + '_UPLOAD': 'success',
                           prefix + '_DOWNLOAD': 'success', prefix + '_ID': '42'})

    def native07_originals(self):
        """Compose one synthetic native result through the actual transport."""
        stage = transport.matrix.NATIVE07_STAGE
        self.control.update(
            stage=stage, owner_statement_sha256=(
                transport.matrix.NATIVE07_OWNER_STATEMENT_SHA256))
        self.receipts['review']['stage'] = stage
        relative = 'tools/hosted_l1_gui_install.py'
        installer = (ROOT / relative).read_bytes()
        (self.source / relative).write_bytes(installer)
        installer_sha = transport.hashlib.sha256(installer).hexdigest()
        for name in ('review', 'readiness', 'recovery'):
            self.receipts[name]['source_files'][relative] = installer_sha
        self.raw = {name: json.dumps(value) + '\n'
                    for name, value in self.receipts.items()}
        self.bind_inputs()
        self.prepare()
        self.finalized()
        self.work.mkdir(mode=0o700)
        logs = self.root / 'compatibility-matrix-logs'
        logs.mkdir()
        for name in ('seed', 'prepare', 'install', 'acquire', 'run', 'finalize'):
            (logs / (name + '.log')).write_text('')
        for relative in ('acquisition.json', 'run-reservation.json'):
            save(self.controls / relative, {})
        for relative in ('installer-intent.json', 'installer-ownership.json',
                         'installer-result.json'):
            save(self.install_work / 'evidence' / relative, {})
        (self.install_work / 'evidence/installer-output.log').write_text('')
        (self.install_work / 'readiness_installer.py').write_text(
            transport.readiness.installer_source(installer.decode()))
        save(self.install_work / 'installer-adaptation.json', {})

        capsule = transport.matrix.load_execution_capsule(
            self.source / transport.matrix.CAPSULE, self.source)
        entry, = transport.matrix.selected_entries(capsule, stage)
        source = transport.matrix.identity(self.source / entry['path'])
        manifest = {'source_files': [{'path': entry['path'],
                                      'assessment': source}]}
        save(self.work / 'assessment-manifest.json', manifest)
        for relative in ('preparation.json', 'original-assessment-manifest.json'):
            save(self.work / relative, {})
        for relative in (
                'attempt.json', 'heavy-deadline.json', 'clearance.json',
                'display-start-intent.json', 'display-ownership.json',
                'display-kernel.json', 'display-cleanup.json'):
            save(self.work / 'evidence' / relative, {})
        for relative in ('display-samples.jsonl', 'host-memory.jsonl', 'xvfb.log'):
            (self.work / 'evidence' / relative).write_text('')
        session = Path('entries/native-07')
        directory = self.work / session
        directory.mkdir(mode=0o700, parents=True)
        directory.parent.chmod(0o700)
        (directory / 'native07-invocation-claim').touch(mode=0o600)
        tree = self.work / 'assessment'
        save(directory / 'invocation.json', {
            'id': entry['id'], 'kind': 'native', 'arguments': [],
            'entry_sha256': source['sha256'], 'assessment': str(tree),
            'entry_path': str(tree / entry['path']),
            'session_directory': str(directory),
        })
        for name in ('input-before.json', 'input-after.json'):
            save(directory / name, transport.observations.BASE_IDENTITY)
        save(directory / 'clearance.json', {'complete': True})
        save(directory / 'resource-assessment.json', {'status': 'PASS'})
        for name in ('clearance.json', 'control.json', 'deadline-clearance.json',
                     'ownership.json'):
            save(directory / 'guard' / name, {})
        save(directory / 'guard/result.json', {
            'status': 'completed', 'process_exit': 0, 'cleanup_proved': True,
        })
        witness = transport.matrix.ENTRY_MARKER + json.dumps({
            'id': entry['id'], 'sha256': source['sha256'],
            'run_name': '__main__',
        })
        stdout = '\n'.join((witness, entry['sentinel'],
                            transport.matrix.DONE_MARKER, ''))
        (directory / 'guard/stdout').write_text(stdout)
        (directory / 'guard/wrapper.stdout').write_text(stdout)
        (directory / 'guard/stderr').write_text('')
        (directory / 'guard/measurements.jsonl').write_text('')
        outcome = {
            'id': entry['id'], 'status': 'PASS', 'sessions': 1,
            'assessment_entry': source, 'originals_directory': str(directory),
        }
        save(self.work / 'evidence/matrix-entries.json', [outcome])
        save(self.work / 'evidence/entry-results.jsonl', outcome)
        save(self.work / 'evidence/matrix-assessment.json', {
            'stage': stage, 'status': 'PASS', 'completed_entries': 1,
            'runtime_admission': False, 'zy_execution': False,
            'display_cleanup': True, 'public_payload_status': 'NOT_SEALED',
        })
        finalizer = self.root / 'compatibility-matrix-finalizer'
        finalization = self.root / 'compatibility-matrix-finalization.json'
        summary = json.loads(finalization.read_text())
        save(finalization, dict(summary, runtime=True))
        save(finalizer / 'runtime.json', {'cleanup': True,
            'sessions': {session.as_posix(): True}})
        for name in ('display.json', 'installer.json'):
            save(finalizer / name, {'cleanup': True})
        for name in ('clearance.json', 'deadline-clearance.json',
                     'finalization.json'):
            save(finalizer / session / 'evidence' / name, {'cleanup': True})
        return directory, manifest

    def native07_seal(self, manifest):
        with (patch.object(transport.matrix.pilot, '_command',
                           side_effect=[self.commit, '']),
              patch.object(transport, 'prepared_manifest',
                           return_value=(manifest, {})),
              patch.object(transport.traceback, 'format_exc',
                           return_value='ValueError: exact injected failure\n'),
              patch.object(transport.observations,
                           'extract_matrix_payload') as typed,
              (self.root / 'compatibility-matrix-logs/seal.log').open('x')
              as log, redirect_stdout(log)):
            code = transport.main(['seal'])
            typed.assert_not_called()
        return code

    def native07_archive(self):
        with tarfile.open(self.root / 'compatibility-matrix-primary.tar') as bundle:
            return {member.name: bundle.extractfile(member).read()
                    for member in bundle.getmembers()}

    def test_native07_operational_result_and_both_exact_readbacks(self):
        directory, original = self.native07_originals()
        (directory / 'private.FCStd').write_bytes(b'PRIVATE DOCUMENT')
        self.assertEqual(self.native07_seal(original), 0)
        self.assertEqual(transport.archive(), 'PASS')
        contents = self.native07_archive()
        summary = json.loads(contents['transport/manifest.json'])
        self.assertEqual(summary['stage'], transport.matrix.NATIVE07_STAGE)
        self.assertTrue(summary['original_diagnostic_preservation_complete'])
        self.assertFalse(summary['payload_sealed'])
        self.assertFalse(summary['matrix_execution'])
        self.assertFalse(summary['runtime_admission'])
        self.assertFalse(summary['zy_execution'])
        self.assertFalse(any('native07-invocation-claim' in name
                             for name in contents))
        self.assertNotIn(b'PRIVATE DOCUMENT', b''.join(contents.values()))
        self.readback('primary')
        self.assertEqual(transport.publish()['status'], 'PASS')
        self.readback('final')
        self.assertEqual(transport.complete(), 'PASS')

    def test_native07_failure_original_survives_without_completion(self):
        directory, original = self.native07_originals()
        stdout = directory / 'guard/stdout'
        stdout.write_text(stdout.read_text().splitlines()[0] + '\n')
        diagnostic = (b'TRACKTEMPLATE_NATIVE07_B15_LOAD_EXCEPTION='
                      b'{"cause_type":"ValueError","reason":"console-argument"}\n')
        (directory / 'guard/stderr').write_bytes(diagnostic)
        self.assertEqual(self.native07_seal(original), 1)
        self.assertEqual(transport.archive(), 'FAIL')
        contents = self.native07_archive()
        summary = json.loads(contents['transport/manifest.json'])
        self.assertEqual(summary['status'], 'FAIL')
        self.assertEqual(contents[
            'operational/entries/native-07/guard/stderr'], diagnostic)
        self.assertIn('original-diagnostics/seal.txt', contents)

    def test_native07_incomplete_early_session_keeps_available_originals(self):
        directory, _ = self.native07_originals()
        finalization = self.root / 'compatibility-matrix-finalization.json'
        summary = json.loads(finalization.read_text())
        summary['workflow_outcomes']['L1_RUN'] = 'failure'
        save(finalization, summary)
        (directory / 'guard/ownership.json').unlink()
        stderr = b'ValueError: setup stopped before ownership\n'
        (directory / 'guard/stderr').write_bytes(stderr)

        self.assertEqual(transport.archive(), 'FAIL')
        contents = self.native07_archive()
        manifest = json.loads(contents['transport/manifest.json'])
        prefix = 'operational/entries/native-07/guard/'
        self.assertIn(prefix + 'ownership.json',
                      manifest['missing_mandatory_evidence'])
        self.assertFalse(manifest['original_diagnostic_preservation_complete'])
        self.assertEqual(contents[prefix + 'stderr'], stderr)

    def test_native07_missing_original_and_other_session_refuse_pass(self):
        directory, original = self.native07_originals()
        self.assertEqual(self.native07_seal(original), 0)
        (directory / 'guard/stderr').unlink()
        other = directory.parent / 'native-08/guard'
        other.mkdir(parents=True)
        (other / 'stderr').write_text('OUTSIDE APPROVED SESSION\n')
        self.assertEqual(transport.archive(), 'FAIL')
        contents = self.native07_archive()
        summary = json.loads(contents['transport/manifest.json'])
        self.assertEqual(summary['missing_mandatory_evidence'], [
            'operational/entries/native-07/guard/stderr',
        ])
        self.assertFalse(summary['scope_isolated'])
        self.assertNotIn(b'OUTSIDE APPROVED SESSION',
                         b''.join(contents.values()))

    def test_native07_private_original_has_no_public_archive(self):
        directory, original = self.native07_originals()
        self.assertEqual(self.native07_seal(original), 0)
        private = b'ValueError: /home/private-operator/document.FCStd\n'
        (directory / 'guard/stderr').write_bytes(private)
        with self.assertRaisesRegex(ValueError, 'Private path'):
            transport.archive()
        self.assertEqual((directory / 'guard/stderr').read_bytes(), private)
        self.assertFalse((self.root / 'compatibility-matrix-primary.tar').exists())

    def test_seed_preserves_all_four_exact_json_strings(self):
        transport.seed()
        for name, raw in self.raw.items():
            self.assertEqual((self.controls / (name + '.json')).read_bytes(),
                             raw.encode())
        self.assertEqual((self.controls / 'control.json').read_text(),
                         self.inputs['readiness_control'])
        self.assertEqual(transport.seeded(), self.controls)
        self.assertFalse(self.install_work.exists())
        self.assertFalse(self.work.exists())
        self.clock_mock.assert_called_once()

    def refused_seed(self):
        logs = self.root / 'compatibility-matrix-logs'
        logs.mkdir(mode=0o700)
        log_path = logs / 'seed.log'
        with (log_path.open('x') as log, redirect_stdout(log),
              redirect_stderr(log)):
            self.assertEqual(transport.main(['seed']), 1)
        self.outcomes(('skipped',) * len(transport.OUTCOMES))
        self.assertTrue(transport.finalize()['cleanup'])
        self.assertFalse(self.install_work.exists())
        self.assertFalse(self.work.exists())
        return log_path

    def test_seed_refusal_survives_both_artifact_readbacks(self):
        self.clock_mock.side_effect = ValueError('Public server clock absent')
        expected = self.refused_seed().read_bytes()
        self.assertEqual(expected, (
            b'COMPATIBILITY_MATRIX_SEED_REFUSAL=clock-server-date\n'
            b'COMPATIBILITY_MATRIX_TRANSPORT_FAIL=seed\n'))
        self.assertFalse((self.controls / 'seed.json').exists())
        self.assertEqual(transport.main(['archive']), 0)
        self.readback('primary')
        self.assertEqual(transport.main(['publish']), 0)
        self.readback('final')

        for kind in ('primary', 'final'):
            path = self.root / ('compatibility-matrix-' + kind + '.tar')
            with tarfile.open(path) as archive:
                self.assertEqual(archive.extractfile('logs/seed.log').read(),
                                 expected)
                self.assertNotIn('original-diagnostics/seed.txt',
                                 archive.getnames())
                self.assertNotIn('prerequisites/control.json',
                                 archive.getnames())
        manifest = json.loads(self.native07_archive()['transport/manifest.json'])
        self.assertEqual(manifest['status'], 'FAIL')
        self.assertFalse(manifest['original_diagnostic_preservation_complete'])
        self.assertFalse(manifest['runtime_admission'])
        self.assertFalse(manifest['zy_execution'])
        captured = StringIO()
        with redirect_stdout(captured):
            self.assertEqual(transport.main(['complete']), 1)
        self.assertEqual(captured.getvalue().splitlines(), [
            'COMPATIBILITY_MATRIX_SEED_REFUSAL=clock-server-date',
            'COMPATIBILITY_MATRIX_TRANSPORT_FAIL',
        ])
        completion = json.loads((self.root /
            'compatibility-matrix-completion.json').read_bytes())
        self.assertEqual(completion['status'], 'FAIL')
        self.assertEqual(completion['primary_readback']['asset_id'], 42)
        self.assertEqual(completion['final_readback']['asset_id'], 42)

    def test_seed_unexpected_private_exception_is_withheld_from_public_output(self):
        private = 'fake secret and /home/private-operator/document.FCStd'
        self.clock_mock.side_effect = RuntimeError(private)
        expected = self.refused_seed().read_bytes()
        self.assertIn(b'SEED_REFUSAL=unexpected-error\n', expected)
        self.assertNotIn(private.encode(), expected)
        raw = (self.root / 'compatibility-matrix-private/seed.txt').read_bytes()
        self.assertIn(private.encode(), raw)
        self.assertEqual(transport.archive(), 'FAIL')
        self.assertNotIn(private.encode(),
                         b''.join(self.native07_archive().values()))

        # Report the capture before requiring the final artifact readback.
        captured = StringIO()
        with redirect_stdout(captured):
            self.assertEqual(transport.main(['complete']), 1)
        self.assertEqual(captured.getvalue().splitlines(), [
            'COMPATIBILITY_MATRIX_SEED_REFUSAL=unexpected-error',
            'COMPATIBILITY_MATRIX_TRANSPORT_FAIL=complete',
        ])
        self.assertNotIn(private, captured.getvalue())

    def test_seed_refusal_overrules_partial_receipt_with_retention_failure(self):
        original = transport.write

        def write(path, value):
            if path.name != 'seed.json':
                return original(path, value)
            path.write_bytes(b'{')
            raise OSError('injected interrupted seed receipt')

        with (patch.object(transport, 'write', side_effect=write),
              patch.object(transport, 'retain_failure',
                           side_effect=OSError('private retention failure'))):
            expected = self.refused_seed().read_bytes()
        self.assertEqual(expected, (
            b'COMPATIBILITY_MATRIX_SEED_REFUSAL=io-error\n'
            b'COMPATIBILITY_MATRIX_SEED_PRIVATE_RETENTION_FAIL\n'
            b'COMPATIBILITY_MATRIX_TRANSPORT_FAIL=seed\n'))
        self.assertEqual((self.controls / 'seed.json').read_bytes(), b'{')

        self.assertEqual(transport.archive(), 'FAIL')
        self.assertEqual(self.native07_archive()['logs/seed.log'], expected)
        self.readback('primary')
        self.assertEqual(transport.publish()['status'], 'PASS')
        with tarfile.open(self.root / 'compatibility-matrix-final.tar') as archive:
            self.assertEqual(archive.extractfile('logs/seed.log').read(), expected)
            self.assertNotIn('prerequisites/seed.json', archive.getnames())

    def test_seed_log_rejects_mixed_unknown_oversized_and_linked_bytes(self):
        logs = self.root / 'compatibility-matrix-logs'
        logs.mkdir(mode=0o700)
        log = logs / 'seed.log'
        suffix = b'\nCOMPATIBILITY_MATRIX_TRANSPORT_FAIL=seed\n'
        prefix = b'COMPATIBILITY_MATRIX_SEED_REFUSAL='
        valid = prefix + b'clock-server-date' + suffix
        for raw in (b'traceback\n' + valid, valid + b'private text\n',
                    prefix + b'unlisted-reason' + suffix,
                    b'x' * 400, valid + b'\xff'):
            with self.subTest(raw=raw[:48]):
                log.write_bytes(raw)
                self.assertIsNone(transport._safe_seed_failure_log(self.root))
        original = logs / 'seed-elsewhere.log'
        original.write_bytes(valid)
        log.unlink()
        log.symlink_to(original)
        self.assertIsNone(transport._safe_seed_failure_log(self.root))

        self.outcomes(('skipped',) * len(transport.OUTCOMES))
        self.assertTrue(transport.finalize()['cleanup'])
        self.assertEqual(transport.archive(), 'FAIL')
        self.assertNotIn('logs/seed.log', self.native07_archive())
        self.readback('primary')
        self.assertEqual(transport.publish()['status'], 'PASS')
        with tarfile.open(self.root / 'compatibility-matrix-final.tar') as archive:
            self.assertNotIn('logs/seed.log', archive.getnames())

    def test_seed_code_remains_visible_when_complete_refuses_scratch(self):
        logs = self.root / 'compatibility-matrix-logs'
        logs.mkdir(mode=0o700)
        with patch.dict(os.environ, {'GITHUB_RUN_ID': ''}):
            with ((logs / 'seed.log').open('x') as log,
                  redirect_stdout(log), redirect_stderr(log)):
                self.assertEqual(transport.main(['seed']), 1)
            captured = StringIO()
            with redirect_stdout(captured), redirect_stderr(captured):
                self.assertEqual(transport.main(['complete']), 1)
        self.assertEqual(captured.getvalue().splitlines(), [
            'COMPATIBILITY_MATRIX_SEED_REFUSAL=run-identity',
            'COMPATIBILITY_MATRIX_TRANSPORT_PRIVATE_RETENTION_FAIL=complete',
            'COMPATIBILITY_MATRIX_TRANSPORT_FAIL=complete',
        ])
        self.assertFalse(self.controls.exists())
        self.assertFalse(self.install_work.exists())

    def test_complete_denied_scratch_with_no_readable_seed_log(self):
        for read_error in (None, PermissionError('private test path')):
            with self.subTest(read_error=read_error):
                captured = StringIO()
                with (patch.dict(os.environ, {'GITHUB_RUN_ID': ''}),
                      patch.object(transport, 'regular',
                                   wraps=transport.regular,
                                   side_effect=read_error),
                      redirect_stdout(captured), redirect_stderr(captured)):
                    self.assertEqual(transport.main(['complete']), 1)
                self.assertEqual(captured.getvalue().splitlines(), [
                    'COMPATIBILITY_MATRIX_TRANSPORT_PRIVATE_RETENTION_FAIL=complete',
                    'COMPATIBILITY_MATRIX_TRANSPORT_FAIL=complete',
                ])
        self.assertFalse(self.controls.exists())
        self.assertFalse(self.install_work.exists())

    def test_seed_clock_http_reason_is_finite(self):
        for status, reason in ((403, 'clock-http-403'), (429, 'clock-http-429'),
                               (404, 'clock-http-other')):
            with self.subTest(status=status):
                error = HTTPError('https://example.invalid/', status,
                                  'untrusted message', {}, None)
                self.assertEqual(transport._seed_failure_reason(error), reason)

    def test_outer_clock_uses_actual_job_start_and_conservative_latency(self):
        job = {'id': 456, 'run_id': 123, 'head_sha': self.commit,
               'name': transport.JOB_NAME, 'status': 'in_progress',
               'started_at': timestamp(1700000000)}
        clocks = {'seed_monotonic': 1000.0, 'request_monotonic': 1001.0,
                  'received_monotonic': 1003.0, 'request_utc': 1700000060.0,
                  'received_utc': 1700000062.0}
        value = transport.clock_projection(job, http_date(1700000062), clocks)
        self.assertEqual(value['outer_deadline_monotonic'],
                         1003 + 8400 - 62 - 2 - 2)
        self.assertEqual(value['outer_seconds'], 8400)
        self.assertEqual(value['heavy_seconds'], 7200)
        self.assertEqual(value['pre_heavy_seconds'], 90)
        self.assertEqual(value['tail_seconds'], 600)
        for field, bad in (('run_id', 124), ('id', True),
                           ('head_sha', '0' * 40), ('status', 'completed'),
                           ('started_at', timestamp(1700000063))):
            with self.subTest(field=field), self.assertRaises(ValueError):
                transport.clock_projection(dict(job, **{field: bad}),
                                           http_date(1700000062), clocks)

    def test_clock_disagreement_nonfinite_and_elapsed_bounds_refused(self):
        job = {'id': 456, 'run_id': 123, 'head_sha': self.commit,
               'name': transport.JOB_NAME, 'status': 'in_progress',
               'started_at': timestamp(1700000000)}
        clocks = {'seed_monotonic': 1000.0, 'request_monotonic': 1001.0,
                  'received_monotonic': 1003.0, 'request_utc': 1700000060.0,
                  'received_utc': 1700000062.0}
        for field, bad in (('received_utc', 1700000077.0),
                           ('received_utc', 1700000064.0),
                           ('received_monotonic', 999.0),
                           ('received_monotonic', 1012.0),
                           ('seed_monotonic', 940.0),
                           ('request_utc', float('nan')),
                           ('request_monotonic', True)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                transport.clock_projection(job, http_date(1700000062),
                                           dict(clocks, **{field: bad}))

    def test_clock_request_is_fixed_unauthenticated_and_body_stays_private(self):
        self.controls.mkdir(mode=0o700)
        job = {'id': 456, 'run_id': 123, 'head_sha': self.commit,
               'name': transport.JOB_NAME, 'status': 'in_progress',
               'started_at': timestamp(1700000000),
               'steps': [{'unreviewed_field': 'excluded API body'}]}
        raw = json.dumps({'total_count': 1, 'jobs': [job]}).encode()
        url = ('https://api.github.com/repos/Richard-Gnitnub/tracktemplate/'
               'actions/runs/123/attempts/1/jobs?per_page=100')
        response = SimpleNamespace(status=200, geturl=lambda: url,
            headers={'Date': http_date(1700000062)}, read=Mock(return_value=raw))
        opener = Mock()
        opener.open.return_value.__enter__ = Mock(return_value=response)
        opener.open.return_value.__exit__ = Mock(return_value=False)
        with (patch.object(transport.urllib.request, 'build_opener',
                           return_value=opener) as build,
              patch.object(transport.time, 'monotonic', side_effect=[1001.0, 1003.0]),
              patch.object(transport.time, 'time', side_effect=[1700000060.0, 1700000062.0]),
              patch.dict(os.environ, {'GITHUB_TOKEN': 'PRIVATE_TOKEN'})):
            value = JOB_CLOCK(self.controls, 1000.0)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, url)
        self.assertNotIn('Authorization', request.headers)
        self.assertNotIn('PRIVATE_TOKEN', repr(request.headers))
        self.assertEqual(opener.open.call_args.kwargs, {'timeout': 10})
        response.read.assert_called_once_with(transport.MAX_CLOCK_RESPONSE + 1)
        self.assertEqual((self.controls / 'job-clock-response.json').read_bytes(), raw)
        self.assertNotIn('excluded API body', json.dumps(value))
        proxy, redirect = build.call_args.args
        self.assertEqual(proxy.proxies, {})
        with self.assertRaisesRegex(ValueError, 'redirect refused'):
            redirect.redirect_request(None, None, 302, None, None,
                                      'https://different.example/')

    def test_clock_rejects_cached_redirected_and_incomplete_job_responses(self):
        job = {'id': 456, 'run_id': 123, 'head_sha': self.commit,
               'name': transport.JOB_NAME, 'status': 'in_progress',
               'started_at': timestamp(1700000000)}
        url = ('https://api.github.com/repos/Richard-Gnitnub/tracktemplate/'
               'actions/runs/123/attempts/1/jobs?per_page=100')
        valid = json.dumps({'total_count': 1, 'jobs': [job]}).encode()
        cases = (
            (valid, {'Age': '1'}, url, 200, False),
            (valid, {}, 'https://different.example/', 200, False),
            (valid, {}, url, 503, False),
            (json.dumps({'total_count': 2, 'jobs': [job]}).encode(),
             {}, url, 200, True),
            (json.dumps({'total_count': 2, 'jobs': [job, job]}).encode(),
             {}, url, 200, True),
            (b'{' + b' ' * transport.MAX_CLOCK_RESPONSE,
             {}, url, 200, True),
        )
        for number, (raw, headers, final_url, status, retained) in enumerate(cases):
            with self.subTest(case=number):
                controls = self.root / ('clock-' + str(number))
                controls.mkdir(mode=0o700)
                response = SimpleNamespace(status=status,
                    geturl=lambda: final_url,
                    headers=dict(headers, Date=http_date(1700000062)),
                    read=Mock(return_value=raw))
                opener = Mock()
                opener.open.return_value.__enter__ = Mock(return_value=response)
                opener.open.return_value.__exit__ = Mock(return_value=False)
                with (patch.object(transport.urllib.request, 'build_opener',
                                   return_value=opener),
                      patch.object(transport.time, 'monotonic',
                                   side_effect=[1001.0, 1003.0]),
                      patch.object(transport.time, 'time',
                                   side_effect=[1700000060.0, 1700000062.0])):
                    with self.assertRaises(ValueError):
                        JOB_CLOCK(controls, 1000.0)
                original = controls / 'job-clock-response.json'
                self.assertEqual(original.exists(), retained)
                if retained:
                    self.assertEqual(original.read_bytes(), raw)

    def test_seed_budget_edit_cannot_reset_deadline(self):
        transport.seed()
        path = self.controls / 'outer-budget.json'
        value = json.loads(path.read_text())
        value['outer_deadline_monotonic'] += 8400
        save(path, value)
        with self.assertRaisesRegex(ValueError, 'Seeded prerequisite changed'):
            transport.seeded()
        self.clock_mock.assert_called_once()

    def test_run_refuses_before_controller_when_full_interval_cannot_fit(self):
        transport.seed()
        budget = transport.outer_budget(self.controls)
        now = budget['outer_deadline_monotonic'] - 7890 + 1
        with (patch.object(transport, 'prerequisites', return_value=self.controls),
              patch.object(transport, 'prepared_manifest', return_value=({}, {})),
              patch.object(transport.time, 'monotonic', return_value=now),
              patch.object(transport.matrix, 'run_matrix') as run):
            with self.assertRaisesRegex(ValueError, 'Full heavy interval and tail'):
                transport.run()
            run.assert_not_called()
        record = json.loads((self.controls / 'run-reservation.json').read_text())
        self.assertEqual(record['status'], 'REFUSED')
        self.assertEqual(record['required_seconds'], 7890)
        self.assertFalse((self.work / 'evidence').exists())

    def test_run_reserves_full_interval_and_never_renews_start(self):
        transport.seed()
        budget = transport.outer_budget(self.controls)
        now = budget['outer_deadline_monotonic'] - 7890
        with (patch.object(transport, 'prerequisites', return_value=self.controls),
              patch.object(transport, 'prepared_manifest', return_value=({}, {})),
              patch.object(transport.time, 'monotonic', return_value=now),
              patch.object(transport.matrix, 'run_matrix',
                           return_value={'status': 'PASS'}) as run):
            self.assertEqual(transport.run(), 'PASS')
            self.assertEqual(run.call_args.kwargs,
                             {'heavy_start_deadline': now + 90})
            with self.assertRaises(FileExistsError):
                transport.run()
            run.assert_called_once()

    def test_unknown_envelope_and_non_string_receipt_refused_before_seed(self):
        for value in ({'review': self.raw['review'],
                       'readiness': self.raw['readiness'], 'extra': 'PRIVATE'},
                      {'review': self.receipts['review'],
                       'readiness': self.raw['readiness']}):
            self.inputs['readiness_review'] = json.dumps(value)
            self.save_event()
            with self.subTest(value=value), self.assertRaises(ValueError):
                transport.seed()
            self.assertFalse(self.controls.exists())

    def test_duplicate_json_is_refused_before_seed(self):
        self.inputs['readiness_review'] = '{"review":"{}","review":"{}"}'
        self.save_event()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            transport.seed()
        self.assertFalse(self.controls.exists())

    def test_changed_readiness_source_prevents_installation(self):
        name = next(iter(self.receipts['readiness']['source_files']))
        self.receipts['readiness']['source_files'][name] = '0' * 64
        self.raw['readiness'] = json.dumps(self.receipts['readiness'])
        self.bind_inputs()
        with self.assertRaisesRegex(ValueError, 'Readiness source differs'):
            transport.seed()
        self.assertFalse((self.controls / 'seed.json').exists())
        self.assertFalse(self.install_work.exists())

    def test_edited_seeded_receipt_and_repeated_seed_refused(self):
        transport.seed()
        with self.assertRaises(FileExistsError):
            transport.seed()
        path = self.controls / 'readiness.json'
        path.write_text(path.read_text() + '\n')
        with self.assertRaisesRegex(ValueError, 'Seeded prerequisite changed'):
            transport.seeded()

    def test_prepare_only_creates_installer_workspace(self):
        self.prepare()
        self.assertTrue((self.install_work / 'evidence').is_dir())
        self.assertFalse(self.work.exists())
        self.assertEqual(self.install_work.stat().st_mode & 0o777, 0o700)

    def test_dirty_checkout_refused_before_preparation(self):
        transport.seed()
        with patch.object(transport.matrix.pilot, '_command',
                          side_effect=[self.commit, ' M guarded.py']):
            with self.assertRaisesRegex(ValueError, 'Reviewed checkout differs'):
                transport.prepare()
        self.assertFalse(self.install_work.exists())

    def test_fixed_session_inventory_has_84_unique_instances(self):
        names = transport.session_paths()
        self.assertEqual(len(names), 84)
        self.assertEqual(len(set(names)), 84)
        self.assertIn(Path('entries/phase3-four-routes/'
                           'phase3-four-routes-route-4'), names)
        self.assertIn(Path('entries/phase7-export-pair/'
                           'phase7-export-pair-route-2'), names)

    def test_runtime_skipped_rejects_existing_execution_state(self):
        target = self.root / 'finalizer'
        target.mkdir()
        outcome = dict.fromkeys(transport.OUTCOMES, 'skipped')
        result = transport._runtime_cleanup(self.work, target, outcome)
        self.assertTrue(result['cleanup'])
        (self.work / 'entries').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'Skipped runtime'):
            transport._runtime_cleanup(self.work, target, outcome)

    def test_finalizer_attempts_all_boundaries_and_keeps_original(self):
        self.outcomes(('failure', 'skipped', 'skipped', 'skipped'))
        with patch.object(transport.transport, 'installer_cleanup',
                          side_effect=ValueError('original installer failure')):
            with patch.object(transport, '_runtime_cleanup',
                              return_value={'cleanup': True}) as runtime:
                with patch.object(transport.readiness.gui, 'display_cleanup',
                                  return_value={'cleanup': True}) as display:
                    result = transport.finalize()
        self.assertFalse(result['cleanup'])
        runtime.assert_called_once()
        display.assert_called_once()
        raw = (self.root / 'compatibility-matrix-private/'
               'finalize-installer.txt').read_text()
        self.assertIn('ValueError: original installer failure', raw)

    def test_finalizer_checks_each_existing_guard_and_uses_owned_emergency(self):
        relative = Path('entries/native-01')
        directory = self.work / relative / 'guard'
        directory.mkdir(mode=0o700, parents=True)
        self.work.chmod(0o700)
        # The unchanged guard uses mkdir's default mode. Privacy belongs
        # to the already-private matrix/session ancestors, not this mode.
        directory.chmod(0o755)
        save(directory / 'ownership.json', {'scope': 'owned-test-scope'})
        target = self.root / 'finalizer'
        target.mkdir()
        with patch.object(transport.native, 'emergency_cleanup',
                          return_value={'proved': True}) as cleanup:
            result = transport._runtime_cleanup(self.work, target,
                dict.fromkeys(transport.OUTCOMES, 'success'))
        self.assertTrue(result['cleanup'])
        self.assertEqual(result['sessions'], {relative.as_posix(): True})
        self.assertEqual(cleanup.call_args.args,
                         (target / relative, {'scope': 'owned-test-scope'}))

    def test_archive_preserves_original_known_failure_and_excludes_documents(self):
        self.prepare()
        self.finalized(False)
        original = b'Traceback (most recent call last):\nValueError: exact failure\n'
        private = self.root / 'compatibility-matrix-private'
        private.mkdir(mode=0o700)
        (private / 'acquire.txt').write_bytes(original)
        self.work.mkdir(mode=0o700)
        (self.work / 'private.FCStd').write_bytes(b'PRIVATE DOCUMENT')
        self.assertEqual(transport.archive(), 'FAIL')
        with tarfile.open(self.root / 'compatibility-matrix-primary.tar') as archive:
            self.assertEqual(archive.extractfile(
                'original-diagnostics/acquire.txt').read(), original)
            self.assertNotIn('private.FCStd', archive.getnames())

    def test_phase5_rpc_requires_exact_sealed_original_before_archive(self):
        self.prepare()
        self.finalized(False)
        relative = 'entries/phase5-view-edit-lifecycle/client.stderr'
        stderr = self.work / relative
        remote = 'Synthetic original RPC diagnostic\n'
        save(stderr, {'status': 'error', 'error': remote, 'code': 'rpc_fault'})
        original = stderr.read_bytes()
        with self.assertRaisesRegex(ValueError, 'matching sealed failure'):
            transport.archive()
        self.assertFalse((self.root / 'compatibility-matrix-primary.tar').exists())
        self.assertEqual(stderr.read_bytes(), original)

        member = 'gui/phase5-view-edit-lifecycle/failure.txt'
        sealed = self.work / 'public-matrix' / member
        sealed.parent.mkdir(parents=True)
        sealed.write_bytes(b'Changed evidence\n')
        with self.assertRaisesRegex(ValueError, 'matching sealed failure'):
            transport.archive()
        self.assertFalse((self.root / 'compatibility-matrix-primary.tar').exists())
        self.assertEqual(stderr.read_bytes(), original)

        sealed.write_bytes(remote.encode())
        with patch.object(transport, '_payload', return_value=(
            {'payload/' + member: sealed.read_bytes()}, {'status': 'FAIL'}
        )):
            self.assertEqual(transport.archive(), 'FAIL')
        with tarfile.open(self.root / 'compatibility-matrix-primary.tar') as archive:
            self.assertEqual(archive.extractfile('operational/' + relative).read(),
                             original)
            self.assertEqual(archive.extractfile('payload/' + member).read(),
                             remote.encode())

    def test_unlisted_guard_diagnostic_refuses_public_archive(self):
        self.prepare()
        self.finalized(False)
        guard = self.work / 'entries/native-01/guard'
        guard.mkdir(parents=True)
        (guard / 'unreviewed.txt').write_text('unknown original')
        with self.assertRaisesRegex(ValueError, 'Unlisted operational'):
            transport.archive()
        self.assertFalse((self.root / 'compatibility-matrix-primary.tar').exists())
        self.assertEqual((guard / 'unreviewed.txt').read_text(), 'unknown original')

    def test_private_original_diagnostic_refuses_without_redaction(self):
        self.prepare()
        self.finalized(False)
        private = self.root / 'compatibility-matrix-private'
        private.mkdir(mode=0o700)
        original = b'ValueError: /home/private-operator/document.FCStd\n'
        (private / 'acquire.txt').write_bytes(original)
        with self.assertRaisesRegex(ValueError, 'Private path'):
            transport.archive()
        self.assertEqual((private / 'acquire.txt').read_bytes(), original)
        self.assertFalse((self.root / 'compatibility-matrix-primary.tar').exists())

    def test_two_exact_artifact_readbacks_required_for_completion(self):
        self.prepare()
        self.finalized(False)
        transport.archive()
        self.readback('primary')
        result = transport.publish()
        self.assertEqual(result['status'], 'PASS')
        self.readback('final')
        self.assertEqual(transport.complete(), 'FAIL')
        result = json.loads((self.root /
            'compatibility-matrix-completion.json').read_text())
        self.assertFalse(result['runtime_admission'])
        self.assertFalse(result['zy_execution'])
        self.assertEqual(result['primary_readback']['asset_id'], 42)

    def test_changed_primary_readback_keeps_failure_and_original_archive(self):
        self.prepare()
        self.finalized(False)
        transport.archive()
        self.readback('primary')
        original = (self.root / 'compatibility-matrix-primary.tar').read_bytes()
        (self.root / 'compatibility-matrix-primary-readback/'
         'compatibility-matrix-primary.tar').write_bytes(b'corrupt readback')
        diagnostic = 'ValueError: Artifact readback differs\n'
        with patch.object(transport.traceback, 'format_exc',
                          return_value=diagnostic):
            result = transport.publish()
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(result['error'], 'primary-readback-unproved')
        self.assertEqual((self.root / 'compatibility-matrix-primary.tar').read_bytes(),
                         original)
        self.assertEqual((self.root /
            'compatibility-matrix-private/publish-primary.txt').read_bytes(),
            diagnostic.encode())
        with tarfile.open(self.root / 'compatibility-matrix-final.tar') as archive:
            self.assertEqual(archive.extractfile(
                'original-diagnostics/publish-primary.txt').read(),
                diagnostic.encode())

    def test_private_readback_failure_refuses_without_redaction(self):
        self.prepare()
        self.finalized(False)
        transport.archive()
        self.readback('primary')
        original = (self.root / 'compatibility-matrix-primary.tar').read_bytes()
        (self.root / 'compatibility-matrix-primary-readback/'
         'compatibility-matrix-primary.tar').write_bytes(b'corrupt readback')
        diagnostic = 'ValueError: /home/private-operator/document.FCStd\n'
        with patch.object(transport.traceback, 'format_exc',
                          return_value=diagnostic):
            with self.assertRaisesRegex(ValueError, 'Private path'):
                transport.publish()
        self.assertEqual((self.root / 'compatibility-matrix-primary.tar').read_bytes(),
                         original)
        self.assertEqual((self.root /
            'compatibility-matrix-private/publish-primary.txt').read_bytes(),
            diagnostic.encode())
        self.assertFalse((self.root / 'compatibility-matrix-final.tar').exists())

    def test_raw_matrix_streams_are_original_bytes_in_fixed_instances(self):
        self.prepare()
        self.finalized(False)
        guard = self.work / 'entries/native-01/guard'
        guard.mkdir(parents=True)
        raw = b'fixed source-safe diagnostic\nAssertionError: original failure\n'
        (guard / 'stderr').write_bytes(raw)
        transport.archive()
        with tarfile.open(self.root / 'compatibility-matrix-primary.tar') as archive:
            self.assertEqual(archive.extractfile(
                'operational/entries/native-01/guard/stderr').read(), raw)

    def test_cli_preserves_original_failure_before_fixed_marker(self):
        with patch.object(transport, 'acquire',
                          side_effect=ValueError('original exact failure')):
            self.assertEqual(transport.main(['acquire']), 1)
        path = self.root / 'compatibility-matrix-private/acquire.txt'
        self.assertIn('ValueError: original exact failure', path.read_text())

    def test_complete_cannot_accept_missing_final_readback(self):
        with self.assertRaises(ValueError):
            transport.complete()
        self.assertFalse((self.root / 'compatibility-matrix-completion.json').exists())


class ComposedPayloadTests(unittest.TestCase):
    def test_real_typed_extractor_is_repeated_and_payload_checked(self):
        spec = importlib.util.spec_from_file_location('matrix_observation_fixture',
            ROOT / 'tests/validate_runtime_compatibility_observations.py')
        fixture_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture_module)
        fixture_type = fixture_module.ObservationTests
        fixture_type.setUpClass()
        fixture = fixture_type()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.full_matrix_fixture()
        fixture.work.chmod(0o700)
        with patch.object(transport.matrix, 'verify_source_members'):
            with patch.object(transport.observations, '_base_object_count', return_value=9):
                destination = fixture.work / 'public-matrix'
                result = transport.observations.extract_matrix_payload(
                    ROOT, fixture.work, fixture.manifest, destination,
                    runtime_observation=fixture.work /
                        'entries/straight-generation/runtime-observation.json')
                save(fixture.work / 'matrix-payload-inventory.json', result)
                with patch.object(transport, 'prepared_manifest',
                                  return_value=(fixture.manifest, {})):
                    contents, repeated = transport._payload(fixture.work)
        self.assertEqual(repeated, result)
        self.assertEqual(len([name for name in contents if name.endswith('.png')]), 159)
        self.assertEqual(len([name for name in contents if name.endswith('result.json')]), 23)
        self.assertEqual(result['native_entries_verified'], 57)


if __name__ == '__main__':
    unittest.main()
