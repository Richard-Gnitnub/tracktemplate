"""Check the finite private TO-001 central CC route without FreeCAD.

Generated records exercise source accounting and proper common frames.
Selected assignment metadata follows the retained B15 TO-001 context;
Templot-informed metadata is GPL-3.0-or-later (see NOTICE.md and
reference/PROVENANCE.md). All host geometry and other positions are doubles.
The existing source capture and final verifier remain real. Host and
catalogue doubles do not prove railway-source geometry, native solids,
fit, GUI state, rights or production clearance.
"""

import ast
import copy
from dataclasses import FrozenInstanceError
import importlib
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

from tracktemplate.compatibility import transition_workflow  # noqa: E402
from tracktemplate.domain.chair_placement import (  # noqa: E402
    PairedChairPlacement,
)
from validate_phase9b_catalogue_p_placement import (  # noqa: E402
    source_case as p_source_case,
)
from validate_phase9b_s1_s1j_reference_preview import (  # noqa: E402
    ShapeDouble,
)

ANALYSIS_SIGNATURE = (
    "dad7acd2955b47ec82ad76e3827443eecce54c072c647e5e7e9ba865303b7379"
)
CC_MODEL_SHA256 = (
    "b28b574a517e677c86fc35e26cab9a966e41504cb2242968db45e7c07ac81637"
)
CC_CONTEXT_SHA256 = (
    "5291c5d1b350373d93d686feb3bad35c5e2dfb62347bfc5d9906bf2c81077b6d"
)
STATIONS = (267.23290043721454, 277.23290043721454, 287.23290043721454)
TIMBERS = ("X2-Y", "X3-X", "X4-A")
RAIL_NAMES = ("main-side stock rail", "main-side check rail")
FIXING_NAMES = ("SourceFixing",) + tuple(
    f"SourceFixing{index:03d}" for index in range(1, 16)
)
SENTINEL = "Phase 9B TO-001 central CC standalone validation passed"


def position_id(timber, *, companion=False):
    rail_name = RAIL_NAMES[int(companion)].replace(" ", "-")
    return f"TO-001:chair:to-001-timber-{timber.lower()}:{rail_name}"


def catalogue_selection():
    """Stand in for the reader, with all 33 components still accounted."""
    names = tuple(f"invented-part-{index:02d}" for index in range(17))
    return SimpleNamespace(
        label="CC", run="context-native-02",
        context={"context_sha256": CC_CONTEXT_SHA256},
        model_sha256=CC_MODEL_SHA256,
        components=tuple(SimpleNamespace(name=name)
                         for name in names + FIXING_NAMES),
    )


