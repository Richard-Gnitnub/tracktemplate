"""Inspect one frozen private catalogue without executing source documents.

Retained BReps are derived inspection evidence, never canonical chair
geometry. This module reads only the reviewed catalogue and its bound assets;
it does not regenerate, scale, place, import Python, or write files.
"""

from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import re
import stat
import xml.etree.ElementTree as ET
import zipfile


CATALOGUE_SHA256 = (
    "f1016a97f35cc87cca9e0b9f09e70ea1cec4620c43d9451430dfb299eed6b885"
)
INVENTORY_SHA256 = (
    "df8c942b3cf74508e45b8ab220c17db53912da7857109f656cda3d5f81236e93"
)
_FILE_LIMIT = 16 * 1024 * 1024
_ARCHIVE_LIMIT = 8 * 1024 * 1024
_MEMBER_LIMIT = 128
_NAME = r"[A-Za-z_][A-Za-z0-9_]*\Z"
_SHA256 = r"[0-9a-f]{64}\Z"


class CatalogueChairError(ValueError):
    """Recoverable refusal before document or source-file mutation."""


@dataclass(frozen=True)
class CatalogueBinding:
    """Exact private input identity; no redistribution permission follows."""

    path: str
    sha256: str


@dataclass(frozen=True)
class CatalogueComponent:
    """Named saved BRep and XML placement, without host interpretation.

    Placement order is tx, ty, tz in model millimetres, then qx, qy, qz,
    qw. The native adapter must preserve saved shape-location semantics.
    """

    name: str
    label: str
    brep_text: str
    xml_placement: tuple[float, ...]


@dataclass(frozen=True)
class CatalogueChair:
    """Immutable private evidence selection, not a chair definition."""

    catalogue_path: str
    label: str
    run: str
    context_json: str
    model_path: str
    model_sha256: str
    catalogue_sha256: str
    components: tuple[CatalogueComponent, ...]
    bindings: tuple[CatalogueBinding, ...]
    limitations: tuple[str, ...]
    metadata_json: str

    @property
    def context(self):
        """Return a detached context value for a neutral result receipt."""
        return json.loads(self.context_json)

    @property
    def metadata(self):
        """Return detached provenance and retained limitations."""
        return json.loads(self.metadata_json)


def _require(condition, message):
    if not condition:
        raise CatalogueChairError(message)


def _encoded(value):
    return json.dumps(value, sort_keys=True, allow_nan=False)


def _pairs(items):
    result = {}
    for name, value in items:
        _require(name not in result, "Duplicate JSON member: " + name)
        result[name] = value
    return result


def _constant(value):
    raise CatalogueChairError("Non-finite JSON value: " + value)


def _json(data):
    return json.loads(data, object_pairs_hook=_pairs, parse_constant=_constant)


def _read(path):
    path = Path(path)
    _require(path.is_absolute() and path.resolve() == path,
             "Source path must be absolute and must not use symbolic links")
    _require(stat.S_ISREG(path.stat().st_mode),
             "Source must be a regular file")
    with path.open("rb") as stream:
        data = stream.read(_FILE_LIMIT + 1)
    _require(len(data) <= _FILE_LIMIT, "Source file exceeds the size limit")
    return data


def _bound(record, root, bindings):
    path = Path(record["path"])
    digest = record["sha256"]
    _require(isinstance(digest, str) and re.fullmatch(_SHA256, digest),
             "Invalid source SHA-256")
    _require(path.is_absolute() and path.is_relative_to(root),
             "Source binding escapes the retained inventory")
    data = _read(path)
    _require(hashlib.sha256(data).hexdigest() == digest,
             "Source binding changed: " + str(path))
    previous = bindings.setdefault(str(path), digest)
    _require(previous == digest, "Conflicting source bindings")
    return data


