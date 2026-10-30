#!/usr/bin/env python3
"""Coordinate the single approved public L1 workload on GitHub.

The workflow preserves complete diagnostics as ordinary Actions artifacts.
Approved inputs are downloaded anonymously and verified before extraction.
Approval records bind an already authorised scope; they do not authenticate
consent. Historical private-oriented filenames remain compatibility names.
"""

from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
import traceback
from unittest.mock import patch
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import freecad_validation_guard as guard  # noqa: E402
from tools import hosted_native_geometry_pilot as original  # noqa: E402
from tools import l1_private_payload as payload  # noqa: E402


CANDIDATE = '155cbb0353ca59a144df697197d8a4a68a91beef'
ENTRY_SHA256 = '20cd1694979830099e1e6988300c1c8bc9ea1dbc59ad7a5cef1832a0fe4bcc71'
SCOPE = 'L1-current-source-600-900-600-v4'
SCOPE_SHA256 = '0bec3956e4116740d702f6f09301430999f01b2935a54ae1c48f64cf9754f20f'
INPUT_REPOSITORY = 'Richard-Gnitnub/tracktemplate-validation-private'
DEPLOYMENT_ROOT = Path('/home/richard')
SENTINELS = {
    'readiness': 'L1 current-source hosted readiness passed',
    'native': 'L1 current-source hosted native validation passed',
}
SELECTORS = {
    'readiness': 'hosted_l1_current_source_suite.L1CurrentSource.test_readiness',
    'native': 'hosted_l1_current_source_suite.L1CurrentSource.test_canonical_600_900_600',
}
CONTROL_FILES = (
    '.github/workflows/l1-private-validation.yml',
    'tools/hosted_l1_private_validation.py', 'tools/l1_private_payload.py',
    'tools/freecad_validation_guard.py', 'tools/hosted_native_geometry_pilot.py',
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def limits(stage):
    require(stage in SELECTORS, 'Unsupported stage')
    return guard.ValidationLimits(4096, 90 if stage == 'readiness' else 7200)


def require_finalization_time(stage, environ, now):
    """Reserve ten minutes for artifact readback within the 140-minute job."""
    started = int(environ['L1_JOB_START_SECONDS'])
    require(0 <= now - started
            <= 140 * 60 - limits(stage).timeout_seconds - 600,
            'Insufficient job time for proof and finalization')


def validate_host(environ, memory):
    require(environ.get('GITHUB_REF') == 'refs/heads/main', 'Main required')
    require(environ.get('GITHUB_RUN_ID', '').isdigit(), 'Missing run identity')
    require(not any(environ.get(name, '').lower() in ('1', 'true') for name in (
        'RUNNER_DEBUG', 'ACTIONS_STEP_DEBUG', 'ACTIONS_RUNNER_DEBUG',
    )), 'Debug logging refused')
    return original.validate_admission(environ, memory)


def child_environment(environ, config, sha256):
    """Construct an allowlist; no tokens, secrets or caller import paths."""
    result = {key: environ[key] for key in (
        'HOME', 'PATH', 'LANG', 'LC_ALL', 'USER', 'LOGNAME',
        'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS',
        'GITHUB_ACTIONS', 'GITHUB_RUN_ID',
    ) if key in environ}
    result.update(TRACKTEMPLATE_L1_RUN_CONFIG=str(config),
                  TRACKTEMPLATE_L1_RUN_CONFIG_SHA256=sha256,
                  OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    return result


def validate_readiness(review, config, current_run, control):
    require(set(control['control_files_sha256']) == set(CONTROL_FILES),
            'Readiness control bindings incomplete')
    expected = {
        'status': 'PASS', 'independent_review': 'PASS',
        'source_commit': CANDIDATE, 'entry_sha256': ENTRY_SHA256,
        'scope_id': SCOPE, 'handling_decision': config['handling_decision'],
        'workflow_commit': control['workflow_commit'],
        'control_files_sha256': control['control_files_sha256'],
        'run_attempt': 1, 'tests': 1, 'skips': 0,
        'sentinel': True, 'cleanup': True, 'evidence_verified': True,
        'independent_preservation': True,
        'input_hashes': {row['id']: row['sha256'] for row in config['inputs']},
    }
    require(all(review.get(key) == value for key, value in expected.items()),
            'Readiness result or independent review does not match')
    require(type(review.get('run_id')) is int and review['run_id'] > 0
            and str(review['run_id']) != current_run,
            'Separate readiness run required')
    require(isinstance(review.get('evidence_sha256'), str)
            and len(review['evidence_sha256']) == 64
            and all(c in '0123456789abcdef' for c in review['evidence_sha256']),
            'Reviewed evidence identity absent')


def qualified_runtime(stdout):
    prefix = 'TRACKTEMPLATE_B16_FOUNDATION='
    lines = [line[len(prefix):] for line in stdout.splitlines()
             if line.startswith(prefix)]
    require(len(lines) == 1, 'Expected one foundation report')
    report = json.loads(lines[0])
    require(report.get('status') == 'modular-foundation-ready'
            and report.get('matched_profile_id') == original.EXPECTED_PROFILE
            and report.get('document_mutation') is False
            and report.get('workflow_launched') is False,
            'Qualified native foundation unproved')


def assess(stage, result, stdout, stderr, samples, clearance):
    """Reuse the pilot's unchanged resource/count/cleanup assessment.

    Only the authorised entry's runtime record, sentinel and fixed deadline
    differ. Raw evidence and resource assertions are not rewritten.
    """
    with ExitStack() as stack:
        for name, value in (
            ('LIMITS', limits(stage)), ('GEOMETRY_SENTINEL', SENTINELS[stage]),
            ('_qualified_runtime', qualified_runtime),
        ):
            stack.enter_context(patch.object(original, name, value))
        return original.assess_result(
            result, stdout, stderr, samples, clearance,
            deadline_clearance=clearance,
        )


def validate_native_receipt(stage, receipt):
    expected = {
        'status': 'PASS', 'stage': stage, 'profile': original.EXPECTED_PROFILE,
        'input_bindings_unchanged': True, 'owned_documents_closed': True,
        'cleanup_errors': [], 'sentinel': SENTINELS[stage],
    }
    if stage == 'native':
        expected.update(source_frame_comparisons=150, component_comparisons=138,
                        successful_preview_component_placements=690,
                        rolled_back_component_placements=230,
                        total_materialised_component_placements=920)
    else:
        expected.update(frame_input_count=150, comparator_negative_controls=8)
    require(all(receipt.get(key) == value for key, value in expected.items()),
            'Native receipt incomplete')


def paths():
    stage = os.environ['L1_STAGE']
    limits(stage)
    run = os.environ['GITHUB_RUN_ID']
    require(run.isdigit(), 'Invalid run')
    base = Path(os.environ['RUNNER_TEMP']).resolve()
    return stage, base / f'l1-private-{run}-{stage}', base / f'l1-publish-{run}-{stage}'


def command(*args, cwd=ROOT):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          check=True, timeout=15).stdout.strip()


def prepare(stage, work):
    """Validate reviewed code and public-input scope before acquisition."""
    require(os.getuid() != 0 and not sys.flags.optimize, 'Unsafe interpreter')
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    admission = validate_host(os.environ, Path('/proc/meminfo').read_text())
    control = json.loads(os.environ['L1_PRIVATE_CONTROL'])
    require(control['workflow_commit'] == os.environ['GITHUB_SHA']
            == command('git', 'rev-parse', 'HEAD'), 'Workflow identity changed')
    require(control['scope_id'] == SCOPE and control['scope_sha256'] == SCOPE_SHA256
            and control['stage'] == stage and control['candidate_commit'] == CANDIDATE,
            'Scope differs')
    require(control['independent_review'] == 'PASS'
            and control['handling_decision'] and control['dispatch_nonce'],
            'Reviewed handling record absent')
    access = control['access_review']
    require(access['status'] == 'PASS' and access['audited_at_utc']
            and access['owner'] == 'Richard-Gnitnub'
            and access['environment'] == 'l1-private-validation'
            and access['branches'] == ['main'] and access['tags'] == []
            and access['input_repository'] == INPUT_REPOSITORY
            and access['repository_public'] is True,
            'Owner-side access audit missing or differs')
    require(set(control['control_files_sha256']) == set(CONTROL_FILES),
            'Incomplete control source review')
    for relative, expected in control['control_files_sha256'].items():
        require(digest(ROOT / relative) == expected, 'Control source changed')
    require(digest(ROOT / 'tools/freecad_validation_guard.py') == original.GUARD_SHA256,
            'Accepted guard changed')
    candidate = ROOT / 'candidate'
    require(command('git', 'rev-parse', 'HEAD', cwd=candidate) == CANDIDATE,
            'Candidate commit differs')
    require(not command('git', 'status', '--porcelain', '--untracked-files=no',
                        cwd=candidate), 'Dirty candidate')
    require(digest(candidate / 'tests/hosted_l1_current_source_suite.py')
            == ENTRY_SHA256, 'Reviewed entry changed')
    write(work / 'control.json', control)
    write(work / 'evidence/admission.json', admission)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def download_asset(record, target, *, maximum_bytes=payload.MAX_ARCHIVE_BYTES):
    """Download only the reviewed public release asset without credentials."""
    require(type(record['asset_id']) is int and record['asset_id'] > 0,
            'Invalid asset identity')
    require(type(record['bytes']) is int and 0 < record['bytes'] <= maximum_bytes,
            'Invalid input archive size')
    url = f"https://api.github.com/repos/{INPUT_REPOSITORY}/releases/assets/{record['asset_id']}"
    request = urllib.request.Request(url, headers={
        'Accept': 'application/octet-stream',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    opener = urllib.request.build_opener(NoRedirect)
    try:
        response = opener.open(request, timeout=30)
    except urllib.error.HTTPError as error:
        require(error.code == 302, 'Asset request refused')
        location = error.headers['Location']
        parsed = urllib.parse.urlsplit(location)
        require(parsed.scheme == 'https' and parsed.hostname in (
            'release-assets.githubusercontent.com', 'objects.githubusercontent.com',
        ) and not parsed.username and not parsed.password,
                'Unexpected asset redirect')
        try:
            response = opener.open(urllib.request.Request(location), timeout=30)
        except urllib.error.URLError:
            # Signed storage URLs are temporary credentials. Do not retain
            # their text in an exception, even in otherwise private logs.
            raise ValueError('Asset storage transport failed') from None
    with response, target.open('xb') as stream:
        remaining = record['bytes']
        while remaining:
            data = response.read(min(1024 * 1024, remaining))
            require(data, 'Truncated input archive')
            stream.write(data)
            remaining -= len(data)
        require(not response.read(1), 'Oversized input archive')
    require(digest(target) == record['sha256'], 'Input archive changed')


def validate_input_map(config, manifest):
    """Reject any changed destination before the first input is deployed."""
    records = {row['id']: row for row in manifest['inputs']}
    rows = config['inputs']
    require(len(rows) == len(records) == 10
            and set(records) == {row['id'] for row in rows}, 'Input set differs')
    for row in rows:
        require(all(row[field] == records[row['id']][field]
                    for field in ('path', 'sha256', 'bytes')),
                'Manifest destination or binding differs')


def emergency_cleanup(work, owner, context=None):
    """Stop only the recorded invocation and verify its remaining resources."""
    context = context or guard.GuardContext()
    records = []
    result = {'proved': False, 'commands': records}
    try:
        scope, invocation = owner['scope'], owner['invocation']
        require(re.fullmatch(r'app-flatpak-org\.freecad\.FreeCAD-[A-Za-z0-9_-]+\.scope', scope)
                and re.fullmatch(r'[0-9a-f]{32}', invocation), 'Invalid owned identity')
        relative = (f'/user.slice/user-{os.getuid()}.slice/'
                    f'user@{os.getuid()}.service/app.slice/{scope}')
        require(owner['cgroup'] == relative, 'Owned cgroup differs')
        group = context.cgroup_root / relative.lstrip('/')
        require(guard._identity(context, records, scope) == invocation,
                'Owned invocation changed')
        require(guard._kill(context, records, scope, invocation), 'Owned stop failed')
        deadline = context.monotonic() + 10
        while True:
            if not group.exists():
                result['cgroup_removed'] = True
                break
            values = {name: (group / name).read_text().strip() for name in
                      ('cgroup.events', 'cgroup.procs', 'pids.current')}
            result['cgroup_readback'] = values
            if (dict(line.split() for line in values['cgroup.events'].splitlines()).get('populated') == '0'
                    and values['cgroup.procs'] == '' and values['pids.current'] == '0'):
                break
            require(context.monotonic() < deadline, 'Owned processes remain')
            context.sleep(0.1)
        listing = guard._command(context, records, [
            'systemctl', '--user', 'list-units', '--all', '--plain', '--no-legend',
            'tracktemplate-validation-*',
        ])
        require(listing.returncode == 0, 'Deadline inventory unavailable')
        units = {line.split()[0].rsplit('.', 1)[0]
                 for line in listing.stdout.splitlines() if line.strip()}
        require(len(units) <= 32, 'Deadline inventory exceeds bounded inspection')
        matched = []
        for name in sorted(units):
            require(re.fullmatch(r'tracktemplate-validation-[0-9a-f]{32}', name),
                    'Unknown deadline unit')
            shown = guard._command(context, records, [
                'systemctl', '--user', 'show', name + '.service',
                '-p', 'ExecStart', '--value',
            ])
            match = re.search(r'argv\[\]=(.*?)\s*;', shown.stdout)
            require(shown.returncode == 0 and match, 'Deadline ownership unavailable')
            arguments = shlex.split(match.group(1))
            expected = ['/usr/bin/python3', str(ROOT / 'tools/freecad_validation_guard.py'),
                        'watchdog', scope, invocation]
            if arguments == expected:
                matched.append(name)
        require(len(matched) <= 1, 'Owned deadline is ambiguous')
        result['owned_deadlines'] = matched
        for name in matched:
            stopped = guard._command(context, records, [
                'systemctl', '--user', 'stop', name + '.timer', name + '.service',
            ])
            require(stopped.returncode == 0, 'Owned deadline stop failed')
            with patch.object(original, 'OUTPUT', work / 'evidence'):
                require(original._deadline_clearance({'cleanup_proved': True,
                                                     'watchdog': name}),
                        'Owned deadline remains')
        with patch.object(original, 'OUTPUT', work / 'evidence'):
            require(original._clearance(), 'Flatpak clearance unproved')
        result['proved'] = True
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        result['error'] = traceback.format_exc()
    return result


def acquire(stage, work):
    control = json.loads((work / 'control.json').read_text())
    validate_host(os.environ, Path('/proc/meminfo').read_text())
    validate_input_repository()
    download_asset(control['input_archive'], work / 'inputs.tar')
    manifest = payload.read_manifest(work / 'inputs.tar')
    extracted = payload.extract_archive(work / 'inputs.tar', manifest, work / 'unpacked')
    config = json.loads(extracted['run-config'].read_text())
    require(config['scope_id'] == SCOPE
            and config['handling_decision'] == control['handling_decision']
            and config['checkpoint_commit'] == CANDIDATE, 'Private scope differs')
    validate_input_map(config, manifest)
    recovery_record = json.loads(extracted['recovery'].read_text())
    require(recovery_record.get('status') == 'PASS'
            and recovery_record.get('independent_review') == 'PASS'
            and recovery_record.get('checkpoint_commit') == CANDIDATE
            and recovery_record.get('input_hashes') == {
                row['id']: row['sha256'] for row in config['inputs']
            }, 'Recovery readiness absent')
    deployed = []
    # This root is created/chowned by setup, never by an archive member.
    allowed = DEPLOYMENT_ROOT
    require(allowed.is_dir() and allowed.resolve() == allowed
            and allowed.stat().st_uid == os.getuid(), 'Private target root unavailable')
    for row in config['inputs']:
        destination = Path(row['path'])
        require(destination.is_absolute() and destination.is_relative_to(allowed)
                and '..' not in destination.parts and not destination.exists(),
                'Unsafe or occupied input destination')
        for parent in reversed(destination.parents):
            if parent.is_relative_to(allowed):
                require(not parent.is_symlink(), 'Linked destination refused')
                parent.mkdir(mode=0o700, exist_ok=True)
        with extracted[row['id']].open('rb') as source, destination.open('xb') as target:
            shutil.copyfileobj(source, target)
        destination.chmod(0o400)
        deployed.append(str(destination))
        write(work / f'evidence/deployed-{len(deployed):02d}.json',
              {'path': str(destination), 'sha256': row['sha256']})
    native_evidence = work / 'evidence/native'
    native_evidence.mkdir(mode=0o700)
    config.update(repository_root=str(ROOT / 'candidate'),
                  private_evidence_dir=str(native_evidence))
    recovery = extracted['recovery']
    config['recovery'] = {'path': str(recovery), 'sha256': digest(recovery),
                          'bytes': recovery.stat().st_size}
    if stage == 'native':
        require('readiness-review' in extracted, 'Readiness review absent')
        validate_readiness(json.loads(extracted['readiness-review'].read_text()),
                           config, os.environ['GITHUB_RUN_ID'], control)
    write(work / 'run-config.json', config)
    write(work / 'evidence/run-config.json', config)
    write(work / 'evidence/private-control.json', control)
    write(work / 'evidence/input-manifest.json', manifest)
    shutil.copyfile(recovery, work / 'evidence/recovery.json')
    if 'readiness-review' in extracted:
        shutil.copyfile(extracted['readiness-review'],
                        work / 'evidence/readiness-review.json')


def run(stage, work):
    control = json.loads((work / 'control.json').read_text())
    validate_host(os.environ, Path('/proc/meminfo').read_text())
    require_finalization_time(stage, os.environ, time.time())
    require(command('flatpak', 'info', '--system', '--show-commit', guard.APP_ID)
            == original.APP_COMMIT, 'FreeCAD build differs')
    require(command('flatpak', 'info', '--system', '--show-runtime', guard.APP_ID)
            == original.RUNTIME, 'Runtime differs')
    require(command('flatpak', 'info', '--system', '--show-commit', original.RUNTIME)
            == original.RUNTIME_COMMIT, 'Runtime build differs')
    configuration = work / 'run-config.json'
    config = json.loads(configuration.read_text())
    if stage == 'native':
        validate_readiness(json.loads((work / 'unpacked/control/readiness-review.json').read_text()),
                           config, os.environ['GITHUB_RUN_ID'], control)
    samples = []

    def observe():
        try:
            row = original._memory(Path('/proc/meminfo').read_text())
            row['memory_pressure'] = Path('/proc/pressure/memory').read_text()
            row['monotonic_seconds'] = time.monotonic()
        except (OSError, ValueError) as error:
            row = {'error': repr(error)}
        samples.append(row)
        with (work / 'evidence/host.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')

    def sleep(seconds):
        # Do not interfere with the guard's finally path on telemetry failure.
        try:
            observe()
        except OSError:
            samples.append({'error': 'host-evidence-write'})
        time.sleep(seconds)

    observe()
    started = time.monotonic()
    clean = child_environment(os.environ, configuration, digest(configuration))
    argv = ['flatpak', 'run', '--command=FreeCADCmd',
            '--env=OMP_NUM_THREADS=1', '--env=OPENBLAS_NUM_THREADS=1']
    for name in ('TRACKTEMPLATE_L1_RUN_CONFIG', 'TRACKTEMPLATE_L1_RUN_CONFIG_SHA256',
                 'GITHUB_ACTIONS', 'GITHUB_RUN_ID'):
        argv.append(f'--env={name}={clean[name]}')
    argv += [guard.APP_ID, '-P', str(ROOT / 'candidate/tests'), '-t', SELECTORS[stage]]
    result = guard.run_guarded_flatpak(
        argv, limits=limits(stage), evidence_dir=work / 'evidence/guard',
        context=guard.GuardContext(sleep=sleep), cwd=ROOT / 'candidate',
        env=clean, isolate_profile=True,
    )
    observe()
    with patch.object(original, 'OUTPUT', work / 'evidence'):
        deadline_clear = original._deadline_clearance(result)
        flatpak_clear = original._clearance()
    guard_dir = work / 'evidence/guard'
    owned = [json.loads(line) for line in (guard_dir / 'measurements.jsonl').read_text().splitlines()]
    assessment = assess(stage, result, (guard_dir / 'stdout').read_text(),
                        (guard_dir / 'stderr').read_text(), owned,
                        deadline_clear and flatpak_clear)
    assessment['elapsed_seconds'] = time.monotonic() - started
    assessment['initial_mem_available_bytes'] = samples[0].get('MemAvailable', 0)
    if any('error' in row for row in samples):
        assessment.update(status='FAIL', classification='EVIDENCE_INCOMPLETE')
    receipt = json.loads((work / f'evidence/native/{stage}/result.json').read_text())
    try:
        validate_native_receipt(stage, receipt)
    except (KeyError, TypeError, ValueError):
        assessment.update(status='FAIL', classification='EVIDENCE_INCOMPLETE')
    assessment['native_receipt'] = receipt
    assessment['handling_decision'] = control['handling_decision']
    write(work / 'evidence/assessment.json', assessment)
    return 0 if assessment['status'] == 'PASS' else 1


def evidence_archive(work, destination, *, late=False):
    """Archive available diagnostics; omit retained input copies and bytes."""
    require(not destination.exists() and not destination.is_symlink(),
            'Evidence archive already exists')
    partial = destination.with_name(destination.name + '.partial')
    config_path = work / 'run-config.json'
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    input_hashes = {row['sha256'] for row in config.get('inputs', [])}
    records, excluded = {}, []
    selected = ([work / 'evidence/publication.json', work / 'evidence/publication.log',
                 work / 'evidence/finalization.json']
                if late else sorted((work / 'evidence').rglob('*')))
    with tarfile.open(partial, 'x') as archive:
        for path in selected:
            require(not path.is_symlink(), 'Linked evidence refused')
            if path.is_file():
                name = path.relative_to(work / 'evidence').as_posix()
                identity = {'sha256': digest(path), 'bytes': path.stat().st_size}
                if name in ('native/native/L1-copy.FCStd',
                            'native/native/XO-001-copy.FCStd') or identity['sha256'] in input_hashes:
                    excluded.append({'member': name, **identity,
                                     'reason': 'restricted-input-copy'})
                    continue
                records[name] = identity
                archive.add(path, arcname='evidence/' + name, recursive=False)
        content = json.dumps({'files': records, 'excluded_inputs': excluded},
                             sort_keys=True).encode()
        info = tarfile.TarInfo('evidence-manifest.json')
        info.size, info.mode = len(content), 0o600
        archive.addfile(info, io.BytesIO(content))
    require(partial.stat().st_size <= 512 * 1024**2,
            'Evidence transport bound exceeded')
    # Expose the exact upload path only after the retained ceiling passes.
    # Hard-link creation is exclusive; a failed archive remains as .partial.
    os.link(partial, destination)
    partial.unlink()
    return {'sha256': digest(destination), 'bytes': destination.stat().st_size}


def finalize(stage, work, public):
    """Prove process cleanup; retain staged inputs until evidence readback."""
    started = time.monotonic()
    cleanup, errors = False, []
    result_path = work / 'evidence/guard/result.json'
    ownership = work / 'evidence/guard/ownership.json'
    try:
        if result_path.exists():
            result = json.loads(result_path.read_text())
            clearance_output = work / 'evidence/finalizer-clearance'
            clearance_output.mkdir(mode=0o700)
            with patch.object(original, 'OUTPUT', clearance_output):
                cleanup = original._deadline_clearance(result) and original._clearance()
            cleanup = cleanup and result.get('cleanup_proved') is True
        elif ownership.exists():
            emergency = emergency_cleanup(work, json.loads(ownership.read_text()))
            write(work / 'evidence/emergency-cleanup.json', emergency)
            cleanup = emergency['proved']
        else:
            # No owned payload exists, but setup failure still cannot PASS.
            with patch.object(original, 'OUTPUT', work / 'evidence'):
                cleanup = original._clearance()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        errors.append(traceback.format_exc())
    write(work / 'evidence/process-finalization.json', {
        'cleanup': cleanup and not errors, 'errors': errors,
        'seconds': time.monotonic() - started,
        'workflow_outcomes': {name: os.environ.get(name, '') for name in (
            'L1_PREPARE', 'L1_INSTALL', 'L1_ACQUIRE', 'L1_RUN',
        )},
    })
    # The publication step archives after this process and its outer log close.
    return 0 if not errors else 1


def cleanup_staging(work, preserved):
    """Remove exact owned plaintext staging only after primary readback.

    This proves file absence, not secure erasure. Controls and diagnostic
    evidence remain private and are not part of this removal allowlist.
    """
    archive = work / 'evidence.tar'
    require(type(preserved.get('asset_id')) is int and preserved['asset_id'] > 0
            and preserved.get('sha256') == digest(archive)
            and preserved.get('bytes') == archive.stat().st_size,
            'Primary preservation not proved')
    process = json.loads((work / 'evidence/process-finalization.json').read_text())
    result = dict(process, staging_inputs_removed=[], staging_files_removed=[],
                  staging_absence_verified=[], primary_preservation=preserved)
    result['errors'] = list(process.get('errors', []))
    targets = [(work / 'inputs.tar', None, False)]
    targets.extend((work / 'unpacked/inputs' / name, None, False)
                   for name in payload.INPUT_IDS)
    targets.extend((work / 'evidence/native/native' / name, None, False)
                   for name in ('L1-copy.FCStd', 'XO-001-copy.FCStd'))
    try:
        require(process.get('cleanup') is True, 'Process cleanup not proved')
        for index in range(1, 11):
            receipt_path = work / f'evidence/deployed-{index:02d}.json'
            if not receipt_path.exists():
                continue
            require(not receipt_path.is_symlink(), 'Linked staging receipt refused')
            row = json.loads(receipt_path.read_text())
            destination = Path(row['path'])
            require(destination.is_absolute()
                    and destination.is_relative_to(DEPLOYMENT_ROOT)
                    and '..' not in destination.parts, 'Staged destination refused')
            targets.append((destination, row['sha256'], True))
    except (OSError, ValueError, KeyError, TypeError):
        result['errors'].append(traceback.format_exc())
    if not result['errors']:
        for path, expected, deployed in targets:
            try:
                require(not any(item.is_symlink() for item in (path, *path.parents)),
                        'Linked staging cleanup refused')
                if path.exists():
                    require(path.is_file() and path.stat().st_uid == os.getuid(),
                            'Staged file ownership differs')
                    identity = {'path': str(path), 'sha256': digest(path),
                                'bytes': path.stat().st_size}
                    require(expected is None or identity['sha256'] == expected,
                            'Staged input changed')
                    path.unlink()
                    result['staging_files_removed'].append(identity)
                    if deployed:
                        result['staging_inputs_removed'].append(str(path))
                require(not path.exists() and not path.is_symlink(),
                        'Staged file remains')
                result['staging_absence_verified'].append(str(path))
            except (OSError, ValueError, KeyError):
                result['errors'].append(traceback.format_exc())
    result['cleanup'] = process.get('cleanup') is True and not result['errors']
    write(work / 'evidence/finalization.json', result)
    return result


def api_request(url):
    """Read fixed GitHub metadata anonymously; refuse redirects and non-200."""
    parsed = urllib.parse.urlsplit(url)
    require(parsed.scheme == 'https' and parsed.hostname == 'api.github.com'
            and not parsed.username and not parsed.password,
            'Unsupported public endpoint')
    request = urllib.request.Request(url, headers={
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
            require(response.status == 200, 'Public metadata HTTP status differs')
            content = response.read(1024 * 1024 + 1)
            require(len(content) <= 1024 * 1024, 'Oversized GitHub metadata')
            return json.loads(content)
    except urllib.error.URLError:
        raise ValueError('Public metadata transport failed') from None


def validate_input_repository():
    metadata = api_request(f'https://api.github.com/repos/{INPUT_REPOSITORY}')
    require(metadata.get('private') is False
            and metadata.get('full_name') == INPUT_REPOSITORY
            and metadata.get('owner', {}).get('login') == 'Richard-Gnitnub',
            'Public input repository differs')


def verify_artifact(source, readback, upload, download, artifact_id):
    """Require successful same-run Actions transport and exact returned bytes."""
    require(upload == download == 'success'
            and artifact_id.isdigit() and int(artifact_id) > 0,
            'Artifact publication or download failed')
    require(not readback.is_symlink() and readback.is_file(),
            'Artifact readback unavailable')
    identity = {'sha256': digest(source), 'bytes': source.stat().st_size,
                'asset_id': int(artifact_id)}
    require(readback.stat().st_size == identity['bytes']
            and digest(readback) == identity['sha256'], 'Artifact readback differs')
    return identity


def public_summary(stage, work, evidence, publication_complete):
    assessment_path = work / 'evidence/assessment.json'
    assessment = json.loads(assessment_path.read_text()) if assessment_path.exists() else {}
    final_path = work / 'evidence/finalization.json'
    final = json.loads(final_path.read_text()) if final_path.exists() else {}
    receipt = assessment.get('native_receipt', {})
    cleanup = final.get('cleanup') is True
    passed = (assessment.get('status') == 'PASS' and cleanup
              and len(final.get('staging_inputs_removed', [])) == 10
              and publication_complete)
    summary = {
        'schema': 1, 'source_commit': CANDIDATE,
        'workflow_commit': os.environ['GITHUB_SHA'],
        'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_attempt': 1,
        'stage': stage, 'outcome': 'PASS' if passed else 'INCOMPLETE',
        'counts': {'expected_tests': 1, 'observed_tests': assessment.get('completed_native_tests', 0),
                   'skips': assessment.get('skips', 0),
                   'expected_frames': 150 if stage == 'native' else 0,
                   'observed_frames': receipt.get('source_frame_comparisons', 0),
                   'expected_components': 138 if stage == 'native' else 0,
                   'observed_components': receipt.get('component_comparisons', 0),
                   'successful_components': receipt.get('successful_preview_component_placements', 0),
                   'rolled_back_components': receipt.get('rolled_back_component_placements', 0)},
        'flags': {'sentinel': receipt.get('sentinel') == SENTINELS[stage],
                  'input_integrity': receipt.get('input_bindings_unchanged') is True,
                  'cleanup': cleanup},
        'timings_seconds': {'total': assessment.get('elapsed_seconds', 0),
                            'readiness': receipt.get('stage_timings', {}).get('readiness_seconds', 0),
                            'native': assessment.get('elapsed_seconds', 0) if stage == 'native' else 0,
                            'finalization': final.get('seconds', 0)},
        'resources': {'memory_peak_bytes': assessment.get('peak_cgroup_memory_bytes', 0),
                      'cpu_usage_usec': assessment.get('cpu_usage_usec', 0), 'swap_peak_bytes': 0,
                      'initial_mem_available_bytes': assessment.get('initial_mem_available_bytes', 0),
                      'tasks_peak': assessment.get('peak_tasks_observed', 0)},
        'evidence': evidence,
    }
    return payload.validate_public_summary(summary)


def seal(work):
    """Seal available diagnostics before the first standard artifact upload."""
    return evidence_archive(work, work / 'evidence.tar')


def publish(stage, work, public):
    """Verify primary readback, clean staging, and seal final diagnostics.

    The workflow performs transport with pinned ordinary artifact actions.
    A failed primary readback retains staging and is recorded in the final
    diagnostics archive. Neither transport nor cleanup is retried.
    """
    publication = {'primary': None, 'errors': [], 'retention_days': 30,
                   'delete_not_before_verified_independent_preservation': True}
    try:
        evidence = verify_artifact(
            work / 'evidence.tar', work / 'readback-primary/evidence.tar',
            os.environ.get('L1_PRIMARY_UPLOAD', ''),
            os.environ.get('L1_PRIMARY_DOWNLOAD', ''),
            os.environ.get('L1_PRIMARY_ID', ''),
        )
        publication['primary'] = evidence
        cleanup = cleanup_staging(work, evidence)
        require(cleanup['cleanup'], 'Plaintext staging cleanup incomplete')
    except (OSError, ValueError, KeyError, TypeError):
        publication['errors'].append(traceback.format_exc())
    write(work / 'evidence/publication.json', publication)
    # Include all available diagnostics when the first upload failed too.
    evidence_archive(work, work / 'publication.tar')
    return 0 if not publication['errors'] else 1


def complete(stage, work, public):
    """Verify final artifact readback before emitting the fixed summary."""
    evidence = {'sha256': '0' * 64, 'bytes': 0, 'asset_id': 0}
    complete = False
    try:
        evidence = verify_artifact(
            work / 'publication.tar', work / 'readback-final/publication.tar',
            os.environ.get('L1_FINAL_UPLOAD', ''),
            os.environ.get('L1_FINAL_DOWNLOAD', ''),
            os.environ.get('L1_FINAL_ID', ''),
        )
        publication = json.loads((work / 'evidence/publication.json').read_text())
        complete = (os.environ.get('L1_PUBLICATION') == 'success'
                    and publication['primary'] is not None
                    and not publication['errors'])
    except (OSError, ValueError, KeyError, TypeError):
        complete = False
    # The final artifact already contains all diagnostic generation. These
    # fixed-schema operations cannot convert missing evidence into PASS.
    try:
        public.mkdir(mode=0o700, exist_ok=True)
        write(public / 'summary.json', public_summary(stage, work, evidence, complete))
        return 0 if complete else 1
    except (OSError, ValueError, KeyError, TypeError):
        return 1

def main():
    require(len(sys.argv) == 2, 'Expected one fixed operation')
    stage, work, public = paths()
    operation = sys.argv[1]
    if operation == 'prepare':
        prepare(stage, work)
    elif operation == 'acquire':
        acquire(stage, work)
    elif operation == 'run':
        return run(stage, work)
    elif operation == 'finalize':
        return finalize(stage, work, public)
    elif operation == 'seal':
        seal(work)
    elif operation == 'complete':
        return complete(stage, work, public)
    elif operation == 'publish':
        return publish(stage, work, public)
    elif operation == 'finish':
        try:
            summary = json.loads((public / 'summary.json').read_text())
            payload.validate_public_summary(summary)
            return 0 if summary['outcome'] == 'PASS' and os.environ.get('L1_SUMMARY_UPLOAD') == 'success' else 1
        except (OSError, ValueError, KeyError):
            return 1
    else:
        raise ValueError('Unsupported operation')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Exception, KeyboardInterrupt):
        # The outer shell must already point both descriptors at evidence logs.
        traceback.print_exc()
        raise SystemExit(1) from None
