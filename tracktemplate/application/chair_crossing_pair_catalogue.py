"""Admit separate fixed RH/XO and LH/TO private crossing contexts."""

import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from tracktemplate.application.chair_catalogue import (
    CATALOGUE_SHA256,
    INVENTORY_SHA256,
    CatalogueBinding,
    CatalogueChair,
    CatalogueChairError,
    _components,
    _encoded,
    _json,
    _read,
    _require,
    prepare_catalogue_chair,
)
from tracktemplate.application.chair_crossing_catalogue import _prepare_contexts


CROSSING_PAIR_CATALOGUE_SHA256 = (
    "91009b0732e3f2f23f9f941675ab9aef392746d11f1a4334c9da50198ae07e4b"
)
TO_CROSSING_PROFILE_SHA256 = (
    "801a2b43f623aa292b87762970fe3f249e4fb5b3a78d3f36bcf64eb435a3e70e"
)
_SPECIFICATIONS = (
    ("RH-X4-A", "AA", 24, 42),
    ("RH-X6-C", "CD", 27, 27),
    ("RH-X7-D", "DD", 27, 33),
    ("RH-X8-E", "EF", 28, 33),
)
CROSSING_PAIR_CONTEXT_IDS = ("RH-X4-A", "RH-X6-C", "RH-X7-D", "RH-X8-E")
CROSSING_SPLIT_CONTEXT_IDS = ("RH-X3-X", "RH-X5-B")
_SPLIT_SPECIFICATIONS = (
    ("RH-X3-X", "XA", 23, 33),
    ("RH-X5-B", "BB", 26, 43),
)


def prepare_crossing_pair_catalogue(path):
    """Return exactly four frozen source-qualified contexts, in order."""
    return _prepare_contexts(
        path, CROSSING_PAIR_CATALOGUE_SHA256, _SPECIFICATIONS,
        ("Private X4-A, X6-C, X7-D and X8-E source contexts only.",
         "No physical-fit, production, export or rights acceptance."),
    )


def verify_crossing_pair_catalogue(selections):
    """Recheck the complete immutable selection before native mutation."""
    _require(isinstance(selections, tuple)
             and len(selections) == len(CROSSING_PAIR_CONTEXT_IDS)
             and all(isinstance(item, CatalogueChair) for item in selections)
             and tuple(item.run for item in selections)
             == CROSSING_PAIR_CONTEXT_IDS,
             "Expected the complete ordered AA/CD/DD/EF catalogue")
    _require(prepare_crossing_pair_catalogue(selections[0].catalogue_path)
             == selections, "Crossing catalogue or prepared state changed")


def prepare_crossing_split_catalogue(path):
    """Read the two retained XA/BB models; do not admit knuckle supports."""
    return _prepare_contexts(
        path, CROSSING_PAIR_CATALOGUE_SHA256, _SPLIT_SPECIFICATIONS,
        ("Private X3-X wing and X5-B wing/vee source supports only.",
         "XN knuckle records remain unqualified.",
         "No physical-fit, production, export or rights acceptance."),
    )


def verify_crossing_split_catalogue(selections):
    """Recheck both complete source selections before native mutation."""
    _require(isinstance(selections, tuple)
             and len(selections) == len(CROSSING_SPLIT_CONTEXT_IDS)
             and all(isinstance(item, CatalogueChair) for item in selections)
             and tuple(item.run for item in selections)
             == CROSSING_SPLIT_CONTEXT_IDS,
             "Expected the complete ordered XA/BB catalogue")
    _require(prepare_crossing_split_catalogue(selections[0].catalogue_path)
             == selections, "Crossing catalogue or prepared state changed")


