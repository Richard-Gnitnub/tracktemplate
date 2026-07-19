"""Real FreeCAD 1.1 headless smoke test for the B15 chair display layer."""

import pathlib

import FreeCAD as App
import Part


ROOT = pathlib.Path(__file__).resolve().parents[1]
MACRO_PATH = ROOT / "model_railway_curve_template_multitrack_v10_2a8a7b15_chair_performance_and_representation.FCMacro"


def load_macro_definitions():
    source = MACRO_PATH.read_text(encoding="utf-8")
    source_without_launch = source.rsplit("\nrun_macro()", 1)[0]
    namespace = {"__name__": "b15_freecad_smoke"}
    exec(compile(source_without_launch, str(MACRO_PATH), "exec"), namespace)
    return namespace


def validate():
    namespace = load_macro_definitions()
    assert namespace["MACRO_VERSION_NUMBER"] == "10.2A8A7B15"

    detailed_cache_before = len(namespace["_CHAIR_PROTOTYPE_SHAPE_CACHE"])
    s1, s1_reused = namespace["_chair_canonical_2d_symbol"](1)
    s1_again, s1_again_reused = namespace["_chair_canonical_2d_symbol"](1)
    s1j, s1j_reused = namespace["_chair_canonical_2d_symbol"](7)
    assert s1_reused is False and s1_again_reused is True and s1j_reused is False
    assert s1_again is s1
    for symbol in (s1, s1j):
        assert not symbol["base"].isNull() and symbol["base"].isValid()
        assert not symbol["details"].isNull() and symbol["details"].isValid()
        assert not symbol["key_forward"].isNull() and symbol["key_forward"].isValid()
        assert not symbol["key_backward"].isNull() and symbol["key_backward"].isValid()
        assert len(symbol["details"].Edges) >= 8
    assert s1j["base"].BoundBox.YLength > s1["base"].BoundBox.YLength
    assert len(namespace["_CHAIR_PROTOTYPE_SHAPE_CACHE"]) == detailed_cache_before

    instance = {
        "centre_point": [12.0, -4.0],
        "rotation_degrees": 37.0,
    }
    placed = namespace["_chair_place_canonical_shape"](s1["details"], instance, 1.25)
    assert not placed.isNull() and placed.isValid()
    assert abs(placed.Placement.Base.x - 12.0) < 1.0e-9
    assert abs(placed.Placement.Base.y + 4.0) < 1.0e-9
    assert abs(placed.Placement.Base.z - 1.25) < 1.0e-9

    doc = App.newDocument("B15HeadlessChairSmoke")
    try:
        group = doc.addObject("App::DocumentObjectGroup", "ChairBatch")
        shapes = []
        for index in range(24):
            item = {
                "centre_point": [float(index) * 4.0, float(index % 3) * 3.0],
                "rotation_degrees": float((index * 11) % 180),
            }
            shapes.append(namespace["_chair_place_canonical_shape"](s1["base"], item, 0.0))
        feature = doc.addObject("Part::Feature", "ChairBaseBatch")
        feature.Shape = Part.makeCompound(shapes)
        group.addObject(feature)
        namespace["_document_recompute"](doc)
        assert len(doc.Objects) == 2
        assert not feature.Shape.isNull() and feature.Shape.isValid()
        assert len(feature.Shape.Edges) >= 24
    finally:
        App.closeDocument(doc.Name)

    print("B15 FreeCAD 1.1 headless smoke test passed")


def _run_as_script():
    try:
        validate()
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)


# FreeCADCmd loads a script using its filename stem as ``__name__`` rather
# than Python's usual ``__main__`` value. Support both execution routes while
# keeping ordinary test-module imports side-effect free.
if __name__ in {"__main__", "freecad_validate_b15"}:
    _run_as_script()
