#!/usr/bin/env python3
"""Compose the fixed compatibility matrix without granting admission.

Only the reviewed assessment copies execute. Original assertions, paired
comparisons and receipts remain authoritative. One deadline includes every
generation, native, GUI, inter-entry and cleanup operation. This module
does not upload documents or evidence, dispatch Actions, retry or resume.
"""

import argparse
from contextlib import ExitStack, contextmanager, nullcontext
from dataclasses import dataclass
import difflib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import runpy
import signal
import stat
import subprocess
import sys
import time
import traceback
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import freecad_validation_guard as guard  # noqa: E402
from tools import compatibility_gui_bridge as bridge  # noqa: E402
from tools import hosted_compatibility_readiness as readiness  # noqa: E402
from tools import hosted_l1_gui_validation as gui  # noqa: E402
from tools import hosted_native_geometry_pilot as pilot  # noqa: E402
from tools import runtime_compatibility_diagnostics as diagnostics  # noqa: E402
from tools import prepare_runtime_assessment as assessment  # noqa: E402


CAPSULE = 'tests/fixtures/runtime-compatibility-execution.json'
CAPSULE_SHA256 = (
    'ea3f7ca505babc03e0c98dc1c732d7daf379d959af76911dfff02f59f2367472'
)
CAPSULE_BYTES = 36561
HEAVY_SECONDS = 7200
READINESS_COMMIT = '33d76895d236cded67c302c0b48faebf26c9d238'
READINESS_SOURCE_FILES = {
    '.github/workflows/native-geometry-pilot.yml':
        '6f3268e3b120097c598201979f874b19d0544af68e6970ae792b5b1628bb85c6',
    'tests/hosted_compatibility_readiness_suite.py':
        '2e7877ed80afcb0d72b6255071c558ff07f12b7077929106a3d62ae931b46f94',
    'tests/hosted_l1_gui_suite.py':
        '1150aab0a68d75a9048bbfd096f60f270d8f452c7333ab692ba063fd878e7012',
    'tests/validate_bounded_freecad.py':
        'cc0d6ef2b3a7a6fd675f268c8364b65deb3b69c76169ddd1c02a6c9853177daf',
    'tests/validate_compatibility_evidence_output.py':
        '7f20c226d7e5eae6dd02e5b1bbd1c683926d789a0d590a23521f6fcb40710166',
    'tests/validate_compatibility_gui_bridge.py':
        '3e39c7f7283f1607e2fda9b0ec19f2a39a71b6d1b8be5cdb3de6ee4a6eabba63',
    'tests/validate_compatibility_readiness_transport.py':
        '0f875646bc3bb7bb1350cfbb02c36f13059f1b428abf3a67e9eee8623fb511dc',
    'tests/validate_hosted_compatibility_readiness.py':
        '6d77e5bf9640e60dc7b4f3b41b85ad42552c40d8423d1bb14a907a85818a29c3',
    'tests/validate_hosted_native_geometry.py':
        '80e9e404d369500a112fc0d40ac2f21ae4d5e5d97e4b51e1e97becd3e243c20b',
    'tests/validate_runtime_assessment.py':
        '3dc552d2591df0cd36726e3f4b660b5b1defd72674e415919aaf26e5631fdc27',
    'tools/compatibility_evidence_output.py':
        'c2ea333aa853a037cd88d5a74f500d197bc3a3c0371ac09dd005992e7f4d1e05',
    'tools/compatibility_gui_bridge.py':
        '69fda253834c4c851dab1afd77fc384da2ca1eb7d16493d84abc9c46ed9d073f',
    'tools/compatibility_readiness_transport.py':
        'c1f43dd3be3ea27f2692c3eab408c2a7a7ef9dc2efe2930195c89af4be05c6f9',
    'tools/development_toolchain_preflight.py':
        'cac71b02e77c2b773d18fc542fa69a4feb2f5781ce45b49c4aebc9dbb4abf9de',
    'tools/freecad_bridge/freecad-cli-tracktemplate.patch':
        '5914ae4390e2b2e242f65feeb35b21685b5492c11015a01f5ba5ccc26fa8bdf9',
    'tools/freecad_bridge/test_freecad_cli_checkout.py':
        '1b8eea4e932b7b3b6e8e6394cedc1630abeb1b8116d8c8a939d8ec4f2d63bc38',
    'tools/freecad_validation_guard.py':
        '1c8c68350f82133d282e5a79914e44be8b6a5dbf564f7f261448e0e9c66b41f2',
    'tools/hosted_compatibility_readiness.py':
        '2d9f96acbc32e0b25ea06134777b81355acab038cf39182ef7caebe78a933633',
    'tools/hosted_l1_gui_install.py':
        '9584375a98db49b974a7631e049ddc5a4b5b3cbfb85aaa9f622ad8ea60a07849',
    'tools/hosted_l1_gui_validation.py':
        '33bb6f418e26575e195b143727f094c69883fac810c59e589f0ce4d5434c81ab',
    'tools/hosted_l1_private_validation.py':
        'b5d1c72636045310eb90d5616fd773e50ebd86173bf85a7fb29d43c5872b0b91',
    'tools/hosted_native_geometry_pilot.py':
        '22864b20ca207a3a3345f3498f6169129c464f0f27280e945049c58889a8b276',
    'tools/prepare_runtime_assessment.py':
        '5200b4369d651f41e2e1b0ba339b6cfa657d90df05be60146468d3025e73c3c0',
}
# The readiness job and its four inputs remain byte-exact. These two
# reviewed successors add only the qualification sibling and its test.
READINESS_DERIVATIVES = {
    '.github/workflows/native-geometry-pilot.yml': (
        '6f3268e3b120097c598201979f874b19d0544af68e6970ae792b5b1628bb85c6',
        'a1532a178aaab244d236f76140ca3e53be4894bcff9a457eb39219ba1609b001'),
    'tests/validate_hosted_native_geometry.py': (
        '80e9e404d369500a112fc0d40ac2f21ae4d5e5d97e4b51e1e97becd3e243c20b',
        '002c7e1cb4b0b2cac80fdcd8f4e65613b603401998cbee27ccbcf90fec42b09f'),
}
CONTROL_FILES = tuple(dict.fromkeys((*readiness.CONTROL_FILES,
    'tools/hosted_runtime_compatibility.py',
    'tests/validate_hosted_runtime_compatibility.py', CAPSULE,
    'tools/compatibility_gui_bridge.py',
    'tests/validate_compatibility_gui_bridge.py',
    'tools/runtime_compatibility_transport.py',
    'tests/validate_runtime_compatibility_transport.py',
    'tools/runtime_compatibility_observations.py',
    'tests/validate_runtime_compatibility_observations.py',
    'tools/runtime_compatibility_diagnostics.py',
    'tests/validate_runtime_compatibility_diagnostics.py',
)))
SERIES = {
    'phase3-four-routes': (
        'tools/freecad_bridge/run_phase3_transition_workflow_series.py',
        '774dbce2abeea7b22f9738f19bf9adb03efb7ae1ec6c4f4383a2265a2e744a9e',
    ),
    'phase7-export-pair': (
        'tools/freecad_bridge/run_phase7_core_layout_export_workflow.py',
        'b8fc72c5c1e21de5f3423081a9d046b896670ace8988d2a5ac161e997b9ee99c',
    ),
}
ENTRY_MARKER = 'TRACKTEMPLATE_MATRIX_ENTRY='
DONE_MARKER = 'TRACKTEMPLATE_MATRIX_ENTRY_COMPLETE'
SENTINEL = 'TRACKTEMPLATE_RUNTIME_COMPATIBILITY_MATRIX_PASS'
NATIVE07_STAGE = 'native07-check'
NATIVE07_SENTINEL = 'TRACKTEMPLATE_RUNTIME_COMPATIBILITY_NATIVE07_PASS'
NATIVE07_REENTRY_REFUSAL = 'TRACKTEMPLATE_NATIVE07_REENTRY_REFUSED'
NATIVE07_FIRST_FAILURE = 'TRACKTEMPLATE_NATIVE07_FIRST_FAILURE='
NATIVE07_OWNER_STATEMENT_SHA256 = (
    'a171b02a052f923073edb82a1b967c22655f30e92e6d947ccccd62c0400af4ae'
)
_NATIVE07_INVOCATION_CLAIM = 'native07-invocation-claim'
_NATIVE07_REFUSAL_WITNESS = 'native07-reentry-refused'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(path):
    raw = assessment._read_regular(Path(path))
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(path, value):
    """Preserve one new receipt; never replace earlier evidence."""
    path = Path(path)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def load_execution_capsule(path, source_root):
    """Load only the fixed public projection of the approved matrix."""
    require(identity(path) == {
        'bytes': CAPSULE_BYTES, 'sha256': CAPSULE_SHA256,
    }, 'Execution capsule changed')
    capsule = json.loads(Path(path).read_text())
    original = json.loads((Path(source_root) /
        'tests/fixtures/runtime-assessment-inputs.json').read_text())
    require(capsule['source_commit'] == assessment.BASE_COMMIT,
            'Matrix source commit differs')
    for kind, count in (('native_entries', 57), ('gui_entries', 22)):
        rows = capsule[kind]
        require(len(rows) == count and [
            {key: row[key] for key in ('path', 'bytes', 'sha256')}
            for row in rows
        ] == original['matrix'][kind], 'Matrix source projection differs')
    require(sum(row['sessions'] for row in capsule['gui_entries']) == 26,
            'GUI session matrix differs')
    for entry in entries(capsule):
        require(identity(Path(source_root) / entry['path']) == {
            key: entry[key] for key in ('bytes', 'sha256')
        }, 'Matrix original source changed: ' + entry['id'])
    return capsule