def _components(model_bytes):
    """Read only the finite saved Part::Feature member layout.

    Never extract an archive or restore a FreeCAD document. The caller must
    verify the complete model hash before this internal parsing boundary.
    """
    with zipfile.ZipFile(BytesIO(model_bytes)) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        _require(0 < len(infos) <= _MEMBER_LIMIT,
                 "Unsupported archive member count")
        _require(len(set(names)) == len(names), "Duplicate archive member")
        _require(sum(info.file_size for info in infos) <= _ARCHIVE_LIMIT,
                 "Expanded archive exceeds the size limit")
        _require(all(not info.is_dir() and not info.flag_bits & 1
                     and info.compress_type in (
                         zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED,
                     ) and "/" not in info.filename
                     and "\\" not in info.filename for info in infos),
                 "Unsupported archive member layout")
        xml = archive.read("Document.xml")
        _require(b"<!DOCTYPE" not in xml.upper()
                 and b"<!ENTITY" not in xml.upper(),
                 "Document XML declarations are unsupported")
        document = ET.fromstring(xml)
        _require(document.tag == "Document"
                 and document.get("SchemaVersion") == "4"
                 and document.get("FileVersion") == "1",
                 "Unsupported saved document schema")
        objects = document.findall("./Objects/Object")
        data = document.findall("./ObjectData/Object")
        object_names = [obj.get("name") for obj in objects]
        _require(objects and len(object_names) == len(set(object_names))
                 and all(isinstance(name, str) and re.fullmatch(_NAME, name)
                         for name in object_names),
                 "Invalid or duplicate saved component name")
        _require([obj.get("name") for obj in data] == object_names,
                 "Saved component ordering differs")
        _require(all(obj.get("type") == "Part::Feature" for obj in objects),
                 "Only retained static Part::Feature components are supported")
        components = []
        shape_members = set()
        for name, obj in zip(object_names, data):
            properties = obj.findall("./Properties/Property")
            property_names = [prop.get("name") for prop in properties]
            _require(len(property_names) == len(set(property_names)),
                     "Duplicate saved property")
            props = {prop.get("name"): prop for prop in properties}
            shape = props["Shape"]
            parts = shape.findall("Part")
            member = name + ".Shape.brp"
            _require(shape.get("type") == "Part::PropertyPartShape"
                     and len(parts) == 1 and parts[0].get("file") == member,
                     "Saved component BRep binding differs")
            place = props["Placement"].find("PropertyPlacement")
            _require(place is not None, "Saved component placement is absent")
            values = tuple(float(place.get(key)) for key in (
                "Px", "Py", "Pz", "Q0", "Q1", "Q2", "Q3",
            ))
            _require(all(math.isfinite(value) for value in values)
                     and any(value != 0 for value in values[3:]),
                     "Invalid saved component placement")
            label = props["Label"].find("String")
            _require(label is not None and label.get("value") is not None,
                     "Saved component label is absent")
            expression = props["ExpressionEngine"].find("ExpressionEngine")
            _require(expression is not None and len(expression) == 0
                     and expression.get("count") == "0",
                     "Saved expressions are unsupported")
            brep = archive.read(member).decode("ascii")
            _require(bool(brep.strip()), "Empty saved BRep")
            shape_members.add(member)
            components.append(CatalogueComponent(
                name, label.get("value"), brep, values,
            ))
        auxiliary = {name + ".Shape.Map.txt" for name in object_names}
        _require(set(names) <= shape_members | auxiliary | {"Document.xml"},
                 "Unbound archive member")
        return tuple(components)


def _selection(index, inventory, label, run):
    _require(index["schema_version"] == 1
             and index["status"] == "PRIVATE_REFERENCE_CATALOGUE"
             and index["active_label_count"] == 29
             and index["native_pass_available_count"] == 29
             and index["unsupported_count"] == 13
             and index["production_accepted"] is False
             and index["rights_cleared"] is False,
             "Unsupported catalogue scope")
    labels = {name for group in inventory["real"] for name in group["members"]}
    entries = index["entries"]
    _require(len(entries) == len(labels) == 29
             and {entry["label"] for entry in entries} == labels,
             "Catalogue labels differ from the frozen inventory")
    _require(isinstance(label, str) and label in labels,
             "Unknown or source-null chair label")
    entry = next(item for item in entries if item["label"] == label)
    _require(entry["project_status"] == "reference-only"
             and entry["intended_use"] == "private-development"
             and entry["acceptance"] == "NO_NEW_ACCEPTANCE",
             "Catalogue use or acceptance boundary differs")
    selected = entry["selected_model"]
    _require(isinstance(selected, dict), "No selected native model")
    if run is not None and run != selected["run"]:
        _require(label == "CC" and run == "context-native-02",
                 "Only the retained CC alternative context is supported")
        matches = [item for item in entry["attempts"] if item["run"] == run]
        _require(len(matches) == 1, "Alternative context is ambiguous")
        selected = matches[0]
    _require(selected["selectable"] is True, "Native model is not selectable")
    return entry, selected


