#!/usr/bin/env python3
"""Transport only reviewed compatibility readiness evidence on a hosted run.

Actions perform upload and download. This coordinator admits exact controls,
selects one approved base member, verifies owned cleanup and seals finite
operational instances. Originals and rejected diagnostics stay in scratch.
"""

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import hosted_compatibility_readiness as readiness  # noqa: E402
from tools import hosted_l1_private_validation as native  # noqa: E402

require = readiness.require
digest = readiness.digest
write = readiness.write
ASSET = {
    'asset_id': 742276777, 'bytes': 2129920,
    'sha256': 'b60f4b90d5d28d0a3098ecf327c133067f945f3f62d49953da52781f43fc4a98',
}
BASE_MEMBER = 'inputs/to_base_fixture'
CAPSULES = {
    'assessment-inputs.json': 'tests/fixtures/runtime-assessment-inputs.json',
    'output-scope.json': 'tests/fixtures/compatibility-evidence-scope.json',
}
OUTCOMES = ('L1_PREPARE', 'L1_INSTALL', 'L1_ACQUIRE', 'L1_RUN')
LOGS = ('seed', 'prepare', 'install', 'acquire', 'run', 'seal', 'finalize',
        'archive', 'publish', 'complete')
FAILURES = ('seed', 'acquire', 'finalize', 'archive', 'publish', 'complete',
            'finalize-installer', 'finalize-runtime', 'finalize-display',
            'archive-payload', 'publish-primary')
EVIDENCE = frozenset({
    'deployment.json', 'macro.json', 'readiness-assessment.json',
    'clearance.json', 'deadline-clearance.json', 'host.jsonl',
    'installer-intent.json', 'installer-ownership.json',
    'installer-result.json', 'installer-output.log', 'installer-samples.jsonl',
    'display-start-intent.json', 'display-ownership.json',
    'display-kernel.json', 'display-samples.jsonl', 'display-cleanup.json',
    'xvfb.log', 'display-preflight/clearance.json',
    'guard/control.json', 'guard/result.json', 'guard/ownership.json',
    'guard/measurements.jsonl', 'guard/stdout', 'guard/stderr',
    'guard/wrapper.stdout', 'guard/watchdog.json', 'guard/shutdown-request.json',
    'process-finalization.json', 'emergency-cleanup.json',
    'finalizer-clearance/clearance.json',
    'finalizer-clearance/deadline-clearance.json',
    'transport-installer-finalization.json',
    'transport-display-finalization.json', 'transport-finalization.json',
})
WORK_RECORDS = ('control.json', 'preparation.json', 'base-binding.json',
                'assessment-manifest.json',
                'readiness-payload-inventory.json')
MAX_FILE = 8 * 1024**2
MAX_ARCHIVE = 64 * 1024**2
DIAGNOSTIC_PREFIX = 'compatibility-acquisition-diagnostic'
REFUSAL_REASONS = {
    'Private path in operational evidence': 'private-path',
    'Credential-like operational evidence': 'credential-pattern',
    'Unlisted operational evidence': 'unlisted-member',
    'Unexpected evidence directory': 'unlisted-member',
    'Operational file too large': 'oversize',
    'Operational archive too large': 'oversize',
    'Archive bound exceeded': 'oversize',
}
# Keep refusal traceback source lines free of the patterns they test. The
# scanner still rejects the same bytes; original tracebacks are never edited.
PRIVATE_PATH = re.compile(
    r'/home/(?!runner(?:/|\b))[A-Za-z0-9_.-]+|/Users/|/root/')
CREDENTIAL = re.compile(
    r'(?i)authorization\s*[:=]|bearer\s+[A-Za-z0-9]|'
    r'gh[pousr]_[A-Za-z0-9]{10}|github_pat_|BEGIN [A-Z ]*PRIVATE KEY|'
    r'X-Amz-(?:Credential|Signature)|[?&](?:sig|token|signature)=')


def strict_json(raw):
    """Reject duplicate keys and non-JSON values before any side effect."""
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'Duplicate JSON field')
            value[key] = item
        return value

    def constant(_value):
        raise ValueError('Nonfinite JSON value')

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def scratch():
    """Use one non-root, first-attempt hosted namespace only."""
    require(os.getuid() != 0 and not sys.flags.optimize,
            'Non-root assertions required')
    readiness.workspace(os.environ)
    expected = {
        'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted',
        'GITHUB_REPOSITORY': 'Richard-Gnitnub/tracktemplate',
        'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_RUN_ATTEMPT': '1',
        'RUNNER_OS': 'Linux', 'RUNNER_ARCH': 'X64',
    }
    require(all(os.environ.get(k) == v for k, v in expected.items()),
            'Hosted first-attempt readiness required')
    require(re.fullmatch('[0-9a-f]{40}', os.environ.get('GITHUB_SHA', '')),
            'Source commit absent')
    return Path(os.environ['RUNNER_TEMP'])


def regular(path):
    path = readiness.regular(path)
    require(path.stat().st_uid == os.getuid(), 'Foreign evidence owner')
    return path


def retain_failure(stage):
    """Keep the causal exception exclusively, outside every public path."""
    require(stage in FAILURES, 'Unknown private failure instance')
    parent = scratch() / 'compatibility-readiness-private'
    parent.mkdir(mode=0o700, exist_ok=True)
    require(parent.is_dir() and not parent.is_symlink()
            and parent.stat().st_uid == os.getuid(),
            'Private failure directory differs')
    with (parent / (stage + '.txt')).open('x', encoding='utf-8') as stream:
        stream.write(traceback.format_exc())


