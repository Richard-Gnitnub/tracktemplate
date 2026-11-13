#!/usr/bin/env python3
"""Prepare one separately authorised hosted L1 GUI proof.

This entry composes the accepted public-input and evidence transport helpers.
An owner record binds the reviewed source and added display resources; the
record does not authenticate consent or reset the exhausted repair allowance.
"""

from contextlib import ExitStack
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import secrets
import shutil
import subprocess
import sys
import time
import traceback
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import hosted_l1_private_validation as native  # noqa: E402
from tools import hosted_l1_gui_install as installer  # noqa: E402


guard = native.guard
original = native.original
require = native.require
write = native.write
digest = native.digest
BASE = 'ad554906172df31008d3a16672f392cdc6473325'
SCOPE = 'L1-QUALIFICATION-001-hosted-gui-v1'
SENTINEL = 'L1 current-source hosted GUI validation passed'
READINESS_SENTINEL = 'L1 current-source hosted GUI readiness passed'
ENTRY = 'tests/hosted_l1_gui_suite.py'
LIMITS = guard.ValidationLimits(4096, 7200)
DISPLAY_LIMITS = guard.ValidationLimits(256, 7300, 25, 16)
DISPLAY = ':99'
RESERVE_MIB = 8192
INPUT_ARCHIVE = {
    'asset_id': 693190316, 'bytes': 15554560,
    'sha256': '78daa0dce01037118bbcededc05092adfef2dbb46ca20867dfb89be1d80854b6',
}
HANDLING_DECISION = (
    'owner-public-handling-decision.json@sha256:'
    '4655a8309c8ad11239053a22955307b4bbaa631eaa1c7f0c58cdbd7ce48c3c48'
)
CONTROL_FILES = (*native.CONTROL_FILES,
                 '.github/workflows/l1-gui-validation.yml',
                 'tools/hosted_l1_gui_validation.py', ENTRY,
                 'tools/hosted_l1_gui_install.py',
                 'tests/validate_hosted_l1_gui_install.py',
                 'tests/validate_hosted_l1_gui_controls.py')
