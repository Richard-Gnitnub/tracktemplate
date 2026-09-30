#!/usr/bin/env python3
"""Check the B16 selected-crossover Edit cue and existing B4 binding."""

import pathlib
import sys
import tempfile
import types


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import (  # noqa: E402
    b15_workflow_host,
    transition_workflow,
)
import validate_phase7_concentric_core as core_proof  # noqa: E402


SENTINEL = "Phase 8 crossover Edit success cue validation passed"
ACTIVE_CUE = "Editing XO-001. Adjust hosts or exact Host A chainage."
SUCCESS_CUE = "Updated XO-001 transactionally."

_SYNTHETIC_B4_ROUTE = """
CROSSOVER_B4_ROLE = "crossover-b4-timbering"
def apply_crossover_b4_timbering(*arguments):
    if arguments is None:
        return _write_crossover_b4_and_timber_analysis_metadata(*arguments)
    return arguments
def _write_crossover_b4_and_timber_analysis_metadata(*arguments):
    return arguments
def _b4_resolution_signature(*arguments):
    return arguments
def _crossover_b4_result_is_current(*arguments):
    return arguments
def _crossover_b4_object(doc, _identifier):
    return doc.b4_object
def crossover_inherited_timber_records(*arguments):
    if arguments is None:
        return interpolate_alignment_station(None, None)
    return arguments
def normalise_crossover_b4_settings(*arguments):
    return arguments
def normalise_crossover_b3_settings(*arguments):
    return arguments
def normalise_crossover_shared_timber_settings(*arguments):
    return arguments
def normalise_crossover_timber_analysis_settings(*arguments):
    return arguments
def tag_generated_object(*arguments):
    return arguments
def crossover_config_by_id(*arguments):
    return arguments
def object_string_property(*arguments):
    return arguments
class CrossoverManagerPanel:
    def current_config(self):
        return self.config
    def use_picked_crossover_position(self):
        return interpolate_alignment_station(None, None)
    def apply_b4_timbering(self):
        return apply_crossover_b4_timbering(self.doc, "XO-001")
    def update_selection_buttons(self):
        self.update_calls += 1
"""


class _Label:
    def __init__(self, value):
        self.value = value

    def text(self):
        return self.value

    def setText(self, value):
        self.value = value


class _Checkbox:
    def __init__(self):
        self.checked = False
        self.signals_blocked = False

    def blockSignals(self, value):
        self.signals_blocked = value

    def setChecked(self, value):
        self.checked = value


def _host(root, contract):
    host = b15_workflow_host.load_b15_workflow_host(root, contract)
    exec(_SYNTHETIC_B4_ROUTE, host.module.__dict__)
    return host


def _panel(panel_type, *, editing_id, cue=ACTIVE_CUE, selected="XO-001"):
    panel = panel_type()
    panel.config = {"crossover_id": selected} if selected else None
    panel.doc = types.SimpleNamespace(
        b4_object=types.SimpleNamespace(
            ViewObject=types.SimpleNamespace(Visibility=True),
        ),
    )
    panel.editing_crossover_id = editing_id
    panel.selection_status = _Label(cue)
    panel.b4_settings = {"show_b4_geometry": False}
    panel.show_b4_checkbox = _Checkbox()
    panel.update_calls = 0
    panel.selected_crossover_id = selected
    panel.source_bindings = ("XO-001:001", "XO-001:002")
    return panel


def _check_unchanged(panel, expected_cue):
    panel.update_selection_buttons()
    assert panel.update_calls == 1
    assert panel.selection_status.text() == expected_cue
    assert panel.selected_crossover_id == "XO-001"
    assert panel.source_bindings == ("XO-001:001", "XO-001:002")
    assert panel.b4_settings["show_b4_geometry"] is True
    assert panel.show_b4_checkbox.checked is True
    assert panel.show_b4_checkbox.signals_blocked is False


def validate():
    with tempfile.TemporaryDirectory(prefix="phase8-xo-edit-cue-") as path:
        root = pathlib.Path(path)
        contract = core_proof._fixture(root)
        host = _host(root, contract)
        panel_type = host.module.CrossoverManagerPanel
        inherited = panel_type.__dict__["update_selection_buttons"]
        functions = {
            name: getattr(api, name)
            for name in transition_workflow.PRODUCT_FUNCTION_NAMES
        }
        session = transition_workflow.ModularTransitionWorkflowSession(
            host, functions,
        )
        record = session.routing_record()
        assert panel_type.__dict__["update_selection_buttons"] is not inherited

        _check_unchanged(
            _panel(panel_type, editing_id="XO-001"), ACTIVE_CUE,
        )
        _check_unchanged(
            _panel(panel_type, editing_id="XO-001", cue="REJECTED"),
            "REJECTED",
        )
        _check_unchanged(
            _panel(
                panel_type, editing_id=None,
                cue="Editing XO-001 cancelled. No crossover geometry changed.",
            ),
            "Editing XO-001 cancelled. No crossover geometry changed.",
        )
        _check_unchanged(
            _panel(panel_type, editing_id=None), SUCCESS_CUE,
        )
        _check_unchanged(
            _panel(panel_type, editing_id=None, cue="Picked XO-001"),
            "Picked XO-001",
        )
        assert session.routing_record() == record

        panel_type.update_selection_buttons = inherited
        try:
            session.routing_record()
        except transition_workflow.TransitionWorkflowError as error:
            assert "timbering recovery route is mixed" in str(error)
        else:
            raise AssertionError("The inherited B4 route lost its guard")
        assert session.launch_workflow()
        assert session.routing_record() == record

    print(SENTINEL)


if __name__ == "__main__":
    validate()
