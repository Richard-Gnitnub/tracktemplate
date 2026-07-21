"""FreeCAD oracle for fixed XO-001 chair-analysis persistence and reuse."""

import ast
import copy
import hashlib
import json
import pathlib
import shutil
import sys
import tempfile
import types

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.freecad_bridge import b14_recipe  # noqa: E402
from tools.freecad_bridge import crossover_timber_recipe  # noqa: E402


CONTRACT_PATH = (
    ROOT / "reference" / "contracts" /
    "phase1-chair-analysis-persistence.json"
)
CORE_KEYS = (
    "entity_id",
    "entity_kind",
    "findings",
    "geometry_signature",
    "model_timber_support_plan",
    "positions",
    "production_geometry_changed",
    "schema_version",
    "settings",
    "source_basis",
    "status",
    "summary",
)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_macro(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    launch = tree.body[-1] if tree.body else None
    assert (
        isinstance(launch, ast.Expr)
        and isinstance(launch.value, ast.Call)
        and isinstance(launch.value.func, ast.Name)
        and launch.value.func.id == "run_macro"
    ), "B14 launch boundary changed"
    tree.body.pop()
    ast.fix_missing_locations(tree)
    module = types.ModuleType("phase1_chair_analysis_persistence_b14")
    module.__file__ = str(path)
    exec(compile(tree, str(path), "exec"), module.__dict__)
    return module


def _canonical(value):
    if isinstance(value, dict):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, set):
        return sorted(_canonical(item) for item in value)
    if isinstance(value, float):
        return round(value, 9)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def _digest(value):
    encoded = json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _analysis_core(result):
    return {
        key: copy.deepcopy(result[key])
        for key in CORE_KEYS
        if key in result
    }


def _assert_result(result, contract):
    expected = contract["legacy_semantics"]
    core = _analysis_core(result)
    assert str(result.get("status") or "") == expected["status"]
    assert str(result.get("geometry_signature") or "") == expected[
        "geometry_signature"
    ]
    assert _digest(core) == expected["semantic_sha256"]
    positions = list(result.get("positions") or [])
    findings = list(result.get("findings") or [])
    assert _digest([
        str(item.get("stable_chair_position_identity") or "")
        for item in positions
    ]) == expected["position_identity_sha256"]
    assert _digest(findings) == expected["finding_sha256"]

    summary = dict(result.get("summary") or {})
    for key, value in expected["summary_counts"].items():
        assert summary.get(key) == value
    assert summary.get("severity_counts") == expected["severity_counts"]
    assert summary.get("family_counts") == expected["family_counts"]


def _shape_summary(shape):
    box = shape.BoundBox
    return {
        "edges": len(shape.Edges),
        "faces": len(shape.Faces),
        "solids": len(shape.Solids),
        "vertices": len(shape.Vertexes),
        "bounds_mm": [
            round(float(value), 9)
            for value in (
                box.XMin, box.YMin, box.ZMin,
                box.XMax, box.YMax, box.ZMax,
            )
        ],
    }


def _display_snapshot(module, document, entity_id, expected):
    objects = module._chair_analysis_display_objects(
        document, "crossover", entity_id
    )
    assert len(objects) == expected["object_count"]
    by_role = {
        module.object_string_property(obj, "GeneratedRole", ""): obj
        for obj in objects
    }
    assert set(by_role) == {
        expected["group_role"], expected["marker_role"]
    }
    group = by_role[expected["group_role"]]
    marker = by_role[expected["marker_role"]]
    assert str(group.Name) == expected["group_name"]
    assert str(marker.Name) == expected["marker_name"]
    assert str(marker.TypeId) == expected["marker_type_id"]
    assert _shape_summary(marker.Shape) == expected["marker_shape"]
    return {
        role: str(obj.Name)
        for role, obj in sorted(by_role.items())
    }


def _persisted(module, document, entity_id):
    result = module._chair_read_cached_result(
        document, "crossover", entity_id
    )
    assert isinstance(result, dict)
    return result


def _metadata_payload(module, document, entity_id):
    obj = module._chair_settings_object(document, "crossover", entity_id)
    assert obj is not None
    return module.object_string_property(
        obj, module.CHAIR_ANALYSIS_RESULT_PROPERTY, ""
    )


def _assert_timing_keys(result, expected):
    assert sorted((result.get("performance_timings_ms") or {}).keys()) == expected


