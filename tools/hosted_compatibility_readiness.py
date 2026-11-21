#!/usr/bin/env python3
"""Prepare one candidate-runtime GUI readiness proof; never run the matrix.

The caller must supply reviewed local control, decision and input files.
This module supplies no upload, dispatch, publication or runtime admission.
"""

import argparse
from contextlib import ExitStack
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import freecad_validation_guard as guard  # noqa: E402
from tools import hosted_l1_gui_validation as gui  # noqa: E402
from tools import hosted_native_geometry_pilot as pilot  # noqa: E402

BASE_COMMIT = 'dcb326e531bde7d861ce4a316776dd00dab297e8'
APP_COMMIT = (
    'b7e0947f142c4e263d2cf950a7decb5a96f7243b0bf5adc9fda60d8e8d1eb811'
)
RUNTIME_COMMIT = (
    '2c059c881e5059ea801dc963cc970b83d775de03b98e9f570b31790e1f92ab5d'
)
BASE_SHA256 = (
    '0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c'
)
DEFAULT_SHA256 = (
    '6539ff066b8abcd81cb111c3127124580e6bca44eb19c09ea8ae93175de7113f'
)
DECISION_SHA256 = (
    '1ae5142f40708bc01b00bf1232e6360e1a43121a62faec4cca7f48eeceb87e6a'
)
DIAGNOSTIC_DECISION_SHA256 = (
    '7220f8f3cca48e3bfaa3dcf1e908139b04674d90016d003ec67e609c09aeaff5'
)
SCOPE_SHA256 = (
    '0dc9d0d13eeb9722e6d3e9e9d4c7ecdf14131fe1e8724be65bfd2ab726a2930b'
)
CANDIDATE_SHA256 = (
    '285192eeb388e0d2d6be64a47170e1cafa9ffb8efbf6ee3b43d51edc3769c7e7'
)
SENTINEL = 'TRACKTEMPLATE_COMPATIBILITY_GUI_READINESS_PASS'
SUITE = 'tests/hosted_compatibility_readiness_suite.py'
LIMITS = guard.ValidationLimits(4096, 90)
CAPSULE_FILES = {
    'assessment-inputs.json': (
        'd70635526b325d392a1074b721602118fb4ae7a587302472cf713bd93b8800f5'
    ),
    'output-scope.json': (
        'db94a823d811dd96ccdc4a2f3917ec365409d4682a781f78feb62e3478098c60'
    ),
}
CONTROL_FILES = (
    'tools/hosted_compatibility_readiness.py', SUITE,
    'tests/validate_hosted_compatibility_readiness.py',
    'tools/prepare_runtime_assessment.py',
    'tests/validate_runtime_assessment.py',
    'tools/compatibility_evidence_output.py',
    'tests/validate_compatibility_evidence_output.py',
    'tools/freecad_validation_guard.py',
    'tools/hosted_l1_gui_validation.py', 'tools/hosted_l1_gui_install.py',
    'tools/hosted_l1_private_validation.py',
    'tools/hosted_native_geometry_pilot.py',
    'tests/hosted_l1_gui_suite.py',
    'tools/compatibility_readiness_transport.py',
    'tests/validate_compatibility_readiness_transport.py',
    '.github/workflows/native-geometry-pilot.yml',
    'tools/compatibility_gui_bridge.py',
    'tests/validate_compatibility_gui_bridge.py',
    'tools/development_toolchain_preflight.py',
    'tools/freecad_bridge/freecad-cli-tracktemplate.patch',
    'tools/freecad_bridge/test_freecad_cli_checkout.py',
    'tests/validate_bounded_freecad.py',
    'tests/validate_hosted_native_geometry.py',
)
CLICK_URL = (
    'https://files.pythonhosted.org/packages/1a/70/'
    'e63223f8116931d365993d4a6b7ef653a4d920b41d03de7c59499962821f/'
    'click-8.1.6-py3-none-any.whl'
)
CLICK_SHA256 = (
    'fa244bb30b3b5ee2cae3da8f55c9e5e0c0e86093306301fb418eb9dc40fbded5'
)


def require(condition, message):
    """Refuse a missing prerequisite without starting a process."""
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def regular(path):
    path = Path(path)
    require(path.is_absolute() and path.is_file()
            and not any(p.is_symlink() for p in (path, *path.parents)),
            'Regular unlinked absolute input required')
    return path


