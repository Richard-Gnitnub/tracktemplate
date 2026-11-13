"""Import-safe native proof of four fixed TO-001 crossing assemblies.

Only a reviewed hosted runner may select either named test. Saved native
components receive one common placement; source constituent frames are
independent comparisons, never a second transformation of those shapes.
"""

from contextlib import ExitStack, contextmanager
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCOPE = "TO-001-fixed-crossing-native-v1"
FAMILIES = ("XA", "AA", "CD", "DD")
FIXTURE = "tests/fixtures/phase9b-to-crossing-cohort-source-frames.json"
FIXTURE_SHA256 = (
    "3fe86e5e6e0a565e1e151555fb9e1bca7723c176df804281486ec795c10da900"
)
SOURCE_ANALYSIS_SHA256 = (
    "dad7acd2955b47ec82ad76e3827443eecce54c072c647e5e7e9ba865303b7379"
)
LEGACY_PATH = "tests/freecad_validate_to_single_rail.py"
LEGACY_SHA256 = (
    "6288286b9b7c45ec26df4cf3d2b891ae59548bab4cc5b3ab92a103fa54d627c0"
)
SENTINELS = {
    "readiness": "Fixed TO crossing hosted readiness passed",
    "native": "Fixed TO crossing hosted native validation passed",
}
INPUT_HASHES = {
    "catalogue": "801a2b43f623aa292b87762970fe3f249e4fb5b3a78d3f36bcf64eb435a3e70e",
    "xa_model": "92cc129808cf86713fdeb6bb8bb6bcd60bd2c417da5a7428fe0011b3478add5b",
    "aa_model": "b2b33ddc9a76a848c92bb08e1971291b6643422ead94073babe654968d274132",
    "cd_model": "d9a411078e8f070565a2358ac1e3f3e68eb504893486a327f658a44a61dd9f4a",
    "dd_model": "a53a5ddab9603a55abce8b45dcd907df653070bae71bcf4f5b212238cce86699",
    "to_base_fixture": "0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c",
}
DEPLOYMENT_NAMES = {
    "catalogue": "four-family-manifest.json",
    "xa_model": "models/XA.FCStd",
    "aa_model": "models/AA.FCStd",
    "cd_model": "models/CD.FCStd",
    "dd_model": "models/DD.FCStd",
    "to_base_fixture": "TO-001-base.FCStd",
}


def legacy():
    path = ROOT / LEGACY_PATH
    assert hashlib.sha256(path.read_bytes()).hexdigest() == LEGACY_SHA256
    import freecad_validate_to_single_rail as helper

    assert Path(helper.__file__).resolve() == path
    return helper


def shared():
    return legacy().shared()


def strict_json(text):
    return legacy().strict_json(text)


def _frozen_fixture():
    content = (ROOT / FIXTURE).read_bytes()
    assert hashlib.sha256(content).hexdigest() == FIXTURE_SHA256
    return strict_json(content)


def validate_fixture(data):
    frozen = _frozen_fixture()
    # Compare canonical encoding too: Python's True == 1 is insufficient.
    assert json.dumps(data, sort_keys=True, allow_nan=False) == json.dumps(
        frozen, sort_keys=True, allow_nan=False
    )
    assert tuple(row["family"] for row in data["positions"]) == FAMILIES
    count = 0
    for row in data["positions"]:
        frames = [row["body"]] + [
            item["frame"]
            for item in (*row["constituent_frames"], *row["fixing_frames"])
        ]
        for frame in frames:
            for key, size in (("origin_mm", 3), ("x_axis", 2), ("y_axis", 2)):
                assert len(frame[key]) == size
                assert all(
                    type(v) in (int, float) and math.isfinite(v)
                    for v in frame[key]
                )
            count += 1
    assert count == 50
    return count


def read_fixture():
    data = _frozen_fixture()
    validate_fixture(data)
    return data


def component_names(family):
    if family not in FAMILIES:
        raise ValueError("Unknown fixed crossing family")
    return tuple(
        next(
            row
            for row in _frozen_fixture()["positions"]
            if row["family"] == family
        )["model"]["component_names"]
    )


def component_frame(row, name):
    if name not in component_names(row["family"]):
        raise ValueError("Unknown fixed crossing component")
    return row["body"]


