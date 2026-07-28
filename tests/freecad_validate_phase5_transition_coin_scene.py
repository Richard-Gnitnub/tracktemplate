"""Qualified-host check for the unexposed Phase 5 Coin scene adapter."""

import math
import pathlib
import sys
import traceback

import FreeCAD as App
from pivy import coin


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate import api  # noqa: E402
from tracktemplate.presentation import transition_coin as renderer  # noqa: E402


def _artifact():
    circle_centre_y_mm = 624.7779655573173
    radius_mm = 655.0
    transition_length_mm = 300.0
    intent = api.TransitionIntent(
        transition_id="transition:phase5:coin-host",
        circle_centre_y_mm=circle_centre_y_mm,
        radius_mm=radius_mm,
        target_signed_offset_mm=api.transition_start_signed_offset(
            circle_centre_y_mm,
            radius_mm,
            transition_length_mm,
        ),
        total_angle_rad=math.pi / 2.0,
        track_name="Phase 5 Coin host transition",
        end_name="Entry",
    )
    state = api.analyse_transition_state(api.TransitionState(intent))
    return api.regenerate_transition_preview(
        api.TransitionDerivedCache(),
        state,
        api.TransitionPreviewSpecification(segment_count=4),
    )


def validate():
    documents_before = tuple(sorted(App.listDocuments()))
    artifact = _artifact()
    binding = renderer.build_transition_coin_binding(
        artifact,
        renderer.TransitionCoinStyle(
            line_color_rgb=(0.2, 0.6, 0.9),
            line_width=2.0,
        ),
        coin,
    )

    assert binding.root.getNumChildren() == 1
    layer = binding.root.getChild(0)
    assert layer.getNumChildren() == 4
    coordinates = layer.getChild(2)
    line_set = layer.getChild(3)
    assert coordinates.point.getNum() == 5
    assert line_set.numVertices.getNum() == 1
    assert line_set.numVertices[0] == 5
    assert (
        binding.selection_for_node(line_set).domain_id
        == artifact.payload.polylines[0].domain_id
    )
    assert tuple(sorted(App.listDocuments())) == documents_before

    assert binding.discard() is True
    assert binding.root.getNumChildren() == 0
    assert tuple(sorted(App.listDocuments())) == documents_before
    print("Phase 5 transition Coin host validation passed")


try:
    validate()
except Exception:
    traceback.print_exc()
    raise