def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def validate_control(control, environ, source_root, decisions):
    """Check review and recovery bindings before installation or acquisition."""
    expected = {
        'schema_version': 1, 'stage': 'readiness',
        'source_base_commit': BASE_COMMIT, 'owner_decision': 'D-P9-023',
        'owner_decision_sha256': DECISION_SHA256,
        'output_scope_sha256': SCOPE_SHA256,
        'app_commit': APP_COMMIT, 'runtime_commit': RUNTIME_COMMIT,
        'execution_authorized': True, 'independent_review': 'PASS',
        'installer_seconds': 540, 'freecad_limits': vars(LIMITS),
        'display_limits': vars(guard.ValidationLimits(256, 190, 25, 16)),
        'reserve_mib': 8192, 'runtime_admission': False,
        'matrix_dispatch': False, 'zy_execution': False,
    }
    if type(control) is dict and control.get('stage') == 'acquisition-diagnostic':
        expected.update(
            stage='acquisition-diagnostic', owner_decision='D-P9-029',
            owner_decision_sha256=DIAGNOSTIC_DECISION_SHA256,
            acquisition_seconds=60, job_seconds=1800, maximum_attempts=1,
            gui_execution=False, sealing=False, fixture_generation=False,
            readiness_dispatch=False)
    require(type(control) is dict and set(control) == set(expected) | {
        'source_commit', 'source_files', 'review', 'recovery'},
        'Exact readiness control fields required')
    require(all(type(control[k]) is type(v) and control[k] == v
                for k, v in expected.items()),
            'Readiness authority or limits differ')
    for name in ('freecad_limits', 'display_limits'):
        require(all(type(value) is int for value in control[name].values()),
                'Integer resource limits required')
    environment = {
        'GITHUB_ACTIONS': 'true',
        'GITHUB_REPOSITORY': 'Richard-Gnitnub/tracktemplate',
        'GITHUB_EVENT_NAME': 'workflow_dispatch',
        'RUNNER_ENVIRONMENT': 'github-hosted', 'GITHUB_RUN_ATTEMPT': '1',
        'RUNNER_OS': 'Linux', 'RUNNER_ARCH': 'X64',
    }
    require(all(environ.get(k) == v for k, v in environment.items()),
            'Hosted first-attempt readiness required')
    require(not any(environ.get(k, '').lower() in ('1', 'true') for k in (
        'RUNNER_DEBUG', 'ACTIONS_STEP_DEBUG', 'ACTIONS_RUNNER_DEBUG')),
        'Debug logging refused')
    commit = control.get('source_commit', '')
    require(type(commit) is str
            and re.fullmatch('[0-9a-f]{40}', commit) is not None
            and commit == environ.get('GITHUB_SHA'),
            'Dispatched source differs')
    require(re.fullmatch('[1-9][0-9]*', environ.get('GITHUB_RUN_ID', ''))
            is not None, 'Run identity absent')
    pins = control.get('source_files', {})
    require(type(pins) is dict and set(pins) == set(CONTROL_FILES),
            'Complete readiness source review required')
    for name, expected_hash in pins.items():
        require(type(expected_hash) is str
                and re.fullmatch('[0-9a-f]{64}', expected_hash) is not None
                and digest(regular(source_root / name)) == expected_hash,
                'Reviewed readiness source changed')
    for name, expected_hash in CAPSULE_FILES.items():
        require(digest(regular(decisions / name)) == expected_hash,
                'Decision input changed')
    require(digest(regular(source_root / 'reference/contracts/'
                           'phase1-compatibility.json')) == DEFAULT_SHA256,
            'Canonical runtime contract changed')
    for key in ('review', 'recovery'):
        binding = control.get(key, {})
        require(type(binding) is dict and set(binding) == {'path', 'sha256'},
                'Exact prerequisite binding required')
        name = binding.get('path', '')
        require(name == key + '.json',
                'Local prerequisite receipt name differs')
        require(type(binding['sha256']) is str
                and re.fullmatch('[0-9a-f]{64}', binding['sha256']) is not None,
                'Prerequisite digest differs')
        path = regular(decisions / name)
        require(digest(path) == binding.get('sha256'),
                'Prerequisite receipt identity changed')
        receipt = json.loads(path.read_text())
        fields = {'status', 'source_commit', 'source_files'}
        fields.update({'independent', 'stage', 'output_scope_sha256'}
                      if key == 'review' else {'independent_preservation'})
        require(type(receipt) is dict and set(receipt) == fields,
                'Exact prerequisite receipt fields required')
        require(receipt.get('status') == 'PASS'
                and receipt.get('source_commit') == commit
                and receipt.get('source_files') == pins,
                'Review or recovery is incomplete for this source')
        if key == 'review':
            require(receipt.get('independent') is True
                    and receipt.get('stage') == expected['stage']
                    and receipt.get('output_scope_sha256') == SCOPE_SHA256,
                    'Independent readiness review missing')
        else:
            require(receipt.get('independent_preservation') is True,
                    'Independent recovery preservation missing')
    return expected


