"""Offline GUI-host admission and evidence controls; never start FreeCAD/Qt."""

import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import hosted_l1_gui_validation as gui  # noqa: E402


def authority():
    """Supply synthetic reviewed records only to pure control functions."""
    record = {
        'schema': 1, 'stage': 'gui', 'scope_id': gui.SCOPE, 'source_base_commit': gui.BASE,
        'source_commit': 'a' * 40, 'owner': 'Richard-Gnitnub',
        'execution_authorized': True, 'independent_review': 'PASS',
        'decision_id': 'test-owner-record', 'dispatch_nonce': 'test-once',
        'run_attempt': 1, 'freecad_limits': vars(gui.LIMITS),
        'display_limits': vars(gui.DISPLAY_LIMITS),
        'initial_reserve_mib': gui.RESERVE_MIB,
        'software_renderer': 'llvmpipe', 'repair_allowance_remaining': 0,
        'handling_decision': gui.HANDLING_DECISION,
        'input_archive': copy.deepcopy(gui.INPUT_ARCHIVE),
        'gui_entry_sha256': 'b' * 64,
        'control_files_sha256': {name: 'c' * 64 for name in gui.CONTROL_FILES},
        'input_hashes': {name: 'd' * 64 for name in gui.native.payload.INPUT_IDS},
        'gui_recovery': {
            'status': 'PASS', 'independent_review': 'PASS',
            'source_commit': 'a' * 40, 'evidence_sha256': 'e' * 64,
        },
        'prior_native_evidence': {
            'status': 'PASS', 'independent_review': 'PASS',
            'run_id': 41116286780,
            'evidence_sha256': '6061358800717ce6d1b3f460ea369a3cadfc0d3602aaaf69b434098a662a8f04',
        },
        'access_review': {
            'status': 'PASS', 'audited_at_utc': '2026-10-31T00:00:00Z',
            'owner': 'Richard-Gnitnub', 'environment': 'l1-private-validation',
            'branches': ['main'], 'tags': [],
            'input_repository': gui.native.INPUT_REPOSITORY,
            'repository_public': True,
        },
    }

    record['gui_readiness_review'] = {
        'status': 'PASS', 'independent_review': 'PASS', 'scope_id': gui.SCOPE,
        'stage': 'readiness', 'source_commit': record['source_commit'],
        'gui_entry_sha256': record['gui_entry_sha256'],
        'control_files_sha256': record['control_files_sha256'],
        'input_hashes': record['input_hashes'],
        'freecad_limits': vars(gui.limits('readiness')),
        'display_limits': vars(gui.display_limits('readiness')),
        'tests': 1, 'skips': 0, 'run_attempt': 1,
        'sentinel': gui.READINESS_SENTINEL, 'cleanup': True,
        'evidence_verified': True, 'independent_preservation': True,
        'run_id': 41, 'evidence_sha256': 'f' * 64,
    }
    return record


def environment():
    return {
        'GITHUB_REF': 'refs/heads/main', 'GITHUB_RUN_ATTEMPT': '1',
        'GITHUB_RUN_ID': '42', 'GITHUB_ACTIONS': 'true',
        'GITHUB_SHA': 'a' * 40, 'L1_GUI_STAGE': 'gui',
        'GITHUB_REPOSITORY': gui.native.INPUT_REPOSITORY,
        'GITHUB_EVENT_NAME': 'workflow_dispatch',
        'RUNNER_ENVIRONMENT': 'github-hosted',
        'RUNNER_OS': 'Linux', 'RUNNER_ARCH': 'X64',
    }


def display_sample():
    return {
        'memory.current': '1048576', 'memory.peak': '1048576',
        'memory.events': 'low 0\nhigh 0\nmax 0\noom 0\noom_kill 0\n',
        'memory.swap.current': '0',
        'memory.pressure': ('some avg10=0.00 avg60=0.00 avg300=0.00 total=0\n'
                            'full avg10=0.00 avg60=0.00 avg300=0.00 total=0'),
        'cpu.stat': 'usage_usec 3000\n', 'pids.current': '2',
        'cgroup.events': 'populated 1\n', 'cgroup.procs': '100\n',
    }


