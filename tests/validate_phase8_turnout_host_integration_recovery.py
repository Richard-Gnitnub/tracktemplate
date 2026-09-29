#!/usr/bin/env python3
"""Check turnout host transaction containment and inherited GUI routing."""

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
from tracktemplate.compatibility.turnout_host_integration_recovery import (  # noqa: E402
    TurnoutHostIntegrationRecoveryAdapter,
    TurnoutHostIntegrationRecoveryError,
)
import validate_phase7_concentric_core as core_proof  # noqa: E402


SENTINEL = "Phase 8 turnout host integration adapter validation passed"


class _Document:
    def __init__(self):
        self.UndoMode = 1
        self.items = ["source"]
        self.undo_count = 0
        self._before = None

    def openTransaction(self, _label):
        assert self._before is None
        self._before = list(self.items)

    def commitTransaction(self):
        assert self._before is not None
        self._before = None
        self.undo_count += 1

    def abortTransaction(self):
        assert self._before is not None
        self.items = self._before
        self._before = None


_INHERITED = """
def create_turnout_host_integration(doc, turnout_id):
    doc.items.append("chair-clear")
    if failure == "create-before-open":
        raise RuntimeError("injected before inherited transaction")
    label = "Integrate Version {} turnout {} into host template".format(
        MACRO_VERSION_NUMBER, turnout_id,
    )
    if failure == "wrong-label":
        label += " drift"
    doc.openTransaction(label)
    doc.items.append("integrated")
    if failure != "missing-commit":
        doc.commitTransaction()
    return turnout_id

def remove_turnout_host_integration(doc, turnout_id):
    doc.items.append("chair-clear")
    if failure == "remove-before-open":
        raise RuntimeError("injected before inherited transaction")
    doc.openTransaction(
        "Remove Version {} turnout host integration {}".format(
            MACRO_VERSION_NUMBER, turnout_id,
        )
    )
    doc.items.append("restored")
    doc.commitTransaction()
    return turnout_id
"""


def _adapter():
    module = types.ModuleType("turnout_host_recovery_probe")
    module.MACRO_VERSION_NUMBER = "10.2A8A7B15"
    module.failure = None
    exec(_INHERITED, module.__dict__)
    adapter = TurnoutHostIntegrationRecoveryAdapter(
        module,
        module.create_turnout_host_integration,
        module.remove_turnout_host_integration,
    )
    return module, adapter


def _expect_error(action, error_type, fragment):
    try:
        action()
    except error_type as error:
        assert fragment in str(error), str(error)
    else:
        raise AssertionError("Unsafe host integration was accepted")


def validate_recovery():
    module, adapter = _adapter()
    document = _Document()
    document.UndoMode = 0
    _expect_error(
        lambda: adapter.create(document, "TO-001"),
        TurnoutHostIntegrationRecoveryError, "Enable document Undo",
    )
    _expect_error(
        lambda: adapter.remove(document, "TO-001"),
        TurnoutHostIntegrationRecoveryError, "Enable document Undo",
    )
    assert document.items == ["source"] and document.undo_count == 0
    document.UndoMode = 1

    for fault, action, error_type, fragment in (
        ("create-before-open", adapter.create, RuntimeError, "injected"),
        ("remove-before-open", adapter.remove, RuntimeError, "injected"),
        ("wrong-label", adapter.create,
         TurnoutHostIntegrationRecoveryError, "transaction changed"),
        ("missing-commit", adapter.create,
         TurnoutHostIntegrationRecoveryError, "did not commit once"),
    ):
        module.failure = fault
        _expect_error(
            lambda: action(document, "TO-001"), error_type, fragment,
        )
        assert document.items == ["source"] and document.undo_count == 0
        assert document._before is None

    module.failure = None
    assert adapter.create(document, "TO-001") == "TO-001"
    assert document.items == ["source", "chair-clear", "integrated"]
    assert document.undo_count == 1
    assert adapter.remove(document, "TO-001") == "TO-001"
    assert document.items[-2:] == ["chair-clear", "restored"]
    assert document.undo_count == 2

    foreign = types.ModuleType("foreign")
    exec("def command(doc, turnout_id): pass", foreign.__dict__)
    changed = TurnoutHostIntegrationRecoveryAdapter(
        module, foreign.command, adapter.original_remove,
    )
    untouched = _Document()
    _expect_error(
        lambda: changed.create(untouched, "TO-001"),
        TurnoutHostIntegrationRecoveryError, "command changed",
    )
    assert untouched.items == ["source"] and untouched.undo_count == 0


_ROUTE = """
def create_turnout_host_integration(*arguments):
    return arguments
def remove_turnout_host_integration(*arguments):
    return arguments
def build_turnout_host_integration(*arguments):
    return arguments
def turnout_integration_by_id(*arguments):
    return arguments
def clear_chair_analysis_display(*arguments):
    return arguments
class TurnoutManagerDialog:
    def integrate_selected_turnout(self):
        return create_turnout_host_integration(self.doc, "TO-001")
    def remove_selected_integration(self):
        return remove_turnout_host_integration(self.doc, "TO-001")
"""


def _functions():
    return {
        name: getattr(api, name)
        for name in transition_workflow.PRODUCT_FUNCTION_NAMES
    }


def validate_binding():
    with tempfile.TemporaryDirectory(prefix="phase8-turnout-host-route-") as path:
        root = pathlib.Path(path)
        contract = core_proof._fixture(root)
        host = b15_workflow_host.load_b15_workflow_host(root, contract)
        namespace = host.module.__dict__
        exec(_ROUTE, namespace)
        original_create = namespace["create_turnout_host_integration"]
        original_remove = namespace["remove_turnout_host_integration"]
        session = transition_workflow.ModularTransitionWorkflowSession(
            host, _functions(),
        )
        record = session.routing_record()
        assert namespace["create_turnout_host_integration"] is not original_create
        assert namespace["remove_turnout_host_integration"] is not original_remove
        panel = namespace["TurnoutManagerDialog"]
        caller = panel.__dict__["integrate_selected_turnout"]
        panel.integrate_selected_turnout = lambda self: None
        try:
            _expect_error(
                session.routing_record,
                transition_workflow.TransitionWorkflowError,
                "turnout host integration route is mixed",
            )
        finally:
            panel.integrate_selected_turnout = caller
        assert session.routing_record() == record

        incomplete = b15_workflow_host.load_b15_workflow_host(root, contract)
        incomplete_namespace = incomplete.module.__dict__
        exec(_ROUTE, incomplete_namespace)
        del incomplete_namespace["remove_turnout_host_integration"]
        _expect_error(
            lambda: transition_workflow.ModularTransitionWorkflowSession(
                incomplete, _functions(),
            ),
            transition_workflow.TransitionWorkflowError,
            "turnout host integration boundary is incomplete",
        )


def validate():
    validate_recovery()
    validate_binding()
    print(SENTINEL)


if __name__ == "__main__":
    validate()