def workspace(environ):
    run_id = environ.get('GITHUB_RUN_ID', '')
    require(re.fullmatch('[1-9][0-9]*', run_id) is not None,
            'Run identity absent')
    root = Path(environ['RUNNER_TEMP'])
    require(root.is_absolute() and root.is_dir()
            and not any(p.is_symlink() for p in (root, *root.parents)),
            'Runner scratch differs')
    return root / ('l1-gui-' + run_id)


def prepare(control_path, decisions):
    """Freeze local prerequisites; this does not install or acquire inputs."""
    require(os.getuid() != 0 and not sys.flags.optimize,
            'Non-root assertions required')
    control = json.loads(regular(control_path).read_text())
    validate_control(control, os.environ, ROOT, decisions)
    require(pilot._command('git', 'rev-parse', 'HEAD')
            == control['source_commit'], 'Checkout differs')
    require(not pilot._command('git', 'status', '--porcelain',
                               '--untracked-files=no'),
            'Tracked source changed')
    work = workspace(os.environ)
    work.mkdir(mode=0o700)
    (work / 'evidence').mkdir(mode=0o700)
    write(work / 'control.json', control)
    write(work / 'preparation.json', {
        'status': 'PASS', 'decision_root': str(decisions),
        'control_sha256': digest(control_path),
        'source_commit': control['source_commit'],
    })
    return work


def prerequisites(work):
    """Recheck the same frozen authority at every process boundary."""
    require(work == workspace(os.environ), 'Workspace differs')
    control = json.loads(regular(work / 'control.json').read_text())
    record = json.loads(regular(work / 'preparation.json').read_text())
    decisions = Path(record['decision_root'])
    validate_control(control, os.environ, ROOT, decisions)
    require(pilot._command('git', 'rev-parse', 'HEAD')
            == control['source_commit'], 'Checkout differs')
    return control, decisions


def installer_source(source):
    """Keep installer ownership logic; narrow its frozen pins and deadline."""
    substitutions = (
        ('RUNTIME_SECONDS = 570', 'RUNTIME_SECONDS = 510'),
        ("('9min 30s', '570000000')", "('8min 30s', '510000000')"),
        ('started + 575, started + 595', 'started + 515, started + 535'),
        ('outer 600-second', 'outer 540-second'),
        (pilot.APP_COMMIT, APP_COMMIT),
        (pilot.RUNTIME_COMMIT, RUNTIME_COMMIT),
        ('test ! -e /home/richard\n'
         'sudo -n install -d -m 700 -o "$(id -u)" -g "$(id -g)" '
         '/home/richard\n', ''),
        ('ROOT = Path(__file__).resolve().parents[1]',
         'ROOT = Path(' + repr(str(ROOT)) + ')'),
    )
    for before, after in substitutions:
        require(source.count(before) == 1,
                'Frozen installer adaptation differs')
        source = source.replace(before, after, 1)
    flatpak = 'sudo -n flatpak '
    require(source.count(flatpak) == 4,
            'Frozen installer Flatpak command count differs')
    # Set the system export lookup after sudo resets the environment.
    source = source.replace(
        flatpak, 'sudo -n env XDG_DATA_DIRS=/var/lib/flatpak/exports/share:'
        '/usr/local/share:/usr/share flatpak ')
    return source


