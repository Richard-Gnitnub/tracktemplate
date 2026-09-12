"""Prove complete straight-route arithmetic and inherited host compatibility."""

import ast
import hashlib
import json
import math
from pathlib import Path
import sys
import types
import inspect
import dataclasses
import tempfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
import validate_phase1_straight_station as legacy  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import transition_workflow as workflow  # noqa: E402


def snapshot(value):
    if isinstance(value, dict):
        return ["dict", [[key, snapshot(item)] for key, item in value.items()]]
    if hasattr(value, "x") and hasattr(value, "y") and hasattr(value, "z"):
        return ["vector", value.x, value.y, value.z]
    if isinstance(value, (list, tuple)):
        return [type(value).__name__, [snapshot(item) for item in value]]
    return [type(value).__name__, value]


def load(path, vector_type=legacy.Point):
    namespace, definitions = legacy._load_straight_namespace(path)
    tree = ast.parse(path.read_text())
    node = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "new_straight_manager_id"
    )
    exec(
        compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"),
        namespace,
    )
    events = {"uuid": [], "vectors": [], "clones": []}

    def uuid4():
        identity = "generated-{:03d}".format(len(events["uuid"]) + 1)
        events["uuid"].append(identity)
        return types.SimpleNamespace(hex=identity)

    namespace["uuid"] = types.SimpleNamespace(uuid4=uuid4)

    def vector(x, y):
        result = vector_type(float(x), float(y), 0.0)
        events["vectors"].append((result.x, result.y, result.z))
        return result

    namespace["vector_xy"] = vector
    original_clone = namespace["clone_straight_config"]

    def clone(config, index=0):
        result = original_clone(config, index)
        events["clones"].append(result)
        return result

    namespace["clone_straight_config"] = clone
    return namespace, definitions, events


def cases(namespace):
    result = []
    for direction in ("Forward", "Reverse"):
        for side in (
            "Left",
            "Right",
            namespace["STRAIGHT_PARALLEL_LEFT"],
            namespace["STRAIGHT_PARALLEL_RIGHT"],
        ):
            for angle in (0.0, 30.0, 90.0, -45.0, 180.0):
                for count in (1, 3):
                    result.append(
                        (
                            f"independent-{direction}-{side}-{angle}-{count}",
                            {
                                "manager_id": "fixed",
                                "name": " Independent ",
                                "direction": direction,
                                "parallel_side": side,
                                "rotation_degrees": angle,
                                "track_count": count,
                                "length": 123.45,
                                "track_spacing": 47.5,
                                "start_x": -17.25,
                                "start_y": 19.75,
                                "template_width": 31.5,
                                "template_thickness": 4.5,
                            },
                            [],
                        )
                    )
    for name, config in (
        ("defaults", {}),
        ("nondict", None),
        (
            "normalization",
            {
                "manager_id": " ",
                "name": " ",
                "length": -2,
                "direction": "invalid",
                "connection_mode": "invalid",
                "parallel_side": "invalid",
                "track_count": "invalid",
                "track_spacing": -1,
                "template_width": 0,
                "template_thickness": -8,
            },
        ),
        ("lower-count", {"track_count": -3}),
        (
            "upper-count",
            {"track_count": namespace["MAX_PARALLEL_TRACKS"] + 10},
        ),
        ("disabled", {"enabled": False}),
        (
            "disabled-invalid-flags",
            {
                "enabled": False,
                "create_template": False,
                "show_centreline": False,
            },
        ),
        (
            "invalid-flags",
            {
                "manager_id": "fixed",
                "create_template": False,
                "show_centreline": False,
            },
        ),
        ("invalid-length", {"manager_id": "fixed", "length": "bad"}),
        ("invalid-length-missing-id", {"length": "bad"}),
    ):
        result.append((name, config, []))
    for mode in (
        namespace["STRAIGHT_CONNECTION_CURVE_ENTRANCE"],
        namespace["STRAIGHT_CONNECTION_CURVE_EXIT"],
    ):
        for angle in (0.0, math.pi / 6.0, -math.pi / 2.0):
            tracks = legacy._curve_tracks()
            for i, track in enumerate(tracks):
                track["headings"] = [angle, angle]
                track["width"] = 27.25 + i
                track["create_template"] = i == 0
                track["show_centreline"] = i == 1
            config = {
                "manager_id": "connected",
                "name": "Connection",
                "connection_mode": mode,
                "length": 83.125,
                "template_thickness": 99.0,
                "direction": "Reverse",
            }
            result.append((f"{mode}-{angle}", config, tracks))
        for kind in (
            "empty",
            "short",
            "mismatch",
            "missing-points",
            "missing-headings",
            "no-name",
            "default-flags",
            "tangent-at",
            "tangent-above",
            "wrapped",
        ):
            tracks = legacy._curve_tracks()
            if kind == "empty":
                tracks = []
            if kind == "short":
                tracks[0]["points"] = tracks[0]["points"][:1]
            if kind == "mismatch":
                tracks[0]["headings"] = [0.0]
            if kind == "missing-points":
                del tracks[0]["points"]
            if kind == "missing-headings":
                del tracks[0]["headings"]
            if kind == "no-name":
                del tracks[0]["name"]
            if kind == "default-flags":
                del tracks[0]["create_template"]
                del tracks[0]["show_centreline"]
            if kind.startswith("tangent"):
                angle = (
                    1e-10
                    if kind == "tangent-at"
                    else math.nextafter(1e-10, math.inf)
                )
                tracks[1]["headings"] = [angle, angle]
            if kind == "wrapped":
                tracks[1]["headings"] = [2 * math.pi] * 2
            result.append(
                (
                    f"{mode}-{kind}",
                    {
                        "manager_id": "connected",
                        "name": "Connection",
                        "connection_mode": mode,
                        "length": 100.0,
                    },
                    tracks,
                )
            )
    return result