FROZEN_PATHS = (
    'tracktemplate', 'TrackTemplate.FCMacro', 'AdvancedTurnout.FCMacro',
    'model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro',
    'tests/hosted_l1_current_source_suite.py', *native.CONTROL_FILES,
)
PRODUCT_REPAIR = {
    'scope_id': 'L1-GUI-PREVIEW-ACTIVATION-001',
    'base_commit': BASE,
    'path': 'tracktemplate/adapters/freecad/chair_reference_preview.py',
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
DIAGNOSTIC_SCOPE = 'L1-GUI-LIFECYCLE-DIAGNOSTIC-001'
DIAGNOSTIC_BASE = 'e6c9a0e3c3215f010138092e23cec7cd0b04794f'
DIAGNOSTIC_ENTRY_SHA256 = (
    '1150aab0a68d75a9048bbfd096f60f270d8f452c7333ab692ba063fd878e7012'
)
DIAGNOSTIC_READINESS_EVIDENCE = (
    'de6e779709ea5fd1569f88773becc217d05221ebd333640a697c1774e38b41d9'
)
DIAGNOSTIC_READINESS_REVIEW = (
    '6c4143761b94d2a45d4ce44caa62da2f0fd1ab8059a9bf840bfe04da4b56e8f9'
)
DIAGNOSTIC_READINESS_PRESERVATION = (
    '4ab46479ba9b05e16af9dbc952e214ac1f60cfc5a83c799434c44f3c659f9cd5'
)
DIAGNOSTIC_FILES = (
    'tools/l1_gui_lifecycle_observer.py',
    'tests/validate_l1_gui_lifecycle_observer.py',
    'tests/validate_l1_gui_lifecycle_controls.py',
)
DIAGNOSTIC_CHANGED_CONTROLS = (
    '.github/workflows/l1-gui-validation.yml',
    'tools/hosted_l1_gui_validation.py',
)

REA_SCOPE = 'REA-BC-LIFECYCLE-GUI-001'
REA_REF = 'refs/heads/codex/rea-bc-exit-profile'
REA_STRAIGHT_SCOPE = 'REA-BC-STRAIGHT-GUI-001'
REA_STRAIGHT_REF = 'refs/heads/codex/rea-bc-straight-closure'
REA_ENTRY = 'tests/hosted_rea_trackwork_gui_suite.py'
REA_INPUTS = (
    'tests/fixtures/phase9b-rea-bc-source.json',
    'tests/validate_phase1_turnout.py',
    'reference/contracts/phase1-compatibility.json',
    'reference/contracts/phase1-transition-pilot.json',
    'TrackTemplate.FCMacro',
    'model_railway_curve_template_multitrack_v10_2a8a7b15_'
    'chair_performance_and_representation.FCMacro',
)
REA_CONTROL_FILES = (
    '.github/workflows/l1-gui-validation.yml',
    'tools/hosted_l1_gui_validation.py',
    'tools/hosted_l1_gui_install.py',
    'tools/hosted_l1_private_validation.py',
    'tools/hosted_native_geometry_pilot.py',
    'tools/freecad_validation_guard.py',
    'tests/hosted_l1_gui_suite.py',
    'tests/freecad_validate_rea_trackwork.py',
    'tests/validate_hosted_l1_gui_controls.py', REA_ENTRY,
)

TO_SCOPE = 'TO-001-fixed-single-rail-gui-v1'
TO_BASE = '7fa2a5a1bd637cf2c3847ec5e35dc35bd04eed77'
TO_ENTRY = 'tests/freecad_validate_to_single_rail_gui.py'
TO_HANDLING_DECISION = (
    'to001-handling-owner-decision.json@sha256:'
    '6a63891440b9c5ae6e5b814a4795485e50b9ccb321837891cded533c46c09398'
)
TO_NATIVE_REUSE_SCOPE = 'TO-001-GUI-PICK-DIAGNOSTIC-001'
TO_NATIVE_REUSE_PATHS = frozenset({
    TO_ENTRY, 'tools/hosted_l1_gui_validation.py',
    'tests/validate_to_single_rail_gui_entry.py',
    'tests/validate_hosted_l1_gui_controls.py',
    'reference/current/PHASE_EVIDENCE.md', 'reference/ste-review-state.json',
})


TO_WORKLOADS = ('to-single', 'to-crossing')
TO_CROSSING_MANIFEST_SHA256 = (
    '303135d7f7f6de4bbee5ee8400bf9a9db2b8ab2e687ef3557ef140154c6b737e'
)
TO_CROSSING_READER = 'tracktemplate/application/chair_crossing_pair_catalogue.py'
TO_CROSSING_READER_SHA256 = (
    '71c285a17d4061db624c690ea9f7b5800528fa99483b41f455b480fd411f1872'
)


def to_profile(workload='to-single'):
    """Select a fixed GUI journey without changing historical defaults."""
    require(workload in TO_WORKLOADS, 'Unsupported TO GUI workload')
    if workload == 'to-crossing':
        return {
            'scope': 'TO-001-fixed-crossing-gui-v1',
            'base': 'a801f4444bec2f6799e7d2ad1fa2da3aac78db95',
            'entry': 'tests/freecad_validate_to_crossing_chairs_gui.py',
            'entry_test': 'tests/validate_to_crossing_chairs_entries.py',
            'selector': ('freecad_validate_to_crossing_chairs_gui.'
                         'ToCrossingGui.test_authorised_gui_stage'),
            'prefix': 'TRACKTEMPLATE_TO_CROSSING_GUI=',
        }
    return {
        'scope': TO_SCOPE, 'base': TO_BASE, 'entry': TO_ENTRY,
        'entry_test': 'tests/validate_to_single_rail_gui_entry.py',
        'selector': ('freecad_validate_to_single_rail_gui.'
                     'ToSingleRailGui.test_authorised_gui_stage'),
        'prefix': 'TRACKTEMPLATE_TO_SINGLE_GUI=',
    }


def to_handling_decision(record, workload='to-single'):
    """Bind the new owner record to the exact reviewed publication manifest."""
    to_profile(workload)
    if workload == 'to-single':
        return TO_HANDLING_DECISION
    decision = record.get('handling_decision')
    prefix = 'to-crossing-handling-owner-decision.json@sha256:'
    require(isinstance(decision, str) and decision.startswith(prefix)
            and _hash(decision[len(prefix):])
            and decision[len(prefix):] != '0' * 64
            and record.get('publication_manifest_sha256')
            == TO_CROSSING_MANIFEST_SHA256,
            'TO crossing handling decision or manifest absent')
    return decision


def to_counts(stage, *, workload='to-single'):
    """Fixed GUI witnesses; native topology qualification stays separate."""
    to_profile(workload)
    require(stage in ('readiness', 'gui'), 'Unsupported TO GUI stage')
    result = {
        'binding_checks': 1, 'catalogue_contracts': 2,
        'source_frame_inputs': 59, 'source_frame_comparisons': 59,
        'successful_previews': 1, 'assemblies': 12, 'layers': 42,
        'successful_components': 270, 'layer_visibility_checks': 42,
        'viewport_picks': 1, 'late_verifier_failures': 1,
        'rolled_back_components': 270, 'source_preservation_checks': 4,
        'preview_disposals': 1, 'screenshots': 6,
        'readiness_empty_documents': 0,
    }
    if workload == 'to-crossing':
        result.update(catalogue_contracts=4, source_frame_inputs=50,
                      source_frame_comparisons=50, assemblies=4, layers=137,
                      successful_components=135, layer_visibility_checks=137,
                      rolled_back_components=135)
    if stage == 'readiness':
        contracts, frames = result['catalogue_contracts'], result['source_frame_inputs']
        result = dict.fromkeys(result, 0)
        result.update(binding_checks=1, catalogue_contracts=contracts,
                      source_frame_inputs=frames, screenshots=1,
                      readiness_empty_documents=1)
    return result


def validate_to_counts(counts, stage, *, workload='to-single'):
    expected = to_counts(stage, workload=workload)
    require(type(counts) is dict and set(counts) == set(expected)
            and all(type(counts[key]) is int and counts[key] == value
                    for key, value in expected.items()),
            'TO GUI operation counts differ')


def to_images(stage, *, workload='to-single'):
    to_profile(workload)
    require(stage in ('readiness', 'gui'), 'Unsupported TO image stage')
    if workload == 'to-crossing':
        if stage == 'readiness':
            return {'to-crossing-readiness.png'}
        return {
            'to-crossing-overview.png', 'to-crossing-XA-AA.png',
            'to-crossing-CD-DD.png', 'to-crossing-selected-chair.png',
            'to-crossing-layer-hidden.png', 'to-crossing-rollback-restored.png',
        }
    if stage == 'readiness':
        return {'to-single-readiness.png'}
    return {
        'to-single-overview.png', 'to-corrected-heels.png',
        'to-retained-placements.png', 'to-selected-chair.png',
        'to-chair-layer-hidden.png', 'to-rollback-restored.png',
    }


def to_report(stdout, *, workload='to-single'):
    """Read one complete report; never accept duplicate or nonfinite JSON."""
    prefix = to_profile(workload)['prefix']
    lines = [line[len(prefix):] for line in stdout.splitlines()
             if line.startswith(prefix)]
    require(stdout.count(prefix) == 1 and len(lines) == 1,
            'Expected one TO GUI report')

    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate TO report field')
            result[key] = value
        return result

    def constant(_value):
        raise ValueError('Nonfinite TO report')

    def finite_float(value):
        number = float(value)
        require(math.isfinite(number), 'Nonfinite TO report number')
        return number

    result = json.loads(lines[0], object_pairs_hook=pairs,
                        parse_constant=constant, parse_float=finite_float)
    require(type(result) is dict, 'TO report object required')
    return result


def to_control_files(workload='to-single'):
    profile = to_profile(workload)
    return tuple(dict.fromkeys((*native.to_profile(workload)['control_files'],
        '.github/workflows/l1-gui-validation.yml',
        'tools/hosted_l1_gui_validation.py', 'tools/hosted_l1_gui_install.py',
        'tests/hosted_l1_gui_suite.py', profile['entry'],
        profile['entry_test'],
        'tests/validate_hosted_l1_gui_controls.py',
        'tests/validate_hosted_l1_gui_install.py')))


def validate_to_native_reuse(record, *, workload='to-single'):
    """Bind unchanged native evidence to one reviewed GUI diagnostic delta."""
    proof = record.get('prior_native_evidence', {})
    source = proof.get('source_commit')
    require(type(source) is str and re.fullmatch(r'[0-9a-f]{40}', source),
            'TO native source identity absent')
    reuse = record.get('native_source_reuse')
    if source == record['source_commit']:
        require(reuse is None, 'Unexpected TO native source reuse record')
        return
    require(workload == 'to-single',
            'TO crossing requires native evidence for the same source')
    expected = {
        'schema': 1, 'scope_id': TO_NATIVE_REUSE_SCOPE,
        'status': 'PASS', 'independent_review': 'PASS',
        'from_commit': source, 'to_commit': record['source_commit'],
        'native_run_id': proof.get('run_id'),
        'native_evidence_sha256': proof.get('evidence_sha256'),
    }
    require(type(reuse) is dict
            and set(reuse) == {*expected, 'review_sha256', 'changed_paths'}
            and all(type(reuse[key]) is type(value) and reuse[key] == value
                    for key, value in expected.items())
            and _hash(reuse['review_sha256']),
            'TO native source reuse review absent or differs')
    paths = reuse['changed_paths']
    require(type(paths) is list and paths
            and all(type(path) is str for path in paths)
            and paths == sorted(set(paths))
            and set(paths) <= TO_NATIVE_REUSE_PATHS,
            'TO native source reuse paths differ')


def validate_to_native_source(record, *, workload='to-single'):
    """Reject every unreviewed tracked delta before input acquisition."""
    validate_to_native_reuse(record, workload=workload)
    reuse = record.get('native_source_reuse')
    if reuse is None:
        return
    source, target = reuse['from_commit'], reuse['to_commit']
    for revision in (source, target):
        require(native.command('git', 'rev-parse', '--verify',
                               revision + '^{commit}') == revision,
                'TO native source commit unavailable')
    require(native.command('git', 'rev-parse', 'HEAD') == target,
            'TO native source target differs from checkout')
    native.command('git', 'merge-base', '--is-ancestor', source, target)
    names = native.command('git', 'diff', '--no-renames', '--name-status',
                           '-z', source, target, '--')
    fields = names.rstrip('\0').split('\0') if names else []
    require(len(fields) % 2 == 0
            and all(status == 'M' for status in fields[::2]),
            'TO native source reuse requires modified files only')
    paths = sorted(fields[1::2])
    require(paths == reuse['changed_paths'],
            'TO native source dependencies or reviewed paths changed')


def validate_to_authority(record, environ):
    """Require exact TO input rights, source, recovery and prior proofs."""
    stage = selected_stage(environ)
    workload = selected_workload(environ)
    profile = to_profile(workload)
    native_profile = native.to_profile(workload)
    decision = to_handling_decision(record, workload)
    expected = {
        'schema': 1, 'scope_id': profile['scope'], 'workload': workload,
        'stage': stage, 'source_commit': environ['GITHUB_SHA'],
        'source_base_commit': profile['base'], 'owner': 'Richard-Gnitnub',
        'execution_authorized': True, 'independent_review': 'PASS',
        'run_attempt': 1, 'initial_reserve_mib': RESERVE_MIB,
        'software_renderer': 'llvmpipe',
        'historical_repair_allowance_consumed': True,
        'automatic_retry': False, 'handling_decision': decision,
        'freecad_limits': vars(limits(stage, workload)),
        'display_limits': vars(display_limits(stage, workload)),
        'input_hashes': native_profile['input_hashes'],
        'native_entry_sha256': native_profile['entry_sha256'],
    }
    require(type(record) is dict and all(
        type(record.get(key)) is type(value) and record[key] == value
        for key, value in expected.items()), 'TO GUI authority differs')
    require(environ.get('GITHUB_REF') == 'refs/heads/main'
            and environ.get('GITHUB_RUN_ATTEMPT') == '1'
            and re.fullmatch(r'[0-9a-f]{40}', record['source_commit'])
            and not diagnostic_enabled(environ),
            'TO source or diagnostic selection differs')
    require(all(isinstance(record.get(key), str) and record[key].strip()
                for key in ('decision_id', 'dispatch_nonce'))
            and _hash(record.get('gui_entry_sha256')),
            'TO source or decision identity absent')
    hashes = record.get('control_files_sha256')
    require(type(hashes) is dict and set(hashes) == set(to_control_files(workload))
            and all(_hash(value) for value in hashes.values()),
            'TO control source bindings incomplete')
    handling = record.get('handling_review', {})
    expected_handling = {
        'decision_sha256': decision.rsplit(':', 1)[1],
        'independent_review': 'PASS', 'retention_days': 30,
        'independent_preservation': True, 'readiness_images': 1,
        'gui_images': 6, 'source_archive_upload': False,
        'operator_documents': False, 'exact_exports': False,
        'working_fcstd_upload': False,
    }
    if workload == 'to-crossing':
        expected_handling['publication_manifest_sha256'] = TO_CROSSING_MANIFEST_SHA256
    require(type(handling) is dict and set(handling) == set(expected_handling)
            and all(type(handling[key]) is type(value)
                    and handling[key] == value
                    for key, value in expected_handling.items()),
            'TO screenshot handling differs')
    publication = record.get('publication_review', {})
    require(publication.get('status') == publication.get('independent_review')
            == 'PASS' and publication.get('input_hashes') == native_profile['input_hashes']
            and publication.get('handling_decision') == decision
            and _hash(publication.get('evidence_sha256'))
            and isinstance(publication.get('publication_basis'), str)
            and publication['publication_basis'].strip(),
            'TO input publication basis unproved')
    acquisition = record.get('native_control', {})
    expected_acquisition = {
        'scope_id': native_profile['scope'], 'source_commit': record['source_commit'],
        'entry_sha256': native_profile['entry_sha256'],
        'handling_decision': decision,
        'input_hashes': native_profile['input_hashes'],
        'input_archive': record.get('input_archive'),
        'publication_review': publication,
    }
    require(all(acquisition.get(key) == value
                for key, value in expected_acquisition.items()),
            'TO acquisition scope differs')
    if workload == 'to-crossing':
        require(acquisition.get('publication_manifest_sha256')
                == TO_CROSSING_MANIFEST_SHA256,
                'TO crossing acquisition manifest differs')
    native.validate_to_acquisition(acquisition, workload=workload)
    archive = record.get('input_archive', {})
    require(type(archive) is dict
            and set(archive) == {'asset_id', 'bytes', 'sha256'}
            and type(archive['asset_id']) is int and archive['asset_id'] > 0
            and type(archive['bytes']) is int
            and 0 < archive['bytes'] <= native.payload.MAX_ARCHIVE_BYTES
            and _hash(archive['sha256']), 'TO input asset binding differs')
    recovery = record.get('gui_recovery', {})
    require(recovery.get('status') == recovery.get('independent_review')
            == 'PASS' and recovery.get('source_commit') == record['source_commit']
            and _hash(recovery.get('evidence_sha256')),
            'TO recovery unproved')
    proof = record.get('prior_native_evidence', {})
    expected_native = {
        'status': 'PASS', 'independent_review': 'PASS',
        'entry_sha256': native_profile['entry_sha256'], 'scope_id': native_profile['scope'],
        'input_hashes': native_profile['input_hashes'],
        'tests': 1, 'skips': 0, 'run_attempt': 1, 'cleanup': True,
        'evidence_verified': True, 'independent_preservation': True,
        'source_frame_comparisons': 59, 'component_comparisons': 270,
        'successful_components': 270, 'rolled_back_components': 270,
    }
    if workload == 'to-crossing':
        expected_native.update(
            source_frame_comparisons=50, component_comparisons=135,
            successful_components=135, rolled_back_components=135,
            stored_compound_checks=135, stored_child_checks=135,
        )
    require(all(type(proof.get(key)) is type(value) and proof[key] == value
                for key, value in expected_native.items())
            and type(proof.get('run_id')) is int and proof['run_id'] > 0
            and str(proof['run_id']) != environ['GITHUB_RUN_ID']
            and _hash(proof.get('evidence_sha256')),
            'TO independent native proof absent or differs')
    validate_to_native_reuse(record, workload=workload)
    if stage == 'gui':
        ready = record.get('gui_readiness_review', {})
        expected_ready = {key: record[key] for key in (
            'scope_id', 'workload', 'source_commit', 'gui_entry_sha256',
            'control_files_sha256', 'input_hashes', 'handling_review',
            'handling_decision', 'publication_review',
        )}
        expected_ready.update(
            status='PASS', independent_review='PASS', stage='readiness',
            freecad_limits=vars(limits('readiness', workload)),
            display_limits=vars(display_limits('readiness', workload)),
            tests=1, skips=0, run_attempt=1, cleanup=True,
            evidence_verified=True, independent_preservation=True,
            sentinel=sentinel('readiness', workload),
        )
        require(all(type(ready.get(key)) is type(value)
                    and ready[key] == value
                    for key, value in expected_ready.items())
                and type(ready.get('run_id')) is int and ready['run_id'] > 0
                and str(ready['run_id']) != environ['GITHUB_RUN_ID']
                and ready['run_id'] != proof['run_id']
                and all(_hash(ready.get(key)) for key in (
                    'evidence_sha256', 'result_review_sha256',
                    'preservation_review_sha256')),
                'Separate TO GUI readiness unproved')
    access = record.get('access_review', {})
    require(access.get('status') == 'PASS' and access.get('audited_at_utc')
            and access.get('owner') == 'Richard-Gnitnub'
            and access.get('environment') == 'l1-private-validation'
            and access.get('branches') == ['main'] and access.get('tags') == []
            and access.get('input_repository') == native.INPUT_REPOSITORY
            and access.get('repository_public') is True,
            'TO public-input access review absent')


def selected_workload(environ):
    """Preserve L1 as the default; admit only the separate reviewed route."""
    value = environ.get('TRACKTEMPLATE_GUI_WORKLOAD', 'l1')
    require(value in ('l1', 'rea-bc', 'rea-bc-straight', *TO_WORKLOADS),
        'Unsupported GUI workload')
    return value


def _hash(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value)


def rea_scope(workload='rea-bc'):
    require(workload in ('rea-bc', 'rea-bc-straight'),
            'Unsupported B/C GUI workload')
    return REA_STRAIGHT_SCOPE if workload == 'rea-bc-straight' else REA_SCOPE


def rea_ref(workload='rea-bc'):
    rea_scope(workload)
    return REA_STRAIGHT_REF if workload == 'rea-bc-straight' else REA_REF


def rea_counts(stage, workload='rea-bc'):
    """Return exact operation counts for the independently reviewed journey."""
    require(stage in ('readiness', 'gui'), 'Unsupported GUI stage')
    rea_scope(workload)
    counts = {
        'tests': 1, 'fresh_documents': 2, 'reopens': 1,
        'source_records_created': 2, 'successful_parameter_updates': 2,
        'no_op_applies': 1, 'undo_redo_pairs': 1,
        'host_invalidation_cases': 1, 'explicit_rebuilds': 3,
        'adopted_view_rollback_cases': 1, 'actual_viewport_picks': 2,
        'visible_input_refusals': 2, 'operator_label_cases': 1,
        'profile_selections': 2, 'profile_deselections': 1,
        'selected_profile_reopens': 1, 'viewport_images': 8,
        'dialog_images': 5, 'screenshots_total': 13,
    }
    if workload == 'rea-bc-straight':
        counts.update(
            successful_parameter_updates=4, undo_redo_pairs=0,
            explicit_rebuilds=2, adopted_view_rollback_cases=0,
            visible_input_refusals=1, profile_deselections=0,
            viewport_images=5, dialog_images=2, screenshots_total=7,
            straight_boundary_edits=2, initial_straight_source_roads=3,
        )
    if stage == 'readiness':
        counts = dict.fromkeys(counts, 0)
        counts.update(tests=1, fresh_documents=1, dialog_images=1,
                      screenshots_total=1)
    return counts


def validate_rea_counts(counts, stage, workload='rea-bc'):
    expected = rea_counts(stage, workload)
    require(type(counts) is dict and set(counts) == set(expected)
            and all(type(counts[key]) is int and counts[key] == value
                    for key, value in expected.items()),
            'B/C GUI operation counts differ')


def rea_images(stage, workload='rea-bc'):
    rea_scope(workload)
    require(stage in ('readiness', 'gui'), 'Unsupported GUI image stage')
    if workload == 'rea-bc-straight':
        if stage == 'readiness':
            return {'straight-readiness-panel.png'}
        return {
            'to-straight.png', 'to-straight-fields.png',
            'upper-out-refused.png', 'straight-reopened-empty.png',
            'straight-rebuilt-picked.png', 'to-b8-returned.png',
            'xo-straight.png',
        }
    if stage == 'readiness':
        return {'readiness-panel.png'}
    require(stage == 'gui', 'Unsupported GUI image stage')
    return {
        'to-b8.png', 'to-c925-selected.png', 'to-b8-returned.png',
        'host-invalidated.png', 'host-rebuilt.png', 'reopened-empty.png',
        'rollback-retained.png', 'xo-selected.png', 'to-b8-fields.png',
        'to-c925-selected-fields.png', 'to-b8-returned-fields.png',
        'rollback-error.png', 'xo-selected-fields.png',
    }


def rea_report(stdout):
    prefix = 'TRACKTEMPLATE_REA_TRACKWORK_GUI='
    lines = [line[len(prefix):] for line in stdout.splitlines()
             if line.startswith(prefix)]
    require(len(lines) == 1 and stdout.count(prefix) == 1,
            'Expected one B/C GUI report')

    def reject_constant(value):
        raise ValueError('Nonfinite GUI report: ' + value)

    def finite_float(value):
        number = float(value)
        require(math.isfinite(number), 'Nonfinite GUI report number')
        return number

    record = json.loads(lines[0], object_pairs_hook=original._unique_object,
                        parse_constant=reject_constant,
                        parse_float=finite_float)
    require(type(record) is dict, 'GUI report must be an object')
    return record


def rea_source_files():
    """Read the complete tracked product inventory on the hosted controller."""
    names = native.command('git', 'ls-files', '--', 'tracktemplate').splitlines()
    require(names and len(names) == len(set(names)),
            'Tracked product inventory unavailable')
    hashes = {}
    for name in names:
        path = ROOT / name
        require(path.is_file() and not path.is_symlink(),
                'Linked or missing product source')
        hashes[name] = digest(path)
    return hashes


def rea_source_tree():
    """Bind all tracked modular product bytes, not merely selected fixtures."""
    return hashlib.sha256(json.dumps(
        rea_source_files(), sort_keys=True, separators=(',', ':'),
    ).encode()).hexdigest()


def validate_rea_authority(record, environ):
    """Bind owner handling, recovery and separate readiness to this source."""
    stage = selected_stage(environ)
    workload = selected_workload(environ)
    scope = rea_scope(workload)
    expected = {
        'schema': 1, 'scope_id': scope, 'workload': workload,
        'stage': stage, 'source_commit': environ['GITHUB_SHA'],
        'source_ref': rea_ref(workload), 'owner': 'Richard-Gnitnub',
        'execution_authorized': True, 'independent_review': 'PASS',
        'run_attempt': 1, 'initial_reserve_mib': RESERVE_MIB,
        'software_renderer': 'llvmpipe', 'external_inputs': 0,
        'private_inputs': 0, 'historical_repair_allowance_consumed': True,
        'automatic_retry': False,
        'freecad_limits': vars(limits(stage, workload)),
        'display_limits': vars(display_limits(stage, workload)),
    }
    require(type(record) is dict and all(
        type(record.get(key)) is type(value) and record[key] == value
        for key, value in expected.items()
    ), 'Separate B/C GUI authority absent or differs')
    require(environ.get('GITHUB_REF') == rea_ref(workload)
            and not diagnostic_enabled(environ),
            'B/C candidate or diagnostic selection differs')
    require(all(isinstance(record.get(key), str) and record[key].strip()
                for key in ('decision_id', 'dispatch_nonce'))
            and _hash(record.get('source_tree_sha256'))
            and _hash(record.get('gui_entry_sha256')),
            'B/C source or decision identity absent')
    for key, paths in (('control_files_sha256', REA_CONTROL_FILES),
                       ('input_hashes', REA_INPUTS)):
        hashes = record.get(key)
        require(type(hashes) is dict and set(hashes) == set(paths)
                and all(_hash(value) for value in hashes.values()),
                'B/C reviewed source bindings incomplete')
    handling = record.get('handling_review', {})
    expected_handling = {
        'independent_review': 'PASS', 'public_research_screenshots': True,
        'retention_days': 30, 'independent_preservation': True,
        'readiness_images': 1,
        'gui_images': 7 if workload == 'rea-bc-straight' else 13,
        'source_archive_upload': False, 'operator_documents': False,
        'exact_exports': False, 'fcstd_upload': False,
    }
    require(type(handling) is dict
            and set(handling) == set(expected_handling) | {'decision_sha256'}
            and _hash(handling.get('decision_sha256'))
            and all(type(handling.get(key)) is type(value)
                    and handling[key] == value
                    for key, value in expected_handling.items()),
            'Separate B/C screenshot handling approval absent or differs')
    recovery = record.get('gui_recovery', {})
    require(recovery.get('status') == recovery.get('independent_review')
            == 'PASS' and recovery.get('source_commit') == record['source_commit']
            and _hash(recovery.get('evidence_sha256')),
            'B/C source recovery evidence absent')
    native_review = record.get('prior_native_evidence', {})
    require(native_review.get('status') == native_review.get('independent_review')
            == 'PASS' and type(native_review.get('run_id')) is int
            and native_review['run_id'] > 0
            and str(native_review['run_id']) != environ['GITHUB_RUN_ID']
            and _hash(native_review.get('evidence_sha256'))
            and _hash(native_review.get('source_compatibility_review_sha256')),
            'B/C independent native evidence or reuse review absent')
    if stage == 'gui':
        ready = record.get('gui_readiness_review', {})
        expected_ready = {
            key: record[key] for key in (
                'scope_id', 'workload', 'source_commit', 'source_tree_sha256',
                'gui_entry_sha256', 'control_files_sha256', 'input_hashes',
                'handling_review',
            )
        }
        expected_ready.update(
            status='PASS', independent_review='PASS', stage='readiness',
            freecad_limits=vars(limits('readiness', workload)),
            display_limits=vars(display_limits('readiness', workload)),
            tests=1, skips=0, run_attempt=1, cleanup=True,
            evidence_verified=True, independent_preservation=True,
            sentinel=sentinel('readiness', workload),
        )
        require(all(type(ready.get(key)) is type(value)
                    and ready[key] == value
                    for key, value in expected_ready.items())
                and type(ready.get('run_id')) is int and ready['run_id'] > 0
                and str(ready['run_id']) != environ['GITHUB_RUN_ID']
                and all(_hash(ready.get(key)) for key in (
                    'evidence_sha256', 'result_review_sha256',
                    'preservation_review_sha256')),
                'Separate exact-source B/C GUI readiness unproved')


def require_rea_finalization_time(stage, environ, now):
    started = int(environ['L1_JOB_START_SECONDS'])
    require(0 <= now - started
            <= 45 * 60 - limits(stage, 'rea-bc').timeout_seconds - 600,
            'Insufficient B/C job time for proof and finalization')


def _rea_profile_inventory(profile):
    """Hash an owned private profile without making its contents public."""
    directories = {
        'FREECAD_USER_HOME': 'user-home', 'FREECAD_USER_DATA': 'user-data',
        'FREECAD_USER_TEMP': 'temp', 'XDG_CACHE_HOME': 'xdg-cache',
        'XDG_CONFIG_HOME': 'xdg-config', 'XDG_DATA_HOME': 'xdg-data',
        'PYTHONPYCACHEPREFIX': 'python-cache',
    }
    require(not any(path.is_symlink() for path in (profile, *profile.parents))
            and profile.is_dir(), 'Linked or missing guard profile')
    require(set(path.name for path in profile.iterdir())
            <= set(directories.values()) | {'user.cfg', 'system.cfg'}
            and all((profile / name).is_dir()
                    for name in directories.values()),
            'Unexpected guard profile layout')
    inventory = {}
    for path in (profile, *sorted(profile.rglob('*'))):
        require(not path.is_symlink() and path.stat().st_uid == os.getuid(),
                'Linked or foreign guard profile member')
        name = path.relative_to(profile).as_posix()
        if path.is_dir():
            require(name not in ('user.cfg', 'system.cfg'),
                    'Guard configuration is not a file')
            inventory[name] = {'kind': 'directory'}
        else:
            require(path.is_file(), 'Nonregular guard profile member')
            inventory[name] = {'kind': 'file', 'sha256': digest(path),
                               'bytes': path.stat().st_size}
    return directories, inventory


def _rea_guard_profile(work):
    """Validate live or retained private state against its guard receipt."""
    source = work / 'evidence/guard/profile'
    parent = work / 'retained-guard-profile'
    retained = parent / 'profile'
    receipt_path = work / 'evidence/guard-profile-exclusion.json'
    if not any(path.exists() or path.is_symlink()
               for path in (source, parent, receipt_path)):
        return None
    live = source.exists() or source.is_symlink()
    require(not live or not (parent.exists() or parent.is_symlink()
                            or receipt_path.exists()
                            or receipt_path.is_symlink()),
            'Guard profile retention target occupied')
    result_path = work / 'evidence/guard/result.json'
    require(not any(path.is_symlink()
                    for path in (result_path, *result_path.parents))
            and result_path.is_file()
            and result_path.stat().st_uid == os.getuid(),
            'Guard profile ownership receipt differs')
    private = json.loads(result_path.read_text()).get('private_profile', {})
    profile = source if live else retained
    directories, inventory = _rea_profile_inventory(profile)
    environment = {name: str(source / directory)
                   for name, directory in directories.items()}
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    require(type(private) is dict and private.get('path') == str(source)
            and private.get('environment') == environment,
            'Guard profile path or environment differs')
    files = [row for row in inventory.values() if row['kind'] == 'file']
    receipt = {
        'schema': 1, 'source': 'guard/profile',
        'retained': 'retained-guard-profile/profile',
        'reason': 'private-runtime-state-not-public-evidence',
        'guard_result_sha256': digest(result_path),
        'tree_sha256': hashlib.sha256(json.dumps(
            inventory, sort_keys=True, separators=(',', ':'),
        ).encode()).hexdigest(),
        'files': len(files), 'bytes': sum(row['bytes'] for row in files),
        'directories': len(inventory) - len(files),
    }
    if not live:
        require(parent.stat().st_uid == os.getuid()
                and set(path.name for path in parent.iterdir())
                == {'profile', 'manifest.json'},
                'Guard profile retention inventory differs')
        for path, expected in ((parent / 'manifest.json', inventory),
                               (receipt_path, receipt)):
            require(not any(item.is_symlink() for item in (path, *path.parents))
                    and path.is_file() and path.stat().st_uid == os.getuid()
                    and json.loads(path.read_text()) == expected,
                    'Retained guard profile identity changed')
    return profile, inventory, receipt


def _retain_rea_guard_profile(work):
    """Keep the owned profile outside both archives, without deleting it."""
    state = _rea_guard_profile(work)
    source = work / 'evidence/guard/profile'
    if state is None or state[0] != source:
        return
    _profile, inventory, receipt = state
    parent = work / 'retained-guard-profile'
    parent.mkdir(mode=0o700)
    write(parent / 'manifest.json', inventory)
    source.rename(parent / 'profile')
    write(work / 'evidence/guard-profile-exclusion.json', receipt)
    _rea_guard_profile(work)


def validate_rea_evidence(work, *, stage, workload='rea-bc'):
    """Exclude archives, documents and unknown media before either upload."""
    evidence = work / 'evidence'
    profile = _rea_guard_profile(work)
    roots = {
        'prepare.log', 'install.log', 'acquisition.log', 'execution.log',
        'finalizer.log', 'seal.log', 'publication.log', 'xvfb.log',
        'gui-authority.json', 'admission.json', 'gui-run-config.json',
        'gui-macro.json', 'display-start-intent.json',
        'display-ownership.json', 'display-kernel.json',
        'display-samples.jsonl', 'host.jsonl', 'display-cleanup.json',
        'assessment.json', 'process-finalization.json',
        'runtime-finalization.json', 'display-finalization.json',
        'gui-staging-cleanup.json', 'gui-document-cleanup.json',
        'publication.json', 'finalization.json',
        'clearance.json', 'deadline-clearance.json', 'emergency-cleanup.json',
        'installer-intent.json', 'installer-ownership.json',
        'installer-result.json', 'installer-output.log',
        'installer-samples.jsonl', 'installer-cleanup.json',
        'guard-profile-exclusion.json',
    }
    images = (to_images(stage, workload=workload) if workload in TO_WORKLOADS
              else rea_images(stage, workload))
    groups = {
        'gui': {'result.json', *images},
        'guard': {'control.json', 'result.json', 'ownership.json',
                  'measurements.jsonl', 'stdout', 'stderr',
                  'wrapper.stdout', 'watchdog.json'},
        'display-preflight': {'clearance.json'},
        'finalizer-clearance': {'clearance.json', 'deadline-clearance.json'},
    }
    if workload in TO_WORKLOADS:
        roots.update({
            'run-config.json', 'private-control.json', 'input-manifest.json',
            'recovery.json', 'readiness-review.json',
            *(f'deployed-{index:02d}.json' for index in range(
                1, len(native.to_profile(workload)['input_hashes']) + 1)),
        })
        groups['native'] = {'result.json'}
        if workload == 'to-crossing':
            groups['native'].update({
                'native-failure.txt', 'input-failure.txt', 'cleanup-failure.txt',
            })
            groups['gui'].update({
                'gui-failure.txt', 'input-failure.txt', 'cleanup-failure.txt',
            })
    require(not evidence.is_symlink() and evidence.is_dir(),
            'B/C evidence directory differs')
    for path in evidence.rglob('*'):
        relative = path.relative_to(evidence)
        require(not path.is_symlink(), 'Linked B/C evidence refused')
        if profile is not None and path.is_relative_to(profile[0]):
            # Receipt validation is read-only while display cleanup is pending.
            # Seal/publication relocate this verified tree before archiving.
            continue
        if path.is_dir():
            require(str(relative) in groups, 'Unexpected evidence directory')
        else:
            allowed = (len(relative.parts) == 1 and relative.name in roots
                       or len(relative.parts) == 2
                       and relative.parts[0] in groups
                       and relative.name in groups[relative.parts[0]])
            require(path.is_file() and allowed,
                    'Unexpected B/C evidence member: ' + str(relative))


def diagnostic_enabled(environ):
    """Require an explicit boolean dispatch value; default remains off."""
    value = environ.get('L1_LIFECYCLE_DIAGNOSTIC', 'false')
    require(value in ('true', 'false'), 'Invalid diagnostic dispatch value')
    return value == 'true'


def validate_product_requalification(record, environ):
    """Bind the single activation repair to separate review and ordinary runs."""
    repair = record.get('product_requalification')
    if repair is None:
        return
    require(not diagnostic_enabled(environ),
            'Historical diagnostic cannot admit repaired product')
    expected = dict(PRODUCT_REPAIR, source_commit=record.get('source_commit'),
                    independent_review='PASS')
    require(isinstance(repair, dict)
            and set(repair) == set(expected) | {'review_sha256'}
            and all(repair.get(key) == value for key, value in expected.items())
            and isinstance(repair.get('review_sha256'), str)
            and re.fullmatch(r'[0-9a-f]{64}', repair['review_sha256'])
            and record.get('gui_entry_sha256') == DIAGNOSTIC_ENTRY_SHA256,
            'Exact reviewed product requalification absent or differs')


def validate_frozen_source(record):
    """Keep BASE frozen except for the exact independently reviewed repair."""
    changed = native.command(
        'git', 'diff', '--name-status', '--no-renames', BASE, '--', *FROZEN_PATHS,
    ).splitlines()
    if record.get('product_requalification') is None:
        require(not changed, 'Frozen product or native entry differs')
        return
    name = PRODUCT_REPAIR['path']
    require(changed == ['M\t' + name],
            'Product requalification changed other frozen source')
    path = ROOT / name
    require(path.is_file() and not path.is_symlink()
            and not path.stat().st_mode & 0o111
            and digest(path) == PRODUCT_REPAIR['sha256'],
            'Exact reviewed product repair bytes differ')
    baseline = subprocess.run(
        ['git', 'show', f'{BASE}:{name}'], cwd=ROOT,
        capture_output=True, check=True, timeout=15,
    ).stdout
    require(hashlib.sha256(baseline).hexdigest()
            == PRODUCT_REPAIR['baseline_sha256'],
            'Product repair baseline identity differs')


def validate_diagnostic(record, environ):
    """Bind observation authority to the preserved failed GUI journey."""
    diagnostic = record.get('lifecycle_diagnostic')
    if not diagnostic_enabled(environ):
        require(diagnostic is None, 'Diagnostic authority/dispatch differs')
        return False
    require(selected_stage(environ) == 'gui' and isinstance(diagnostic, dict),
            'Separate lifecycle diagnostic authority absent')
    expected = {
        'scope_id': DIAGNOSTIC_SCOPE, 'execution_authorized': True,
        'preparation_review': 'PASS', 'failed_run_id': 41298217983,
        'baseline_commit': DIAGNOSTIC_BASE,
    }
    require(all(diagnostic.get(key) == value
                for key, value in expected.items())
            and diagnostic.get('execution_authorized') is True
            and diagnostic.get('automatic_retry') is False
            and diagnostic.get('product_changes') is False
            and re.fullmatch(r'[0-9a-f]{64}',
                             diagnostic.get('preparation_review_sha256', '')),
            'Lifecycle diagnostic scope or preparation differs')
    for key, names in (('baseline_controls', CONTROL_FILES),
                       ('control_files_sha256', DIAGNOSTIC_FILES)):
        hashes = diagnostic.get(key, {})
        require(set(hashes) == set(names)
                and all(re.fullmatch(r'[0-9a-f]{64}', value)
                        for value in hashes.values()),
                'Diagnostic source bindings incomplete')
    ready = record.get('gui_readiness_review', {})
    require(record.get('gui_entry_sha256') == DIAGNOSTIC_ENTRY_SHA256
            and ready.get('run_id') == 41297405795
            and ready.get('evidence_sha256') == DIAGNOSTIC_READINESS_EVIDENCE
            and ready.get('result_review_sha256') == DIAGNOSTIC_READINESS_REVIEW
            and ready.get('preservation_review_sha256')
            == DIAGNOSTIC_READINESS_PRESERVATION,
            'Preserved diagnostic readiness evidence differs')
    baseline = dict(record, source_commit=DIAGNOSTIC_BASE,
                    control_files_sha256=diagnostic['baseline_controls'])
    validate_readiness(ready, baseline, environ['GITHUB_RUN_ID'])
    return True


def validate_diagnostic_source(record):
    """Allow only the reviewed observer and its bounded control wiring."""
    diagnostic = record['lifecycle_diagnostic']
    changed = native.command(
        'git', 'diff', '--name-only', DIAGNOSTIC_BASE, '--',
    ).splitlines()
    require(set(changed) <= set((*DIAGNOSTIC_FILES,
                                *DIAGNOSTIC_CHANGED_CONTROLS)),
            'Diagnostic changed frozen source or fixture')
    for name, expected in diagnostic['baseline_controls'].items():
        baseline = subprocess.run(
            ['git', 'show', f'{DIAGNOSTIC_BASE}:{name}'], cwd=ROOT,
            capture_output=True, check=True, timeout=15,
        ).stdout
        require(hashlib.sha256(baseline).hexdigest() == expected,
                'Diagnostic baseline control identity differs')
        if name not in DIAGNOSTIC_CHANGED_CONTROLS:
            require(digest(ROOT / name) == expected,
                    'Diagnostic changed a frozen control')
    for name, expected in diagnostic['control_files_sha256'].items():
        require(digest(ROOT / name) == expected,
                'Reviewed diagnostic observer control changed')


def selected_stage(environ):
    stage = environ.get('L1_GUI_STAGE')
    require(stage in ('readiness', 'gui'), 'Unsupported GUI stage')
    return stage


def limits(stage, workload='l1'):
    require(stage in ('readiness', 'gui'), 'Unsupported GUI stage')
    require(workload in ('l1', 'rea-bc', 'rea-bc-straight', *TO_WORKLOADS),
        'Unsupported GUI workload')
    full = 900 if workload in ('rea-bc', 'rea-bc-straight') else 7200
    return guard.ValidationLimits(4096, 90 if stage == 'readiness' else full)


def display_limits(stage, workload='l1'):
    require(stage in ('readiness', 'gui'), 'Unsupported GUI stage')
    require(workload in ('l1', 'rea-bc', 'rea-bc-straight', *TO_WORKLOADS),
        'Unsupported GUI workload')
    full = 1000 if workload in ('rea-bc', 'rea-bc-straight') else 7300
    return guard.ValidationLimits(256, 190 if stage == 'readiness' else full,
                                  25, 16)


def sentinel(stage, workload='l1'):
    if workload == 'to-crossing':
        require(stage in ('readiness', 'gui'), 'Unsupported TO GUI stage')
        return ('Fixed TO crossing GUI readiness passed'
                if stage == 'readiness'
                else 'Fixed TO crossing GUI validation passed')
    if workload == 'to-single':
        require(stage in ('readiness', 'gui'), 'Unsupported TO GUI stage')
        return ('Fixed TO single-rail hosted GUI readiness passed'
                if stage == 'readiness'
                else 'Fixed TO single-rail hosted GUI validation passed')
    if workload == 'rea-bc-straight':
        return ('REA B straight hosted GUI readiness passed'
                if stage == 'readiness'
                else 'REA B straight hosted GUI validation passed')
    if workload in ('rea-bc', 'rea-bc-straight'):
        return ('REA B/C hosted GUI readiness passed' if stage == 'readiness'
                else 'REA B/C hosted GUI validation passed')
    require(workload == 'l1', 'Unsupported GUI workload')
    return READINESS_SENTINEL if stage == 'readiness' else SENTINEL


def validate_readiness(review, control, current_run):
    """Require independent actual GUI readiness before the chair journey."""
    expected = {
        'status': 'PASS', 'independent_review': 'PASS', 'scope_id': SCOPE,
        'stage': 'readiness', 'source_commit': control['source_commit'],
        'gui_entry_sha256': control['gui_entry_sha256'],
        'control_files_sha256': control['control_files_sha256'],
        'input_hashes': control['input_hashes'],
        'freecad_limits': vars(limits('readiness')),
        'display_limits': vars(display_limits('readiness')),
        'tests': 1, 'skips': 0, 'run_attempt': 1,
        'sentinel': READINESS_SENTINEL, 'cleanup': True,
        'evidence_verified': True, 'independent_preservation': True,
        'product_requalification': control.get('product_requalification'),
    }
    require(all(review.get(key) == value for key, value in expected.items()),
            'Independent GUI readiness does not match reviewed journey')
    require(type(review.get('run_id')) is int and review['run_id'] > 0
            and str(review['run_id']) != current_run
            and re.fullmatch(r'[0-9a-f]{64}',
                             review.get('evidence_sha256', '')),
            'Separate preserved GUI readiness result absent')


def validate_host(environ, memory):
    """Keep native admission and add the display ceiling to initial reserve."""
    if selected_workload(environ) in ('rea-bc', 'rea-bc-straight'):
        require(environ.get('GITHUB_REF') == rea_ref(selected_workload(environ))
                and environ.get('GITHUB_RUN_ID', '').isdigit()
                and not diagnostic_enabled(environ),
                'Reviewed B/C candidate required')
        require(not any(environ.get(name, '').lower() in ('1', 'true')
                        for name in ('RUNNER_DEBUG', 'ACTIONS_STEP_DEBUG',
                                     'ACTIONS_RUNNER_DEBUG')),
                'Debug logging refused')
        values = original.validate_admission(environ, memory)
    else:
        values = native.validate_host(environ, memory)
    require(values['MemAvailable'] >= (
        LIMITS.memory_max_mib + DISPLAY_LIMITS.memory_max_mib + RESERVE_MIB
    ) * 1024**2, 'Insufficient memory for FreeCAD, display and reserve')
    return values


def validate_authority(record, environ):
    """Require a separate explicit GUI scope; native approval is insufficient."""
    if selected_workload(environ) in ('rea-bc', 'rea-bc-straight'):
        return validate_rea_authority(record, environ)
    if selected_workload(environ) in TO_WORKLOADS:
        return validate_to_authority(record, environ)
    stage = selected_stage(environ)
    validate_product_requalification(record, environ)
    diagnostic = validate_diagnostic(record, environ)
    expected = {
        'schema': 1, 'stage': stage, 'scope_id': SCOPE, 'source_base_commit': BASE,
        'source_commit': environ['GITHUB_SHA'], 'owner': 'Richard-Gnitnub',
        'execution_authorized': True, 'independent_review': 'PASS',
        'run_attempt': 1, 'freecad_limits': vars(limits(stage)),
        'display_limits': vars(display_limits(stage)),
        'initial_reserve_mib': RESERVE_MIB, 'software_renderer': 'llvmpipe',
        'repair_allowance_remaining': 0, 'input_archive': INPUT_ARCHIVE,
        'handling_decision': HANDLING_DECISION,
    }
    require(record.get('execution_authorized') is True
            and type(record.get('schema')) is int
            and type(record.get('run_attempt')) is int
            and all(record.get(key) == value for key, value in expected.items()),
            'Separate GUI execution authority absent or differs')
    require(all(isinstance(record.get(key), str) and record[key].strip()
                for key in ('decision_id', 'dispatch_nonce', 'handling_decision')),
            'GUI decision binding absent')
    require(set(record.get('control_files_sha256', {})) == set(CONTROL_FILES)
            and all(re.fullmatch(r'[0-9a-f]{64}', value)
                    for value in record['control_files_sha256'].values()),
            'GUI control source review incomplete')
    require(set(record.get('input_hashes', {})) == set(native.payload.INPUT_IDS)
            and all(re.fullmatch(r'[0-9a-f]{64}', value)
                    for value in record['input_hashes'].values()),
            'GUI input identities incomplete')
    require(re.fullmatch(r'[0-9a-f]{64}', record.get('gui_entry_sha256', '')),
            'GUI entry identity absent')
    recovery = record.get('gui_recovery', {})
    require(recovery.get('status') == recovery.get('independent_review')
            == 'PASS' and recovery.get('source_commit') == record['source_commit']
            and re.fullmatch(r'[0-9a-f]{64}', recovery.get('evidence_sha256', '')),
            'GUI source recovery evidence absent')
    review = record.get('prior_native_evidence', {})
    require(review.get('status') == review.get('independent_review') == 'PASS'
            and type(review.get('run_id')) is int
            and review['run_id'] == 41116286780
            and str(review['run_id']) != environ['GITHUB_RUN_ID']
            and review.get('evidence_sha256') == (
                '6061358800717ce6d1b3f460ea369a3cadfc0d3602aaaf69b434098a662a8f04'),
            'Independent preceding native evidence absent')
    if stage == 'gui' and not diagnostic:
        validate_readiness(record.get('gui_readiness_review', {}), record,
                           environ['GITHUB_RUN_ID'])
    access = record.get('access_review', {})
    require(access.get('status') == 'PASS' and access.get('audited_at_utc')
            and access.get('owner') == 'Richard-Gnitnub'
            and access.get('environment') == 'l1-private-validation'
            and access.get('branches') == ['main'] and access.get('tags') == []
            and access.get('input_repository') == native.INPUT_REPOSITORY
            and access.get('repository_public') is True,
            'Owner-side public-input access review absent')


def prepare(work):
    """Check exact reviewed source before acquiring inputs or starting Xvfb."""
    require(os.getuid() != 0 and not sys.flags.optimize, 'Unsafe interpreter')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    admission = validate_host(os.environ, Path('/proc/meminfo').read_text())
    workload = selected_workload(os.environ)
    key = {'to-single': 'TO_SINGLE_GUI_CONTROL',
           'to-crossing': 'TO_CROSSING_GUI_CONTROL'}.get(workload, 'L1_GUI_CONTROL')
    control = json.loads(os.environ[key])
    validate_authority(control, os.environ)
    require(native.command('git', 'rev-parse', 'HEAD') == control['source_commit'],
            'Reviewed checkout differs')
    require(not native.command('git', 'status', '--porcelain',
                               '--untracked-files=no'), 'Dirty source checkout')
    workload = selected_workload(os.environ)
    if workload in ('rea-bc', 'rea-bc-straight'):
        require(rea_source_tree() == control['source_tree_sha256'],
                'Reviewed modular source tree changed')
        for name, expected in control['input_hashes'].items():
            require(digest(ROOT / name) == expected,
                'Reviewed B/C input changed')
    elif workload in TO_WORKLOADS:
        validate_to_native_source(control, workload=workload)
        profile = to_profile(workload)
        native_profile = native.to_profile(workload)
        changed = native.command(
            'git', 'diff', '--name-only', profile['base'], '--',
            'tracktemplate', 'TrackTemplate.FCMacro', 'AdvancedTurnout.FCMacro',
            native_profile['entry'], native_profile['fixture'],
        ).splitlines()
        allowed = ({TO_CROSSING_READER, native_profile['entry']}
                   if workload == 'to-crossing' else set())
        require(set(changed) <= allowed,
                'Frozen TO product or native preparation differs')
        if workload == 'to-crossing':
            require(digest(ROOT / TO_CROSSING_READER)
                    == TO_CROSSING_READER_SHA256,
                    'Reviewed crossing reader changed')
    else:
        validate_frozen_source(control)
    for name, expected in control['control_files_sha256'].items():
        require(digest(ROOT / name) == expected,
            'Reviewed GUI control changed')
    if diagnostic_enabled(os.environ):
        validate_diagnostic_source(control)
    entry = REA_ENTRY if workload in ('rea-bc', 'rea-bc-straight') else ENTRY
    if workload in TO_WORKLOADS:
        entry = to_profile(workload)['entry']
    require(digest(ROOT / entry) == control['gui_entry_sha256'],
            'Reviewed GUI entry changed')
    require(digest(ROOT / 'tools/freecad_validation_guard.py')
            == original.GUARD_SHA256, 'Accepted guard changed')
    write(work / 'control.json', control)
    write(work / 'evidence/gui-authority.json', control)
    write(work / 'evidence/admission.json', admission)


def acquire(work):
    """Reuse L1 acquisition; B/C uses only its exact reviewed public tree."""
    if selected_workload(os.environ) in ('rea-bc', 'rea-bc-straight'):
        control = json.loads((work / 'control.json').read_text())
        config = {
            'schema': 1, 'workload': selected_workload(os.environ),
            'inputs': [],
            'external_inputs': 0, 'input_hashes': control['input_hashes'],
            'source_tree_sha256': control['source_tree_sha256'],
            'product_files_sha256': rea_source_files(),
            'source_commit': control['source_commit'],
            'repository_root': str(ROOT),
            'private_evidence_dir': str(work / 'evidence'),
            'temporary_document_dir': str(work / 'test-data'),
        }
        write(work / 'run-config.json', config)
        write(work / 'gui-run-config.json', config)
        write(work / 'evidence/gui-run-config.json', config)
        return
    if selected_workload(os.environ) in TO_WORKLOADS:
        control = json.loads((work / 'control.json').read_text())
        config = native.acquire_to(
            'readiness', work, source_root=ROOT,
            control=control['native_control'],
            workload=selected_workload(os.environ),
        )
        directory = work / 'evidence/gui'
        directory.mkdir(mode=0o700)
        config.update(
            stage=('readiness' if selected_stage(os.environ) == 'readiness'
                   else 'native'), evidence_directory=str(directory),
        )
        write(work / 'gui-run-config.json', config)
        write(work / 'evidence/gui-run-config.json', config)
        return
    native.acquire('readiness', work)
    config = json.loads((work / 'run-config.json').read_text())
    control = json.loads((work / 'control.json').read_text())
    require({row['id']: row['sha256'] for row in config['inputs']}
            == control['input_hashes'], 'GUI input set differs from approval')
    config.update(repository_root=str(ROOT),
                  private_evidence_dir=str(work / 'evidence'))
    write(work / 'gui-run-config.json', config)
    write(work / 'evidence/gui-run-config.json', config)


def display_unit(environ):
    run_id = environ.get('GITHUB_RUN_ID', '')
    require(run_id.isdigit() and int(run_id) > 0, 'Invalid display owner run')
    return f'tracktemplate-l1-gui-display-{run_id}.service'


def display_properties(stage='gui', workload='l1'):
    """Return explicit kernel and deadline properties for the display alone."""
    return {
        'MemoryMax': str(DISPLAY_LIMITS.memory_max_mib * 1024**2),
        'MemoryHigh': str(DISPLAY_LIMITS.memory_max_mib * 1024**2),
        'MemorySwapMax': '0', 'CPUQuota': '25%',
        'CPUQuotaPeriodSec': '100ms', 'TasksMax': '16',
        'RuntimeMaxSec': str(display_limits(stage, workload).timeout_seconds), 'TimeoutStopSec': '5',
        'KillMode': 'control-group', 'Restart': 'no',
        'Type': 'exec', 'RemainAfterExit': 'yes',
    }


def _display_show(unit):
    raw = native.command('systemctl', '--user', 'show', unit,
                         '-p', 'InvocationID', '-p', 'ControlGroup',
                         '-p', 'MainPID', '-p', 'ActiveState',
                         '-p', 'RuntimeMaxUSec', '-p', 'TimeoutStopUSec',
                         '-p', 'KillMode', '-p', 'Restart')
    return dict(line.split('=', 1) for line in raw.splitlines() if '=' in line)


def _display_group(owner):
    unit = display_unit(os.environ)
    prefix = (f'/user.slice/user-{os.getuid()}.slice/'
              f'user@{os.getuid()}.service/')
    require(owner.get('unit') == unit
            and re.fullmatch(r'[0-9a-f]{32}', owner.get('invocation', ''))
            and owner.get('cgroup', '').startswith(prefix)
            and owner['cgroup'].endswith('/' + unit)
            and '..' not in Path(owner['cgroup']).parts,
            'Display ownership differs')
    return Path('/sys/fs/cgroup') / owner['cgroup'].lstrip('/')


def display_kernel_limits():
    return {'memory.max': str(256 * 1024**2),
            'memory.high': str(256 * 1024**2), 'memory.swap.max': '0',
            'cpu.max': '25000 100000', 'pids.max': '16'}


def start_display(work):
    """Start only the owned X server, with its own systemd resource bounds."""
    unit = display_unit(os.environ)
    require(not Path('/tmp/.X99-lock').exists()
            and not Path('/tmp/.X11-unix/X99').exists(),
            'Display 99 is occupied')
    loaded = native.command('systemctl', '--user', 'list-units', '--all',
                            '--plain', '--no-legend', unit)
    require(not loaded, 'Display unit already exists')
    output = work / 'display'
    output.mkdir(mode=0o700)
    authority = output / 'Xauthority'
    # The cookie is private local display authentication, never evidence.
    subprocess.run(['xauth', '-f', str(authority)],
                   input=f'add {DISPLAY} . {secrets.token_hex(16)}\n',
                   check=True, capture_output=True, text=True, timeout=15)
    authority.chmod(0o600)
    argv = ['systemd-run', '--user', '--quiet', '--unit=' + unit]
    stage = selected_stage(os.environ)
    workload = selected_workload(os.environ)
    properties = display_properties(stage, workload)
    properties.update(StandardOutput='append:' + str(work / 'evidence/xvfb.log'),
                      StandardError='append:' + str(work / 'evidence/xvfb.log'))
    argv += [f'--property={key}={value}' for key, value in properties.items()]
    argv += ['/usr/bin/Xvfb', DISPLAY, '-screen', '0', '1280x960x24',
             '-nolisten', 'tcp', '-noreset', '-auth', str(authority)]
    write(work / 'evidence/display-start-intent.json', {'unit': unit,
                                                     'argv': argv})
    subprocess.run(argv, check=True, capture_output=True, text=True, timeout=15)
    state = _display_show(unit)
    owner = {'unit': unit, 'invocation': state.get('InvocationID'),
             'cgroup': state.get('ControlGroup'), 'pid': state.get('MainPID')}
    write(work / 'evidence/display-ownership.json', owner)
    group = _display_group(owner)
    require(state.get('ActiveState') == 'active'
            and state.get('RuntimeMaxUSec') == (
                '3min 10s' if stage == 'readiness' else
                '16min 40s' if workload in ('rea-bc', 'rea-bc-straight')
                else '2h 1min 40s')
            and state.get('TimeoutStopUSec') == '5s'
            and state.get('KillMode') == 'control-group'
            and state.get('Restart') == 'no', 'Display deadline unproved')
    kernel = {name: (group / name).read_text().strip()
              for name in display_kernel_limits()}
    write(work / 'evidence/display-kernel.json', kernel)
    require(kernel == display_kernel_limits(), 'Display kernel bounds differ')
    deadline = time.monotonic() + 10
    while not Path('/tmp/.X11-unix/X99').exists():
        require(time.monotonic() < deadline, 'Display socket unavailable')
        time.sleep(0.1)
    return owner


def display_cleanup(work):
    """Independently inspect and stop only the exact recorded display unit."""
    receipt = {'cleanup': False, 'errors': []}
    path = work / 'evidence/display-ownership.json'
    try:
        if not path.exists():
            require(not (work / 'evidence/display-start-intent.json').exists(),
                    'Display launch attempted without an ownership receipt')
            receipt['cleanup'] = True
            receipt['never_started'] = True
            return receipt
        owner = json.loads(path.read_text())
        group = _display_group(owner)
        if group.exists():
            state = _display_show(owner['unit'])
            receipt['before'] = state
            require(state.get('InvocationID') == owner['invocation'],
                    'Display invocation changed; refuse stop')
            native.command('systemctl', '--user', 'stop', owner['unit'])
        deadline = time.monotonic() + 10
        while group.exists():
            sample = guard._sample(group)
            receipt['after'] = sample
            require(all(isinstance(sample.get(name), str) for name in (
                'pids.current', 'cgroup.procs', 'cgroup.events',
            )), 'Display cleanup accounting incomplete')
            if (sample['pids.current'] == '0'
                    and not sample['cgroup.procs'].strip()
                    and dict(line.split() for line in
                             sample['cgroup.events'].splitlines()).get(
                                 'populated') == '0'):
                break
            require(time.monotonic() < deadline, 'Display processes remain')
            time.sleep(0.1)
        receipt['cgroup_removed'] = not group.exists()
        require(not Path('/tmp/.X99-lock').exists()
                and not Path('/tmp/.X11-unix/X99').exists(),
                'Display socket or lock remains')
        receipt['cleanup'] = True
    except (OSError, ValueError, KeyError, TypeError,
            subprocess.SubprocessError):
        receipt['errors'].append(traceback.format_exc())
    return receipt


def assess_display(samples):
    """Require complete display samples with no limit events or swap use."""
    require(bool(samples), 'Display resource samples absent')
    previous_cpu = -1
    previous_pressure = {'some': -1, 'full': -1}
    for sample in samples:
        require(all(sample.get(name) is not None
                    for name in original.SAMPLE_FIELDS),
                'Display resource evidence incomplete')
        events = dict(line.split() for line in sample['memory.events'].splitlines())
        require({'high', 'max', 'oom', 'oom_kill'} <= events.keys()
                and not any(int(events[key]) for key in events),
                'Display memory event observed')
        require(0 <= int(sample['memory.current'])
                <= int(sample['memory.peak']) <= 256 * 1024**2
                and int(sample['memory.swap.current']) == 0
                and 0 <= int(sample['pids.current']) <= 16,
                'Display resource ceiling exceeded')
        cpu = int(dict(line.split() for line in
                       sample['cpu.stat'].splitlines())['usage_usec'])
        require(cpu >= previous_cpu, 'Display CPU evidence incomplete')
        previous_cpu = cpu
        pressure = {}
        for line in sample['memory.pressure'].splitlines():
            match = re.fullmatch(
                r'(some|full) avg10=([0-9.]+) avg60=([0-9.]+) '
                r'avg300=([0-9.]+) total=([0-9]+)', line,
            )
            require(match is not None, 'Display pressure evidence incomplete')
            name = match[1]
            averages = [float(value) for value in match.group(2, 3, 4)]
            require(name not in pressure
                    and all(math.isfinite(value) and value >= 0
                            for value in averages)
                    and int(match[5]) >= previous_pressure[name],
                    'Display pressure evidence differs')
            pressure[name] = int(match[5])
        require(set(pressure) == {'some', 'full'},
                'Display pressure evidence incomplete')
        previous_pressure = pressure


def child_environment(work):
    config = work / 'gui-run-config.json'
    authority = work / 'evidence/gui-authority.json'
    clean = native.child_environment(os.environ, config, digest(config))
    clean.update({name: os.environ[name] for name in (
        'GITHUB_SHA', 'GITHUB_RUN_ATTEMPT', 'RUNNER_ENVIRONMENT',
        'L1_GUI_STAGE',
    )})
    clean.update(TRACKTEMPLATE_L1_GUI_AUTHORITY=str(authority),
                 TRACKTEMPLATE_L1_GUI_AUTHORITY_SHA256=digest(authority),
                 DISPLAY=DISPLAY, XAUTHORITY=str(work / 'display/Xauthority'),
                 QT_QPA_PLATFORM='xcb', LIBGL_ALWAYS_SOFTWARE='1',
                 GALLIUM_DRIVER='llvmpipe')
    if selected_workload(os.environ) in ('rea-bc', 'rea-bc-straight'):
        clean['TRACKTEMPLATE_GUI_WORKLOAD'] = selected_workload(os.environ)
        clean['GITHUB_REF'] = os.environ['GITHUB_REF']
    if selected_workload(os.environ) in TO_WORKLOADS:
        for name in ('TRACKTEMPLATE_L1_RUN_CONFIG',
                     'TRACKTEMPLATE_L1_RUN_CONFIG_SHA256',
                     'TRACKTEMPLATE_L1_GUI_AUTHORITY',
                     'TRACKTEMPLATE_L1_GUI_AUTHORITY_SHA256'):
            clean.pop(name, None)
        clean.update(
            TRACKTEMPLATE_GUI_WORKLOAD=selected_workload(os.environ),
            TRACKTEMPLATE_TO_RUN_CONFIG=str(config),
            TRACKTEMPLATE_TO_RUN_CONFIG_SHA256=digest(config),
            TRACKTEMPLATE_TO_GUI_AUTHORITY=str(authority),
            TRACKTEMPLATE_TO_GUI_AUTHORITY_SHA256=digest(authority),
        )
    return clean


def write_gui_macro(work):
    """Bind the literal import-safe suite launcher before any FreeCAD start."""
    macro = work / 'gui-entry.FCMacro'
    observer = ''
    if diagnostic_enabled(os.environ):
        control = json.loads((work / 'control.json').read_text())
        require(control.get('lifecycle_diagnostic', {}).get(
            'execution_authorized') is True, 'Diagnostic macro not admitted')
        observer = (
            f'sys.path.insert(0, {str(ROOT)!r})\n'
            'from tools import l1_gui_lifecycle_observer as observer\n'
            f'observer.install({str(work / "evidence")!r})\n'
        )
    suite = ('hosted_rea_trackwork_gui_suite'
             if selected_workload(os.environ) in ('rea-bc', 'rea-bc-straight')
             else 'hosted_l1_gui_suite')
    if selected_workload(os.environ) in TO_WORKLOADS:
        suite = Path(to_profile(selected_workload(os.environ))['entry']).stem
    content = ('import sys\n'
               'import FreeCAD as App\n'
               'import FreeCADGui as Gui\n'
               f'sys.path.insert(0, {str(ROOT / "tests")!r})\n'
               f'import {suite}\n'
               + observer +
               f'{suite}.start()\n')
    with macro.open('x', encoding='utf-8') as stream:
        stream.write(content)
    write(work / 'evidence/gui-macro.json', {
        'content': content, 'sha256': digest(macro),
        'bytes': macro.stat().st_size,
    })
    return macro


def gui_argv(clean, macro):
    """Use only the direct FreeCAD entry and unchanged guard-approved options."""
    names = ('TRACKTEMPLATE_L1_RUN_CONFIG',
             'TRACKTEMPLATE_L1_RUN_CONFIG_SHA256',
             'TRACKTEMPLATE_L1_GUI_AUTHORITY',
             'TRACKTEMPLATE_L1_GUI_AUTHORITY_SHA256',
             'GITHUB_ACTIONS', 'GITHUB_RUN_ID', 'GITHUB_SHA',
             'GITHUB_RUN_ATTEMPT', 'RUNNER_ENVIRONMENT', 'L1_GUI_STAGE',
             'DISPLAY', 'XAUTHORITY', 'QT_QPA_PLATFORM',
             'LIBGL_ALWAYS_SOFTWARE', 'GALLIUM_DRIVER',
             'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS')
    if clean.get('TRACKTEMPLATE_GUI_WORKLOAD') in (
        'rea-bc', 'rea-bc-straight',
    ):
        names += ('TRACKTEMPLATE_GUI_WORKLOAD', 'GITHUB_REF')
    if clean.get('TRACKTEMPLATE_GUI_WORKLOAD') in TO_WORKLOADS:
        names = tuple(name for name in names
                      if not name.startswith('TRACKTEMPLATE_L1_'))
        names += ('TRACKTEMPLATE_GUI_WORKLOAD',
                  'TRACKTEMPLATE_TO_RUN_CONFIG',
                  'TRACKTEMPLATE_TO_RUN_CONFIG_SHA256',
                  'TRACKTEMPLATE_TO_GUI_AUTHORITY',
                  'TRACKTEMPLATE_TO_GUI_AUTHORITY_SHA256')
    argv = ['flatpak', 'run', '--command=FreeCAD']
    argv += [f'--env={name}={clean[name]}' for name in names]
    return [*argv, guard.APP_ID, str(macro)]


def qualified_runtime(stdout):
    """Reuse the accepted strict parser with the one actual GUI test frame."""
    selector = ('hosted_rea_trackwork_gui_suite.ReaGui.test_authorised_gui_stage'
                if selected_workload(os.environ) in (
                    'rea-bc', 'rea-bc-straight',
                )
                else 'hosted_l1_gui_suite.L1Gui.test_authorised_gui_stage')
    if selected_workload(os.environ) in TO_WORKLOADS:
        selector = to_profile(selected_workload(os.environ))['selector']
    with patch.object(native, 'SELECTORS', {'gui': selector}):
        native.qualified_runtime(stdout)


def record_diagnostic_assessment(work, assessment, *, assessor=None):
    """Retain the original verdict even when observation is incomplete."""
    try:
        if assessor is None:
            from tools import l1_gui_lifecycle_observer

            assessor = l1_gui_lifecycle_observer.assess
        diagnostic = assessor(work / 'evidence')
        complete = diagnostic['status'] == 'COMPLETE'
    except Exception:
        # Observation cannot prevent preservation of the original assessment.
        diagnostic = {'status': 'INCOMPLETE',
                      'errors': [traceback.format_exc()]}
        complete = False
    assessment['lifecycle_diagnostic'] = diagnostic
    if not complete:
        assessment['product_assessment_before_diagnostic'] = {
            'status': assessment['status'],
            'classification': assessment['classification'],
        }
        assessment.update(status='FAIL', classification='DIAGNOSTIC_INCOMPLETE')
    elif assessment['status'] == 'PASS':
        assessment['classification'] = 'DIAGNOSTIC_NON_REPRODUCTION'


def run(work):
    """Execute one real GUI unittest with distinct FreeCAD/display accounting."""
    stage = selected_stage(os.environ)
    validate_host(os.environ, Path('/proc/meminfo').read_text())
    workload = selected_workload(os.environ)
    if workload in ('rea-bc', 'rea-bc-straight'):
        require_rea_finalization_time(stage, os.environ, time.time())
    else:
        native.require_finalization_time(
            'readiness' if stage == 'readiness' else 'native',
            os.environ, time.time(),
        )
    require(native.command('flatpak', 'info', '--system', '--show-commit',
                           guard.APP_ID) == original.APP_COMMIT,
            'FreeCAD build differs')
    require(native.command('flatpak', 'info', '--system', '--show-runtime',
                           guard.APP_ID) == original.RUNTIME, 'Runtime differs')
    require(native.command('flatpak', 'info', '--system', '--show-commit',
                           original.RUNTIME) == original.RUNTIME_COMMIT,
            'Runtime build differs')
    display_samples = []
    host_samples = []
    started = time.monotonic()
    assessment = {'status': 'FAIL', 'classification': 'SETUP_FAILURE'}
    ownership = ExitStack()
    try:
        lease = ownership.enter_context(guard.acquire_validation_lease(
            Path(os.environ['XDG_RUNTIME_DIR']),
        ))
        preflight = work / 'evidence/display-preflight'
        preflight.mkdir(mode=0o700)
        with patch.object(original, 'OUTPUT', preflight):
            require(original._clearance(), 'Foreign FreeCAD process present')
        owner = start_display(work)
        group = _display_group(owner)

        def observe():
            sample = guard._sample(group)
            display_samples.append(sample)
            with (work / 'evidence/display-samples.jsonl').open('a') as stream:
                stream.write(json.dumps(sample) + '\n')
            host = original._memory(Path('/proc/meminfo').read_text())
            host['memory_pressure'] = Path('/proc/pressure/memory').read_text()
            host_samples.append(host)
            with (work / 'evidence/host.jsonl').open('a') as stream:
                stream.write(json.dumps(host) + '\n')

        def sleep(seconds):
            try:
                observe()
            except (OSError, ValueError):
                display_samples.append({'error': 'telemetry-incomplete'})
            time.sleep(seconds)

        observe()
        clean = child_environment(work)
        macro = write_gui_macro(work)
        argv = gui_argv(clean, macro)
        result = guard.run_guarded_flatpak(
            argv, limits=limits(stage, workload),
            evidence_dir=work / 'evidence/guard',
            lease=lease,
            context=guard.GuardContext(sleep=sleep), cwd=ROOT, env=clean,
            isolate_profile=True,
        )
        observe()
        with patch.object(original, 'OUTPUT', work / 'evidence'):
            clearance = (original._deadline_clearance(result)
                         and original._clearance())
        guard_dir = work / 'evidence/guard'
        samples = [json.loads(line) for line in
                   (guard_dir / 'measurements.jsonl').read_text().splitlines()]
        with ExitStack() as stack:
            for name, value in (
                ('LIMITS', limits(stage, workload)),
                ('GEOMETRY_SENTINEL', sentinel(stage, workload)),
                ('_qualified_runtime', qualified_runtime),
            ):
                stack.enter_context(patch.object(original, name, value))
            assessment = original.assess_result(
                result, (guard_dir / 'stdout').read_text(),
                (guard_dir / 'stderr').read_text(), samples, clearance,
                deadline_clearance=clearance,
            )
        assess_display(display_samples)
        receipt = json.loads((work / 'evidence/gui/result.json').read_text())
        if workload in ('rea-bc', 'rea-bc-straight'):
            require(rea_report((guard_dir / 'stdout').read_text()) == receipt,
                    'B/C stdout and retained report differ')
            validate_rea_receipt(receipt, work, stage=stage, workload=workload)
        elif workload in TO_WORKLOADS:
            require(to_report((guard_dir / 'stdout').read_text(),
                              workload=workload) == receipt,
                    'TO stdout and retained report differ')
            validate_to_receipt(receipt, work, stage=stage, workload=workload)
        else:
            validate_gui_receipt(receipt, work, stage=stage)
        assessment['gui_receipt'] = receipt
        assessment['scope'] = (rea_scope(workload)
                               if workload in ('rea-bc', 'rea-bc-straight')
                               else SCOPE)
        if workload in TO_WORKLOADS:
            assessment['scope'] = to_profile(workload)['scope']
        if assessment['status'] == 'PASS':
            assessment['classification'] = 'HOSTED_GUI_PASS'
    except (OSError, ValueError, KeyError, TypeError,
            subprocess.SubprocessError):
        assessment.update(status='FAIL', classification='EVIDENCE_INCOMPLETE',
                          error=traceback.format_exc())
    finally:
        cleanup = display_cleanup(work)
        ownership.close()
        write(work / 'evidence/display-cleanup.json', cleanup)
        if not cleanup['cleanup']:
            assessment.update(status='FAIL', classification='CLEANUP_FAILURE')
        assessment['elapsed_seconds'] = time.monotonic() - started
        assessment['display_resource_samples'] = len(display_samples)
        assessment['host_resource_samples'] = len(host_samples)
        if diagnostic_enabled(os.environ):
            record_diagnostic_assessment(work, assessment)
        write(work / 'evidence/assessment.json', assessment)
    return 0 if assessment['status'] == 'PASS' else 1


def validate_to_receipt(receipt, work, *, stage, workload='to-single'):
    """Require the fixed journey, source bindings and exact public images."""
    control = json.loads((work / 'control.json').read_text())
    profile = to_profile(workload)
    native_profile = native.to_profile(workload)
    expected = {
        'status': 'PASS', 'stage': stage, 'scope_id': profile['scope'],
        'test_id': profile['selector'],
        'source_commit': control['source_commit'],
        'fixture_sha256': native_profile['fixture_sha256'],
        'profile': original.EXPECTED_PROFILE, 'gui': True,
        'visual_review': 'REQUIRED', 'physical_fit': 'NOT_PROVED',
        'native_evidence_reused': control['prior_native_evidence'],
        'input_sha256': native_profile['input_hashes'],
        'input_bindings_unchanged': True, 'owned_documents_closed': True,
        'remaining_documents': 0, 'cleanup_errors': [],
        'sentinel': sentinel(stage, workload),
    }
    if workload == 'to-crossing':
        expected['failures'] = []
        expected['native_evidence_reused'] = {
            key: control['prior_native_evidence'][key] for key in (
                'run_id', 'source_commit', 'entry_sha256', 'evidence_sha256',
            )
        }
    result_fields = {'checks', 'stage_timings', 'screenshots', 'renderer'}
    if workload == 'to-crossing' and stage == 'gui':
        result_fields.add('pick_witness')
    require(type(receipt) is dict
            and set(receipt) == set(expected) | result_fields
            and all(type(receipt.get(key)) is type(value)
                    and receipt[key] == value
                    for key, value in expected.items()),
            'TO GUI receipt incomplete')
    if workload == 'to-crossing' and stage == 'gui':
        witness = receipt['pick_witness']
        require(type(witness) is dict and set(witness) == {
            'family', 'component', 'face_index',
            'native_interior', 'selection_matches',
        } and witness['family'] == 'XA'
            and witness['component'] == 'base_plinth'
            and type(witness['face_index']) is int
            and witness['face_index'] > 0
            and witness['native_interior'] is True
            and witness['selection_matches'] is True,
            'TO crossing pick witness differs')
    validate_to_counts(receipt['checks'], stage, workload=workload)
    timings = receipt['stage_timings']
    names = {'readiness_seconds', 'cleanup_seconds', 'total_seconds'}
    if stage == 'gui':
        names.update({'successful_preview_seconds', 'late_rollback_seconds',
                      'gui_seconds'})
    require(type(timings) is dict and set(timings) == names
            and all(type(value) in (int, float)
                    and 0 <= value <= limits(stage, workload).timeout_seconds
                    and math.isfinite(value)
                    for value in timings.values()),
            'TO GUI timings incomplete or outside limits')
    renderer = receipt['renderer']
    if workload == 'to-crossing':
        require(type(renderer) is dict and set(renderer) == {
            'platform', 'gui_up', 'widget_valid', 'renderer', 'vendor', 'version',
        }, 'TO crossing renderer fields differ')
    require(type(renderer) is dict and renderer.get('platform') == 'xcb'
            and renderer.get('gui_up') is True
            and renderer.get('widget_valid') is True
            and all(isinstance(renderer.get(key), str) and renderer[key]
                    for key in ('renderer', 'vendor', 'version'))
            and 'llvmpipe' in renderer['renderer'].lower(),
            'Real TO software OpenGL context unproved')
    require(all(digest(ROOT / name) == value for name, value
                in control['control_files_sha256'].items()),
            'Reviewed TO source changed during GUI execution')
    names = to_images(stage, workload=workload)
    images = receipt['screenshots']
    require(type(images) is list and len(images) == len(names),
            'TO screenshot count differs')
    observed = set()
    for row in images:
        require(type(row) is dict and set(row) == {'path', 'sha256', 'bytes'},
                'TO screenshot record differs')
        name = row['path']
        require(type(name) is str and name in names and name not in observed
                and _hash(row['sha256']) and type(row['bytes']) is int
                and row['bytes'] > 0, 'TO screenshot identity differs')
        observed.add(name)
        path = work / 'evidence/gui' / name
        require(path.is_file()
                and not any(item.is_symlink() for item in (path, *path.parents))
                and digest(path) == row['sha256']
                and path.stat().st_size == row['bytes']
                and path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'),
                'TO screenshot bytes differ')
    require(observed == names, 'TO screenshot set differs')
    validate_rea_evidence(work, stage=stage, workload=workload)


def validate_gui_receipt(receipt, work, *, stage='gui'):
    """Require suite assertions and independently hash each screenshot."""
    expected = {'status': 'PASS', 'stage': stage,
                'profile': original.EXPECTED_PROFILE,
                'input_bindings_unchanged': True, 'owned_documents_closed': True,
                'cleanup_errors': [], 'sentinel': sentinel(stage),
                'body_frame_comparisons': 30,
                'layer_visibility_selection_checks': 75,
                'successful_preview_component_placements': 690,
                'preview_image_count': 12, 'dialog_image_count': 3,
                'source_and_foreign_preserved': True, 'no_eager_chairs': True,
                'generate_operations': 3}

    if stage == 'readiness':
        for name in ('body_frame_comparisons', 'layer_visibility_selection_checks',
                     'successful_preview_component_placements',
                     'preview_image_count', 'dialog_image_count',
                     'source_and_foreign_preserved', 'no_eager_chairs'):
            expected.pop(name)
        expected.update(pre_geometry_readiness=True, source_copy_only=True,
                        generate_operations=0,
                        successful_preview_component_placements=0)
    require(all(receipt.get(key) == value for key, value in expected.items()),
            'GUI receipt incomplete')
    renderer = receipt.get('renderer', {})
    require(renderer.get('platform') == 'xcb'
            and renderer.get('gui_up') is True
            and renderer.get('widget_valid') is True
            and 'llvmpipe' in renderer.get('renderer', '').lower()
            and renderer.get('vendor') and renderer.get('version'),
            'Real software OpenGL context unproved')
    cases = receipt.get('cases', [])
    labels = ('reference-600', 'changed-900', 'returned-600')
    require((stage == 'readiness' and cases == [])
            or (stage == 'gui'
                and [row.get('case') for row in cases] == list(labels)
                and [row.get('radius_mm') for row in cases] == [600, 900, 600]),
            'GUI radius journey differs')
    expected_images = {f'{label}/radius-input.png' for label in labels}
    expected_images.update(
        f'{label}/representative-{index}/{name}.png'
        for label in labels for index in (0, 1)
        for name in ('overview', 'chair-closeup')
    )
    if stage == 'readiness':
        expected_images = {'readiness-source.png'}
    screenshots = receipt.get('screenshots', [])
    require(len(screenshots) == len(expected_images), 'GUI screenshot witnesses incomplete')
    names = set()
    for row in screenshots:
        name = row['path']
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts
                and relative.suffix == '.png' and name not in names,
                'Screenshot identity differs')
        names.add(name)
        path = work / 'evidence/gui' / name
        require(not any(item.is_symlink() for item in (path, *path.parents))
                and path.is_file()
                and digest(path) == row['sha256']
                and path.stat().st_size == row['bytes'] > 0,
                'Screenshot bytes differ')
    require(names == expected_images, 'GUI screenshot witness set differs')


