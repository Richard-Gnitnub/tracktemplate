"""FreeCAD oracle for fixed XO-001 chair-analysis invalidation behavior."""

import copy
import json
import pathlib
import shutil
import sys
import tempfile

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import b14_recipe  # noqa: E402
from tools.freecad_bridge import chair_analysis_recipe as chair_recipe  # noqa: E402
from tools.freecad_bridge import crossover_timber_recipe  # noqa: E402


CONTRACT_PATH = (
    ROOT / "reference" / "contracts" /
    "phase1-chair-analysis-invalidation.json"
)


def _mutate_point(points, delta):
    result = copy.deepcopy(points)
    result[0][0] = float(result[0][0]) + float(delta)
    return result


def _logical_case(module, baseline_signature, baseline_output, entity_kind,
                  config, settings, rails, timbers):
    signature = module._chair_geometry_signature(
        entity_kind, config, settings, rails, timbers
    )
    result = module.analyse_chair_position_records(
        entity_kind, config, rails, timbers, settings
    )
    output_sha256 = chair_recipe.digest(
        chair_recipe.output_without_settings(result)
    )
    return {
        "signature_changed": signature != baseline_signature,
        "output_changed": output_sha256 != baseline_output,
        "output_sha256": output_sha256,
        "position_count": len(result.get("positions") or []),
        "finding_count": len(result.get("findings") or []),
        "status": result.get("status"),
    }


def _display_layers(module, document, entity_id):
    result = {}
    for obj in module._chair_analysis_display_objects(
        document, "crossover", entity_id
    ):
        role = module.object_string_property(obj, "GeneratedRole", "")
        shape = getattr(obj, "Shape", None)
        result[role] = {
            "type_id": str(obj.TypeId),
            "edges": (
                len(shape.Edges)
                if shape is not None and not shape.isNull()
                else 0
            ),
        }
    return result


def _assert_application_step(module, document, entity_id, result, expected,
                             presentation):
    assert result.get("cache_reused") is expected["cache_reused"]
    assert (
        result.get("display_cache_reused")
        is expected["display_cache_reused"]
    )
    assert result.get("geometry_signature") == presentation[
        "common_geometry_signature"
    ]
    assert chair_recipe.digest(
        chair_recipe.output_without_settings(result)
    ) == presentation["common_output_without_settings_sha256"]
    assert len(document.Objects) == expected["object_count"]
    assert _display_layers(module, document, entity_id) == expected["layers"]