def observe(namespace, events, config, curves, action=None):
    before = snapshot((config, curves))
    events["uuid"].clear()
    events["vectors"].clear()
    events["clones"].clear()
    try:
        result = (action or namespace["build_straight_route"])(config, curves)
        error = None
    except (ValueError, TypeError, KeyError) as exc:
        result = None
        error = [type(exc).__name__, str(exc)]
    assert snapshot((config, curves)) == before
    if result is not None:
        routes = result if isinstance(result, list) else [result]
        for route in routes:
            assert any(route["config"] is clone for clone in events["clones"])
            assert route["config"] is not config
            for item in route["alignments"]:
                assert len(item) == 20 and len(item["points"]) == 2
                assert all(
                    point is not original
                    for point in item["points"]
                    for curve in curves
                    for original in curve.get("points", [])
                )
                assert item["total_length"] == 0.0 + math.hypot(
                    item["points"][1].x - item["points"][0].x,
                    item["points"][1].y - item["points"][0].y,
                )
    return {
        "result": snapshot(result),
        "error": error,
        "uuid": list(events["uuid"]),
        "vectors": list(events["vectors"]),
        "clones": [snapshot(item) for item in events["clones"]],
        "input_unchanged": True,
        "config_identity": True,
    }


def characterize():
    results = []
    definitions = []
    hashes = {}
    for path in (legacy.B14_PATH, legacy.B15_PATH):
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        namespace, nodes, events = load(path)
        definitions.append(nodes)
        rows = []
        for name, config, curves in cases(namespace):
            rows.append(
                {"name": name, **observe(namespace, events, config, curves)}
            )
        configs = [
            {"manager_id": "duplicate", "name": "First"},
            {"manager_id": "duplicate", "name": "Second"},
            {"manager_id": "disabled", "enabled": False},
            {},
        ]
        rows.append(
            {
                "name": "actual-batch-duplicate-disabled-UUID",
                **observe(
                    namespace,
                    events,
                    configs,
                    [],
                    namespace["build_straight_routes"],
                ),
            }
        )
        results.append(rows)
    assert definitions[0] == definitions[1]
    assert results[0] == results[1]
    return {
        "status": "PASS",
        "case_count": len(results[0]),
        "source_hashes": hashes,
        "complete_B14": results[0],
        "complete_B15": results[1],
        "limits": [
            "Supported plain configuration and curve records; no arbitrary custom container exception timing claim."
        ],
    }


