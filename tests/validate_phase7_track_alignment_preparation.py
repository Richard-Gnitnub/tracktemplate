#!/usr/bin/env python3
"""Prove complete three-mode track preparation and atomic B16 routing."""

import ast
import copy
import hashlib
import inspect
import json
import math
import pathlib
import subprocess
import sys
import tempfile
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow  # noqa: E402
from tracktemplate.domain import alignment  # noqa: E402
import validate_phase7_concentric_core as core_proof  # noqa: E402
import validate_phase7_platform_transitions as transition_proof  # noqa: E402


SENTINEL = "Phase 7 track-alignment preparation and routing validation passed"
PARAMETERS = (
    "config",
    "circle_centre",
    "main_radius",
    "total_angle",
    "main_alignment",
)
PUBLIC = (
    "signed_side_factor",
    "effective_constant_radius",
    "prepare_track_alignment",
)
PREPARATION_DEPENDENCIES = (
    "signed_side_factor",
    "effective_constant_radius",
    "transition_start_signed_offset",
    "solve_transition_length",
    "build_concentric_core",
    "solve_platform_shape_parameter",
    "build_platform_core",
)
RESULT_METADATA = (
    "name", "side", "alignment_mode", "start_spacing", "curve_spacing",
    "finish_spacing", "width", "create_template", "show_centreline",
)


class _TrackedConfig(dict):
    """Record only in-place writes while retaining ordinary dict behaviour."""

    def __init__(self, source):
        super().__init__(copy.deepcopy(source))
        self.writes = []

    def __setitem__(self, key, value):
        self.writes.append([key, _snapshot(value)])
        super().__setitem__(key, value)


def _snapshot(value):
    """Return one host-neutral, ordering-sensitive value."""
    if isinstance(value, dict):
        return [
            [key, _snapshot(item)]
            for key, item in value.items()
        ]
    if hasattr(value, "x") and hasattr(value, "y"):
        return [_snapshot(value.x), _snapshot(value.y)]
    if isinstance(value, (tuple, list)):
        return [_snapshot(item) for item in value]
    if isinstance(value, float):
        return {"float": value.hex()}
    return value


def _observe(function, config, circle_centre, main_radius, total_angle, main):
    before_keys = tuple(config)
    metadata = config["metadata"]
    try:
        value = function(
            config,
            circle_centre,
            main_radius,
            total_angle,
            main,
        )
    except Exception as error:  # noqa: BLE001 - exact inherited failure proof
        result = {
            "exception": type(error).__name__,
            "message": str(error),
        }
    else:
        result = {"value": _snapshot(value), "keys": list(value)}
    assert tuple(config) == before_keys
    assert config["metadata"] is metadata
    return {
        "config": _snapshot(config),
        "writes": list(getattr(config, "writes", ())),
        "result": result,
    }


def _legacy_namespaces():
    records = []
    definitions = []
    for path in (transition_proof.B14, transition_proof.B15):
        namespace, nodes = transition_proof.legacy_namespace(path)
        records.append(namespace)
        definitions.append({
            name: ast.dump(nodes[name], include_attributes=False)
            for name in PUBLIC
        })
    assert definitions[0] == definitions[1]
    return records


def _main(namespace):
    centre = namespace["main_circle_centre"](600.0, 600.0)
    main = namespace["build_concentric_core"](
        centre,
        600.0,
        600.0,
        600.0,
        math.pi / 2.0,
        "Main Track",
    )
    return centre, main


def _config(mode, side, **changes):
    config = {
        "name": "{} {}".format(side, mode),
        "side": side,
        "alignment_mode": mode,
        "start_spacing": 50.0,
        "curve_spacing": 45.0 if side == "Inside" else 55.0,
        "finish_spacing": 50.0,
        "entry_transition_length": 600.0,
        "exit_transition_length": 600.0,
        "width": 32.0,
        "create_template": True,
        "show_centreline": True,
        "metadata": {"stable_id": "{}-{}".format(side, mode)},
    }
    config.update(changes)
    return config


