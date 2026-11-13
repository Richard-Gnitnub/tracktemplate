"""Offline fixed crossing controller contracts; no native runtime or network."""

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import hosted_l1_private_validation as pilot  # noqa: E402

WORKLOAD = "to-crossing"
HASHES = {
    "catalogue": "801a2b43f623aa292b87762970fe3f249e4fb5b3a78d3f36bcf64eb435a3e70e",
    "xa_model": "92cc129808cf86713fdeb6bb8bb6bcd60bd2c417da5a7428fe0011b3478add5b",
    "aa_model": "b2b33ddc9a76a848c92bb08e1971291b6643422ead94073babe654968d274132",
    "cd_model": "d9a411078e8f070565a2358ac1e3f3e68eb504893486a327f658a44a61dd9f4a",
    "dd_model": "a53a5ddab9603a55abce8b45dcd907df653070bae71bcf4f5b212238cce86699",
    "to_base_fixture": "0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c",
}
SIZES = dict(zip(HASHES, (22951, 397349, 492552, 271016, 286034, 636344)))
MEMBERS = dict(
    zip(
        HASHES,
        (
            "four-family-manifest.json",
            "models/XA.FCStd",
            "models/AA.FCStd",
            "models/CD.FCStd",
            "models/DD.FCStd",
            "TO-001-base.FCStd",
        ),
    )
)
FIXTURE = "tests/fixtures/phase9b-to-crossing-cohort-source-frames.json"
FIXTURE_SHA = (
    "3fe86e5e6e0a565e1e151555fb9e1bca7723c176df804281486ec795c10da900"
)
COPY_NAMES = (
    "XA-copy.FCStd",
    "AA-copy.FCStd",
    "CD-copy.FCStd",
    "DD-copy.FCStd",
    "TO-001-copy.FCStd",
)
SENTINEL = "Fixed TO crossing native controller offline validation passed"
PUBLICATION_SHA = (
    "303135d7f7f6de4bbee5ee8400bf9a9db2b8ab2e687ef3557ef140154c6b737e"
)
OWNER_DECISION = "to-crossing-handling-owner-decision.json@sha256:" + "d" * 64


def config(profile):
    return dict(
        schema_version=1,
        scope_id=profile["scope"],
        source_commit="a" * 40,
        entry_sha256=profile["entry_sha256"],
        handling_decision=OWNER_DECISION,
        inputs=[
            dict(
                id=name,
                path="/home/richard/crossing/" + member,
                sha256=HASHES[name],
                bytes=SIZES[name],
            )
            for name, member in MEMBERS.items()
        ],
    )


def control(profile):
    result = {
        key: value
        for key, value in config(profile).items()
        if key not in ("schema_version", "inputs")
    }
    result.update(
        publication_manifest_sha256=PUBLICATION_SHA,
        input_hashes=dict(HASHES),
        input_archive=dict(asset_id=42, bytes=10240, sha256="c" * 64),
        publication_review=dict(
            status="PASS",
            independent_review="PASS",
            input_hashes=dict(HASHES),
            handling_decision=result["handling_decision"],
            evidence_sha256="b" * 64,
            publication_basis="Exact research scope",
            publication_manifest_sha256=PUBLICATION_SHA,
        ),
    )
    return result


def checks(stage):
    full = stage == "native"
    return dict(
        binding_checks=1,
        catalogue_contracts=4,
        source_frame_inputs=50,
        comparator_negative_controls=8,
        source_frame_comparisons=50 if full else 0,
        component_comparisons=135 if full else 0,
        stored_compound_checks=135 if full else 0,
        stored_child_checks=135 if full else 0,
        successful_components=135 if full else 0,
        rolled_back_components=135 if full else 0,
        wrong_frame_rejections=4 if full else 0,
        preview_undo_redo=1 if full else 0,
    )


def comparisons():
    rows = json.loads((ROOT / FIXTURE).read_text())["positions"]
    return [
        dict(
            position_id=row["source_positions"][0]["position_id"],
            component=name,
            counts=[1, 1, 6, 6, 12, 8],
            vertex_residual_mm=0.0,
        )
        for row in rows
        for name in row["model"]["component_names"]
    ]


