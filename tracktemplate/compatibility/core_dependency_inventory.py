"""Read the bounded Core dependency inventory without changing a document.

The frozen host still owns its persisted input fields. This adapter refuses
missing or unsupported inventory before file preparation. It does not infer
canonical state from geometry or silently use the host's default readers.
"""

import copy
import hashlib
import importlib
import json
import math
from pathlib import Path

from tracktemplate import DEVELOPMENT_CHECKPOINT
from tracktemplate.application.core_dependency_manifest import (
    CORE_DEPENDENCY_SCOPE,
    LINEAGE,
    build_core_dependency_manifest,
    canonical_json,
)


_B15_NAME = (
    "model_railway_curve_template_multitrack_v10_2a8a7b15_"
    "chair_performance_and_representation.FCMacro"
)
_B15_SHA256 = (
    "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848"
)
_JSON_INPUTS = (
    ("tracks", "TrackConfigurationJSON"),
    ("straight_routes", "StraightTrackConfigurationsJSON"),
    ("platforms", "PlatformConfigurationsJSON"),
    ("formation_board", "FormationConfigurationJSON"),
    ("sectioning", "SectionConfigurationJSON"),
    ("registration", "RegistrationConfigurationJSON"),
    ("template_joints", "TrackTemplateAssemblyConfigurationJSON"),
    ("assembly_labels", "AssemblyLabelConfigurationJSON"),
    ("production_export", "ProductionExportConfigurationJSON"),
    ("material_report", "MaterialReportConfigurationJSON"),
)
_SCALARS = (
    ("transition", "TransitionLength", "App::PropertyLength"),
    ("radius", "CurveRadius", "App::PropertyLength"),
    ("angle", "TotalTurnAngle", "App::PropertyAngle"),
    ("main_width", "MainTemplateWidth", "App::PropertyLength"),
)
_ROLES = (
    "Group", "Settings", "Template", "Centreline", "ProductionSource",
    "ProductionSourceGroup", "ProductionSchedule", "MaterialLengthReport",
)
_RECORD_TYPES = (
    (("Template", "TrackTemplateCompound", "CuttingProfile"),
     "track_template_compound_2d"),
    (("Template", "TrackTemplateCompound", "Solid"),
     "track_template_compound_3d"),
    (("Centreline", "TrackCentreline", "Engraving"), "track_centrelines"),
)
_RECORD_KEYS = (
    "record_id", "role", "subtype", "category", "selection_key",
    "route_id", "track_number", "platform_number", "section_number",
    "feature_number", "source_name",
)
_EXPORTERS = (("dxf", "importDXF"), ("svg", "importSVG"),
              ("stl", "Mesh"), ("step", "Part"))


def _reject(reason):
    raise ValueError("Core dependency inventory refused: " + reason)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _reject("duplicate JSON key " + key)
        result[key] = value
    return result


def _constant(value):
    _reject("non-finite JSON value " + value)


def _json(value):
    if not isinstance(value, str) or not value:
        _reject("missing persisted JSON")
    try:
        result = json.loads(value, object_pairs_hook=_pairs,
                            parse_constant=_constant)
        canonical_json(result)
        return result
    except (TypeError, ValueError, RecursionError) as error:
        _reject("invalid persisted JSON: " + str(error))


def _property(obj, name, expected_type):
    if name not in obj.PropertiesList:
        _reject("missing persisted property " + name)
    if obj.getTypeIdOfProperty(name) != expected_type:
        _reject("wrong persisted property type for " + name)
    return getattr(obj, name)


def _text(obj, name):
    value = _property(obj, name, "App::PropertyString")
    if not isinstance(value, str) or not value:
        _reject("empty persisted identity " + name)
    return value


