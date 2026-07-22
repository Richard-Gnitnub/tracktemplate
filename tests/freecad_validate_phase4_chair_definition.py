#!/usr/bin/env python3
"""Exercise the Phase 4 chair package contract in qualified FreeCAD."""

import pathlib
import sys

import FreeCAD as App


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api, bootstrap  # noqa: E402


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "chair-definition-v1-contract.json"
MANIFEST_PATH = (
    ROOT
    / "tests"
    / "fixtures"
    / "chair-definition-v1-contract.dependency-manifest.json"
)


def _document_state():
    return {
        name: len(document.Objects)
        for name, document in sorted(App.listDocuments().items())
    }


before = _document_state()
qualification = bootstrap.require_qualified_runtime(
    ROOT / "reference" / "contracts" / "phase1-compatibility.json"
)
fixture_text = FIXTURE_PATH.read_text(encoding="utf-8")
manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
package = api.chair_definition_package_from_json(fixture_text, manifest_text)
encoded = api.chair_definition_package_to_json(package)
reopened = api.chair_definition_package_from_json(encoded, manifest_text)
status = api.chair_definition_package_status(reopened, manifest_text)
after = _document_state()

assert qualification["compatibility_evaluation"]["matched_profile_id"] == (
    "linux-x86_64-flatpak-freecad-1.1.1"
)
assert reopened == package
assert api.chair_definition_package_to_json(reopened) == encoded
assert status["status"] == "blocked"
assert status["findings"] == ("phase9-production-admission-not-enabled",)
assert status["production_geometry_authorized"] is False
assert status["document_mutation_authorized"] is False
assert status["filesystem_mutation_authorized"] is False
assert before == after, "chair package validation changed FreeCAD document state"

print("Phase 4 chair-definition FreeCAD compatibility validation passed")