def receipt(profile, stage):
    value = dict(
        status="PASS",
        stage=stage,
        scope_id=profile["scope"],
        test_id=profile["selectors"][stage],
        source_commit="a" * 40,
        fixture_sha256=FIXTURE_SHA,
        physical_fit="NOT_PROVED",
        input_sha256=dict(HASHES),
        input_bindings_unchanged=True,
        remaining_documents=0,
        owned_documents_closed=True,
        sentinel=profile["sentinels"][stage],
        checks=checks(stage),
        failures=[],
        stage_timings=dict.fromkeys(
            ("readiness_seconds", "cleanup_seconds", "total_seconds")
            + (("native_seconds",) if stage == "native" else ()),
            1.0,
        ),
    )
    if stage == "native":
        value.update(
            component_comparisons=comparisons(),
            preview_disposal_preserves_source_and_foreign=True,
        )
    return value


class CrossingControls(unittest.TestCase):
    def profile(self):
        return pilot.to_profile(WORKLOAD)

    def test_exact_descriptor_detached_and_original_defaults(self):
        p = self.profile()
        self.assertEqual(p["input_hashes"], HASHES)
        self.assertEqual(p["input_bytes"], SIZES)
        self.assertEqual(sum(SIZES.values()), 2106246)
        self.assertEqual(p["scope"], "TO-001-fixed-crossing-native-v1")
        self.assertEqual(
            p["entry"], "tests/freecad_validate_to_crossing_chairs.py"
        )
        self.assertEqual(p["entry_sha256"], pilot.digest(ROOT / p["entry"]))
        self.assertEqual(
            (p["fixture"], p["fixture_sha256"]), (FIXTURE, FIXTURE_SHA)
        )
        self.assertEqual(p["copy_names"], COPY_NAMES)
        self.assertTrue(
            {
                "tests/freecad_validate_phase9b_catalogue_p_placement.py",
                "reference/contracts/phase1-chair-analysis-persistence.json",
                "tools/freecad_bridge/b14_recipe.py",
                "tools/freecad_bridge/turnout_recipe.py",
                "tracktemplate/application/chair_crossing_pair_catalogue.py",
            }
            <= set(p["control_files"])
        )
        self.assertEqual(
            p["selectors"],
            {
                "readiness": "freecad_validate_to_crossing_chairs.ToCrossingChairs.test_readiness",
                "native": "freecad_validate_to_crossing_chairs.ToCrossingChairs.test_fixed_four",
            },
        )
        p["input_hashes"]["catalogue"] = "0" * 64
        self.assertEqual(self.profile()["input_hashes"], HASHES)
        self.assertEqual(
            pilot.to_profile()["input_hashes"], pilot.TO_INPUT_HASHES
        )
        self.assertEqual(
            pilot.to_profile()["entry_sha256"], pilot.TO_ENTRY_SHA256
        )
        with self.assertRaises(ValueError):
            pilot.to_profile("anything")

    def test_exact_stage_counts_and_unchanged_resource_limits(self):
        for stage in ("readiness", "native"):
            self.assertEqual(
                pilot.to_expected_checks(stage, workload=WORKLOAD),
                checks(stage),
            )
        self.assertEqual(
            pilot.to_expected_checks("native")["successful_components"], 270
        )
        limits = pilot.limits("native")
        self.assertEqual(
            (
                limits.memory_max_mib,
                limits.timeout_seconds,
                limits.cpu_percent,
                limits.tasks_max,
            ),
            (4096, 7200, 100, 128),
        )
        with self.assertRaises(ValueError):
            pilot.to_expected_checks("gui", workload=WORKLOAD)

    def test_acquisition_requires_exact_six_input_publication_review(self):
        good = control(self.profile())
        pilot.validate_to_acquisition(good, workload=WORKLOAD)
        for path, value in (
            (("scope_id",), pilot.TO_SCOPE),
            (("entry_sha256",), pilot.TO_ENTRY_SHA256),
            (("input_hashes",), pilot.TO_INPUT_HASHES),
            (("publication_review", "input_hashes"), pilot.TO_INPUT_HASHES),
            (("publication_review", "independent_review"), "PENDING"),
            (("publication_manifest_sha256",), "0" * 64),
            (("publication_review", "publication_manifest_sha256"), "f" * 64),
            (
                ("handling_decision",),
                "to-crossing-handling-owner-decision.json@sha256:" + "0" * 64,
            ),
        ):
            candidate = copy.deepcopy(good)
            parent = candidate
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ValueError):
                pilot.validate_to_acquisition(candidate, workload=WORKLOAD)

    def test_exact_deployment_mapping_before_any_write(self):
        good = config(self.profile())
        manifest = {"inputs": copy.deepcopy(good["inputs"])}
        pilot.validate_to_inputs(good, manifest, workload=WORKLOAD)
        for field, value in (
            ("id", "l1_model"),
            ("bytes", True),
            ("sha256", "0" * 64),
            ("path", "/home/richard/crossing/XA.FCStd"),
        ):
            candidate = copy.deepcopy(good)
            candidate["inputs"][1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                pilot.validate_to_inputs(
                    candidate, manifest, workload=WORKLOAD
                )
        alias = copy.deepcopy(good)
        alias["inputs"][1]["path"] = (
            "/home/richard/crossing/models/../models/XA.FCStd"
        )
        with self.assertRaises(ValueError):
            pilot.validate_to_inputs(
                alias, {"inputs": alias["inputs"]}, workload=WORKLOAD
            )

    def test_receipt_all_counters_types_and_old_scope_refused(self):
        p = self.profile()
        for stage in ("readiness", "native"):
            good = receipt(p, stage)
            pilot.validate_to_receipt(
                stage, good, config(p), workload=WORKLOAD
            )
            for key in good["checks"]:
                for value in (True, good["checks"][key] + 1):
                    altered = copy.deepcopy(good)
                    altered["checks"][key] = value
                    with (
                        self.subTest(stage=stage, key=key, value=value),
                        self.assertRaises(ValueError),
                    ):
                        pilot.validate_to_receipt(
                            stage, altered, config(p), workload=WORKLOAD
                        )
            altered = dict(good, scope_id=pilot.TO_SCOPE)
            with self.assertRaises(ValueError):
                pilot.validate_to_receipt(
                    stage, altered, config(p), workload=WORKLOAD
                )
            for failure in (None, [{"phase": "native"}], False):
                altered = dict(good, failures=failure)
                with self.assertRaises(ValueError):
                    pilot.validate_to_receipt(
                        stage, altered, config(p), workload=WORKLOAD
                    )

    def test_all135_ordered_comparison_identities_and_residuals(self):
        good = comparisons()
        self.assertEqual(len(good), 135)
        pilot.validate_to_comparisons(good, workload=WORKLOAD)
        for altered in (good[:-1], list(reversed(good)), good + [good[0]]):
            with self.assertRaises(ValueError):
                pilot.validate_to_comparisons(altered, workload=WORKLOAD)
        for key, value in (
            ("position_id", "wrong"),
            ("component", "wrong"),
            ("counts", [True] * 6),
            ("vertex_residual_mm", float("nan")),
            ("vertex_residual_mm", float("inf")),
            ("vertex_residual_mm", 1.1e-7),
        ):
            altered = copy.deepcopy(good)
            altered[-1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                pilot.validate_to_comparisons(altered, workload=WORKLOAD)

    def test_separate_readiness_rejects_old_profile_and_same_run(self):
        p = self.profile()
        c = control(p) | dict(
            workflow_commit="a" * 40,
            control_files_sha256=dict.fromkeys(p["control_files"], "c" * 64),
        )
        review = dict(
            status="PASS",
            independent_review="PASS",
            source_commit="a" * 40,
            entry_sha256=p["entry_sha256"],
            scope_id=p["scope"],
            workload=WORKLOAD,
            handling_decision=c["handling_decision"],
            workflow_commit="a" * 40,
            control_files_sha256=c["control_files_sha256"],
            run_attempt=1,
            tests=1,
            skips=0,
            failures=0,
            errors=0,
            sentinel=p["sentinels"]["readiness"],
            cleanup=True,
            evidence_verified=True,
            independent_preservation=True,
            input_hashes=HASHES,
            checks=checks("readiness"),
            run_id=41,
            evidence_sha256="d" * 64,
        )
        pilot.validate_to_readiness(
            review, config(p), "42", c, workload=WORKLOAD
        )
        for key, value in (
            ("run_id", 42),
            ("workload", "to-single"),
            ("checks", pilot.to_expected_checks("readiness")),
            ("input_hashes", pilot.TO_INPUT_HASHES),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                pilot.validate_to_readiness(
                    dict(review, **{key: value}),
                    config(p),
                    "42",
                    c,
                    workload=WORKLOAD,
                )

    def test_environment_runtime_selector_and_sentinel_are_profile_specific(
        self,
    ):
        p = self.profile()
        env = dict(
            GITHUB_SHA="a" * 40,
            GITHUB_RUN_ATTEMPT="1",
            GITHUB_RUN_ID="42",
            GITHUB_ACTIONS="true",
            RUNNER_ENVIRONMENT="github-hosted",
            GITHUB_TOKEN="secret",
        )
        child = pilot.child_environment(
            env, Path("/approved/config"), "b" * 64, workload=WORKLOAD
        )
        self.assertEqual(
            child["TRACKTEMPLATE_TO_RUN_CONFIG"], "/approved/config"
        )
        self.assertNotIn("GITHUB_TOKEN", child)
        self.assertNotIn("TRACKTEMPLATE_L1_RUN_CONFIG", child)
        self.assertEqual(
            pilot.selected_workload(
                {"TRACKTEMPLATE_NATIVE_WORKLOAD": WORKLOAD}
            ),
            WORKLOAD,
        )
        report = dict(
            status="modular-foundation-ready",
            matched_profile_id=pilot.original.EXPECTED_PROFILE,
            document_mutation=False,
            workflow_launched=False,
        )
        selector = p["selectors"]["native"]
        line = (
            f"test_fixed_four ({selector}) ... TRACKTEMPLATE_B16_FOUNDATION="
            + json.dumps(report)
        )
        pilot.qualified_runtime(line, workload=WORKLOAD)
        with self.assertRaises(ValueError):
            pilot.qualified_runtime(line, workload="to-single")

    def test_evidence_allowlist_has_six_deployments_and_no_input_media(self):
        for name in (
            "native/native-failure.txt",
            "native/input-failure.txt",
            "native/cleanup-failure.txt",
        ):
            pilot.validate_to_evidence_name(name, workload=WORKLOAD)
            with self.assertRaises(ValueError):
                pilot.validate_to_evidence_name(name)
        for index in range(1, 7):
            pilot.validate_to_evidence_name(
                f"deployed-{index:02d}.json", workload=WORKLOAD
            )
        for name in (
            "deployed-07.json",
            "native-failure.txt",
            "native/gui-failure.txt",
            "gui/gui-failure.txt",
            "models/XA.FCStd",
            "native/XA-copy.FCStd",
            "source/source-map.json",
            "../native/result.json",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                pilot.validate_to_evidence_name(name, workload=WORKLOAD)
        pilot.validate_to_evidence_name("deployed-10.json")

    def test_summary_requires_six_removed_inputs_and_reports50_135(self):
        p = self.profile()
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / "evidence").mkdir()
            pilot.write(
                work / "evidence/assessment.json",
                dict(
                    status="PASS",
                    completed_native_tests=1,
                    skips=0,
                    native_receipt=receipt(p, "native"),
                ),
            )
            final = dict(
                cleanup=True,
                working_copies_absent=True,
                staging_inputs_removed=list(HASHES),
            )
            pilot.write(work / "evidence/finalization.json", final)
            with patch.dict(
                os.environ,
                dict(
                    TRACKTEMPLATE_NATIVE_WORKLOAD=WORKLOAD,
                    GITHUB_SHA="a" * 40,
                    GITHUB_RUN_ID="42",
                ),
            ):
                result = pilot.public_summary(
                    "native",
                    work,
                    dict(sha256="d" * 64, bytes=1, asset_id=1),
                    True,
                )
            self.assertEqual(result["outcome"], "PASS")
            self.assertEqual(result["counts"]["expected_frames"], 50)
            self.assertEqual(result["counts"]["observed_frames"], 50)
            self.assertEqual(result["counts"]["expected_components"], 135)
            self.assertEqual(result["counts"]["successful_components"], 135)
            self.assertEqual(result["counts"]["rolled_back_components"], 135)
            self.assertEqual(result["workload"], WORKLOAD)

    def test_real_deployment_and_cleanup_use_exact_six_inputs_five_copies(
        self,
    ):
        descriptor = self.profile()
        original_profile = pilot.to_profile
        contents = {name: name.encode() for name in HASHES}
        descriptor["input_hashes"] = {
            name: hashlib.sha256(data).hexdigest()
            for name, data in contents.items()
        }
        descriptor["input_bytes"] = {
            name: len(data) for name, data in contents.items()
        }
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            deployment = base / "deployed"
            deployment.mkdir()
            work = base / "work"
            (work / "evidence").mkdir(parents=True)
            staged = work / "unpacked"
            (staged / "inputs").mkdir(parents=True)
            cfg = config(descriptor)
            for item in cfg["inputs"]:
                name = item["id"]
                item.update(
                    path=str(deployment / MEMBERS[name]),
                    sha256=descriptor["input_hashes"][name],
                    bytes=len(contents[name]),
                )
            ctl = control(descriptor)
            ctl["input_hashes"] = descriptor["input_hashes"]
            ctl["publication_review"]["input_hashes"] = descriptor[
                "input_hashes"
            ]
            manifest = {"inputs": copy.deepcopy(cfg["inputs"])}
            extracted = {}
            for name, data in contents.items():
                target = staged / "inputs" / name
                target.write_bytes(data)
                extracted[name] = target
            for name, value in (
                ("run-config", cfg),
                (
                    "recovery",
                    dict(
                        status="PASS",
                        independent_review="PASS",
                        checkpoint_commit="a" * 40,
                        input_hashes=descriptor["input_hashes"],
                    ),
                ),
            ):
                extracted[name] = staged / (name + ".json")
                pilot.write(extracted[name], value)
            with (
                patch.object(
                    pilot,
                    "to_profile",
                    side_effect=lambda workload="to-single": (
                        descriptor
                        if workload == WORKLOAD
                        else original_profile(workload)
                    ),
                ),
                patch.object(pilot, "DEPLOYMENT_ROOT", deployment),
                patch.object(
                    pilot,
                    "download_asset",
                    side_effect=lambda record, target: target.write_bytes(
                        b"dummy transport"
                    ),
                ),
                patch.object(
                    pilot.payload, "read_manifest", return_value=manifest
                ) as read,
                patch.object(
                    pilot.payload, "extract_archive", return_value=extracted
                ) as extract,
                patch.object(pilot, "validate_host"),
                patch.object(pilot, "validate_input_repository"),
                patch.object(pilot, "command", return_value="a" * 40),
                patch.dict(os.environ, {"GITHUB_SHA": "a" * 40}),
            ):
                result = pilot.acquire_to(
                    "readiness", work, control=ctl, workload=WORKLOAD
                )
                self.assertEqual(read.call_args.kwargs, {"profile": WORKLOAD})
                self.assertEqual(
                    extract.call_args.kwargs, {"profile": WORKLOAD}
                )
                self.assertEqual(
                    set(result),
                    set(cfg)
                    | {
                        "stage",
                        "working_directory",
                        "evidence_directory",
                        "recovery",
                    },
                )
                for item in result["inputs"]:
                    target = Path(item["path"])
                    self.assertEqual(target.read_bytes(), contents[item["id"]])
                    self.assertEqual(target.stat().st_mode & 0o777, 0o400)
                self.assertFalse((work / "evidence/deployed-07.json").exists())
                for name in COPY_NAMES:
                    (work / "test-data" / name).write_bytes(b"owned copy")
                pilot.write(
                    work / "evidence/process-finalization.json",
                    dict(cleanup=True, errors=[], seconds=0),
                )
                (work / "evidence.tar").write_bytes(b"preserved diagnostics")
                preserved = dict(
                    asset_id=42,
                    **pilot.payload.file_identity(work / "evidence.tar"),
                )
                final = pilot.cleanup_to_staging(
                    work, preserved, workload=WORKLOAD
                )
                self.assertTrue(final["cleanup"])
                self.assertTrue(final["working_copies_absent"])
                self.assertEqual(len(final["staging_inputs_removed"]), 6)
                self.assertEqual(len(final["staging_absence_verified"]), 18)
                self.assertFalse(list((work / "test-data").iterdir()))

    def test_guarded_run_keeps_current_source_selector_and_result_path(self):
        p = self.profile()
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            (work / "evidence/native").mkdir(parents=True)
            pilot.write(work / "run-config.json", config(p))
            pilot.write(work / "control.json", control(p))
            calls = []

            def guarded(argv, **kwargs):
                calls.append((argv, kwargs))
                directory = kwargs["evidence_dir"]
                directory.mkdir()
                (directory / "measurements.jsonl").write_text("{}\n")
                (directory / "stdout").write_text("raw stdout")
                (directory / "stderr").write_text("raw stderr")
                pilot.write(
                    work / "evidence/native/result.json",
                    receipt(p, "readiness"),
                )
                return {"cleanup_proved": True}

            def command(*args, **kwargs):
                if "--show-runtime" in args:
                    return pilot.original.RUNTIME
                return (
                    pilot.original.RUNTIME_COMMIT
                    if pilot.original.RUNTIME in args
                    else pilot.original.APP_COMMIT
                )

            with (
                patch.dict(
                    os.environ,
                    dict(
                        TRACKTEMPLATE_NATIVE_WORKLOAD=WORKLOAD,
                        GITHUB_SHA="a" * 40,
                        GITHUB_RUN_ID="42",
                        GITHUB_RUN_ATTEMPT="1",
                        GITHUB_ACTIONS="true",
                        RUNNER_ENVIRONMENT="github-hosted",
                    ),
                ),
                patch.object(pilot, "validate_host"),
                patch.object(pilot, "require_finalization_time"),
                patch.object(pilot, "command", side_effect=command),
                patch.object(
                    pilot.guard, "run_guarded_flatpak", side_effect=guarded
                ),
                patch.object(
                    pilot.original, "_deadline_clearance", return_value=True
                ),
                patch.object(pilot.original, "_clearance", return_value=True),
                patch.object(
                    pilot,
                    "assess",
                    return_value=dict(
                        status="PASS", completed_native_tests=1, skips=0
                    ),
                ) as assess,
            ):
                self.assertEqual(pilot.run("readiness", work), 0)
            self.assertEqual(len(calls), 1)
            argv, kwargs = calls[0]
            self.assertEqual(
                argv[-3:],
                [str(ROOT / "tests"), "-t", p["selectors"]["readiness"]],
            )
            self.assertEqual(kwargs["cwd"], ROOT)
            self.assertTrue(kwargs["isolate_profile"])
            self.assertEqual(assess.call_args.kwargs, {"workload": WORKLOAD})
            self.assertEqual(
                json.loads((work / "evidence/assessment.json").read_text())[
                    "status"
                ],
                "PASS",
            )


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(CrossingControls)
    )
    if result.wasSuccessful():
        print(SENTINEL)
    raise SystemExit(0 if result.wasSuccessful() else 1)