def entries(capsule):
    return [capsule['generation'], *capsule['native_entries'],
            *capsule['gui_entries']]


def selected_entries(capsule, stage):
    """Select the exact execution scope of the reviewed control."""
    if stage == 'qualification':
        return tuple(entries(capsule))
    require(stage == NATIVE07_STAGE, 'Unknown compatibility execution scope')
    rows = tuple(row for row in entries(capsule) if row['id'] == 'native-07')
    require(len(rows) == 1, 'Native 07 row missing or repeated')
    entry = rows[0]
    require(entry['kind'] == 'native'
            and entry['path'] == 'tests/freecad_validate_phase3_transition_slice.py'
            and entry['arguments'] == [] and entry['sessions'] == 1
            and entry['timeout_seconds'] == 900,
            'Native 07 execution scope differs')
    return rows


def adapt_series(manifest, tree):
    """Replace two exact launch sites; retain their original comparisons.

    The callback is supplied only when the controller invokes these exact
    series. It validates every command argument before starting a session.
    No subprocess module or client implementation is monkeypatched.
    """
    changed = json.loads(json.dumps(manifest))
    extra_diff = []
    for name, original_hash in SERIES.values():
        row = next(item for item in changed['source_files']
                   if item['path'] == name)
        require(row['original']['sha256'] == original_hash,
                'Series original source changed')
        path = Path(tree) / name
        before = path.read_text()
        require(identity(path) == row['assessment'],
                'Series assessment source changed')
        require(before.count('completed = subprocess.run(') == 1,
                'Series launch site differs')
        after = before.replace('completed = subprocess.run(',
                               'completed = _hosted_route(', 1)
        path.write_text(after)
        row['assessment'] = identity(path)
        row['adapted'] = True
        extra_diff.extend(difflib.unified_diff(
            before.splitlines(keepends=True), after.splitlines(keepends=True),
            fromfile='assessment/' + name, tofile='hosted/' + name))
    path = Path(tree) / '_assessment/adaptations.diff'
    path.write_text(path.read_text() + ''.join(extra_diff))
    changed['adaptation_diff'] = identity(path)
    (Path(tree) / '_assessment/manifest.json').write_bytes(
        assessment._json_bytes(changed))
    assessment.verify_assessment(tree, changed)
    return changed


def prepare_matrix(source_root, decision_capsule, base_fixture, destination):
    """Create exclusive source-bound scratch without starting a process."""
    source_root = Path(source_root).resolve()
    destination = Path(destination).absolute()
    require('..' not in destination.parts, 'Matrix destination parent traversal')
    require(not destination.exists() and not destination.is_symlink(),
            'Matrix destination already exists')
    require(destination.parent.is_dir()
            and not any(p.is_symlink() for p in destination.parents),
            'Matrix destination parent differs')
    capsule = load_execution_capsule(source_root / CAPSULE, source_root)
    destination.mkdir(mode=0o700)
    manifest = assessment.prepare_assessment(
        source_root, decision_capsule, base_fixture, destination / 'assessment')
    write(destination / 'original-assessment-manifest.json', manifest)
    manifest = adapt_series(manifest, destination / 'assessment')
    manifest, diagnostic_receipt = diagnostics.adapt_diagnostics(
        destination / 'assessment', manifest)
    write(destination / 'diagnostic-preparation.json', diagnostic_receipt)
    write(destination / 'assessment-manifest.json', manifest)
    write(destination / 'execution.json', capsule)
    preparation = {
        'schema_version': 1, 'status': 'PREPARED_NOT_EXECUTED',
        'capsule': identity(source_root / CAPSULE),
        'assessment_manifest': identity(destination / 'assessment-manifest.json'),
        'original_assessment_manifest': identity(
            destination / 'original-assessment-manifest.json'),
        'base': identity(base_fixture),
        'diagnostic_preparation': identity(
            destination / 'diagnostic-preparation.json'),
        'counts': {'generation': 1, 'native': 57, 'gui_groups': 22,
                   'gui_sessions': 26},
        'runtime_admission': False, 'zy_execution': False,
    }
    write(destination / 'preparation.json', preparation)
    return preparation


def verify_preparation(work, expected):
    """Check against caller-held preparation, never a self-declared hash."""
    work = Path(work)
    require(json.loads((work / 'preparation.json').read_text()) == expected,
            'Matrix preparation changed')
    require(identity(work / 'assessment-manifest.json')
            == expected['assessment_manifest'], 'Assessment manifest changed')
    require(identity(work / 'original-assessment-manifest.json')
            == expected['original_assessment_manifest'],
            'Original assessment provenance changed')
    require(identity(work / 'diagnostic-preparation.json')
            == expected['diagnostic_preparation'],
            'Diagnostic preparation changed')
    manifest = json.loads((work / 'assessment-manifest.json').read_text())
    require(json.loads((work / 'diagnostic-preparation.json').read_text())
            == manifest['diagnostic_successor'],
            'Diagnostic manifest binding changed')
    assessment.verify_assessment(work / 'assessment', manifest)
    return manifest


def verify_source_members(tree, manifest):
    """Keep frozen source exact after original drivers create runtime output."""
    for row in manifest['source_files']:
        path = Path(tree) / row['path']
        require(identity(path) == row['assessment']
                and stat.S_IMODE(path.stat().st_mode) == row['mode'],
                'Immutable assessment source changed: ' + row['path'])
    base = manifest['base_fixture']
    require(identity(Path(tree) / base['path']) == {
        key: base[key] for key in ('bytes', 'sha256')
    }, 'Approved base changed')


@dataclass(frozen=True)
class Deadline:
    """One absolute monotonic deadline, with no renewal operation."""

    started: float
    expires: float

    def __post_init__(self):
        require(type(self.started) in (int, float)
                and math.isfinite(self.started)
                and self.expires == self.started + HEAVY_SECONDS,
                'Heavy deadline interval differs')

    @classmethod
    def start(cls, clock=time.monotonic):
        now = clock()
        require(type(now) in (int, float) and math.isfinite(now),
                'Invalid monotonic clock')
        return cls(now, now + HEAVY_SECONDS)

    def remaining(self, clock=time.monotonic):
        now = clock()
        require(type(now) in (int, float) and math.isfinite(now)
                and now >= self.started, 'Monotonic clock regressed')
        remaining = self.expires - now
        require(remaining > 0, 'Shared heavy deadline exhausted')
        return remaining

    def entry_seconds(self, entry, clock=time.monotonic):
        seconds = int(self.remaining(clock))
        if entry['timeout_seconds'] is not None:
            seconds = min(entry['timeout_seconds'], seconds)
        require(seconds > 0, 'No complete second remains for entry')
        return seconds


