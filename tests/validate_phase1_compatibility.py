#!/usr/bin/env python3
"""Validate the Phase 1 runtime and legacy ingress compatibility contract."""

import ast
import copy
import hashlib
import json
import math
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import runtime_compatibility_probe  # noqa: E402


CONTRACT_PATH = ROOT / "reference" / "contracts" / "phase1-compatibility.json"
EXPECTED_CONTRACT_SHA256 = (
    "7c23fd8371a197b38b77fcc2fdbaca2dd36e852ba00f4e99357e58cd1732624f"
)
SOURCE_PATHS = {
    "b14": ROOT / "AdvancedTurnout.FCMacro",
    "b15": ROOT
    / (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ),
}
SOURCE_HASHES = {
    "b14": "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088",
    "b15": "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}
VERSION_TOKENS = {
    "b14": "10.2A8A7B14",
    "b15": "10.2A8A7B15",
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "contract_id",
    "recorded_on",
    "status",
    "phase",
    "scope",
    "source_state",
    "official_host_metadata",
    "runtime_baseline",
    "legacy_document_window",
    "external_configuration_window",
    "persisted_schema_anchors",
    "enforcement_and_requalification",
    "evidence",
}
EXPECTED_SCHEMA_ANCHORS = {
    "ASSEMBLY_LABEL_SCHEMA_VERSION": 1,
    "CHAIR_ANALYSIS_SCHEMA_VERSION": 5,
    "CHAIR_SOLID_SCHEMA_VERSION": 2,
    "CONFIGURATION_SCHEMA_VERSION": 1,
    "CROSSOVER_B3_SCHEMA_VERSION": 1,
    "CROSSOVER_B4_SCHEMA_VERSION": 1,
    "CROSSOVER_INTEGRATION_SCHEMA_VERSION": 1,
    "CROSSOVER_SCHEMA_VERSION": 1,
    "CROSSOVER_SHARED_TIMBER_SCHEMA_VERSION": 3,
    "CROSSOVER_TIMBER_ANALYSIS_SCHEMA_VERSION": 1,
    "LAST_INPUTS_SCHEMA_VERSION": 3,
    "MATERIAL_REPORT_SCHEMA_VERSION": 1,
    "PLATFORM_DEFAULTS_SCHEMA_VERSION": 3,
    "PRESET_LIBRARY_SCHEMA_VERSION": 1,
    "PRESET_RECORD_SCHEMA_VERSION": 1,
    "PRODUCTION_PREFLIGHT_SCHEMA_VERSION": 1,
    "PRODUCTION_RECORD_SCHEMA_VERSION": 2,
    "PRODUCTION_SCHEDULE_SCHEMA_VERSION": 1,
    "TURNOUT_INTEGRATION_SCHEMA_VERSION": 1,
    "TURNOUT_SCHEMA_VERSION": 1,
}
EXPECTED_SHARED_PROFILE_MATCH = {
    "freecad.coin_version": "SIM Coin 4.0.8",
    "freecad.opencascade_version": "7.8.1",
    "freecad.pyside_version": "6.10.3",
    "freecad.qt_binding": "PySide6",
    "freecad.qt_version": "6.10.3",
    "platform.flatpak_id": "org.freecad.FreeCAD",
    "platform.machine": "x86_64",
    "platform.packaging": "flatpak",
    "platform.system": "Linux",
    "python.implementation": "CPython",
    "python.version_info": [3, 13, 14],
}
EXPECTED_UPDATED_PROFILE_MATCH = {
    "freecad.coin_version": "SIM Coin 4.0.8",
    "freecad.opencascade_version": "7.8.1",
    "freecad.pyside_version": "6.11.1",
    "freecad.qt_binding": "PySide6",
    "freecad.qt_version": "6.11.1",
    "freecad.version_info": [1, 1, 3],
    "platform.flatpak_id": "org.freecad.FreeCAD",
    "platform.machine": "x86_64",
    "platform.packaging": "flatpak",
    "platform.system": "Linux",
    "python.implementation": "CPython",
    "python.version_info": [3, 13, 13],
}
EXPECTED_QUALIFIED_PROFILES = {
    "linux-x86_64-flatpak-freecad-1.1.1": {
        "status": "qualified-reference-and-initial-rc-profile",
        "exact_match": {
            **EXPECTED_SHARED_PROFILE_MATCH,
            "freecad.version_info": [1, 1, 1],
        },
        "observed_freecad_revision": "44874 (Git)",
        "observed_freecad_commit": (
            "0108fd4b4850cc46e625b60e53cea7a7bbe69f8d"
        ),
    },
    "linux-x86_64-flatpak-freecad-1.1.3": {
        "status": "qualified-patch-requalification-profile",
        "exact_match": {
            **EXPECTED_SHARED_PROFILE_MATCH,
            "freecad.version_info": [1, 1, 3],
        },
        "observed_freecad_revision": "44987 (Git)",
        "observed_freecad_commit": (
            "145529fe741292ff0b3977a01195bf0247425794"
        ),
    },
    "linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1": {
        "status": "qualified-additional-exact-host-profile",
        "exact_match": EXPECTED_UPDATED_PROFILE_MATCH,
        "observed_freecad_revision": "44987 (Git)",
        "observed_freecad_commit": (
            "145529fe741292ff0b3977a01195bf0247425794"
        ),
        "observed_flatpak_ref": (
            "app/org.freecad.FreeCAD/x86_64/stable"
        ),
        "observed_flatpak_app_commit": (
            "fa3ef6bebc139083246bd4fb6b8baf6a032a3b5bbb0a57479cb14d52bad733ae"
        ),
        "observed_flatpak_parent_commit": (
            "d7a54c855bce9f4fb7b00b33d43f0ecb1908af510f9147bcc9bc32f614a6bbad"
        ),
        "observed_flatpak_runtime": "org.kde.Platform/x86_64/6.11",
        "observed_flatpak_sdk": "org.kde.Sdk/x86_64/6.11",
        "observed_flatpak_origin": "flathub",
        "observed_flatpak_collection": "org.flathub.Stable",
        "observed_flatpak_installation": "system",
    },
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _functions(tree, names):
    wanted = set(names)
    result = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in wanted
    ]
    observed = [node.name for node in result]
    missing = sorted(wanted - set(observed))
    if missing:
        raise AssertionError("missing functions: {}".format(", ".join(missing)))
    if len(observed) != len(set(observed)):
        raise AssertionError("compatibility helper selection is ambiguous")
    return result


def _function(tree, name):
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    if len(matches) != 1:
        raise AssertionError("expected one top-level {} function".format(name))
    return matches[0]


def _assignment_values(tree, name):
    values = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        if any(
            isinstance(target, ast.Name) and target.id == name
            for target in targets
        ):
            values.append(ast.literal_eval(node.value))
    if not values:
        raise AssertionError("missing assignment {}".format(name))
    return values


def _compile_selected(tree, names, namespace):
    module = ast.Module(body=_functions(tree, names), type_ignores=[])
    exec(compile(module, "<phase1-compatibility>", "exec"), namespace)
    return namespace


def _non_empty_text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_contract(document):
    errors = []
    if not isinstance(document, dict):
        return ["compatibility contract must be an object"]
    if set(document) != TOP_LEVEL_KEYS:
        errors.append("compatibility contract top-level fields are invalid")
    exact_root = {
        "schema_version": 1,
        "contract_id": "tracktemplate:phase1:runtime-and-legacy-compatibility:1",
        "recorded_on": "2026-07-20",
        "status": (
            "phase1-policy-accepted-phase2-development-guard-implemented-"
            "three-exact-freecad-profiles-qualified"
        ),
        "phase": 1,
    }
    for field, expected in exact_root.items():
        if document.get(field) != expected:
            errors.append("compatibility {} is invalid".format(field))

    scope = document.get("scope")
    if not isinstance(scope, dict) or set(scope) != {
        "release_candidate_intent",
        "current_effect",
        "support_meaning",
        "licensing_separation",
        "security_boundary",
    }:
        errors.append("compatibility scope fields are invalid")
    elif not all(_non_empty_text(value) for value in scope.values()):
        errors.append("compatibility scope contains empty policy text")
    else:
        security_boundary = scope["security_boundary"]
        for fragment in (
            "1.1.1 host profile has functional compatibility authority only",
            "no security endorsement",
            "security issues for all releases before 1.1.3",
            "recommends that all users install 1.1.3",
        ):
            if fragment not in security_boundary:
                errors.append(
                    "compatibility security boundary drifted: " + fragment
                )

    source_state = document.get("source_state")
    if not isinstance(source_state, dict) or set(source_state) != set(SOURCE_PATHS):
        errors.append("compatibility source_state must contain B14 and B15")
    else:
        for label, path in SOURCE_PATHS.items():
            record = source_state.get(label)
            if not isinstance(record, dict) or set(record) != {
                "path",
                "version_token",
                "sha256",
                "role",
            }:
                errors.append("{} compatibility source fields are invalid".format(label))
                continue
            if record.get("path") != path.relative_to(ROOT).as_posix():
                errors.append("{} compatibility path is invalid".format(label))
            if record.get("version_token") != VERSION_TOKENS[label]:
                errors.append("{} compatibility version is invalid".format(label))
            if record.get("sha256") != SOURCE_HASHES[label]:
                errors.append("{} compatibility hash is invalid".format(label))
            if not _non_empty_text(record.get("role")):
                errors.append("{} compatibility role is missing".format(label))

    official = document.get("official_host_metadata")
    if not isinstance(official, dict):
        errors.append("official host metadata is missing")
    else:
        if official.get("observed_on") != "2026-07-20":
            errors.append("official host observation date is invalid")
        if official.get("observed_current_stable_release") != "1.1.1":
            errors.append("observed stable FreeCAD release must remain 1.1.1")
        schema = official.get("addon_manifest_schema")
        if not isinstance(schema, dict):
            errors.append("official Addon manifest schema record is missing")
        else:
            if schema.get("branch") != "Stable" or schema.get(
                "observed_tree_sha"
            ) != "90c9b419cdb284130533d472dfdc0b8b03f9176c":
                errors.append("official Addon manifest schema anchor drifted")
            fields = schema.get("fields")
            if not isinstance(fields, dict) or set(fields) != {
                "freecadmin",
                "freecadmax",
                "pythonmin",
            }:
                errors.append("official Addon compatibility fields are incomplete")
        manifest = official.get("initial_package_manifest_intent")
        if not isinstance(manifest, dict) or {
            key: manifest.get(key)
            for key in ("freecadmin", "freecadmax", "pythonmin")
        } != {
            "freecadmin": "1.1.1",
            "freecadmax": "1.1.1",
            "pythonmin": "3.12.0",
        }:
            errors.append("initial Addon manifest compatibility intent drifted")
        elif not _non_empty_text(manifest.get("phase_10_rule")):
            errors.append("initial Addon manifest requires a Phase 10 rule")

    runtime = document.get("runtime_baseline")
    if not isinstance(runtime, dict):
        errors.append("runtime baseline is missing")
    else:
        floor = runtime.get("standalone_development_floor")
        if not isinstance(floor, dict) or floor.get("pythonmin") != "3.12.0" or floor.get(
            "observed_python"
        ) != "3.12.3" or floor.get("implementation") != "CPython":
            errors.append("standalone development Python baseline drifted")
        profiles = runtime.get("qualified_profiles")
        if not isinstance(profiles, list):
            errors.append("qualified profiles must be a list")
        else:
            profile_ids = [
                profile.get("profile_id")
                for profile in profiles
                if isinstance(profile, dict)
            ]
            if profile_ids != list(EXPECTED_QUALIFIED_PROFILES):
                errors.append("exact qualified profile set or order drifted")
            for profile in profiles:
                if not isinstance(profile, dict):
                    errors.append("qualified profile must be an object")
                    continue
                profile_id = profile.get("profile_id")
                expected = EXPECTED_QUALIFIED_PROFILES.get(profile_id)
                if expected is None:
                    errors.append("unexpected qualified profile")
                    continue
                for field, value in expected.items():
                    if profile.get(field) != value:
                        errors.append(
                            "{} {} drifted".format(profile_id, field)
                        )
                basis = profile.get("qualification_basis")
                if not isinstance(basis, list) or not basis or not all(
                    _non_empty_text(item) for item in basis
                ):
                    errors.append(
                        "{} qualification basis is missing".format(profile_id)
                    )
        matrix = runtime.get("platform_matrix")
        observed_matrix = {
            item.get("platform"): item.get("status")
            for item in matrix
            if isinstance(item, dict)
        } if isinstance(matrix, list) else {}
        if observed_matrix != {
            "Linux x86_64 stable org.freecad.FreeCAD Flatpak": "qualified",
            "Other Linux packages or architectures": "qualification-pending",
            "Windows": "qualification-pending",
            "macOS": "qualification-pending",
        }:
            errors.append("runtime platform qualification matrix drifted")
        for field in ("runtime_policy", "support_rule", "unqualified_runtime_rule"):
            if not _non_empty_text(runtime.get(field)):
                errors.append("runtime baseline requires {}".format(field))

    legacy = document.get("legacy_document_window")
    if not isinstance(legacy, dict):
        errors.append("legacy document window is missing")
    else:
        if legacy.get("current_implementation_status") != (
            "contract-only-no-successor-document-detector-or-migrator-exists"
        ):
            errors.append("legacy window must not claim an implemented migrator")
        if legacy.get("generator_id") != (
            "ModelRailwayCurveTemplate.IndependentEasements"
        ):
            errors.append("legacy generator identity drifted")
        if legacy.get("supported_ingress_versions") != [
            VERSION_TOKENS["b14"],
            VERSION_TOKENS["b15"],
        ]:
            errors.append("legacy ingress versions must remain B14 and B15")
        if legacy.get("accepted_version_sets") != [
            [VERSION_TOKENS["b14"]],
            [VERSION_TOKENS["b15"]],
            [VERSION_TOKENS["b14"], VERSION_TOKENS["b15"]],
        ]:
            errors.append("legacy accepted version sets drifted")
        classifications = legacy.get("classification")
        statuses = [
            item.get("status")
            for item in classifications
            if isinstance(item, dict)
        ] if isinstance(classifications, list) else []
        if statuses != [
            "supported-migration-source",
            "inspection-only",
            "blocked-corrupt-or-conflicting",
        ]:
            errors.append("legacy classification must retain all fail-closed states")
        elif not all(
            _non_empty_text(item.get("condition"))
            and _non_empty_text(item.get("write_policy"))
            for item in classifications
        ):
            errors.append("legacy classifications require conditions/write policies")
        invariants = legacy.get("migration_invariants")
        if not isinstance(invariants, list) or len(invariants) != 7 or not all(
            _non_empty_text(item) for item in invariants
        ):
            errors.append("legacy migration invariants are incomplete")
        for field in (
            "mixed_b14_b15_rule",
            "family_evidence_rule",
            "successor_target_status",
        ):
            if not _non_empty_text(legacy.get(field)):
                errors.append("legacy window requires {}".format(field))

    external = document.get("external_configuration_window")
    if not isinstance(external, dict):
        errors.append("external configuration window is missing")
    else:
        last_inputs = external.get("last_dialog_inputs")
        if not isinstance(last_inputs, dict) or last_inputs.get(
            "accepted_schema_versions"
        ) != [1, 2, 3] or last_inputs.get("other_versions") != (
            "reject-and-use-no-payload"
        ):
            errors.append("last-input schema window drifted")
        presets = external.get("named_preset_records")
        if not isinstance(presets, dict) or presets.get("current_schema") != 1 or presets.get(
            "recognised_legacy_aliases"
        ) != [
            "payload -> configuration",
            "schema_version -> preset_schema_version",
        ] or presets.get("other_versions") != "reject-fail-closed":
            errors.append("named-preset record window drifted")
        config_rows = external.get("configuration_json")
        if not isinstance(config_rows, list) or [
            row.get("disposition") for row in config_rows if isinstance(row, dict)
        ] != [
            "validate-and-normalise-current",
            "deterministically-migrate-to-1",
            "recognised-legacy-saved-dialog-shape-migrate-to-1",
            "reject-fail-closed",
        ]:
            errors.append("configuration JSON compatibility matrix drifted")
        library_rows = external.get("named_preset_library")
        if not isinstance(library_rows, list) or [
            row.get("disposition") for row in library_rows if isinstance(row, dict)
        ] != [
            "migrate-in-memory-to-library-object",
            "validate-current",
            "reject-fail-closed",
        ]:
            errors.append("preset-library compatibility matrix drifted")

    if document.get("persisted_schema_anchors") != EXPECTED_SCHEMA_ANCHORS:
        errors.append("persisted schema-anchor map drifted")

    enforcement = document.get("enforcement_and_requalification")
    if not isinstance(enforcement, dict):
        errors.append("compatibility enforcement/requalification record is missing")
    else:
        for phase in ("phase_2", "phase_4", "phase_10"):
            if not _non_empty_text(enforcement.get(phase)):
                errors.append("compatibility enforcement requires {}".format(phase))
        triggers = enforcement.get("requalification_triggers")
        matrix = enforcement.get("required_matrix")
        if not isinstance(triggers, list) or len(triggers) != 5:
            errors.append("compatibility requalification triggers are incomplete")
        if not isinstance(matrix, list) or len(matrix) != 6:
            errors.append("compatibility required matrix is incomplete")

    evidence = document.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("compatibility evidence map is missing")
    else:
        if evidence.get("probe_tool") != "tools/runtime_compatibility_probe.py" or evidence.get(
            "probe_sentinel"
        ) != runtime_compatibility_probe.SENTINEL:
            errors.append("runtime-probe evidence pointer drifted")
        if evidence.get("freecad_probe_command") != (
            "flatpak run --command=FreeCADCmd org.freecad.FreeCAD "
            "tools/runtime_compatibility_probe.py "
            "--pass --require-qualified"
        ):
            errors.append("qualified runtime-probe command drifted")
        for field in (
            "probe_tool",
            "baseline",
            "b15_acceptance",
            "plain_line_save_reopen",
            "straight_station_save_reopen",
            "turnout_save_reopen",
            "phase2_foundation",
            "phase2_freecad_smoke",
        ):
            relative = evidence.get(field)
            if not _non_empty_text(relative) or not (ROOT / relative).is_file():
                errors.append("compatibility evidence path is missing: {}".format(field))
        for field, label in (
            (
                "freecad_1_1_3_requalification",
                "FreeCAD 1.1.3 requalification",
            ),
            (
                "freecad_1_1_3_py31313_qt6111_qualification",
                "FreeCAD 1.1.3 Python 3.13.13 and Qt 6.11.1 qualification",
            ),
        ):
            qualification = evidence.get(field)
            if not _non_empty_text(qualification):
                errors.append(label + " evidence is missing")
                continue
            relative, separator, anchor = qualification.partition("#")
            path = ROOT / relative
            if (
                not separator
                or not path.is_file()
                or 'id="{}"'.format(anchor)
                not in path.read_text(encoding="utf-8")
            ):
                errors.append(label + " evidence link is invalid")
        if evidence.get("runtime_probe_observed_on") != "2026-08-23":
            errors.append("runtime-probe observation date drifted")
        gaps = evidence.get("known_evidence_gaps")
        if not isinstance(gaps, list) or len(gaps) != 5 or not all(
            _non_empty_text(item) for item in gaps
        ):
            errors.append("compatibility evidence gaps are incomplete")
    return errors


def _configuration_migration_namespace(tree):
    names = (
        "_configuration_json_copy",
        "_configuration_diagnostic",
        "_configuration_add_diagnostic",
        "_configuration_string_looks_executable",
        "_configuration_scan_plain_data",
        "_configuration_alias_section",
        "_legacy_last_inputs_to_configuration",
        "migrate_configuration_payload",
    )
    namespace = {
        "json": json,
        "math": math,
        "re": re,
        "CONFIGURATION_SCHEMA_VERSION": 1,
        "CONFIGURATION_SEVERITY_INFORMATION": "Information",
        "CONFIGURATION_SEVERITY_WARNING": "Warning",
        "CONFIGURATION_SEVERITY_ERROR": "Error",
        "OUTPUT_REPLACE": "Replace all existing generated templates",
    }
    for name in (
        "default_platform_config",
        "default_formation_config",
        "default_section_config",
        "default_registration_config",
        "default_template_assembly_config",
        "default_assembly_label_config",
        "default_production_export_config",
        "default_material_report_config",
    ):
        namespace[name] = lambda marker=name: {"stub_default": marker}
    return _compile_selected(tree, names, namespace)


def validate_configuration_migrations(tree):
    errors = []
    namespace = _configuration_migration_namespace(tree)
    migrate = namespace["migrate_configuration_payload"]
    current = {
        "schema_version": 1,
        "macro_version": "fixture",
        "configuration": {"marker": [1, 2, 3]},
        "presets": [],
    }
    migrated, diagnostics = migrate(current)
    if migrated != current or migrated is current or diagnostics:
        errors.append("configuration schema 1 no longer passes as a defensive copy")

    schema_zero, diagnostics = migrate({"schema_version": 0, "configuration": {}})
    if not isinstance(schema_zero, dict) or schema_zero.get("schema_version") != 1:
        errors.append("configuration schema 0 no longer migrates to schema 1")
    if not any(item.get("migration_action") == "Schema 0 -> schema 1" for item in diagnostics):
        errors.append("configuration schema 0 migration diagnostic drifted")

    legacy, diagnostics = migrate(
        {
            "transition": 150.0,
            "radius": 600.0,
            "angle": 90.0,
            "main_width": 40.0,
        }
    )
    curve = ((legacy or {}).get("configuration") or {}).get("curve")
    if curve != {
        "transition": 150.0,
        "radius": 600.0,
        "angle": 90.0,
        "main_width": 40.0,
    } or not any(
        item.get("migration_action") == (
            "Legacy saved inputs -> configuration schema 1"
        )
        for item in diagnostics
    ):
        errors.append("recognised legacy saved-dialog migration drifted")

    invalid_cases = (
        {"schema_version": 2, "configuration": {}},
        {"schema_version": -1, "configuration": {}},
        {"schema_version": "1", "configuration": {}},
        {"schema_version": 1, "configuration": {"unsafe": "eval('x')"}},
    )
    for payload in invalid_cases:
        result, diagnostics = migrate(payload)
        if result is not None or not any(item.get("blocks_import") for item in diagnostics):
            errors.append("invalid/future configuration no longer fails closed")
            break
    return errors


def validate_last_input_window(tree):
    namespace = {
        "LAST_INPUTS_SCHEMA_VERSION": 3,
        "OUTPUT_REPLACE": "Replace all existing generated templates",
        "OUTPUT_CREATE_NEW": "Create a new template set",
        "MAX_PARALLEL_TRACKS": 20,
        "DEFAULT_PARALLEL_TRACKS": [],
        "clone_track_config": lambda value, _transition: dict(value),
        "clone_straight_configs": lambda value: list(value),
        "clone_platform_configs": lambda value: list(value),
        "clone_formation_config": lambda value: dict(value),
        "clone_section_config": lambda value: dict(value),
        "clone_registration_config": lambda value: dict(value),
        "clone_template_assembly_config": lambda value: dict(value),
        "clone_production_export_config": lambda value: dict(value),
    }
    _compile_selected(tree, ("_normalise_last_input_payload",), namespace)
    normalise = namespace["_normalise_last_input_payload"]
    base = {
        "transition": 150.0,
        "radius": 600.0,
        "angle": 90.0,
        "main_width": 40.0,
        "track_configs": [],
        "straight_configs": [],
        "platform_configs": [],
        "formation_config": {},
        "section_config": {},
        "registration_config": {},
        "template_assembly_config": {},
        "production_export_config": {},
    }
    errors = []
    for schema in (1, 2, 3):
        payload = dict(base, schema_version=schema)
        if normalise(payload) is None:
            errors.append("last-input schema {} is no longer accepted".format(schema))
    for schema in (0, 4, "bad"):
        payload = dict(base, schema_version=schema)
        if normalise(payload) is not None:
            errors.append("unsupported last-input schema {!r} no longer rejects".format(schema))
    return errors


class _ParameterGroup:
    def __init__(self, stored):
        self.stored = stored

    def GetString(self, _key, _default):
        return self.stored


class _FakeApp:
    def __init__(self, stored):
        self.stored = stored

    def ParamGet(self, _path):
        return _ParameterGroup(self.stored)


def validate_preset_window(tree):
    namespace = {
        "json": json,
        "LAST_INPUTS_PARAMETER_PATH": "fixture",
        "PRESET_LIBRARY_PARAMETER_KEY": "fixture",
        "PRESET_LIBRARY_SCHEMA_VERSION": 1,
        "CONFIGURATION_SEVERITY_INFORMATION": "Information",
        "_configuration_diagnostic": lambda *args, **kwargs: {
            "severity": args[0] if args else "Information",
            "migration_action": args[5] if len(args) > 5 else "",
        },
        "validate_named_preset_collection": lambda presets: {
            "valid": True,
            "blocked": False,
            "presets": list(presets),
            "diagnostics": [],
        },
    }
    _compile_selected(tree, ("load_named_preset_library",), namespace)
    load = namespace["load_named_preset_library"]
    errors = []
    cases = (
        ([], True, "Loaded 0 saved preset(s)."),
        ({"library_schema_version": 1, "presets": []}, True, "Loaded 0 saved preset(s)."),
        ({"library_schema_version": 2, "presets": []}, False, "Unsupported preset library schema: 2"),
        ({"presets": []}, False, "Unsupported preset library schema: None"),
    )
    for payload, expected_valid, expected_message in cases:
        namespace["App"] = _FakeApp(json.dumps(payload))
        result = load()
        if result.get("valid") is not expected_valid or result.get("message") != expected_message:
            errors.append("preset-library disposition drifted for {!r}".format(payload))
    namespace["App"] = _FakeApp("{")
    if load().get("valid") is not False:
        errors.append("malformed preset library no longer rejects")

    constants = {
        node.value
        for node in ast.walk(_function(tree, "_validate_presets"))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    for alias in (
        "payload -> configuration",
        "schema_version -> preset_schema_version",
    ):
        if alias not in constants:
            errors.append("named-preset legacy alias drifted: {}".format(alias))
    return errors


def _set_path(record, dotted_path, value):
    target = record
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value


def _qualified_record(profile):
    record = {
        "schema_version": 1,
        "freecad": {"available": True},
        "platform": {},
        "python": {},
    }
    for path, value in profile["exact_match"].items():
        _set_path(record, path, copy.deepcopy(value))
    return record


def validate_runtime_evaluator(contract):
    errors = []
    profiles = contract["runtime_baseline"]["qualified_profiles"]
    for profile in profiles:
        record = _qualified_record(profile)
        result = runtime_compatibility_probe.evaluate_runtime(record, contract)
        if result != {
            "status": "qualified",
            "matched_profile_id": profile["profile_id"],
            "mismatches": [],
        }:
            errors.append(
                "exact runtime does not qualify: " + profile["profile_id"]
            )
        for path, value in profile["exact_match"].items():
            changed = copy.deepcopy(record)
            replacement = (
                list(value[:-1]) + [value[-1] + 1]
                if isinstance(value, list)
                else str(value) + "-drift"
            )
            _set_path(changed, path, replacement)
            result = runtime_compatibility_probe.evaluate_runtime(
                changed,
                contract,
            )
            if result.get("status") != "unqualified" or not any(
                message.startswith(path + " ")
                for message in result.get("mismatches", [])
            ):
                errors.append(
                    "runtime drift no longer fails closed for {} {}".format(
                        profile["profile_id"],
                        path,
                    )
                )
    record = _qualified_record(profiles[0])
    absent = copy.deepcopy(record)
    absent["freecad"]["available"] = False
    if runtime_compatibility_probe.evaluate_runtime(absent, contract).get(
        "status"
    ) != "not-freecad-runtime":
        errors.append("standalone Python is incorrectly host-qualified")
    no_profiles = copy.deepcopy(contract)
    no_profiles["runtime_baseline"]["qualified_profiles"] = []
    if runtime_compatibility_probe.evaluate_runtime(record, no_profiles).get(
        "status"
    ) != "contract-has-no-qualified-profile":
        errors.append("empty runtime matrix no longer fails closed")

    observed = runtime_compatibility_probe.runtime_record()
    if observed.get("schema_version") != 1 or set(observed) != {
        "schema_version",
        "python",
        "platform",
        "freecad",
    }:
        errors.append("runtime probe record schema drifted")
    serialised = json.dumps(observed, sort_keys=True)
    if "/home/" in serialised or "\\Users\\" in serialised:
        errors.append("runtime probe exposed a user path")
    return errors


def validate_source_anchors(trees):
    errors = []
    for label, tree in trees.items():
        for name, expected in EXPECTED_SCHEMA_ANCHORS.items():
            if _assignment_values(tree, name)[-1] != expected:
                errors.append("{} {} drifted".format(label, name))
        versions = _assignment_values(tree, "MACRO_VERSION_NUMBER")
        if set(versions) != {VERSION_TOKENS[label]}:
            errors.append("{} macro-version assignments drifted".format(label))
        if _assignment_values(tree, "GENERATOR_ID")[-1] != (
            "ModelRailwayCurveTemplate.IndependentEasements"
        ):
            errors.append("{} generator identity drifted".format(label))
        tag = _function(tree, "tag_generated_object")
        tag_dump = ast.dump(tag, include_attributes=False)
        if "GeneratorVersion" not in tag_dump or "MACRO_VERSION" not in tag_dump:
            errors.append("{} generated-object version tagging drifted".format(label))
    return errors


def validate_fail_closed_mutations(contract):
    errors = []
    mutations = []

    changed = copy.deepcopy(contract)
    changed["legacy_document_window"]["supported_ingress_versions"].insert(
        0, "10.2A8A7B13"
    )
    mutations.append(changed)

    changed = copy.deepcopy(contract)
    changed["runtime_baseline"]["qualified_profiles"][0]["exact_match"][
        "freecad.version_info"
    ] = [1, 2, 0]
    mutations.append(changed)

    changed = copy.deepcopy(contract)
    changed["runtime_baseline"]["qualified_profiles"][1]["exact_match"][
        "freecad.version_info"
    ] = [1, 1, 2]
    mutations.append(changed)

    changed = copy.deepcopy(contract)
    changed["runtime_baseline"]["qualified_profiles"][2]["exact_match"][
        "freecad.qt_version"
    ] = "6.10.3"
    mutations.append(changed)

    changed = copy.deepcopy(contract)
    changed["runtime_baseline"]["platform_matrix"][2]["status"] = "qualified"
    mutations.append(changed)

    changed = copy.deepcopy(contract)
    changed["external_configuration_window"]["last_dialog_inputs"][
        "accepted_schema_versions"
    ].append(4)
    mutations.append(changed)

    changed = copy.deepcopy(contract)
    changed["source_state"]["b14"]["sha256"] = "0" * 64
    mutations.append(changed)

    for index, mutation in enumerate(mutations, 1):
        if not validate_contract(mutation):
            errors.append("compatibility mutation {} did not fail closed".format(index))
    return errors


def main():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    errors = []
    if _sha256(CONTRACT_PATH) != EXPECTED_CONTRACT_SHA256:
        errors.append("Phase 1 compatibility contract fingerprint drifted")
    for label, path in SOURCE_PATHS.items():
        if _sha256(path) != SOURCE_HASHES[label]:
            errors.append("{} source fingerprint drifted".format(label))
    trees = {label: _tree(path) for label, path in SOURCE_PATHS.items()}
    errors.extend(validate_contract(contract))
    errors.extend(validate_source_anchors(trees))
    errors.extend(validate_configuration_migrations(trees["b14"]))
    errors.extend(validate_last_input_window(trees["b14"]))
    errors.extend(validate_preset_window(trees["b14"]))
    errors.extend(validate_runtime_evaluator(contract))
    errors.extend(validate_fail_closed_mutations(contract))

    if errors:
        for error in errors:
            print("ERROR: {}".format(error), file=sys.stderr)
        raise SystemExit(1)
    print("Phase 1 compatibility contract validation passed")


if __name__ == "__main__":
    main()
