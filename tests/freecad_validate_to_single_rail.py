"""Import-safe native qualification of twelve fixed TO-001 assemblies.

Select one named unittest in a fresh, externally guarded hosted process.
Readiness opens no document and constructs no shape. The full test reuses
retained catalogue geometry and independent source frames. Neither method
supplies GUI, physical-fit, production or phase-exit acceptance.
"""

from contextlib import ExitStack
import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import struct
import sys
import time
import traceback
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = "tests/fixtures/phase9b-to-single-rail-frames.json"
FIXTURE_SHA256 = (
    "407040d01dd0f9c8ac275d7e4d40c928ea32a5da0a05c853bf3a1de4221a8d4b"
)
SHARED_PATH = "tests/hosted_l1_current_source_suite.py"
SHARED_SHA256 = (
    "20cd1694979830099e1e6988300c1c8bc9ea1dbc59ad7a5cef1832a0fe4bcc71"
)
SCOPE = "TO-001-fixed-single-rail-native-v1"
SENTINELS = {
    "readiness": "Fixed TO single-rail hosted readiness passed",
    "native": "Fixed TO single-rail hosted native validation passed",
}
INPUT_HASHES = {
    "catalogue":
    "f1016a97f35cc87cca9e0b9f09e70ea1cec4620c43d9451430dfb299eed6b885",
    "inventory":
    "df8c942b3cf74508e45b8ab220c17db53912da7857109f656cda3d5f81236e93",
    "context_recipes":
    "e484b241fb8edc435b12a162f5eec99ba6c3a3f36100d47fb624fd07956e90a9",
    "supplemental_recipes":
    "fad0ddaa24eb582f9c669cc5dce9f7b68e0df66719466a3f5c1208f74132335f",
    "l1_model":
    "a0289c046b6ae8cb1e2df88a8f6a1f3f0dc79f7a0ae1870d0b3b13154e0eb042",
    "s1_model":
    "a3c8c99a67d9f18b0ee5668400a8bf94f9f39fa641a22da7477141b74cc120eb",
    "validation_receipt":
    "a91d7e9bc8f74e07a5ce8afdbe3f96c018504a40b7e6f13fa259c5c366ac24ad",
    "execution_receipt":
    "77967d8ee640c8aab3a2ec47d2664cf075e1d87328dff0fc1f858ab1c1ed5661",
    "build_receipt":
    "b3a5d11827ade1c961219efd50488aaf46fa14ca449059fd22f371e1e71b9a65",
    "to_base_fixture":
    "0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c",
}
HELPERS = {
    "archive": (
        "tests/freecad_validate_phase9b_s1_reference_preview.py",
        "caeb23ae8a01407b636ceafe2d5ec0aed647cc9c479f762824a2291e0c2494f6",
    ),
    "state": (
        "tests/freecad_validate_phase9b_chair_l1_model.py",
        "257fd6dc196e9d8a51ccc277a7c8b698ff7a66c1f241225d981d6a01651b22c6",
    ),
}


def shared():
    """Reuse the frozen import-safe helper; do not run its XO journey."""
    path = ROOT / SHARED_PATH
    assert hashlib.sha256(path.read_bytes()).hexdigest() == SHARED_SHA256
    import hosted_l1_current_source_suite as helper

    assert Path(helper.__file__).resolve() == path
    return helper


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def constant(_value):
        raise ValueError("Nonfinite JSON value")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def _frozen_fixture():
    content = (ROOT / FIXTURE).read_bytes()
    assert hashlib.sha256(content).hexdigest() == FIXTURE_SHA256
    return strict_json(content)


def identities():
    rails = ("main-side-stock-rail", "curved-switch-and-closure-rail",
             "straight-switch-and-closure-rail", "turnout-side-stock-rail")
    selected = (("S13", 1), ("S13", 2), ("S13", 3), ("S13", 4),
                ("T1", 1), ("T1", 2), ("T1", 3), ("T1", 4),
                ("T2", 2), ("T2", 3), ("T2", 4), ("T14", 2))
    return sorted((
        f"TO-001:chair:to-001-timber-{timber.lower()}:{rails[rail - 1]}",
        f"TO-001:rail:{rails[rail - 1]}", f"TO-001:timber:{timber}",
        "S1" if (timber, rail) == ("T2", 4) else "L1", rail,
    ) for timber, rail in selected)


