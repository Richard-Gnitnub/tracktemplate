"""Admit separate fixed RH/XO and LH/TO private crossing contexts."""

from tracktemplate.application.chair_catalogue import (
    CATALOGUE_SHA256,
    CatalogueChair,
    _require,
    prepare_catalogue_chair,
)
from tracktemplate.application.chair_crossing_catalogue import _prepare_contexts


CROSSING_PAIR_CATALOGUE_SHA256 = (
    "91009b0732e3f2f23f9f941675ab9aef392746d11f1a4334c9da50198ae07e4b"
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
        and prepared.catalogue_sha256 == CATALOGUE_SHA256
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


def prepare_turnout_crossing_catalogue(path):
    """Read exactly the four retained LH XA/AA/CD/DD selections, in order."""
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
