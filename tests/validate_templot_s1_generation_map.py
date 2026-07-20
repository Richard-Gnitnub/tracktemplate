#!/usr/bin/env python3
"""Validate the bounded active-route Templot5 556b S1 generation map."""

import copy
import hashlib
import json
import pathlib
import re
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
MAP_PATH = (
    ROOT
    / "reference"
    / "lineage"
    / "templot5-556b-s1-generation-map.json"
)
ORACLE_PATH = (
    ROOT / "reference" / "oracles" / "templot5-556b-s1-oracle.json"
)
LINEAGE_PATH = (
    ROOT / "reference" / "lineage" / "phase1-s1-core-lineage.json"
)

TOP_LEVEL_KEYS = {
    "schema_version",
    "map_id",
    "recorded_on",
    "status",
    "status_reason",
    "permitted_role",
    "source_state",
    "scope",
    "unit_model",
    "coordinate_frames",
    "value_groups",
    "generation_stages",
    "components",
    "manufacturing_branches",
    "open_findings",
    "acceptance_gate",
}
EXPECTED_ARCHIVE_SHA256 = (
    "2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3"
)
EXPECTED_PROJECT_ENTRY = (
    "T556B_ZIPPED_FOR_UPLOAD/OpenTemplot2024.lpr",
    "ceefe944c2300f5dedea7eb64778d4048f0b1545daa4052cf023aa02d67d5766",
)
EXPECTED_ACTIVE_UNITS = {
    "chairs_unit": (
        "T556B_ZIPPED_FOR_UPLOAD/chairs_unit.pas",
        "0a996ea4ad6fa7556dde43f6af0a1e41463112d3f69c4efce3dd3c29406dc21b",
        "chairs_unit in 'chairs_unit.pas'",
    ),
    "math_unit": (
        "T556B_ZIPPED_FOR_UPLOAD/math_unit.pas",
        "341c6aeeb4d3136d9f85688453dbd4e4163c8543efe6ce9362aba8c505b55a65",
        "math_unit in 'math_unit.pas'",
    ),
    "pad_unit": (
        "T556B_ZIPPED_FOR_UPLOAD/pad_unit.pas",
        "c5c05b9406de434a81946fd68d8179f8f6b27fd004c8fae36977932194887fbb",
        "pad_unit in 'pad_unit.pas'",
    ),
    "dxf_unit": (
        "T556B_ZIPPED_FOR_UPLOAD/dxf_unit.pas",
        "f6bd9cbe8ef63397f4a632535f7160a7e6f82498a334bcde8580c9d0ed5b4f8d",
        "dxf_unit in 'dxf_unit.pas'",
    ),
    "custom_3d_unit": (
        "T556B_ZIPPED_FOR_UPLOAD/custom_3d_unit.pas",
        "04899d1060c8d2946def1d3f660cfea2571c3e41d7e3c4c1915b5c3039668934",
        "custom_3d_unit in 'custom_3d_unit.pas'",
    ),
}
EXPECTED_INACTIVE_ALTERNATES = {
    "T556B_ZIPPED_FOR_UPLOAD/chairs_unit_x.pas": (
        "aff0e0079c4749c1132aac0ff15a742afef3f13080178c2ad66545be7235d92a"
    ),
    "T556B_ZIPPED_FOR_UPLOAD/math_unit_x.pas": (
        "1baad39862ac11e2b10cdba8c8ed3eb3a4eb6909b3149abddb8f561d378a64ee"
    ),
}
EXPECTED_COMPONENTS = (
    "S1-BASE-PLINTH",
    "S1OUTJAW",
    "S1INJAW",
    "S1SEAT",
    "KEY",
)
EXPECTED_VALUE_GROUPS = {
    "s1-plan-footprint-and-fasteners",
    "selected-rail-section-and-derived-faces",
    "common-base-seat-and-key",
    "s1-outer-jaw-sections",
    "s1-inner-jaw-sections",
    "assignment-and-instance-placement",
    "key-placement-policy",
    "manufacturing-and-output-compensation",
}
EXPECTED_FINDINGS = {
    "exact-556b-artifact-oracle",
    "field-level-independent-provenance",
    "prototype-versus-model-adjustment-split",
    "direct-base-face-semantics",
    "placement-handedness-and-datum",
    "stochastic-export-controls",
    "custom-data-is-not-chair-schema",
    "non-s1-heaved-rail-options-nyi",
}
TEMPLOT_CLASSIFICATIONS = {
    "templot_source_expression",
    "templot_reference_data",
    "templot_media_output",
}