def validate_rea_receipt(receipt, work, *, stage, workload='rea-bc'):
    """Require the real B/C journey, source identities and each visible witness."""
    control = json.loads((work / 'control.json').read_text())
    expected = {
        'status': 'PASS', 'stage': stage, 'scope_id': rea_scope(workload),
        'workload': workload, 'profile': original.EXPECTED_PROFILE,
        'source_commit': control['source_commit'],
        'source_tree_sha256': control['source_tree_sha256'],
        'input_hashes': control['input_hashes'],
        'gui_entry_sha256': control['gui_entry_sha256'],
        'input_bindings_unchanged': True, 'owned_documents_closed': True,
        'owned_windows_closed': True, 'cleanup_errors': [],
        'documents_remaining': 0, 'failures': 0, 'errors': 0, 'skips': 0,
        'geometry_builds': 0 if stage == 'readiness' else 8,
        'sentinel': sentinel(stage, workload),
    }
    require(all(type(receipt.get(key)) is type(value)
                and receipt[key] == value for key, value in expected.items()),
            'B/C GUI receipt incomplete')
    validate_rea_counts(receipt.get('checks'), stage, workload)
    elapsed = receipt.get('total_seconds')
    require(type(elapsed) in (int, float)
            and 0 <= elapsed <= limits(stage, workload).timeout_seconds
            and math.isfinite(elapsed),
            'B/C elapsed time missing, nonfinite or outside stage limit')
    require(rea_source_tree() == control['source_tree_sha256']
            and all(digest(ROOT / name) == value
                    for group in ('input_hashes', 'control_files_sha256')
                    for name, value in control[group].items()),
            'Reviewed source changed during B/C GUI execution')
    renderer = receipt.get('renderer', {})
    require(renderer.get('platform') == 'xcb'
            and renderer.get('gui_up') is True
            and renderer.get('widget_valid') is True
            and all(isinstance(renderer.get(key), str) and renderer[key]
                    for key in ('renderer', 'vendor', 'version'))
            and 'llvmpipe' in renderer['renderer'].lower(),
            'Real B/C software OpenGL context unproved')
    screenshots = receipt.get('screenshots')
    expected_images = rea_images(stage, workload)
    require(type(screenshots) is list
            and len(screenshots) == len(expected_images),
            'B/C screenshot count differs')
    names = set()
    for row in screenshots:
        require(type(row) is dict
                and set(row) == {'path', 'sha256', 'bytes'},
                'B/C screenshot record differs')
        name = row['path']
        require(name in expected_images and name not in names
                and _hash(row['sha256']) and type(row['bytes']) is int
                and row['bytes'] > 0, 'B/C screenshot identity differs')
        names.add(name)
        path = work / 'evidence/gui' / name
        require(path.is_file()
                and not any(item.is_symlink() for item in (path, *path.parents))
                and digest(path) == row['sha256']
                and path.stat().st_size == row['bytes']
                and path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'),
                'B/C screenshot bytes differ')
    require(names == expected_images, 'B/C screenshot set differs')
    validate_rea_evidence(work, stage=stage, workload=workload)