def layer_names():
    return (
        "ReferenceRails",
        "ReferenceTimbers",
        *(
            family + "_" + name
            for family in FAMILIES
            for name in component_names(family)
        ),
    )


def check_layers(names, counts):
    assert tuple(names) == layer_names() and len(names) == 137
    assert set(counts) == set(layer_names()[2:])
    assert all(type(value) is int and value == 1 for value in counts.values())
    assert sum(counts.values()) == 135
    return 135


def expected_checks(stage):
    assert stage in SENTINELS
    checks = dict(
        binding_checks=1,
        catalogue_contracts=4,
        source_frame_inputs=50,
        comparator_negative_controls=8,
        source_frame_comparisons=0,
        component_comparisons=0,
        stored_compound_checks=0,
        stored_child_checks=0,
        successful_components=0,
        rolled_back_components=0,
        wrong_frame_rejections=0,
        preview_undo_redo=0,
    )
    if stage == "native":
        checks.update(
            source_frame_comparisons=50,
            component_comparisons=135,
            stored_compound_checks=135,
            stored_child_checks=135,
            successful_components=135,
            rolled_back_components=135,
            wrong_frame_rejections=4,
            preview_undo_redo=1,
        )
    return checks


def verify_inputs(inputs):
    for record in inputs.values():
        shared().bound_file(record)


def catalogues(inputs):
    from tracktemplate.application.chair_crossing_pair_catalogue import (
        prepare_turnout_crossing_catalogue,
        verify_turnout_crossing_catalogue,
    )

    values = prepare_turnout_crossing_catalogue(inputs["catalogue"]["path"])
    assert tuple(value.family for value in values) == FAMILIES
    approved = {row["path"]: row["sha256"] for row in inputs.values()}
    for family, value in zip(FAMILIES, values):
        record = inputs[family.lower() + "_model"]
        assert value.catalogue_sha256 == INPUT_HASHES["catalogue"]
        assert (value.model_path, value.model_sha256) == (
            record["path"],
            record["sha256"],
        )
        assert tuple(c.name for c in value.components) == component_names(
            family
        )
        assert all(approved.get(b.path) == b.sha256 for b in value.bindings)
    verify_turnout_crossing_catalogue(values)
    return dict(zip(FAMILIES, values))


def compare_frames(groups, fixture):
    assert type(groups) is dict and tuple(groups) == FAMILIES
    count = 0
    for row in fixture["positions"]:
        (value,) = groups[row["family"]]
        owner = row["source_positions"][0]
        assert (value.position_id, value.rail_id, value.timber_id) == (
            owner["position_id"],
            owner["rail_id"],
            row["timber_id"],
        )
        shared().compare_frame(value, row["body"])
        count += 1
        targets = [
            (c["source_origin_mm"], c["source_angle_rad"], c["frame"])
            for c in row["constituent_frames"]
        ]
        targets += [
            (c["source_origin_mm"], 0.0, c["frame"])
            for c in row["fixing_frames"]
        ]
        for (x, y, z), angle, target in targets:
            cosine, sine = math.cos(angle), math.sin(angle)
            actual = SimpleNamespace(
                origin_mm=value.transform_point((-x, -y - 0.45, z + 149 / 60)),
                x_axis=tuple(
                    -cosine * value.x_axis[i] - sine * value.y_axis[i]
                    for i in (0, 1)
                ),
                y_axis=tuple(
                    sine * value.x_axis[i] - cosine * value.y_axis[i]
                    for i in (0, 1)
                ),
            )
            shared().compare_frame(actual, target)
            count += 1
    assert count == 50
    return count