def validate():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    source = contract["source_state"]["b14"]
    macro_path = ROOT / source["path"]
    assert chair_recipe.sha256_file(macro_path) == source["sha256"]
    module = chair_recipe.load_macro_without_launch(
        macro_path, "phase1_chair_analysis_invalidation_b14"
    )
    assert str(module.MACRO_VERSION_NUMBER) == source["version"]

    fixture = contract["fixture"]
    fixture_path = ROOT / fixture["path"]
    assert fixture_path.is_file(), (
        "Reproduce the ignored fixture first with: {}"
        .format(fixture["reproduction_command"])
    )
    fixture_hash = chair_recipe.sha256_file(fixture_path)
    assert fixture_hash == fixture["sha256"]

    document = None
    with tempfile.TemporaryDirectory(
        prefix="phase1-chair-invalidation-"
    ) as temporary:
        copied_path = pathlib.Path(temporary) / "b14-chair-invalidation.FCStd"
        shutil.copy2(str(fixture_path), str(copied_path))
        document = App.openDocument(str(copied_path))
        try:
            base = b14_recipe.freecad_base_snapshot(module, document)
            assert base["semantic_sha256"] == fixture["semantic_sha256"]
            assert len(document.Objects) == fixture["object_count"]

            scenario = contract["scenario"]
            config, _selected = (
                crossover_timber_recipe.create_controlled_crossover(
                    module, document, scenario["host_a_chainage_mm"]
                )
            )
            entity_id = str(config["crossover_id"])
            assert entity_id == scenario["crossover_id"]
            timbering = module.apply_crossover_b4_timbering(
                document, entity_id
            )
            assert timbering["resolution_signature"] == scenario[
                "prerequisite_b4_resolution_signature"
            ]

            config = module.crossover_config_by_id(document, entity_id)
            settings = module.normalise_chair_analysis_settings(
                config.get("chair_analysis_settings")
            )
            rails = module.chair_rail_records_for_entity(
                document, "crossover", config
            )
            timbers = module.chair_timber_records_for_entity(
                document, "crossover", config
            )
            assert len(rails) == scenario["rail_count"]
            assert len(timbers) == scenario["timber_count"]

            inputs = contract["observed_inputs"]
            assert sorted(settings) == inputs["settings"]["normalised_keys"]
            assert chair_recipe.record_schema(rails) == inputs[
                "rail_records"
            ]["schema"]
            assert chair_recipe.record_schema(timbers) == inputs[
                "timber_records"
            ]["schema"]

            baseline_signature = module._chair_geometry_signature(
                "crossover", config, settings, rails, timbers
            )
            baseline_result = module.analyse_chair_position_records(
                "crossover", config, rails, timbers, settings
            )
            baseline = contract["baseline"]
            baseline_output = chair_recipe.digest(
                chair_recipe.output_without_settings(baseline_result)
            )
            assert baseline_signature == baseline["geometry_signature"]
            assert chair_recipe.digest(
                chair_recipe.deterministic_result(baseline_result)
            ) == baseline["deterministic_result_sha256"]
            assert baseline_output == baseline[
                "output_without_settings_sha256"
            ]
            assert baseline_result.get("status") == baseline["status"]
            assert len(baseline_result.get("positions") or []) == baseline[
                "position_count"
            ]
            assert len(baseline_result.get("findings") or []) == baseline[
                "finding_count"
            ]

            expected_settings = contract["mutation_matrix"]["settings"]
            assert set(expected_settings) == set(
                chair_recipe.SETTING_ALTERNATIVES
            )
            for key, value in chair_recipe.SETTING_ALTERNATIVES.items():
                changed = dict(settings)
                changed[key] = value
                changed = module.normalise_chair_analysis_settings(changed)
                signature = module._chair_geometry_signature(
                    "crossover", config, changed, rails, timbers
                )
                result = module.analyse_chair_position_records(
                    "crossover", config, rails, timbers, changed
                )
                actual = {
                    "signature_changed": signature != baseline_signature,
                    "output_without_settings_changed": (
                        chair_recipe.digest(
                            chair_recipe.output_without_settings(result)
                        ) != baseline_output
                    ),
                    "position_count": len(result.get("positions") or []),
                    "finding_count": len(result.get("findings") or []),
                }
                assert actual == expected_settings[key], key

            actual_records = {}

            def record_case(name, changed_config=None, changed_rails=None,
                            changed_timbers=None):
                actual_records[name] = _logical_case(
                    module,
                    baseline_signature,
                    baseline_output,
                    "crossover",
                    changed_config if changed_config is not None else config,
                    settings,
                    changed_rails if changed_rails is not None else rails,
                    changed_timbers if changed_timbers is not None else timbers,
                )

            changed = copy.deepcopy(config)
            changed["template_set_id"] = "SET-PROBE"
            record_case(
                "config_template_set_omitted", changed_config=changed
            )
            changed = copy.deepcopy(config)
            changed["handing"] = module.TURNOUT_HAND_RIGHT
            record_case(
                "config_handing_current_core_unused", changed_config=changed
            )

            changed = copy.deepcopy(rails)
            changed[0]["points"] = _mutate_point(
                changed[0]["points"], 0.01
            )
            record_case("rail_points_included", changed_rails=changed)
            changed = copy.deepcopy(rails)
            changed[0]["name"] = str(changed[0].get("name") or "") + " probe"
            record_case("rail_name_omitted", changed_rails=changed)
            changed = copy.deepcopy(rails)
            changed[0]["supported_feature"] = "probe supported feature"
            record_case(
                "rail_supported_feature_omitted", changed_rails=changed
            )
            changed = copy.deepcopy(rails)
            changed[0]["parent_turnout_identity"] = "TO-PROBE"
            record_case(
                "rail_parent_turnout_omitted", changed_rails=changed
            )
            changed = copy.deepcopy(rails)
            source_config = dict(
                changed[0].get("source_configuration") or {}
            )
            source_config["gauge_face"] = "probe gauge face"
            changed[0]["source_configuration"] = source_config
            record_case(
                "rail_source_configuration_omitted", changed_rails=changed
            )
            assert rails[0].get("gauge_face_points")
            changed = copy.deepcopy(rails)
            changed[0]["gauge_face_points"] = _mutate_point(
                changed[0]["gauge_face_points"], 0.50
            )
            record_case(
                "rail_gauge_face_current_core_unused", changed_rails=changed
            )
            changed = copy.deepcopy(rails)
            changed[0]["points"] = _mutate_point(
                changed[0]["points"], 0.000004
            )
            record_case(
                "rail_point_below_signature_precision", changed_rails=changed
            )
            changed = copy.deepcopy(rails)
            changed.reverse()
            record_case("rail_order_over_invalidates", changed_rails=changed)

            changed = copy.deepcopy(timbers)
            changed[0]["centre"][0] = (
                float(changed[0]["centre"][0]) + 0.01
            )
            record_case("timber_centre_included", changed_timbers=changed)
            changed = copy.deepcopy(timbers)
            changed[0]["identifier"] = "S99-PROBE"
            record_case("timber_identifier_omitted", changed_timbers=changed)
            changed_axes = copy.deepcopy(timbers)
            changed_axes[0]["width_axis"] = [0.0, 1.0]
            changed_axes[0]["length_axis"] = [1.0, 0.0]
            record_case("timber_axes_omitted", changed_timbers=changed_axes)
            changed = copy.deepcopy(timbers)
            changed[0]["protected_features"] = ["probe crossing feature"]
            record_case(
                "timber_protected_features_omitted", changed_timbers=changed
            )
            changed = copy.deepcopy(timbers)
            source_config = dict(
                changed[0].get("source_configuration") or {}
            )
            source_config["probe"] = "changed"
            changed[0]["source_configuration"] = source_config
            record_case(
                "timber_source_configuration_omitted", changed_timbers=changed
            )
            support_index = next(
                index for index, item in enumerate(timbers)
                if item.get("support_requirements")
            )
            changed = copy.deepcopy(timbers)
            changed[support_index]["support_requirements"] = []
            record_case(
                "timber_support_requirements_omitted", changed_timbers=changed
            )
            suffix_index = next(
                index for index, item in enumerate(timbers)
                if (item.get("source_configuration") or {}).get(
                    "crossing_suffix"
                )
            )
            changed = copy.deepcopy(timbers)
            changed[suffix_index]["source_configuration"] = dict(
                changed[suffix_index].get("source_configuration") or {}
            )
            changed[suffix_index]["source_configuration"][
                "crossing_suffix"
            ] = "A"
            record_case(
                "timber_crossing_suffix_omitted", changed_timbers=changed
            )
            changed = copy.deepcopy(timbers)
            changed.reverse()
            record_case(
                "timber_order_over_invalidates", changed_timbers=changed
            )
            assert actual_records == contract["mutation_matrix"]["records"]

            original_rail_extractor = module.chair_rail_records_for_entity
            original_timber_extractor = module.chair_timber_records_for_entity
            module.chair_rail_records_for_entity = (
                lambda *_args, **_kwargs: copy.deepcopy(rails)
            )
            module.chair_timber_records_for_entity = (
                lambda *_args, **_kwargs: copy.deepcopy(timbers)
            )
            try:
                presentation = contract["presentation_boundary"]
                expected_steps = presentation["steps"]
                first = module.analyse_entity_chair_positions(
                    document, "crossover", entity_id, settings
                )
                _assert_application_step(
                    module, document, entity_id, first,
                    expected_steps["baseline"], presentation
                )

                steps = (
                    ("markers_hidden", "markers_visible", False),
                    ("markers_restored", "markers_visible", True),
                    ("protected_shown", "protected_markers_visible", True),
                    ("protected_hidden", "protected_markers_visible", False),
                    ("footprints_shown", "footprints_visible", True),
                    ("footprints_hidden", "footprints_visible", False),
                    (
                        "physical_visibility_changed",
                        "physical_solids_visible",
                        True,
                    ),
                    (
                        "unresolved_visibility_changed",
                        "unresolved_markers_visible",
                        True,
                    ),
                    ("cache_disabled", "cache_enabled", False),
                )
                current_settings = dict(settings)
                for name, key, value in steps:
                    current_settings[key] = value
                    result = module.analyse_entity_chair_positions(
                        document, "crossover", entity_id, current_settings
                    )
                    _assert_application_step(
                        module, document, entity_id, result,
                        expected_steps[name], presentation
                    )

                current_settings["cache_enabled"] = True
                current_settings["physical_solids_visible"] = False
                current_settings["unresolved_markers_visible"] = False
                module.chair_timber_records_for_entity = (
                    lambda *_args, **_kwargs: copy.deepcopy(changed_axes)
                )
                stale = module.analyse_entity_chair_positions(
                    document, "crossover", entity_id, current_settings
                )
                cache = contract["application_cache"]
                actual_stale_sha = chair_recipe.digest(
                    chair_recipe.output_without_settings(stale)
                )
                assert stale.get("cache_reused") is cache["cache_reused"]
                assert stale.get("geometry_signature") == cache[
                    "geometry_signature"
                ]
                assert actual_stale_sha == cache[
                    "actual_stale_output_sha256"
                ]
                assert actual_records["timber_axes_omitted"][
                    "output_sha256"
                ] == cache["expected_recalculated_output_sha256"]
                assert (
                    actual_stale_sha
                    != cache["expected_recalculated_output_sha256"]
                ) is cache["stale_result_returned"]
            finally:
                module.chair_rail_records_for_entity = original_rail_extractor
                module.chair_timber_records_for_entity = (
                    original_timber_extractor
                )
        finally:
            if document is not None and document.Name in App.listDocuments():
                App.closeDocument(document.Name)

    assert chair_recipe.sha256_file(fixture_path) == fixture_hash
    print("Phase 1 chair analysis invalidation FreeCAD oracle passed")


def _run_as_script():
    try:
        validate()
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


if __name__ in {
    "__main__", "freecad_validate_phase1_chair_analysis_invalidation"
}:
    _run_as_script()
