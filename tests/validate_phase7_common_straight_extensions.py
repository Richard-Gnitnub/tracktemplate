#!/usr/bin/env python3
"""Prove common straight-end calculations and in-place host compatibility."""

import ast
import copy
import hashlib
import json
import math
import pathlib
import sys
import types


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import (  # noqa: E402
    b15_workflow_host as host_loader,
    transition_workflow as workflow,
)
import validate_phase7_concentric_core as core_proof  # noqa: E402


EXTENSION_KEYS = (
    "entry_extension", "exit_extension", "total_length",
    "extended_start", "extended_end",
)
TOLERANCE = 1.0e-8
Vector = core_proof.Vector


def legacy_calculations(path):
    """Load frozen arithmetic with the existing vector fixture boundary."""
    namespace, definitions = core_proof.legacy_calculations(path)
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {
        "dot_xy", "add_common_straight_extensions", "prepare_track_alignment",
        "effective_constant_radius", "signed_side_factor",
    }
    added = {
        node.name: node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    }
    assert set(added) == names
    constants = {
        target.id: ast.literal_eval(node.value)
        for node in tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
        and target.id in {"MODE_MATCH_SPACINGS", "MODE_USE_LENGTHS"}
    }
    assert set(constants) == {"MODE_MATCH_SPACINGS", "MODE_USE_LENGTHS"}
    namespace.update(constants)
    module = ast.Module(body=list(added.values()), type_ignores=[])
    exec(compile(module, str(path), "exec"), namespace)
    return namespace, dict(definitions, **added)


def _synthetic_record(start_x, end_projection, offset, angle, label):
    tangent_x, tangent_y = math.cos(angle), math.sin(angle)
    start = (float(start_x), float(offset))
    end = (
        end_projection * tangent_x - offset * tangent_y,
        end_projection * tangent_y + offset * tangent_x,
    )
    return {
        "label": label,
        "points": [Vector(*start, 0.0), Vector(*end, 0.0)],
        "headings": [0.0, angle],
        "start": start,
        "end": end,
        "core_length": 100.0,
        "unrelated_metadata": {"preserve": label},
    }


def calculation_groups(namespace):
    """Return direct boundary groups and accepted-builder track records."""
    groups = [("empty", [], 0.0), ("empty-nonfinite", [], math.inf)]
    layouts = (
        ((0.0, 10.0, 0.0),),
        ((0.0, 10.0, 0.0), (0.0, 10.0, 50.0)),
        ((0.0, 10.0, 0.0), (4.0, 6.0, 50.0)),
        ((4.0, 10.0, 0.0), (0.0, 6.0, 50.0)),
        ((0.0, 6.0, -50.0), (4.0, 10.0, 0.0), (2.0, 8.0, 50.0)),
    )
    for angle in (0.0, math.pi / 6.0, math.pi / 2.0, math.pi, -math.pi / 6.0):
        for layout_index, layout in enumerate(layouts):
            records = [
                _synthetic_record(*values, angle, str(index))
                for index, values in enumerate(layout)
            ]
            groups.append((f"direct-{angle}-{layout_index}", records, angle))
            if len(records) > 1:
                groups.append((
                    f"reverse-{angle}-{layout_index}",
                    copy.deepcopy(list(reversed(records))), angle,
                ))
    for delta in (
        0.0, 1.0e-9, TOLERANCE,
        math.nextafter(TOLERANCE, math.inf), 1.0e-7,
    ):
        records = [
            _synthetic_record(0.0, 0.0, 0.0, 0.0, "anchor"),
            _synthetic_record(delta, -delta, 50.0, 0.0, "threshold"),
        ]
        groups.append((f"threshold-{delta}", records, 0.0))

    angle = math.pi / 2.0
    centre = namespace["main_circle_centre"](600.0, 600.0)
    main = namespace["build_concentric_core"](
        centre, 600.0, 600.0, 600.0, angle, "Main Track",
    )
    config = {
        "name": "Outside Track", "side": "Outside",
        "alignment_mode": namespace["MODE_MATCH_SPACINGS"],
        "start_spacing": 50.0, "curve_spacing": 55.0,
        "finish_spacing": 50.0, "entry_transition_length": 600.0,
        "exit_transition_length": 600.0, "width": 75.0,
        "create_template": True, "show_centreline": True,
    }
    matched = namespace["prepare_track_alignment"](
        copy.deepcopy(config), centre, 600.0, angle, main,
    )
    config["alignment_mode"] = namespace["MODE_USE_LENGTHS"]
    config["name"] = "Manual Track"
    manual = namespace["prepare_track_alignment"](
        copy.deepcopy(config), centre, 600.0, angle, main,
    )
    for name, records in (
        ("main", [main]), ("main-matched", [main, matched]),
        ("main-manual", [main, manual]),
        ("main-matched-manual", [main, matched, manual]),
        ("permuted-builders", [manual, main, matched]),
    ):
        groups.append((name, copy.deepcopy(records), angle))
    return groups


