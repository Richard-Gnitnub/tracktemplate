"""Read two frozen private ZY crossing contexts without opening documents.

The existing eight-context evidence remains immutable. Only X1-Z and X2-Y
are admitted here; no other crossing family or geometry is constructed.
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


ZY_CATALOGUE_SHA256 = (
    "91009b0732e3f2f23f9f941675ab9aef392746d11f1a4334c9da50198ae07e4b"
)
ZY_CONTEXT_IDS = ("RH-X1-Z", "RH-X2-Y")
_RUNTIME_FIELDS = (
    "qualified_runtime", "freecad_version", "occt_version", "python_version",
)


def _prepare(path):
    path = Path(path).absolute()
    data = _read(path)
    _require(hashlib.sha256(data).hexdigest() == ZY_CATALOGUE_SHA256,
             "ZY supplement differs from the reviewed private evidence")
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
             "Unsupported ZY catalogue scope")
    root = Path(manifest["inventory_root"])
    _require(root.is_absolute() and root.resolve() == root
             and path.is_relative_to(root), "Invalid ZY inventory root")
    _require(all(isinstance(manifest[key], str)
                 and re.fullmatch(r"[0-9a-f]{64}", manifest[key])
                 for key in ("source_context_sha256", "host_context_sha256")),
             "Invalid ZY source or host context identity")
    bindings = {str(path): ZY_CATALOGUE_SHA256}
    qualification = _json(_bound(manifest["qualification"], root, bindings))
    oracle = _json(_bound(manifest["source_oracle"], root, bindings))
    hosts = _json(_bound(manifest["canonical_hosts"], root, bindings))
    process = _json(_bound(manifest["native_process"], root, bindings))
    _require(qualification["status"] == "PASS"
             and qualification["documents_closed"] is True
             and qualification["production_accepted"] is False
             and qualification["physical_fit"] == "NOT_PROVED"
             and all(qualification.get(key) for key in _RUNTIME_FIELDS),
             "ZY native qualification is incomplete")
    _require(oracle["status"] == "PASS" and oracle["context_count"] == 8
             and oracle["position_count"] == 40,
             "Independent crossing source qualification is incomplete")
    _require(process["status"] == "PASS" and process["returncode"] == 0
             and process["sentinel_present"] is True
             and process["sentinel"] == "CROSSING_CONTEXT_NATIVE_PASS",
             "ZY native process qualification is incomplete")
    _require(hashlib.sha256(_encoded(hosts["hosts"]).encode()).hexdigest()
             == manifest["host_context_sha256"],
             "Canonical host evidence differs")
    records = qualification["contexts"]
    context_ids = manifest["context_ids"]
    _require(len(context_ids) == len(set(context_ids)) == 8
             and set(records) == set(context_ids)
             and set(ZY_CONTEXT_IDS) <= set(records),
             "Frozen crossing qualification identities differ")
    selections = []
    for context_id in ZY_CONTEXT_IDS:
        record = records[context_id]
        recipe = record["source_recipe"]
        context = recipe["context"]
        native = recipe["native_frame"]
        _require(record["status"] == record["native_reload"]
                 == record["fixing_proof"] == "PASS"
                 and record["family"] == recipe["family"] == "ZY"
                 and record["context_id"] == recipe["context_id"]
                 == context_id
                 and record["timber_id"] == recipe["timber_id"]
                 == context_id[3:]
                 and record["chair_code"] == recipe["chair_code"] == 21
                 and record["source_station_mm"] == recipe["station_mm"]
                 and recipe["sample_kind"]
                 == "fixture_timber_" + context_id[3:]
                 and context["rail_code"] == 3
                 and context["hand_i"] == native["hand_i"] == -1
                 and context["chair_y_mm"] == 16.5
                 and context["chair_k_rad"] == context["keq_rad"] == 0
                 and native["common_timber_curving_applied"] is False,
                 "ZY context identity or source frame differs")
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
                 and execution["model_hashes"]["ZY"]
                 == record["model"]["sha256"]
                 and execution["result_sha256"]
                 == record["result_receipt"]["sha256"]
                 and result["ZY"]["status"]
                 == result["ZY"]["native_reload"] == "PASS"
                 and source_recipe == [recipe],
                 "ZY execution and native result disagree")
        components = _components(model)
        _require(len(components) == record["component_count"] == 33
                 and tuple(item.name for item in components)
                 == tuple(item["name"] for item in record["components"]),
                 "ZY native component identities differ")
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
        str(path), "ZY", recipe["context_id"], _encoded(recipe),
        record["model"]["path"], record["model"]["sha256"],
        ZY_CATALOGUE_SHA256, components, frozen,
        ("Private X1-Z and X2-Y source contexts only.",
         "No physical-fit, production, export or rights acceptance."),
        _encoded(metadata),
    ) for record, recipe, components, metadata in selections)


def prepare_zy_catalogue(path):
    """Read both qualified ZY contexts or refuse before any mutation."""
    try:
        return _prepare(path)
    except CatalogueChairError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            zipfile.BadZipFile, ET.ParseError, UnicodeError) as error:
        raise CatalogueChairError("Invalid ZY catalogue evidence: "
                                  + str(error)) from error


def verify_zy_catalogue(selections):
    """Recheck both immutable selections at the transaction boundary."""
    _require(isinstance(selections, tuple)
             and len(selections) == len(ZY_CONTEXT_IDS)
             and all(isinstance(item, CatalogueChair) for item in selections)
             and tuple(item.run for item in selections) == ZY_CONTEXT_IDS,
             "Expected the complete ordered ZY catalogue")
    _require(prepare_zy_catalogue(selections[0].catalogue_path) == selections,
             "ZY catalogue or prepared state changed")