class ControllerWatchdog:
    """Enforce the same deadline on host comparisons without blocking cleanup.

    The existing guard independently enforces its contained processes.
    The one-shot alarm must not interrupt that guard's mandatory cleanup.
    After expiry, no entry may start and final cleanup cannot produce PASS.
    """

    def __init__(self, deadline):
        self.deadline = deadline
        self.protected = False
        self.expired = False
        self.previous = None

    def _expire(self, signum, frame):
        self.expired = True
        if not self.protected:
            raise ValueError('Shared heavy deadline exhausted')

    def __enter__(self):
        require(signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0),
                'An unrelated controller alarm is active')
        remaining = self.deadline.remaining()
        self.previous = signal.signal(signal.SIGALRM, self._expire)
        signal.setitimer(signal.ITIMER_REAL, remaining)
        return self

    def __exit__(self, *exception):
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, self.previous)

    @contextmanager
    def cleanup_safe(self):
        require(not self.protected, 'Nested guarded cleanup differs')
        self.protected = True
        try:
            yield
        finally:
            self.protected = False


def resolve_arguments(entry, base, straight_receipt=None, b4_receipt=None):
    values = {'{BASE}': base, '{STRAIGHT_RECEIPT}': straight_receipt,
              '{B4_RECEIPT}': b4_receipt}
    arguments = []
    for argument in entry['arguments']:
        if argument in values:
            require(values[argument] is not None, 'Required actual receipt absent')
            argument = str(values[argument])
        arguments.append(argument)
    return arguments


def original_receipt(stdout, prefix, root, suffix):
    """Capture one emitted original receipt within this owned assessment."""
    lines = [line[len(prefix):] for line in stdout.splitlines()
             if line.startswith(prefix)]
    require(len(lines) == 1, 'Original receipt witness missing or repeated')
    path = (Path(lines[0]) / suffix) if suffix else Path(lines[0])
    require(path.is_absolute() and '..' not in path.parts
            and path.is_relative_to(Path(root).absolute()),
            'Original receipt escaped owned scratch')
    identity(path)
    return path


def validate_generation(receipt, tree):
    """Retain the real same-run recipe for every straight-fixture consumer."""
    value = json.loads(Path(receipt).read_text())
    require(value['status'] == 'completed'
            and value['recipe_id'] == 'phase8-b14-straight-host-source-v1'
            and value['scenario'] == 'phase8-straight-host'
            and value['comparison_witness_sha256'] ==
            '496a64e43033a5b742d4c82b686ad1bc622508cc4eb6ce8ecadf4d7b9796944d'
            and value['recipe']['save_reopen']['semantic_sha256'] ==
            value['comparison_witness_sha256']
            and value['source_fixture_sha256'] == assessment.BASE_SHA256
            and value['source_fixture_sha256_after'] == assessment.BASE_SHA256
            and value['cleanup']['remaining'] == [],
            'Original generation proof incomplete')
    generated = Path(value['run_document'])
    require(generated.is_absolute() and '..' not in generated.parts
            and generated.is_relative_to(Path(tree).absolute())
            and generated.name == 'b14-long-straight-generated.FCStd',
            'Generated straight path differs')
    require(identity(generated)['sha256'] == value['run_document_sha256'],
            'Generated straight bytes changed')
    return generated


def validate_entry(entry, result, stdout):
    """A process exit alone never proves an original entry ran."""
    require(result.get('status') == 'completed'
            and result.get('process_exit') == 0
            and result.get('cleanup_proved') is True,
            'Guarded entry or cleanup failed')
    require(sum(line.startswith(entry['sentinel'])
                for line in stdout.splitlines()) == 1,
            'Original entry sentinel missing or repeated')
    require(stdout.splitlines().count(DONE_MARKER) == 1,
            'Entry invocation completion missing')


def assess_session_resources(result, samples, seconds, clearance):
    """Require the existing pilot's complete resource proof for this entry.

    The matrix controller owns these duplicated numerical checks from
    hosted_native_geometry_pilot.assess_result. Retire the duplication only
    when a separately reviewed shared resource-only helper accepts variable
    entry deadlines without claiming a runtime-observation workload.
    """
    require(result.get('status') == 'completed'
            and result.get('process_exit') == 0
            and result.get('cleanup_proved') is True and clearance
            and not (result.get('failure_reason')
                     or result.get('execution_failure_reason')),
            'Session resource or cleanup outcome failed')
    require(result.get('deadline_cancellation_exit') in (0, 5),
            'Session deadline cancellation unproved')
    require(result.get('limits') == vars(guard.ValidationLimits(4096, seconds))
            and result.get('kernel_limits') == {
                'memory.max': str(4096 * 1024**2),
                'memory.high': str(4096 * 1024**2), 'memory.swap.max': '0',
                'cpu.max': '100000 100000', 'pids.max': '128'},
            'Session kernel limits differ')
    live, removed, final_accounting = [], False, False
    final = [result[key] for key in ('before_cleanup', 'after_cleanup')
             if isinstance(result.get(key), dict)]
    for sample in [*samples, *final]:
        if all(sample.get(key) is None for key in pilot.SAMPLE_FIELDS):
            removed = True
            continue
        require(not removed
                and all(sample.get(key) is not None
                        for key in pilot.SAMPLE_FIELDS),
                'Incomplete live session telemetry')
        values = {key: int(sample[key]) for key in (
            'memory.current', 'memory.peak', 'memory.swap.current',
            'pids.current')}
        require(all(value >= 0 for value in values.values()),
                'Negative session resource value')
        events = dict(line.split() for line in
                      sample['memory.events'].splitlines())
        require({'high', 'max', 'oom', 'oom_kill'} <= events.keys(),
                'Incomplete session memory events')
        require(not any(int(events.get(key, 0)) for key in (
                    'high', 'max', 'oom', 'oom_kill', 'oom_group_kill'))
                and values['memory.swap.current'] == 0
                and values['memory.peak'] <= 4096 * 1024**2
                and values['pids.current'] <= 128,
                'Session resource ceiling or memory event')
        cpu = dict(line.split() for line in sample['cpu.stat'].splitlines())
        values['cpu_usage_usec'] = int(cpu['usage_usec'])
        require(values['cpu_usage_usec'] >= 0, 'Negative session CPU value')
        live.append(values)
        if (any(sample is item for item in final)
                and values['pids.current'] == 0
                and not sample['cgroup.procs'].strip()
                and dict(line.split() for line in
                         sample['cgroup.events'].splitlines()).get(
                             'populated') == '0'):
            final_accounting = True
    require(bool(live), 'No complete owned session sample')
    return {'status': 'PASS',
            'peak_cgroup_memory_bytes': max(x['memory.peak'] for x in live),
            'peak_tasks_observed': max(x['pids.current'] for x in live),
            'cpu_usage_usec': max(x['cpu_usage_usec'] for x in live),
            'complete_resource_samples': len(live),
            'resource_accounting': (
                'final' if final_accounting else 'sampled-lower-bound')}


@contextmanager
def script_arguments(arguments):
    before = sys.argv
    sys.argv = list(arguments)
    try:
        yield
    finally:
        sys.argv = before


