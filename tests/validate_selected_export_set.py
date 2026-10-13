#!/usr/bin/env python3
"""Prove selected-set publication, optional CSV and confirmed GUI planning.

Synthetic files and controls exercise the real application/policy boundary.
They do not qualify CAD formats, physical production or actual Qt behaviour.
"""

import copy
import csv
import errno
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.adapters.export import core_layout_set as files  # noqa: E402
from tracktemplate.application.selected_export_set import (  # noqa: E402
    prepare_selected_export_plan,
    run_atomic_selected_production_export,
)
from tracktemplate.compatibility.selected_export_policy import (  # noqa: E402
    SelectedExportConfiguration,
)
from tracktemplate.compatibility.selected_export_workflow import (  # noqa: E402
    SelectedExportBinding,
)
import validate_selected_export_rollback as retained  # noqa: E402


SENTINEL = "Selected export set validation passed"


def run_case(root, *, manifest=True, fault=None, factory=None):
    plan, config = retained.inputs(root, manifest=manifest)
    child = root / "Selected_Export_test"
    for task in plan["tasks"]:
        task["path"] = str(child / Path(task["path"]).name)
    plan["manifest_path"] = str(child / "selected.csv") if manifest else ""
    plan["output_directory"] = str(child)
    plan["selected_scope"] = {"scope_type": "highlighted", "record_ids": ["R1"]}
    plan["skipped"] = [{"record": {"record_id": "S1"}, "reason": "plan skip"}]
    extra = [{"record": {"record_id": "S2"}, "reason": "preliminary skip"}]
    saved = copy.deepcopy((plan, config, extra))
    before = retained.regular_files(root)
    document = object()
    dispatched, observed_skips = [], []

    def dispatch(doc, task, path):
        assert doc is document and not child.exists()
        assert task is plan["tasks"][len(dispatched)]
        dispatched.append(task)
        Path(path).write_bytes(retained.payload(task))
        if fault == "early" or (fault == "late" and len(dispatched) == 2):
            raise OSError("controlled writer failure")

    def rows(results, skipped, *_args):
        assert manifest and not child.exists()
        assert skipped == plan["skipped"] + extra
        observed_skips.extend(skipped)
        if fault == "rows":
            raise OSError("controlled CSV rows failure")
        return [{"path": item["task"]["path"]} for item in results]

    def write(path, values):
        assert manifest and not child.exists()
        with open(path, "w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, ["path"])
            writer.writeheader()
            writer.writerows(values)
        if fault == "csv":
            raise OSError("controlled CSV writer failure")

    result = run_atomic_selected_production_export(
        document, plan, config, "SET", {}, {}, {}, {}, extra,
        dispatch_export_task=dispatch, build_manifest_rows=rows,
        write_export_manifest=write,
        failed_export_report=retained.Collaborators.failed,
        skipped_export_report=retained.Collaborators.skipped,
        export_files_factory=factory or files.CoreLayoutExportSetFiles,
    )
    assert (plan, config, extra) == saved
    after = retained.regular_files(root)
    assert all(after[name] == data for name, data in before.items())
    assert result["skipped_objects"] == 2
    assert len(result["skipped_outputs"]) == 2
    assert result["manifest_requested"] is manifest
    for item, task in zip(result["results"], plan["tasks"]):
        assert item["task"] is task
    if result["publication_state"] == "published":
        assert result["successful_files"] == 2 + int(manifest)
        assert result["output_directory"] == str(child)
        assert set(path.name for path in child.iterdir()) == (
            {"first.step", "second.svg"} | ({"selected.csv"} if manifest else set())
        )
        for task in plan["tasks"]:
            assert Path(task["path"]).read_bytes() == retained.payload(task)
        if manifest:
            with open(result["manifest_path"], newline="") as stream:
                assert [row["path"] for row in csv.DictReader(stream)] == [
                    task["path"] for task in plan["tasks"]
                ]
            assert observed_skips == plan["skipped"] + extra
    else:
        assert result["successful_files"] == 0
        assert result["output_directory"] == str(root)
        assert result["manifest_path"] == "" and result["formats"] == []
    return result, plan


def validate_application(base):
    cases = 0

    def case(name, **kwargs):
        nonlocal cases
        root = base / name
        root.mkdir()
        cases += 1
        return run_case(root, **kwargs)

    for manifest in (True, False):
        result, _plan = case("success-" + str(manifest), manifest=manifest)
        assert result["publication_state"] == "published"
        assert result["failed_files"] == 0
    for fault in ("early", "late", "rows", "csv"):
        result, plan = case(fault, fault=fault)
        assert result["publication_state"] == "not-published"
        assert not Path(plan["output_directory"]).exists()
        assert result["failed_files"] > 0

    class Collision(files.CoreLayoutExportSetFiles):
        def publish(self):
            child = Path(self.output_directory)
            child.mkdir()
            (child / "foreign.txt").write_bytes(b"foreign")
            super().publish()

    class Before(files.CoreLayoutExportSetFiles):
        def publish(self):
            raise OSError("controlled error before publication")

    class After(files.CoreLayoutExportSetFiles):
        def publish(self):
            super().publish()
            raise OSError("controlled error after publication")

    class Cleanup(files.CoreLayoutExportSetFiles):
        def cleanup(self):
            return super().cleanup() + ["controlled cleanup diagnostic"]

    for factory in (Collision, Before, After, Cleanup):
        result, plan = case(factory.__name__, factory=factory)
        published = factory in (After, Cleanup)
        assert result["publication_state"] == (
            "published" if published else "not-published"
        )
        assert result["failed_files"] > 0
        if factory is Collision:
            assert (Path(plan["output_directory"]) / "foreign.txt").read_bytes() == b"foreign"

    rename = files._rename_noreplace
    for after in (False, True):
        def broken_rename(*args):
            if after:
                rename(*args)
            raise OSError(errno.ENOSYS, "controlled unsupported rename")

        with mock.patch.object(files, "_rename_noreplace", broken_rename):
            result, plan = case("rename-" + str(after))
        assert result["publication_state"] == (
            "published" if after else "not-published"
        )
        assert Path(plan["output_directory"]).exists() is after

    class Uncertain(files.CoreLayoutExportSetFiles):
        def _reconcile_publication(self):
            raise OSError("controlled inspection failure")

    with mock.patch.object(files, "_rename_noreplace", side_effect=OSError("uncertain")):
        result, plan = case("uncertain", factory=Uncertain)
    assert result["publication_state"] == "uncertain"
    assert "Publication is uncertain" in "\n".join(result["failures"])
    assert list(Path(plan["output_directory"]).parent.glob(".tracktemplate*"))

    class Interruption(BaseException):
        pass

    for after in (False, True):
        class Interrupted(files.CoreLayoutExportSetFiles):
            def publish(self):
                if after:
                    super().publish()
                raise Interruption("controlled interruption boundary")

        try:
            case("interrupted-" + str(after), factory=Interrupted)
        except Interruption as error:
            state = "published" if after else "not-published"
            assert any("state: " + state in note for note in error.__notes__)
        else:
            raise AssertionError("Interruption was swallowed")
        child = base / ("interrupted-" + str(after)) / "Selected_Export_test"
        assert child.exists() is after
    return cases


class Control:
    def __init__(self):
        self.checked = True
        self.enabled = True
        self.text = ""
        self.blocked = False

    def blockSignals(self, value):
        previous, self.blocked = self.blocked, value
        return previous

    def setChecked(self, value):
        self.checked = value

    def setEnabled(self, value):
        self.enabled = value

    def setText(self, value):
        self.text = value

    def setToolTip(self, value):
        self.tooltip = value


class Shape:
    """Expose the same mutable BRep observation used at the host boundary."""

    def __init__(self):
        self.payload = "initial BRep"

    def exportBrepToString(self):
        return self.payload


class MessageBox:
    Yes, No, Ok, Question, Information, Warning, ActionRole = range(7)
    boxes = []
    errors = []
    on_confirm = None
    accept = True
    open_folder = True

    def __init__(self):
        self.informative = self.details = self.text = ""
        self.button = None
        self.boxes.append(self)

    def setWindowTitle(self, value):
        self.title = value

    def setIcon(self, value):
        self.icon = value

    def setText(self, value):
        self.text = value

    def setInformativeText(self, value):
        self.informative = value

    def setDetailedText(self, value):
        self.details = value

    def setStandardButtons(self, value):
        self.buttons = value

    def setDefaultButton(self, value):
        self.default = value

    def addButton(self, text, role):
        self.button = (text, role)
        return self.button

    def clickedButton(self):
        return self.button if self.open_folder else None

    @classmethod
    def critical(cls, _dialog, _title, value):
        cls.errors.append(value)


def policy_fixture(root):
    namespace = {"__name__": "selected_set_fixture", "Path": Path,
                 "MessageBox": MessageBox, "Control": Control}
    exec('''
def plan_selected_production_export(records, config, set_id, scope):
    child = Path(config['output_directory'])
    return {'tasks': [{'path': str(child / 'member.svg'), 'format': 'svg',
                      'records': records, 'combined': False}],
            'manifest_path': str(child / 'selected.csv')
                if config['create_manifest'] else '',
            'selected_scope': dict(scope), 'skipped': []}
def selected_export_preflight_config(config, plan):
    return dict(config, formats={'svg': True, 'step': False})
def confirm_selected_export_operation(*args):
    return 'retained confirmation'
def dispatch_freecad_export(doc, task, path):
    executed.append(task)
    Path(path).write_text('selected output', encoding='utf-8')
def build_manifest_rows(results, skips, *args):
    return [item['task']['path'] for item in results]
def write_export_manifest(path, rows):
    Path(path).write_text('\\n'.join(rows), encoding='utf-8')
def _failed_export_report(item):
    return item['error'], item['error']
def _skipped_export_report(item):
    return item['reason'], item['reason']
def run_selected_production_export(*args):
    raise AssertionError('retained command is not the normal route')
def ensure_production_export_directory(config):
    assert config['output_directory'] == parent
    assert not Path(dialog.plan['output_directory']).exists()
def settings_for_template_set(*args):
    return None
def read_section_config(*args):
    return {}
read_registration_config = read_section_config
read_template_assembly_config = read_section_config
read_formation_config = read_section_config
def read_platform_configs(*args):
    return [{}]
def selected_export_filename_issues(*args):
    return []
def selected_export_validation_records(catalogue, matching, scope):
    return matching
def run_production_preflight(doc, catalogue, records, config, *args, **kwargs):
    preflights.append(config)
    assert config['output_directory'] == kwargs['plan']['output_directory']
    assert config['formats'] == {'svg': True, 'step': False}
    if preflight_hook:
        preflight_hook(kwargs['plan'])
    return []
def preflight_blocking_report(issues):
    return ''
def selected_export_scope_description(scope):
    return scope['scope_type']
def selected_export_plan_rows(plan, config):
    return [{'Full path': task['path'], 'Format': task['format']}
            for task in plan['tasks']] + (
                [{'Full path': plan['manifest_path'], 'Format': 'CSV'}]
                if plan['manifest_path'] else [])
def dialog_exec(box):
    if 'Confirm' in box.title:
        confirmations.append((dialog.plan['output_directory'], box.informative))
        if MessageBox.on_confirm:
            MessageBox.on_confirm()
        return MessageBox.Yes if MessageBox.accept else MessageBox.No
    summaries.append(box)
    return MessageBox.Ok
def open_export_directory(path):
    opened.append(path)
class SelectedProductionExportDialog:
    def __init__(self):
        self.doc = object()
        self.set_id = 'SET'
        self.config = dict(output_directory=parent, create_manifest=True,
                           overwrite_existing=True)
        self.scope = {'scope_type': 'Selected rows'}
        self.export_records = [{'record_id': 'R1', 'metadata': {'value': 1}}]
        self.matching_records = self.catalogue_records = self.export_records
        self.preliminary_skipped = []
        self.issues = []
        self.highlighted = []
        self.expand_highlights = False
        self.unstable_highlights = False
        self.preview_count = 0
        self.overwrite_box = Control()
        self.output_box = Control()
        self.manifest_box = Control()
        self.export_button = Control()
        self.summary_label = Control()
    def current_set_id(self):
        return self.set_id
    def _current_config(self):
        return dict(self.config)
    def _highlighted_record_ids(self):
        return set(self.highlighted)
    def refresh_preview(self, *args):
        self.preview_count += 1
        if self.highlighted:
            self.scope['highlighted_record_ids'] = sorted(self.highlighted)
        self.plan = plan_selected_production_export(
            self.export_records, self._current_config(), self.current_set_id(),
            self.scope)
        if self.expand_highlights:
            self.highlighted = ['outline', 'solid']
        if self.unstable_highlights:
            self.highlighted.append('unstable-' + str(self.preview_count))
    def export_selected(self):
        return run_selected_production_export
''', namespace)
    namespace.update(
        parent=str(root), QtWidgets=SimpleNamespace(QMessageBox=MessageBox),
        versioned_dialog_title=lambda value: value,
        PRODUCTION_PREFLIGHT_SEVERITY_WARNING="warning", executed=[],
        preflights=[], confirmations=[], summaries=[], opened=[],
        preflight_hook=None,
    )
    MessageBox.boxes, MessageBox.errors = [], []
    MessageBox.on_confirm, MessageBox.accept = None, True
    binding = SelectedExportBinding(
        namespace, export_files_factory=files.CoreLayoutExportSetFiles,
        export_dispatcher_factory=lambda serializer: serializer, atomic=True,
    )
    before = binding.snapshot()
    binding.bind()
    binding.validate()
    dialog = namespace["SelectedProductionExportDialog"]()
    namespace["dialog"] = dialog
    return namespace, binding, before, dialog


def validate_policy(base):
    cases = 0
    scenarios = (
        "success", "reconfirm", "decline", "collision", "same-path", "shape",
        "second-set",
    )
    for scenario in scenarios:
        root = base / ("policy-" + scenario)
        root.mkdir()
        ns, binding, before, dialog = policy_fixture(root)
        if scenario == "shape":
            dialog.export_records[0]["shape"] = Shape()
        dialog.refresh_preview()
        first = dialog.plan
        dialog.refresh_preview()
        assert dialog.plan == first
        config = dialog._current_config()
        assert isinstance(config, SelectedExportConfiguration)
        assert json.loads(json.dumps(config)) == dict(config)
        assert config["output_directory"] == str(root)
        assert not dialog.overwrite_box.checked
        assert not dialog.overwrite_box.enabled
        assert "New folder" in dialog.overwrite_box.text
        if scenario == "decline":
            MessageBox.accept = False
        elif scenario in ("reconfirm", "second-set"):
            def changed():
                if len(ns["confirmations"]) == 1:
                    dialog.export_records[0]["metadata"]["value"] += 1
                elif scenario == "second-set":
                    dialog.set_id = "OTHER"
            MessageBox.on_confirm = changed
        elif scenario in ("same-path", "shape"):
            def alter_record(plan):
                record = plan["tasks"][0]["records"][0]
                if scenario == "shape":
                    record["shape"].payload = "changed BRep"
                else:
                    record["metadata"]["value"] += 1
            ns["preflight_hook"] = alter_record
        elif scenario == "collision":
            def collide():
                Path(dialog.plan["output_directory"]).mkdir()
            MessageBox.on_confirm = collide
        dialog.export_selected()
        if scenario in ("success", "reconfirm", "same-path", "shape"):
            assert len(ns["executed"]) == 1
            assert len(ns["confirmations"]) == (1 if scenario == "success" else 2)
            completed = ns["confirmations"][-1][0]
            if scenario in ("same-path", "shape"):
                assert ns["confirmations"][0][0] == completed
            assert ns["opened"] == [completed]
            assert Path(completed).is_dir()
            assert ns["summaries"][0].button[0] == "Open output folder"
            assert "complete selected output set was published" in ns["summaries"][0].text
            assert dialog.plan["output_directory"] != completed
            assert not MessageBox.errors
        else:
            assert ns["executed"] == [] and ns["opened"] == []
            assert bool(MessageBox.errors) is (
                scenario in ("collision", "second-set")
            )
        assert dialog.config["output_directory"] == str(root)
        binding.validate()
        binding.restore(before)
        assert binding.snapshot() == before
        assert ns["confirm_selected_export_operation"]() == "retained confirmation"
        cases += 1

    root = base / "policy-invalidation"
    root.mkdir()
    ns, binding, _before, dialog = policy_fixture(root)
    dialog.refresh_preview()
    original = dialog.plan["output_directory"]
    dialog.scope["scope_type"] = "Other selected scope"
    dialog.refresh_preview()
    assert dialog.plan["output_directory"] != original
    original = dialog.plan["output_directory"]
    dialog.config["create_manifest"] = False
    dialog.refresh_preview()
    assert dialog.plan["output_directory"] != original
    assert not dialog.plan["manifest_path"]
    plain = ns["plan_selected_production_export"](
        dialog.export_records, dict(dialog.config), "SET", dialog.scope,
    )
    assert "output_directory" not in plain
    assert Path(plain["tasks"][0]["path"]).parent == root
    binding.policy.show_summary({
        "publication_state": "uncertain", "output_directory": str(root),
        "successful_files": 0, "failed_files": 1, "skipped_objects": 0,
        "formats": [], "manifest_path": "", "manifest_requested": False,
        "failures": ["uncertain"], "failure_details": ["uncertain"],
        "skipped_details": [],
    })
    assert ns["summaries"][-1].button is None
    assert ns["opened"] == []
    ns["SelectedProductionExportDialog"].export_selected = object()
    try:
        binding.validate()
    except RuntimeError:
        pass
    else:
        raise AssertionError("Changed export callback was accepted")
    return cases + 1


def validate_preview_expansion(base):
    root = base / "policy-expanded-highlights"
    root.mkdir()
    _ns, binding, _before, dialog = policy_fixture(root)
    dialog.highlighted = ["outline"]
    dialog.expand_highlights = True
    dialog.refresh_preview()
    first = dialog.plan
    assert first["selected_scope"]["highlighted_record_ids"] == [
        "outline", "solid",
    ]
    assert dialog.preview_count == 2
    dialog.refresh_preview()
    assert dialog.plan == first
    assert dialog.preview_count == 3
    binding.validate()

    root = base / "policy-unstable-highlights"
    root.mkdir()
    _ns, _binding, _before, dialog = policy_fixture(root)
    dialog.highlighted = ["outline"]
    dialog.unstable_highlights = True
    dialog.refresh_preview()
    assert dialog.preview_count == 2
    assert dialog.plan is None
    assert not dialog.export_button.enabled
    assert "selection did not settle" in dialog.summary_label.text
    return 2


def main():
    with tempfile.TemporaryDirectory(prefix="selected-set-", dir=ROOT / "tmp") as area:
        base = Path(area)
        application = validate_application(base)
        policies = validate_policy(base)
        policies += validate_preview_expansion(base)
        parent = base / "planner"
        parent.mkdir()
        config = {"output_directory": str(parent)}
        records, scope = [{"record_id": "kept"}], {"scope_type": "kept"}
        def planner(values, settings, set_id, selected_scope):
            assert values is records and selected_scope is scope
            assert settings["overwrite_existing"] is False
            return {"tasks": [], "skipped": []}
        first = prepare_selected_export_plan(
            records, config, "SET", scope, plan_export=planner,
        )
        assert Path(first["output_directory"]).name.startswith("Selected_Export_")
        assert not Path(first["output_directory"]).exists()
    print(SENTINEL + ": {} application cases; {} policy cases".format(
        application, policies,
    ))


if __name__ == "__main__":
    main()
