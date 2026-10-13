#!/usr/bin/env python3
"""Prove bounded Core inventory, schema compatibility and refusal controls."""

import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import validate_b15 as legacy  # noqa: E402
from tools.validate_dependency_manifest import validate_document  # noqa: E402
from tracktemplate.application import core_dependency_manifest as manifest  # noqa: E402
from tracktemplate.compatibility import core_dependency_inventory as inventory  # noqa: E402


SENTINEL = "Core dependency manifest validation passed"
RUNTIME = {
    "schema_version": 1,
    "python": {"version": "3.13.15", "implementation": "CPython"},
    "freecad": {"available": True, "version_info": [1, 1, 4],
                "opencascade_version": "7.8.1", "qt_binding": "PySide6",
                "qt_version": "6.11.2", "pyside_version": "6.11.2",
                "coin_version": "SIM Coin 4.0.10"},
}


class Object:
    def __init__(self, name, properties):
        self.Name = name
        self.PropertiesList = list(properties)
        self.types = {}
        for key, value in properties.items():
            if isinstance(value, tuple):
                self.types[key], number = value
                value = types.SimpleNamespace(Value=number)
            else:
                self.types[key] = "App::PropertyString"
            setattr(self, key, value)

    def getTypeIdOfProperty(self, name):
        return self.types[name]


class Document:
    def __init__(self, objects):
        self.Objects = objects

    def getObject(self, name):
        return next((obj for obj in self.Objects if obj.Name == name), None)


class Placement:
    def __init__(self, x=0.0):
        self.values = (1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, 0.0,
                       0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)

    def toMatrix(self):
        return types.SimpleNamespace(A=self.values)


class Shape:
    """Model the distinct copied BRep established by the native proof."""

    def __init__(self, content="bound geometry", *, copied=False, null=False):
        self.content = content
        self.copied = copied
        self.null = null
        self._placement = Placement()
        self.explicit_placement = False

    @property
    def Placement(self):
        return self._placement

    @Placement.setter
    def Placement(self, value):
        self._placement = value
        self.explicit_placement = True

    def isNull(self):
        return self.null

    def copy(self):
        result = Shape(self.content, copied=True, null=self.null)
        result._placement = self._placement
        result.explicit_placement = self.explicit_placement
        return result

    def exportBrepToString(self):
        return (self.content + (":copy" if self.copied else ":source")
                + str(self._placement.values) + str(self.explicit_placement))


def fixture(namespace, *, csv=True):
    set_id = "SET-047"
    tags = {"GeneratedBy": namespace["GENERATOR_ID"],
            "TemplateSetID": set_id,
            "GeneratorVersion": namespace["MACRO_VERSION"]}
    config = namespace["default_production_export_config"]()
    config.update(enabled=True, output_directory="/operator/output",
                  create_manifest=csv, overwrite_existing=False)
    settings = {
        **tags, "GeneratedRole": "Settings",
        "TransitionLength": ("App::PropertyLength", 600.0),
        "CurveRadius": ("App::PropertyLength", 600.0),
        "TotalTurnAngle": ("App::PropertyAngle", 90.0),
        "MainTemplateWidth": ("App::PropertyLength", 32.0),
        "OutputBehaviour": namespace["OUTPUT_REPLACE"],
        "TrackConfigurationJSON": json.dumps([
            namespace["default_track_config"](0, 600.0),
        ]),
        "StraightTrackConfigurationsJSON": "[]",
        "PlatformConfigurationsJSON": json.dumps(
            [namespace["default_platform_config"]()]
        ),
        "ProductionExportConfigurationJSON": json.dumps(config),
    }
    for property_name, function in (
        ("FormationConfigurationJSON", "default_formation_config"),
        ("SectionConfigurationJSON", "default_section_config"),
        ("RegistrationConfigurationJSON", "default_registration_config"),
        ("TrackTemplateAssemblyConfigurationJSON",
         "default_template_assembly_config"),
        ("AssemblyLabelConfigurationJSON", "default_assembly_label_config"),
        ("MaterialReportConfigurationJSON", "default_material_report_config"),
    ):
        settings[property_name] = json.dumps(namespace[function]())
    source = Object("DisposableSourceName", {**tags, "GeneratedRole": "Template",
                                            "ProductionRecordID": "pending"})
    source.Shape = Shape()
    record = {
        "template_set_id": set_id,
        "role": "Template", "subtype": "TrackTemplateCompound",
        "category": "Solid", "selection_key": "track_template_compound_3d",
        "route_id": "", "track_number": 0, "platform_number": 0,
        "section_number": 0, "feature_number": 0,
        "source_name": source.Name,
    }
    record["record_id"] = namespace["production_record_identity"](record, set_id)
    source.ProductionRecordID = record["record_id"]
    settings["ProductionRecordIndexJSON"] = json.dumps({
        "schema_version": 2, "template_set_id": set_id, "records": [record],
    })
    owner = Object("DisposableSettingsName", settings)
    doc = Document([owner, source])
    plan = {
        "tasks": [{"format": "step", "path": "/new-uuid/template.step",
                   "records": [dict(record, shape=source.Shape.copy())]}],
        "manifest_path": "/new-uuid/inventory.csv" if csv else "",
        "skipped": [],
    }
    return doc, plan, config, set_id


