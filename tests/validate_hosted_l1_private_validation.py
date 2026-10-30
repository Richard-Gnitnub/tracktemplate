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



if __name__ == '__main__':
    unittest.main()