def check_structure(receipt, preview, fixture):
    assert (
        receipt["placement_count"],
        receipt["component_count"],
        receipt["family_count"],
        receipt["layer_count"],
    ) == (4, 135, 4, 137)
    assert receipt["project_status"] == "reference-only"
    assert receipt["intended_uses"] == ["private-development"]
    assert receipt["production_geometry_authorized"] is False
    assert receipt["geometry_rebuilt"] is False
    assert not preview.FileName and not preview.Temporary
    source = receipt["source_receipt"]
    assert source["source_document_mutation"] is False
    assert source["model_support_adjustments_applied"] is False
    assert source["analysis_position_count"] == 168
    assert source["represented_source_position_count"] == 8
    assert source["selected_family_counts"] == dict.fromkeys(FAMILIES, 1)
    assert len(source["remaining_positions"]) == 160
    assert set(fixture["provenance"]["excluded_position_ids"]) <= {
        row["stable_chair_position_identity"]
        for row in source["remaining_positions"]
    }
    assert source["retained_research_key_direction_sign"] == 1
    assert source["retained_research_key_offset_mm"] == 0
    expected_shared = {}
    for row in fixture["positions"]:
        family = row["family"]
        owner, companion = row["source_positions"]
        expected_shared[companion["position_id"]] = owner["position_id"]
        item = receipt["families"][family]
        assert item["source_model_sha256"] == row["model"]["model_sha256"]
        assert item["excluded_source_components"] == []
        assert item["source_hand"] == "LH" and item["source_rail_code"] == 3
        assert [p["position_id"] for p in item["placements"]] == [
            owner["position_id"]
        ]
    assert source["shared_supports"] == expected_shared
    return check_layers(
        [obj.Name for obj in preview.Objects],
        {
            name: len(preview.getObject(name).Shape.childShapes())
            for name in layer_names()[2:]
        },
    )


@contextmanager
def observe_stored_checks(counts):
    """Count only the real stored verifier, separately from construction."""
    from tracktemplate.adapters.freecad import (
        chair_catalogue_placement_preview,
    )

    adapter = chair_catalogue_placement_preview
    prepare = adapter._prepare_catalogue_family
    original = adapter._verify_component

    def wrap(*args, **kwargs):
        selected, specs, build = prepare(*args, **kwargs)

        def build_and_observe():
            layers, receipt, verify = build()

            def stored(values):
                compound_ids = {id(value) for value in values}

                def compare(actual, expected, **options):
                    answer = original(actual, expected, **options)
                    key = (
                        "stored_compound_checks"
                        if id(actual) in compound_ids
                        else "stored_child_checks"
                    )
                    counts[key] += 1
                    return answer

                with patch.object(adapter, "_verify_component", compare):
                    verify(values)

            return layers, receipt, stored

        return selected, specs, build_and_observe

    with patch.object(adapter, "_prepare_catalogue_family", wrap):
        yield


def record_failure(config, result, phase, error):
    """Retain the original approved-input trace and its typed identity."""
    assert phase in ("native", "gui", "input", "cleanup")
    raw = "".join(traceback.format_exception(error)).encode()
    path = config.evidence / (phase + "-failure.txt")
    with path.open("xb") as stream:
        stream.write(raw)
    path.chmod(0o600)
    kinds = {
        "AssertionError",
        "ValueError",
        "TypeError",
        "RuntimeError",
        "OSError",
        "KeyError",
        "CatalogueChairError",
    }
    kind = type(error).__name__
    result.setdefault("failures", []).append(
        dict(
            phase=phase,
            exception_type=kind if kind in kinds else "OtherError",
            code="TO_CROSSING_CHECK_FAILED",
            raw_bytes=len(raw),
            raw_sha256=hashlib.sha256(raw).hexdigest(),
        )
    )


def write_result(config, result):
    shared().write_private_result(config.evidence, result)