def _cases(namespace):
    """Cover every mode and side with valid inherited input preparation."""
    cases = []
    for side in ("Outside", "Inside"):
        matched = _config(namespace["MODE_MATCH_SPACINGS"], side)
        solved = copy.deepcopy(matched)
        centre, main = _main(namespace)
        namespace["prepare_track_alignment"](
            solved, centre, 600.0, math.pi / 2.0, main,
        )
        manual = _config(
            namespace["MODE_USE_LENGTHS"],
            side,
            entry_transition_length=solved["entry_transition_length"],
            exit_transition_length=solved["exit_transition_length"],
        )
        platform = _config(
            namespace["MODE_PLATFORM"],
            side,
            start_spacing=60.0 if side == "Inside" else 40.0,
            finish_spacing=60.0 if side == "Inside" else 40.0,
        )
        cases.extend((matched, manual, platform))
    return cases


def _invalid_cases(namespace):
    match = namespace["MODE_MATCH_SPACINGS"]
    manual = namespace["MODE_USE_LENGTHS"]
    platform = namespace["MODE_PLATFORM"]
    centre, main = _main(namespace)
    solved = _config(match, "Inside")
    namespace["prepare_track_alignment"](
        solved, centre, 600.0, math.pi / 2.0, main,
    )
    return (
        (
            _config(match, "Outside", start_spacing=0.0),
            "All spacing and width values",
        ),
        (
            _config(match, "Outside", curve_spacing=0.0),
            "All spacing and width values",
        ),
        (
            _config(match, "Outside", finish_spacing=0.0),
            "All spacing and width values",
        ),
        (
            _config(match, "Outside", width=0.0),
            "All spacing and width values",
        ),
        (
            _config(match, "Inside", curve_spacing=599.0, width=4.0),
            "constant radius",
        ),
        (_config("Unknown", "Outside"), "Unknown alignment mode"),
        (_config(
            platform,
            "Outside",
            entry_transition_length=0.0,
            exit_transition_length=0.0,
        ), "positive Entry transition"),
        (_config(
            platform,
            "Outside",
            entry_transition_length=600.0,
            exit_transition_length=0.0,
        ), "positive Exit transition"),
        (_config(
            manual,
            "Inside",
            entry_transition_length=4000.0,
            exit_transition_length=solved["exit_transition_length"],
        ), "manual entry Euler easement"),
        (_config(
            manual,
            "Inside",
            entry_transition_length=solved["entry_transition_length"],
            exit_transition_length=4000.0,
        ), "manual exit Euler easement"),
        (
            _config(match, "Outside", start_spacing=1.0e6),
            "Entry spacing",
        ),
        (_config(
            manual,
            "Outside",
            entry_transition_length=1100.0,
            exit_transition_length=1100.0,
        ), "consume more angle"),
        (
            _config(platform, "Outside", start_spacing=1.0e6),
            "Entry platform spacing",
        ),
        (
            _config(
                platform,
                "Outside",
                start_spacing=40.0,
                finish_spacing=1.0e6,
            ),
            "Exit platform spacing",
        ),
        (_config(
            platform,
            "Outside",
            start_spacing=40.0,
            finish_spacing=40.0,
            width=1309.0,
        ), "peak minimum radius"),
    )


def _candidate_main():
    centre = api.main_circle_centre(600.0, 600.0)
    main = api.build_concentric_core(
        centre,
        600.0,
        600.0,
        600.0,
        math.pi / 2.0,
        "Main Track",
    )
    return centre, main


def _result_keys(mode, namespace):
    if mode == namespace["MODE_PLATFORM"]:
        mode_specific = (
            "entry_shape_parameter", "exit_shape_parameter",
            "minimum_radius",
        )
    else:
        mode_specific = ("minimum_radius",)
    return list(core_proof.RESULT_KEYS + mode_specific + RESULT_METADATA)