def _sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unique_ids(items, key, label, errors):
    if not isinstance(items, list) or not items:
        errors.append("{} must be a non-empty list".format(label))
        return []
    values = [item.get(key) for item in items if isinstance(item, dict)]
    if len(values) != len(items) or any(not value for value in values):
        errors.append("{} entries require {}".format(label, key))
    elif len(values) != len(set(values)):
        errors.append("{} {} values must be unique".format(label, key))
    return values


def validate_map(document):
    """Return fail-closed errors for the tracked active-route map."""
    errors = []
    if not isinstance(document, dict):
        return ["generation map must be an object"]
    if set(document) != TOP_LEVEL_KEYS:
        errors.append("generation-map top-level fields do not match the contract")
    if document.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if document.get("status") != "mapped-with-open-findings":
        errors.append("the Phase 1 map must retain mapped-with-open-findings status")
    if document.get("permitted_role") != "local comparison evidence only":
        errors.append("the map must remain local comparison evidence only")
    if not str(document.get("status_reason", "")).strip():
        errors.append("the map requires a status reason")

    source_state = document.get("source_state")
    if not isinstance(source_state, dict):
        errors.append("source_state must be an object")
        source_state = {}
    archive = source_state.get("archive")
    if not isinstance(archive, dict):
        errors.append("source_state.archive must be an object")
        archive = {}
    if archive.get("sha256") != EXPECTED_ARCHIVE_SHA256:
        errors.append("the exact 556b archive fingerprint changed")
    if archive.get("tracked") is not False:
        errors.append("the 556b archive must remain untracked")
    if archive.get("required_in_clean_checkout") is not False:
        errors.append("the 556b archive cannot be required in a clean checkout")

    entry = source_state.get("project_entry")
    if not isinstance(entry, dict) or (
        entry.get("archive_member"), entry.get("sha256")
    ) != EXPECTED_PROJECT_ENTRY:
        errors.append("the exact Lazarus project entry fingerprint changed")

    active_units = source_state.get("active_units")
    active_ids = _unique_ids(active_units, "unit", "active_units", errors)
    if set(active_ids) != set(EXPECTED_ACTIVE_UNITS):
        errors.append("active_units do not match the compiled 556b route")
    if isinstance(active_units, list):
        for item in active_units:
            if not isinstance(item, dict):
                continue
            expected = EXPECTED_ACTIVE_UNITS.get(item.get("unit"))
            if expected is None:
                continue
            actual = (
                item.get("archive_member"),
                item.get("sha256"),
                item.get("project_marker"),
            )
            if actual != expected:
                errors.append("active unit {} drifted".format(item.get("unit")))
            if not str(item.get("role", "")).strip():
                errors.append("every active unit requires a role")

    alternates = source_state.get("inactive_alternates")
    alternate_paths = _unique_ids(
        alternates, "archive_member", "inactive_alternates", errors
    )
    if set(alternate_paths) != set(EXPECTED_INACTIVE_ALTERNATES):
        errors.append("inactive alternate source set changed")
    if isinstance(alternates, list):
        for item in alternates:
            if not isinstance(item, dict):
                continue
            expected = EXPECTED_INACTIVE_ALTERNATES.get(item.get("archive_member"))
            if expected is not None and item.get("sha256") != expected:
                errors.append("inactive alternate fingerprint changed")
            if item.get("present_in_project_entry") is not False:
                errors.append("an inactive alternate cannot be marked active")
            if "inactive" not in str(item.get("disposition", "")):
                errors.append("inactive alternates require an explicit disposition")

    scope = document.get("scope")
    if not isinstance(scope, dict) or scope.get("chair_code") != 1:
        errors.append("the map must remain bounded to chair code 1")
        scope = {}
    if scope.get("designation") != "S1 plain-line chair":
        errors.append("the mapped designation must remain S1 plain-line chair")
    if not isinstance(scope.get("included"), list) or not scope.get("included"):
        errors.append("scope requires included items")
    if not isinstance(scope.get("excluded"), list) or not scope.get("excluded"):
        errors.append("scope requires excluded items")

    units = document.get("unit_model")
    if not isinstance(units, dict):
        errors.append("unit_model must be an object")
        units = {}
    capture_scale = units.get("selected_capture_scale")
    if not isinstance(capture_scale, dict) or capture_scale != {
        "scale_mm_per_foot": 4.0,
        "inscale_mm_per_inch": 1.0 / 3.0,
        "denominator": 76.2,
    }:
        errors.append("the proposed comparison scale contract changed")
    if units.get("dxf_angles") != "degrees" or not str(
        units.get("stl_angles", "")
    ).startswith("radians"):
        errors.append("DXF/STL angle-unit distinction is missing")

    frames = document.get("coordinate_frames")
    frame_ids = _unique_ids(frames, "frame_id", "coordinate_frames", errors)
    frame_id_set = set(frame_ids)
    if frame_id_set != {
        "component-local-rail-top",
        "chair-on-timber",
        "template-export-placement",
        "output",
    }:
        errors.append("coordinate-frame set changed")
    if isinstance(frames, list):
        for frame in frames:
            if not isinstance(frame, dict):
                continue
            axes = frame.get("axes")
            if not isinstance(axes, dict) or set(axes) != {"x", "y", "z"}:
                errors.append("every coordinate frame requires x/y/z axes")
            if not str(frame.get("origin", "")).strip():
                errors.append("every coordinate frame requires an origin")

    groups = document.get("value_groups")
    group_ids = _unique_ids(groups, "group_id", "value_groups", errors)
    group_id_set = set(group_ids)
    if group_id_set != EXPECTED_VALUE_GROUPS:
        errors.append("value-group set changed")
    active_members = {
        value[0] for value in EXPECTED_ACTIVE_UNITS.values()
    }
    if isinstance(groups, list):
        for group in groups:
            if not isinstance(group, dict):
                continue
            group_id = group.get("group_id")
            if group.get("source_member") not in active_members:
                errors.append("{} does not use an active source member".format(group_id))
            symbols = group.get("source_symbols")
            if (
                not isinstance(symbols, list)
                or not symbols
                or len(symbols) != len(set(symbols))
            ):
                errors.append("{} requires unique source symbols".format(group_id))
            classifications = group.get("classifications")
            if (
                not isinstance(classifications, list)
                or not classifications
                or not set(classifications).issubset(TEMPLOT_CLASSIFICATIONS)
            ):
                errors.append("{} has invalid classifications".format(group_id))
            if group.get("project_status") != "reference-only":
                errors.append("{} must remain reference-only".format(group_id))
            for field in ("source_units", "model_conversion"):
                if not str(group.get(field, "")).strip():
                    errors.append("{} requires {}".format(group_id, field))
            if not isinstance(group.get("affects"), list) or not group.get("affects"):
                errors.append("{} requires output effects".format(group_id))

    stages = document.get("generation_stages")
    stage_ids = _unique_ids(stages, "stage_id", "generation_stages", errors)
    if len(stage_ids) != 9:
        errors.append("the active generation route must contain nine bounded stages")
    if isinstance(stages, list):
        for stage in stages:
            if not isinstance(stage, dict):
                continue
            for field in ("source_member", "transform"):
                if not str(stage.get(field, "")).strip():
                    errors.append("every stage requires {}".format(field))
            for field in ("symbols", "consumes", "produces"):
                if not isinstance(stage.get(field), list) or not stage.get(field):
                    errors.append("every stage requires {}".format(field))

    components = document.get("components")
    component_ids = _unique_ids(components, "component_id", "components", errors)
    if tuple(component_ids) != EXPECTED_COMPONENTS:
        errors.append("component order or identity changed")
    if isinstance(components, list):
        for component in components:
            if not isinstance(component, dict):
                continue
            component_id = component.get("component_id")
            if component.get("project_status") != "reference-only":
                errors.append("{} must remain reference-only".format(component_id))
            if component.get("local_frame_id") not in frame_id_set:
                errors.append("{} references an unknown frame".format(component_id))
            value_ids = component.get("value_group_ids")
            if not isinstance(value_ids, list) or not value_ids:
                errors.append("{} requires value groups".format(component_id))
            elif set(value_ids) - group_id_set:
                errors.append("{} references unknown value groups".format(component_id))
            for field in ("builder", "construction", "output_route"):
                if not str(component.get(field, "")).strip():
                    errors.append("{} requires {}".format(component_id, field))

    branches = document.get("manufacturing_branches")
    branch_ids = _unique_ids(
        branches, "branch_id", "manufacturing_branches", errors
    )
    if len(branch_ids) != 7:
        errors.append("seven manufacturing/output branch groups are required")
    if isinstance(branches, list):
        for branch in branches:
            if not isinstance(branch, dict):
                continue
            if branch.get("project_status") != "reference-only":
                errors.append("manufacturing branches must remain reference-only")
            source_members = branch.get("source_members")
            if (
                not isinstance(source_members, list)
                or not source_members
                or len(source_members) != len(set(source_members))
                or set(source_members) - active_members
            ):
                errors.append(
                    "every manufacturing branch requires unique active source members"
                )
            for field in ("affects", "frozen_oracle_policy"):
                if not str(branch.get(field, "")).strip():
                    errors.append("every manufacturing branch requires {}".format(field))
            if not isinstance(branch.get("controls"), list) or not branch.get("controls"):
                errors.append("every manufacturing branch requires controls")

    findings = document.get("open_findings")
    finding_ids = _unique_ids(findings, "finding_id", "open_findings", errors)
    if set(finding_ids) != EXPECTED_FINDINGS:
        errors.append("open-finding set changed")
    if isinstance(findings, list):
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            if finding.get("status") not in {"open", "bounded-exclusion"}:
                errors.append("findings must remain open or explicitly bounded")
            for field in ("owner_role", "minimum_evidence"):
                if not str(finding.get(field, "")).strip():
                    errors.append("every finding requires {}".format(field))

    gate = document.get("acceptance_gate")
    if not isinstance(gate, dict):
        errors.append("acceptance_gate must be an object")
        gate = {}
    if gate.get("status") != "blocked":
        errors.append("the generation-map acceptance gate must remain blocked")
    if gate.get("canonical_production_input") is not False:
        errors.append("Templot generation evidence cannot be canonical input")
    if gate.get("code_translation_authorised") is not False:
        errors.append("the map cannot authorise source translation")
    if not isinstance(gate.get("required_before_use"), list) or not gate.get(
        "required_before_use"
    ):
        errors.append("the gate requires explicit unblock conditions")
    return errors