@contextmanager
def assessment_imports(tree):
    """Keep original proof imports in their frozen assessment closure.

    Only the three project namespaces are replaced temporarily. FreeCAD,
    Qt, the bridge and the controller keep their existing references.
    Cached checkout modules cannot satisfy an assessment import.
    """
    namespaces = ('tools', 'tracktemplate', 'tests')

    def selected(name):
        return any(name == root or name.startswith(root + '.')
                   for root in namespaces)

    modules = {name: module for name, module in list(sys.modules.items())
               if selected(name)}
    path = sys.path[:]
    bytecode = sys.dont_write_bytecode
    for name in modules:
        del sys.modules[name]
    sys.path[:] = [str(tree), *(
        item for item in path if Path(item or os.getcwd()).resolve() != ROOT)]
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        for name in list(sys.modules):
            if selected(name):
                del sys.modules[name]
        sys.modules.update(modules)
        sys.path[:] = path
        sys.dont_write_bytecode = bytecode


def runtime_observation(tree):
    """Measure this GUI process; keep default rejection and candidate pins."""
    from tools.compatibility_evidence_output import RUNTIME

    default = ROOT / assessment.CANONICAL_PATH
    candidate = Path(tree) / assessment.CANONICAL_PATH
    require(identity(default)['sha256'] == assessment.CANONICAL_SHA256
            and identity(candidate)['sha256'] == assessment.CANDIDATE_SHA256,
            'Runtime observation contract changed')
    with assessment_imports(tree):
        from tracktemplate.bootstrap import evaluate_runtime, runtime_record

        record = runtime_record()
        original = evaluate_runtime(record, json.loads(default.read_text()))
        actual = evaluate_runtime(record, json.loads(candidate.read_text()))
    require(original['status'] == 'unqualified'
            and actual['status'] == 'qualified'
            and actual['matched_profile_id'] == assessment.CANDIDATE_PROFILE
            and actual['mismatches'] == [], 'Actual matrix runtime differs')
    result = {
        'freecad': record['freecad']['version_info'],
        'python': record['python']['version_info'],
        'pyside': record['freecad']['pyside_version'],
        'qt': record['freecad']['qt_version'],
        'occt': record['freecad']['opencascade_version'],
        'coin': record['freecad']['coin_version'],
        'app_commit': readiness.APP_COMMIT,
        'runtime_commit': readiness.RUNTIME_COMMIT,
    }
    require(result == RUNTIME, 'Observed runtime tuple differs')
    return result


def verify_readiness_sources(receipt, pins, source_root):
    """Accept exact prerequisites or the one reviewed sibling-job addition.

    This is not a semantic YAML comparison or an approval flag. Every
    successor byte is pinned, and reversing only its finite additions must
    recover the exact original readiness source. Any further edit refuses.
    """
    required = set(readiness.CONTROL_FILES)
    before = receipt['source_files']
    require(type(before) is dict and set(before) == required,
            'Readiness source inventory differs')
    changed = {name for name in required if before[name] != pins[name]}
    if not changed:
        return
    require(receipt['source_commit'] == READINESS_COMMIT
            and before == READINESS_SOURCE_FILES
            and changed == set(READINESS_DERIVATIVES),
            'Readiness source differs from matrix prerequisites')
    for name, (original_hash, successor_hash) in READINESS_DERIVATIVES.items():
        raw = readiness.regular(Path(source_root) / name).read_bytes()
        require(before[name] == original_hash and pins[name] == successor_hash
                and hashlib.sha256(raw).hexdigest() == successor_hash,
                'Readiness derivative source identity changed')
        if name.endswith('.yml'):
            marker = b'\n  compatibility-matrix:\n'
            require(raw.count(marker) == 1,
                    'Qualification sibling job boundary changed')
            original = raw.split(marker, 1)[0]
            additions = (
                (b'          - compatibility-qualification\n', b''),
                (b"      inputs.workload != 'compatibility-readiness' &&\n"
                 b"      inputs.workload != 'compatibility-qualification'\n",
                 b"      inputs.workload != 'compatibility-readiness'\n"),
            )
        else:
            original = raw
            additions = ((b'            "- compatibility-qualification",\n',
                          b''),)
        for added, prior in additions:
            require(original.count(added) == 1,
                    'Exact qualification addition changed')
            original = original.replace(added, prior, 1)
        require(hashlib.sha256(original).hexdigest() == original_hash,
                'Original readiness source could not be reconstructed')


def validate_control(control, receipts, environment, source_root):
    """Require exact reviewed sources, recovery and actual hosted readiness."""
    require(type(control) is dict, 'Exact matrix control fields required')
    stage = control.get('stage')
    require(stage in ('qualification', NATIVE07_STAGE),
            'Unknown compatibility execution scope')
    owner_statement_sha256 = (
        NATIVE07_OWNER_STATEMENT_SHA256 if stage == NATIVE07_STAGE else
        'd193c34674fa4eb09de4ccaad6a6ddfbf1a930fdd50f369652f33204e2daa19a'
    )
    fixed = {
        'schema_version': 1, 'stage': stage,
        'owner_decision': 'D-P9-024',
        'owner_statement_sha256': owner_statement_sha256,
        'output_scope_sha256': readiness.SCOPE_SHA256,
        'app_commit': readiness.APP_COMMIT,
        'runtime_commit': readiness.RUNTIME_COMMIT,
        'capsule_sha256': CAPSULE_SHA256,
        'heavy_seconds': 7200, 'display_seconds': 7300,
        'outer_seconds': 8400, 'installer_seconds': 540,
        'readiness_seconds': 90, 'memory_mib': 4096, 'reserve_mib': 8192,
        'cpu_percent': 100, 'tasks': 128, 'swap_bytes': 0,
        'parallel': False, 'retry': False, 'runtime_admission': False,
        'zy_execution': False,
    }
    require(set(control) == set(fixed) | {
        'source_commit', 'source_files', 'review', 'recovery', 'readiness'},
        'Exact matrix control fields required')
    require(all(type(control[k]) is type(v) and control[k] == v
                for k, v in fixed.items()), 'Matrix authority or limits differ')
    expected_environment = {
        'GITHUB_ACTIONS': 'true',
        'GITHUB_REPOSITORY': 'Richard-Gnitnub/tracktemplate',
        'GITHUB_EVENT_NAME': 'workflow_dispatch',
        'RUNNER_ENVIRONMENT': 'github-hosted', 'GITHUB_RUN_ATTEMPT': '1',
        'RUNNER_OS': 'Linux', 'RUNNER_ARCH': 'X64',
    }
    require(all(environment.get(k) == v
                for k, v in expected_environment.items()),
            'Hosted first-attempt matrix required')
    require(not any(environment.get(k, '').lower() in ('1', 'true') for k in (
        'RUNNER_DEBUG', 'ACTIONS_STEP_DEBUG', 'ACTIONS_RUNNER_DEBUG')),
        'Debug logging refused')
    require(re.fullmatch('[0-9a-f]{40}', control['source_commit']) is not None
            and control['source_commit'] == environment.get('GITHUB_SHA'),
            'Dispatched matrix source differs')
    pins = control['source_files']
    require(type(pins) is dict and set(pins) == set(CONTROL_FILES),
            'Complete matrix source review required')
    for name, digest in pins.items():
        require(identity(Path(source_root) / name)['sha256'] == digest,
                'Reviewed matrix source changed')
    require(identity(Path(source_root) / assessment.CANONICAL_PATH)['sha256']
            == assessment.CANONICAL_SHA256, 'Canonical contract changed')
    for key in ('review', 'recovery', 'readiness'):
        binding = control[key]
        require(type(binding) is dict and set(binding) == {'path', 'sha256'}
                and binding['path'] == key + '.json',
                'Exact matrix prerequisite binding required')
        path = Path(receipts) / binding['path']
        require(identity(path)['sha256'] == binding['sha256'],
                'Matrix prerequisite changed')
        receipt = json.loads(path.read_text())
        common = {'status', 'source_commit', 'source_files'}
        if key == 'review':
            require(set(receipt) == common | {
                'independent', 'stage', 'output_scope_sha256'},
                'Exact matrix review required')
            require(receipt['independent'] is True
                    and receipt['stage'] == stage
                    and receipt['output_scope_sha256'] == readiness.SCOPE_SHA256,
                    'Matrix review incomplete')
        elif key == 'recovery':
            require(set(receipt) == common | {'independent_preservation'}
                    and receipt['independent_preservation'] is True,
                    'Matrix preservation incomplete')
        else:
            require(set(receipt) == common | {
                'independent', 'stage', 'runtime', 'base_sha256',
                'candidate_sha256', 'artifact_sha256', 'run_id'},
                'Exact actual readiness review required')
            from tools.compatibility_evidence_output import RUNTIME

            require(type(receipt['source_commit']) is str
                    and re.fullmatch('[0-9a-f]{40}', receipt['source_commit']),
                    'Readiness source commit must be lowercase 40-hex')
            runtime = receipt['runtime']
            require(type(runtime) is dict and runtime == RUNTIME
                    and all(type(runtime[name]) is type(value)
                            for name, value in RUNTIME.items())
                    and all(type(part) is int for name in ('freecad', 'python')
                            for part in runtime[name]),
                    'Actual reviewed runtime field types or values differ')
            require(receipt['independent'] is True
                    and receipt['stage'] == 'readiness'
                    and receipt['base_sha256'] == assessment.BASE_SHA256
                    and receipt['candidate_sha256'] == assessment.CANDIDATE_SHA256
                    and re.fullmatch('[0-9a-f]{64}', receipt['artifact_sha256'])
                    and re.fullmatch('[1-9][0-9]*', receipt['run_id']),
                    'Actual reviewed runtime and bridge readiness missing')
            verify_readiness_sources(receipt, pins, source_root)
        require(receipt['status'] == 'PASS', 'Matrix prerequisite failed')
        if key != 'readiness':
            require(receipt['source_commit'] == control['source_commit']
                    and receipt['source_files'] == pins,
                    'Matrix review or recovery is for other source')
    return fixed