def cleanup_rea_documents(work):
    """After verified evidence preservation remove only owned test documents."""
    directory = work / 'test-data'
    receipt = work / 'evidence/gui/result.json'
    rows = (json.loads(receipt.read_text()).get('temporary_documents', [])
            if receipt.exists() else [])
    require(type(rows) is list and len(rows) <= 1,
            'B/C temporary document inventory differs')
    expected = set()
    removed = []
    for row in rows:
        require(type(row) is dict
                and set(row) == {'path', 'sha256', 'bytes'}
                and row['path'] == 'test-data/research.FCStd'
                and _hash(row['sha256']) and type(row['bytes']) is int
                and row['bytes'] > 0, 'B/C temporary document identity differs')
        expected.add(row['path'])
    require(len(expected) == len(rows), 'Duplicate temporary document')
    require(not directory.is_symlink(), 'Linked B/C document directory')
    if directory.exists():
        actual = {str(path.relative_to(work)) for path in directory.iterdir()}
        require(directory.is_dir() and actual == expected,
                'Unknown B/C temporary document')
    else:
        require(not rows, 'Recorded B/C temporary document missing')
    for row in rows:
        path = work / row['path']
        require(path.is_file() and path.stat().st_uid == os.getuid()
                and not any(item.is_symlink() for item in (path, *path.parents))
                and digest(path) == row['sha256']
                and path.stat().st_size == row['bytes'],
                'B/C temporary document bytes or ownership changed')
        path.unlink()
        require(not path.exists(), 'B/C temporary document remains')
        removed.append(row)
    if directory.exists():
        require(not tuple(directory.iterdir()), 'B/C temporary data remains')
        directory.rmdir()
    write(work / 'evidence/gui-document-cleanup.json', {
        'cleanup': True, 'removed': removed, 'directory_absent': True,
        'secure_erasure_claimed': False,
    })


