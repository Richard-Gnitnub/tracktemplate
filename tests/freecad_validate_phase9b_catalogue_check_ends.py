"""Prove eight check-end additions in native and real-GUI hosts.

The frozen central-CC receipt owns the unchanged 195 assemblies and 3951
components. The 264 additions use independent source and canonical-host
witnesses. Reuse accepted lifecycle helpers and the old failure matrix;
repeat only the new preparation and focused shared lifecycle failures.
Private source agreement gives no physical-fit or production acceptance.
"""

import ast
from collections import Counter
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


def _load_central():
    spec = importlib.util.spec_from_file_location(
        "_check_end_central",
        ROOT / "tests/freecad_validate_phase9b_catalogue_central_check.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


central = _load_central()
paired, p, xo, whole = central.paired, central.p, central.xo, central.whole
adapter, lifecycle = central.adapter, central.lifecycle
catalogue, combined, reader = central.catalogue, central.combined, central.reader
_frame, _near_frame = central._frame, central._near_frame
_world_point, _world_frame = central._world_point, central._world_frame
_source_vertices = central._source_vertices
POSITION_FIELDS, FRAME_FIELDS = central.POSITION_FIELDS, central.FRAME_FIELDS

import check_end_source_oracle as oracle  # noqa: E402
from tracktemplate.domain.check_end_placement import (  # noqa: E402
    CheckEndPlacement,
    place_check_end,
)

SENTINEL = "Phase 9B check-end catalogue FreeCAD validation passed"
BASELINE_SHA256 = (
    "6a4a096e0f322614ea6cf4f2c297fd0f76a0b7176292292a8c4bd68fde83c109"
)
MODEL_SHA256 = {
    "CCL": "692a8cfbe6845fd9fce4e8b471f1ec37d5388366c6451f9bff2d65601dbccb3d",
    "CCR": "d594dfb2f387c2b2a0360863ea8dcc30cd2057ed06095f8eb1e49a9421282fa7",
}
CONTAINMENT_SHA256 = (
    "0e15ef9ce3080bed185f21a034d437ea0f7e192568bc38041bc43d81b03514bc"
)
CHECK_NAMES = ("c06_CCSEATCK_CCSEATCK", "c07_CCKEY_CCKEY")


def _read_baseline(path):
    assert catalogue._hash(path) == BASELINE_SHA256
    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["status"] == "PASS" and not result["gui"]
    assert result["profile"] == p.PROFILE
    assert result["fixture_sha256"] == xo.FIXTURE_SHA256
    assert result["baseline_component_comparisons"] == 3555
    assert result["cc_component_comparisons"] == 396
    assert result["preview"]["placement_count"] == 195
    return result


def _references(path, supplement, run_dir):
    references, prepared = central._references(path, supplement, run_dir)
    for family, digest in MODEL_SHA256.items():
        selected = reader.prepare_catalogue_chair(
            path, family, run="context-native-02",
        )
        assert selected.model_sha256 == digest
        native = catalogue._reference((family, {
            "run": selected.run,
            "model": {"path": selected.model_path, "sha256": digest},
        }), run_dir / "native-copies")
        references[family] = {
            name: shape for name, _label, shape, _matrix in native
        }
        prepared[family] = selected
        assert len(native) == len(selected.components) == 33
        assert tuple(references[family]) == tuple(
            component.name for component in selected.components
        )
    return references, prepared


def _containment(path):
    """Reuse the frozen containment predicate without importing builders."""
    assert catalogue._hash(path) == CONTAINMENT_SHA256
    tree = ast.parse(path.read_bytes())
    function, = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef)
                 and node.name == "_contained"]
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]),
                 str(path), "exec"), namespace)
    return namespace["_contained"]


def _native_source_bases(data, references):
    """Check copied native components against their frozen source vertices."""
    checks = {}
    for context_id, target in data["contexts"].items():
        family = target["family"]
        parts = data["parts_by_family"][family]
        assert len(parts) == 33
        assert {part["native_object"] for part in parts.values()} == set(
            references[family]
        )
        checks[context_id] = {
            part_id: _source_vertices(
                references[family][part["native_object"]],
                oracle.retained_native_vertices(data, context_id, part_id),
            ) for part_id, part in parts.items()
        }
    assert len(checks) == 4
    return checks


def _source_closure_triangles(data, context_id, part_id, *, retained=False):
    """Transform the bound source closure facets without building geometry."""
    family = data["contexts"][context_id]["family"]
    part = data["parts_by_family"][family][part_id]
    assert part["kind"] == "fixing" and part["fixing_part"] == "boss"
    faces = [face for face in part["source_faces"]
             if face.get("closure_ring") is not None]
    assert len({face["closure_ring"] for face in faces}) == 1
    assert len(faces) == 22 and all(len(face["vertices"]) == 3 for face in faces)
    transform = (oracle.retained_native_vertices if retained
                 else oracle.source_target_vertices)
    triangles = []
    for face in faces:
        parts = dict(data["parts_by_family"][family])
        parts[part_id] = dict(part, source_vertices_mm=face["vertices"])
        local = dict(data, parts_by_family=dict(
            data["parts_by_family"], **{family: parts},
        ))
        triangles.append(transform(local, context_id, part_id))
    return triangles