# The existing guard stderr may carry only fixed codes for this failure.
_NATIVE07_B15_DIAGNOSTIC = '''except Exception as error:
    load_error = error
    wrappers = (
        ("tools.phase3_transition_pilot", "TransitionPilotError"),
        ("tracktemplate.compatibility.transition_workflow",
         "TransitionWorkflowError"),
    )
    if any(type(error) is getattr(sys.modules.get(module), name, None)
           for module, name in wrappers):
        load_error = error.__cause__
    host = sys.modules.get("tracktemplate.compatibility.b15_workflow_host")
    if (type(load_error) is getattr(host, "B15WorkflowHostError", None)
            and load_error.args == ("The frozen B15 definitions could not load.",)
            and load_error.__cause__ is not None):
        cause = load_error.__cause__
        cause_types = (ValueError, ModuleNotFoundError, ImportError,
                       SyntaxError, TypeError, NameError, AttributeError,
                       KeyError, OSError, RuntimeError)
        cause_type = next((kind.__name__ for kind in cause_types
                           if type(cause) is kind), "Other")
        reason = "other"
        if (type(cause) is ValueError and len(cause.args) == 1
                and type(cause.args[0]) is str):
            reason = {
                "Diagnostic B15 original fingerprint differs": "fingerprint",
                "Diagnostic B15 loader AST differs": "loader-ast",
                "Diagnostic B15 console site differs": "console-site",
                "Diagnostic B15 console argument differs": "console-argument",
            }.get(cause.args[0], reason)
        try:
            print("TRACKTEMPLATE_NATIVE07_B15_LOAD_EXCEPTION=" + json.dumps({
                "cause_type": cause_type, "reason": reason,
            }), file=sys.stderr, flush=True)
        except (OSError, ValueError):
            pass
'''
NATIVE07_B15_FAILURE = _NATIVE07_B15_DIAGNOSTIC + '    raise\n'


_NATIVE07_INVOKE_ONCE = f'''def _claim_native07_invocation(name):
    path = os.path.join(config["session_directory"], name)
    os.close(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))


try:
    _claim_native07_invocation({_NATIVE07_INVOCATION_CLAIM!r})
except FileExistsError:
    try:
        _claim_native07_invocation({_NATIVE07_REFUSAL_WITNESS!r})
    except FileExistsError:
        pass
    finally:
        print({NATIVE07_REENTRY_REFUSAL!r}, file=sys.stderr, flush=True)
    raise SystemExit(1)
'''

_NATIVE07_CAPTURE_FAILURE = f'''def _fail_native07(error):
    categories = (
        AssertionError, AttributeError, FileNotFoundError, ImportError, KeyError,
        ModuleNotFoundError, NameError, OSError, RuntimeError, SyntaxError,
        SystemExit, TypeError, ValueError,
    )
    category = next((kind.__name__ for kind in categories
                     if type(error) is kind), "Other")
    original_line = None
    trace = BaseException.__traceback__.__get__(error)
    while trace is not None:
        if trace.tb_frame.f_code.co_filename == path and trace.tb_lineno > 0:
            original_line = trace.tb_lineno
        trace = trace.tb_next
    try:
        print({NATIVE07_FIRST_FAILURE!r} + json.dumps({{
            "exception_category": category, "original_line": original_line,
        }}), file=sys.stderr, flush=True)
    except (OSError, ValueError):
        pass
    raise SystemExit(1) from None


'''


def _native_source(config, *, native07_once=False):
    """Use the original script's real main invocation, including unittest."""
    require(not native07_once or config['id'] == 'native-07',
            'Native 07 one-shot wrapper requires the fixed entry')
    setup = ''
    failed_exit = '        raise\n'
    failure = NATIVE07_B15_FAILURE if config['id'] == 'native-07' else ''
    if native07_once:
        setup = (_NATIVE07_INVOKE_ONCE + _NATIVE07_CAPTURE_FAILURE
                 + 'sys.path.insert(0, os.path.dirname(path))\n')
        failed_exit = '        _fail_native07(error)\n'
        failure = _NATIVE07_B15_DIAGNOSTIC + '    _fail_native07(error)\n'
    return (
        'import hashlib, json, os, runpy, sys\n'
        'assert __debug__ and not sys.flags.optimize\n'
        f'config = {config!r}\n'
        'path = config["entry_path"]\n'
        'assert hashlib.sha256(open(path, "rb").read()).hexdigest() '
        '== config["entry_sha256"]\n'
        'sys.path.insert(0, config["assessment"])\n'
        'os.environ.update(config["fixture_environment"])\n'
        'sys.argv = [path, *config["arguments"]]\n'
        f'{setup}'
        f'print({ENTRY_MARKER!r} + json.dumps({{"id":config["id"], '
        '"sha256":config["entry_sha256"], "run_name":"__main__"}), '
        'flush=True)\n'
        'try:\n'
        '    runpy.run_path(path, run_name="__main__")\n'
        'except SystemExit as error:\n'
        '    if error.code not in (None, 0):\n'
        f'{failed_exit}'
        f'{failure}'
        f'print({DONE_MARKER!r}, flush=True)\n'
    )


def _verify_native07_invocation(directory):
    require(not os.path.lexists(directory / _NATIVE07_REFUSAL_WITNESS),
            'Native 07 wrapper re-entry refused')
    marker = readiness.regular(directory / _NATIVE07_INVOCATION_CLAIM)
    require(marker.stat().st_size == 0, 'Native 07 invocation claim differs')