def _snapshot(value):
    if isinstance(value, dict):
        return (
            "dict", tuple((key, _snapshot(item)) for key, item in value.items()),
        )
    if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
        return ("vector", value.x, value.y, value.z)
    if isinstance(value, list):
        return ("list", tuple(_snapshot(item) for item in value))
    if isinstance(value, tuple):
        return ("tuple", tuple(_snapshot(item) for item in value))
    return (type(value).__name__, value)


def check_host_call(function, alignments, angle):
    """Assert values and every pre-existing mutable or vector identity."""
    outer = alignments
    references = [
        (item, item["points"], item["headings"], tuple(item["points"]),
         tuple(item["headings"]), tuple(item), _snapshot(item))
        for item in alignments
    ]
    result = function(alignments, angle)
    assert result is None and alignments is outer
    for current, saved in zip(alignments, references):
        (item, points, headings, old_points, old_headings,
         old_keys, _before) = saved
        assert current is item
        assert item["points"] is points and item["headings"] is headings
        entry_added = item["entry_extension"] > TOLERANCE
        exit_added = item["exit_extension"] > TOLERANCE
        start = int(entry_added)
        assert len(points) == len(old_points) + start + int(exit_added)
        assert all(
            points[start + index] is point
            for index, point in enumerate(old_points)
        )
        assert headings[start:start + len(old_headings)] == list(old_headings)
        if entry_added:
            assert _snapshot(points[0]) == (
                "vector", *item["extended_start"], 0.0,
            )
            assert headings[0] == 0.0
        if exit_added:
            assert _snapshot(points[-1]) == (
                "vector", *item["extended_end"], 0.0,
            )
            assert headings[-1] == angle
        expected_keys = list(old_keys) + [
            key for key in EXTENSION_KEYS if key not in old_keys
        ]
        assert list(item) == expected_keys
        assert item["total_length"] == (
            item["core_length"] + item["entry_extension"]
            + item["exit_extension"]
        )
        old_mapping = dict(_before[1])
        for key in old_keys:
            if key not in {"points", "headings", *EXTENSION_KEYS}:
                assert _snapshot(item[key]) == old_mapping[key]
    return _snapshot(alignments)


def malformed_observations(namespace):
    """Retain unsupported malformed-record mutation evidence explicitly."""
    observations = []
    function = namespace["add_common_straight_extensions"]
    for missing in ("start", "end", "points", "headings", "core_length"):
        records = [
            _synthetic_record(0.0, 10.0, 0.0, 0.0, "anchor"),
            _synthetic_record(4.0, 6.0, 50.0, 0.0, "late"),
        ]
        del records[1][missing]
        before = _snapshot(records)
        try:
            function(records, 0.0)
        except Exception as error:
            failure = (type(error).__name__, str(error))
        else:
            raise AssertionError("Malformed record unexpectedly succeeded")
        observations.append({
            "missing": missing, "before": before, "after": _snapshot(records),
            "failure": failure, "scope": "unsupported-internal-record",
        })
    return observations


def characterize_legacy():
    namespaces = []
    definitions = []
    for relative, expected in core_proof.centre_proof.SOURCE_HASHES.items():
        path = ROOT / relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
        namespace, nodes = legacy_calculations(path)
        namespaces.append(namespace)
        definitions.append(nodes)
    for name in definitions[0]:
        assert ast.dump(definitions[0][name]) == ast.dump(definitions[1][name])
    groups = [calculation_groups(namespace) for namespace in namespaces]
    assert len(groups[0]) == len(groups[1])
    results = []
    for left, right in zip(*groups):
        name, first, angle = left
        assert right[0] == name and _snapshot(first) == _snapshot(right[1])
        snapshots = [
            check_host_call(namespace["add_common_straight_extensions"],
                            group[1], group[2])
            for namespace, group in zip(namespaces, (left, right))
        ]
        assert snapshots[0] == snapshots[1]
        repeated = [
            check_host_call(namespace["add_common_straight_extensions"],
                            group[1], group[2])
            for namespace, group in zip(namespaces, (left, right))
        ]
        assert repeated[0] == repeated[1]
        results.append({
            "name": name, "angle": angle, "result": snapshots[0],
            "repeated_result": repeated[0],
        })
    invalid = [malformed_observations(namespace) for namespace in namespaces]
    assert invalid[0] == invalid[1]
    payload = {
        "status": "PASS", "groups": len(results),
        "source_sha256": core_proof.centre_proof.SOURCE_HASHES,
        "complete_results": results,
        "unsupported_malformed_observations": invalid[0],
    }
    print(json.dumps(payload, sort_keys=True))
    print(
        "Phase 7 B14/B15 common straight extensions characterization passed:"
        f" {len(results)} groups"
    )
    return namespaces, definitions


