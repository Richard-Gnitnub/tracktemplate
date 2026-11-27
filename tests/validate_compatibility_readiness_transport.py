#!/usr/bin/env python3
"""Offline tests for finite readiness transport and failed-stage preservation."""

import copy
import hashlib
import importlib.util
import io
import json
import linecache
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import traceback
from contextlib import contextmanager, ExitStack, redirect_stdout
from types import CodeType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import compatibility_readiness_transport as transport  # noqa: E402

spec = importlib.util.spec_from_file_location(
    'readiness_control_fixtures',
    ROOT / 'tests/validate_hosted_compatibility_readiness.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
spec = importlib.util.spec_from_file_location(
    'readiness_output_fixtures',
    ROOT / 'tests/validate_compatibility_evidence_output.py')
output_fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(output_fixtures)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@contextmanager
def hosted_tracebacks():
    """Use hosted source filenames without changing code or traceback bytes."""
    with ExitStack() as stack:
        stack.enter_context(patch.dict(linecache.cache))
        modules = (transport, transport.readiness, transport.native,
                   output_fixtures.output,
                   sys.modules[__name__])
        for module in modules:
            for function in tuple(vars(module).values()):
                code = getattr(function, '__code__', None)
                if not isinstance(code, CodeType):
                    continue
                path = Path(code.co_filename)
                if not path.is_relative_to(ROOT):
                    continue
                name = '/home/runner/work/tracktemplate/' + str(path.relative_to(ROOT))
                source = path.read_text()
                linecache.cache[name] = (
                    len(source), None, source.splitlines(True), name)
                stack.callback(setattr, function, '__code__', code)
                function.__code__ = code.replace(co_filename=name)
        yield


def capture_refusal(path, receipt):
    """Retain the actual exception at a neutral, controlled source site."""
    try:
        transport.public_bytes(path)
    except ValueError:
        raw = traceback.format_exc().encode()
        receipt.write_bytes(raw)
        return raw
    raise AssertionError('Expected unsafe input refusal')


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ControlTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.work = self.root / 'l1-gui-123'
        self.controls = self.root / 'compatibility-readiness-control'
        self.event = self.root / 'event.json'
        self.environment = dict(self.fixture.environment,
                                RUNNER_TEMP=str(self.root),
                                GITHUB_EVENT_PATH=str(self.event))
        self.inputs = {'workload': 'compatibility-readiness'}
        for name in ('review', 'recovery'):
            self.inputs['readiness_' + name] = (
                self.fixture.decisions / (name + '.json')).read_text()
        self.inputs['readiness_control'] = json.dumps(self.fixture.control)
        self.save_event()
        capsules = {name: str(self.fixture.decisions / name)
                    for name in self.fixture.capsule_pins}
        for target, attribute, value in (
            (transport, 'ROOT', self.fixture.source),
            (transport, 'CAPSULES', capsules),
            (transport.readiness, 'CAPSULE_FILES', self.fixture.capsule_pins),
            (transport.readiness, 'DEFAULT_SHA256', self.fixture.default_hash),
        ):
            manager = patch.object(target, attribute, value)
            manager.start()
            self.addCleanup(manager.stop)
        manager = patch.dict(os.environ, self.environment, clear=True)
        manager.start()
        self.addCleanup(manager.stop)

    def save_event(self):
        save(self.event, {'repository': {
            'private': False, 'full_name': 'Richard-Gnitnub/tracktemplate'},
            'inputs': self.inputs})

    def outcome(self, *, prepare='failure', install='skipped',
                acquire='skipped', run='skipped'):
        os.environ.update(dict(zip(transport.OUTCOMES,
                                   (prepare, install, acquire, run))))

    def prepared_payload(self, *, seal=True):
        """Compose real admission and sealing with synthetic GUI observations.

        No test opens FreeCAD, starts a process or downloads anything. Only
        Git identity queries are replaced; the runtime observations, image
        and cleanup receipts are explicit offline fixtures, not host proof.
        """
        controller = transport.readiness
        capsules = {
            'assessment-inputs.json': 'tests/fixtures/runtime-assessment-inputs.json',
            'output-scope.json': 'tests/fixtures/compatibility-evidence-scope.json',
        }
        actual_pins = {name: transport.digest(ROOT / path)
                       for name, path in capsules.items()}
        for target, attribute, value in (
            (transport, 'ROOT', ROOT),
            (transport, 'CAPSULES', capsules),
            (controller, 'CAPSULE_FILES', actual_pins),
            (controller, 'DEFAULT_SHA256', transport.digest(
                ROOT / 'reference/contracts/phase1-compatibility.json')),
        ):
            manager = patch.object(target, attribute, value)
            manager.start()
            self.addCleanup(manager.stop)
        control = dict(self.fixture.control)
        control['source_files'] = {
            name: transport.digest(ROOT / name)
            for name in controller.CONTROL_FILES}
        for name in ('review', 'recovery'):
            receipt = json.loads(self.inputs['readiness_' + name])
            receipt['source_files'] = control['source_files']
            raw = json.dumps(receipt)
            self.inputs['readiness_' + name] = raw
            control[name] = {'path': name + '.json',
                             'sha256': hashlib.sha256(raw.encode()).hexdigest()}
        self.inputs['readiness_control'] = json.dumps(control)
        self.save_event()
        transport.seed()
        manager = patch.object(controller.pilot, '_command',
                               side_effect=lambda *args: (
                                   'a' * 40 if args == (
                                       'git', 'rev-parse', 'HEAD') else ''))
        manager.start()
        self.addCleanup(manager.stop)
        controller.prepare(self.controls / 'control.json', self.controls)
        self.assertEqual(self.work.stat().st_mode & 0o777, 0o700)
        scope = output_fixtures.output.load_scope_capsule(
            self.controls / 'output-scope.json', ROOT)
        observation = output_fixtures.EvidenceOutputTests.observation(
            SimpleNamespace(scope=scope))
        observation['assessment_entry_sha256'] = control['source_files'][controller.SUITE]
        observation.pop('returncode')
        observation.pop('cleanup')
        save(self.work / 'readiness-observation.json', observation)
        save(self.work / 'evidence/readiness-assessment.json', {
            'status': 'PASS', 'display_cleanup': True, 'freecad_cleanup': True})
        save(self.work / 'evidence/guard/result.json', {
            'status': 'completed', 'process_exit': 0, 'cleanup_proved': True})
        image = self.work / 'payload/gui/readiness/readiness-source.png'
        image.parent.mkdir(parents=True)
        image.write_bytes(output_fixtures.png())
        if seal:
            controller.seal(self.work)
        save(self.root / 'compatibility-readiness-finalization.json', {
            'cleanup': True,
            'workflow_outcomes': {name: 'success' for name in transport.OUTCOMES}})
        # Explicit synthetic counterparts of the successful hosted stages.
        # Their presence tests transport completeness, not runtime validity.
        for name in ('acquisition.json',):
            save(self.controls / name, {'synthetic': True})
        for name in ('base-binding.json', 'assessment-manifest.json'):
            save(self.work / name, {'synthetic': True})
        for name in (
            'installer-intent.json', 'installer-ownership.json',
            'installer-result.json', 'installer-output.log',
            'deployment.json', 'macro.json', 'clearance.json',
            'deadline-clearance.json', 'host.jsonl',
            'display-start-intent.json', 'display-ownership.json',
            'display-kernel.json', 'display-samples.jsonl',
            'display-cleanup.json', 'xvfb.log',
            'guard/control.json', 'guard/ownership.json',
            'guard/measurements.jsonl', 'guard/stdout', 'guard/stderr',
            'guard/wrapper.stdout', 'process-finalization.json',
            'transport-finalization.json',
            'transport-installer-finalization.json',
            'transport-display-finalization.json',
            'finalizer-clearance/clearance.json',
            'finalizer-clearance/deadline-clearance.json',
        ):
            save(self.work / 'evidence' / name, {'synthetic': True})
        (self.work / 'readiness_installer.py').write_text(
            controller.installer_source(
                (ROOT / 'tools/hosted_l1_gui_install.py').read_text()))
        save(self.work / 'installer-adaptation.json', {'synthetic': True})
        for name in ('seed', 'prepare', 'install', 'acquire', 'run',
                     'seal', 'finalize'):
            path = self.root / 'compatibility-readiness-logs' / (name + '.log')
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b'SYNTHETIC_CLOSED_STAGE\n')

    def readback(self, kind, identity):
        source = self.root / ('compatibility-readiness-' + kind + '.tar')
        destination = self.root / ('compatibility-readiness-' + kind + '-readback')
        destination.mkdir()
        (destination / source.name).write_bytes(source.read_bytes())
        prefix = 'L1_PRIMARY' if kind == 'primary' else 'L1_FINAL'
        os.environ.update({prefix + '_UPLOAD': 'success',
                           prefix + '_DOWNLOAD': 'success',
                           prefix + '_ID': str(identity)})

    def acquisition_only_control(self):
        """Use distinct diagnostic authority without a readiness receipt."""
        control = copy.deepcopy(self.fixture.control)
        control.update(
            stage='acquisition-diagnostic', owner_decision='D-P9-029',
            owner_decision_sha256=(
                transport.readiness.DIAGNOSTIC_DECISION_SHA256),
            acquisition_seconds=60, job_seconds=1800, maximum_attempts=1,
            gui_execution=False, sealing=False, fixture_generation=False,
            readiness_dispatch=False)
        receipt = json.loads(self.inputs['readiness_review'])
        receipt['stage'] = 'acquisition-diagnostic'
        raw = json.dumps(receipt)
        self.inputs['readiness_review'] = raw
        control['review']['sha256'] = hashlib.sha256(raw.encode()).hexdigest()
        self.inputs['readiness_control'] = json.dumps(control)
        self.inputs['workload'] = 'compatibility-acquisition-diagnostic'
        self.save_event()
        return control

    def prepared_diagnostic(self, *, acquisition='success', cleanup=True):
        """Compose admission and transport with explicit offline receipts.

        Installer process observations are synthetic. No installer, network,
        FreeCAD or display is started. Actual finalization still proves that
        neither runtime nor display state was created.
        """
        self.acquisition_only_control()
        controller = transport.readiness
        installer = self.fixture.source / 'tools/hosted_l1_gui_install.py'
        installer.write_bytes((ROOT / 'tools/hosted_l1_gui_install.py').read_bytes())
        control = json.loads(self.inputs['readiness_control'])
        control['source_files']['tools/hosted_l1_gui_install.py'] = (
            transport.digest(installer))
        for name in ('review', 'recovery'):
            receipt = json.loads(self.inputs['readiness_' + name])
            receipt['source_files'] = control['source_files']
            raw = json.dumps(receipt)
            self.inputs['readiness_' + name] = raw
            control[name]['sha256'] = hashlib.sha256(raw.encode()).hexdigest()
        self.inputs['readiness_control'] = json.dumps(control)
        self.save_event()
        transport.seed()
        with patch.object(controller, 'ROOT', self.fixture.source), \
                patch.object(controller.pilot, '_command',
                             side_effect=lambda *args: (
                                 'a' * 40 if args == (
                                     'git', 'rev-parse', 'HEAD') else '')):
            controller.prepare(self.controls / 'control.json', self.controls)
        (self.work / 'readiness_installer.py').write_text(
            controller.installer_source(installer.read_text()))
        save(self.work / 'installer-adaptation.json', {'synthetic': True})
        for name in ('installer-intent.json', 'installer-ownership.json',
                     'installer-output.log'):
            save(self.work / 'evidence' / name, {'synthetic': True})
        save(self.work / 'evidence/installer-result.json', {
            'status': 'PASS', 'cleanup': True, 'synthetic': True})
        if acquisition == 'success':
            save(self.controls / 'acquisition.json', {'synthetic': True})
            for name in ('base-binding.json', 'assessment-manifest.json'):
                save(self.work / name, {'synthetic': True})
        logs = self.root / 'compatibility-readiness-logs'
        logs.mkdir()
        for name in ('seed', 'prepare', 'install', 'acquire', 'finalize'):
            (logs / (name + '.log')).write_bytes(b'SYNTHETIC_CLOSED_STAGE\n')
        self.outcome(prepare='success', install='success', acquire=acquisition)
        with patch.object(transport, 'installer_cleanup',
                          return_value={'cleanup': cleanup, 'synthetic': True}):
            result = transport.finalize()
        self.assertEqual(result['cleanup'], cleanup)
        self.assertTrue(result['runtime'])
        self.assertTrue(result['display'])
        return control

    def diagnostic_readback(self, kind):
        prefix = transport.DIAGNOSTIC_PREFIX
        environment = 'L1_' + kind.upper()
        if kind == 'acquisition-failure':
            prefix = 'compatibility-readiness'
            environment = 'L1_DIAGNOSTIC'
        elif kind == 'transport-failure':
            environment = 'L1_TRANSPORT_FAILURE'
        source = self.root / (prefix + '-' + kind + '.tar')
        destination = self.root / (prefix + '-' + kind + '-readback')
        destination.mkdir()
        (destination / source.name).write_bytes(source.read_bytes())
        os.environ.update({environment + '_UPLOAD': 'success',
                           environment + '_DOWNLOAD': 'success',
                           environment + '_ID': '123'})
        return destination / source.name

    def assert_partial_diagnostic(self, originals, rejected, missing):
        """Prove safe byte preservation without accepting incomplete evidence."""
        with patch.object(transport, 'reseal_payload') as seal, \
                patch.object(transport.readiness, 'run') as run:
            self.assertEqual(transport.diagnostic_archive(), 'FAIL')
            primary = self.diagnostic_readback('primary')
            publication = transport.diagnostic_publish()
            self.assertEqual(publication['status'], 'FAIL')
            self.assertIs(
                publication['original_diagnostic_preservation_complete'], False)
            self.assertEqual(publication['missing_mandatory_evidence'], missing)
            final = self.diagnostic_readback('final')
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(transport.main(['diagnostic-complete']), 1)
            seal.assert_not_called()
            run.assert_not_called()
        self.assertEqual(output.getvalue(),
                         'COMPATIBILITY_ACQUISITION_DIAGNOSTIC_FAIL\n')
        completion = json.loads((self.root / (transport.DIAGNOSTIC_PREFIX
                                + '-completion.json')).read_bytes())
        self.assertEqual(completion['status'], 'FAIL')
        self.assertEqual(completion['evidence_status'], 'FAIL')
        self.assertEqual(completion['acquisition_outcome'], 'success')
        for name in ('runtime_admission', 'matrix_dispatch', 'zy_execution',
                     'readiness_dispatch'):
            self.assertIs(completion[name], False)
        for kind, readback in (('primary', primary), ('final', final)):
            artifact = self.root / (transport.DIAGNOSTIC_PREFIX
                                    + '-' + kind + '.tar')
            self.assertEqual(readback.read_bytes(), artifact.read_bytes())
            with tarfile.open(readback, 'r:') as bundle:
                names = set(bundle.getnames())
                self.assertTrue(set(originals) <= names)
                for name, raw in originals.items():
                    self.assertEqual(bundle.extractfile(name).read(), raw)
                self.assertFalse(set(rejected) & names)
                self.assertFalse(any(name.startswith('payload/')
                                     for name in names))
                refusal_raw = bundle.extractfile(
                    'transport/member-refusals.json').read()
                refusal = json.loads(refusal_raw)
                self.assertEqual(refusal, {
                    'schema_version': 1, 'status': 'FAIL',
                    'source_commit': os.environ['GITHUB_SHA'],
                    'run_id': os.environ['GITHUB_RUN_ID'], 'run_attempt': 1,
                    'stage': ('diagnostic-archive' if kind == 'primary'
                              else 'diagnostic-publish'),
                    'members': {name: reason for name, (_, _, reason)
                                in rejected.items()},
                })
                if kind == 'primary':
                    manifest = json.loads(bundle.extractfile(
                        'transport/manifest.json').read())
                    self.assertEqual(manifest['evidence_status'], 'FAIL')
                    self.assertIs(manifest[
                        'original_diagnostic_preservation_complete'], False)
                    self.assertEqual(manifest['missing_mandatory_evidence'],
                                     missing)
                    self.assertEqual(manifest['files'], {
                        name: {'bytes': len(raw),
                               'sha256': hashlib.sha256(raw).hexdigest()}
                        for name, raw in dict(originals, **{
                            'transport/member-refusals.json': refusal_raw,
                        }).items()})
            for path, raw, _ in rejected.values():
                self.assertEqual(path.read_bytes(), raw)
                self.assertNotIn(raw, artifact.read_bytes())

    def test_diagnostic_rejected_mandatory_member_keeps_all_safe_originals(self):
        self.prepared_diagnostic()
        diagnostic = self.root / 'compatibility-readiness-private/acquire.txt'
        diagnostic.parent.mkdir()
        diagnostic.write_bytes(b'Original safe diagnostic\n')
        originals, _, _ = transport._operational_contents(self.root, self.work)
        self.assertGreaterEqual(len(originals), 24)
        name = 'operational/installer-output.log'
        rejected = self.work / 'evidence/installer-output.log'
        raw = b'/root/.local/share/flatpak/exports/share\n'
        rejected.write_bytes(raw)
        originals.pop(name)
        self.assert_partial_diagnostic(
            originals, {name: (rejected, raw, 'private-path')}, [name])

    def test_diagnostic_multiple_content_refusals_remain_finite_and_exact(self):
        self.prepared_diagnostic()
        diagnostic = self.root / 'compatibility-readiness-private/acquire.txt'
        diagnostic.parent.mkdir()
        diagnostic.write_bytes(b'Original safe diagnostic\n')
        samples = self.work / 'evidence/installer-samples.jsonl'
        samples.write_bytes(b'Original safe samples\n')
        originals, _, _ = transport._operational_contents(self.root, self.work)
        rejected = {
            'operational/installer-output.log': (
                self.work / 'evidence/installer-output.log',
                b'/home/operator/private-original\n', 'private-path'),
            'logs/install.log': (
                self.root / 'compatibility-readiness-logs/install.log',
                b'Authorization: synthetic-excluded-value\n',
                'credential-pattern'),
            'original-diagnostics/acquire.txt': (
                diagnostic, b'\xff\x00', 'invalid-utf8'),
            'operational/installer-samples.jsonl': (
                samples, b'x' * (transport.MAX_FILE + 1), 'oversize'),
        }
        for name, (path, raw, _) in rejected.items():
            path.write_bytes(raw)
            originals.pop(name)
        self.assert_partial_diagnostic(originals, rejected, [
            'logs/install.log', 'operational/installer-output.log'])

    def test_diagnostic_optional_refusal_cannot_claim_complete_evidence(self):
        self.prepared_diagnostic()
        originals, _, _ = transport._operational_contents(self.root, self.work)
        rejected = self.work / 'evidence/installer-samples.jsonl'
        raw = b'/home/operator/private-optional-original\n'
        rejected.write_bytes(raw)
        self.assert_partial_diagnostic(originals, {
            'operational/installer-samples.jsonl': (
                rejected, raw, 'private-path'),
        }, [])

    def test_diagnostic_rejected_readback_traceback_keeps_final_failure(self):
        self.prepared_diagnostic()
        originals, _, _ = transport._operational_contents(self.root, self.work)
        self.assertEqual(transport.diagnostic_archive(), 'PASS')
        hostile = '/home/operator/private-readback-detail'
        with patch.object(transport, '_readback',
                          side_effect=ValueError(hostile)):
            publication = transport.diagnostic_publish()
        self.assertEqual(publication['status'], 'FAIL')
        self.assertIsNone(publication['primary'])
        self.assertEqual(publication['missing_mandatory_evidence'], [])
        self.assertIs(publication[
            'original_diagnostic_preservation_complete'], False)
        original = self.root / 'compatibility-readiness-private/publish-primary.txt'
        raw = original.read_bytes()
        self.assertIn(hostile.encode(), raw)
        final = self.diagnostic_readback('final')
        with tarfile.open(final, 'r:') as bundle:
            for name, safe_raw in originals.items():
                self.assertEqual(bundle.extractfile(name).read(), safe_raw)
            self.assertNotIn('original-diagnostics/publish-primary.txt',
                             bundle.getnames())
            ledger = json.loads(bundle.extractfile(
                'transport/member-refusals.json').read())
            self.assertEqual(ledger['members'], {
                'original-diagnostics/publish-primary.txt': 'private-path'})
            self.assertEqual(ledger['status'], 'FAIL')
        self.assertNotIn(hostile.encode(), final.read_bytes())
        self.assertEqual(original.read_bytes(), raw)
        self.assertEqual(transport.diagnostic_complete(), 'FAIL')

    def test_diagnostic_link_refuses_before_partial_artifact(self):
        self.prepared_diagnostic()
        original = self.work / 'evidence/installer-output.log'
        retained = self.work / 'retained-installer-output.log'
        original.rename(retained)
        original.symlink_to(retained)
        for operation in (transport.diagnostic_archive,
                          transport.diagnostic_publish):
            with self.subTest(operation=operation.__name__):
                with self.assertRaisesRegex(ValueError, 'Linked evidence member'):
                    operation()
        self.assertTrue(original.is_symlink())
        self.assertEqual(retained.read_bytes(), b'{"synthetic": true}')
        for kind in ('primary', 'final'):
            self.assertFalse((self.root / (transport.DIAGNOSTIC_PREFIX
                                          + '-' + kind + '.tar')).exists())

    def test_diagnostic_foreign_owner_and_io_error_are_not_content_refusals(self):
        self.prepared_diagnostic()
        original = self.work / 'evidence/installer-output.log'
        raw = original.read_bytes()
        original_stat = Path.stat
        original_read = Path.read_bytes

        def foreign_stat(candidate, *args, **kwargs):
            result = original_stat(candidate, *args, **kwargs)
            if candidate == original:
                fields = list(result)
                fields[4] = os.getuid() + 1
                return os.stat_result(fields)
            return result

        def refused_read(candidate):
            if candidate == original:
                raise PermissionError('Injected unreadable original')
            return original_read(candidate)

        for operation in (transport.diagnostic_archive,
                          transport.diagnostic_publish):
            with self.subTest(operation=operation.__name__):
                with patch.object(Path, 'stat', foreign_stat), \
                        self.assertRaisesRegex(ValueError, 'Foreign evidence owner'):
                    operation()
                with patch.object(Path, 'read_bytes', refused_read), \
                        self.assertRaises(PermissionError):
                    operation()
        self.assertEqual(original.read_bytes(), raw)
        for kind in ('primary', 'final'):
            self.assertFalse((self.root / (transport.DIAGNOSTIC_PREFIX
                                          + '-' + kind + '.tar')).exists())

    def test_readiness_content_refusal_still_rejects_whole_archive(self):
        self.prepared_payload()
        original = self.work / 'evidence/installer-output.log'
        raw = b'/home/operator/private-readiness-original\n'
        original.write_bytes(raw)
        for operation in (transport.archive, transport.publish):
            with self.subTest(operation=operation.__name__):
                with self.assertRaisesRegex(ValueError, 'Private path'):
                    operation()
        self.assertEqual(original.read_bytes(), raw)
        for kind in ('primary', 'final'):
            self.assertFalse((self.root / (
                'compatibility-readiness-' + kind + '.tar')).exists())

    def test_diagnostic_control_is_distinct_and_cannot_run_or_seal(self):
        control = self.acquisition_only_control()
        transport.seed()
        self.assertEqual(transport._diagnostic_controls(), self.controls)
        with patch.object(transport.readiness, 'prerequisites',
                          return_value=(control, self.controls)), \
                patch.object(transport.readiness.gui, 'start_display') as display:
            for action in (transport.readiness.run, transport.readiness.seal):
                with self.subTest(action=action.__name__), self.assertRaisesRegex(
                        ValueError, 'Acquisition diagnostic cannot'):
                    action(self.work)
            display.assert_not_called()
        self.assertFalse(self.work.exists())

    def test_diagnostic_control_rejects_authority_limits_and_scope_drift(self):
        control = self.acquisition_only_control()
        save(self.fixture.decisions / 'review.json', json.loads(
            self.inputs['readiness_review']))
        control['review']['sha256'] = transport.digest(
            self.fixture.decisions / 'review.json')
        for key, value in (
            ('owner_decision', 'D-P9-023'),
            ('owner_decision', 'D-P9-026'),
            ('owner_decision', 'D-P9-027'),
            ('owner_decision', 'D-P9-028'),
            ('owner_decision_sha256', transport.readiness.DECISION_SHA256),
            ('owner_decision_sha256',
             '71b317be170dd7541f8a4deea759182ca6cecf6ff693a1c79d363dda4bc96b33'),
            ('owner_decision_sha256',
             'f4f3e129f36b1544ace05dcfbeb8cb53e453462e43df422fb8adb9da0b217a74'),
            ('owner_decision_sha256',
             'e52cf467250d8a8c7e43742c2066760e565e22f906890d4ba8776e352dfb30db'),
            ('acquisition_seconds', 61), ('job_seconds', 1801),
            ('maximum_attempts', 2), ('gui_execution', True),
            ('sealing', True), ('fixture_generation', True),
            ('readiness_dispatch', True), ('source_commit', 'b' * 40),
        ):
            changed = dict(control, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.fixture.validate(changed)
        for key, value in (('GITHUB_RUN_ATTEMPT', '2'),
                           ('RUNNER_ARCH', 'ARM64')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.fixture.validate(control, dict(self.environment, **{key: value}))

    def test_diagnostic_receipt_and_dispatch_cannot_claim_readiness(self):
        self.acquisition_only_control()
        self.inputs['workload'] = 'compatibility-readiness'
        self.save_event()
        with self.assertRaisesRegex(ValueError, 'Dispatch stage differs'):
            transport.seed()
        self.assertFalse(self.controls.exists())

    def test_readiness_receipt_cannot_authorize_diagnostic_entry(self):
        control = self.acquisition_only_control()
        self.inputs['readiness_review'] = (
            self.fixture.decisions / 'review.json').read_text()
        control['review'] = self.fixture.control['review']
        self.inputs['readiness_control'] = json.dumps(control)
        self.save_event()
        with self.assertRaisesRegex(ValueError, 'Independent readiness review missing'):
            transport.seed()
        self.assertFalse((self.controls / 'seed.json').exists())

    def test_diagnostic_success_stops_before_gui_and_means_nonreproduction(self):
        self.prepared_diagnostic()
        with patch.object(transport, 'reseal_payload') as seal, \
                patch.object(transport.readiness, 'run') as run:
            self.assertEqual(transport.diagnostic_archive(), 'PASS')
            self.diagnostic_readback('primary')
            self.assertEqual(transport.diagnostic_publish()['status'], 'PASS')
            self.diagnostic_readback('final')
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(transport.main(['diagnostic-complete']), 0)
            seal.assert_not_called()
            run.assert_not_called()
        self.assertEqual(output.getvalue(),
                         'COMPATIBILITY_ACQUISITION_DIAGNOSTIC_'
                         'PASS_NON_REPRODUCTION\n')
        record = json.loads((self.root / (transport.DIAGNOSTIC_PREFIX
                            + '-completion.json')).read_bytes())
        self.assertEqual(record['interpretation'], 'non-reproduction-only')
        self.assertEqual(record['evidence_status'], 'PASS')
        self.assertEqual(record['acquisition_outcome'], 'success')
        self.assertIsNone(record['acquisition_failure_readback'])
        for name in ('runtime_admission', 'matrix_dispatch', 'zy_execution',
                     'readiness_dispatch'):
            self.assertIs(record[name], False)
        self.assertFalse((self.work / 'evidence/guard').exists())
        self.assertFalse((self.work / 'payload').exists())
        self.assertFalse((self.root /
                          'compatibility-readiness-completion.json').exists())

    def test_diagnostic_failure_retains_failure_after_all_exact_readbacks(self):
        self.prepared_diagnostic(acquisition='failure')
        original = b'ValueError: injected second acquisition command failure\n'
        (self.root / 'compatibility-readiness-logs/acquire.log').write_bytes(original)
        transport.acquisition_diagnostic()
        self.diagnostic_readback('acquisition-failure')
        self.assertEqual(transport.diagnostic_archive(), 'FAIL')
        self.diagnostic_readback('primary')
        self.assertEqual(transport.diagnostic_publish()['status'], 'PASS')
        self.diagnostic_readback('final')
        with redirect_stdout(io.StringIO()):
            self.assertEqual(transport.main(['diagnostic-complete']), 1)
        record = json.loads((self.root / (transport.DIAGNOSTIC_PREFIX
                            + '-completion.json')).read_bytes())
        self.assertEqual(record['status'], 'FAIL')
        self.assertEqual(record['evidence_status'], 'PASS')
        self.assertEqual(record['acquisition_outcome'], 'failure')
        for kind in ('primary', 'final'):
            with tarfile.open(self.root / (transport.DIAGNOSTIC_PREFIX
                                           + '-' + kind + '.tar')) as bundle:
                self.assertEqual(bundle.extractfile('logs/acquire.log').read(),
                                 original)
                self.assertFalse(any(name.startswith('payload/')
                                     for name in bundle.getnames()))

    def test_diagnostic_capture_survives_both_diagnostic_archive_refusals(self):
        self.acquisition_only_control()
        originals = self.failed_acquisition()
        (self.work / 'evidence/unlisted.txt').write_text('not approved')
        with hosted_tracebacks(), redirect_stdout(io.StringIO()):
            self.assertEqual(transport.main(['diagnostic-archive']), 1)
            self.assertEqual(transport.main(['diagnostic-publish']), 1)
        transport.acquisition_diagnostic()
        _, members, _ = self.diagnostic_members()
        self.assertEqual(members, originals)
        for kind in ('primary', 'final'):
            self.assertFalse((self.root / (transport.DIAGNOSTIC_PREFIX
                                          + '-' + kind + '.tar')).exists())

    def test_transport_refusal_after_successful_acquisition_is_independent(self):
        self.prepared_diagnostic()
        os.environ['GITHUB_JOB'] = transport.DIAGNOSTIC_PREFIX
        rejected = self.work / 'evidence/unlisted.txt'
        original = b'/home/operator/private-input\n'
        rejected.write_bytes(original)
        for stage in ('archive', 'publish'):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(transport.main(['diagnostic-' + stage]), 1)
        os.environ.update(L1_ARCHIVE='failure', L1_PUBLISH='failure')
        with ExitStack() as stack:
            operations = [stack.enter_context(patch.object(
                transport, name, side_effect=AssertionError('Collector reused')))
                for name in ('_operational_contents', 'diagnostic_archive',
                             'diagnostic_publish')]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(transport.main(['diagnostic-failure']), 0)
                self.diagnostic_readback('transport-failure')
                self.assertEqual(transport.main([
                    'diagnostic-failure-readback']), 0)
            for operation in operations:
                operation.assert_not_called()
        artifact = self.root / (transport.DIAGNOSTIC_PREFIX
                                + '-transport-failure.tar')
        with tarfile.open(artifact, 'r:') as bundle:
            self.assertEqual(set(bundle.getnames()), {
                'transport/archive-refusal.json',
                'transport/publish-refusal.json'})
            for stage in ('archive', 'publish'):
                raw = bundle.extractfile(
                    'transport/' + stage + '-refusal.json').read()
                record = json.loads(raw)
                self.assertEqual(record['reason_code'], 'unlisted-member')
                self.assertEqual(record['status'], 'FAIL')
                self.assertEqual(record['stage'], 'diagnostic-' + stage)
                self.assertEqual(record['source_commit'],
                                 os.environ['GITHUB_SHA'])
                self.assertEqual(record['run_id'], os.environ['GITHUB_RUN_ID'])
                self.assertNotIn(original.strip(), raw)
        self.assertEqual(rejected.read_bytes(), original)
        for kind in ('primary', 'final'):
            self.assertFalse((self.root / (transport.DIAGNOSTIC_PREFIX
                                          + '-' + kind + '.tar')).exists())
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(transport.main(['diagnostic-complete']), 1)
        self.assertNotIn('PASS_NON_REPRODUCTION', output.getvalue())

    def test_transport_refusal_categories_are_finite(self):
        os.environ['GITHUB_JOB'] = transport.DIAGNOSTIC_PREFIX
        cases = (
            (ValueError('Private path in operational evidence'), 'private-path'),
            (ValueError('Credential-like operational evidence'),
             'credential-pattern'),
            (ValueError('Unlisted operational evidence'), 'unlisted-member'),
            (ValueError('Unexpected evidence directory'), 'unlisted-member'),
            (ValueError('Operational file too large'), 'oversize'),
            (ValueError('Operational archive too large'), 'oversize'),
            (ValueError('Archive bound exceeded'), 'oversize'),
            (UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'bad'), 'invalid-utf8'),
            (OSError('unknown private cause'), 'operation-refused'),
            (KeyError('unknown private field'), 'operation-refused'),
            (TypeError('unknown private type'), 'operation-refused'),
        )
        for error, expected in cases:
            with self.subTest(reason=expected), patch.object(
                    transport, 'write') as writer:
                transport._diagnostic_refusal_record('diagnostic-archive', error)
                record = writer.call_args.args[1]
                self.assertEqual(record['reason_code'], expected)
                self.assertEqual(set(record), {
                    'schema_version', 'status', 'source_commit', 'run_id',
                    'run_attempt', 'stage', 'reason_code', 'exception_category'})

    def test_transport_refusal_survives_private_retention_failure(self):
        self.prepared_diagnostic()
        os.environ['GITHUB_JOB'] = transport.DIAGNOSTIC_PREFIX
        hostile = '/home/operator/secret github_pat_SYNTHETIC_ONLY rejected-data'
        with patch.object(transport, '_operational_contents',
                          side_effect=ValueError(hostile)):
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(transport.main(['diagnostic-archive']), 1)
            self.assertNotIn(hostile, output.getvalue())
            private = self.root / 'compatibility-readiness-private/archive.txt'
            self.assertIn(hostile, private.read_text())
            receipt = self.root / (transport.DIAGNOSTIC_PREFIX
                                   + '-publish-refusal.json')

            def unavailable(_stage):
                self.assertTrue(receipt.is_file())
                raise OSError(hostile)

            with patch.object(transport, 'retain_failure',
                              side_effect=unavailable), \
                    redirect_stdout(io.StringIO()) as output:
                self.assertEqual(transport.main(['diagnostic-publish']), 1)
            self.assertIn('COMPATIBILITY_DIAGNOSTIC_PRIVATE_RETENTION_FAIL',
                          output.getvalue())
            self.assertNotIn(hostile, output.getvalue())
        os.environ.update(L1_ARCHIVE='failure', L1_PUBLISH='failure')
        transport.diagnostic_failure()
        artifact = self.root / (transport.DIAGNOSTIC_PREFIX
                                + '-transport-failure.tar')
        self.assertNotIn(hostile.encode(), artifact.read_bytes())
        self.assertEqual(json.loads(receipt.read_bytes())['reason_code'],
                         'operation-refused')
        self.diagnostic_readback('transport-failure')
        self.assertEqual(transport.diagnostic_failure_readback()['asset_id'], 123)

    def test_transport_refusal_missing_changed_receipt_and_readback_refuse(self):
        os.environ.update(GITHUB_JOB=transport.DIAGNOSTIC_PREFIX,
                          L1_ARCHIVE='failure', L1_PUBLISH='success')
        with self.assertRaises((OSError, ValueError)):
            transport.diagnostic_failure()
        transport._diagnostic_refusal_record(
            'diagnostic-archive', ValueError('Unlisted operational evidence'))
        receipt = self.root / (transport.DIAGNOSTIC_PREFIX
                               + '-archive-refusal.json')
        original = receipt.read_bytes()
        record = json.loads(original)
        changes = (('source_commit', 'b' * 40), ('run_id', '999'),
                   ('run_attempt', True), ('schema_version', True),
                   ('status', 'PASS'), ('stage', 'diagnostic-publish'),
                   ('reason_code', 'unknown'), ('exception_category', 'Secret'),
                   ('extra', 'unapproved'))
        for key, value in changes:
            with self.subTest(field=key):
                receipt.write_text(json.dumps(dict(record, **{key: value})))
                with self.assertRaises(ValueError):
                    transport.diagnostic_failure()
        receipt.write_bytes(original)
        transport.diagnostic_failure()
        readback = self.diagnostic_readback('transport-failure')
        self.assertEqual(transport.diagnostic_failure_readback()['asset_id'], 123)
        changed = bytearray(readback.read_bytes())
        changed[-1] ^= 1
        readback.write_bytes(changed)
        with self.assertRaisesRegex(ValueError, 'Artifact readback differs'):
            transport.diagnostic_failure_readback()

    def test_transport_refusal_requires_acquisition_job_and_step_outcomes(self):
        for job in ('compatibility-readiness', 'compatibility-matrix', ''):
            with self.subTest(job=job), patch.dict(os.environ, GITHUB_JOB=job):
                with self.assertRaises(ValueError):
                    transport.diagnostic_failure()
        os.environ['GITHUB_JOB'] = transport.DIAGNOSTIC_PREFIX
        with self.assertRaises(ValueError):
            transport.diagnostic_failure()

    def test_diagnostic_missing_mandatory_original_is_incomplete(self):
        self.prepared_diagnostic()
        original = self.work / 'evidence/installer-output.log'
        original.rename(self.work / 'retained-installer-output.log')
        self.assertEqual(transport.diagnostic_archive(), 'FAIL')
        record = json.loads((self.root / (transport.DIAGNOSTIC_PREFIX
                            + '-archive.json')).read_bytes())
        self.assertIn('operational/installer-output.log',
                      record['manifest']['missing_mandatory_evidence'])
        self.assertEqual(record['manifest']['evidence_status'], 'FAIL')

    def test_diagnostic_unproved_cleanup_cannot_report_nonreproduction(self):
        self.prepared_diagnostic(cleanup=False)
        self.assertEqual(transport.diagnostic_archive(), 'FAIL')
        self.diagnostic_readback('primary')
        self.assertEqual(transport.diagnostic_publish()['status'], 'FAIL')
        self.diagnostic_readback('final')
        self.assertEqual(transport.diagnostic_complete(), 'FAIL')

    def test_diagnostic_missing_separate_readback_prevents_completion(self):
        self.prepared_diagnostic(acquisition='failure')
        transport.acquisition_diagnostic()
        transport.diagnostic_archive()
        self.diagnostic_readback('primary')
        with hosted_tracebacks():
            self.assertEqual(transport.diagnostic_publish()['status'], 'FAIL')
        self.diagnostic_readback('final')
        self.assertEqual(transport.diagnostic_complete(), 'FAIL')
        record = json.loads((self.root / (transport.DIAGNOSTIC_PREFIX
                            + '-completion.json')).read_bytes())
        self.assertEqual(record['evidence_status'], 'FAIL')

    def test_diagnostic_changed_final_readback_refuses(self):
        self.prepared_diagnostic()
        transport.diagnostic_archive()
        self.diagnostic_readback('primary')
        transport.diagnostic_publish()
        path = self.diagnostic_readback('final')
        path.write_bytes(b'changed artifact')
        with self.assertRaises(ValueError):
            transport.diagnostic_complete()

    def test_diagnostic_forbidden_runtime_state_refuses_before_archiving(self):
        self.prepared_diagnostic()
        (self.work / 'readiness-entry.FCMacro').write_text('not executed')
        with self.assertRaisesRegex(ValueError, 'Acquisition-only boundary exceeded'):
            transport.diagnostic_archive()
        self.assertFalse((self.root / (transport.DIAGNOSTIC_PREFIX
                                      + '-primary.tar')).exists())

    def test_diagnostic_changed_separate_readback_prevents_evidence_pass(self):
        self.prepared_diagnostic(acquisition='failure')
        transport.acquisition_diagnostic()
        path = self.diagnostic_readback('acquisition-failure')
        path.write_bytes(b'changed separate artifact')
        transport.diagnostic_archive()
        self.diagnostic_readback('primary')
        with hosted_tracebacks():
            publication = transport.diagnostic_publish()
        self.assertEqual(publication['status'], 'FAIL')
        self.assertIsNone(publication['acquisition_failure'])

    def test_diagnostic_workflow_is_one_serial_first_attempt_without_runtime(self):
        workflow = (ROOT / '.github/workflows/native-geometry-pilot.yml').read_text()
        job = workflow.split('  compatibility-acquisition-diagnostic:\n', 1)[1].split(
            '\n  compatibility-matrix:', 1)[0]
        self.assertIn("inputs.workload == 'compatibility-acquisition-diagnostic'", job)
        self.assertIn('github.run_attempt == 1', job)
        self.assertIn('runs-on: ubuntu-24.04', job)
        self.assertIn('timeout-minutes: 30', job)
        self.assertIn('group: issue230-native-geometry', workflow)
        self.assertIn('cancel-in-progress: false', workflow)
        native = workflow.split('  native-geometry:\n', 1)[1].split(
            '\n  compatibility-readiness:', 1)[0]
        self.assertIn("inputs.workload != 'compatibility-acquisition-diagnostic'", native)
        self.assertEqual(job.count('id: install\n'), 1)
        self.assertEqual(job.count('id: acquire\n'), 1)
        self.assertNotIn('continue-on-error', job)
        for forbidden in ('id: run\n', 'id: seal\n', 'strategy:',
                          'runtime_compatibility_transport.py',
                          'hosted_compatibility_readiness.py run',
                          'hosted_compatibility_readiness.py seal'):
            self.assertNotIn(forbidden, job)
        self.assertIn('L1_RUN: skipped', job)
        refusal = job.split('        id: transport_failure\n', 1)[1].split(
            '\n      - name:', 1)[0]
        upload = job.split('        id: transport_failure_upload\n', 1)[1].split(
            '\n      - name:', 1)[0]
        download = job.split('        id: transport_failure_download\n', 1)[1].split(
            '\n      - name:', 1)[0]
        self.assertIn("steps.archive.outcome == 'failure' || "
                      "steps.publish.outcome == 'failure'", refusal)
        self.assertIn('L1_ARCHIVE: ${{ steps.archive.outcome }}', refusal)
        self.assertIn('L1_PUBLISH: ${{ steps.publish.outcome }}', refusal)
        self.assertIn('compatibility_readiness_transport.py diagnostic-failure',
                      refusal)
        self.assertIn("steps.transport_failure.outcome == 'success'", upload)
        self.assertIn('retention-days: 30', upload)
        self.assertIn('if-no-files-found: error', upload)
        self.assertIn('artifact-ids: ${{ steps.transport_failure_upload.outputs.'
                      'artifact-id }}', download)
        self.assertIn('compatibility_readiness_transport.py '
                      'diagnostic-failure-readback', job)
        install = job.split('        id: install\n', 1)[1].split(
            '\n      - name:', 1)[0]
        self.assertIn('timeout-minutes: 9', install)
        acquisition = job.split('        id: acquire\n', 1)[1].split(
            '\n      - name:', 1)[0]
        self.assertIn('timeout-minutes: 1', acquisition)
        readiness = workflow.split('  compatibility-readiness:\n', 1)[1].split(
            '\n  compatibility-acquisition-diagnostic:', 1)[0]
        original = readiness.split('        id: acquire\n', 1)[1].split(
            '\n      - name:', 1)[0]
        self.assertEqual(acquisition, original)
        commands = acquisition.split('        run: |\n', 1)[1]
        commands = '\n'.join(line[10:] for line in commands.splitlines())
        stub = '''python3() {
  printf '%s\\n' "$1" >> "$RUNNER_TEMP/invocations.log"
  if [[ "$1" == tools/compatibility_readiness_transport.py ]]; then
    return "$FIRST_EXIT"
  fi
  return "$SECOND_EXIT"
}
'''
        logs = self.root / 'compatibility-readiness-logs'
        logs.mkdir()
        for first, second, expected, count in (
            (17, 0, 17, 1), (0, 23, 23, 2), (0, 0, 0, 2),
        ):
            with self.subTest(first=first, second=second):
                result = subprocess.run(
                    ['/bin/bash', '--noprofile', '--norc', '-e', '-o',
                     'pipefail', '-c', stub + commands],
                    env=dict(self.environment, FIRST_EXIT=str(first),
                             SECOND_EXIT=str(second)),
                    capture_output=True, check=False, timeout=5)
                self.assertEqual(result.returncode, expected)
                calls = self.root / 'invocations.log'
                self.assertEqual(len(calls.read_text().splitlines()), count)
                calls.rename(self.root / f'invocations-{first}-{second}.log')
        for step in ('acquire_diagnostic_upload', 'primary_upload', 'final_upload'):
            block = job.split('        id: ' + step + '\n', 1)[1].split(
                '\n      - name:', 1)[0]
            self.assertIn('retention-days: 30', block)
            self.assertIn('if-no-files-found: error', block)
            self.assertNotIn('*', block)
        self.assertIn('id: acquire_diagnostic_download', job)
        self.assertIn('id: primary_download', job)
        self.assertIn('id: final_download', job)
        self.assertIn('compatibility_readiness_transport.py diagnostic-complete', job)
        self.assertLess(job.index('id: acquire_diagnostic_upload'),
                        job.index('id: archive\n'))

    def test_seed_preserves_exact_receipt_bytes_and_binds_sources(self):
        self.assertEqual(transport.seed(), self.controls)
        for name in ('control', 'review', 'recovery'):
            self.assertEqual((self.controls / (name + '.json')).read_bytes(),
                             self.inputs['readiness_' + name].encode())
        self.assertEqual(transport.seeded(), self.controls)
        (self.controls / 'review.json').write_text('{}')
        with self.assertRaises(ValueError):
            transport.seeded()

    def test_unknown_event_and_duplicate_keys_refuse_without_seed(self):
        self.inputs['unreviewed'] = 'private'
        self.save_event()
        with self.assertRaises(ValueError):
            transport.seed()
        self.assertFalse(self.controls.exists())
        with self.assertRaises(ValueError):
            transport.strict_json('{"key":1,"key":2}')
        with self.assertRaises(ValueError):
            transport.strict_json('{"key":NaN}')

    def test_unreviewed_control_never_gets_admission_receipt(self):
        value = dict(self.fixture.control, credential='unreviewed')
        self.inputs['readiness_control'] = json.dumps(value)
        self.save_event()
        with self.assertRaises(ValueError):
            transport.seed()
        self.assertFalse((self.controls / 'seed.json').exists())
        self.assertTrue((self.controls / 'control.json').exists())

    def test_seed_is_single_use_and_links_refuse(self):
        transport.seed()
        with self.assertRaises(FileExistsError):
            transport.seed()
        target = self.controls / 'review.json'
        target.rename(self.controls / 'retained.json')
        target.symlink_to(self.controls / 'retained.json')
        with self.assertRaises(ValueError):
            transport.seeded()

    def test_acquisition_selects_one_member_without_archive_extraction(self):
        content = b'b' * 636344
        archive = self.root / 'inputs.tar'
        with tarfile.open(archive, 'w') as bundle:
            for name, data in ((transport.BASE_MEMBER, content),
                               ('../../unexpected.FCStd', b'not extracted')):
                member = tarfile.TarInfo(name)
                member.size = len(data)
                bundle.addfile(member, io.BytesIO(data))
        identity = {'bytes': archive.stat().st_size,
                    'sha256': transport.digest(archive)}
        target = self.root / 'base.FCStd'
        with patch.object(transport, 'ASSET', identity), patch.object(
                transport.readiness, 'BASE_SHA256',
                hashlib.sha256(content).hexdigest()):
            transport.extract_base(archive, target)
            self.assertEqual(target.read_bytes(), content)
            with self.assertRaises(FileExistsError):
                transport.extract_base(archive, target)
        self.assertEqual({p.name for p in self.root.iterdir()},
                         {'source', 'decisions', 'event.json',
                          'inputs.tar', 'base.FCStd'})

    def test_changed_archive_and_duplicate_or_linked_base_refuse(self):
        archive = self.root / 'inputs.tar'
        for linked in (False, True):
            with self.subTest(linked=linked):
                with tarfile.open(archive, 'w') as bundle:
                    for _ in range(1 if linked else 2):
                        member = tarfile.TarInfo(transport.BASE_MEMBER)
                        member.size = 636344
                        if linked:
                            member.type = tarfile.SYMTYPE
                            member.linkname = '/private.FCStd'
                        bundle.addfile(member, io.BytesIO(b'b' * 636344))
                identity = {'bytes': archive.stat().st_size,
                            'sha256': transport.digest(archive)}
                with patch.object(transport, 'ASSET', identity), \
                        self.assertRaises(ValueError):
                    transport.extract_base(archive, self.root / 'refused.FCStd')
                self.assertFalse((self.root / 'refused.FCStd').exists())
        with self.assertRaises(ValueError):
            transport.extract_base(archive, self.root / 'refused.FCStd')

    def failed_acquisition(self):
        """Inject a download refusal after real offline control admission."""
        transport.seed()
        controller = transport.readiness
        with patch.object(controller, 'ROOT', self.fixture.source), \
                patch.object(controller.pilot, '_command',
                             side_effect=lambda *args: (
                                 'a' * 40 if args == (
                                     'git', 'rev-parse', 'HEAD') else '')):
            controller.prepare(self.controls / 'control.json', self.controls)
            save(self.work / 'evidence/installer-result.json', {
                'status': 'PASS', 'cleanup': True})
            logs = self.root / 'compatibility-readiness-logs'
            logs.mkdir()
            with (logs / 'acquire.log').open('w') as stream, \
                    redirect_stdout(stream), hosted_tracebacks(), \
                    patch.object(transport.native, 'download_asset',
                                 side_effect=ValueError(
                                     'Injected approved asset refusal')):
                status = transport.main(['acquire'])
        self.assertEqual(status, 1)
        self.assertFalse((self.controls / 'acquisition.json').exists())
        self.assertFalse((self.work / 'assessment-manifest.json').exists())
        os.environ['L1_ACQUIRE'] = 'failure'
        return {
            'logs/acquire.log': (logs / 'acquire.log').read_bytes(),
            'original-diagnostics/acquire.txt': (
                self.root / 'compatibility-readiness-private/acquire.txt'
            ).read_bytes(),
        }

    def test_acquisition_failure_survives_both_archive_failures(self):
        originals = self.failed_acquisition()
        # An unrelated collector refusal must not hide these closed originals.
        (self.work / 'evidence/unlisted.txt').write_text('not approved')
        with hosted_tracebacks(), redirect_stdout(io.StringIO()):
            self.assertEqual(transport.main(['archive']), 1)
            self.assertEqual(transport.main(['publish']), 1)
        for kind in ('primary', 'final'):
            self.assertFalse((self.root / (
                'compatibility-readiness-' + kind + '.tar')).exists())
        transport.acquisition_diagnostic()
        artifact = self.root / 'compatibility-readiness-acquisition-failure.tar'
        with tarfile.open(artifact) as bundle:
            self.assertEqual(set(bundle.getnames()), {
                *originals, 'transport/acquisition-failure.json'})
            for name, raw in originals.items():
                self.assertEqual(bundle.extractfile(name).read(), raw)
            record = json.loads(bundle.extractfile(
                'transport/acquisition-failure.json').read())
        self.assertEqual(record['acquisition_outcome'], 'failure')
        self.assertEqual(record['source_commit'], 'a' * 40)
        self.assertEqual(record['run_id'], '123')
        self.assertEqual(record['run_attempt'], 1)
        for name, raw in originals.items():
            self.assertEqual(record['originals'][name], {
                'status': 'PRESERVED', 'bytes': len(raw),
                'sha256': hashlib.sha256(raw).hexdigest()})
        self.assertEqual(os.environ['L1_ACQUIRE'], 'failure')
        self.assertFalse((self.root /
                          'compatibility-readiness-completion.json').exists())

    def diagnostic_input(self, raw=b'Original acquisition failure\n'):
        """Admit controls and one closed synthetic log without acquisition."""
        transport.seed()
        os.environ['L1_ACQUIRE'] = 'failure'
        path = self.root / 'compatibility-readiness-logs/acquire.log'
        path.parent.mkdir()
        path.write_bytes(raw)
        return path

    def diagnostic_members(self):
        artifact = self.root / 'compatibility-readiness-acquisition-failure.tar'
        with tarfile.open(artifact) as bundle:
            members = {name: bundle.extractfile(name).read()
                       for name in bundle.getnames()}
        record = json.loads(members.pop('transport/acquisition-failure.json'))
        self.assertEqual(record['status'], 'FAIL')
        self.assertEqual(record['acquisition_outcome'], 'failure')
        self.assertEqual(record['control_sha256'],
                         transport.digest(self.controls / 'control.json'))
        return artifact, members, record

    def test_acquisition_second_command_failure_preserves_only_raw_log(self):
        raw = (b'Traceback (most recent call last):\n'
               b'  File "/home/runner/work/tracktemplate/tools/'
               b'hosted_compatibility_readiness.py", line 1, in acquire\n'
               b'ValueError: Injected assessment copy refusal\n')
        path = self.diagnostic_input(raw)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(transport.main(['acquire-diagnostic']), 0)
        _, members, record = self.diagnostic_members()
        self.assertEqual(members, {'logs/acquire.log': raw})
        self.assertEqual(record['originals']['original-diagnostics/acquire.txt'],
                         {'status': 'MISSING'})
        self.assertEqual(record['originals']['logs/acquire.log'], {
            'status': 'PRESERVED', 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()})
        self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(stdout.getvalue(),
                         'COMPATIBILITY_READINESS_ACQUISITION_'
                         'DIAGNOSTIC_PRESERVED\n')
        self.assertNotIn('Injected assessment', stdout.getvalue())

    def test_acquisition_unsafe_or_invalid_bytes_are_withheld_unchanged(self):
        path = self.diagnostic_input()
        cases = (b'/home/private-owner/operator.FCStd\n',
                 b'Authorization: excluded-credential\n', b'\xff\x00')
        for index, raw in enumerate(cases):
            with self.subTest(index=index):
                path.write_bytes(raw)
                transport.acquisition_diagnostic()
                artifact, members, record = self.diagnostic_members()
                self.assertEqual(members, {})
                self.assertEqual(record['originals'], {
                    'logs/acquire.log': {'status': 'WITHHELD'},
                    'original-diagnostics/acquire.txt': {'status': 'MISSING'},
                })
                self.assertNotIn(raw, artifact.read_bytes())
                self.assertEqual(path.read_bytes(), raw)
                artifact.rename(self.root / f'withheld-{index}.tar')

    def test_acquisition_missing_originals_are_not_reconstructed(self):
        path = self.diagnostic_input()
        path.rename(path.with_name('retained-original.log'))
        transport.acquisition_diagnostic()
        _, members, record = self.diagnostic_members()
        self.assertEqual(members, {})
        self.assertEqual(record['originals'], {
            'logs/acquire.log': {'status': 'MISSING'},
            'original-diagnostics/acquire.txt': {'status': 'MISSING'},
        })
        self.assertFalse(path.exists())

    def test_acquisition_link_and_foreign_owner_are_withheld(self):
        path = self.diagnostic_input()
        retained = path.with_name('retained-original.log')
        path.rename(retained)
        path.symlink_to(retained)
        transport.acquisition_diagnostic()
        artifact, members, record = self.diagnostic_members()
        self.assertEqual(members, {})
        self.assertEqual(record['originals']['logs/acquire.log'],
                         {'status': 'WITHHELD'})
        self.assertTrue(path.is_symlink())
        self.assertEqual(retained.read_bytes(), b'Original acquisition failure\n')
        artifact.rename(self.root / 'linked-original.tar')
        # Keep the symlink as evidence; simulate ownership only on a fresh file.
        path.rename(path.with_name('retained-link'))
        path.write_bytes(b'Foreign-owned original\n')
        original_stat = Path.stat

        def foreign_stat(candidate, *args, **kwargs):
            result = original_stat(candidate, *args, **kwargs)
            if candidate == path:
                fields = list(result)
                fields[4] = os.getuid() + 1
                return os.stat_result(fields)
            return result

        with patch.object(Path, 'stat', foreign_stat):
            transport.acquisition_diagnostic()
        _, members, record = self.diagnostic_members()
        self.assertEqual(members, {})
        self.assertEqual(record['originals']['logs/acquire.log'],
                         {'status': 'WITHHELD'})
        self.assertEqual(path.read_bytes(), b'Foreign-owned original\n')

    def test_acquisition_oversize_original_is_withheld_without_truncation(self):
        raw = b'x' * (transport.MAX_FILE + 1)
        path = self.diagnostic_input(raw)
        transport.acquisition_diagnostic()
        artifact, members, record = self.diagnostic_members()
        self.assertEqual(members, {})
        self.assertEqual(record['originals']['logs/acquire.log'],
                         {'status': 'WITHHELD'})
        self.assertEqual(path.read_bytes(), raw)
        self.assertLess(artifact.stat().st_size, len(raw))

    def test_acquisition_diagnostic_requires_failure_and_bound_source(self):
        self.diagnostic_input()
        artifact = self.root / 'compatibility-readiness-acquisition-failure.tar'
        for outcome in ('success', 'skipped', 'cancelled', ''):
            with self.subTest(outcome=outcome):
                os.environ['L1_ACQUIRE'] = outcome
                with redirect_stdout(io.StringIO()) as stdout:
                    self.assertEqual(transport.main(['acquire-diagnostic']), 1)
                self.assertEqual(stdout.getvalue(),
                                 'COMPATIBILITY_READINESS_ACQUISITION_'
                                 'DIAGNOSTIC_REFUSED\n')
                self.assertFalse(artifact.exists())
        os.environ['L1_ACQUIRE'] = 'failure'
        source = self.fixture.source / transport.readiness.SUITE
        source.write_text('changed after independent review')
        with redirect_stdout(io.StringIO()):
            self.assertEqual(transport.main(['acquire-diagnostic']), 1)
        self.assertFalse(artifact.exists())

    def test_acquisition_diagnostic_never_overwrites_existing_artifact(self):
        path = self.diagnostic_input()
        transport.acquisition_diagnostic()
        artifact, _, _ = self.diagnostic_members()
        original = artifact.read_bytes()
        path.write_bytes(b'Changed later original\n')
        with redirect_stdout(io.StringIO()):
            self.assertEqual(transport.main(['acquire-diagnostic']), 1)
        self.assertEqual(artifact.read_bytes(), original)
        self.assertEqual(path.read_bytes(), b'Changed later original\n')

    def test_acquisition_workflow_keeps_shell_failure_and_independent_upload(self):
        workflow = (ROOT / '.github/workflows/native-geometry-pilot.yml').read_text()
        job = workflow.split('  compatibility-readiness:\n', 1)[1].split(
            '\n  compatibility-matrix:', 1)[0]
        block = job.split('        id: acquire\n', 1)[1].split(
            '\n      - name:', 1)[0]
        commands = block.split('        run: |\n', 1)[1]
        commands = '\n'.join(line[10:] for line in commands.splitlines())
        stub = '''python3() {
  if [[ "$1" == tools/compatibility_readiness_transport.py ]]; then
    printf first > "$RUNNER_TEMP/first-ran"
    printf 'FIRST_COMMAND_OUTPUT\\n'
    return "$FIRST_EXIT"
  fi
  printf second > "$RUNNER_TEMP/second-ran"
  printf 'SECOND_COMMAND_OUTPUT\\n'
  return "$SECOND_EXIT"
}
'''
        logs = self.root / 'compatibility-readiness-logs'
        logs.mkdir()
        for first, second, expected in ((17, 0, 17), (0, 23, 23)):
            with self.subTest(first=first, second=second):
                completed = subprocess.run(
                    ['/bin/bash', '--noprofile', '--norc', '-e', '-o',
                     'pipefail', '-c', stub + commands],
                    env=dict(self.environment, FIRST_EXIT=str(first),
                             SECOND_EXIT=str(second)),
                    capture_output=True, check=False, timeout=5)
                self.assertEqual(completed.returncode, expected)
                self.assertEqual(completed.stdout, b'')
                self.assertEqual(completed.stderr, b'')
                self.assertTrue((self.root / 'first-ran').exists())
                self.assertEqual((self.root / 'second-ran').exists(), first == 0)
                expected_log = b'FIRST_COMMAND_OUTPUT\n'
                if first == 0:
                    expected_log += b'SECOND_COMMAND_OUTPUT\n'
                self.assertEqual((logs / 'acquire.log').read_bytes(), expected_log)
        capture = job.split('        id: acquire_diagnostic\n', 1)[1].split(
            '\n      - name:', 1)[0]
        upload = job.split('        id: acquire_diagnostic_upload\n', 1)[1].split(
            '\n      - name:', 1)[0]
        self.assertIn("if: always() && steps.acquire.outcome == 'failure'", capture)
        self.assertIn('L1_ACQUIRE: ${{ steps.acquire.outcome }}', capture)
        self.assertIn('compatibility_readiness_transport.py acquire-diagnostic',
                      capture)
        self.assertIn("if: always() && steps.acquire.outcome == 'failure' && "
                      "steps.acquire_diagnostic.outcome == 'success'", upload)
        self.assertIn('retention-days: 30', upload)
        self.assertIn('if-no-files-found: error', upload)
        self.assertIn('path: ${{ runner.temp }}/'
                      'compatibility-readiness-acquisition-failure.tar', upload)
        for step in (capture, upload):
            self.assertNotIn('steps.archive', step)
            self.assertNotIn('steps.publish', step)
            self.assertNotIn('continue-on-error', step)
        self.assertLess(job.index('id: acquire_diagnostic_upload'),
                        job.index('id: archive\n'))

    def test_no_launch_failure_has_no_process_side_effect(self):
        self.outcome()
        with patch.object(transport.native, 'finalize') as native_cleanup, \
                patch.object(transport, 'installer_cleanup') as installer:
            result = transport.finalize()
        self.assertTrue(result['cleanup'])
        self.assertTrue(result['never_started'])
        native_cleanup.assert_not_called()
        installer.assert_not_called()
        self.assertEqual(transport.archive(), 'FAIL')
        with tarfile.open(self.root / 'compatibility-readiness-primary.tar') as bundle:
            self.assertEqual(set(bundle.getnames()), {
                'transport/finalization.json', 'transport/manifest.json'})

    def test_outcomes_cannot_claim_absent_launched_work(self):
        self.outcome(prepare='success', install='success', run='failure')
        with self.assertRaises(ValueError):
            transport.finalize()

    def test_all_cleanup_boundaries_run_after_first_failure(self):
        (self.work / 'evidence').mkdir(parents=True)
        self.outcome(prepare='success', install='failure')
        with patch.object(transport, 'installer_cleanup',
                          side_effect=ValueError('original failure')), \
                patch.object(transport, '_runtime_cleanup',
                             return_value={'cleanup': True}) as runtime, \
                patch.object(transport.readiness.gui, 'display_cleanup',
                             return_value={'cleanup': True}) as display:
            result = transport.finalize()
        runtime.assert_called_once()
        display.assert_called_once()
        self.assertFalse(result['cleanup'])
        self.assertEqual(result['errors'], ['installer-cleanup-unproved'])

    def test_cleanup_original_exception_is_retained_privately(self):
        (self.work / 'evidence').mkdir(parents=True)
        self.outcome(prepare='success', install='failure')
        with patch.object(transport, 'installer_cleanup',
                          side_effect=ValueError('ORIGINAL_PRIVATE_CAUSE')), \
                patch.object(transport, '_runtime_cleanup',
                             return_value={'cleanup': True}), \
                patch.object(transport.readiness.gui, 'display_cleanup',
                             return_value={'cleanup': True}):
            transport.finalize()
        path = self.root / 'compatibility-readiness-private/finalize-installer.txt'
        self.assertIn('ValueError: ORIGINAL_PRIVATE_CAUSE', path.read_text())
        summary = (self.root / 'compatibility-readiness-finalization.json').read_text()
        self.assertNotIn('ORIGINAL_PRIVATE_CAUSE', summary)

    def test_skipped_runtime_with_launch_state_refuses(self):
        (self.work / 'evidence/guard').mkdir(parents=True)
        with self.assertRaises(ValueError):
            transport._runtime_cleanup(self.work, {'L1_RUN': 'skipped'})

    def test_installer_cleanup_checks_exact_adapted_module(self):
        (self.work / 'evidence').mkdir(parents=True)
        save(self.work / 'evidence/installer-intent.json', {})
        (self.work / 'readiness_installer.py').write_text('changed')
        with patch.object(transport, 'ROOT', ROOT), self.assertRaises(ValueError):
            transport.installer_cleanup(self.work)

    def test_allowlist_refuses_unknown_documents_links_and_credentials(self):
        directory = self.root / 'evidence'
        directory.mkdir()
        path = directory / 'guard.json'
        path.write_text('{}')
        self.assertEqual(transport._inventory(directory, {'guard.json'}),
                         {'guard.json': b'{}'})
        document = directory / 'private.FCStd'
        document.write_bytes(b'document')
        with self.assertRaises(ValueError):
            transport._inventory(directory, {'guard.json'})
        self.assertEqual(document.read_bytes(), b'document')
        for value in ('/home/operator/private.FCStd',
                      'Authorization: secret', 'github_pat_secret'):
            path.write_text(value)
            with self.assertRaises(ValueError):
                transport.public_bytes(path)
            self.assertEqual(path.read_text(), value)
        link = directory / 'linked'
        link.symlink_to(path)
        with self.assertRaises(ValueError):
            transport.public_bytes(link)

    def test_refusal_traceback_survives_without_editing_original_bytes(self):
        path = self.root / 'unsafe.txt'
        for index, value in enumerate((
                '/home/operator/private.FCStd', '/Users/operator/private',
                '/root/private', 'Authorization: secret', 'github_pat_secret')):
            with self.subTest(value=value), hosted_tracebacks():
                path.write_text(value)
                receipt = self.root / ('original-' + str(index) + '.txt')
                original = capture_refusal(path, receipt)
                self.assertEqual(transport.public_bytes(receipt), original)
                self.assertEqual(receipt.read_bytes(), original)
                self.assertEqual(path.read_text(), value)
                self.assertNotIn(value.encode(), original)
                self.assertIn(b'ValueError:', original)

    def test_archive_is_exact_single_use_and_does_not_follow_paths(self):
        path = self.root / 'transport.tar'
        identity = transport._tar(path, {'guard/result.json': b'{}'})
        self.assertEqual(identity['sha256'], transport.digest(path))
        with tarfile.open(path) as bundle:
            self.assertEqual(bundle.getnames(), ['guard/result.json'])
        with self.assertRaises(FileExistsError):
            transport._tar(path, {'guard/result.json': b'changed'})
        with self.assertRaises(ValueError):
            transport._tar(self.root / 'unsafe.tar', {'../private': b'no'})

    def test_readback_requires_both_actions_and_exact_bytes(self):
        source = self.root / 'compatibility-readiness-primary.tar'
        source.write_bytes(b'original')
        target = self.root / 'compatibility-readiness-primary-readback' / source.name
        target.parent.mkdir()
        target.write_bytes(b'original')
        os.environ.update(L1_PRIMARY_UPLOAD='success',
                          L1_PRIMARY_DOWNLOAD='success', L1_PRIMARY_ID='123')
        self.assertEqual(transport._readback(self.root, 'primary')['asset_id'], 123)
        target.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            transport._readback(self.root, 'primary')
        target.write_bytes(b'original')
        os.environ['L1_PRIMARY_UPLOAD'] = 'failure'
        with self.assertRaises(ValueError):
            transport._readback(self.root, 'primary')

    def test_failed_primary_readback_still_seals_final_failure_receipt(self):
        self.outcome()
        transport.finalize()
        transport.archive()
        result = transport.publish()
        self.assertEqual(result['status'], 'FAIL')
        self.assertTrue((self.root / 'compatibility-readiness-final.tar').is_file())
        self.assertIsNone(result['primary'])

    def test_missing_finalization_still_seals_truthful_final_failure(self):
        result = transport.publish()
        self.assertEqual(result['status'], 'FAIL')
        path = self.root / 'compatibility-readiness-final.tar'
        self.assertTrue(path.is_file())
        with tarfile.open(path) as bundle:
            self.assertEqual(bundle.getnames(), ['transport/publication.json'])

    def test_self_consistent_payload_hashes_cannot_replace_typed_seal(self):
        self.prepared_payload()
        path = self.work / 'public-readiness/gui/readiness/result.json'
        save(path, {'status': 'PASS'})
        save(self.work / 'payload/gui/readiness/result.json', {'status': 'PASS'})
        save(self.work / 'readiness-payload-inventory.json', {
            'gui/readiness/result.json': {
                'bytes': path.stat().st_size, 'sha256': transport.digest(path)}})
        with hosted_tracebacks():
            self.assertEqual(transport.archive(), 'FAIL')
        original = (self.root /
                    'compatibility-readiness-private/archive-payload.txt').read_bytes()
        self.assertIn(b'EvidenceError: stored result differs from projection', original)
        with tarfile.open(self.root / 'compatibility-readiness-primary.tar') as bundle:
            self.assertFalse(any(name.startswith('payload/') for name in bundle.getnames()))
            self.assertEqual(bundle.extractfile(
                'original-diagnostics/archive-payload.txt').read(), original)
            manifest = json.loads(bundle.extractfile('transport/manifest.json').read())
            self.assertEqual(manifest['status'], 'FAIL')
            self.assertIs(manifest['payload_sealed'], False)

    def test_final_fallback_preserves_original_seal_run_and_guard_diagnostics(self):
        self.prepared_payload()
        logs = self.root / 'compatibility-readiness-logs'
        expected = {
            'logs/seal.log': b'Traceback (most recent call last):\nValueError: original seal cause\n',
            'logs/run.log': b'ORIGINAL_RUN_SENTINEL\n',
            'operational/guard/stdout': b'ORIGINAL_GUARD_STDOUT\n',
            'operational/guard/stderr': b'ORIGINAL_GUARD_STDERR\n',
        }
        for name, raw in expected.items():
            path = (logs / Path(name).name if name.startswith('logs/')
                    else self.work / 'evidence' / name.removeprefix('operational/'))
            path.write_bytes(raw)
        # Primary creation/readback was unavailable. Final transport must
        # preserve originals without attempting another payload seal.
        with hosted_tracebacks():
            publication = transport.publish()
        self.assertEqual(publication['status'], 'FAIL')
        self.assertIsNone(publication['primary'])
        with tarfile.open(self.root / 'compatibility-readiness-final.tar') as bundle:
            for name, raw in expected.items():
                self.assertEqual(bundle.extractfile(name).read(), raw)
            self.assertFalse(any(name.startswith('payload/') for name in bundle.getnames()))
        self.assertFalse((self.work / 'transport-readiness').exists())

    def test_payload_failure_preserves_operational_originals_in_both_archives(self):
        self.prepared_payload()
        save(self.work / 'public-readiness/gui/readiness/result.json', {'status': 'PASS'})
        log = self.root / 'compatibility-readiness-logs/seal.log'
        original = b'ValueError: original failed seal\n'
        log.write_bytes(original)
        with hosted_tracebacks():
            self.assertEqual(transport.archive(), 'FAIL')
            self.readback('primary', 123)
            transport.publish()
        for kind in ('primary', 'final'):
            with tarfile.open(self.root / ('compatibility-readiness-' + kind + '.tar')) as bundle:
                self.assertEqual(bundle.extractfile('logs/seal.log').read(), original)
                self.assertIn('original-diagnostics/archive-payload.txt', bundle.getnames())
                self.assertFalse(any(name.startswith('payload/') for name in bundle.getnames()))
        self.readback('final', 456)
        self.assertEqual(transport.complete(), 'FAIL')

    def test_rejected_safe_opengl_version_survives_both_readbacks(self):
        self.prepared_payload(seal=False)
        controller = transport.readiness
        evidence_error = output_fixtures.output.EvidenceError
        observation_path = self.work / 'readiness-observation.json'
        observation = json.loads(observation_path.read_bytes())
        log = self.root / 'compatibility-readiness-logs/seal.log'
        for version in (
            '4.5 Mesa 25.2.8',
            '4.5 Mesa 25.2.8 (git-0123456789)',
        ):
            observation['renderer']['version'] = version
            save(observation_path, observation)
            before = observation_path.read_bytes()
            with self.subTest(version=version), hosted_tracebacks():
                try:
                    controller.seal(self.work)
                except evidence_error as error:
                    self.assertEqual(str(error), 'renderer version differs')
                    original = ''.join(traceback.format_exception(
                        type(error), error, error.__traceback__.tb_next
                    )).encode()
                else:
                    self.fail('Expected renderer version refusal')
                self.assertEqual(original.count(
                    f'Readiness rejected GL_VERSION: {version}\n'.encode()), 1)
                self.assertEqual(observation_path.read_bytes(), before)
                self.assertFalse((self.work / 'public-readiness').exists())
                self.assertFalse((self.work /
                                  'payload/gui/readiness/result.json').exists())
        log.write_bytes(original)
        self.assertEqual(transport.archive(), 'FAIL')
        self.readback('primary', 123)
        self.assertEqual(transport.publish()['status'], 'PASS')
        for kind in ('primary', 'final'):
            path = self.root / ('compatibility-readiness-' + kind + '.tar')
            with tarfile.open(path) as bundle:
                self.assertEqual(bundle.extractfile('logs/seal.log').read(),
                                 original)
                self.assertFalse(any(name.startswith('payload/')
                                     for name in bundle.getnames()))
        self.readback('final', 456)
        self.assertEqual(transport.complete(), 'FAIL')

    def test_rejected_opengl_version_withholds_unapproved_values(self):
        self.prepared_payload(seal=False)
        controller = transport.readiness
        evidence_error = output_fixtures.output.EvidenceError
        path = self.work / 'readiness-observation.json'
        observation = json.loads(path.read_bytes())
        renderer = observation['renderer']
        prefix = '4.5 (Compatibility Profile) Mesa 25.2.8'
        for version in (
            None, prefix + '\nextra', prefix + '\x1b[31m',
            prefix + ' /home/operator/private', prefix + ' token=secret',
            prefix + ' (git-' + 'a' * 65 + ')',
            prefix.replace('25.2.8', '２５.２.８'),
        ):
            with self.subTest(version=version):
                renderer['version'] = version
                save(path, observation)
                with self.assertRaisesRegex(evidence_error,
                                            '^renderer version differs$') as result:
                    controller.seal(self.work)
                self.assertEqual(getattr(result.exception, '__notes__', []),
                                 ['Readiness rejected GL_VERSION: withheld'])
        renderer.update(version='4.5 Mesa 25.2.8', vendor='unsupported')
        save(path, observation)
        with self.assertRaisesRegex(evidence_error,
                                    '^renderer identity differs$') as result:
            controller.seal(self.work)
        self.assertFalse(getattr(result.exception, '__notes__', []))

    def test_missing_mandatory_original_prevents_completeness_and_pass(self):
        self.prepared_payload()
        path = self.work / 'evidence/guard/stderr'
        path.rename(self.work / 'retained-original-stderr')
        self.assertEqual(transport.archive(), 'FAIL')
        record = json.loads((self.root / 'compatibility-readiness-archive.json').read_text())
        self.assertIs(record['manifest']['original_diagnostic_preservation_complete'], False)
        self.assertIn('operational/guard/stderr', record['manifest']['missing_mandatory_evidence'])

    def test_started_failed_installer_missing_result_is_incomplete(self):
        self.prepared_payload()
        contents, summary, admitted = transport._operational_contents(
            self.root, self.work)
        contents.pop('operational/installer-result.json')
        summary['workflow_outcomes'].update(
            L1_INSTALL='failure', L1_ACQUIRE='skipped', L1_RUN='skipped')
        preserved, missing = transport._preservation(contents, summary, admitted)
        self.assertIs(preserved, False)
        self.assertIn('operational/installer-result.json', missing)

    def test_fallback_still_refuses_unsafe_original_without_modifying_it(self):
        self.prepared_payload()
        path = self.root / 'compatibility-readiness-logs/seal.log'
        raw = b'Authorization: excluded-credential\n'
        path.write_bytes(raw)
        with hosted_tracebacks(), self.assertRaisesRegex(
                ValueError, '^Credential-like operational evidence$'):
            transport.publish()
        self.assertEqual(path.read_bytes(), raw)
        self.assertFalse((self.root / 'compatibility-readiness-final.tar').exists())

    def test_active_logs_are_not_read_but_closed_archive_log_is_preserved(self):
        self.prepared_payload()
        logs = self.root / 'compatibility-readiness-logs'
        active = logs / 'archive.log'
        active.write_bytes(b'Authorization: active-not-an-original\n')
        self.assertEqual(transport.archive(), 'PASS')
        with tarfile.open(self.root / 'compatibility-readiness-primary.tar') as bundle:
            self.assertNotIn('logs/archive.log', bundle.getnames())
        closed = b'ORIGINAL_ARCHIVE_LOG\n'
        active.write_bytes(closed)
        (logs / 'publish.log').write_bytes(b'Authorization: active-not-an-original\n')
        self.readback('primary', 123)
        self.assertEqual(transport.publish()['status'], 'PASS')
        with tarfile.open(self.root / 'compatibility-readiness-final.tar') as bundle:
            self.assertEqual(bundle.extractfile('logs/archive.log').read(), closed)
            self.assertNotIn('logs/publish.log', bundle.getnames())

    def test_supported_shutdown_control_survives_exact_archive(self):
        self.prepared_payload()
        request = {
            'schema_version': 1, 'supervisor_pid': 123,
            'supervisor_start': '456',
            'scope': 'app-flatpak-org.freecad.FreeCAD-123.scope',
            'invocation': 'a' * 32, 'lease_id': 'b' * 32,
            'client_exit': 1, 'signal': 'SIGTERM', 'signal_sent': True,
        }
        path = self.work / 'evidence/guard/shutdown-request.json'
        save(path, request)
        original = path.read_bytes()
        finalization = self.root / 'compatibility-readiness-finalization.json'
        result = json.loads(finalization.read_text())
        result['workflow_outcomes']['L1_RUN'] = 'failure'
        save(finalization, result)
        self.assertEqual(transport.archive(), 'FAIL')
        with tarfile.open(self.root / 'compatibility-readiness-primary.tar') as bundle:
            self.assertEqual(bundle.extractfile(
                'operational/guard/shutdown-request.json').read(), original)
        self.assertEqual(path.read_bytes(), original)
        save(self.work / 'evidence/guard/unreviewed-stop.json', request)
        with self.assertRaisesRegex(ValueError, '^Unlisted operational evidence$'):
            transport._inventory(self.work / 'evidence', transport.EVIDENCE)

    def test_composed_readiness_seal_and_both_readbacks_complete(self):
        self.prepared_payload()
        self.assertEqual(transport.archive(), 'PASS')
        primary = self.root / 'compatibility-readiness-primary.tar'
        with tarfile.open(primary) as bundle:
            self.assertEqual(bundle.extractfile(
                'payload/gui/readiness/readiness-source.png').read(),
                output_fixtures.png())
            record = json.loads(bundle.extractfile(
                'payload/gui/readiness/result.json').read())
            self.assertEqual(record['status'], 'PASS')
            self.assertEqual(record['assessment_entry_sha256'],
                             transport.digest(ROOT / transport.readiness.SUITE))
            self.assertFalse(any(name.endswith('.FCStd') for name in bundle.getnames()))
        self.readback('primary', 123)
        self.assertEqual(transport.publish()['status'], 'PASS')
        self.readback('final', 456)
        self.assertEqual(transport.complete(), 'PASS')
        completion = json.loads((self.root /
                                 'compatibility-readiness-completion.json').read_text())
        self.assertEqual(completion['primary_readback']['sha256'], transport.digest(primary))
        self.assertEqual(completion['final_readback']['asset_id'], 456)
        self.assertIs(completion['independent_preservation_required'], True)
        for name in ('runtime_admission', 'matrix_dispatch', 'zy_execution'):
            self.assertIs(completion[name], False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