def gui_entry(config, launcher_name):
    """Run one original proof while Qt remains responsive in its cgroup."""
    import FreeCAD as App
    from PySide6 import QtCore
    require(launcher_name == '__main__' and __debug__ and App.GuiUp,
            'Actual GUI main invocation required')
    directory = Path(config['session_directory'])
    # Embedded bridge proofs run in this FreeCAD process. The separate
    # driver receives these same values through its fixed entry wrapper.
    os.environ.update(config['fixture_environment'])
    guard_dir = directory / 'guard'
    state = {'timer': None, 'child': None, 'phase': 'probe', 'streams': []}

    def fail():
        with (directory / 'gui-failure.txt').open('x') as stream:
            traceback.print_exc(file=stream)
        state['timer'].stop()
        for stream in state['streams']:
            stream.close()
        QtCore.QCoreApplication.exit(1)

    def tick():
        try:
            require(time.monotonic() < config['deadline'],
                    'GUI absolute deadline exhausted')
            child = state['child']
            if child is None:
                state['child'] = bridge.launch_readiness_probe(
                    config['bridge'], directory / 'bridge-readiness.json',
                    deadline=config['deadline'], guard_evidence=guard_dir)
                return
            if child.poll() is None:
                return
            require(child.returncode == 0, 'Contained bridge or proof failed')
            if state['phase'] == 'proof':
                for stream in state['streams']:
                    stream.close()
                require(not App.listDocuments(), 'Proof left GUI documents open')
                print(DONE_MARKER, flush=True)
                state['timer'].stop()
                QtCore.QCoreApplication.quit()
                return
            proof = json.loads((directory / 'bridge-readiness.json').read_text())
            require(proof['status'] == 'PASS', 'Bridge readiness failed')
            write(directory / 'runtime-observation.json',
                  runtime_observation(config['assessment']))
            if config['kind'] == 'gui-main':
                require(identity(config['entry_path'])['sha256']
                        == config['entry_sha256'], 'GUI main source changed')
                sys.path.insert(0, config['assessment'])
                print(ENTRY_MARKER + json.dumps({
                    'id': config['id'], 'sha256': config['entry_sha256'],
                    'run_name': '__main__'}), flush=True)
                with assessment_imports(config['assessment']):
                    with script_arguments([config['entry_path']]):
                        runpy.run_path(config['entry_path'], run_name='__main__')
                require(not App.listDocuments(), 'GUI main left documents open')
                print(DONE_MARKER, flush=True)
                state['timer'].stop()
                QtCore.QCoreApplication.quit()
                return
            command = ['/usr/bin/python3', '-I', '-S', '-B',
                       str(directory / 'driver.py')]
            streams = [(directory / name).open('xb')
                       for name in ('client.stdout', 'client.stderr')]
            state['streams'] = streams
            ownership = json.loads((guard_dir / 'ownership.json').read_text())
            require(bridge._process_cgroup('self') == ownership['cgroup'],
                    'Proof parent escaped guard cgroup')
            state['child'] = subprocess.Popen(
                command, env=bridge.client_environment(),
                cwd=config['assessment'], stdin=subprocess.DEVNULL,
                stdout=streams[0], stderr=streams[1], close_fds=True)
            if (bridge._process_cgroup(state['child'].pid)
                    != ownership['cgroup']):
                state['child'].kill()
                state['child'].wait(timeout=5)
                raise ValueError('Proof child escaped guard cgroup')
            state['phase'] = 'proof'
        except BaseException:
            fail()

    state['timer'] = QtCore.QTimer()
    state['timer'].timeout.connect(tick)
    state['timer'].start(100)
    # Qt must retain this state after the macro returns.
    App._tracktemplate_matrix_session = state


def _gui_macro(config):
    return (
        'import importlib.util, sys\n'
        f'sys.path.insert(0, {str(ROOT)!r})\n'
        'from tools.hosted_runtime_compatibility import gui_entry\n'
        f'gui_entry({config!r}, __name__)\n'
    )


def _driver_source(config):
    paths = [str(Path(config['bridge']) / 'src'),
             str(Path(config['bridge']) / bridge.CLICK_WHEEL),
             config['assessment']]
    return f'import sys\nsys.path[:0] = {paths!r}\n' + _native_source(config)


