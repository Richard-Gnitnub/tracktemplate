"""Prove all twenty qualified paired additions in one private XO-001 view.

Reuse the original 163-position witnesses and native component comparator.
Independently read active Pascal dimensions for both RH source rail sides.
Source-frame agreement and measured rail residuals give no physical-fit,
key-direction, production, rights or phase acceptance.
"""

from collections import Counter
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import runpy
import shutil
import sys
import time
import traceback
from types import SimpleNamespace
from unittest.mock import patch

import FreeCAD as App
import Part

if App.GuiUp:
    import FreeCADGui as Gui


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]


def _load_whole():
    name = "_paired_crossover_whole"
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "tests/freecad_validate_phase9b_catalogue_whole_crossover.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ROOT == ROOT
    return module


whole = _load_whole()
p, px, xo = whole.p, whole.px, whole.xo
adapter, lifecycle = whole.adapter, whole.lifecycle
catalogue, combined, helpers = whole.catalogue, whole.combined, whole.helpers

from tracktemplate.application import chair_catalogue as reader  # noqa: E402
from tracktemplate.application import chair_pair_catalogue as pairs  # noqa: E402
import paired_switch_source_oracle as oracle  # noqa: E402

SENTINEL = "Phase 9B paired crossover catalogue FreeCAD validation passed"
PAIR_IDS = tuple(f"RH-{side}-{number}P" for side in ("MS", "TS")
                 for number in range(1, 6))
COUNTS = dict(whole.COUNTS, **{identity: 2 for identity in PAIR_IDS})
FIXINGS = ("SourceFixing", *("SourceFixing" + str(index).zfill(3)
                             for index in range(1, 16)))


def _component_names(context_id):
    """Assert complete source constituents, including all sixteen fixings."""
    side, family = context_id.split("-")[1:]
    names = ["base_plinth", "c00_SCOUTJAW_SCOUTJAW"]
    names += ["c01_SCINJAW_" + part for part in (
        "body", "bevel_negative", "bevel_positive", "grip", "stiffener",
    )]
    names += ["c02_SCCCSEAT_SCCCSEAT", "c03_KEY_KEY"]
    if family in ("1P", "2P"):
        block = "MM" if side == "MS" else "TM"
        names += ["c04_" + block + "_" + part for part in (
            "body", "bevel_negative", "bevel_positive", "grip", "stiffener",
        )]
        names += ["c05_PLR1SEAT_PLR1SEAT"]
    else:
        outer, inner = ("MN", "MH") if side == "MS" else ("TN", "TH")
        names += ["c04_" + outer + "_" + part
                  for part in ("body", "stiffener")]
        names += ["c05_" + inner + "_" + part for part in (
            "body", "bevel_negative", "bevel_positive", "grip",
        )]
        names += ["c06_PLR3SEAT_PLR3SEAT", "c07_KEY_KEY"]
    return tuple(names) + FIXINGS


COMPONENT_NAMES = dict(whole.COMPONENT_NAMES, **{
    identity: _component_names(identity) for identity in PAIR_IDS
})
LAYER_NAMES = ("ReferenceRails", "ReferenceTimbers") + tuple(
    group.replace("-", "_") + "_" + name
    for group, names in COMPONENT_NAMES.items() for name in names
)


def _references(path, supplement, run_dir):
    references, prepared = whole._references(path, run_dir)
    selections = pairs.prepare_paired_catalogue(supplement)
    assert tuple(item.run for item in selections) == PAIR_IDS
    for selection in selections:
        case = (selection.label, {
            "run": selection.run,
            "model": {"path": selection.model_path,
                      "sha256": selection.model_sha256},
        })
        native = catalogue._reference(case, run_dir / "native-copies")
        references[selection.run] = {
            name: shape for name, _label, shape, _matrix in native
        }
        assert tuple(references[selection.run]) == (
            COMPONENT_NAMES[selection.run]
        )
        prepared[selection.run] = selection
    assert sum(len(values) for values in references.values()) == 378
    return references, prepared


