"""Import-safe, private-input L1 tests for FreeCAD's unittest runner.

Invoke exactly one named test in each guarded GitHub process. The external
reviewed launcher owns limits, telemetry, process containment and cleanup.
This entry never launches processes or publishes evidence. Raw diagnostics
and its result belong in the approved private evidence directory.

Expected railway frames remain in the ten approved private inputs. The
original component comparator and canonical Generate driver are extracted
unchanged from hash-bound tracked tests. No private helper is executed.
"""

import ast
from contextlib import ExitStack
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import runpy
import shutil
import stat
import sys
import time
import traceback
from types import SimpleNamespace
import unittest
from unittest.mock import patch


PROFILE = (
    "linux-x86_64-flatpak-freecad-1.1.4-py3.13.15-"
    "qt6.11.2-coin4.0.10"
)
CASES = (("reference-600", 600.0, 355), ("changed-900", 900.0, 354),
         ("returned-600", 600.0, 355))
COMPONENT_NAMES = (
    *(f"Part_{index:02d}" for index in range(7)),
    "SourceFixing", *(f"SourceFixing{index:03d}" for index in range(1, 16)),
)
REPRESENTATIVES = (
    "XO-001:chair:xo-001-a-s13:main-side-stock-rail",
    "XO-001:chair:xo-001-b-s13:straight-switch-and-closure-rail",
)
INPUT_IDS = (
    "catalogue", "inventory", "context_recipes", "supplemental_recipes",
    "l1_model", "validation_receipt", "execution_receipt", "build_receipt",
    "reference_document", "expected_frames",
)
HELPERS = {
    "comparator": (
        "tests/freecad_validate_phase9b_catalogue_p_placement.py",
        "764f3862d7b846a8836e6f26ea79e22579b1b33cd3496950189218a6080bf61a",
    ),
    "generate": (
        "tests/freecad_validate_phase9b_p_dependent_recalculation.py",
        "4527a70f64188599740f15459b7054649f3c497a89d9243b9489f345fbfaa705",
    ),
    "snapshot": (
        "tests/freecad_validate_phase8_crossover_edit_recovery.py",
        "d4c95244c3eb0dbeb53441e9937b2efa584c3fe783fae3f434635fba24e84f17",
    ),
}
SENTINELS = {
    "readiness": "L1 current-source hosted readiness passed",
    "native": "L1 current-source hosted native validation passed",
}


def identities():
    """Return the ten accepted identities, with no derived coordinates."""
    values = []
    rails = ("main-side-stock-rail", "straight-switch-and-closure-rail")
    for side in ("A", "B"):
        for timber in ("S13", "T1", "T2"):
            for rail in (rails if timber != "T2" else rails[1:]):
                values.append((
                    f"XO-001:chair:xo-001-{side.lower()}-{timber.lower()}:{rail}",
                    f"XO-001-{side}001:rail:{rail}", f"XO-001:{side}:{timber}",
                ))
    return tuple(values)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def regular_path(path):
    """Reject relative, linked, absent or non-regular input paths."""
    path = Path(path)
    assert path.is_absolute() and path.resolve(strict=True) == path
    assert all(not item.is_symlink() for item in (path, *path.parents))
    assert stat.S_ISREG(path.stat().st_mode), "input is not a regular file"
    return path


def bound_file(record):
    path = regular_path(record["path"])
    assert path.stat().st_size == record["bytes"], "input size differs"
    assert sha256(path) == record["sha256"], "input hash differs"
    return path


def private_directory(path):
    path = Path(path)
    assert path.is_absolute() and path.resolve(strict=True) == path
    assert all(not item.is_symlink() for item in (path, *path.parents))
    assert path.is_dir() and path.stat().st_mode & 0o077 == 0, (
        "private evidence directory must deny group and other access"
    )
    assert path.stat().st_uid == os.getuid()
    return path