RESULT_KEYS = EXTENSION_KEYS + ("entry_point", "exit_point")
FUNCTION_NAMES = core_proof.FUNCTION_NAMES + (
    "add_common_straight_extensions",
)


def neutral_inputs(records):
    return [
        {"start": item["start"], "end": item["end"],
         "core_length": item["core_length"]}
        for item in records
    ]


def validate_calculations():
    namespaces, _definitions = characterize_legacy()
    assert api.add_common_straight_extensions.__module__ == (
        "tracktemplate.domain.alignment"
    )
    assert "add_common_straight_extensions" in api.__all__
    for name, records, angle in calculation_groups(namespaces[0]):
        original = copy.deepcopy(records)
        inputs = neutral_inputs(records)
        before = _snapshot(inputs)
        result = api.add_common_straight_extensions(inputs, angle)
        assert _snapshot(inputs) == before
        repeated = api.add_common_straight_extensions(inputs, angle)
        assert repeated == result and repeated is not result
        legacy = copy.deepcopy(records)
        namespaces[0]["add_common_straight_extensions"](legacy, angle)
        assert len(result) == len(legacy)
        for item, expected, again in zip(result, legacy, repeated):
            assert tuple(item) == RESULT_KEYS and item is not again
            assert {key: item[key] for key in EXTENSION_KEYS} == {
                key: expected[key] for key in EXTENSION_KEYS
            }, name
            assert item["entry_point"] == (
                expected["extended_start"]
                if expected["entry_extension"] > TOLERANCE else None
            )
            assert item["exit_point"] == (
                expected["extended_end"]
                if expected["exit_extension"] > TOLERANCE else None
            )
        adapter = workflow._CommonStraightExtensionsAdapter(
            api.add_common_straight_extensions, Vector,
        )
        assert check_host_call(adapter, records, angle) == _snapshot(legacy)
        namespaces[0]["add_common_straight_extensions"](legacy, angle)
        assert check_host_call(adapter, records, angle) == _snapshot(legacy)

        if original:
            tangent = (math.cos(angle), math.sin(angle))
            common_projection = max(
                x["end"][0] * tangent[0] + x["end"][1] * tangent[1]
                for x in original
            )
            for old, extended in zip(original, result):
                assert extended["extended_start"][0] == min(
                    x["start"][0] for x in original
                )
                end = extended["extended_end"]
                assert abs(
                    end[0] * tangent[0] + end[1] * tangent[1]
                    - common_projection
                ) <= TOLERANCE + 1.0e-10
                # Extension follows the tangent, preserving normal spacing.
                assert abs(
                    -(end[0] - old["end"][0]) * tangent[1]
                    + (end[1] - old["end"][1]) * tangent[0]
                ) <= 1.0e-10
            assert api.add_common_straight_extensions(
                list(reversed(inputs)), angle,
            ) == list(reversed(result))

    contract = json.loads((
        ROOT / "reference/contracts/phase7-common-straight-extensions.json"
    ).read_text())
    assert contract["contract_id"] == (
        "tracktemplate:phase7:common-straight-extensions:1"
    )
    assert contract["authority"] == ["D-GOV-004", "D-P7-001"]
    assert contract["calculation"]["input_keys"] == [
        "start", "end", "core_length",
    ]
    assert contract["calculation"]["result_keys"] == list(RESULT_KEYS)
    assert contract["calculation"]["geometry_tolerance"] == TOLERANCE
    assert contract["product_routing"]["record_schema_version"] == 5
    assert contract["product_routing"]["function_names"] == (
        list(FUNCTION_NAMES)
    )


def validate_vector_failure():
    """Keep inherited partial list mutation if host vector creation fails."""
    namespace, _definitions = legacy_calculations(
        ROOT / "AdvancedTurnout.FCMacro"
    )
    for fail_at in (1, 2):
        snapshots = []
        for modular in (False, True):
            records = [
                _synthetic_record(0.0, 10.0, 0.0, 0.0, "anchor"),
                _synthetic_record(4.0, 6.0, 50.0, 0.0, "both"),
            ]
            count = 0

            def failing_vector(x, y, z):
                nonlocal count
                count += 1
                if count == fail_at:
                    raise RuntimeError("Injected vector construction failure")
                return Vector(x, y, z)

            if modular:
                function = workflow._CommonStraightExtensionsAdapter(
                    api.add_common_straight_extensions, failing_vector,
                )
            else:
                namespace["App"] = types.SimpleNamespace(
                    Vector=failing_vector,
                )
                function = namespace["add_common_straight_extensions"]
            try:
                function(records, 0.0)
            except RuntimeError as error:
                assert str(error) == "Injected vector construction failure"
            else:
                raise AssertionError("Expected injected vector failure")
            assert count == fail_at
            snapshots.append(_snapshot(records))
        assert snapshots[0] == snapshots[1]