ROUTE_KEYS = (
    "route_id",
    "name",
    "connection_mode",
    "config",
    "alignments",
    "length",
)
ALIGNMENT_KEYS = (
    "route_id",
    "route_name",
    "track_number",
    "name",
    "points",
    "headings",
    "width",
    "template_thickness",
    "create_template",
    "show_centreline",
    "connection_mode",
    "source_alignment_name",
    "total_length",
    "core_length",
    "entry_extension",
    "exit_extension",
    "start",
    "end",
    "extended_start",
    "extended_end",
)
CURVE_KEYS = (
    "point_count",
    "heading_count",
    "start",
    "end",
    "start_heading",
    "end_heading",
)
ADAPTER_FIELDS = (
    "calculation",
    "vector_factory",
    "config_cloner",
    "connected_template_thickness",
)


STATION_CALLER_NAMES = (
    "main_circle_centre",
    "build_concentric_core",
    "prepare_track_alignment",
    "run_macro",
    "build_straight_routes",
    "alignment_progress_at_station",
    "platform_coverage_bounds",
    "sample_station_interval",
    "_project_centreline_to_reference_normal",
    "_offset_point_towards_reference",
    "calculate_platform_boundaries",
    "create_between_alignments_face",
    "_project_formation_point_to_reference",
    "_simple_formation_swept_face",
    "create_section_mask_face",
    "create_section_masks",
    "apply_registration_features",
    "find_section_number_origin",
    "alignment_station_at_cross_section",
    "calculate_template_section_stations",
    "apply_track_template_joints",
    "create_track_template_fixing_holes",
    "prepare_straight_route_production",
    "turnout_host_alignment",
    "map_turnout_local_point",
    "_turnout_interval_samples",
    "_crossover_nearest_point_on_alignment",
    "_crossover_host_travel_vector",
    "_crossover_automatic_hand",
    "_crossover_orientation_b",
    "solve_rea_c10_crossover_geometry",
    "resolve_automatic_turnout_crossover_extension",
    "_timber_record_from_layout",
    "crossover_inherited_timber_records",
    "crossover_shared_timber_envelope_context",
    "_crossover_integration_alignment_signature",
    "_chair_turnout_timber_records",
    "CrossoverManagerPanel.use_picked_crossover_position",
)


def station_fixture_source():
    """Load frozen station callers with their actual method and nested code."""
    source = legacy.B15_PATH.read_text()
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    names = set(STATION_CALLER_NAMES[5:]) | {
        "alignment_station_data", "interpolate_alignment_station",
    }
    names.remove("CrossoverManagerPanel.use_picked_crossover_position")
    constants = {
        "TURNOUT_SAMPLE_SPACING", "CROSSOVER_ARRANGEMENT_FACING",
        "CROSSOVER_HAND_AUTO", "TURNOUT_DEFAULT_GAUGE",
        "TURNOUT_DEFAULT_FLANGEWAY", "CROSSOVER_DEFAULT_MINIMUM_RADIUS",
        "GEOMETRY_TOLERANCE",
    }
    selected = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in constants
            for target in node.targets
        ):
            selected.append("".join(lines[node.lineno - 1:node.end_lineno]))
        if isinstance(node, ast.FunctionDef) and node.name in names:
            selected.append("".join(lines[node.lineno - 1:node.end_lineno]))
        if (
            isinstance(node, ast.ClassDef)
            and node.name == "CrossoverManagerPanel"
        ):
            method = next(
                item for item in node.body
                if isinstance(item, ast.FunctionDef)
                and item.name == "use_picked_crossover_position"
            )
            minimal_class = ast.ClassDef(
                name=node.name, bases=[], keywords=[], body=[method],
                decorator_list=[], type_params=[],
            )
            selected.append(ast.unparse(minimal_class))
    return "import bisect\n" + "\n\n".join(selected) + "\n"