# Retained 556b LH models and semantic order; no new geometry definition.
# Source-informed GPL-3.0-or-later; see NOTICE.md and PROVENANCE.md.
# Each row: timber, literal code, station, model/context/fixing hashes,
# already-twisted fixing centres, and saved semantic component order.
_TO_CROSSING_BINDINGS = (
    (
        "XA",
        (
            "X3-X",
            23,
            277.23290043721454,
            "92cc129808cf86713fdeb6bb8bb6bcd60bd2c417da5a7428fe0011b3478add5b",
            "36546313e1234ab7a926419c482c2136a20d2ab7e52a9cd74c88d9de59e7a4e6",
            "ad26a3270b2e5e015d8d2ef4133e48fb29d2b6d4b0b67c0f3399faba003ff992",
            (
                (-0.49150112037601545, -3.528662296990189),
                (0.8401769155237165, -3.462244027816643),
                (-0.8097153136842643, 2.851492699715519),
                (0.5219627222154677, 2.9179109688890654),
            ),
            (
                "base_plinth",
                "c00_WC_WC",
                "c01_WJ_body",
                "c01_WJ_bevel_negative",
                "c01_WJ_bevel_positive",
                "c01_WJ_grip",
                "c01_WJ_stiffener",
                "c02_XASEAT_XASEAT",
                "c03_KEY_KEY",
                "c04_VC_VC",
                "c05_VJ_body",
                "c05_VJ_bevel_negative",
                "c05_VJ_bevel_positive",
                "c05_VJ_grip",
                "c05_VJ_stiffener",
                "c06_XASEAT_XASEAT",
                "c07_KEY_KEY",
                "SourceFixing",
                "SourceFixing001",
                "SourceFixing002",
                "SourceFixing003",
                "SourceFixing004",
                "SourceFixing005",
                "SourceFixing006",
                "SourceFixing007",
                "SourceFixing008",
                "SourceFixing009",
                "SourceFixing010",
                "SourceFixing011",
                "SourceFixing012",
                "SourceFixing013",
                "SourceFixing014",
                "SourceFixing015",
            ),
        ),
    ),
    (
        "AA",
        (
            "X4-A",
            24,
            287.23290043721454,
            "b2b33ddc9a76a848c92bb08e1971291b6643422ead94073babe654968d274132",
            "bb2e8baaac2561b3c14b0c996b7ed24b2e8b33f6a2b6d3322d57444f8ff10753",
            "8008fe0ed7b5a14f1123f4350f7c303d774f231199cd53cc5541b1aad478e839",
            (
                (-0.49168603280261625, -3.5249548258360432),
                (0.8399920030971157, -3.458536556662497),
                (-0.859405100116341, 3.847766737318715),
                (0.4722729357833911, 3.914185006492261),
            ),
            (
                "base_plinth",
                "c00_WD_WD",
                "c01_WK_body",
                "c01_WK_bevel_negative",
                "c01_WK_bevel_positive",
                "c01_WK_grip",
                "c01_WK_stiffener",
                "c02_WP_body",
                "c02_WP_bevel_negative",
                "c02_WP_bevel_positive",
                "c02_WP_grip",
                "c02_WP_stiffener",
                "c03_AASEAT_AASEAT",
                "c04_KEY_KEY",
                "c05_VD_VD",
                "c06_VK_body",
                "c06_VK_bevel_negative",
                "c06_VK_bevel_positive",
                "c06_VK_grip",
                "c06_VK_stiffener",
                "c07_VP_body",
                "c07_VP_bevel_negative",
                "c07_VP_bevel_positive",
                "c07_VP_stiffener",
                "c08_AASEAT_AASEAT",
                "c09_KEY_KEY",
                "SourceFixing",
                "SourceFixing001",
                "SourceFixing002",
                "SourceFixing003",
                "SourceFixing004",
                "SourceFixing005",
                "SourceFixing006",
                "SourceFixing007",
                "SourceFixing008",
                "SourceFixing009",
                "SourceFixing010",
                "SourceFixing011",
                "SourceFixing012",
                "SourceFixing013",
                "SourceFixing014",
                "SourceFixing015",
            ),
        ),
    ),
    (
        "CD",
        (
            "X6-C",
            27,
            307.23290043721454,
            "d9a411078e8f070565a2358ac1e3f3e68eb504893486a327f658a44a61dd9f4a",
            "1feb5d717637761554ccbacf02247bc467fce389cd6cb9e82d2eb031d90475a1",
            "25ec147c6af88de3fa3441e16f69a6549f2e81f1015c2aab566b676d3878e914",
            (
                (-0.607723032423013, -1.1984274159990387),
                (0.723955003476719, -1.1320091468254925),
                (-0.8422858276895278, 3.5045274544370284),
                (0.4893922082102042, 3.5709457236105746),
            ),
            (
                "base_plinth",
                "c00_WG_body",
                "c00_WG_bevel_negative",
                "c00_WG_bevel_positive",
                "c00_WG_grip",
                "c01_ZYSEAT_ZYSEAT",
                "c02_VG_body",
                "c02_VG_bevel_negative",
                "c02_VG_bevel_positive",
                "c02_VG_grip",
                "c03_ZYSEAT_ZYSEAT",
                "SourceFixing",
                "SourceFixing001",
                "SourceFixing002",
                "SourceFixing003",
                "SourceFixing004",
                "SourceFixing005",
                "SourceFixing006",
                "SourceFixing007",
                "SourceFixing008",
                "SourceFixing009",
                "SourceFixing010",
                "SourceFixing011",
                "SourceFixing012",
                "SourceFixing013",
                "SourceFixing014",
                "SourceFixing015",
            ),
        ),
    ),
    (
        "DD",
        (
            "X7-D",
            27,
            317.23290043721454,
            "a53a5ddab9603a55abce8b45dcd907df653070bae71bcf4f5b212238cce86699",
            "b93b9d3dff5738f0bef39270b0a3251ea958ac583fb5045f0d443beda5ee03e4",
            "132398c9a40e57cfd19f9bd7944508db8c218a10c548c6328590ad8b5a9723ed",
            (
                (-0.607723032423013, -1.1984274159990387),
                (0.723955003476719, -1.1320091468254925),
                (-0.8919120707048136, 4.499527454437026),
                (0.43976596519491845, 4.5659457236105725),
            ),
            (
                "base_plinth",
                "c00_WG_body",
                "c00_WG_bevel_negative",
                "c00_WG_bevel_positive",
                "c00_WG_grip",
                "c01_WN_spacer",
                "c01_WN_body",
                "c02_DDSEAT_DDSEAT",
                "c03_DXSEAT_DXSEAT",
                "c04_VG_body",
                "c04_VG_bevel_negative",
                "c04_VG_bevel_positive",
                "c04_VG_grip",
                "c05_VN_spacer",
                "c05_VN_body",
                "c06_DDSEAT_DDSEAT",
                "c07_DXSEAT_DXSEAT",
                "SourceFixing",
                "SourceFixing001",
                "SourceFixing002",
                "SourceFixing003",
                "SourceFixing004",
                "SourceFixing005",
                "SourceFixing006",
                "SourceFixing007",
                "SourceFixing008",
                "SourceFixing009",
                "SourceFixing010",
                "SourceFixing011",
                "SourceFixing012",
                "SourceFixing013",
                "SourceFixing014",
                "SourceFixing015",
            ),
        ),
    ),
)