def source_case(*, heading=0.37):
    """Extend the P fixture to 168 positions and an invented host.

    Nominal source metadata is explicit test input, not extracted proof.
    The 59 S1 and 14 P records only witness preservation of other routes.
    """
    module, document, app, context, plan, objects = p_source_case()
    module.TURNOUT_HAND_LEFT = "Left-hand"
    module.TURNOUT_ORIENTATION_FACING = "Facing in host travel direction"
    module.CHAIR_ASSIGNMENT_DEFERRED_SPECIAL = (
        "deferred to special-chair assignment"
    )
    module.CHAIR_FAMILY_CHECK = "check-rail chair"
    module.CHAIR_FAMILY_CROSSING = "common-crossing chair"
    module.CHAIR_FAMILY_NOSE = "crossing-nose support"
    configuration, analysis, _settings, rails, timbers = context[1:]
    configuration.update(
        handing=module.TURNOUT_HAND_LEFT,
        orientation=module.TURNOUT_ORIENTATION_FACING,
        toe_chainage=746.298, template_width=32.0,
        rail_geometry_revision=2, timber_geometry_revision=2,
        host_object="Host", chair_analysis_signature=ANALYSIS_SIGNATURE,
    )
    analysis["geometry_signature"] = ANALYSIS_SIGNATURE
    tangent = (math.cos(heading), math.sin(heading))
    normal = (-tangent[1], tangent[0])

    def interpolate(_data, station):
        return SimpleNamespace(
            x=13.0 + station * tangent[0],
            y=-7.0 + station * tangent[1],
        ), heading

    host = SimpleNamespace(Name="Host", Shape=ShapeDouble("host"))
    objects[host.Name] = host
    data = {
        "points": [SimpleNamespace(x=13.0, y=-7.0),
                   interpolate(None, 2000.0)[0]],
        "headings": [heading, heading], "stations": [0.0, 2000.0],
        "total": 2000.0,
    }
    module.turnout_host_alignment = lambda _obj: data
    module.interpolate_alignment_station = interpolate
    module._turnout_orientation_sign = lambda value: (
        1.0 if value == module.TURNOUT_ORIENTATION_FACING else -1.0
    )
    module.rea_c10_dimensions = lambda *_args: {"a_timber_x": STATIONS[2]}
    layout = [
        {"identifier": name, "x": station, "near_y": near,
         "far_y": far, "length_prototype_inches": length}
        for name, station, near, far, length in zip(
            TIMBERS, STATIONS,
            (-16.516718458769496, -16.016718458769496, -16.516718458769496),
            (31.483281541230504, 31.983281541230504, 33.483281541230504),
            (144.0, 144.0, 150.0),
        )
    ]
    module.rea_c10_timber_layout = lambda *_args: copy.deepcopy(layout)
    selected_rails = [rails[0], {
        "stable_identity": "TO-001:rail:main-side-check-rail",
        "name": RAIL_NAMES[1], "rail_role": "check rail",
        "parent_turnout_identity": "TO-001",
        "parent_crossover_identity": "",
    }]
    rails.append(selected_rails[1])
    for rail in selected_rails:
        rail["source_configuration"] = {
            "gauge_face": rail["name"] + " gauge face",
            "outer_face": rail["name"] + " outer face",
            "gauge_orientation_source": "mapped named turnout rail faces",
            "rail_geometry_revision": 2,
        }
        rail["turnout_side"] = ""
    for index, (name, local_station) in enumerate(zip(TIMBERS, STATIONS)):
        station = configuration["toe_chainage"] + local_station
        point, _heading = interpolate(data, station)
        nominal = layout[index]
        centre_y = (nominal["near_y"] + nominal["far_y"]) / 2
        timber = {
            "stable_identity": f"TO-001:timber:{name}",
            "identifier": name, "prototype_reference": name,
            "parent_turnout_identity": "TO-001",
            "crossover_identity": "", "turnout_side": "",
            "section": "crossing wing front" if index < 2 else "crossing vee",
            "host_chainage": station,
            "local_rail_heading_radians": heading,
            "centre": [point.x + centre_y * normal[0],
                       point.y + centre_y * normal[1]],
            "source_configuration": {
                "local_x": local_station,
                "local_near_y": nominal["near_y"],
                "local_far_y": nominal["far_y"],
                "length_prototype_inches": nominal["length_prototype_inches"],
                "crossing_suffix": name[-1], "turnout_geometry_revision": 2,
                "longitudinal_reference_axis": list(tangent),
                "source_note": (
                    "REA wing-front crossing-chair spacing: 30 inches"
                    if index < 2 else
                    "REA vee-rail crossing-chair spacing: 30 inches"
                ),
            },
        }
        timbers.append(timber)
        for companion, rail in enumerate(selected_rails):
            code, label = ((15, "CC") if companion else
                           ((22, "XN"), (23, "XA"), (24, "AA"))[index])
            family = (module.CHAIR_FAMILY_CHECK if companion else
                      module.CHAIR_FAMILY_NOSE if index == 2 else
                      module.CHAIR_FAMILY_CROSSING)
            record = {
                "stable_chair_position_identity": position_id(
                    name, companion=bool(companion),
                ),
                "rail_identity": rail["stable_identity"],
                "timber_identity": timber["stable_identity"],
                "rail_name": rail["name"], "rail_role": rail["rail_role"],
                "parent_turnout_identity": "TO-001",
                "parent_crossover_identity": "",
                "prototype_timber_identifier": name, "timber_identifier": name,
                "chair_code": code, "chair_code_label": label,
                "chair_family": family,
                "chair_subtype": (
                    "REA check-chair subtype awaiting detailed "
                    "special-chair assignment" if companion else
                    "REA common-crossing subtype awaiting detailed "
                    "special-chair assignment"
                ),
                "assignment_status": module.CHAIR_ASSIGNMENT_DEFERRED_SPECIAL,
                "assignment_complete_in_current_stage": False,
                "special_assignment_deferred": True,
                "deliberate_omission": False, "stale_signature_state": False,
                "validation_status": "Advisory", "handedness": "Left-hand",
                "key_direction_sign": 0,
                "key_orientation": (
                    "requires confirmation from the final special-chair "
                    "subtype and keying arrangement"
                ),
                "key_orientation_classification": (
                    "dimension requiring later confirmation"
                ),
                "source_or_assumed_classification": (
                    "source-derived prototype requirement" if companion else
                    "temporary visual approximation"
                ),
                "source_configuration": {
                    "rail": copy.deepcopy(rail["source_configuration"]),
                    "timber": copy.deepcopy(timber["source_configuration"]),
                },
                "centre_point": [point.x, point.y],
                "local_rail_tangent": list(tangent),
            }
            analysis["positions"].append(record)
            plan["analytical_only"].append({
                "chair_position_identity": record[
                    "stable_chair_position_identity"
                ],
                "rail_identity": rail["stable_identity"],
                "timber_identity": timber["stable_identity"],
                "chair_label": label, "chair_family": family,
                "reason": "special chair assignment remains analytical",
                "unresolved_special": True, "deliberate_omission": False,
            })
    original = analysis["positions"][14]
    for index in range(58):
        record = copy.deepcopy(original)
        identity = f"invented-S1-{index:03d}"
        record["stable_chair_position_identity"] = identity
        analysis["positions"].append(record)
        instance = copy.deepcopy(plan["instances"][0])
        instance["chair_position_identity"] = identity
        plan["instances"].append(instance)
    for index in range(87):
        record = copy.deepcopy(analysis["positions"][15])
        identity = f"invented-unselected-{index:03d}"
        record["stable_chair_position_identity"] = identity
        analysis["positions"].append(record)
        exclusion = copy.deepcopy(plan["analytical_only"][14])
        exclusion["chair_position_identity"] = identity
        plan["analytical_only"].append(exclusion)
    return SimpleNamespace(
        module=module, document=document, app=app, context=context, plan=plan,
        objects=objects, host_data=data, layout=layout, heading=heading,
    )