def _installation_was_skipped(work):
    """Recognise only a preparation failure with no later side effects."""
    expected = {'L1_PREPARE': 'failure', 'L1_INSTALL': 'skipped',
                'L1_ACQUIRE': 'skipped', 'L1_RUN': 'skipped'}
    if any(os.environ.get(name) != value for name, value in expected.items()):
        return False
    evidence = work / 'evidence'
    allowed = {
        work: {'evidence', 'control.json'},
        evidence: {'prepare.log', 'gui-authority.json', 'admission.json',
                   'finalizer.log'},
    }
    for directory, names in allowed.items():
        if directory.is_symlink() or not directory.is_dir():
            return False
        for path in directory.iterdir():
            if path.name not in names or path.is_symlink():
                return False
            if path != evidence and not path.is_file():
                return False
    return True


def finalize(work, public):
    started = time.monotonic()
    if _installation_was_skipped(work):
        # Workflow outcomes and the complete work inventory prove no launch.
        # This owns no runtime process; it does not claim test success.
        write(work / 'evidence/process-finalization.json', {
            'cleanup': True, 'never_started': True, 'errors': [],
            'seconds': time.monotonic() - started,
            'workflow_outcomes': {name: os.environ[name] for name in (
                'L1_PREPARE', 'L1_INSTALL', 'L1_ACQUIRE', 'L1_RUN',
            )},
        })
        native_result = 0
    elif os.environ.get('L1_INSTALL') in ('failure', 'cancelled'):
        native_result = _failed_install_cleanup(work, public)
    else:
        native_result, process = _native_cleanup(work, public)
        if (work / 'evidence/installer-intent.json').exists():
            setup = installer.cleanup(work)
            if not setup['cleanup']:
                process['cleanup'] = False
                process['errors'].append('Installer cleanup unproved')
                native_result = 1
        write(work / 'evidence/process-finalization.json', process)
    receipt = display_cleanup(work)
    write(work / 'evidence/display-finalization.json', receipt)
    return 0 if native_result == 0 and receipt['cleanup'] else 1