def validate_cross_document_contract(document):
    oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
    oracle_members = {
        item["path"]: item["sha256"]
        for item in oracle["source"]["required_members"]
    }
    math_path, math_hash, _marker = EXPECTED_ACTIVE_UNITS["math_unit"]
    assert oracle_members[math_path] == math_hash
    assert "T556B_ZIPPED_FOR_UPLOAD/chairs_unit_x.pas" not in oracle_members

    lineage = json.loads(LINEAGE_PATH.read_text(encoding="utf-8"))
    evidence = {
        item["evidence_id"]: item for item in lineage["upstream_evidence"]
    }
    assert "templot5-556b-chairs-unit-x" not in evidence
    math_evidence = evidence["templot5-556b-math-unit"]
    assert math_evidence["archive_member"] == math_path
    assert math_evidence["sha256"] == math_hash
    assert math_evidence["permitted_role"] == (
        "local active assembly/timber comparison oracle"
    )
    assert set(math_evidence["symbols"]) == {
        "drawtimber",
        "calc_fill_chair_outline",
        "add_jaw",
        "add_seat",
        "add_key",
    }

    gap = next(
        entry
        for scope in lineage["scopes"]
        for entry in scope["entries"]
        if entry["entry_id"] == "s1.current-representation-gap"
    )
    assert set(gap["upstream_evidence_ids"]) == {
        "templot5-556b-math-unit",
        "templot5-556b-dxf-unit",
    }

    map_archive = document["source_state"]["archive"]
    assert map_archive["sha256"] == oracle["source"]["archive"]["sha256"]
    assert map_archive["sha256"] == lineage["source_state"]["templot5_archive"][
        "sha256"
    ]


