"""Read fixed private crossing evidence through one bounded verifier.

Callers own explicit context allow-lists and immutable catalogue pins.
No geometry is constructed and no document is opened here.
"""

import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from tracktemplate.application.chair_catalogue import (
    CatalogueBinding,
    CatalogueChair,
    CatalogueChairError,
    _bound,
    _components,
    _encoded,
    _json,
    _read,
    _require,
)


_RUNTIME_FIELDS = (
    "qualified_runtime", "freecad_version", "occt_version", "python_version",
)


def _read_contexts(path, digest, specifications, limits):
    path = Path(path).absolute()
    data = _read(path)
    _require(hashlib.sha256(data).hexdigest() == digest,
             "Crossing supplement differs from the reviewed private evidence")
    manifest = _json(data)
    _require(manifest["schema_version"] == 1
             and manifest["contract_id"]
             == "tracktemplate.private-crossing-catalogue.v1"
             and manifest["project_status"] == "reference-only"
             and manifest["intended_uses"] == ["private-development"]
             and manifest["production_accepted"] is False
             and manifest["rights_cleared"] is False
             and manifest["physical_fit"] == "NOT_PROVED"
             and manifest["context_count"] == 8
             and manifest["source_position_count"] == 40,
             "Unsupported Crossing catalogue scope")
    root = Path(manifest["inventory_root"])
    _require(root.is_absolute() and root.resolve() == root
             and path.is_relative_to(root), "Invalid Crossing inventory root")
    _require(all(isinstance(manifest[key], str)
                 and re.fullmatch(r"[0-9a-f]{64}", manifest[key])
                 for key in ("source_context_sha256", "host_context_sha256")),
             "Invalid Crossing source or host context identity")
    bindings = {str(path): digest}
    qualification = _json(_bound(manifest["qualification"], root, bindings))
    oracle = _json(_bound(manifest["source_oracle"], root, bindings))
    hosts = _json(_bound(manifest["canonical_hosts"], root, bindings))
    process = _json(_bound(manifest["native_process"], root, bindings))
    _require(qualification["status"] == "PASS"
             and qualification["documents_closed"] is True
             and qualification["production_accepted"] is False
             and qualification["physical_fit"] == "NOT_PROVED"
             and all(qualification.get(key) for key in _RUNTIME_FIELDS),
             "Crossing native qualification is incomplete")
    _require(oracle["status"] == "PASS" and oracle["context_count"] == 8
             and oracle["position_count"] == 40,
             "Independent crossing source qualification is incomplete")
    _require(process["status"] == "PASS" and process["returncode"] == 0
             and process["sentinel_present"] is True
             and process["sentinel"] == "CROSSING_CONTEXT_NATIVE_PASS",
             "Crossing native process qualification is incomplete")
    _require(hashlib.sha256(_encoded(hosts["hosts"]).encode()).hexdigest()
             == manifest["host_context_sha256"],
             "Canonical host evidence differs")
    records = qualification["contexts"]
    context_ids = manifest["context_ids"]
    _require(len(context_ids) == len(set(context_ids)) == 8
             and set(records) == set(context_ids)
             and {item[0] for item in specifications} <= set(records),
             "Frozen crossing qualification identities differ")
    selections = []
    for context_id, family, chair_code, component_count in specifications:
        record = records[context_id]
        recipe = record["source_recipe"]
        context = recipe["context"]
        native = recipe["native_frame"]
        _require(record["status"] == record["native_reload"]
                 == record["fixing_proof"] == "PASS"
                 and record["family"] == recipe["family"] == family
                 and record["context_id"] == recipe["context_id"]
                 == context_id
                 and record["timber_id"] == recipe["timber_id"]
                 == context_id[3:]
                 and record["chair_code"] == recipe["chair_code"] == chair_code
                 and record["source_station_mm"] == recipe["station_mm"]
                 and recipe["sample_kind"]
                 == "fixture_timber_" + context_id[3:]
                 and context["rail_code"] == 3
                 and context["hand_i"] == native["hand_i"] == -1
                 and context["chair_y_mm"] == 16.5
                 and context["chair_k_rad"] == context["keq_rad"] == 0
                 and native["common_timber_curving_applied"] is False,
                 "Crossing context identity or source frame differs")
        model = _bound(record["model"], root, bindings)
        result = _json(_bound(record["result_receipt"], root, bindings))
        _bound(record["receipt"], root, bindings)
        execution = _json(_bound(record["execution_receipt"], root, bindings))
        source_recipe = _json(_bound(
            execution["source_recipe_binding"], root, bindings,
        ))
        _require(execution["status"] == execution["native_reload"]
                 == execution["fixing_proof"] == "PASS"
                 and execution["context_id"] == context_id
                 and execution["model_hashes"][family]
                 == record["model"]["sha256"]
                 and execution["result_sha256"]
                 == record["result_receipt"]["sha256"]
                 and result[family]["status"]
                 == result[family]["native_reload"] == "PASS"
                 and source_recipe == [recipe],
                 "Crossing execution and native result disagree")
        components = _components(model)
        _require(len(components) == record["component_count"] == component_count
                 and tuple(item.name for item in components)
                 == tuple(item["name"] for item in record["components"]),
                 "Crossing native component identities differ")
        metadata = {
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "acceptance": "NO_NEW_ACCEPTANCE",
            "native_record": record,
            "source_context_sha256": manifest["source_context_sha256"],
            "host_context_sha256": manifest["host_context_sha256"],
            "source_oracle": manifest["source_oracle"],
        }
        selections.append((record, recipe, components, metadata))
    frozen = tuple(CatalogueBinding(name, digest)
                   for name, digest in sorted(bindings.items()))
    return tuple(CatalogueChair(
        str(path), record["family"], recipe["context_id"], _encoded(recipe),
        record["model"]["path"], record["model"]["sha256"],
        digest, components, frozen,
        limits,
        _encoded(metadata),
    ) for record, recipe, components, metadata in selections)



def _prepare_contexts(path, digest, specifications, limits):
    """Read an internal fixed selection or fail before any mutation."""
    try:
        return _read_contexts(path, digest, specifications, limits)
    except CatalogueChairError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            zipfile.BadZipFile, ET.ParseError, UnicodeError) as error:
        raise CatalogueChairError("Invalid crossing catalogue evidence: "
                                  + str(error)) from error
