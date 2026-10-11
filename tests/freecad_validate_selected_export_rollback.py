#!/usr/bin/env python3
"""Prove selected-export rollback on a copied qualified FreeCAD document.

Ordinary filesystem faults exercise retained prior output and diagnostics.
This does not qualify document isolation, atomic publication or recovery.
"""

import datetime
import importlib.util
import json
from pathlib import Path
import sys
import traceback

import FreeCAD as App


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SENTINEL = "Selected export rollback FreeCAD validation passed"
PUBLISH_FAULT = "controlled selected publication failure"
RESTORE_FAULT = "controlled selected original restore failure"


def helper(filename):
    path = ROOT / "tests" / filename
    spec = importlib.util.spec_from_file_location(
        "_selected_rollback_" + path.stem, path,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CORE = helper("freecad_validate_core_export_staging.py")
SELECTED = helper("freecad_validate_phase8_turnout_selected_export.py")
HOST = SELECTED._host_proof()


def source_evidence():
    contract = json.loads(SELECTED.CONTRACT.read_text(encoding="utf-8"))
    source = ROOT / contract["fixture"]["path"]
    identities = {
        ROOT / item["path"]: item["sha256"]
        for item in contract["source_state"].values()
    }
    identities[source] = contract["fixture"]["sha256"]
    assert all(CORE.sha256(path) == value
               for path, value in identities.items())
    return source, identities


def prepare_document(module, directory):
    source, _ = source_evidence()
    return SELECTED._prepared_copy(
        module, HOST, source, directory / "selected-rollback.FCStd",
    )


def document_witness(module, document):
    return {
        "snapshot": HOST._snapshot(module, document),
        "objects": {obj.Name: obj for obj in document.Objects},
        "shapes": {
            obj.Name: obj.Shape for obj in document.Objects
            if "Shape" in obj.PropertiesList and not obj.Shape.isNull()
        },
    }


def assert_document(module, document, before):
    HOST._assert_equal(
        before["snapshot"], HOST._snapshot(module, document),
        "Selected export rollback",
    )
    for name, obj in before["objects"].items():
        assert document.getObject(name) is obj, name
    for name, shape in before["shapes"].items():
        assert document.getObject(name).Shape.isSame(shape), name


def reopen_document(module, document):
    document.save()
    saved = HOST._snapshot(module, document)
    path = document.FileName
    App.closeDocument(document.Name)
    document = App.openDocument(path)
    document.UndoMode = 1
    HOST._assert_reopen_equal(saved, HOST._snapshot(module, document))
    return document


def fault_factory(restore_failure, observed):
    from tracktemplate.adapters.export.selected_export_files import (
        SelectedExportFiles,
    )

    class FaultFiles(SelectedExportFiles):
        def __init__(self):
            super().__init__()
            self.replace_calls = 0
            observed.append(self)

        def _replace(self, source, destination, *, source_directory_fd,
                     destination_directory_fd):
            self.replace_calls += 1
            if self.replace_calls == 4:
                raise OSError(PUBLISH_FAULT)
            if restore_failure and self.replace_calls == 5:
                raise OSError(RESTORE_FAULT)
            return super()._replace(
                source, destination,
                source_directory_fd=source_directory_fd,
                destination_directory_fd=destination_directory_fd,
            )

    return FaultFiles


def seed_previous(plan):
    paths = [Path(task["path"]) for task in plan["tasks"]]
    paths.append(Path(plan["manifest_path"]))
    assert len(paths) == 2
    previous = {}
    for index, path in enumerate(paths):
        content = ("previous operator output {}\n".format(index)).encode()
        path.write_bytes(content)
        previous[path] = content
    return previous


def failure_witness(summary, directory, previous, restore_failure):
    assert summary["successful_files"] == 0, summary
    assert summary["failed_files"] == 1, summary
    assert not summary["manifest_path"], summary
    text = "\n".join(summary["failures"] + summary["failure_details"])
    assert PUBLISH_FAULT in text, summary
    retained = [path for path in directory.iterdir() if path.is_dir()]
    if restore_failure:
        assert RESTORE_FAULT in text, summary
        assert "Rollback is incomplete or uncertain" in text, summary
        assert "No destination export file was changed" not in text
        assert len(retained) == 1, retained
        assert str(retained[0].resolve()) in text, summary
        assert retained[0].name.startswith(".railway_selected_export_")
        backups = retained[0] / ".backups"
        assert backups.is_dir() and list(backups.iterdir())
        assert any(not path.exists() for path in previous)
        for content in previous.values():
            matches = [path for path in directory.rglob("*")
                       if path.is_file() and path.read_bytes() == content]
            assert len(matches) == 1, matches
        assert any(path.read_bytes() in previous.values()
                   for path in backups.iterdir() if path.is_file())
    else:
        assert "Original destination files were restored" in text, summary
        assert not retained, retained
        assert all(path.read_bytes() == value
                   for path, value in previous.items())
        assert {path.name for path in directory.iterdir()} == {
            path.name for path in previous
        }
    return {
        "summary": summary,
        "retained_paths": [str(path.resolve()) for path in retained],
        "prior_bytes_preserved": True,
        "files_sha256": {
            str(path.relative_to(directory)): CORE.sha256(path)
            for path in directory.rglob("*") if path.is_file()
        },
    }


def success(module, document, directory, *, legacy=False):
    directory.mkdir()
    config, plan, skipped, issues, outline, solid, _ = (
        SELECTED._selected_plan(module, document, directory)
    )
    assert not module.preflight_blocking_report(issues), issues
    binding = module.run_selected_production_export
    before = document_witness(module, document)
    if legacy:
        module.run_selected_production_export = binding.original_command
    try:
        summary = SELECTED._export(module, document, config, plan, skipped)
    finally:
        module.run_selected_production_export = binding
    assert summary["successful_files"] == 2, summary
    assert summary["failed_files"] == 0, summary
    assert_document(module, document, before)
    hashes, manifest = SELECTED._output_witness(
        module, directory, plan, outline, solid,
    )
    return {"normalised_hashes": hashes, "manifest_binding": manifest}


def validate():
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    directory = ROOT / "tmp/selected-export-rollback/native-runs" / stamp
    directory.mkdir(parents=True, exist_ok=False)
    _, identities = source_evidence()
    sources = CORE.source_hashes()
    for path in (Path(__file__), Path(SELECTED.__file__), Path(HOST.__file__)):
        sources[str(path.relative_to(ROOT))] = CORE.sha256(path)
    receipt = {"status": "RUNNING", "source_sha256": sources}
    document = None
    try:
        module, routing = CORE.load_product(atomic=True)
        receipt.update(profile=CORE.PROFILE, core_routing=routing)
        document = prepare_document(module, directory)
        expected = success(module, document, directory / "legacy", legacy=True)
        actual = success(module, document, directory / "modular")
        repeated = success(module, document, directory / "repeated")
        assert expected == actual == repeated
        receipt["success_equivalence"] = actual
        receipt["cases"] = {}
        for restore_failure in (False, True):
            name = "restore-failure" if restore_failure else "full-rollback"
            output = directory / name
            output.mkdir()
            config, plan, skipped, issues, *_ = SELECTED._selected_plan(
                module, document, output,
            )
            assert not module.preflight_blocking_report(issues), issues
            config["overwrite_existing"] = True
            previous = seed_previous(plan)
            before = document_witness(module, document)
            binding = module.run_selected_production_export
            original_factory = binding.export_files_factory
            observed = []
            binding.export_files_factory = fault_factory(
                restore_failure, observed,
            )
            try:
                summary = SELECTED._export(
                    module, document, config, plan, skipped,
                )
            finally:
                binding.export_files_factory = original_factory
            assert len(observed) == 1 and observed[0].replace_calls == 6
            result = failure_witness(
                summary, output, previous, restore_failure,
            )
            assert_document(module, document, before)
            document = reopen_document(module, document)
            result["editable_state_and_save_reopen_unchanged"] = True
            receipt["cases"][name] = result
        receipt["status"] = "PASS"
    except Exception:
        receipt["status"] = "FAIL"
        receipt["traceback"] = traceback.format_exc()
        raise
    finally:
        if document is not None and document.Name in App.listDocuments():
            App.closeDocument(document.Name)
        receipt["source_fixture_and_oracles_preserved"] = all(
            CORE.sha256(path) == value for path, value in identities.items()
        )
        receipt["remaining_documents"] = sorted(App.listDocuments())
        receipt["source_unchanged"] = all(
            CORE.sha256(ROOT / path) == value
            for path, value in sources.items()
        )
        if (not receipt["source_fixture_and_oracles_preserved"]
                or receipt["remaining_documents"]
                or not receipt["source_unchanged"]):
            receipt["status"] = "FAIL"
        (directory / "result.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("SELECTED_EXPORT_ROLLBACK_EVIDENCE=" + str(directory), flush=True)
    assert receipt["source_fixture_and_oracles_preserved"]
    assert not receipt["remaining_documents"]
    assert receipt["source_unchanged"]
    print(SENTINEL, flush=True)


if __name__ in {"__main__", "freecad_validate_selected_export_rollback"}:
    try:
        validate()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
