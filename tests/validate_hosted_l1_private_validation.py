"""Offline checks for private hosted L1 coordination; never start FreeCAD."""

import copy
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import socket
import ssl
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
        pilot.require_finalization_time('native', environment, 700)
        with self.assertRaises(ValueError):
            pilot.require_finalization_time('native', environment, 701)

    def test_public_input_download_is_anonymous_and_hash_bound(self):
        data = b'approved-tar-bytes'
        record = {'asset_id': 123, 'bytes': len(data),
                  'sha256': hashlib.sha256(data).hexdigest()}
        redirect = pilot.urllib.error.HTTPError(
            'https://api.github.com/', 302, 'redirect',
            {'Location': 'https://release-assets.githubusercontent.com/approved'}, None)
        opener = Mock()
        opener.open.side_effect = [redirect, io.BytesIO(data)]
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'inputs.tar'
            with patch.object(pilot.urllib.request, 'build_opener', return_value=opener):
                pilot.download_asset(record, target)
            self.assertEqual(target.read_bytes(), data)
        for call in opener.open.call_args_list:
            self.assertIsNone(call.args[0].get_header('Authorization'))
        opener.open.side_effect = [io.BytesIO(b'x' * len(data))]
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(pilot.urllib.request, 'build_opener', return_value=opener):
                with self.assertRaisesRegex(ValueError, 'Input archive changed'):
                    pilot.download_asset(record, Path(temporary) / 'bad.tar')

    def test_acquisition_uses_main_repository_and_refuses_previous_repository(self):
        repository = 'Richard-Gnitnub/tracktemplate'
        data = b'approved-tar-bytes'
        record = {'asset_id': 123, 'bytes': len(data),
                  'sha256': hashlib.sha256(data).hexdigest()}
        opener = Mock()
        opener.open.return_value = io.BytesIO(data)
        with self.subTest(boundary='download'), tempfile.TemporaryDirectory() as temporary:
            with patch.object(pilot.urllib.request, 'build_opener', return_value=opener):
                pilot.download_asset(record, Path(temporary) / 'inputs.tar')
            self.assertEqual(opener.open.call_args.args[0].full_url,
                             f'https://api.github.com/repos/{repository}/releases/assets/123')
        metadata = {'private': False, 'full_name': repository,
                    'owner': {'login': 'Richard-Gnitnub'}}
        with self.subTest(boundary='main metadata'):
            with patch.object(pilot, 'api_request', return_value=metadata) as request:
                pilot.validate_input_repository()
                request.assert_called_once_with(f'https://api.github.com/repos/{repository}')
        previous = dict(metadata, full_name='Richard-Gnitnub/tracktemplate-validation-private')
        with self.subTest(boundary='previous repository'):
            with patch.object(pilot, 'api_request', return_value=previous):
                with self.assertRaisesRegex(ValueError, 'Public input repository differs'):
                    pilot.validate_input_repository()

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

    def test_public_repository_requires_exact_owner_visibility_and_status(self):
        good = {'private': False, 'full_name': pilot.INPUT_REPOSITORY,
                'owner': {'login': 'Richard-Gnitnub'}}
        for field, value in (('private', True), ('full_name', 'other/repository'),
                             ('owner', {'login': 'other'})):
            with patch.object(pilot, 'api_request', return_value=dict(good, **{field: value})):
                with self.assertRaises(ValueError):
                    pilot.validate_input_repository()
        with patch.object(pilot, 'api_request', return_value=good):
            pilot.validate_input_repository()
        for status in (200, 201):
            response = io.BytesIO(b'{}')
            response.status = status
            opener = Mock()
            opener.open.return_value = response
            with patch.object(pilot.urllib.request, 'build_opener', return_value=opener):
                if status == 200:
                    self.assertEqual(pilot.api_request('https://api.github.com/repos/example'), {})
                else:
                    with self.assertRaises(ValueError):
                        pilot.api_request('https://api.github.com/repos/example')
            self.assertIsNone(opener.open.call_args.args[0].get_header('Authorization'))

    def test_metadata_http_failures_are_bounded_and_anonymous(self):
        cases = (
            (403, {'X-RateLimit-Remaining': '0'},
             {'X-RateLimit-Remaining': 0}),
            (403, {'X-RateLimit-Remaining': '59'},
             {'X-RateLimit-Remaining': 59}),
            (403, {}, {}),
            (429, {'Retry-After': '30'}, {'Retry-After': 30}),
            (503, {'X-RateLimit-Limit': '60',
                   'X-RateLimit-Reset': '1794539821'},
             {'X-RateLimit-Limit': 60, 'X-RateLimit-Reset': 1794539821}),
            (302, {}, {}),
            (403, {'X-RateLimit-Remaining': '9' * 21,
                   'X-RateLimit-Reset': '12\nSECRET',
                   'X-RateLimit-Limit': '-1', 'Retry-After': 'SECRET'}, {}),
        )
        for status, headers, expected_headers in cases:
            with self.subTest(status=status, headers=headers):
                body = Mock()
                headers = dict(
                    headers, Location='https://SECRET',
                    Authorization='SECRET', **{'Set-Cookie': 'SECRET'})
                error = pilot.urllib.error.HTTPError(
                    'https://api.github.com/SECRET', status, 'SECRET',
                    headers, body)
                opener = Mock()
                opener.open.side_effect = error
                with patch.object(pilot.urllib.request, 'build_opener',
                                  return_value=opener):
                    with self.assertRaises(ValueError) as caught:
                        pilot.api_request(
                            'https://api.github.com/repos/example')
                message = str(caught.exception)
                prefix = 'Public metadata request failed: '
                self.assertTrue(message.startswith(prefix), message)
                self.assertEqual(json.loads(message[len(prefix):]), {
                    'category': 'http', 'status': status,
                    'headers': expected_headers,
                })
                self.assertNotIn('SECRET', message)
                self.assertLess(len(message), 400)
                self.assertTrue(caught.exception.__suppress_context__)
                body.read.assert_not_called()
                opener.open.assert_called_once()
                self.assertIsNone(
                    opener.open.call_args.args[0].get_header('Authorization'))
                self.assertEqual(opener.open.call_args.kwargs, {'timeout': 30})

    def test_metadata_transport_failures_preserve_only_typed_cause(self):
        for reason, cause, wrapped in (
            (socket.gaierror(-2, 'SECRET'), 'dns', True),
            (ssl.SSLCertVerificationError('SECRET'), 'tls', True),
            (ssl.SSLError('SECRET'), 'tls', True),
            (TimeoutError('SECRET'), 'timeout', True),
            (TimeoutError('SECRET'), 'timeout', False),
            (ConnectionRefusedError('SECRET'), 'connection', True),
            (ConnectionResetError('SECRET'), 'connection', True),
            (OSError('SECRET'), 'unknown', True),
            ('https://SECRET?token=SECRET', 'unknown', True),
        ):
            with self.subTest(cause=cause, wrapped=wrapped):
                opener = Mock()
                opener.open.side_effect = (
                    pilot.urllib.error.URLError(reason) if wrapped else reason)
                with patch.object(pilot.urllib.request, 'build_opener',
                                  return_value=opener):
                    with self.assertRaises(ValueError) as caught:
                        pilot.api_request(
                            'https://api.github.com/repos/example')
                message = str(caught.exception)
                prefix = 'Public metadata request failed: '
                self.assertTrue(message.startswith(prefix), message)
                self.assertEqual(json.loads(message[len(prefix):]), {
                    'category': 'transport', 'cause': cause,
                })
                self.assertNotIn('SECRET', message)
                self.assertTrue(caught.exception.__suppress_context__)
                opener.open.assert_called_once()

    def test_metadata_payload_errors_keep_original_rejection(self):
        for content, message in ((b'x' * (1024 * 1024 + 1),
                                  'Oversized GitHub metadata'),
                                 (b'{', 'Expecting property name')):
            with self.subTest(message=message):
                response = io.BytesIO(content)
                response.status = 200
                opener = Mock()
                opener.open.return_value = response
                with patch.object(pilot.urllib.request, 'build_opener',
                                  return_value=opener):
                    with self.assertRaisesRegex(ValueError, message) as caught:
                        pilot.api_request(
                            'https://api.github.com/repos/example')
                self.assertNotIn('transport', str(caught.exception))
                opener.open.assert_called_once()

    def test_never_started_prepare_failure_does_not_require_flatpak(self):
        environment = {'L1_PREPARE': 'failure', 'L1_INSTALL': 'skipped',
                       'L1_ACQUIRE': 'skipped', 'L1_RUN': 'skipped'}
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            evidence = work / 'evidence'
            evidence.mkdir()
            (evidence / 'prepare.log').write_bytes(b'ORIGINAL-FAILURE')
            (evidence / 'admission.json').write_text('{}')
            (evidence / 'finalizer.log').write_text('')
            (work / 'control.json').write_text('{}')
            with (
                patch.dict(os.environ, environment, clear=True),
                patch.object(original, '_clearance',
                             side_effect=FileNotFoundError('flatpak')) as clear,
            ):
                result = pilot.finalize('readiness', work, work / 'public')
            self.assertEqual(result, 0)
            clear.assert_not_called()
            record = json.loads(
                (evidence / 'process-finalization.json').read_text())
            self.assertTrue(record['cleanup'])
            self.assertTrue(record['never_started'])
            self.assertEqual(record['errors'], [])
            self.assertEqual(record['workflow_outcomes'], environment)
            self.assertEqual((evidence / 'prepare.log').read_bytes(),
                             b'ORIGINAL-FAILURE')
            self.assertFalse((evidence / 'assessment.json').exists())

    def test_ambiguous_states_never_bypass_runtime_clearance(self):
        original_environment = {
            'L1_PREPARE': 'failure', 'L1_INSTALL': 'skipped',
            'L1_ACQUIRE': 'skipped', 'L1_RUN': 'skipped',
        }
        cases = [
            ('L1_PREPARE', 'success'), ('L1_PREPARE', 'cancelled'),
            ('L1_INSTALL', 'success'), ('L1_INSTALL', 'failure'),
            ('L1_INSTALL', 'cancelled'), ('L1_INSTALL', ''),
            ('L1_ACQUIRE', 'failure'), ('L1_RUN', 'failure'),
        ]
        cases.extend(('path', value) for value in (
            'installer.sh', 'evidence/install.log', 'evidence/guard',
            'evidence/guard/ownership.json', 'evidence/guard/result.json',
            'evidence/unexpected.json', 'linked-evidence',
        ))
        for kind, value in cases:
            with (self.subTest(kind=kind, value=value),
                  tempfile.TemporaryDirectory() as temporary):
                work = Path(temporary)
                evidence = work / 'evidence'
                if value == 'linked-evidence':
                    (work / 'outside').mkdir()
                    evidence.symlink_to(
                        work / 'outside', target_is_directory=True)
                else:
                    evidence.mkdir()
                environment = dict(original_environment)
                if kind != 'path':
                    environment[kind] = value
                elif value != 'linked-evidence':
                    path = work / value
                    if value.endswith('/guard'):
                        path.mkdir()
                    else:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text('{}')
                with (patch.dict(os.environ, environment, clear=True),
                      patch.object(original, '_clearance',
                                   side_effect=FileNotFoundError('flatpak')),
                      patch.object(original, '_deadline_clearance',
                                   return_value=False),
                      patch.object(pilot, 'emergency_cleanup',
                                   return_value={'proved': False})):
                    pilot.finalize('readiness', work, work / 'public')
                record = json.loads(
                    (evidence / 'process-finalization.json').read_text())
                self.assertFalse(record['cleanup'])
                self.assertNotEqual(record.get('never_started'), True)

    def test_native_install_deadline_does_not_exceed_approved_budget(self):
        text = (
            ROOT / '.github/workflows/l1-private-validation.yml').read_text()
        installation = text.split('id: install', 1)[1].split(
            '- name: Acquire only the approved public inputs', 1)[0]
        self.assertIn('timeout-minutes: 9\n', installation)
        self.assertNotIn('timeout-minutes: 10', installation)
        self.assertLessEqual(9 * 60, 570)

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

    def test_runtime_report_accepts_exact_unittest_progress_frames(self):
        record = {'status': 'modular-foundation-ready',
                  'matched_profile_id': original.EXPECTED_PROFILE,
                  'document_mutation': False, 'workflow_launched': False}
        report = 'TRACKTEMPLATE_B16_FOUNDATION=' + json.dumps(record)
        # Readiness prefix is captured verbatim from run41108114397 stdout.
        prefixes = (
            '',
            'test_readiness (hosted_l1_current_source_suite.L1CurrentSource.test_readiness) ... ',
            'test_canonical_600_900_600 (hosted_l1_current_source_suite.L1CurrentSource.test_canonical_600_900_600) ... ',
        )
        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                pilot.qualified_runtime(prefix + report + '\nok\n')

    def test_runtime_report_rejects_duplicate_or_unexpected_framing(self):
        record = {'status': 'modular-foundation-ready',
                  'matched_profile_id': original.EXPECTED_PROFILE,
                  'document_mutation': False, 'workflow_launched': False}
        report = 'TRACKTEMPLATE_B16_FOUNDATION=' + json.dumps(record)
        progress = 'test_readiness (hosted_l1_current_source_suite.L1CurrentSource.test_readiness) ... '
        native = 'test_canonical_600_900_600 (hosted_l1_current_source_suite.L1CurrentSource.test_canonical_600_900_600) ... '
        for output in ('', report + '\n' + report,
                       progress + report + '\n' + report,
                       report + '\n' + progress + report,
                       progress + report + '\n' + native + report,
                       'noise ' + report, ' ' + progress + report,
                       progress.replace(' ... ', ' ...  ') + report,
                       progress.replace('test_readiness', 'test_other') + report,
                       report + '\nnoise ' + report):
            with self.subTest(output=output):
                with self.assertRaises(ValueError):
                    pilot.qualified_runtime(output)

    def test_runtime_report_rejects_malformed_objects_and_unsafe_fields(self):
        record = {'status': 'modular-foundation-ready',
                  'matched_profile_id': original.EXPECTED_PROFILE,
                  'document_mutation': False, 'workflow_launched': False}
        payloads = ['{', '[]', 'null', 'true', '1', '"text"']
        payloads.extend(json.dumps(dict(record, **{key: value})) for key, value in (
            ('status', 'blocked'), ('matched_profile_id', 'unqualified'),
            ('document_mutation', True), ('workflow_launched', True),
            ('document_mutation', 0), ('workflow_launched', 0),
        ))
        for prefix in (
                '',
                'test_readiness (hosted_l1_current_source_suite.L1CurrentSource.test_readiness) ... ',
                'test_canonical_600_900_600 (hosted_l1_current_source_suite.L1CurrentSource.test_canonical_600_900_600) ... '):
            for payload in payloads:
                with self.subTest(prefix=prefix, payload=payload):
                    with self.assertRaises(ValueError):
                        pilot.qualified_runtime(prefix + 'TRACKTEMPLATE_B16_FOUNDATION=' + payload)

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

    def test_artifact_requires_upload_download_and_exact_readback(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            source, readback = work / 'source.tar', work / 'readback.tar'
            source.write_bytes(b'evidence')
            readback.write_bytes(source.read_bytes())
            good = ('success', 'success', '123')
            result = pilot.verify_artifact(source, readback, *good)
            self.assertEqual(result, {'sha256': pilot.digest(source), 'bytes': 8, 'asset_id': 123})
            for values in (('failure', 'success', '123'), ('success', 'failure', '123'),
                           ('success', 'success', '0'), ('success', 'success', '')):
                with self.assertRaises(ValueError):
                    pilot.verify_artifact(source, readback, *values)
            readback.write_bytes(b'changed!')
            with self.assertRaises(ValueError):
                pilot.verify_artifact(source, readback, *good)

    def test_complete_requires_publication_success_and_final_readback(self):
        for fault in ('none', 'publication', 'readback', 'cleanup'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                (work / 'evidence').mkdir()
                (work / 'readback-final').mkdir()
                (work / 'publication.tar').write_bytes(b'completed evidence')
                (work / 'readback-final/publication.tar').write_bytes(
                    b'changed' if fault == 'readback' else b'completed evidence')
                (work / 'evidence/publication.json').write_text(json.dumps({
                    'primary': {'asset_id': 123}, 'errors': []}))
                (work / 'evidence/finalization.json').write_text(json.dumps({
                    'cleanup': fault != 'cleanup', 'staging_inputs_removed': list(range(10))}))
                (work / 'evidence/assessment.json').write_text(json.dumps({
                    'status': 'PASS', 'completed_native_tests': 1,
                    'native_receipt': {'sentinel': pilot.SENTINELS['readiness'],
                                       'input_bindings_unchanged': True}}))
                environment = {'GITHUB_SHA': 'a' * 40, 'GITHUB_RUN_ID': '42',
                               'L1_FINAL_UPLOAD': 'success', 'L1_FINAL_DOWNLOAD': 'success',
                               'L1_FINAL_ID': '124',
                               'L1_PUBLICATION': 'failure' if fault == 'publication' else 'success'}
                with patch.dict(os.environ, environment):
                    pilot.complete('readiness', work, work / 'public')
                summary = json.loads((work / 'public/summary.json').read_text())
                self.assertEqual(summary['outcome'], 'PASS' if fault == 'none' else 'INCOMPLETE')

    def test_evidence_archive_cap_precedes_both_upload_paths(self):
        from types import SimpleNamespace
        limit = 512 * 1024**2
        real_stat = Path.stat
        for name in ('evidence.tar', 'publication.tar'):
            for size in (limit, limit + 1):
                with self.subTest(name=name, size=size), tempfile.TemporaryDirectory() as temporary:
                    work = Path(temporary)
                    (work / 'evidence').mkdir()
                    destination = work / name
                    partial = work / (name + '.partial')
                    def measured(path, *args, **kwargs):
                        if path == partial:
                            return SimpleNamespace(st_size=size)
                        return real_stat(path, *args, **kwargs)
                    with patch.object(Path, 'stat', measured):
                        if size > limit:
                            with self.assertRaisesRegex(ValueError, 'Evidence transport bound exceeded'):
                                pilot.evidence_archive(work, destination)
                        else:
                            pilot.evidence_archive(work, destination)
                    self.assertEqual(destination.exists(), size <= limit)
                    self.assertEqual(partial.exists(), size > limit)
                    if size <= limit:
                        before = destination.read_bytes()
                        with self.assertRaises((ValueError, FileExistsError)):
                            pilot.evidence_archive(work, destination)
                        self.assertEqual(destination.read_bytes(), before)

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

    def test_failure_publication_preserves_diagnostics_and_cannot_pass(self):
        for failed in ('none', 'primary', 'final'):
            with self.subTest(failed=failed), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                (work / 'evidence').mkdir()
                (work / 'evidence/prepare.log').write_text('TRACEBACK-MARKER')
                (work / 'evidence/publication.log').write_text('LATE-MARKER')
                for name in ('readback-primary', 'readback-final'):
                    (work / name).mkdir()
                env = {'GITHUB_SHA': 'a' * 40, 'GITHUB_RUN_ID': '42',
                       'L1_PRIMARY_UPLOAD': 'success', 'L1_PRIMARY_DOWNLOAD': 'success',
                       'L1_PRIMARY_ID': '121', 'L1_FINAL_UPLOAD': 'success',
                       'L1_FINAL_DOWNLOAD': 'success', 'L1_FINAL_ID': '122'}
                with patch.dict(os.environ, env), patch.object(original, '_clearance', return_value=True):
                    pilot.finalize('readiness', work, work / 'public')
                    pilot.seal(work)
                    (work / 'readback-primary/evidence.tar').write_bytes(
                        b'wrong' if failed == 'primary' else (work / 'evidence.tar').read_bytes())
                    self.assertEqual(pilot.publish('readiness', work, work / 'public'),
                                     1 if failed == 'primary' else 0)
                    (work / 'readback-final/publication.tar').write_bytes(
                        b'wrong' if failed == 'final' else (work / 'publication.tar').read_bytes())
                    pilot.complete('readiness', work, work / 'public')
                summary = json.loads((work / 'public/summary.json').read_text())
                self.assertEqual(summary['outcome'], 'INCOMPLETE')
                self.assertNotIn('MARKER', json.dumps(summary))
                with tarfile.open(work / 'publication.tar') as archive:
                    self.assertEqual(archive.extractfile('evidence/prepare.log').read(), b'TRACEBACK-MARKER')
                    self.assertEqual(archive.extractfile('evidence/publication.log').read(), b'LATE-MARKER')
                    receipt = json.load(archive.extractfile('evidence/publication.json'))
                    self.assertEqual(bool(receipt['errors']), failed == 'primary')

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
                (work / 'readback-primary').mkdir()
                staged = work / 'staged-input'
                staged.write_bytes(b'restricted input')
                (work / 'evidence/deployed-01.json').write_text(json.dumps({
                    'path': str(staged), 'sha256': pilot.digest(staged)}))
                (work / 'evidence/publication.log').write_text('publication diagnostics')
                env = {'GITHUB_SHA': 'a' * 40, 'GITHUB_RUN_ID': '42',
                       'L1_PRIMARY_UPLOAD': 'success', 'L1_PRIMARY_DOWNLOAD': 'success',
                       'L1_PRIMARY_ID': '123'}
                with (patch.dict(os.environ, env), patch.object(pilot, 'DEPLOYMENT_ROOT', work),
                      patch.object(original, '_clearance', return_value=True)):
                    pilot.finalize('readiness', work, work / 'public')
                    pilot.seal(work)
                    self.assertTrue(staged.exists())
                    self.assertFalse((work / 'evidence/finalization.json').exists())
                    (work / 'readback-primary/evidence.tar').write_bytes(
                        b'wrong' if primary_fails else (work / 'evidence.tar').read_bytes())
                    result = pilot.publish('readiness', work, work / 'public')
                self.assertEqual(result, 1 if primary_fails else 0)
                self.assertEqual(staged.exists(), primary_fails)
                with tarfile.open(work / 'publication.tar') as archive:
                    self.assertEqual('evidence/finalization.json' in archive.getnames(), not primary_fails)

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
        self.assertNotIn('secrets.', text)
        self.assertNotIn('github-token:', text)
        self.assertIn('${{ vars.L1_PRIVATE_CONTROL }}', text)
        self.assertNotIn("if: always() && steps.prepare.outcome", text)
        self.assertEqual(text.count('uses: actions/upload-artifact@'), 3)
        self.assertEqual(text.count('uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093'), 2)
        self.assertIn('artifact-ids: ${{ steps.primary_artifact.outputs.artifact-id }}', text)
        self.assertIn('artifact-ids: ${{ steps.final_artifact.outputs.artifact-id }}', text)
        self.assertIn('summary.json', upload)




class ToSingleControls(unittest.TestCase):
    def config(self):
        return {
            "schema_version": 1,
            "scope_id": pilot.TO_SCOPE,
            "source_commit": "a" * 40,
            "entry_sha256": pilot.TO_ENTRY_SHA256,
            "handling_decision": "approved-exact-inputs",
            "inputs": [
                {
                    "id": name,
                    "path": "/home/richard/" + name,
                    "sha256": value,
                    "bytes": pilot.TO_INPUT_BYTES[name],
                }
                for name, value in pilot.TO_INPUT_HASHES.items()
            ],
        }

    def control(self):
        config = self.config()
        return {
            key: config[key]
            for key in (
                "scope_id",
                "source_commit",
                "entry_sha256",
                "handling_decision",
            )
        } | {
            "input_hashes": dict(pilot.TO_INPUT_HASHES),
            "input_archive": {
                "asset_id": 42,
                "bytes": 10240,
                "sha256": "c" * 64,
            },
            "publication_review": {
                "status": "PASS",
                "independent_review": "PASS",
                "input_hashes": dict(pilot.TO_INPUT_HASHES),
                "handling_decision": config["handling_decision"],
                "evidence_sha256": "b" * 64,
                "publication_basis": "Exact reviewed fixture basis",
            },
        }

    def receipt(self, stage):
        result = {
            "status": "PASS",
            "stage": stage,
            "scope_id": pilot.TO_SCOPE,
            "test_id": pilot.TO_SELECTORS[stage],
            "source_commit": "a" * 40,
            "fixture_sha256": pilot.TO_FIXTURE_SHA256,
            "physical_fit": "NOT_PROVED",
            "checks": pilot.to_expected_checks(stage),
            "input_sha256": dict(pilot.TO_INPUT_HASHES),
            "stage_timings": dict.fromkeys(
                ("readiness_seconds", "cleanup_seconds", "total_seconds")
                + (("native_seconds",) if stage == "native" else ()),
                1.0,
            ),
            "input_bindings_unchanged": True,
            "remaining_documents": 0,
            "owned_documents_closed": True,
            "sentinel": pilot.TO_SENTINELS[stage],
        }
        if stage == "native":
            fixture = json.loads(
                (
                    ROOT / "tests/fixtures/phase9b-to-single-rail-frames.json"
                ).read_text()
            )
            records = []
            for family, bodies, fixings in (("L1", 7, 16), ("S1", 5, 12)):
                names = [f"Part_{i:02d}" for i in range(bodies)]
                names += ["SourceFixing"] + [
                    f"SourceFixing{i:03d}" for i in range(1, fixings)
                ]
                for name in names:
                    for row in fixture["positions"]:
                        if row["family"] == family:
                            records.append(
                                dict(
                                    position_id=row["position_id"],
                                    component=name,
                                    counts=[1, 1, 6, 6, 12, 8],
                                    vertex_residual_mm=0.0,
                                )
                            )
            result.update(
                component_comparisons=records,
                preview_disposal_preserves_source_and_foreign=True,
            )
        return result

    def test_profile_pins_equal_frozen_entry_and_ten_distinct_inputs(self):
        entry = runpy.run_path(
            str(ROOT / "tests/freecad_validate_to_single_rail.py")
        )
        self.assertEqual(pilot.TO_INPUT_HASHES, entry["INPUT_HASHES"])
        self.assertEqual(
            pilot.TO_ENTRY_SHA256, pilot.digest(ROOT / pilot.TO_ENTRY)
        )
        self.assertEqual(sum(pilot.TO_INPUT_BYTES.values()), 2425834)
        self.assertEqual(
            set(pilot.payload.input_ids("to-single")),
            set(pilot.TO_INPUT_HASHES),
        )
        self.assertNotIn("reference_document", pilot.TO_INPUT_HASHES)
        self.assertNotIn("expected_frames", pilot.TO_INPUT_HASHES)
        for stage in ("readiness", "native"):
            self.assertEqual(
                pilot.to_expected_checks(stage),
                entry["expected_checks"](stage),
            )

    def test_native_comparison_evidence_requires_all270_exact_identities(self):
        good = self.receipt("native")
        pilot.validate_to_receipt("native", good, self.config())
        for edit in (
            lambda r: r.pop("component_comparisons"),
            lambda r: r["component_comparisons"].pop(),
            lambda r: r["component_comparisons"].__setitem__(
                -1, r["component_comparisons"][0]
            ),
            lambda r: r["component_comparisons"][0].update(
                component="foreign"
            ),
            lambda r: r["component_comparisons"][0].update(
                vertex_residual_mm=1e-6
            ),
            lambda r: r["component_comparisons"][0].update(counts=[True] * 6),
            lambda r: r.update(
                preview_disposal_preserves_source_and_foreign=False
            ),
        ):
            bad = copy.deepcopy(good)
            edit(bad)
            with self.assertRaises(ValueError):
                pilot.validate_to_receipt("native", bad, self.config())

    def test_to_environment_passes_identity_without_credentials(self):
        env = {
            "GITHUB_SHA": "a" * 40,
            "GITHUB_RUN_ATTEMPT": "1",
            "RUNNER_ENVIRONMENT": "github-hosted",
            "GITHUB_ACTIONS": "true",
            "GITHUB_RUN_ID": "42",
            "GITHUB_TOKEN": "secret",
            "PYTHONPATH": "untrusted",
        }
        result = pilot.child_environment(
            env, Path("/tmp/config"), "b" * 64, workload="to-single"
        )
        for key in ("GITHUB_SHA", "GITHUB_RUN_ATTEMPT", "RUNNER_ENVIRONMENT"):
            self.assertEqual(result[key], env[key])
        self.assertEqual(
            result["TRACKTEMPLATE_TO_RUN_CONFIG_SHA256"], "b" * 64
        )
        self.assertNotIn("TRACKTEMPLATE_L1_RUN_CONFIG", result)
        self.assertNotIn("GITHUB_TOKEN", result)
        self.assertNotIn("PYTHONPATH", result)

    def test_explicit_workload_and_workflow_default_preserve_main_and_pins(
        self,
    ):
        self.assertEqual(pilot.selected_workload({}), "l1")
        self.assertEqual(
            pilot.selected_workload(
                {"TRACKTEMPLATE_NATIVE_WORKLOAD": "to-single"}
            ),
            "to-single",
        )
        with self.assertRaises(ValueError):
            pilot.selected_workload(
                {"TRACKTEMPLATE_NATIVE_WORKLOAD": "arbitrary"}
            )
        workflow = (
            ROOT / ".github/workflows/l1-private-validation.yml"
        ).read_text()
        self.assertIn("default: l1", workflow)
        self.assertIn("          - to-single", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn(
            "ref: 155cbb0353ca59a144df697197d8a4a68a91beef", workflow
        )
        self.assertIn("if: inputs.workload != 'to-single'", workflow)
        self.assertNotIn("inputs.ref", workflow)
        self.assertIn("TRACKTEMPLATE_NATIVE_WORKLOAD:", workflow)

    def test_exact_to_receipt_counts_types_source_and_failure_fields(self):
        for stage in ("readiness", "native"):
            good = self.receipt(stage)
            pilot.validate_to_receipt(stage, good, self.config())
            for key in good["checks"]:
                for value in (good["checks"][key] + 1, True):
                    bad = copy.deepcopy(good)
                    bad["checks"][key] = value
                    with self.subTest(stage=stage, key=key, value=value):
                        with self.assertRaises(ValueError):
                            pilot.validate_to_receipt(
                                stage, bad, self.config()
                            )
            for edit in (
                lambda r: r.update(source_commit="0" * 40),
                lambda r: r.update(test_id=pilot.SELECTORS[stage]),
                lambda r: r.update(fixture_sha256="0" * 64),
                lambda r: r.update(sentinel=pilot.SENTINELS[stage]),
                lambda r: r.update(remaining_documents=True),
                lambda r: r.update(traceback="failure"),
                lambda r: r["stage_timings"].update(
                    total_seconds=float("nan")
                ),
                lambda r: r["stage_timings"].update(total_seconds=10**1000),
            ):
                bad = copy.deepcopy(good)
                edit(bad)
                with self.assertRaises(ValueError):
                    pilot.validate_to_receipt(stage, bad, self.config())

    def test_runtime_accepts_only_selected_to_unittest_frame(self):
        report = json.dumps(
            {
                "status": "modular-foundation-ready",
                "matched_profile_id": original.EXPECTED_PROFILE,
                "document_mutation": False,
                "workflow_launched": False,
            }
        )
        selector = pilot.TO_SELECTORS["native"]
        stdout = (
            f"{selector.rsplit('.', 1)[1]} ({selector}) ... "
            "TRACKTEMPLATE_B16_FOUNDATION=" + report
        )
        pilot.qualified_runtime(stdout, workload="to-single")
        with self.assertRaises(ValueError):
            pilot.qualified_runtime(stdout)
        with self.assertRaises(ValueError):
            pilot.qualified_runtime(
                stdout + "\n" + stdout, workload="to-single"
            )

    def test_publication_review_refuses_before_download(self):
        good = self.control()
        pilot.validate_to_acquisition(good)
        for edit in (
            lambda c: c.pop("publication_review"),
            lambda c: c["publication_review"].update(status="PENDING"),
            lambda c: c["publication_review"].update(
                independent_review="PENDING"
            ),
            lambda c: c["publication_review"].update(input_hashes={}),
            lambda c: c["publication_review"].update(
                handling_decision="other"
            ),
            lambda c: c["publication_review"].update(evidence_sha256="0" * 64),
            lambda c: c["publication_review"].update(publication_basis=""),
            lambda c: c.update(input_hashes={}),
            lambda c: c.update(source_commit="bad"),
        ):
            bad = copy.deepcopy(good)
            edit(bad)
            with tempfile.TemporaryDirectory() as temporary:
                with patch.object(pilot, "download_asset") as download:
                    with self.assertRaises(ValueError):
                        pilot.acquire_to(
                            "readiness", Path(temporary), control=bad
                        )
                    download.assert_not_called()

    def test_input_profile_rejects_changed_bytes_paths_and_duplicate_ids(self):
        config = self.config()
        manifest = {"inputs": copy.deepcopy(config["inputs"])}
        pilot.validate_to_inputs(config, manifest)
        for edit in (
            lambda c: c["inputs"][-1].update(bytes=True),
            lambda c: c["inputs"][-1].update(bytes=1),
            lambda c: c["inputs"][-1].update(sha256="0" * 64),
            lambda c: c["inputs"][-1].update(id=c["inputs"][0]["id"]),
            lambda c: c["inputs"][-1].update(path=c["inputs"][0]["path"]),
        ):
            bad = copy.deepcopy(config)
            edit(bad)
            with self.assertRaises(ValueError):
                pilot.validate_to_inputs(bad, manifest)

    def test_to_public_summary_has_explicit_profile_and_exact_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / "evidence").mkdir()
            pilot.write(
                work / "evidence/assessment.json",
                {
                    "status": "PASS",
                    "completed_native_tests": 1,
                    "skips": 0,
                    "native_receipt": self.receipt("native"),
                },
            )
            pilot.write(
                work / "evidence/finalization.json",
                {
                    "cleanup": True,
                    "working_copies_absent": True,
                    "staging_inputs_removed": list(pilot.TO_INPUT_HASHES),
                },
            )
            with patch.dict(
                os.environ,
                {
                    "GITHUB_SHA": "a" * 40,
                    "GITHUB_RUN_ID": "42",
                    "TRACKTEMPLATE_NATIVE_WORKLOAD": "to-single",
                },
            ):
                summary = pilot.public_summary(
                    "native",
                    work,
                    {"sha256": "b" * 64, "bytes": 100, "asset_id": 1},
                    True,
                )
            self.assertEqual(summary["workload"], "to-single")
            self.assertEqual(summary["source_commit"], "a" * 40)
            self.assertEqual(summary["outcome"], "PASS")
            self.assertEqual(summary["counts"]["observed_frames"], 59)
            self.assertEqual(summary["counts"]["observed_components"], 270)
            bad = copy.deepcopy(summary)
            bad["counts"]["observed_components"] = 138
            with self.assertRaises(ValueError):
                pilot.payload.validate_public_summary(bad, profile="to-single")

    def test_to_archive_preserves_failed_diagnostics_excludes_profile_and_documents(
        self,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            guard_dir = work / "evidence/guard"
            guard_dir.mkdir(parents=True)
            _, profile = pilot.guard._private_profile(
                ["flatpak", pilot.guard.APP_ID], guard_dir
            )
            pilot.write(
                guard_dir / "result.json",
                {"private_profile": profile, "status": "FAIL"},
            )
            (guard_dir / "profile/user.cfg").write_text("private settings")
            (guard_dir / "wrapper.stdout").write_text(
                "failed wrapper diagnostic"
            )
            (work / "evidence/execution.log").write_text("original failure")
            (work / "test-data").mkdir()
            (work / "test-data/TO-001-copy.FCStd").write_bytes(b"not public")
            with patch.dict(
                os.environ, {"TRACKTEMPLATE_NATIVE_WORKLOAD": "to-single"}
            ):
                pilot.evidence_archive(work, work / "evidence.tar")
                pilot.evidence_archive(work, work / "publication.tar")
                with tarfile.open(work / "evidence.tar") as archive:
                    names = archive.getnames()
                    self.assertIn("evidence/guard/wrapper.stdout", names)
                    self.assertIn("evidence/execution.log", names)
                    self.assertFalse(
                        any(
                            "profile/" in n or n.endswith(".FCStd")
                            for n in names
                        )
                    )
                (work / "evidence/unexpected.FCStd").write_bytes(
                    b"changed document"
                )
                with self.assertRaises(ValueError):
                    pilot.evidence_archive(work, work / "bad.tar")

    def test_to_cleanup_refuses_unknown_or_linked_working_copies_before_deletion(
        self,
    ):
        for name, linked in (
            ("unknown.FCStd", False),
            ("L1-copy.FCStd", True),
        ):
            with (
                self.subTest(name=name),
                tempfile.TemporaryDirectory() as temporary,
            ):
                work = Path(temporary)
                (work / "evidence").mkdir()
                (work / "test-data").mkdir(mode=0o700)
                pilot.write(
                    work / "evidence/process-finalization.json",
                    {"cleanup": True, "errors": [], "seconds": 0},
                )
                archive = work / "evidence.tar"
                archive.write_bytes(b"evidence")
                target = work / "test-data" / name
                if linked:
                    target.symlink_to(archive)
                else:
                    target.write_bytes(b"unknown")
                preserved = {
                    "asset_id": 1,
                    "sha256": pilot.digest(archive),
                    "bytes": archive.stat().st_size,
                }
                result = pilot.cleanup_to_staging(work, preserved)
                self.assertFalse(result["cleanup"])
                self.assertTrue(target.exists())
                self.assertEqual(archive.read_bytes(), b"evidence")

    def test_readiness_review_is_separate_exact_source_and_exact_profile(self):
        config = self.config()
        control = self.control() | {
            "workflow_commit": "a" * 40,
            "control_files_sha256": dict.fromkeys(
                pilot.TO_CONTROL_FILES, "b" * 64
            ),
        }
        good = dict(
            status="PASS",
            independent_review="PASS",
            source_commit="a" * 40,
            entry_sha256=pilot.TO_ENTRY_SHA256,
            scope_id=pilot.TO_SCOPE,
            workload="to-single",
            handling_decision=config["handling_decision"],
            workflow_commit="a" * 40,
            control_files_sha256=control["control_files_sha256"],
            run_attempt=1,
            tests=1,
            skips=0,
            failures=0,
            errors=0,
            sentinel=pilot.TO_SENTINELS["readiness"],
            cleanup=True,
            evidence_verified=True,
            independent_preservation=True,
            input_hashes=dict(pilot.TO_INPUT_HASHES),
            checks=pilot.to_expected_checks("readiness"),
            run_id=41,
            evidence_sha256="c" * 64,
        )
        pilot.validate_to_readiness(good, config, "42", control)
        for key, value in (
            ("source_commit", pilot.CANDIDATE),
            ("workload", "l1"),
            ("run_id", 42),
            ("tests", True),
            ("independent_preservation", False),
            ("sentinel", pilot.SENTINELS["readiness"]),
        ):
            bad = copy.deepcopy(good)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                pilot.validate_to_readiness(bad, config, "42", control)

    def test_real_acquisition_config_and_exact_cleanup_on_dummy_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir(mode=0o700)
            deployment = root / "deployed"
            deployment.mkdir(mode=0o700)
            work = root / "work"
            (work / "evidence").mkdir(parents=True, mode=0o700)
            contents = {name: name.encode() for name in pilot.TO_INPUT_HASHES}
            hashes = {
                name: hashlib.sha256(data).hexdigest()
                for name, data in contents.items()
            }
            sizes = {name: len(data) for name, data in contents.items()}
            with (
                patch.object(pilot, "TO_INPUT_HASHES", hashes),
                patch.object(pilot, "TO_INPUT_BYTES", sizes),
                patch.object(pilot, "DEPLOYMENT_ROOT", deployment),
            ):
                config = self.config()
                for row in config["inputs"]:
                    row["path"] = str(deployment / row["id"])
                control = self.control()
                manifest = {"schema": 1, "inputs": [], "controls": []}
                for row in config["inputs"]:
                    target = source / row["id"]
                    target.write_bytes(contents[row["id"]])
                    manifest["inputs"].append(
                        dict(
                            row,
                            member=pilot.payload.member_name(
                                "inputs", row["id"], profile="to-single"
                            ),
                        )
                    )
                # Manifest destination paths bind deployment, so create the
                # small source archive directly without touching inputs there.
                recovery = dict(
                    status="PASS",
                    independent_review="PASS",
                    checkpoint_commit="a" * 40,
                    input_hashes=hashes,
                )
                for name, record in (
                    ("run-config", config),
                    ("recovery", recovery),
                ):
                    target = source / (name + ".json")
                    pilot.write(target, record)
                    manifest["controls"].append(
                        dict(
                            id=name,
                            path=str(target),
                            member=pilot.payload.member_name("controls", name),
                            **pilot.payload.file_identity(target),
                        )
                    )
                archive = source / "payload.tar"
                with tarfile.open(archive, "w") as stream:
                    pairs = [
                        (
                            pilot.payload.MANIFEST_MEMBER,
                            json.dumps(manifest).encode(),
                        )
                    ]
                    pairs += [
                        (row["member"], contents[row["id"]])
                        for row in manifest["inputs"]
                    ]
                    pairs += [
                        (row["member"], Path(row["path"]).read_bytes())
                        for row in manifest["controls"]
                    ]
                    for name, data in pairs:
                        info = tarfile.TarInfo(name)
                        info.size = len(data)
                        stream.addfile(info, io.BytesIO(data))
                control["input_archive"] = dict(
                    asset_id=42, **pilot.payload.file_identity(archive)
                )

                def download(record, target):
                    self.assertEqual(record, control["input_archive"])
                    target.write_bytes(archive.read_bytes())

                with (
                    patch.object(
                        pilot, "download_asset", side_effect=download
                    ),
                    patch.object(pilot, "validate_input_repository"),
                    patch.object(pilot, "validate_host"),
                    patch.object(pilot, "command", return_value="a" * 40),
                    patch.dict(os.environ, {"GITHUB_SHA": "a" * 40}),
                ):
                    result = pilot.acquire_to(
                        "readiness", work, control=control
                    )
                self.assertEqual(
                    set(result),
                    {
                        *config,
                        "stage",
                        "working_directory",
                        "evidence_directory",
                        "recovery",
                    },
                )
                self.assertEqual(
                    Path(result["working_directory"]), work / "test-data"
                )
                self.assertEqual(
                    Path(result["evidence_directory"]),
                    work / "evidence/native",
                )
                for name in ("working_directory", "evidence_directory"):
                    self.assertEqual(
                        Path(result[name]).stat().st_mode & 0o777, 0o700
                    )
                for row in result["inputs"]:
                    self.assertEqual(
                        Path(row["path"]).read_bytes(), contents[row["id"]]
                    )
                    self.assertEqual(
                        Path(row["path"]).stat().st_mode & 0o777, 0o400
                    )
                self.assertEqual(
                    json.loads(
                        (work / "evidence/run-config.json").read_text()
                    ),
                    result,
                )
                for name in pilot.TO_COPY_NAMES:
                    (work / "test-data" / name).write_bytes(b"working copy")
                pilot.write(
                    work / "evidence/process-finalization.json",
                    dict(cleanup=True, errors=[], seconds=0),
                )
                (work / "evidence.tar").write_bytes(b"diagnostics")
                preserved = dict(
                    asset_id=42,
                    **pilot.payload.file_identity(work / "evidence.tar"),
                )
                final = pilot.cleanup_to_staging(work, preserved)
                self.assertTrue(final["cleanup"])
                self.assertTrue(final["working_copies_absent"])
                self.assertEqual(len(final["staging_inputs_removed"]), 10)
                self.assertFalse(list((work / "test-data").iterdir()))
                self.assertEqual(
                    archive.read_bytes()[:10],
                    (source / "payload.tar").read_bytes()[:10],
                )

    def test_profile_and_unknown_evidence_refuse_without_publication(self):
        for name in (
            "unknown.txt",
            "native/private.FCStd",
            "guard/unapproved.json",
        ):
            with (
                self.subTest(name=name),
                tempfile.TemporaryDirectory() as temporary,
            ):
                work = Path(temporary)
                path = work / "evidence" / name
                path.parent.mkdir(parents=True)
                path.write_bytes(b"unapproved")
                with patch.dict(
                    os.environ, {"TRACKTEMPLATE_NATIVE_WORKLOAD": "to-single"}
                ):
                    with self.assertRaises(ValueError):
                        pilot.evidence_archive(work, work / "evidence.tar")
                    self.assertFalse((work / "evidence.tar").exists())
        for mode in ("linked", "foreign-receipt"):
            with (
                self.subTest(mode=mode),
                tempfile.TemporaryDirectory() as temporary,
            ):
                work = Path(temporary)
                directory = work / "evidence/guard"
                directory.mkdir(parents=True)
                _, profile = pilot.guard._private_profile(
                    ["flatpak", pilot.guard.APP_ID], directory
                )
                if mode == "linked":
                    (directory / "profile/user-data/link").symlink_to(
                        directory / "stderr"
                    )
                else:
                    profile["path"] = "/unrelated/profile"
                pilot.write(
                    directory / "result.json", {"private_profile": profile}
                )
                with self.assertRaises(ValueError):
                    pilot.to_profile_exclusion(work)

    def test_to_summary_refuses_missing_working_copy_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / "evidence").mkdir()
            pilot.write(
                work / "evidence/assessment.json",
                dict(
                    status="PASS",
                    completed_native_tests=1,
                    skips=0,
                    native_receipt=self.receipt("native"),
                ),
            )
            pilot.write(
                work / "evidence/finalization.json",
                dict(
                    cleanup=True,
                    staging_inputs_removed=list(pilot.TO_INPUT_HASHES),
                ),
            )
            with patch.dict(
                os.environ,
                {
                    "GITHUB_SHA": "a" * 40,
                    "GITHUB_RUN_ID": "42",
                    "TRACKTEMPLATE_NATIVE_WORKLOAD": "to-single",
                },
            ):
                summary = pilot.public_summary(
                    "native",
                    work,
                    dict(sha256="b" * 64, bytes=100, asset_id=1),
                    True,
                )
            self.assertEqual(summary["outcome"], "INCOMPLETE")

    def test_guarded_run_uses_to_config_identity_selector_and_result_location(
        self,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / "evidence/native").mkdir(parents=True)
            config = self.config() | dict(stage="readiness")
            pilot.write(work / "run-config.json", config)
            pilot.write(work / "control.json", self.control())
            calls = []

            def guarded(argv, **kwargs):
                calls.append((argv, kwargs))
                directory = kwargs["evidence_dir"]
                directory.mkdir()
                (directory / "measurements.jsonl").write_text("{}\n")
                (directory / "stdout").write_text("raw stdout")
                (directory / "stderr").write_text("raw stderr")
                pilot.write(
                    work / "evidence/native/result.json",
                    self.receipt("readiness"),
                )
                return {"cleanup_proved": True}

            def command(*args, **kwargs):
                if "--show-runtime" in args:
                    return original.RUNTIME
                return (
                    original.RUNTIME_COMMIT
                    if original.RUNTIME in args
                    else original.APP_COMMIT
                )

            environment = dict(
                TRACKTEMPLATE_NATIVE_WORKLOAD="to-single",
                GITHUB_SHA="a" * 40,
                GITHUB_RUN_ID="42",
                GITHUB_RUN_ATTEMPT="1",
                GITHUB_ACTIONS="true",
                RUNNER_ENVIRONMENT="github-hosted",
            )
            with (
                patch.dict(os.environ, environment),
                patch.object(pilot, "validate_host"),
                patch.object(pilot, "require_finalization_time"),
                patch.object(pilot, "command", side_effect=command),
                patch.object(
                    pilot.guard, "run_guarded_flatpak", side_effect=guarded
                ),
                patch.object(
                    original, "_deadline_clearance", return_value=True
                ),
                patch.object(original, "_clearance", return_value=True),
                patch.object(
                    pilot,
                    "assess",
                    return_value={
                        "status": "PASS",
                        "completed_native_tests": 1,
                        "skips": 0,
                    },
                ) as assess,
            ):
                self.assertEqual(pilot.run("readiness", work), 0)
            self.assertEqual(len(calls), 1)
            argv, kwargs = calls[0]
            self.assertEqual(
                argv[-2:], ["-t", pilot.TO_SELECTORS["readiness"]]
            )
            self.assertEqual(argv[-3], str(ROOT / "tests"))
            self.assertEqual(kwargs["cwd"], ROOT)
            self.assertTrue(kwargs["isolate_profile"])
            self.assertEqual(
                vars(kwargs["limits"]), vars(pilot.limits("readiness"))
            )
            for name in (
                "GITHUB_SHA",
                "GITHUB_RUN_ATTEMPT",
                "RUNNER_ENVIRONMENT",
                "TRACKTEMPLATE_TO_RUN_CONFIG",
                "TRACKTEMPLATE_TO_RUN_CONFIG_SHA256",
            ):
                self.assertIn(
                    "--env=" + name + "=" + kwargs["env"][name], argv
                )
            self.assertEqual(
                assess.call_args.kwargs, {"workload": "to-single"}
            )
            self.assertEqual(
                json.loads((work / "evidence/assessment.json").read_text())[
                    "status"
                ],
                "PASS",
            )

    def test_prepare_binds_current_main_source_controls_and_entry(self):
        control = self.control() | dict(
            stage="readiness",
            workload="to-single",
            workflow_commit="a" * 40,
            independent_review="PASS",
            dispatch_nonce="nonce",
            control_files_sha256={
                name: pilot.digest(ROOT / name)
                for name in pilot.TO_CONTROL_FILES
            },
            access_review=dict(
                status="PASS",
                audited_at_utc="2026-11-02T00:00:00Z",
                owner="Richard-Gnitnub",
                environment="l1-private-validation",
                branches=["main"],
                tags=[],
                input_repository=pilot.INPUT_REPOSITORY,
                repository_public=True,
            ),
        )
        for field, value in (
            (None, None),
            ("source_commit", "b" * 40),
            ("workload", "l1"),
            ("independent_review", "PENDING"),
            ("metadata", "unavailable"),
        ):
            with (
                self.subTest(field=field),
                tempfile.TemporaryDirectory() as temporary,
            ):
                work = Path(temporary)
                (work / "evidence").mkdir()
                candidate = copy.deepcopy(control)
                if field and field != "metadata":
                    candidate[field] = value

                def command(*args, **kwargs):
                    return "" if "status" in args else "a" * 40

                environment = dict(
                    TRACKTEMPLATE_NATIVE_WORKLOAD="to-single",
                    GITHUB_SHA="a" * 40,
                    L1_PRIVATE_CONTROL=json.dumps(candidate),
                )
                with (
                    patch.dict(os.environ, environment),
                    patch.object(pilot, "command", side_effect=command),
                    patch.object(
                        pilot, "validate_host", return_value={"status": "PASS"}
                    ),
                    patch.object(pilot.resource, "setrlimit"),
                    patch.object(
                        pilot, "validate_input_repository",
                        side_effect=(ValueError("metadata unavailable")
                                     if field == "metadata" else None),
                    ) as metadata,
                ):
                    if field:
                        with self.assertRaises(ValueError):
                            pilot.prepare("readiness", work)
                        if field == "metadata":
                            self.assertEqual(
                                json.loads(
                                    (work / "control.json").read_text()),
                                control,
                            )
                        else:
                            self.assertFalse((work / "control.json").exists())
                    else:
                        pilot.prepare("readiness", work)
                        self.assertEqual(
                            json.loads((work / "control.json").read_text()),
                            control,
                        )
                    if field in (None, "metadata"):
                        metadata.assert_called_once_with()
                    else:
                        metadata.assert_not_called()


if __name__ == '__main__':
    unittest.main()
