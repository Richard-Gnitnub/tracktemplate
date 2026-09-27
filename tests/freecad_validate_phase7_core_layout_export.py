#!/usr/bin/env python3
"""Prove the selected core-layout export route in qualified FreeCAD."""

import datetime
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api  # noqa: E402
from tracktemplate.compatibility import b15_workflow_host  # noqa: E402
from tracktemplate.compatibility import transition_workflow as workflow  # noqa: E402
from tracktemplate import bootstrap  # noqa: E402


SENTINEL = "Phase 7 core-layout export FreeCAD validation passed"
PROFILE = "linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2"


class FixedDateTime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 9, 27, 12, 34, 56, tzinfo=tz)


def document_state(document):
    return {
        "name": document.Name,
        "objects": tuple(
            (item.Name, item.TypeId, tuple(item.State))
            for item in document.Objects
        ),
        "undo": document.UndoCount,
        "redo": document.RedoCount,
    }


def records():
    return (
        {
            "source_name": "CurveTemplate001",
            "source_label": "Curve template",
            "role": "Template",
            "track_number": 1,
        },
        {
            "source_name": "StraightTemplate001",
            "source_label": "Connected straight template",
            "role": "StraightTrackTemplate",
            "track_number": 1,
        },
        {
            "source_name": "PlatformBody001",
            "source_label": "Platform body",
            "role": "PlatformBody",
            "platform_number": 1,
            "platform_name": "Island",
            "platform_height": 15.0,
        },
        {
            "source_name": "TrackCentreline002",
            "source_label": "Parallel track centreline",
            "role": "Centreline",
            "track_number": 2,
        },
    )


def plan(root):
    formats = ("dxf", "svg", "stl", "step")
    return {
        "tasks": [
            {
                "format": format_name,
                "path": str(root / "core-layout.{}".format(format_name)),
                "records": [record],
                "combined": False,
            }
            for format_name, record in zip(formats, records())
        ],
        "skipped": [{
            "format": "dxf",
            "reason": "controlled unsupported record",
            "record": {
                "source_name": "SkippedFormation",
                "role": "StraightFormationOutline",
                "track_number": 2,
            },
        }],
        "manifest_path": str(root / "core-layout-manifest.csv"),
    }


def config(root):
    return {
        "output_directory": str(root),
        "overwrite_existing": False,
    }


def file_snapshot(root):
    return {
        path.name: {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(root.iterdir())
        if path.is_file()
    }


def exporter(*, fail_step):
    def write(_document, task, temporary_path):
        if fail_step and task["format"] == "step":
            raise RuntimeError("controlled STEP export failure")
        pathlib.Path(temporary_path).write_bytes(
            json.dumps(
                {
                    "format": task["format"],
                    "roles": [item["role"] for item in task["records"]],
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )

    return write


def run_route(function, document, root, *, fail_step):
    selected_plan = plan(root)
    result = function(
        document,
        selected_plan,
        config(root),
        "SET-PHASE7",
        {"platform_height": 15.0},
        {"board_thickness": 3.0},
        {"joint_type": "Registration"},
        {"joint_type": "Butt", "hole_diameter": 1.2},
        exporter(fail_step=fail_step),
    )
    return result, file_snapshot(root)


def validate():
    qualification = bootstrap.require_qualified_runtime(
        ROOT / "reference/contracts/phase1-compatibility.json"
    )
    assert qualification["compatibility_evaluation"]["matched_profile_id"] == (
        PROFILE
    )
    contract = bootstrap.load_contract(
        ROOT / "reference/contracts/phase1-transition-pilot.json"
    )
    host = b15_workflow_host.load_b15_workflow_host(ROOT, contract)
    namespace = host.module.__dict__
    native = namespace["run_production_export"]
    assert native.__globals__ is namespace
    assert "run_production_export" in namespace["run_macro"].__code__.co_names

    functions = {
        name: getattr(api, name)
        for name in workflow.PRODUCT_FUNCTION_NAMES
    }
    calculation_session = workflow.ModularTransitionWorkflowSession(
        host, functions,
    )
    session = workflow.ModularCoreLayoutWorkflowSession(
        calculation_session, api.run_core_layout_export,
    )
    assert session.routing_record()["schema_version"] == 16
    export_record = session.core_layout_export_routing_record()
    assert export_record["schema_version"] == 1
    assert export_record["contract_id"] == (
        "tracktemplate:phase7:core-layout-export:1"
    )
    assert export_record["mixed_route"] is False
    selected = namespace["run_production_export"]
    assert type(selected) is workflow._CoreLayoutExportAdapter
    assert selected.calculation is api.run_core_layout_export

    document = App.newDocument("TrackTemplatePhase7CoreLayoutExport")
    before = document_state(document)
    original_datetime = namespace["datetime"].datetime
    namespace["datetime"].datetime = FixedDateTime
    try:
        with tempfile.TemporaryDirectory(
            prefix="tracktemplate-phase7-core-layout-export-",
        ) as temporary:
            root = pathlib.Path(temporary)
            for fail_step in (False, True):
                namespace["run_production_export"] = native
                expected, expected_files = run_route(
                    native, document, root, fail_step=fail_step,
                )
                assert document_state(document) == before
                shutil.rmtree(root)
                root.mkdir()

                namespace["run_production_export"] = selected
                observed, observed_files = run_route(
                    selected, document, root, fail_step=fail_step,
                )
                assert observed == expected
                assert observed_files == expected_files
                assert document_state(document) == before
                assert not any(".tmp" in path.name for path in root.iterdir())
                assert observed["skipped_objects"] == 1
                assert observed["manifest_requested"] is True
                assert bool(observed["manifest_path"]) is True
                if fail_step:
                    assert observed["successful_files"] == 4
                    assert observed["failed_files"] == 1
                    assert len(observed_files) == 4
                    assert any(
                        "controlled STEP export failure" in item
                        for item in observed["failures"]
                    )
                else:
                    assert observed["successful_files"] == 5
                    assert observed["failed_files"] == 0
                    assert len(observed_files) == 5
                shutil.rmtree(root)
                root.mkdir()

        namespace["run_production_export"] = native
        try:
            session.core_layout_export_routing_record()
        except workflow.TransitionWorkflowError as error:
            assert "mixed" in str(error)
        else:
            raise AssertionError("The native export route passed as modular")
        session._bind_core_layout_export()
        assert session.core_layout_export_routing_record() == export_record
    finally:
        namespace["datetime"].datetime = original_datetime
        App.closeDocument(document.Name)
    assert App.ActiveDocument is None
    print(SENTINEL)


if __name__ in {"__main__", "freecad_validate_phase7_core_layout_export"}:
    validate()