def _require_turnout_crossing_selection(prepared, family):
    """Require the exact immutable model, recipe and saved component order."""
    _require(isinstance(prepared, CatalogueChair),
             "Expected an immutable TO crossing selection")
    specifications = dict(_TO_CROSSING_BINDINGS)
    _require(family in specifications, "Unsupported TO crossing family")
    (timber, code, station, model_hash, context_hash, fixing_hash,
     fixing_centres, names) = specifications[family]
    context = prepared.context
    native = prepared.metadata.get("native_record", {})
    recipe = native.get("source_recipe", {})
    fixing = native.get("fixing_proof", {})
    source = fixing.get("source_fixings", {})
    placement = source.get("placement", {})
    centres = [list(value) for value in fixing_centres]
    sample = "fixture_timber_" + timber
    _require(
        prepared.label == family and prepared.run == "context-native-02"
        and prepared.catalogue_sha256 in (
            CATALOGUE_SHA256, TO_CROSSING_PROFILE_SHA256,
        )
        and prepared.model_sha256 == model_hash
        and isinstance(context, dict)
        and context.get("context_sha256") == context_hash
        and context.get("sample_kind") == sample
        and type(context.get("station_mm")) in (int, float)
        and context["station_mm"] == station
        and native.get("family") == family
        and native.get("status") in ("PASS", "native-components-valid")
        and native.get("native_reload") == "PASS"
        and native.get("scope") == "private-development"
        and native.get("production_ready") is False
        and recipe.get("family") == family
        and recipe.get("context_sha256") == context_hash
        and recipe.get("sample_kind") == sample
        and type(recipe.get("station_mm")) in (int, float)
        and recipe["station_mm"] == station
        and type(recipe.get("chair_code")) is int
        and recipe["chair_code"] == code
        and recipe.get("base", {}).get("bolt_centres_twisted_mm") == centres
        and fixing.get("model_sha256") == model_hash
        and placement.get("recipe_sha256") == fixing_hash
        and placement.get("centres_source_mm") == centres
        and placement.get("basis")
        == "recipe.base.bolt_centres_twisted_mm; used once"
        and placement.get("source_twist_reapplied") is False
        and type(source.get("head_rotation_degrees")) in (int, float)
        and source["head_rotation_degrees"] == 0
        and source.get("random_export_parity") is False
        and source.get("p_bolt_status") == "NOT_APPLICABLE_SOURCE_DISPATCH"
        and tuple(item.name for item in prepared.components) == names,
        "The fixed LH crossing model, context, fixing or component order differs",
    )


