"""Pure contracts for the Phase 1 B14 plain-line export paths."""

import copy
import csv
import hashlib
import json
import pathlib
import re


EXPORT_RECIPE_SCHEMA_VERSION = 1
EXPORT_SCOPE = "One template set"
EXPORT_FORMATS = ("dxf", "svg", "stl", "step")
COMMIT_FAILURE_MESSAGE = (
    "Injected Phase 1 selected-export commit failure after one file replacement"
)

EXPECTED_EXPORT_FILENAMES = (
    "Curve_Set_001_Combined_Cutting_Profiles.dxf",
    "Curve_Set_001_Combined_Cutting_Profiles.svg",
    "Curve_Set_001_Combined_Engraving.dxf",
    "Curve_Set_001_Combined_Engraving.svg",
    "Curve_Set_001_Combined_Solid_Assembly.step",
    "Curve_Set_001_Export_Manifest.csv",
    "Curve_Set_001_Track_01_Centreline.dxf",
    "Curve_Set_001_Track_01_Centreline.svg",
    "Curve_Set_001_Track_02_Centreline.dxf",
    "Curve_Set_001_Track_02_Centreline.svg",
    "Curve_Set_001_Track_Template_Compound.dxf",
    "Curve_Set_001_Track_Template_Compound.step",
    "Curve_Set_001_Track_Template_Compound.stl",
    "Curve_Set_001_Track_Template_Compound.svg",
)
EXPECTED_TASK_COUNT = 13
EXPECTED_MANIFEST_ROW_COUNT = 15
EXPECTED_LOGICAL_EXPORT_SHA256 = (
    "91922662487f92b8bdb8f92a65e09fb7b62f2f9d1461704bb7c8cd41c2a15413"
)
EXPECTED_EXPORT_METRICS_SHA256 = (
    "37dcbc20e8ecda9c1a80b3e73646b0c1127211e01488d56eeef49aa08d0789b4"
)
CREATE_TIME_EXPORT_RECIPE_SCHEMA_VERSION = 1
CREATE_TIME_EXPORT_FAILURE_MESSAGE = (
    "Injected Phase 1 create-time export failure at the final planned task"
)
CREATE_TIME_EXPORT_FAILED_FILENAME = (
    "Curve_Set_001_Combined_Solid_Assembly.step"
)
CREATE_TIME_OUTPUT_DIRECTORY_PLACEHOLDER = "<create-time-output-directory>"
EXPECTED_CREATE_TIME_LOGICAL_EXPORT_SHA256 = (
    "b33a2c5cfb6937d988046ad17584ed7bc2957514e77213282dfd665960bc4ffb"
)
EXPECTED_CREATE_TIME_DOCUMENT_SHA256 = (
    "a6aae6d70610ceec50a6223328db1454eca264effc12e7db5df07204707b3aa2"
)
EXPECTED_CREATE_TIME_PARTIAL_EXPORT_SHA256 = (
    "05d27a32b26435eda3b776498c2b28195a943bc2499ced404450f18ce349bf29"
)

MANIFEST_FIELDS = (
    "Macro version",
    "Export date and time",
    "Template-set identifier",
    "Generated object name",
    "Generated object role",
    "Track number",
    "Platform number",
    "Platform name",
    "Section number",
    "Travel-order number",
    "Export format",
    "Export filename",
    "Full export path",
    "Section length",
    "Template thickness",
    "Platform thickness",
    "Formation-board thickness",
    "Joint type",
    "Fixing-hole diameter",
    "Export status",
    "Error message",
)


