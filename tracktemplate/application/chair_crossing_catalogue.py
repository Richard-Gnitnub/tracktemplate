"""Read eight frozen, source-qualified private RH crossing contexts.

The original catalogue is unchanged. Only a reviewed complete supplement
can supply derived geometry; no source execution or caller hash is used.
"""

import hashlib
from pathlib import Path
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


# Frozen after native qualification and independent source review.
CROSSING_CATALOGUE_SHA256 = (
    "91009b0732e3f2f23f9f941675ab9aef392746d11f1a4334c9da50198ae07e4b"
)
CROSSING_CONTEXT_IDS = (
    "RH-X1-Z", "RH-X2-Y", "RH-X3-X", "RH-X4-A",
    "RH-X5-B", "RH-X6-C", "RH-X7-D", "RH-X8-E",
)
_FAMILIES = ("ZY", "ZY", "XA", "AA", "BB", "CD", "DD", "EF")


def _prepare(path):
    path = Path(path).absolute()
    data = _read(path)
    _require(hashlib.sha256(data).hexdigest() == CROSSING_CATALOGUE_SHA256,
             "Crossing supplement differs from the reviewed private evidence")
    manifest = _json(data)
    _require(manifest["contract_id"]
             == "tracktemplate.private-crossing-catalogue.v1"
             and manifest["project_status"] == "reference-only"
             and manifest["intended_uses"] == ["private-development"]
             and manifest["production_accepted"] is False
             and manifest["rights_cleared"] is False,
             "Unsupported crossing catalogue scope")
    root = Path(manifest["inventory_root"])
    _require(root.is_absolute() and root.resolve() == root
             and path.is_relative_to(root), "Invalid crossing inventory root")
    bindings = {str(path): CROSSING_CATALOGUE_SHA256}
    qualification = _json(_bound(manifest["qualification"], root, bindings))
    oracle = _json(_bound(manifest["source_oracle"], root, bindings))
    hosts = _json(_bound(manifest["canonical_hosts"], root, bindings))
    _require(qualification["status"] == "PASS"
             and qualification["documents_closed"] is True
             and qualification["production_accepted"] is False
             and qualification["physical_fit"] == "NOT_PROVED"
             and all(qualification.get(key) for key in (
                 "qualified_runtime", "freecad_version", "occt_version",
                 "python_version",
             )), "Crossing native qualification is incomplete")
    _require(oracle["status"] == "PASS" and oracle["context_count"] == 8
             and oracle["position_count"] == 40,
             "Independent crossing source qualification is incomplete")
    _require(hashlib.sha256(_encoded(hosts["hosts"]).encode()).hexdigest()
             == manifest["host_context_sha256"],
             "Canonical host evidence differs")
    records = qualification["contexts"]
    _require(set(records) == set(CROSSING_CONTEXT_IDS),
             "All eight crossing contexts are required")
    selections = []
    for context_id, family in zip(CROSSING_CONTEXT_IDS, _FAMILIES):
        record = records[context_id]
        recipe = record["source_recipe"]
        context = recipe["context"]
        _require(record["status"] == record["native_reload"]
                 == record["fixing_proof"] == "PASS"
                 and record["family"] == recipe["family"] == family
                 and recipe["context_id"] == context_id
                 and recipe["timber_id"] == context_id[3:]
                 and context["hand_i"] == -1
                 and context["chair_y_mm"] == 16.5
                 and context["chair_k_rad"] == context["keq_rad"] == 0,
                 "Crossing context identity or qualification differs")
        model = _bound(record["model"], root, bindings)
        result = _json(_bound(record["result_receipt"], root, bindings))
        _bound(record["receipt"], root, bindings)
        execution = _json(_bound(record["execution_receipt"], root, bindings))
        _bound(execution["source_recipe_binding"], root, bindings)
        _require(execution["status"] == "PASS"
                 and execution["context_id"] == context_id
                 and execution["model_hashes"][family]
                 == record["model"]["sha256"]
                 and execution["result_sha256"]
                 == record["result_receipt"]["sha256"]
                 and result[family]["status"] == "PASS"
                 and result[family]["native_reload"] == "PASS",
                 "Crossing execution and native result disagree")
        components = _components(model)
        _require(len(components) == record["component_count"],
                 "Crossing component count differs")
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
        str(path), recipe["family"], recipe["context_id"], _encoded(recipe),
        record["model"]["path"], record["model"]["sha256"],
        CROSSING_CATALOGUE_SHA256, components, frozen,
        ("Private source-qualified RH crossing context only.",
         "No physical-fit, production, export or rights acceptance."),
        _encoded(metadata),
    ) for record, recipe, components, metadata in selections)


def prepare_crossing_catalogue(path):
    """Read all eight qualified contexts or refuse before mutation."""
    try:
        return _prepare(path)
    except CatalogueChairError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            zipfile.BadZipFile, ET.ParseError, UnicodeError) as error:
        raise CatalogueChairError("Invalid crossing catalogue evidence: "
                                  + str(error)) from error


def verify_crossing_catalogue(selections):
    """Recheck the complete immutable set at the transaction boundary."""
    _require(isinstance(selections, tuple)
             and len(selections) == len(CROSSING_CONTEXT_IDS)
             and all(isinstance(item, CatalogueChair) for item in selections)
             and tuple(item.run for item in selections) == CROSSING_CONTEXT_IDS,
             "Expected the complete ordered crossing catalogue")
    _require(prepare_crossing_catalogue(selections[0].catalogue_path)
             == selections, "Crossing catalogue or prepared state changed")
