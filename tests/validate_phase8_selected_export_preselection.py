#!/usr/bin/env python3
"""Protect B16 modal export scope from temporary-probe selection loss."""

import pathlib
import sys
import types
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.compatibility import transition_workflow  # noqa: E402


SENTINEL = "Phase 8 selected-export preselection validation passed"


class _SetBox:
    def __init__(self, set_ids):
        self.set_ids = tuple(set_ids)

    def count(self):
        return len(self.set_ids)

    def itemText(self, index):
        return self.set_ids[index]


_HOST_SOURCE = """
def execute_export_tasks(*args):
    return None

def build_manifest_rows(*args):
    return None

def write_export_manifest(*args):
    return None

def _failed_export_report(*args):
    return None

def _skipped_export_report(*args):
    return None

def run_macro():
    return run_production_export

def selected_export_selection_snapshot(doc, set_id):
    doc.events.append(("selection", set_id))
    return doc.selected.get(set_id, [])

class SelectedProductionExportDialog:
    def __init__(self, doc, set_ids=("SET-A", "SET-B")):
        self.doc = doc
        self.set_box = SetBox(set_ids)
        self.set_id = set_ids[0]
        self.scope_type = "selected FreeCAD objects"
        self.route_id = "XO-001"
        self.section_number = 2

    def current_set_id(self):
        return self.set_id

    def _current_scope(self):
        self.doc.events.append("inherited-scope")
        return {
            "scope_type": self.scope_type,
            "route_id": self.route_id,
            "section_number": self.section_number,
            "selected_objects": selected_export_selection_snapshot(
                self.doc, self.current_set_id()
            ),
        }

    def refresh_preview(self):
        self.scope = self._current_scope()
        # The qualified host loses live selection when its probe opens a doc.
        self.doc.selected.clear()
        self.doc.events.append("temporary-probe")
        return self.scope
"""


def _host_session():
    module = types.ModuleType("selected_export_host_probe")
    module.SetBox = _SetBox
    exec(_HOST_SOURCE, module.__dict__)
    return types.SimpleNamespace(
        module=module,
        _host=types.SimpleNamespace(source_sha256="synthetic-host"),
        routing_record=lambda: {"route": "modular", "schema_version": 16},
        launch_workflow=lambda: "launched",
    )


def _bind(host):
    return transition_workflow.ModularCoreLayoutWorkflowSession(
        host, lambda *_args: None,
    )


def _document(selected):
    return types.SimpleNamespace(selected=selected, events=[])


def validate_refresh_and_scope_changes():
    host = _host_session()
    _bind(host)
    selected_a = {"name": "XO-001", "record_ids": {"A1", "A2"}}
    doc = _document({
        "SET-A": [selected_a],
        "SET-B": [{"name": "TO-001", "record_ids": {"B1"}}],
    })
    dialog = host.module.SelectedProductionExportDialog(doc)
    first = dialog.refresh_preview()
    expected = [{"name": "XO-001", "record_ids": {"A1", "A2"}}]
    assert first["selected_objects"] == expected
    assert doc.selected == {}
    assert dialog.refresh_preview()["selected_objects"] == expected, (
        "A temporary exporter-bound probe erased the modal export scope"
    )
    assert doc.events[:4] == [
        ("selection", "SET-A"),
        ("selection", "SET-B"),
        "inherited-scope",
        ("selection", "SET-A"),
    ]

    first["selected_objects"][0]["record_ids"].add("returned-corruption")
    selected_a["record_ids"].add("input-corruption")
    assert dialog.refresh_preview()["selected_objects"] == expected

    dialog.scope_type = "section"
    dialog.route_id = "TO-002"
    dialog.section_number = 7
    scope = dialog.refresh_preview()
    assert scope == {
        "scope_type": "section", "route_id": "TO-002",
        "section_number": 7, "selected_objects": expected,
    }
    dialog.set_id = "SET-B"
    assert dialog.refresh_preview()["selected_objects"] == [
        {"name": "TO-001", "record_ids": {"B1"}},
    ]
    dialog.set_id = "unrecognised-set"
    assert dialog.refresh_preview()["selected_objects"] == []
    dialog.set_id = "SET-A"
    dialog.scope_type = "selected FreeCAD objects"
    assert dialog.refresh_preview()["selected_objects"] == expected