def _native_cleanup(work, public):
    """Keep the native receipt before composing installation cleanup."""
    path = work / 'evidence/process-finalization.json'
    retained = work / 'evidence/runtime-finalization.json'

    def retain(destination, record):
        write(retained if destination == path else destination, record)

    with patch.object(native, 'write', retain):
        result = native.finalize('gui', work, public)
    if not retained.is_file():
        return 1, {'cleanup': False, 'errors': ['Native cleanup receipt absent']}
    return result, json.loads(retained.read_text())


def _failed_install_cleanup(work, public):
    """Prove a failed setup stopped before any input or GUI execution."""
    result = {'cleanup': False, 'errors': [], 'workflow_outcomes': {
        name: os.environ.get(name, '') for name in (
            'L1_PREPARE', 'L1_INSTALL', 'L1_ACQUIRE', 'L1_RUN',
        )
    }}
    try:
        expected = {'L1_PREPARE': 'success', 'L1_ACQUIRE': 'skipped',
                    'L1_RUN': 'skipped'}
        if not all(os.environ.get(key) == value
                   for key, value in expected.items()):
            # An inconsistent workflow cannot use the never-started path.
            # Preserve the previous runtime clearance attempt and its errors.
            _, previous = _native_cleanup(work, public)
            result['errors'].extend(previous['errors'])
            raise ValueError(
                'Installation failure has uncertain execution outcomes')
        evidence = work / 'evidence'
        allowed = {
            work: {'evidence', 'control.json', 'installer.sh'},
            evidence: {
                'prepare.log', 'gui-authority.json', 'admission.json',
                'install.log', 'finalizer.log', 'installer-intent.json',
                'installer-ownership.json', 'installer-result.json',
                'installer-output.log', 'installer-samples.jsonl',
                'installer-cleanup.json',
            },
        }
        for directory, names in allowed.items():
            require(not directory.is_symlink() and directory.is_dir(),
                    'Installation evidence directory differs')
            for path in directory.iterdir():
                require(path.name in names and not path.is_symlink()
                        and (path == evidence or path.is_file()),
                        'Unexpected state after installation failure')
        setup = installer.cleanup(work)
        require(setup['cleanup'] is True, 'Installer cleanup unproved')
        if shutil.which('flatpak') is not None:
            with patch.object(original, 'OUTPUT', evidence):
                require(original._clearance(), 'Foreign FreeCAD remains')
        result.update(cleanup=True, never_started=True,
                      installer_cleanup=setup)
    except (OSError, ValueError, KeyError, TypeError,
            subprocess.SubprocessError):
        result['errors'].append(traceback.format_exc())
    write(work / 'evidence/process-finalization.json', result)
    return 0 if result['cleanup'] else 1


