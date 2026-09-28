"""Prove complete-radius crossover preflight on a copied qualified host."""

import hashlib
import json
import math
import os
import pathlib
import runpy
import shutil
import sys
import tempfile

import FreeCAD as App
import Part


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_ROOT = pathlib.Path(
    os.environ.get("TRACKTEMPLATE_CROSSOVER_SOURCE_ROOT", ROOT)
).resolve()
sys.path.insert(0, str(SOURCE_ROOT))

from tools.freecad_bridge import b14_recipe  # noqa: E402
from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility.crossover_preflight import (  # noqa: E402
    CrossoverPreflightAdapter,
)
from tracktemplate.compatibility import transition_workflow  # noqa: E402


SENTINEL = "Phase 8 crossover complete-radius FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"
CONTRACT = (
    SOURCE_ROOT / "reference/contracts/phase1-crossover-feasibility.json"
)
COMPONENTS = (
    ("turnout_a_minimum_radius_mm",
     "turnout_a_mapped_minimum_radius_mm"),
    ("turnout_b_minimum_radius_mm",
     "turnout_b_mapped_minimum_radius_mm"),
    ("connector_minimum_radius_mm", "connector_minimum_radius_mm"),
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot(document):
    persisted_names = {
        "TemplateSetID", "GeneratedBy", "GeneratedRole",
        "TrackNumber", "TrackName", "RouteID", "ExportSubtype",
        "TurnoutID", "CrossoverID",
    }
    objects = []
    for obj in document.Objects:
        persisted = tuple(sorted(
            (name, str(getattr(obj, name)))
            for name in obj.PropertiesList
            if name in persisted_names or name.endswith("JSON")
        ))
        shape = getattr(obj, "Shape", None)
        geometry = None
        if shape is not None and not shape.isNull():
            geometry = (
                shape.ShapeType,
                len(shape.Edges),
                len(shape.Faces),
                float(shape.Length).hex(),
                float(shape.Area).hex(),
                float(shape.Volume).hex(),
                tuple(
                    (float(vertex.Point.x).hex(),
                     float(vertex.Point.y).hex(),
                     float(vertex.Point.z).hex())
                    for vertex in shape.Vertexes
                ),
            )
        objects.append((obj.Name, obj.TypeId, persisted, geometry))
    return {
        "objects": tuple(objects),
        "undo": document.UndoCount,
        "redo": document.RedoCount,
        "file_name": document.FileName,
    }


def _assert_close(actual, expected, tolerance_mm):
    assert math.isclose(
        float(actual), float(expected), rel_tol=0.0,
        abs_tol=tolerance_mm,
    ), (actual, expected)


def _expect_rejected(action):
    try:
        action()
    except ValueError as error:
        diagnostic = str(error)
        assert "Host Track B turnout road" in diagnostic, diagnostic
        assert "540.848375 mm" in diagnostic, diagnostic
        assert "600.000000 mm" in diagnostic, diagnostic
        return diagnostic
    raise AssertionError("Incomplete crossover radius was accepted")


def _load_product():
    assert pathlib.Path(api.__file__).resolve() == (
        SOURCE_ROOT / "tracktemplate/api.py"
    )
    launcher = runpy.run_path(str(SOURCE_ROOT / "TrackTemplate.FCMacro"))
    foundation = launcher["FOUNDATION_RESULT"]
    assert foundation["status"] == "modular-foundation-ready"
    assert foundation["matched_profile_id"] == PROFILE
    modular_api, bootstrap = launcher["_load_foundation"](SOURCE_ROOT)
    assert modular_api is api
    contract = bootstrap.load_contract(
        SOURCE_ROOT / "reference/contracts/phase1-transition-pilot.json"
    )
    session = transition_workflow.load_modular_transition_workflow_session(
        SOURCE_ROOT, api, contract,
    )
    return session.module


def _selected_hosts(module, document, fixture):
    hosts = module.turnout_host_objects(document)
    selection = b14_recipe.select_crossover_hosts(
        hosts,
        module.object_string_property,
        module._integer_object_property,
    )
    for side in ("a", "b"):
        for key, expected in fixture["host_{}_identity".format(side)].items():
            assert selection["host_{}_identity".format(side)][key] == (
                expected
            )
    return hosts[selection["a"]], hosts[selection["b"]]


def _request_arguments(document, hosts, chainage_mm, request):
    return (
        document,
        hosts[0],
        hosts[1],
        chainage_mm,
        request["arrangement"],
        request["handing"],
        request["track_gauge_mm"],
        request["flangeway_mm"],
        request["minimum_radius_mm"],
    )


class _Proxy:
    """Expose a changed signature input without mutating the copy."""

    def __init__(self, original, **overrides):
        self.original = original
        self.overrides = overrides

    def __getattr__(self, name):
        if name in self.overrides:
            return self.overrides[name]
        return getattr(self.original, name)


class _AddedTurnoutSettings:
    PropertiesList = ("GeneratedRole", "TurnoutConfigurationJSON")
    GeneratedRole = "TurnoutSettings"
    TurnoutConfigurationJSON = json.dumps({
        "turnout_id": "TO-PROBE",
        "host_object": "other",
        "toe_chainage": 10.0,
        "orientation": "Facing with host travel direction",
        "track_gauge": 16.5,
        "flangeway": 1.0,
    })


class _AddedCrossoverSettings:
    PropertiesList = ("GeneratedRole", "CrossoverConfigurationJSON")
    GeneratedRole = "CrossoverSettings"
    CrossoverConfigurationJSON = json.dumps({
        "crossover_id": "XO-PROBE",
        "host_a_object": "other-a",
        "host_b_object": "other-b",
        "host_a_station_interval": [10.0, 20.0],
        "host_b_station_interval": [30.0, 40.0],
    })


def _expect_stale(action, label):
    try:
        action()
    except ValueError as error:
        assert "cached crossover preflight is stale" in str(error), (
            label, str(error),
        )
        return
    raise AssertionError("Stale crossover preflight reused: {}".format(
        label,
    ))


def _verify_signature_invalidation(module, solved, arguments):
    adapter = module.solve_rea_c10_crossover_geometry.__self__
    assert type(adapter) is CrossoverPreflightAdapter
    assert adapter.module is module
    original = solved["complete_radius_preflight"]["input_signature"]
    assert adapter.input_signature(*arguments) == original
    assert adapter.input_signature(*arguments) == original

    host_a, host_b = arguments[1:3]
    points_a = module.turnout_host_alignment(host_a)["points"]
    points_b = module.turnout_host_alignment(host_b)["points"]
    shape_a = Part.makePolygon([
        App.Vector(point.x + 0.001, point.y, point.z)
        for point in points_a
    ])
    shape_b = Part.makePolygon([
        App.Vector(point.x, point.y + 0.001, point.z)
        for point in points_b
    ])
    variants = []
    for index, label, value in (
        (3, "chainage", arguments[3] + 0.001),
        (4, "arrangement", "Trailing crossover"),
        (5, "handing", "Right-hand"),
        (6, "gauge", arguments[6] + 0.1),
        (7, "flangeway", arguments[7] + 0.1),
        (8, "minimum radius", arguments[8] + 0.001),
        (1, "Host A identity", _Proxy(host_a, TrackName="Renamed")),
        (2, "Host B identity", _Proxy(host_b, TrackNumber=99)),
        (1, "Host A geometry", _Proxy(host_a, Shape=shape_a)),
        (2, "Host B geometry", _Proxy(host_b, Shape=shape_b)),
        (0, "turnout occupancy", _Proxy(
            arguments[0],
            Objects=list(arguments[0].Objects) + [_AddedTurnoutSettings()],
        )),
        (0, "crossover occupancy", _Proxy(
            arguments[0],
            Objects=list(arguments[0].Objects) + [_AddedCrossoverSettings()],
        )),
    ):
        changed = list(arguments)
        changed[index] = value
        variants.append((label, tuple(changed), {}))
    variants.extend((
        ("ignored crossover", arguments, {"ignored_crossover_id": "XO-1"}),
        ("ignored turnout", arguments, {"ignored_turnout_id": "TO-1"}),
    ))
    for label, changed, keywords in variants:
        signature = adapter.input_signature(*changed, **keywords)
        assert signature != original, label
        _expect_stale(
            lambda changed=changed, keywords=keywords: (
                module._build_rea_c10_crossover_geometry(
                    *changed, pre_solved=solved, **keywords,
                )
            ),
            label,
        )
    display_only = list(arguments)
    display_only[1] = _Proxy(host_a, Label="Display-only label")
    assert adapter.input_signature(*display_only) == original
    assert adapter.input_signature(*arguments) == original


def _verify_complete_result(solved, witness, request):
    result = solved["complete_radius_preflight"]
    assert result["accepted"] is True
    assert isinstance(result["input_signature"], str)
    assert len(result["input_signature"]) == 64
    assert result["minimum_requested_radius_mm"] == (
        request["minimum_radius_mm"]
    )
    tolerance = request["comparison_tolerance_mm"]
    _assert_close(
        solved["toe_chainage_b"],
        witness["host_b_chainage_mm"],
        tolerance,
    )
    for result_key, witness_key in COMPONENTS:
        _assert_close(result[result_key], witness[witness_key], tolerance)
    _assert_close(
        result["complete_minimum_radius_mm"],
        witness["complete_minimum_radius_mm"],
        tolerance,
    )
    assert result["limiting_component"] == "Connecting road"
    return result


def _verify_exact_result(config, preflight, tolerance_mm):
    exact = {
        "turnout_a_minimum_radius_mm": config[
            "turnout_a_config"
        ]["turnout_minimum_radius_sampled"],
        "turnout_b_minimum_radius_mm": config[
            "turnout_b_config"
        ]["turnout_minimum_radius_sampled"],
        "connector_minimum_radius_mm": config["connector_minimum_radius"],
        "complete_minimum_radius_mm": config["minimum_resulting_radius"],
    }
    for key, actual in exact.items():
        _assert_close(actual, preflight[key], tolerance_mm)
    assert config["production_ready"] is False
    assert config["host_integration_allowed"] is False


def _verify_edit_rejection(
    module, document, arguments, rejected_chainage_mm,
):
    solved = module.solve_rea_c10_crossover_geometry(
        *arguments, ignored_crossover_id="XO-001",
    )
    assert solved["complete_radius_preflight"]["accepted"] is True
    before = _snapshot(document)
    changed = list(arguments)
    changed[8] += 0.001
    original_clear = module.clear_chair_analysis_display
    original_builder = module._build_curve_inheriting_c10_turnout
    original_recompute = module._document_recompute

    def unexpected_clear(*_args, **_kwargs):
        raise AssertionError("Edit cleared display before preflight rejection")

    def unexpected_exact_build(*_args, **_kwargs):
        raise AssertionError("Edit built Part geometry before rejection")

    def unexpected_recompute(*_args, **_kwargs):
        raise AssertionError("Edit recomputed before rejection")

    module.clear_chair_analysis_display = unexpected_clear
    module._build_curve_inheriting_c10_turnout = unexpected_exact_build
    module._document_recompute = unexpected_recompute
    try:
        _expect_stale(
            lambda: module.edit_rea_c10_crossover(
                changed[0], "XO-001", *changed[1:], pre_solved=solved,
            ),
            "edit request change",
        )
        assert _snapshot(document) == before
        rejected = list(arguments)
        rejected[3] = rejected_chainage_mm
        preview_diagnostic = _expect_rejected(
            lambda: module.solve_rea_c10_crossover_geometry(
                *rejected, ignored_crossover_id="XO-001",
            )
        )
        assert _snapshot(document) == before
        edit_diagnostic = _expect_rejected(
            lambda: module.edit_rea_c10_crossover(
                rejected[0], "XO-001", *rejected[1:],
                pre_solved=None,
            )
        )
        assert edit_diagnostic == preview_diagnostic
    finally:
        module.clear_chair_analysis_display = original_clear
        module._build_curve_inheriting_c10_turnout = original_builder
        module._document_recompute = original_recompute
    assert _snapshot(document) == before


def _verify_extension_rejection(module, source, temporary, contract):
    copied = pathlib.Path(temporary) / "turnout-extension.FCStd"
    shutil.copy2(source, copied)
    document = App.openDocument(str(copied))
    try:
        document.UndoMode = 1
        fixture = contract["fixture"]
        hosts = _selected_hosts(module, document, fixture)
        request = contract["request"]
        invalid = contract["witnesses"][0]
        assert invalid["id"] == "lower-preview-pass-complete-fail"
        arguments = _request_arguments(
            document, hosts, invalid["host_a_chainage_mm"], request,
        )
        adapter = module.solve_rea_c10_crossover_geometry.__self__
        inherited = adapter.original_solver(*arguments)
        turnout = module.create_curve_inheriting_c10_turnout(
            document, hosts[0], invalid["host_a_chainage_mm"],
            inherited["handing"], inherited["orientation_a"],
            request["track_gauge_mm"], request["flangeway_mm"],
            create_timber_numbers=False,
        )
        turnout_id = turnout["turnout_id"]
        before = _snapshot(document)
        preview_diagnostic = _expect_rejected(
            lambda: module.solve_rea_c10_crossover_geometry(
                *arguments, ignored_turnout_id=turnout_id,
            )
        )
        inherited_builder = module._build_curve_inheriting_c10_turnout
        inherited_recompute = module._document_recompute

        def unexpected_exact_build(*_args, **_kwargs):
            raise AssertionError(
                "Extension began exact construction before rejection"
            )

        def unexpected_recompute(*_args, **_kwargs):
            raise AssertionError("Extension recomputed before rejection")

        module._build_curve_inheriting_c10_turnout = unexpected_exact_build
        module._document_recompute = unexpected_recompute
        try:
            extension_diagnostic = _expect_rejected(
                lambda: module.extend_turnout_to_rea_c10_crossover(
                    document, turnout_id, hosts[1],
                    request["minimum_radius_mm"],
                )
            )
        finally:
            module._build_curve_inheriting_c10_turnout = inherited_builder
            module._document_recompute = inherited_recompute
        assert extension_diagnostic == preview_diagnostic
        assert _snapshot(document) == before
    finally:
        App.closeDocument(document.Name)


def validate():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["contract_id"] == (
        "tracktemplate:phase1:crossover-feasibility:1"
    )
    fixture = contract["fixture"]
    source = SOURCE_ROOT / fixture["path"]
    source_hash = _sha256(source)
    assert source_hash == fixture["sha256"]
    witnesses = {item["id"]: item for item in contract["witnesses"]}
    rejected = witnesses["lower-preview-pass-complete-fail"]
    accepted = witnesses["documented-valid-placement"]
    module = _load_product()

    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-phase8-crossover-preflight-"
    ) as temporary:
        copy = pathlib.Path(temporary) / "crossover-preflight.FCStd"
        shutil.copy2(source, copy)
        document = App.openDocument(str(copy))
        try:
            document.UndoMode = 1
            assert len(document.Objects) == fixture["object_count"]
            base = b14_recipe.freecad_base_snapshot(
                module, document,
                expected_macro_version=module.MACRO_VERSION_NUMBER,
            )
            assert base["semantic"]["object_count"] == (
                fixture["object_count"]
            )
            hosts = _selected_hosts(module, document, fixture)
            before = _snapshot(document)
            request = contract["request"]
            invalid_args = _request_arguments(
                document, hosts, rejected["host_a_chainage_mm"], request,
            )
            inherited_builder = module._build_curve_inheriting_c10_turnout
            inherited_recompute = module._document_recompute

            def unexpected_exact_build(*_args, **_kwargs):
                raise AssertionError(
                    "Exact turnout construction began before rejection"
                )

            def unexpected_recompute(*_args, **_kwargs):
                raise AssertionError(
                    "Document recompute began before rejection"
                )

            module._build_curve_inheriting_c10_turnout = (
                unexpected_exact_build
            )
            module._document_recompute = unexpected_recompute
            try:
                preview_diagnostic = _expect_rejected(
                    lambda: module.solve_rea_c10_crossover_geometry(
                        *invalid_args,
                    )
                )
                assert _snapshot(document) == before
                create_diagnostic = _expect_rejected(
                    lambda: module.create_rea_c10_crossover(*invalid_args)
                )
            finally:
                module._build_curve_inheriting_c10_turnout = inherited_builder
                module._document_recompute = inherited_recompute
            assert create_diagnostic == preview_diagnostic
            assert _snapshot(document) == before

            valid_args = _request_arguments(
                document, hosts, accepted["host_a_chainage_mm"], request,
            )
            solved = module.solve_rea_c10_crossover_geometry(*valid_args)
            preflight = _verify_complete_result(
                solved, accepted, request,
            )
            assert _snapshot(document) == before
            _verify_signature_invalidation(module, solved, valid_args)
            after_signatures = _snapshot(document)
            assert after_signatures == before, {
                "history_before": (before["undo"], before["redo"]),
                "history_after": (
                    after_signatures["undo"], after_signatures["redo"],
                ),
                "objects": [
                    (old[0], old[2] == new[2], old[3] == new[3])
                    for old, new in zip(
                        before["objects"], after_signatures["objects"],
                    )
                    if old != new
                ],
            }

            config = module.create_rea_c10_crossover(
                *valid_args, pre_solved=solved,
            )
            assert config["crossover_id"] == "XO-001"
            _verify_exact_result(
                config, preflight, request["comparison_tolerance_mm"],
            )
            assert len(document.Objects) > fixture["object_count"]
            assert document.UndoCount == before["undo"] + 1
            _verify_edit_rejection(
                module, document, valid_args,
                rejected["host_a_chainage_mm"],
            )
        finally:
            App.closeDocument(document.Name)
        _verify_extension_rejection(module, source, temporary, contract)
    assert _sha256(source) == source_hash
    print(SENTINEL)


def _run_as_script():
    try:
        validate()
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


if __name__ in {"__main__", "freecad_validate_phase8_crossover_preflight"}:
    _run_as_script()
