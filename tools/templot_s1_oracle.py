#!/usr/bin/env python3
"""Validate the local-only Templot5 556b S1 comparison-oracle contract.

The raw Templot executable, fixture and generated DXF/STL files are deliberately
not repository assets.  This standard-library tool fingerprints the exact
source evidence, rejects a non-556b executable candidate, and produces a small
semantic summary of a future local capture without importing FreeCAD.
"""

import argparse
import hashlib
import json
import math
import pathlib
import re
import sys
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_SPEC_PATH = (
    ROOT / "reference" / "oracles" / "templot5-556b-s1-oracle.json"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VERSION_RE = re.compile(rb"(?<![0-9])([0-9]+\.[0-9]{2}\.[A-Za-z])(?![A-Za-z0-9])")


class OracleValidationError(ValueError):
    """Raised when source evidence or a proposed capture fails closed."""


def _sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_keys(value, expected, path, errors):
    if not isinstance(value, dict):
        errors.append("{} must be an object".format(path))
        return {}
    missing = sorted(set(expected) - set(value))
    extra = sorted(set(value) - set(expected))
    if missing:
        errors.append("{} is missing: {}".format(path, ", ".join(missing)))
    if extra:
        errors.append(
            "{} has unsupported fields: {}".format(path, ", ".join(extra))
        )
    return value


def _valid_sha256(value):
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def validate_spec(document):
    """Return fail-closed errors for the current Phase 1 oracle specification."""
    errors = []
    root = _require_keys(
        document,
        {
            "schema_version",
            "oracle_id",
            "recorded_on",
            "status",
            "status_reason",
            "permitted_role",
            "source",
            "capture_recipe",
            "semantic_contract",
            "blockers",
            "acceptance_gate",
        },
        "oracle",
        errors,
    )
    if root.get("schema_version") != 1:
        errors.append("oracle.schema_version must be 1")
    if root.get("status") != "blocked":
        errors.append("the current Phase 1 oracle specification must remain blocked")
    for key in ("oracle_id", "recorded_on", "status_reason", "permitted_role"):
        if not isinstance(root.get(key), str) or not root.get(key, "").strip():
            errors.append("oracle.{} must be a non-empty string".format(key))
    if root.get("permitted_role") != "local comparison oracle only":
        errors.append("oracle.permitted_role must remain local comparison oracle only")

    source = _require_keys(
        root.get("source"),
        {
            "product",
            "required_revision",
            "accepted_executable_markers",
            "archive",
            "required_members",
            "build_probe",
            "observed_candidate",
        },
        "oracle.source",
        errors,
    )
    if source.get("product") != "Templot5":
        errors.append("oracle.source.product must be Templot5")
    if source.get("required_revision") != "556b":
        errors.append("oracle.source.required_revision must be 556b")
    markers = source.get("accepted_executable_markers")
    if (
        not isinstance(markers, list)
        or not markers
        or any(not isinstance(item, str) or not item.strip() for item in markers)
        or len(set(markers)) != len(markers)
    ):
        errors.append("accepted_executable_markers must be unique non-empty strings")

    archive = _require_keys(
        source.get("archive"),
        {"path", "sha256", "tracked", "required_in_clean_checkout"},
        "oracle.source.archive",
        errors,
    )
    if not isinstance(archive.get("path"), str) or not archive.get("path", "").strip():
        errors.append("oracle.source.archive.path must be a non-empty string")
    if not _valid_sha256(archive.get("sha256")):
        errors.append("oracle.source.archive.sha256 must be a lowercase SHA-256")
    if archive.get("tracked") is not False:
        errors.append("the Templot source archive must remain untracked")
    if archive.get("required_in_clean_checkout") is not False:
        errors.append("a clean checkout must not require the local source archive")

    members = source.get("required_members")
    if not isinstance(members, list) or not members:
        errors.append("oracle.source.required_members must be a non-empty list")
        members = []
    member_paths = []
    for index, item in enumerate(members):
        item = _require_keys(
            item,
            {"path", "sha256", "role"},
            "oracle.source.required_members[{}]".format(index),
            errors,
        )
        member_paths.append(item.get("path"))
        if not isinstance(item.get("path"), str) or not item.get("path", "").strip():
            errors.append("every required source member needs a path")
        if not _valid_sha256(item.get("sha256")):
            errors.append("every required source member needs a SHA-256")
        if not isinstance(item.get("role"), str) or not item.get("role", "").strip():
            errors.append("every required source member needs a role")
    if len(member_paths) != len(set(member_paths)):
        errors.append("required source member paths must be unique")

    build_probe = _require_keys(
        source.get("build_probe"),
        {
            "environment",
            "command",
            "result",
            "first_fatal_error",
            "archive_missing_inputs",
            "disposition",
        },
        "oracle.source.build_probe",
        errors,
    )
    if build_probe.get("result") != "blocked":
        errors.append("the exact 556b build probe must remain blocked")
    missing_inputs = build_probe.get("archive_missing_inputs")
    if (
        not isinstance(missing_inputs, list)
        or not missing_inputs
        or any(not isinstance(item, str) or not item.strip() for item in missing_inputs)
    ):
        errors.append("build_probe.archive_missing_inputs must name the gaps")

    candidate = _require_keys(
        source.get("observed_candidate"),
        {
            "observed_on",
            "location_description",
            "sha256",
            "detected_version",
            "disposition",
        },
        "oracle.source.observed_candidate",
        errors,
    )
    if not _valid_sha256(candidate.get("sha256")):
        errors.append("observed_candidate.sha256 must be a lowercase SHA-256")
    if candidate.get("detected_version") == source.get("required_revision"):
        errors.append("the rejected candidate cannot claim the required revision")
    if candidate.get("disposition") != "rejected-version-mismatch":
        errors.append("the observed executable must remain rejected for version mismatch")

    recipe = _require_keys(
        root.get("capture_recipe"),
        {
            "raw_output_root",
            "raw_artifacts_tracked",
            "isolated_profile_required",
            "existing_user_profile_allowed",
            "fixture",
            "settings",
            "required_artifacts",
            "required_capture_record_fields",
        },
        "oracle.capture_recipe",
        errors,
    )
    raw_root = recipe.get("raw_output_root")
    if not isinstance(raw_root, str) or not raw_root.startswith("benchmark-output/"):
        errors.append("raw_output_root must be below ignored benchmark-output/")
    if recipe.get("raw_artifacts_tracked") is not False:
        errors.append("Templot raw capture artifacts must remain untracked")
    if recipe.get("isolated_profile_required") is not True:
        errors.append("the capture must require an isolated profile")
    if recipe.get("existing_user_profile_allowed") is not False:
        errors.append("the capture must reject an existing everyday user profile")
    fixture = recipe.get("fixture")
    if not isinstance(fixture, dict) or fixture.get("status") != "missing":
        errors.append("the exact frozen S1 fixture must remain visibly missing")
    settings = recipe.get("settings")
    if not isinstance(settings, dict) or not settings:
        errors.append("the capture recipe must contain explicit settings")
    artifacts = recipe.get("required_artifacts")
    if artifacts != ["3d-dxf", "ascii-stl"]:
        errors.append("the capture must require 3d-dxf and ascii-stl in order")
    record_fields = recipe.get("required_capture_record_fields")
    if (
        not isinstance(record_fields, list)
        or not record_fields
        or len(record_fields) != len(set(record_fields))
    ):
        errors.append("required_capture_record_fields must be a unique non-empty list")

    contract = _require_keys(
        root.get("semantic_contract"),
        {"dxf", "stl", "comparison_limits"},
        "oracle.semantic_contract",
        errors,
    )
    dxf = _require_keys(
        contract.get("dxf"),
        {
            "required_block_names",
            "required_insert_names",
            "minimum_faces_per_required_block",
            "minimum_direct_entity_faces",
            "require_equal_nonzero_insert_counts",
            "units",
        },
        "oracle.semantic_contract.dxf",
        errors,
    )
    blocks = dxf.get("required_block_names")
    inserts = dxf.get("required_insert_names")
    if not isinstance(blocks, list) or not blocks or len(blocks) != len(set(blocks)):
        errors.append("DXF required block names must be unique and non-empty")
        blocks = []
    if not isinstance(inserts, list) or not inserts or len(inserts) != len(set(inserts)):
        errors.append("DXF required insert names must be unique and non-empty")
        inserts = []
    if set(blocks) != set(inserts):
        errors.append("DXF required block and insert names must describe the same parts")
    for key in ("minimum_faces_per_required_block", "minimum_direct_entity_faces"):
        if not isinstance(dxf.get(key), int) or dxf.get(key, 0) < 1:
            errors.append("DXF {} must be a positive integer".format(key))
    if dxf.get("require_equal_nonzero_insert_counts") is not True:
        errors.append("S1 component insert counts must be equal and non-zero")
    if dxf.get("units") != "mm":
        errors.append("the DXF semantic contract must use mm")

    stl = _require_keys(
        contract.get("stl"),
        {"encoding", "minimum_facets", "units"},
        "oracle.semantic_contract.stl",
        errors,
    )
    if stl.get("encoding") != "ascii":
        errors.append("the 556b STL contract must remain ASCII")
    if not isinstance(stl.get("minimum_facets"), int) or stl.get("minimum_facets", 0) < 1:
        errors.append("STL minimum_facets must be a positive integer")
    if stl.get("units") != "mm":
        errors.append("the STL semantic contract must use mm")
    limits = contract.get("comparison_limits")
    if not isinstance(limits, list) or not limits:
        errors.append("semantic comparison limits must be recorded")

    blockers = root.get("blockers")
    if not isinstance(blockers, list) or not blockers:
        errors.append("the blocked oracle needs named blockers")
        blockers = []
    blocker_ids = []
    for index, blocker in enumerate(blockers):
        blocker = _require_keys(
            blocker,
            {"blocker_id", "status", "owner_role", "minimum_evidence"},
            "oracle.blockers[{}]".format(index),
            errors,
        )
        blocker_ids.append(blocker.get("blocker_id"))
        if blocker.get("status") != "open":
            errors.append("every current oracle blocker must remain open")
        if not isinstance(blocker.get("owner_role"), str) or not blocker.get("owner_role", "").strip():
            errors.append("every blocker needs an owner_role")
        evidence = blocker.get("minimum_evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append("every blocker needs minimum_evidence")
    if len(blocker_ids) != len(set(blocker_ids)):
        errors.append("oracle blocker identifiers must be unique")

    gate = _require_keys(
        root.get("acceptance_gate"),
        {
            "status",
            "required_review",
            "raw_hash_equality_is_geometry_oracle",
            "canonical_production_input",
        },
        "oracle.acceptance_gate",
        errors,
    )
    if gate.get("status") != "blocked":
        errors.append("the current oracle acceptance gate must remain blocked")
    if gate.get("raw_hash_equality_is_geometry_oracle") is not False:
        errors.append("raw hash equality must not be treated as a geometry oracle")
    if gate.get("canonical_production_input") is not False:
        errors.append("Templot output cannot be canonical production input")
    return errors


def load_spec(path=DEFAULT_SPEC_PATH):
    """Load and validate the tracked oracle specification."""
    path = pathlib.Path(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_spec(document)
    if errors:
        raise OracleValidationError("; ".join(errors))
    return document


def _source_archive_path(spec):
    path = pathlib.Path(spec["source"]["archive"]["path"])
    return path if path.is_absolute() else ROOT / path


def probe_source_archive(archive_path, spec):
    """Verify exact archive/member hashes and the recorded S1 export route."""
    archive_path = pathlib.Path(archive_path)
    if not archive_path.is_file():
        raise OracleValidationError(
            "local Templot5 source archive is unavailable: {}".format(archive_path)
        )
    expected_archive = spec["source"]["archive"]["sha256"]
    actual_archive = _sha256_path(archive_path)
    if actual_archive != expected_archive:
        raise OracleValidationError(
            "source archive SHA-256 mismatch: expected {}, got {}".format(
                expected_archive, actual_archive
            )
        )

    member_results = []
    with zipfile.ZipFile(str(archive_path)) as archive:
        names = set(archive.namelist())
        for expected in spec["source"]["required_members"]:
            name = expected["path"]
            if name not in names:
                raise OracleValidationError(
                    "required source archive member is missing: {}".format(name)
                )
            actual = _sha256_bytes(archive.read(name))
            if actual != expected["sha256"]:
                raise OracleValidationError(
                    "source member SHA-256 mismatch for {}".format(name)
                )
            member_results.append(
                {"path": name, "sha256": actual, "role": expected["role"]}
            )

        dxf_source = archive.read(
            "T556B_ZIPPED_FOR_UPLOAD/dxf_unit.pas"
        ).decode("utf-8-sig", errors="replace")
        assembly_source = archive.read(
            "T556B_ZIPPED_FOR_UPLOAD/chairs_unit_x.pas"
        ).decode("utf-8-sig", errors="replace")
        version_form = archive.read(
            "T556B_ZIPPED_FOR_UPLOAD/control_room.lfm"
        ).decode("utf-8-sig", errors="replace")

        required_names = spec["semantic_contract"]["dxf"]["required_block_names"]
        for name in required_names:
            if name not in dxf_source or name not in assembly_source:
                raise OracleValidationError(
                    "source route does not contain required S1 component {}".format(name)
                )
        if "version  556b" not in version_form:
            raise OracleValidationError("source revision label 556b is missing")

        missing_build_inputs = []
        lowered_names = [name.lower() for name in names]
        for expected in spec["source"]["build_probe"]["archive_missing_inputs"]:
            if not any(expected.lower() in name for name in lowered_names):
                missing_build_inputs.append(expected)

    return {
        "status": "exact-source-verified-build-blocked",
        "archive": {
            "filename": archive_path.name,
            "sha256": actual_archive,
            "verified_member_count": len(member_results),
        },
        "required_revision": spec["source"]["required_revision"],
        "required_members": member_results,
        "s1_component_route_confirmed": True,
        "self_contained_build_ready": False,
        "missing_declared_build_inputs": missing_build_inputs,
        "build_probe_disposition": spec["source"]["build_probe"]["disposition"],
    }


def inspect_executable(path, spec):
    """Fingerprint a local candidate and reject any non-556b version marker."""
    path = pathlib.Path(path)
    if not path.is_file():
        raise OracleValidationError("executable candidate is unavailable: {}".format(path))
    payload = path.read_bytes()
    flattened = payload.replace(b"\x00", b"")
    lowered = flattened.lower()
    detected = sorted(
        {
            match.group(1).decode("ascii", errors="replace").lower()
            for match in VERSION_RE.finditer(flattened)
        }
    )
    accepted_markers = spec["source"]["accepted_executable_markers"]
    matched_markers = [
        marker
        for marker in accepted_markers
        if marker.lower().encode("ascii") in lowered
    ]
    digest = _sha256_bytes(payload)
    rejected_digest = spec["source"]["observed_candidate"]["sha256"]
    is_pe = payload.startswith(b"MZ")
    return {
        "status": (
            "exact-version-candidate"
            if is_pe and matched_markers and digest != rejected_digest
            else "rejected-version-candidate"
        ),
        "filename": path.name,
        "sha256": digest,
        "pe_signature": is_pe,
        "detected_versions": detected,
        "matched_required_markers": matched_markers,
        "matches_recorded_rejected_candidate": digest == rejected_digest,
        "eligible_for_isolated_capture": bool(
            is_pe and matched_markers and digest != rejected_digest
        ),
    }


def _dxf_records(payload):
    try:
        text = payload.decode("ascii")
    except UnicodeDecodeError:
        text = payload.decode("latin-1")
    lines = text.splitlines()
    if lines:
        lines[0] = lines[0].lstrip("\ufeff")
    if len(lines) % 2:
        raise OracleValidationError("DXF has an unmatched group-code line")
    pairs = []
    for index in range(0, len(lines), 2):
        try:
            code = int(lines[index].strip())
        except ValueError:
            raise OracleValidationError(
                "DXF group code at line {} is not an integer".format(index + 1)
            )
        pairs.append((code, lines[index + 1].strip()))

    record = []
    for pair in pairs:
        if pair[0] == 0 and record:
            yield record
            record = []
        record.append(pair)
    if record:
        yield record


def _record_value(record, code, default=None):
    for item_code, value in record:
        if item_code == code:
            return value
    return default


def _finite_float(value, label):
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise OracleValidationError("{} is not numeric".format(label))
    if not math.isfinite(result):
        raise OracleValidationError("{} is not finite".format(label))
    return result


def _face_vertices(record):
    vertices = []
    for offset in range(4):
        values = [_record_value(record, code + offset) for code in (10, 20, 30)]
        if offset == 3 and all(value is None for value in values):
            break
        if any(value is None for value in values):
            raise OracleValidationError("DXF 3DFACE has an incomplete vertex")
        vertices.append(
            tuple(
                _finite_float(value, "DXF 3DFACE coordinate")
                for value in values
            )
        )
    if len(vertices) < 3:
        raise OracleValidationError("DXF 3DFACE has fewer than three vertices")
    return vertices


def _empty_bounds():
    return [[math.inf, math.inf, math.inf], [-math.inf, -math.inf, -math.inf]]


def _extend_bounds(bounds, vertices):
    for vertex in vertices:
        for axis, value in enumerate(vertex):
            bounds[0][axis] = min(bounds[0][axis], value)
            bounds[1][axis] = max(bounds[1][axis], value)


def _normalise_number(value):
    rounded = round(float(value), 9)
    return 0.0 if rounded == 0 else rounded


def _serialise_bounds(bounds):
    if math.isinf(bounds[0][0]):
        return None
    return {
        "min": [_normalise_number(value) for value in bounds[0]],
        "max": [_normalise_number(value) for value in bounds[1]],
    }


def inspect_dxf(path, spec):
    """Parse the bounded DXF semantics needed by the S1 comparison recipe."""
    path = pathlib.Path(path)
    payload = path.read_bytes()
    section = None
    current_block = None
    blocks = {}
    direct_faces = 0
    direct_bounds = _empty_bounds()
    inserts = []

    for record in _dxf_records(payload):
        entity_type = _record_value(record, 0, "").upper()
        if entity_type == "SECTION":
            section = (_record_value(record, 2, "") or "").upper()
            continue
        if entity_type == "ENDSEC":
            section = None
            current_block = None
            continue
        if section == "BLOCKS" and entity_type == "BLOCK":
            name = (_record_value(record, 2, "") or "").upper()
            if not name:
                raise OracleValidationError("DXF BLOCK has no name")
            if name in blocks:
                raise OracleValidationError("DXF contains duplicate BLOCK {}".format(name))
            current_block = name
            blocks[name] = {"face_count": 0, "bounds": _empty_bounds()}
            continue
        if section == "BLOCKS" and entity_type == "ENDBLK":
            current_block = None
            continue
        if entity_type == "3DFACE":
            vertices = _face_vertices(record)
            if section == "BLOCKS" and current_block is not None:
                blocks[current_block]["face_count"] += 1
                _extend_bounds(blocks[current_block]["bounds"], vertices)
            elif section == "ENTITIES":
                direct_faces += 1
                _extend_bounds(direct_bounds, vertices)
            continue
        if section == "ENTITIES" and entity_type == "INSERT":
            name = (_record_value(record, 2, "") or "").upper()
            if not name:
                raise OracleValidationError("DXF INSERT has no block name")
            insertion = [
                _finite_float(_record_value(record, code, "0"), "DXF INSERT position")
                for code in (10, 20, 30)
            ]
            scale = [
                _finite_float(_record_value(record, code, "1"), "DXF INSERT scale")
                for code in (41, 42, 43)
            ]
            rotation = _finite_float(
                _record_value(record, 50, "0"), "DXF INSERT rotation"
            )
            inserts.append(
                {
                    "name": name,
                    "insertion": [_normalise_number(value) for value in insertion],
                    "scale": [_normalise_number(value) for value in scale],
                    "rotation_degrees": _normalise_number(rotation),
                }
            )

    contract = spec["semantic_contract"]["dxf"]
    required_names = contract["required_block_names"]
    required_blocks = {}
    for name in required_names:
        block = blocks.get(name)
        if block is None:
            raise OracleValidationError("DXF required S1 block is missing: {}".format(name))
        if block["face_count"] < contract["minimum_faces_per_required_block"]:
            raise OracleValidationError("DXF required S1 block has no usable faces: {}".format(name))
        required_blocks[name] = {
            "face_count": block["face_count"],
            "bounds_mm": _serialise_bounds(block["bounds"]),
        }

    if direct_faces < contract["minimum_direct_entity_faces"]:
        raise OracleValidationError(
            "DXF has no direct assembly/base 3DFACE entities"
        )
    required_insert_names = contract["required_insert_names"]
    required_inserts = {
        name: sorted(
            (item for item in inserts if item["name"] == name),
            key=lambda item: (
                item["insertion"], item["scale"], item["rotation_degrees"]
            ),
        )
        for name in required_insert_names
    }
    counts = {name: len(items) for name, items in required_inserts.items()}
    if contract["require_equal_nonzero_insert_counts"] and (
        not counts or 0 in counts.values() or len(set(counts.values())) != 1
    ):
        raise OracleValidationError(
            "DXF S1 component INSERT counts must be equal and non-zero: {}".format(
                counts
            )
        )

    return {
        "sha256": _sha256_bytes(payload),
        "block_count": len(blocks),
        "required_blocks": required_blocks,
        "direct_entity_3dface_count": direct_faces,
        "direct_entity_bounds_mm": _serialise_bounds(direct_bounds),
        "required_insert_counts": counts,
        "required_inserts": required_inserts,
    }


def inspect_ascii_stl(path, spec):
    """Parse deterministic bounds/facet semantics from Templot's ASCII STL."""
    path = pathlib.Path(path)
    payload = path.read_bytes()
    try:
        text = payload.decode("ascii")
    except UnicodeDecodeError:
        raise OracleValidationError("STL is not ASCII")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or not lines[0].lower().startswith("solid"):
        raise OracleValidationError("ASCII STL has no solid header")
    if not lines[-1].lower().startswith("endsolid"):
        raise OracleValidationError("ASCII STL has no endsolid record")

    facet_count = 0
    endfacet_count = 0
    vertices = []
    for line in lines:
        words = line.split()
        if len(words) >= 2 and words[0].lower() == "facet" and words[1].lower() == "normal":
            facet_count += 1
        elif words and words[0].lower() == "endfacet":
            endfacet_count += 1
        elif words and words[0].lower() == "vertex":
            if len(words) != 4:
                raise OracleValidationError("ASCII STL vertex is malformed")
            vertices.append(
                tuple(
                    _finite_float(value, "ASCII STL vertex")
                    for value in words[1:]
                )
            )

    minimum = spec["semantic_contract"]["stl"]["minimum_facets"]
    if facet_count < minimum:
        raise OracleValidationError("ASCII STL contains too few facets")
    if endfacet_count != facet_count or len(vertices) != facet_count * 3:
        raise OracleValidationError(
            "ASCII STL facet/vertex records are incomplete"
        )
    bounds = _empty_bounds()
    _extend_bounds(bounds, vertices)
    return {
        "sha256": _sha256_bytes(payload),
        "facet_count": facet_count,
        "vertex_record_count": len(vertices),
        "bounds_mm": _serialise_bounds(bounds),
    }


def inspect_artifacts(dxf_path, stl_path, spec):
    """Return a reviewable summary; never promote the capture to canonical data."""
    dxf_path = pathlib.Path(dxf_path)
    stl_path = pathlib.Path(stl_path)
    return {
        "schema_version": 1,
        "oracle_id": spec["oracle_id"],
        "status": "semantically-valid-unaccepted-capture",
        "source_revision_required": spec["source"]["required_revision"],
        "artifacts": {
            "dxf": {"filename": dxf_path.name, "semantics": inspect_dxf(dxf_path, spec)},
            "stl": {"filename": stl_path.name, "semantics": inspect_ascii_stl(stl_path, spec)},
        },
        "acceptance_gate": "blocked pending exact source, fixture, settings and owner review",
        "canonical_production_input": False,
    }


def _print_json(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def _build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=pathlib.Path, default=DEFAULT_SPEC_PATH)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-spec", help="validate the tracked oracle contract")

    source_parser = subparsers.add_parser(
        "probe-source", help="verify the ignored exact-556b source archive"
    )
    source_parser.add_argument("--archive", type=pathlib.Path)

    exe_parser = subparsers.add_parser(
        "inspect-executable", help="fingerprint and version-check a local executable"
    )
    exe_parser.add_argument("executable", type=pathlib.Path)

    artifact_parser = subparsers.add_parser(
        "inspect-artifacts", help="validate a local S1 DXF/STL capture"
    )
    artifact_parser.add_argument("--dxf", type=pathlib.Path, required=True)
    artifact_parser.add_argument("--stl", type=pathlib.Path, required=True)
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        spec = load_spec(args.spec)
        if args.command == "validate-spec":
            _print_json(
                {
                    "oracle_id": spec["oracle_id"],
                    "status": spec["status"],
                    "validation": "passed",
                }
            )
            return 0
        if args.command == "probe-source":
            archive_path = args.archive or _source_archive_path(spec)
            _print_json(probe_source_archive(archive_path, spec))
            return 0
        if args.command == "inspect-executable":
            result = inspect_executable(args.executable, spec)
            _print_json(result)
            return 0 if result["eligible_for_isolated_capture"] else 2
        if args.command == "inspect-artifacts":
            _print_json(inspect_artifacts(args.dxf, args.stl, spec))
            return 0
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print("S1 oracle validation failed: {}".format(exc), file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
