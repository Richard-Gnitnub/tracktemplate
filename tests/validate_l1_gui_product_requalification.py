"""Test exact product repair admission without FreeCAD or hosted execution."""

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]

from tools import hosted_l1_gui_validation as gui  # noqa: E402
import validate_hosted_l1_gui_controls as prior  # noqa: E402
import validate_l1_gui_lifecycle_controls as diagnostic  # noqa: E402


REPAIR_PATH = 'tracktemplate/adapters/freecad/chair_reference_preview.py'
REPAIR = {
    'scope_id': 'L1-GUI-PREVIEW-ACTIVATION-001',
    'base_commit': 'ad554906172df31008d3a16672f392cdc6473325',
    'path': REPAIR_PATH,
    'baseline_sha256': (
        '3869a12c81d7ed0eca56547dfe66da87283adfa29952b19a7967149652424604'
    ),
    'sha256': (
        '0f15b9765e7787ef94116f378fa66a2fe4ecee13725796a3474a51e30e4123da'
    ),
    'failure_run_id': 41304566238,
    'authority_sha256': (
        '60a6466e8022793407ad779986ca42920c3e0ee9886016f0a64f33197fef40af'
    ),
}


def repaired_authority(stage='gui'):
    record = prior.authority()
    record['gui_entry_sha256'] = gui.DIAGNOSTIC_ENTRY_SHA256
    record['product_requalification'] = dict(
        REPAIR, source_commit=record['source_commit'],
        independent_review='PASS', review_sha256='3' * 64,
    )
    record['gui_readiness_review'].update(
        gui_entry_sha256=record['gui_entry_sha256'],
        product_requalification=copy.deepcopy(
            record['product_requalification']),
    )
    if stage == 'readiness':
        record.update(stage=stage, freecad_limits=vars(gui.limits(stage)),
                      display_limits=vars(gui.display_limits(stage)))
        record.pop('gui_readiness_review')
    return record


