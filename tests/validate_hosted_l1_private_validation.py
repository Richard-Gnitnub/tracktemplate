"""Offline checks for private hosted L1 coordination; never start FreeCAD."""

import copy
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import hosted_l1_private_validation as pilot  # noqa: E402
from tools import hosted_native_geometry_pilot as original  # noqa: E402


class L1PrivateControls(unittest.TestCase):
    def test_child_environment_drops_credentials_and_unlisted_values(self):
        values = {"PATH": "/usr/bin", "HOME": "/home/runner",
                  "GITHUB_RUN_ID": "42", "GITHUB_ACTIONS": "true",
                  "L1_PRIVATE_INPUT_READ_TOKEN": "do-not-copy",
                  "L1_PRIVATE_INPUT_PASSPHRASE": "do-not-copy",
                  "GITHUB_TOKEN": "do-not-copy", "GH_TOKEN": "do-not-copy",
                  "PYTHONPATH": "/untrusted", "LD_PRELOAD": "/untrusted"}
        result = pilot.child_environment(values, Path('/private/config'), 'a' * 64)
        self.assertEqual(result['TRACKTEMPLATE_L1_RUN_CONFIG_SHA256'], 'a' * 64)
        self.assertEqual(result['GITHUB_RUN_ID'], '42')
        self.assertFalse(any('TOKEN' in key or 'PASSPHRASE' in key
                             for key in result))
        self.assertNotIn('PYTHONPATH', result)
        self.assertNotIn('LD_PRELOAD', result)

    def test_stage_is_fixed_and_limits_remain_bounded(self):
        self.assertEqual(pilot.limits('readiness').timeout_seconds, 90)
        self.assertEqual(pilot.limits('native').timeout_seconds, 7200)
        self.assertEqual(pilot.limits('native').memory_max_mib, 4096)
        self.assertEqual(pilot.limits('native').cpu_percent, 100)
        self.assertEqual(pilot.limits('native').tasks_max, 128)
        for invalid in ('all', 'gui', 'native; echo wrong', ''):
            with self.assertRaises(ValueError):
                pilot.limits(invalid)

    def test_finalization_reserve_does_not_raise_limits(self):
        environment = {'L1_JOB_START_SECONDS': '100'}
        pilot.require_finalization_time('native', environment, 1000)
        with self.assertRaises(ValueError):
            pilot.require_finalization_time('native', environment, 1001)

    def test_private_token_is_not_forwarded_to_asset_storage(self):
        data = b'encrypted-dummy'
        record = {'asset_id': 123, 'bytes': len(data),
                  'sha256': hashlib.sha256(data).hexdigest()}
        redirect = pilot.urllib.error.HTTPError(
            'https://api.github.com/', 302, 'redirect',
            {'Location': 'https://release-assets.githubusercontent.com/private?signature=private'},
            None,
        )
        opener = Mock()
        opener.open.side_effect = [redirect, io.BytesIO(data)]
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(pilot.urllib.request, 'build_opener', return_value=opener):
                pilot.download_asset(record, 'private-token', Path(temporary) / 'cipher')
        first, second = [call.args[0] for call in opener.open.call_args_list]
        self.assertEqual(first.get_header('Authorization'), 'Bearer private-token')
        self.assertIsNone(second.get_header('Authorization'))

    def test_entire_manifest_destination_map_is_checked_before_writes(self):
        rows = [{'id': str(index), 'path': '/approved/' + str(index),
                 'sha256': 'a' * 64, 'bytes': 3} for index in range(10)]
        pilot.validate_input_map({'inputs': rows}, {'inputs': copy.deepcopy(rows)})
        altered = copy.deepcopy(rows)
        altered[-1]['path'] = '/elsewhere/same-bytes'
        with patch.object(Path, 'open', side_effect=AssertionError('write')):
            with self.assertRaises(ValueError):
                pilot.validate_input_map({'inputs': altered}, {'inputs': rows})

    def test_emergency_cleanup_requires_owned_identity_and_readback(self):
        from types import SimpleNamespace
        scope = 'app-flatpak-org.freecad.FreeCAD-123.scope'
        invocation = '1' * 32
        relative = f'/user.slice/user-{os.getuid()}.slice/user@{os.getuid()}.service/app.slice/{scope}'
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence').mkdir()
            group = work / 'cgroups' / relative.lstrip('/')
            group.mkdir(parents=True)
            (group / 'cgroup.events').write_text('populated 0')
            (group / 'cgroup.procs').write_text('')
            (group / 'pids.current').write_text('0')
            owner = {'scope': scope, 'invocation': invocation, 'cgroup': relative}
            for identity, clear, expected in ((invocation, True, True),
                                             ('2' * 32, True, False),
                                             (invocation, False, False)):
                calls = []
                def command(arguments, **kwargs):
                    calls.append(arguments)
                    value = identity if 'InvocationID' in arguments else ''
                    return SimpleNamespace(returncode=0, stdout=value, stderr='')
                context = pilot.guard.GuardContext(run=command, cgroup_root=work / 'cgroups')
                with patch.object(original, '_clearance', return_value=clear):
                    result = pilot.emergency_cleanup(work, owner, context=context)
                self.assertEqual(result['proved'], expected)
                if identity != invocation:
                    self.assertFalse(any('kill' in call for call in calls))

    def test_private_phase_refuses_debug_retry_or_nonmain(self):
        good = {'GITHUB_REF': 'refs/heads/main', 'GITHUB_RUN_ATTEMPT': '1',
                'GITHUB_RUN_ID': '42', 'GITHUB_ACTIONS': 'true',
                'GITHUB_REPOSITORY': 'Richard-Gnitnub/tracktemplate',
                'GITHUB_EVENT_NAME': 'workflow_dispatch',
                'RUNNER_ENVIRONMENT': 'github-hosted',
                'RUNNER_OS': 'Linux', 'RUNNER_ARCH': 'X64'}
        memory = ('MemTotal: 16777216 kB\nMemAvailable: 12582912 kB\n'
                  'SwapTotal: 0 kB\nSwapFree: 0 kB\n')
        pilot.validate_host(good, memory)
        for key, value in (('RUNNER_DEBUG', '1'), ('ACTIONS_STEP_DEBUG', 'true'),
                           ('GITHUB_REF', 'refs/tags/main'),
                           ('GITHUB_RUN_ATTEMPT', '2')):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    pilot.validate_host(dict(good, **{key: value}), memory)

    def test_native_requires_independent_readiness_bound_to_candidate(self):
        controls = {name: 'c' * 64 for name in pilot.CONTROL_FILES}
        good = {'status': 'PASS', 'independent_review': 'PASS',
                'source_commit': pilot.CANDIDATE,
                'entry_sha256': pilot.ENTRY_SHA256, 'scope_id': pilot.SCOPE,
                'workflow_commit': 'd' * 40,
                'control_files_sha256': controls,
                'handling_decision': 'accepted-handling',
                'run_id': 41, 'run_attempt': 1,
                'input_hashes': {'input': 'a' * 64},
                'evidence_sha256': 'b' * 64,
                'evidence_verified': True, 'independent_preservation': True,
                'tests': 1, 'skips': 0, 'sentinel': True, 'cleanup': True}
        config = {'handling_decision': 'accepted-handling',
                  'inputs': [{'id': 'input', 'sha256': 'a' * 64}]}
        control = {'workflow_commit': 'd' * 40,
                   'control_files_sha256': controls}
        pilot.validate_readiness(good, config, '42', control)
        for field, value in (('status', 'FAIL'), ('independent_review', 'PENDING'),
                             ('run_id', 42), ('tests', 0), ('skips', 1),
                             ('cleanup', False), ('input_hashes', {}),
                             ('source_commit', '0' * 40),
                             ('workflow_commit', 'e' * 40),
                             ('control_files_sha256', {}),
                             ('control_files_sha256',
                              dict(controls, **{pilot.CONTROL_FILES[0]: 'f' * 64}))):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    pilot.validate_readiness(dict(good, **{field: value}),
                                             config, '42', control)
        with self.assertRaises(ValueError):
            pilot.validate_readiness(good, config, '42',
                                     dict(control, control_files_sha256={}))

    def test_private_metadata_requires_exact_http_success_status(self):
        for method, status, accepted in (
            ('GET', 200, True), ('POST', 201, True),
            ('GET', 201, False), ('POST', 200, False),
            ('POST', 202, False),
        ):
            with self.subTest(method=method, status=status):
                response = io.BytesIO(b'{"id": 1}')
                response.status = status
                opener = Mock()
                opener.open.return_value = response
                with patch.object(pilot.urllib.request, 'build_opener',
                                  return_value=opener):
                    if accepted:
                        self.assertEqual(pilot.api_request(
                            method, 'https://api.github.com/private',
                            'dummy-token'), {'id': 1})
                    else:
                        with self.assertRaises(ValueError):
                            pilot.api_request(
                                method, 'https://api.github.com/private',
                                'dummy-token')

    def test_runtime_adapter_uses_exact_foundation_report(self):
        record = {'status': 'modular-foundation-ready',
                  'matched_profile_id': original.EXPECTED_PROFILE,
                  'document_mutation': False, 'workflow_launched': False}
        text = 'TRACKTEMPLATE_B16_FOUNDATION=' + json.dumps(record)
        pilot.qualified_runtime(text)
        for output in ('', text + '\n' + text,
                       text.replace('modular-foundation-ready', 'blocked')):
            with self.assertRaises(ValueError):
                pilot.qualified_runtime(output)

    def test_native_receipt_requires_all_comparisons_and_cleanup(self):
        receipt = {'status': 'PASS', 'stage': 'native',
                   'profile': original.EXPECTED_PROFILE,
                   'input_bindings_unchanged': True,
                   'owned_documents_closed': True, 'cleanup_errors': [],
                   'sentinel': pilot.SENTINELS['native'],
                   'source_frame_comparisons': 150, 'component_comparisons': 138,
                   'successful_preview_component_placements': 690,
                   'rolled_back_component_placements': 230,
                   'total_materialised_component_placements': 920}
        pilot.validate_native_receipt('native', receipt)
        for key, value in (('component_comparisons', 137),
                           ('source_frame_comparisons', 149),
                           ('rolled_back_component_placements', 0),
                           ('owned_documents_closed', False)):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    pilot.validate_native_receipt('native',
                                                  dict(receipt, **{key: value}))

    def test_existing_assessor_is_used_with_restored_bindings(self):
        before = original.LIMITS, original.GEOMETRY_SENTINEL, original._qualified_runtime
        with patch.object(original, 'assess_result', return_value={'status': 'FAIL'}) as run:
            self.assertEqual(pilot.assess('native', {}, '', '', [], False),
                             {'status': 'FAIL'})
            self.assertEqual(run.call_count, 1)
        self.assertEqual(before, (original.LIMITS, original.GEOMETRY_SENTINEL,
                                  original._qualified_runtime))

    def test_original_resource_assessment_keeps_failure_controls(self):
        fixture = runpy.run_path(str(ROOT / 'tests/validate_hosted_native_geometry.py'))
        result = fixture['good_guard']()
        result['limits'] = vars(pilot.limits('native'))
        foundation = {'status': 'modular-foundation-ready',
                      'matched_profile_id': original.EXPECTED_PROFILE,
                      'document_mutation': False, 'workflow_launched': False}
        stdout = ('TRACKTEMPLATE_B16_FOUNDATION=' + json.dumps(foundation)
                  + '\n' + pilot.SENTINELS['native'] + '\n')
        stderr = fixture['native_report']()
        samples = [fixture['live_sample']()]
        self.assertEqual(pilot.assess('native', result, stdout, stderr,
                                     samples, True)['status'], 'PASS')
        invalid = copy.deepcopy(samples)
        invalid[0]['memory.swap.current'] = '1'
        self.assertEqual(pilot.assess('native', result, stdout, stderr,
                                     invalid, True)['status'], 'FAIL')
        for bad_stdout, bad_stderr, cleanup in (
                ('', stderr, True), (stdout, stderr + '\nskipped=1', True),
                (stdout, stderr, False)):
            self.assertEqual(pilot.assess('native', result, bad_stdout,
                                         bad_stderr, samples, cleanup)['status'],
                             'FAIL')

    def test_private_upload_requires_exact_receipt_and_digest_readback(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            archive = work / 'dummy.tar'
            archive.write_bytes(b'dummy permitted evidence')
            record = {'id': 123, 'name': 'dummy.tar', 'state': 'uploaded',
                      'size': archive.stat().st_size}
            def readback(binding, token, destination, **kwargs):
                self.assertEqual(binding['asset_id'], 123)
                self.assertEqual(token, 'dummy-token')
                destination.write_bytes(archive.read_bytes())
            with (patch.object(pilot, 'api_request', return_value=record) as request,
                  patch.object(pilot, 'download_asset', side_effect=readback)):
                result = pilot.upload_private_asset(archive, 'dummy.tar', 429232376,
                                                    'dummy-token', work)
            self.assertEqual(result, {'asset_id': 123, 'bytes': archive.stat().st_size,
                                      'sha256': pilot.digest(archive)})
            self.assertIn('/releases/429232376/assets?name=dummy.tar', request.call_args.args[1])
            with (patch.object(pilot, 'api_request', return_value=dict(record, size=1)),
                  patch.object(pilot, 'download_asset') as download):
                with self.assertRaises(ValueError):
                    pilot.upload_private_asset(archive, 'dummy.tar', 429232376,
                                                'dummy-token', work)
                download.assert_not_called()

    def test_readable_archive_omits_exact_and_byte_identical_input_copies(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            evidence = work / 'evidence'
            (evidence / 'native/native').mkdir(parents=True)
            private = b'restricted-input'
            rows = [{'sha256': hashlib.sha256(private).hexdigest()}]
            (work / 'run-config.json').write_text(json.dumps({'inputs': rows}))
            (evidence / 'native/native/L1-copy.FCStd').write_bytes(b'changed copy')
            (evidence / 'native/native/XO-001-copy.FCStd').write_bytes(private)
            (evidence / 'renamed-input.bin').write_bytes(private)
            (evidence / 'result.json').write_text('permitted-result')
            pilot.evidence_archive(work, work / 'evidence.tar')
            with tarfile.open(work / 'evidence.tar') as archive:
                self.assertEqual(set(archive.getnames()),
                                 {'evidence/result.json', 'evidence-manifest.json'})
                manifest = json.load(archive.extractfile('evidence-manifest.json'))
                self.assertEqual(len(manifest['excluded_inputs']), 3)
                self.assertEqual(archive.extractfile('evidence/result.json').read(),
                                 b'permitted-result')

    def test_failure_publication_keeps_primary_and_finite_late_diagnostics(self):
        for failed_upload in (None, 1, 2):
            with self.subTest(failed_upload=failed_upload), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary) / 'private'
                (work / 'evidence').mkdir(parents=True, mode=0o700)
                (work / 'evidence/prepare.log').write_text('PRIVATE-TRACEBACK-MARKER')
                (work / 'evidence/publication.log').write_text('PRIVATE-LATE-MARKER')
                public = Path(temporary) / 'public'
                control = {'workflow_commit': 'a' * 40, 'scope_id': pilot.SCOPE,
                           'stage': 'readiness', 'independent_review': 'PASS',
                           'evidence_release_id': 429232376,
                           'control_files_sha256': {name: pilot.digest(ROOT / name)
                                                    for name in pilot.CONTROL_FILES}}
                environment = {'GITHUB_SHA': 'a' * 40, 'GITHUB_RUN_ID': '42',
                               'L1_PRIVATE_CONTROL': json.dumps(control),
                               'L1_PRIVATE_EVIDENCE_WRITE_TOKEN': 'dummy-write-secret'}
                calls = []

                def upload(path, name, release, token, root):
                    calls.append(name)
                    self.assertEqual(release, 429232376)
                    self.assertEqual(token, 'dummy-write-secret')
                    if len(calls) == failed_upload:
                        raise ValueError('PRIVATE-PUBLICATION-FAILURE')
                    return {'sha256': pilot.digest(path), 'bytes': path.stat().st_size,
                            'asset_id': 120 + len(calls)}

                metadata = [{'private': True, 'full_name': pilot.INPUT_REPOSITORY},
                            {'id': 429232376, 'assets': []}]
                with (patch.dict(os.environ, environment),
                      patch.object(original, '_clearance', return_value=True),
                      patch.object(pilot, 'api_request', side_effect=metadata),
                      patch.object(pilot, 'upload_private_asset', side_effect=upload)):
                    pilot.finalize('readiness', work, public)
                    status = pilot.publish('readiness', work, public)
                self.assertEqual(status, 0 if failed_upload is None else 1)
                self.assertEqual(len(calls), 2)  # One primary and one supplement, no retry.
                summary = json.loads((public / 'summary.json').read_text())
                self.assertEqual(summary['outcome'], 'INCOMPLETE')
                self.assertEqual(summary['evidence']['asset_id'],
                                 0 if failed_upload == 1 else 121)
                self.assertNotIn('PRIVATE-', json.dumps(summary))
                self.assertNotIn('dummy-write-secret', json.dumps(summary))
                with tarfile.open(work / 'evidence.tar') as archive:
                    self.assertEqual(archive.extractfile('evidence/prepare.log').read(),
                                     b'PRIVATE-TRACEBACK-MARKER')
                with tarfile.open(work / 'publication.tar') as archive:
                    self.assertEqual(archive.extractfile('evidence/publication.log').read(),
                                     b'PRIVATE-LATE-MARKER')
                    receipt = json.load(archive.extractfile('evidence/publication.json'))
                    self.assertEqual(bool(receipt['errors']), failed_upload == 1)
                self.assertNotIn('L1_PRIVATE_EVIDENCE_WRITE_TOKEN', os.environ)

    def test_emergency_cleanup_refuses_missing_or_live_process_telemetry(self):
        from types import SimpleNamespace
        scope = 'app-flatpak-org.freecad.FreeCAD-123.scope'
        invocation = '1' * 32
        relative = f'/user.slice/user-{os.getuid()}.slice/user@{os.getuid()}.service/app.slice/{scope}'
        for missing in (False, True):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                (work / 'evidence').mkdir()
                group = work / relative.lstrip('/')
                group.mkdir(parents=True)
                (group / 'cgroup.events').write_text('populated 1')
                (group / 'cgroup.procs').write_text('123')
                if not missing:
                    (group / 'pids.current').write_text('1')
                def command(arguments, **kwargs):
                    return SimpleNamespace(returncode=0, stdout=invocation, stderr='')
                clock = iter((0, 11))
                context = pilot.guard.GuardContext(run=command, cgroup_root=work,
                                                  monotonic=lambda: next(clock),
                                                  sleep=lambda seconds: None)
                with patch.object(original, '_clearance') as flatpak:
                    result = pilot.emergency_cleanup(work,
                        {'scope': scope, 'invocation': invocation, 'cgroup': relative}, context)
                self.assertFalse(result['proved'])
                flatpak.assert_not_called()

    def test_emergency_deadline_is_owned_and_verified_after_stop(self):
        from types import SimpleNamespace
        scope = 'app-flatpak-org.freecad.FreeCAD-123.scope'
        invocation = '1' * 32
        relative = f'/user.slice/user-{os.getuid()}.slice/user@{os.getuid()}.service/app.slice/{scope}'
        unit = 'tracktemplate-validation-' + '3' * 32
        argv = f'/usr/bin/python3 {ROOT}/tools/freecad_validation_guard.py watchdog {scope} {invocation}'
        for deadline_clear in (True, False):
            with self.subTest(clear=deadline_clear), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                (work / 'evidence').mkdir()
                commands = []
                def command(arguments, **kwargs):
                    commands.append(arguments)
                    value = ''
                    if 'InvocationID' in arguments:
                        value = invocation
                    elif 'list-units' in arguments:
                        value = unit + '.timer loaded active waiting'
                    elif 'ExecStart' in arguments:
                        value = '{ path=/usr/bin/python3 ; argv[]=' + argv + ' ; ignore_errors=no ; }'
                    return SimpleNamespace(returncode=0, stdout=value, stderr='')
                context = pilot.guard.GuardContext(run=command, cgroup_root=work)
                with (patch.object(original, '_clearance', return_value=True),
                      patch.object(original, '_deadline_clearance', return_value=deadline_clear) as readback):
                    result = pilot.emergency_cleanup(work,
                        {'scope': scope, 'invocation': invocation, 'cgroup': relative}, context)
                self.assertEqual(result['proved'], deadline_clear)
                readback.assert_called_once_with({'cleanup_proved': True, 'watchdog': unit})
                self.assertIn(['systemctl', '--user', 'stop', unit + '.timer', unit + '.service'], commands)

    def test_finalizer_preserves_staging_until_primary_readback(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence').mkdir()
            staged = work / 'deployed-input'
            staged.write_bytes(b'restricted source')
            (work / 'evidence/deployed-01.json').write_text(json.dumps({
                'path': str(staged), 'sha256': pilot.digest(staged)}))
            with patch.object(original, '_clearance', return_value=True):
                pilot.finalize('readiness', work, work / 'public')
            self.assertTrue(staged.exists())
            self.assertTrue((work / 'evidence/process-finalization.json').exists())

    def test_staging_cleanup_needs_preservation_and_removes_only_exact_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence/native/native').mkdir(parents=True)
            (work / 'unpacked/inputs').mkdir(parents=True)
            (work / 'unpacked/control').mkdir()
            control = work / 'unpacked/control/run-config.json'
            control.write_text('preserved control evidence')
            (work / 'evidence/process-finalization.json').write_text(json.dumps({
                'cleanup': True, 'errors': [], 'seconds': 0}))
            expected = [work / 'inputs.tar']
            expected.extend(work / 'unpacked/inputs' / name for name in pilot.payload.INPUT_IDS)
            expected.extend(work / 'evidence/native/native' / name
                            for name in ('L1-copy.FCStd', 'XO-001-copy.FCStd'))
            for path in expected:
                path.write_bytes(b'restricted staging')
            for index in range(1, 11):
                staged = work / f'deployed-{index}'
                staged.write_bytes(b'restricted input')
                expected.append(staged)
                (work / f'evidence/deployed-{index:02d}.json').write_text(json.dumps({
                    'path': str(staged), 'sha256': pilot.digest(staged)}))
            archive = work / 'evidence.tar'
            archive.write_bytes(b'permitted evidence')
            preserved = {'sha256': pilot.digest(archive), 'bytes': archive.stat().st_size,
                         'asset_id': 123}
            with patch.object(pilot, 'DEPLOYMENT_ROOT', work):
                with self.assertRaises(ValueError):
                    pilot.cleanup_staging(work, dict(preserved, asset_id=0))
                self.assertTrue(all(path.exists() for path in expected))
                result = pilot.cleanup_staging(work, preserved)
            self.assertTrue(result['cleanup'])
            self.assertEqual(len(result['staging_inputs_removed']), 10)
            self.assertEqual(len(result['staging_files_removed']), 23)
            self.assertTrue(all(not path.exists() for path in expected))
            self.assertTrue(control.exists())
            self.assertEqual(len(result['staging_absence_verified']), 23)

    def test_staging_cleanup_follows_primary_readback_and_precedes_supplement(self):
        for primary_fails in (False, True):
            with self.subTest(primary_fails=primary_fails), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                (work / 'evidence').mkdir()
                staged = work / 'staged-input'
                staged.write_bytes(b'restricted input')
                (work / 'evidence/deployed-01.json').write_text(json.dumps({
                    'path': str(staged), 'sha256': pilot.digest(staged)}))
                (work / 'evidence/publication.log').write_text('private publication diagnostics')
                control = {'workflow_commit': 'a' * 40, 'scope_id': pilot.SCOPE,
                           'stage': 'readiness', 'independent_review': 'PASS',
                           'evidence_release_id': 429232376,
                           'control_files_sha256': {name: pilot.digest(ROOT / name)
                                                    for name in pilot.CONTROL_FILES}}
                environment = {'GITHUB_SHA': 'a' * 40, 'GITHUB_RUN_ID': '42',
                               'L1_PRIVATE_CONTROL': json.dumps(control),
                               'L1_PRIVATE_EVIDENCE_WRITE_TOKEN': 'dummy-token'}
                calls = []
                def upload(path, name, release, token, root):
                    calls.append(name)
                    if len(calls) == 1:
                        self.assertTrue(staged.exists())
                        self.assertFalse((work / 'evidence/finalization.json').exists())
                        if primary_fails:
                            raise ValueError('Primary readback failed')
                    else:
                        self.assertEqual(staged.exists(), primary_fails)
                        with tarfile.open(path) as archive:
                            self.assertEqual('evidence/finalization.json' in archive.getnames(),
                                             not primary_fails)
                    return {'asset_id': 100 + len(calls), 'sha256': pilot.digest(path),
                            'bytes': path.stat().st_size}
                metadata = [{'private': True, 'full_name': pilot.INPUT_REPOSITORY},
                            {'id': 429232376, 'assets': []}]
                with (patch.dict(os.environ, environment),
                      patch.object(pilot, 'DEPLOYMENT_ROOT', work),
                      patch.object(original, '_clearance', return_value=True),
                      patch.object(pilot, 'api_request', side_effect=metadata),
                      patch.object(pilot, 'upload_private_asset', side_effect=upload)):
                    pilot.finalize('readiness', work, work / 'public')
                    result = pilot.publish('readiness', work, work / 'public')
                self.assertEqual(result, 1 if primary_fails else 0)
                self.assertEqual(len(calls), 2)

    def test_staging_cleanup_refuses_changed_input_or_link(self):
        for linked in (False, True):
            with self.subTest(linked=linked), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                (work / 'evidence').mkdir()
                (work / 'evidence/process-finalization.json').write_text(json.dumps({
                    'cleanup': True, 'errors': [], 'seconds': 0}))
                original_input = work / 'original-input'
                original_input.write_bytes(b'restricted input')
                staged = work / 'staged-input'
                if linked:
                    staged.symlink_to(original_input)
                else:
                    staged.write_bytes(b'changed bytes')
                (work / 'evidence/deployed-01.json').write_text(json.dumps({
                    'path': str(staged), 'sha256': pilot.digest(original_input)}))
                archive = work / 'evidence.tar'
                archive.write_bytes(b'permitted evidence')
                preserved = {'sha256': pilot.digest(archive), 'bytes': archive.stat().st_size,
                             'asset_id': 123}
                with patch.object(pilot, 'DEPLOYMENT_ROOT', work):
                    result = pilot.cleanup_staging(work, preserved)
                self.assertFalse(result['cleanup'])
                self.assertTrue(result['errors'])
                reason = 'Linked staging cleanup refused' if linked else 'Staged input changed'
                self.assertIn(reason, '\n'.join(result['errors']))
                self.assertTrue(staged.exists())
                self.assertTrue(original_input.exists())

    def test_staging_cleanup_production_root_refuses_outside_file(self):
        self.assertEqual(pilot.DEPLOYMENT_ROOT, Path('/home/richard'))
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self.assertFalse(work.is_relative_to(pilot.DEPLOYMENT_ROOT))
            (work / 'evidence').mkdir()
            (work / 'evidence/process-finalization.json').write_text(json.dumps({
                'cleanup': True, 'errors': [], 'seconds': 0}))
            staged = work / 'outside-input'
            staged.write_bytes(b'restricted input')
            (work / 'evidence/deployed-01.json').write_text(json.dumps({
                'path': str(staged), 'sha256': pilot.digest(staged)}))
            archive = work / 'evidence.tar'
            archive.write_bytes(b'permitted evidence')
            preserved = {'sha256': pilot.digest(archive), 'bytes': archive.stat().st_size,
                         'asset_id': 123}
            result = pilot.cleanup_staging(work, preserved)
            self.assertFalse(result['cleanup'])
            self.assertIn('Staged destination refused', '\n'.join(result['errors']))
            self.assertTrue(staged.exists())

    def test_workflow_has_no_private_raw_upload_or_local_fallback(self):
        text = (ROOT / '.github/workflows/l1-private-validation.yml').read_text()
        self.assertIn('workflow_dispatch:', text)
        self.assertNotIn('pull_request:', text)
        self.assertNotIn('pull_request_target:', text)
        self.assertIn('environment: l1-private-validation', text)
        self.assertIn('group: issue230-native-geometry', text)
        self.assertIn('timeout-minutes: 140', text)
        self.assertIn('retention-days: 30', text)
        self.assertIn('persist-credentials: false', text)
        upload = text.split('uses: actions/upload-artifact@', 1)[1]
        self.assertNotIn('*.gpg', upload)
        self.assertNotIn('guard/stdout', upload)
        self.assertNotIn('tee ', text)
        self.assertEqual(text.count('${{ secrets.L1_PRIVATE_INPUT_READ_TOKEN }}'), 1)
        self.assertEqual(text.count('${{ secrets.L1_PRIVATE_INPUT_PASSPHRASE }}'), 1)
        self.assertEqual(text.count('${{ secrets.L1_PRIVATE_EVIDENCE_WRITE_TOKEN }}'), 1)
        self.assertNotIn('L1_EVIDENCE_PUBLIC_KEY', text)
        self.assertNotIn("if: always() && steps.prepare.outcome", text)
        self.assertEqual(text.count('uses: actions/upload-artifact@'), 1)
        self.assertIn('summary.json', upload)


if __name__ == '__main__':
    unittest.main()