def _matching_closure_facets(faces, expected):
    """Require every declared source facet exactly once in the native cap."""
    assert len(faces) == len(expected)
    used, maximum = set(), 0.0
    for face in faces:
        assert face.isValid() and face.Area > 0
        vertices = [tuple(vertex.Point) for vertex in face.Vertexes]
        assert len(vertices) == 3
        matches = []
        for index, triangle in enumerate(expected):
            residual = max(
                max(min(math.dist(a, b) for b in triangle) for a in vertices),
                max(min(math.dist(a, b) for b in vertices) for a in triangle),
            )
            if residual <= p.EPSILON_MM:
                matches.append((index, residual))
        assert len(matches) == 1
        index, residual = matches[0]
        assert index not in used
        used.add(index)
        maximum = max(maximum, residual)
    assert used == set(range(len(expected)))
    return {"source_facet_count": len(expected), "native_facet_count": len(faces),
            "complete_source_facet_bijection": True,
            "maximum_source_facet_residual_mm": maximum}


def _mounting_footprint(boss, expected):
    """Keep all source-matched native triangles in the mounting footprint."""
    faces = [face for face in boss.Faces
             if face.BoundBox.ZLength <= p.EPSILON_MM
             and abs(face.CenterOfMass.z - boss.BoundBox.ZMin) <= p.EPSILON_MM]
    proof = _matching_closure_facets(faces, expected)
    return Part.makeCompound(faces), proof


def _native_closure_controls(data, references, containment):
    """Reject missing, duplicate and outside caps before a full preview."""
    reports = {}
    for family in MODEL_SHA256:
        context_id = next(identity for identity, context in data["contexts"].items()
                          if context["family"] == family)
        parts = data["parts_by_family"][family]
        reports[family] = {}
        for part_id, part in parts.items():
            if part.get("fixing_part") != "boss":
                continue
            name = part["native_object"]
            expected = _source_closure_triangles(
                data, context_id, part_id, retained=True,
            )
            footprint, proof = _mounting_footprint(references[family][name], expected)
            base = references[family]["base_plinth"]
            containment(footprint, base, proof)
            faces = footprint.Faces
            for invalid in (faces[:-1], faces[:-1] + faces[:1]):
                catalogue._reject(
                    lambda: _matching_closure_facets(invalid, expected),
                    AssertionError,
                )
            outside = footprint.copy()
            outside.translate(App.Vector(2 * base.BoundBox.XLength, 0, 0))
            message = catalogue._reject(
                lambda: containment(outside, base, {}), ValueError,
            )
            assert "not wholly contained" in message
            proof["missing_duplicate_outside_negatives"] = "PASS"
            reports[family][name] = proof
        assert len(reports[family]) == 4
    return reports


def _source_boundary_resolver(module, source_directory, data):
    """Compare the accepted inverse resolver with direct source geometry.

    Each calculation rounds its join independently. Test both adjacent
    binary64 neighbourhoods, and compare poses with a numerical budget
    that preserves the large circle-subtraction operands. A difference
    in branch labels between the two rounded joins is not a fit defect.
    """
    parameters = oracle._central()._source_oracle().source_parameters(
        source_directory, scale_mm_per_inch=1 / 3, gauge_mm=16.5,
        flangeway_mm=1.0, rail_head_width_mm=11 / 12, crossing_ratio=10,
    )
    geometry = oracle.source_rail_geometry(parameters)
    assert geometry == data["parameters"]["rail_geometry"]
    dimensions = module.rea_c10_dimensions(16.5, 1.0, 76.2)
    product_join = (dimensions["switch_curve_end_x"]
                    - dimensions["gauge"] * math.sin(dimensions["k3"]))
    source_join = geometry["curve_end_station_mm"]
    scale_mm = max(
        1.0, abs(geometry["centre_y_mm"]),
        abs(geometry["stock_radius_mm"]),
        abs(dimensions["turnout_origin_y"]),
        abs(dimensions["turnout_radius"]),
    )
    length_budget_mm = 64 * sys.float_info.epsilon * scale_mm
    assert abs(product_join - source_join) <= length_budget_mm
    records = []
    for boundary_owner, join in (("product", product_join),
                                 ("independent_source", source_join)):
        for relation, station in (
            ("below", math.nextafter(join, -math.inf)),
            ("equal", join),
            ("above", math.nextafter(join, math.inf)),
        ):
            source = oracle.source_rail_pose(parameters, station, "TS")
            x, y, angle = module._rea_c10_turnout_outer_gauge_point_at_x(
                dimensions, station,
            )
            assert x == station
            gauge_y = y + 8.25
            angle_budget_rad = 64 * sys.float_info.epsilon * max(
                1.0, abs(angle), abs(source["k_rad"]),
            )
            angle_residual = abs(angle - source["k_rad"])
            gauge_residual = abs(gauge_y - source["y_mm"])
            assert angle_residual <= angle_budget_rad
            assert gauge_residual <= length_budget_mm
            product_branch = ("radcurve" if station < product_join
                              else "turnoutst_main")
            source_branch = ("radcurve" if station < source_join
                             else "turnoutst_main")
            assert source["source_branch"] == source_branch
            own_branch = (product_branch if boundary_owner == "product"
                          else source_branch)
            assert own_branch == ("radcurve" if relation == "below"
                                  else "turnoutst_main")
            if product_branch != source_branch:
                assert min(product_join, source_join) <= station <= max(
                    product_join, source_join,
                )
            records.append({
                "boundary_owner": boundary_owner, "relation": relation,
                "station_mm": station, "product_branch": product_branch,
                "source_branch": source_branch,
                "product_angle_rad": angle, "source_angle_rad": source["k_rad"],
                "product_gauge_y_mm": gauge_y,
                "source_gauge_y_mm": source["y_mm"],
                "angle_residual_rad": angle_residual,
                "gauge_residual_mm": gauge_residual,
                "angle_roundoff_budget_rad": angle_budget_rad,
                "length_roundoff_budget_mm": length_budget_mm,
            })
    assert len(records) == 6
    return {
        "status": "PASS", "product_join_mm": product_join,
        "independent_source_join_mm": source_join,
        "circle_subtraction_scale_mm": scale_mm, "cases": records,
        "product_branch_label": "Strict source-placement predicate",
        "physical_fit": "NOT_PROVED",
    }