def install(work):
    """Run the source-bound installer inside its 540-second outer allowance."""
    prerequisites(work)
    deadline = time.monotonic() + 540
    path = ROOT / 'tools/hosted_l1_gui_install.py'
    original = path.read_text()
    adapted = installer_source(original)
    target = work / 'readiness_installer.py'
    with target.open('x', encoding='utf-8') as stream:
        stream.write(adapted)
    write(work / 'installer-adaptation.json', {
        'original_sha256': digest(path), 'copy_sha256': digest(target),
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
        acquire_bridge(work, deadline)
    return result


def acquire_bridge(work, deadline):
    """Acquire the existing pinned bridge within the installation allowance."""
    from tools import compatibility_gui_bridge as bridge

    def remaining():
        value = deadline - time.monotonic()
        require(value > 0, 'Bridge acquisition deadline expired')
        return value

    source = work / 'bridge-source'
    source.mkdir(mode=0o700)
    private_home = work / 'bridge-acquisition-home'
    private_home.mkdir(mode=0o700)
    clean = dict(bridge.BASE_ENV, HOME=str(private_home),
                 GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
    patch_path = ROOT / 'tools/freecad_bridge/freecad-cli-tracktemplate.patch'
    require(digest(patch_path) == bridge.PATCH_SHA256,
            'Bridge acquisition patch differs')
    commands = (
        ['init', str(source)],
        ['-C', str(source), 'fetch', '--depth=1', '--no-tags',
         'https://github.com/yoshikouki/freecad-cli.git',
         bridge.UPSTREAM_COMMIT],
        ['-C', str(source), 'checkout', '--detach', 'FETCH_HEAD'],
        ['-C', str(source), 'apply', str(patch_path)],
    )
    for command in commands:
        # Original diagnostics enter the existing, captured install streams.
        result = subprocess.run(
            ['/usr/bin/git', *command], env=clean,
            timeout=min(30, remaining()), check=False)
        require(result.returncode == 0, 'Pinned bridge acquisition failed')
        remaining()
    wheel = work / 'click-8.1.6-py3-none-any.whl'
    with urllib.request.urlopen(CLICK_URL, timeout=min(15, remaining())) as response:
        content = response.read(97910)
    require(len(content) == 97909
            and hashlib.sha256(content).hexdigest() == CLICK_SHA256,
            'Pinned Click wheel differs')
    with wheel.open('xb') as stream:
        stream.write(content)
    remaining()
    receipt = bridge.prepare_bridge(source, work / 'bridge', click_wheel=wheel)
    remaining()
    receipt['checkout_tests'] = bridge_checkout_tests(
        work, source, wheel, clean, deadline)
    write(work / 'bridge-preparation.json', receipt)


def bridge_checkout_tests(work, checkout, wheel, clean, deadline):
    """Run the existing 22 assertions with exact hosted path bindings."""
    original_path = ROOT / 'tools/freecad_bridge/test_freecad_cli_checkout.py'
    source = original_path.read_text()
    substitutions = (
        ('TOOL_ROOT = PROJECT_ROOT / ".devtools" / "freecad-cli"',
         'TOOL_ROOT = pathlib.Path(' + repr(str(checkout)) + ')'),
        ('"/usr/lib/python3/dist-packages"', repr(str(wheel))),
    )
    for before, after in substitutions:
        require(source.count(before) == 1, 'Bridge test source differs')
        source = source.replace(before, after, 1)
    copied = work / 'bridge-checkout-tests.py'
    with copied.open('x') as stream:
        stream.write(source)
    remaining = deadline - time.monotonic()
    require(remaining > 0, 'Bridge acquisition deadline expired')

    def preserve(stdout, stderr):
        for stream, value in ((sys.stdout, stdout), (sys.stderr, stderr)):
            if value:
                stream.buffer.write(value)
                stream.buffer.flush()

    try:
        result = subprocess.run(
            ['/usr/bin/python3', '-I', '-S', '-B', str(copied)], env=clean,
            capture_output=True, timeout=min(30, remaining), check=False)
    except subprocess.TimeoutExpired as error:
        preserve(error.stdout, error.stderr)
        raise
    preserve(result.stdout, result.stderr)
    require(result.returncode == 0 and result.stdout.splitlines().count(
        b'22 bridge tests passed') == 1, 'Existing bridge tests failed')
    require(time.monotonic() < deadline, 'Bridge acquisition deadline expired')
    return {'status': 'PASS', 'count': 22,
            'original_sha256': digest(original_path),
            'copy_sha256': digest(copied)}


def acquire(work, base_fixture):
    """Copy only the previously approved base and prepare isolated source."""
    from tools.prepare_runtime_assessment import prepare_assessment

    _, decisions = prerequisites(work)
    installation = json.loads(regular(
        work / 'evidence/installer-result.json').read_text())
    require(installation.get('status') == 'PASS'
            and installation.get('cleanup') is True,
            'Installer result or cleanup missing')
    base_fixture = regular(base_fixture)
    require(base_fixture.stat().st_size == 636344
            and digest(base_fixture) == BASE_SHA256,
            'Approved base identity differs')
    manifest = prepare_assessment(
        ROOT, decisions / 'assessment-inputs.json', base_fixture,
        work / 'assessment')
    write(work / 'assessment-manifest.json', manifest)
    write(work / 'base-binding.json', {
        'sha256': BASE_SHA256, 'bytes': 636344,
        'external_models': 1, 'working_model_publication': False,
    })


def candidate_deployment(command=pilot._command):
    """Require exact system deployment commits immediately before launch."""
    expected = (
        command('flatpak', 'info', '--system', '--show-commit', guard.APP_ID),
        command('flatpak', 'info', '--system', '--show-runtime', guard.APP_ID),
        command('flatpak', 'info', '--system', '--show-commit', pilot.RUNTIME),
    )
    require(expected == (APP_COMMIT, pilot.RUNTIME, RUNTIME_COMMIT),
            'Candidate deployment differs')
    return {'app_commit': expected[0], 'runtime_commit': expected[2]}


def child_environment(work):
    """Pass fixed display settings and required host identifiers only."""
    names = ('PATH', 'HOME', 'USER', 'LOGNAME', 'LANG', 'XDG_RUNTIME_DIR',
             'DBUS_SESSION_BUS_ADDRESS', 'GITHUB_ACTIONS', 'GITHUB_SHA',
             'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'RUNNER_ENVIRONMENT')
    clean = {name: os.environ[name] for name in names if name in os.environ}
    clean.update(DISPLAY=':99', XAUTHORITY=str(work / 'display/Xauthority'),
                 QT_QPA_PLATFORM='xcb', LIBGL_ALWAYS_SOFTWARE='1',
                 GALLIUM_DRIVER='llvmpipe', OMP_NUM_THREADS='1',
                 OPENBLAS_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1',
                 PYTHONNODEBUGRANGES='1')
    return clean


def run(work):
    """Run one source-copy GUI proof with unchanged guard/display controls."""
    from tools.prepare_runtime_assessment import verify_assessment
    from tools import compatibility_gui_bridge as bridge

    control, _ = prerequisites(work)
    require(control['stage'] == 'readiness',
            'Acquisition diagnostic cannot execute a GUI proof')
    manifest = json.loads(regular(work / 'assessment-manifest.json').read_text())
    verify_assessment(work / 'assessment', manifest)
    memory = pilot.validate_admission(os.environ, Path('/proc/meminfo').read_text())
    require(memory['MemAvailable'] >= (4096 + 256 + 8192) * 1024**2,
            'FreeCAD, display and reserve exceed available memory')
    deployment = candidate_deployment()
    bridge.verify_bridge(work / 'bridge')
    write(work / 'evidence/deployment.json', deployment)
    output = work / 'payload'
    output.mkdir(mode=0o700)
    config = {
        'assessment_root': str(work / 'assessment'),
        'default_contract': str(ROOT / 'reference/contracts/'
                                'phase1-compatibility.json'),
        'output_root': str(output), 'source_commit': control['source_commit'],
        'entry_sha256': digest(ROOT / SUITE),
        'app_commit': APP_COMMIT, 'runtime_commit': RUNTIME_COMMIT,
        'bridge_root': str(work / 'bridge'),
        'bridge_adapter': str(ROOT / 'tools/compatibility_gui_bridge.py'),
        'bridge_adapter_sha256': digest(
            ROOT / 'tools/compatibility_gui_bridge.py'),
        'guard_evidence': str(work / 'evidence/guard'),
        'bridge_receipt': str(work / 'bridge-readiness.json'),
    }
    write(work / 'suite-config.json', config)
    macro = work / 'readiness-entry.FCMacro'
    content = (
        'import sys, linecache, types\n'
        'sys.dont_write_bytecode = True\n'
        f'source = open({str(ROOT / SUITE)!r}, encoding="utf-8").read()\n'
        f'linecache.cache[{SUITE!r}] = (len(source), None, '
        f'source.splitlines(True), {SUITE!r})\n'
        'suite = types.ModuleType("hosted_compatibility_readiness_suite")\n'
        f'suite.__file__ = {str(ROOT / SUITE)!r}\n'
        f'exec(compile(source, {SUITE!r}, "exec"), suite.__dict__)\n'
        f'suite.start({str(work / "suite-config.json")!r}, '
        f'{digest(work / "suite-config.json")!r}, launcher_name=__name__)\n'
    )
    with macro.open('x', encoding='utf-8') as stream:
        stream.write(content)
    write(work / 'evidence/macro.json', {
        'sha256': digest(macro), 'bytes': macro.stat().st_size})
    display_samples, host_samples = [], []
    result = None
    assessment = {'status': 'FAIL', 'runtime_admission': False,
                  'matrix_dispatch': False, 'zy_execution': False}
    ownership = ExitStack()
    try:
        lease = ownership.enter_context(guard.acquire_validation_lease(
            Path(os.environ['XDG_RUNTIME_DIR'])))
        with patch.object(pilot, 'OUTPUT', work / 'evidence'):
            require(pilot._clearance(), 'Foreign FreeCAD instance')
        with patch.dict(os.environ, {'L1_GUI_STAGE': 'readiness',
                                    'TRACKTEMPLATE_GUI_WORKLOAD': 'l1'}):
            owner = gui.start_display(work)
        group = gui._display_group(owner)

        def observe():
            sample = guard._sample(group)
            display_samples.append(sample)
            with (work / 'evidence/display-samples.jsonl').open('a') as stream:
                stream.write(json.dumps(sample) + '\n')
            host = pilot._memory(Path('/proc/meminfo').read_text())
            host['memory_pressure'] = Path('/proc/pressure/memory').read_text()
            host_samples.append(host)
            with (work / 'evidence/host.jsonl').open('a') as stream:
                stream.write(json.dumps(host) + '\n')
            require(host['MemAvailable'] >= 8192 * 1024**2,
                    'Host reserve lost')

        pressure_failed = False

        def sleep(seconds):
            nonlocal pressure_failed
            try:
                observe()
            except (OSError, ValueError):
                # The first observation failure stops work. During guard
                # cleanup, sampling must not interrupt owned process removal.
                if not pressure_failed:
                    pressure_failed = True
                    raise guard.GuardFailure('host-pressure-unproved') from None
            time.sleep(seconds)

        observe()
        clean = child_environment(work)
        argv, clean = bridge.session_command(
            work / 'bridge', work / 'assessment', clean,
            execution_seconds=LIMITS.timeout_seconds, macro=macro)
        result = guard.run_guarded_flatpak(
            argv, limits=LIMITS, evidence_dir=work / 'evidence/guard',
            lease=lease, context=guard.GuardContext(sleep=sleep),
            cwd=work / 'assessment', env=clean, isolate_profile=True)
        observe()
        with patch.object(pilot, 'OUTPUT', work / 'evidence'):
            cleared = (pilot._deadline_clearance(result)
                       and pilot._clearance())
        guard_dir = work / 'evidence/guard'
        stdout = (guard_dir / 'stdout').read_text()
        samples = [json.loads(line) for line in (
            guard_dir / 'measurements.jsonl').read_text().splitlines()]
        # Reuse resource assessment, then separately require the GUI proof.
        resources = pilot.assess_result(
            result, stdout, (guard_dir / 'stderr').read_text(), samples,
            cleared, deadline_clearance=cleared,
            workload='runtime-observation')
        require(resources['status'] == 'PASS',
                'Runtime resource assessment failed')
        gui.assess_display(display_samples)
        entry_lines = [line.removeprefix(
            'TRACKTEMPLATE_COMPATIBILITY_READINESS_ENTRY=')
            for line in stdout.splitlines()
            if line.startswith('TRACKTEMPLATE_COMPATIBILITY_READINESS_ENTRY=')]
        require(len(entry_lines) == 1 and json.loads(entry_lines[0]) == {
            'launcher_name': '__main__',
            'suite_name': 'hosted_compatibility_readiness_suite',
            'entry_sha256': control['source_files'][SUITE],
        }, 'Actual readiness invocation differs')
        require(stdout.splitlines().count(SENTINEL) == 1,
                'Readiness sentinel missing or repeated')
        raw = json.loads((work / 'readiness-observation.json').read_text())
        require(raw.get('status') == 'PASS', 'GUI readiness failed')
        bridge_record = json.loads(regular(
            work / 'bridge-readiness.json').read_text())
        require(bridge_record.get('status') == 'PASS'
                and bridge_record.get('sentinel') == bridge.SENTINEL,
                'Bridge readiness failed')
        verify_assessment(work / 'assessment', manifest)
        require(digest(ROOT / 'reference/contracts/'
                       'phase1-compatibility.json') == DEFAULT_SHA256,
                'Canonical contract changed')
        resources.pop('scope', None)
        resources['scope'] = (
            'Guard resources and runtime observation only. Separate GUI '
            'readiness opens and closes one approved synthetic base copy.')
        assessment.update(status='PASS', resource_assessment=resources,
                          sentinel=SENTINEL, bridge=bridge_record)
        assessment['bridge_checkout_tests'] = json.loads(regular(
            work / 'bridge-preparation.json').read_text())['checkout_tests']
    finally:
        cleanup = gui.display_cleanup(work)
        ownership.close()
        write(work / 'evidence/display-cleanup.json', cleanup)
        assessment['display_cleanup'] = cleanup['cleanup']
        assessment['freecad_cleanup'] = bool(result and result.get('cleanup_proved'))
        if not cleanup['cleanup'] or not assessment['freecad_cleanup']:
            assessment['status'] = 'FAIL'
        write(work / 'evidence/readiness-assessment.json', assessment)
    return 0 if assessment['status'] == 'PASS' else 1


def seal(work):
    """Project only approved readiness payloads after actual cleanup proof.

    Operational logs remain separate. This does not upload either tree.
    """
    from tools import compatibility_evidence_output as output

    control, decisions = prerequisites(work)
    require(control['stage'] == 'readiness',
            'Acquisition diagnostic cannot seal readiness outputs')
    assessment = json.loads(regular(
        work / 'evidence/readiness-assessment.json').read_text())
    require(assessment.get('status') in ('PASS', 'FAIL')
            and assessment.get('display_cleanup') is True
            and assessment.get('freecad_cleanup') is True,
            'Readiness status and cleanup required for sealing')
    scope = output.load_scope_capsule(decisions / 'output-scope.json', ROOT)
    scope = output.bind_assessment_source(
        scope, 'readiness', SUITE, ROOT / SUITE,
        control['source_files'][SUITE])
    observation = json.loads(regular(
        work / 'readiness-observation.json').read_text())
    if assessment['status'] != 'PASS':
        observation['status'] = 'FAIL'
        observation['sentinel'] = ''
    guard_result = json.loads(regular(
        work / 'evidence/guard/result.json').read_text())
    require(type(guard_result.get('process_exit')) is int
            and guard_result.get('cleanup_proved') is True,
            'Guard process completion missing')
    observation['returncode'] = guard_result['process_exit']
    # The guard attests the complete owned cgroup, including descendants.
    observation['cleanup'] = {
        'owned_pids': [], 'remaining_pids': [], 'complete': True,
    }
    payload = work / 'payload'
    record = output.build_result(scope, 'readiness', observation, payload)
    write(payload / 'gui/readiness/result.json', record)
    inventory = output.seal_outputs(
        scope, payload, work / 'public-readiness', ['readiness'],
        {'readiness': observation})
    write(work / 'readiness-payload-inventory.json', inventory)
    return inventory


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('prepare', 'install', 'acquire', 'run', 'seal'))
    parser.add_argument('--control', type=Path)
    parser.add_argument('--decisions', type=Path)
    parser.add_argument('--base', type=Path)
    arguments = parser.parse_args(argv)
    if arguments.stage == 'prepare':
        require(arguments.control is not None and arguments.decisions is not None,
                'Control and decisions required')
        prepare(arguments.control, arguments.decisions)
        return 0
    work = workspace(os.environ)
    if arguments.stage == 'install':
        return install(work)
    if arguments.stage == 'acquire':
        require(arguments.base is not None, 'Approved base required')
        acquire(work, arguments.base)
        return 0
    if arguments.stage == 'seal':
        seal(work)
        return 0
    return run(work)


if __name__ == '__main__':
    raise SystemExit(main())
