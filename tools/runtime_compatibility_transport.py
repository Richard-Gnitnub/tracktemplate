#!/usr/bin/env python3
"""Transport one reviewed compatibility matrix and its original evidence.

The original controller owns execution. This module binds exact event strings,
reuses the accepted installer and input transport, rechecks owned cleanup, and
verifies two Actions artifact readbacks. It never retries, resumes, dispatches
Actions, admits a runtime, or publishes working documents and exports.
"""

import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback
import urllib.request
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import compatibility_evidence_output as output  # noqa: E402
from tools import compatibility_readiness_transport as transport  # noqa: E402
from tools import hosted_compatibility_readiness as readiness  # noqa: E402
from tools import hosted_l1_private_validation as native  # noqa: E402
from tools import hosted_runtime_compatibility as matrix  # noqa: E402
from tools import runtime_compatibility_observations as observations  # noqa: E402

require = readiness.require
regular = transport.regular
digest = readiness.digest
write = matrix.write
strict_json = transport.strict_json
public_bytes = transport.public_bytes
PREFIX = 'compatibility-matrix'
OUTER_SECONDS = 8400
PRE_HEAVY_SECONDS = 90
TAIL_SECONDS = 600
JOB_NAME = 'compatibility-matrix'
MAX_CLOCK_RESPONSE = 4 * 1024**2
CAPSULES = dict(transport.CAPSULES,
               **{'execution.json': matrix.CAPSULE})
OUTCOMES = transport.OUTCOMES
STAGES = ('seed', 'prepare', 'install', 'acquire', 'run', 'seal', 'finalize',
          'archive', 'publish', 'complete')
FAILURES = (*STAGES, 'finalize-installer', 'finalize-runtime',
            'finalize-display', 'publish-primary')
INSTALLER_EVIDENCE = frozenset({
    'installer-intent.json', 'installer-ownership.json',
    'installer-result.json', 'installer-output.log', 'installer-samples.jsonl',
})
MATRIX_EVIDENCE = frozenset({
    'attempt.json', 'heavy-deadline.json', 'entry-results.jsonl',
    'matrix-entries.json', 'matrix-failure.txt', 'controller-failure.txt',
    'display-samples.jsonl', 'host-memory.jsonl', 'display-cleanup.json',
    'cleanup-failure.txt', 'lease-cleanup-failure.txt', 'matrix-assessment.json',
    'clearance.json', 'display-start-intent.json', 'display-ownership.json',
    'display-kernel.json', 'xvfb.log',
})
GUARD_EVIDENCE = frozenset({
    'control.json', 'result.json', 'ownership.json', 'measurements.jsonl',
    'stdout', 'stderr', 'wrapper.stdout', 'watchdog.json',
    'shutdown-request.json', 'clearance.json', 'deadline-clearance.json',
})
SESSION_EVIDENCE = frozenset({
    'invocation.json', 'input-before.json', 'input-after.json',
    'runtime-observation.json', 'bridge-readiness.json', 'gui-failure.txt',
    'client.stdout', 'client.stderr', 'clearance.json',
    'resource-assessment.json',
})
FINALIZER_EVIDENCE = frozenset({
    'clearance.json', 'deadline-clearance.json', 'emergency-cleanup.json',
    'finalization.json',
})
NATIVE07_RELATIVE = Path('entries/native-07')
NATIVE07_TRANSPORT_MARKER = 'COMPATIBILITY_NATIVE07_TRANSPORT_'


def scratch():
    return transport.scratch()


def paths():
    root = scratch()
    return (root, root / (PREFIX + '-control'),
            readiness.workspace(os.environ), root / 'runtime-compatibility')


def private_directory(path, *, new=False):
    if new:
        path.mkdir(mode=0o700)
    require(path.is_dir() and not any(p.is_symlink() for p in (path, *path.parents))
            and path.stat().st_uid == os.getuid()
            and path.stat().st_mode & 0o077 == 0, 'Private scratch differs')
    return path


def retain_failure(stage):
    """Preserve the exact causal exception before producing a stable marker."""
    require(stage in FAILURES, 'Unknown failure instance')
    parent = scratch() / (PREFIX + '-private')
    parent.mkdir(mode=0o700, exist_ok=True)
    private_directory(parent)
    with (parent / (stage + '.txt')).open('x', encoding='utf-8') as stream:
        stream.write(traceback.format_exc())


def _capsule_hashes():
    return dict(readiness.CAPSULE_FILES, **{'execution.json': matrix.CAPSULE_SHA256})


