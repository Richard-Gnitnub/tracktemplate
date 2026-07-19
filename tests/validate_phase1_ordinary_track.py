#!/usr/bin/env python3
"""Fast contract checks for the Phase 1 B14 plain-line document oracle."""

import copy
import hashlib
import json
import pathlib
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.freecad_bridge import ordinary_track_recipe  # noqa: E402


class FakeQuantity:
    def __init__(self, value):
        self.Value = value


class FakeBounds:
    XMin = -1.0000004
    YMin = -2.0
    ZMin = 0.0
    XMax = 9.0
    YMax = 18.0
    ZMax = 1.0
    XLength = 10.0000004
    YLength = 20.0
    ZLength = 1.0


class FakeShape:
    ShapeType = "Compound"
    Solids = [1]
    Shells = [1]
    Faces = [1, 2]
    Wires = [1, 2, 3]
    Edges = [1, 2, 3, 4]
    Vertexes = [1, 2, 3, 4, 5]
    Length = 12.34567891
    Area = 98.76543219
    Volume = 7.0000004
    BoundBox = FakeBounds()

    @staticmethod
    def isNull():
        return False

    @staticmethod
    def isValid():
        return True

    @staticmethod
    def hashCode():
        raise AssertionError("FreeCAD hashCode must not enter the semantic oracle")


class FakeNullShape:
    ShapeType = "Shape"

    @staticmethod
    def isNull():
        return True

    @staticmethod
    def isValid():
        raise AssertionError("A null OCC shape must not be passed to isValid")


class FakePersistedObject:
    Name = "FakeParameters"

    def __init__(self):
        self.PropertiesList = sorted(ordinary_track_recipe.PERSISTED_PROPERTY_TYPES)
        self.types = dict(ordinary_track_recipe.PERSISTED_PROPERTY_TYPES)
        for name, property_type in self.types.items():
            if name in ordinary_track_recipe.JSON_PROPERTIES:
                value = json.dumps({"value": 1.2345678901234}, sort_keys=True)
            elif property_type in ("App::PropertyLength", "App::PropertyAngle"):
                value = FakeQuantity(1.2345678901234)
            elif property_type == "App::PropertyInteger":
                value = 3
            elif property_type == "App::PropertyBool":
                value = True
            else:
                value = "stored"
            setattr(self, name, value)

    def getTypeIdOfProperty(self, name):
        return self.types[name]


def expect_value_error(action, text):
    try:
        action()
    except ValueError as error:
        assert text in str(error), str(error)
        return
    raise AssertionError("Expected ValueError containing {!r}".format(text))


def validate():
    payload = {
        "created_at": "2026-07-19T12:00:00Z",
        "items": [
            {"manager_id": "random-a", "value": 1.2345678901239},
            {"manager_id": "random-b", "value": 2.0},
        ],
    }
    normalised = ordinary_track_recipe.normalise_persisted_json(
        json.dumps(payload, sort_keys=True)
    )
    assert normalised == {
        "created_at": "<generated-timestamp>",
        "items": [
            {"manager_id": "<generated-manager-id>", "value": 1.234567890124},
            {"manager_id": "<generated-manager-id>", "value": 2.0},
        ],
    }
    assert ordinary_track_recipe.normalise_persisted_json(
        [{"position": 2}, {"position": 1}]
    ) == [{"position": 2}, {"position": 1}]
    expect_value_error(
        lambda: ordinary_track_recipe.normalise_persisted_json("not-json"),
        "Invalid persisted JSON",
    )
    expect_value_error(
        lambda: ordinary_track_recipe.normalise_persisted_json({"manager_id": ""}),
        "manager_id value is empty",
    )

    semantic = {"b": [2, 1], "a": {"value": 3}}
    expected_digest = hashlib.sha256(
        json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert ordinary_track_recipe.semantic_sha256(semantic) == expected_digest

    shape = ordinary_track_recipe.shape_summary(FakeShape())
    assert shape == {
        "is_null": False,
        "is_valid": True,
        "shape_type": "Compound",
        "solids": 1,
        "shells": 1,
        "faces": 2,
        "wires": 3,
        "edges": 4,
        "vertexes": 5,
        "length_mm": 12.345679,
        "area_mm2": 98.765432,
        "volume_mm3": 7.0,
        "bounds_mm": {
            "XMin": -1.0,
            "YMin": -2.0,
            "ZMin": 0.0,
            "XMax": 9.0,
            "YMax": 18.0,
            "ZMax": 1.0,
            "XLength": 10.0,
            "YLength": 20.0,
            "ZLength": 1.0,
        },
    }
    assert ordinary_track_recipe.shape_summary(FakeNullShape()) == {
        "is_null": True,
        "is_valid": False,
        "shape_type": "",
    }

    persisted = FakePersistedObject()
    snapshot = ordinary_track_recipe.persisted_parameter_snapshot(persisted)
    assert snapshot["values"]["TransitionLength"] == 1.234567890123
    assert snapshot["values"]["ParallelTrackCount"] == 3
    assert snapshot["values"]["TurnDirection"] == "stored"
    assert snapshot["values"]["TrackConfigurationJSON"] == {
        "value": 1.234567890123
    }
    missing = copy.copy(persisted)
    missing.PropertiesList = [
        name for name in missing.PropertiesList if name != "TransitionLength"
    ]
    expect_value_error(
        lambda: ordinary_track_recipe.persisted_parameter_snapshot(missing),
        "missing persisted parameter properties: TransitionLength",
    )
    wrong_type = copy.copy(persisted)
    wrong_type.types = dict(persisted.types)
    wrong_type.types["TransitionLength"] = "App::PropertyString"
    expect_value_error(
        lambda: ordinary_track_recipe.persisted_parameter_snapshot(wrong_type),
        "unexpected persisted property types",
    )

    bridge_root = PROJECT_ROOT / "tools" / "freecad_bridge"
    wrapper = bridge_root / "run-b14-ordinary-snapshot"
    runner = bridge_root / "run_b14_ordinary_snapshot.py"
    probe = bridge_root / "probes" / "snapshot_b14_ordinary_track.py"
    assert wrapper.is_file() and wrapper.stat().st_mode & 0o111
    assert runner.is_file() and runner.stat().st_mode & 0o111
    assert probe.is_file()
    wrapper_text = wrapper.read_text(encoding="utf-8")
    runner_text = runner.read_text(encoding="utf-8")
    probe_text = probe.read_text(encoding="utf-8")
    assert "run-isolated" in wrapper_text
    assert 'action="append"' in runner_text
    assert "shutil.copy2(base_path, copied_path)" in runner_text
    assert "App.openDocument" in runner_text
    assert "App.closeDocument" in runner_text
    assert "saveDocument" not in runner_text and ".save(" not in runner_text
    assert "ordinary_track_snapshot" in probe_text

    digest = ordinary_track_recipe.EXPECTED_ORDINARY_TRACK_SEMANTIC_SHA256
    assert len(digest) == 64
    int(digest, 16)

    print("Phase 1 plain-line oracle validation passed")


if __name__ == "__main__":
    validate()
