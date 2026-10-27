"""Prove complete private XO-001 crossing and exit placement coverage.

The frozen PR 214 receipt binds 237 assemblies and 4,889 components.
Independent source witnesses qualify 24 additions. Two finite-rail end
candidates remain evidenced exclusions; no physical-fit acceptance follows.
"""

from collections import Counter
import importlib.util
import json
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


def _load_previous():
    specification = importlib.util.spec_from_file_location(
        "_crossing_exit_previous",
        ROOT / "tests/freecad_validate_phase9b_catalogue_single_rail.py",
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    assert module.ROOT == ROOT
    return module


previous = _load_previous()
central, p, xo = previous.central, previous.p, previous.xo
adapter, lifecycle = previous.adapter, previous.lifecycle
catalogue, combined, reader = (
    previous.catalogue, previous.combined, previous.reader,
)

SENTINEL = "Phase 9B crossing-exit catalogue FreeCAD validation passed"
BASELINE_SHA256 = (
    "21407f24f9819a37fc57ab257b8fa6bf4c258d0b6a5ebb30c60c22c465c6afba"
)
CROSSING_GROUPS = (
    "RH-X1-Z", "RH-X2-Y", "RH-X3-X", "RH-X4-A",
    "RH-X5-B", "RH-X6-C", "RH-X7-D", "RH-X8-E",
)
EXIT_GROUPS = {"ExitS1": ("S1", 4), "ExitS1J": ("S1J", 2),
               "ExitL1": ("L1", 2)}
NEW_COUNTS = {**{group: 2 for group in CROSSING_GROUPS},
              **{group: count for group, (_family, count)
                 in EXIT_GROUPS.items()}}
EVIDENCED_EXCLUSIONS = {
    "XO-001:chair:xo-001-envelope-001:vee-point-rail",
    "XO-001:chair:xo-001-envelope-001:vee-splice-rail",
}


def _read_baseline(path):
    """Bind the complete accepted fixed-XO result and its exclusions."""
    assert catalogue._hash(path) == BASELINE_SHA256
    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["status"] == "PASS" and not result["gui"]
    assert result["profile"] == p.PROFILE
    assert result["fixture_sha256"] == xo.FIXTURE_SHA256
    assert result["owned_documents_closed"]
    assert result["source_bindings_unchanged"]
    assert result["baseline_component_comparisons"] == 4215
    assert result["new_component_comparisons"] == 674
    assert result["preview"]["placement_count"] == 237
    assert result["preview"]["layer_count"] == 536
    assert result["preview"]["assembly_group_count"] == 19
    assert result["preview"]["source_receipt"][
        "unrepresented_source_position_count"] == 50
    return result


def _references(path, paired, crossing, run_dir, crossing_reader):
    """Load copied, source-qualified native components without builders."""
    references, prepared = previous._references(path, paired, run_dir)
    for group, family in previous.GROUP_FAMILY.items():
        references[group] = references[family]
        prepared[group] = prepared[family]
    for group, (family, _count) in EXIT_GROUPS.items():
        references[group] = references[family]
        prepared[group] = prepared[family]
    choices = crossing_reader.prepare_crossing_catalogue(crossing)
    assert tuple(choice.run for choice in choices) == CROSSING_GROUPS
    for choice in choices:
        native = catalogue._reference((choice.run, {
            "run": choice.run,
            "model": {"path": choice.model_path,
                      "sha256": choice.model_sha256},
        }), run_dir / "native-copies")
        references[choice.run] = {
            name: shape for name, _label, shape, _matrix in native
        }
        prepared[choice.run] = choice
        assert tuple(references[choice.run]) == tuple(
            component.name for component in choice.components
        )
    return references, prepared


def _assert_baseline(result, document, references, baseline):
    """Compare every accepted component in its unchanged recorded frame."""
    checks = []
    for group, accepted in baseline["preview"]["families"].items():
        current = result["families"][group]
        for field in ("run", "source_model_sha256", "source_bindings",
                      "context", "placement_count", "component_count",
                      "components", "placements"):
            assert json.loads(json.dumps(current[field])) == accepted[field], (
                group, field,
            )
        for index, placement in enumerate(accepted["placements"]):
            for component in placement["components"]:
                name = component["source_name"]
                frame_record = dict(placement)
                for field in previous.previous.FRAME_FIELDS:
                    if field in component:
                        frame_record[field] = component[field]
                frame = central._frame(frame_record)
                children = document.getObject(
                    group.replace("-", "_") + "_" + name,
                ).Shape.childShapes()
                assert len(children) == len(accepted["placements"])
                checks.append(dict(
                    p._compare_component(
                        children[index], references[group][name], frame,
                    ), group=group, position_id=frame.position_id,
                    component=name,
                ))
        print("CROSSING_EXIT_BASELINE_GROUP_PASS", group, flush=True)
    assert len(checks) == 4889
    return checks


def _coverage(receipt, context, baseline, witnesses):
    """Require a complete identity partition, including evidenced absences."""
    old = baseline["preview"]["source_receipt"]
    positions = {item["stable_chair_position_identity"]: item
                 for item in context[1]["positions"]}
    selected = {item["position_id"]: item
                for item in receipt["selected_positions"]}
    excluded = {item["position_id"]: item
                for item in receipt["excluded_positions"]}
    assert len(selected) == receipt["placement_count"] == 261
    assert len(excluded) == receipt["excluded_position_count"] == 94
    assert len(positions) == receipt["analysis_position_count"] == 355
    assert not selected.keys() & excluded.keys()
    assert selected.keys() | excluded.keys() == positions.keys()
    assert len(witnesses) == 24
    assert receipt["represented_source_position_count"] == 353
    assert receipt["unrepresented_source_position_count"] == 2
    assert receipt["unresolved_remaining_position_count"] == 0
    assert receipt["existing_shared_support_count"] == 48
    assert receipt["source_paired_check_support_count"] == 12
    assert receipt["source_paired_check_end_support_count"] == 8
    assert receipt["source_paired_crossing_support_count"] == 24
    assert receipt["evidenced_source_exclusion_count"] == 2
    assert receipt["canonical_deferred_assignment_count"] == 124
    assert sum(bool(item["special_assignment_deferred"])
               for item in positions.values()) == 124
    for field in ("source_context_signature", "source_analysis_signature",
                  "original_analytical_exclusions"):
        assert receipt[field] == old[field]
    assert receipt["original_analytical_exclusions"] == context[3]["analytical_only"]
    assert not receipt["source_document_mutation"]
    assert not receipt["model_support_adjustments_applied"]
    old_selected = {item["position_id"]: item
                    for item in old["selected_positions"]}
    for identity, item in old_selected.items():
        assert selected[identity] == item
    assert selected.keys() - old_selected.keys() == witnesses.keys()
    historical_exclusions = {
        item["position_id"]: item for item in old["excluded_positions"]
        if item["exclusion_kind"] != "source-assignment-deferred"
    }
    assert len(historical_exclusions) == 68
    for identity, item in historical_exclusions.items():
        assert excluded[identity] == item
    source_exclusions = set(excluded) - set(historical_exclusions)
    assert len(source_exclusions) == 26
    assert EVIDENCED_EXCLUSIONS <= source_exclusions
    for identity in EVIDENCED_EXCLUSIONS:
        assert excluded[identity]["exclusion_kind"] != "source-assignment-deferred"
        assert excluded[identity]["rail_id"] == positions[identity]["rail_identity"]
    companions = {}
    for identity, witness in witnesses.items():
        if witness["group"] not in CROSSING_GROUPS:
            continue
        owner = positions[identity]
        for mate_id, mate in positions.items():
            if (mate_id != identity
                    and mate["parent_turnout_identity"]
                    == owner["parent_turnout_identity"]
                    and mate["timber_identity"] == owner["timber_identity"]
                    and mate_id in source_exclusions):
                companions[mate_id] = identity
    assert len(companions) == 24
    assert source_exclusions == companions.keys() | EVIDENCED_EXCLUSIONS
    for identity, owner in companions.items():
        item = excluded[identity]
        assert item["exclusion_kind"] == "source-paired-crossing-support"
        assert item["supporting_position_id"] == owner
        assert item["supporting_assembly_placed"] is True
    for identity, witness in witnesses.items():
        item = selected[identity]
        assert item["family"] == witness["family"]
        assert item["physical_fit"] == "NOT_PROVED"
        for field in ("position_id", "rail_id", "timber_id", "chair_code",
                      "chair_label", "original_exclusion", "key_direction_sign",
                      "key_orientation", "key_orientation_classification"):
            before, = [entry for entry in old["excluded_positions"]
                       if entry["position_id"] == identity]
            assert item[field] == before[field]
    discrepancies = receipt["accepted_heel_family_discrepancies"]
    assert len(discrepancies) == 10
    assert len({item["position_id"] for item in discrepancies}) == 10
    assert Counter(item["timber"] for item in discrepancies) == {
        "S13": 4, "T1": 4, "T2": 2,
    }
    for discrepancy in discrepancies:
        identity = discrepancy["position_id"]
        assert selected[identity] == old_selected[identity]
        assert discrepancy["accepted_preview_family"] == "S1"
        assert discrepancy["source_family"] == "L1"


def _finite_rail_exclusions(receipt, context):
    """Clip actual finite segments against polygon edges independently.

    This uses neither the product width-axis separation nor its endpoint
    residual. A boundary touch counts as an intersection, with no padding
    or physical-fit tolerance added to the actual polygon.
    """
    positions = {item["stable_chair_position_identity"]: item
                 for item in context[1]["positions"]}
    rails = {item["stable_identity"]: item for item in context[4]}
    timbers = {item["stable_identity"]: item for item in context[5]}
    exclusions = {item["position_id"]: item
                  for item in receipt["excluded_positions"]}

    def cross(first, second):
        return first[0] * second[1] - first[1] * second[0]

    def intersects(first, last, polygon):
        edges = tuple(zip(polygon, polygon[1:] + polygon[:1]))
        area = sum(cross(start, end) for start, end in edges)
        assert area != 0
        orientation = 1 if area > 0 else -1
        low, high = 0.0, 1.0
        direction = tuple(last[i] - first[i] for i in (0, 1))
        for start, end in edges:
            edge = tuple(end[i] - start[i] for i in (0, 1))
            offset = tuple(first[i] - start[i] for i in (0, 1))
            value = orientation * cross(edge, offset)
            slope = orientation * cross(edge, direction)
            if slope == 0:
                if value < 0:
                    return False
            elif slope > 0:
                low = max(low, -value / slope)
            else:
                high = min(high, -value / slope)
            if low > high:
                return False
        return True

    square = [[0, 0], [1, 0], [1, 1], [0, 1]]
    assert intersects((-1, 0.5), (2, 0.5), square)
    assert intersects((-1, 0), (0, 0), square)
    assert intersects((0.1, 0.1), (0.9, 0.9), square)
    assert not intersects((-1, -1), (-0.1, -0.1), square)
    assert not intersects((2, -1), (2, 2), square)
    checks = {}
    for identity in sorted(EVIDENCED_EXCLUSIONS):
        position = positions[identity]
        rail = rails[position["rail_identity"]]
        timber = timbers[position["timber_identity"]]
        polygon = timber["outline_polygon"]
        points = rail["points"]
        assert position["centre_point"] == points[-1]
        hits = sum(intersects(first, last, polygon)
                   for first, last in zip(points, points[1:]))
        assert hits == 0
        proof = exclusions[identity]
        assert proof["exclusion_kind"] == (
            "source-anchor-outside-finite-rail-domain"
        )
        assert proof["finite_rail_segment_count"] == len(points) - 1
        assert proof["analytical_padding_unchanged"] is True
        assert proof["physical_fit"] == "NOT_ASSESSED"
        assert context[2]["position_tolerance"] == 0.2
        checks[identity] = {
            "finite_segment_count": len(points) - 1,
            "actual_polygon_intersections": hits,
            "canonical_position_is_exact_rail_endpoint": True,
            "legacy_analytical_padding_mm_unchanged": 0.2,
            "physical_fit": "NOT_ASSESSED",
        }
    return checks


def _assert_new(result, document, references, prepared, witnesses):
    """Check every added component against its independent source frame."""
    checks, seen = [], set()
    for group, count in NEW_COUNTS.items():
        record = result["families"][group]
        choice = prepared[group]
        names = tuple(references[group])
        assert record["source_model_sha256"] == choice.model_sha256
        assert record["run"] == choice.run
        assert record["context"] == choice.context
        assert record["component_count"] == len(names)
        assert record["placement_count"] == count
        assert tuple(item["source_name"] for item in record["components"]) == names
        for index, placement in enumerate(record["placements"]):
            identity = placement["position_id"]
            assert identity not in seen
            seen.add(identity)
            witness = witnesses[identity]
            assert witness["group"] == group
            assert witness["family"] == choice.label
            assert tuple(witness["components"]) == names
            assert len(placement["components"]) == len(names)
            for name, component in zip(names, placement["components"]):
                assert component["source_name"] == name
                assert tuple(component["placement_identity"]) == (
                    identity, choice.model_sha256, name,
                )
                frame = witness["components"][name]
                central._near_frame(
                    placement if group in CROSSING_GROUPS else component, frame,
                )
                layer = document.getObject(
                    group.replace("-", "_") + "_" + name,
                )
                children = layer.Shape.childShapes()
                assert len(children) == count
                checks.append(dict(
                    p._compare_component(
                        children[index], references[group][name], frame,
                    ), group=group, position_id=identity, component=name,
                ))
    assert seen == witnesses.keys()
    assert len(checks) == sum(
        count * len(references[group]) for group, count in NEW_COUNTS.items()
    )
    return checks


def _assert_preview(result, document, references, prepared, baseline, witnesses):
    catalogue.helpers._active_document_state(document)
    assert not document.FileName and not document.Temporary
    assert result["contract_id"] == "tracktemplate.private-catalogue-crossover.v6"
    assert result["placement_count"] == result["track_placements_added"] == 261
    assert result["assembly_group_count"] == 30
    assert set(result["families"]) == (
        set(baseline["preview"]["families"]) | set(NEW_COUNTS)
    )
    assert result["project_status"] == "reference-only"
    assert result["intended_uses"] == ["private-development"]
    assert result["production_geometry_authorized"] is False
    assert result["geometry_rebuilt"] is False
    assert result["length_basis"] == "model" and result["length_unit"] == "mm"
    assert result["scale_denominator"] == "76.2"
    names = tuple(item["name"] for item in baseline["preview"]["layers"])
    names += tuple(group.replace("-", "_") + "_" + name
                   for group in NEW_COUNTS for name in references[group])
    assert tuple(obj.Name for obj in document.Objects) == names
    assert tuple(item["name"] for item in result["layers"]) == names
    assert result["layer_count"] == len(names)
    assert result["component_count"] == len(names) - 2
    for obj in document.Objects:
        assert obj.TypeId == "Part::Feature"
        assert "GeneratedBy" not in obj.PropertiesList
    for obj in document.Objects[:2]:
        assert not obj.Shape.Faces and not obj.Shape.Solids
    old_checks = _assert_baseline(result, document, references, baseline)
    new_checks = _assert_new(result, document, references, prepared, witnesses)
    expected_solids = baseline["preview"]["solid_count"] + sum(
        count * sum(len(shape.Solids) for shape in references[group].values())
        for group, count in NEW_COUNTS.items()
    )
    assert result["solid_count"] == expected_solids == sum(
        len(obj.Shape.Solids) for obj in document.Objects
    )
    return {"baseline": old_checks, "crossing_exit": new_checks}


def _gui_inspection(document, witnesses, run_dir):
    """Check every layer and capture each added assembly for visual review."""
    for obj in document.Objects:
        assert obj.ViewObject.Visibility
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(obj)
        assert Gui.Selection.getSelection() == [obj]
        obj.ViewObject.Visibility = False
        combined._settle(document)
        assert not obj.ViewObject.Visibility
        obj.ViewObject.Visibility = True
        combined._settle(document)
        assert obj.ViewObject.Visibility
    Gui.Selection.clearSelection()
    view = Gui.getDocument(document.Name).activeView()
    animation = view.isAnimationEnabled()
    images = {}
    try:
        view.setAnimationEnabled(False)
        assert not view.isAnimationEnabled()
        for index, (identity, witness) in enumerate(sorted(witnesses.items())):
            directory = run_dir / "views" / f"position-{index:02d}"
            directory.mkdir(parents=True)
            filenames = previous.previous.whole.helpers._images(
                document, (witness["inspection_frame"],), directory,
            )
            images[identity] = {
                "family": witness["family"],
                "files": [{"path": str(directory / name),
                           "sha256": catalogue._hash(directory / name)}
                          for name in filenames],
                "capture_state": str(directory / "capture-state.json"),
            }
    finally:
        view.setAnimationEnabled(animation)
    assert view.isAnimationEnabled() == animation
    assert len(images) == 24
    manifest = run_dir / "image-manifest.json"
    manifest.write_text(json.dumps(images, indent=2) + "\n", encoding="utf-8")
    print("CROSSING_EXIT_IMAGES_READY", str(manifest), flush=True)
    return images


def _inspection_frame(identity, components, references):
    """Centre the camera on independent transformed reference bounds."""
    points = []
    for name, shape in references.items():
        box, frame = shape.BoundBox, components[name]
        for x in (box.XMin, box.XMax):
            for y in (box.YMin, box.YMax):
                for z in (box.ZMin, box.ZMax):
                    points.append(tuple(
                        frame.origin_mm[axis] + x * frame.x_axis[axis]
                        + y * frame.y_axis[axis] for axis in (0, 1)
                    ) + (frame.origin_mm[2] + z,))
    centre = tuple((min(point[i] for point in points)
                    + max(point[i] for point in points)) / 2
                   for i in range(3))
    return SimpleNamespace(position_id=identity, origin_mm=centre)


def _witnesses(module, source, context, paired, data, references, oracle):
    """Derive source frames without consuming product placement records."""
    binding = json.loads(paired.read_text())["canonical_hosts"]
    host_path = Path(binding["path"])
    assert catalogue._hash(host_path) == binding["sha256"]
    captured = json.loads(host_path.read_text())
    assert captured["fixture_sha256"] == xo.FIXTURE_SHA256
    data["bindings"][str(host_path)] = binding["sha256"]
    config = json.loads(context[0])["configuration"]
    hosts = {}
    for side in ("A", "B"):
        item = config["turnout_" + side.lower() + "_config"]
        obj = source.getObject(item["host_object"])
        host = module.turnout_host_alignment(obj)
        hosts[side] = {
            "object_name": obj.Name,
            "points": [[point.x, point.y] for point in host["points"]],
            "headings": host["headings"], "stations": host["stations"],
            "total": host["total"], "toe_chainage": item["toe_chainage"],
            "orientation": item["orientation"], "handing": item["handing"],
        }
        assert hosts[side] == captured["hosts"][side]
    base_z, = {instance["base_z"] for instance in context[3]["instances"]}
    witnesses = {}
    for position in context[1]["positions"]:
        timber = position["prototype_timber_identifier"]
        name = position["rail_name"]
        if timber in oracle.TIMBERS:
            primary = (
                "straight switch and closure rail" if timber in ("X1-Z", "X2-Y")
                else "turnout-side wing rail" if timber in ("X3-X", "X4-A")
                else "vee point rail"
            )
            if name != primary:
                continue
            decision = oracle.crossing_context(timber)
            group, family = decision["context_id"], decision["family"]
            station = decision["station_mm"]
            local = {part: oracle.native_to_target()
                     for part in references[group]}
            # New models use the same qualified rail-top to mounting-plane
            # normalisation as retained paired models. It cancels here.
            world_z = base_z + 149 / 60
        elif timber in ("R1", "R2") and name in (
                "vee point rail", "vee splice rail"):
            rail = 3 if name == "vee point rail" else 2
            family, station = oracle.exit_family(timber, rail)
            group = "Exit" + family
            pose = previous.oracle.source_rail_pose(
                data["parameters"], station, rail,
            )
            frames = previous.oracle.local_frames(
                family, rail, pose["k_rad"], pose["y_mm"],
            )
            local = {
                part["native_object"]: (
                    frames["fixings"][part["source_fixing_index"] - 1]
                    if part["kind"] == "fixing" else frames["body"]
                ) for part in data["parts_by_family"][family].values()
            }
            decision = dict(pose, family=family, station_mm=station)
            world_z = base_z
        else:
            continue
        side = {"XO-001-A001": "A", "XO-001-B001": "B"}[
            position["parent_turnout_identity"]]
        host = hosts[side]
        common = previous.oracle.expected_world_frame(
            host, toe_chainage_mm=host["toe_chainage"],
            direction=1 if side == "A" else -1, hand=-1,
            station_mm=station, gauge_mm=16.5,
        )
        components = {
            name: central._world_frame(position, matrix, common, world_z)
            for name, matrix in local.items()
        }
        assert tuple(components) == tuple(references[group])
        identity = position["stable_chair_position_identity"]
        assert identity not in witnesses
        witnesses[identity] = {
            "group": group, "family": family, "side": side,
            "components": components,
            "inspection_frame": _inspection_frame(
                identity, components, references[group],
            ),
            "source_decision": decision,
            "expected_component_frames": {
                name: vars(frame) for name, frame in components.items()
            },
        }
    assert Counter(item["group"] for item in witnesses.values()) == NEW_COUNTS
    assert Counter(item["side"] for item in witnesses.values()) == {
        "A": 12, "B": 12,
    }
    return witnesses


def _focused_failures(create, captured, module, path, prepared, registry,
                      source, unchanged):
    """Exercise new preparation paths and the unchanged rollback boundary."""
    from tracktemplate.application import chair_crossing_catalogue

    groups, context_shapes, source_receipt, verify_source = captured["args"][1:]
    failures = {}
    for prerequisite, value in (
            ("paired_contexts_path", None), ("include_central_cc", False),
            ("include_check_ends", False), ("include_single_rail", False)):
        with patch.object(App, "newDocument", side_effect=AssertionError(
                "Missing crossing-exit prerequisite created a document")):
            failures[prerequisite] = catalogue._reject(
                lambda: create(**{prerequisite: value}), ValueError,
            )
        unchanged("early " + prerequisite + " refusal", source)
    original_host = module.turnout_host_alignment
    original_check = adapter._same_presented_shape
    original_read = reader._read
    for group in NEW_COUNTS:
        selected = prepared[group]
        layer_count = 2 + len(selected.components)
        checks = {}

        def changed_bytes(filename):
            content = original_read(filename)
            return (content + b"\n" if str(filename) == selected.model_path
                    else content)

        if group in CROSSING_GROUPS:
            with patch.object(reader, "_read", changed_bytes), patch.object(
                    chair_crossing_catalogue, "_read", changed_bytes
            ), patch.object(App, "newDocument", side_effect=AssertionError(
                    "Changed crossing geometry created a document")):
                checks["early_model_refusal"] = catalogue._reject(
                    create, ValueError,
                )
            unchanged(group + " early model refusal", source)
        incomplete = dict(groups)
        del incomplete[group]
        with patch.object(App, "newDocument", side_effect=AssertionError(
                "Incomplete crossing-exit groups created a document")):
            checks["missing_group_refusal"] = catalogue._reject(
                lambda: adapter.create_private_catalogue_crossover_preview(
                    captured["args"][0], incomplete, context_shapes,
                    source_receipt, verify_source, **captured["kwargs"],
                ), ValueError,
            )
        unchanged(group + " early group refusal", source)

        def focused(verify=verify_source):
            _choice, specs, prepare = adapter._prepare_catalogue_family(
                path, groups[group], context_shapes, source_receipt,
                family=selected.label, placement_type=type(groups[group][0]),
                model_sha256=selected.model_sha256,
                source_names=tuple(item.name for item in selected.components),
                run=selected.run, source_context=selected.context,
                prepared_selection=selected,
            )
            return adapter._materialise_preview(
                selected.label, source_receipt, specs, prepare, verify,
            )

        def late_bytes(filename):
            if App.ActiveDocument not in registry.values():
                assert len(App.ActiveDocument.Objects) == layer_count
                return changed_bytes(filename)
            return original_read(filename)

        if group in CROSSING_GROUPS:
            with patch.object(reader, "_read", late_bytes), patch.object(
                    chair_crossing_catalogue, "_read", late_bytes):
                checks["late_model_refusal"] = catalogue._reject(
                    focused, ValueError,
                )
            unchanged(group + " late model rollback", source)

        def stale_source():
            assert App.ActiveDocument not in registry.values()
            assert len(App.ActiveDocument.Objects) == layer_count

            def changed_host(obj):
                host = dict(original_host(obj))
                headings = list(host["headings"])
                headings[0] += 1e-8
                return dict(host, headings=headings)

            with patch.object(module, "turnout_host_alignment", changed_host):
                verify_source()

        checks["late_host_refusal"] = previous.previous.paired.helpers._reject(
            lambda: focused(stale_source), "changed",
        )
        unchanged(group + " late host rollback", source)

        def reject_stored(actual, expected):
            if App.ActiveDocument not in registry.values():
                assert len(App.ActiveDocument.Objects) == layer_count
                return False
            return original_check(actual, expected)

        with patch.object(adapter, "_same_presented_shape", reject_stored):
            checks["stored_shape_refusal"] = catalogue._reject(focused, ValueError)
        unchanged(group + " stored shape rollback", source)
        failures[group] = checks
        print("CROSSING_EXIT_FOCUSED_ROLLBACK_PASS", group, flush=True)
    return failures


def validate():
    """Build one complete preview in an isolated qualified host."""
    import crossing_exit_source_oracle as oracle
    from tracktemplate.application import chair_crossing_catalogue

    assert not App.listDocuments(), "Use an empty isolated FreeCAD host"
    path = Path(os.environ["TRACKTEMPLATE_CHAIR_CATALOGUE"]).resolve()
    paired = Path(os.environ["TRACKTEMPLATE_PAIRED_CATALOGUE"]).resolve()
    crossing = Path(os.environ["TRACKTEMPLATE_CROSSING_CATALOGUE"]).resolve()
    fixture = Path(os.environ["TRACKTEMPLATE_CROSSOVER_REFERENCE_FIXTURE"])
    source_directory = Path(os.environ["TRACKTEMPLATE_TEMPLOT_SOURCE"])
    source_context = Path(os.environ["TRACKTEMPLATE_SINGLE_RAIL_SOURCE_CONTEXT"])
    baseline_path = Path(os.environ["TRACKTEMPLATE_SINGLE_RAIL_BASELINE_RECEIPT"])
    run_dir = Path(os.environ["TRACKTEMPLATE_CROSSING_EXIT_RUN_DIR"]).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    receipt = {
        "status": "RUNNING", "gui": bool(App.GuiUp),
        "physical_fit": "NOT_PROVED", "baseline_sha256": BASELINE_SHA256,
        "source_agreement_scope": "24 new crossing and exit assemblies",
        "baseline_scope": "237 accepted assemblies preserved unchanged",
        "global_templot_equivalence": "NOT_CLAIMED",
    }
    initial = catalogue.helpers._document_state()
    try:
        assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
        baseline = _read_baseline(baseline_path)
        data = previous.oracle.load(source_directory, path.parent, source_context)
        for filename in (Path(oracle.__file__), crossing, baseline_path):
            data["bindings"][str(filename)] = catalogue._hash(filename)
        references, prepared = _references(
            path, paired, crossing, run_dir, chair_crossing_catalogue,
        )
        for group in NEW_COUNTS:
            for binding in prepared[group].bindings:
                previous_digest = data["bindings"].setdefault(
                    binding.path, binding.sha256,
                )
                assert previous_digest == binding.sha256
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
        foreign = App.newDocument("CrossingExitUnrelatedWitness")
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
        witnesses = _witnesses(
            module, source, context, paired, data, references, oracle,
        )
        receipt["source_bindings"] = data["bindings"]
        receipt["source_references"] = oracle.REFERENCES
        receipt["source_witnesses"] = {
            identity: {key: value for key, value in witness.items()
                       if key not in ("components", "inspection_frame")}
            for identity, witness in witnesses.items()
        }
        registry = dict(App.listDocuments())
        unchanged, selection, preselection, state_hash, negatives = (
            previous.guard._guard(module, source, foreign, gui, 355)
        )
        receipt["source_state_sha256"] = state_hash
        receipt["source_guard_negative_witnesses"] = negatives
        captured = {}
        native_create = adapter.create_private_catalogue_crossover_preview

        def capture_factory(*args, **kwargs):
            captured.update(args=args, kwargs=kwargs)
            return native_create(*args, **kwargs)

        def create(**options):
            kwargs = dict(
                paired_contexts_path=paired, include_central_cc=True,
                include_check_ends=True, include_single_rail=True,
                crossing_contexts_path=crossing,
            )
            kwargs.update(options)
            return command(source, "XO-001", path, **kwargs)

        started = time.perf_counter()
        with patch.object(session, "_private_catalogue_crossover_preview_factory",
                          side_effect=capture_factory), patch.object(
                App, "openDocument", side_effect=AssertionError(
                    "Product restored an external source document")):
            result = create()
        receipt["elapsed_creation_seconds"] = time.perf_counter() - started
        preview = App.getDocument(result["document_name"])
        receipt["preview"] = result
        _coverage(result["source_receipt"], context, baseline, witnesses)
        receipt["finite_rail_exclusion_proofs"] = _finite_rail_exclusions(
            result["source_receipt"], context,
        )
        receipt["comparisons"] = _assert_preview(
            result, preview, references, prepared, baseline, witnesses,
        )
        unchanged("created", preview)
        print("CROSSING_EXIT_COMPLETE_PREVIEW_PASS", flush=True)
        before = tuple(obj.Shape for obj in preview.Objects)
        assert preview.UndoCount == 1
        preview.undo()
        assert not preview.Objects
        preview.redo()
        assert len(preview.Objects) == len(before)
        assert all(p.catalogue_adapter._same_presented_shape(obj.Shape, shape)
                   for obj, shape in zip(preview.Objects, before))
        receipt["redo_new_comparisons"] = _assert_new(
            result, preview, references, prepared, witnesses,
        )
        unchanged("Undo/Redo", preview)
        receipt["undo_redo"] = "PASS"
        if gui:
            receipt["images"] = _gui_inspection(preview, witnesses, run_dir)
            lifecycle._restore_selection(App, gui, selection)
            lifecycle._restore_preselection(App, gui, preselection)
            unchanged("GUI inspection", preview)
            receipt["visibility_selection"] = "PASS"
            receipt["camera_animation_restored"] = True
        previous._close_preview(
            preview, source, gui, selection, preselection, unchanged,
        )
        receipt["focused_failures"] = _focused_failures(
            create, captured, module, path, prepared, registry, source, unchanged,
        )
        chair_crossing_catalogue.verify_crossing_catalogue(tuple(
            prepared[group] for group in CROSSING_GROUPS
        ))
        for family in (*previous.previous.whole.COUNTS, "CC", "CCL", "CCR", "L1"):
            reader.verify_catalogue_sources(prepared[family])
        previous.previous.paired.pairs.verify_paired_catalogue(tuple(
            prepared[group] for group in previous.previous.paired.PAIR_IDS
        ))
        for filename, digest in data["bindings"].items():
            assert catalogue._hash(Path(filename)) == digest
        assert catalogue._hash(source.FileName) == xo.FIXTURE_SHA256
        assert catalogue._hash(fixture) == xo.FIXTURE_SHA256
        assert xo._context(module, source) == context
        unchanged("complete proof", source)
        count = sum(NEW_COUNTS[group] * len(references[group])
                    for group in NEW_COUNTS)
        receipt.update(
            fixture_sha256=xo.FIXTURE_SHA256, source_bindings_unchanged=True,
            baseline_component_comparisons=4889, new_component_comparisons=count,
            redo_new_component_comparisons=count, transaction_rollback="PASS",
            rollback_scope="new crossing-exit groups and shared lifecycle",
            complete_baseline_failure_suite="reused accepted PR 214 receipt",
            legacy_exclusions_unchanged_except_qualified_additions=True,
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
