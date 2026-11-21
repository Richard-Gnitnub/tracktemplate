#!/usr/bin/env python3
"""Offline fixed-matrix, invocation, deadline and failure proofs."""

import ast
from contextlib import ExitStack, nullcontext
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import hosted_runtime_compatibility as matrix  # noqa: E402


class MatrixTests(unittest.TestCase):
    @staticmethod
    def resource_fixture(seconds):
        sample = {'memory.current': '100', 'memory.peak': '100',
            'memory.events': 'high 0\nmax 0\noom 0\noom_kill 0\n',
            'memory.swap.current': '0', 'memory.pressure': 'some avg10=0.00',
            'cpu.stat': 'usage_usec 42\n', 'pids.current': '0',
            'cgroup.events': 'populated 0\n', 'cgroup.procs': ''}
        result = {'status': 'completed', 'process_exit': 0,
            'cleanup_proved': True, 'deadline_cancellation_exit': 0,
            'limits': vars(matrix.guard.ValidationLimits(4096, seconds)),
            'kernel_limits': {'memory.max': str(4096 * 1024**2),
                'memory.high': str(4096 * 1024**2), 'memory.swap.max': '0',
                'cpu.max': '100000 100000', 'pids.max': '128'},
            'before_cleanup': sample.copy()}
        return result, sample

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.capsule = matrix.load_execution_capsule(ROOT / matrix.CAPSULE, ROOT)

    def test_fixed_public_projection_and_original_sources(self):
        self.assertEqual(len(self.capsule['native_entries']), 57)
        self.assertEqual(len(self.capsule['gui_entries']), 22)
        self.assertEqual(sum(row['sessions'] for row in
                             self.capsule['gui_entries']), 26)
        self.assertEqual(len(matrix.entries(self.capsule)), 80)
        self.assertNotIn('/home/', (ROOT / matrix.CAPSULE).read_text())
        self.assertEqual(self.capsule['generation']['arguments'], [
            '--base', '{BASE}', '--scenario', 'phase8-straight-host'])

    def test_changed_capsule_is_not_a_new_workload(self):
        path = self.work / 'capsule.json'
        raw = (ROOT / matrix.CAPSULE).read_bytes()
        path.write_bytes(raw.replace(b'"sessions": 4', b'"sessions": 3'))
        with self.assertRaisesRegex(ValueError, 'Execution capsule changed'):
            matrix.load_execution_capsule(path, ROOT)

    def test_original_source_drift_is_refused(self):
        real = matrix.identity
        target = self.capsule['native_entries'][0]['path']

        def identity(path):
            value = real(path)
            if Path(path) == ROOT / target:
                value['sha256'] = '0' * 64
            return value

        with patch.object(matrix, 'identity', side_effect=identity):
            with self.assertRaisesRegex(ValueError, 'original source changed'):
                matrix.load_execution_capsule(ROOT / matrix.CAPSULE, ROOT)

    def test_deadline_is_one_immutable_interval(self):
        deadline = matrix.Deadline.start(lambda: 100)
        self.assertEqual(deadline.expires, 7300)
        self.assertEqual(deadline.entry_seconds({'timeout_seconds': 900},
                                               lambda: 7250), 50)
        for entry in matrix.entries(self.capsule):
            self.assertGreater(deadline.entry_seconds(entry, lambda: 7250), 0)
        self.assertEqual(deadline.entry_seconds({'timeout_seconds': None},
                                               lambda: 7250), 50)
        with self.assertRaises(FrozenInstanceError):
            deadline.expires = 8000
        with self.assertRaisesRegex(ValueError, 'interval differs'):
            matrix.Deadline(100, 10000)
        with self.assertRaisesRegex(ValueError, 'regressed'):
            deadline.remaining(lambda: 99)
        with self.assertRaisesRegex(ValueError, 'exhausted'):
            deadline.remaining(lambda: 7300)

    def test_controller_alarm_stops_comparison_and_preserves_guard_cleanup(self):
        deadline = matrix.Deadline.start()
        with patch.object(matrix.Deadline, 'remaining', return_value=0.02):
            with self.assertRaisesRegex(ValueError, 'heavy deadline exhausted'):
                with matrix.ControllerWatchdog(deadline):
                    time.sleep(1)
            with matrix.ControllerWatchdog(deadline) as watchdog:
                with watchdog.cleanup_safe():
                    time.sleep(0.04)
                self.assertTrue(watchdog.expired)
            self.assertEqual(matrix.signal.getitimer(matrix.signal.ITIMER_REAL),
                             (0.0, 0.0))

    def test_heavy_start_requires_a_live_outer_reservation(self):
        with patch.object(matrix.time, 'monotonic', return_value=100):
            for value in (None, True, '190', float('inf'), float('nan'),
                          -1, 0, 100, 191):
                with self.subTest(value=value):
                    with self.assertRaisesRegex(
                            ValueError, 'Heavy-start reservation absent'):
                        matrix.run_matrix(None, None, None, None, None,
                                          heavy_start_deadline=value)

    def test_display_delay_cannot_start_heavy_work_or_skip_cleanup(self):
        control = self.work / 'control.json'
        control.write_text(json.dumps({'source_commit': 'a' * 40}))
        (self.work / 'preparation.json').write_text('{}')
        clock = [100]

        def start_display(_work):
            clock[0] = 191
            return {}

        with ExitStack() as mocks:
            mocks.enter_context(patch.dict(matrix.os.environ, {
                'RUNNER_TEMP': str(self.work),
                'XDG_RUNTIME_DIR': str(self.work)}))
            mocks.enter_context(patch.object(matrix.time, 'monotonic',
                                              side_effect=lambda: clock[0]))
            for owner, name, value in (
                (matrix, 'validate_control', {}),
                (matrix, 'verify_preparation', {}),
                (matrix.bridge, 'verify_bridge', {}),
                (matrix.readiness, 'candidate_deployment', {}),
                (matrix.bridge, 'install_driver_token', None),
                (matrix.pilot, '_memory', {'MemAvailable': 20000 * 1024**2}),
                (matrix.pilot, '_clearance', True),
                (matrix.gui, '_display_group', self.work),
                (matrix.guard, '_sample', {}),
                (matrix.gui, 'assess_display', None),
                (matrix.guard, 'acquire_validation_lease', nullcontext(None)),
            ):
                mocks.enter_context(patch.object(owner, name,
                                                  return_value=value))
            mocks.enter_context(patch.object(matrix.pilot, '_command',
                                              side_effect=['a' * 40, '']))
            mocks.enter_context(patch.object(matrix.gui, 'start_display',
                                              side_effect=start_display))
            cleanup = mocks.enter_context(patch.object(
                matrix.gui, 'display_cleanup', return_value={'cleanup': True}))
            start = mocks.enter_context(patch.object(matrix.Deadline, 'start'))
            execute = mocks.enter_context(patch.object(matrix, 'execute_entries'))
            outcome = matrix.run_matrix(
                self.work, {}, control, self.work, self.work,
                heavy_start_deadline=190)
        self.assertEqual(outcome['status'], 'FAIL')
        self.assertEqual(outcome['completed_entries'], 0)
        self.assertTrue(outcome['display_cleanup'])
        start.assert_not_called()
        execute.assert_not_called()
        cleanup.assert_called_once_with(self.work)
        self.assertIn('Heavy-start reservation exhausted before generation',
                      (self.work / 'evidence/controller-failure.txt').read_text())
        self.assertFalse((self.work / 'evidence/heavy-deadline.json').exists())

    def test_complete_serial_schedule_keeps_exact_order(self):
        calls = []

        class Runner:
            def run_entry(self, row):
                calls.append(row['id'])
                return {'id': row['id'], 'status': 'PASS',
                        'sessions': row['sessions']}

        rows = matrix.execute_entries(self.capsule, Runner(),
            matrix.Deadline(0, 7200), self.work, clock=lambda: 1)
        self.assertEqual(calls, [row['id'] for row in matrix.entries(self.capsule)])
        self.assertEqual(sum(row['sessions'] for row in rows), 84)
        with self.assertRaises(FileExistsError):
            matrix.execute_entries(self.capsule, Runner(),
                matrix.Deadline(0, 7200), self.work, clock=lambda: 1)

    def test_first_failure_preserves_original_and_not_run_rows(self):
        calls = []

        class Runner:
            def run_entry(self, row):
                calls.append(row['id'])
                if len(calls) == 2:
                    raise RuntimeError('original fixture failure')
                return {'id': row['id'], 'status': 'PASS',
                        'sessions': row['sessions']}

        rows = matrix.execute_entries(self.capsule, Runner(),
            matrix.Deadline(0, 7200), self.work, clock=lambda: 1)
        self.assertEqual(len(calls), 2)
        self.assertEqual([row['status'] for row in rows[:3]],
                         ['PASS', 'FAIL', 'NOT_RUN'])
        self.assertIn('RuntimeError: original fixture failure',
                      (self.work / 'matrix-failure.txt').read_text())

    def test_deadline_after_entry_stops_before_next_entry(self):
        clock = [0]

        class Runner:
            def run_entry(self, row):
                clock[0] = 7200
                return {'id': row['id'], 'status': 'PASS',
                        'sessions': row['sessions']}

        rows = matrix.execute_entries(self.capsule, Runner(),
            matrix.Deadline(0, 7200), self.work, clock=lambda: clock[0])
        self.assertEqual(rows[0]['status'], 'FAIL')
        self.assertTrue(all(row['status'] == 'NOT_RUN' for row in rows[1:]))

    def test_wrong_actual_session_count_fails(self):
        class Runner:
            def run_entry(self, row):
                return {'id': row['id'], 'status': 'PASS', 'sessions': 0}

        rows = matrix.execute_entries(self.capsule, Runner(),
            matrix.Deadline(0, 7200), self.work, clock=lambda: 1)
        self.assertEqual(rows[0]['status'], 'FAIL')
        self.assertEqual(rows[1]['status'], 'NOT_RUN')

    def test_original_main_and_system_exit_zero_are_exercised(self):
        source = self.work / 'proof.py'
        source.write_text("import os\nassert __name__ == '__main__'\n"
                          "assert os.environ['MATRIX_INPUT'] == 'exact'\n"
                          "print('ORIGINAL_PROOF_PASS')\nraise SystemExit(0)\n")
        config = {'id': 'fixture', 'entry_path': str(source),
                  'entry_sha256': matrix.identity(source)['sha256'],
                  'assessment': str(self.work), 'arguments': [],
                  'fixture_environment': {'MATRIX_INPUT': 'exact'}}
        wrapper = self.work / 'wrapper.py'
        wrapper.write_text(matrix._native_source(config))
        result = subprocess.run([sys.executable, '-B', str(wrapper)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        matrix.validate_entry({'sentinel': 'ORIGINAL_PROOF_PASS'}, {
            'status': 'completed', 'process_exit': 0, 'cleanup_proved': True},
            result.stdout)
        self.assertIn('"run_name": "__main__"', result.stdout)

    def test_no_success_from_zero_exit_without_original_sentinel(self):
        good = {'status': 'completed', 'process_exit': 0,
                'cleanup_proved': True}
        with self.assertRaisesRegex(ValueError, 'sentinel missing'):
            matrix.validate_entry({'sentinel': 'ORIGINAL'}, good,
                                  matrix.DONE_MARKER)
        with self.assertRaisesRegex(ValueError, 'invocation completion'):
            matrix.validate_entry({'sentinel': 'ORIGINAL'}, good, 'ORIGINAL')
        with self.assertRaisesRegex(ValueError, 'cleanup failed'):
            matrix.validate_entry({'sentinel': 'ORIGINAL'},
                dict(good, cleanup_proved=False),
                'ORIGINAL\n' + matrix.DONE_MARKER)

    def test_real_receipt_must_remain_in_owned_tree(self):
        path = self.work / 'run.json'
        path.write_text('{}')
        self.assertEqual(matrix.original_receipt(
            'receipt=' + str(path), 'receipt=', self.work, ''), path)
        with self.assertRaisesRegex(ValueError, 'escaped'):
            matrix.original_receipt('receipt=/etc/passwd', 'receipt=',
                                    self.work, '')
        owned = self.work / 'owned'
        owned.mkdir()
        with self.assertRaisesRegex(ValueError, 'escaped'):
            matrix.original_receipt('receipt=' + str(owned / '../run.json'),
                                    'receipt=', owned, '')
        with self.assertRaisesRegex(ValueError, 'missing or repeated'):
            matrix.original_receipt('receipt=x\nreceipt=y', 'receipt=',
                                    self.work, '')

    def test_missing_generation_and_b4_receipts_cannot_be_substituted(self):
        entry = next(row for row in self.capsule['gui_entries']
                     if row['id'] == 'phase8-straight_crossover_b4')
        with self.assertRaisesRegex(ValueError, 'actual receipt absent'):
            matrix.resolve_arguments(entry, self.work / 'base')
        actual = matrix.resolve_arguments(entry, self.work / 'base',
                                          self.work / 'straight.json',
                                          self.work / 'native.json')
        self.assertEqual(actual, ['--source-receipt',
            str(self.work / 'straight.json'), '--headless-receipt',
            str(self.work / 'native.json')])

    def test_series_adaptation_only_changes_two_launch_calls(self):
        manifest = {'source_files': []}
        tree = self.work / 'assessment'
        (tree / '_assessment').mkdir(parents=True)
        (tree / '_assessment/adaptations.diff').write_text('')
        originals = {}
        for name, expected_hash in matrix.SERIES.values():
            path = tree / name
            path.parent.mkdir(parents=True, exist_ok=True)
            raw = (ROOT / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected_hash)
            path.write_bytes(raw)
            originals[name] = raw.decode()
            manifest['source_files'].append({'path': name,
                'original': matrix.identity(path),
                'assessment': matrix.identity(path), 'adapted': False,
                'mode': 0o644})
        with patch.object(matrix.assessment, 'verify_assessment'):
            result = matrix.adapt_series(manifest, tree)
        for row in result['source_files']:
            before = ast.parse(originals[row['path']])
            after = ast.parse((tree / row['path']).read_text())
            for node in ast.walk(before):
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == 'subprocess'
                        and node.func.attr == 'run'):
                    node.func = ast.Name(id='_hosted_route', ctx=ast.Load())
            self.assertEqual(ast.dump(before), ast.dump(after))
            self.assertTrue(row['adapted'])

    def test_assessment_imports_reject_cached_checkout_modules_and_restore(self):
        root = self.work / 'assessment'
        package = root / 'tracktemplate'
        package.mkdir(parents=True)
        (package / '__init__.py').write_text('')
        (package / 'matrix_fixture.py').write_text('ORIGIN = "assessment"\n')
        cached = types.ModuleType('tracktemplate.matrix_fixture')
        cached.ORIGIN = 'checkout'
        original_path = sys.path[:]
        with patch.dict(sys.modules, {'tracktemplate.matrix_fixture': cached}):
            with self.assertRaisesRegex(RuntimeError, 'fixture stop'):
                with matrix.assessment_imports(root):
                    from tracktemplate import matrix_fixture

                    self.assertEqual(matrix_fixture.ORIGIN, 'assessment')
                    self.assertEqual(Path(matrix_fixture.__file__),
                                     package / 'matrix_fixture.py')
                    raise RuntimeError('fixture stop')
            self.assertIs(sys.modules['tracktemplate.matrix_fixture'], cached)
            self.assertEqual(sys.path, original_path)

    def test_original_phase3_series_runs_all_routes_and_rejects_mismatch(self):
        from tools.freecad_bridge import phase3_transition_workflow_recipe as recipe

        def contract(workflow):
            value = {'schema_version': recipe.EXPECTED_SCHEMA_VERSIONS[workflow],
                'source_document': 'offline source', 'preference_store_restored': True,
                'scenarios': [{'name': name, 'measurement': {}}
                              for name in recipe.EXPECTED_SCENARIOS[workflow]]}
            if workflow == recipe.PLAIN_LINE_EDIT:
                value['history_actions'] = [{'name': name, 'measurement': {},
                    'before_history': {'memory_bytes': 0},
                    'after_history': {'memory_bytes': 0}}
                    for name in recipe.EXPECTED_PLAIN_LINE_HISTORY_ACTIONS]
                value.update({name: {'memory_bytes': 0} for name in (
                    'initial_history', 'post_replace_history',
                    'post_change_back_history')})
                value['right_hand_save_reopen'] = {
                    'measurement': {}, 'path': 'copy',
                    'history': {'memory_bytes': 0}}
            else:
                value.update({name: {'memory_bytes': 0} for name in (
                    'initial_history', 'created_history', 'edited_history')})
                value['history_cycles'] = [{'wall_ms': 0,
                    **{key: {'memory_bytes': 0}
                       for key in ('before', 'after_undo', 'after_redo')}}
                    for _ in range(2)]
                value['save_reopen'] = {'wall_ms': 0, 'path': 'copy',
                                       'history': {'memory_bytes': 0}}
            return value

        for different in (False, True):
            with self.subTest(different=different):
                work = self.work / str(different)
                tree = work / 'assessment'
                tree.mkdir(parents=True)
                (work / 'entries').mkdir()
                row = next(row for row in self.capsule['gui_entries']
                           if row['id'] == 'phase3-four-routes')
                for name in (row['path'], 'tools/semantic_compare.py',
                        'tools/freecad_bridge/orchestration.py',
                        'tools/freecad_bridge/phase3_transition_workflow_recipe.py'):
                    path = tree / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    source = (ROOT / name).read_text()
                    if name == row['path']:
                        source = source.replace('completed = subprocess.run(',
                                                'completed = _hosted_route(', 1)
                    path.write_text(source)
                runner = matrix.MatrixRunner(work, {}, work / 'bridge', None,
                                              None, matrix.Deadline.start())
                runner.base.parent.mkdir(parents=True)
                runner.base.write_bytes(b'offline same base')
                calls = []

                def session(child, options, directory):
                    values = dict(zip(options[::2], options[1::2]))
                    workflow, route = values['--workflow'], values['--route']
                    calls.append((workflow, route))
                    path = Path(values['--run-dir'])
                    path.mkdir(parents=True)
                    actual = contract(workflow)
                    if different and route == 'modular':
                        actual['scenarios'][0]['wrong_semantics'] = True
                    matrix.write(path / 'run.json', {'status': 'completed',
                        'workflow': workflow, 'calculation_route': route,
                        'transition_workflow': {'recipe': actual},
                        'workflow_contract_sha256': 'a' * 64})
                    runner.session_count += 1
                    return '', {'receipt_path': str(directory / 'guard/result.json')}

                with patch.object(runner, '_session', side_effect=session):
                    if different:
                        with self.assertRaisesRegex(RuntimeError, 'parity failed'):
                            runner._series(row, work / 'entries' / row['id'],
                                           ['--base', str(runner.base)])
                        self.assertEqual(len(calls), 2)
                    else:
                        stdout = runner._series(row,
                            work / 'entries' / row['id'],
                            ['--base', str(runner.base)])
                        self.assertIn(row['sentinel'], stdout)
                        self.assertEqual(calls, [(workflow, route)
                            for workflow in recipe.WORKFLOWS
                            for route in recipe.ROUTES])
                comparisons = list((tree / 'benchmark-output').rglob(
                    'comparison.json'))
                self.assertEqual(len(comparisons), 1)
                self.assertEqual(json.loads(comparisons[0].read_text())['status'],
                                 'failed' if different else 'completed')

    def test_original_phase7_pair_keeps_source_cleanup_and_comparison_checks(self):
        original, _ = matrix.assessment._frozen_source(ROOT)
        capsule = json.loads((ROOT /
            'tests/fixtures/runtime-assessment-inputs.json').read_text())
        adapted = matrix.assessment._adapt_source(original, capsule)
        fixture = matrix.runpy.run_path(str(ROOT /
            'tests/validate_phase7_core_layout_export.py'))['_routed_gui_report']
        row = next(row for row in self.capsule['gui_entries']
                   if row['id'] == 'phase7-export-pair')
        for fault in (None, 'comparison', 'cleanup', 'source'):
            with self.subTest(fault=fault):
                work = self.work / str(fault)
                tree = work / 'assessment'
                for name, raw in adapted.items():
                    path = tree / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if name == row['path']:
                        raw = raw.replace(b'completed = subprocess.run(',
                                          b'completed = _hosted_route(', 1)
                    path.write_bytes(raw)
                (work / 'entries').mkdir()
                runner = matrix.MatrixRunner(work, {}, work / 'bridge', None,
                                              None, matrix.Deadline.start())
                runner.base.parent.mkdir(parents=True, exist_ok=True)
                runner.base.write_bytes(b'offline same base')
                with matrix.assessment_imports(tree):
                    definitions = matrix.runpy.run_path(str(tree / row['path']))
                harness = types.SimpleNamespace(**definitions)
                sources = harness._source_hashes()
                calls = []

                def session(child, options, directory):
                    values = dict(zip(options[::2], options[1::2]))
                    route = values['--route']
                    calls.append(route)
                    path = Path(values['--run-dir'])
                    path.mkdir(parents=True)
                    report = fixture(harness, route)
                    state = {'status': 'completed', 'route': route,
                        'workflow': report,
                        'workflow_contract_sha256': 'a' * 64,
                        'source_sha256': sources, 'source_sha256_after': sources,
                        'cleanup': {'closed': ['offline-copy'], 'remaining': []}}
                    if route == 'modular':
                        if fault == 'comparison':
                            report['recipe_contract']['stable'] = False
                        elif fault == 'cleanup':
                            state['cleanup']['remaining'] = ['offline-copy']
                        elif fault == 'source':
                            state['source_sha256_after'] = {}
                    matrix.write(path / 'run.json', state)
                    runner.session_count += 1
                    return '', {'receipt_path': str(directory / 'guard/result.json')}

                with patch.object(runner, '_session', side_effect=session):
                    if fault:
                        message = {'comparison': 'parity failed',
                            'cleanup': 'shutdown evidence',
                            'source': 'source map drifted'}[fault]
                        with self.assertRaisesRegex(RuntimeError, message):
                            runner._series(row, work / 'entries' / row['id'],
                                           ['--base', str(runner.base)])
                    else:
                        stdout = runner._series(row,
                            work / 'entries' / row['id'],
                            ['--base', str(runner.base)])
                        self.assertIn(row['sentinel'], stdout)
                self.assertEqual(calls, ['legacy', 'modular'])
                comparisons = list((tree / 'benchmark-output').rglob(
                    'comparison.json'))
                self.assertEqual(len(comparisons), 1)
                self.assertEqual(json.loads(comparisons[0].read_text())['status'],
                                 'failed' if fault else 'completed')

    def test_native_session_composes_guard_invocation_and_original_receipts(self):
        tree = self.work / 'assessment'
        tree.mkdir()
        base = tree / matrix.assessment.BASE_PATH
        base.parent.mkdir(parents=True)
        base.write_bytes(b'offline-approved-base-substitute')
        proof = tree / 'proof.py'
        proof.write_text(
            "import os\nfrom pathlib import Path\n"
            "assert __name__ == '__main__'\n"
            "assert Path(os.environ['TRACKTEMPLATE_DIAGNOSTIC_SESSION'])"
            f".parent == Path({str(self.work)!r})\n"
            "print('PROOF_PASS')\n")
        proof.chmod(0o644)
        manifest = {'source_files': [{'path': 'proof.py',
            'assessment': matrix.identity(proof), 'mode': 0o644}],
            'base_fixture': {'path': matrix.assessment.BASE_PATH,
                             **matrix.identity(base)}}
        deadline = matrix.Deadline.start()
        runner = matrix.MatrixRunner(self.work, manifest, self.work / 'bridge',
                                     object(), object(), deadline)
        observed = []

        def guard(argv, **kwargs):
            observed.append(kwargs['absolute_deadline'])
            self.assertEqual(kwargs['limits'].memory_max_mib, 4096)
            self.assertTrue(kwargs['isolate_profile'])
            path = kwargs['evidence_dir']
            path.mkdir()
            result = subprocess.run([sys.executable, '-B', argv[-1]],
                                    capture_output=True, text=True, check=False)
            (path / 'stdout').write_text(result.stdout)
            (path / 'stderr').write_text(result.stderr)
            receipt, sample = self.resource_fixture(
                kwargs['limits'].timeout_seconds)
            (path / 'measurements.jsonl').write_text(json.dumps(sample) + '\n')
            receipt['process_exit'] = result.returncode
            return receipt

        row = {'id': 'native-01', 'path': 'proof.py', 'kind': 'native',
               'timeout_seconds': 900, 'sentinel': 'PROOF_PASS', 'sessions': 1}
        with ExitStack() as stack:
            stack.enter_context(patch.object(matrix.guard,
                'run_guarded_flatpak', side_effect=guard))
            stack.enter_context(patch.object(matrix.pilot, '_deadline_clearance',
                                             return_value=True))
            stack.enter_context(patch.object(matrix.pilot, '_clearance',
                                             return_value=True))
            stack.enter_context(patch.object(matrix.readiness,
                'child_environment', return_value={}))
            stdout, _ = runner._session(row, [], self.work / 'session')
            with self.assertRaisesRegex(
                    ValueError, 'required original diagnostic reports'):
                runner._session(dict(row, id='native-24'), [],
                                self.work / 'missing-report')
        self.assertIn('PROOF_PASS', stdout)
        self.assertEqual(runner.session_count, 1)
        self.assertEqual(len(observed), 2)
        self.assertTrue(all(value <= deadline.expires for value in observed))
        self.assertEqual(json.loads((self.work / 'session/input-before.json')
                                    .read_text()), matrix.identity(base))
        self.assertEqual((self.work / 'session/input-before.json').read_bytes(),
                         (self.work / 'session/input-after.json').read_bytes())

    def test_gui_parent_gives_embedded_proofs_the_same_diagnostic_owner(self):
        class Timer:
            timeout = types.SimpleNamespace(connect=lambda _callback: None)

            def start(self, _milliseconds):
                pass

        app = types.SimpleNamespace(GuiUp=True)
        pyside = types.SimpleNamespace(QtCore=types.SimpleNamespace(QTimer=Timer))
        with patch.dict(sys.modules, {'FreeCAD': app, 'PySide6': pyside}):
            with patch.dict(matrix.os.environ, {}, clear=True):
                matrix.gui_entry({
                    'session_directory': str(self.work),
                    'fixture_environment': {
                        matrix.diagnostics.SESSION_ENV: str(self.work),
                        'TRACKTEMPLATE_STRAIGHT_CROSSOVER_FIXTURE': 'owned-copy'},
                }, '__main__')
                self.assertEqual(matrix.os.environ[
                    matrix.diagnostics.SESSION_ENV], str(self.work))
                self.assertEqual(matrix.os.environ[
                    'TRACKTEMPLATE_STRAIGHT_CROSSOVER_FIXTURE'], 'owned-copy')
        self.assertIsInstance(app._tracktemplate_matrix_session['timer'], Timer)

    def test_session_resource_completeness_and_limits(self):
        result, sample = self.resource_fixture(600)
        value = matrix.assess_session_resources(result, [sample], 600, True)
        self.assertEqual(value['status'], 'PASS')
        self.assertEqual(value['resource_accounting'], 'final')
        for key, bad, message in (
                ('memory.peak', str(4096 * 1024**2 + 1), 'ceiling'),
                ('memory.swap.current', '1', 'ceiling'),
                ('pids.current', '129', 'ceiling'),
                ('memory.events', 'high 1\nmax 0\noom 0\noom_kill 0', 'ceiling'),
                ('memory.events', 'high 0', 'Incomplete'),
                ('memory.pressure', None, 'Incomplete'),
                ('cpu.stat', 'usage_usec -1', 'Negative')):
            with self.subTest(key=key, bad=bad):
                with self.assertRaisesRegex(ValueError, message):
                    matrix.assess_session_resources(result,
                        [dict(sample, **{key: bad})], 600, True)
        with self.assertRaisesRegex(ValueError, 'kernel limits'):
            matrix.assess_session_resources(result, [sample], 601, True)
        with self.assertRaisesRegex(ValueError, 'cleanup outcome'):
            matrix.assess_session_resources(result, [sample], 600, False)
        with self.assertRaisesRegex(ValueError, 'Incomplete live'):
            matrix.assess_session_resources(result, [{}, sample], 600, True)

    def test_derivative_cannot_substitute_same_hash_in_both_source_maps(self):
        before = dict(matrix.READINESS_SOURCE_FILES)
        pins = dict(before)
        for name, (_original, successor) in matrix.READINESS_DERIVATIVES.items():
            pins[name] = successor
        # A matching receipt/current value does not prove that the
        # controller was present in the actual 33d readiness execution.
        changed = 'tools/hosted_compatibility_readiness.py'
        before[changed] = pins[changed] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'Readiness source differs'):
            matrix.verify_readiness_sources({
                'source_commit': matrix.READINESS_COMMIT,
                'source_files': before}, pins, self.work)

    def test_frozen_derivatives_reject_current_repaired_readiness(self):
        before = dict(matrix.READINESS_SOURCE_FILES)
        self.assertEqual(set(before), set(matrix.readiness.CONTROL_FILES))
        receipt = {'source_commit': matrix.READINESS_COMMIT,
                   'source_files': before}
        current = {name: matrix.identity(ROOT / name)['sha256']
                   for name in before}
        with self.assertRaisesRegex(ValueError, 'Readiness source differs'):
            matrix.verify_readiness_sources(receipt, current, self.work)
        # Reconstruct the historical positive fixture independently of the
        # later transport repair, which needs its own actual readiness proof.
        pins = dict(before)
        for name, (original, successor) in matrix.READINESS_DERIVATIVES.items():
            raw = (ROOT / name).read_bytes()
            if name.endswith('.yml'):
                # The separate diagnostic job was not in the historical
                # readiness derivative. Its current source is rejected above.
                diagnostic_job = b'  compatibility-acquisition-diagnostic:\n'
                matrix_job = b'  compatibility-matrix:\n'
                self.assertEqual(raw.count(diagnostic_job), 1)
                self.assertEqual(raw.count(matrix_job), 1)
                prefix, diagnostic = raw.split(diagnostic_job, 1)
                raw = prefix + matrix_job + diagnostic.split(matrix_job, 1)[1]
                for added in (
                    b'          - compatibility-acquisition-diagnostic\n',
                    b"      inputs.workload != 'compatibility-acquisition-diagnostic' &&\n",
                ):
                    self.assertEqual(raw.count(added), 1)
                    raw = raw.replace(added, b'', 1)
                start = (b'      - name: Capture permitted acquisition '
                         b'failure originals separately\n')
                end = (b'      - name: Run the separate 90-second GUI '
                       b'readiness proof\n')
                self.assertEqual(raw.count(start), 1)
                self.assertEqual(raw.count(end), 1)
                prefix, diagnostic = raw.split(start, 1)
                raw = prefix + end + diagnostic.split(end, 1)[1]
            else:
                added = b'            "- compatibility-acquisition-diagnostic",\n'
                self.assertEqual(raw.count(added), 1)
                raw = raw.replace(added, b'', 1)
            pins[name] = hashlib.sha256(raw).hexdigest()
            self.assertEqual(before[name], original)
            self.assertEqual(pins[name], successor)
            path = self.work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        matrix.verify_readiness_sources(receipt, pins, self.work)
        with self.assertRaisesRegex(ValueError, 'Readiness source differs'):
            matrix.verify_readiness_sources(dict(receipt, source_commit='a' * 40),
                                            pins, self.work)
        for name in matrix.READINESS_DERIVATIVES:
            with self.subTest(changed=name):
                path = self.work / name
                original_bytes = path.read_bytes()
                if name.endswith('.yml'):
                    needle = b'compatibility_readiness_transport.py complete'
                    self.assertEqual(original_bytes.count(needle), 1)
                    changed = original_bytes.replace(
                        needle, b'compatibility_readiness_transport.py publish')
                else:
                    changed = original_bytes + b'\n# Unreviewed validator edit\n'
                path.write_bytes(changed)
                # Even self-consistent new caller pins cannot approve
                # another readiness job or validator revision.
                altered_pins = dict(pins, **{
                    name: matrix.identity(path)['sha256']})
                with self.assertRaisesRegex(
                        ValueError, 'derivative source identity changed'):
                    matrix.verify_readiness_sources(receipt, altered_pins,
                                                    self.work)
                path.write_bytes(original_bytes)
        matrix.verify_readiness_sources(receipt, pins, self.work)

    def test_control_requires_exact_actual_readiness_and_review(self):
        receipts = self.work / 'receipts'
        receipts.mkdir()
        commit = '1' * 40
        source_root = self.work / 'reviewed-source-fixture'
        for name in matrix.CONTROL_FILES:
            path = source_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('Offline source identity fixture: ' + name + '\n')
        canonical = source_root / matrix.assessment.CANONICAL_PATH
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_bytes((ROOT / matrix.assessment.CANONICAL_PATH).read_bytes())
        pins = {name: matrix.identity(source_root / name)['sha256']
                for name in matrix.CONTROL_FILES}
        from tools.compatibility_evidence_output import RUNTIME

        prerequisite = {
            'review': {'status': 'PASS', 'source_commit': commit,
                'source_files': pins, 'independent': True,
                'stage': 'qualification',
                'output_scope_sha256': matrix.readiness.SCOPE_SHA256},
            'recovery': {'status': 'PASS', 'source_commit': commit,
                'source_files': pins, 'independent_preservation': True},
            'readiness': {'status': 'PASS', 'source_commit': '2' * 40,
                'source_files': {name: pins[name]
                                for name in matrix.readiness.CONTROL_FILES},
                'independent': True, 'stage': 'readiness', 'runtime': RUNTIME,
                'base_sha256': matrix.assessment.BASE_SHA256,
                'candidate_sha256': matrix.assessment.CANDIDATE_SHA256,
                'artifact_sha256': 'a' * 64, 'run_id': '123'},
        }
        control = {
            'schema_version': 1, 'stage': 'qualification',
            'owner_decision': 'D-P9-024', 'owner_statement_sha256':
            'd193c34674fa4eb09de4ccaad6a6ddfbf1a930fdd50f369652f33204e2daa19a',
            'output_scope_sha256': matrix.readiness.SCOPE_SHA256,
            'app_commit': matrix.readiness.APP_COMMIT,
            'runtime_commit': matrix.readiness.RUNTIME_COMMIT,
            'capsule_sha256': matrix.CAPSULE_SHA256,
            'heavy_seconds': 7200, 'display_seconds': 7300,
            'outer_seconds': 8400, 'installer_seconds': 540,
            'readiness_seconds': 90, 'memory_mib': 4096, 'reserve_mib': 8192,
            'cpu_percent': 100, 'tasks': 128, 'swap_bytes': 0,
            'parallel': False, 'retry': False, 'runtime_admission': False,
            'zy_execution': False, 'source_commit': commit, 'source_files': pins,
        }
        env = {'GITHUB_ACTIONS': 'true',
            'GITHUB_REPOSITORY': 'Richard-Gnitnub/tracktemplate',
            'GITHUB_EVENT_NAME': 'workflow_dispatch',
            'RUNNER_ENVIRONMENT': 'github-hosted', 'GITHUB_RUN_ATTEMPT': '1',
            'RUNNER_OS': 'Linux', 'RUNNER_ARCH': 'X64', 'GITHUB_SHA': commit}
        for name, value in prerequisite.items():
            path = receipts / (name + '.json')
            matrix.write(path, value)
            control[name] = {'path': path.name,
                             'sha256': matrix.identity(path)['sha256']}
        matrix.validate_control(control, receipts, env, source_root)
        for key, wrong in (('heavy_seconds', 7201), ('parallel', True),
                           ('retry', True), ('runtime_admission', True),
                           ('zy_execution', True), ('heavy_seconds', 7200.0)):
            with self.subTest(key=key, wrong=wrong):
                with self.assertRaisesRegex(ValueError, 'authority or limits'):
                    matrix.validate_control(dict(control, **{key: wrong}),
                                             receipts, env, source_root)
        with self.assertRaisesRegex(ValueError, 'Exact matrix control'):
            matrix.validate_control(dict(control, private_data='excluded'),
                                     receipts, env, source_root)
        path = receipts / 'readiness.json'
        for invalid in ('not-a-commit', 'A' * 40, '2' * 39, True, None):
            with self.subTest(source_commit=invalid):
                candidate = dict(prerequisite['readiness'],
                                 source_commit=invalid)
                path.write_text(json.dumps(candidate))
                control['readiness']['sha256'] = matrix.identity(path)['sha256']
                with self.assertRaisesRegex(ValueError,
                                            'Readiness source commit'):
                    matrix.validate_control(control, receipts, env, source_root)
        for field, index, invalid in (('freecad', 0, True),
                                      ('freecad', 0, 1.0),
                                      ('python', 0, 3.0)):
            with self.subTest(field=field, invalid=invalid):
                runtime = json.loads(json.dumps(RUNTIME))
                runtime[field][index] = invalid
                candidate = dict(prerequisite['readiness'], runtime=runtime)
                path.write_text(json.dumps(candidate))
                control['readiness']['sha256'] = matrix.identity(path)['sha256']
                with self.assertRaisesRegex(ValueError,
                                            'Actual reviewed runtime field'):
                    matrix.validate_control(control, receipts, env, source_root)
        prerequisite['readiness']['runtime'] = dict(RUNTIME, occt='wrong')
        path.write_text(json.dumps(prerequisite['readiness']))
        control['readiness']['sha256'] = matrix.identity(path)['sha256']
        with self.assertRaisesRegex(ValueError, 'Actual reviewed runtime'):
            matrix.validate_control(control, receipts, env, source_root)


if __name__ == '__main__':
    unittest.main()