def _sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def format_metrics_sha256(metrics):
    encoded = json.dumps(
        metrics, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def logical_export_name(name):
    """Map allocator revision names back to their intended output identity."""
    path = pathlib.PurePath(str(name))
    stem = re.sub(r"_Rev_[0-9]+$", "", path.stem)
    return "{}{}".format(stem, path.suffix.lower())


def _normalise_step(raw):
    text = raw.decode("latin-1")
    text = re.sub(
        r"(FILE_NAME\s*\(\s*)'[^']*'(\s*,\s*)'[^']*'",
        r"\1'<export-path>'\2'<export-time>'",
        text,
        count=1,
        flags=re.I,
    )
    text = re.sub(
        r"Open CASCADE STEP translator ([0-9.]+) [0-9]+",
        r"Open CASCADE STEP translator \1 <transient-product-id>",
        text,
    )
    return text.encode("latin-1")


def _normalise_dxf(raw):
    try:
        text = raw.decode("utf-8")
        encoding = "utf-8"
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
        encoding = "latin-1"
    lines = text.splitlines()
    pairs = [lines[index:index + 2] for index in range(0, len(lines) - 1, 2)]
    volatile = {
        "$FINGERPRINTGUID",
        "$HANDSEED",
        "$TDCREATE",
        "$TDUPDATE",
        "$TDINDWG",
        "$USRTIMER",
        "$VERSIONGUID",
    }
    for index, pair in enumerate(pairs[:-1]):
        if pair[0].strip() == "9" and pair[1].strip().upper() in volatile:
            pairs[index + 1][1] = "<volatile>"
    normalised_lines = [value for pair in pairs for value in pair]
    normalised = "\n".join(normalised_lines) + "\n"
    normalised = re.sub(
        r"TemporaryProductionExport_[0-9a-fA-F]+_[0-9]+",
        "TemporaryProductionExport_<transient-id>",
        normalised,
    )
    return normalised.encode(encoding)


def _normalise_svg(raw):
    text = raw.decode("utf-8")
    text = re.sub(
        r"TemporaryProductionExport_[0-9a-fA-F]+_[0-9]+",
        "TemporaryProductionExport_<transient-id>",
        text,
    )
    return text.encode("utf-8")


def _normalise_manifest(path):
    with pathlib.Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fields = tuple(reader.fieldnames or ())
        rows = []
        for source_row in reader:
            row = {field: str(source_row.get(field, "")) for field in fields}
            row["Export date and time"] = "<export-time>"
            filename = logical_export_name(row.get("Export filename", ""))
            row["Export filename"] = filename
            full_path = str(row.get("Full export path", ""))
            row["Full export path"] = (
                "<output>/{}".format(filename) if full_path else ""
            )
            rows.append(row)
    semantic = {"fields": list(fields), "rows": rows}
    encoded = json.dumps(
        semantic, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return semantic, encoded


def normalised_artifact(path):
    path = pathlib.Path(path)
    raw = path.read_bytes()
    suffix = path.suffix.lower()
    manifest = None
    if suffix == ".csv":
        manifest, normalised = _normalise_manifest(path)
    elif suffix in (".step", ".stp"):
        normalised = _normalise_step(raw)
    elif suffix == ".dxf":
        normalised = _normalise_dxf(raw)
    elif suffix == ".svg":
        normalised = _normalise_svg(raw)
    else:
        normalised = raw
    result = {
        "bytes": len(raw),
        "raw_sha256": _sha256_bytes(raw),
        "normalised_sha256": _sha256_bytes(normalised),
    }
    if manifest is not None:
        result["manifest"] = manifest
    return result


def export_directory_snapshot(directory):
    directory = pathlib.Path(directory)
    if not directory.is_dir():
        raise ValueError("Export directory does not exist: {}".format(directory))
    files = {}
    directories = []
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory).as_posix()
        if path.is_dir():
            directories.append(relative)
            continue
        item = normalised_artifact(path)
        item["logical_name"] = logical_export_name(relative)
        files[relative] = item
    content_by_path = {
        relative: item["normalised_sha256"] for relative, item in files.items()
    }
    encoded = json.dumps(
        content_by_path,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return {
        "files": files,
        "directories": directories,
        "content_by_path": content_by_path,
        "content_sha256": _sha256_bytes(encoded),
    }


def _variant_names(revision=None):
    if revision is None:
        return set(EXPECTED_EXPORT_FILENAMES)
    return {
        "{}_Rev_{}{}".format(
            pathlib.PurePath(name).stem,
            str(revision).zfill(2),
            pathlib.PurePath(name).suffix,
        )
        for name in EXPECTED_EXPORT_FILENAMES
    }


def export_variant_snapshot(snapshot, revision=None):
    expected = _variant_names(revision)
    files = {
        name: item for name, item in snapshot.get("files", {}).items()
        if name in expected
    }
    logical = {
        item["logical_name"]: item["normalised_sha256"]
        for item in files.values()
    }
    encoded = json.dumps(
        logical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return {
        "files": files,
        "directories": list(snapshot.get("directories", [])),
        "logical_files": logical,
        "logical_sha256": _sha256_bytes(encoded),
    }


def validate_export_snapshot(snapshot, expected_revision=None):
    files = snapshot.get("files", {})
    names = sorted(files)
    expected = sorted(_variant_names(expected_revision))
    if names != expected:
        raise ValueError(
            "Unexpected plain-line export files: {}".format(names)
        )
    manifest_items = [
        item for name, item in files.items() if name.lower().endswith(".csv")
    ]
    if len(manifest_items) != 1:
        raise ValueError("Expected one plain-line export manifest")
    manifest = manifest_items[0].get("manifest", {})
    if tuple(manifest.get("fields", [])) != MANIFEST_FIELDS:
        raise ValueError("Unexpected plain-line export manifest schema")
    rows = manifest.get("rows", [])
    if len(rows) != EXPECTED_MANIFEST_ROW_COUNT:
        raise ValueError(
            "Unexpected plain-line manifest row count: {}".format(len(rows))
        )
    if any(row.get("Export status") != "Success" for row in rows):
        raise ValueError("Plain-line manifest contains a non-success row")
    formats = sorted({row.get("Export format", "") for row in rows})
    if formats != ["DXF", "STEP", "STL", "SVG"]:
        raise ValueError("Unexpected plain-line manifest formats: {}".format(formats))
    if snapshot.get("directories"):
        raise ValueError(
            "Temporary export directories remain: {}".format(
                snapshot.get("directories")
            )
        )
    return snapshot.get("logical_sha256", "")


def compare_logical_exports(reference, candidate):
    expected = reference.get("logical_files", {})
    actual = candidate.get("logical_files", {})
    if expected != actual:
        differences = {
            name: {"reference": expected.get(name), "candidate": actual.get(name)}
            for name in sorted(set(expected) | set(actual))
            if expected.get(name) != actual.get(name)
        }
        raise ValueError("Export semantics differ: {}".format(differences))
    return reference.get("logical_sha256", "")


def create_time_export_document_snapshot(snapshot, enforce_expected_hash=True):
    """Normalise only the per-run create-time export directory in document state."""
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("semantic"), dict):
        raise ValueError("Invalid create-time plain-line document snapshot")
    semantic = copy.deepcopy(snapshot["semantic"])
    persistence = semantic.get("persistence", {})
    configs = []
    output_directories = []
    for owner in ("settings", "template"):
        values = persistence.get(owner, {}).get("values", {})
        config = values.get("ProductionExportConfigurationJSON")
        if not isinstance(config, dict):
            raise ValueError(
                "Create-time export document lacks {} production configuration".format(
                    owner
                )
            )
        output_directory = str(config.get("output_directory") or "")
        if not output_directory:
            raise ValueError("Create-time export document has no output directory")
        output_directories.append(output_directory)
        config["output_directory"] = CREATE_TIME_OUTPUT_DIRECTORY_PLACEHOLDER
        configs.append(config)
    if output_directories[0] != output_directories[1]:
        raise ValueError(
            "Create-time export settings/template output directories differ"
        )
    if configs[0] != configs[1]:
        raise ValueError("Create-time export settings/template configurations differ")

    config = configs[0]
    expected_fields = {
        "enabled": True,
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
    }
    differences = {
        name: {"actual": config.get(name), "expected": expected}
        for name, expected in expected_fields.items()
        if config.get(name) != expected
    }
    if differences:
        raise ValueError(
            "Unexpected create-time production-export configuration: {}".format(
                differences
            )
        )
    formats = config.get("formats")
    if formats != {key: True for key in EXPORT_FORMATS}:
        raise ValueError("Create-time export does not enable all four formats")
    selections = config.get("selections")
    required_selections = (
        "track_template_compound_2d",
        "track_template_compound_3d",
        "track_centrelines",
    )
    if not isinstance(selections, dict) or any(
        selections.get(name) is not True for name in required_selections
    ):
        raise ValueError("Create-time export omits a fixed-fixture output selection")

    encoded = json.dumps(
        semantic, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    digest = _sha256_bytes(encoded)
    if (
        enforce_expected_hash
        and EXPECTED_CREATE_TIME_DOCUMENT_SHA256
        and digest != EXPECTED_CREATE_TIME_DOCUMENT_SHA256
    ):
        raise ValueError(
            "Unexpected create-time document SHA-256: {} (expected {})".format(
                digest, EXPECTED_CREATE_TIME_DOCUMENT_SHA256
            )
        )
    return {
        "semantic": semantic,
        "semantic_sha256": digest,
        "output_directory": output_directories[0],
        "production_export_config": copy.deepcopy(config),
    }


def compare_create_time_document_to_base(base_snapshot, created_snapshot):
    """Prove create-time export changed only the persisted export configuration."""
    if not isinstance(base_snapshot, dict) or not isinstance(
        base_snapshot.get("semantic"), dict
    ):
        raise ValueError("Invalid base document snapshot for create-time comparison")
    if not isinstance(created_snapshot, dict) or not isinstance(
        created_snapshot.get("semantic"), dict
    ):
        raise ValueError("Invalid created document snapshot for create-time comparison")
    base = copy.deepcopy(base_snapshot["semantic"])
    created = copy.deepcopy(created_snapshot["semantic"])
    for semantic in (base, created):
        for owner in ("settings", "template"):
            values = semantic.get("persistence", {}).get(owner, {}).get("values", {})
            if "ProductionExportConfigurationJSON" not in values:
                raise ValueError(
                    "{} lacks ProductionExportConfigurationJSON".format(owner)
                )
            values.pop("ProductionExportConfigurationJSON")
    if base != created:
        raise ValueError(
            "Create-time export changed plain-line state beyond export configuration"
        )
    return True


def validate_create_time_failure_snapshot(
    snapshot,
    reference_variant,
    enforce_expected_hash=True,
):
    """Diagnose B14's known partial output after the injected final-task failure."""
    files = snapshot.get("files", {})
    expected = set(EXPECTED_EXPORT_FILENAMES)
    expected.remove(CREATE_TIME_EXPORT_FAILED_FILENAME)
    if set(files) != expected:
        raise ValueError(
            "Unexpected create-time failure files: {}".format(sorted(files))
        )
    if snapshot.get("directories"):
        raise ValueError(
            "Create-time failure leaked directories: {}".format(
                snapshot.get("directories")
            )
        )

    reference_files = reference_variant.get("files", {})
    differences = {}
    for name, item in sorted(files.items()):
        if name.lower().endswith(".csv"):
            continue
        expected_item = reference_files.get(name, {})
        if item.get("normalised_sha256") != expected_item.get("normalised_sha256"):
            differences[name] = {
                "failure": item.get("normalised_sha256"),
                "success": expected_item.get("normalised_sha256"),
            }
    if differences:
        raise ValueError(
            "Successful create-time failure artifacts changed: {}".format(differences)
        )

    manifest_items = [
        item for name, item in files.items() if name.lower().endswith(".csv")
    ]
    if len(manifest_items) != 1:
        raise ValueError("Expected one create-time failure manifest")
    manifest = manifest_items[0].get("manifest", {})
    if tuple(manifest.get("fields", [])) != MANIFEST_FIELDS:
        raise ValueError("Unexpected create-time failure manifest schema")
    rows = manifest.get("rows", [])
    if len(rows) != EXPECTED_MANIFEST_ROW_COUNT:
        raise ValueError(
            "Unexpected create-time failure manifest row count: {}".format(len(rows))
        )
    failure_rows = [row for row in rows if row.get("Export status") == "Failure"]
    success_rows = [row for row in rows if row.get("Export status") == "Success"]
    if len(failure_rows) != 1 or len(success_rows) != EXPECTED_MANIFEST_ROW_COUNT - 1:
        raise ValueError("Create-time failure manifest has unexpected status counts")
    failure = failure_rows[0]
    if failure.get("Export filename") != CREATE_TIME_EXPORT_FAILED_FILENAME:
        raise ValueError("Create-time failure manifest identifies the wrong file")
    if failure.get("Export format") != "STEP":
        raise ValueError("Create-time failure manifest identifies the wrong format")
    if CREATE_TIME_EXPORT_FAILURE_MESSAGE not in failure.get("Error message", ""):
        raise ValueError("Create-time failure manifest omits the injected reason")

    digest = str(snapshot.get("content_sha256") or "")
    if (
        enforce_expected_hash
        and EXPECTED_CREATE_TIME_PARTIAL_EXPORT_SHA256
        and digest != EXPECTED_CREATE_TIME_PARTIAL_EXPORT_SHA256
    ):
        raise ValueError(
            "Unexpected create-time partial-output SHA-256: {} (expected {})".format(
                digest, EXPECTED_CREATE_TIME_PARTIAL_EXPORT_SHA256
            )
        )
    return {
        "atomic_output_set": False,
        "content_sha256": digest,
        "file_count": len(files),
        "missing_file": CREATE_TIME_EXPORT_FAILED_FILENAME,
        "manifest_success_rows": len(success_rows),
        "manifest_failure_rows": len(failure_rows),
        "temporary_directories": list(snapshot.get("directories", [])),
    }
