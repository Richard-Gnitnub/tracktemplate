#!/usr/bin/env python3
"""Fast contract checks for the development-only FreeCAD bridge recipe."""

import json
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.freecad_bridge import b14_recipe  # noqa: E402


class FakeHost:
    def __init__(self, name, type_id="Part::Feature", **properties):
        self.Name = name
        self.TypeId = type_id
        self.properties = properties


def read_string(host, name, default=""):
    return host.properties.get(name, default)


def read_integer(host, name, default=0):
    return host.properties.get(name, default)


def centreline(name, set_id, track_number, track_name):
    return FakeHost(
        name,
        TemplateSetID=set_id,
        RouteID="",
        TrackNumber=track_number,
        TrackName=track_name,
        GeneratedRole="Centreline",
        ExportSubtype="TrackCentreline",
    )


def expect_value_error(action, text):
    try:
        action()
    except ValueError as error:
        assert text in str(error), str(error)
        return
    raise AssertionError("Expected ValueError containing {!r}".format(text))


class FakeDocument:
    def __init__(self, objects):
        self.Objects = list(objects)


class FakeModule:
    MACRO_VERSION_NUMBER = "10.2A8A7B14"
    TURNOUT_ID_PROPERTY = "TurnoutID"
    CROSSOVER_ID_PROPERTY = "CrossoverID"

    @staticmethod
    def object_string_property(obj, name, default=""):
        return obj.properties.get(name, default)

    @staticmethod
    def _integer_object_property(obj, name, default=0):
        return obj.properties.get(name, default)

    @staticmethod
    def turnout_host_objects(document):
        return [
            obj for obj in document.Objects
            if obj.properties.get("GeneratedRole") == "Centreline"
        ]

    @staticmethod
    def turnout_host_alignment(host):
        return {"total": host.properties["TotalLength"]}

    @staticmethod
    def settings_for_template_set(document, set_id):
        matches = [
            obj for obj in document.Objects
            if obj.properties.get("GeneratedRole") == "Settings"
            and obj.properties.get("TemplateSetID") == set_id
        ]
        return matches[0] if len(matches) == 1 else None

    @staticmethod
    def quantity_value(obj, name, default):
        return obj.properties.get(name, default)


def generated_object(name, role, type_id="Part::Feature", **properties):
    payload = {"GeneratedRole": role}
    payload.update(properties)
    return FakeHost(name, type_id=type_id, **payload)


def base_document():
    track_configs = [{
        "name": "Track 2",
        "side": "Outside",
        "alignment_mode": "Euler - match spacings",
        "start_spacing": 50.0,
        "curve_spacing": 55.0,
        "finish_spacing": 50.0,
        "entry_transition_length": 559.4102547270278,
        "exit_transition_length": 559.4102547270278,
        "width": 32.0,
        "create_template": True,
        "show_centreline": True,
    }]
    return FakeDocument([
        generated_object("Generated", "Group", "App::DocumentObjectGroup"),
        generated_object(
            "ProductionSources",
            "ProductionSourceGroup",
            "App::DocumentObjectGroup",
        ),
        generated_object(
            "Main",
            "Centreline",
            TemplateSetID="SET-001",
            TrackNumber=1,
            TrackName="Main Track",
            ExportSubtype="TrackCentreline",
            TotalLength=1542.475839,
        ),
        generated_object(
            "Track2",
            "Centreline",
            TemplateSetID="SET-001",
            TrackNumber=2,
            TrackName="Track 2",
            ExportSubtype="TrackCentreline",
            TotalLength=1627.287516,
        ),
        generated_object("Source", "ProductionSource"),
        generated_object(
            "Settings",
            "Settings",
            TemplateSetID="SET-001",
            TransitionLength=600.0,
            CurveRadius=600.0,
            TotalTurnAngle=90.0,
            MainTemplateWidth=32.0,
            TrackConfigurationJSON=json.dumps(track_configs, sort_keys=True),
        ),
        generated_object("Template", "Template"),
        generated_object(
            "Schedule",
            "ProductionSchedule",
            "Spreadsheet::Sheet",
        ),
        generated_object(
            "MaterialReport",
            "MaterialLengthReport",
            "Spreadsheet::Sheet",
        ),
    ])


