"""Offline GUI-host admission and evidence controls; never start FreeCAD/Qt."""

import ast
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
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


class ReadinessSetupRegressions(unittest.TestCase):
    def checkout_fixture(self, temporary, depth):
        """Make a local history with an older unchanged frozen baseline."""
        self.assertTrue(temporary.resolve().is_relative_to(
            Path(tempfile.gettempdir()).resolve(),
        ))
        origin = temporary / 'origin'
        origin.mkdir()
        command = gui.native.command
        command('git', 'init', '--initial-branch=main', cwd=origin)
        for name in (*gui.CONTROL_FILES, gui.ENTRY):
            target = origin / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
        frozen = origin / 'tracktemplate/frozen.py'
        frozen.parent.mkdir()
        frozen.write_text('FROZEN = True\n')
        for index in range(3):
            (origin / 'revision.txt').write_text(str(index))
            command('git', 'add', '.', cwd=origin)
            command('git', '-c', 'user.name=Regression Fixture', '-c',
                    'user.email=fixture@example.invalid', 'commit', '-m',
                    f'Fixture {index}', cwd=origin)
            if index == 0:
                baseline = command('git', 'rev-parse', 'HEAD', cwd=origin)
        checkout = temporary / 'checkout'
        depth_args = ('--depth', str(depth)) if depth else ()
        command('git', 'clone', *depth_args, origin.as_uri(), str(checkout),
                cwd=temporary)
        return checkout, baseline

    def prepare_checkout(self, checkout, baseline, work):
        command = gui.native.command
        head = command('git', 'rev-parse', 'HEAD', cwd=checkout)
        record = authority()
        record.update(
            stage='readiness', source_base_commit=baseline, source_commit=head,
            freecad_limits=vars(gui.limits('readiness')),
            display_limits=vars(gui.display_limits('readiness')),
            gui_entry_sha256=gui.digest(checkout / gui.ENTRY),
            control_files_sha256={
                name: gui.digest(checkout / name) for name in gui.CONTROL_FILES
            },
        )
        record['gui_recovery']['source_commit'] = head
        values = dict(environment(), GITHUB_SHA=head, L1_GUI_STAGE='readiness',
                      L1_GUI_CONTROL=json.dumps(record))
        with (patch.dict(os.environ, values, clear=True),
              patch.object(gui, 'ROOT', checkout),
              patch.object(gui, 'BASE', baseline),
              patch.object(gui, 'validate_host', return_value={}),
              patch.object(gui.resource, 'setrlimit'),
              patch.object(gui.native, 'command', side_effect=lambda *args:
                           command(*args, cwd=checkout))):
            gui.prepare(work)

    def test_workflow_checkout_supports_historical_frozen_comparison(self):
        workflow = (ROOT / '.github/workflows/l1-gui-validation.yml').read_text()
        checkout = workflow.split('uses: actions/checkout@', 1)[1].split(
            '\n      - name:', 1,
        )[0]
        configured = re.search(r'^\s+fetch-depth:\s*(\d+)\s*$', checkout,
                               re.MULTILINE)
        depth = int(configured.group(1)) if configured else 1
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, baseline = self.checkout_fixture(root, depth)
            work = root / 'work'
            (work / 'evidence').mkdir(parents=True)
            self.prepare_checkout(source, baseline, work)
            self.assertEqual(json.loads((work / 'control.json').read_text())[
                'source_base_commit'], baseline)

    def test_missing_baseline_and_changed_frozen_source_remain_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, baseline = self.checkout_fixture(root, 0)
            work = root / 'work'
            (work / 'evidence').mkdir(parents=True)
            for missing in ('f' * 40, 'not-a-commit'):
                with self.subTest(baseline=missing), self.assertRaises(
                        subprocess.CalledProcessError):
                    self.prepare_checkout(source, missing, work)
                self.assertFalse((work / 'control.json').exists())
            (source / 'tracktemplate/frozen.py').write_text('FROZEN = False\n')
            command = gui.native.command
            command('git', 'add', 'tracktemplate/frozen.py', cwd=source)
            command('git', '-c', 'user.name=Regression Fixture', '-c',
                    'user.email=fixture@example.invalid', 'commit', '-m',
                    'Changed frozen fixture', cwd=source)
            with self.assertRaisesRegex(ValueError, 'Frozen product'):
                self.prepare_checkout(source, baseline, work)
            self.assertFalse((work / 'control.json').exists())

    def failed_prepare_environment(self):
        return dict(environment(), L1_GUI_STAGE='readiness',
                    L1_PREPARE='failure', L1_INSTALL='skipped',
                    L1_ACQUIRE='skipped', L1_RUN='skipped')

    def test_skipped_install_needs_no_flatpak_for_never_started_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence').mkdir()
            (work / 'evidence/prepare.log').write_text('baseline unavailable')
            (work / 'evidence/finalizer.log').write_text('')
            values = self.failed_prepare_environment()
            with (patch.dict(os.environ, values, clear=True),
                  patch.object(gui.original, '_clearance',
                               side_effect=FileNotFoundError('flatpak'))
                  as clearance):
                result = gui.finalize(work, work / 'public')
            self.assertEqual(result, 0)
            clearance.assert_not_called()
            process = json.loads((
                work / 'evidence/process-finalization.json').read_text())
            self.assertTrue(process['cleanup'])
            self.assertTrue(process['never_started'])
            self.assertEqual(process['errors'], [])
            self.assertEqual(process['workflow_outcomes'], {
                name: values[name] for name in (
                    'L1_PREPARE', 'L1_INSTALL', 'L1_ACQUIRE', 'L1_RUN',
                )
            })

    def test_uncertain_outcomes_still_require_native_clearance(self):
        expected = self.failed_prepare_environment()
        for name in ('L1_PREPARE', 'L1_INSTALL', 'L1_ACQUIRE', 'L1_RUN'):
            for outcome in (None, '', 'unknown', 'failure', 'cancelled',
                            'success', 'skipped'):
                if outcome == expected[name]:
                    continue
                with (self.subTest(name=name, outcome=outcome),
                      tempfile.TemporaryDirectory() as temporary):
                    work = Path(temporary)
                    (work / 'evidence').mkdir()
                    values = dict(expected)
                    if outcome is None:
                        values.pop(name)
                    else:
                        values[name] = outcome
                    with (patch.dict(os.environ, values, clear=True),
                          patch.object(gui.original, '_clearance',
                                       side_effect=FileNotFoundError('flatpak'))
                          as clearance):
                        self.assertEqual(gui.finalize(work, work / 'public'), 1)
                    clearance.assert_called_once_with()
                    process = json.loads((
                        work / 'evidence/process-finalization.json').read_text())
                    self.assertFalse(process['cleanup'])
                    self.assertTrue(process['errors'])
                    self.assertFalse(process.get('never_started', False))

    def test_runtime_input_unknown_or_linked_state_uses_native_finalizer(self):
        cases = (
            ('evidence/guard/result.json', 'file'),
            ('evidence/guard/ownership.json', 'file'),
            ('evidence/display-start-intent.json', 'file'),
            ('evidence/display-ownership.json', 'file'),
            ('evidence/execution.log', 'file'),
            ('evidence/install.log', 'file'),
            ('evidence/acquisition.log', 'file'),
            ('run-config.json', 'file'), ('gui-run-config.json', 'file'),
            ('inputs.tar', 'file'), ('unpacked', 'directory'),
            ('gui-entry.FCMacro', 'file'), ('unexpected', 'file'),
            ('evidence/unexpected', 'file'),
            ('control.json', 'file-link'),
            ('control.json', 'dangling-link'),
            ('evidence/prepare.log', 'file-link'),
            ('evidence/prepare.log', 'dangling-link'),
            ('evidence', 'directory-link'),
        )
        for name, kind in cases:
            with (self.subTest(path=name, kind=kind),
                  tempfile.TemporaryDirectory() as temporary):
                root = Path(temporary)
                work = root / 'work'
                work.mkdir()
                if kind == 'directory-link':
                    target = root / 'linked-evidence'
                    target.mkdir()
                    (work / name).symlink_to(target, target_is_directory=True)
                else:
                    (work / 'evidence').mkdir()
                    target = work / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if kind == 'directory':
                        target.mkdir()
                    elif kind == 'file-link':
                        linked = root / 'linked-file'
                        linked.write_text('{}')
                        target.symlink_to(linked)
                    elif kind == 'dangling-link':
                        target.symlink_to(work / 'absent')
                    else:
                        target.write_text('{}')
                with (patch.dict(os.environ, self.failed_prepare_environment(),
                                 clear=True),
                      patch.object(gui.native, 'finalize', return_value=1)
                      as native_finalizer,
                      patch.object(gui, 'display_cleanup', return_value={
                          'cleanup': False, 'errors': [],
                      })):
                    self.assertEqual(gui.finalize(work, work / 'public'), 1)
                native_finalizer.assert_called_once_with(
                    'gui', work, work / 'public',
                )

    def test_never_started_cleanup_cannot_complete_failed_readiness(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence').mkdir()
            (work / 'evidence/prepare.log').write_text('BASELINE-FAILURE')
            values = dict(
                self.failed_prepare_environment(),
                L1_PRIMARY_UPLOAD='success', L1_PRIMARY_DOWNLOAD='success',
                L1_PRIMARY_ID='121', L1_FINAL_UPLOAD='success',
                L1_FINAL_DOWNLOAD='success', L1_FINAL_ID='122',
                L1_PUBLICATION='success',
            )
            with (patch.dict(os.environ, values, clear=True),
                  patch.object(gui.original, '_clearance',
                               side_effect=FileNotFoundError('flatpak'))):
                self.assertEqual(gui.finalize(work, work / 'public'), 0)
                for name in ('readback-primary', 'readback-final'):
                    (work / name).mkdir()
                gui.native.seal(work)
                (work / 'readback-primary/evidence.tar').write_bytes(
                    (work / 'evidence.tar').read_bytes())
                self.assertEqual(gui.publish(work), 0)
                (work / 'readback-final/publication.tar').write_bytes(
                    (work / 'publication.tar').read_bytes())
                self.assertEqual(gui.complete(work, work / 'public'), 1)
            summary = json.loads((work / 'public/summary.json').read_text())
            self.assertEqual(summary['outcome'], 'INCOMPLETE')
            self.assertNotIn('tests', summary)
            self.assertEqual((work / 'evidence/prepare.log').read_text(),
                             'BASELINE-FAILURE')


class InstallationFailureRegressions(unittest.TestCase):
    def fixture(self, work):
        (work / 'evidence').mkdir()
        for name in ('prepare.log', 'gui-authority.json', 'admission.json',
                     'install.log', 'installer-intent.json',
                     'installer-ownership.json', 'installer-result.json',
                     'installer-output.log', 'finalizer.log'):
            (work / 'evidence' / name).write_text('{}')
        return dict(environment(), L1_PREPARE='success',
                    L1_INSTALL='failure', L1_ACQUIRE='skipped',
                    L1_RUN='skipped')

    def finalize(self, work, values, *, cleanup=True, flatpak=None,
                 clearance=True):
        service = SimpleNamespace(cleanup=Mock(return_value={
            'cleanup': cleanup, 'errors': [] if cleanup else ['not empty'],
        }))
        with (patch.dict(os.environ, values, clear=True),
              patch.object(gui, 'installer', service, create=True),
              patch.object(gui, 'shutil', SimpleNamespace(
                  which=lambda name: flatpak), create=True),
              patch.object(gui.original, '_clearance',
                           return_value=clearance) as probe):
            result = gui.finalize(work, work / 'public')
        process = json.loads((
            work / 'evidence/process-finalization.json').read_text())
        return result, process, service.cleanup, probe

    def test_failed_install_proves_owned_runtime_never_started(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            values = self.fixture(work)
            result, process, cleanup, probe = self.finalize(work, values)
            self.assertEqual(result, 0)
            self.assertTrue(process['cleanup'])
            self.assertTrue(process['never_started'])
            cleanup.assert_called_once_with(work)
            probe.assert_not_called()

    def test_failed_install_requires_empty_installer(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            values = self.fixture(work)
            result, process, _, _ = self.finalize(
                work, values, cleanup=False)
            self.assertEqual(result, 1)
            self.assertFalse(process['cleanup'])
            self.assertFalse(process.get('never_started', False))

    def test_installed_flatpak_keeps_foreign_instance_clearance(self):
        for clear in (False, True):
            with (self.subTest(clearance=clear),
                  tempfile.TemporaryDirectory() as temporary):
                work = Path(temporary)
                values = self.fixture(work)
                result, process, _, probe = self.finalize(
                    work, values, flatpak='/usr/bin/flatpak', clearance=clear)
                probe.assert_called_once_with()
                self.assertEqual(process['cleanup'], clear)
                self.assertEqual(result, 0 if clear else 1)

    def test_failed_install_rejects_unknown_or_later_state(self):
        for name in ('run-config.json', 'inputs.tar',
                     'evidence/acquisition.log', 'evidence/guard/result.json',
                     'evidence/display-start-intent.json', 'evidence/unknown'):
            with (self.subTest(name=name),
                  tempfile.TemporaryDirectory() as temporary):
                work = Path(temporary)
                values = self.fixture(work)
                target = work / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('{}')
                result, process, _, _ = self.finalize(work, values)
                self.assertEqual(result, 1)
                self.assertFalse(process['cleanup'])

    def test_install_wrapper_is_used_with_original_outer_deadline(self):
        workflow = (ROOT / '.github/workflows/l1-gui-validation.yml').read_text()
        block = workflow.split('id: install', 1)[1].split(
            '- name: Acquire only', 1)[0]
        self.assertIn('timeout-minutes: 10', block)
        self.assertIn('hosted_l1_gui_validation.py install', block)
        self.assertNotIn('sudo apt-get update', block)

    def test_failed_install_rejects_links_and_inconsistent_outcomes(self):
        for change in ('link', 'acquired', 'ran', 'prepare_unknown'):
            with (self.subTest(change=change),
                  tempfile.TemporaryDirectory() as temporary):
                work = Path(temporary)
                values = self.fixture(work)
                if change == 'link':
                    (work / 'evidence/installer-samples.jsonl').symlink_to(
                        work / 'absent')
                else:
                    values[{'acquired': 'L1_ACQUIRE', 'ran': 'L1_RUN',
                            'prepare_unknown': 'L1_PREPARE'}[change]] = (
                                'success' if change != 'prepare_unknown'
                                else 'unknown')
                result, process, _, _ = self.finalize(work, values)
                self.assertEqual(result, 1)
                self.assertFalse(process['cleanup'])

    def test_failed_install_cleanup_never_becomes_a_test_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            values = self.fixture(work)
            values.update(
                L1_PRIMARY_UPLOAD='success', L1_PRIMARY_DOWNLOAD='success',
                L1_PRIMARY_ID='121', L1_FINAL_UPLOAD='success',
                L1_FINAL_DOWNLOAD='success', L1_FINAL_ID='122',
                L1_PUBLICATION='success',
            )
            (work / 'evidence/install.log').write_text('APT-SETUP-FAILED')
            result, _, _, _ = self.finalize(work, values)
            self.assertEqual(result, 0)
            with patch.dict(os.environ, values, clear=True):
                for name in ('readback-primary', 'readback-final'):
                    (work / name).mkdir()
                gui.native.seal(work)
                (work / 'readback-primary/evidence.tar').write_bytes(
                    (work / 'evidence.tar').read_bytes())
                self.assertEqual(gui.publish(work), 0)
                (work / 'readback-final/publication.tar').write_bytes(
                    (work / 'publication.tar').read_bytes())
                self.assertEqual(gui.complete(work, work / 'public'), 1)
            summary = json.loads((work / 'public/summary.json').read_text())
            self.assertEqual(summary['outcome'], 'INCOMPLETE')
            self.assertNotIn('tests', summary)
            self.assertEqual((work / 'evidence/install.log').read_text(),
                             'APT-SETUP-FAILED')

    def test_runtime_cleanup_keeps_original_receipt_and_installer_failure(self):
        for clean in (False, True):
            with (self.subTest(installer_cleanup=clean),
                  tempfile.TemporaryDirectory() as temporary):
                work = Path(temporary)
                values = self.fixture(work)
                values.update(L1_INSTALL='success', L1_ACQUIRE='success',
                              L1_RUN='success')
                result, process, _, probe = self.finalize(
                    work, values, cleanup=clean)
                probe.assert_called_once_with()
                retained = json.loads((
                    work / 'evidence/runtime-finalization.json').read_text())
                self.assertTrue(retained['cleanup'])
                self.assertEqual(process['cleanup'], clean)
                self.assertEqual(result, 0 if clean else 1)


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

    def _cross_document_selection(self):
        # FreeCAD 1.1.4 filters omitted document names by the active document.
        active = SimpleNamespace(name='source')
        selected = [SimpleNamespace(DocumentName='foreign', ObjectName='Keep',
                                    SubElementNames=('Face1',))]

        def selection(document=None):
            return [item for item in selected if document == '*'
                    or item.DocumentName == (document or active.name)]

        document_state = [{'name': 'source', 'native': 'hash-a',
                           'view': 'hash-b', 'camera': 'camera-a'}]

        def state():
            return {
                'active': active.name,
                'documents': copy.deepcopy(document_state),
                'selection': tuple((item.DocumentName, item.ObjectName,
                                    tuple(item.SubElementNames))
                                   for item in selection()),
            }

        native = SimpleNamespace(HELPERS={}, extract_helper=Mock(side_effect=[
            {'_images': None, '_archive_state': None},
            {'_settle': None, '_document_state': state,
             '_active_document_state': None},
            {'_gui_generate': None},
        ]))
        gui_host = SimpleNamespace(Selection=SimpleNamespace(
            getSelectionEx=selection,
        ))
        helpers = self.suite._helpers(native, None, gui_host, None, None)
        return helpers, active, selected, document_state

    def test_selection_snapshot_survives_active_document_change(self):
        helpers, active, selected, documents = self._cross_document_selection()
        selected.append(SimpleNamespace(
            DocumentName='source', ObjectName='Track', SubElementNames=(),
        ))
        expected = (('foreign', 'Keep', ('Face1',)), ('source', 'Track', ()))
        before = helpers.state()
        self.assertEqual(before['selection'], expected)
        self.assertEqual(before['documents'], documents)
        active.name = 'preview'
        after = helpers.state()
        self.assertEqual(after['active'], 'preview')
        self.assertEqual(after['selection'], expected)
        self.suite._preserved(before, after)

    def test_foreign_selection_loss_and_changes_are_not_hidden(self):
        for change in ('missing', 'document', 'object', 'subelement'):
            with self.subTest(change=change):
                helpers, active, selected, _ = self._cross_document_selection()
                before = helpers.state()
                active.name = 'preview'
                if change == 'missing':
                    selected.clear()
                elif change == 'document':
                    selected[0].DocumentName = 'different'
                elif change == 'object':
                    selected[0].ObjectName = 'Different'
                else:
                    selected[0].SubElementNames = ('Face2',)
                with self.assertRaises(AssertionError):
                    self.suite._preserved(before, helpers.state())

    def test_witness_baseline_requires_settled_selection_and_exact_identity(self):
        marker = SimpleNamespace(Document=SimpleNamespace(Name='foreign'),
                                 Name='Keep')
        for observed in (
            (), (('different', 'Keep', ()),),
            (('foreign', 'Different', ()),),
            (('foreign', 'Keep', ('Face1',)),),
            (('foreign', 'Keep', ()), ('source', 'Track', ())),
        ):
            with self.subTest(observed=observed):
                gui_host = SimpleNamespace(Selection=SimpleNamespace(
                    getSelection=lambda document: [marker],
                ))
                helpers = SimpleNamespace(settle=Mock(), state=lambda: {
                    'selection': observed,
                })
                with self.assertRaises(AssertionError):
                    self.suite._witness_baseline(helpers, gui_host, marker)

        selected = [marker]
        gui_host = SimpleNamespace(Selection=SimpleNamespace(
            getSelection=lambda document: list(selected),
        ))
        helpers = SimpleNamespace(settle=selected.clear,
                                  state=lambda: {'selection': ()})
        with self.assertRaises(AssertionError):
            self.suite._witness_baseline(helpers, gui_host, marker)

        selected.append(marker)
        expected = {'selection': (('foreign', 'Keep', ()),)}
        helpers = SimpleNamespace(settle=Mock(), state=lambda: expected)
        self.assertEqual(
            self.suite._witness_baseline(helpers, gui_host, marker), expected,
        )

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


class ReaGuiControls(unittest.TestCase):
    """Additive B/C controls must not inherit L1 input/publication scope."""

    @staticmethod
    def environment(stage='gui'):
        return dict(environment(), TRACKTEMPLATE_GUI_WORKLOAD='rea-bc',
                    GITHUB_REF='refs/heads/codex/rea-bc-exit-profile',
                    L1_GUI_STAGE=stage, L1_LIFECYCLE_DIAGNOSTIC='false')

    def authority(self, stage='gui'):
        record = {
            'schema': 1, 'scope_id': 'REA-BC-LIFECYCLE-GUI-001',
            'workload': 'rea-bc', 'stage': stage,
            'source_commit': 'a' * 40,
            'source_ref': 'refs/heads/codex/rea-bc-exit-profile',
            'source_tree_sha256': 'b' * 64,
            'owner': 'Richard-Gnitnub', 'execution_authorized': True,
            'independent_review': 'PASS', 'run_attempt': 1,
            'decision_id': 'synthetic-owner-record', 'dispatch_nonce': 'one',
            'gui_entry_sha256': 'c' * 64,
            'control_files_sha256': dict.fromkeys(gui.REA_CONTROL_FILES,
                                                 'd' * 64),
            'input_hashes': dict.fromkeys(gui.REA_INPUTS, 'e' * 64),
            'freecad_limits': vars(gui.limits(stage, 'rea-bc')),
            'display_limits': vars(gui.display_limits(stage, 'rea-bc')),
            'initial_reserve_mib': 8192, 'software_renderer': 'llvmpipe',
            'external_inputs': 0, 'private_inputs': 0,
            'historical_repair_allowance_consumed': True,
            'automatic_retry': False,
            'handling_review': {
                'decision_sha256': 'f' * 64, 'independent_review': 'PASS',
                'public_research_screenshots': True,
                'retention_days': 30, 'independent_preservation': True,
                'readiness_images': 1, 'gui_images': 13,
                'source_archive_upload': False, 'operator_documents': False,
                'exact_exports': False, 'fcstd_upload': False,
            },
            'gui_recovery': {
                'status': 'PASS', 'independent_review': 'PASS',
                'source_commit': 'a' * 40, 'evidence_sha256': '1' * 64,
            },
            'prior_native_evidence': {
                'status': 'PASS', 'independent_review': 'PASS',
                'run_id': 40, 'evidence_sha256': '2' * 64,
                'source_compatibility_review_sha256': '3' * 64,
            },
        }
        if stage == 'gui':
            ready = self.authority('readiness')
            record['gui_readiness_review'] = {
                key: copy.deepcopy(ready[key]) for key in (
                    'scope_id', 'workload', 'stage', 'source_commit',
                    'source_tree_sha256', 'gui_entry_sha256',
                    'control_files_sha256', 'input_hashes',
                    'freecad_limits', 'display_limits', 'handling_review',
                )
            }
            record['gui_readiness_review'].update(
                status='PASS', independent_review='PASS', run_id=41,
                tests=1, skips=0, run_attempt=1, cleanup=True,
                evidence_verified=True, independent_preservation=True,
                evidence_sha256='4' * 64, result_review_sha256='5' * 64,
                preservation_review_sha256='6' * 64,
                sentinel='REA B/C hosted GUI readiness passed',
            )
        return record

    def test_workload_is_explicit_and_l1_remains_default(self):
        self.assertEqual(gui.selected_workload({}), 'l1')
        self.assertEqual(gui.selected_workload(self.environment()), 'rea-bc')
        for value in ('', 'REA', 'native', 'l1,rea-bc'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                gui.selected_workload({'TRACKTEMPLATE_GUI_WORKLOAD': value})
        self.assertEqual(gui.limits('gui').timeout_seconds, 7200)
        self.assertEqual(gui.display_limits('gui').timeout_seconds, 7300)
        self.assertEqual(gui.limits('gui', 'rea-bc').timeout_seconds, 900)
        self.assertEqual(gui.display_limits('gui', 'rea-bc').timeout_seconds,
                         1000)
        self.assertEqual(gui.limits('readiness', 'rea-bc').timeout_seconds, 90)

    def test_candidate_host_ref_rerun_debug_and_local_refused(self):
        memory = ('MemTotal: 16777216 kB\nMemAvailable: 12845056 kB\n'
                  'SwapTotal: 0 kB\nSwapFree: 0 kB\n')
        gui.validate_host(self.environment(), memory)
        for key, value in (('GITHUB_REF', 'refs/heads/main'),
                           ('GITHUB_REF', 'refs/heads/unreviewed'),
                           ('GITHUB_RUN_ATTEMPT', '2'),
                           ('RUNNER_ENVIRONMENT', 'self-hosted'),
                           ('RUNNER_DEBUG', '1'),
                           ('L1_LIFECYCLE_DIAGNOSTIC', 'true')):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                gui.validate_host(dict(self.environment(), **{key: value}), memory)
        with self.assertRaises(ValueError):
            gui.validate_host(self.environment(), memory.replace('12845056',
                                                               '12582912'))

    def test_separate_handling_recovery_and_native_review_required(self):
        good = self.authority()
        gui.validate_authority(good, self.environment())
        changes = {'scope_id': gui.SCOPE, 'workload': 'l1',
                   'source_ref': 'refs/heads/main', 'source_commit': '0' * 40,
                   'source_tree_sha256': '', 'execution_authorized': False,
                   'independent_review': 'PENDING', 'external_inputs': 1,
                   'private_inputs': 1, 'automatic_retry': True,
                   'historical_repair_allowance_consumed': False,
                   'gui_entry_sha256': 'bad', 'control_files_sha256': {},
                   'input_hashes': {}, 'handling_review': {},
                   'gui_recovery': {}, 'prior_native_evidence': {},
                   'gui_readiness_review': {}}
        for key, value in changes.items():
            with self.subTest(key=key), self.assertRaises(ValueError):
                gui.validate_authority(dict(good, **{key: value}),
                                       self.environment())
        for key, value in (('fcstd_upload', True), ('retention_days', 90),
                           ('public_research_screenshots', False),
                           ('decision_sha256', ''), ('gui_images', 12)):
            bad = copy.deepcopy(good)
            bad['handling_review'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                gui.validate_authority(bad, self.environment())

    def test_readiness_is_separate_exact_source_and_complete(self):
        gui.validate_authority(self.authority('readiness'),
                               self.environment('readiness'))
        for key, value in (('run_id', 42), ('tests', 0), ('skips', 1),
                           ('cleanup', False), ('source_commit', '0' * 40),
                           ('source_tree_sha256', '0' * 64),
                           ('input_hashes', {}), ('handling_review', {}),
                           ('result_review_sha256', ''),
                           ('preservation_review_sha256', '')):
            bad = self.authority()
            bad['gui_readiness_review'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                gui.validate_authority(bad, self.environment())

    def test_zero_external_acquisition_never_downloads_or_deploys(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence').mkdir()
            (work / 'control.json').write_text(json.dumps(self.authority()))
            with patch.dict(os.environ, self.environment(), clear=True), \
                    patch.object(gui.native, 'acquire', side_effect=AssertionError(
                        'B/C attempted L1 acquisition')):
                gui.acquire(work)
            config = json.loads((work / 'gui-run-config.json').read_text())
            self.assertEqual(config['inputs'], [])
            self.assertEqual(config['input_hashes'], self.authority()['input_hashes'])
            self.assertEqual(config['external_inputs'], 0)
            self.assertFalse((work / 'inputs.tar').exists())

    def test_900_second_budget_preserves_ten_minute_finalization_reserve(self):
        env = dict(self.environment(), L1_JOB_START_SECONDS='1000')
        gui.require_rea_finalization_time('gui', env, 2200)
        with self.assertRaises(ValueError):
            gui.require_rea_finalization_time('gui', env, 2201)
        with self.assertRaises(ValueError):
            gui.require_rea_finalization_time('gui', env, 999)

    def test_candidate_macro_is_literal_and_env_contains_no_secrets(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence').mkdir()
            (work / 'gui-run-config.json').write_text('{}')
            (work / 'evidence/gui-authority.json').write_text('{}')
            with patch.dict(os.environ, dict(self.environment(),
                                            GITHUB_TOKEN='do-not-forward'),
                            clear=True):
                macro = gui.write_gui_macro(work)
                clean = gui.child_environment(work)
                argv = gui.gui_argv(clean, macro)
            self.assertIn('hosted_rea_trackwork_gui_suite.start()',
                          macro.read_text())
            self.assertNotIn('hosted_l1_gui_suite.start()', macro.read_text())
            self.assertNotIn('GITHUB_TOKEN', clean)
            self.assertIn('--env=TRACKTEMPLATE_GUI_WORKLOAD=rea-bc', argv)
            self.assertEqual(gui.guard._payload_command(argv)[-1], str(macro))

    def test_exact_operation_counts_reject_low_high_bool_and_missing(self):
        counts = gui.rea_counts('gui')
        self.assertEqual(counts, {
            'tests': 1, 'fresh_documents': 2, 'reopens': 1,
            'source_records_created': 2, 'successful_parameter_updates': 2,
            'no_op_applies': 1, 'undo_redo_pairs': 1,
            'host_invalidation_cases': 1, 'explicit_rebuilds': 3,
            'adopted_view_rollback_cases': 1, 'actual_viewport_picks': 2,
            'visible_input_refusals': 2, 'operator_label_cases': 1,
            'profile_selections': 2, 'profile_deselections': 1,
            'selected_profile_reopens': 1, 'viewport_images': 8,
            'dialog_images': 5, 'screenshots_total': 13,
        })
        for key, value in counts.items():
            for bad in (value - 1, value + 1, True, None):
                with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                    gui.validate_rea_counts(dict(counts, **{key: bad}), 'gui')
        gui.validate_rea_counts(counts, 'gui')
        with self.assertRaises(ValueError):
            gui.validate_rea_counts(dict(counts, extra=1), 'gui')
        ready = gui.rea_counts('readiness')
        self.assertEqual(ready['fresh_documents'], 1)
        self.assertEqual(ready['source_records_created'], 0)
        self.assertEqual(ready['screenshots_total'], 1)

    def test_unique_result_parser_rejects_missing_duplicate_and_malformed(self):
        record = {'workload': 'rea-bc', 'stage': 'gui', 'status': 'PASS'}
        text = 'TRACKTEMPLATE_REA_TRACKWORK_GUI=' + json.dumps(record)
        self.assertEqual(gui.rea_report(text), record)
        for bad in ('', text + '\n' + text,
                    'TRACKTEMPLATE_REA_TRACKWORK_GUI={"stage":"gui","stage":"gui"}',
                    'TRACKTEMPLATE_REA_TRACKWORK_GUI={"value":NaN}',
                    'TRACKTEMPLATE_REA_TRACKWORK_GUI={"value":1e999}',
                    'TRACKTEMPLATE_REA_TRACKWORK_GUI={"value":-1e999}',
                    'TRACKTEMPLATE_REA_TRACKWORK_GUI=[]'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                gui.rea_report(bad)

    def test_candidate_evidence_excludes_unknown_media_and_documents(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence/gui').mkdir(parents=True)
            (work / 'evidence/gui/result.json').write_text('{}')
            (work / 'evidence/gui/to-b8.png').write_bytes(b'png')
            gui.validate_rea_evidence(work, stage='gui')
            for name in ('private.FCStd', 'private.FCStd1', 'unknown.png',
                         'archive.zip', 'upstream.pas', 'part.brep', 'part.step'):
                path = work / 'evidence/gui' / name
                path.write_bytes(b'not-approved')
                with self.subTest(name=name), self.assertRaises(ValueError):
                    gui.validate_rea_evidence(work, stage='gui')
                path.unlink()
            linked = work / 'evidence/gui/linked.json'
            linked.symlink_to(work / 'evidence/gui/result.json')
            with self.assertRaises(ValueError):
                gui.validate_rea_evidence(work, stage='gui')

    def test_new_entry_import_starts_no_host_or_process(self):
        path = ROOT / 'tests/hosted_rea_trackwork_gui_suite.py'
        self.assertTrue(path.is_file(), 'Missing B/C GUI entry')
        spec = importlib.util.spec_from_file_location('rea_gui_entry', path)
        suite = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'FreeCAD': None, 'FreeCADGui': None,
                                     'PySide6': None, 'pivy': None}), \
                patch.object(subprocess, 'Popen', side_effect=AssertionError(
                    'Import started a process')):
            spec.loader.exec_module(suite)
        self.assertTrue(callable(suite.start))
        self.assertEqual(suite.SCOPE, 'REA-BC-LIFECYCLE-GUI-001')

    def test_cleanup_finds_observers_among_native_and_python_views(self):
        suite = self._entry()
        first = SimpleNamespace(_observer_app=object())
        second = SimpleNamespace(_observer_app=None)
        document = SimpleNamespace(Objects=[
            SimpleNamespace(ViewObject=SimpleNamespace()),
            SimpleNamespace(ViewObject=None),
            SimpleNamespace(ViewObject=SimpleNamespace(Proxy=None)),
            SimpleNamespace(ViewObject=SimpleNamespace(Proxy=first)),
            SimpleNamespace(ViewObject=SimpleNamespace(Proxy=object())),
            SimpleNamespace(ViewObject=SimpleNamespace(Proxy=second)),
        ])
        self.assertEqual(suite._observer_proxies(document), (first, second))

        class BrokenView:
            @property
            def Proxy(self):
                raise RuntimeError('Unreadable observer ownership')

        document.Objects.append(SimpleNamespace(ViewObject=BrokenView()))
        with self.assertRaisesRegex(RuntimeError, 'observer ownership'):
            suite._observer_proxies(document)

    def test_workflow_keeps_l1_and_candidate_mutually_exclusive(self):
        text = (ROOT / '.github/workflows/l1-gui-validation.yml').read_text()
        self.assertIn('default: l1', text)
        self.assertIn("inputs.workload == 'rea-bc'", text)
        self.assertIn("refs/heads/codex/rea-bc-exit-profile", text)
        self.assertIn("inputs.workload == 'l1'", text)
        self.assertIn('timeout-minutes: 45', text)
        self.assertEqual(text.count('environment: l1-private-validation'), 1)
        self.assertIn('TRACKTEMPLATE_GUI_WORKLOAD: ${{ inputs.workload }}', text)


    def _receipt_fixture(self, work, stage='gui'):
        control = self.authority(stage)
        for group in ('control_files_sha256', 'input_hashes'):
            control[group] = {name: gui.digest(ROOT / name)
                              for name in control[group]}
        control['gui_entry_sha256'] = gui.digest(ROOT / gui.REA_ENTRY)
        (work / 'control.json').write_text(json.dumps(control))
        directory = work / 'evidence/gui'
        directory.mkdir(parents=True)
        screenshots = []
        for name in sorted(gui.rea_images(stage)):
            path = directory / name
            path.write_bytes(b'\x89PNG\r\n\x1a\n' + name.encode())
            screenshots.append({'path': name, 'sha256': gui.digest(path),
                                'bytes': path.stat().st_size})
        receipt = {
            'status': 'PASS', 'stage': stage, 'scope_id': gui.REA_SCOPE,
            'workload': 'rea-bc', 'profile': gui.original.EXPECTED_PROFILE,
            'source_commit': control['source_commit'],
            'source_tree_sha256': control['source_tree_sha256'],
            'input_hashes': control['input_hashes'],
            'gui_entry_sha256': control['gui_entry_sha256'],
            'input_bindings_unchanged': True, 'owned_documents_closed': True,
            'owned_windows_closed': True, 'cleanup_errors': [],
            'documents_remaining': 0, 'failures': 0, 'errors': 0, 'skips': 0,
            'geometry_builds': 0 if stage == 'readiness' else 8,
            'sentinel': gui.sentinel(stage, 'rea-bc'),
            'checks': gui.rea_counts(stage), 'screenshots': screenshots,
            'total_seconds': 20.0,
            'renderer': {'platform': 'xcb', 'gui_up': True,
                         'widget_valid': True, 'renderer': 'llvmpipe',
                         'vendor': 'Mesa', 'version': '4.5'},
        }
        return control, receipt

    def test_complete_receipt_requires_owned_cleanup_runtime_and_exact_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            control, good = self._receipt_fixture(work)
            with patch.object(gui, 'rea_source_tree', return_value='b' * 64):
                gui.validate_rea_receipt(good, work, stage='gui')
                for key, value in (
                    ('owned_windows_closed', False),
                    ('owned_documents_closed', False), ('documents_remaining', 1),
                    ('cleanup_errors', ['incomplete']), ('skips', 1),
                    ('errors', 1), ('failures', 1), ('geometry_builds', 7),
                    ('input_bindings_unchanged', False),
                    ('source_commit', '0' * 40), ('source_tree_sha256', ''),
                    ('input_hashes', {}), ('gui_entry_sha256', '0' * 64),
                    ('sentinel', 'other'), ('checks', {}), ('status', 'FAIL'),
                    ('documents_remaining', False),
                ):
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        gui.validate_rea_receipt(dict(good, **{key: value}),
                                                work, stage='gui')
                for key, value in (('platform', 'offscreen'), ('gui_up', False),
                                   ('widget_valid', False),
                                   ('renderer', 'hardware'), ('vendor', '')):
                    bad = copy.deepcopy(good)
                    bad['renderer'][key] = value
                    with self.subTest(renderer=key), self.assertRaises(ValueError):
                        gui.validate_rea_receipt(bad, work, stage='gui')
            with patch.object(gui, 'rea_source_tree', return_value='0' * 64), \
                    self.assertRaises(ValueError):
                gui.validate_rea_receipt(good, work, stage='gui')

    def test_image_omission_duplicate_path_hash_and_unlisted_media_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            _, good = self._receipt_fixture(work)
            with patch.object(gui, 'rea_source_tree', return_value='b' * 64):
                bad = copy.deepcopy(good)
                bad['screenshots'].pop()
                with self.assertRaises(ValueError):
                    gui.validate_rea_receipt(bad, work, stage='gui')
                for key, value in (('path', '../outside.png'),
                                   ('path', 'unexpected.png'),
                                   ('sha256', '0' * 64), ('bytes', 0),
                                   ('bytes', True)):
                    bad = copy.deepcopy(good)
                    bad['screenshots'][0][key] = value
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        gui.validate_rea_receipt(bad, work, stage='gui')
                bad = copy.deepcopy(good)
                bad['screenshots'][0] = bad['screenshots'][1]
                with self.assertRaises(ValueError):
                    gui.validate_rea_receipt(bad, work, stage='gui')
                (work / 'evidence/gui/unlisted.png').write_bytes(b'png')
                with self.assertRaises(ValueError):
                    gui.validate_rea_receipt(good, work, stage='gui')

    def test_empty_readiness_proves_no_geometry_and_one_panel_image(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            _, good = self._receipt_fixture(work, 'readiness')
            with patch.object(gui, 'rea_source_tree', return_value='b' * 64):
                gui.validate_rea_receipt(good, work, stage='readiness')
                for key, value in (('geometry_builds', 1), ('stage', 'gui')):
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        gui.validate_rea_receipt(dict(good, **{key: value}),
                                                work, stage='readiness')
                bad = copy.deepcopy(good)
                bad['checks']['source_records_created'] = 1
                with self.assertRaises(ValueError):
                    gui.validate_rea_receipt(bad, work, stage='readiness')

    def test_temporary_document_cleanup_requires_exact_manifest_and_bytes(self):
        for changed in (False, True):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as tmp:
                work = Path(tmp)
                (work / 'evidence/gui').mkdir(parents=True)
                (work / 'test-data').mkdir()
                saved = work / 'test-data/research.FCStd'
                saved.write_bytes(b'owned fixture')
                row = {'path': 'test-data/research.FCStd',
                       'sha256': gui.digest(saved), 'bytes': saved.stat().st_size}
                (work / 'evidence/gui/result.json').write_text(json.dumps({
                    'temporary_documents': [row],
                }))
                if changed:
                    saved.write_bytes(b'changed')
                    with self.assertRaises(ValueError):
                        gui.cleanup_rea_documents(work)
                    self.assertTrue(saved.exists())
                else:
                    gui.cleanup_rea_documents(work)
                    self.assertFalse(saved.exists())
                    receipt = json.loads((work / 'evidence/gui-document-cleanup.json').read_text())
                    self.assertTrue(receipt['cleanup'])
                    self.assertEqual(receipt['removed'], [row])
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / 'evidence/gui').mkdir(parents=True)
            (work / 'test-data').mkdir()
            saved = work / 'test-data/unknown.FCStd'
            saved.write_bytes(b'unknown')
            (work / 'evidence/gui/result.json').write_text('{}')
            with self.assertRaises(ValueError):
                gui.cleanup_rea_documents(work)
            self.assertTrue(saved.exists())

    def test_display_candidate_deadline_and_default_l1_stay_distinct(self):
        self.assertEqual(gui.display_properties('gui', 'rea-bc')['RuntimeMaxSec'],
                         '1000')
        self.assertEqual(gui.display_properties('readiness', 'rea-bc')['RuntimeMaxSec'],
                         '190')
        self.assertEqual(gui.display_properties()['RuntimeMaxSec'], '7300')
        self.assertEqual(gui.display_properties('gui', 'rea-bc')['MemorySwapMax'],
                         '0')

    def test_source_manifest_binds_bytes_without_child_git_or_host_import(self):
        path = ROOT / gui.REA_ENTRY
        spec = importlib.util.spec_from_file_location('rea_gui_manifest', path)
        suite = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(suite)
        case = suite.ReaGui('test_authorised_gui_stage')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'tracktemplate').mkdir()
            (root / 'tracktemplate/example.py').write_text('answer = 42\n')
            hashes = {'tracktemplate/example.py': gui.digest(
                root / 'tracktemplate/example.py')}
            digest = gui.hashlib.sha256(json.dumps(
                hashes, sort_keys=True, separators=(',', ':'),
            ).encode()).hexdigest()
            with patch.object(suite, 'ROOT', root), \
                    patch.object(subprocess, 'Popen', side_effect=AssertionError(
                        'Child source check attempted git')):
                case.assert_source_tree({'product_files_sha256': hashes},
                                        {'source_tree_sha256': digest})
                (root / 'tracktemplate/example.py').write_text('changed\n')
                with self.assertRaises(AssertionError):
                    case.assert_source_tree({'product_files_sha256': hashes},
                                            {'source_tree_sha256': digest})

    def test_event_loop_reports_success_only_for_exact_one_unskipped_test(self):
        path = ROOT / gui.REA_ENTRY
        spec = importlib.util.spec_from_file_location('rea_gui_start', path)
        suite = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(suite)
        for passed, count, skips, exit_code in (
            (True, 1, [], 0), (False, 1, [], 1), (True, 0, [], 1),
            (True, 2, [], 1), (True, 1, ['skipped'], 1),
        ):
            with self.subTest(passed=passed, count=count, skips=skips):
                callbacks, exit_qt = [], Mock()
                pyside = ModuleType('PySide6')
                pyside.QtCore = SimpleNamespace(
                    QTimer=SimpleNamespace(singleShot=lambda delay, callback:
                                           callbacks.append((delay, callback))),
                    QCoreApplication=SimpleNamespace(exit=exit_qt),
                )
                case = suite.ReaGui('test_authorised_gui_stage')
                case.receipt = {'status': 'PASS', 'sentinel': 'bounded success'}
                runner = Mock()
                runner.run.return_value = SimpleNamespace(
                    wasSuccessful=lambda: passed, testsRun=count, skipped=skips)
                output = io.StringIO()
                with patch.dict(sys.modules, {'PySide6': pyside}), \
                        patch.object(suite, 'ReaGui', return_value=case), \
                        patch.object(suite.unittest, 'TextTestRunner', return_value=runner), \
                        patch.object(sys, 'stdout', output):
                    suite.start()
                    self.assertEqual(len(callbacks), 1)
                    exit_qt.assert_not_called()
                    callbacks[0][1]()
                exit_qt.assert_called_once_with(exit_code)
                self.assertEqual(runner.run.call_args.args[0].countTestCases(), 1)
                self.assertEqual(suite.PREFIX in output.getvalue(), exit_code == 0)

    @staticmethod
    def _entry():
        spec = importlib.util.spec_from_file_location(
            'rea_gui_entry_review', ROOT / gui.REA_ENTRY,
        )
        suite = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(suite)
        return suite

    def test_receipt_elapsed_time_must_be_finite_and_within_stage_limit(self):
        for stage, limit in (('readiness', 90), ('gui', 900)):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                _, receipt = self._receipt_fixture(work, stage)
                with patch.object(gui, 'rea_source_tree', return_value='b' * 64):
                    for value in (None, True, '20', -1, float('nan'),
                                  float('inf'), -float('inf'), limit + 0.01,
                                  10 ** 400):
                        with self.subTest(value=value), self.assertRaises(ValueError):
                            gui.validate_rea_receipt(
                                dict(receipt, total_seconds=value), work,
                                stage=stage,
                            )
                    gui.validate_rea_receipt(
                        dict(receipt, total_seconds=limit), work, stage=stage,
                    )

    def test_archive_boundaries_reject_other_stage_image(self):
        for stage, extra in (('readiness', 'to-b8.png'),
                             ('gui', 'readiness-panel.png')):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                _, receipt = self._receipt_fixture(work, stage)
                (work / 'evidence/gui' / extra).write_bytes(b'other-stage')
                with patch.dict(os.environ, self.environment(stage), clear=True), \
                        patch.object(gui, 'rea_source_tree', return_value='b' * 64):
                    with self.assertRaisesRegex(ValueError, 'Unexpected B/C evidence'):
                        gui.validate_rea_receipt(receipt, work, stage=stage)
                    with self.assertRaisesRegex(ValueError, 'Unexpected B/C evidence'):
                        gui.exclude_gui_copy(work)
                    # Failed runs must not publish an out-of-stage image either.
                    with patch.object(gui.native, 'verify_artifact',
                                      side_effect=ValueError('injected failure')), \
                            patch.object(gui.native, 'evidence_archive') as archive, \
                            self.assertRaisesRegex(ValueError, 'Unexpected B/C evidence'):
                        gui.publish(work)
                    archive.assert_not_called()

    def test_gui_document_inventory_rejects_hidden_geometry_objects(self):
        case = self._entry().ReaGui('test_authorised_gui_stage')
        doc = SimpleNamespace(Objects=[])
        source = SimpleNamespace(Name='Source', Document=doc,
                                 TypeId='App::FeaturePython', PropertiesList=[])
        baseline = [SimpleNamespace(Name=name) for name in
                    ('Settings', 'HostA', 'HostB')] + [source]
        doc.Objects = baseline
        case.assert_document_inventory(source)
        for bad in (baseline + [SimpleNamespace(Name='Point001')],
                    baseline + [SimpleNamespace(Name='Rail001')],
                    baseline[:-1], baseline + [source]):
            with self.subTest(names=[item.Name for item in bad]), \
                    self.assertRaises(AssertionError):
                doc.Objects = bad
                case.assert_document_inventory(source)
        doc.Objects = baseline
        source.TypeId = 'Part::Feature'
        with self.assertRaises(AssertionError):
            case.assert_document_inventory(source)
        source.TypeId = 'App::FeaturePython'
        source.PropertiesList = ['Shape']
        with self.assertRaises(AssertionError):
            case.assert_document_inventory(source)

    def test_nested_manager_releases_polling_timer_before_modal_click(self):
        for click_error in (False, True):
            with self.subTest(click_error=click_error):
                self._nested_manager_case(click_error)

    def _nested_manager_case(self, click_error):
        suite = self._entry()
        case = suite.ReaGui('test_authorised_gui_stage')
        state = {'active': None, 'timers': [], 'queue': [], 'actions': 0}

        class Timer:
            def __init__(self):
                self.active = False
                self.busy = False
                self.timeout = SimpleNamespace(connect=self.connect)
                state['timers'].append(self)

            def connect(self, callback):
                self.callback = callback

            def setInterval(self, value):
                pass

            def start(self):
                self.active = True

            def stop(self):
                self.active = False

            def emit(self):
                if not self.active or self.busy:
                    return
                self.busy = True
                try:
                    self.callback()
                finally:
                    self.busy = False

            @staticmethod
            def singleShot(delay, callback):
                state['queue'].append(callback)

        class Dialog:
            turnout_manager_button = object()

            def isVisible(self):
                return state['active'] is self

            def reject(self):
                if state['active'] is self:
                    state['active'] = None

        class Curve(Dialog):
            pass

        class Manager(Dialog):
            def resize(self, *args):
                pass

        curve, manager = Curve(), Manager()
        doc = object()
        panel = SimpleNamespace(
            controller=SimpleNamespace(document=doc),
            widget=SimpleNamespace(isVisible=lambda: True),
            last_error=None, scroll_area=object(),
        )
        manager._tracktemplate_rea_panel = panel
        manager.mode_tabs = SimpleNamespace(
            indexOf=lambda widget: 0, setCurrentIndex=lambda index: None,
        )
        case.qt = SimpleNamespace(
            QtCore=SimpleNamespace(QTimer=Timer),
            QtWidgets=SimpleNamespace(QApplication=SimpleNamespace(
                activeModalWidget=lambda: state['active'],
            )), isValid=lambda dialog: True,
        )
        case.module = SimpleNamespace(CurveInputDialog=Curve,
                                      TurnoutManagerDialog=Manager)
        case.app = SimpleNamespace(ActiveDocument=doc)
        case.owned_windows = []
        case.receipt = {}
        case.session = object()
        case.qualification = object()
        case.settle = lambda: None

        def click(button):
            if click_error:
                raise RuntimeError('injected modal click failure')
            self.assertIs(button, curve.turnout_manager_button)
            state['active'] = manager
            # Qt refuses reentrant delivery of the currently active timer.
            state['timers'][0].emit()

        def launch(*args):
            state['active'] = curve
            state['timers'][0].emit()
            while state['queue']:
                state['queue'].pop(0)()

        def action(actual_panel, dialog):
            self.assertIs(actual_panel, panel)
            self.assertIs(dialog, manager)
            state['actions'] += 1

        case.click = click
        case.launcher = {'_launch_workflow_with_rea_editor': launch}
        if click_error:
            with self.assertRaisesRegex(RuntimeError, 'injected modal'):
                case.panel(action)
            self.assertIn('injected modal', case.receipt['modal_failure'])
        else:
            case.panel(action)
            self.assertEqual(state['actions'], 1)
        self.assertFalse(state['timers'][0].active)
        self.assertIsNone(state['active'])

    def test_actual_pick_path_uses_qt_click_not_selection_injection(self):
        tree = ast.parse((ROOT / gui.REA_ENTRY).read_text())
        case = next(node for node in tree.body
                    if isinstance(node, ast.ClassDef) and node.name == 'ReaGui')
        pick = next(node for node in case.body
                    if isinstance(node, ast.FunctionDef) and node.name == 'pick')
        calls = [ast.unparse(node.func) for node in ast.walk(pick)
                 if isinstance(node, ast.Call)]
        self.assertIn('view.getPointOnScreen', calls)
        self.assertIn('self.qt.QtTest.QTest.mouseClick', calls)
        self.assertNotIn('self.gui.Selection.addSelection', calls)
        self.assertIn('self.gui.Selection.getSelectionEx', calls)
        method = next(node for node in case.body
                      if isinstance(node, ast.FunctionDef)
                      and node.name == 'full_journey')
        self.assertNotIn('ViewObject.Proxy = None', ast.unparse(method))


class ReaGuardEvidenceRegressions(unittest.TestCase):
    """Use the guard's actual private-profile layout without a host process."""

    def profile(self, work):
        output = work / 'evidence/guard'
        output.mkdir(parents=True)
        _argv, profile = gui.guard._private_profile(
            ['flatpak', 'run', gui.guard.APP_ID, 'synthetic.FCMacro'], output,
        )
        root = Path(profile['path'])
        (root / 'user.cfg').write_bytes(b'private synthetic configuration')
        (root / 'temp/owned.FCStd').write_bytes(b'private synthetic document')
        gui.write(output / 'result.json', {
            'status': 'failed', 'private_profile': profile,
        })
        (output / 'wrapper.stdout').write_text('Synthetic raw failure\n')
        (output / 'watchdog.json').write_text('{"action":"owned-kill"}\n')
        (work / 'evidence/execution.log').write_text('Original exception\n')
        return root

    def test_live_receipt_validation_does_not_move_owned_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            root = self.profile(work)
            before = (root / 'user.cfg').read_bytes()
            gui.validate_rea_evidence(work, stage='readiness')
            self.assertEqual((root / 'user.cfg').read_bytes(), before)
            self.assertFalse((work / 'retained-guard-profile').exists())
            self.assertFalse((work / 'evidence/guard-profile-exclusion.json').exists())

    def test_failed_diagnostics_seal_and_publication_exclude_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            source = self.profile(work)
            original = {str(path.relative_to(source)): path.read_bytes()
                        for path in source.rglob('*') if path.is_file()}
            with patch.dict(os.environ,
                            ReaGuiControls.environment('readiness'), clear=True):
                gui.exclude_gui_copy(work)
                retained = work / 'retained-guard-profile/profile'
                self.assertFalse(source.exists())
                self.assertEqual({str(path.relative_to(retained)): path.read_bytes()
                                  for path in retained.rglob('*') if path.is_file()},
                                 original)
                receipt = work / 'evidence/guard-profile-exclusion.json'
                before = receipt.read_bytes()
                gui.exclude_gui_copy(work)
                self.assertEqual(receipt.read_bytes(), before)
                gui.native.seal(work)
                with patch.object(gui.native, 'verify_artifact',
                                  side_effect=ValueError('Synthetic missing readback')):
                    self.assertEqual(gui.publish(work), 1)
                self.assertEqual(receipt.read_bytes(), before)
            for name in ('evidence.tar', 'publication.tar'):
                with gui.native.tarfile.open(work / name) as archive:
                    names = archive.getnames()
                    self.assertIn('evidence/execution.log', names)
                    self.assertIn('evidence/guard/wrapper.stdout', names)
                    self.assertIn('evidence/guard/watchdog.json', names)
                    self.assertIn('evidence/guard-profile-exclusion.json', names)
                    self.assertFalse(any('/profile/' in member for member in names))
                    self.assertEqual(archive.extractfile(
                        'evidence/execution.log').read(), b'Original exception\n')
            self.assertTrue((retained / 'temp/owned.FCStd').is_file())

    def test_profile_rejects_foreign_receipt_unknown_root_and_owner(self):
        for problem in ('foreign-path', 'unknown-root', 'owner'):
            with self.subTest(problem=problem), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                root = self.profile(work)
                if problem == 'foreign-path':
                    path = work / 'evidence/guard/result.json'
                    record = json.loads(path.read_text())
                    record['private_profile']['path'] = str(work / 'foreign')
                    path.write_text(json.dumps(record))
                if problem == 'unknown-root':
                    (root / 'unknown').mkdir()
                with patch.object(gui.os, 'getuid', return_value=(
                        os.getuid() + 1 if problem == 'owner' else os.getuid())):
                    with self.assertRaises(ValueError):
                        gui.validate_rea_evidence(work, stage='readiness')
                self.assertTrue(root.exists())
                self.assertFalse((work / 'retained-guard-profile').exists())

    def test_profile_rejects_links_and_occupied_retention(self):
        for problem in ('profile', 'nested', 'receipt', 'retention'):
            with self.subTest(problem=problem), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                root = self.profile(work)
                if problem == 'profile':
                    moved = work / 'foreign-profile'
                    root.rename(moved)
                    root.symlink_to(moved, target_is_directory=True)
                elif problem == 'nested':
                    (root / 'temp/linked').symlink_to(root / 'user.cfg')
                elif problem == 'receipt':
                    path = work / 'evidence/guard/result.json'
                    moved = work / 'foreign-result.json'
                    path.rename(moved)
                    path.symlink_to(moved)
                else:
                    (work / 'retained-guard-profile').mkdir()
                with patch.dict(os.environ,
                                ReaGuiControls.environment('readiness'), clear=True):
                    with self.assertRaises(ValueError):
                        gui.exclude_gui_copy(work)
                self.assertTrue(root.exists())

    def test_repeated_exclusion_refuses_retained_tree_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self.profile(work)
            with patch.dict(os.environ,
                            ReaGuiControls.environment('readiness'), clear=True):
                gui.exclude_gui_copy(work)
                retained = work / 'retained-guard-profile/profile/user.cfg'
                retained.write_bytes(b'changed')
                with self.assertRaises(ValueError):
                    gui.exclude_gui_copy(work)
                self.assertFalse((work / 'evidence.tar').exists())

    def test_known_profile_does_not_admit_other_evidence(self):
        for name in ('guard/unknown.json', 'guard/shutdown-request.json',
                     'guard/gui-completion.json', 'guard/watchdog2.json',
                     'gui/to-b8.png', 'gui/private.FCStd'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                root = self.profile(work)
                path = work / 'evidence' / name
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(b'unapproved')
                with self.assertRaises(ValueError):
                    gui.validate_rea_evidence(work, stage='readiness')
                self.assertTrue(root.exists())

    def test_actual_guard_early_failure_preserves_raw_stdout(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            runtime = work / 'private-runtime'
            runtime.mkdir(mode=0o700)
            command = Mock(return_value=subprocess.CompletedProcess(
                [], 0, gui.guard.APP_ID + ' 999999\n', '',
            ))
            process = Mock(side_effect=AssertionError('No host process'))
            result = gui.guard.run_guarded_flatpak(
                ['flatpak', 'run', gui.guard.APP_ID, 'synthetic.FCMacro'],
                limits=gui.limits('readiness', 'rea-bc'),
                evidence_dir=work / 'evidence/guard', isolate_profile=True,
                context=gui.guard.GuardContext(run=command, popen=process,
                                               runtime_dir=runtime),
            )
            self.assertEqual(result['failure_reason'], 'foreign-freecad-instance')
            process.assert_not_called()
            gui.validate_rea_evidence(work, stage='readiness')
            with patch.dict(os.environ,
                            ReaGuiControls.environment('readiness'), clear=True):
                gui.exclude_gui_copy(work)
                gui.native.seal(work)
            self.assertTrue((work / 'evidence.tar').is_file())




class StraightGuiControls(unittest.TestCase):
    """The straight journey has its own exact source and image authority."""

    @staticmethod
    def environment(stage='gui'):
        return dict(ReaGuiControls.environment(stage),
                    TRACKTEMPLATE_GUI_WORKLOAD='rea-bc-straight',
                    GITHUB_REF='refs/heads/codex/rea-bc-straight-closure')

    def authority(self, stage='gui'):
        record = ReaGuiControls().authority(stage)
        record.update(scope_id='REA-BC-STRAIGHT-GUI-001',
                      workload='rea-bc-straight',
                      source_ref=self.environment(stage)['GITHUB_REF'])
        record['handling_review']['gui_images'] = 7
        if stage == 'gui':
            ready = record['gui_readiness_review']
            ready.update(scope_id=record['scope_id'], workload=record['workload'],
                         handling_review=copy.deepcopy(record['handling_review']),
                         sentinel='REA B straight hosted GUI readiness passed')
        return record

    def test_only_named_straight_scope_and_ref_are_admitted(self):
        self.assertEqual(gui.selected_workload(self.environment()),
                         'rea-bc-straight')
        self.assertEqual(gui.rea_scope('rea-bc-straight'),
                         'REA-BC-STRAIGHT-GUI-001')
        self.assertEqual(gui.rea_ref('rea-bc-straight'),
                         self.environment()['GITHUB_REF'])
        self.assertEqual(gui.rea_scope(), 'REA-BC-LIFECYCLE-GUI-001')
        for value in ('straight', 'rea-bc-straight-gui', '', 'l1,rea-bc'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                gui.selected_workload({'TRACKTEMPLATE_GUI_WORKLOAD': value})
        for stage in ('gui', 'readiness'):
            self.assertEqual(vars(gui.limits(stage, 'rea-bc-straight')),
                             vars(gui.limits(stage, 'rea-bc')))
            self.assertEqual(vars(gui.display_limits(stage, 'rea-bc-straight')),
                             vars(gui.display_limits(stage, 'rea-bc')))

    def test_exact_twenty_one_counters_and_seven_full_images(self):
        counts = gui.rea_counts('gui', 'rea-bc-straight')
        self.assertEqual(counts, {
            'tests': 1, 'fresh_documents': 2, 'reopens': 1,
            'source_records_created': 2, 'successful_parameter_updates': 4,
            'no_op_applies': 1, 'undo_redo_pairs': 0,
            'host_invalidation_cases': 1, 'explicit_rebuilds': 2,
            'adopted_view_rollback_cases': 0, 'actual_viewport_picks': 2,
            'visible_input_refusals': 1, 'operator_label_cases': 1,
            'profile_selections': 2, 'profile_deselections': 0,
            'selected_profile_reopens': 1, 'viewport_images': 5,
            'dialog_images': 2, 'screenshots_total': 7,
            'straight_boundary_edits': 2, 'initial_straight_source_roads': 3,
        })
        self.assertEqual(gui.rea_images('gui', 'rea-bc-straight'), {
            'to-straight.png', 'to-straight-fields.png',
            'upper-out-refused.png', 'straight-reopened-empty.png',
            'straight-rebuilt-picked.png', 'to-b8-returned.png',
            'xo-straight.png',
        })
        for key, expected in counts.items():
            for bad in (expected + 1, True, float(expected)):
                with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                    gui.validate_rea_counts(dict(counts, **{key: bad}), 'gui',
                                            'rea-bc-straight')
        ready = gui.rea_counts('readiness', 'rea-bc-straight')
        self.assertEqual({k: v for k, v in ready.items() if v}, {
            'tests': 1, 'fresh_documents': 1, 'dialog_images': 1,
            'screenshots_total': 1,
        })
        self.assertEqual(gui.rea_images('readiness', 'rea-bc-straight'),
                         {'straight-readiness-panel.png'})
        self.assertEqual(len(gui.rea_images('gui')), 13)

    def test_prior_image_scope_and_wrong_ref_cannot_authorise_straight(self):
        for stage in ('readiness', 'gui'):
            good = self.authority(stage)
            env = self.environment(stage)
            gui.validate_rea_authority(good, env)
            for key, value in (
                ('scope_id', 'REA-BC-LIFECYCLE-GUI-001'),
                ('workload', 'rea-bc'),
                ('source_ref', 'refs/heads/codex/rea-bc-exit-profile'),
                ('automatic_retry', True), ('execution_authorized', False),
            ):
                with self.subTest(stage=stage, key=key), self.assertRaises(ValueError):
                    gui.validate_rea_authority(dict(good, **{key: value}), env)
            for key, value in (('gui_images', 13), ('readiness_images', 0),
                               ('fcstd_upload', True), ('decision_sha256', '')):
                bad = copy.deepcopy(good)
                bad['handling_review'][key] = value
                with self.subTest(stage=stage, key=key), self.assertRaises(ValueError):
                    gui.validate_rea_authority(bad, env)
            with self.assertRaises(ValueError):
                gui.validate_rea_authority(good, dict(
                    env, GITHUB_REF='refs/heads/codex/rea-bc-exit-profile'))

    def test_native_recovery_and_exact_readiness_remain_required(self):
        good, env = self.authority(), self.environment()
        for group in ('gui_recovery', 'prior_native_evidence',
                      'gui_readiness_review'):
            bad = copy.deepcopy(good)
            bad[group] = {}
            with self.subTest(group=group), self.assertRaises(ValueError):
                gui.validate_rea_authority(bad, env)
        for key, value in (('workload', 'rea-bc'), ('skips', 1),
                           ('source_commit', 'b' * 40), ('cleanup', False),
                           ('sentinel', 'REA B/C hosted GUI readiness passed')):
            bad = copy.deepcopy(good)
            bad['gui_readiness_review'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                gui.validate_rea_authority(bad, env)

    def test_image_stage_unknown_and_symlink_stay_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            directory = work / 'evidence/gui'
            directory.mkdir(parents=True)
            (directory / 'result.json').write_text('{}')
            selected = directory / 'straight-readiness-panel.png'
            selected.write_bytes(b'\x89PNG\r\n\x1a\n')
            gui.validate_rea_evidence(work, stage='readiness',
                                      workload='rea-bc-straight')
            for name in ('to-straight.png', 'readiness-panel.png', 'unknown.png'):
                path = directory / name
                path.write_bytes(b'\x89PNG\r\n\x1a\n')
                try:
                    with self.subTest(name=name), self.assertRaises(ValueError):
                        gui.validate_rea_evidence(
                            work, stage='readiness', workload='rea-bc-straight')
                finally:
                    path.unlink()
            selected.unlink()
            selected.symlink_to(directory / 'result.json')
            with self.assertRaises(ValueError):
                gui.validate_rea_evidence(work, stage='readiness',
                                          workload='rea-bc-straight')

    def test_straight_entry_stays_one_named_gui_test(self):
        tree = ast.parse((ROOT / gui.REA_ENTRY).read_text())
        cls = next(node for node in tree.body
                   if isinstance(node, ast.ClassDef) and node.name == 'ReaGui')
        methods = {node.name: node for node in cls.body
                   if isinstance(node, ast.FunctionDef)}
        self.assertIn('straight_journey', methods)
        self.assertEqual([name for name in methods if name.startswith('test_')],
                         ['test_authorised_gui_stage'])
        text = ast.get_source_segment((ROOT / gui.REA_ENTRY).read_text(),
                                      methods['straight_journey'])
        for token in ('0x1.26afe3537fbd7p+4', '0x1.26afe353ae7fdp+4',
                      '0x1.26afe353ae7fep+4', 'float.fromhex',
                      'straight_boundary_edits', 'openDocument', 'self.pick'):
            self.assertIn(token, text)

    def test_upper_out_refusal_requires_specific_source_error_and_visibility(self):
        from tracktemplate.domain.rea_turnout import ReaTurnoutError

        tree = ast.parse((ROOT / gui.REA_ENTRY).read_text())
        action = next(node for node in ast.walk(tree)
                      if isinstance(node, ast.FunctionDef)
                      and node.name == 'refused_boundary')

        def exercise(error, visible):
            case = unittest.TestCase()
            case.gui = None
            case.receipt = {'refusals': []}
            counts = []
            case.count = counts.append
            case.select_record = lambda *args: None
            case.edit = lambda *args: None
            case.click = lambda *args: None
            case.image = lambda *args, **kwargs: None
            case.read = lambda obj: SimpleNamespace(entity_id='source-id')
            proxy = SimpleNamespace(snapshot=lambda: ('unchanged-view',))
            obj = SimpleNamespace(
                Name='Source', TrackTemplateReaIntentJSON='canonical',
                ViewObject=SimpleNamespace(Proxy=proxy),
            )
            doc = SimpleNamespace(Objects=[obj])
            panel = SimpleNamespace(
                last_error=error, ratio_edit=object(), apply_button=object(),
                status_label=SimpleNamespace(text=lambda: visible),
            )
            namespace = {
                'self': case, 'obj': obj, 'doc': doc, 'proxy': proxy,
                'payload': 'canonical', 'history': ('unchanged-history',),
                'selection': ('unchanged-selection',), 'inventory': ('Source',),
                'snapshot': ('unchanged-view',), 'identity': 'source-id',
                '_history': lambda doc: ('unchanged-history',),
                '_selection': lambda gui: ('unchanged-selection',),
            }
            exec(compile(ast.Module(body=[action], type_ignores=[]),
                         str(ROOT / gui.REA_ENTRY), 'exec'), namespace)
            namespace['refused_boundary'](panel, object())
            return counts, case.receipt

        correct = ReaTurnoutError(
            'unsupported-negative-closure',
            'A nonpositive source closure span is not construction-qualified.',
        )
        visible = 'Could not complete: {}'.format(correct)
        counts, receipt = exercise(correct, visible)
        self.assertEqual(counts, ['visible_input_refusals'])
        self.assertEqual(receipt['refusals'][0]['input_hex'],
                         '0x1.26afe353ae7fep+4')
        self.assertEqual(receipt['refusals'][0]['visible_text'], visible)
        cases = (
            (RuntimeError('unrelated failure'),
             'Could not complete: unrelated failure'),
            (RuntimeError(str(correct)), visible),
            (ReaTurnoutError('invalid-auto-fit-entry', 'Different source error'),
             'Could not complete: invalid-auto-fit-entry: Different source error'),
            (correct, 'Could not complete: unrelated failure'),
            (correct, 'Could not complete:'),
            (correct, ''),
        )
        for error, label in cases:
            with self.subTest(error=repr(error), visible=label):
                with self.assertRaises(AssertionError):
                    exercise(error, label)

    def test_workflow_ref_pairs_cannot_cross_route(self):
        text = (ROOT / '.github/workflows/l1-gui-validation.yml').read_text()
        self.assertIn("inputs.workload == 'rea-bc-straight'", text)
        self.assertIn("refs/heads/codex/rea-bc-straight-closure", text)
        self.assertIn('TRACKTEMPLATE_GUI_WORKLOAD: ${{ inputs.workload }}', text)
        self.assertIn('default: l1', text)
        self.assertEqual(text.count('rea-bc-gui:'), 1)
        self.assertEqual(text.count('timeout-minutes: 45'), 1)


class HostedToSingleGuiControls(unittest.TestCase):
    def reuse_authority(self, stage='readiness'):
        record = self.to_authority(stage)
        proof = record['prior_native_evidence']
        proof['source_commit'] = 'b' * 40
        record['native_source_reuse'] = {
            'schema': 1, 'scope_id': 'TO-001-GUI-PICK-DIAGNOSTIC-001',
            'status': 'PASS', 'independent_review': 'PASS',
            'from_commit': proof['source_commit'],
            'to_commit': record['source_commit'],
            'native_run_id': proof['run_id'],
            'native_evidence_sha256': proof['evidence_sha256'],
            'review_sha256': 'd' * 64,
            'changed_paths': ['tests/freecad_validate_to_single_rail_gui.py'],
        }
        return record

    def test_to_native_reuse_requires_exact_independent_binding(self):
        env = dict(environment(), L1_GUI_STAGE='readiness',
                   TRACKTEMPLATE_GUI_WORKLOAD='to-single')
        good = self.reuse_authority()
        original = copy.deepcopy(good['prior_native_evidence'])
        gui.validate_authority(good, env)
        self.assertEqual(good['prior_native_evidence'], original)
        for key, value in (
            ('schema', True), ('scope_id', 'other'), ('status', 'FAIL'),
            ('independent_review', 'Pending'), ('review_sha256', ''),
            ('from_commit', 'c' * 40), ('to_commit', 'c' * 40),
            ('native_run_id', 99), ('native_evidence_sha256', 'e' * 64),
            ('changed_paths', ['tracktemplate/unreviewed.py']),
            ('changed_paths', ['tests/freecad_validate_to_single_rail_gui.py']
             * 2), ('changed_paths', []),
        ):
            changed = copy.deepcopy(good)
            changed['native_source_reuse'][key] = value
            with self.subTest(field=key, value=value):
                with self.assertRaises(ValueError):
                    gui.validate_authority(changed, env)
        for value in (None, {}, []):
            changed = dict(good, native_source_reuse=value)
            with self.subTest(reuse=value), self.assertRaises(ValueError):
                gui.validate_authority(changed, env)
        changed = copy.deepcopy(good)
        changed['prior_native_evidence']['source_commit'] = 'not-a-sha'
        changed['native_source_reuse']['from_commit'] = 'not-a-sha'
        with self.assertRaises(ValueError):
            gui.validate_authority(changed, env)
        same = self.to_authority('readiness')
        gui.validate_authority(same, env)
        same['native_source_reuse'] = good['native_source_reuse']
        with self.assertRaises(ValueError):
            gui.validate_authority(same, env)

    def test_to_native_reuse_compares_actual_tracked_dependencies(self):
        allowed = 'tests/freecad_validate_to_single_rail_gui.py'
        protected = (
            'tracktemplate/geometry.py', 'AdvancedTurnout.FCMacro',
            'model_railway_curve_template_multitrack_v10_2a8a7b15_'
            'chair_performance_and_representation.FCMacro',
            'tests/freecad_validate_to_single_rail.py',
            'tests/fixtures/phase9b-to-single-rail-frames.json',
            'tools/freecad_bridge/chair_recipe.py',
            'tests/helpers/comparator.py', 'tools/freecad_validation_guard.py',
            'reference/contracts/phase1-compatibility.json', 'unknown.txt',
            ' tests/freecad_validate_to_single_rail_gui.py',
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command = gui.native.command

            def git(*args):
                return command('git', *args, cwd=root)

            def commit(message):
                git('add', '.')
                git('-c', 'user.name=Regression Fixture', '-c',
                    'user.email=fixture@example.invalid', 'commit', '-m',
                    message)
                return git('rev-parse', 'HEAD')

            git('init', '-q')
            for name in (allowed, *protected):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('baseline\n')
            baseline = commit('Original native dependencies')
            (root / allowed).write_text('diagnostic\n')
            head = commit('GUI diagnostics only')
            record = self.reuse_authority()
            record['source_commit'] = head
            record['prior_native_evidence']['source_commit'] = baseline
            record['native_source_reuse'].update(
                from_commit=baseline, to_commit=head,
            )
            with patch.object(gui.native, 'command', side_effect=lambda *args:
                              command(*args, cwd=root)):
                gui.validate_to_native_source(record)
                for source in ('f' * 40, head):
                    bad = copy.deepcopy(record)
                    bad['prior_native_evidence']['source_commit'] = source
                    bad['native_source_reuse']['from_commit'] = source
                    with self.subTest(source=source), self.assertRaises(
                            (ValueError, subprocess.CalledProcessError)):
                        gui.validate_to_native_source(bad)
                for name in protected:
                    (root / name).write_text('changed dependency\n')
                    bad_head = commit('Changed protected dependency')
                    bad = copy.deepcopy(record)
                    bad['source_commit'] = bad_head
                    bad['native_source_reuse']['to_commit'] = bad_head
                    with self.subTest(path=name), self.assertRaisesRegex(
                            ValueError, 'native source'):
                        gui.validate_to_native_source(bad)
                    (root / name).write_text('baseline\n')
                    commit('Restore fixture dependency')
                (root / allowed).write_text('baseline\n')
                (root / (' ' + allowed)).write_text('unknown input\n')
                bad_head = commit('Only a leading-space path changed')
                bad = copy.deepcopy(record)
                bad['source_commit'] = bad_head
                bad['native_source_reuse']['to_commit'] = bad_head
                with self.assertRaisesRegex(ValueError, 'native source'):
                    gui.validate_to_native_source(bad)

    def to_authority(self, stage='gui'):
        source = ast.parse((ROOT / 'tests/freecad_validate_to_single_rail.py')
                           .read_text())
        hashes = next(ast.literal_eval(node.value) for node in source.body
                      if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name)
                              and target.id == 'INPUT_HASHES'
                              for target in node.targets))
        record = authority()
        record.pop('product_requalification', None)
        record.update(
            stage=stage, workload='to-single', scope_id=gui.TO_SCOPE,
            source_base_commit=gui.TO_BASE,
            handling_decision=gui.TO_HANDLING_DECISION,
            freecad_limits=vars(gui.limits(stage, 'to-single')),
            display_limits=vars(gui.display_limits(stage, 'to-single')),
            historical_repair_allowance_consumed=True,
            automatic_retry=False, input_hashes=hashes,
            native_entry_sha256=gui.native.TO_ENTRY_SHA256,
            control_files_sha256={name: 'c' * 64
                                  for name in gui.to_control_files()},
        )
        record['publication_review'] = {
            'status': 'PASS', 'independent_review': 'PASS',
            'input_hashes': hashes, 'evidence_sha256': 'e' * 64,
            'handling_decision': gui.TO_HANDLING_DECISION,
            'publication_basis': 'synthetic offline test record only',
        }
        record['handling_review'] = {
            'decision_sha256': gui.TO_HANDLING_DECISION.rsplit(':', 1)[1],
            'independent_review': 'PASS', 'retention_days': 30,
            'independent_preservation': True, 'readiness_images': 1,
            'gui_images': 6, 'source_archive_upload': False,
            'operator_documents': False, 'exact_exports': False,
            'working_fcstd_upload': False,
        }
        record['native_control'] = {
            'scope_id': 'TO-001-fixed-single-rail-native-v1',
            'source_commit': record['source_commit'],
            'entry_sha256': gui.native.TO_ENTRY_SHA256,
            'handling_decision': record['handling_decision'],
            'input_hashes': hashes,
            'input_archive': record['input_archive'],
            'publication_review': record['publication_review'],
        }
        record['prior_native_evidence'].update(
            run_id=40, source_commit=record['source_commit'],
            entry_sha256=gui.native.TO_ENTRY_SHA256,
            scope_id='TO-001-fixed-single-rail-native-v1',
            input_hashes=hashes, tests=1, skips=0, run_attempt=1,
            cleanup=True, evidence_verified=True,
            independent_preservation=True, source_frame_comparisons=59,
            component_comparisons=270, successful_components=270,
            rolled_back_components=270,
        )
        ready = {key: record[key] for key in (
            'scope_id', 'workload', 'source_commit', 'gui_entry_sha256',
            'control_files_sha256', 'input_hashes', 'handling_review',
            'handling_decision', 'publication_review',
        )}
        ready.update(
            status='PASS', independent_review='PASS', stage='readiness',
            freecad_limits=vars(gui.limits('readiness', 'to-single')),
            display_limits=vars(gui.display_limits('readiness', 'to-single')),
            tests=1, skips=0, run_attempt=1, cleanup=True,
            evidence_verified=True, independent_preservation=True,
            sentinel=gui.sentinel('readiness', 'to-single'), run_id=41,
            evidence_sha256='e' * 64, result_review_sha256='f' * 64,
            preservation_review_sha256='1' * 64,
        )
        record['gui_readiness_review'] = ready
        return record

    def test_to_authority_requires_publication_native_and_separate_readiness(self):
        env = dict(environment(), TRACKTEMPLATE_GUI_WORKLOAD='to-single')
        good = self.to_authority()
        gui.validate_authority(good, env)
        for name, value in (
            ('publication_review', {}), ('handling_review', {}),
            ('native_control', {}), ('prior_native_evidence', {}),
            ('gui_readiness_review', {}), ('gui_recovery', {}),
            ('scope_id', gui.SCOPE), ('handling_decision', gui.HANDLING_DECISION),
            ('input_hashes', {}), ('automatic_retry', True),
            ('source_base_commit', 'd' * 40),
        ):
            with self.subTest(field=name), self.assertRaises(ValueError):
                gui.validate_authority(dict(good, **{name: value}), env)
        for key in ('publication_review', 'prior_native_evidence',
                    'gui_readiness_review'):
            changed = copy.deepcopy(good)
            changed[key]['input_hashes']['s1_model'] = '0' * 64
            with self.subTest(record=key), self.assertRaises(ValueError):
                gui.validate_authority(changed, env)
        changed = copy.deepcopy(good)
        changed['gui_readiness_review']['run_id'] = 42
        with self.assertRaises(ValueError):
            gui.validate_authority(changed, env)
        ready = self.to_authority('readiness')
        ready.pop('gui_readiness_review')
        gui.validate_authority(ready, dict(env, L1_GUI_STAGE='readiness'))

    def test_gui_acquisition_record_passes_actual_native_contract(self):
        record = self.to_authority()
        gui.native.validate_to_acquisition(record['native_control'])
        missing = copy.deepcopy(record['native_control'])
        missing['publication_review'].pop('publication_basis')
        with self.assertRaises(ValueError):
            gui.native.validate_to_acquisition(missing)

    def test_reused_native_proof_requires_actual_entry_binding(self):
        with patch.object(sys, 'path', [str(ROOT / 'tests'), *sys.path]):
            import freecad_validate_to_single_rail_gui as entry

        for stage in ('readiness', 'gui'):
            record = self.reuse_authority(stage)
            original = copy.deepcopy(record['prior_native_evidence'])
            env = dict(environment(), L1_GUI_STAGE=stage,
                       TRACKTEMPLATE_GUI_WORKLOAD='to-single')
            config = SimpleNamespace(source_commit=record['source_commit'])
            with patch.dict(os.environ, env, clear=True):
                entry.validate_authority(record, config,
                                         record['gui_entry_sha256'])
                self.assertEqual(record['prior_native_evidence'], original)
                for key, value in (
                    ('from_commit', 'c' * 40), ('to_commit', 'c' * 40),
                    ('native_run_id', 99), ('independent_review', 'Pending'),
                    ('review_sha256', ''), ('native_evidence_sha256', ''),
                ):
                    changed = copy.deepcopy(record)
                    changed['native_source_reuse'][key] = value
                    with self.subTest(stage=stage, field=key):
                        with self.assertRaises(AssertionError):
                            entry.validate_authority(
                                changed, config, record['gui_entry_sha256'],
                            )
                changed = copy.deepcopy(record)
                changed.pop('native_source_reuse')
                with self.assertRaises(AssertionError):
                    entry.validate_authority(changed, config,
                                             record['gui_entry_sha256'])

    def test_controller_record_matches_real_gui_entry_before_launch(self):
        with patch.object(sys, 'path', [str(ROOT / 'tests'), *sys.path]):
            import freecad_validate_to_single_rail_gui as entry

            for stage in ('readiness', 'gui'):
                record = self.to_authority(stage)
                env = dict(environment(), L1_GUI_STAGE=stage,
                           TRACKTEMPLATE_GUI_WORKLOAD='to-single')
                with patch.dict(os.environ, env, clear=True):
                    entry.validate_authority(
                        record, SimpleNamespace(source_commit='a' * 40),
                        record['gui_entry_sha256'],
                    )
                self.assertEqual(gui.to_counts(stage), entry.expected_checks(stage))
                self.assertEqual(gui.to_images(stage), set(entry.image_names(stage)))
                self.assertEqual(gui.sentinel(stage, 'to-single'),
                                 entry.sentinel(stage))

    def test_fixed_to_counts_and_image_sets_reject_other_workloads(self):
        self.assertEqual(gui.selected_workload({
            'TRACKTEMPLATE_GUI_WORKLOAD': 'to-single',
        }), 'to-single')
        self.assertEqual(gui.selected_workload({}), 'l1')
        counts = gui.to_counts('gui')
        self.assertEqual(counts, {
            'binding_checks': 1, 'catalogue_contracts': 2,
            'source_frame_inputs': 59, 'source_frame_comparisons': 59,
            'successful_previews': 1, 'assemblies': 12, 'layers': 42,
            'successful_components': 270, 'layer_visibility_checks': 42,
            'viewport_picks': 1, 'late_verifier_failures': 1,
            'rolled_back_components': 270, 'source_preservation_checks': 4,
            'preview_disposals': 1, 'screenshots': 6,
            'readiness_empty_documents': 0,
        })
        gui.validate_to_counts(counts, 'gui')
        for key in counts:
            for invalid in (True, counts[key] + 1):
                with self.subTest(key=key, value=invalid):
                    with self.assertRaises(ValueError):
                        gui.validate_to_counts(dict(counts, **{key: invalid}),
                                               'gui')
        self.assertEqual(gui.to_images('readiness'),
                         {'to-single-readiness.png'})
        self.assertEqual(gui.to_images('gui'), {
            'to-single-overview.png', 'to-corrected-heels.png',
            'to-retained-placements.png', 'to-selected-chair.png',
            'to-chair-layer-hidden.png', 'to-rollback-restored.png',
        })
        self.assertEqual(gui.limits('gui', 'to-single').memory_max_mib, 4096)
        self.assertEqual(gui.limits('gui', 'to-single').timeout_seconds, 7200)
        self.assertEqual(gui.display_limits('gui', 'to-single').tasks_max, 16)
        self.assertEqual(gui.display_limits('gui', 'to-single').cpu_percent, 25)
        with self.assertRaises(ValueError):
            gui.to_images('native')

    def test_single_complete_to_report_and_duplicate_keys(self):
        prefix = 'TRACKTEMPLATE_TO_SINGLE_GUI='
        self.assertEqual(gui.to_report(prefix + '{"status":"FAIL"}\n'),
                         {'status': 'FAIL'})
        for text in ('', prefix + '{}\n' + prefix + '{}',
                     prefix + '{"status":"FAIL","status":"PASS"}',
                     prefix + '{"duration":NaN}', prefix + '[]',
                     'noise ' + prefix + '{}', prefix + '{broken',
                     prefix + '{"duration":1e999}',
                     prefix + '{"duration":-1e999}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                gui.to_report(text)

    def test_to_macro_and_child_use_only_reviewed_import_safe_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence').mkdir()
            (work / 'gui-run-config.json').write_text('{}')
            (work / 'evidence/gui-authority.json').write_text('{}')
            env = dict(environment(), TRACKTEMPLATE_GUI_WORKLOAD='to-single',
                       HOME=temporary, PATH='/usr/bin')
            with patch.dict(os.environ, env, clear=True):
                macro = gui.write_gui_macro(work)
                clean = gui.child_environment(work)
                argv = gui.gui_argv(clean, macro)
            self.assertIn('import freecad_validate_to_single_rail_gui',
                          macro.read_text())
            self.assertIn('freecad_validate_to_single_rail_gui.start()',
                          macro.read_text())
            for name in ('TRACKTEMPLATE_TO_RUN_CONFIG',
                         'TRACKTEMPLATE_TO_RUN_CONFIG_SHA256',
                         'TRACKTEMPLATE_TO_GUI_AUTHORITY',
                         'TRACKTEMPLATE_TO_GUI_AUTHORITY_SHA256'):
                self.assertIn(name, clean)
                self.assertIn('--env=' + name + '=' + clean[name], argv)
            self.assertNotIn('TRACKTEMPLATE_L1_RUN_CONFIG', clean)
            self.assertEqual(clean['GITHUB_SHA'], 'a' * 40)
            self.assertEqual(clean['QT_QPA_PLATFORM'], 'xcb')
            self.assertEqual(clean['GALLIUM_DRIVER'], 'llvmpipe')

    def test_to_receipt_requires_counts_images_cleanup_and_exact_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            images = work / 'evidence/gui'
            images.mkdir(parents=True)
            control = self.to_authority()
            control['control_files_sha256'] = {}
            (work / 'control.json').write_text(json.dumps(control))
            rows = []
            for name in sorted(gui.to_images('gui')):
                path = images / name
                path.write_bytes(b'\x89PNG\r\n\x1a\nsynthetic-offline-fixture')
                rows.append({'path': name, 'sha256': gui.digest(path),
                             'bytes': path.stat().st_size})
            receipt = {
                'status': 'PASS', 'stage': 'gui', 'scope_id': gui.TO_SCOPE,
                'test_id': ('freecad_validate_to_single_rail_gui.'
                            'ToSingleRailGui.test_authorised_gui_stage'),
                'source_commit': 'a' * 40,
                'fixture_sha256': (
                    '407040d01dd0f9c8ac275d7e4d40c928ea32a5da0a05c853bf3a1de4221a8d4b'),
                'profile': gui.original.EXPECTED_PROFILE, 'gui': True,
                'visual_review': 'REQUIRED', 'physical_fit': 'NOT_PROVED',
                'native_evidence_reused': control['prior_native_evidence'],
                'input_sha256': control['input_hashes'],
                'input_bindings_unchanged': True,
                'owned_documents_closed': True, 'remaining_documents': 0,
                'cleanup_errors': [], 'sentinel': gui.sentinel('gui', 'to-single'),
                'checks': gui.to_counts('gui'), 'screenshots': rows,
                'stage_timings': dict.fromkeys((
                    'readiness_seconds', 'cleanup_seconds', 'total_seconds',
                    'successful_preview_seconds', 'late_rollback_seconds',
                    'gui_seconds'), 1.0),
                'renderer': {'platform': 'xcb', 'gui_up': True,
                             'widget_valid': True, 'renderer': 'llvmpipe',
                             'vendor': 'fixture', 'version': 'fixture'},
            }
            gui.validate_to_receipt(receipt, work, stage='gui')
            for field, value in (
                ('remaining_documents', 1), ('remaining_documents', False),
                ('owned_documents_closed', False), ('cleanup_errors', ['error']),
                ('source_commit', 'b' * 40), ('input_sha256', {}),
                ('screenshots', rows[:-1]), ('screenshots', [rows[0]] * 6),
                ('stage_timings', {}), ('physical_fit', 'PASS'),
            ):
                with self.subTest(field=field), self.assertRaises(ValueError):
                    gui.validate_to_receipt(dict(receipt, **{field: value}),
                                            work, stage='gui')
            for bad in (10**400, -(10**400), float('inf'),
                        float('-inf'), float('nan'), True, -1, 7201):
                malformed = copy.deepcopy(receipt)
                malformed['stage_timings']['total_seconds'] = bad
                with self.subTest(timing=bad), self.assertRaises(ValueError):
                    gui.validate_to_receipt(malformed, work, stage='gui')
            unexpected = images / 'unapproved.png'
            unexpected.write_bytes(b'image')
            with self.assertRaisesRegex(ValueError, 'Unexpected'):
                gui.validate_to_receipt(receipt, work, stage='gui')
            unexpected.unlink()
            prohibited = work / 'evidence/working.FCStd'
            prohibited.write_bytes(b'input-copy')
            with self.assertRaisesRegex(ValueError, 'Unexpected'):
                gui.validate_to_receipt(receipt, work, stage='gui')

    def test_to_uses_existing_main_job_and_separate_control_record(self):
        text = (ROOT / '.github/workflows/l1-gui-validation.yml').read_text()
        self.assertIn("inputs.workload == 'to-single'", text)
        self.assertIn('vars.TO_SINGLE_GUI_CONTROL', text)
        self.assertEqual(text.count('group: issue230-native-geometry'), 1)
        self.assertEqual(text.count('timeout-minutes: 140'), 1)
        self.assertIn('cancel-in-progress: false', text)
        self.assertIn('retention-days: 30', text)


class HostedToCrossingGuiControls(unittest.TestCase):
    WORKLOAD = 'to-crossing'
    SCOPE = 'TO-001-fixed-crossing-gui-v1'
    IMAGES = {
        'to-crossing-overview.png', 'to-crossing-XA-AA.png',
        'to-crossing-CD-DD.png', 'to-crossing-selected-chair.png',
        'to-crossing-layer-hidden.png', 'to-crossing-rollback-restored.png',
    }

    def crossing_authority(self, stage='gui'):
        record = HostedToSingleGuiControls().to_authority(stage)
        profile = gui.native.to_profile(self.WORKLOAD)
        decision = 'to-crossing-handling-owner-decision.json@sha256:' + '2' * 64
        manifest = '303135d7f7f6de4bbee5ee8400bf9a9db2b8ab2e687ef3557ef140154c6b737e'
        record.update(
            workload=self.WORKLOAD, scope_id=self.SCOPE,
            source_base_commit='a801f4444bec2f6799e7d2ad1fa2da3aac78db95',
            input_hashes=profile['input_hashes'],
            native_entry_sha256=profile['entry_sha256'],
            handling_decision=decision, publication_manifest_sha256=manifest,
            control_files_sha256={name: 'c' * 64
                                  for name in gui.to_control_files(self.WORKLOAD)},
        )
        record['handling_review'].update(
            decision_sha256='2' * 64, publication_manifest_sha256=manifest,
        )
        record['publication_review'].update(
            input_hashes=profile['input_hashes'], handling_decision=decision,
            publication_manifest_sha256=manifest,
        )
        record['native_control'].update(
            scope_id='TO-001-fixed-crossing-native-v1',
            input_hashes=profile['input_hashes'], handling_decision=decision,
            entry_sha256=profile['entry_sha256'],
            publication_manifest_sha256=manifest,
        )
        record['prior_native_evidence'].update(
            scope_id='TO-001-fixed-crossing-native-v1',
            input_hashes=profile['input_hashes'],
            entry_sha256=profile['entry_sha256'],
            source_frame_comparisons=50, component_comparisons=135,
            stored_compound_checks=135, stored_child_checks=135,
            successful_components=135, rolled_back_components=135,
        )
        ready = record['gui_readiness_review']
        for key in (
            'scope_id', 'workload', 'input_hashes', 'handling_decision',
            'handling_review', 'publication_review', 'control_files_sha256',
        ):
            ready[key] = copy.deepcopy(record[key])
        ready['sentinel'] = 'Fixed TO crossing GUI readiness passed'
        return record

    def test_crossing_authority_rejects_missing_or_foreign_proofs(self):
        for stage in ('readiness', 'gui'):
            env = dict(environment(), TRACKTEMPLATE_GUI_WORKLOAD=self.WORKLOAD,
                       L1_GUI_STAGE=stage)
            good = self.crossing_authority(stage)
            if stage == 'readiness':
                good.pop('gui_readiness_review')
            gui.validate_authority(good, env)
            for key, value in (
                ('publication_manifest_sha256', '0' * 64),
                ('handling_decision', gui.TO_HANDLING_DECISION),
                ('handling_decision', 'to-crossing-handling-owner-decision.json@sha256:' + '0' * 64),
                ('publication_review', {}), ('handling_review', {}),
                ('native_control', {}), ('prior_native_evidence', {}),
                ('gui_recovery', {}), ('input_hashes', {}),
                ('automatic_retry', True), ('source_base_commit', 'b' * 40),
            ):
                with self.subTest(stage=stage, key=key):
                    with self.assertRaises(ValueError):
                        gui.validate_authority(dict(good, **{key: value}), env)
            for key, value in (
                ('source_commit', 'b' * 40), ('stored_child_checks', 0),
                ('stored_compound_checks', 0), ('component_comparisons', 270),
                ('run_id', 42), ('skips', 1), ('cleanup', False),
            ):
                changed = copy.deepcopy(good)
                changed['prior_native_evidence'][key] = value
                with self.subTest(stage=stage, proof=key):
                    with self.assertRaises(ValueError):
                        gui.validate_authority(changed, env)
            if stage == 'gui':
                for key, value in (
                    ('run_id', 42), ('run_id', 40), ('source_commit', 'b' * 40),
                    ('result_review_sha256', ''), ('cleanup', False),
                    ('independent_preservation', False),
                ):
                    changed = copy.deepcopy(good)
                    changed['gui_readiness_review'][key] = value
                    with self.subTest(readiness=key):
                        with self.assertRaises(ValueError):
                            gui.validate_authority(changed, env)

    def test_crossing_controller_matches_real_entry_before_launch(self):
        with patch.object(sys, 'path', [str(ROOT / 'tests'), *sys.path]):
            import freecad_validate_to_crossing_chairs_gui as entry
        for stage in ('readiness', 'gui'):
            record = self.crossing_authority(stage)
            env = dict(environment(), L1_GUI_STAGE=stage,
                       TRACKTEMPLATE_GUI_WORKLOAD=self.WORKLOAD)
            with patch.dict(os.environ, env, clear=True):
                entry.validate_authority(
                    record, SimpleNamespace(source_commit='a' * 40),
                    record['gui_entry_sha256'],
                )
            self.assertEqual(gui.to_counts(stage, workload=self.WORKLOAD),
                             entry.expected_checks(stage))
            self.assertEqual(gui.to_images(stage, workload=self.WORKLOAD),
                             set(entry.image_names(stage)))
            self.assertEqual(gui.sentinel(stage, self.WORKLOAD),
                             entry.sentinel(stage))

    def test_crossing_receipt_requires_all_counters_and_exact_images(self):
        for stage in ('readiness', 'gui'):
            with tempfile.TemporaryDirectory() as temporary:
                work = Path(temporary)
                images = work / 'evidence/gui'
                images.mkdir(parents=True)
                control = self.crossing_authority(stage)
                control['control_files_sha256'] = {}
                (work / 'control.json').write_text(json.dumps(control))
                rows = []
                for name in sorted(gui.to_images(stage, workload=self.WORKLOAD)):
                    path = images / name
                    path.write_bytes(b'\x89PNG\r\n\x1a\nsynthetic-offline-fixture')
                    rows.append({'path': name, 'sha256': gui.digest(path),
                                 'bytes': path.stat().st_size})
                timings = {'readiness_seconds', 'cleanup_seconds', 'total_seconds'}
                if stage == 'gui':
                    timings.update({'successful_preview_seconds',
                                    'late_rollback_seconds', 'gui_seconds'})
                receipt = {
                    'status': 'PASS', 'stage': stage, 'scope_id': self.SCOPE,
                    'test_id': ('freecad_validate_to_crossing_chairs_gui.'
                                'ToCrossingGui.test_authorised_gui_stage'),
                    'source_commit': 'a' * 40,
                    'fixture_sha256': (
                        '3fe86e5e6e0a565e1e151555fb9e1bca7723c176df804281486ec795c10da900'),
                    'profile': gui.original.EXPECTED_PROFILE, 'gui': True,
                    'visual_review': 'REQUIRED', 'physical_fit': 'NOT_PROVED',
                    'native_evidence_reused': {
                        key: control['prior_native_evidence'][key] for key in (
                            'run_id', 'source_commit', 'entry_sha256',
                            'evidence_sha256',
                        )
                    },
                    'input_sha256': control['input_hashes'],
                    'input_bindings_unchanged': True,
                    'owned_documents_closed': True, 'remaining_documents': 0,
                    'cleanup_errors': [], 'failures': [],
                    'sentinel': gui.sentinel(stage, self.WORKLOAD),
                    'checks': gui.to_counts(stage, workload=self.WORKLOAD),
                    'screenshots': rows,
                    'stage_timings': dict.fromkeys(timings, 1.0),
                    'renderer': {'platform': 'xcb', 'gui_up': True,
                                 'widget_valid': True, 'renderer': 'llvmpipe',
                                 'vendor': 'fixture', 'version': 'fixture'},
                }
                gui.validate_to_receipt(receipt, work, stage=stage,
                                        workload=self.WORKLOAD)
                for key, value in (
                    ('remaining_documents', 1), ('remaining_documents', False),
                    ('owned_documents_closed', False), ('failures', [{}]),
                    ('screenshots', []), ('input_sha256', {}),
                    ('stage_timings', {}), ('physical_fit', 'PASS'),
                    ('source_commit', 'b' * 40),
                ):
                    with self.subTest(stage=stage, key=key):
                        with self.assertRaises(ValueError):
                            gui.validate_to_receipt(
                                dict(receipt, **{key: value}), work,
                                stage=stage, workload=self.WORKLOAD,
                            )
                for name in ('unapproved.png', 'operator.FCStd', 'raw-shape.brep'):
                    extra = images / name
                    extra.write_bytes(b'not approved')
                    with self.subTest(name=name), self.assertRaises(ValueError):
                        gui.validate_to_receipt(receipt, work, stage=stage,
                                                workload=self.WORKLOAD)
                    extra.unlink()

    def test_explicit_crossing_workload_and_unchanged_resource_limits(self):
        self.assertEqual(gui.selected_workload({
            'TRACKTEMPLATE_GUI_WORKLOAD': self.WORKLOAD,
        }), self.WORKLOAD)
        for stage, timeout, display_timeout in (
            ('readiness', 90, 190), ('gui', 7200, 7300),
        ):
            self.assertEqual(vars(gui.limits(stage, self.WORKLOAD)),
                             vars(gui.limits(stage, 'to-single')))
            self.assertEqual(gui.limits(stage, self.WORKLOAD).timeout_seconds,
                             timeout)
            self.assertEqual(vars(gui.display_limits(stage, self.WORKLOAD)),
                             vars(gui.display_limits(stage, 'to-single')))
            self.assertEqual(
                gui.display_limits(stage, self.WORKLOAD).timeout_seconds,
                display_timeout,
            )
        with self.assertRaises(ValueError):
            gui.selected_workload({'TRACKTEMPLATE_GUI_WORKLOAD': 'all-chairs'})

    def test_crossing_counts_are_exact_typed_and_separate_from_old_profile(self):
        counts = gui.to_counts('gui', workload=self.WORKLOAD)
        for name, expected in (
            ('catalogue_contracts', 4), ('source_frame_inputs', 50),
            ('source_frame_comparisons', 50), ('assemblies', 4),
            ('layers', 137), ('successful_components', 135),
            ('layer_visibility_checks', 137), ('rolled_back_components', 135),
            ('viewport_picks', 1), ('screenshots', 6),
        ):
            self.assertEqual(counts[name], expected)
        gui.validate_to_counts(counts, 'gui', workload=self.WORKLOAD)
        with self.assertRaises(ValueError):
            gui.validate_to_counts(counts, 'gui')
        for name, expected in counts.items():
            for invalid in (True, expected + 1):
                with self.subTest(name=name, invalid=invalid):
                    with self.assertRaises(ValueError):
                        gui.validate_to_counts(
                            dict(counts, **{name: invalid}), 'gui',
                            workload=self.WORKLOAD,
                        )
        ready = gui.to_counts('readiness', workload=self.WORKLOAD)
        self.assertEqual(ready['source_frame_inputs'], 50)
        self.assertEqual(ready['assemblies'], 0)
        self.assertEqual(ready['screenshots'], 1)

    def test_crossing_images_and_exact_report_parser(self):
        self.assertEqual(gui.to_images('gui', workload=self.WORKLOAD), self.IMAGES)
        self.assertEqual(gui.to_images('readiness', workload=self.WORKLOAD),
                         {'to-crossing-readiness.png'})
        prefix = 'TRACKTEMPLATE_TO_CROSSING_GUI='
        self.assertEqual(gui.to_report(prefix + '{"status":"FAIL"}\n',
                                       workload=self.WORKLOAD), {'status': 'FAIL'})
        for text in ('', prefix + '{}\n' + prefix + '{}',
                     prefix + '{"status":"FAIL","status":"PASS"}',
                     prefix + '{"duration":NaN}', prefix + '[]',
                     'noise ' + prefix + '{}', prefix + '{broken',
                     prefix + '{"duration":1e999}',
                     'TRACKTEMPLATE_TO_SINGLE_GUI={}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                gui.to_report(text, workload=self.WORKLOAD)

    def test_crossing_macro_uses_only_its_import_safe_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / 'evidence').mkdir()
            (work / 'gui-run-config.json').write_text('{}')
            (work / 'evidence/gui-authority.json').write_text('{}')
            env = dict(environment(), TRACKTEMPLATE_GUI_WORKLOAD=self.WORKLOAD,
                       HOME=temporary, PATH='/usr/bin')
            with patch.dict(os.environ, env, clear=True):
                macro = gui.write_gui_macro(work)
                clean = gui.child_environment(work)
                argv = gui.gui_argv(clean, macro)
            self.assertIn('import freecad_validate_to_crossing_chairs_gui',
                          macro.read_text())
            self.assertIn('freecad_validate_to_crossing_chairs_gui.start()',
                          macro.read_text())
            self.assertNotIn('to_single_rail', macro.read_text())
            self.assertEqual(clean['TRACKTEMPLATE_GUI_WORKLOAD'], self.WORKLOAD)
            self.assertNotIn('TRACKTEMPLATE_L1_RUN_CONFIG', clean)
            for name in ('TRACKTEMPLATE_TO_RUN_CONFIG',
                         'TRACKTEMPLATE_TO_GUI_AUTHORITY'):
                self.assertIn('--env=' + name + '=' + clean[name], argv)

    def test_crossing_workflow_uses_existing_job_and_separate_control(self):
        text = (ROOT / '.github/workflows/l1-gui-validation.yml').read_text()
        self.assertIn("inputs.workload == 'to-crossing'", text)
        self.assertIn('vars.TO_CROSSING_GUI_CONTROL', text)
        self.assertEqual(text.count('group: issue230-native-geometry'), 1)
        self.assertEqual(text.count('timeout-minutes: 140'), 1)
        self.assertIn('cancel-in-progress: false', text)
        self.assertIn('retention-days: 30', text)


if __name__ == '__main__':
    result = unittest.main(exit=False)
    if not result.result.wasSuccessful():
        raise SystemExit(1)
    print('Hosted L1 GUI controls passed')