def prepare(namespace, args):
    return inventory.prepare_core_dependency_manifest(
        *args, namespace=namespace, source_path=legacy.B15_PATH,
        source_sha256=inventory._B15_SHA256,
        runtime_record=lambda: copy.deepcopy(RUNTIME),
    )


def artifacts(csv=True):
    result = [{"path": "template.step", "format": "step",
               "sha256": hashlib.sha256(b"actual step bytes").hexdigest()}]
    if csv:
        result.append({"path": "inventory.csv", "format": "csv",
                       "sha256": hashlib.sha256(b"actual csv bytes").hexdigest()})
    return result


def refuses(action, expected):
    try:
        action()
    except (ValueError, OSError) as error:
        assert expected in str(error), str(error)
    else:
        raise AssertionError("Expected refusal: " + expected)


def validate_success(namespace):
    with mock.patch.object(inventory, "_host_inventory", return_value=(
        RUNTIME, [{"path": "Part:Part.so", "sha256": "a" * 64}],
    )):
        for csv in (True, False):
            args = fixture(namespace, csv=csv)
            with mock.patch.object(
                inventory, "build_core_dependency_manifest",
                wraps=manifest.build_core_dependency_manifest,
            ) as called:
                build = prepare(namespace, args)
                captured = copy.deepcopy(called.call_args.args[0])
            result = build(artifacts(csv))
            assert validate_document(result) == []
            assert validate_document(result, require_project_cleared=True)
            assert result["intended_uses"] == ["private-development"]
            assert result["project_status"]["status"] == "unknown"
            assert result["subject"]["artifacts"] == artifacts(csv)
            assert len(result["dependencies"]) == 10
            by_id = {item["identifier"]: item for item in result["dependencies"]}
            assert any("cached executing" in condition for condition in by_id[
                "tracktemplate:core-generator-source"
            ]["conditions"])
            for name, status, classifications in manifest.LINEAGE:
                assert by_id[name]["classifications"] == list(classifications)
                assert by_id[name]["project_status"]["status"] == status
            source_records = captured["generator_sources"]
            for item in source_records:
                assert item["sha256"] == hashlib.sha256(
                    (ROOT / item["path"]).read_bytes()
                ).hexdigest()
            assert source_records == sorted(source_records, key=lambda x: x["path"])
            canonical = result["subject"]["canonical_model_sha256"]
            assert canonical == manifest.content_digest(captured["canonical_input"])
            assert by_id["tracktemplate:core-canonical-input"]["source"][
                "evidence_sha256"
            ] == canonical
            assert result == build(artifacts(csv))
            # Fresh generation keeps an original task shape while document
            # assignment gives its copied source an explicit root placement.
            fresh = fixture(namespace, csv=csv)
            planned = Shape()
            fresh[1]["tasks"][0]["records"][0]["shape"] = planned
            bound = planned.copy()
            bound.Placement = planned.Placement
            fresh[0].Objects[1].Shape = bound
            original_breps = (planned.exportBrepToString(),
                              bound.exportBrepToString())
            assert original_breps[0] != original_breps[1]
            assert prepare(namespace, fresh)(artifacts(csv)) == result
            assert (planned.exportBrepToString(),
                    bound.exportBrepToString()) == original_breps
            # The closure remains a snapshot even after live input changes.
            args[0].Objects[0].CurveRadius.Value += 10
            assert build(artifacts(csv)) == result
            changed = prepare(namespace, args)(artifacts(csv))
            assert changed["subject"]["canonical_model_sha256"] != canonical
            args = fixture(namespace, csv=csv)
            args[2]["output_directory"] = "/different-parent"
            args[0].Objects[0].Name = "OtherDisposableSettings"
            result2 = prepare(namespace, args)(artifacts(csv))
            assert result2["subject"]["canonical_model_sha256"] == canonical
            rejects = [artifacts(csv)[:-1], artifacts(csv) + artifacts(csv)]
            wrong = artifacts(csv)
            wrong[0]["sha256"] = "invalid"
            rejects.append(wrong)
            wrong = artifacts(csv)
            wrong[0]["path"] = "../template.step"
            rejects.append(wrong)
            for bad in rejects:
                refuses(lambda bad=bad: build(bad), "Core dependency")
            for status in ("unknown", "reference-only", "restricted"):
                substitute = copy.deepcopy(captured)
                substitute["lineage"][1]["status"] = status
                conservative = manifest.build_core_dependency_manifest(
                    substitute, artifacts(csv)
                )
                assert conservative["project_status"]["status"] == "unknown"
                assert validate_document(conservative) == []
                assert validate_document(conservative, True)
            for change in (
                lambda value: value.pop("runtime"),
                lambda value: value["lineage"].pop(),
                lambda value: value["lineage"][0].update(status="project-cleared"),
                lambda value: value["lineage"][0].update(classifications=["engineering_fact"]),
                lambda value: value["generator_sources"][0].update(sha256="bad"),
            ):
                bad = copy.deepcopy(captured)
                change(bad)
                refuses(lambda: manifest.build_core_dependency_manifest(
                    bad, artifacts(csv)
                ), "Core dependency")