def exclude_gui_copy(work):
    """Retain the one copied document outside the diagnostic archive."""
    if selected_workload(os.environ) in ('rea-bc', 'rea-bc-straight',
                                         *TO_WORKLOADS):
        _retain_rea_guard_profile(work)
        validate_rea_evidence(work, stage=selected_stage(os.environ),
                              workload=selected_workload(os.environ))
        return
    source = work / 'evidence/gui/XO-001-copy.FCStd'
    others = [path for path in (work / 'evidence').rglob('*')
              if path.is_file() and path.suffix.lower() == '.fcstd'
              and path != source]
    require(not others, 'Unexpected FreeCAD document in diagnostic evidence')
    if source.exists():
        require(not any(item.is_symlink() for item in (source, *source.parents))
                and source.stat().st_uid == os.getuid(),
                'Copied document ownership differs')
        target_dir = work / 'retained-gui-inputs'
        target_dir.mkdir(mode=0o700)
        target = target_dir / source.name
        require(not target.exists(),
            'Copied document retention target occupied')
        identity = {'member': 'gui/' + source.name, 'sha256': digest(source),
                    'bytes': source.stat().st_size,
                    'reason': 'copied-input-not-diagnostic-evidence'}
        source.rename(target)
        write(work / 'evidence/gui-copy-exclusion.json', identity)