def _diagnostic_transport_context():
    """Bind minimal refusal reporting to this acquisition-only attempt."""
    root = scratch()
    require(os.environ.get('GITHUB_JOB') == DIAGNOSTIC_PREFIX,
            'Acquisition-only job required')
    run_id = os.environ.get('GITHUB_RUN_ID', '')
    require(re.fullmatch('[1-9][0-9]*', run_id), 'Run identity absent')
    return root, {
        'schema_version': 1, 'status': 'FAIL',
        'source_commit': os.environ['GITHUB_SHA'],
        'run_id': run_id, 'run_attempt': 1,
    }


def _diagnostic_refusal_record(stage, error):
    """Write only finite failure facts before retaining private traceback."""
    root, record = _diagnostic_transport_context()
    require(stage in ('diagnostic-archive', 'diagnostic-publish'),
            'Unknown diagnostic refusal stage')
    reason = 'operation-refused'
    if isinstance(error, UnicodeDecodeError):
        reason = 'invalid-utf8'
    elif type(error) is ValueError and len(error.args) == 1:
        if type(error.args[0]) is str:
            reason = REFUSAL_REASONS.get(error.args[0], reason)
    category = next(kind.__name__ for kind in (
        OSError, ValueError, KeyError, TypeError) if isinstance(error, kind))
    record.update(stage=stage, reason_code=reason, exception_category=category)
    target = root / (DIAGNOSTIC_PREFIX + '-' + stage.removeprefix(
        'diagnostic-') + '-refusal.json')
    write(target, record)


def diagnostic_failure():
    """Pack finite refusal records without reading operational contents."""
    root, identity = _diagnostic_transport_context()
    contents = {}
    for stage in ('archive', 'publish'):
        outcome = os.environ.get('L1_' + stage.upper())
        require(outcome in ('success', 'failure', 'skipped', 'cancelled'),
                'Diagnostic step outcome absent')
        path = root / (DIAGNOSTIC_PREFIX + '-' + stage + '-refusal.json')
        if outcome != 'failure':
            require(not path.exists(), 'Unexpected diagnostic refusal')
            continue
        raw = public_bytes(path)
        record = strict_json(raw)
        require(type(record) is dict and set(record) == set(identity) | {
            'stage', 'reason_code', 'exception_category'},
            'Diagnostic refusal fields differ')
        require(all(record[key] == value for key, value in identity.items())
                and type(record['schema_version']) is int
                and type(record['run_attempt']) is int
                and record['stage'] == 'diagnostic-' + stage
                and record['reason_code'] in {
                    *REFUSAL_REASONS.values(), 'invalid-utf8',
                    'operation-refused'}
                and record['exception_category'] in (
                    'OSError', 'ValueError', 'KeyError', 'TypeError'),
                'Diagnostic refusal identity or category differs')
        contents['transport/' + stage + '-refusal.json'] = raw
    require(contents, 'No diagnostic refusal to preserve')
    return _tar(root / (DIAGNOSTIC_PREFIX + '-transport-failure.tar'),
                contents)


def diagnostic_failure_readback():
    """Verify exact refusal bytes without reopening operational evidence."""
    root, _ = _diagnostic_transport_context()
    return _readback(root, 'transport-failure', namespace=DIAGNOSTIC_PREFIX)


def seed():
    """Keep exact event strings; admit fixed schemas before installation."""
    root = scratch()
    event_path = regular(Path(os.environ['GITHUB_EVENT_PATH']))
    require(event_path.stat().st_size <= 128 * 1024, 'Oversized event')
    event = strict_json(event_path.read_bytes())
    require(event.get('repository', {}).get('private') is False
            and event.get('repository', {}).get('full_name')
            == 'Richard-Gnitnub/tracktemplate', 'Public repository required')
    inputs = event.get('inputs')
    require(type(inputs) is dict and set(inputs) == {
        'workload', 'readiness_control', 'readiness_review',
        'readiness_recovery'}, 'Dispatch inputs differ')
    stages = {'compatibility-readiness': 'readiness',
              'compatibility-acquisition-diagnostic': 'acquisition-diagnostic'}
    require(inputs['workload'] in stages, 'Reviewed dispatch required')
    raw = {}
    for name in ('control', 'review', 'recovery'):
        value = inputs['readiness_' + name]
        require(type(value) is str and 0 < len(value.encode()) <= 32768,
                'Prerequisite input bound differs')
        strict_json(value)
        raw[name] = value.encode()
    require(strict_json(raw['control']).get('stage')
            == stages[inputs['workload']], 'Dispatch stage differs')
    destination = root / 'compatibility-readiness-control'
    destination.mkdir(mode=0o700)
    for name, value in raw.items():
        with (destination / (name + '.json')).open('xb') as stream:
            stream.write(value)
    for name, source in CAPSULES.items():
        path = regular(ROOT / source)
        require(digest(path) == readiness.CAPSULE_FILES[name],
                'Frozen public capsule changed')
        with (destination / name).open('xb') as stream:
            stream.write(path.read_bytes())
    readiness.validate_control(strict_json(raw['control']), os.environ,
                               ROOT, destination)
    write(destination / 'seed.json', {
        'status': 'PASS', 'source_commit': os.environ['GITHUB_SHA'],
        'files': {name: digest(destination / name) for name in (
            'control.json', 'review.json', 'recovery.json', *CAPSULES)},
    })
    return destination


