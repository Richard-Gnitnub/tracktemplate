"""Admit four qualified AA/CD/DD/EF contexts for private XO-001 use."""

from tracktemplate.application.chair_catalogue import CatalogueChair, _require
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