def selected_record(source, timber="X2-Y", *, companion=False):
    identity = position_id(timber, companion=companion)
    return next(item for item in source.context[2]["positions"]
                if item["stable_chair_position_identity"] == identity)


def selected_timber(source, name="X2-Y"):
    return next(item for item in source.context[5]
                if item["identifier"] == name)


def preview(source, factory=None, *, selection=None):
    """Keep source capture, source checks and placement arithmetic real."""
    binding = placement_binding()
    if factory is None:
        factory = lambda *args: args
    with (
        patch.dict(sys.modules, {"FreeCAD": source.app}),
        patch.object(binding, "prepare_catalogue_chair",
                     return_value=selection or catalogue_selection()),
        patch.object(binding, "verify_catalogue_sources"),
    ):
        return binding.preview_private_catalogue_turnout_cc_chairs(
            source.module, source.document, "TO-001", "private-catalogue.json",
            factory,
        )

def placement_binding():
    return importlib.import_module(
        "tracktemplate.compatibility.chair_turnout_check_placement",
    )


class TurnoutCentralCheckTests(unittest.TestCase):
    def test_public_preview_entry_exists(self):
        self.assertTrue(callable(
            placement_binding().preview_private_catalogue_turnout_cc_chairs,
        ))

    def test_three_proper_frames_and_six_positions_are_deterministic(self):
        for heading in (0.0, 0.37, math.pi / 2):
            with self.subTest(heading=heading):
                source = source_case(heading=heading)
                _path, placements, _shapes, receipt, verify = preview(source)
                self.assertEqual(len(placements), 3)
                self.assertEqual([item.position_id for item in placements],
                                 sorted(position_id(name) for name in TIMBERS))
                tangent = (math.cos(heading), math.sin(heading))
                normal = (-tangent[1], tangent[0])
                for placement, local_station in zip(placements, STATIONS):
                    self.assertIs(type(placement), PairedChairPlacement)
                    station = 746.298 + local_station
                    expected = (13.0 + station * tangent[0] - 8.70 * normal[0],
                                -7.0 + station * tangent[1] - 8.70 * normal[1],
                                1.7500000001)
                    for actual, value in zip(placement.origin_mm, expected):
                        self.assertAlmostEqual(actual, value, places=11)
                    self.assertEqual(placement.x_axis,
                                     (-tangent[0], -tangent[1]))
                    self.assertEqual(placement.y_axis,
                                     (-normal[0], -normal[1]))
                    self.assertAlmostEqual(
                        placement.x_axis[0] * placement.y_axis[1]
                        - placement.x_axis[1] * placement.y_axis[0], 1.0,
                    )
                    self.assertEqual(placement.transform_point((0, 0, 2))[2],
                                     3.7500000001)
                    with self.assertRaises(FrozenInstanceError):
                        placement.position_id = "changed"
                self.assertEqual(receipt["selected_cc_count"], 3)
                self.assertEqual(
                    receipt["represented_source_position_count"], 6,
                )
                shared = {item["position_id"]: item["assembly_position_id"]
                          for item in receipt["shared_supports"]}
                self.assertEqual(len(receipt["shared_supports"]), 3)
                self.assertEqual(shared, {
                    position_id(name, companion=True): position_id(name)
                    for name in TIMBERS
                })
                source.context[2]["positions"].reverse()
                source.plan["analytical_only"].reverse()
                self.assertEqual(preview(source)[1], placements)
                # Use a fresh snapshot: deliberate order changes invalidate
                # the preceding source signature, even with identical frames.
                with self.assertRaises(ValueError):
                    with patch.dict(sys.modules, {"FreeCAD": source.app}):
                        verify()

    def test_full_partition_copied_context_and_source_are_preserved(self):
        source = source_case()
        before = copy.deepcopy((source.context, source.plan))

        def factory(path, placements, shapes, receipt, verify):
            self.assertEqual(path, "private-catalogue.json")
            self.assertEqual(len(shapes), 2)
            for shape, role in zip(shapes, ("rails", "timbers")):
                original = source.objects[role].Shape
                self.assertIsNot(shape, original)
                self.assertTrue(shape.isSame(original))
            verify()
            return receipt

        receipt = preview(source, factory)
        self.assertEqual(receipt["analysis_position_count"], 168)
        self.assertEqual(receipt["source_base_z_mm"], 1.7500000001)
        self.assertEqual(len(receipt["selected_positions"]), 3)
        self.assertEqual(len(receipt["remaining_positions"]), 162)
        self.assertEqual(receipt["original_analytical_exclusions"],
                         before[1]["analytical_only"])
        self.assertEqual((source.context, source.plan), before)
        self.assertEqual(len(source.plan["instances"]), 59)
        self.assertEqual(sum(p["chair_code"] == 2
                             for p in source.context[2]["positions"]), 14)

    def assert_refused(self, source, *, selection=None):
        factory = Mock(side_effect=AssertionError("preview must not start"))
        with self.assertRaises(ValueError):
            preview(source, factory, selection=selection)
        factory.assert_not_called()

    def test_unqualified_configuration_or_analysis_is_rejected(self):
        for field, value in (
            ("handing", "Right-hand"), ("orientation", "Trailing"),
            ("toe_chainage", 746.299), ("template_width", 33),
            ("rail_geometry_revision", 1), ("timber_geometry_revision", 1),
            ("track_gauge", 18.83), ("flangeway", 1.1),
            ("chair_analysis_signature", "different"),
        ):
            with self.subTest(field=field):
                source = source_case()
                source.context[1][field] = value
                self.assert_refused(source)
        source = source_case()
        source.context[2]["geometry_signature"] = "different"
        source.context[1]["chair_analysis_signature"] = "different"
        self.assert_refused(source)

    def test_profile_and_mounting_datum_are_not_substituted(self):
        for change in ("profile", "embed", "scale", "datum", "nonfinite"):
            with self.subTest(change=change):
                source = source_case()
                if change == "profile":
                    source.plan["rail_profile"]["rail_depth_mm"] += 1e-9
                elif change == "embed":
                    source.context[3]["future_chair_embed_depth"] += 1e-9
                elif change == "scale":
                    source.module.TURNOUT_DEFAULT_SCALE = 87.0
                else:
                    source.plan["instances"][0]["base_z"] = (
                        math.nan if change == "nonfinite" else 2.0
                    )
                self.assert_refused(source)

    def test_owner_assignment_and_label_substitutions_are_rejected(self):
        for field, value in (
            ("parent_turnout_identity", "TO-002"),
            ("parent_crossover_identity", "XO-001"),
            ("rail_name", "turnout-side stock rail"),
            ("chair_code", 22.0), ("chair_code_label", "CC"),
            ("special_assignment_deferred", False),
            ("assignment_complete_in_current_stage", True),
            ("assignment_status", "confirmed"), ("deliberate_omission", True),
            ("stale_signature_state", True),
            ("validation_status", "validated"),
            ("handedness", "Right-hand"), ("key_direction_sign", 1),
        ):
            with self.subTest(field=field):
                source = source_case()
                selected_record(source)[field] = value
                self.assert_refused(source)

    def test_missing_duplicate_or_wrong_companion_is_rejected(self):
        for change in ("missing", "duplicate", "owner", "code", "rail"):
            with self.subTest(change=change):
                source = source_case()
                record = selected_record(source, companion=True)
                positions = source.context[2]["positions"]
                if change == "missing":
                    positions.remove(record)
                elif change == "duplicate":
                    duplicate = copy.deepcopy(record)
                    duplicate["stable_chair_position_identity"] += "-duplicate"
                    positions.append(duplicate)
                elif change == "owner":
                    record["parent_turnout_identity"] = "TO-002"
                elif change == "code":
                    record["chair_code"] = 16
                else:
                    record["rail_identity"] = "unknown"
                self.assert_refused(source)

    def test_nominal_station_and_world_timber_must_agree(self):
        for change in ("station", "layout", "chainage", "heading", "centre"):
            with self.subTest(change=change):
                source = source_case()
                timber = selected_timber(source)
                if change == "station":
                    timber["source_configuration"]["local_x"] += 1e-6
                    position = selected_record(source)
                    position["source_configuration"]["timber"] = copy.deepcopy(
                        timber["source_configuration"],
                    )
                    selected_record(source, companion=True)[
                        "source_configuration"
                    ]["timber"] = copy.deepcopy(timber["source_configuration"])
                elif change == "layout":
                    source.layout[0]["x"] += 1e-6
                elif change == "chainage":
                    timber["host_chainage"] += 1e-6
                elif change == "heading":
                    timber["local_rail_heading_radians"] += 1e-6
                else:
                    timber["centre"][0] += 1e-6
                self.assert_refused(source)

    def test_nonfinite_or_unavailable_host_cannot_create_preview(self):
        for change in ("total", "outside", "heading", "point", "missing"):
            with self.subTest(change=change):
                source = source_case()
                if change in ("total", "outside"):
                    source.host_data["total"] = (
                        math.inf if change == "total" else 100.0
                    )
                elif change in ("heading", "point"):
                    source.module.interpolate_alignment_station = lambda *_: (
                        SimpleNamespace(x=math.nan if change == "point" else 0,
                                        y=0),
                        math.nan if change == "heading" else 0,
                    )
                else:
                    source.objects.pop("Host")
                self.assert_refused(source)

    def test_source_partition_and_exclusion_reasons_remain_binding(self):
        for change in ("count", "missing", "duplicate", "reason", "overlap"):
            with self.subTest(change=change):
                source = source_case()
                excluded = source.plan["analytical_only"]
                selected = next(item for item in excluded
                                if item["chair_position_identity"]
                                == position_id("X2-Y"))
                if change == "count":
                    source.context[2]["positions"].pop()
                    excluded.pop()
                elif change == "missing":
                    excluded.remove(selected)
                elif change == "duplicate":
                    excluded.append(copy.deepcopy(selected))
                elif change == "reason":
                    selected["reason"] = "unknown geometry"
                else:
                    source.plan["instances"].append(
                        dict(selected, base_z=1.75),
                    )
                self.assert_refused(source)

    def test_wrong_catalogue_never_reaches_native_factory(self):
        for field, value in (("label", "CCL"), ("run", "other"),
                             ("model_sha256", "0" * 64),
                             ("components", ())):
            with self.subTest(field=field):
                selection = catalogue_selection()
                setattr(selection, field, value)
                self.assert_refused(source_case(), selection=selection)

    def test_final_verifier_refuses_source_host_and_catalogue_changes(self):
        for change in ("analysis", "shape", "object", "host", "host-object",
                       "catalogue"):
            with self.subTest(change=change):
                source = source_case()

                def factory(_path, _placements, _shapes, _receipt, verify):
                    if change == "analysis":
                        selected_record(source)["centre_point"][0] += 1e-9
                    elif change == "shape":
                        source.objects["rails"].Shape = ShapeDouble("changed")
                    elif change in ("object", "host-object"):
                        key = "Host" if change == "host-object" else "rails"
                        old = source.objects[key]
                        source.objects[key] = SimpleNamespace(
                            Name=old.Name, Shape=old.Shape,
                        )
                    elif change == "host":
                        source.host_data["points"][0].x += 1e-9
                    else:
                        with patch.object(
                            placement_binding(), "verify_catalogue_sources",
                            side_effect=ValueError("changed catalogue"),
                        ):
                            verify()
                        return
                    verify()

                with self.assertRaises(ValueError):
                    preview(source, factory)

    def test_session_routes_exact_inputs_after_routing_check(self):
        calls = []
        session = SimpleNamespace(
            module=object(), _private_catalogue_cc_preview_factory=object(),
            routing_record=lambda: calls.append("route"),
        )
        document = object()

        def operation(*args):
            self.assertEqual(calls, ["route"])
            self.assertEqual(args, (
                session.module, document, "TO-001", "catalogue.json",
                session._private_catalogue_cc_preview_factory,
            ))
            return "receipt"

        with patch.object(placement_binding(),
                          "preview_private_catalogue_turnout_cc_chairs",
                          operation):
            result = (
                transition_workflow.ModularCoreLayoutWorkflowSession
                .preview_private_catalogue_turnout_cc_chairs(
                    session, document, "TO-001", "catalogue.json",
                )
            )
        self.assertEqual(result, "receipt")

    def test_native_factory_uses_common_frame_helper_and_is_injected(self):
        path = (ROOT / "tracktemplate/adapters/freecad"
                / "chair_catalogue_placement_preview.py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        function = "create_private_catalogue_cc_preview"
        nodes = [node for node in tree.body if (
            isinstance(node, ast.FunctionDef)
            and node.name in (function, "_require")
        ) or (
            isinstance(node, ast.Assign)
            and all(isinstance(target, ast.Name) and target.id.isupper()
                    for target in node.targets)
        )]
        selection = catalogue_selection()
        reader = Mock(return_value=selection)
        helper = Mock(return_value="native-boundary")
        namespace = {
            "prepare_catalogue_chair": reader,
            "_create_private_catalogue_preview": helper,
            "PairedChairPlacement": PairedChairPlacement,
        }
        code = compile(
            ast.Module(body=nodes, type_ignores=[]), str(path), "exec",
        )
        exec(code, namespace)
        args = ("catalogue.json", object(), object(), {"source": "kept"},
                Mock())
        self.assertEqual(namespace[function](*args), "native-boundary")
        self.assertEqual(helper.call_args.args, args)
        specification = helper.call_args.kwargs
        self.assertEqual(specification["family"], "CC")
        self.assertIs(specification["placement_type"], PairedChairPlacement)
        self.assertEqual(specification["model_sha256"], CC_MODEL_SHA256)
        self.assertEqual(specification["source_names"],
                         tuple(item.name for item in selection.components))
        self.assertEqual(specification["run"], "context-native-02")
        self.assertEqual(specification["source_context"], selection.context)
        macro = ast.parse((ROOT / "TrackTemplate.FCMacro").read_text())
        keywords = [keyword for node in ast.walk(macro)
                    if isinstance(node, ast.Call) for keyword in node.keywords
                    if keyword.arg == "private_catalogue_cc_preview_factory"]
        self.assertEqual(len(keywords), 1)
        self.assertIsInstance(keywords[0].value, ast.Attribute)
        self.assertEqual(keywords[0].value.attr, function)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TurnoutCentralCheckTests,
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print(SENTINEL)
