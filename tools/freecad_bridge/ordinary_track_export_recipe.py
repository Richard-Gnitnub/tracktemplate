"""Pure contracts for the Phase 1 B14 ordinary-track selected export."""

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
            "Unexpected ordinary-track export files: {}".format(names)
        )
    manifest_items = [
        item for name, item in files.items() if name.lower().endswith(".csv")
    ]
    if len(manifest_items) != 1:
        raise ValueError("Expected one ordinary-track export manifest")
    manifest = manifest_items[0].get("manifest", {})
    if tuple(manifest.get("fields", [])) != MANIFEST_FIELDS:
        raise ValueError("Unexpected ordinary-track export manifest schema")
    rows = manifest.get("rows", [])
    if len(rows) != EXPECTED_MANIFEST_ROW_COUNT:
        raise ValueError(
            "Unexpected ordinary-track manifest row count: {}".format(len(rows))
        )
    if any(row.get("Export status") != "Success" for row in rows):
        raise ValueError("Ordinary-track manifest contains a non-success row")
    formats = sorted({row.get("Export format", "") for row in rows})
    if formats != ["DXF", "STEP", "STL", "SVG"]:
        raise ValueError("Unexpected ordinary-track manifest formats: {}".format(formats))
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