def _settings(doc, set_id, namespace):
    if not isinstance(set_id, str) or not set_id:
        _reject("missing template set identity")
    members = [obj for obj in doc.Objects
               if getattr(obj, "TemplateSetID", None) == set_id]
    owners = [obj for obj in members
              if getattr(obj, "GeneratedRole", None) == "Settings"]
    if len(owners) != 1:
        _reject("expected exactly one same-set Settings object")
    for obj in members:
        if (_text(obj, "GeneratedBy") != namespace["GENERATOR_ID"]
                or _text(obj, "GeneratedRole") not in _ROLES):
            _reject("unsupported plain-line object or source family")
        for name in ("TurnoutHostIntegrationJSON",
                     "CrossoverHostIntegrationJSON"):
            if name in obj.PropertiesList and getattr(obj, name):
                _reject("integrated special-trackwork source")
    return owners[0]


def _configuration(settings, config, namespace):
    raw = {}
    for section, name in _JSON_INPUTS:
        raw[section] = _json(_property(settings, name, "App::PropertyString"))
    curve = {}
    for name, property_name, property_type in _SCALARS:
        value = _property(settings, property_name, property_type).Value
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value)):
            _reject("invalid finite input " + property_name)
        curve[name] = float(value)
    raw["curve"] = curve
    raw["production_utilities"] = {
        "output_mode": _text(settings, "OutputBehaviour"),
    }
    # Validate both the persisted intent and this invocation. Never use the
    # read_* helpers: their fallback defaults would conceal missing evidence.
    validator = namespace["validate_configuration_payload"]
    for selected in (raw, dict(raw, production_export=dict(config))):
        checked = validator({
            "schema_version": 1,
            "macro_version": namespace["MACRO_VERSION_NUMBER"],
            "configuration": copy.deepcopy(selected), "presets": [],
        })
        if (not checked.get("valid") or checked.get("diagnostics")):
            _reject("incomplete or unsupported configuration: "
                    + canonical_json(checked.get("diagnostics", [])))
    if (not isinstance(raw["tracks"], list)
            or not isinstance(raw["straight_routes"], list)
            or not isinstance(raw["platforms"], list)):
        _reject("invalid ordered canonical records")
    if any(item.get("enabled") is not False
           for item in raw["straight_routes"] + raw["platforms"]):
        _reject("unsupported scope: straight routes or platforms enabled")
    for name in ("formation_board", "sectioning", "template_joints",
                 "assembly_labels"):
        if raw[name].get("enabled") is not False:
            _reject("unsupported scope: " + name + " enabled")
    # Disabled manager IDs and export locations do not describe this model.
    model = copy.deepcopy(raw)
    for name in ("straight_routes", "platforms"):
        for item in model[name]:
            item.pop("manager_id", None)
            item.pop("stl_directory", None)
    for name in ("production_export", "material_report",
                 "production_utilities"):
        model.pop(name)
    intent = copy.deepcopy(dict(config))
    for name in ("output_directory", "open_output_directory",
                 "overwrite_existing"):
        intent.pop(name, None)
    return model, intent


def _record_identity(record):
    if not isinstance(record, dict):
        _reject("malformed production record")
    if any(name not in record for name in _RECORD_KEYS):
        _reject("incomplete production record identity")
    key = tuple(record[name] for name in ("role", "subtype", "category"))
    record_types = dict(_RECORD_TYPES)
    if (key not in record_types
            or record["selection_key"] != record_types[key]
            # The inherited empty route identifier denotes the main curve;
            # production_record_identity writes its CURVE identity token.
            or record["route_id"] != ""
            or any(record[name] != 0 for name in
                   ("platform_number", "section_number", "feature_number"))
            or record.get("assembly_label_derived", False)):
        _reject("unsupported plain-line production record")
    for name in ("record_id", "source_name"):
        if not isinstance(record[name], str) or not record[name]:
            _reject("missing production identity " + name)
    return {name: record[name] for name in _RECORD_KEYS}


