"""FreeCAD lifecycle oracle for fixed B14 crossover automatic timbering."""

import ast
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
from tools.freecad_bridge import crossover_timber_recipe as recipe  # noqa: E402


CONTRACT_PATH = (
    ROOT / "reference" / "contracts" / "phase1-crossover-timbering.json"
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
    module = types.ModuleType("phase1_crossover_timbering_b14")
    module.__file__ = str(path)
    exec(compile(tree, str(path), "exec"), module.__dict__)
    return module


def _expected_result(contract, signature_field):
    expected = contract["legacy_semantics"]
    return {
        "status": expected["status"],
        "counts": expected["counts"],
        "record_turnout_sides": expected["record_turnout_sides"],
        "record_envelope_kinds": expected["record_envelope_kinds"],
        "record_identity_sha256": expected["record_identity_sha256"],
        "stable_record_sha256": expected["stable_record_sha256"],
        "resolution_signature": expected[signature_field],
    }


def _assert_core(module, result, contract, signature_field):
    assert recipe.result_snapshot(module, result) == _expected_result(
        contract, signature_field
    )


def _assert_shape(module, document, crossover_id, expected):
    obj = module._crossover_b4_object(document, crossover_id)
    assert obj is not None
    assert recipe.shape_summary(obj.Shape) == expected
    return obj


def _diagnostic_witness(result):
    analysis = result.get("resolved_analysis") or {}
    return {
        "has_geometry_signature": bool(analysis.get("geometry_signature")),
        "analysis_basis": str(analysis.get("analysis_basis") or ""),
    }


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
    with tempfile.TemporaryDirectory(prefix="phase1-b4-oracle-") as temporary:
        copied_path = pathlib.Path(temporary) / "b14-xo001-timbering.FCStd"
        shutil.copy2(str(fixture_path), str(copied_path))
        document = App.openDocument(str(copied_path))
        try:
            document.UndoMode = 1
            base = b14_recipe.freecad_base_snapshot(module, document)
            assert base["semantic_sha256"] == fixture["semantic_sha256"]
            assert len(document.Objects) == fixture["object_count"]

            scenario = contract["scenario"]
            config, selected = recipe.create_controlled_crossover(
                module, document, scenario["host_a_chainage_mm"]
            )
            crossover_id = str(config["crossover_id"])
            assert crossover_id == scenario["crossover_id"]
            for side in ("a", "b"):
                expected_identity = scenario["host_{}_identity".format(side)]
                actual_identity = selected["host_{}_identity".format(side)]
                for key, value in expected_identity.items():
                    assert actual_identity[key] == value

            lifecycle = contract["legacy_semantics"]["lifecycle_object_counts"]
            assert len(document.Objects) == lifecycle["after_crossover_geometry"]
            before_apply = recipe.document_snapshot(
                module, document, crossover_id
            )

            first = module.apply_crossover_b4_timbering(document, crossover_id)
            assert first.get("cache_reused") is False
            _assert_core(
                module, first, contract, "default_resolution_signature"
            )
            first_object = _assert_shape(
                module,
                document,
                crossover_id,
                contract["legacy_semantics"]["display_shape"],
            )
            assert str(first_object.Name) == "CrossoverB4Timbering_XO_001"
            assert len(document.Objects) == lifecycle["after_first_apply"]
            first_state = recipe.document_snapshot(module, document, crossover_id)

            stored = module.crossover_config_by_id(document, crossover_id)
            stored_result = stored.get("b4_result") or {}
            first_diagnostic = _diagnostic_witness(first)
            stored_diagnostic = _diagnostic_witness(stored_result)
            defect = contract["legacy_defects"][
                "resolved_analysis_persistence_drift"
            ]["witness"]
            assert first_diagnostic == {
                "has_geometry_signature": defect[
                    "first_has_geometry_signature"
                ],
                "analysis_basis": defect["first_analysis_basis"],
            }
            assert stored_diagnostic == {
                "has_geometry_signature": defect[
                    "reused_has_geometry_signature"
                ],
                "analysis_basis": defect["reused_analysis_basis"],
            }

            second = module.apply_crossover_b4_timbering(document, crossover_id)
            assert second.get("cache_reused") is True
            _assert_core(
                module, second, contract, "default_resolution_signature"
            )
            assert _diagnostic_witness(second) == stored_diagnostic
            assert len(document.Objects) == lifecycle["after_unchanged_reuse"]
            assert recipe.document_snapshot(
                module, document, crossover_id
            ) == first_state
            assert str(module._crossover_b4_object(
                document, crossover_id
            ).Name) == str(first_object.Name)

            document.undo()
            document.recompute()
            assert len(document.Objects) == lifecycle["after_undo"]
            assert module._crossover_b4_object(document, crossover_id) is None
            assert recipe.document_snapshot(
                module, document, crossover_id
            ) == before_apply

            document.redo()
            document.recompute()
            assert len(document.Objects) == lifecycle["after_redo"]
            assert recipe.document_snapshot(
                module, document, crossover_id
            ) == first_state

            document.save()
            document_name = document.Name
            App.closeDocument(document_name)
            document = App.openDocument(str(copied_path))
            assert len(document.Objects) == lifecycle["after_reopen"]
            assert recipe.document_snapshot(
                module, document, crossover_id
            ) == first_state
            reopened = module.apply_crossover_b4_timbering(
                document, crossover_id
            )
            assert reopened.get("cache_reused") is True
            _assert_core(
                module, reopened, contract, "default_resolution_signature"
            )

            hidden = module.apply_crossover_b4_timbering(
                document,
                crossover_id,
                b4_settings={"show_b4_geometry": False},
            )
            assert hidden.get("cache_reused") is False
            _assert_core(
                module,
                hidden,
                contract,
                "display_hidden_resolution_signature",
            )
            assert recipe.shape_summary(
                module._crossover_b4_object(document, crossover_id).Shape
            ) == contract["legacy_semantics"]["display_shape"]

            restored = module.apply_crossover_b4_timbering(
                document,
                crossover_id,
                b4_settings={"show_b4_geometry": True},
            )
            assert restored.get("cache_reused") is False
            _assert_core(
                module, restored, contract, "default_resolution_signature"
            )

            calculation_changed = module.apply_crossover_b4_timbering(
                document,
                crossover_id,
                b3_settings=scenario["b3_calculation_change"],
            )
            assert calculation_changed.get("cache_reused") is False
            _assert_core(
                module,
                calculation_changed,
                contract,
                "calculation_change_resolution_signature",
            )

            module.clear_crossover_b4_timbering(document, crossover_id)
            cleared_config = module.crossover_config_by_id(
                document, crossover_id
            )
            assert len(document.Objects) == lifecycle["after_clear"]
            assert module._crossover_b4_object(document, crossover_id) is None
            assert module.crossover_b4_effective_status(
                document, cleared_config
            ) == module.CROSSOVER_B4_STATUS_NOT_APPLIED
            roles = recipe.role_counts(module, document)
            assert roles.get(module.CROSSOVER_B4_ROLE, 0) == 0
            assert roles.get(module.CROSSOVER_TIMBER_ANALYSIS_GROUP_ROLE) == 1
            assert roles.get(module.CROSSOVER_TIMBER_CONFLICT_MARKER_ROLE) == 1

            before_fault = recipe.document_snapshot(
                module, document, crossover_id
            )
            before_objects = recipe.object_map(module, document)
            original_tagger = module.tag_generated_object
            fault = contract["legacy_defects"]["incomplete_abort_cleanup"]

            def failing_tagger(obj, role, set_id):
                if str(role) == str(module.CROSSOVER_B4_ROLE):
                    raise RuntimeError(fault["fault_text"])
                return original_tagger(obj, role, set_id)

            module.tag_generated_object = failing_tagger
            try:
                try:
                    module.apply_crossover_b4_timbering(
                        document, crossover_id
                    )
                except RuntimeError as error:
                    assert str(error) == fault["fault_text"]
                else:
                    raise AssertionError("Injected B4 failure was not raised")
            finally:
                module.tag_generated_object = original_tagger

            after_fault = recipe.document_snapshot(
                module, document, crossover_id
            )
            after_objects = recipe.object_map(module, document)
            assert after_fault["config"] == before_fault["config"]
            assert len(document.Objects) == lifecycle["after_injected_failure"]
            assert set(before_objects) - set(after_objects) == set()
            added_names = set(after_objects) - set(before_objects)
            retained = fault["retained_object"]
            assert added_names == {retained["name"]}
            added = after_objects[retained["name"]]
            assert {
                key: added[key]
                for key in (
                    "name",
                    "type_id",
                    "generated_role",
                    "crossover_id",
                )
            } == retained
            assert all(
                before_objects[name] == after_objects[name]
                for name in before_objects
            )
        finally:
            if document is not None and document.Name in App.listDocuments():
                App.closeDocument(document.Name)

    assert _sha256(fixture_path) == fixture_hash
    print("Phase 1 crossover timbering FreeCAD oracle passed")


def _run_as_script():
    try:
        validate()
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


if __name__ in {"__main__", "freecad_validate_phase1_crossover_timbering"}:
    _run_as_script()