def straight_fixture_source():
    """Use exact frozen host normalization and its real direct caller."""
    source = legacy.B14_PATH.read_text()
    names = {
        "new_straight_manager_id",
        "default_straight_config",
        "clone_straight_config",
        "build_straight_routes",
        "build_straight_route",
        "_straight_alignment_record",
        "_straight_heading_delta",
        "polyline_length",
    }
    selected = []
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            selected.append(ast.get_source_segment(source, node))
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in legacy.CONSTANT_NAMES
            for target in node.targets
        ):
            selected.append(ast.get_source_segment(source, node))
    return "import uuid\n" + "\n\n".join(selected) + "\n"


def neutral_curves(curves):
    """Independent test projection of the supported endpoint-only contract."""
    records = []
    for curve in curves:
        points, headings = curve.get("points", []), curve.get("headings", [])
        valid = len(points) >= 2 and len(points) == len(headings)
        record = dict(
            zip(
                CURVE_KEYS,
                (
                    len(points),
                    len(headings),
                    (points[0].x, points[0].y) if valid else None,
                    (points[-1].x, points[-1].y) if valid else None,
                    headings[0] if valid else None,
                    headings[-1] if valid else None,
                ),
            )
        )
        record.update(
            {
                key: curve[key]
                for key in (
                    "name",
                    "width",
                    "create_template",
                    "show_centreline",
                )
                if key in curve
            }
        )
        records.append(record)
    return records


def adapter_for(namespace, calculation=api.build_straight_route):
    return workflow._StraightRouteAdapter(
        calculation,
        lambda x, y, z: namespace["vector_xy"](x, y),
        namespace["clone_straight_config"],
        namespace["TEMPLATE_THICKNESS"],
    )


def assert_route_geometry(namespace, route, curves):
    assert tuple(route) == ROUTE_KEYS
    config = route["config"]
    namespace["validate_connected_straight_routes"]([route], curves)
    for index, item in enumerate(route["alignments"]):
        assert tuple(item) == ALIGNMENT_KEYS
        assert item["track_number"] == index + 1
        assert item["route_id"] == "straight-" + config["manager_id"]
        assert item["headings"][0] == item["headings"][1]
        first, last = item["points"]
        heading = item["headings"][0]
        assert (
            abs(
                math.hypot(last.x - first.x, last.y - first.y)
                - config["length"]
            )
            < 1e-8
        )
        assert (
            abs(
                (last.x - first.x) * math.sin(heading)
                - (last.y - first.y) * math.cos(heading)
            )
            < 1e-8
        )
        assert (last.x - first.x) * math.cos(heading) + (
            last.y - first.y
        ) * math.sin(heading) > 0.0
        stations = namespace["alignment_station_data"](item)
        assert stations["stations"] == [0.0, item["total_length"]]
        assert stations["alignment"] is item
        if config["connection_mode"] == "Independent datum":
            side = (
                -1.0 if config["parallel_side"] == "Right of travel" else 1.0
            )
            dx = first.x - config["start_x"]
            dy = first.y - config["start_y"]
            assert (
                abs(
                    -dx * math.sin(heading)
                    + dy * math.cos(heading)
                    - side * index * config["track_spacing"]
                )
                < 1e-8
            )
            assert item["template_thickness"] == config["template_thickness"]
        else:
            assert (
                item["template_thickness"] == namespace["TEMPLATE_THICKNESS"]
            )