def _witnesses(module, source, context, supplement, data):
    """Read actual host arrays and compose independent source matrices."""
    binding = json.loads(supplement.read_text())["canonical_hosts"]
    host_path = Path(binding["path"])
    assert catalogue._hash(host_path) == binding["sha256"]
    captured = json.loads(host_path.read_text())
    assert captured["fixture_sha256"] == xo.FIXTURE_SHA256
    configuration = json.loads(context[0])["configuration"]
    hosts = {}
    for side in ("A", "B"):
        config = configuration["turnout_" + side.lower() + "_config"]
        obj = source.getObject(config["host_object"])
        host = module.turnout_host_alignment(obj)
        hosts[side] = {
            "object_name": obj.Name,
            "points": [[point.x, point.y] for point in host["points"]],
            "headings": host["headings"], "stations": host["stations"],
            "total": host["total"], "toe_chainage": config["toe_chainage"],
            "orientation": config["orientation"], "handing": config["handing"],
        }
        assert hosts[side] == captured["hosts"][side]
    base_z, = {instance["base_z"] for instance in context[3]["instances"]}
    positions = {item["stable_chair_position_identity"]: item
                 for item in context[1]["positions"]}
    checks = {}
    for context_id, target in data["contexts"].items():
        for identity in target["source_position_ids"]:
            position = positions[identity]
            if not position["rail_name"].endswith("stock rail"):
                continue
            side = {"XO-001-A001": "A", "XO-001-B001": "B"}[
                position["parent_turnout_identity"]]
            host = hosts[side]
            common = oracle.expected_world_frame(
                host, toe_chainage_mm=host["toe_chainage"],
                direction=1 if side == "A" else -1, hand=-1,
                station_mm=target["station_mm"], gauge_mm=16.5,
            )
            components, expected_points, closure_triangles = {}, {}, {}
            for part_id, part in data["parts_by_family"][target["family"]].items():
                name = part["native_object"]
                components[name] = _world_frame(
                    position, oracle.native_to_target(data, context_id, part_id),
                    common, base_z + 149 / 60,
                )
                expected_points[name] = [
                    _world_point(common, point)
                    + (base_z + 149 / 60 + point[2],)
                    for point in oracle.source_target_vertices(
                        data, context_id, part_id,
                    )
                ]
                if part.get("fixing_part") == "boss":
                    closure_triangles[name] = [
                        [_world_point(common, point)
                         + (base_z + 149 / 60 + point[2],)
                         for point in triangle]
                        for triangle in _source_closure_triangles(
                            data, context_id, part_id,
                        )
                    ]
            mates = [value for value in target["source_position_ids"]
                     if positions[value]["parent_turnout_identity"]
                     == position["parent_turnout_identity"] and value != identity]
            mate, = mates
            assert positions[mate]["rail_name"].endswith("check rail")
            points = expected_points["base_plinth"]
            centre = tuple((min(p[i] for p in points)
                            + max(p[i] for p in points)) / 2 for i in range(3))
            checks[identity] = {
                "context_id": context_id, "side": side, "family": target["family"],
                "mate_position_id": mate, "components": components,
                "source_vertices": expected_points, "centre_mm": centre,
                "source_closure_triangles": closure_triangles,
                "source_gauge_arithmetic_scale_mm": max(
                    abs(data["parameters"]["rail_geometry"][field])
                    for field in ("centre_y_mm", "stock_radius_mm")
                ),
                "source_decision": {
                    "source_rail_code": target["source_rail_code"],
                    "source_branch": target["source_branch"],
                    "source_curve_end_station_mm": (
                        target["curve_end_station_mm"]
                        if target["side"] == "TS" else None
                    ),
                    "source_chair_code": target["source_code"],
                    "source_station_mm": target["station_mm"],
                    "source_angle_rad": target["chair_k_rad"],
                    "source_gauge_y_mm": (
                        target["aq3_mm"] if target["side"] == "TS" else 0.0
                    ),
                    "source_crop_mm": 0.5 + data["parameters"]["flare_mm"],
                    "source_inner_shear_rad": (
                        -1 if target["family"] == "CCL" else 1
                    ) * data["parameters"]["flare_angle_rad"],
                    "source_outer_shear_rad": (
                        1 if target["family"] == "CCL" else -1
                    ) * data["parameters"]["flare_angle_rad"],
                    "source_flare_mm": data["parameters"]["flare_mm"],
                    "source_flare_angle_rad": (
                        data["parameters"]["flare_angle_rad"]
                    ),
                },
            }
    assert len(checks) == 8
    return checks