def validate():
    main = centreline("InternalMain", "SET-001", 1, "Main Track")
    track_2 = centreline("InternalTrack2", "SET-001", 2, "Track 2")
    unrelated = centreline("OtherSet", "SET-009", 1, "Main Track")

    selection = b14_recipe.select_crossover_hosts(
        [track_2, unrelated, main],
        read_string,
        read_integer,
    )
    assert selection["a"] == 2
    assert selection["b"] == 0
    assert selection["host_a_identity"]["object_name"] == "InternalMain"
    assert selection["host_b_identity"]["object_name"] == "InternalTrack2"

    expect_value_error(
        lambda: b14_recipe.select_crossover_hosts(
            [main, centreline("DuplicateMain", "SET-001", 1, "Main Track"), track_2],
            read_string,
            read_integer,
        ),
        "exactly one Host A",
    )
    expect_value_error(
        lambda: b14_recipe.select_crossover_hosts(
            [main],
            read_string,
            read_integer,
        ),
        "exactly one Host B",
    )

    assert b14_recipe.DEFAULT_CHAINAGE_MM == 746.298
    assert b14_recipe.DEFAULT_STAGES == (
        "geometry", "timber", "chairs", "support", "layout", "integration", "solids"
    )
    assert b14_recipe.EXPECTED_BASE_OBJECT_COUNT == 9
    placement_keys = set(b14_recipe.HOST_A_IDENTITY) | set(b14_recipe.HOST_B_IDENTITY)
    assert not placement_keys.intersection({"x", "y", "z", "point"})

    module = FakeModule()
    document = base_document()
    snapshot = b14_recipe.freecad_base_snapshot(module, document)
    assert snapshot["semantic"]["object_count"] == 9
    assert snapshot["semantic"]["hosts"][0]["identity"]["track_name"] == "Main Track"
    assert snapshot["semantic"]["hosts"][1]["identity"]["track_name"] == "Track 2"
    reversed_snapshot = b14_recipe.freecad_base_snapshot(
        module,
        FakeDocument(reversed(document.Objects)),
    )
    assert reversed_snapshot["semantic_sha256"] == snapshot["semantic_sha256"]

    document_with_turnout = base_document()
    document_with_turnout.Objects[4].properties["TurnoutID"] = "TO-001"
    expect_value_error(
        lambda: b14_recipe.freecad_base_snapshot(module, document_with_turnout),
        "already contains managed special trackwork",
    )

    wrong_curve = base_document()
    wrong_curve.Objects[5].properties["CurveRadius"] = 601.0
    expect_value_error(
        lambda: b14_recipe.freecad_base_snapshot(module, wrong_curve),
        "Unexpected B14 base curve contract",
    )

    bridge_root = PROJECT_ROOT / "tools" / "freecad_bridge"
    patch_text = (bridge_root / "freecad-cli-tracktemplate.patch").read_text(
        encoding="utf-8"
    )
    setup_text = (bridge_root / "setup-freecad-cli").read_text(encoding="utf-8")
    assert "660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7" in setup_text
    assert "freecad-cli-tracktemplate.patch" in setup_text
    assert patch_text.count("diff --git ") == 6

    cold_wrapper = bridge_root / "run-b14-cold"
    warm_wrapper = bridge_root / "run-b14-warm"
    warm_host = bridge_root / "run_b14_warm_reuse.py"
    warm_probe = bridge_root / "probes" / "b14_warm_reuse_driver.py"
    for executable in (
        bridge_root / "setup-freecad-cli",
        bridge_root / "build-b14-base",
        cold_wrapper,
        warm_wrapper,
    ):
        assert executable.is_file(), executable
        assert executable.stat().st_mode & 0o111, executable

    cold_wrapper_text = cold_wrapper.read_text(encoding="utf-8")
    warm_wrapper_text = warm_wrapper.read_text(encoding="utf-8")
    warm_host_text = warm_host.read_text(encoding="utf-8")
    warm_probe_text = warm_probe.read_text(encoding="utf-8")
    assert "run-isolated" in cold_wrapper_text
    assert "run-isolated" in warm_wrapper_text
    assert 'parser.add_argument("--base", type=pathlib.Path, required=True)' in warm_host_text
    assert "if args.iterations != 3:" in warm_host_text
    assert "shutil.copy2(base_path, document_path)" in warm_host_text
    assert "unchanged_result_reused" in warm_probe_text
    assert "Warm reuse changed stable document state" in warm_probe_text
    assert "toe_chainage_a_mm\"] != 746.298" in warm_probe_text

    print("FreeCAD bridge recipe validation passed")


if __name__ == "__main__":
    validate()
