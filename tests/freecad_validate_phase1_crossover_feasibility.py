"""FreeCAD analytical oracle for the Phase 1 B14 crossover feasibility gap."""

import ast
import hashlib
import json
import math
import pathlib
import sys
import types

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import b14_recipe  # noqa: E402


CONTRACT_PATH = (
    ROOT / "reference" / "contracts" / "phase1-crossover-feasibility.json"
)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_b14(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    final_statement = tree.body[-1] if tree.body else None
    assert (
        isinstance(final_statement, ast.Expr)
        and isinstance(final_statement.value, ast.Call)
        and isinstance(final_statement.value.func, ast.Name)
        and final_statement.value.func.id == "run_macro"
    ), "B14 launch boundary changed"
    tree.body.pop()
    ast.fix_missing_locations(tree)
    module = types.ModuleType("phase1_crossover_feasibility_b14")
    module.__file__ = str(path)
    exec(compile(tree, str(path), "exec"), module.__dict__)
    return module


def _assert_close(actual, expected, tolerance):
    assert math.isclose(
        float(actual),
        float(expected),
        rel_tol=0.0,
        abs_tol=float(tolerance),
    ), (actual, expected)


def _evaluate_witness(module, document, host_a, host_b, request, witness):
    before_objects = [
        (str(obj.Name), str(obj.TypeId))
        for obj in document.Objects
    ]
    solved = module.solve_rea_c10_crossover_geometry(
        document,
        host_a,
        host_b,
        witness["host_a_chainage_mm"],
        request["arrangement"],
        request["handing"],
        request["track_gauge_mm"],
        request["flangeway_mm"],
        request["minimum_radius_mm"],
    )
    metrics_a = module.turnout_mapping_metrics(
        solved["host_a_data"],
        solved["toe_chainage_a"],
        solved["orientation_a"],
        solved["handing"],
        solved["dimensions"],
    )
    metrics_b = module.turnout_mapping_metrics(
        solved["host_b_data"],
        solved["toe_chainage_b"],
        solved["orientation_b"],
        solved["handing"],
        solved["dimensions"],
    )
    components = {
        "turnout_a_mapped_minimum_radius_mm": metrics_a["turnout_minimum_radius"],
        "turnout_b_mapped_minimum_radius_mm": metrics_b["turnout_minimum_radius"],
        "connector_minimum_radius_mm": solved["connector"].get("minimum_radius"),
    }
    complete = min(float(value) for value in components.values())
    tolerance = request["comparison_tolerance_mm"]

    assert witness["current_b14_preview"] == "accepted"
    _assert_close(
        solved["toe_chainage_b"],
        witness["host_b_chainage_mm"],
        tolerance,
    )
    for field, actual in components.items():
        _assert_close(actual, witness[field], tolerance)
    _assert_close(
        complete,
        witness["complete_minimum_radius_mm"],
        tolerance,
    )
    complete_result = (
        "accept"
        if complete >= float(request["minimum_radius_mm"]) - 1.0e-7
        else "reject"
    )
    assert complete_result == witness["complete_rule_result"]
    assert before_objects == [
        (str(obj.Name), str(obj.TypeId))
        for obj in document.Objects
    ], "Analytical feasibility evaluation mutated the document"


def validate():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    b14_state = contract["source_state"]["b14"]
    macro_path = ROOT / b14_state["path"]
    assert _sha256(macro_path) == b14_state["sha256"]
    module = _load_b14(macro_path)
    assert str(module.MACRO_VERSION_NUMBER) == b14_state["version"]

    fixture_contract = contract["fixture"]
    fixture_path = ROOT / fixture_contract["path"]
    assert fixture_path.is_file(), (
        "Build the ignored B14 base fixture first with: {}"
        .format(fixture_contract["reproduction_command"])
    )
    fixture_hash_before = _sha256(fixture_path)
    assert fixture_hash_before == fixture_contract["sha256"]

    document = App.openDocument(str(fixture_path))
    try:
        snapshot = b14_recipe.freecad_base_snapshot(module, document)
        assert snapshot["semantic_sha256"] == fixture_contract["semantic_sha256"]
        assert len(document.Objects) == fixture_contract["object_count"]
        hosts = module.turnout_host_objects(document)
        selection = b14_recipe.select_crossover_hosts(
            hosts,
            module.object_string_property,
            module._integer_object_property,
        )
        host_a = hosts[selection["a"]]
        host_b = hosts[selection["b"]]
        for key, expected in fixture_contract["host_a_identity"].items():
            assert selection["host_a_identity"][key] == expected
        for key, expected in fixture_contract["host_b_identity"].items():
            assert selection["host_b_identity"][key] == expected

        for witness in contract["witnesses"]:
            _evaluate_witness(
                module,
                document,
                host_a,
                host_b,
                contract["request"],
                witness,
            )
        assert len(document.Objects) == fixture_contract["object_count"]
    finally:
        App.closeDocument(document.Name)

    assert _sha256(fixture_path) == fixture_hash_before
    print("Phase 1 crossover feasibility FreeCAD oracle passed")


def _run_as_script():
    try:
        validate()
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


if __name__ in {"__main__", "freecad_validate_phase1_crossover_feasibility"}:
    _run_as_script()