def _near(actual, expected, residuals):
    """Compare independent source values using the existing native budget."""
    if isinstance(expected, dict):
        for key, value in expected.items():
            _near(actual[key], value, residuals)
    elif isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected)
        for first, second in zip(actual, expected):
            _near(first, second, residuals)
    elif type(expected) in (int, float):
        assert type(actual) in (int, float) and math.isfinite(actual)
        residual = abs(actual - expected)
        assert residual <= p.EPSILON_MM, (actual, expected, residual)
        residuals.append(residual)
    else:
        assert actual == expected


def _source_recipe(selection, expected):
    """Check anchors, angles, crops, shears and every retained base point."""
    recipe = selection.context
    residuals = []
    _near(recipe, {key: expected[key] for key in (
        "family", "chair_code", "context",
    )}, residuals)
    assert recipe["native_frame"]["common_timber_curving_applied"] is False
    assert recipe["native_frame"]["native_from_source"] == [
        [-1, 0, 0, 0], [0, -1, 0, -0.45],
        [0, 0, 1, 149 / 60], [0, 0, 0, 1],
    ]
    assert len(recipe["components"]) == len(expected["components"])
    for actual, target in zip(recipe["components"], expected["components"]):
        _near(actual, {key: target[key] for key in (
            "source_block", "source_endpoints_mm", "transformed_endpoints_mm",
        )}, residuals)
        _near(actual["insertion"], {key: target["insertion"][key]
                                  for key in ("x_mm", "y_mm", "z_mm")},
              residuals)
        angle = actual["insertion"]["rotation_rad"]
        delta = angle - target["insertion"]["rotation_rad"]
        _near([math.sin(delta), math.cos(delta)], [0, 1], residuals)
    jaws = expected["jaw_parameters"]
    components = recipe["components"]
    _near(components[1]["request_parameters"]["crop_mm"],
          jaws["stock_inner_crop_mm"], residuals)
    _near(components[4]["request_parameters"]["crop_mm"],
          jaws["switch_outer_crop_mm"], residuals)
    _near(components[4]["request_parameters"]["shear_rad"],
          jaws["switch_shear_rad"], residuals)
    if recipe["chair_code"] == 12:
        _near(components[5]["request_parameters"]["crop_mm"],
              jaws["switch_inner_crop_mm"], residuals)
        _near(components[5]["request_parameters"]["shear_rad"],
              jaws["switch_shear_rad"], residuals)
    base = recipe["base"]
    _near(base, {key: expected["base"][key] for key in (
        "outlong_mm", "inlong_mm", "half_width_mm",
    )}, residuals)
    retained = base["source_pre_chair_transform"]
    for key in ("corner_centres_mm", "bolt_centres_mm", "midvertices_mm",
                "outline32_pre_twist_mm", "plinth_top_pre_twist_mm",
                "outline32_mm", "plinth_top_mm", "bolt_centres_twisted_mm",
                "native_vertices_mm"):
        points = [oracle.expected_base_point(expected, point)
                  for point in retained[key]]
        _near(base[key], points, residuals)
    return {"source_scalar_count": len(residuals),
            "maximum_source_scalar_residual": max(residuals),
            "comparison_budget": p.EPSILON_MM,
            "aq_branch": expected["aq_branch"],
            "physical_fit": "NOT_PROVED"}


def _distance_to_polyline(point, points):
    distances = []
    for first, second in zip(points, points[1:]):
        delta = [second[axis] - first[axis] for axis in (0, 1)]
        norm = sum(value * value for value in delta)
        assert norm > 0
        fraction = min(1, max(0, sum(
            (point[axis] - first[axis]) * delta[axis] for axis in (0, 1)
        ) / norm))
        nearest = [first[axis] + fraction * delta[axis] for axis in (0, 1)]
        distances.append(math.dist(point, nearest))
    assert distances
    return min(distances)