class HostedL1GuiControls(unittest.TestCase):
    def test_native_authority_cannot_admit_gui_or_reset_repairs(self):
        good = authority()
        gui.validate_authority(good, environment())
        cases = {
            'execution_authorized': False, 'scope_id': gui.native.SCOPE,
            'source_commit': 'e' * 40, 'source_base_commit': 'e' * 40,
            'independent_review': 'PENDING', 'run_attempt': 2,
            'software_renderer': 'hardware', 'repair_allowance_remaining': 1,
            'input_archive': dict(gui.INPUT_ARCHIVE, asset_id=1),
            'handling_decision': 'new-handling',
            'freecad_limits': dict(vars(gui.LIMITS), memory_max_mib=8192),
            'display_limits': dict(vars(gui.DISPLAY_LIMITS), tasks_max=128),
            'control_files_sha256': {}, 'input_hashes': {},
            'gui_recovery': {}, 'prior_native_evidence': {},
            'gui_readiness_review': {},
        }
        for key, value in cases.items():
            with self.subTest(key=key), self.assertRaises(ValueError):
                gui.validate_authority(dict(good, **{key: value}), environment())
        with self.assertRaises(ValueError):
            gui.validate_authority({}, environment())

    def test_short_readiness_precedes_separately_reviewed_gui_journey(self):
        ready = authority()
        ready.update(stage='readiness',
                     freecad_limits=vars(gui.limits('readiness')),
                     display_limits=vars(gui.display_limits('readiness')))
        ready.pop('gui_readiness_review')
        gui.validate_authority(ready, dict(environment(), L1_GUI_STAGE='readiness'))
        self.assertEqual(gui.limits('readiness').timeout_seconds, 90)
        self.assertEqual(gui.display_limits('readiness').timeout_seconds, 190)
        self.assertEqual(gui.display_properties('readiness')['RuntimeMaxSec'], '190')
        journey = authority()
        for key, value in (('run_id', 42), ('tests', 0), ('skips', 1),
                           ('independent_review', 'PENDING'), ('cleanup', False),
                           ('input_hashes', {}), ('gui_entry_sha256', '0' * 64)):
            changed = copy.deepcopy(journey)
            changed['gui_readiness_review'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                gui.validate_authority(changed, environment())
        with self.assertRaises(ValueError):
            gui.selected_stage({})

    def test_main_attempt_one_and_added_display_headroom_are_required(self):
        memory = ('MemTotal: 16777216 kB\nMemAvailable: 12845056 kB\n'
                  'SwapTotal: 0 kB\nSwapFree: 0 kB\n')
        gui.validate_host(environment(), memory)
        insufficient = memory.replace('12845056', '12582912')
        with self.assertRaisesRegex(ValueError, 'FreeCAD, display and reserve'):
            gui.validate_host(environment(), insufficient)
        for key, value in (('GITHUB_RUN_ATTEMPT', '2'),
                           ('GITHUB_REF', 'refs/heads/feature'),
                           ('RUNNER_ENVIRONMENT', 'self-hosted')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                gui.validate_host(dict(environment(), **{key: value}), memory)

    def test_display_limits_do_not_expand_existing_freecad_guard(self):
        self.assertEqual(vars(gui.LIMITS), vars(gui.native.limits('native')))
        self.assertEqual(vars(gui.DISPLAY_LIMITS), {
            'memory_max_mib': 256, 'timeout_seconds': 7300,
            'cpu_percent': 25, 'tasks_max': 16,
        })
        properties = gui.display_properties()
        self.assertEqual(properties['MemorySwapMax'], '0')
        self.assertEqual(properties['KillMode'], 'control-group')
        self.assertEqual(properties['RuntimeMaxSec'], '7300')
        self.assertEqual(properties['Restart'], 'no')

    def test_display_telemetry_rejects_events_swap_and_incomplete_reads(self):
        good = display_sample()
        gui.assess_display([good])
        cases = {
            'memory.events': good['memory.events'].replace('oom 0', 'oom 1'),
            'memory.swap.current': '1', 'memory.peak': str(257 * 1024**2),
            'pids.current': '17', 'cpu.stat': 'other 1',
            'cgroup.events': None, 'memory.pressure': 'some avg10=0.00',
        }
        for key, value in cases.items():
            with self.subTest(key=key), self.assertRaises((KeyError, ValueError)):
                gui.assess_display([dict(good, **{key: value})])
        with self.assertRaises(ValueError):
            gui.assess_display([])

    def test_display_pressure_preserves_valid_positive_observations(self):
        positive = (
            'some avg10=1.25 avg60=2.00 avg300=3.00 total=10\n'
            'full avg10=0.25 avg60=0.50 avg300=0.75 total=20'
        )
        later = positive.replace('total=10', 'total=11').replace(
            'total=20', 'total=21',
        )
        first = display_sample()
        first['memory.pressure'] = positive
        second = display_sample()
        second['memory.pressure'] = later
        gui.assess_display([first, second])
        invalid = {
            'malformed': later.replace('avg60=2.00', 'avg60=..'),
            'negative': later.replace('avg10=1.25', 'avg10=-1.25'),
            'nonfinite': later.replace('avg10=1.25', 'avg10=nan'),
            'overflow': later.replace('avg10=1.25', 'avg10=' + '9' * 400),
            'decreasing': later.replace('total=11', 'total=9'),
            'duplicate': later + '\n' + later.splitlines()[0],
            'missing': later.splitlines()[0],
        }
        for label, text in invalid.items():
            bad = display_sample()
            bad['memory.pressure'] = text
            with self.subTest(case=label), self.assertRaises(ValueError):
                gui.assess_display([first, bad])

    def test_runtime_parser_accepts_only_exact_gui_frame_or_direct_record(self):
        record = {'status': 'modular-foundation-ready',
                  'matched_profile_id': gui.original.EXPECTED_PROFILE,
                  'document_mutation': False, 'workflow_launched': False}
        direct = 'TRACKTEMPLATE_B16_FOUNDATION=' + json.dumps(record)
        frame = ('test_authorised_gui_stage '
                 '(hosted_l1_gui_suite.L1Gui.test_authorised_gui_stage) ... ')
        gui.qualified_runtime(direct)
        gui.qualified_runtime(frame + direct)
        for bad in ('', direct + '\n' + direct, 'other ... ' + direct,
                    'TRACKTEMPLATE_B16_FOUNDATION={broken',
                    direct.replace(gui.original.EXPECTED_PROFILE, 'wrong')):
            with self.subTest(text=bad), self.assertRaises(ValueError):
                gui.qualified_runtime(bad)

    def test_child_environment_drops_secrets_and_selects_real_xcb(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence').mkdir()
            (work / 'gui-run-config.json').write_text('{}')
            (work / 'evidence/gui-authority.json').write_text('{}')
            values = dict(environment(), HOME='/home/runner', PATH='/usr/bin',
                          GITHUB_TOKEN='private', PYTHONPATH='/untrusted',
                          LD_PRELOAD='/untrusted', QT_QPA_PLATFORM='offscreen')
            with patch.dict(os.environ, values, clear=True):
                clean = gui.child_environment(work)
            self.assertEqual(clean['QT_QPA_PLATFORM'], 'xcb')
            self.assertEqual(clean['GALLIUM_DRIVER'], 'llvmpipe')
            self.assertEqual(clean['DISPLAY'], ':99')
            self.assertEqual(clean['LIBGL_ALWAYS_SOFTWARE'], '1')
            for key in ('GITHUB_TOKEN', 'PYTHONPATH', 'LD_PRELOAD'):
                self.assertNotIn(key, clean)

    def test_no_owner_receipt_after_launch_is_not_cleanup_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence').mkdir()
            self.assertTrue(gui.display_cleanup(work)['cleanup'])
            (work / 'evidence/display-start-intent.json').write_text('{}')
            self.assertFalse(gui.display_cleanup(work)['cleanup'])

    def test_display_identity_mismatch_never_stops_another_invocation(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence').mkdir()
            owner = {'unit': 'owned.service', 'invocation': 'a' * 32}
            (work / 'evidence/display-ownership.json').write_text(json.dumps(owner))
            with patch.object(gui, '_display_group', return_value=work):
                with patch.object(gui, '_display_show', return_value={
                        'InvocationID': 'b' * 32}):
                    with patch.object(gui.native, 'command') as command:
                        receipt = gui.display_cleanup(work)
            self.assertFalse(receipt['cleanup'])
            command.assert_not_called()

    def test_copied_fcstd_is_retained_outside_all_diagnostic_archives(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            source = work / 'evidence/gui/XO-001-copy.FCStd'
            source.parent.mkdir(parents=True)
            source.write_bytes(b'copied-input')
            gui.exclude_gui_copy(work)
            self.assertFalse(source.exists())
            retained = work / 'retained-gui-inputs/XO-001-copy.FCStd'
            self.assertEqual(retained.read_bytes(), b'copied-input')
            excluded = json.loads((work / 'evidence/gui-copy-exclusion.json').read_text())
            self.assertEqual(excluded['sha256'], gui.digest(retained))
            (source.parent / 'unexpected.FCStd').write_bytes(b'other')
            with self.assertRaisesRegex(ValueError, 'Unexpected FreeCAD document'):
                gui.exclude_gui_copy(work)

    def test_receipt_requires_exact_images_counts_software_gl_and_original_bytes(self):
        labels = ('reference-600', 'changed-900', 'returned-600')
        names = [f'{label}/radius-input.png' for label in labels]
        names += [f'{label}/representative-{index}/{name}.png'
                  for label in labels for index in (0, 1)
                  for name in ('overview', 'chair-closeup')]
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            screenshots = []
            for name in names:
                path = work / 'evidence/gui' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'synthetic-png-for-identity-control')
                screenshots.append({'path': name, 'sha256': gui.digest(path),
                                    'bytes': path.stat().st_size})
            receipt = {
                'status': 'PASS', 'stage': 'gui',
                'profile': gui.original.EXPECTED_PROFILE,
                'input_bindings_unchanged': True, 'owned_documents_closed': True,
                'cleanup_errors': [], 'sentinel': gui.SENTINEL,
                'body_frame_comparisons': 30,
                'layer_visibility_selection_checks': 75,
                'successful_preview_component_placements': 690,
                'preview_image_count': 12, 'dialog_image_count': 3,
                'source_and_foreign_preserved': True, 'no_eager_chairs': True,
                'generate_operations': 3,
                'renderer': {'platform': 'xcb', 'gui_up': True,
                             'widget_valid': True, 'renderer': 'llvmpipe',
                             'vendor': 'Mesa', 'version': '4.5'},
                'cases': [{'case': name, 'radius_mm': radius}
                          for name, radius in zip(labels, (600, 900, 600))],
                'screenshots': screenshots,
            }
            gui.validate_gui_receipt(receipt, work)
            cases = {
                'renderer': dict(receipt['renderer'], renderer='hardware'),
                'screenshots': screenshots[:-1], 'owned_documents_closed': False,
                'successful_preview_component_placements': 689,
                'body_frame_comparisons': 29, 'cases': receipt['cases'][:-1],
            }
            for key, value in cases.items():
                with self.subTest(key=key), self.assertRaises(ValueError):
                    gui.validate_gui_receipt(dict(receipt, **{key: value}), work)
            altered = copy.deepcopy(receipt)
            altered['screenshots'][0]['path'] = '../outside.png'
            with self.assertRaises(ValueError):
                gui.validate_gui_receipt(altered, work)
            (work / 'evidence/gui' / names[-1]).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Screenshot bytes differ'):
                gui.validate_gui_receipt(receipt, work)

    def test_workflow_is_serial_manual_pinned_and_reuses_evidence_transport(self):
        workflow = (ROOT / '.github/workflows/l1-gui-validation.yml').read_text()
        self.assertIn('workflow_dispatch:', workflow)
        self.assertIn('group: issue230-native-geometry', workflow)
        self.assertIn('cancel-in-progress: false', workflow)
        self.assertIn("github.ref == 'refs/heads/main' && github.run_attempt == 1", workflow)
        self.assertIn('L1_GUI_CONTROL: ${{ vars.L1_GUI_CONTROL }}', workflow)
        self.assertIn('retention-days: 30', workflow)
        self.assertNotIn('L1_PRIVATE_CONTROL:', workflow)
        self.assertIn('L1_GUI_STAGE: ${{ inputs.stage }}', workflow)
        self.assertNotIn('xvfb-run', workflow)
        self.assertNotIn('FreeCADCmd', workflow)
        for operation in ('prepare', 'acquire', 'run', 'finalize', 'seal',
                          'publish', 'complete', 'finish'):
            self.assertIn('hosted_l1_gui_validation.py ' + operation, workflow)
        for line in workflow.splitlines():
            if 'uses:' in line:
                self.assertRegex(line, r'@[0-9a-f]{40}(?: |$)')


class GuiProofContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            'l1_gui_contract_under_test', ROOT / gui.ENTRY,
        )
        cls.suite = importlib.util.module_from_spec(spec)
        with patch.object(gui.subprocess, 'Popen', side_effect=AssertionError(
                'Import attempted process start')):
            spec.loader.exec_module(cls.suite)

    def test_actual_renderer_rejects_missing_context_hardware_and_offscreen(self):
        good = {'gui_up': True, 'widget_valid': True, 'platform': 'xcb',
                'vendor': 'Mesa', 'renderer': 'llvmpipe', 'version': '4.5'}
        self.suite.validate_gl(good)
        with self.assertRaises((AssertionError, KeyError)):
            self.suite.validate_gl({})
        for key, value in (('gui_up', False), ('widget_valid', False),
                           ('platform', 'offscreen'), ('renderer', 'hardware'),
                           ('vendor', ''), ('version', '')):
            with self.subTest(key=key), self.assertRaises(AssertionError):
                self.suite.validate_gl(dict(good, **{key: value}))

    def test_structure_rejects_wrong_identities_layers_and_child_counts(self):
        components = (
            *(f'Part_{index:02d}' for index in range(7)), 'SourceFixing',
            *(f'SourceFixing{index:03d}' for index in range(1, 16)),
        )
        ids = [f'position-{index}' for index in range(10)]
        result = {
            'placement_count': 10, 'component_count': 23, 'layer_count': 25,
            'placements': [{'position_id': identity} for identity in ids],
            'project_status': 'reference-only',
            'production_geometry_authorized': False, 'geometry_rebuilt': False,
            'excluded_source_components': [],
            'source_receipt': {'source_document_mutation': False},
        }
        names = ('ReferenceRails', 'ReferenceTimbers', *components)
        counts = dict.fromkeys(components, 10)
        self.suite.check_structure(result, names, counts, ids)
        for key, value in (
            ('placement_count', 9), ('layer_count', 24),
            ('placements', result['placements'][:-1]),
            ('placements', result['placements'][:-1] + [result['placements'][0]]),
            ('project_status', 'project-cleared'),
            ('production_geometry_authorized', True),
        ):
            with self.subTest(key=key), self.assertRaises(AssertionError):
                self.suite.check_structure(dict(result, **{key: value}),
                                           names, counts, ids)
        with self.assertRaises(AssertionError):
            self.suite.check_structure(result, names[:-1], counts, ids)
        with self.assertRaises(AssertionError):
            self.suite.check_structure(result, names,
                                       dict(counts, Part_00=9), ids)

    def test_dialog_needs_one_real_input_confirmation_and_success(self):
        good = {
            'control': 'real-GUI', 'cancel': False, 'errors': [],
            'inputs': [{'radius': 600}],
            'messages': [
                {'kind': 'question', 'text': 'Replace?'},
                {'kind': 'information',
                 'text': 'Curve and straight-track outputs created successfully'},
            ],
        }
        self.suite.check_dialog(good)
        for key, value in (
            ('control', 'mock'), ('cancel', True), ('errors', ['error']),
            ('inputs', []), ('inputs', [{}, {}]), ('messages', []),
            ('messages', [good['messages'][0], good['messages'][0]]),
            ('messages', [good['messages'][1], good['messages'][1]]),
        ):
            with self.subTest(key=key), self.assertRaises(AssertionError):
                self.suite.check_dialog(dict(good, **{key: value}))

    def test_suite_authority_is_separate_and_hash_bound(self):
        good = authority()
        config = {'handling_decision': good['handling_decision'],
                  'inputs': [{'id': name, 'sha256': value}
                             for name, value in good['input_hashes'].items()]}
        with patch.dict(os.environ, environment(), clear=True):
            self.suite.validate_authority(good, config, 'b' * 64)
            for key, value in (
                ('execution_authorized', False), ('scope_id', gui.native.SCOPE),
                ('input_hashes', {}), ('gui_entry_sha256', 'e' * 64),
                ('handling_decision', 'other'), ('display_limits', {}),
            ):
                with self.subTest(key=key), self.assertRaises(AssertionError):
                    self.suite.validate_authority(dict(good, **{key: value}),
                                                  config, 'b' * 64)
            with self.assertRaises(AssertionError):
                self.suite.validate_authority({}, config, 'b' * 64)
        with patch.dict(os.environ, dict(environment(), GITHUB_RUN_ATTEMPT='2'),
                        clear=True), self.assertRaises(AssertionError):
            self.suite.validate_authority(good, config, 'b' * 64)

    def test_preservation_catches_document_view_camera_and_selection_changes(self):
        before = {
            'documents': [{'name': 'source', 'native': 'hash-a',
                           'view': 'hash-b', 'camera': 'camera-a'}],
            'selection': ['source/Keep'],
        }
        self.suite._preserved(before, copy.deepcopy(before))
        added = copy.deepcopy(before)
        added['documents'].append({'name': 'new-preview'})
        self.suite._preserved(before, added)
        for field in ('native', 'view', 'camera'):
            changed = copy.deepcopy(before)
            changed['documents'][0][field] = 'changed'
            with self.subTest(field=field), self.assertRaises(AssertionError):
                self.suite._preserved(before, changed)
        changed = copy.deepcopy(before)
        changed['selection'] = []
        with self.assertRaises(AssertionError):
            self.suite._preserved(before, changed)

    def test_start_schedules_one_unittest_and_exits_qt_from_actual_result(self):
        for passed, count, skips, exit_code in (
            (True, 1, [], 0), (False, 1, [], 1),
            (True, 0, [], 1), (True, 1, ['skipped'], 1),
        ):
            with self.subTest(passed=passed, count=count, skips=skips):
                callbacks = []
                exit_qt = Mock()
                qtcore = SimpleNamespace(
                    QTimer=SimpleNamespace(singleShot=lambda delay, callback:
                                           callbacks.append((delay, callback))),
                    QCoreApplication=SimpleNamespace(exit=exit_qt),
                )
                pyside = ModuleType('PySide6')
                pyside.QtCore = qtcore
                result = SimpleNamespace(wasSuccessful=lambda: passed,
                                         testsRun=count, skipped=skips)
                runner = Mock()
                runner.run.return_value = result
                with patch.dict(sys.modules, {'PySide6': pyside}):
                    with patch.object(self.suite.unittest, 'TextTestRunner',
                                      return_value=runner):
                        self.suite.start()
                        self.assertEqual(len(callbacks), 1)
                        self.assertEqual(callbacks[0][0], 0)
                        exit_qt.assert_not_called()
                        callbacks[0][1]()
                test_suite = runner.run.call_args.args[0]
                self.assertEqual(test_suite.countTestCases(), 1)
                self.assertEqual(list(test_suite)[0]._testMethodName,
                                 'test_authorised_gui_stage')
                exit_qt.assert_called_once_with(exit_code)

    def test_macro_and_flatpak_argv_use_reviewed_start_without_wrapper(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence').mkdir()
            (work / 'gui-run-config.json').write_text('{}')
            (work / 'evidence/gui-authority.json').write_text('{}')
            macro = gui.write_gui_macro(work)
            record = json.loads((work / 'evidence/gui-macro.json').read_text())
            self.assertEqual(record['sha256'], gui.digest(macro))
            parsed = ast.parse(macro.read_text())
            self.assertEqual(len(parsed.body), 6)
            self.assertIn('hosted_l1_gui_suite.start()', macro.read_text())
            with patch.dict(os.environ, environment(), clear=True):
                argv = gui.gui_argv(gui.child_environment(work), macro)
            guarded = gui.guard._payload_command(argv)
            self.assertIn('FreeCAD', guarded)
            self.assertEqual(guarded[-1], str(macro))
            self.assertNotIn('xvfb-run', guarded)
            self.assertNotIn('FreeCADCmd', guarded)
            self.assertIn('--env=GITHUB_SHA=' + 'a' * 40, argv)


if __name__ == '__main__':
    result = unittest.main(exit=False)
    if not result.result.wasSuccessful():
        raise SystemExit(1)
    print('Hosted L1 GUI controls passed')