class MatrixRunner:
    """Fixed original entries, serial fresh sessions and original receipts."""

    def __init__(self, work, manifest, bridge_root, lease, context, deadline,
                 watchdog=None, *, native07_once=False):
        self.work = Path(work)
        self.tree = self.work / 'assessment'
        self.manifest = manifest
        self.bridge = Path(bridge_root)
        self.lease, self.context, self.deadline = lease, context, deadline
        self.base = self.tree / assessment.BASE_PATH
        self.straight_receipt = self.straight = self.b4_receipt = None
        self.session_count = 0
        self.group_deadline = deadline.expires
        self.watchdog = watchdog
        self.native07_once = native07_once

    def _session(self, entry, arguments, directory):
        require(not self.native07_once or entry['id'] == 'native-07',
                'Unexpected entry in Native 07 check')
        self.deadline.remaining()
        verify_source_members(self.tree, self.manifest)
        directory.mkdir(mode=0o700, parents=True)
        seconds = min(self.deadline.entry_seconds(entry),
                      int(self.group_deadline - time.monotonic()))
        require(seconds > 0, 'Entry deadline exhausted before session')
        expires = min(self.deadline.expires, self.group_deadline,
                      time.monotonic() + seconds)
        source = self.tree / entry['path']
        fixture_environment = {diagnostics.SESSION_ENV: str(directory)}
        if self.straight is not None:
            fixture_environment.update({
                'TRACKTEMPLATE_STRAIGHT_TURNOUT_FIXTURE': str(self.straight),
                'TRACKTEMPLATE_STRAIGHT_CROSSOVER_FIXTURE': str(self.straight),
                'TRACKTEMPLATE_STRAIGHT_CROSSOVER_SOURCE_RECEIPT':
                    str(self.straight_receipt),
            })
        config = {
            'id': entry['id'], 'entry_path': str(source),
            'entry_sha256': identity(source)['sha256'],
            'kind': entry['kind'], 'arguments': arguments,
            'assessment': str(self.tree), 'bridge': str(self.bridge),
            'session_directory': str(directory), 'deadline': expires,
            'fixture_environment': fixture_environment,
        }
        write(directory / 'invocation.json', config)
        write(directory / 'input-before.json', identity(self.base))
        clean = readiness.child_environment(self.work)
        if entry['kind'] == 'native':
            # FreeCAD imports .py arguments and executes them again on error.
            macro = directory / ('entry.FCMacro' if self.native07_once
                                 else 'entry.py')
            macro.write_text(_native_source(
                config, native07_once=self.native07_once))
            argv = ['flatpak', 'run', '--command=FreeCADCmd']
            argv += [f'--env={name}={value}' for name, value in clean.items()
                     if name not in ('PATH', 'HOME', 'USER', 'LOGNAME', 'LANG',
                                     'XDG_RUNTIME_DIR',
                                     'DBUS_SESSION_BUS_ADDRESS')]
            argv += [guard.APP_ID, str(macro)]
        else:
            macro = directory / 'entry.FCMacro'
            macro.write_text(_gui_macro(config))
            (directory / 'driver.py').write_text(_driver_source(config))
            argv, clean = bridge.session_command(
                self.bridge, self.tree, clean,
                execution_seconds=seconds, macro=macro)
        try:
            with (self.watchdog.cleanup_safe() if self.watchdog
                  else nullcontext()):
                result = guard.run_guarded_flatpak(
                    argv, limits=guard.ValidationLimits(4096, seconds),
                    evidence_dir=directory / 'guard', lease=self.lease,
                    context=self.context, cwd=self.tree, env=clean,
                    isolate_profile=True, absolute_deadline=expires)
        finally:
            write(directory / 'input-after.json', identity(self.base))
        self.deadline.remaining()
        with patch.object(pilot, 'OUTPUT', directory / 'guard'):
            clearance = (pilot._deadline_clearance(result)
                         and pilot._clearance())
        write(directory / 'clearance.json', {'complete': clearance})
        require(clearance, 'Owned process or deadline cleanup unproved')
        samples = [json.loads(line) for line in (
            directory / 'guard/measurements.jsonl').read_text().splitlines()]
        resources = assess_session_resources(result, samples, seconds, clearance)
        write(directory / 'resource-assessment.json', resources)
        if self.native07_once:
            _verify_native07_invocation(directory)
        guard_stdout = (directory / 'guard/stdout').read_text()
        stdout = ((directory / 'client.stdout').read_text()
                  if entry['kind'] == 'gui-client' else guard_stdout)
        if entry['kind'] == 'gui-client':
            require(guard_stdout.splitlines().count(DONE_MARKER) == 1,
                    'GUI parent completion missing')
        witness = [json.loads(line[len(ENTRY_MARKER):])
                   for line in stdout.splitlines()
                   if line.startswith(ENTRY_MARKER)]
        require(witness == [{'id': entry['id'],
                             'sha256': config['entry_sha256'],
                             'run_name': '__main__'}],
                'Actual original main invocation differs')
        # Paired children have original completion records checked by the
        # unchanged parent series, rather than a new invented sentinel.
        if entry.get('paired_child'):
            require(result['status'] == 'completed'
                    and result['process_exit'] == 0
                    and result['cleanup_proved'] is True
                    and stdout.splitlines().count(DONE_MARKER) == 1,
                    'Original paired child failed')
        else:
            validate_entry(entry, result, stdout)
        diagnostic_streams = [
            readiness.regular(directory / name).read_text()
            for name in ('guard/stdout', 'guard/stderr',
                         'client.stdout', 'client.stderr')
            if (directory / name).exists()
        ]
        diagnostics.verify_private_reports(
            directory, entry['id'], diagnostic_streams, completed=True)
        self.deadline.remaining()
        verify_source_members(self.tree, self.manifest)
        self.session_count += 1
        return stdout, result

    def _series(self, entry, directory, arguments):
        calls = []
        expected_order = (
            [(workflow, route) for workflow in (
                'plain-line-edit', 'connected-straight')
             for route in ('legacy', 'modular')]
            if entry['id'] == 'phase3-four-routes'
            else [('export', route) for route in ('legacy', 'modular')])

        def route(command, *, cwd, check):
            require(cwd == self.tree and check is False
                    and type(command) is list
                    and all(type(item) is str for item in command),
                    'Unreviewed series dispatch')
            require(len(calls) < len(expected_order), 'Extra series route')
            if entry['id'] == 'phase3-four-routes':
                require(command[0] == str(self.tree /
                    'tools/freecad_bridge/run-phase3-transition-workflow'),
                    'Phase 3 wrapper differs')
                options = command[1:]
                path = 'tools/freecad_bridge/run_phase3_transition_workflow.py'
                flags = ['--base', '--workflow', '--route', '--run-dir',
                         '--timeout']
            else:
                prefix = [str(self.tree / 'tools/freecad_bridge/run-isolated'),
                    '/usr/bin/env', 'TRACKTEMPLATE_BRIDGE_PORT=19875',
                    'PYTHONPATH=' + str(self.tree / '.devtools/freecad-cli/src'),
                    '/usr/bin/python3', str(self.tree / entry['path'])]
                require(command[:6] == prefix, 'Phase 7 wrapper differs')
                options, path = command[6:], entry['path']
                flags = ['--route', '--base', '--run-dir', '--port', '--timeout']
            require(len(options) == 2 * len(flags)
                    and options[::2] == flags, 'Series route options differ')
            values = dict(zip(flags, options[1::2]))
            workflow = values.get('--workflow', 'export')
            require((workflow, values['--route']) == expected_order[len(calls)]
                    and values['--base'] == str(self.base)
                    and values.get('--port', '19875') == '19875'
                    and float(values['--timeout']) == 1200.0,
                    'Original series route or order differs')
            run_directory = Path(values['--run-dir'])
            require('..' not in run_directory.parts
                    and run_directory.is_relative_to(self.tree / 'benchmark-output')
                    and not run_directory.exists()
                    and not any(p.is_symlink() for p in run_directory.parents),
                    'Original route destination differs')
            child = dict(entry, path=path, kind='gui-client',
                         id=entry['id'] + '-route-' + str(len(calls) + 1),
                         sessions=1, timeout_seconds=1200, paired_child=True)
            stdout, result = self._session(
                child, options, directory / child['id'])
            calls.append({'id': child['id'], 'guard': result['receipt_path'],
                          'original': str(run_directory / 'run.json')})
            print(stdout, end='', flush=True)
            return subprocess.CompletedProcess(command, 0)

        source = self.tree / entry['path']
        directory.mkdir(mode=0o700)
        with (directory / 'series.stdout').open('x') as stdout:
            with (directory / 'series.stderr').open('x') as stderr:
                from contextlib import redirect_stderr, redirect_stdout

                with redirect_stdout(stdout), redirect_stderr(stderr):
                    with assessment_imports(self.tree), patch.dict(
                            os.environ,
                            {diagnostics.SESSION_ENV: str(directory)}):
                        with script_arguments([str(source), *arguments]):
                            runpy.run_path(str(source), run_name='__main__',
                                           init_globals={'_hosted_route': route})
                    require(len(calls) == entry['sessions'],
                            'Original series omitted sessions')
                    print(DONE_MARKER, flush=True)
        text = (directory / 'series.stdout').read_text()
        require(sum(line.startswith(entry['sentinel'])
                    for line in text.splitlines()) == 1,
                'Original series sentinel missing')
        write(directory / 'sessions.json', calls)
        return text

    def run_entry(self, entry):
        self.deadline.remaining()
        started = time.monotonic()
        self.group_deadline = self.deadline.expires
        if entry['timeout_seconds'] is not None:
            self.group_deadline = min(
                self.group_deadline, started + entry['timeout_seconds'])
        arguments = resolve_arguments(entry, self.base,
                                     self.straight_receipt, self.b4_receipt)
        directory = self.work / 'entries' / entry['id']
        before_sessions = self.session_count
        if entry['kind'] == 'series':
            stdout = self._series(entry, directory, arguments)
        else:
            stdout, _ = self._session(entry, arguments, directory)
        if entry['id'] == 'straight-generation':
            self.straight_receipt = original_receipt(
                stdout, entry['sentinel'], self.tree, 'run.json')
            self.straight = validate_generation(self.straight_receipt, self.tree)
        elif entry['path'].endswith('freecad_validate_phase8_straight_crossover_b4.py'):
            self.b4_receipt = original_receipt(
                stdout, 'PHASE8_STRAIGHT_CROSSOVER_B4_RECEIPT=', self.tree, '')
            value = json.loads(self.b4_receipt.read_text())
            require(value['source_receipt_sha256']
                    == identity(self.straight_receipt)['sha256'],
                    'B4 native receipt is not paired with same-run generation')
        self.deadline.remaining()
        return {
            'id': entry['id'], 'status': 'PASS',
            'sessions': self.session_count - before_sessions,
            'assessment_entry': identity(self.tree / entry['path']),
            'elapsed_seconds': time.monotonic() - started,
            'originals_directory': str(directory),
        }


def execute_entries(capsule, runner, deadline, evidence, *,
                    stage='qualification', clock=time.monotonic):
    """Stop at first failure; preserve exact failures and every not-run row.

    The runner boundary is injectable for offline tests. Production always
    constructs MatrixRunner; no command or arbitrary runner comes from JSON.
    """
    rows = selected_entries(capsule, stage)
    results = [{'id': row['id'], 'status': 'NOT_RUN'} for row in rows]
    evidence = Path(evidence)
    with (evidence / 'entry-results.jsonl').open('x') as journal:
        for index, entry in enumerate(rows):
            try:
                deadline.remaining(clock)
                outcome = runner.run_entry(entry)
                deadline.remaining(clock)
                require(outcome['id'] == entry['id']
                        and outcome['status'] == 'PASS'
                        and outcome['sessions'] == entry['sessions'],
                        'Entry outcome or actual session count differs')
                results[index] = outcome
            except BaseException:
                with (evidence / 'matrix-failure.txt').open('x') as stream:
                    traceback.print_exc(file=stream)
                results[index] = {'id': entry['id'], 'status': 'FAIL'}
                journal.write(json.dumps(results[index]) + '\n')
                journal.flush()
                break
            journal.write(json.dumps(outcome, sort_keys=True) + '\n')
            journal.flush()
    write(evidence / 'matrix-entries.json', results)
    return results


