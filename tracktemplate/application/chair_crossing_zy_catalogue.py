"""Read only the two qualified private ZY crossing contexts."""

from tracktemplate.application.chair_catalogue import CatalogueChair, _require
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