def _native_source_bases(prepared, references):
    """Bind native bases to unquantised source vertices in the fixed frame."""
    results = {}
    for group in PAIR_IDS:
        points = prepared[group].context["base"]["native_vertices_mm"]
        expected = [(-x, -y - 0.45, z + 149 / 60) for x, y, z in points]
        actual = [tuple(vertex.Point)
                  for vertex in references[group]["base_plinth"].Vertexes]
        assert len(points) == 68 and actual
        residuals = [min(math.dist(point, other) for other in expected)
                     for point in actual]
        residuals += [min(math.dist(point, other) for other in actual)
                      for point in expected]
        assert max(residuals) <= p.EPSILON_MM
        assert min(point[2] for point in expected) == 0
        results[group] = {
            "source_vertex_count": len(expected),
            "native_vertex_count": len(actual),
            "maximum_bidirectional_vertex_residual_mm": max(residuals),
            "source_grid_quantisation_applied": False,
        }
    return results


def _pair_witnesses(module, source, context, prepared, source_directory,
                    supplement):
    """Construct frames from canonical host arrays and active source only."""
    parameters = oracle.source_parameters(
        source_directory, scale_mm_per_inch=1 / 3, gauge_mm=16.5,
        flangeway_mm=1.0, rail_head_width_mm=0.9, crossing_ratio=10,
    )
    manifest = json.loads(supplement.read_text(encoding="utf-8"))
    host_binding = manifest["canonical_hosts"]
    host_path = Path(host_binding["path"])
    assert catalogue._hash(host_path) == host_binding["sha256"]
    captured = json.loads(host_path.read_text(encoding="utf-8"))
    assert captured["fixture_sha256"] == xo.FIXTURE_SHA256
    configuration = json.loads(context[0])["configuration"]
    hosts = {}
    for side in ("A", "B"):
        config = configuration["turnout_" + side.lower() + "_config"]
        obj = source.getObject(config["host_object"])
        data = module.turnout_host_alignment(obj)
        actual = {
            "object_name": obj.Name,
            "points": [[point.x, point.y] for point in data["points"]],
            "headings": data["headings"], "stations": data["stations"],
            "total": data["total"], "toe_chainage": config["toe_chainage"],
            "orientation": config["orientation"], "handing": config["handing"],
        }
        assert actual == captured["hosts"][side]
        hosts[side] = actual
    timbers = {item["stable_identity"]: item for item in context[5]}
    rails = {item["stable_identity"]: item for item in context[4]}
    base_values = {item["base_z"] for item in context[3]["instances"]}
    assert len(base_values) == 1
    base_z = base_values.pop()
    frames = {identity: [] for identity in PAIR_IDS}
    checks, centres = {}, {}
    for position in sorted(context[1]["positions"], key=lambda item:
                           item["stable_chair_position_identity"]):
        if position["chair_code"] not in (11, 12):
            continue
        identity = position["stable_chair_position_identity"]
        side = {"XO-001-A001": "A", "XO-001-B001": "B"}[
            position["parent_turnout_identity"]]
        rail_side = {"main-side stock rail": "MS",
                     "turnout-side stock rail": "TS"}[position["rail_name"]]
        timber_id = position["prototype_timber_identifier"]
        group = f"RH-{rail_side}-{int(timber_id[1:]) - 7}P"
        station = timbers[position["timber_identity"]][
            "source_configuration"]["local_x"]
        expected = oracle.expected_local_pair(
            parameters, timber_id, rail_side, hand=-1, station_mm=station,
        )
        assert expected["aq_branch"] == (
            "closure" if timber_id == "S12" else "switch"
        )
        checks[identity] = _source_recipe(prepared[group], expected)
        host = hosts[side]
        world = oracle.expected_world_frame(
            host, toe_chainage_mm=host["toe_chainage"],
            direction=1 if side == "A" else -1, hand=-1,
            station_mm=station, gauge_mm=16.5,
        )
        frame = SimpleNamespace(
            position_id=identity, rail_id=position["rail_identity"],
            timber_id=position["timber_identity"],
            origin_mm=tuple(world["origin_mm"][axis]
                            - 0.45 * world["y_axis"][axis]
                            for axis in (0, 1)) + (base_z,),
            x_axis=tuple(-value for value in world["x_axis"]),
            y_axis=tuple(-value for value in world["y_axis"]),
        )
        frames[group].append(frame)
        recipe = prepared[group].context
        corners = [oracle.world_point(world, oracle.expected_base_point(
            expected, point,
        )) for point in recipe["base"]["source_pre_chair_transform"][
            "corner_centres_mm"]]
        centres[identity] = tuple(sum(point[axis] for point in corners)
                                  / len(corners) for axis in (0, 1)) + (base_z,)
        mate_name = ("curved-switch-and-closure-rail" if rail_side == "MS"
                     else "straight-switch-and-closure-rail")
        mate_id = position["parent_turnout_identity"] + ":rail:" + mate_name
        fit = {}
        for name, rail_id, index in (
                ("stock", frame.rail_id, 0), ("switch", mate_id, 4)):
            points = expected["components"][index]["transformed_endpoints_mm"]
            world_points = [oracle.world_point(world, point) for point in points]
            residuals = [_distance_to_polyline(
                point, rails[rail_id]["gauge_face_points"],
            ) for point in world_points]
            assert all(math.isfinite(value) for value in residuals)
            fit[name] = {"rail_id": rail_id, "world_endpoints_mm": world_points,
                         "sampled_gauge_polyline_residuals_mm": residuals}
        checks[identity].update(
            context_id=group, source_station_mm=station,
            host_station_mm=world["host_chainage_mm"],
            physical_fit_measurements=fit,
            physical_fit_threshold=None,
            physical_fit_limit=("Endpoint-to-sampled-gauge measurements only; "
                                "no interference, clearance or fit acceptance"),
        )
    assert len(checks) == 20 and all(len(values) == 2
                                    for values in frames.values())
    return {key: tuple(values) for key, values in frames.items()}, checks, centres