def seeded():
    root = scratch()
    destination = root / 'compatibility-readiness-control'
    record = strict_json(regular(destination / 'seed.json').read_bytes())
    require(set(record) == {'status', 'source_commit', 'files'}
            and record['status'] == 'PASS'
            and record['source_commit'] == os.environ['GITHUB_SHA']
            and set(record['files']) == {
                'control.json', 'review.json', 'recovery.json', *CAPSULES},
            'Seed binding differs')
    for name, identity in record['files'].items():
        require(digest(regular(destination / name)) == identity,
                'Seeded prerequisite changed')
    readiness.validate_control(
        strict_json((destination / 'control.json').read_bytes()),
        os.environ, ROOT, destination)
    return destination


def extract_base(archive, destination):
    """Read one member without extracting any archive path."""
    archive = regular(archive)
    require(archive.stat().st_size == ASSET['bytes']
            and digest(archive) == ASSET['sha256'], 'Approved archive differs')
    with tarfile.open(archive, 'r:') as bundle:
        matches = [member for member in bundle.getmembers()
                   if member.name == BASE_MEMBER]
        require(len(matches) == 1 and matches[0].isfile()
                and matches[0].size == 636344,
                'Approved base member differs')
        with bundle.extractfile(matches[0]) as stream:
            content = stream.read(636345)
    require(len(content) == 636344
            and hashlib.sha256(content).hexdigest() == readiness.BASE_SHA256,
            'Approved base content differs')
    require(not any(p.is_symlink() for p in destination.parents),
            'Linked base destination')
    with destination.open('xb') as stream:
        stream.write(content)


def acquire():
    destination = seeded()
    work = readiness.workspace(os.environ)
    readiness.prerequisites(work)
    installation = strict_json(regular(
        work / 'evidence/installer-result.json').read_bytes())
    require(installation.get('status') == 'PASS'
            and installation.get('cleanup') is True,
            'Installation or cleanup unproved')
    archive = destination / 'approved-base-inputs.tar'
    native.download_asset(ASSET, archive, maximum_bytes=ASSET['bytes'])
    extract_base(archive, destination / 'base.FCStd')
    write(destination / 'acquisition.json', {
        'status': 'PASS', 'archive': ASSET, 'member': BASE_MEMBER,
        'base': {'bytes': 636344, 'sha256': readiness.BASE_SHA256},
        'other_members_extracted': False,
    })