def publish(work):
    publication = {'primary': None, 'errors': [], 'retention_days': 30,
                   'delete_not_before_verified_independent_preservation': True}
    try:
        evidence = native.verify_artifact(
            work / 'evidence.tar', work / 'readback-primary/evidence.tar',
            os.environ.get('L1_PRIMARY_UPLOAD', ''),
            os.environ.get('L1_PRIMARY_DOWNLOAD', ''),
            os.environ.get('L1_PRIMARY_ID', ''),
        )
        publication['primary'] = evidence
        display = json.loads((work / 'evidence/display-finalization.json').read_text())
        require(display['cleanup'], 'Independent display cleanup unproved')
        process = json.loads((work / 'evidence/process-finalization.json').read_text())
        require(process['cleanup'], 'Independent FreeCAD cleanup unproved')
        target = work / 'retained-gui-inputs/XO-001-copy.FCStd'
        require(not any(path.is_symlink() for path in (target, *target.parents)),
                'Linked copied input refused')
        if target.exists():
            require(target.is_file() and target.stat().st_uid == os.getuid(),
                    'Copied input ownership differs')
            target.unlink()
        require(not target.exists(), 'Copied input remains')
        cookie = work / 'display/Xauthority'
        require(not cookie.is_symlink(), 'Linked display cookie refused')
        if cookie.exists():
            require(cookie.is_file() and cookie.stat().st_uid == os.getuid(),
                    'Display cookie ownership differs')
            cookie.unlink()
        write(work / 'evidence/gui-staging-cleanup.json', {
            'copied_input_absent': not target.exists(),
            'display_cookie_absent': not cookie.exists(),
        })
        if selected_workload(os.environ) in ('rea-bc', 'rea-bc-straight'):
            cleanup_rea_documents(work)
        cleanup = (native.cleanup_to_staging(
                       work, evidence, workload=selected_workload(os.environ))
                   if selected_workload(os.environ) in TO_WORKLOADS
                   else native.cleanup_staging(work, evidence))
        require(cleanup['cleanup'], 'Input staging cleanup incomplete')
    except (OSError, ValueError, KeyError, TypeError):
        publication['errors'].append(traceback.format_exc())
    write(work / 'evidence/publication.json', publication)
    exclude_gui_copy(work)
    if selected_workload(os.environ) in ('rea-bc', 'rea-bc-straight'):
        validate_rea_evidence(work, stage=selected_stage(os.environ),
                              workload=selected_workload(os.environ))
    native.evidence_archive(work, work / 'publication.tar')
    return 0 if not publication['errors'] else 1


def complete(work, public):
    """Emit PASS only after both exact artifacts and every cleanup proof."""
    workload = selected_workload(os.environ)
    summary = {'schema': 1,
               'scope_id': (rea_scope(workload)
                            if workload in ('rea-bc', 'rea-bc-straight')
                            else SCOPE),
               'outcome': 'INCOMPLETE',
               'source_commit': os.environ['GITHUB_SHA'],
               'stage': selected_stage(os.environ),
               'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_attempt': 1}
    if workload in TO_WORKLOADS:
        summary.update(scope_id=to_profile(workload)['scope'], workload=workload)
    try:
        evidence = native.verify_artifact(
            work / 'publication.tar', work / 'readback-final/publication.tar',
            os.environ.get('L1_FINAL_UPLOAD', ''),
            os.environ.get('L1_FINAL_DOWNLOAD', ''),
            os.environ.get('L1_FINAL_ID', ''),
        )
        publication = json.loads((work / 'evidence/publication.json').read_text())
        assessment = json.loads((work / 'evidence/assessment.json').read_text())
        cleanup = json.loads((work / 'evidence/finalization.json').read_text())
        display = json.loads((work / 'evidence/display-finalization.json').read_text())
        staging = json.loads((work / 'evidence/gui-staging-cleanup.json').read_text())
        require(os.environ.get('L1_PUBLICATION') == 'success'
                and publication['primary'] and not publication['errors']
                and assessment['status'] == 'PASS' and cleanup['cleanup']
                and len(cleanup['staging_inputs_removed'])
                == (0 if workload in ('rea-bc', 'rea-bc-straight')
                    else len(native.to_profile(workload)['input_hashes'])
                    if workload in TO_WORKLOADS else 10)
                and display['cleanup'] and staging['copied_input_absent']
                and staging['display_cookie_absent'], 'GUI proof incomplete')
        if workload in ('rea-bc', 'rea-bc-straight'):
            documents = json.loads((work / 'evidence/gui-document-cleanup.json').read_text())
            require(documents['cleanup'] is True,
                    'B/C temporary document cleanup unproved')
            summary['workload'] = workload
        if workload in TO_WORKLOADS:
            require(cleanup.get('working_copies_absent') is True,
                    'TO working copy cleanup unproved')
        summary.update(outcome='PASS', tests=1, skips=0, evidence=evidence,
                       independent_preservation_required=True,
                       repair_allowance_remaining=0)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    if diagnostic_enabled(os.environ):
        summary.update(scope_id=DIAGNOSTIC_SCOPE, diagnostic_only=True)
        if summary['outcome'] == 'PASS':
            summary['outcome'] = 'NON_REPRODUCTION'
    public.mkdir(mode=0o700, exist_ok=True)
    write(public / 'summary.json', summary)
    return 0 if summary['outcome'] in ('PASS', 'NON_REPRODUCTION') else 1


def main():
    require(len(sys.argv) == 2, 'Expected one fixed operation')
    selected_stage(os.environ)
    run_id = os.environ['GITHUB_RUN_ID']
    require(run_id.isdigit(), 'Invalid run')
    base = Path(os.environ['RUNNER_TEMP']).resolve()
    work = base / f'l1-gui-{run_id}'
    public = base / f'l1-gui-publish-{run_id}'
    operation = sys.argv[1]
    if operation == 'prepare':
        prepare(work)
    elif operation == 'install':
        return installer.run(work)
    elif operation == 'acquire':
        acquire(work)
    elif operation == 'run':
        return run(work)
    elif operation == 'finalize':
        return finalize(work, public)
    elif operation == 'seal':
        exclude_gui_copy(work)
        native.seal(work)
    elif operation == 'publish':
        return publish(work)
    elif operation == 'complete':
        return complete(work, public)
    elif operation == 'finish':
        summary = json.loads((public / 'summary.json').read_text())
        expected = ('NON_REPRODUCTION' if diagnostic_enabled(os.environ)
                    else 'PASS')
        return 0 if (summary.get('outcome') == expected
                     and os.environ.get('L1_SUMMARY_UPLOAD') == 'success') else 1
    else:
        raise ValueError('Unsupported operation')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Exception, KeyboardInterrupt):
        traceback.print_exc()
        raise SystemExit(1) from None