def validate_expectations(data):
    """Reject incomplete 150-frame input before any document is opened."""
    assert set(data) == {case[0] for case in CASES}
    count = 0
    for label, _radius, _positions in CASES:
        assert set(data[label]) == {item[0] for item in identities()}
        for identity, rail, timber in identities():
            record = data[label][identity]
            assert record["family"] == "L1"
            assert (record["rail_id"], record["timber_id"]) == (rail, timber)
            assert len(record["fixing_frames"]) == 4
            for frame in (record["body"], *record["fixing_frames"]):
                assert set(frame) == {"origin_mm", "x_axis", "y_axis"}
                for name, size in (("origin_mm", 3), ("x_axis", 2),
                                   ("y_axis", 2)):
                    values = frame[name]
                    assert isinstance(values, (tuple, list))
                    assert len(values) == size
                    assert all(type(value) in (int, float)
                               and math.isfinite(value) for value in values)
                count += 1
    assert count == 150
    return count


def compare_frame(actual, expected):
    """Use PR221's arithmetic budget, separately from physical fit."""
    for field in ("origin_mm", "x_axis", "y_axis"):
        observed, required = getattr(actual, field), expected[field]
        assert len(observed) == len(required)
        for value, mark in zip(observed, required):
            assert math.isfinite(value) and math.isfinite(mark)
            budget = 128 * sys.float_info.epsilon * max(
                1000, abs(value), abs(mark),
            )
            assert abs(value - mark) <= budget, (field, value, mark, budget)


def extract_helper(root, key, functions, constants=(), namespace=None):
    """Reuse original tracked definitions with exact file-hash binding."""
    relative, digest = HELPERS[key]
    path = regular_path(root / relative)
    assert sha256(path) == digest, "retained helper hash differs"
    tree = ast.parse(path.read_text(), filename=str(path))
    values = {} if namespace is None else dict(namespace)
    selected, found = [], {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in functions:
            assert not node.decorator_list
            selected.append(node)
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in constants:
                assert target.id not in found
                found[target.id] = ast.literal_eval(node.value)
    assert sorted(node.name for node in selected) == sorted(functions)
    assert set(found) == set(constants)
    values.update(found)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path),
                 "exec"), values)
    return values


def load_comparator(root):
    return extract_helper(root, "comparator", ("_point", "_compare_component"),
                          ("EPSILON_MM",), {"math": math})


def comparator_controls(helpers):
    """Exercise the unchanged comparator without constructing geometry."""
    frame = SimpleNamespace(origin_mm=(0, 0, 0), x_axis=(1, 0), y_axis=(0, 1))
    shape = SimpleNamespace(
        isValid=lambda: True, isNull=lambda: False, ShapeType="Solid",
        Orientation="Forward", Volume=1.0, Area=6.0, Length=12.0,
        getTolerance=lambda _kind: 1.0e-7,
        Solids=[SimpleNamespace(isClosed=lambda: True, isValid=lambda: True,
                                Volume=1.0)],
        Shells=[object()], Faces=[SimpleNamespace(Orientation="Forward")],
        Wires=[object()], Edges=[object()],
        Vertexes=[SimpleNamespace(Point=(0.0, 0.0, 0.0))],
    )
    compare = helpers["_compare_component"]
    compare(shape, shape, frame)
    changes = (
        ("isValid", lambda: False), ("Orientation", "Reversed"),
        ("getTolerance", lambda _kind: 1.0),
        ("Vertexes", [SimpleNamespace(Point=(1.0, 0.0, 0.0))]),
        ("Volume", 2.0), ("Area", 7.0), ("Edges", []),
        ("Faces", [SimpleNamespace(Orientation="Reversed")]),
    )
    for field, value in changes:
        altered = copy.copy(shape)
        setattr(altered, field, value)
        try:
            compare(altered, shape, frame)
        except AssertionError:
            continue
        raise AssertionError("comparator accepted negative " + field)
    return len(changes)