def _coverage(receipt, context, baseline, witnesses):
    """Keep canonical deferred records while deriving bounded support."""
    old = baseline["preview"]["source_receipt"]
    old_excluded = {
        item["position_id"]: item for item in old["excluded_positions"]
    }
    positions = {item["stable_chair_position_identity"]: item
                 for item in context[1]["positions"]}
    selected = {item["position_id"]: item for item in receipt["selected_positions"]}
    excluded = {item["position_id"]: item for item in receipt["excluded_positions"]}
    assert len(selected) == receipt["placement_count"] == 203
    assert len(excluded) == receipt["excluded_position_count"] == 152
    assert len(positions) == receipt["analysis_position_count"] == 355
    assert not selected.keys() & excluded.keys()
    assert selected.keys() | excluded.keys() == positions.keys()
    assert receipt["selected_counts"] == dict(paired.COUNTS, CC=12, CCL=4, CCR=4)
    assert Counter(item["exclusion_kind"] for item in excluded.values()) == {
        "source-assignment-deferred": 84,
        "confirmed-no-separate-chair": 48,
        "source-paired-reference-support": 12,
        "source-paired-check-end-support": 8,
    }
    assert receipt["represented_source_position_count"] == 271
    assert receipt["unrepresented_source_position_count"] == 84
    assert receipt["existing_shared_support_count"] == 48
    assert receipt["source_paired_check_support_count"] == 12
    assert receipt["source_paired_check_end_support_count"] == 8
    assert receipt["canonical_deferred_assignment_count"] == 124
    assert sum(bool(p["special_assignment_deferred"])
               for p in positions.values()) == 124
    for name in ("source_context_signature", "source_analysis_signature",
                 "original_analytical_exclusions"):
        assert receipt[name] == old[name]
    assert receipt["original_analytical_exclusions"] == context[3]["analytical_only"]
    assert not receipt["source_document_mutation"]
    assert not receipt["model_support_adjustments_applied"]
    for item in old["selected_positions"]:
        assert selected[item["position_id"]] == item
    for item in old["excluded_positions"]:
        identity = item["position_id"]
        if identity not in witnesses and identity not in {
                w["mate_position_id"] for w in witnesses.values()}:
            assert excluded[identity] == item
    for identity, witness in witnesses.items():
        item = selected[identity]
        assert item["family"] == witness["family"]
        assert item["context_id"] == witness["context_id"]
        assert item["mate_position_id"] == witness["mate_position_id"]
        for field, expected in witness["source_decision"].items():
            actual = item[field]
            if isinstance(expected, float):
                # This budget covers source arithmetic only. It is not a
                # physical-fit or kernel tolerance.
                scale = max(1.0, abs(actual), abs(expected))
                if field == "source_gauge_y_mm":
                    # Circle ordinate subtraction has large operands even
                    # when its gauge offset is small. Keep their scale.
                    scale = max(
                        scale, witness["source_gauge_arithmetic_scale_mm"],
                    )
                budget = 64 * sys.float_info.epsilon * scale
                assert abs(actual - expected) <= budget, (identity, field)
            else:
                assert actual == expected, (identity, field)
        mate = excluded[witness["mate_position_id"]]
        assert mate["supporting_position_id"] == identity
        assert mate["supporting_assembly_placed"] is True
        assert mate["exclusion_kind"] == "source-paired-check-end-support"
        assert mate["assignment_status"] == old_excluded[
            witness["mate_position_id"]
        ]["assignment_status"]
        for position_id in (identity, witness["mate_position_id"]):
            position = positions[position_id]
            assert position["special_assignment_deferred"]
            assert position["timber_identity"] == positions[identity]["timber_identity"]
            derived = selected.get(position_id, excluded.get(position_id))
            for field in POSITION_FIELDS + (
                    "chair_code", "chair_label", "original_exclusion",
                    "key_direction_sign", "key_orientation",
                    "key_orientation_classification"):
                assert derived[field] == old_excluded[position_id][field]
        for name in ("rail_id", "timber_id"):
            assert item[name] == getattr(witness["components"]["base_plinth"], name)


def _assert_ends(result, document, references, witnesses, containment):
    checks, caps = [], []
    for family, digest in MODEL_SHA256.items():
        record = result["families"][family]
        assert record["source_model_sha256"] == digest
        assert record["run"] == "context-native-02"
        assert record["placement"] == "source-check-end-component-frames.v1"
        assert record["component_count"] == 33
        assert record["placement_count"] == 4
        assert record["fixing_head_rotation_rad"] == 0
        assert record["random_export_parity"] is False
        assert record["templot_global_fixing_angle_parity"] is False
        assert record["fixing_angle_frame"] == (
            "uncurved-RH-source-before-common-host-rotation"
        )
        names = tuple(references[family])
        assert tuple(c["source_name"] for c in record["components"]) == names
        for index, placement in enumerate(record["placements"]):
            identity = placement["position_id"]
            witness = witnesses[identity]
            assert witness["family"] == family
            _near_frame(placement, witness["components"]["base_plinth"])
            assert len(placement["components"]) == 33
            shapes = {}
            for name, component in zip(names, placement["components"]):
                frame = witness["components"][name]
                _near_frame(component, frame)
                assert component["source_name"] == name
                assert tuple(component["placement_identity"]) == (
                    identity, digest, name,
                )
                children = document.getObject(
                    family + "_" + name,
                ).Shape.childShapes()
                assert len(children) == 4
                child = children[index]
                shapes[name] = child
                checks.append(dict(
                    p._compare_component(child, references[family][name], frame),
                    source_vertex_residual_mm=_source_vertices(
                        child, witness["source_vertices"][name],
                    ), position_id=identity, component=name,
                ))
            for fixing in range(4):
                name = "SourceFixing" + (f"{fixing * 4:03d}" if fixing else "")
                boss = shapes[name]
                footprint, proof = _mounting_footprint(
                    boss, witness["source_closure_triangles"][name],
                )
                proof.update(position_id=identity, fixing=name)
                containment(footprint, shapes["base_plinth"], proof)
                caps.append(proof)
    assert len(checks) == 264 and len(caps) == 32
    assert {item["position_id"] for family in MODEL_SHA256
            for item in result["families"][family]["placements"]} == witnesses.keys()
    return {"components": checks, "boss_cap_containment": caps}


