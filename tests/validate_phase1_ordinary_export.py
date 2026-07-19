#!/usr/bin/env python3
"""Fast contracts for the Phase 1 B14 ordinary-track export paths."""

import ast
import copy
import csv
import hashlib
import pathlib
import sys
import tempfile


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.freecad_bridge import ordinary_track_export_recipe as recipe  # noqa: E402


EXPECTED_B14_SHA256 = (
    "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_rows(revision=False):
    formats = ["DXF", "SVG", "STL", "STEP"]
    rows = []
    for index in range(recipe.EXPECTED_MANIFEST_ROW_COUNT):
        base_name = "Output_{:02d}.{}".format(
            index + 1,
            formats[index % len(formats)].lower(),
        )
        if revision:
            path = pathlib.PurePath(base_name)
            base_name = "{}_Rev_02{}".format(path.stem, path.suffix)
        row = {field: "" for field in recipe.MANIFEST_FIELDS}
        row.update({
            "Macro version": "10.2A8A7B14",
            "Export date and time": (
                "2026-07-19T21:00:00+00:00"
                if revision else "2026-07-19T20:00:00+00:00"
            ),
            "Template-set identifier": "SET-001",
            "Generated object name": "Object_{:02d}".format(index + 1),
            "Generated object role": "Template",
            "Export format": formats[index % len(formats)],
            "Export filename": base_name,
            "Full export path": "/different/root/{}".format(base_name),
            "Export status": "Success",
        })
        rows.append(row)
    return rows


def _write_manifest(path, revision=False):
    with path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(
            target, fieldnames=recipe.MANIFEST_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(_manifest_rows(revision))


def _write_failure_manifest(path):
    rows = _manifest_rows()
    rows[-1].update({
        "Export format": "STEP",
        "Export filename": recipe.CREATE_TIME_EXPORT_FAILED_FILENAME,
        "Full export path": "/different/root/{}".format(
            recipe.CREATE_TIME_EXPORT_FAILED_FILENAME
        ),
        "Export status": "Failure",
        "Error message": recipe.CREATE_TIME_EXPORT_FAILURE_MESSAGE,
    })
    with path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(
            target, fieldnames=recipe.MANIFEST_FIELDS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def _create_time_document_snapshot(output_directory):
    config = {
        "enabled": True,
        "output_directory": str(output_directory),
        "include_set_identifier": True,
        "include_object_role": True,
        "include_track_number": True,
        "include_section_number": True,
        "export_each_section": True,
        "create_combined_files": True,
        "overwrite_existing": False,
        "create_manifest": True,
        "open_output_directory": False,
        "current_template_set_only": True,
        "formats": {key: True for key in recipe.EXPORT_FORMATS},
        "selections": {
            "track_template_compound_2d": True,
            "track_template_compound_3d": True,
            "track_centrelines": True,
            "other_engraving": False,
        },
    }
    return {
        "semantic": {
            "schema_version": 1,
            "marker": "stable ordinary-track state",
            "persistence": {
                "settings": {
                    "values": {
                        "ProductionExportConfigurationJSON": copy.deepcopy(config),
                        "CurveRadius": 600.0,
                    }
                },
                "template": {
                    "values": {
                        "ProductionExportConfigurationJSON": copy.deepcopy(config),
                        "CurveRadius": 600.0,
                    }
                },
            },
        }
    }


def _revision_name(name):
    path = pathlib.PurePath(name)
    return "{}_Rev_02{}".format(path.stem, path.suffix)


def _write_variant(directory, revision=False):
    for name in recipe.EXPECTED_EXPORT_FILENAMES:
        target_name = _revision_name(name) if revision else name
        path = directory / target_name
        suffix = path.suffix.lower()
        if suffix == ".csv":
            _write_manifest(path, revision)
        elif suffix == ".step":
            path.write_text(
                "ISO-10303-21;\nHEADER;\n"
                "FILE_NAME('{}','{}',(''),(''),'','','');\nENDSEC;\n"
                "DATA;\n#1=PRODUCT('Open CASCADE STEP translator 7.8 {}','','',());\n"
                "#2=CARTESIAN_POINT('',(0.,0.,0.));\nENDSEC;\nEND-ISO-10303-21;\n".format(
                    "/different/root/{}".format(target_name),
                    "2026-07-19T21:00:00" if revision else "2026-07-19T20:00:00",
                    "902" if revision else "401",
                ),
                encoding="latin-1",
            )
        elif suffix == ".dxf":
            path.write_text(
                "0\nSECTION\n2\nHEADER\n9\n$TDCREATE\n40\n{}\n"
                "0\nENDSEC\n0\nSECTION\n2\nENTITIES\n"
                "0\nLINE\n8\nTemporaryProductionExport_{}_{}\n"
                "10\n0\n20\n0\n11\n10\n21\n10\n"
                "0\nENDSEC\n0\nEOF\n".format(
                    "999.0" if revision else "111.0",
                    "def456" if revision else "abc123",
                    "9" if revision else "2",
                ),
                encoding="utf-8",
            )
        elif suffix == ".svg":
            path.write_text(
                "<svg><g id=\"TemporaryProductionExport_{}_{}\">"
                "<path d=\"M 0 0 L 10 10\"/></g></svg>\n".format(
                    "def456" if revision else "abc123",
                    "9" if revision else "2",
                ),
                encoding="utf-8",
            )
        else:
            path.write_bytes(
                "stable {} content\n".format(recipe.logical_export_name(name)).encode(
                    "utf-8"
                )
            )


def _function_source(source, tree, name):
    node = next(
        item for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.ClassDef)) and item.name == name
    )
    return ast.get_source_segment(source, node)


def validate():
    assert recipe.EXPORT_RECIPE_SCHEMA_VERSION == 1
    assert recipe.EXPORT_SCOPE == "One template set"
    assert recipe.EXPORT_FORMATS == ("dxf", "svg", "stl", "step")
    assert recipe.EXPECTED_TASK_COUNT == 13
    assert len(recipe.EXPECTED_EXPORT_FILENAMES) == 14
    assert recipe.EXPECTED_MANIFEST_ROW_COUNT == 15
    assert recipe.EXPECTED_LOGICAL_EXPORT_SHA256 == (
        "91922662487f92b8bdb8f92a65e09fb7b62f2f9d1461704bb7c8cd41c2a15413"
    )
    assert recipe.EXPECTED_EXPORT_METRICS_SHA256 == (
        "37dcbc20e8ecda9c1a80b3e73646b0c1127211e01488d56eeef49aa08d0789b4"
    )
    assert recipe.EXPECTED_CREATE_TIME_LOGICAL_EXPORT_SHA256 == (
        "b33a2c5cfb6937d988046ad17584ed7bc2957514e77213282dfd665960bc4ffb"
    )
    assert recipe.EXPECTED_CREATE_TIME_DOCUMENT_SHA256 == (
        "a6aae6d70610ceec50a6223328db1454eca264effc12e7db5df07204707b3aa2"
    )
    assert recipe.EXPECTED_CREATE_TIME_PARTIAL_EXPORT_SHA256 == (
        "05d27a32b26435eda3b776498c2b28195a943bc2499ced404450f18ce349bf29"
    )
    assert recipe.CREATE_TIME_EXPORT_RECIPE_SCHEMA_VERSION == 1
    assert recipe.CREATE_TIME_EXPORT_FAILED_FILENAME == (
        "Curve_Set_001_Combined_Solid_Assembly.step"
    )
    assert recipe.logical_export_name("Example_Rev_02.svg") == "Example.svg"
    assert recipe.logical_export_name("Example.step") == "Example.step"

    with tempfile.TemporaryDirectory(prefix="phase1_export_contract_") as value:
        directory = pathlib.Path(value)
        _write_variant(directory)
        base_complete = recipe.export_directory_snapshot(directory)
        base = recipe.export_variant_snapshot(base_complete)
        recipe.validate_export_snapshot(base)

        _write_variant(directory, revision=True)
        complete = recipe.export_directory_snapshot(directory)
        preserved_base = recipe.export_variant_snapshot(complete)
        revision = recipe.export_variant_snapshot(complete, revision=2)
        recipe.validate_export_snapshot(preserved_base)
        recipe.validate_export_snapshot(revision, expected_revision=2)
        assert recipe.compare_logical_exports(base, preserved_base)
        assert recipe.compare_logical_exports(base, revision)
        assert len(complete["files"]) == 28
        assert complete["directories"] == []

        broken = directory / _revision_name(recipe.EXPECTED_EXPORT_FILENAMES[0])
        broken.write_text("different", encoding="utf-8")
        changed = recipe.export_variant_snapshot(
            recipe.export_directory_snapshot(directory), revision=2
        )
        try:
            recipe.compare_logical_exports(base, changed)
        except ValueError as error:
            assert "Export semantics differ" in str(error)
        else:
            raise AssertionError("Changed export content was accepted")

    left_document = _create_time_document_snapshot("/first/create-time/output")
    right_document = _create_time_document_snapshot("/second/create-time/output")
    left_before = copy.deepcopy(left_document)
    left_normalised = recipe.create_time_export_document_snapshot(
        left_document, enforce_expected_hash=False
    )
    right_normalised = recipe.create_time_export_document_snapshot(
        right_document, enforce_expected_hash=False
    )
    assert left_document == left_before
    assert left_normalised["semantic_sha256"] == right_normalised["semantic_sha256"]
    assert left_normalised["output_directory"] == "/first/create-time/output"
    assert left_normalised["production_export_config"]["output_directory"] == (
        recipe.CREATE_TIME_OUTPUT_DIRECTORY_PLACEHOLDER
    )
    base_document = copy.deepcopy(left_document)
    for owner in ("settings", "template"):
        config = base_document["semantic"]["persistence"][owner]["values"][
            "ProductionExportConfigurationJSON"
        ]
        config["enabled"] = False
        config["output_directory"] = ""
    assert recipe.compare_create_time_document_to_base(
        base_document, left_document
    )
    changed_document = copy.deepcopy(left_document)
    changed_document["semantic"]["marker"] = "changed"
    try:
        recipe.compare_create_time_document_to_base(
            base_document, changed_document
        )
    except ValueError as error:
        assert "beyond export configuration" in str(error)
    else:
        raise AssertionError("A non-export document change was accepted")
    mismatched_directories = copy.deepcopy(left_document)
    mismatched_directories["semantic"]["persistence"]["template"]["values"][
        "ProductionExportConfigurationJSON"
    ]["output_directory"] = "/different/template/output"
    try:
        recipe.create_time_export_document_snapshot(
            mismatched_directories, enforce_expected_hash=False
        )
    except ValueError as error:
        assert "output directories differ" in str(error)
    else:
        raise AssertionError("Mismatched persisted export directories were accepted")

    with tempfile.TemporaryDirectory(prefix="phase1_create_export_failure_") as value:
        directory = pathlib.Path(value)
        _write_variant(directory)
        success_variant = recipe.export_variant_snapshot(
            recipe.export_directory_snapshot(directory)
        )
        (directory / recipe.CREATE_TIME_EXPORT_FAILED_FILENAME).unlink()
        _write_failure_manifest(directory / "Curve_Set_001_Export_Manifest.csv")
        failure_snapshot = recipe.export_directory_snapshot(directory)
        failure = recipe.validate_create_time_failure_snapshot(
            failure_snapshot,
            success_variant,
            enforce_expected_hash=False,
        )
        assert failure["atomic_output_set"] is False
        assert failure["file_count"] == 13
        assert failure["missing_file"] == recipe.CREATE_TIME_EXPORT_FAILED_FILENAME
        assert failure["manifest_success_rows"] == 14
        assert failure["manifest_failure_rows"] == 1
        assert failure["temporary_directories"] == []

    helper_path = (
        PROJECT_ROOT / "tools" / "freecad_bridge" / "ordinary_track_export_recipe.py"
    )
    helper_text = helper_path.read_text(encoding="utf-8")
    for forbidden in ("import FreeCAD", "import Part", "import Mesh", "PySide"):
        assert forbidden not in helper_text
    metrics_helper = (
        PROJECT_ROOT / "tools" / "freecad_bridge" / "freecad_export_metrics.py"
    )
    metrics_text = metrics_helper.read_text(encoding="utf-8")
    assert "Mesh.Mesh" in metrics_text
    assert "Part.Shape" in metrics_text
    assert "format_export_metrics" in metrics_text
    assert "validate_dxf_export_bounds" in metrics_text
    assert "validate_svg_export_bounds" in metrics_text

    macro_path = PROJECT_ROOT / "AdvancedTurnout.FCMacro"
    assert _sha256(macro_path) == EXPECTED_B14_SHA256
    source = macro_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(macro_path))
    commit_source = _function_source(
        source, tree, "commit_staged_export_entries"
    )
    ordered_commit_markers = (
        "backups = []",
        "committed = []",
        "backups.append",
        "committed.append",
        "except Exception as error",
        "for final_path in reversed(committed)",
        "for final_path, backup_path in reversed(backups)",
        "Selected export commit failed and was rolled back",
    )
    positions = [commit_source.index(value) for value in ordered_commit_markers]
    assert positions == sorted(positions)

    selected_source = _function_source(
        source, tree, "run_selected_production_export"
    )
    for required in (
        "tempfile.mkdtemp",
        "dispatch_freecad_export",
        "write_export_manifest",
        "commit_staged_export_entries",
        "finally",
        "shutil.rmtree",
    ):
        assert required in selected_source
    assert selected_source.index("tempfile.mkdtemp") < selected_source.index(
        "dispatch_freecad_export"
    ) < selected_source.index("commit_staged_export_entries") < selected_source.index(
        "shutil.rmtree"
    )

    create_execute_source = _function_source(source, tree, "execute_export_tasks")
    create_order = (
        create_execute_source.index('for task in plan["tasks"]'),
        create_execute_source.index("dispatch_freecad_export"),
        create_execute_source.index("os.replace"),
        create_execute_source.index("except Exception as error"),
    )
    assert create_order == tuple(sorted(create_order))
    create_export_source = _function_source(source, tree, "run_production_export")
    assert "execute_export_tasks" in create_export_source
    assert "write_export_manifest" in create_export_source
    assert "commit_staged_export_entries" not in create_export_source
    run_macro_source = _function_source(source, tree, "run_macro")
    assert run_macro_source.index("doc.commitTransaction()") < run_macro_source.index(
        "run_production_export"
    ) < run_macro_source.index("show_production_export_summary") < run_macro_source.index(
        "Railway production outputs created"
    )

    bridge_root = PROJECT_ROOT / "tools" / "freecad_bridge"
    wrapper = bridge_root / "run-b14-ordinary-export"
    runner = bridge_root / "run_b14_ordinary_export.py"
    driver = bridge_root / "probes" / "b14_ordinary_export_driver.py"
    assert wrapper.is_file() and wrapper.stat().st_mode & 0o111
    assert runner.is_file() and runner.stat().st_mode & 0o111
    assert driver.is_file()
    wrapper_text = wrapper.read_text(encoding="utf-8")
    runner_text = runner.read_text(encoding="utf-8")
    driver_text = driver.read_text(encoding="utf-8")
    assert "run-isolated" in wrapper_text
    assert "shutil.copy2(base_path, document_path)" in runner_text
    assert "run_document_sha256_after" in runner_text
    assert "source_fixture_sha256_after" in runner_text
    assert "recipe_source_sha256" in runner_text
    assert "b14_ordinary_export_driver.py" in runner_text
    for scenario in (
        '"initial_selected_export"',
        '"non_overwrite_revision_export"',
        '"confirmed_atomic_overwrite"',
        '"injected_commit_failure_rollback"',
    ):
        assert scenario in driver_text
    for required in (
        "SelectedProductionExportDialog",
        "run_production_preflight",
        "run_selected_production_export",
        "commit_staged_export_entries",
        "ordinary_track_document_snapshot",
        "format_export_metrics",
    ):
        assert required in driver_text

    create_wrapper = bridge_root / "run-b14-ordinary-create-export"
    create_runner = bridge_root / "run_b14_ordinary_create_export.py"
    create_driver = (
        bridge_root / "probes" / "b14_ordinary_create_export_driver.py"
    )
    assert create_wrapper.is_file() and create_wrapper.stat().st_mode & 0o111
    assert create_runner.is_file() and create_runner.stat().st_mode & 0o111
    assert create_driver.is_file()
    create_wrapper_text = create_wrapper.read_text(encoding="utf-8")
    create_runner_text = create_runner.read_text(encoding="utf-8")
    create_driver_text = create_driver.read_text(encoding="utf-8")
    assert "run-isolated" in create_wrapper_text
    assert "shutil.copy2(base_path, document_path)" in create_runner_text
    assert "run_document_sha256_before" in create_runner_text
    assert "run_document_sha256_after" in create_runner_text
    assert "source_fixture_sha256_after" in create_runner_text
    assert "recipe_source_sha256" in create_runner_text
    assert "b14_ordinary_create_export_driver.py" in create_runner_text
    for scenario in (
        '"create_time_export_success"',
        '"create_time_export_final_task_failure"',
    ):
        assert scenario in create_driver_text
    for required in (
        "CurveInputDialog",
        "run_production_preflight",
        "run_production_export",
        "dispatch_freecad_export",
        "ordinary_track_document_snapshot",
        "create_time_export_document_snapshot",
        "validate_create_time_failure_snapshot",
        "format_export_metrics",
        "EXPECTED_EXPORT_METRICS_SHA256",
        "document.save()",
        "App.openDocument(saved_path)",
    ):
        assert required in create_driver_text

    print("Phase 1 ordinary-track export validation passed")


if __name__ == "__main__":
    validate()