def load_configuration():
    """Bind the reviewed private configuration; this is no consent check."""
    assert sys.flags.optimize == 0, "assertions must remain enabled"
    assert os.environ.get("GITHUB_ACTIONS") == "true", "hosted execution only"
    assert os.environ.get("GITHUB_RUN_ID", "").isdigit()
    path = regular_path(os.environ["TRACKTEMPLATE_L1_RUN_CONFIG"])
    assert sha256(path) == os.environ["TRACKTEMPLATE_L1_RUN_CONFIG_SHA256"]
    config = json.loads(path.read_text())
    assert config["schema_version"] == 1
    for name in ("scope_id", "handling_decision", "review_reference",
                 "checkpoint_commit"):
        assert isinstance(config[name], str) and config[name].strip()
    root = Path(config["repository_root"])
    assert root == Path(__file__).resolve().parents[1]
    assert len(config["inputs"]) == len(INPUT_IDS)
    inputs = {item["id"]: item for item in config["inputs"]}
    assert set(inputs) == set(INPUT_IDS)
    assert len({item["path"] for item in inputs.values()}) == len(INPUT_IDS)
    for item in inputs.values():
        bound_file(item)
    evidence = private_directory(config["private_evidence_dir"])
    assert not any(evidence == Path(item["path"]).parent
                   for item in inputs.values())
    recovery = json.loads(bound_file(config["recovery"]).read_text())
    assert recovery["status"] == recovery["independent_review"] == "PASS"
    assert recovery["checkpoint_commit"] == config["checkpoint_commit"]
    assert recovery["input_hashes"] == {
        key: record["sha256"] for key, record in inputs.items()
    }
    data = json.loads(Path(inputs["expected_frames"]["path"]).read_text())
    validate_expectations(data)
    return config, root, inputs, evidence, data


def write_private_result(directory, result):
    """Write once; the launcher must keep this unredacted result private."""
    path = private_directory(directory) / "result.json"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def load_runtime(root):
    """Qualify imports while refusing document creation or restore."""
    import FreeCAD as app

    assert not app.GuiUp and not app.listDocuments()
    sys.path[:0] = [str(root), str(root / "tests")]
    with (patch.object(app, "newDocument", side_effect=AssertionError(
            "readiness opened a document")),
          patch.object(app, "openDocument", side_effect=AssertionError(
              "readiness restored a document"))):
        launcher = runpy.run_path(str(root / "TrackTemplate.FCMacro"))
        assert launcher["FOUNDATION_RESULT"]["matched_profile_id"] == PROFILE
        api, bootstrap = launcher["_load_foundation"](root)
        session, routing = launcher["_load_modular_transition_workflow"](
            root, api, bootstrap,
        )
    assert not app.listDocuments() and app.ActiveDocument is None
    return app, session, routing


def catalogue_contract(inputs):
    from tracktemplate.application import chair_catalogue as reader

    selected = reader.prepare_catalogue_chair(
        inputs["catalogue"]["path"], "L1", run="existing-02",
    )
    assert selected.model_sha256 == inputs["l1_model"]["sha256"]
    assert selected.model_path == inputs["l1_model"]["path"]
    assert tuple(item.name for item in selected.components) == COMPONENT_NAMES
    approved = {item["path"]: item["sha256"] for item in inputs.values()}
    for item in selected.bindings:
        assert approved.get(item.path) == item.sha256, (
            "catalogue dependency is outside the approved ten inputs"
        )
    reader.verify_catalogue_sources(selected)
    return selected


def snapshotter(root):
    from tools.freecad_bridge import crossover_timber_recipe as recipe

    witness = extract_helper(
        root, "snapshot", ("_history", "_shape", "_snapshot"),
        namespace={"hashlib": hashlib, "recipe": recipe},
    )["_snapshot"]

    def snapshot(module, document):
        # Preserve PR212's treatment of FreeCAD's derived group cache.
        for obj in sorted(document.Objects, key=lambda item: item.Name):
            if (obj.TypeId == "App::DocumentObjectGroup"
                    and "Shape" not in obj.PropertiesList):
                getattr(obj, "Shape", None)
        return witness(module, document, "XO-001")

    return snapshot


