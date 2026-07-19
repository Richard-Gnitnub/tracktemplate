#!/usr/bin/env python3
"""Fast contracts for the Phase 1 B14 ordinary-track selected export."""

import ast
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

    helper_path = (
        PROJECT_ROOT / "tools" / "freecad_bridge" / "ordinary_track_export_recipe.py"
    )
    helper_text = helper_path.read_text(encoding="utf-8")
    for forbidden in ("import FreeCAD", "import Part", "import Mesh", "PySide"):
        assert forbidden not in helper_text

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
        "validate_dxf_export_bounds",
        "validate_svg_export_bounds",
        "Mesh.Mesh",
        "Part.Shape",
    ):
        assert required in driver_text

    print("Phase 1 ordinary-track selected-export validation passed")


if __name__ == "__main__":
    validate()