def _bound_shape(record, source):
    """Check the inherited copied shape, without asserting regeneration."""
    shape = record.get("shape")
    source_shape = getattr(source, "Shape", None)
    if shape is None or source_shape is None:
        _reject("missing planned or bound source shape")
    try:
        null = shape.isNull() or source_shape.isNull()
    except Exception as error:
        _reject("unreadable planned or bound source shape: " + str(error))
    if null:
        _reject("null planned or bound source shape")
    try:
        placement = tuple(shape.Placement.toMatrix().A)
        source_placement = tuple(source_shape.Placement.toMatrix().A)
    except Exception as error:
        _reject("cannot read planned and bound source placement: " + str(error))
    if placement != source_placement:
        _reject("planned shape placement differs from current bound source")
    try:
        snapshots = []
        for original in (shape, source_shape):
            # Document assignment adds an explicit root location. Reapply
            # each unchanged placement only to a temporary copy, then copy
            # symmetrically. Child placements and geometry stay intact.
            candidate = original.copy()
            candidate.Placement = original.Placement
            snapshots.append(candidate.copy().exportBrepToString())
        actual, expected = snapshots
    except Exception as error:
        _reject("cannot compare planned and bound source shape: " + str(error))
    if not isinstance(expected, str) or not expected or actual != expected:
        _reject("planned shape differs from current bound source copy")


def _planned_artifacts(doc, settings, plan, config, model, set_id, namespace):
    index = _json(_property(settings, "ProductionRecordIndexJSON",
                            "App::PropertyString"))
    if (not isinstance(index, dict) or index.get("schema_version") != 2
            or index.get("template_set_id") != set_id
            or not isinstance(index.get("records"), list)):
        _reject("missing or unsupported production index")
    indexed = {}
    for record in index["records"]:
        identity = _record_identity(record)
        track = identity["track_number"]
        if (type(track) is not int
                or (identity["role"] == "Template" and track != 0)
                or (identity["role"] == "Centreline"
                    and not 1 <= track <= 1 + len(model["tracks"]))):
            _reject("record track identity differs from canonical inputs")
        if (record.get("template_set_id") != set_id
                or identity["record_id"] in indexed
                or identity["record_id"] != namespace[
                    "production_record_identity"
                ](record, set_id)):
            _reject("duplicate or mismatched production identity")
        indexed[identity["record_id"]] = identity
    if not indexed or not isinstance(plan.get("tasks"), list):
        _reject("empty production inventory")
    expected = []
    for task in plan["tasks"]:
        if (task.get("format") not in dict(_EXPORTERS)
                or not task.get("records")):
            _reject("unsupported or empty export task")
        if config["formats"].get(task["format"]) is not True:
            _reject("planned format differs from requested production intent")
        for record in task["records"]:
            identity = _record_identity(record)
            if indexed.get(identity["record_id"]) != identity:
                _reject("planned record differs from persisted input binding")
            if config["selections"].get(identity["selection_key"]) is not True:
                _reject("planned record differs from requested selection")
            solid = identity["category"] == "Solid"
            if solid != (task["format"] in {"stl", "step"}):
                _reject("planned format is inconsistent with record category")
            source = doc.getObject(identity["source_name"])
            if (source is None or getattr(source, "TemplateSetID", None)
                    != set_id or getattr(source, "GeneratedBy", None)
                    != namespace["GENERATOR_ID"]
                    or getattr(source, "ProductionRecordID", None)
                    != identity["record_id"]):
                _reject("missing or replaced generated source binding")
            _bound_shape(record, source)
        expected.append({"path": Path(task["path"]).name,
                         "format": task["format"]})
    if bool(plan.get("manifest_path")) != config["create_manifest"]:
        _reject("planned CSV differs from requested production intent")
    if plan.get("manifest_path"):
        expected.append({"path": Path(plan["manifest_path"]).name,
                         "format": "csv"})
    if not expected or len({item["path"] for item in expected}) != len(expected):
        _reject("missing or duplicate planned artifact identity")
    return expected