def validate():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    source = contract["source_state"]["b14"]
    macro_path = ROOT / source["path"]
    assert _sha256(macro_path) == source["sha256"]
    module = _load_macro(macro_path)
    assert str(module.MACRO_VERSION_NUMBER) == source["version"]

    fixture = contract["fixture"]
    fixture_path = ROOT / fixture["path"]
    assert fixture_path.is_file(), (
        "Reproduce the ignored fixture first with: {}"
        .format(fixture["reproduction_command"])
    )
    fixture_hash = _sha256(fixture_path)
    assert fixture_hash == fixture["sha256"]

    document = None
    with tempfile.TemporaryDirectory(prefix="phase1-chair-oracle-") as temporary:
        copied_path = pathlib.Path(temporary) / "b14-xo001-chair.FCStd"
        shutil.copy2(str(fixture_path), str(copied_path))
        document = App.openDocument(str(copied_path))
        try:
            document.UndoMode = 1
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
            timber = module.apply_crossover_b4_timbering(document, entity_id)
            assert timber["resolution_signature"] == scenario[
                "prerequisite_b4_resolution_signature"
            ]

            lifecycle = contract["legacy_semantics"][
                "lifecycle_object_counts"
            ]
            display_expected = contract["legacy_semantics"]["display"]
            persistence = contract["persistence_boundary"]
            assert len(document.Objects) == lifecycle[
                "after_b4_before_analysis"
            ]
            assert module._chair_analysis_display_objects(
                document, "crossover", entity_id
            ) == []
            assert module._chair_read_cached_result(
                document, "crossover", entity_id
            ) is None

            first = module.analyse_entity_chair_positions(
                document, "crossover", entity_id
            )
            assert first.get("cache_reused") is False
            assert first.get("display_cache_reused") is False
            _assert_result(first, contract)
            _assert_timing_keys(
                first, persistence["cold_returned_timing_keys"]
            )
            stored_first = _persisted(module, document, entity_id)
            _assert_result(stored_first, contract)
            _assert_timing_keys(
                stored_first, persistence["cold_persisted_timing_keys"]
            )
            assert stored_first.get("cache_reused") is False
            assert stored_first.get("display_cache_reused") is False
            assert len(document.Objects) == lifecycle["after_cold_analysis"]
            first_display = _display_snapshot(
                module, document, entity_id, display_expected
            )
            first_payload = _metadata_payload(module, document, entity_id)
            assert len(first_payload) > 1_000_000
            current_config = module.crossover_config_by_id(document, entity_id)
            assert module.chair_analysis_effective_status(
                document, "crossover", current_config
            ) == contract["legacy_semantics"]["status"]

            second = module.analyse_entity_chair_positions(
                document, "crossover", entity_id
            )
            assert second.get("cache_reused") is True
            assert second.get("display_cache_reused") is True
            _assert_result(second, contract)
            _assert_timing_keys(
                second, persistence["reuse_returned_timing_keys"]
            )
            stored_second = _persisted(module, document, entity_id)
            _assert_result(stored_second, contract)
            _assert_timing_keys(
                stored_second, persistence["reuse_persisted_timing_keys"]
            )
            assert stored_second.get("cache_reused") is True
            assert stored_second.get("display_cache_reused") is True
            assert len(document.Objects) == lifecycle[
                "after_unchanged_reuse"
            ]
            assert _display_snapshot(
                module, document, entity_id, display_expected
            ) == first_display
            second_payload = _metadata_payload(module, document, entity_id)
            assert second_payload != first_payload

            document.undo()
            assert len(document.Objects) == lifecycle["after_reuse_undo"]
            assert _metadata_payload(
                module, document, entity_id
            ) == first_payload
            assert _persisted(
                module, document, entity_id
            ).get("cache_reused") is False
            assert _display_snapshot(
                module, document, entity_id, display_expected
            ) == first_display

            document.redo()
            assert len(document.Objects) == lifecycle["after_reuse_redo"]
            assert _metadata_payload(
                module, document, entity_id
            ) == second_payload
            assert _persisted(
                module, document, entity_id
            ).get("cache_reused") is True

            document.save()
            name = document.Name
            App.closeDocument(name)
            document = App.openDocument(str(copied_path))
            assert len(document.Objects) == lifecycle["after_reopen"]
            assert _metadata_payload(
                module, document, entity_id
            ) == second_payload
            reopened = _persisted(module, document, entity_id)
            _assert_result(reopened, contract)
            _assert_timing_keys(
                reopened, persistence["reuse_persisted_timing_keys"]
            )
            assert _display_snapshot(
                module, document, entity_id, display_expected
            ) == first_display
            reopened_config = module.crossover_config_by_id(
                document, entity_id
            )
            assert module.chair_analysis_effective_status(
                document, "crossover", reopened_config
            ) == contract["legacy_semantics"]["status"]

            third = module.analyse_entity_chair_positions(
                document, "crossover", entity_id
            )
            assert third.get("cache_reused") is True
            assert third.get("display_cache_reused") is True
            _assert_result(third, contract)
            _assert_timing_keys(
                third, persistence["reuse_returned_timing_keys"]
            )
            stored_third = _persisted(module, document, entity_id)
            _assert_timing_keys(
                stored_third, persistence["reuse_persisted_timing_keys"]
            )
            assert _metadata_payload(
                module, document, entity_id
            ) != second_payload
            assert len(document.Objects) == lifecycle[
                "after_reopened_reuse"
            ]
            assert _display_snapshot(
                module, document, entity_id, display_expected
            ) == first_display
        finally:
            if document is not None and document.Name in App.listDocuments():
                App.closeDocument(document.Name)

    assert _sha256(fixture_path) == fixture_hash
    print("Phase 1 chair analysis persistence FreeCAD oracle passed")


def _run_as_script():
    try:
        validate()
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


if __name__ in {
    "__main__", "freecad_validate_phase1_chair_analysis_persistence"
}:
    _run_as_script()