def _validate_host_independence():
    script = """
import importlib.abc
import sys

blocked = {{
    "FreeCAD", "FreeCADGui", "Part", "PySide", "PySide2", "PySide6",
    "PyQt5", "PyQt6", "pivy", "qtpy",
}}
attempted = []

class Blocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in blocked:
            attempted.append(fullname)
            raise ModuleNotFoundError(fullname)
        return None

sys.meta_path.insert(0, Blocker())
sys.path.insert(0, {root!r})
from tracktemplate import api
from tracktemplate.domain import alignment

public = {public!r}
assert all(getattr(api, name) is getattr(alignment, name) for name in public)
assert all(name in api.__all__ and name in alignment.__all__ for name in public)
assert not attempted, attempted
""".format(root=str(ROOT), public=PUBLIC)
    completed = subprocess.run(
        [sys.executable, "-I", "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def validate_calculation():
    legacy = _legacy_namespaces()
    for name in PUBLIC:
        assert getattr(api, name) is getattr(alignment, name)
        assert name in api.__all__ and name in alignment.__all__
    assert tuple(inspect.signature(api.prepare_track_alignment).parameters) == (
        PARAMETERS
    )
    assert all(
        parameter.default is inspect.Parameter.empty
        for parameter in inspect.signature(
            api.prepare_track_alignment
        ).parameters.values()
    )
    assert api.signed_side_factor("Inside") == 1.0
    assert api.signed_side_factor("Outside") == -1.0
    assert api.signed_side_factor(object()) == -1.0
    assert api.effective_constant_radius(600.0, 55.0, "Inside") == 545.0
    assert api.effective_constant_radius(600.0, 55.0, "Outside") == 655.0

    centre, candidate_main = _candidate_main()
    candidate_main_before = _snapshot(candidate_main)
    for source in _cases(legacy[0]):
        expected_records = []
        for namespace in legacy:
            legacy_centre, legacy_main = _main(namespace)
            config = _TrackedConfig(source)
            expected_records.append(_observe(
                namespace["prepare_track_alignment"],
                config,
                legacy_centre,
                600.0,
                math.pi / 2.0,
                legacy_main,
            ))
        assert expected_records[0] == expected_records[1]

        config = _TrackedConfig(source)
        actual = _observe(
            api.prepare_track_alignment,
            config,
            centre,
            600.0,
            math.pi / 2.0,
            candidate_main,
        )
        assert actual == expected_records[0]
        assert actual["result"]["keys"] == _result_keys(
            source["alignment_mode"], legacy[0],
        )
        assert _snapshot(candidate_main) == candidate_main_before
        assert actual["writes"] == [
            ["entry_transition_length", _snapshot(config["entry_transition_length"])],
            ["exit_transition_length", _snapshot(config["exit_transition_length"])],
            ["start_spacing", _snapshot(config["start_spacing"])],
            ["finish_spacing", _snapshot(config["finish_spacing"])],
        ]
        assert "value" in actual["result"]
        result = api.prepare_track_alignment(
            _TrackedConfig(source),
            centre,
            600.0,
            math.pi / 2.0,
            candidate_main,
        )
        assert all(type(point) is tuple and len(point) == 2
                   for point in result["points"])

        repeated_config = _TrackedConfig(source)
        repeated = api.prepare_track_alignment(
            repeated_config,
            centre,
            600.0,
            math.pi / 2.0,
            candidate_main,
        )
        assert repeated == result
        assert repeated is not result
        assert repeated["points"] is not result["points"]
        assert repeated["headings"] is not result["headings"]
        assert not ({id(point) for point in repeated["points"]}
                    & {id(point) for point in result["points"]})

    for source, diagnostic in _invalid_cases(legacy[0]):
        expected_records = []
        for namespace in legacy:
            legacy_centre, legacy_main = _main(namespace)
            expected_records.append(_observe(
                namespace["prepare_track_alignment"],
                _TrackedConfig(source),
                legacy_centre,
                600.0,
                math.pi / 2.0,
                legacy_main,
            ))
        assert expected_records[0] == expected_records[1]
        actual = _observe(
            api.prepare_track_alignment,
            _TrackedConfig(source),
            centre,
            600.0,
            math.pi / 2.0,
            candidate_main,
        )
        assert actual == expected_records[0]
        assert "exception" in actual["result"]
        assert diagnostic in actual["result"]["message"]
        assert _snapshot(candidate_main) == candidate_main_before

    _validate_host_independence()


def validate_contract():
    contract = json.loads(
        (ROOT / "reference/contracts/phase7-track-preparation.json").read_text()
    )
    assert contract["contract_id"] == (
        "tracktemplate:phase7:track-preparation:1"
    )
    assert contract["change_level"] == 2
    calculation = contract["calculation"]
    assert calculation["module"] == "tracktemplate.domain.alignment"
    assert calculation["public_functions"] == list(PUBLIC)
    assert calculation["document_mutation"] is False
    assert calculation["host_objects"] is False
    preparation = calculation["functions"]["prepare_track_alignment"]
    assert preparation["parameters"] == list(PARAMETERS)
    assert preparation["selected_dependencies"] == list(
        PREPARATION_DEPENDENCIES
    )
    assert preparation["private_dependencies"] == [
        "_left_normal", "_dot_xy",
    ]
    assert preparation["config_update_order"] == [
        "entry_transition_length", "exit_transition_length",
        "start_spacing", "finish_spacing",
    ]
    assert preparation["result_metadata_order"] == list(RESULT_METADATA)

    adapter = contract["host_adapter"]
    assert adapter["private_type"] == "_PrepareTrackAlignmentAdapter"
    assert adapter["frozen_fields"] == ["calculation", "vector_factory"]
    assert adapter["parameters"] == list(PARAMETERS)
    assert adapter["document_mutation"] is False

    routing = contract["product_routing"]
    assert routing["record_schema_version"] == 11
    assert routing["function_names"] == list(
        transition_workflow.PRODUCT_FUNCTION_NAMES
    )
    assert routing["caller_names"] == [
        name for name, _targets in transition_workflow.PRODUCT_CALLER_ROUTES
    ]
    assert routing["track_preparation_dependencies"] == list(
        PREPARATION_DEPENDENCIES
    )
    assert routing["complete_current_function_count"] == 18
    assert routing["complete_current_caller_count"] == 39
    assert routing["mixed_route"] is False

    provenance = contract["provenance"]
    fragments = []
    ranges = []
    for key, path in (
        ("b14", transition_proof.B14),
        ("b15", transition_proof.B15),
    ):
        source = path.read_text()
        tree = ast.parse(source)
        nodes = {
            node.name: node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in PUBLIC
        }
        assert set(nodes) == set(PUBLIC)
        assert provenance[key + "_path"] == path.name
        assert provenance[key + "_sha256"] == hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        fragment = "\n\n".join(
            ast.get_source_segment(source, nodes[name]) for name in PUBLIC
        )
        fragments.append(fragment)
        ranges.append([nodes[PUBLIC[0]].lineno, nodes[PUBLIC[-1]].end_lineno])
    assert fragments[0] == fragments[1]
    assert ranges[0] == ranges[1] == provenance["definition_lines"]
    encoded = fragments[0].encode()
    assert len(encoded) == provenance["joined_function_source_bytes"]
    assert hashlib.sha256(encoded).hexdigest() == provenance[
        "joined_function_source_sha256"
    ]
    assert contract["scope"]["deferred_obligation"] == (
        "D-P6-008 unchanged in full"
    )
    assert contract["validation"]["qualified_profile"] == (
        "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
    )


def validate_complete_characterisation():
    """Retain the complete platform-transition baseline at the new seam."""
    legacy = _legacy_namespaces()
    baseline = transition_proof.characterise(legacy[0])
    assert transition_proof.characterise(legacy[1]) == baseline
    candidate, _nodes = transition_proof.legacy_namespace(
        transition_proof.B15,
    )
    candidate.update({
        name: getattr(api, name) for name in transition_proof.PUBLIC
    })
    candidate["build_platform_core"] = (
        transition_workflow._PlatformCoreAdapter(
            api.build_platform_core,
            transition_proof.Vector,
        )
    )
    candidate["prepare_track_alignment"] = (
        transition_workflow._PrepareTrackAlignmentAdapter(
            api.prepare_track_alignment,
            transition_proof.Vector,
        )
    )
    assert transition_proof.characterise(candidate) == baseline


def _fixture(temporary_root):
    """Use the retained executable fixture with its exact five-arg caller."""
    return core_proof._fixture(temporary_root)


def _functions():
    return {
        name: getattr(api, name)
        for name in transition_workflow.PRODUCT_FUNCTION_NAMES
    }


def _expect_route_error(action, text=None):
    try:
        action()
    except transition_workflow.TransitionWorkflowError as error:
        if text is not None:
            assert text in str(error)
        return
    raise AssertionError("An invalid track-preparation route was accepted")


def validate_binding():
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-track-preparation-",
    ) as path:
        temporary_root = pathlib.Path(path)
        contract = _fixture(temporary_root)

        def load_host():
            return b15_workflow_host.load_b15_workflow_host(
                temporary_root,
                contract,
            )

        host = load_host()
        session = transition_workflow.ModularTransitionWorkflowSession(
            host,
            _functions(),
        )
        record = session.routing_record()
        assert record["schema_version"] == 11
        assert record["contract_id"] == (
            "tracktemplate:phase7:track-preparation:1"
        )
        assert record["function_names"] == list(
            transition_workflow.PRODUCT_FUNCTION_NAMES
        )
        assert len(record["function_names"]) == 18
        assert record["caller_names"] == [
            name
            for name, _targets in transition_workflow.PRODUCT_CALLER_ROUTES
        ]
        assert len(record["caller_names"]) == 39
        assert record["mixed_route"] is False

        adapter = session.module.prepare_track_alignment
        assert type(adapter) is (
            transition_workflow._PrepareTrackAlignmentAdapter
        )
        assert adapter.calculation is api.prepare_track_alignment
        assert adapter.vector_factory is session.module.App.Vector
        assert tuple(inspect.signature(adapter).parameters) == PARAMETERS
        runner = session.module.run_macro
        assert runner.__globals__ is session.module.__dict__
        assert {
            "prepare_track_alignment", "signed_side_factor",
        } <= set(runner.__code__.co_names)
        assert runner.__globals__["prepare_track_alignment"] is adapter
        assert runner.__globals__["signed_side_factor"] is (
            api.signed_side_factor
        )

        assert session.launch_workflow() == core_proof._expected()
        assert session.module.LAUNCH_COUNT == 1
        centre = session.module.main_circle_centre(600.0, 600.0)
        main = session.module.build_concentric_core(
            centre,
            600.0,
            600.0,
            600.0,
            math.pi / 2.0,
            "Main Track",
        )
        result = adapter(
            _TrackedConfig(_config("Euler - match spacings", "Outside")),
            centre,
            600.0,
            math.pi / 2.0,
            main,
        )
        assert all(type(point) is session.module.App.Vector
                   for point in result["points"])
        assert all(point.z == 0.0 for point in result["points"])
        assert session.routing_record() == record

        for name in transition_workflow.PRODUCT_FUNCTION_NAMES:
            previous = session.module.__dict__[name]
            session.module.__dict__[name] = object()
            try:
                _expect_route_error(session.routing_record, "mixed")
            finally:
                session.module.__dict__[name] = previous
            assert session.routing_record() == record

        for dependency in PREPARATION_DEPENDENCIES:
            functions = _functions()
            functions["prepare_track_alignment"] = core_proof.detached(
                api.prepare_track_alignment,
                dependency,
                lambda *arguments: None,
            )
            fresh = load_host()
            before = core_proof._snapshot(fresh)
            _expect_route_error(
                lambda: transition_workflow.ModularTransitionWorkflowSession(
                    fresh,
                    functions,
                ),
            )
            assert core_proof._snapshot(fresh) == before
            assert fresh.module.LAUNCH_COUNT == 0

        invalid = _functions()
        invalid.pop("prepare_track_alignment")
        fresh = load_host()
        before = core_proof._snapshot(fresh)
        _expect_route_error(
            lambda: transition_workflow.ModularTransitionWorkflowSession(
                fresh,
                invalid,
            ),
            "complete eighteen-function",
        )
        assert core_proof._snapshot(fresh) == before
        assert fresh.module.LAUNCH_COUNT == 0

        detached_host = load_host()
        detached_host.module.run_macro = core_proof.detached(
            detached_host.module.run_macro,
            "prepare_track_alignment",
            api.prepare_track_alignment,
        )
        before = core_proof._snapshot(detached_host)
        _expect_route_error(
            lambda: transition_workflow.ModularTransitionWorkflowSession(
                detached_host,
                _functions(),
            ),
        )
        assert core_proof._snapshot(detached_host) == before
        assert detached_host.module.LAUNCH_COUNT == 0

        rollback_host = load_host()
        rollback_host.module.__dict__.pop("prepare_track_alignment")
        before_keys = tuple(rollback_host.module.__dict__)
        before = dict(rollback_host.module.__dict__)
        with mock.patch.object(
            transition_workflow.ModularTransitionWorkflowSession,
            "_validate_binding",
            side_effect=RuntimeError("controlled track-preparation failure"),
        ):
            try:
                transition_workflow.ModularTransitionWorkflowSession(
                    rollback_host,
                    _functions(),
                )
            except RuntimeError as error:
                assert str(error) == "controlled track-preparation failure"
            else:
                raise AssertionError("A controlled binding failure was lost")
        assert tuple(rollback_host.module.__dict__) == before_keys
        assert all(
            rollback_host.module.__dict__[name] is value
            for name, value in before.items()
        )
        assert "prepare_track_alignment" not in rollback_host.module.__dict__
        assert rollback_host.module.LAUNCH_COUNT == 0


def main():
    validate_calculation()
    validate_complete_characterisation()
    validate_contract()
    validate_binding()
    print(SENTINEL)


if __name__ == "__main__":
    main()