def validate_binding():
    import dataclasses
    import inspect
    import tempfile

    prefix = "tracktemplate-phase7-ends-"
    with tempfile.TemporaryDirectory(prefix=prefix) as path:
        temporary = pathlib.Path(path)
        contract = core_proof._fixture(temporary)

        def load_host():
            return host_loader.load_b15_workflow_host(temporary, contract)

        functions = core_proof._functions()
        session = workflow.load_modular_transition_workflow_session(
            temporary, api, contract,
        )
        assert session.launch_workflow() == core_proof._expected()
        assert session.routing_record()["schema_version"] == 5
        assert session.routing_record()["contract_id"] == (
            "tracktemplate:phase7:common-straight-extensions:1"
        )
        assert session.routing_record()["function_names"] == (
            list(FUNCTION_NAMES)
        )
        adapter = session.module.add_common_straight_extensions
        assert type(adapter) is workflow._CommonStraightExtensionsAdapter
        assert adapter.calculation is api.add_common_straight_extensions
        assert adapter.vector_factory is session.module.App.Vector
        assert tuple(inspect.signature(adapter).parameters) == (
            "alignments", "total_angle",
        )
        assert [field.name for field in dataclasses.fields(adapter)] == [
            "calculation", "vector_factory",
        ]
        try:
            adapter.calculation = None
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("Extension adapter is mutable")
        empty = []
        assert adapter(empty, math.inf) is None and empty == []

        for missing in FUNCTION_NAMES:
            host = load_host()
            before = core_proof._snapshot(host)
            incomplete = dict(functions)
            incomplete.pop(missing)
            core_proof.centre_proof._expect_error(
                lambda: workflow.ModularTransitionWorkflowSession(
                    host, incomplete,
                ),
                "complete seven-function",
            )
            assert core_proof._snapshot(host) == before

        for remove_previous in (False, True):
            host = load_host()
            if remove_previous:
                del host.module.add_common_straight_extensions
            runner = host.module.run_macro
            host.module.run_macro = core_proof.detached(
                runner, "add_common_straight_extensions",
                api.add_common_straight_extensions,
            )
            before = core_proof._snapshot(host)
            core_proof.centre_proof._expect_error(
                lambda: workflow.ModularTransitionWorkflowSession(
                    host, functions,
                ),
                "caller 'run_macro' is unavailable",
            )
            assert core_proof._snapshot(host) == before
            assert host.module.LAUNCH_COUNT == 0

        session.module.add_common_straight_extensions = None
        core_proof.centre_proof._expect_error(
            session.routing_record, "mixed 'add_common_straight_extensions'",
        )
        assert session.launch_workflow() == core_proof._expected()
        assert session.module.add_common_straight_extensions is adapter

        # Corrupt only the newly added adapter; keep the core adapter valid.
        class WrongAdapter(workflow._CommonStraightExtensionsAdapter):
            pass

        corrupt_adapters = (
            workflow._CommonStraightExtensionsAdapter(
                lambda *values: [], adapter.vector_factory,
            ),
            workflow._CommonStraightExtensionsAdapter(
                adapter.calculation, lambda *values: None,
            ),
            WrongAdapter(adapter.calculation, adapter.vector_factory),
        )
        for corrupt in corrupt_adapters:
            saved = session._host_functions["add_common_straight_extensions"]
            session._host_functions["add_common_straight_extensions"] = corrupt
            before = core_proof._snapshot(session)
            count = session.module.LAUNCH_COUNT
            core_proof.centre_proof._expect_error(
                session.launch_workflow, "straight-extension adapter",
            )
            assert core_proof._snapshot(session) == before
            assert session.module.LAUNCH_COUNT == count
            session._host_functions["add_common_straight_extensions"] = saved
            assert session.launch_workflow() == core_proof._expected()


def main():
    validate_calculations()
    validate_vector_failure()
    validate_binding()
    print(
        "Phase 7 common straight extensions calculation and routing "
        "validation passed"
    )


if __name__ == "__main__":
    if sys.argv[1:] == ["--characterize"]:
        characterize_legacy()
    else:
        main()