def validate_fixture(data):
    frozen = _frozen_fixture()
    assert type(data) is dict and set(data) == set(frozen)
    assert type(data["schema_version"]) is int
    assert {key: value for key, value in data.items() if key != "positions"} == {
        key: value for key, value in frozen.items() if key != "positions"
    }
    assert type(data["positions"]) is list and len(data["positions"]) == 12
    count = 0
    for row, expected in zip(data["positions"], identities()):
        assert type(row) is dict and set(row) == {
            "position_id", "rail_id", "timber_id", "family",
            "source_rail_code", "source_receipt_sha256", "body",
            "fixing_frames",
        }
        assert tuple(row[key] for key in (
            "position_id", "rail_id", "timber_id", "family",
            "source_rail_code",
        )) == expected
        assert type(row["source_rail_code"]) is int
        group = ("corrected_five" if expected[-1] in (1, 3)
                 else "retained_seven")
        assert row["source_receipt_sha256"] == data[
            "source_receipt_sha256"][group]
        assert type(row["fixing_frames"]) is list
        assert len(row["fixing_frames"]) == (4 if row["family"] == "L1" else 3)
        for frame in (row["body"], *row["fixing_frames"]):
            assert type(frame) is dict and set(frame) == {
                "origin_mm", "x_axis", "y_axis",
            }
            for field, size in (("origin_mm", 3), ("x_axis", 2), ("y_axis", 2)):
                values = frame[field]
                assert type(values) is list and len(values) == size
                for value in values:
                    assert type(value) in (int, float)
                    try:
                        valid = math.isfinite(value)
                    except OverflowError:
                        valid = False
                    assert valid, "Nonfinite frame value"
            count += 1
    assert count == 59
    return count


def read_fixture():
    data = _frozen_fixture()
    validate_fixture(data)
    return data


def component_names(family):
    if family not in ("L1", "S1"):
        raise ValueError("Unknown fixed TO family")
    bodies, fixings = (7, 16) if family == "L1" else (5, 12)
    return (*(f"Part_{index:02d}" for index in range(bodies)),
            "SourceFixing", *(f"SourceFixing{index:03d}"
                              for index in range(1, fixings)))