def validate_calculations():
    baseline = characterize()
    from validate_phase7_main_circle_centre import SOURCE_HASHES

    assert baseline["source_hashes"] == SOURCE_HASHES
    namespace, _nodes, events = load(legacy.B14_PATH)
    candidate = adapter_for(namespace)
    for name, config, curves in cases(namespace):
        expected = observe(namespace, events, config, curves)
        actual = observe(namespace, events, config, curves, candidate)
        # Errors occur before adapter vector realization. Combined injected
        # failures and malformed-object interleaving are outside this contract.
        if expected["error"]:
            expected.pop("vectors")
            actual.pop("vectors")
        assert actual == expected, name
        if expected["error"] or not (
            config is None or config.get("enabled", True)
        ):
            continue
        route = candidate(config, curves)
        assert_route_geometry(namespace, route, curves)
        normalized = namespace["clone_straight_config"](config)
        inputs = neutral_curves(curves)
        before = snapshot((normalized, inputs))
        pure = api.build_straight_route(
            normalized, inputs, namespace["TEMPLATE_THICKNESS"]
        )
        assert pure["config"] is normalized
        assert snapshot((normalized, inputs)) == before
        again = api.build_straight_route(
            normalized, inputs, namespace["TEMPLATE_THICKNESS"]
        )
        assert again == pure and again is not pure
        assert again["alignments"] is not pure["alignments"]
        for result, repeated in zip(pure["alignments"], again["alignments"]):
            assert (
                result is not repeated
                and result["points"] is not repeated["points"]
            )
            assert all(
                type(point) is tuple
                and all(type(value) is float for value in point)
                for point in result["points"]
            )
        # Manager generation is observed separately; compare the same clone.
        domain_adapter = workflow._StraightRouteAdapter(
            api.build_straight_route,
            legacy.Point,
            lambda value: value,
            namespace["TEMPLATE_THICKNESS"],
        )
        host_form = domain_adapter(normalized, curves)
        for item in pure["alignments"]:
            item["points"] = [legacy.Point(*point) for point in item["points"]]
        assert snapshot(pure) == snapshot(host_form), name

    configs = [
        {"manager_id": "duplicate", "name": "First"},
        {"manager_id": "duplicate", "name": "Second"},
        {"manager_id": "disabled", "enabled": False},
        {},
    ]
    expected = observe(
        namespace, events, configs, [], namespace["build_straight_routes"]
    )
    namespace["build_straight_route"] = candidate
    actual = observe(
        namespace, events, configs, [], namespace["build_straight_routes"]
    )
    assert actual == expected
    assert len(actual["uuid"]) == 10
    return baseline["case_count"]


def validate_guards_and_failures():
    namespace, _nodes, events = load(legacy.B14_PATH)
    adapter = adapter_for(namespace)

    class UnreadableCurves:
        def __iter__(self):
            raise AssertionError("Early guard inspected curve records")

    for config in (
        {"enabled": False},
        {"create_template": False, "show_centreline": False},
    ):
        config["connection_mode"] = "Curve entrance"
        try:
            result = adapter(config, UnreadableCurves())
        except ValueError as error:
            assert "must create a strip, a centreline, or both" in str(error)
        else:
            assert result is None
    for curves in ([], None):
        try:
            adapter({"connection_mode": "Curve exit"}, curves)
        except ValueError as error:
            assert "no curve tracks exist" in str(error)
        else:
            raise AssertionError("Missing curves were admitted")
    # Invalid counts must reject before any unusable endpoint is read.
    bad = [{"points": [object()], "headings": [0.0], "name": "Incomplete"}]
    try:
        adapter({"connection_mode": "Curve entrance"}, bad)
    except ValueError as error:
        assert "incomplete curve track 'Incomplete'" in str(error)
    else:
        raise AssertionError("Incomplete curve admitted")
    normalized = namespace["clone_straight_config"]({"name": "Short"})
    normalized["length"] = 1e-8
    try:
        api.build_straight_route(
            normalized, [], namespace["TEMPLATE_THICKNESS"]
        )
    except ValueError as error:
        assert (
            str(error)
            == "Straight route 'Short' must have a length greater than zero."
        )
    else:
        raise AssertionError("Domain length guard omitted")
    for mode in ("Independent datum", "Curve entrance", "Curve exit"):
        for fail_at in (1, 2, 3, 4):
            observations = []
            for modular in (False, True):
                namespace, _nodes, events = load(legacy.B14_PATH)
                vector = namespace["vector_xy"]
                calls = []

                def failing_vector(x, y):
                    calls.append((float(x), float(y), 0.0))
                    if len(calls) == fail_at:
                        raise RuntimeError("Injected straight vector failure")
                    return vector(x, y)

                namespace["vector_xy"] = failing_vector
                config = {
                    "manager_id": "known",
                    "connection_mode": mode,
                    "track_count": 2,
                }
                curves = legacy._curve_tracks()
                before = snapshot((config, curves))
                function = (
                    adapter_for(namespace)
                    if modular
                    else namespace["build_straight_route"]
                )
                try:
                    function(config, curves)
                except RuntimeError as error:
                    assert str(error) == "Injected straight vector failure"
                else:
                    raise AssertionError("Injected vector failure was lost")
                assert snapshot((config, curves)) == before
                observations.append((calls, list(events["uuid"])))
            assert observations[0] == observations[1]