def _profile_object(value, keys):
    """Reject unknown or absent fields before using projected metadata."""
    _require(isinstance(value, dict) and set(value) == set(keys.split()),
             "Fixed TO profile object fields differ: " + keys)
    return value


def _profile_strings(value):
    _require(isinstance(value, list) and value
             and all(isinstance(item, str) and item.strip() for item in value),
             "Fixed TO profile requires nonempty text entries")


def _profile_digest(value):
    _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value),
             "Fixed TO profile requires a SHA256 digest")


def _profile_centres(value):
    _require(isinstance(value, list) and len(value) == 4
             and all(isinstance(point, list) and len(point) == 2
                     and all(type(number) in (int, float) for number in point)
                     for point in value),
             "Fixed TO profile requires four numeric fixing centres")


def _profile_provenance(manifest, families):
    """Validate lineage links without treating historical text as authority."""
    authority = _profile_object(
        manifest["authority"], "acceptance rights_cleared "
        "native_execution_authorized production_accepted "
        "public_transfer_authorized",
    )
    _require(authority["acceptance"] == "NO_NEW_ACCEPTANCE"
             and all(value is False for key, value in authority.items()
                     if key != "acceptance"),
             "Fixed TO profile gives no additional authority")
    lineage = _profile_object(
        manifest["original_lineage"], "catalogue execution_plan_sha256 "
        "execution_receipt recipe_file result_and_receipt "
        "source_archive_sha256 source_inventory source_members",
    )
    for name in ("catalogue", "execution_receipt", "recipe_file",
                 "result_and_receipt", "source_inventory"):
        record = _profile_object(lineage[name], "bytes sha256")
        _require(type(record["bytes"]) is int and record["bytes"] > 0,
                 "Original lineage byte count must be positive")
        _profile_digest(record["sha256"])
    _require(lineage["catalogue"]["sha256"] == CATALOGUE_SHA256
             and lineage["source_inventory"]["sha256"] == INVENTORY_SHA256,
             "Original catalogue or source inventory identity differs")
    for name in ("execution_plan_sha256", "source_archive_sha256"):
        _profile_digest(lineage[name])
    members = _profile_object(
        lineage["source_members"], "chairs_unit.pas dxf_unit.pas licence.txt "
        "math_unit.pas pad_unit.pas",
    )
    for digest in members.values():
        _profile_digest(digest)
    execution = _profile_object(
        manifest["historical_execution"], "status execution_plan_sha256 "
        "result_sha256 model_hashes freecad_version occt_version "
        "python_version qualified_runtime",
    )
    _require(execution["status"] == "PASS"
             and execution["execution_plan_sha256"]
             == lineage["execution_plan_sha256"]
             and execution["result_sha256"]
             == lineage["result_and_receipt"]["sha256"],
             "Historical execution lineage differs")
    _profile_object(execution["model_hashes"], " ".join(families))
    _profile_strings(execution["freecad_version"])
    _require(len(execution["freecad_version"]) == 8,
             "Historical FreeCAD version fields differ")
    for name in ("occt_version", "python_version", "qualified_runtime"):
        _profile_strings([execution[name]])
    return execution["model_hashes"]