def component_frame(row, name):
    index = component_names(row["family"]).index(name)
    bodies = 7 if row["family"] == "L1" else 5
    return (row["body"] if index < bodies else
            row["fixing_frames"][(index - bodies) // 4])


def layer_names():
    return ("ReferenceRails", "ReferenceTimbers", *(
        family + "_" + name for family in ("L1", "S1")
        for name in component_names(family)
    ))


def check_layers(names, counts):
    assert tuple(names) == layer_names() and len(names) == 42
    assert set(counts) == set(layer_names()[2:])
    assert all(type(value) is int and value == (
        11 if name.startswith("L1_") else 1
    ) for name, value in counts.items())
    assert sum(counts.values()) == 270
    return 270


def expected_checks(stage):
    assert stage in SENTINELS
    values = dict(binding_checks=1, catalogue_contracts=2,
                  source_frame_inputs=59, comparator_negative_controls=8,
                  source_frame_comparisons=0, component_comparisons=0,
                  successful_components=0, rolled_back_components=0,
                  wrong_frame_rejections=0, preview_undo_redo=0)
    if stage == "native":
        values.update(source_frame_comparisons=59, component_comparisons=270,
                      successful_components=270, rolled_back_components=270,
                      wrong_frame_rejections=2, preview_undo_redo=1)
    return values


def verify_inputs(inputs):
    for record in inputs.values():
        shared().bound_file(record)


def configuration(stage):
    """Read a reviewed runner configuration, not grant execution authority."""
    assert sys.flags.optimize == 0
    assert os.environ.get("GITHUB_ACTIONS") == "true"
    assert os.environ.get("RUNNER_ENVIRONMENT") == "github-hosted"
    assert os.environ.get("GITHUB_RUN_ATTEMPT") == "1"
    assert os.environ.get("GITHUB_RUN_ID", "").isdigit()
    base = shared()
    path = base.regular_path(os.environ["TRACKTEMPLATE_TO_RUN_CONFIG"])
    assert base.sha256(path) == os.environ[
        "TRACKTEMPLATE_TO_RUN_CONFIG_SHA256"]
    config = strict_json(path.read_bytes())
    assert set(config) == {
        "schema_version", "scope_id", "stage", "source_commit",
        "entry_sha256", "inputs", "recovery", "working_directory",
        "evidence_directory", "handling_decision",
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
    assert all(type(row) is dict and set(row) == {
        "id", "path", "sha256", "bytes",
    } for row in rows)
    inputs = {row["id"]: row for row in rows}
    assert len(inputs) == len(rows)
    assert {key: row["sha256"] for key, row in inputs.items()} == INPUT_HASHES
    assert len({row["path"] for row in rows}) == len(rows)
    assert all(type(row["bytes"]) is int and row["bytes"] > 0 for row in rows)
    verify_inputs(inputs)
    recovery = strict_json(base.bound_file(config["recovery"]).read_bytes())
    assert recovery["status"] == recovery["independent_review"] == "PASS"
    assert recovery["checkpoint_commit"] == config["source_commit"]
    assert recovery["input_hashes"] == INPUT_HASHES
    work = base.private_directory(config["working_directory"])
    evidence = base.private_directory(config["evidence_directory"])
    assert work != evidence and not work.is_relative_to(evidence)
    assert not evidence.is_relative_to(work)
    assert not any(base.regular_path(row["path"]).is_relative_to(directory)
                   for row in rows for directory in (work, evidence))
    return SimpleNamespace(inputs=inputs, fixture=read_fixture(), work=work,
                           evidence=evidence,
                           source_commit=config["source_commit"])


def runtime():
    app, session, _routing = shared().load_runtime(ROOT)
    return app, session


def native_imports():
    import Part
    from tracktemplate.adapters.freecad import chair_catalogue_preview

    assert callable(chair_catalogue_preview._import_components)
    return Part


def catalogues(inputs):
    from tracktemplate.application import chair_catalogue as reader

    selected = {}
    approved = {row["path"]: row["sha256"] for row in inputs.values()}
    for family in ("L1", "S1"):
        item = reader.prepare_catalogue_chair(
            inputs["catalogue"]["path"], family, run="existing-02",
        )
        record = inputs[family.lower() + "_model"]
        assert item.model_sha256 == record["sha256"]
        assert item.model_path == record["path"]
        assert tuple(value.name for value in item.components) == component_names(
            family,
        )
        assert all(approved.get(binding.path) == binding.sha256
                   for binding in item.bindings)
        reader.verify_catalogue_sources(item)
        selected[family] = item
    return selected


def snapshotter(app):
    base = shared()
    namespace = dict(App=app, io=io, struct=struct, zipfile=zipfile,
                     hashlib=hashlib)
    with patch.dict(base.HELPERS, HELPERS):
        archive = base.extract_helper(
            ROOT, "archive", ("_archive_state",), namespace=namespace,
        )["_archive_state"]
        return base.extract_helper(
            ROOT, "state", ("_document_state",),
            namespace={**namespace, "_archive_state": archive},
        )["_document_state"]


def source_contract():
    contract_path = ROOT / (
        "reference/contracts/phase1-chair-analysis-persistence.json"
    )
    assert shared().sha256(contract_path) == (
        "6cb871ba642c2336ad57e4befc4d5ce69fb9705631975d85f4cf0d6827105b3f"
    )
    contract = strict_json(contract_path.read_bytes())
    assert contract["fixture"]["sha256"] == INPUT_HASHES["to_base_fixture"]
    return contract


def open_copy(app, record, work, name, owned):
    """Track owned copies even if native restoration raises after creation."""
    source = shared().bound_file(record)
    target = work / name
    assert not target.exists()
    with source.open("rb") as reader, target.open("xb") as writer:
        shutil.copyfileobj(reader, writer)
    target.chmod(0o600)
    assert shared().sha256(target) == shared().sha256(source)
    previous = dict(app.listDocuments())
    try:
        document = app.openDocument(str(target))
    finally:
        for name, value in app.listDocuments().items():
            if name not in previous and value.FileName == str(target):
                owned[name] = value
    assert document is not None and owned.get(document.Name) is document
    assert app.listDocuments() == {**previous, document.Name: document}
    return document


def reference_shapes(app, part, inputs, work, owned):
    """Read expected shapes through native restore, not the product importer."""
    references = {}
    for family in ("L1", "S1"):
        document = open_copy(app, inputs[family.lower() + "_model"], work,
                             family + "-copy.FCStd", owned)
        name = document.Name
        try:
            assert tuple(obj.Name for obj in document.Objects) == component_names(
                family,
            )
            assert all(obj.TypeId == "Part::Feature" for obj in document.Objects)
            references[family] = {
                obj.Name: part.Shape(obj.Shape) for obj in document.Objects
            }
        finally:
            assert app.listDocuments().get(name) is document
            app.closeDocument(name)
        assert name not in app.listDocuments()
    return references


def prepare_source(app, module, config, owned):
    """Compose the retained TO setup on a copy; do no export or save proof."""
    from tools.freecad_bridge import b14_recipe, turnout_recipe

    contract = source_contract()
    document = open_copy(app, config.inputs["to_base_fixture"], config.work,
                         "TO-001-copy.FCStd", owned)
    document.UndoMode = 1
    snapshot = b14_recipe.freecad_base_snapshot(
        module, document, expected_macro_version="10.2A8A7B15",
    )
    semantic = dict(snapshot["semantic"], macro_version="10.2A8A7B14")
    encoded = json.dumps(semantic, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8")
    assert hashlib.sha256(encoded).hexdigest() == contract[
        "fixture"]["semantic_sha256"]
    hosts = module.turnout_host_objects(document)
    host = turnout_recipe.select_turnout_host(
        hosts, module.object_string_property, module._integer_object_property,
    )
    created = module.create_curve_inheriting_c10_turnout(
        document, hosts[host["index"]], turnout_recipe.TURNOUT_CHAINAGE_MM,
        module.TURNOUT_HAND_LEFT, module.TURNOUT_ORIENTATION_FACING,
        turnout_recipe.TRACK_GAUGE_MM, turnout_recipe.FLANGEWAY_MM,
    )
    assert created["turnout_id"] == "TO-001"
    module.create_turnout_host_integration(document, "TO-001")
    module.analyse_entity_chair_positions(document, "turnout", "TO-001")
    return document


def cleanup(app, owned):
    errors = []
    for name, document in reversed(tuple(owned.items())):
        try:
            present = app.listDocuments().get(name)
            assert present is None or present is document
            if present is document:
                app.closeDocument(name)
            assert name not in app.listDocuments()
        except BaseException as error:
            errors.append(error)
    if app.listDocuments() or app.ActiveDocument is not None:
        errors.append(AssertionError("Document cleanup incomplete"))
    if errors:
        raise RuntimeError("Native document cleanup failed") from errors[0]


def write_result(config, result):
    shared().write_private_result(config.evidence, result)


class ToSingleRail(unittest.TestCase):
    def test_readiness(self):
        self._execute("readiness")

    def test_fixed_twelve(self):
        self._execute("native")

    def _execute(self, stage):
        config = configuration(stage)
        started = time.monotonic()
        result = dict(status="RUNNING", stage=stage, scope_id=SCOPE,
                      test_id=self.id(), source_commit=config.source_commit,
                      fixture_sha256=FIXTURE_SHA256, physical_fit="NOT_PROVED",
                      checks=dict.fromkeys(expected_checks(stage), 0),
                      input_sha256=dict(INPUT_HASHES), stage_timings={})
        app, owned, failure = None, {}, None
        try:
            app, session = runtime()
            assert not app.GuiUp and not app.listDocuments()
            part = native_imports()
            with ExitStack() as guards:
                for owner, name in ((app, "newDocument"), (app, "openDocument"),
                                    (part, "Shape"), (part, "makeCompound")):
                    guards.enter_context(patch.object(
                        owner, name, side_effect=AssertionError(
                            "Readiness attempted document or geometry creation"),
                    ))
                session.routing_record()
                result["checks"]["binding_checks"] = 1
                source_contract()
                snapshotter(app)
                selected = catalogues(config.inputs)
                assert set(selected) == {"L1", "S1"}
                result["checks"]["catalogue_contracts"] = len(selected)
                result["checks"]["source_frame_inputs"] = validate_fixture(
                    config.fixture,
                )
                comparator = shared().load_comparator(ROOT)
                result["checks"]["comparator_negative_controls"] = shared(
                ).comparator_controls(comparator)
            assert not app.listDocuments() and app.ActiveDocument is None
            result["stage_timings"]["readiness_seconds"] = (
                time.monotonic() - started
            )
            if stage == "native":
                native_started = time.monotonic()
                self._journey(app, session, config, selected, comparator,
                              owned, result)
                result["stage_timings"]["native_seconds"] = (
                    time.monotonic() - native_started
                )
            assert result["checks"] == expected_checks(stage)
        except BaseException as error:
            failure = error
            result["traceback"] = traceback.format_exc()
        finally:
            cleanup_started = time.monotonic()
            try:
                verify_inputs(config.inputs)
                result["input_bindings_unchanged"] = True
            except BaseException as error:
                result["input_bindings_unchanged"] = False
                result["input_traceback"] = traceback.format_exc()
                if failure is None:
                    failure = error
            try:
                if app is None:
                    raise RuntimeError("Runtime did not provide cleanup evidence")
                cleanup(app, owned)
                result["remaining_documents"] = len(app.listDocuments())
                result["owned_documents_closed"] = True
            except BaseException as error:
                result["cleanup_traceback"] = traceback.format_exc()
                result["owned_documents_closed"] = False
                if failure is None:
                    failure = error
            result["stage_timings"]["cleanup_seconds"] = (
                time.monotonic() - cleanup_started
            )
            result["stage_timings"]["total_seconds"] = time.monotonic() - started
            result["status"] = "PASS" if failure is None else "FAIL"
            if failure is None:
                result["sentinel"] = SENTINELS[stage]
            write_result(config, result)
        if failure is not None:
            raise failure
        print("\n" + SENTINELS[stage], flush=True)

    def _journey(self, app, session, config, selected, comparator, owned, result):
        from tracktemplate.adapters.freecad import chair_catalogue_preview
        from tracktemplate.compatibility.chair_reference_preview import (
            _open_source_context,
        )

        module = session.module
        part = native_imports()
        references = reference_shapes(
            app, part, config.inputs, config.work, owned,
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
        context = _open_source_context(module, source, "TO-001", "L1/S1")
        assert len(context[1]["positions"]) == 168
        assert context[1]["geometry_signature"] == config.fixture[
            "source_analysis_sha256"]
        state = snapshotter(app)
        # Preserve the retained treatment of FreeCAD's derived group cache.
        for document in app.listDocuments().values():
            for obj in document.Objects:
                if obj.TypeId == "App::DocumentObjectGroup":
                    getattr(obj, "Shape", None)
        baseline = state()
        captured = []
        factory_name = "_private_catalogue_turnout_single_rail_preview_factory"
        original = getattr(session, factory_name)

        def capture(*args):
            captured.extend(args[1])
            return original(*args)

        with (patch.object(session, factory_name, capture),
              patch.object(app, "openDocument", side_effect=AssertionError(
                  "Product reopened an external document"))):
            preview_result = session.preview_private_catalogue_turnout_single_rail_chairs(
                source, "TO-001", config.inputs["catalogue"]["path"],
            )
        preview = app.getDocument(preview_result["document_name"])
        assert preview is not None and preview.Name not in owned
        owned[preview.Name] = preview
        self._preview(preview_result, preview, captured, config.fixture,
                      references, comparator, result)
        assert [row for row in state()["documents"]
                if row["name"] != preview.Name] == baseline["documents"]
        assert _open_source_context(module, source, "TO-001", "L1/S1") == context
        assert preview.UndoCount == 1
        shapes = tuple(part.Shape(obj.Shape) for obj in preview.Objects)
        preview.undo()
        assert not preview.Objects
        preview.redo()
        assert tuple(obj.Name for obj in preview.Objects) == layer_names()
        assert all(chair_catalogue_preview._same_presented_shape(obj.Shape, shape)
                   for obj, shape in zip(preview.Objects, shapes))
        result["checks"]["preview_undo_redo"] = 1
        self._rollback(app, session, source, selected, config, state, result)
        assert _open_source_context(module, source, "TO-001", "L1/S1") == context
        preview_name = preview.Name
        app.closeDocument(preview_name)
        assert preview_name not in app.listDocuments()
        assert state()["documents"] == baseline["documents"]
        result["preview_disposal_preserves_source_and_foreign"] = True

    def _preview(self, receipt, preview, placements, fixture, shapes,
                 comparator, result):
        assert (receipt["placement_count"], receipt["component_count"],
                receipt["family_count"], receipt["layer_count"]) == (12, 40, 2, 42)
        assert receipt["project_status"] == "reference-only"
        assert receipt["intended_uses"] == ["private-development"]
        assert receipt["production_geometry_authorized"] is False
        assert receipt["geometry_rebuilt"] is False
        assert not preview.FileName and not preview.Temporary
        source = receipt["source_receipt"]
        assert source["source_document_mutation"] is False
        assert source["model_support_adjustments_applied"] is False
        assert source["analysis_position_count"] == 168
        assert source["represented_source_position_count"] == 12
        assert source["selected_family_counts"] == {"L1": 11, "S1": 1}
        assert len(source["corrected_heel_positions"]) == 5
        assert len(source["remaining_positions"]) == 156
        expected = {row["position_id"]: row for row in fixture["positions"]}
        assert [value.position_id for value in placements] == sorted(expected)
        comparisons = []
        for actual in placements:
            row = expected[actual.position_id]
            assert (actual.family, actual.rail_id, actual.timber_id) == (
                row["family"], row["rail_id"], row["timber_id"],
            )
            assert len(actual.fixing_frames) == len(row["fixing_frames"])
            for frame, target in zip((actual, *actual.fixing_frames),
                                     (row["body"], *row["fixing_frames"])):
                shared().compare_frame(frame, target)
                result["checks"]["source_frame_comparisons"] += 1
        counts = {}
        for family in ("L1", "S1"):
            family_receipt = receipt["families"][family]
            rows = [row for row in fixture["positions"]
                    if row["family"] == family]
            assert family_receipt["source_model_sha256"] == fixture[
                "model_sha256"][family]
            assert family_receipt["excluded_source_components"] == []
            assert [row["position_id"] for row in family_receipt[
                "placements"]] == [row["position_id"] for row in rows]
            for name in component_names(family):
                layer = family + "_" + name
                children = preview.getObject(layer).Shape.childShapes()
                counts[layer] = len(children)
                assert len(children) == len(rows)
                for child, row in zip(children, rows):
                    frame = component_frame(row, name)
                    comparison = comparator["_compare_component"](
                        child, shapes[family][name], SimpleNamespace(**frame),
                    )
                    comparisons.append(dict(position_id=row["position_id"],
                                            component=name, **comparison))
                if name == "Part_00":
                    wrong = copy.deepcopy(rows[0]["body"])
                    wrong["origin_mm"][0] += 1
                    with self.assertRaises(AssertionError):
                        comparator["_compare_component"](
                            children[0], shapes[family][name],
                            SimpleNamespace(**wrong),
                        )
                    result["checks"]["wrong_frame_rejections"] += 1
        result["checks"]["successful_components"] = check_layers(
            [obj.Name for obj in preview.Objects], counts,
        )
        result["checks"]["component_comparisons"] = len(comparisons)
        assert len(comparisons) == 270
        result["component_comparisons"] = comparisons

    def _rollback(self, app, session, source, selected, config, state, result):
        from tracktemplate.application import chair_catalogue as reader

        before, registry = state(), dict(app.listDocuments())
        active = app.ActiveDocument
        original = reader._read
        witnessed = []

        def late_read(path):
            content = original(path)
            if str(path) == selected["L1"].model_path and (
                    app.ActiveDocument is not active):
                preview = app.ActiveDocument
                assert preview not in registry.values()
                counts = {name: len(preview.getObject(name).Shape.childShapes())
                          for name in layer_names()[2:]}
                witnessed.append(check_layers(
                    [obj.Name for obj in preview.Objects], counts,
                ))
                return content + b"\n"
            return content

        with patch.object(reader, "_read", late_read):
            with self.assertRaisesRegex(reader.CatalogueChairError,
                                        "Source binding changed"):
                session.preview_private_catalogue_turnout_single_rail_chairs(
                    source, "TO-001", config.inputs["catalogue"]["path"],
                )
        assert witnessed == [270]
        assert app.listDocuments() == registry and app.ActiveDocument is active
        assert state() == before
        for item in selected.values():
            reader.verify_catalogue_sources(item)
        result["checks"]["rolled_back_components"] = witnessed[0]