def validate_empty_and_separate_dialogs():
    host = _host_session()
    _bind(host)
    doc = _document({})
    first = host.module.SelectedProductionExportDialog(doc)
    assert first.refresh_preview()["selected_objects"] == []
    selected = [{"name": "XO-002", "record_ids": {"A3"}}]
    doc.selected = {"SET-A": selected}
    assert first._current_scope()["selected_objects"] == []
    second = host.module.SelectedProductionExportDialog(doc)
    assert second.refresh_preview()["selected_objects"] == selected
    assert first.refresh_preview()["selected_objects"] == []
    assert second.refresh_preview()["selected_objects"] == selected


def _expect_route_error(action, fragment):
    try:
        action()
    except transition_workflow.TransitionWorkflowError as error:
        assert fragment in str(error), str(error)
    else:
        raise AssertionError("An incomplete or mixed selection route passed")


def validate_binding_guards_and_rebinding():
    for member in (
        "SelectedProductionExportDialog",
        "selected_export_selection_snapshot",
    ):
        host = _host_session()
        del host.module.__dict__[member]
        _expect_route_error(lambda: _bind(host), "incomplete")

    host = _host_session()
    host.module.SelectedProductionExportDialog._current_scope = (
        lambda _dialog: {}
    )
    _expect_route_error(lambda: _bind(host), "incomplete")

    host = _host_session()
    host.module.selected_export_selection_snapshot = lambda *_args: []
    _expect_route_error(lambda: _bind(host), "incomplete")

    for member in (
        "SelectedProductionExportDialog",
        "selected_export_selection_snapshot",
        "_current_scope",
    ):
        host = _host_session()
        dialog_class = host.module.SelectedProductionExportDialog
        inherited_scope = dialog_class._current_scope
        session = _bind(host)
        bound_scope = dialog_class._current_scope
        assert session.routing_record() == {
            "route": "modular", "schema_version": 16,
        }
        target = dialog_class if member == "_current_scope" else host.module
        original = getattr(target, member)
        setattr(target, member, lambda *_args: None)
        _expect_route_error(session.routing_record, "mixed binding")
        setattr(target, member, original)
        dialog_class._current_scope = inherited_scope
        _expect_route_error(session.routing_record, "mixed binding")
        assert session.launch_workflow() == "launched"
        assert dialog_class._current_scope is bound_scope
        assert session.routing_record()["schema_version"] == 16


def validate_binding_rollback():
    for existing_binding in (False, True):
        host = _host_session()
        namespace = host.module.__dict__
        dialog_class = host.module.SelectedProductionExportDialog
        original_scope = dialog_class._current_scope
        original_export = object()
        if existing_binding:
            namespace[transition_workflow.CORE_LAYOUT_EXPORT_HOST_BINDING] = (
                original_export
            )
        with mock.patch.object(
            transition_workflow.ModularCoreLayoutWorkflowSession,
            "_validate_core_layout_export_binding",
            side_effect=RuntimeError("controlled binding failure"),
        ):
            try:
                _bind(host)
            except RuntimeError as error:
                assert str(error) == "controlled binding failure"
            else:
                raise AssertionError("The controlled failure was lost")
        assert dialog_class._current_scope is original_scope
        if existing_binding:
            assert namespace[
                transition_workflow.CORE_LAYOUT_EXPORT_HOST_BINDING
            ] is original_export
        else:
            assert transition_workflow.CORE_LAYOUT_EXPORT_HOST_BINDING not in (
                namespace
            )


def validate():
    validate_refresh_and_scope_changes()
    validate_empty_and_separate_dialogs()
    validate_binding_guards_and_rebinding()
    validate_binding_rollback()
    print(SENTINEL)


if __name__ == "__main__":
    validate()
