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


def limits(stage):
    require(stage in ('readiness', 'gui'), 'Unsupported GUI stage')
    return guard.ValidationLimits(4096, 90 if stage == 'readiness' else 7200)


def display_limits(stage):
    require(stage in ('readiness', 'gui'), 'Unsupported GUI stage')
    return guard.ValidationLimits(256, 190 if stage == 'readiness' else 7300,
                                  25, 16)


def sentinel(stage):
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
    values = native.validate_host(environ, memory)
    require(values['MemAvailable'] >= (
        LIMITS.memory_max_mib + DISPLAY_LIMITS.memory_max_mib + RESERVE_MIB
    ) * 1024**2, 'Insufficient memory for FreeCAD, display and reserve')
    return values


def validate_authority(record, environ):
    """Require a separate explicit GUI scope; native approval is insufficient."""
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
    control = json.loads(os.environ['L1_GUI_CONTROL'])
    validate_authority(control, os.environ)
    require(native.command('git', 'rev-parse', 'HEAD') == control['source_commit'],
            'Reviewed checkout differs')
    require(not native.command('git', 'status', '--porcelain',
                               '--untracked-files=no'), 'Dirty source checkout')
    validate_frozen_source(control)
    for name, expected in control['control_files_sha256'].items():
        require(digest(ROOT / name) == expected, 'Reviewed GUI control changed')
    if diagnostic_enabled(os.environ):
        validate_diagnostic_source(control)
    require(digest(ROOT / ENTRY) == control['gui_entry_sha256'],
            'Reviewed GUI entry changed')
    require(digest(ROOT / 'tools/freecad_validation_guard.py')
            == original.GUARD_SHA256, 'Accepted guard changed')
    write(work / 'control.json', control)
    write(work / 'evidence/gui-authority.json', control)
    write(work / 'evidence/admission.json', admission)


def acquire(work):
    """Reuse the unchanged ten-input native archive and recovery bindings."""
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


def display_properties(stage='gui'):
    """Return explicit kernel and deadline properties for the display alone."""
    return {
        'MemoryMax': str(DISPLAY_LIMITS.memory_max_mib * 1024**2),
        'MemoryHigh': str(DISPLAY_LIMITS.memory_max_mib * 1024**2),
        'MemorySwapMax': '0', 'CPUQuota': '25%',
        'CPUQuotaPeriodSec': '100ms', 'TasksMax': '16',
        'RuntimeMaxSec': str(display_limits(stage).timeout_seconds), 'TimeoutStopSec': '5',
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
    properties = display_properties(stage)
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
                '3min 10s' if stage == 'readiness' else '2h 1min 40s')
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
    content = ('import sys\n'
               'import FreeCAD as App\n'
               'import FreeCADGui as Gui\n'
               f'sys.path.insert(0, {str(ROOT / "tests")!r})\n'
               'import hosted_l1_gui_suite\n'
               + observer +
               'hosted_l1_gui_suite.start()\n')
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
    argv = ['flatpak', 'run', '--command=FreeCAD']
    argv += [f'--env={name}={clean[name]}' for name in names]
    return [*argv, guard.APP_ID, str(macro)]


def qualified_runtime(stdout):
    """Reuse the accepted strict parser with the one actual GUI test frame."""
    with patch.object(native, 'SELECTORS', {
        'gui': 'hosted_l1_gui_suite.L1Gui.test_authorised_gui_stage',
    }):
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
            argv, limits=limits(stage), evidence_dir=work / 'evidence/guard',
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
                ('LIMITS', limits(stage)),
                ('GEOMETRY_SENTINEL', sentinel(stage)),
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
        validate_gui_receipt(receipt, work, stage=stage)
        assessment['gui_receipt'] = receipt
        assessment['scope'] = SCOPE
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
        require(not target.exists(), 'Copied document retention target occupied')
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
        cleanup = native.cleanup_staging(work, evidence)
        require(cleanup['cleanup'], 'Input staging cleanup incomplete')
    except (OSError, ValueError, KeyError, TypeError):
        publication['errors'].append(traceback.format_exc())
    write(work / 'evidence/publication.json', publication)
    exclude_gui_copy(work)
    native.evidence_archive(work, work / 'publication.tar')
    return 0 if not publication['errors'] else 1


def complete(work, public):
    """Emit PASS only after both exact artifacts and every cleanup proof."""
    summary = {'schema': 1, 'scope_id': SCOPE, 'outcome': 'INCOMPLETE',
               'source_commit': os.environ['GITHUB_SHA'],
               'stage': selected_stage(os.environ),
               'run_id': int(os.environ['GITHUB_RUN_ID']), 'run_attempt': 1}
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
                and len(cleanup['staging_inputs_removed']) == 10
                and display['cleanup'] and staging['copied_input_absent']
                and staging['display_cookie_absent'], 'GUI proof incomplete')
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