def validate_refusals(namespace):
    changes = [
        (lambda args: args[0].Objects.pop(0), "exactly one"),
        (lambda args: args[0].Objects.append(copy.deepcopy(args[0].Objects[0])),
         "exactly one"),
        (lambda args: args[0].Objects[0].PropertiesList.remove("TrackConfigurationJSON"),
         "missing persisted"),
        (lambda args: setattr(args[0].Objects[0], "TrackConfigurationJSON", "[NaN]"),
         "invalid persisted JSON"),
        (lambda args: setattr(args[0].Objects[0], "TrackConfigurationJSON", '[{"x":1,"x":2}]'),
         "duplicate JSON key"),
        (lambda args: setattr(args[0].Objects[0], "TrackConfigurationJSON", "[{}]"),
         "configuration"),
        (lambda args: setattr(args[0].Objects[0].CurveRadius, "Value", float("inf")),
         "finite input"),
        (lambda args: args[1]["tasks"][0]["records"][0].update(subtype="Chair"),
         "unsupported plain-line"),
        (lambda args: args[1]["tasks"][0]["records"][0].update(source_name="foreign"),
         "persisted input binding"),
        (lambda args: setattr(args[0].Objects[1], "ProductionRecordID", "foreign"),
         "source binding"),
        (lambda args: args[1]["tasks"][0]["records"][0].pop("shape"),
         "missing planned"),
        (lambda args: args[1]["tasks"][0]["records"][0].update(shape=None),
         "missing planned"),
        (lambda args: args[1]["tasks"][0]["records"][0].update(shape=Shape(null=True)),
         "null planned"),
        (lambda args: args[1]["tasks"][0]["records"][0].update(shape=Shape("foreign")),
         "planned shape differs"),
        (lambda args: setattr(args[1]["tasks"][0]["records"][0]["shape"],
                              "Placement", Placement(10.0)),
         "planned shape placement differs"),
        (lambda args: args[1]["tasks"][0]["records"][0].update(
            shape=Shape("transformed geometry with unchanged root placement")
        ), "planned shape differs"),
        (lambda args: setattr(args[0].Objects[1], "Shape", None),
         "missing planned"),
        (lambda args: setattr(args[0].Objects[1], "GeneratedRole", "TurnoutRails"),
         "unsupported plain-line"),
        (lambda args: args[2]["formats"].update(step=False),
         "planned format"),
        (lambda args: args[2]["selections"].update(track_template_compound_3d=False),
         "requested selection"),
        (lambda args: args[2].update(create_manifest=False),
         "planned CSV"),
    ]
    with mock.patch.object(inventory, "_host_inventory") as host:
        for mutate, expected in changes:
            args = fixture(namespace)
            mutate(args)
            refuses(lambda: prepare(namespace, args), expected)
        for name in ("FormationConfigurationJSON", "AssemblyLabelConfigurationJSON"):
            args = fixture(namespace)
            config = json.loads(getattr(args[0].Objects[0], name))
            config["enabled"] = True
            setattr(args[0].Objects[0], name, json.dumps(config))
            refuses(lambda: prepare(namespace, args), "unsupported scope")
        host.assert_not_called()
    refuses(lambda: inventory._generator_sources(legacy.B15_PATH, "0" * 64),
            "generator source identity")
    refuses(lambda: inventory._host_inventory({"step"}, None), "provider")
    refuses(lambda: inventory._host_inventory(
        {"step"}, lambda: {"freecad": {"available": False}}
    ), "runtime identity")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "serializer.py"
        path.write_bytes(b"actual serializer source")
        module = types.SimpleNamespace(__file__=str(path))
        with (
            mock.patch.object(inventory.importlib, "import_module",
                              return_value=module),
        ):
            runtime, exporters = inventory._host_inventory(
                {"svg", "step"}, lambda: RUNTIME,
            )
            assert runtime == RUNTIME
            assert {item["path"].split(":")[0] for item in exporters} == {
                "FreeCAD", "Part", "importSVG",
            }
            assert {item["sha256"] for item in exporters} == {
                hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            builtin = types.SimpleNamespace(
                __spec__=types.SimpleNamespace(origin="built-in"),
            )
            with mock.patch.object(
                inventory.importlib, "import_module",
                side_effect=lambda name: builtin if name == "FreeCAD" else module,
            ):
                _, files = inventory._host_inventory({"step"}, lambda: RUNTIME)
                assert files == [{"path": "Part:serializer.py",
                                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}]
                builtin.__spec__.origin = "unidentified"
                refuses(lambda: inventory._host_inventory(
                    {"step"}, lambda: RUNTIME,
                ), "exporter source FreeCAD")
            module.__file__ = ""
            refuses(lambda: inventory._host_inventory(
                {"step"}, lambda: RUNTIME,
            ), "exporter source")


def main():
    for module in (manifest, inventory):
        ast.parse(Path(module.__file__).read_text())
    ast.parse(Path(__file__).read_text())
    register = json.loads((ROOT / manifest.LINEAGE_LOCATOR).read_text())
    entries = {item["entry_id"]: item for scope in register["scopes"]
               for item in scope["entries"]}
    for name, status, classifications in manifest.LINEAGE:
        assert entries[name]["current_project_status"] == status
        assert entries[name]["classifications"] == list(classifications)
    assert "special-trackwork" in entries[
        "legacy.source-informed-geometry-and-data-basis"
    ]["output_effect"]
    namespace, _ = legacy._load_namespace()
    validate_success(namespace)
    validate_refusals(namespace)
    print(SENTINEL)


if __name__ == "__main__":
    main()