def validate_contract():
    assert tuple(inspect.signature(api.build_straight_route).parameters) == (
        "config",
        "curve_alignments",
        "connected_template_thickness",
    )
    assert all(
        parameter.default is inspect.Parameter.empty
        for parameter in inspect.signature(
            api.build_straight_route
        ).parameters.values()
    )
    assert (
        api.build_straight_route.__module__ == "tracktemplate.domain.alignment"
    )
    assert "build_straight_route" in api.__all__
    assert not {"FreeCAD", "FreeCADGui", "Part"} & set(sys.modules)
    contract = json.loads(
        (ROOT / "reference/contracts/phase7-straight-route.json").read_text()
    )
    assert contract["contract_id"] == "tracktemplate:phase7:straight-route:1"
    assert contract["authority"] == ["D-GOV-004", "D-P7-001"]
    assert contract["calculation"]["parameters"] == list(
        inspect.signature(api.build_straight_route).parameters
    )
    assert contract["calculation"]["route_keys"] == list(ROUTE_KEYS)
    assert contract["calculation"]["alignment_keys"] == list(ALIGNMENT_KEYS)
    assert contract["calculation"]["curve_required_keys"] == list(CURVE_KEYS)
    assert contract["calculation"]["input_mutation"] is False
    assert (
        contract["calculation"]["result_config_identity"]
        == "supplied_normalized_config"
    )
    assert contract["host_adapter"]["frozen_fields"] == list(ADAPTER_FIELDS)
    assert contract["product_routing"]["record_schema_version"] == 6
    assert contract["product_routing"]["function_names"] == list(
        workflow.PRODUCT_FUNCTION_NAMES[:8]
    )
    assert contract["product_routing"]["caller_names"] == [
        name for name, _targets in workflow.PRODUCT_CALLER_ROUTES[:5]
    ]