def configuration(stage):
    """Read a reviewed runner configuration, not grant execution authority."""
    assert sys.flags.optimize == 0
    assert os.environ.get("GITHUB_ACTIONS") == "true"
    assert os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
    assert os.environ.get("GITHUB_RUN_ATTEMPT") == "1"
    assert os.environ.get("GITHUB_RUN_ID", "").isdigit()
    base = shared()
    path = base.regular_path(os.environ["TRACKTEMPLATE_TO_RUN_CONFIG"])
    assert (
        base.sha256(path) == os.environ["TRACKTEMPLATE_TO_RUN_CONFIG_SHA256"]
    )
    config = strict_json(path.read_bytes())
    assert set(config) == {
        "schema_version",
        "scope_id",
        "stage",
        "source_commit",
        "entry_sha256",
        "inputs",
        "recovery",
        "working_directory",
        "evidence_directory",
        "handling_decision",
    }
    assert type(config["schema_version"]) is int
    assert config["schema_version"] == 1 and config["scope_id"] == SCOPE
    assert config["stage"] == stage and stage in SENTINELS
    commit = config["source_commit"]
    assert type(commit) is str and len(commit) == 40
    assert all(character in "0123456789abcdef" for character in commit)
    assert config["source_commit"] == os.environ.get("GITHUB_SHA")
    assert config["entry_sha256"] == base.sha256(Path(__file__).resolve())
    assert type(config["handling_decision"]) is str
    assert config["handling_decision"].strip()
    rows = config["inputs"]
    assert type(rows) is list and len(rows) == len(INPUT_HASHES)
    assert all(
        type(row) is dict
        and set(row)
        == {
            "id",
            "path",
            "sha256",
            "bytes",
        }
        for row in rows
    )
    inputs = {row["id"]: row for row in rows}
    assert len(inputs) == len(rows)
    assert {key: row["sha256"] for key, row in inputs.items()} == INPUT_HASHES
    assert len({row["path"] for row in rows}) == len(rows)
    assert all(type(row["bytes"]) is int and row["bytes"] > 0 for row in rows)
    root = Path(inputs["catalogue"]["path"]).parent
    assert all(
        Path(inputs[key]["path"]) == root / name
        for key, name in DEPLOYMENT_NAMES.items()
    )
    verify_inputs(inputs)
    recovery = strict_json(base.bound_file(config["recovery"]).read_bytes())
    assert recovery["status"] == recovery["independent_review"] == "PASS"
    assert recovery["checkpoint_commit"] == config["source_commit"]
    assert recovery["input_hashes"] == INPUT_HASHES
    work = base.private_directory(config["working_directory"])
    evidence = base.private_directory(config["evidence_directory"])
    assert work != evidence and not work.is_relative_to(evidence)
    assert not evidence.is_relative_to(work)
    assert not any(
        base.regular_path(row["path"]).is_relative_to(directory)
        for row in rows
        for directory in (work, evidence)
    )
    return SimpleNamespace(
        inputs=inputs,
        fixture=read_fixture(),
        work=work,
        evidence=evidence,
        source_commit=config["source_commit"],
    )


def runtime():
    return legacy().runtime()


def native_imports():
    return legacy().native_imports()


def source_contract():
    return legacy().source_contract()


def snapshotter(app):
    return legacy().snapshotter(app)


def prepare_source(app, module, config, owned):
    return legacy().prepare_source(app, module, config, owned)


def cleanup(app, owned):
    return legacy().cleanup(app, owned)


def reference_shapes(app, part, inputs, work, owned):
    """Read expected shapes through native restore, not the product importer."""
    references = {}
    for family in FAMILIES:
        document = legacy().open_copy(
            app,
            inputs[family.lower() + "_model"],
            work,
            family + "-copy.FCStd",
            owned,
        )
        name = document.Name
        try:
            assert tuple(
                obj.Name for obj in document.Objects
            ) == component_names(
                family,
            )
            assert all(
                obj.TypeId == "Part::Feature" for obj in document.Objects
            )
            references[family] = {
                obj.Name: part.Shape(obj.Shape) for obj in document.Objects
            }
        finally:
            assert app.listDocuments().get(name) is document
            app.closeDocument(name)
        assert name not in app.listDocuments()
    return references