class ProductRequalification(unittest.TestCase):
    def test_ordinary_source_and_reviewed_repair_keep_stage_limits(self):
        gui.validate_authority(prior.authority(), prior.environment())
        for stage in ('readiness', 'gui'):
            gui.validate_authority(
                repaired_authority(stage),
                dict(prior.environment(), L1_GUI_STAGE=stage),
            )

    def test_repair_record_requires_exact_scope_source_and_review(self):
        record = repaired_authority('readiness')
        environ = dict(prior.environment(), L1_GUI_STAGE='readiness')
        for key in record['product_requalification']:
            for value in (None, 'unreviewed'):
                bad = copy.deepcopy(record)
                bad['product_requalification'][key] = value
                with (
                    self.subTest(key=key, value=value),
                    self.assertRaises(ValueError),
                ):
                    gui.validate_authority(bad, environ)
            bad = copy.deepcopy(record)
            del bad['product_requalification'][key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                gui.validate_authority(bad, environ)
        extra = dict(record['product_requalification'], extra_product='allowed')
        for value in ({}, [], 'approved', extra):
            bad = dict(record, product_requalification=value)
            with self.subTest(record=value), self.assertRaises(ValueError):
                gui.validate_authority(bad, environ)
        bad = dict(record, gui_entry_sha256='0' * 64)
        with self.assertRaises(ValueError):
            gui.validate_authority(bad, environ)

    def test_repair_cannot_reuse_stale_or_different_readiness(self):
        record = repaired_authority()
        for key, value in (
            ('product_requalification', None),
            ('product_requalification', dict(record['product_requalification'],
                                             review_sha256='4' * 64)),
            ('source_commit', gui.DIAGNOSTIC_BASE),
            ('control_files_sha256', {}),
            ('input_hashes', {}),
        ):
            bad = copy.deepcopy(record)
            bad['gui_readiness_review'][key] = value
            with (
                self.subTest(key=key, value=value),
                self.assertRaises(ValueError),
            ):
                gui.validate_authority(bad, prior.environment())

    def test_historical_diagnostic_refuses_product_requalification(self):
        record = diagnostic.diagnostic_authority()
        record['product_requalification'] = repaired_authority()[
            'product_requalification']
        with self.assertRaises(ValueError):
            gui.validate_authority(
                record,
                dict(prior.environment(), L1_LIFECYCLE_DIAGNOSTIC='true'),
            )

    def test_frozen_source_requires_record_and_only_one_modified_path(self):
        valid = repaired_authority()
        for changed, record in (
            ('M\t' + REPAIR_PATH, prior.authority()),
            ('M\ttracktemplate/other.py', valid),
            ('M\t' + REPAIR_PATH + '\nM\ttracktemplate/other.py', valid),
            ('M\t' + REPAIR_PATH
             + '\nM\ttests/hosted_l1_current_source_suite.py', valid),
            ('D\t' + REPAIR_PATH, valid),
            ('A\t' + REPAIR_PATH, valid),
            ('', valid),
        ):
            with self.subTest(changed=changed, repair=record.get(
                    'product_requalification') is not None):
                with patch.object(gui.native, 'command', return_value=changed):
                    with self.assertRaises(ValueError):
                        gui.validate_frozen_source(record)
        with patch.object(gui.native, 'command', return_value=''):
            gui.validate_frozen_source(prior.authority())

    def test_source_checks_exact_bytes_and_original_baseline(self):
        baseline = b'baseline fixture\n'
        repaired = b'repaired fixture\n'
        repair = dict(REPAIR,
                      baseline_sha256=hashlib.sha256(baseline).hexdigest(),
                      sha256=hashlib.sha256(repaired).hexdigest())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / REPAIR_PATH
            path.parent.mkdir(parents=True)
            path.write_bytes(repaired)
            path.chmod(0o644)
            with (
                patch.object(gui, 'ROOT', root),
                patch.object(gui, 'PRODUCT_REPAIR', repair),
                patch.object(gui.native, 'command',
                             return_value='M\t' + REPAIR_PATH),
                patch.object(gui.subprocess, 'run',
                             return_value=SimpleNamespace(stdout=baseline)),
            ):
                gui.validate_frozen_source(repaired_authority())
                path.write_bytes(b'other repair\n')
                with self.assertRaises(ValueError):
                    gui.validate_frozen_source(repaired_authority())
                path.write_bytes(repaired)
                path.chmod(0o755)
                with self.assertRaises(ValueError):
                    gui.validate_frozen_source(repaired_authority())
                path.chmod(0o644)
                with patch.object(
                    gui.subprocess, 'run',
                    return_value=SimpleNamespace(stdout=b'other baseline'),
                ):
                    with self.assertRaises(ValueError):
                        gui.validate_frozen_source(repaired_authority())
                target = root / 'target.py'
                target.write_bytes(repaired)
                path.unlink()
                path.symlink_to(target)
                with self.assertRaises(ValueError):
                    gui.validate_frozen_source(repaired_authority())

    def test_prepare_admits_only_the_actual_reviewed_product_bytes(self):
        record = repaired_authority('readiness')
        record['control_files_sha256'] = {
            name: gui.digest(ROOT / name) for name in gui.CONTROL_FILES
        }
        environ = dict(prior.environment(), L1_GUI_STAGE='readiness',
                       L1_GUI_CONTROL=json.dumps(record))
        original_command = gui.native.command

        def command(*args):
            if args[:2] == ('git', 'rev-parse'):
                return record['source_commit']
            if args[:2] == ('git', 'status'):
                return ''
            return original_command(*args)

        with (
            patch.dict(gui.os.environ, environ, clear=True),
            patch.object(gui.os, 'getuid', return_value=1000),
            patch.object(gui.resource, 'setrlimit'),
            patch.object(gui, 'validate_host', return_value={}),
            patch.object(gui.native, 'command', side_effect=command),
            patch.object(gui, 'write') as write,
        ):
            gui.prepare(Path('/unused-admission-test'))
            self.assertEqual(write.call_count, 3)
            self.assertEqual(write.call_args_list[1].args[1], record)

    def test_prepare_rejects_other_product_before_writing_admission(self):
        record = repaired_authority('readiness')
        environ = dict(prior.environment(), L1_GUI_STAGE='readiness',
                       L1_GUI_CONTROL=json.dumps(record))

        def command(*args):
            if args[:2] == ('git', 'rev-parse'):
                return record['source_commit']
            if args[:2] == ('git', 'status'):
                return ''
            return 'M\ttracktemplate/other.py'

        with (
            patch.dict(gui.os.environ, environ, clear=True),
            patch.object(gui.os, 'getuid', return_value=1000),
            patch.object(gui.resource, 'setrlimit'),
            patch.object(gui, 'validate_host', return_value={}),
            patch.object(gui.native, 'command', side_effect=command),
            patch.object(gui, 'write') as write,
        ):
            with self.assertRaises(ValueError):
                gui.prepare(Path('/unused-admission-test'))
            write.assert_not_called()


if __name__ == '__main__':
    unittest.main()