def _profile_family(entry, family, specification):
    """Check the exact projection shape; the shared qualifier checks values."""
    timber, code, station, model_hash, context_hash, _, _, names = specification
    _profile_object(entry, "label run model context component_names "
                    "limitations metadata")
    _require(entry["label"] == family and entry["run"] == "context-native-02"
             and entry["component_names"] == list(names),
             "Fixed TO profile family, run or component order differs")
    _profile_strings(entry["limitations"])
    model = _profile_object(entry["model"], "member bytes sha256")
    # Compare the literal spelling before Path can normalize aliases.
    _require(model["member"] == "models/" + family + ".FCStd"
             and type(model["bytes"]) is int and model["bytes"] > 0
             and model["sha256"] == model_hash,
             "Fixed TO profile model identity or member differs")
    context = _profile_object(entry["context"], "context_id context_sha256 "
                              "frame sample_id sample_kind station_mm timber_id")
    _require(context["context_id"] is None and context["sample_id"] is None
             and context["timber_id"] is None
             and context["context_sha256"] == context_hash
             and context["sample_kind"] == "fixture_timber_" + timber
             and type(context["station_mm"]) in (int, float)
             and context["station_mm"] == station
             and context["frame"] == (
                 "chair-local model mm, X along main rail, rail-top Z=0; "
                 "crossing origin at main crossing rail gauge face"
             ), "Fixed TO profile context differs")
    metadata = _profile_object(
        entry["metadata"], "acceptance intended_uses native_record "
        "phase_acceptance production_geometry_authorized project_status "
        "reference_admission source_codes source_explicit_nyi source_inventory",
    )
    _require(metadata["acceptance"] == "NO_NEW_ACCEPTANCE"
             and metadata["intended_uses"] == ["private-development"]
             and metadata["phase_acceptance"] == "UNCHANGED_PHASE_9B_3_OF_6"
             and metadata["production_geometry_authorized"] is False
             and metadata["project_status"] == "reference-only"
             and isinstance(metadata["source_codes"], list)
             and len(metadata["source_codes"]) == 1
             and type(metadata["source_codes"][0]) is int
             and metadata["source_codes"] == [code],
             "Fixed TO profile provenance or authority differs")
    for name in ("reference_admission", "source_inventory"):
        _profile_strings([metadata[name]])
    _profile_strings(metadata["source_explicit_nyi"])
    native = _profile_object(
        metadata["native_record"], "family status native_reload scope "
        "production_ready physical_fit fused_casting source_recipe fixing_proof",
    )
    _require(native["physical_fit"] == "NOT_PROVED"
             and native["fused_casting"] == "NOT_PROVED",
             "Fixed TO profile does not prove fit or fused geometry")
    recipe = _profile_object(native["source_recipe"], "family chair_code "
                             "context_sha256 sample_kind station_mm base")
    base = _profile_object(recipe["base"], "bolt_centres_twisted_mm")
    _profile_centres(base["bolt_centres_twisted_mm"])
    fixing = _profile_object(native["fixing_proof"], "model_sha256 source_fixings")
    source = _profile_object(fixing["source_fixings"], "head_rotation_degrees "
                             "p_bolt_status random_export_parity placement")
    placement = _profile_object(source["placement"], "basis recipe_sha256 "
                                "centres_source_mm source_twist_reapplied")
    _profile_centres(placement["centres_source_mm"])