def _coverage(source, context, frames, prepared, checks):
    positions = {item["stable_chair_position_identity"]: item
                 for item in context[1]["positions"]}
    selected = {item["position_id"]: item
                for item in source["selected_positions"]}
    excluded = {item["position_id"]: item
                for item in source["excluded_positions"]}
    assert len(positions) == source["analysis_position_count"] == 355
    assert len(selected) == len(source["selected_positions"]) == 183
    assert len(excluded) == len(source["excluded_positions"]) == 172
    assert source["placement_count"] == 183
    assert source["excluded_position_count"] == 172
    assert source["selected_counts"] == COUNTS
    assert not selected.keys() & excluded.keys()
    assert selected.keys() | excluded.keys() == positions.keys()
    assert Counter(item["exclusion_kind"] for item in excluded.values()) == {
        "source-assignment-deferred": 124, "confirmed-no-separate-chair": 48,
    }
    assert source["original_analytical_exclusions"] == context[3]["analytical_only"]
    assert source["source_context_signature"] == "sha256:" + hashlib.sha256(
        context[0].encode("utf-8"),
    ).hexdigest()
    assert source["source_analysis_signature"] == context[1]["geometry_signature"]
    assert source["source_document_mutation"] is False
    assert source["model_support_adjustments_applied"] is False
    assert source["source_kind"] == "crossover" and source["crossover_id"] == "XO-001"
    assert source["timber_context"] == "current B4 resolved timbers"
    for group, values in frames.items():
        assert {frame.position_id for frame in values} == {
            identity for identity, item in selected.items()
            if item.get("context_id", item["family"]) == group
        }
    for identity, item in {**selected, **excluded}.items():
        position = positions[identity]
        assert item["rail_id"] == position["rail_identity"]
        assert item["timber_id"] == position["timber_identity"]
        assert item["chair_code"] == position["chair_code"]
        for field in ("key_direction_sign", "key_orientation",
                      "key_orientation_classification"):
            assert item[field] == position[field]
        if identity in selected:
            assert not position["deliberate_omission"]
            assert not position["special_assignment_deferred"]
            assert position["assignment_status"] == (
                "confirmed ordinary or turnout assignment"
            )
            assert item["key_direction_sign"] == 0
            if identity in checks:
                group = checks[identity]["context_id"]
                recipe = prepared[group].context
                assert item["family"] == prepared[group].label
                assert item["source_model_sha256"] == prepared[group].model_sha256
                assert item["source_context_sha256"] == recipe["context_sha256"]
                assert item["source_parameters"] == recipe["context"]
                assert item["source_station_mm"] == checks[identity]["source_station_mm"]
                assert item["host_station_mm"] == checks[identity]["host_station_mm"]
                assert item["physical_fit"] == "NOT_PROVED"
                mate = excluded[item["mate_position_id"]]
                assert mate["supporting_position_id"] == identity
        else:
            assert item["reason"] and item["original_exclusion"] in (
                context[3]["analytical_only"]
            )
            if item["exclusion_kind"] == "source-assignment-deferred":
                assert position["special_assignment_deferred"]
            else:
                assert position["deliberate_omission"]
                owner_id = item["supporting_position_id"]
                assert owner_id in selected
                assert item["supporting_assembly_placed"] is True
                owner = positions[owner_id]
                assert owner["timber_identity"] == position["timber_identity"]
                assert owner["rail_role"] == "stock rail"


