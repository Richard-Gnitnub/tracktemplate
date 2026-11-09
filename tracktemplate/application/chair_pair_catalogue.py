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


# Fixed reference-only 556b LH main-side model and source-recipe bindings.
# GPL-3.0-or-later source-informed values; see NOTICE.md. No key-policy
# or physical-fit acceptance follows from this private selection.
_TO_MAIN_BLOCK_BINDINGS = (
    ("1P", (
        "f91a528e232fd8eb80ae55745f94bed588342c7047f812840a6704c42239b693",
        "30481fd010f5f68f0d6f4b812d0b76f9b3444cc5aa1bc2cda6bb74ed63d1299f",
        "ff065519fc2db613ac92d124ea5dd426969d5457ac93880d3c9e09ea59326d43",
        69.66666666666666, "S8",
    )),
    ("2P", (
        "bcdcf82ca8ade6c5470ad8dcde7edbe792e4af436de1e03ea51b197c41c87f93",
        "d9ba7b95d4fc8be8e4b9a6d58941d67bb8413e4783d228436e6f7f2848b8bf73",
        "65037d96776b6bd452d2199ad7f8bffd2a339f3a694a4faf2d841f969fa4bd55",
        79.66666666666666, "S9",
    )),
    ("3P", (
        "8ba16c037c8f404f5546a4065f9f4630529a9bd7325b7b9a6a31f3f035a9720f",
        "51cefb0ba8214d7f8672ed5ed88bfd608217a0b66e094ab9fc54a88aa8f6223b",
        "612dec4f8021c12f836adc4a3325c7b170c87c5571d6b9a667e30ed1d99799e5",
        89.66666666666666, "S10",
    )),
    ("4P", (
        "66ddcfa5b3b64594cd2695b4103f4861ddf971640e1fbb31e11422c20cad97ac",
        "f402cf4fca91b0fb64a6b72eb1b321debc4cb8c1dacb2ac640a33fbba7f039f5",
        "e92fce654e3e2d48c0a5ebdb2f1bc134fd5901bb7a37d42879f929b03a2c0b35",
        99.66666666666666, "S11",
    )),
    ("5P", (
        "ddbd7eba4838648d515e7d046328b713ee59884f1cbeae374699396bdbe7bee0",
        "0e2fefc4cc31b67678e962ffb12f03d54a5ad3c9613145a0484eaf259a10e94c",
        "fee800faad82ff38f14225cbf7beb22b24778aa8b86c519d8fbbba8805610d51",
        109.66666666666666, "S12",
    )),
)


def _turnout_block_component_names(family):
    """Bind saved semantic order, including four indexed fixing groups."""
    common = (
        "base_plinth",
        "c00_SCOUTJAW_SCOUTJAW",
        "c01_SCINJAW_body",
        "c01_SCINJAW_bevel_negative",
        "c01_SCINJAW_bevel_positive",
        "c01_SCINJAW_grip",
        "c01_SCINJAW_stiffener",
        "c02_SCCCSEAT_SCCCSEAT",
        "c03_KEY_KEY",
    )
    tail = (
        (
            "c04_MM_body",
            "c04_MM_bevel_negative",
            "c04_MM_bevel_positive",
            "c04_MM_grip",
            "c04_MM_stiffener",
            "c05_PLR1SEAT_PLR1SEAT",
        )
        if family in ("1P", "2P")
        else (
            "c04_MN_body",
            "c04_MN_stiffener",
            "c05_MH_body",
            "c05_MH_bevel_negative",
            "c05_MH_bevel_positive",
            "c05_MH_grip",
            "c06_PLR3SEAT_PLR3SEAT",
            "c07_KEY_KEY",
        )
    )
    return (
        common
        + tail
        + ("SourceFixing",)
        + tuple(f"SourceFixing{index:03d}" for index in range(1, 16))
    )


def _verify_turnout_block_selection(prepared, family, *, require):
    """Admit only the retained model, context and once-applied fixing recipe."""
    bindings = dict(_TO_MAIN_BLOCK_BINDINGS)
    require(family in bindings, "unknown TO block family")
    model_hash, context_hash, fixing_hash, station, timber = bindings[family]
    number = int(family[0])
    context = prepared.context
    record = prepared.metadata.get("native_record", {})
    recipe = record.get("source_recipe", {})
    fixing = record.get("fixing_proof", {})
    source_fixings = fixing.get("source_fixings", {})
    placement = source_fixings.get("placement", {})
    require(
        prepared.label == family
        and prepared.run == "context-native-02"
        and prepared.model_sha256 == model_hash
        and isinstance(context, dict)
        and context.get("context_sha256") == context_hash
        and context.get("station_mm") == station
        and context.get("timber_id") == timber
        and context.get("sample_kind") == "fixture_timber"
        and record.get("family") == family
        and recipe.get("family") == family
        and recipe.get("context_sha256") == context_hash
        and recipe.get("station_mm") == station
        and recipe.get("timber_id") == timber
        and type(recipe.get("chair_code")) is int
        and recipe["chair_code"] == (11 if number <= 2 else 12)
        and fixing.get("model_sha256") == model_hash
        and placement.get("recipe_sha256") == fixing_hash
        and placement.get("source_twist_reapplied") is False
        and type(source_fixings.get("head_rotation_degrees")) in (int, float)
        and source_fixings["head_rotation_degrees"] == 0
        and source_fixings.get("random_export_parity") is False
        and source_fixings.get("p_bolt_status")
        == "NOT_APPLICABLE_SOURCE_DISPATCH"
        and tuple(item.name for item in prepared.components)
        == _turnout_block_component_names(family),
        "the fixed LH block model, context, recipe or component order differs",
    )
