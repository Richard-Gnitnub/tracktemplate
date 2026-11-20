#!/usr/bin/env python3
"""Offline refusal, containment-binding and source-copy readiness checks."""

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import hosted_compatibility_readiness as controller  # noqa: E402

spec = importlib.util.spec_from_file_location(
    'hosted_compatibility_readiness_suite', ROOT / controller.SUITE)
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)


def save(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record))


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.decisions = self.root / 'decisions'
        self.source.mkdir()
        self.decisions.mkdir()
        self.environment = {
            'GITHUB_ACTIONS': 'true',
            'GITHUB_REPOSITORY': 'Richard-Gnitnub/tracktemplate',
            'GITHUB_EVENT_NAME': 'workflow_dispatch',
            'RUNNER_ENVIRONMENT': 'github-hosted', 'GITHUB_RUN_ATTEMPT': '1',
            'RUNNER_OS': 'Linux', 'RUNNER_ARCH': 'X64',
            'GITHUB_SHA': 'a' * 40, 'GITHUB_RUN_ID': '123',
        }
        pins = {}
        for name in controller.CONTROL_FILES:
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(name)
            pins[name] = controller.digest(target)
        self.capsule_pins = {}
        for name in controller.CAPSULE_FILES:
            target = self.decisions / name
            target.write_text(name)
            self.capsule_pins[name] = controller.digest(target)
        default = self.source / 'reference/contracts/phase1-compatibility.json'
        save(default, {})
        self.default_hash = controller.digest(default)
        self.control = {
            'schema_version': 1, 'stage': 'readiness',
            'source_base_commit': controller.BASE_COMMIT,
            'owner_decision': 'D-P9-023',
            'owner_decision_sha256': controller.DECISION_SHA256,
            'output_scope_sha256': controller.SCOPE_SHA256,
            'app_commit': controller.APP_COMMIT,
            'runtime_commit': controller.RUNTIME_COMMIT,
            'execution_authorized': True, 'independent_review': 'PASS',
            'installer_seconds': 540,
            'freecad_limits': vars(controller.LIMITS),
            'display_limits': vars(
                controller.guard.ValidationLimits(256, 190, 25, 16)),
            'reserve_mib': 8192, 'runtime_admission': False,
            'matrix_dispatch': False, 'zy_execution': False,
            'source_commit': 'a' * 40, 'source_files': pins,
        }
        for key in ('review', 'recovery'):
            record = {
                'status': 'PASS', 'source_commit': 'a' * 40,
                'source_files': pins,
            }
            record.update({
                'stage': 'readiness',
                'output_scope_sha256': controller.SCOPE_SHA256,
                'independent': True,
            } if key == 'review' else {'independent_preservation': True})
            path = self.decisions / (key + '.json')
            save(path, record)
            self.control[key] = {
                'path': path.name, 'sha256': controller.digest(path)}

    def validate(self, control=None, environment=None):
        with patch.object(controller, 'CAPSULE_FILES', self.capsule_pins), \
                patch.object(controller, 'DEFAULT_SHA256', self.default_hash):
            return controller.validate_control(
                control or self.control, environment or self.environment,
                self.source, self.decisions)

    def test_reviewed_source_and_prerequisites_accept(self):
        self.validate()

    def test_unknown_control_or_receipt_fields_refuse(self):
        with self.subTest(key='control'), self.assertRaises(ValueError):
            self.validate(dict(self.control, private_data='not-public'))
        for key in ('review', 'recovery'):
            with self.subTest(key=key):
                path = self.decisions / (key + '.json')
                original = path.read_text()
                record = json.loads(original)
                record['private_data'] = 'not-public'
                save(path, record)
                changed = copy.deepcopy(self.control)
                changed[key]['sha256'] = controller.digest(path)
                with self.assertRaises(ValueError):
                    self.validate(changed)
                path.write_text(original)

    def test_unknown_binding_and_nonexact_scalar_types_refuse(self):
        variants = []
        for key, value in [('schema_version', True), ('installer_seconds', 540.0),
                           ('source_commit', 123)]:
            variants.append(dict(self.control, **{key: value}))
        changed = copy.deepcopy(self.control)
        changed['freecad_limits']['memory_max_mib'] = 4096.0
        variants.append(changed)
        changed = copy.deepcopy(self.control)
        changed['review']['private_data'] = 'not-public'
        variants.append(changed)
        changed = copy.deepcopy(self.control)
        changed['review']['path'] = 'other.json'
        variants.append(changed)
        for changed in variants:
            with self.subTest(control=changed), self.assertRaises(ValueError):
                self.validate(changed)

    def test_local_execution_rerun_and_debug_refuse(self):
        for key, value in [('GITHUB_ACTIONS', 'false'),
                           ('GITHUB_RUN_ATTEMPT', '2'),
                           ('RUNNER_ENVIRONMENT', 'self-hosted'),
                           ('ACTIONS_STEP_DEBUG', 'true')]:
            changed = dict(self.environment, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(environment=changed)

    def test_runtime_limits_and_wider_dispatch_refuse(self):
        for key, value in [('runtime_commit', '0' * 64),
                           ('installer_seconds', 541),
                           ('matrix_dispatch', True),
                           ('runtime_admission', True),
                           ('zy_execution', True),
                           ('execution_authorized', 1)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(dict(self.control, **{key: value}))

    def test_missing_review_and_changed_source_refuse(self):
        changed = copy.deepcopy(self.control)
        changed['review']['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.validate(changed)
        (self.source / controller.SUITE).write_text('changed')
        with self.assertRaises(ValueError):
            self.validate()

    def test_symlinked_capsule_refuses(self):
        name = next(iter(self.capsule_pins))
        target = self.decisions / name
        saved = self.decisions / 'original'
        target.rename(saved)
        target.symlink_to(saved)
        with self.assertRaises(ValueError):
            self.validate()

    def test_installer_preserves_controls_inside_smaller_deadline(self):
        original = (ROOT / 'tools/hosted_l1_gui_install.py').read_text()
        with patch.object(controller, 'ROOT', Path('/home/runner/work/repo')):
            adapted = controller.installer_source(original)
        compile(adapted, 'candidate-installer', 'exec')
        self.assertIn('RUNTIME_SECONDS = 510', adapted)
        self.assertIn('started + 515, started + 535', adapted)
        self.assertIn("('8min 30s', '510000000')", adapted)
        self.assertIn(controller.APP_COMMIT, adapted)
        self.assertIn(controller.RUNTIME_COMMIT, adapted)
        self.assertNotIn('/home/richard', adapted)
        for marker in ('KillMode', 'SendSIGKILL', 'installer-ownership.json',
                       'cleanup(work, deadline=cleanup_deadline)'):
            self.assertIn(marker, adapted)
        with self.assertRaises(ValueError):
            controller.installer_source(original.replace(
                'RUNTIME_SECONDS = 570', 'RUNTIME_SECONDS = 571'))

    def test_deployed_pin_drift_refuses(self):
        values = iter((controller.APP_COMMIT, controller.pilot.RUNTIME,
                       controller.RUNTIME_COMMIT))
        controller.candidate_deployment(lambda *_: next(values))
        for index in range(3):
            values = [controller.APP_COMMIT, controller.pilot.RUNTIME,
                      controller.RUNTIME_COMMIT]
            values[index] = 'wrong'
            iterator = iter(values)
            with self.subTest(index=index), self.assertRaises(ValueError):
                controller.candidate_deployment(lambda *_: next(iterator))

    def test_child_environment_excludes_credentials_and_overrides(self):
        contaminated = dict(self.environment, GITHUB_TOKEN='secret',
                            TRACKTEMPLATE_SOURCE_ROOT='/private', PATH='/bin')
        with patch.dict(os.environ, contaminated, clear=True):
            clean = controller.child_environment(self.root)
        self.assertNotIn('GITHUB_TOKEN', clean)
        self.assertNotIn('TRACKTEMPLATE_SOURCE_ROOT', clean)
        self.assertEqual(clean['PYTHONNODEBUGRANGES'], '1')
        self.assertEqual(clean['PYTHONDONTWRITEBYTECODE'], '1')


class SuiteTests(unittest.TestCase):
    def test_import_starts_no_freecad_or_qt(self):
        self.assertNotIn('FreeCAD', suite.__dict__)
        self.assertNotIn('PySide6', suite.__dict__)

    def test_wrong_launcher_name_refuses_before_timer(self):
        gui = ModuleType('FreeCADGui')
        side = ModuleType('PySide6')
        side.QtCore = SimpleNamespace(QTimer=SimpleNamespace(
            singleShot=lambda *_: self.fail('Timer must not start')))
        with patch.dict(sys.modules, {'FreeCADGui': gui, 'PySide6': side}):
            with self.assertRaises(AssertionError):
                suite.start('/not-read', '0' * 64,
                            launcher_name='unexpected_entry')

    def test_bad_config_fails_before_timer_or_document(self):
        gui = ModuleType('FreeCADGui')
        side = ModuleType('PySide6')
        side.QtCore = SimpleNamespace(QTimer=SimpleNamespace(
            singleShot=lambda *_: self.fail('Timer must not start')))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            path.write_text('{}')
            with patch.dict(sys.modules, {'FreeCADGui': gui, 'PySide6': side}), \
                    patch.dict(os.environ, {
                        'GITHUB_ACTIONS': 'true', 'GITHUB_RUN_ATTEMPT': '1'}):
                with self.assertRaises(AssertionError):
                    suite.start(path, '0' * 64, launcher_name='__main__')

    def test_original_failure_is_retained_and_no_pass_sentinel_is_written(self):
        calls = []
        gui = ModuleType('FreeCADGui')
        gui.getMainWindow = lambda: SimpleNamespace(close=lambda: calls.append('close'))
        side = ModuleType('PySide6')
        side.QtCore = SimpleNamespace(QTimer=SimpleNamespace(
            singleShot=lambda _, callback: callback()))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / 'config.json'
            save(config, {'entry_sha256': controller.digest(Path(suite.__file__)),
                          'output_root': str(root / 'payload')})
            with patch.dict(sys.modules, {'FreeCADGui': gui, 'PySide6': side}), \
                    patch.dict(os.environ, {
                        'GITHUB_ACTIONS': 'true', 'GITHUB_RUN_ATTEMPT': '1'}), \
                    patch.object(suite, '_run', side_effect=AssertionError('fixed')), \
                    patch('sys.stderr'):
                suite.start(config, controller.digest(config), launcher_name='__main__')
            raw = (root / 'payload/gui/readiness/failure.txt').read_text()
            self.assertIn('AssertionError: fixed', raw)
            observation = json.loads((root / 'readiness-observation.json').read_text())
            self.assertEqual(observation['status'], 'FAIL')
            self.assertEqual(observation['sentinel'], '')
            self.assertIsNone(observation['runtime'])
            self.assertEqual(calls, ['close'])


if __name__ == '__main__':
    unittest.main()
