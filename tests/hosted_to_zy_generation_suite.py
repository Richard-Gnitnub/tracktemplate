"""Import-safe entry for the single approved X2 construction workload.

Only the hosted controller may invoke one named case in a fresh qualified
FreeCAD process. The source generator remains an exact approved input.
"""

import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import traceback
import unittest


class ZyGeneration(unittest.TestCase):
    def run_stage(self, stage):
        """Verify input bytes, then call one already-reviewed operation."""
        # Embedded FreeCAD can ignore PYTHON* environment settings.
        sys.dont_write_bytecode = True
        config_path = Path(os.environ["TRACKTEMPLATE_ZY_RUN_CONFIG"])
        raw = config_path.read_bytes()
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            os.environ["TRACKTEMPLATE_ZY_RUN_CONFIG_SHA256"],
        )
        config = json.loads(raw)
        self.assertEqual(config["stage"], stage)
        root = Path(config["repository_root"])
        sys.path.insert(0, str(root))
        from tools import hosted_to_zy_generation as generation

        approved = Path(config["approved_directory"])
        generated = Path(config["generated_directory"])
        evidence = Path(config["evidence_directory"])
        self.assertEqual(config["manifest_sha256"], generation.MANIFEST_SHA256)
        self.assertEqual(config["entry_sha256"], generation.ENTRY_SHA256)
        generation.verify_inputs(approved)
        result = {
            "stage": stage,
            "status": "FAIL",
            "model_admitted": False,
            "manifest_sha256": generation.MANIFEST_SHA256,
            "source_commit": config["source_commit"],
            "run_id": config["run_id"],
            "input_files": 71,
        }
        try:
            self.assertFalse(
                any(
                    name.split(".")[0] == "tracktemplate"
                    for name in sys.modules
                ),
                "Fresh native process required",
            )
            if stage == "readiness":
                sys.path.insert(0, str(approved / "source/runtime"))
                import FreeCAD as App
                from tracktemplate import bootstrap

                self.assertEqual(App.listDocuments(), {})
                runtime = bootstrap.require_qualified_runtime(
                    approved
                    / "source/runtime/reference/contracts/phase1-compatibility.json"
                )
                profile = runtime["compatibility_evaluation"][
                    "matched_profile_id"
                ]
                self.assertEqual(profile, generation.pilot.EXPECTED_PROFILE)
                self.assertFalse(generated.exists())
                self.assertEqual(App.listDocuments(), {})
                result["runtime_profile_id"] = profile
                result["geometry_constructed"] = False
            else:
                entry = approved / "x2/build_x2_zy.py"
                self.assertEqual(
                    generation.identity(entry)["sha256"],
                    generation.ENTRY_SHA256,
                )
                operations = runpy.run_path(
                    str(entry), run_name="_approved_x2_entry"
                )
                operations["native"](approved / "source", generated)
                summary = generation.read(generated / "x2-native-summary.json")
                self.assertEqual(
                    summary["status"], "PASS_NEW_CONTEXT_CONSTRUCTION_ONLY"
                )
                self.assertEqual(summary["component_count"], 33)
                self.assertEqual(summary["native_reload"], "PASS")
                self.assertEqual(summary["fixing_status"], "PASS")
                self.assertEqual(len(summary["complete_reload_checks"]), 33)
                self.assertEqual(len(summary["component_checks"]), 6)
                self.assertEqual(summary["open_documents_after"], 0)
                self.assertIs(summary["production_ready"], False)
                self.assertEqual(summary["physical_fit"], "NOT_ASSESSED")
                self.assertEqual(
                    summary["model"],
                    generation.identity(generated / "native-x2/ZY/ZY.FCStd"),
                )
                result.update(
                    runtime_profile_id=summary["runtime_profile_id"],
                    components=33,
                    new_models=1,
                    model=summary["model"],
                    geometry_constructed=True,
                )
            generation.verify_inputs(approved)
            result["status"] = "PASS"
            result["input_bindings_unchanged"] = True
            print(
                "TRACKTEMPLATE_ZY_RUNTIME="
                + json.dumps(
                    {"profile": result["runtime_profile_id"], "stage": stage}
                ),
                flush=True,
            )
            print(dict(generation.SENTINELS)[stage], flush=True)
        except Exception:
            with (evidence / "native-failure.txt").open("x") as stream:
                stream.write(traceback.format_exc())
                stream.flush()
                os.fsync(stream.fileno())
            raise
        finally:
            generation.write(evidence / "native-result.json", result)

    def test_readiness(self):
        self.run_stage("readiness")

    def test_native(self):
        self.run_stage("native")