def clock_projection(job, server_date, clocks):
    """Convert one public job start to a conservative monotonic deadline.

    The server Date has one-second precision. Charging the complete request
    interval and two extra seconds cannot add time for network latency or
    timestamp rounding. Host UTC is only a bounded consistency check.
    """
    require(type(job) is dict and type(job.get('id')) is int and job['id'] > 0
            and type(job.get('run_id')) is int
            and job['run_id'] == int(os.environ['GITHUB_RUN_ID'])
            and job.get('head_sha') == os.environ['GITHUB_SHA']
            and job.get('name') == JOB_NAME and job.get('status') == 'in_progress',
            'Current public job identity differs')
    started = job.get('started_at')
    require(type(started) is str and re.fullmatch(
        r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', started),
        'Job start timestamp differs')
    require(type(server_date) is str and re.fullmatch(
        r'[A-Za-z]{3}, [0-9]{2} [A-Za-z]{3} [0-9]{4} '
        r'[0-9]{2}:[0-9]{2}:[0-9]{2} GMT', server_date),
        'Public server clock absent')
    job_started = datetime.strptime(started, '%Y-%m-%dT%H:%M:%SZ').replace(
        tzinfo=timezone.utc).timestamp()
    server = datetime.strptime(server_date, '%a, %d %b %Y %H:%M:%S GMT').replace(
        tzinfo=timezone.utc).timestamp()
    fields = {'seed_monotonic', 'request_monotonic', 'received_monotonic',
              'request_utc', 'received_utc'}
    require(type(clocks) is dict and set(clocks) == fields
            and all(type(value) in (int, float) and math.isfinite(value)
                    and value > 0 for value in clocks.values()),
            'Finite clock observations required')
    elapsed = clocks['received_monotonic'] - clocks['request_monotonic']
    require(0 <= elapsed <= 10
            and clocks['seed_monotonic'] <= clocks['request_monotonic']
            and clocks['received_monotonic'] - clocks['seed_monotonic'] <= 60
            and abs((clocks['received_utc'] - clocks['request_utc']) - elapsed) <= 1
            and abs(clocks['received_utc'] - server) <= 15
            and job_started <= server, 'Public and host clocks disagree')
    remaining = job_started + OUTER_SECONDS - server - elapsed - 2
    require(0 < remaining <= OUTER_SECONDS, 'Outer job budget exhausted')
    return {
        'schema_version': 1, 'run_id': job['run_id'], 'run_attempt': 1,
        'source_commit': job['head_sha'], 'job_id': job['id'],
        'job_name': JOB_NAME, 'job_started_at': started,
        'server_date': server_date, 'clocks': clocks,
        'outer_seconds': OUTER_SECONDS, 'heavy_seconds': matrix.HEAVY_SECONDS,
        'pre_heavy_seconds': PRE_HEAVY_SECONDS, 'tail_seconds': TAIL_SECONDS,
        'outer_deadline_monotonic': clocks['received_monotonic'] + remaining,
    }


def job_clock(controls, seed_started):
    """Read one fixed unauthenticated public endpoint, without refresh."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, response, code, message, headers, url):
            raise ValueError('Public clock redirect refused')

    run_id = os.environ['GITHUB_RUN_ID']
    url = ('https://api.github.com/repos/Richard-Gnitnub/tracktemplate/'
           'actions/runs/' + run_id + '/attempts/1/jobs?per_page=100')
    request = urllib.request.Request(url, headers={
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'Cache-Control': 'no-cache',
        'User-Agent': 'TrackTemplate-compatibility-clock',
    })
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                        NoRedirect())
    clocks = {'seed_monotonic': seed_started,
              'request_monotonic': time.monotonic(), 'request_utc': time.time()}
    with opener.open(request, timeout=10) as response:
        require(response.status == 200 and response.geturl() == url
                and response.headers.get('Age', '0') == '0',
                'Fresh public clock response required')
        raw = response.read(MAX_CLOCK_RESPONSE + 1)
        server_date = response.headers.get('Date')
    clocks.update(received_monotonic=time.monotonic(), received_utc=time.time())
    # The public API's unfiltered body stays private and is never an archive
    # member. Retain it for diagnosis; only the typed projection is public.
    with (controls / 'job-clock-response.json').open('xb') as stream:
        stream.write(raw)
    require(len(raw) <= MAX_CLOCK_RESPONSE, 'Public clock response too large')
    value = strict_json(raw)
    require(type(value) is dict and type(value.get('total_count')) is int
            and 0 < value['total_count'] <= 100
            and type(value.get('jobs')) is list
            and len(value['jobs']) == value['total_count']
            and all(type(job) is dict for job in value['jobs']),
            'Complete bounded job list required')
    selected = [job for job in value['jobs'] if job.get('name') == JOB_NAME]
    require(len(selected) == 1, 'Unique current matrix job required')
    return clock_projection(selected[0], server_date, clocks)


def outer_budget(controls):
    value = strict_json(regular(controls / 'outer-budget.json').read_bytes())
    require(type(value) is dict and set(value) == {
        'schema_version', 'run_id', 'run_attempt', 'source_commit', 'job_id',
        'job_name', 'job_started_at', 'server_date', 'clocks', 'outer_seconds',
        'heavy_seconds', 'pre_heavy_seconds', 'tail_seconds',
        'outer_deadline_monotonic'}, 'Exact outer budget fields required')
    reconstructed = clock_projection({
        'id': value['job_id'], 'run_id': value['run_id'],
        'head_sha': value['source_commit'], 'name': value['job_name'],
        'started_at': value['job_started_at'], 'status': 'in_progress',
    }, value['server_date'], value['clocks'])
    require(all(type(value[key]) is type(expected) and value[key] == expected
                for key, expected in reconstructed.items()),
            'Outer budget derivation changed')
    require(time.monotonic() >= value['clocks']['received_monotonic'],
            'Monotonic clock moved backwards')
    return value


def reserve_heavy(controls):
    """Refuse before geometry unless the full unchanged interval can fit."""
    budget = outer_budget(controls)
    now = time.monotonic()
    needed = matrix.HEAVY_SECONDS + PRE_HEAVY_SECONDS + TAIL_SECONDS
    remaining = budget['outer_deadline_monotonic'] - now
    record = {
        'status': 'PASS' if remaining >= needed else 'REFUSED',
        'source_commit': os.environ['GITHUB_SHA'],
        'run_id': int(os.environ['GITHUB_RUN_ID']),
        'outer_budget_sha256': digest(controls / 'outer-budget.json'),
        'observed_monotonic': now, 'remaining_seconds': remaining,
        'required_seconds': needed,
        'heavy_start_deadline': min(now + PRE_HEAVY_SECONDS,
            budget['outer_deadline_monotonic'] - matrix.HEAVY_SECONDS - TAIL_SECONDS),
    }
    write(controls / 'run-reservation.json', record)
    require(record['status'] == 'PASS', 'Full heavy interval and tail cannot fit')
    return record['heavy_start_deadline']


def seed():
    """Validate the four existing inputs before installation or acquisition."""
    seed_started = time.monotonic()
    root, controls, _, _ = paths()
    event_path = regular(Path(os.environ['GITHUB_EVENT_PATH']))
    require(event_path.stat().st_size <= 128 * 1024, 'Oversized dispatch event')
    event = strict_json(event_path.read_bytes())
    require(event.get('repository', {}).get('private') is False
            and event.get('repository', {}).get('full_name')
            == 'Richard-Gnitnub/tracktemplate', 'Public repository required')
    inputs = event.get('inputs')
    require(type(inputs) is dict and set(inputs) == {
        'workload', 'readiness_control', 'readiness_review',
        'readiness_recovery'}, 'Exact dispatch inputs required')
    require(inputs['workload'] == 'compatibility-qualification',
            'Qualification dispatch required')
    require(type(inputs['readiness_review']) is str,
            'Exact review envelope string required')
    envelope = strict_json(inputs['readiness_review'])
    require(type(envelope) is dict and set(envelope) == {'review', 'readiness'},
            'Exact review envelope fields required')
    values = {'control': inputs['readiness_control'],
              'recovery': inputs['readiness_recovery'], **envelope}
    raw = {}
    for name, value in values.items():
        require(type(value) is str and 0 < len(value.encode()) <= 32768,
                'Prerequisite string bound differs')
        require(type(strict_json(value)) is dict, 'Prerequisite object required')
        raw[name] = value.encode()
    private_directory(controls, new=True)
    for name, value in raw.items():
        with (controls / (name + '.json')).open('xb') as stream:
            stream.write(value)
    for name, relative in CAPSULES.items():
        source = regular(ROOT / relative)
        require(digest(source) == _capsule_hashes()[name],
                'Frozen public capsule changed')
        with (controls / name).open('xb') as stream:
            stream.write(source.read_bytes())
    matrix.validate_control(strict_json(raw['control']), controls, os.environ, ROOT)
    write(controls / 'outer-budget.json', job_clock(controls, seed_started))
    write(controls / 'seed.json', {
        'status': 'PASS', 'source_commit': os.environ['GITHUB_SHA'],
        'files': {name: digest(controls / name) for name in (
            'control.json', 'review.json', 'recovery.json', 'readiness.json',
            'outer-budget.json',
            *CAPSULES)},
    })
    return controls


def seeded():
    _, controls, _, _ = paths()
    private_directory(controls)
    record = strict_json(regular(controls / 'seed.json').read_bytes())
    require(type(record) is dict and set(record) == {
        'status', 'source_commit', 'files'} and record['status'] == 'PASS'
        and record['source_commit'] == os.environ['GITHUB_SHA']
        and type(record['files']) is dict and set(record['files']) == {
            'control.json', 'review.json', 'recovery.json', 'readiness.json',
            'outer-budget.json',
            *CAPSULES}, 'Seed binding differs')
    for name, expected in record['files'].items():
        require(digest(regular(controls / name)) == expected,
                'Seeded prerequisite changed')
    matrix.validate_control(strict_json(regular(
        controls / 'control.json').read_bytes()), controls, os.environ, ROOT)
    outer_budget(controls)
    return controls


def prerequisites():
    controls = seeded()
    control = strict_json((controls / 'control.json').read_bytes())
    require(matrix.pilot._command('git', 'rev-parse', 'HEAD')
            == control['source_commit']
            and not matrix.pilot._command('git', 'status', '--porcelain',
                                           '--untracked-files=no'),
            'Reviewed checkout differs')
    return controls


def prepare():
    """Prepare the existing installer namespace, without acquiring inputs."""
    controls = prerequisites()
    _, _, install_work, work = paths()
    require(not work.exists() and not work.is_symlink(),
            'Matrix scratch already exists')
    private_directory(install_work, new=True)
    private_directory(install_work / 'evidence', new=True)
    write(install_work / 'matrix-install-preparation.json', {
        'status': 'PASS', 'source_commit': os.environ['GITHUB_SHA'],
        'control_sha256': digest(controls / 'control.json'),
    })
    return install_work


def _installation_workspace():
    controls = prerequisites()
    _, _, install_work, _ = paths()
    private_directory(install_work)
    expected = {'status': 'PASS', 'source_commit': os.environ['GITHUB_SHA'],
                'control_sha256': digest(controls / 'control.json')}
    require(strict_json(regular(install_work /
        'matrix-install-preparation.json').read_bytes()) == expected,
        'Installer preparation changed')
    return install_work


def install():
    """Reuse the exact readiness installer and bridge within one 540s budget."""
    work = _installation_workspace()
    deadline = time.monotonic() + 540
    source = regular(ROOT / 'tools/hosted_l1_gui_install.py')
    original = source.read_text()
    adapted = readiness.installer_source(original)
    target = work / 'readiness_installer.py'
    with target.open('x', encoding='utf-8') as stream:
        stream.write(adapted)
    write(work / 'installer-adaptation.json', {
        'original_sha256': digest(source), 'copy_sha256': digest(target),
        'diff': ''.join(difflib.unified_diff(
            original.splitlines(True), adapted.splitlines(True),
            fromfile='original/hosted_l1_gui_install.py',
            tofile='assessment/hosted_l1_gui_install.py')),
    })
    spec = importlib.util.spec_from_file_location('readiness_installer', target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.run(work)
    if result == 0:
        readiness.acquire_bridge(work, deadline)
    return result


def acquire():
    controls = prerequisites()
    _, _, install_work, work = paths()
    _installation_workspace()
    installation = strict_json(regular(
        install_work / 'evidence/installer-result.json').read_bytes())
    require(installation.get('status') == 'PASS'
            and installation.get('cleanup') is True,
            'Installer completion and cleanup required')
    matrix.bridge.verify_bridge(install_work / 'bridge')
    bridge = strict_json(regular(install_work / 'bridge-preparation.json').read_bytes())
    require(bridge['checkout_tests']['status'] == 'PASS'
            and type(bridge['checkout_tests']['count']) is int
            and bridge['checkout_tests']['count'] == 22,
            'Existing bridge assertions unproved')
    archive = controls / 'approved-base-inputs.tar'
    native.download_asset(transport.ASSET, archive,
                          maximum_bytes=transport.ASSET['bytes'])
    transport.extract_base(archive, controls / 'base.FCStd')
    preparation = matrix.prepare_matrix(
        ROOT, controls / 'assessment-inputs.json', controls / 'base.FCStd', work)
    require(preparation == strict_json(regular(
        work / 'preparation.json').read_bytes()), 'Preparation receipt differs')
    write(controls / 'acquisition.json', {
        'status': 'PASS', 'archive': transport.ASSET,
        'member': transport.BASE_MEMBER, 'other_members_extracted': False,
        'base': {'bytes': 636344, 'sha256': readiness.BASE_SHA256},
        'preparation': matrix.identity(work / 'preparation.json'),
    })


def prepared_manifest(*, before_execution=False):
    controls = seeded()
    _, _, _, work = paths()
    private_directory(work)
    acquisition = strict_json(regular(controls / 'acquisition.json').read_bytes())
    require(set(acquisition) == {'status', 'archive', 'member',
        'other_members_extracted', 'base', 'preparation'}
        and acquisition['status'] == 'PASS'
        and acquisition['archive'] == transport.ASSET
        and acquisition['member'] == transport.BASE_MEMBER
        and acquisition['other_members_extracted'] is False
        and acquisition['base'] == {'bytes': 636344,
                                     'sha256': readiness.BASE_SHA256}
        and matrix.identity(work / 'preparation.json')
        == acquisition['preparation'], 'Acquired preparation binding differs')
    expected = strict_json(regular(work / 'preparation.json').read_bytes())
    if before_execution:
        return matrix.verify_preparation(work, expected), expected
    require(matrix.identity(work / 'assessment-manifest.json')
            == expected['assessment_manifest'], 'Assessment manifest changed')
    manifest = strict_json(regular(work / 'assessment-manifest.json').read_bytes())
    matrix.verify_source_members(work / 'assessment', manifest)
    return manifest, expected


def run():
    controls = prerequisites()
    _, _, install_work, work = paths()
    _, expected = prepared_manifest(before_execution=True)
    latest_start = reserve_heavy(controls)
    return matrix.run_matrix(work, expected, controls / 'control.json',
                             controls, install_work / 'bridge',
                             heavy_start_deadline=latest_start)['status']


def _is_native07(controls):
    control = strict_json(regular(controls / 'control.json').read_bytes())
    return control['stage'] == matrix.NATIVE07_STAGE


def _transport_marker():
    controls = paths()[1]
    if (controls / 'seed.json').exists() and _is_native07(controls):
        return NATIVE07_TRANSPORT_MARKER
    return 'COMPATIBILITY_MATRIX_TRANSPORT_'


def _native07_scope_isolated(work):
    entries = work / NATIVE07_RELATIVE.parent
    if not entries.exists() and not entries.is_symlink():
        return True
    private_directory(entries)
    return all(path.name == NATIVE07_RELATIVE.name
               and path.is_dir() and not path.is_symlink()
               for path in entries.iterdir())


def _verify_native07(work, manifest):
    """Recheck the sole original native result without a typed payload."""
    require(_native07_scope_isolated(work), 'Other execution state present')
    capsule = matrix.load_execution_capsule(ROOT / matrix.CAPSULE, ROOT)
    entry, = matrix.selected_entries(capsule, matrix.NATIVE07_STAGE)
    directory = work / NATIVE07_RELATIVE
    private_directory(directory)
    matrix._verify_native07_invocation(directory)
    source, = [row['assessment'] for row in manifest['source_files']
               if row['path'] == entry['path']]
    rows = strict_json(public_bytes(work / 'evidence/matrix-entries.json'))
    journal = public_bytes(work / 'evidence/entry-results.jsonl').splitlines()
    assessment = strict_json(public_bytes(
        work / 'evidence/matrix-assessment.json'))
    require(type(rows) is list and len(rows) == len(journal) == 1
            and rows[0] == strict_json(journal[0])
            and rows[0]['id'] == entry['id'] and rows[0]['status'] == 'PASS'
            and type(rows[0]['sessions']) is int and rows[0]['sessions'] == 1
            and rows[0]['assessment_entry'] == source
            and rows[0]['originals_directory'] == str(directory)
            and assessment['stage'] == matrix.NATIVE07_STAGE
            and assessment['status'] == 'PASS'
            and type(assessment['completed_entries']) is int
            and assessment['completed_entries'] == 1
            and assessment['display_cleanup'] is True
            and assessment['public_payload_status'] == 'NOT_SEALED'
            and assessment['runtime_admission'] is False
            and assessment['zy_execution'] is False,
            'Native 07 original result differs')
    invocation = strict_json(public_bytes(directory / 'invocation.json'))
    tree = work / 'assessment'
    require(invocation['id'] == entry['id']
            and invocation['kind'] == 'native'
            and invocation['arguments'] == entry['arguments']
            and invocation['entry_path'] == str(tree / entry['path'])
            and invocation['entry_sha256'] == source['sha256']
            and invocation['assessment'] == str(tree)
            and invocation['session_directory'] == str(directory),
            'Native 07 original invocation differs')
    for name in ('input-before.json', 'input-after.json'):
        require(strict_json(public_bytes(directory / name))
                == observations.BASE_IDENTITY,
                'Native 07 approved base identity differs')
    guard = directory / 'guard'
    result = strict_json(public_bytes(guard / 'result.json'))
    require(type(result['process_exit']) is int,
            'Native 07 process exit differs')
    for name in ('stdout', 'wrapper.stdout'):
        stdout = public_bytes(guard / name).decode('utf-8')
        witnesses = [strict_json(line[len(matrix.ENTRY_MARKER):])
                     for line in stdout.splitlines()
                     if line.startswith(matrix.ENTRY_MARKER)]
        require(witnesses == [{
            'id': entry['id'], 'sha256': source['sha256'], 'run_name': '__main__',
        }], 'Native 07 actual main invocation differs')
        matrix.validate_entry(entry, result, stdout)
    stderr = public_bytes(guard / 'stderr').decode('utf-8').splitlines()
    require(matrix.NATIVE07_REENTRY_REFUSAL not in stderr
            and not any(line.startswith(
                'TRACKTEMPLATE_NATIVE07_B15_LOAD_EXCEPTION=') for line in stderr),
            'Native 07 contains an original failure')
    require(strict_json(public_bytes(directory / 'clearance.json'))
            == {'complete': True}, 'Native 07 session clearance differs')


def seal():
    controls = prerequisites()
    _, _, _, work = paths()
    manifest, _ = prepared_manifest()
    if _is_native07(controls):
        _verify_native07(work, manifest)
        return 'PASS'
    receipt = observations.extract_matrix_payload(
        ROOT, work, manifest, work / 'public-matrix',
        runtime_observation=work / 'entries/straight-generation/runtime-observation.json')
    write(work / 'matrix-payload-inventory.json', receipt)
    return receipt['status']


def session_paths():
    """Derive exact instances from the pinned execution capsule only."""
    capsule = matrix.load_execution_capsule(ROOT / matrix.CAPSULE, ROOT)
    names = []
    for entry in matrix.entries(capsule):
        parent = Path('entries') / entry['id']
        if entry['kind'] == 'series':
            names.extend(parent / (entry['id'] + '-route-' + str(index))
                         for index in range(1, entry['sessions'] + 1))
        else:
            names.append(parent)
    require(len(names) == len(set(names)) == 84, 'Fixed session count differs')
    return tuple(names)


def _runtime_cleanup(work, destination, outcomes):
    if outcomes['L1_RUN'] == 'skipped':
        require(not (work / 'entries').exists()
                and not (work / 'evidence/attempt.json').exists(),
                'Skipped runtime has execution state')
        return {'cleanup': True, 'never_started': True, 'sessions': {}}
    if work.exists():
        private_directory(work)
    sessions = {}
    for relative in session_paths():
        guard = work / relative / 'guard'
        if not guard.exists():
            continue
        require(guard.is_dir()
                and not any(p.is_symlink() for p in (guard, *guard.parents))
                and guard.stat().st_uid == os.getuid(),
                'Owned guard directory differs')
        target = destination / relative
        target.mkdir(mode=0o700, parents=True)
        (target / 'evidence').mkdir(mode=0o700)
        result = guard / 'result.json'
        owner = guard / 'ownership.json'
        record = {'cleanup': False}
        try:
            if result.exists():
                value = strict_json(regular(result).read_bytes())
                with patch.object(matrix.pilot, 'OUTPUT', target / 'evidence'):
                    deadline = matrix.pilot._deadline_clearance(value)
                    clearance = matrix.pilot._clearance()
                record['cleanup'] = (deadline and clearance
                                     and value.get('cleanup_proved') is True)
            elif owner.exists():
                emergency = native.emergency_cleanup(
                    target, strict_json(regular(owner).read_bytes()))
                write(target / 'evidence/emergency-cleanup.json', emergency)
                record['cleanup'] = emergency['proved'] is True
            else:
                with patch.object(matrix.pilot, 'OUTPUT', target / 'evidence'):
                    record['cleanup'] = matrix.pilot._clearance()
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            record['original_exception'] = traceback.format_exc()
        write(target / 'evidence/finalization.json', record)
        sessions[relative.as_posix()] = record['cleanup']
    return {'cleanup': all(sessions.values()), 'sessions': sessions}


def finalize():
    """Attempt every owned cleanup boundary even after an earlier failure."""
    root, _, install_work, work = paths()
    outcomes = {key: os.environ.get(key, '') for key in OUTCOMES}
    require(all(value in ('success', 'failure', 'cancelled', 'skipped')
                for value in outcomes.values()), 'Workflow outcomes absent')
    destination = private_directory(root / (PREFIX + '-finalizer'), new=True)
    summary = {'cleanup': False, 'workflow_outcomes': outcomes, 'errors': []}
    for name, action in (
        ('installer', lambda: transport.installer_cleanup(install_work)),
        ('runtime', lambda: _runtime_cleanup(work, destination, outcomes)),
        ('display', lambda: readiness.gui.display_cleanup(work)),
    ):
        try:
            record = action()
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            retain_failure('finalize-' + name)
            record = {'cleanup': False, 'error': name + '-cleanup-unproved'}
        summary[name] = record.get('cleanup') is True
        if not summary[name]:
            summary['errors'].append(name + '-cleanup-unproved')
        write(destination / (name + '.json'), record)
    summary['cleanup'] = not summary['errors']
    write(root / (PREFIX + '-finalization.json'), summary)
    return summary


def _add_existing(contents, root, names, prefix):
    for name in sorted(names):
        path = root / name
        if path.exists() or path.is_symlink():
            contents[prefix + name] = public_bytes(path)


def _original_failures(root):
    return transport._inventory(root / (PREFIX + '-private'),
                                {stage + '.txt' for stage in FAILURES})


def _payload(work):
    """Re-extract originals into a second fresh seal, then compare every byte."""
    manifest, _ = prepared_manifest()
    expected = strict_json(regular(work / 'matrix-payload-inventory.json').read_bytes())
    repeated = observations.extract_matrix_payload(
        ROOT, work, manifest, work / 'transport-matrix',
        runtime_observation=work / 'entries/straight-generation/runtime-observation.json')
    require(repeated == expected, 'Repeated matrix seal differs')
    payload = work / 'public-matrix'
    private_directory(payload)
    actual = set()
    for path in payload.rglob('*'):
        require(not path.is_symlink(), 'Linked public payload')
        if path.is_file():
            actual.add(path.relative_to(payload).as_posix())
        else:
            require(path.is_dir(), 'Special public payload node')
    require(actual == set(expected['members']), 'Public payload inventory differs')
    contents = {}
    for name, identity in expected['members'].items():
        path = regular(payload / name)
        require(matrix.identity(path) == identity, 'Sealed payload changed')
        contents['payload/' + name] = path.read_bytes()
    return contents, expected


def _native07_missing(contents, outcomes):
    """Require the existing operational records for the reached stages."""
    required = {'transport/finalization.json', 'logs/seed.log',
                'logs/finalize.log'}
    required.update('prerequisites/' + name + '.json' for name in (
        'control', 'review', 'recovery', 'readiness', 'seed', 'outer-budget'))
    required.update('finalizer/' + name + '.json' for name in (
        'installer', 'runtime', 'display'))
    for key, stage in zip(OUTCOMES, ('prepare', 'install', 'acquire', 'run')):
        if outcomes[key] != 'skipped':
            required.add('logs/' + stage + '.log')
    if outcomes['L1_PREPARE'] == 'success':
        required.add('installation/matrix-install-preparation.json')
    if outcomes['L1_INSTALL'] == 'success' or (
            'installation/installer-intent.json' in contents):
        required.update('installation/' + name for name in (
            'installer-intent.json', 'installer-ownership.json',
            'installer-result.json', 'installer-output.log', 'derivation.json'))
    if outcomes['L1_ACQUIRE'] == 'success':
        required.add('prerequisites/acquisition.json')
        required.update('operational/' + name for name in (
            'preparation.json', 'assessment-manifest.json',
            'original-assessment-manifest.json'))
    if (outcomes['L1_PREPARE'] == 'success'
            and outcomes['L1_RUN'] != 'skipped'):
        required.update(('logs/seal.log',
                         'prerequisites/run-reservation.json'))
    session = 'operational/' + NATIVE07_RELATIVE.as_posix() + '/'
    if (outcomes['L1_RUN'] == 'success'
            or any(name.startswith(session) for name in contents)):
        required.update(session + name for name in (
            'invocation.json', 'input-before.json', 'input-after.json',
            'guard/control.json', 'guard/result.json', 'guard/ownership.json',
            'guard/measurements.jsonl', 'guard/stdout', 'guard/stderr',
            'guard/wrapper.stdout'))
        finalizer = 'finalizer/' + NATIVE07_RELATIVE.as_posix() + '/'
        required.add(finalizer + 'finalization.json')
    if outcomes['L1_RUN'] == 'success':
        required.update(session + name for name in (
            'clearance.json', 'resource-assessment.json',
            'guard/clearance.json', 'guard/deadline-clearance.json'))
        required.update(finalizer + name for name in (
            'clearance.json', 'deadline-clearance.json'))
        required.update('operational/' + name for name in (
            'attempt.json', 'heavy-deadline.json', 'entry-results.jsonl',
            'matrix-entries.json', 'matrix-assessment.json', 'clearance.json',
            'display-start-intent.json', 'display-ownership.json',
            'display-kernel.json', 'display-samples.jsonl', 'host-memory.jsonl',
            'display-cleanup.json', 'xvfb.log'))
    return sorted(required - contents.keys())


def archive():
    root, controls, install_work, work = paths()
    finalization = root / (PREFIX + '-finalization.json')
    summary = strict_json(regular(finalization).read_bytes())
    contents = {'transport/finalization.json': public_bytes(finalization)}
    admitted = (controls / 'seed.json').exists()
    native07 = admitted and _is_native07(seeded())
    isolated = not native07 or _native07_scope_isolated(work)
    if admitted:
        _add_existing(contents, controls, (
            'control.json', 'review.json', 'recovery.json', 'readiness.json',
            'seed.json', 'acquisition.json', 'outer-budget.json',
            'run-reservation.json'), 'prerequisites/')
        _add_existing(contents, install_work, ('matrix-install-preparation.json',),
                      'installation/')
        for name, raw in transport._inventory(
                install_work / 'evidence', INSTALLER_EVIDENCE).items():
            contents['installation/' + name] = raw
        adaptation = install_work / 'installer-adaptation.json'
        if adaptation.exists():
            original = regular(ROOT / 'tools/hosted_l1_gui_install.py')
            adapted = regular(install_work / 'readiness_installer.py')
            require(adapted.read_text() == readiness.installer_source(
                original.read_text()), 'Installer derivation changed')
            contents['installation/derivation.json'] = json.dumps({
                'original_sha256': digest(original),
                'adapted_sha256': digest(adapted),
                'derivation_receipt_sha256': digest(regular(adaptation)),
                'adaptation': 'source-bound-readiness-installer-v1',
            }, sort_keys=True).encode() + b'\n'
        _add_existing(contents, work, (
            'preparation.json', 'assessment-manifest.json',
            'original-assessment-manifest.json', 'matrix-payload-inventory.json'),
            'operational/')
        for name, raw in transport._inventory(
                work / 'evidence', MATRIX_EVIDENCE).items():
            contents['operational/' + name] = raw
        paths_to_preserve = (NATIVE07_RELATIVE,) if native07 else session_paths()
        for relative in paths_to_preserve:
            directory = work / relative
            prefix = 'operational/' + relative.as_posix() + '/'
            _add_existing(contents, directory, SESSION_EVIDENCE, prefix)
            if relative.name == output.PHASE5_GROUP:
                stderr = contents.get(prefix + 'client.stderr', b'')
                if any(line.lstrip().startswith(b'{') and b'"rpc_fault"' in line
                       for line in stderr.splitlines()):
                    # The sealed original is verified again below by _payload.
                    failure = (work / 'public-matrix' / 'gui'
                               / output.PHASE5_GROUP / 'failure.txt')
                    require(
                        failure.exists() and observations._phase5_rpc_traceback(
                            stderr) == public_bytes(failure),
                        'Phase 5 RPC original lacks a matching sealed failure',
                    )
            for name, raw in transport._inventory(
                    directory / 'guard', GUARD_EVIDENCE,
                    excluded=('profile',)).items():
                contents[prefix + 'guard/' + name] = raw
            finalizer = root / (PREFIX + '-finalizer') / relative / 'evidence'
            for name, raw in transport._inventory(
                    finalizer, FINALIZER_EVIDENCE).items():
                contents['finalizer/' + relative.as_posix() + '/' + name] = raw
        if not native07:
            for group in matrix.SERIES:
                _add_existing(contents, work / 'entries' / group,
                    ('series.stdout', 'series.stderr', 'sessions.json'),
                    'operational/entries/' + group + '/')
        _add_existing(contents, root / (PREFIX + '-finalizer'),
                      ('installer.json', 'runtime.json', 'display.json'), 'finalizer/')
        logs = transport._inventory(root / (PREFIX + '-logs'),
                                    {name + '.log' for name in STAGES})
        for name in STAGES[:7]:
            if name + '.log' in logs:
                contents['logs/' + name + '.log'] = logs[name + '.log']
        for name, raw in _original_failures(root).items():
            contents['original-diagnostics/' + name] = raw
    sealed = not native07 and (work / 'public-matrix').exists()
    payload_status = 'FAIL'
    if sealed:
        require(admitted, 'Unadmitted matrix payload')
        payload, inventory = _payload(work)
        contents.update(payload)
        payload_status = inventory['status']
    status = ('PASS' if sealed and payload_status == 'PASS'
              and summary['cleanup'] is True
              and all(summary['workflow_outcomes'][key] == 'success'
                      for key in OUTCOMES) else 'FAIL')
    missing = []
    if native07:
        outcomes = summary['workflow_outcomes']
        missing = _native07_missing(contents, outcomes)
        if (not missing and isolated and summary['cleanup'] is True
                and all(outcomes[key] == 'success' for key in OUTCOMES)
                and summary['runtime'] is True
                and strict_json(contents['finalizer/runtime.json']) == {
                    'cleanup': True,
                    'sessions': {NATIVE07_RELATIVE.as_posix(): True}}
                and contents['logs/seal.log']
                == (NATIVE07_TRANSPORT_MARKER + 'PASS\n').encode()
                and not (work / 'public-matrix').exists()
                and not (work / 'public-matrix').is_symlink()):
            try:
                manifest_bytes = contents['operational/assessment-manifest.json']
                _verify_native07(work, strict_json(manifest_bytes))
            except (OSError, ValueError, KeyError, TypeError):
                retain_failure('archive')
                contents['original-diagnostics/archive.txt'] = public_bytes(
                    root / (PREFIX + '-private') / 'archive.txt')
            else:
                status = 'PASS'
    manifest = {
        'schema': 1, 'status': status, 'source_commit': os.environ['GITHUB_SHA'],
        'run_id': int(os.environ['GITHUB_RUN_ID']), 'retention_days': 30,
        'independent_preservation_required': True,
        'original_diagnostic_preservation_complete': admitted,
        'runtime_admission': False, 'zy_execution': False,
        'payload_sealed': sealed,
        'files': {name: {'bytes': len(raw),
                         'sha256': hashlib.sha256(raw).hexdigest()}
                  for name, raw in contents.items()},
    }
    if native07:
        manifest.update(
            stage=matrix.NATIVE07_STAGE, scope_isolated=isolated,
            matrix_execution=False, missing_mandatory_evidence=missing,
            original_diagnostic_preservation_complete=not missing and isolated,
        )
    contents['transport/manifest.json'] = json.dumps(
        manifest, indent=2, sort_keys=True).encode() + b'\n'
    identity = transport._tar(root / (PREFIX + '-primary.tar'), contents)
    write(root / (PREFIX + '-archive.json'),
          {'status': status, 'archive': identity, 'manifest': manifest})
    return status


def _readback(root, kind):
    require(kind in ('primary', 'final'), 'Unknown artifact instance')
    source = regular(root / (PREFIX + '-' + kind + '.tar'))
    readback = regular(root / (PREFIX + '-' + kind + '-readback') / source.name)
    prefix = 'L1_PRIMARY' if kind == 'primary' else 'L1_FINAL'
    return native.verify_artifact(source, readback,
                                  os.environ.get(prefix + '_UPLOAD', ''),
                                  os.environ.get(prefix + '_DOWNLOAD', ''),
                                  os.environ.get(prefix + '_ID', ''))


def publish():
    root = scratch()
    publication = {'status': 'FAIL', 'primary': None,
                   'independent_preservation_required': True}
    try:
        publication['primary'] = _readback(root, 'primary')
        publication['status'] = 'PASS'
    except (OSError, ValueError, KeyError, TypeError):
        retain_failure('publish-primary')
        publication['error'] = 'primary-readback-unproved'
    contents = {}
    finalization = root / (PREFIX + '-finalization.json')
    if finalization.exists():
        contents['transport/finalization.json'] = public_bytes(finalization)
    else:
        publication['status'] = 'FAIL'
        publication['finalization_missing'] = True
    write(root / (PREFIX + '-publication.json'), publication)
    contents['transport/publication.json'] = public_bytes(
        root / (PREFIX + '-publication.json'))
    record = root / (PREFIX + '-archive.json')
    if record.exists():
        contents['transport/archive.json'] = public_bytes(record)
    if (root / (PREFIX + '-control/seed.json')).exists():
        seeded()
        _add_existing(contents, root / (PREFIX + '-logs'),
                      ('archive.log',), 'logs/')
        for name, raw in _original_failures(root).items():
            contents['original-diagnostics/' + name] = raw
    transport._tar(root / (PREFIX + '-final.tar'), contents)
    return publication


def complete():
    root = scratch()
    final = _readback(root, 'final')
    publication = strict_json(regular(
        root / (PREFIX + '-publication.json')).read_bytes())
    archive_record = strict_json(regular(
        root / (PREFIX + '-archive.json')).read_bytes())
    status = ('PASS' if publication['status'] == archive_record['status'] == 'PASS'
              else 'FAIL')
    write(root / (PREFIX + '-completion.json'), {
        'status': status, 'final_readback': final,
        'primary_readback': publication['primary'],
        'independent_preservation_required': True,
        'runtime_admission': False, 'zy_execution': False,
    })
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=STAGES)
    arguments = parser.parse_args(argv)
    try:
        result = globals()[arguments.stage]()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        retain_failure(arguments.stage)
        print(_transport_marker() + 'FAIL=' + arguments.stage)
        return 1
    if arguments.stage in ('run', 'seal', 'complete'):
        print(_transport_marker() + str(result))
        return 0 if result == 'PASS' else 1
    if arguments.stage == 'install':
        return result
    if arguments.stage == 'finalize':
        return 0 if result['cleanup'] else 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