def _prepare(catalogue_path, label, run):
    path = Path(catalogue_path).absolute()
    data = _read(path)
    _require(hashlib.sha256(data).hexdigest() == CATALOGUE_SHA256,
             "Catalogue differs from the reviewed private catalogue")
    index = _json(data)
    root = Path(index["inventory_root"])
    _require(root.is_absolute() and root.resolve() == root,
             "Retained inventory root differs")
    bindings = {str(path): CATALOGUE_SHA256}
    _require(index["inventory_binding"]["sha256"] == INVENTORY_SHA256,
             "Catalogue inventory identity differs")
    inventory = _json(_bound(index["inventory_binding"], root, bindings))
    for binding in index["recipe_bindings"]:
        _bound(binding, root, bindings)
    entry, selected = _selection(index, inventory, label, run)
    bound = {name: _bound(selected[name], root, bindings) for name in (
        "model", "receipt", "execution_receipt", "result_receipt",
    )}
    execution = _json(bound["execution_receipt"])
    receipts = _json(bound["receipt"])
    existing = selected["run"] == "existing-02"
    record = receipts["families"][label] if existing else receipts[label]
    _require(execution["status"] == "PASS"
             and all(execution.get(field) for field in (
                 "qualified_runtime", "freecad_version", "occt_version",
                 "python_version",
             )), "Native runtime receipt is incomplete")
    _require(execution["model_hashes"][label] == selected["model"]["sha256"]
             and execution["result_sha256"] ==
             selected["result_receipt"]["sha256"],
             "Native validation-time artifact identity differs")
    if existing:
        _require(execution["validation_sha256"] ==
                 selected["receipt"]["sha256"]
                 and record["status"] == "PASS",
                 "Existing-family validation identity differs")
    else:
        _require(record["status"] in ("PASS", "native-components-valid")
                 and record["native_reload"] == "PASS"
                 and record["scope"] == "private-development"
                 and record["production_ready"] is False,
                 "Native family receipt is not an admitted private result")
    components = _components(bound["model"])
    limitations = tuple(entry["limitations"]) + (
        "Retained finite source context only; no new geometry acceptance.",
        "Private reference; no production, export or redistribution "
        "authority.",
        "No track placement, live invalidation or persistence contract.",
        "Source overlaps, component closures and physical-fit findings "
        "remain.",
    )
    metadata = {
        "project_status": "reference-only",
        "intended_uses": ["private-development"],
        "production_geometry_authorized": False,
        "acceptance": entry["acceptance"],
        "reference_admission": entry["reference_admission"],
        "source_codes": entry["source_codes"],
        "source_inventory": inventory["source"],
        "source_explicit_nyi": index["source_explicit_nyi"],
        "native_record": record,
        "phase_acceptance": index["phase_acceptance"],
    }
    return CatalogueChair(
        str(path), label, selected["run"], _encoded(selected["context"]),
        selected["model"]["path"], selected["model"]["sha256"],
        CATALOGUE_SHA256, components,
        tuple(CatalogueBinding(name, digest)
              for name, digest in sorted(bindings.items())),
        limitations, _encoded(metadata),
    )


def prepare_catalogue_chair(catalogue_path, label, *, run=None):
    """Read one frozen private model; refuse changed or unsupported inputs.

    No arbitrary catalogue admission or caller-supplied hash is supported.
    Default selection preserves the frozen catalogue; only CC also permits
    its retained C10 context. All source files remain untouched.
    """
    try:
        return _prepare(catalogue_path, label, run)
    except CatalogueChairError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            zipfile.BadZipFile, ET.ParseError, UnicodeError) as error:
        raise CatalogueChairError("Invalid private catalogue evidence: "
                                  + str(error)) from error


def verify_catalogue_sources(prepared):
    """Recheck all consumed bytes and reject altered derived records."""
    _require(isinstance(prepared, CatalogueChair),
             "Expected an immutable catalogue selection")
    current = prepare_catalogue_chair(
        prepared.catalogue_path, prepared.label, run=prepared.run,
    )
    _require(current == prepared, "Catalogue source or prepared state changed")
