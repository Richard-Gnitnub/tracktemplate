"""Import-safe source-copy readiness for the isolated candidate runtime."""

import hashlib
import importlib.util
import linecache
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback
import types

BASE_SHA256 = (
    '0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c'
)
DEFAULT_SHA256 = (
    '6539ff066b8abcd81cb111c3127124580e6bca44eb19c09ea8ae93175de7113f'
)
CANDIDATE_SHA256 = (
    '285192eeb388e0d2d6be64a47170e1cafa9ffb8efbf6ee3b43d51edc3769c7e7'
)
HELPER_SHA256 = (
    '1150aab0a68d75a9048bbfd096f60f270d8f452c7333ab692ba063fd878e7012'
)
PROFILE = 'linux-x86_64-flatpak-freecad-1.1.4-py3.13.16-qt6.11.3-coin4.0.10'
SENTINEL = 'TRACKTEMPLATE_COMPATIBILITY_GUI_READINESS_PASS'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write(path, record):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')


def _run(config):
    import FreeCAD as app
    import FreeCADGui as gui
    from PySide6 import QtGui, QtWidgets

    root = Path(config['assessment_root'])
    sys.path.insert(0, str(root))
    from tracktemplate.bootstrap import evaluate_runtime, runtime_record

    default = Path(config['default_contract'])
    candidate = root / 'reference/contracts/phase1-compatibility.json'
    assert digest(default) == DEFAULT_SHA256
    assert digest(candidate) == CANDIDATE_SHA256
    record = runtime_record()
    original_result = evaluate_runtime(record, json.loads(default.read_text()))
    assert original_result['status'] == 'unqualified'
    assessment = evaluate_runtime(record, json.loads(candidate.read_text()))
    assert assessment['status'] == 'qualified'
    assert assessment['matched_profile_id'] == PROFILE
    assert assessment['mismatches'] == []
    record['compatibility_evaluation'] = original_result
    print('TRACKTEMPLATE_RUNTIME_PROBE=' + json.dumps(record, sort_keys=True),
          flush=True)
    assert app.GuiUp
    assert not app.listDocuments()
    assert app.ActiveDocument is None
    helper_path = root / 'tests/hosted_l1_gui_suite.py'
    assert digest(helper_path) == HELPER_SHA256
    helper_source = helper_path.read_text()
    helper_name = 'tests/hosted_l1_gui_suite.py'
    linecache.cache[helper_name] = (
        len(helper_source), None, helper_source.splitlines(True), helper_name)
    helpers = types.ModuleType('readiness_helpers')
    helpers.__file__ = str(helper_path)
    exec(compile(helper_source, helper_name, 'exec'), helpers.__dict__)
    base = root / ('benchmark-output/freecad-bridge/fixtures/'
                   'b14-default-base-regenerated.FCStd')
    assert base.stat().st_size == 636344
    assert digest(base) == BASE_SHA256
    output = Path(config['output_root'])
    images = output / 'gui/readiness'
    images.mkdir(parents=True, mode=0o700)
    # Working documents stay outside the exact public evidence tree.
    target = output.parent / 'readiness-source-copy.FCStd'
    assert not target.exists()
    shutil.copyfile(base, target)
    assert digest(target) == BASE_SHA256
    owned = None
    before_count = after_count = 0
    renderer = None
    try:
        owned = app.openDocument(str(target))
        assert owned is not None
        app.setActiveDocument(owned.Name)
        assert set(app.listDocuments()) == {owned.Name}
        before_count = len(owned.Objects)
        assert before_count == 9
        owned.Label = 'Approved synthetic base'
        gui.activeDocument().activeView().viewTop()
        gui.activeDocument().activeView().fitAll()
        for _ in range(12):
            QtWidgets.QApplication.processEvents()
        renderer = helpers._gl_record(app, gui, QtGui, QtWidgets)
        helpers._readiness_image(
            gui, QtWidgets, images / 'readiness-source.png')
        after_count = len(owned.Objects)
        assert after_count == before_count
        assert digest(base) == BASE_SHA256
        assert digest(target) == BASE_SHA256
    finally:
        if owned is not None:
            app.closeDocument(owned.Name)
        assert not app.listDocuments()
        assert app.ActiveDocument is None
    assert digest(default) == DEFAULT_SHA256
    observation = {
        'status': 'PASS', 'assessment_entry_sha256': config['entry_sha256'],
        'runtime': {
            'freecad': record['freecad']['version_info'],
            'python': record['python']['version_info'],
            'pyside': record['freecad']['pyside_version'],
            'qt': record['freecad']['qt_version'],
            'occt': record['freecad']['opencascade_version'],
            'coin': record['freecad']['coin_version'],
            'app_commit': config['app_commit'],
            'runtime_commit': config['runtime_commit'],
        },
        'sentinel': SENTINEL, 'sessions': 1,
        'inputs': [{'id': 'approved-base', 'sha256': BASE_SHA256,
                    'bytes': 636344}],
        'document_preservation': {
            'source_sha256_before': BASE_SHA256,
            'source_sha256_after': digest(base),
            'original_unchanged': True, 'copy_only': True,
            'object_count_before': before_count, 'object_count_after': after_count,
            'undo': 'NOT_APPLICABLE', 'redo': 'NOT_APPLICABLE',
            'save_reopen': 'NOT_APPLICABLE',
        },
        'failure': None, 'renderer': renderer, 'pre_geometry_readiness': True,
        'source_copy_only': True, 'geometry_builds': 0,
    }
    _write(output.parent / 'readiness-observation.json', observation)
    print(SENTINEL, flush=True)