def validate_optional_source_archive(document):
    archive_record = document["source_state"]["archive"]
    archive_path = ROOT / archive_record["path"]
    if not archive_path.is_file():
        return
    assert _sha256_path(archive_path) == EXPECTED_ARCHIVE_SHA256

    with zipfile.ZipFile(archive_path) as archive:
        project_path, project_hash = EXPECTED_PROJECT_ENTRY
        project_payload = archive.read(project_path)
        assert _sha256_bytes(project_payload) == project_hash
        project_source = project_payload.decode("utf-8-sig", errors="replace")

        source_text = {}
        for unit, (path, digest, marker) in EXPECTED_ACTIVE_UNITS.items():
            payload = archive.read(path)
            assert _sha256_bytes(payload) == digest, unit
            source_text[path] = payload.decode("utf-8-sig", errors="replace")
            assert marker in project_source, unit
        for path, digest in EXPECTED_INACTIVE_ALTERNATES.items():
            payload = archive.read(path)
            assert _sha256_bytes(payload) == digest, path
            assert pathlib.PurePosixPath(path).name not in project_source

        for group in document["value_groups"]:
            text = source_text[group["source_member"]]
            for symbol in group["source_symbols"]:
                assert symbol in text, (group["group_id"], symbol)

        stage_source = {
            EXPECTED_PROJECT_ENTRY[0]: project_source,
            **source_text,
        }
        for stage in document["generation_stages"]:
            text = stage_source[stage["source_member"]]
            for symbol in stage["symbols"]:
                assert symbol in text, (stage["stage_id"], symbol)

        math_source = source_text[EXPECTED_ACTIVE_UNITS["math_unit"][0]]
        dxf_source = source_text[EXPECTED_ACTIVE_UNITS["dxf_unit"][0]]
        active_s1_assembly = re.compile(
            r"add_jaw\('S1OUTJAW',\s*False,\s*bbin\);"
            r"\s*add_jaw\('S1INJAW',\s*True,\s*bbin\);"
            r"\s*add_seat\('S1SEAT',\s*bbin,\s*0\);"
            r"\s*add_key\('KEY',\s*bbin,\s*0,\s*0\);"
        )
        assert active_s1_assembly.search(math_source)
        for marker in (
            "procedure create_s1_outer_jaw_block",
            "procedure create_S1_SC_L1_CC_inner_jaw_block",
            "procedure create_S1_S1J_L1_CC_seat_block",
            "procedure create_3d_key_block",
            "procedure insert_stl_block",
            "function make_dim",
            "function make_stl_dim",
        ):
            assert marker in dxf_source, marker


def validate_fail_closed_contract(document):
    changed = copy.deepcopy(document)
    changed["source_state"]["inactive_alternates"][0][
        "present_in_project_entry"
    ] = True
    assert any("cannot be marked active" in error for error in validate_map(changed))

    changed = copy.deepcopy(document)
    changed["value_groups"][0]["project_status"] = "project-cleared"
    assert any("must remain reference-only" in error for error in validate_map(changed))

    changed = copy.deepcopy(document)
    changed["scope"]["chair_code"] = 7
    assert any("chair code 1" in error for error in validate_map(changed))

    changed = copy.deepcopy(document)
    changed["acceptance_gate"]["canonical_production_input"] = True
    assert any("cannot be canonical input" in error for error in validate_map(changed))


def validate():
    document = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    errors = validate_map(document)
    assert errors == [], errors
    validate_cross_document_contract(document)
    validate_optional_source_archive(document)
    validate_fail_closed_contract(document)
    print("Phase 1 Templot5 556b active S1 generation-map validation passed")


if __name__ == "__main__":
    validate()