def _assert_preview(result, document, references, baseline, witnesses,
                    containment):
    catalogue.helpers._active_document_state(document)
    assert not document.FileName and not document.Temporary
    assert result["contract_id"] == "tracktemplate.private-catalogue-crossover.v4"
    assert result["placement_count"] == result["track_placements_added"] == 203
    assert result["family_count"] == 11 and result["assembly_group_count"] == 16
    assert result["component_count"] == 477 and result["layer_count"] == 479
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["geometry_rebuilt"] is False
    assert result["length_basis"] == "model" and result["length_unit"] == "mm"
    assert result["scale_denominator"] == "76.2"
    names = tuple(layer["name"] for layer in baseline["preview"]["layers"])
    names += tuple(family + "_" + name for family in MODEL_SHA256
                   for name in references[family])
    assert tuple(obj.Name for obj in document.Objects) == names
    assert tuple(layer["name"] for layer in result["layers"]) == names
    for obj in document.Objects:
        assert obj.TypeId == "Part::Feature"
        assert "GeneratedBy" not in obj.PropertiesList
    for obj in document.Objects[:2]:
        assert not obj.Shape.Faces and not obj.Shape.Solids
    baseline_checks = []
    for group, old in baseline["preview"]["families"].items():
        actual = result["families"][group]
        for name in ("run", "source_model_sha256", "source_bindings",
                     "context", "placement_count", "component_count"):
            assert json.loads(json.dumps(actual[name])) == old[name]
        assert len(actual["placements"]) == len(old["placements"])
        for index, (current, accepted) in enumerate(zip(
                actual["placements"], old["placements"])):
            for name in POSITION_FIELDS + FRAME_FIELDS:
                assert json.loads(json.dumps(current[name])) == accepted[name]
            assert len(current["components"]) == len(accepted["components"])
            for component, previous in zip(
                    current["components"], accepted["components"]):
                name = component["source_name"]
                assert name == previous["source_name"]
                for field in ("source_identity", "placement_identity"):
                    assert tuple(component[field]) == tuple(previous[field])
                frame_record = dict(accepted)
                if group == "CC":
                    for field in FRAME_FIELDS:
                        assert json.loads(json.dumps(component[field])) == previous[field]
                        frame_record[field] = previous[field]
                else:
                    assert not any(field in component for field in FRAME_FIELDS)
                frame = _frame(frame_record)
                children = document.getObject(
                    group.replace("-", "_") + "_" + name,
                ).Shape.childShapes()
                assert len(children) == len(old["placements"])
                baseline_checks.append(dict(
                    p._compare_component(children[index], references[group][name], frame),
                    position_id=frame.position_id, group=group, component=name,
                ))
        print("CHECK_END_BASELINE_GROUP_PASS", group, flush=True)
    assert len(baseline_checks) == 3951
    assert result["solid_count"] == sum(len(obj.Shape.Solids)
                                       for obj in document.Objects)
    return {"baseline": baseline_checks,
            "check_ends": _assert_ends(
                result, document, references, witnesses, containment,
            )}


def _inspection_frames(baseline, witnesses):
    groups = {group: tuple(_frame(item) for item in record["placements"])
              for group, record in baseline["preview"]["families"].items()}
    for identity, witness in witnesses.items():
        label = witness["context_id"]
        groups.setdefault(label, [])
        groups[label].append(SimpleNamespace(
            position_id=identity, origin_mm=witness["centre_mm"],
        ))
    return groups


def _check_factory_inputs(arguments, baseline, witnesses):
    """Check the full analytical command boundary before materialisation."""
    assert len(arguments) == 5
    groups, _context, receipt, _verify = arguments[1:]
    assert set(groups) == set(paired.COUNTS) | {"CC", "CCL", "CCR"}
    for group, old in baseline["preview"]["families"].items():
        assert len(groups[group]) == len(old["placements"])
        for placement, accepted in zip(groups[group], old["placements"]):
            for name in POSITION_FIELDS + FRAME_FIELDS:
                assert json.loads(json.dumps(getattr(placement, name))) == accepted[name]
            if group == "CC":
                components = {c["source_name"]: c for c in accepted["components"]}
                for index, fixing in enumerate(placement.fixing_frames):
                    name = "SourceFixing" + (f"{index * 4:03d}" if index else "")
                    _near_frame(components[name], fixing)
    for family in MODEL_SHA256:
        assert len(groups[family]) == 4
        for placement in groups[family]:
            witness = witnesses[placement.position_id]
            assert placement.family == family == witness["family"]
            _near_frame(vars(placement), witness["components"]["base_plinth"])
            for name in CHECK_NAMES:
                _near_frame(vars(placement.check_frame), witness["components"][name])
            for index, fixing in enumerate(placement.fixing_frames):
                name = "SourceFixing" + (f"{index * 4:03d}" if index else "")
                _near_frame(vars(fixing), witness["components"][name])
    return receipt