def run_matrix(work, expected, control_path, receipts, bridge_root, *,
               heavy_start_deadline):
    """Execute the reviewed scope under one non-renewable deadline."""
    entered = time.monotonic()
    require(type(heavy_start_deadline) in (int, float)
            and math.isfinite(heavy_start_deadline)
            and 0 < heavy_start_deadline - entered <= 90,
            'Heavy-start reservation absent or outside allowed interval')
    require(os.getuid() != 0 and not sys.flags.optimize,
            'Non-root assertions required')
    work = Path(work).absolute()
    require('..' not in work.parts
            and work.is_relative_to(Path(os.environ['RUNNER_TEMP']).absolute()),
            'Matrix scratch must be runner owned')
    control = json.loads(readiness.regular(control_path).read_text())
    validate_control(control, receipts, os.environ, ROOT)
    stage = control['stage']
    native07 = stage == NATIVE07_STAGE
    require(pilot._command('git', 'rev-parse', 'HEAD')
            == control['source_commit']
            and not pilot._command('git', 'status', '--porcelain',
                                   '--untracked-files=no'),
            'Matrix checkout differs')
    manifest = verify_preparation(work, expected)
    bridge.verify_bridge(bridge_root)
    readiness.candidate_deployment()
    memory = pilot._memory(Path('/proc/meminfo').read_text())
    require(memory['MemAvailable'] >= (4096 + 256 + 8192) * 1024**2,
            'Host admission reserve unavailable')
    evidence = work / 'evidence'
    evidence.mkdir(mode=0o700)
    (work / 'entries').mkdir(mode=0o700)
    # Exclusive creation is the no-retry/no-resume marker. A later call
    # cannot establish a fresh deadline in this attempt's scratch.
    write(evidence / 'attempt.json', {
        'source_commit': control['source_commit'],
        'control': identity(control_path),
        'preparation': identity(work / 'preparation.json'),
        'heavy_start_deadline': heavy_start_deadline,
        'runtime_admission': False, 'zy_execution': False,
        **({'stage': stage} if native07 else {}),
    })
    bridge.install_driver_token(bridge_root, work / 'assessment')
    capsule = load_execution_capsule(ROOT / CAPSULE, ROOT)
    outcome = {'status': 'FAIL', 'runtime_admission': False,
               'zy_execution': False, 'public_payload_status': 'NOT_SEALED'}
    if native07:
        outcome['stage'] = stage
    display_samples, host_samples = [], []
    ownership = ExitStack()
    deadline = None
    watchdog = None
    results = []
    try:
        lease = ownership.enter_context(guard.acquire_validation_lease(
            Path(os.environ['XDG_RUNTIME_DIR'])))
        with patch.object(pilot, 'OUTPUT', evidence):
            require(pilot._clearance(), 'Foreign FreeCAD instance')
        with patch.dict(os.environ, {'L1_GUI_STAGE': 'gui',
                                    'TRACKTEMPLATE_GUI_WORKLOAD': 'l1'}):
            owner = gui.start_display(work)
        group = gui._display_group(owner)

        def observe():
            sample = guard._sample(group)
            display_samples.append(sample)
            host = pilot._memory(Path('/proc/meminfo').read_text())
            host_samples.append(host)
            with (evidence / 'display-samples.jsonl').open('a') as stream:
                stream.write(json.dumps(sample) + '\n')
            with (evidence / 'host-memory.jsonl').open('a') as stream:
                stream.write(json.dumps(host) + '\n')
            gui.assess_display(display_samples)
            require(host['MemAvailable'] >= 8192 * 1024**2,
                    'Host reserve lost')

        pressure_failed = False

        def sleep(seconds):
            nonlocal pressure_failed
            try:
                observe()
            except (OSError, ValueError):
                if not pressure_failed:
                    pressure_failed = True
                    raise guard.GuardFailure('host-pressure-unproved') from None
            time.sleep(seconds)

        observe()
        require(time.monotonic() < heavy_start_deadline,
                ('Heavy-start reservation exhausted before Native 07'
                 if native07 else
                 'Heavy-start reservation exhausted before generation'))
        # Established once, before the first entry. Session starts and all
        # between-entry checks consume this same immutable interval.
        deadline = Deadline.start()
        write(evidence / 'heavy-deadline.json', vars(deadline))
        watchdog = ownership.enter_context(ControllerWatchdog(deadline))
        runner = MatrixRunner(work, manifest, bridge_root, lease,
                              guard.GuardContext(sleep=sleep), deadline,
                              watchdog, native07_once=native07)
        results = execute_entries(capsule, runner, deadline, evidence,
                                  stage=stage)
        deadline.remaining()
        observe()
        expected_entries, expected_sessions = (1, 1) if native07 else (80, 84)
        require(len(results) == expected_entries
                and all(row['status'] == 'PASS' for row in results)
                and runner.session_count == expected_sessions,
                ('Native 07 check incomplete' if native07
                 else 'Qualification matrix incomplete'))
        verify_source_members(work / 'assessment', manifest)
        require(identity(ROOT / assessment.CANONICAL_PATH)['sha256']
                == assessment.CANONICAL_SHA256, 'Canonical contract changed')
        outcome['status'] = 'PASS'
        if not native07:
            outcome['straight_receipt'] = {
                'path': str(runner.straight_receipt),
                **identity(runner.straight_receipt)}
            outcome['b4_receipt'] = {
                'path': str(runner.b4_receipt), **identity(runner.b4_receipt)}
    except BaseException:
        with (evidence / 'controller-failure.txt').open('x') as stream:
            traceback.print_exc(file=stream)
    finally:
        try:
            with (watchdog.cleanup_safe() if watchdog else nullcontext()):
                cleanup = gui.display_cleanup(work)
            write(evidence / 'display-cleanup.json', cleanup)
            outcome['display_cleanup'] = cleanup['cleanup']
            if not cleanup['cleanup']:
                outcome['status'] = 'FAIL'
        except BaseException:
            outcome['display_cleanup'] = False
            outcome['status'] = 'FAIL'
            with (evidence / 'cleanup-failure.txt').open('x') as stream:
                traceback.print_exc(file=stream)
        try:
            ownership.close()
        except BaseException:
            outcome['status'] = 'FAIL'
            with (evidence / 'lease-cleanup-failure.txt').open('x') as stream:
                traceback.print_exc(file=stream)
        if deadline is not None:
            try:
                outcome['remaining_heavy_seconds'] = deadline.remaining()
            except ValueError:
                outcome['status'] = 'FAIL'
                outcome['deadline_exhausted'] = True
        outcome['completed_entries'] = sum(
            row['status'] == 'PASS' for row in results)
        write(evidence / 'matrix-assessment.json', outcome)
    if outcome['status'] == 'PASS':
        print(NATIVE07_SENTINEL if native07 else SENTINEL)
    return outcome


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    preparation = commands.add_parser('prepare')
    preparation.add_argument('--assessment-capsule', type=Path, required=True)
    preparation.add_argument('--base', type=Path, required=True)
    preparation.add_argument('--work', type=Path, required=True)
    run = commands.add_parser('run')
    run.add_argument('--work', type=Path, required=True)
    run.add_argument('--preparation-sha256', required=True)
    run.add_argument('--control', type=Path, required=True)
    run.add_argument('--receipts', type=Path, required=True)
    run.add_argument('--bridge', type=Path, required=True)
    run.add_argument('--heavy-start-deadline', type=float, required=True)
    args = parser.parse_args(argv)
    if args.command == 'prepare':
        prepare_matrix(ROOT, args.assessment_capsule, args.base, args.work)
        print(json.dumps(identity(args.work / 'preparation.json')))
        return 0
    path = args.work / 'preparation.json'
    require(identity(path)['sha256'] == args.preparation_sha256,
            'Caller-held preparation identity differs')
    outcome = run_matrix(args.work, json.loads(path.read_text()),
                         args.control, args.receipts, args.bridge,
                         heavy_start_deadline=args.heavy_start_deadline)
    return 0 if outcome['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
