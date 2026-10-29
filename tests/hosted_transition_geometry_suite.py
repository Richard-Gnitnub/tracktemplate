"""Expose the unchanged transition validator to FreeCAD's unittest runner."""

import json
from pathlib import Path
import runpy
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class TestTransitionGeometry(unittest.TestCase):
    """Run one existing native validator, with no work during import."""

    def test_transition(self):
        from tracktemplate import bootstrap

        self.assertEqual(sys.flags.optimize, 0, "Assertions must be enabled")
        report = bootstrap.require_qualified_runtime(
            ROOT / "reference/contracts/phase1-compatibility.json",
        )
        self.assertEqual(
            report["compatibility_evaluation"]["matched_profile_id"],
            "linux-x86_64-flatpak-freecad-1.1.4-"
            "py3.13.15-qt6.11.2-coin4.0.10",
        )
        print("TRACKTEMPLATE_HOSTED_RUNTIME=" + json.dumps(report), flush=True)
        runpy.run_path(str(
            ROOT / "tests/freecad_validate_phase6_transition_exact_geometry.py"
        ))
