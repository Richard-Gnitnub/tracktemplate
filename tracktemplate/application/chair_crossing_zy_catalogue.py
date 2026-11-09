"""Read separate qualified RH/XO and fixed LH/TO private ZY contexts."""

from tracktemplate.application.chair_catalogue import (
    CATALOGUE_SHA256,
    CatalogueChair,
    _require,
    prepare_catalogue_chair,
)
from tracktemplate.application.chair_crossing_catalogue import _prepare_contexts


ZY_CATALOGUE_SHA256 = (
    "91009b0732e3f2f23f9f941675ab9aef392746d11f1a4334c9da50198ae07e4b"
)
ZY_CONTEXT_IDS = ("RH-X1-Z", "RH-X2-Y")


def prepare_zy_catalogue(path):
    """Read both qualified ZY contexts or refuse before any mutation."""
    return _prepare_contexts(
        path, ZY_CATALOGUE_SHA256,
        tuple((name, "ZY", 21, 33) for name in ZY_CONTEXT_IDS),
        ("Private X1-Z and X2-Y source contexts only.",
         "No physical-fit, production, export or rights acceptance."),
    )


def verify_zy_catalogue(selections):
    """Recheck both immutable selections at the transaction boundary."""
    _require(isinstance(selections, tuple)
             and len(selections) == len(ZY_CONTEXT_IDS)
             and all(isinstance(item, CatalogueChair) for item in selections)
             and tuple(item.run for item in selections) == ZY_CONTEXT_IDS,
             "Expected the complete ordered ZY catalogue")
    _require(prepare_zy_catalogue(selections[0].catalogue_path) == selections,
             "ZY catalogue or prepared state changed")


# Retained 556b LH X1-Z source recipe, not a new geometry definition.
# Source-informed GPL-3.0-or-later; see NOTICE.md and PROVENANCE.md.
_TO_ZY_MODEL_SHA256 = (
    "794a9115892a7c5e6b20021a5492705be23d8b17be3fbd78eb95c925d500af35"
)
_TO_ZY_CONTEXT_SHA256 = (
    "5f560e710eea23d350d46a8df3b739bb0b845960767a6eeb57089d82b1cafdee"
)
_TO_ZY_FIXING_SHA256 = (
    "3d25b0a0d137c257d1062f02ebf6a57c12f2ec27b94e6359316b1d5a83c9e338"
)
_TO_ZY_STATION_MM = 257.23290043721454
_TO_ZY_SOURCE_NAMES = (
    "base_plinth", "c00_WA_WA", "c01_WH_body",
    "c01_WH_bevel_negative", "c01_WH_bevel_positive", "c01_WH_grip",
    "c01_WH_stiffener", "c02_ZYSEAT_ZYSEAT", "c03_KEY_KEY",
    "c04_VA_VA", "c05_VH_body", "c05_VH_bevel_negative",
    "c05_VH_bevel_positive", "c05_VH_grip", "c05_VH_stiffener",
    "c06_ZYSEAT_ZYSEAT", "c07_KEY_KEY", "SourceFixing",
) + tuple(f"SourceFixing{index:03d}" for index in range(1, 16))
_TO_ZY_FIXING_CENTRES = (
    (-0.41181975781693214, -5.126263705621249),
    (0.9198582780827999, -5.059845436447703),
    (-0.7903732726502655, 2.4636871827252245),
    (0.5413047632494665, 2.5301054518987707),
)


def _require_turnout_zy_selection(prepared):
    """Bind one immutable LH model and its saved component/fixing order."""
    _require(isinstance(prepared, CatalogueChair),
             "Expected an immutable TO ZY selection")
    context = prepared.context
    native = prepared.metadata.get("native_record", {})
    recipe = native.get("source_recipe", {})
    fixing = native.get("fixing_proof", {})
    source = fixing.get("source_fixings", {})
    placement = source.get("placement", {})
    centres = [list(value) for value in _TO_ZY_FIXING_CENTRES]
    _require(
        prepared.label == "ZY" and prepared.run == "context-native-02"
        and prepared.catalogue_sha256 == CATALOGUE_SHA256
        and prepared.model_sha256 == _TO_ZY_MODEL_SHA256
        and isinstance(context, dict)
        and context.get("context_sha256") == _TO_ZY_CONTEXT_SHA256
        and context.get("sample_kind") == "fixture_timber_X1-Z"
        and type(context.get("station_mm")) in (int, float)
        and context["station_mm"] == _TO_ZY_STATION_MM
        and native.get("family") == "ZY"
        and native.get("status") in ("PASS", "native-components-valid")
        and native.get("native_reload") == "PASS"
        and native.get("scope") == "private-development"
        and native.get("production_ready") is False
        and recipe.get("family") == "ZY"
        and recipe.get("context_sha256") == _TO_ZY_CONTEXT_SHA256
        and recipe.get("sample_kind") == "fixture_timber_X1-Z"
        and type(recipe.get("station_mm")) in (int, float)
        and recipe["station_mm"] == _TO_ZY_STATION_MM
        and type(recipe.get("chair_code")) is int
        and recipe["chair_code"] == 21
        and recipe.get("base", {}).get("bolt_centres_twisted_mm") == centres
        and fixing.get("model_sha256") == _TO_ZY_MODEL_SHA256
        and placement.get("recipe_sha256") == _TO_ZY_FIXING_SHA256
        and placement.get("centres_source_mm") == centres
        and placement.get("basis")
        == "recipe.base.bolt_centres_twisted_mm; used once"
        and placement.get("source_twist_reapplied") is False
        and type(source.get("head_rotation_degrees")) in (int, float)
        and source["head_rotation_degrees"] == 0
        and source.get("random_export_parity") is False
        and source.get("p_bolt_status") == "NOT_APPLICABLE_SOURCE_DISPATCH"
        and tuple(item.name for item in prepared.components)
        == _TO_ZY_SOURCE_NAMES,
        "The fixed LH ZY model, context, recipe or component order differs",
    )


def prepare_turnout_zy_catalogue(path):
    """Read the one retained LH X1-Z model; refuse before any mutation."""
    prepared = prepare_catalogue_chair(path, "ZY", run="context-native-02")
    _require_turnout_zy_selection(prepared)
    return prepared


def verify_turnout_zy_catalogue(prepared):
    """Recheck all retained inputs and the complete prepared selection."""
    _require_turnout_zy_selection(prepared)
    _require(prepare_turnout_zy_catalogue(prepared.catalogue_path) == prepared,
             "TO ZY catalogue or prepared state changed")