def validate_binding():
    import validate_phase7_concentric_core as core
    from tracktemplate.compatibility import b15_workflow_host as host_loader

    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-phase7-straight-"
    ) as directory:
        root = Path(directory)
        contract = core._fixture(root)

        def host():
            return host_loader.load_b15_workflow_host(root, contract)

        functions = core._functions()
        session = workflow.ModularTransitionWorkflowSession(host(), functions)
        assert session.launch_workflow() == core._expected()
        adapter = session.module.build_straight_route
        assert type(adapter) is workflow._StraightRouteAdapter
        assert (
            tuple(field.name for field in dataclasses.fields(adapter))
            == ADAPTER_FIELDS
        )
        assert tuple(inspect.signature(adapter).parameters) == (
            "config",
            "curve_alignments",
        )
        assert adapter.calculation is api.build_straight_route
        assert adapter.vector_factory is session.module.App.Vector
        assert adapter.config_cloner is session.module.clone_straight_config
        assert (
            adapter.connected_template_thickness
            is session.module.TEMPLATE_THICKNESS
        )
        try:
            adapter.config_cloner = None
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("Straight adapter is mutable")
        record = session.routing_record()
        assert record["schema_version"] == 8
        assert record["contract_id"] == (
            "tracktemplate:phase7:alignment-handedness:1"
        )
        assert record["function_names"] == list(functions)
        assert record["caller_names"] == list(STATION_CALLER_NAMES)
        caller = session.module.build_straight_routes
        assert caller.__globals__ is session.module.__dict__
        assert "build_straight_route" in caller.__code__.co_names
        routes = caller([{"manager_id": "actual-caller", "length": 82.0}], [])
        assert len(routes) == 1 and routes[0]["length"] == 82.0
        assert routes[0]["alignments"][0]["points"][1].x == 82.0
        # Historical three-function binder must never participate in composition.
        with mock.patch.object(
            type(session._host), "bind_transition_functions",
            side_effect=AssertionError("Frozen binder called"),
        ):
            assert session.launch_workflow() == core._expected()
        for missing in functions:
            for absent in (False, True):
                source = host()
                if absent:
                    del source.module.__dict__[missing]
                before = core._snapshot(source)
                invalid = dict(functions)
                invalid.pop(missing)
                core.centre_proof._expect_error(
                    lambda: workflow.ModularTransitionWorkflowSession(
                        source, invalid
                    ),
                    "complete eleven-function",
                )
                assert core._snapshot(source) == before
        for absent in (False, True):
            source = host()
            if absent:
                del source.module.build_straight_route
            source.module.build_straight_routes = core.detached(
                source.module.build_straight_routes,
                "build_straight_route",
                api.build_straight_route,
            )
            before = core._snapshot(source)
            core.centre_proof._expect_error(
                lambda: workflow.ModularTransitionWorkflowSession(
                    source, functions
                ),
                "caller 'build_straight_routes' is unavailable",
            )
            assert (
                core._snapshot(source) == before
                and source.module.LAUNCH_COUNT == 0
            )

        class WrongAdapter(workflow._StraightRouteAdapter):
            pass

        corruptions = [
            WrongAdapter(*(getattr(adapter, name) for name in ADAPTER_FIELDS))
        ]
        for field in ADAPTER_FIELDS:
            corruptions.append(
                dataclasses.replace(adapter, **{field: object()})
            )
        for corrupt in corruptions:
            session._host_functions["build_straight_route"] = corrupt
            before = core._snapshot(session)
            count = session.module.LAUNCH_COUNT
            core.centre_proof._expect_error(
                session.launch_workflow, "straight-route adapter"
            )
            assert (
                core._snapshot(session) == before
                and session.module.LAUNCH_COUNT == count
            )
        session._host_functions["build_straight_route"] = adapter
        for field in ("clone_straight_config", "TEMPLATE_THICKNESS"):
            old = getattr(session.module, field)
            setattr(session.module, field, object())
            before = core._snapshot(session)
            core.centre_proof._expect_error(
                session.launch_workflow, "straight-route adapter"
            )
            assert core._snapshot(session) == before
            setattr(session.module, field, old)
        assert session.launch_workflow() == core._expected()
        for field in ("clone_straight_config", "TEMPLATE_THICKNESS"):
            source = host()
            delattr(source.module, field)
            before = core._snapshot(source)
            core.centre_proof._expect_error(
                lambda: workflow.ModularTransitionWorkflowSession(
                    source, functions
                ),
                "straight-route configuration",
            )
            assert core._snapshot(source) == before


def validate():
    count = validate_calculations()
    validate_guards_and_failures()
    validate_contract()
    validate_binding()
    print(f"Phase 7 straight route validation passed: {count} legacy cases")


if __name__ == "__main__":
    validate()