def _assert_preview(result, document, references, prepared, frames):
    """Compare every native component with an independent proper frame."""
    catalogue.helpers._active_document_state(document)
    assert not document.FileName and not document.Temporary
    for text in ("183 placed", "172 excluded", "355 source positions"):
        assert text in document.Label
    assert tuple(obj.Name for obj in document.Objects) == LAYER_NAMES
    assert result["contract_id"] == "tracktemplate.private-catalogue-crossover.v2"
    assert result["family_count"] == 8 and result["assembly_group_count"] == 13
    assert result["placement_count"] == result["track_placements_added"] == 183
    assert result["component_count"] == 378 and result["layer_count"] == 380
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["geometry_rebuilt"] is False
    assert result["scale_denominator"] == "76.2"
    assert result["length_basis"] == "model" and result["length_unit"] == "mm"
    assert tuple(result["families"]) == tuple(COUNTS)
    assert tuple(item["name"] for item in result["layers"]) == LAYER_NAMES
    for obj in document.Objects[:2]:
        assert not obj.Shape.Solids and not obj.Shape.Faces
    comparisons, solids = {}, 0
    for group, values in frames.items():
        record, selection = result["families"][group], prepared[group]
        assert record["family"] == group and record["label"] == selection.label
        assert record["run"] == selection.run
        assert record["context"] == selection.context
        assert record["source_model_sha256"] == selection.model_sha256
        assert record["source_metadata"] == selection.metadata
        assert record["source_bindings"] == [
            {"path": item.path, "sha256": item.sha256}
            for item in selection.bindings
        ]
        assert record["placement_count"] == len(values) == COUNTS[group]
        names = COMPONENT_NAMES[group]
        assert record["component_count"] == len(record["components"]) == len(names)
        assert len(record["placements"]) == len(values)
        assert [item["source_name"] for item in record[
            "excluded_source_components"]] == (
                ["display_rail"] if group in ("S1J", "P") else []
            )
        checks = []
        for name, component in zip(names, record["components"]):
            obj = document.getObject(group.replace("-", "_") + "_" + name)
            assert obj.TypeId == "Part::Feature"
            assert "GeneratedBy" not in obj.PropertiesList
            assert component["source_name"] == name
            assert tuple(component["source_identity"]) == (
                selection.model_sha256, name,
            )
            children = obj.Shape.childShapes()
            assert len(children) == len(values)
            checks.append({"name": name, "positions": [
                dict(p._compare_component(child, references[group][name], frame),
                     position_id=frame.position_id)
                for child, frame in zip(children, values)
            ]})
            solids += len(references[group][name].Solids) * len(values)
        for actual, frame in zip(record["placements"], values):
            for field in ("position_id", "rail_id", "timber_id"):
                assert actual[field] == getattr(frame, field)
            for field in ("origin_mm", "x_axis", "y_axis"):
                if group in whole.COUNTS:
                    assert tuple(actual[field]) == getattr(frame, field)
                else:
                    _near(actual[field], getattr(frame, field), [])
            assert len(actual["components"]) == len(names)
            for name, component in zip(names, actual["components"]):
                assert tuple(component["placement_identity"]) == (
                    frame.position_id, selection.model_sha256, name,
                )
        comparisons[group] = checks
    assert sum(len(item["positions"]) for values in comparisons.values()
               for item in values) == 3555
    assert result["solid_count"] == solids == sum(
        len(obj.Shape.Solids) for obj in document.Objects
    )
    return comparisons