def _parametric_native_frames(path, prepared, references, data):
    """Prove family transforms without admitting another whole host.

    Explicit circle points and tangents supply independent host frames.
    The pure placement function receives those same canonical inputs;
    the existing adapter must preserve every retained component. The
    standalone matrix owns interpolation and radius eligibility tests.
    These synthetic parameters give no physical-fit qualification.
    """
    active = App.ActiveDocument
    registry = dict(App.listDocuments())
    if App.GuiUp:
        selection = lifecycle._selection_snapshot(App, Gui)
        preselection = lifecycle._preselection_snapshot(App, Gui)
    groups = {family: [] for family in MODEL_SHA256}
    witnesses = {}
    base_z, initial_heading = 2.75, 0.37
    for context_id, target in data["contexts"].items():
        family = target["family"]
        for direction in (-1, 1):
            station = 500.0 + direction * target["station_mm"]
            for curve_sign in (-1, 0, 1):
                curvature = curve_sign / 1200.0
                heading = initial_heading + curvature * station
                if curvature:
                    point = (
                        314.0 + (math.sin(heading)
                                 - math.sin(initial_heading)) / curvature,
                        -271.0 + (math.cos(initial_heading)
                                  - math.cos(heading)) / curvature,
                    )
                else:
                    point = (314.0 + station * math.cos(initial_heading),
                             -271.0 + station * math.sin(initial_heading))
                travel = heading + (math.pi if direction < 0 else 0.0)
                tangent = (math.cos(travel), math.sin(travel))
                normal = (-tangent[1], tangent[0])
                common = {
                    "origin_mm": tuple(point[i] + 8.25 * normal[i]
                                       for i in (0, 1)),
                    "x_axis": tangent, "y_axis": normal,
                }
                identity = f"frame:{context_id}:{direction}:{curve_sign}"
                position = {
                    "stable_chair_position_identity": identity,
                    "rail_identity": identity + ":rail",
                    "timber_identity": identity + ":timber",
                }
                placement = place_check_end(
                    identity, position["rail_identity"],
                    position["timber_identity"], point, travel, base_z,
                    side=target["side"], family=family,
                    source_angle_rad=target["chair_k_rad"],
                    source_gauge_y_mm=(target["aq3_mm"]
                                       if target["side"] == "TS" else 0.0),
                )
                groups[family].append(placement)
                frames, vertices = {}, {}
                for part_id, part in data["parts_by_family"][family].items():
                    name = part["native_object"]
                    frames[name] = _world_frame(
                        position,
                        oracle.native_to_target(data, context_id, part_id),
                        common, base_z + 149 / 60,
                    )
                    vertices[name] = [
                        _world_point(common, vertex)
                        + (base_z + 149 / 60 + vertex[2],)
                        for vertex in oracle.source_target_vertices(
                            data, context_id, part_id,
                        )
                    ]
                witnesses[identity] = {
                    "context_id": context_id, "direction": direction,
                    "curvature_per_mm": curvature,
                    "host_station_mm": station, "host_point_mm": point,
                    "travel_heading_rad": travel,
                    "components": frames, "source_vertices": vertices,
                }
    assert len(witnesses) == 24
    comparisons, cases = [], {}
    for family, placements in groups.items():
        assert len(placements) == 12
        selected = prepared[family]
        choice, specs, prepare = adapter._prepare_catalogue_family(
            path, tuple(placements), None,
            {"scope": "component mathematics; whole host not admitted",
             "physical_fit": "NOT_PROVED"},
            family=family, placement_type=CheckEndPlacement,
            model_sha256=MODEL_SHA256[family],
            source_names=tuple(item.name for item in selected.components),
            run=selected.run, source_context=selected.context,
        )
        result = adapter._materialise_preview(
            family, {}, specs, prepare,
            lambda: reader.verify_catalogue_sources(choice),
        )
        document = App.getDocument(result["document_name"])
        try:
            if App.GuiUp:
                assert lifecycle._selection_snapshot(App, Gui) == selection, (
                    "Parametric materialisation changed selection"
                )
                assert lifecycle._preselection_snapshot(App, Gui) == preselection, (
                    "Parametric materialisation changed preselection"
                )
            assert result["placement_count"] == 12
            assert result["component_count"] == result["layer_count"] == 33
            assert result["geometry_rebuilt"] is False
            assert result["production_geometry_authorized"] is False
            assert not document.FileName and not document.Temporary
            for index, placement in enumerate(result["placements"]):
                identity = placement["position_id"]
                expected = witnesses[identity]
                _near_frame(placement, expected["components"]["base_plinth"])
                for component in placement["components"]:
                    name = component["source_name"]
                    frame = expected["components"][name]
                    _near_frame(component, frame)
                    children = document.getObject(name).Shape.childShapes()
                    assert len(children) == 12
                    child = children[index]
                    comparisons.append(dict(
                        p._compare_component(
                            child, references[family][name], frame,
                        ),
                        source_vertex_residual_mm=_source_vertices(
                            child, expected["source_vertices"][name],
                        ), position_id=identity, component=name,
                    ))
                cases[identity] = {
                    key: value for key, value in expected.items()
                    if key not in ("components", "source_vertices")
                }
            if App.GuiUp:
                assert lifecycle._selection_snapshot(App, Gui) == selection, (
                    "Parametric comparison changed selection"
                )
                assert lifecycle._preselection_snapshot(App, Gui) == preselection, (
                    "Parametric comparison changed preselection"
                )
        finally:
            App.closeDocument(document.Name)
            App.setActiveDocument(active.Name)
            if App.GuiUp:
                lifecycle._restore_selection(App, Gui, selection)
                lifecycle._restore_preselection(App, Gui, preselection)
                assert lifecycle._selection_snapshot(App, Gui) == selection
                assert lifecycle._preselection_snapshot(App, Gui) == preselection
        assert App.listDocuments() == registry
        reader.verify_catalogue_sources(selected)
    assert len(comparisons) == 792
    return {
        "status": "PASS", "assembly_count": 24,
        "component_comparisons": comparisons, "cases": cases,
        "whole_preview_host_admission": "UNCHANGED",
        "radius_eligibility": "SEPARATE_STANDALONE_PROOF",
        "physical_fit": "NOT_PROVED",
    }