def load_generate(root, app):
    return extract_helper(
        root, "generate", ("_native_generate",), namespace={
            "App": app, "copy": copy, "SimpleNamespace": SimpleNamespace,
            "patch": patch,
        },
    )["_native_generate"]


def native_setup(root, app):
    """Qualify every native helper/import without constructing geometry."""
    import Part
    from tracktemplate.adapters.freecad import (
        chair_catalogue_placement_preview as adapter,
    )
    from tracktemplate.application import chair_catalogue as reader
    from tracktemplate.compatibility.chair_reference_preview import (
        _open_source_context,
    )

    return SimpleNamespace(
        part=Part, adapter=adapter, reader=reader,
        context=_open_source_context, snapshot=snapshotter(root),
        generate=load_generate(root, app),
    )


class L1CurrentSource(unittest.TestCase):
    """Select one method per fresh, externally guarded native process."""

    def test_readiness(self):
        self._execute("readiness")

    def test_canonical_600_900_600(self):
        self._execute("native")

    def _execute(self, stage):
        config, root, inputs, evidence, expectations = load_configuration()
        directory = evidence / stage
        directory.mkdir(mode=0o700, exist_ok=False)
        receipt = {"status": "RUNNING", "stage": stage, "test_id": self.id(),
                   "scope_id": config["scope_id"], "profile": PROFILE,
                   "physical_fit": "NOT_PROVED", "stage_timings": {}}
        started = time.monotonic()
        app, owned = None, {}
        failure = None
        try:
            app, session, routing = load_runtime(root)
            receipt["routing"] = routing
            import Part
            with (patch.object(app, "newDocument", side_effect=AssertionError(
                    "readiness opened a document")),
                  patch.object(app, "openDocument", side_effect=AssertionError(
                      "readiness restored a document")),
                  patch.object(Part, "Shape", side_effect=AssertionError(
                      "readiness constructed geometry")),
                  patch.object(Part, "makeCompound", side_effect=AssertionError(
                      "readiness constructed geometry"))):
                setup = native_setup(root, app)
                selected = catalogue_contract(inputs)
                compare = load_comparator(root)
                receipt["comparator_negative_controls"] = comparator_controls(compare)
                receipt["frame_input_count"] = validate_expectations(expectations)
            assert receipt["comparator_negative_controls"] == 8
            assert not app.listDocuments() and app.ActiveDocument is None
            receipt["stage_timings"]["readiness_seconds"] = time.monotonic() - started
            if stage == "native":
                self._journey(app, session, root, inputs, selected, expectations,
                              directory, owned, receipt, compare, setup)
            assert all(bound_file(record) for record in inputs.values())
        except BaseException as error:
            failure = error
            receipt.update(status="FAIL", traceback=traceback.format_exc())
        finally:
            cleanup_started = time.monotonic()
            cleanup_errors = []
            try:
                assert all(bound_file(record) for record in inputs.values())
                receipt["input_bindings_unchanged"] = True
            except BaseException:
                receipt["input_bindings_unchanged"] = False
                cleanup_errors.append(traceback.format_exc())
            if app is not None:
                for name, document in reversed(tuple(owned.items())):
                    try:
                        current = app.listDocuments().get(name)
                        if current is not None:
                            assert current is document, "document ownership changed"
                            app.closeDocument(name)
                        assert name not in app.listDocuments()
                    except BaseException:
                        cleanup_errors.append(traceback.format_exc())
                if app.listDocuments() or app.ActiveDocument is not None:
                    cleanup_errors.append("document registry or active document remains")
            receipt["cleanup_errors"] = cleanup_errors
            receipt["owned_documents_closed"] = app is not None and not cleanup_errors
            receipt["stage_timings"]["cleanup_seconds"] = time.monotonic() - cleanup_started
            receipt["stage_timings"]["total_seconds"] = time.monotonic() - started
            if cleanup_errors and failure is None:
                failure = AssertionError("native document cleanup not proved")
            receipt["status"] = "PASS" if failure is None else "FAIL"
            if failure is None:
                receipt["sentinel"] = SENTINELS[stage]
            write_private_result(directory, receipt)
        if failure is not None:
            raise failure
        # Only this fixed sentinel is suitable for the public summary.
        print("\n" + SENTINELS[stage], flush=True)

    def _journey(self, app, session, root, inputs, selected, expectations,
                 directory, owned, receipt, comparator, setup):
        Part, adapter, reader = setup.part, setup.adapter, setup.reader
        _open_source_context = setup.context
        module = session.module
        snapshot, generate = setup.snapshot, setup.generate

        def open_copy(input_id, name):
            target = directory / name
            assert not target.exists()
            shutil.copyfile(inputs[input_id]["path"], target)
            target.chmod(0o600)
            assert sha256(target) == inputs[input_id]["sha256"]
            document = app.openDocument(str(target))
            assert document is not None and document.Name not in owned
            owned[document.Name] = document
            return document

        reference = open_copy("l1_model", "L1-copy.FCStd")
        assert tuple(obj.Name for obj in reference.Objects) == COMPONENT_NAMES
        assert all(obj.TypeId == "Part::Feature" for obj in reference.Objects)
        shapes = {obj.Name: Part.Shape(obj.Shape) for obj in reference.Objects}
        app.closeDocument(reference.Name)
        assert not app.listDocuments()
        source = open_copy("reference_document", "XO-001-copy.FCStd")
        source.UndoMode = 1
        original = copy.deepcopy(module.crossover_config_by_id(source, "XO-001"))
        foreign = app.newDocument("L1UnrelatedDocument")
        owned[foreign.Name] = foreign
        marker = foreign.addObject("App::FeaturePython", "Keep")
        marker.addProperty("App::PropertyString", "ProofValue")
        marker.ProofValue = "Preserve unrelated document"
        foreign.recompute()
        foreign_before = snapshot(module, foreign)
        kept = source.addObject("App::FeaturePython", "L1UnrelatedObject")
        kept.addProperty("App::PropertyString", "ProofValue")
        kept.ProofValue = "Preserve unrelated source object"
        source.recompute()
        previews, verifiers, frames_by_case = [], [], []
        receipt["cases"] = []
        for label, radius, analysis_count in CASES:
            case_started = time.monotonic()
            item = {"case": label, "radius_mm": radius}
            receipt["cases"].append(item)
            if previews:
                before_previews = [snapshot(module, doc) for doc in previews]
                registry = dict(app.listDocuments())
                with ExitStack() as stack:
                    for name in vars(session):
                        if name.endswith("_preview_factory"):
                            stack.enter_context(patch.object(
                                session, name,
                                side_effect=AssertionError("eager chair creation"),
                            ))
                    stack.enter_context(patch.object(
                        app, "newDocument",
                        side_effect=AssertionError("unexpected document"),
                    ))
                    item["canonical_generate"] = generate(module, source, radius)
                assert dict(app.listDocuments()) == registry
                assert all(message["kind"] not in ("critical", "warning")
                           for message in item["canonical_generate"]["messages"])
                with self.assertRaises(ValueError):
                    verifiers[-1]()
                assert [snapshot(module, doc) for doc in previews] == before_previews
                item["stale_source_rejected"] = True
                item["old_previews_unchanged"] = True
            config = module.crossover_config_by_id(source, "XO-001")
            assert config["crossover_id"] == original["crossover_id"] == "XO-001"
            for field in ("host_a_object", "host_b_object", "reference_chainage",
                          "arrangement", "handing", "track_gauge", "flangeway",
                          "minimum_requested_radius", "toe_chainage_a",
                          "template_set_id", "shared_timber_settings",
                          "b3_settings", "b4_settings", "chair_analysis_settings"):
                assert config[field] == original[field], field
            assert config["b4_result"] and config["integration_active"] is True
            assert config["production_ready"] is False
            assert config["minimum_resulting_radius"] >= config["minimum_requested_radius"]
            assert module.quantity_value(module.latest_generated_settings(source),
                                         "CurveRadius", -1) == radius
            assert source.getObject(kept.Name) is kept
            assert kept.ProofValue == "Preserve unrelated source object"
            context = _open_source_context(
                module, source, "XO-001", "heel L1", entity_kind="crossover",
            )
            assert len(context[1]["positions"]) == analysis_count
            assert context[1]["geometry_signature"] == config["chair_analysis_signature"]
            before = snapshot(module, source)
            app.setActiveDocument(source.Name)
            create = session._private_catalogue_l1_preview_factory
            captured = []

            def capture(*args):
                captured.extend(args[1])
                verifiers.append(args[-1])
                return create(*args)

            with (patch.object(session, "_private_catalogue_l1_preview_factory", capture),
                  patch.object(app, "openDocument", side_effect=AssertionError(
                      "product restored an external document"))):
                result = session.preview_private_catalogue_heel_l1_chairs(
                    source, "XO-001", inputs["catalogue"]["path"],
                )
            preview = app.getDocument(result["document_name"])
            assert preview is not None and preview.Name not in owned
            owned[preview.Name] = preview
            previews.append(preview)
            item["preview"] = result
            self._check_preview(result, preview, captured, expectations[label],
                                shapes, comparator, item, selected)
            frames_by_case.append(copy.deepcopy(result["placements"]))
            assert snapshot(module, source) == before
            assert snapshot(module, foreign) == foreign_before
            saved = tuple(Part.Shape(obj.Shape) for obj in preview.Objects)
            names = tuple(obj.Name for obj in preview.Objects)
            assert preview.UndoCount == 1
            preview.undo()
            assert not preview.Objects
            preview.redo()
            assert tuple(obj.Name for obj in preview.Objects) == names
            assert all(adapter._same_presented_shape(obj.Shape, shape)
                       for obj, shape in zip(preview.Objects, saved))
            assert snapshot(module, source) == before
            item["preview_undo_redo"] = True
            if label == "changed-900":
                self._rollback(app, session, source, selected, reader,
                               inputs, snapshot, previews, foreign, item)
            assert snapshot(module, source) == before
            assert snapshot(module, foreign) == foreign_before
            assert _open_source_context(module, source, "XO-001", "heel L1",
                                        entity_kind="crossover") == context
            item["seconds"] = time.monotonic() - case_started
        for first, changed, returned in zip(*frames_by_case):
            assert first["position_id"] == changed["position_id"] == returned["position_id"]
            assert first["origin_mm"] != changed["origin_mm"]
            assert first["x_axis"] != changed["x_axis"]
            compare_frame(SimpleNamespace(**returned), first)
        receipt["source_frame_comparisons"] = sum(
            case["source_frame_comparisons"] for case in receipt["cases"])
        receipt["component_comparisons"] = sum(
            len(case["component_comparisons"]) for case in receipt["cases"])
        assert receipt["source_frame_comparisons"] == 150
        assert receipt["component_comparisons"] == 138
        successful = sum(case["successful_preview_component_placements"]
                         for case in receipt["cases"])
        rolled_back = sum(case.get("rolled_back_component_placements", 0)
                          for case in receipt["cases"])
        assert successful == 690 and rolled_back == 230
        receipt["successful_preview_component_placements"] = successful
        receipt["rolled_back_component_placements"] = rolled_back
        receipt["total_materialised_component_placements"] = (
            successful + rolled_back
        )
        assert receipt["total_materialised_component_placements"] == 920
        reader.verify_catalogue_sources(selected)
        source_before_disposal = snapshot(module, source)
        for preview in reversed(previews):
            name = preview.Name
            app.closeDocument(name)
            assert name not in app.listDocuments()
            assert snapshot(module, source) == source_before_disposal
            assert snapshot(module, foreign) == foreign_before
        receipt["preview_disposal_preserves_source_and_foreign"] = True

    def _check_preview(self, result, preview, placements, expected, shapes,
                       comparator, item, selected):
        assert result["placement_count"] == len(placements) == 10
        assert result["component_count"] == 23 and result["layer_count"] == 25
        assert result["source_model_sha256"] == selected.model_sha256
        assert result["project_status"] == "reference-only"
        assert result["production_geometry_authorized"] is False
        assert result["geometry_rebuilt"] is False
        assert result["excluded_source_components"] == []
        assert result["source_receipt"]["source_document_mutation"] is False
        assert tuple(obj.Name for obj in preview.Objects) == (
            "ReferenceRails", "ReferenceTimbers", *COMPONENT_NAMES,
        )
        assert not preview.FileName and not preview.Temporary
        assert {value.position_id for value in placements} == set(expected)
        count = 0
        for placement in placements:
            record = expected[placement.position_id]
            assert (placement.rail_id, placement.timber_id) == (
                record["rail_id"], record["timber_id"],
            )
            for actual, frame in zip((placement, *placement.fixing_frames),
                                     (record["body"], *record["fixing_frames"])):
                compare_frame(actual, frame)
                count += 1
        assert count == 50
        item["source_frame_comparisons"] = count
        observed = result["placements"]
        assert [record["position_id"] for record in observed] == sorted(expected)
        comparisons = []
        materialised = 0
        compare = comparator["_compare_component"]
        for index, name in enumerate(COMPONENT_NAMES):
            children = preview.getObject(name).Shape.childShapes()
            assert len(children) == 10
            materialised += len(children)
            frame_name = 0 if index < 7 else (index - 7) // 4 + 1
            for identity in REPRESENTATIVES:
                child_index = next(i for i, record in enumerate(observed)
                                   if record["position_id"] == identity)
                record = expected[identity]
                frame = (record["body"], *record["fixing_frames"])[frame_name]
                proof = compare(children[child_index], shapes[name],
                                SimpleNamespace(**frame))
                comparisons.append({"position_id": identity, "component": name,
                                    **proof})
                if index == 0:
                    wrong = copy.deepcopy(frame)
                    wrong["origin_mm"][0] += 1.0
                    with self.assertRaises(AssertionError):
                        compare(children[child_index], shapes[name],
                                SimpleNamespace(**wrong))
        assert len(comparisons) == 46
        assert materialised == 230
        item["successful_preview_component_placements"] = materialised
        item["component_comparisons"] = comparisons
        item["wrong_frame_rejections"] = 2

    def _rollback(self, app, session, source, selected, reader, inputs,
                  snapshot, previews, foreign, item):
        registry = dict(app.listDocuments())
        before = {name: snapshot(session.module, doc)
                  for name, doc in registry.items()}
        active = app.ActiveDocument
        original_read = reader._read
        injected = []
        rollback_counts = []

        def late_model_read(path):
            content = original_read(path)
            if str(path) == selected.model_path and app.ActiveDocument is not active:
                target = app.ActiveDocument
                assert target is not source and target not in registry.values()
                assert len(target.Objects) == 25
                assert tuple(obj.Name for obj in target.Objects) == (
                    "ReferenceRails", "ReferenceTimbers", *COMPONENT_NAMES,
                )
                counts = [len(target.getObject(name).Shape.childShapes())
                          for name in COMPONENT_NAMES]
                assert len(counts) == 23 and all(count == 10 for count in counts)
                rollback_counts.append(sum(counts))
                injected.append(str(path))
                return content + b"\n"
            return content

        with patch.object(reader, "_read", late_model_read):
            with self.assertRaisesRegex(reader.CatalogueChairError,
                                        "Source binding changed"):
                session.preview_private_catalogue_heel_l1_chairs(
                    source, "XO-001", inputs["catalogue"]["path"],
                )
        assert injected == [selected.model_path]
        assert rollback_counts == [230]
        assert dict(app.listDocuments()) == registry and app.ActiveDocument is active
        assert {name: snapshot(session.module, doc)
                for name, doc in registry.items()} == before
        assert foreign in registry.values() and all(doc in registry.values()
                                                    for doc in previews)
        reader.verify_catalogue_sources(selected)
        item["late_verification_rollback"] = True
        item["rolled_back_component_placements"] = rollback_counts[0]