def _gui_inspection(document, frames, context, centres, run_dir):
    """Capture both constituents for all five families and both rail sides."""
    targets = {
        group: tuple(SimpleNamespace(
            position_id=frame.position_id,
            origin_mm=centres.get(frame.position_id, frame.origin_mm),
        ) for frame in values) for group, values in frames.items()
    }
    images = whole._gui_inspection(document, targets, context, run_dir)
    assert len(images) == 26
    return images


def validate():
    """Run the same source, geometry and lifecycle proof in either host."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    path = Path(os.environ["TRACKTEMPLATE_CHAIR_CATALOGUE"]).resolve()
    supplement = Path(os.environ["TRACKTEMPLATE_PAIRED_CATALOGUE"]).resolve()
    source_directory = Path(os.environ["TRACKTEMPLATE_TEMPLOT_SOURCE"])
    fixture = Path(os.environ["TRACKTEMPLATE_CROSSOVER_REFERENCE_FIXTURE"])
    assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ",
    )
    run_dir = Path(os.environ.get(
        "TRACKTEMPLATE_PAIRED_CROSSOVER_RUN_DIR",
        ROOT / "benchmark-output/catalogue-paired-crossover" / stamp,
    )).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp),
               "physical_fit": "NOT_PROVED"}
    initial = catalogue.helpers._document_state()
    try:
        references, prepared = _references(path, supplement, run_dir)
        receipt["native_source_bases"] = _native_source_bases(
            prepared, references,
        )
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        api, bootstrap = launcher["_load_foundation"](ROOT)
        session, routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, bootstrap,
        )
        assert launcher["FOUNDATION_RESULT"]["matched_profile_id"] == p.PROFILE
        receipt.update(profile=p.PROFILE, routing=routing)
        module = session.module
        command = session.preview_private_catalogue_crossover_chairs
        target = run_dir / "XO-001.FCStd"
        shutil.copy2(fixture, target)
        source = App.openDocument(str(target))
        source.UndoMode = 1
        foreign = App.newDocument("PairedCrossoverUnrelatedWitness")
        foreign.addObject("Part::Feature", "Keep").Shape = Part.makeBox(2, 3, 4)
        foreign.recompute()
        combined._settle(foreign)
        App.setActiveDocument(source.Name)
        gui = Gui if App.GuiUp else None
        if gui:
            gui.getMainWindow().resize(1600, 1000)
            gui.Selection.addSelection(source.Objects[0])
        combined._settle(source)
        context = xo._context(module, source)
        previous, excluded, recovered, observations = xo._expected_placements(
            module, context,
        )
        frames = {"S1": previous[0], "S1J": previous[1],
                  "P": px._expected_frames(module, context)}
        paired_frames, checks, centres = _pair_witnesses(
            module, source, context, prepared, source_directory, supplement,
        )
        frames.update(paired_frames)
        assert {group: len(values) for group, values in frames.items()} == COUNTS
        partition = px._legacy_partition(module, context)
        assert len(excluded) == 220
        receipt.update(frame_observations=observations,
                       recovered_positions=recovered, source_checks=checks,
                       source_references=oracle.SOURCE_REFERENCES,
                       source_hashes=oracle.SOURCE_HASHES)
        xo._state(module, source)
        combined._settle(source)
        source_state = xo._state(module, source)
        foreign_state = combined._foreign_state(foreign)
        combined._settle(source)
        assert xo._state(module, source) == source_state
        registry = dict(App.listDocuments())
        identities = {(doc.Name, obj.Name): obj for doc in registry.values()
                      for obj in doc.Objects}
        shapes = {key: obj.Shape for key, obj in identities.items()
                  if "Shape" in obj.PropertiesList}
        selection = lifecycle._selection_snapshot(App, gui)
        preselection = lifecycle._preselection_snapshot(App, gui)
        receipt.update(source_before=source_state, foreign_before=foreign_state)

        def unchanged(stage, active):
            receipt["last_preservation_stage"] = stage
            assert xo._state(module, source) == source_state, stage
            assert combined._foreign_state(foreign) == foreign_state, stage
            assert App.listDocuments() == dict(
                registry, **({active.Name: active}
                             if active.Name not in registry else {}),
            ), stage
            for name, document in registry.items():
                assert App.getDocument(name) is document, stage
            for (name, obj_name), obj in identities.items():
                assert App.getDocument(name).getObject(obj_name) is obj, stage
            for key, shape in shapes.items():
                assert identities[key].Shape.isSame(shape), stage
            assert lifecycle._selection_snapshot(App, gui) == selection, stage
            assert lifecycle._preselection_snapshot(App, gui) == preselection
            catalogue.helpers._active_document_state(active)

        def create(manifest=supplement):
            return command(source, "XO-001", path,
                           paired_contexts_path=manifest)

        started = time.perf_counter()
        with patch.object(App, "openDocument", side_effect=AssertionError(
            "Product restored an external source document",
        )):
            result = create()
        receipt["elapsed_seconds"] = time.perf_counter() - started
        preview = App.getDocument(result["document_name"])
        receipt["preview"] = result
        _coverage(result["source_receipt"], context, frames, prepared, checks)
        receipt["comparisons"] = _assert_preview(
            result, preview, references, prepared, frames,
        )
        unchanged("created", preview)
        before = tuple(obj.Shape for obj in preview.Objects)
        assert preview.UndoCount == 1
        preview.undo()
        assert not preview.Objects
        preview.redo()
        _assert_preview(result, preview, references, prepared, frames)
        assert all(p.catalogue_adapter._same_presented_shape(obj.Shape, shape)
                   for obj, shape in zip(preview.Objects, before))
        unchanged("Undo/Redo", preview)
        receipt["undo_redo"] = "PASS"
        if gui:
            receipt["images"] = _gui_inspection(
                preview, frames, context, centres, run_dir,
            )
            lifecycle._restore_selection(App, gui, selection)
            lifecycle._restore_preselection(App, gui, preselection)
            unchanged("GUI inspection", preview)
            receipt["visibility_selection"] = "PASS"
            receipt["camera_animation_restored"] = True
        App.closeDocument(preview.Name)
        App.setActiveDocument(source.Name)
        lifecycle._restore_selection(App, gui, selection)
        lifecycle._restore_preselection(App, gui, preselection)
        combined._settle(source)
        unchanged("test-owned close", source)
        invalid = run_dir / "changed-supplement.json"
        invalid.write_bytes(supplement.read_bytes() + b"\n")
        with patch.object(App, "newDocument", side_effect=AssertionError(
            "Invalid paired evidence created a document",
        )):
            receipt["supplement_refusal"] = catalogue._reject(
                lambda: create(invalid), ValueError,
            )
        unchanged("early supplement refusal", source)
        original_read = reader._read
        changed_model = prepared["RH-TS-5P"].model_path

        def changed_bytes(filename):
            data = original_read(filename)
            if str(filename) == changed_model:
                return data + b"\n"
            return data

        with patch.object(reader, "_read", changed_bytes), patch.object(
                App, "newDocument", side_effect=AssertionError(
                    "Changed paired geometry created a document")):
            receipt["model_refusal"] = catalogue._reject(create, ValueError)
        unchanged("early model refusal", source)

        def late_bytes(filename):
            if App.ActiveDocument not in registry.values():
                assert len(App.ActiveDocument.Objects) == 380
                return changed_bytes(filename)
            return original_read(filename)

        with patch.object(reader, "_read", late_bytes):
            receipt["late_model_refusal"] = catalogue._reject(create, ValueError)
        unchanged("late model rollback", source)
        native_create = adapter.create_private_catalogue_crossover_preview
        original_host = module.turnout_host_alignment

        def stale_host(*args, **kwargs):
            def verify():
                assert App.ActiveDocument not in registry.values()
                assert len(App.ActiveDocument.Objects) == 380

                def changed_host(obj):
                    data = dict(original_host(obj))
                    headings = list(data["headings"])
                    headings[0] += 1e-8
                    return dict(data, headings=headings)

                with patch.object(module, "turnout_host_alignment", changed_host):
                    args[-1]()
            return native_create(*args[:-1], verify, **kwargs)

        with patch.object(session, "_private_catalogue_crossover_preview_factory",
                          side_effect=stale_host):
            receipt["late_host_refusal"] = helpers._reject(create, "changed")
        unchanged("late host rollback", source)
        original_check = adapter._same_presented_shape

        def reject_stored(actual, expected):
            if App.ActiveDocument not in registry.values():
                assert len(App.ActiveDocument.Objects) == 380
                return False
            return original_check(actual, expected)

        with patch.object(adapter, "_same_presented_shape", reject_stored):
            receipt["stored_shape_refusal"] = catalogue._reject(create, ValueError)
        unchanged("stored shape rollback", source)
        for group in whole.COUNTS:
            p.verify_catalogue_sources(prepared[group])
        pairs.verify_paired_catalogue(tuple(prepared[key] for key in PAIR_IDS))
        assert catalogue._hash(source.FileName) == xo.FIXTURE_SHA256
        assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
        assert xo._context(module, source) == context
        assert px._legacy_partition(module, context) == partition
        receipt.update(source_after=xo._state(module, source),
                       foreign_after=combined._foreign_state(foreign),
                       source_bindings_unchanged=True,
                       fixture_sha256=xo.FIXTURE_SHA256,
                       component_comparisons=3555,
                       existing_component_comparisons=2911,
                       paired_component_comparisons=644,
                       transaction_rollback="PASS",
                       legacy_exclusions_unchanged=True)
    except BaseException:
        receipt.update(status="FAIL", traceback=traceback.format_exc())
        raise
    finally:
        for name in tuple(App.listDocuments()):
            App.closeDocument(name)
        catalogue.helpers._settle()
        receipt["owned_documents_closed"] = not App.listDocuments()
        (run_dir / "result.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
        )
    assert catalogue.helpers._document_state() == initial
    receipt["status"] = "PASS"
    (run_dir / "result.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8",
    )
    print(SENTINEL, flush=True)


if __name__ in ("__main__", Path(__file__).stem):
    validate()