class ToCrossingChairs(unittest.TestCase):
    def test_readiness(self):
        self._execute("readiness")

    def test_fixed_four(self):
        self._execute("native")

    def _execute(self, stage):
        config = configuration(stage)
        started = time.monotonic()
        result = dict(
            status="RUNNING",
            stage=stage,
            scope_id=SCOPE,
            test_id=self.id(),
            source_commit=config.source_commit,
            fixture_sha256=FIXTURE_SHA256,
            physical_fit="NOT_PROVED",
            checks=dict.fromkeys(expected_checks(stage), 0),
            input_sha256=dict(INPUT_HASHES),
            stage_timings={},
            failures=[],
        )
        app, owned, failure = None, {}, None
        try:
            app, session = runtime()
            assert not app.GuiUp and not app.listDocuments()
            part = native_imports()
            with ExitStack() as guards:
                for owner, name in (
                    (app, "newDocument"),
                    (app, "openDocument"),
                    (part, "Shape"),
                    (part, "makeCompound"),
                ):
                    guards.enter_context(
                        patch.object(
                            owner,
                            name,
                            side_effect=AssertionError(
                                "Readiness attempted document or geometry creation"
                            ),
                        )
                    )
                session.routing_record()
                result["checks"]["binding_checks"] = 1
                source_contract()
                snapshotter(app)
                selected = catalogues(config.inputs)
                assert set(selected) == set(FAMILIES)
                result["checks"]["catalogue_contracts"] = len(selected)
                result["checks"]["source_frame_inputs"] = validate_fixture(
                    config.fixture,
                )
                comparator = shared().load_comparator(ROOT)
                result["checks"]["comparator_negative_controls"] = (
                    shared().comparator_controls(comparator)
                )
            assert not app.listDocuments() and app.ActiveDocument is None
            result["stage_timings"]["readiness_seconds"] = (
                time.monotonic() - started
            )
            if stage == "native":
                native_started = time.monotonic()
                self._journey(
                    app, session, config, selected, comparator, owned, result
                )
                result["stage_timings"]["native_seconds"] = (
                    time.monotonic() - native_started
                )
            assert result["checks"] == expected_checks(stage)
        except BaseException as error:
            failure = error
            record_failure(config, result, "native", error)
        finally:
            cleanup_started = time.monotonic()
            try:
                verify_inputs(config.inputs)
                result["input_bindings_unchanged"] = True
            except BaseException as error:
                result["input_bindings_unchanged"] = False
                record_failure(config, result, "input", error)
                if failure is None:
                    failure = error
            try:
                if app is None:
                    raise RuntimeError(
                        "Runtime did not provide cleanup evidence"
                    )
                cleanup(app, owned)
                result["remaining_documents"] = len(app.listDocuments())
                result["owned_documents_closed"] = True
            except BaseException as error:
                record_failure(config, result, "cleanup", error)
                result["owned_documents_closed"] = False
                if failure is None:
                    failure = error
            result["stage_timings"]["cleanup_seconds"] = (
                time.monotonic() - cleanup_started
            )
            result["stage_timings"]["total_seconds"] = (
                time.monotonic() - started
            )
            result["status"] = "PASS" if failure is None else "FAIL"
            if failure is None:
                result["sentinel"] = SENTINELS[stage]
            write_result(config, result)
        if failure is not None:
            raise AssertionError("TO_CROSSING_NATIVE_FAILED") from None
        print("\n" + SENTINELS[stage], flush=True)

    def _journey(
        self, app, session, config, selected, comparator, owned, result
    ):
        from tracktemplate.adapters.freecad import chair_catalogue_preview
        from tracktemplate.compatibility.chair_reference_preview import (
            _open_source_context,
        )

        module = session.module
        part = native_imports()
        references = reference_shapes(
            app,
            part,
            config.inputs,
            config.work,
            owned,
        )
        assert not app.listDocuments()
        source = prepare_source(app, module, config, owned)
        foreign = app.newDocument("TOUnrelatedWitness")
        owned[foreign.Name] = foreign
        marker = foreign.addObject("App::FeaturePython", "Keep")
        marker.addProperty("App::PropertyString", "ProofValue")
        marker.ProofValue = "Preserve unrelated document"
        foreign.recompute()
        app.setActiveDocument(source.Name)
        context = _open_source_context(module, source, "TO-001", "Crossings")
        assert len(context[1]["positions"]) == 168
        assert context[1]["geometry_signature"] == SOURCE_ANALYSIS_SHA256
        state = snapshotter(app)
        # Preserve the retained treatment of FreeCAD's derived group cache.
        for document in app.listDocuments().values():
            for obj in document.Objects:
                if obj.TypeId == "App::DocumentObjectGroup":
                    getattr(obj, "Shape", None)
        baseline = state()
        captured = {}
        factory_name = "_private_catalogue_turnout_crossing_preview_factory"
        original = getattr(session, factory_name)

        def capture(*args):
            captured.update(args[1])
            return original(*args)

        with (
            observe_stored_checks(result["checks"]),
            patch.object(session, factory_name, capture),
            patch.object(
                app,
                "openDocument",
                side_effect=AssertionError(
                    "Product reopened an external document"
                ),
            ),
        ):
            preview_result = (
                session.preview_private_catalogue_turnout_crossing_chairs(
                    source,
                    "TO-001",
                    config.inputs["catalogue"]["path"],
                )
            )
        preview = app.getDocument(preview_result["document_name"])
        assert preview is not None and preview.Name not in owned
        owned[preview.Name] = preview
        self._preview(
            preview_result,
            preview,
            captured,
            config.fixture,
            references,
            comparator,
            result,
        )
        assert [
            row for row in state()["documents"] if row["name"] != preview.Name
        ] == baseline["documents"]
        assert (
            _open_source_context(module, source, "TO-001", "Crossings")
            == context
        )
        assert preview.UndoCount == 1
        shapes = tuple(part.Shape(obj.Shape) for obj in preview.Objects)
        preview.undo()
        assert not preview.Objects
        preview.redo()
        assert tuple(obj.Name for obj in preview.Objects) == layer_names()
        assert all(
            chair_catalogue_preview._same_presented_shape(obj.Shape, shape)
            for obj, shape in zip(preview.Objects, shapes)
        )
        result["checks"]["preview_undo_redo"] = 1
        self._rollback(app, session, source, selected, config, state, result)
        assert (
            _open_source_context(module, source, "TO-001", "Crossings")
            == context
        )
        preview_name = preview.Name
        app.closeDocument(preview_name)
        assert preview_name not in app.listDocuments()
        assert state()["documents"] == baseline["documents"]
        result["preview_disposal_preserves_source_and_foreign"] = True

    def _preview(
        self, receipt, preview, placements, fixture, shapes, comparator, result
    ):
        result["checks"]["successful_components"] = check_structure(
            receipt, preview, fixture
        )
        result["checks"]["source_frame_comparisons"] = compare_frames(
            placements, fixture
        )
        comparisons = []
        for row in fixture["positions"]:
            family = row["family"]
            for name in component_names(family):
                (child,) = preview.getObject(
                    family + "_" + name
                ).Shape.childShapes()
                comparison = comparator["_compare_component"](
                    child,
                    shapes[family][name],
                    SimpleNamespace(**component_frame(row, name)),
                )
                comparisons.append(
                    dict(
                        position_id=row["source_positions"][0]["position_id"],
                        component=name,
                        **comparison,
                    )
                )
                if name == "base_plinth":
                    wrong = copy.deepcopy(row["body"])
                    wrong["origin_mm"][0] += 1
                    with self.assertRaises(AssertionError):
                        comparator["_compare_component"](
                            child,
                            shapes[family][name],
                            SimpleNamespace(**wrong),
                        )
                    result["checks"]["wrong_frame_rejections"] += 1
        assert len(comparisons) == 135
        result["checks"]["component_comparisons"] = len(comparisons)
        result["component_comparisons"] = comparisons

    def _rollback(self, app, session, source, selected, config, state, result):
        from tracktemplate.application import chair_crossing_pair_catalogue

        reader = chair_crossing_pair_catalogue
        before, registry = state(), dict(app.listDocuments())
        active, original = app.ActiveDocument, reader._read
        witnessed = []

        def late_read(path):
            content = original(path)
            if str(path) == selected["DD"].model_path and (
                app.ActiveDocument is not active
            ):
                preview = app.ActiveDocument
                assert preview not in registry.values()
                counts = {
                    name: len(preview.getObject(name).Shape.childShapes())
                    for name in layer_names()[2:]
                }
                witnessed.append(
                    check_layers(
                        [obj.Name for obj in preview.Objects],
                        counts,
                    )
                )
                return content + b"\n"
            return content

        stored = dict(stored_compound_checks=0, stored_child_checks=0)
        with (
            observe_stored_checks(stored),
            patch.object(reader, "_read", late_read),
        ):
            with self.assertRaises(reader.CatalogueChairError):
                session.preview_private_catalogue_turnout_crossing_chairs(
                    source,
                    "TO-001",
                    config.inputs["catalogue"]["path"],
                )
        assert witnessed == [135]
        assert stored == dict(
            stored_compound_checks=135, stored_child_checks=135
        )
        assert app.listDocuments() == registry and app.ActiveDocument is active
        assert state() == before
        reader.verify_turnout_crossing_catalogue(tuple(selected.values()))
        result["checks"]["rolled_back_components"] = witnessed[0]