def validate():
    """Run one complete build and the focused check-end lifecycle failures."""
    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    path = Path(os.environ["TRACKTEMPLATE_CHAIR_CATALOGUE"]).resolve()
    supplement = Path(os.environ["TRACKTEMPLATE_PAIRED_CATALOGUE"]).resolve()
    fixture = Path(os.environ["TRACKTEMPLATE_CROSSOVER_REFERENCE_FIXTURE"])
    source_directory = Path(os.environ["TRACKTEMPLATE_TEMPLOT_SOURCE"])
    source_context = Path(os.environ["TRACKTEMPLATE_CHECK_END_SOURCE_CONTEXT"])
    baseline_path = Path(os.environ["TRACKTEMPLATE_CENTRAL_BASELINE_RECEIPT"])
    run_dir = Path(os.environ["TRACKTEMPLATE_CHECK_END_PREVIEW_RUN_DIR"]).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "RUNNING", "gui": bool(App.GuiUp),
               "physical_fit": "NOT_PROVED", "baseline_sha256": BASELINE_SHA256}
    initial = catalogue.helpers._document_state()
    try:
        assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
        baseline = _read_baseline(baseline_path)
        data = oracle.load(source_directory, path.parent, source_context)
        receipt["source_analytical_admission"] = oracle.analytical_admission(data)
        references, prepared = _references(path, supplement, run_dir)
        containment_path = path.parent / "final_adapter/inventory_native.py"
        containment = _containment(containment_path)
        data["bindings"][str(containment_path)] = CONTAINMENT_SHA256
        receipt["native_source_bases"] = _native_source_bases(data, references)
        receipt["native_source_closure_controls"] = _native_closure_controls(
            data, references, containment,
        )
        launcher = runpy.run_path(str(ROOT / "TrackTemplate.FCMacro"))
        api, bootstrap = launcher["_load_foundation"](ROOT)
        session, routing = launcher["_load_modular_transition_workflow"](
            ROOT, api, bootstrap,
        )
        assert launcher["FOUNDATION_RESULT"]["matched_profile_id"] == p.PROFILE
        receipt.update(profile=p.PROFILE, routing=routing)
        module = session.module
        receipt["source_boundary_resolver"] = _source_boundary_resolver(
            module, source_directory, data,
        )
        command = session.preview_private_catalogue_crossover_chairs
        target = run_dir / "XO-001.FCStd"
        shutil.copy2(fixture, target)
        source = App.openDocument(str(target))
        source.UndoMode = 1
        foreign = App.newDocument("CheckEndUnrelatedWitness")
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
        witnesses = _witnesses(module, source, context, supplement, data)
        receipt["source_bindings"] = data["bindings"]
        receipt["source_references"] = data["references"]
        receipt["source_witnesses"] = {
            identity: {key: value for key, value in witness.items()
                       if key not in ("components", "source_vertices",
                                      "source_closure_triangles")}
            for identity, witness in witnesses.items()
        }
        receipt["source_position_decisions"] = {
            position_id: dict(witness["source_decision"],
                              supporting_position_id=identity)
            for identity, witness in witnesses.items()
            for position_id in (identity, witness["mate_position_id"])
        }
        assert len(receipt["source_position_decisions"]) == 16
        xo._state(module, source)
        combined._settle(source)
        source_state = xo._state(module, source)
        foreign_state = combined._foreign_state(foreign)
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
            assert all(identities[key].Shape.isSame(shape)
                       for key, shape in shapes.items()), stage
            assert lifecycle._selection_snapshot(App, gui) == selection, stage
            assert lifecycle._preselection_snapshot(App, gui) == preselection
            catalogue.helpers._active_document_state(active)

        def create(**options):
            kwargs = dict(paired_contexts_path=supplement, include_central_cc=True,
                          include_check_ends=True)
            kwargs.update(options)
            return command(source, "XO-001", path, **kwargs)

        captured = {}
        native_create = adapter.create_private_catalogue_crossover_preview

        def capture_factory(*args, **kwargs):
            captured.update(args=args, kwargs=kwargs)
            return native_create(*args, **kwargs)

        if os.environ.get("TRACKTEMPLATE_CHECK_END_PREFLIGHT_ONLY") == "1":
            def capture_only(*args, **kwargs):
                captured.update(args=args, kwargs=kwargs)
                return {"captured": True}

            with patch.object(
                    session, "_private_catalogue_crossover_preview_factory",
                    side_effect=capture_only):
                assert create() == {"captured": True}
            source_receipt = _check_factory_inputs(
                captured["args"], baseline, witnesses,
            )
            _coverage(source_receipt, context, baseline, witnesses)
            unchanged("analytical command preflight", source)
            receipt.update(status="PASS_ANALYTICAL_COMMAND_PREFLIGHT",
                           source_receipt=source_receipt)
            print("CHECK_END_ANALYTICAL_COMMAND_PREFLIGHT_PASS", flush=True)
            return

        receipt["parametric_native_frames"] = _parametric_native_frames(
            path, prepared, references, data,
        )
        unchanged("parametric family documents closed", source)
        print("CHECK_END_PARAMETRIC_NATIVE_FRAMES_PASS", flush=True)

        started = time.perf_counter()
        with patch.object(session, "_private_catalogue_crossover_preview_factory",
                          side_effect=capture_factory), patch.object(
                App, "openDocument", side_effect=AssertionError(
                    "Product restored an external source document")):
            result = create()
        _check_factory_inputs(captured["args"], baseline, witnesses)
        receipt["elapsed_creation_seconds"] = time.perf_counter() - started
        preview = App.getDocument(result["document_name"])
        receipt["preview"] = result
        _coverage(result["source_receipt"], context, baseline, witnesses)
        receipt["comparisons"] = _assert_preview(
            result, preview, references, baseline, witnesses, containment,
        )
        unchanged("created", preview)
        print("CHECK_END_COMPLETE_PREVIEW_PASS", flush=True)
        before = tuple(obj.Shape for obj in preview.Objects)
        assert preview.UndoCount == 1
        preview.undo()
        assert not preview.Objects
        preview.redo()
        assert len(preview.Objects) == len(before)
        assert all(p.catalogue_adapter._same_presented_shape(obj.Shape, shape)
                   for obj, shape in zip(preview.Objects, before))
        receipt["redo_check_end_comparisons"] = _assert_ends(
            result, preview, references, witnesses, containment,
        )
        unchanged("Undo/Redo", preview)
        receipt["undo_redo"] = "PASS"
        if gui:
            receipt["images"] = whole._gui_inspection(
                preview, _inspection_frames(baseline, witnesses), context, run_dir,
            )
            assert len(receipt["images"]) == 36
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

        with patch.object(App, "newDocument", side_effect=AssertionError(
                "Missing paired prerequisite created a document")):
            receipt["paired_prerequisite_refusal"] = catalogue._reject(
                lambda: create(paired_contexts_path=None), ValueError,
            )
        unchanged("early prerequisite refusal", source)
        with patch.object(App, "newDocument", side_effect=AssertionError(
                "Missing central prerequisite created a document")):
            receipt["central_prerequisite_refusal"] = catalogue._reject(
                lambda: create(include_central_cc=False), ValueError,
            )
        unchanged("central prerequisite refusal", source)
        original_read = reader._read
        arguments = captured["args"]
        placements, context_shapes, source_receipt, verify_source = arguments[1:]
        receipt["focused_failures"] = {}
        for family, digest in MODEL_SHA256.items():
            selected = prepared[family]
            assert len(placements[family]) == 4

            def changed_bytes(filename):
                content = original_read(filename)
                return (content + b"\n" if str(filename) == selected.model_path
                        else content)

            checks = {}
            with patch.object(reader, "_read", changed_bytes), patch.object(
                    App, "newDocument", side_effect=AssertionError(
                        "Changed check-end geometry created a document")):
                checks["early_model_refusal"] = catalogue._reject(create, ValueError)
            unchanged(family + " early model refusal", source)

            def focused(verify=verify_source):
                choice, specs, prepare = adapter._prepare_catalogue_family(
                    path, placements[family], context_shapes, source_receipt,
                    family=family, placement_type=CheckEndPlacement,
                    model_sha256=digest,
                    source_names=tuple(item.name for item in selected.components),
                    run=selected.run, source_context=selected.context,
                )

                def verify_inputs():
                    verify()
                    reader.verify_catalogue_sources(choice)

                return adapter._materialise_preview(
                    family, source_receipt, specs, prepare, verify_inputs,
                )

            def late_bytes(filename):
                if App.ActiveDocument not in registry.values():
                    assert len(App.ActiveDocument.Objects) == 35
                    return changed_bytes(filename)
                return original_read(filename)

            with patch.object(reader, "_read", late_bytes):
                checks["late_model_refusal"] = catalogue._reject(focused, ValueError)
            unchanged(family + " late model rollback", source)
            original_host = module.turnout_host_alignment

            def stale_source():
                assert App.ActiveDocument not in registry.values()
                assert len(App.ActiveDocument.Objects) == 35

                def changed_host(obj):
                    host = dict(original_host(obj))
                    headings = list(host["headings"])
                    headings[0] += 1e-8
                    return dict(host, headings=headings)

                with patch.object(module, "turnout_host_alignment", changed_host):
                    verify_source()

            checks["late_host_refusal"] = paired.helpers._reject(
                lambda: focused(stale_source), "changed",
            )
            unchanged(family + " late host rollback", source)
            original_check = adapter._same_presented_shape

            def reject_stored(actual, expected):
                if App.ActiveDocument not in registry.values():
                    assert len(App.ActiveDocument.Objects) == 35
                    return False
                return original_check(actual, expected)

            with patch.object(adapter, "_same_presented_shape", reject_stored):
                checks["stored_shape_refusal"] = catalogue._reject(focused, ValueError)
            unchanged(family + " stored shape rollback", source)
            receipt["focused_failures"][family] = checks
            print("CHECK_END_FOCUSED_ROLLBACK_PASS", family, flush=True)
        for group in (*whole.COUNTS, "CC", "CCL", "CCR"):
            reader.verify_catalogue_sources(prepared[group])
        paired.pairs.verify_paired_catalogue(tuple(
            prepared[group] for group in paired.PAIR_IDS
        ))
        for filename, digest in data["bindings"].items():
            assert catalogue._hash(Path(filename)) == digest
        assert catalogue._hash(source.FileName) == xo.FIXTURE_SHA256
        assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
        assert xo._context(module, source) == context
        receipt.update(
            source_after=xo._state(module, source),
            foreign_after=combined._foreign_state(foreign),
            fixture_sha256=xo.FIXTURE_SHA256, source_bindings_unchanged=True,
            baseline_component_comparisons=3951, check_end_component_comparisons=264,
            redo_check_end_component_comparisons=264, transaction_rollback="PASS",
            rollback_scope="new check-end preparation and shared lifecycle",
            complete_baseline_failure_suite="reused accepted central CC and paired receipts",
            legacy_exclusions_unchanged=True,
        )
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
