#!/usr/bin/env python3
"""Offline tests for finite readiness transport and failed-stage preservation."""

import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile
from types import SimpleNamespace
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

    def prepared_payload(self):
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
        controller.seal(self.work)
        save(self.root / 'compatibility-readiness-finalization.json', {
            'cleanup': True,
            'workflow_outcomes': {name: 'success' for name in transport.OUTCOMES}})

    def readback(self, kind, identity):
        source = self.root / ('compatibility-readiness-' + kind + '.tar')
        destination = self.root / ('compatibility-readiness-' + kind + '-readback')
        destination.mkdir()
        (destination / source.name).write_bytes(source.read_bytes())
        prefix = 'L1_PRIMARY' if kind == 'primary' else 'L1_FINAL'
        os.environ.update({prefix + '_UPLOAD': 'success',
                           prefix + '_DOWNLOAD': 'success',
                           prefix + '_ID': str(identity)})

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
        with self.assertRaisesRegex(
                ValueError, '^stored result differs from projection$'):
            transport.archive()
        self.assertFalse((self.root / 'compatibility-readiness-primary.tar').exists())

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