def start(config_path, config_sha256, *, launcher_name):
    """Run once after the Qt event loop starts; preserve the original failure."""
    import FreeCADGui as gui
    from PySide6 import QtCore

    assert launcher_name == '__main__'
    assert __name__ == 'hosted_compatibility_readiness_suite'
    assert not sys.flags.optimize
    assert os.environ.get('GITHUB_ACTIONS') == 'true'
    assert os.environ.get('GITHUB_RUN_ATTEMPT') == '1'
    config_path = Path(config_path)
    assert digest(config_path) == config_sha256
    config = json.loads(config_path.read_text())
    assert config['entry_sha256'] == digest(Path(__file__))
    print('TRACKTEMPLATE_COMPATIBILITY_READINESS_ENTRY=' + json.dumps({
        'launcher_name': launcher_name, 'suite_name': __name__,
        'entry_sha256': config['entry_sha256'],
    }, sort_keys=True), flush=True)
    probe = None
    # The guard's 90-second allowance starts before this macro. This local
    # deadline can only stop the client sooner; it cannot extend the guard.
    probe_deadline = time.monotonic() + 80

    def execute():
        nonlocal probe
        finished = False
        try:
            if probe is None:
                probe = _begin_bridge(config, probe_deadline)
            if probe.poll() is None:
                assert time.monotonic() < probe_deadline
                QtCore.QTimer.singleShot(50, execute)
                return
            assert probe.returncode == 0
            bridge_record = json.loads(
                Path(config['bridge_receipt']).read_text())
            assert bridge_record['status'] == 'PASS'
            assert bridge_record['sentinel'] == (
                'TRACKTEMPLATE_COMPATIBILITY_BRIDGE_READINESS_PASS')
            _run(config)
            finished = True
        except BaseException as error:
            finished = True
            # Retain original bytes; publication may refuse unsafe diagnostics.
            target = Path(config['output_root']) / 'gui/readiness'
            target.mkdir(parents=True, exist_ok=True)
            with (target / 'failure.txt').open('x', encoding='utf-8') as stream:
                stream.write(traceback.format_exc())
            traceback.print_exc()
            failure = error.__traceback__
            while failure.tb_next is not None:
                failure = failure.tb_next
            observation = {
                'status': 'FAIL',
                'assessment_entry_sha256': config['entry_sha256'],
                'runtime': None, 'sentinel': '', 'sessions': 1, 'inputs': [],
                'document_preservation': None, 'renderer': None,
                'pre_geometry_readiness': None, 'source_copy_only': None,
                'geometry_builds': None,
                'failure': {
                    'exception_type': type(error).__name__,
                    'source_relative_file': failure.tb_frame.f_code.co_filename,
                    'line': failure.tb_lineno,
                    'reason_code': ('ASSERTION_FAILED' if isinstance(
                        error, AssertionError) else 'SOURCE_EXCEPTION'),
                },
            }
            _write(Path(config['output_root']).parent /
                   'readiness-observation.json', observation)
        finally:
            if finished:
                if probe is not None and probe.poll() is None:
                    probe.terminate()
                gui.getMainWindow().close()

    QtCore.QTimer.singleShot(0, execute)


def _begin_bridge(config, deadline):
    """Start the fixed client as a child of the contained GUI process."""
    path = Path(config['bridge_adapter'])
    assert digest(path) == config['bridge_adapter_sha256']
    spec = importlib.util.spec_from_file_location('readiness_bridge', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.launch_readiness_probe(
        Path(config['bridge_root']), Path(config['bridge_receipt']),
        deadline=deadline, guard_evidence=Path(config['guard_evidence']))
