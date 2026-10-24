"""Read the frozen private RH switch-block context supplement.

The original catalogue remains unchanged. Admission requires the exact
reviewed supplement, native qualification and independent source evidence.
No caller-provided digest, source execution or document restoration is
supported. These derived BReps supply no physical-fit or rights acceptance.
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


# Exact private native-03 qualification and independent twenty-position
# source comparison. No arbitrary supplement or caller hash is admitted.
PAIRED_CATALOGUE_SHA256 = (
    "cc2f17536cd98f552b12ee610b70e5389b3154d2d8b13ce828c23b0fe7e55738"
)
CONTEXT_IDS = (
    "RH-MS-1P", "RH-MS-2P", "RH-MS-3P", "RH-MS-4P", "RH-MS-5P",
    "RH-TS-1P", "RH-TS-2P", "RH-TS-3P", "RH-TS-4P", "RH-TS-5P",
)


def _prepare(path):
    path = Path(path).absolute()
    data = _read(path)
    _require(hashlib.sha256(data).hexdigest() == PAIRED_CATALOGUE_SHA256,
             "Paired supplement differs from the reviewed private evidence")
    manifest = _json(data)
    _require(manifest["contract_id"]
             == "tracktemplate.private-paired-catalogue.v1"
             and manifest["project_status"] == "reference-only"
             and manifest["intended_uses"] == ["private-development"]
             and manifest["production_accepted"] is False
             and manifest["rights_cleared"] is False,
             "Unsupported paired catalogue scope")
    root = Path(manifest["inventory_root"])
    _require(root.is_absolute() and root.resolve() == root
             and path.is_relative_to(root), "Invalid paired inventory root")
    bindings = {str(path): PAIRED_CATALOGUE_SHA256}
    qualification = _json(_bound(manifest["qualification"], root, bindings))
    oracle = _json(_bound(manifest["source_oracle"], root, bindings))
    host = _json(_bound(manifest["canonical_hosts"], root, bindings))
    _require(qualification["status"] == "PASS"
             and qualification["documents_closed"] is True
             and qualification["production_accepted"] is False
             and qualification["physical_fit"] == "NOT_PROVED"
             and all(qualification.get(key) for key in (
                 "qualified_runtime", "freecad_version", "occt_version",
                 "python_version",
             )), "Paired native qualification is incomplete")
    _require(oracle["status"] == "PASS"
             and oracle["context_count"] == 10
             and oracle["position_count"] == 20,
             "Independent paired source qualification is incomplete")
    _require(hashlib.sha256(_encoded(host["hosts"]).encode()).hexdigest()
             == manifest["host_context_sha256"],
             "Canonical host evidence differs")
    records = qualification["contexts"]
    _require(set(records) == set(CONTEXT_IDS),
             "All ten paired contexts are required")
    selections = []
    for context_id in CONTEXT_IDS:
        record = records[context_id]
        family = context_id.rsplit("-", 1)[1]
        recipe = record["source_recipe"]
        source = recipe["context"]
        _require(record["status"] == "PASS"
                 and record["native_reload"] == "PASS"
                 and record["fixing_proof"] == "PASS"
                 and record["family"] == recipe["family"] == family
                 and recipe["context_id"] == context_id
                 and source["hand_i"] == -1
                 and source["keq_rad"] == 0
                 and source["side"] == context_id.split("-")[1]
                 and recipe["sample_kind"] == "fixture_timber",
                 "Paired context identity or qualification differs")
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
                 "Paired validation-time artifact identity differs")
        components = _components(model)
        _require(tuple(item.name for item in components)
                 == tuple(item["name"] for item in record["components"])
                 and len(components) == record["component_count"],
                 "Paired native component identities differ")
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
    # Every selection retains all consumed bindings. Revalidation therefore
    # cannot admit a partial ten-context set after a late source change.
    frozen_bindings = tuple(CatalogueBinding(name, digest)
                            for name, digest in sorted(bindings.items()))
    return tuple(CatalogueChair(
        str(path), recipe["family"], recipe["context_id"], _encoded(recipe),
        record["model"]["path"], record["model"]["sha256"],
        PAIRED_CATALOGUE_SHA256, components, frozen_bindings,
        ("Private source-qualified RH paired context only.",
         "No physical-fit, keying, production, export or rights acceptance."),
        _encoded(metadata),
    ) for record, recipe, components, metadata in selections)


def prepare_paired_catalogue(path):
    """Read all ten qualified private contexts or refuse without mutation."""
    try:
        return _prepare(path)
    except CatalogueChairError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            zipfile.BadZipFile, ET.ParseError, UnicodeError) as error:
        raise CatalogueChairError("Invalid paired catalogue evidence: "
                                  + str(error)) from error


def verify_paired_sources(prepared):
    """Revalidate the complete frozen supplement and one derived selection."""
    _require(isinstance(prepared, CatalogueChair)
             and prepared.run in CONTEXT_IDS,
             "Expected a qualified paired selection")
    current = {item.run: item
               for item in prepare_paired_catalogue(prepared.catalogue_path)}
    _require(current[prepared.run] == prepared,
             "Paired source or prepared state changed")


def verify_paired_catalogue(selections):
    """Recheck a complete prepared set once at the transaction boundary."""
    _require(isinstance(selections, tuple)
             and len(selections) == len(CONTEXT_IDS)
             and all(isinstance(item, CatalogueChair) for item in selections)
             and tuple(item.run for item in selections) == CONTEXT_IDS,
             "Expected the complete ordered paired catalogue")
    _require(prepare_paired_catalogue(selections[0].catalogue_path) == selections,
             "Paired catalogue or prepared state changed")
