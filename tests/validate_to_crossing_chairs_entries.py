#!/usr/bin/env python3
"""Check crossing entry contracts without FreeCAD, Part or Qt."""

import copy
from contextlib import redirect_stdout
import hashlib
import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
SENTINEL = "Fixed TO crossing entries offline checks passed"


class CrossingEntryTests(unittest.TestCase):
    def native(self):
        return importlib.import_module("freecad_validate_to_crossing_chairs")

    def gui(self):
        return importlib.import_module(
            "freecad_validate_to_crossing_chairs_gui"
        )

    def test_import_and_named_discovery_are_host_free(self):
        native, gui = self.native(), self.gui()
        for name in ("FreeCAD", "FreeCADGui", "Part", "PySide6"):
            self.assertNotIn(name, sys.modules)
        loader = unittest.defaultTestLoader
        self.assertEqual(
            loader.getTestCaseNames(native.ToCrossingChairs),
            ["test_fixed_four", "test_readiness"],
        )
        self.assertEqual(
            loader.getTestCaseNames(gui.ToCrossingGui),
            ["test_authorised_gui_stage"],
        )

    def test_exact_fixture_components_layers_and_input_names(self):
        entry = self.native()
        fixture = entry.read_fixture()
        self.assertEqual(entry.validate_fixture(fixture), 50)
        self.assertEqual(
            tuple(r["family"] for r in fixture["positions"]),
            ("XA", "AA", "CD", "DD"),
        )
        self.assertEqual(
            sum(len(entry.component_names(f)) for f in entry.FAMILIES), 135
        )
        self.assertEqual(len(entry.layer_names()), 137)
        self.assertEqual(len(entry.INPUT_HASHES), 6)
        self.assertEqual(entry.DEPLOYMENT_NAMES["xa_model"], "models/XA.FCStd")
        self.assertEqual(
            entry.DEPLOYMENT_NAMES["catalogue"], "four-family-manifest.json"
        )
        self.assertEqual(
            entry.DEPLOYMENT_NAMES["to_base_fixture"], "TO-001-base.FCStd"
        )

    def test_source_fixture_is_immutable_and_type_strict(self):
        entry = self.native()
        for field in ("family", "source_rail_code", "source_hand_i"):
            value = entry.read_fixture()
            value["positions"][0][field] = "wrong"
            with self.subTest(field=field), self.assertRaises(AssertionError):
                entry.validate_fixture(value)
        for number in (True, None, "1", float("inf"), float("nan")):
            value = entry.read_fixture()
            value["positions"][0]["body"]["origin_mm"][0] = number
            with (
                self.subTest(number=number),
                self.assertRaises((AssertionError, ValueError)),
            ):
                entry.validate_fixture(value)
        value = entry.read_fixture()
        value["positions"].reverse()
        with self.assertRaises(AssertionError):
            entry.validate_fixture(value)

    def test_component_frames_use_saved_model_outer_frame_once(self):
        entry = self.native()
        for row in entry.read_fixture()["positions"]:
            for name in entry.component_names(row["family"]):
                self.assertIs(entry.component_frame(row, name), row["body"])
            with self.assertRaises(ValueError):
                entry.component_frame(row, "unknown")

    def test_counts_distinguish_source_compounds_and_children(self):
        entry = self.native()
        checks = entry.expected_checks("native")
        self.assertEqual(checks["source_frame_comparisons"], 50)
        self.assertEqual(checks["component_comparisons"], 135)
        self.assertEqual(checks["stored_compound_checks"], 135)
        self.assertEqual(checks["stored_child_checks"], 135)
        self.assertEqual(checks["rolled_back_components"], 135)
        ready = entry.expected_checks("readiness")
        self.assertEqual(ready["source_frame_inputs"], 50)
        self.assertEqual(ready["component_comparisons"], 0)
        names = entry.layer_names()
        counts = dict.fromkeys(names[2:], 1)
        self.assertEqual(entry.check_layers(names, counts), 135)
        for key in (names[2], names[-1]):
            changed = dict(counts, **{key: 0})
            with self.assertRaises(AssertionError):
                entry.check_layers(names, changed)

    def test_gui_stage_images_limits_and_no_native_comparison_rerun(self):
        gui = self.gui()
        self.assertEqual(len(gui.image_names("readiness")), 1)
        self.assertEqual(len(gui.image_names("gui")), 6)
        checks = gui.expected_checks("gui")
        self.assertEqual(
            (
                checks["assemblies"],
                checks["layers"],
                checks["source_frame_comparisons"],
            ),
            (4, 137, 50),
        )
        self.assertEqual(checks["rolled_back_components"], 135)
        self.assertNotIn("component_comparisons", checks)
        for stage in ("readiness", "gui"):
            gui.check_counts(gui.expected_checks(stage), stage)
            changed = copy.deepcopy(gui.expected_checks(stage))
            changed["binding_checks"] = True
            with self.assertRaises(AssertionError):
                gui.check_counts(changed, stage)
        self.assertEqual(gui.limits("gui")[0]["timeout_seconds"], 7200)
        self.assertEqual(gui.limits("gui")[1]["timeout_seconds"], 7300)

    def test_all_fifty_frames_compare_to_independent_source_expectations(self):
        from tracktemplate.domain.chair_placement import PairedChairPlacement

        entry = self.native()
        fixture = entry.read_fixture()
        groups = {}
        for row in fixture["positions"]:
            owner = row["source_positions"][0]
            groups[row["family"]] = (
                PairedChairPlacement(
                    owner["position_id"],
                    owner["rail_id"],
                    row["timber_id"],
                    **row["body"],
                ),
            )
        self.assertEqual(entry.compare_frames(groups, fixture), 50)
        for family in entry.FAMILIES:
            row = next(
                r for r in fixture["positions"] if r["family"] == family
            )
            original = groups[family][0]
            for change in ("translated", "reversed", "wrong-identity"):
                body = copy.deepcopy(row["body"])
                identity = original.position_id
                if change == "translated":
                    body["origin_mm"][0] += 1
                elif change == "reversed":
                    body["x_axis"] = [-v for v in body["x_axis"]]
                    body["y_axis"] = [-v for v in body["y_axis"]]
                else:
                    identity += "-wrong"
                changed = dict(groups)
                changed[family] = (
                    PairedChairPlacement(
                        identity,
                        original.rail_id,
                        original.timber_id,
                        **body,
                    ),
                )
                with self.subTest(family=family, change=change):
                    with self.assertRaises(AssertionError):
                        entry.compare_frames(changed, fixture)

    def test_stored_observer_excludes_construction_and_calls_original(self):
        import tracktemplate.adapters.freecad as package

        adapter = SimpleNamespace(
            _prepare_catalogue_family=None, _verify_component=None
        )
        entry = self.native()
        compound, child = object(), object()
        compared = []

        def compare(actual, expected, **_kwargs):
            self.assertIs(actual, expected)
            compared.append(actual)

        def prepare():
            def build():
                adapter._verify_component(child, child)

                def stored(values):
                    adapter._verify_component(values[0], compound)
                    adapter._verify_component(child, child)

                return [compound], {}, stored

            return object(), ["source-component"], build

        counts = dict(stored_compound_checks=0, stored_child_checks=0)
        with (
            patch.object(
                package,
                "chair_catalogue_placement_preview",
                adapter,
                create=True,
            ),
            patch.object(adapter, "_prepare_catalogue_family", prepare),
            patch.object(adapter, "_verify_component", compare),
            entry.observe_stored_checks(counts),
        ):
            _, _, build = adapter._prepare_catalogue_family()
            layers, _, verify = build()
            self.assertEqual(
                counts, dict(stored_compound_checks=0, stored_child_checks=0)
            )
            verify(layers)
        self.assertEqual(compared, [child, compound, child])
        self.assertEqual(
            counts, dict(stored_compound_checks=1, stored_child_checks=1)
        )

    def test_interior_target_refuses_boundary_outside_and_downward_faces(self):
        gui = self.gui()

        def face(area, distance=0.0, clearance=1.0, upward=1):
            point = object()
            return SimpleNamespace(
                Area=area,
                CenterOfMass=point,
                isValid=lambda: True,
                normalAt=lambda *_args: SimpleNamespace(z=upward),
                distToShape=lambda _v: (distance, (), ()),
                Edges=[
                    SimpleNamespace(distToShape=lambda _v: (clearance, (), ()))
                ],
            )

        part = SimpleNamespace(Vertex=lambda point: point)
        broad = face(20)
        child = SimpleNamespace(
            Faces=[
                face(100, distance=1),
                face(200, clearance=0),
                face(300, upward=-1),
                broad,
                face(1),
            ]
        )
        self.assertEqual(
            gui.interior_target(part, child), (4, broad.CenterOfMass)
        )
        with self.assertRaisesRegex(AssertionError, "NO_INTERIOR_TARGET"):
            gui.interior_target(part, SimpleNamespace(Faces=child.Faces[:3]))

    def test_pick_requires_exact_object_and_face(self):
        gui = self.gui()
        row = SimpleNamespace(
            DocumentName="Preview",
            ObjectName="XA_base_plinth",
            SubElementNames=["Face7"],
        )
        gui.check_pick([row], "Preview", "XA_base_plinth", 7)
        for changed in (
            [],
            [row, row],
            [
                SimpleNamespace(
                    DocumentName="Other",
                    ObjectName="XA_base_plinth",
                    SubElementNames=["Face7"],
                )
            ],
            [
                SimpleNamespace(
                    DocumentName="Preview",
                    ObjectName="XA_base_plinth",
                    SubElementNames=["Vertex7"],
                )
            ],
            [
                SimpleNamespace(
                    DocumentName="Preview",
                    ObjectName="XA_base_plinth",
                    SubElementNames=["Face8"],
                )
            ],
        ):
            with (
                self.subTest(rows=len(changed)),
                self.assertRaises(AssertionError),
            ):
                gui.check_pick(changed, "Preview", "XA_base_plinth", 7)

    def gui_authority(self, stage):
        gui, entry = self.gui(), self.native()
        hashes = dict(entry.INPUT_HASHES)
        return dict(
            schema=1,
            scope_id=gui.SCOPE,
            stage=stage,
            source_base_commit=gui.BASE,
            source_commit="1" * 40,
            owner="Richard-Gnitnub",
            execution_authorized=True,
            independent_review="PASS",
            run_attempt=1,
            gui_entry_sha256="2" * 64,
            native_entry_sha256=gui.NATIVE_SHA256,
            input_hashes=hashes,
            freecad_limits=gui.limits(stage)[0],
            display_limits=gui.limits(stage)[1],
            initial_reserve_mib=8192,
            software_renderer="llvmpipe",
            decision_id="offline-test",
            handling_decision="offline-test",
            publication_review=dict(
                status="PASS",
                independent_review="PASS",
                input_hashes=hashes,
                handling_decision="offline-test",
                evidence_sha256="3" * 64,
                publication_basis="offline test; no runtime authority",
            ),
            prior_native_evidence=dict(
                status="PASS",
                independent_review="PASS",
                source_commit="1" * 40,
                entry_sha256=gui.NATIVE_SHA256,
                input_hashes=hashes,
                scope_id=entry.SCOPE,
                tests=1,
                skips=0,
                run_attempt=1,
                cleanup=True,
                evidence_verified=True,
                independent_preservation=True,
                source_frame_comparisons=50,
                component_comparisons=135,
                stored_compound_checks=135,
                stored_child_checks=135,
                successful_components=135,
                rolled_back_components=135,
                run_id=123,
                evidence_sha256="4" * 64,
            ),
            gui_readiness_review=dict(
                status="PASS",
                independent_review="PASS",
                source_commit="1" * 40,
                gui_entry_sha256="2" * 64,
                input_hashes=hashes,
                tests=1,
                skips=0,
                cleanup=True,
                independent_preservation=True,
                run_id=124,
            ),
        )

    def test_gui_authority_refuses_old_counts_source_and_unpreserved_proof(
        self,
    ):
        gui = self.gui()
        environment = dict(
            GITHUB_SHA="1" * 40,
            GITHUB_ACTIONS="true",
            RUNNER_ENVIRONMENT="github-hosted",
            GITHUB_RUN_ATTEMPT="1",
            GITHUB_RUN_ID="125",
        )
        config = SimpleNamespace(source_commit="1" * 40)
        with patch.dict("os.environ", environment, clear=True):
            for stage in ("readiness", "gui"):
                gui.validate_authority(
                    self.gui_authority(stage), config, "2" * 64
                )
            for field, value in (
                ("source_commit", "0" * 40),
                ("component_comparisons", 270),
                ("stored_compound_checks", 134),
                ("stored_child_checks", True),
                ("independent_preservation", False),
                ("run_id", 125),
                ("evidence_sha256", "0" * 64),
            ):
                record = self.gui_authority("gui")
                record["prior_native_evidence"][field] = value
                with (
                    self.subTest(field=field),
                    self.assertRaises(AssertionError),
                ):
                    gui.validate_authority(record, config, "2" * 64)

            record = self.gui_authority("gui")
            record["gui_readiness_review"]["independent_preservation"] = False
            with self.assertRaises(AssertionError):
                gui.validate_authority(record, config, "2" * 64)

    def test_native_configuration_binds_six_deployed_paths_and_recovery(self):
        entry = self.native()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "models").mkdir()
            work, evidence = root / "work", root / "evidence"
            work.mkdir(mode=0o700)
            evidence.mkdir(mode=0o700)
            inputs = []
            for identity, name in entry.DEPLOYMENT_NAMES.items():
                path = root / name
                data = identity.encode()
                path.write_bytes(data)
                inputs.append(
                    dict(
                        id=identity,
                        path=str(path),
                        bytes=len(data),
                        sha256=hashlib.sha256(data).hexdigest(),
                    )
                )
            hashes = {row["id"]: row["sha256"] for row in inputs}
            recovery = root / "recovery.json"
            recovery.write_text(
                json.dumps(
                    dict(
                        status="PASS",
                        independent_review="PASS",
                        checkpoint_commit="1" * 40,
                        input_hashes=hashes,
                    )
                )
            )
            config = dict(
                schema_version=1,
                scope_id=entry.SCOPE,
                stage="readiness",
                source_commit="1" * 40,
                entry_sha256=hashlib.sha256(
                    Path(entry.__file__).read_bytes()
                ).hexdigest(),
                inputs=inputs,
                recovery=dict(
                    path=str(recovery),
                    bytes=recovery.stat().st_size,
                    sha256=hashlib.sha256(recovery.read_bytes()).hexdigest(),
                ),
                working_directory=str(work),
                evidence_directory=str(evidence),
                handling_decision="offline fixture only",
            )
            path = root / "run-config.json"
            env = dict(
                GITHUB_ACTIONS="true",
                RUNNER_ENVIRONMENT="github-hosted",
                GITHUB_RUN_ATTEMPT="1",
                GITHUB_RUN_ID="123",
                GITHUB_SHA="1" * 40,
                TRACKTEMPLATE_TO_RUN_CONFIG=str(path),
            )
            for change in (
                None,
                "duplicate",
                "layout",
                "hash",
                "stage",
                "source",
                "unknown",
                "bool-schema",
            ):
                value = copy.deepcopy(config)
                if change == "duplicate":
                    value["inputs"][-1] = value["inputs"][0]
                elif change == "layout":
                    value["inputs"][1]["path"] = str(root / "XA.FCStd")
                elif change == "hash":
                    value["inputs"][1]["sha256"] = "0" * 64
                elif change == "stage":
                    value["stage"] = "native"
                elif change == "source":
                    value["source_commit"] = "2" * 40
                elif change == "unknown":
                    value["extra"] = True
                elif change == "bool-schema":
                    value["schema_version"] = True
                path.write_text(json.dumps(value))
                env["TRACKTEMPLATE_TO_RUN_CONFIG_SHA256"] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                with (
                    patch.dict(entry.INPUT_HASHES, hashes, clear=True),
                    patch.dict("os.environ", env, clear=True),
                ):
                    if change is None:
                        self.assertEqual(
                            entry.configuration("readiness").work, work
                        )
                    else:
                        with self.subTest(change=change):
                            with self.assertRaises(AssertionError):
                                entry.configuration("readiness")

    def test_original_failure_is_retained_without_raw_generic_result(self):
        entry = self.native()
        with tempfile.TemporaryDirectory() as directory:
            config = SimpleNamespace(evidence=Path(directory))
            receipt = {"status": "FAIL"}
            try:
                raise ValueError("original controlled failure")
            except ValueError as error:
                entry.record_failure(config, receipt, "native", error)
            raw = (Path(directory) / "native-failure.txt").read_bytes()
            self.assertIn(b"original controlled failure", raw)
            self.assertEqual(
                receipt["failures"],
                [
                    dict(
                        phase="native",
                        exception_type="ValueError",
                        code="TO_CROSSING_CHECK_FAILED",
                        raw_bytes=len(raw),
                        raw_sha256=hashlib.sha256(raw).hexdigest(),
                    )
                ],
            )
            self.assertNotIn(
                "original controlled failure", json.dumps(receipt)
            )
            with self.assertRaises(FileExistsError):
                entry.record_failure(
                    config, receipt, "native", ValueError("new")
                )

    def test_readiness_never_opens_documents_and_cleanup_always_runs(self):
        entry = self.native()
        app = SimpleNamespace(
            GuiUp=False,
            ActiveDocument=None,
            listDocuments=lambda: {},
            newDocument=Mock(),
            openDocument=Mock(),
        )
        part = SimpleNamespace(Shape=Mock(), makeCompound=Mock())
        for failure in (None, "input", "cleanup"):
            with tempfile.TemporaryDirectory() as directory:
                config = SimpleNamespace(
                    inputs={},
                    fixture=entry.read_fixture(),
                    source_commit="1" * 40,
                    evidence=Path(directory),
                )
                captured = []
                helper = SimpleNamespace(
                    load_comparator=lambda _root: {},
                    comparator_controls=lambda _value: 8,
                )
                with (
                    patch.object(entry, "configuration", return_value=config),
                    patch.object(
                        entry,
                        "runtime",
                        return_value=(
                            app,
                            SimpleNamespace(routing_record=lambda: None),
                        ),
                    ),
                    patch.object(entry, "native_imports", return_value=part),
                    patch.object(entry, "source_contract"),
                    patch.object(entry, "snapshotter"),
                    patch.object(
                        entry,
                        "catalogues",
                        return_value=dict.fromkeys(entry.FAMILIES),
                    ),
                    patch.object(entry, "shared", return_value=helper),
                    patch.object(
                        entry,
                        "verify_inputs",
                        side_effect=(
                            ValueError("input failure")
                            if failure == "input"
                            else None
                        ),
                    ),
                    patch.object(
                        entry,
                        "cleanup",
                        side_effect=(
                            ValueError("cleanup failure")
                            if failure == "cleanup"
                            else None
                        ),
                    ) as cleanup,
                    patch.object(
                        entry,
                        "write_result",
                        side_effect=(
                            lambda _config, result: captured.append(result)
                        ),
                    ),
                    redirect_stdout(io.StringIO()),
                ):
                    test = entry.ToCrossingChairs("test_readiness")
                    if failure:
                        with self.assertRaisesRegex(
                            AssertionError, "NATIVE_FAILED"
                        ):
                            test.test_readiness()
                    else:
                        test.test_readiness()
                    cleanup.assert_called_once()
                self.assertEqual(
                    captured[0]["status"], "FAIL" if failure else "PASS"
                )
                self.assertEqual("sentinel" in captured[0], failure is None)
                self.assertEqual(
                    captured[0]["checks"], entry.expected_checks("readiness")
                )
        app.newDocument.assert_not_called()
        app.openDocument.assert_not_called()
        part.Shape.assert_not_called()
        part.makeCompound.assert_not_called()


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(CrossingEntryTests)
    )
    if not result.wasSuccessful() or result.skipped:
        raise SystemExit(1)
    print(SENTINEL)
