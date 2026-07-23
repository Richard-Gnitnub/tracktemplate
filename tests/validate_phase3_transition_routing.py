#!/usr/bin/env python3
"""Validate the fail-closed Phase 3 all-three-functions routing boundary."""

import hashlib
import pathlib
import sys
import tempfile
import types


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import modular_structure  # noqa: E402
from tools import phase3_transition_pilot as transition_pilot  # noqa: E402


LEGACY_SOURCE = '''
MACRO_VERSION_NUMBER = "10.2A8A7B15"

def clothoid_entry_displacement(*arguments):
    return ("legacy-displacement", arguments)

def transition_start_signed_offset(*arguments):
    return ("legacy-offset", clothoid_entry_displacement(*arguments))

def solve_transition_length(*arguments):
    return ("legacy-solver", transition_start_signed_offset(*arguments))

def main_circle_centre(*arguments):
    return clothoid_entry_displacement(*arguments)

def build_concentric_core(*arguments):
    return clothoid_entry_displacement(*arguments)

def prepare_track_alignment(*arguments):
    return (
        transition_start_signed_offset(*arguments),
        solve_transition_length(*arguments),
    )

def run_macro():
    return (
        main_circle_centre("main"),
        build_concentric_core("core"),
        prepare_track_alignment("parallel"),
    )

run_macro()
'''.lstrip()


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _modular_api():
    namespace = {}
    exec(
        '''
def clothoid_entry_displacement(*arguments):
    return ("modular-displacement", arguments)

def transition_start_signed_offset(*arguments):
    return ("modular-offset", clothoid_entry_displacement(*arguments))

def solve_transition_length(*arguments):
    return ("modular-solver", transition_start_signed_offset(*arguments))
'''.lstrip(),
        namespace,
    )
    return types.SimpleNamespace(
        **{
            name: namespace[name]
            for name in transition_pilot.FUNCTION_NAMES
        }
    )


def _contract(source_path):
    return {
        "contract_id": transition_pilot.EXPECTED_CONTRACT_ID,
        "source_state": {
            "b15": {
                "path": source_path.name,
                "sha256": _sha256(source_path),
            }
        },
        "successor": {
            "development_checkpoint_id": transition_pilot.EXPECTED_CHECKPOINT,
        },
        "module_boundary": {
            "functions": [
                {"name": name}
                for name in transition_pilot.FUNCTION_NAMES
            ],
            "external_caller_routes": [
                {"caller": caller, "targets": list(targets)}
                for caller, targets in transition_pilot.CALLER_ROUTES
            ],
        },
    }


def _expect_transition_error(action, required_text):
    try:
        action()
    except transition_pilot.TransitionPilotError as error:
        assert required_text in str(error), str(error)
        return
    raise AssertionError(
        "Expected TransitionPilotError containing {!r}".format(required_text)
    )


def _validate_route_switch(temporary_root):
    source_path = temporary_root / "legacy.FCMacro"
    source_path.write_text(LEGACY_SOURCE, encoding="utf-8")
    contract = _contract(source_path)
    api = _modular_api()
    session = transition_pilot.load_transition_pilot_session(
        temporary_root,
        api,
        contract,
    )
    assert session.active_route is None
    _expect_transition_error(session.launch_workflow, "before launch")

    legacy_record = session.apply_route(transition_pilot.LEGACY_ROUTE)
    legacy_result = session.launch_workflow()
    assert legacy_record == {
        "schema_version": 1,
        "route": "legacy",
        "rollback_route": "legacy",
        "function_names": list(transition_pilot.FUNCTION_NAMES),
        "caller_names": [item[0] for item in transition_pilot.CALLER_ROUTES],
        "legacy_version": "10.2A8A7B15",
        "legacy_source_sha256": contract["source_state"]["b15"]["sha256"],
        "mixed_route": False,
    }
    assert legacy_result[0][0] == "legacy-displacement"
    assert legacy_result[1][0] == "legacy-displacement"
    assert legacy_result[2][0][0] == "legacy-offset"
    assert legacy_result[2][1][0] == "legacy-solver"

    modular_record = session.apply_route(transition_pilot.MODULAR_ROUTE)
    modular_result = session.launch_workflow()
    assert modular_record["route"] == "modular"
    assert modular_record["mixed_route"] is False
    assert modular_result[0][0] == "modular-displacement"
    assert modular_result[1][0] == "modular-displacement"
    assert modular_result[2][0][0] == "modular-offset"
    assert modular_result[2][1][0] == "modular-solver"

    session.apply_route(transition_pilot.LEGACY_ROUTE)
    assert session.launch_workflow() == legacy_result
    before_invalid = {
        name: session.module.__dict__[name]
        for name in transition_pilot.FUNCTION_NAMES
    }
    _expect_transition_error(
        lambda: session.apply_route("mixed"),
        "Unknown transition calculation route",
    )
    assert session.active_route == transition_pilot.LEGACY_ROUTE
    assert before_invalid == {
        name: session.module.__dict__[name]
        for name in transition_pilot.FUNCTION_NAMES
    }


def _validate_fail_closed(temporary_root):
    source_path = temporary_root / "legacy.FCMacro"
    source_path.write_text(LEGACY_SOURCE, encoding="utf-8")
    contract = _contract(source_path)

    wrong_hash = dict(contract)
    wrong_hash["source_state"] = {
        "b15": dict(contract["source_state"]["b15"], sha256="0" * 64)
    }
    _expect_transition_error(
        lambda: transition_pilot.load_transition_pilot_session(
            temporary_root, _modular_api(), wrong_hash
        ),
        "fingerprint drifted",
    )

    wrong_callers = dict(contract)
    wrong_callers["module_boundary"] = dict(contract["module_boundary"])
    wrong_callers["module_boundary"]["external_caller_routes"] = []
    _expect_transition_error(
        lambda: transition_pilot.load_transition_pilot_session(
            temporary_root, _modular_api(), wrong_callers
        ),
        "routing boundary drifted",
    )

    incomplete_api = _modular_api()
    del incomplete_api.solve_transition_length
    _expect_transition_error(
        lambda: transition_pilot.load_transition_pilot_session(
            temporary_root, incomplete_api, contract
        ),
        "modular transition calculation route",
    )

    source_path.write_text(LEGACY_SOURCE.rsplit("run_macro()", 1)[0], encoding="utf-8")
    malformed_contract = _contract(source_path)
    _expect_transition_error(
        lambda: transition_pilot.load_transition_pilot_session(
            temporary_root, _modular_api(), malformed_contract
        ),
        "launch boundary",
    )


def _validate_structure():
    report = modular_structure.structure_report(ROOT)
    assert modular_structure.validate_report(report) == []
    modules = {item["module"]: item for item in report["modules"]}
    assert "tracktemplate.compatibility.transition_pilot" not in modules
    assert (
        modules["tracktemplate.compatibility.b15_workflow_host"]["layer"]
        == "compatibility"
    )
    assert (
        modules["tracktemplate.compatibility.transition_workflow"]["layer"]
        == "compatibility"
    )
    assert (ROOT / "tools" / "phase3_transition_pilot.py").is_file()


def validate():
    with tempfile.TemporaryDirectory(prefix="phase3-transition-route-") as temporary:
        temporary_root = pathlib.Path(temporary)
        _validate_route_switch(temporary_root)
        _validate_fail_closed(temporary_root)
    _validate_structure()
    print("Phase 3 transition routing validation passed")


if __name__ == "__main__":
    validate()
