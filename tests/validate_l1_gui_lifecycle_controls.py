"""Exercise diagnostic admission without FreeCAD, Qt or hosted execution."""

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tools import hosted_l1_gui_validation as gui  # noqa: E402
import validate_hosted_l1_gui_controls as prior  # noqa: E402


def diagnostic_authority():
    record = prior.authority()
    record["gui_entry_sha256"] = gui.DIAGNOSTIC_ENTRY_SHA256
    ready = record["gui_readiness_review"]
    ready.update(
        source_commit=gui.DIAGNOSTIC_BASE,
        gui_entry_sha256=gui.DIAGNOSTIC_ENTRY_SHA256,
        run_id=41297405795,
        evidence_sha256=gui.DIAGNOSTIC_READINESS_EVIDENCE,
        result_review_sha256=gui.DIAGNOSTIC_READINESS_REVIEW,
        preservation_review_sha256=gui.DIAGNOSTIC_READINESS_PRESERVATION,
    )
    record["lifecycle_diagnostic"] = {
        "scope_id": gui.DIAGNOSTIC_SCOPE,
        "execution_authorized": True,
        "preparation_review": "PASS",
        "preparation_review_sha256": "1" * 64,
        "failed_run_id": 41298217983,
        "baseline_commit": gui.DIAGNOSTIC_BASE,
        "baseline_controls": copy.deepcopy(ready["control_files_sha256"]),
        "control_files_sha256": {
            name: "2" * 64 for name in gui.DIAGNOSTIC_FILES
        },
        "automatic_retry": False,
        "product_changes": False,
    }
    return record