def _file_digest(path):
    if path.is_symlink() or not path.is_file():
        _reject("missing or indirect installed source " + str(path))
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _generator_sources(source_path, source_sha256):
    package = Path(__file__).resolve().parents[1]
    root = package.parent
    source = Path(source_path)
    if (source.name != _B15_NAME or source.resolve().parent != root
            or source_sha256 != _B15_SHA256
            or _file_digest(source) != source_sha256):
        _reject("inherited generator source identity differs")
    paths = [root / "TrackTemplate.FCMacro", source,
             *sorted(package.rglob("*.py"))]
    return [{"path": str(path.relative_to(root)),
             "sha256": _file_digest(path)}
            for path in sorted(paths)]


def _host_inventory(formats, runtime_record):
    if not callable(runtime_record):
        _reject("actual runtime inventory provider is unavailable")
    runtime = runtime_record()
    host = runtime.get("freecad", {})
    if (host.get("available") is not True or not host.get("version_info")
            or any(host.get(key) in (None, "", "unknown", "unavailable")
                   for key in ("opencascade_version", "qt_binding",
                               "qt_version", "pyside_version", "coin_version"))):
        _reject("incomplete actual FreeCAD runtime identity")
    names = {"FreeCAD", "Part"} | {dict(_EXPORTERS)[key] for key in formats}
    exporters = []
    for name in sorted(names):
        module = importlib.import_module(name)
        path = getattr(module, "__file__", None)
        if (name == "FreeCAD" and path is None
                and getattr(getattr(module, "__spec__", None), "origin", None)
                == "built-in"):
            # The qualified embedded host has no Python module file. Its
            # actual version/revision is in runtime, not a fabricated hash.
            continue
        if not isinstance(path, str) or not path:
            _reject("missing actual exporter source " + name)
        exporters.append({"path": name + ":" + Path(path).name,
                          "sha256": _file_digest(Path(path))})
    return runtime, exporters


def prepare_core_dependency_manifest(doc, plan, config, set_id, *, namespace,
                                     source_path, source_sha256,
                                     runtime_record=None):
    """Snapshot a supported same-set inventory and return its pure builder.

    Refusal preserves the already committed generated document. Persisted
    settings identify inputs; record/source checks establish binding, not an
    independent proof that arbitrary modified BReps match those inputs.
    """
    settings = _settings(doc, set_id, namespace)
    model, intent = _configuration(settings, config, namespace)
    expected = _planned_artifacts(
        doc, settings, plan, config, model, set_id, namespace,
    )
    sources = _generator_sources(source_path, source_sha256)
    runtime, exporters = _host_inventory(
        {item["format"] for item in expected if item["format"] != "csv"},
        runtime_record,
    )
    inventory = {
        "canonical_input": {
            "scope": CORE_DEPENDENCY_SCOPE, "template_set_id": set_id,
            "length_unit": "mm", "angle_unit": "degree",
            "frame": "FreeCAD global XY; positive Z is template thickness",
            "configuration": model, "production_intent": intent,
            "production_admission_enabled": False,
        },
        "generator_version": DEVELOPMENT_CHECKPOINT,
        "generator_sources": sources, "runtime": runtime,
        "exporters": exporters,
        "lineage": [
            {"identifier": name, "status": status,
             "classifications": list(classifications)}
            for name, status, classifications in LINEAGE
        ],
        "expected_artifacts": expected,
        "source_origin": (
            "Persisted generation origin: " + _text(settings, "GeneratorVersion")
            + ". The current B16 export uses the inherited B15 workflow. "
            "A copied legacy document does not prove regeneration by B16."
        ),
    }
    # Validate complete inventory and artifact membership before staging. The
    # zero hashes are syntax-only placeholders, never emitted as real output.
    build_core_dependency_manifest(inventory, [dict(item, sha256="0" * 64)
                                              for item in expected])

    def build(artifacts):
        return build_core_dependency_manifest(inventory, artifacts)

    return build