def installer_cleanup(work):
    """Load only the exact adapted module that created installer ownership."""
    target = work / 'readiness_installer.py'
    intent = work / 'evidence/installer-intent.json'
    owner = work / 'evidence/installer-ownership.json'
    if not intent.exists():
        require(not owner.exists() and not (work / 'installer.sh').exists(),
                'Unrecorded installer state')
        return {'cleanup': True, 'never_started': True}
    require(regular(target).read_text() == readiness.installer_source(
        regular(ROOT / 'tools/hosted_l1_gui_install.py').read_text()),
        'Adapted installer source changed')
    spec = importlib.util.spec_from_file_location('readiness_installer', target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if owner.exists():
        return module.cleanup(work)
    # A missing ownership receipt cannot authorise stopping a service.
    identity = module._identity(work)
    require(strict_json(regular(intent).read_bytes()) == identity,
            'Installer intent changed')
    absent = module._absent(module._show(identity['unit'], time.monotonic() + 10),
                            identity['unit'])
    return {'cleanup': absent, 'ownership_missing': True,
            'service_absence_proved': absent}


def finalize():
    """Independently recheck each owned process even after an earlier failure."""
    root = scratch()
    work = readiness.workspace(os.environ)
    outcomes = {key: os.environ.get(key, '') for key in OUTCOMES}
    require(all(value in ('success', 'failure', 'cancelled', 'skipped')
                for value in outcomes.values()), 'Workflow outcomes absent')
    summary = {'cleanup': False, 'workflow_outcomes': outcomes, 'errors': []}
    if not work.exists():
        require(outcomes['L1_PREPARE'] in ('failure', 'cancelled', 'skipped')
                and all(outcomes[key] == 'skipped' for key in OUTCOMES[1:]),
                'Absent work contradicts process outcomes')
        summary.update(cleanup=True, never_started=True)
        write(root / 'compatibility-readiness-finalization.json', summary)
        return summary
    require(work.is_dir() and not any(p.is_symlink() for p in (work, *work.parents)),
            'Unsafe finalization workspace')
    evidence = work / 'evidence'
    require(evidence.is_dir() and not evidence.is_symlink(),
            'Finalization evidence absent')
    # Always attempt all three boundaries; failure never suppresses cleanup.
    for name, action in (
        ('installer', lambda: installer_cleanup(work)),
        ('runtime', lambda: _runtime_cleanup(work, outcomes)),
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
        if name != 'runtime':
            write(evidence / ('transport-' + name + '-finalization.json'), record)
    summary['cleanup'] = not summary['errors']
    write(evidence / 'transport-finalization.json', summary)
    write(root / 'compatibility-readiness-finalization.json', summary)
    return summary


def _runtime_cleanup(work, outcomes):
    if outcomes['L1_RUN'] == 'skipped':
        require(not (work / 'evidence/guard').exists()
                and not (work / 'evidence/display-start-intent.json').exists()
                and not (work / 'readiness-entry.FCMacro').exists(),
                'Skipped runtime has execution state')
        record = {'cleanup': True, 'never_started': True}
        write(work / 'evidence/process-finalization.json', record)
        return record
    native.finalize('gui', work, work)
    return strict_json(regular(
        work / 'evidence/process-finalization.json').read_bytes())


def public_bytes(path):
    """Apply defense checks to source-reviewed originals without redaction.

    This scanner alone never establishes source safety. Admission binds the
    complete producer/workflow source, fixed inputs and fresh owned scratch.
    Independent source review must establish that those producers cannot read
    operator data, credentials or unapproved geometry into these instances.
    """
    path = regular(path)
    require(path.stat().st_size <= MAX_FILE, 'Operational file too large')
    content = path.read_bytes()
    text = content.decode('utf-8')
    require(not PRIVATE_PATH.search(text),
            'Private path in operational evidence')
    require(not CREDENTIAL.search(text),
            'Credential-like operational evidence')
    return content


def _inventory(directory, allowed, *, excluded=()):
    """Reject unexpected files, links and special nodes before any upload."""
    if not directory.exists():
        return {}
    require(directory.is_dir() and not directory.is_symlink(),
            'Evidence directory differs')
    contents = {}
    for path in sorted(directory.rglob('*')):
        name = path.relative_to(directory).as_posix()
        require(not path.is_symlink(), 'Linked evidence member')
        if any(name == prefix or name.startswith(prefix + '/')
               for prefix in excluded):
            # These runtime-owned inputs never become archive members.
            continue
        if path.is_dir():
            require(any(item.startswith(name + '/') for item in allowed),
                    'Unexpected evidence directory')
            continue
        require(name in allowed and path.is_file(),
                'Unlisted operational evidence')
        contents[name] = public_bytes(path)
    return contents


def original_failures(root):
    """Admit only the finite original exceptions of this reviewed attempt."""
    return _inventory(root / 'compatibility-readiness-private',
                      {name + '.txt' for name in FAILURES})


def _tar(destination, contents):
    """Expose no upload path until a bounded, exact archive is complete."""
    require(sum(len(data) for data in contents.values()) <= MAX_ARCHIVE,
            'Operational archive too large')
    require(all(re.fullmatch('[A-Za-z0-9_./-]+', name)
                and '..' not in Path(name).parts and not name.startswith('/')
                for name in contents), 'Unsafe transport member')
    partial = destination.with_suffix('.partial')
    with partial.open('xb') as stream, tarfile.open(fileobj=stream, mode='w') as bundle:
        for name, data in sorted(contents.items()):
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(data), 0o600
            bundle.addfile(member, io.BytesIO(data))
    require(partial.stat().st_size <= MAX_ARCHIVE, 'Archive bound exceeded')
    os.link(partial, destination)
    partial.unlink()
    return {'bytes': destination.stat().st_size, 'sha256': digest(destination)}


def acquisition_diagnostic():
    """Preserve only admitted acquisition originals in a separate artifact.

    Missing or unsafe originals remain explicit and are never reconstructed
    or redacted. This artifact records failure, not readiness or cleanup.
    It does not depend on either readiness archive or their collector.
    """
    root = scratch()
    controls = seeded()
    require(os.environ.get('L1_ACQUIRE') == 'failure',
            'Failed acquisition required')
    paths = {
        'logs/acquire.log': root / 'compatibility-readiness-logs/acquire.log',
        'original-diagnostics/acquire.txt': (
            root / 'compatibility-readiness-private/acquire.txt'),
    }
    contents, originals = {}, {}
    for name, path in paths.items():
        try:
            path.lstat()
        except FileNotFoundError:
            originals[name] = {'status': 'MISSING'}
            continue
        try:
            data = public_bytes(path)
        except (OSError, ValueError):
            originals[name] = {'status': 'WITHHELD'}
            continue
        contents[name] = data
        originals[name] = {
            'status': 'PRESERVED', 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest(),
        }
    record = {
        'schema_version': 1, 'status': 'FAIL',
        'acquisition_outcome': 'failure',
        'source_commit': os.environ['GITHUB_SHA'],
        'run_id': os.environ['GITHUB_RUN_ID'], 'run_attempt': 1,
        'control_sha256': digest(controls / 'control.json'),
        'originals': originals,
    }
    contents['transport/acquisition-failure.json'] = json.dumps(
        record, sort_keys=True, indent=2).encode() + b'\n'
    return _tar(root / 'compatibility-readiness-acquisition-failure.tar',
                contents)


def reseal_payload(work, controls):
    """Repeat the typed seal; an edited inventory alone is not evidence."""
    from tools import compatibility_evidence_output as output

    control = strict_json(regular(controls / 'control.json').read_bytes())
    require(control['stage'] == 'readiness',
            'Acquisition diagnostic cannot seal readiness outputs')
    assessment = strict_json(regular(
        work / 'evidence/readiness-assessment.json').read_bytes())
    require(assessment.get('status') in ('PASS', 'FAIL')
            and assessment.get('display_cleanup') is True
            and assessment.get('freecad_cleanup') is True,
            'Readiness cleanup unproved')
    scope = output.load_scope_capsule(controls / 'output-scope.json', ROOT)
    scope = output.bind_assessment_source(
        scope, 'readiness', readiness.SUITE, ROOT / readiness.SUITE,
        control['source_files'][readiness.SUITE])
    observation = strict_json(regular(
        work / 'readiness-observation.json').read_bytes())
    if assessment['status'] != 'PASS':
        observation['status'], observation['sentinel'] = 'FAIL', ''
    result = strict_json(regular(work / 'evidence/guard/result.json').read_bytes())
    require(type(result.get('process_exit')) is int
            and result.get('cleanup_proved') is True,
            'Guard process completion missing')
    observation.update(returncode=result['process_exit'], cleanup={
        'owned_pids': [], 'remaining_pids': [], 'complete': True})
    inventory = output.seal_outputs(
        scope, work / 'payload', work / 'transport-readiness', ['readiness'],
        {'readiness': observation})
    require(inventory == strict_json(regular(
        work / 'readiness-payload-inventory.json').read_bytes()),
        'Independent payload seal differs')
    return inventory, assessment['status']


def _operational_contents(root, work, *, through_archive=False):
    """Collect the same admitted originals for primary and final transport.

    Payload validation is separate. A failed typed seal must not prevent
    preservation of its original traceback or existing resource evidence.
    Active logs stay excluded. Every included original is byte-exact.
    """
    finalization = root / 'compatibility-readiness-finalization.json'
    contents, summary = {}, {}
    if finalization.exists():
        summary = strict_json(regular(finalization).read_bytes())
        contents['transport/finalization.json'] = public_bytes(finalization)
    seed_path = root / 'compatibility-readiness-control/seed.json'
    admitted = seed_path.exists()
    if admitted:
        controls = seeded()
        if work.exists():
            require(work.stat().st_uid == os.getuid()
                    and work.stat().st_mode & 0o077 == 0,
                    'Readiness scratch is not private')
            control_path = work / 'control.json'
            if control_path.exists():
                require(strict_json(regular(control_path).read_bytes())
                        == strict_json((controls / 'control.json').read_bytes()),
                        'Prepared controls differ from admitted controls')
        for name in ('control.json', 'review.json', 'recovery.json',
                     'seed.json', 'acquisition.json'):
            path = controls / name
            if path.exists():
                contents['prerequisites/' + name] = public_bytes(path)
        for name in WORK_RECORDS:
            path = work / name
            if path.exists():
                contents['operational/' + name] = public_bytes(path)
        adaptation = work / 'installer-adaptation.json'
        if adaptation.exists():
            original = regular(ROOT / 'tools/hosted_l1_gui_install.py')
            adapted = regular(work / 'readiness_installer.py')
            require(adapted.read_text() == readiness.installer_source(
                original.read_text()), 'Installer derivation changed')
            # This finite derivation record is not a diagnostic. The original
            # diff remains private because it includes a removed host path.
            contents['operational/installer-derivation.json'] = json.dumps({
                'original_sha256': digest(original),
                'adapted_sha256': digest(adapted),
                'derivation_receipt_sha256': digest(regular(adaptation)),
                'adaptation': 'source-bound-readiness-installer-v1',
            }, sort_keys=True).encode() + b'\n'
        for name, content in _inventory(
                work / 'evidence', EVIDENCE, excluded=('guard/profile',)).items():
            contents['operational/' + name] = content
        closed = 8 if through_archive else 7
        logroot = root / 'compatibility-readiness-logs'
        unread = tuple(name + '.log' for name in LOGS[closed:])
        for name in unread:
            path = logroot / name
            if path.exists():
                regular(path)
        logs = _inventory(logroot, {name + '.log' for name in LOGS},
                          excluded=unread)
        for name in LOGS[:closed]:
            if name + '.log' in logs:
                contents['logs/' + name + '.log'] = logs[name + '.log']
        for name, content in original_failures(root).items():
            contents['original-diagnostics/' + name] = content
    return contents, summary, admitted


def _preservation(contents, summary, admitted):
    """Check mandatory instances for the stages the workflow reached.

    These are existing producer outputs, not substitute result assertions.
    Failed stages keep every existing admitted original; absent mandatory
    instances remain an explicit incomplete-preservation result.
    """
    required = {'transport/finalization.json'}
    outcomes = summary.get('workflow_outcomes', {})
    if admitted:
        required.update('prerequisites/' + name + '.json'
                        for name in ('control', 'review', 'recovery', 'seed'))
        required.update(('logs/seed.log', 'logs/finalize.log'))
        for key, stage in zip(OUTCOMES, ('prepare', 'install', 'acquire', 'run')):
            if outcomes.get(key) in ('success', 'failure', 'cancelled'):
                required.add('logs/' + stage + '.log')
        if outcomes.get('L1_PREPARE') == 'success':
            required.update('operational/' + name for name in (
                'control.json', 'preparation.json',
                'process-finalization.json', 'transport-finalization.json',
                'transport-installer-finalization.json',
                'transport-display-finalization.json'))
        if outcomes.get('L1_INSTALL') == 'success':
            required.update('operational/' + name for name in (
                'installer-intent.json', 'installer-ownership.json',
                'installer-result.json', 'installer-output.log',
                'installer-derivation.json'))
        elif 'operational/installer-intent.json' in contents:
            required.update('operational/' + name for name in (
                'installer-result.json', 'installer-output.log',
                'installer-derivation.json'))
        if outcomes.get('L1_ACQUIRE') == 'success':
            required.add('prerequisites/acquisition.json')
            required.update('operational/' + name for name in (
                'base-binding.json', 'assessment-manifest.json'))
        if (outcomes.get('L1_PREPARE') == 'success'
                and outcomes.get('L1_RUN') in ('success', 'failure', 'cancelled')):
            required.add('logs/seal.log')
        if outcomes.get('L1_RUN') == 'success':
            required.update('operational/' + name for name in (
                'deployment.json', 'macro.json', 'readiness-assessment.json',
                'clearance.json', 'deadline-clearance.json', 'host.jsonl',
                'display-start-intent.json', 'display-ownership.json',
                'display-kernel.json', 'display-samples.jsonl',
                'display-cleanup.json', 'xvfb.log',
                'finalizer-clearance/clearance.json',
                'finalizer-clearance/deadline-clearance.json'))
        elif 'operational/display-start-intent.json' in contents:
            required.add('operational/display-cleanup.json')
        if (outcomes.get('L1_RUN') == 'success'
                or 'operational/guard/ownership.json' in contents):
            required.update('operational/guard/' + name for name in (
                'control.json', 'result.json', 'ownership.json',
                'measurements.jsonl', 'stdout', 'stderr', 'wrapper.stdout'))
    missing = sorted(required - contents.keys())
    return admitted and not missing, missing


def archive():
    root = scratch()
    work = readiness.workspace(os.environ)
    contents, summary, admitted = _operational_contents(root, work)
    payload = work / 'public-readiness'
    sealed = False
    payload_status = 'FAIL'
    if payload.exists():
        require(admitted, 'Unadmitted readiness payload')
        try:
            controls = root / 'compatibility-readiness-control'
            inventory, payload_status = reseal_payload(work, controls)
            allowed = {'gui/readiness/readiness-source.png',
                       'gui/readiness/result.json', 'gui/readiness/failure.txt'}
            require(set(inventory) <= allowed
                    and 'gui/readiness/result.json' in inventory,
                    'Payload instance differs')
            actual = {p.relative_to(payload).as_posix()
                      for p in payload.rglob('*') if not p.is_dir()}
            require(actual == set(inventory), 'Sealed payload inventory differs')
            verified = {}
            for name, expected in inventory.items():
                path = regular(payload / name)
                require(path.stat().st_size == expected['bytes']
                        and digest(path) == expected['sha256'],
                        'Sealed payload changed')
                verified['payload/' + name] = path.read_bytes()
        except (OSError, ValueError, KeyError, TypeError):
            retain_failure('archive-payload')
            path = root / 'compatibility-readiness-private/archive-payload.txt'
            contents['original-diagnostics/archive-payload.txt'] = public_bytes(path)
        else:
            contents.update(verified)
            sealed = True
    preserved, missing = _preservation(contents, summary, admitted)
    status = ('PASS' if sealed and payload_status == 'PASS'
              and preserved and summary.get('cleanup') is True
              and all(summary.get('workflow_outcomes', {}).get(key) == 'success'
                      for key in OUTCOMES) else 'FAIL')
    manifest = {
        'schema': 1, 'status': status, 'source_commit': os.environ['GITHUB_SHA'],
        'run_id': int(os.environ['GITHUB_RUN_ID']), 'retention_days': 30,
        'independent_preservation_required': True,
        'original_diagnostic_preservation_complete': preserved,
        'missing_mandatory_evidence': missing,
        'runtime_admission': False, 'matrix_dispatch': False,
        'zy_execution': False, 'payload_sealed': sealed,
        'files': {name: {'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest()}
                  for name, data in contents.items()},
    }
    contents['transport/manifest.json'] = json.dumps(
        manifest, sort_keys=True, indent=2).encode() + b'\n'
    identity = _tar(root / 'compatibility-readiness-primary.tar', contents)
    write(root / 'compatibility-readiness-archive.json',
          {'status': status, 'archive': identity, 'manifest': manifest})
    return status


def _readback(root, kind, *, namespace='compatibility-readiness'):
    source = regular(root / (namespace + '-' + kind + '.tar'))
    readback = regular(root / (namespace + '-' + kind + '-readback')
                       / source.name)
    prefix = {'primary': 'L1_PRIMARY', 'final': 'L1_FINAL',
              'acquisition-failure': 'L1_DIAGNOSTIC',
              'transport-failure': 'L1_TRANSPORT_FAILURE'}[kind]
    return native.verify_artifact(source, readback,
                                  os.environ.get(prefix + '_UPLOAD', ''),
                                  os.environ.get(prefix + '_DOWNLOAD', ''),
                                  os.environ.get(prefix + '_ID', ''))


def publish():
    """Bind primary readback; preserve both success and failure transport."""
    root = scratch()
    publication = {'status': 'FAIL', 'primary': None,
                   'independent_preservation_required': True}
    try:
        publication['primary'] = _readback(root, 'primary')
        publication['status'] = 'PASS'
    except (OSError, ValueError, KeyError):
        retain_failure('publish-primary')
        publication['error'] = 'primary-readback-unproved'
    contents, summary, admitted = _operational_contents(
        root, readiness.workspace(os.environ), through_archive=True)
    preserved, missing = _preservation(contents, summary, admitted)
    publication['original_diagnostic_preservation_complete'] = preserved
    publication['missing_mandatory_evidence'] = missing
    if not preserved:
        publication['status'] = 'FAIL'
    if 'transport/finalization.json' not in contents:
        publication['status'] = 'FAIL'
        publication['finalization_missing'] = True
    write(root / 'compatibility-readiness-publication.json', publication)
    contents['transport/publication.json'] = public_bytes(
        root / 'compatibility-readiness-publication.json')
    record = root / 'compatibility-readiness-archive.json'
    if record.exists():
        contents['transport/archive.json'] = public_bytes(record)
    _tar(root / 'compatibility-readiness-final.tar', contents)
    return publication


def complete():
    root = scratch()
    final = _readback(root, 'final')
    publication = strict_json(regular(
        root / 'compatibility-readiness-publication.json').read_bytes())
    archive_record = strict_json(regular(
        root / 'compatibility-readiness-archive.json').read_bytes())
    status = ('PASS' if publication['status'] == archive_record['status'] == 'PASS'
              else 'FAIL')
    record = {'status': status, 'final_readback': final,
              'primary_readback': publication['primary'],
              'independent_preservation_required': True,
              'runtime_admission': False, 'matrix_dispatch': False,
              'zy_execution': False}
    write(root / 'compatibility-readiness-completion.json', record)
    return status


def _diagnostic_controls():
    """Require diagnostic authority and refuse any runtime execution state."""
    controls = seeded()
    control = strict_json(regular(controls / 'control.json').read_bytes())
    require(control['stage'] == 'acquisition-diagnostic',
            'Acquisition-only authority required')
    work = readiness.workspace(os.environ)
    forbidden = (
        'evidence/guard', 'evidence/display-start-intent.json',
        'readiness-entry.FCMacro', 'readiness-observation.json',
        'payload', 'public-readiness', 'transport-readiness',
    )
    require(not any((work / name).exists() for name in forbidden),
            'Acquisition-only boundary exceeded')
    return controls


def diagnostic_archive():
    """Preserve operational originals without invoking a payload producer."""
    root = scratch()
    _diagnostic_controls()
    contents, summary, admitted = _operational_contents(
        root, readiness.workspace(os.environ))
    outcomes = summary.get('workflow_outcomes', {})
    require(outcomes.get('L1_RUN') == 'skipped',
            'Acquisition diagnostic must stop before runtime')
    preserved, missing = _preservation(contents, summary, admitted)
    complete = (preserved and summary.get('cleanup') is True
                and outcomes.get('L1_PREPARE') == 'success'
                and outcomes.get('L1_INSTALL') == 'success'
                and outcomes.get('L1_ACQUIRE') in ('success', 'failure'))
    status = ('PASS' if complete and outcomes['L1_ACQUIRE'] == 'success'
              else 'FAIL')
    manifest = {
        'schema': 1, 'stage': 'acquisition-diagnostic', 'status': status,
        'evidence_status': 'PASS' if complete else 'FAIL',
        'acquisition_outcome': outcomes.get('L1_ACQUIRE'),
        'interpretation': ('non-reproduction-only' if status == 'PASS'
                           else 'acquisition-or-evidence-failed'),
        'source_commit': os.environ['GITHUB_SHA'],
        'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_attempt': 1,
        'retention_days': 30, 'independent_preservation_required': True,
        'original_diagnostic_preservation_complete': preserved,
        'missing_mandatory_evidence': missing,
        'runtime_admission': False, 'matrix_dispatch': False,
        'zy_execution': False, 'gui_execution': False, 'sealing': False,
        'fixture_generation': False, 'readiness_dispatch': False,
        'files': {name: {'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest()}
                  for name, data in contents.items()},
    }
    contents['transport/manifest.json'] = json.dumps(
        manifest, sort_keys=True, indent=2).encode() + b'\n'
    identity = _tar(root / (DIAGNOSTIC_PREFIX + '-primary.tar'), contents)
    write(root / (DIAGNOSTIC_PREFIX + '-archive.json'),
          {'status': status, 'archive': identity, 'manifest': manifest})
    return status


def _diagnostic_failure_readback(root, control):
    """Require exact separate readback and every available safe original."""
    identity = _readback(root, 'acquisition-failure')
    source = root / 'compatibility-readiness-acquisition-failure.tar'
    with tarfile.open(source, 'r:') as bundle:
        stream = bundle.extractfile('transport/acquisition-failure.json')
        record = strict_json(stream.read())
    require(record.get('status') == 'FAIL'
            and record.get('acquisition_outcome') == 'failure'
            and record.get('source_commit') == os.environ['GITHUB_SHA']
            and record.get('run_id') == os.environ['GITHUB_RUN_ID']
            and record.get('run_attempt') == 1
            and record.get('control_sha256') == digest(control),
            'Acquisition failure identity differs')
    originals = record.get('originals', {})
    require(set(originals) == {
        'logs/acquire.log', 'original-diagnostics/acquire.txt'}
        and originals['logs/acquire.log'].get('status') == 'PRESERVED'
        and originals['original-diagnostics/acquire.txt'].get('status')
        in ('PRESERVED', 'MISSING'), 'Acquisition originals incomplete')
    return identity


def diagnostic_publish():
    """Bind both diagnostic readbacks and retain final operational evidence."""
    root = scratch()
    controls = _diagnostic_controls()
    contents, summary, admitted = _operational_contents(
        root, readiness.workspace(os.environ), through_archive=True)
    preserved, missing = _preservation(contents, summary, admitted)
    publication = {
        'status': 'FAIL', 'primary': None, 'acquisition_failure': None,
        'independent_preservation_required': True,
        'original_diagnostic_preservation_complete': preserved,
        'missing_mandatory_evidence': missing,
    }
    try:
        publication['primary'] = _readback(
            root, 'primary', namespace=DIAGNOSTIC_PREFIX)
        outcome = summary.get('workflow_outcomes', {}).get('L1_ACQUIRE')
        if outcome == 'failure':
            publication['acquisition_failure'] = _diagnostic_failure_readback(
                root, controls / 'control.json')
        require(outcome in ('success', 'failure'),
                'Acquisition did not reach a diagnostic result')
        if preserved and summary.get('cleanup') is True:
            publication['status'] = 'PASS'
    except (OSError, ValueError, KeyError, tarfile.TarError):
        retain_failure('publish-primary')
        publication['error'] = 'diagnostic-readback-unproved'
        path = root / 'compatibility-readiness-private/publish-primary.txt'
        contents['original-diagnostics/publish-primary.txt'] = public_bytes(path)
    target = root / (DIAGNOSTIC_PREFIX + '-publication.json')
    write(target, publication)
    contents['transport/publication.json'] = public_bytes(target)
    record = root / (DIAGNOSTIC_PREFIX + '-archive.json')
    if record.exists():
        contents['transport/archive.json'] = public_bytes(record)
    _tar(root / (DIAGNOSTIC_PREFIX + '-final.tar'), contents)
    return publication


def diagnostic_complete():
    """Report non-reproduction only after complete evidence and readbacks."""
    root = scratch()
    _diagnostic_controls()
    final = _readback(root, 'final', namespace=DIAGNOSTIC_PREFIX)
    publication = strict_json(regular(
        root / (DIAGNOSTIC_PREFIX + '-publication.json')).read_bytes())
    archive_record = strict_json(regular(
        root / (DIAGNOSTIC_PREFIX + '-archive.json')).read_bytes())
    manifest = archive_record['manifest']
    status = ('PASS' if publication['status'] == archive_record['status'] == 'PASS'
              else 'FAIL')
    record = {
        'stage': 'acquisition-diagnostic', 'status': status,
        'evidence_status': ('PASS' if publication['status']
                            == manifest['evidence_status'] == 'PASS' else 'FAIL'),
        'acquisition_outcome': manifest['acquisition_outcome'],
        'interpretation': manifest['interpretation'],
        'final_readback': final, 'primary_readback': publication['primary'],
        'acquisition_failure_readback': publication['acquisition_failure'],
        'independent_preservation_required': True,
        'runtime_admission': False, 'matrix_dispatch': False,
        'zy_execution': False, 'readiness_dispatch': False,
    }
    write(root / (DIAGNOSTIC_PREFIX + '-completion.json'), record)
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=(
        'seed', 'acquire', 'acquire-diagnostic', 'finalize', 'archive',
        'publish', 'complete', 'diagnostic-archive', 'diagnostic-publish',
        'diagnostic-complete', 'diagnostic-failure',
        'diagnostic-failure-readback'))
    arguments = parser.parse_args(argv)
    if arguments.stage == 'acquire-diagnostic':
        try:
            acquisition_diagnostic()
        except (OSError, ValueError, KeyError, TypeError):
            # Do not echo rejected bytes or depend on the failed collector.
            print('COMPATIBILITY_READINESS_ACQUISITION_DIAGNOSTIC_REFUSED')
            return 1
        print('COMPATIBILITY_READINESS_ACQUISITION_DIAGNOSTIC_PRESERVED')
        return 0
    if arguments.stage in ('diagnostic-failure', 'diagnostic-failure-readback'):
        try:
            globals()[arguments.stage.replace('-', '_')]()
        except (OSError, ValueError, KeyError, TypeError):
            print('COMPATIBILITY_DIAGNOSTIC_REFUSAL_PRESERVATION_FAIL')
            return 1
        print('COMPATIBILITY_DIAGNOSTIC_REFUSAL_PRESERVATION_PASS')
        return 0
    try:
        result = globals()[arguments.stage.replace('-', '_')]()
    except (OSError, ValueError, KeyError, TypeError) as error:
        if arguments.stage in ('diagnostic-archive', 'diagnostic-publish'):
            try:
                _diagnostic_refusal_record(arguments.stage, error)
            except (OSError, ValueError, KeyError, TypeError):
                print('COMPATIBILITY_DIAGNOSTIC_REFUSAL_RECORD_FAIL')
            try:
                retain_failure(arguments.stage.removeprefix('diagnostic-'))
            except (OSError, ValueError, KeyError, TypeError):
                print('COMPATIBILITY_DIAGNOSTIC_PRIVATE_RETENTION_FAIL')
        else:
            retain_failure(arguments.stage.removeprefix('diagnostic-'))
        print('COMPATIBILITY_READINESS_TRANSPORT_FAIL=' + arguments.stage)
        return 1
    if arguments.stage == 'diagnostic-complete':
        print('COMPATIBILITY_ACQUISITION_DIAGNOSTIC_' + (
            'PASS_NON_REPRODUCTION' if result == 'PASS' else 'FAIL'))
        return 0 if result == 'PASS' else 1
    if arguments.stage == 'complete':
        print('COMPATIBILITY_READINESS_TRANSPORT_' + result)
        return 0 if result == 'PASS' else 1
    if arguments.stage == 'finalize':
        return 0 if result['cleanup'] else 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