class DiagnosticControls(unittest.TestCase):
    def test_explicit_mode_and_separate_preparation_are_required(self):
        record = diagnostic_authority()
        environ = dict(prior.environment(), L1_LIFECYCLE_DIAGNOSTIC="true")
        gui.validate_authority(record, environ)
        for key, value in (
            ("execution_authorized", False),
            ("preparation_review", "PENDING"),
            ("preparation_review_sha256", "missing"),
            ("failed_run_id", 41),
            ("baseline_commit", "a" * 40),
            ("baseline_controls", {}),
            ("control_files_sha256", {}),
            ("automatic_retry", True),
            ("product_changes", True),
        ):
            bad = copy.deepcopy(record)
            bad["lifecycle_diagnostic"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                gui.validate_authority(bad, environ)
        with self.assertRaises(ValueError):
            gui.validate_authority(record, prior.environment())
        with self.assertRaises(ValueError):
            gui.validate_authority(prior.authority(), environ)

    def test_prior_readiness_is_exact_and_not_ordinary_gui_admission(self):
        good = diagnostic_authority()
        environ = dict(prior.environment(), L1_LIFECYCLE_DIAGNOSTIC="true")
        for key, value in (
            ("run_id", 41292901538), ("source_commit", "a" * 40),
            ("result_review_sha256", "0" * 64),
            ("preservation_review_sha256", "0" * 64),
            ("evidence_sha256", "0" * 64),
            ("gui_entry_sha256", "0" * 64),
        ):
            bad = copy.deepcopy(good)
            bad["gui_readiness_review"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                gui.validate_authority(bad, environ)
        ordinary = copy.deepcopy(good)
        ordinary.pop("lifecycle_diagnostic")
        with self.assertRaises(ValueError):
            gui.validate_authority(ordinary, prior.environment())
        for value in ("TRUE", "1", "", "unexpected"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                gui.diagnostic_enabled({"L1_LIFECYCLE_DIAGNOSTIC": value})

    def test_macro_installs_observer_only_for_admitted_control(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled), tempfile.TemporaryDirectory() as d:
                work = Path(d)
                (work / "evidence").mkdir()
                record = diagnostic_authority() if enabled else prior.authority()
                (work / "control.json").write_text(json.dumps(record))
                environ = {"L1_LIFECYCLE_DIAGNOSTIC": str(enabled).lower()}
                with patch.dict(gui.os.environ, environ):
                    macro = gui.write_gui_macro(work).read_text()
                self.assertEqual("l1_gui_lifecycle_observer" in macro, enabled)
                self.assertIn("hosted_l1_gui_suite.start()", macro)
                if enabled:
                    self.assertLess(macro.index("observer.install("),
                                    macro.index("hosted_l1_gui_suite.start()"))

    def test_frozen_bytes_and_complete_change_scope_are_checked(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            frozen = root / "fixture.py"
            observer = root / "observer.py"
            frozen.write_bytes(b"original fixture\n")
            observer.write_bytes(b"reviewed observer\n")
            record = {"lifecycle_diagnostic": {
                "baseline_controls": {
                    "fixture.py": hashlib.sha256(frozen.read_bytes()).hexdigest(),
                },
                "control_files_sha256": {
                    "observer.py": hashlib.sha256(observer.read_bytes()).hexdigest(),
                },
            }}
            with (patch.object(gui, "ROOT", root),
                  patch.object(gui, "DIAGNOSTIC_FILES", ("observer.py",)),
                  patch.object(gui.native, "command", return_value="observer.py")
                  as changed,
                  patch.object(gui.subprocess, "run", return_value=
                               SimpleNamespace(stdout=b"original fixture\n"))):
                gui.validate_diagnostic_source(record)
                frozen.write_bytes(b"modified fixture\n")
                with self.assertRaisesRegex(ValueError, "frozen control"):
                    gui.validate_diagnostic_source(record)
                frozen.write_bytes(b"original fixture\n")
                observer.write_bytes(b"unreviewed observer\n")
                with self.assertRaisesRegex(ValueError, "observer control"):
                    gui.validate_diagnostic_source(record)
                changed.return_value = "product.py"
                with self.assertRaisesRegex(ValueError, "frozen source"):
                    gui.validate_diagnostic_source(record)

    def test_complete_diagnostics_do_not_upgrade_product_failure(self):
        with tempfile.TemporaryDirectory() as d:
            work = Path(d)
            for product_status in ("PASS", "FAIL"):
                for diagnostic_status in ("COMPLETE", "INCOMPLETE"):
                    with self.subTest(product=product_status,
                                      diagnostic=diagnostic_status):
                        assessment = {"status": product_status,
                                      "classification": "original",
                                      "error": "original traceback"}
                        result = {"status": diagnostic_status}
                        gui.record_diagnostic_assessment(
                            work, assessment, assessor=lambda _path: result,
                        )
                        self.assertEqual(assessment["error"],
                                         "original traceback")
                        expected = (product_status if diagnostic_status
                                    == "COMPLETE" else "FAIL")
                        self.assertEqual(assessment["status"], expected)
                        if expected == "PASS":
                            self.assertEqual(assessment["classification"],
                                             "DIAGNOSTIC_NON_REPRODUCTION")
            assessment = {"status": "FAIL", "classification": "original"}

            for error_type in (OSError, RuntimeError):
                def unreadable(_path):
                    raise error_type("diagnostic evidence unreadable")

                gui.record_diagnostic_assessment(work, assessment,
                                                 assessor=unreadable)
                self.assertEqual(assessment["status"], "FAIL")
                self.assertEqual(assessment["lifecycle_diagnostic"]["status"],
                                 "INCOMPLETE")
            with patch("builtins.__import__", side_effect=ImportError("observer")):
                gui.record_diagnostic_assessment(work, assessment)
            self.assertEqual(assessment["lifecycle_diagnostic"]["status"],
                             "INCOMPLETE")

    def test_public_result_does_not_claim_gui_qualification(self):
        for success in (False, True):
            with self.subTest(success=success), tempfile.TemporaryDirectory() as d:
                work = Path(d)
                evidence = work / "evidence"
                evidence.mkdir()
                records = {
                    "publication.json": {"primary": True, "errors": []},
                    "assessment.json": {"status": "PASS" if success else "FAIL"},
                    "finalization.json": {"cleanup": True,
                                          "staging_inputs_removed": list(range(10))},
                    "display-finalization.json": {"cleanup": True},
                    "gui-staging-cleanup.json": {
                        "copied_input_absent": True,
                        "display_cookie_absent": True,
                    },
                }
                for name, record in records.items():
                    (evidence / name).write_text(json.dumps(record))
                environ = dict(prior.environment(),
                               L1_LIFECYCLE_DIAGNOSTIC="true",
                               L1_PUBLICATION="success")
                with (patch.dict(gui.os.environ, environ, clear=True),
                      patch.object(gui.native, "verify_artifact", return_value={} )):
                    self.assertEqual(gui.complete(work, work / "public"),
                                     0 if success else 1)
                summary = json.loads((work / "public/summary.json").read_text())
                self.assertEqual(summary["scope_id"], gui.DIAGNOSTIC_SCOPE)
                self.assertTrue(summary["diagnostic_only"])
                self.assertEqual(summary["outcome"],
                                 "NON_REPRODUCTION" if success else "INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