def _read_turnout_crossing_profile(path, data):
    """Read the pinned local projection, without acquiring execution rights."""
    manifest = _profile_object(
        _json(data), "schema_version profile status authority scope families "
        "original_lineage historical_execution limitations",
    )
    _require(type(manifest["schema_version"]) is int
             and manifest["schema_version"] == 1
             and manifest["profile"]
             == "TO-001-XA-AA-CD-DD-fixed-reference-candidate-v1"
             and manifest["status"] == "LOCAL_CANDIDATE_NOT_ADMITTED",
             "Unsupported fixed TO profile schema or status")
    families = tuple(family for family, _spec in _TO_CROSSING_BINDINGS)
    scope = _profile_object(manifest["scope"], "component_count family_count "
                            "family_order source_position_count")
    for name, count in (("component_count", 135), ("family_count", 4),
                        ("source_position_count", 8)):
        _require(type(scope[name]) is int and scope[name] == count,
                 "Fixed TO profile scope count differs")
    _require(scope["family_order"] == list(families)
             and isinstance(manifest["families"], list)
             and len(manifest["families"]) == len(families),
             "Fixed TO profile family scope differs")
    _profile_strings(manifest["limitations"])
    model_hashes = _profile_provenance(manifest, families)
    inputs = []
    bindings = [CatalogueBinding(str(path), TO_CROSSING_PROFILE_SHA256)]
    # Bind all four files before interpreting any model archive.
    for entry, (family, specification) in zip(
        manifest["families"], _TO_CROSSING_BINDINGS,
    ):
        _profile_family(entry, family, specification)
        model = entry["model"]
        _require(model_hashes[family] == model["sha256"],
                 "Historical model hash differs")
        model_path = path.parent / model["member"]
        model_data = _read(model_path)
        _require(len(model_data) == model["bytes"]
                 and hashlib.sha256(model_data).hexdigest() == model["sha256"],
                 "Fixed TO profile model bytes changed")
        bindings.append(CatalogueBinding(str(model_path), model["sha256"]))
        inputs.append((entry, model_path, model_data))
    result = []
    for entry, model_path, model_data in inputs:
        prepared = CatalogueChair(
            catalogue_path=str(path), label=entry["label"], run=entry["run"],
            context_json=_encoded(entry["context"]), model_path=str(model_path),
            model_sha256=entry["model"]["sha256"],
            catalogue_sha256=TO_CROSSING_PROFILE_SHA256,
            components=_components(model_data), bindings=tuple(bindings),
            limitations=tuple(entry["limitations"]),
            metadata_json=_encoded(entry["metadata"]),
        )
        _require_turnout_crossing_selection(prepared, entry["label"])
        result.append(prepared)
    return tuple(result)


def prepare_turnout_crossing_catalogue(path):
    """Dispatch only the original catalogue or the pinned four-family profile."""
    try:
        source = Path(path).absolute()
        data = _read(source)
        digest = hashlib.sha256(data).hexdigest()
        _require(digest in (CATALOGUE_SHA256, TO_CROSSING_PROFILE_SHA256),
                 "Unrecognized fixed TO crossing catalogue identity")
        if digest == TO_CROSSING_PROFILE_SHA256:
            return _read_turnout_crossing_profile(source, data)
    except CatalogueChairError:
        raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            zipfile.BadZipFile, ET.ParseError) as exc:
        raise CatalogueChairError("Cannot read fixed TO crossing profile") from exc
    result = []
    for family, _specification in _TO_CROSSING_BINDINGS:
        prepared = prepare_catalogue_chair(
            path, family, run="context-native-02",
        )
        _require_turnout_crossing_selection(prepared, family)
        result.append(prepared)
    return tuple(result)


def verify_turnout_crossing_catalogue(prepared):
    """Re-read the complete four-family selection before native commit."""
    families = tuple(family for family, _spec in _TO_CROSSING_BINDINGS)
    _require(isinstance(prepared, tuple) and len(prepared) == len(families),
             "Expected the complete ordered LH XA/AA/CD/DD catalogue")
    for family, selection in zip(families, prepared):
        _require_turnout_crossing_selection(selection, family)
    _require(prepare_turnout_crossing_catalogue(prepared[0].catalogue_path)
             == prepared, "TO crossing catalogue or prepared state changed")
