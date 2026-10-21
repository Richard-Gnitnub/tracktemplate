#!/usr/bin/env python3
"""Prove private chair-frame recovery with independent invented geometry."""

import copy
from fractions import Fraction
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.domain.chair_placement import (  # noqa: E402
    S1Placement,
    recover_reference_frame,
)


def _close(first, second, *, scale=1):
    """Allow arithmetic roundoff only, never a railway/fit allowance."""
    assert math.dist(first, second) <= 32 * sys.float_info.epsilon * scale


def _placement(frame, centre=(0, 0)):
    return S1Placement(
        "chair", "rail", "timber", (*centre, 0.8),
        frame["x_axis"], frame["y_axis"],
    )


def validate_hand_cases():
    """Use axis-aligned and skewed faces with hand-calculated crossings."""
    source = ((0, 0), (1, 0), [(-3, -1), (3, -1)],
              [(-3, 1), (3, 1)])
    original = copy.deepcopy(source)
    frame = recover_reference_frame(*source)
    assert frame["x_axis"] == (1, 0) and frame["y_axis"] == (0, 1)
    assert _placement(frame).transform_point((2, 3, 4)) == (2, 3, 4.8)
    assert frame["witness"]["gauge_face"] == {
        "point_mm_exact": ["0", "-1"],
        "normal_parameter_mm_exact": "-1",
        "segments": [{"index": 0, "fraction_exact": "1/2"}],
    }
    assert source == original
    assert json.loads(json.dumps(frame["witness"])) == frame["witness"]

    # The nearest-face vector is skewed to the unchanged horizontal rail.
    # The normal line still crosses at the hand-known points (0,-2),(0,2).
    skewed = recover_reference_frame(
        (0, 0), (1, 0), [(-2, -3), (2, -1)], [(-2, 1), (2, 3)],
    )
    assert skewed["x_axis"] == (1, 0)
    assert skewed["y_axis"] == (0, 1)
    assert skewed["witness"]["gauge_face"]["point_mm_exact"] == [
        "0", "-2",
    ]
    assert skewed["witness"]["outer_face"]["point_mm_exact"] == [
        "0", "2",
    ]
    _placement(skewed)

    # Reversing the explicit gauge side changes both axes, never handedness.
    swapped = recover_reference_frame(
        source[0], source[1], source[3], source[2],
    )
    assert swapped["x_axis"] == (-1, 0)
    assert swapped["y_axis"] == (0, -1)
    _placement(swapped)
    return 3


def validate_rigid_invariants():
    """Use four quarter turns and a 3:4:5 rotation, with translations."""
    count = 0
    for cosine, sine in ((1, 0), (0, 1), (-1, 0), (0, -1), (0.6, 0.8)):
        for centre in ((0, 0), (1024, -2048)):
            def transform(point):
                x, y = point
                return (centre[0] + cosine * x - sine * y,
                        centre[1] + sine * x + cosine * y)

            gauge = [transform(p) for p in ((-4, -2), (4, -2))]
            outer = [transform(p) for p in ((-4, 2), (4, 2))]
            frame = recover_reference_frame(
                centre, (cosine, sine), gauge, outer,
            )
            _close(frame["x_axis"], (cosine, sine))
            _close(frame["y_axis"], (-sine, cosine))
            _close(_placement(frame, centre).transform_point((2, 3, 0))[:2],
                   transform((2, 3)), scale=4096)
            reversed_tangent = recover_reference_frame(
                centre, (-cosine, -sine), gauge, outer,
            )
            assert reversed_tangent["x_axis"] == frame["x_axis"]
            assert reversed_tangent["y_axis"] == frame["y_axis"]
            reversed_faces = recover_reference_frame(
                centre, (cosine, sine), gauge[::-1], outer[::-1],
            )
            assert reversed_faces["x_axis"] == frame["x_axis"]
            assert reversed_faces["y_axis"] == frame["y_axis"]
            for name in ("gauge_face", "outer_face"):
                assert reversed_faces["witness"][name]["point_mm_exact"] == (
                    frame["witness"][name]["point_mm_exact"]
                )
            count += 1
    return count


def validate_exact_topology():
    """Separate shared vertices and arbitrarily near parallel crossings."""
    frame = recover_reference_frame(
        (0, 0), (1, 0), [(-2, -1), (0, -1), (2, -1)],
        [(-2, 1), (0, 1), (2, 1)],
    )
    for name in ("gauge_face", "outer_face"):
        assert frame["witness"][name]["segments"] == [
            {"index": 0, "fraction_exact": "1"},
            {"index": 1, "fraction_exact": "0"},
        ]
    _placement(frame)
    near_parallel = recover_reference_frame(
        (0, 0), (1, 0), [(-1e-300, -3), (1e-300, -1)],
        [(-1, 1), (1, 1)],
    )
    assert near_parallel["witness"]["gauge_face"]["point_mm_exact"] == [
        "0", "-2",
    ]
    tiny = recover_reference_frame(
        (0, 0), (1, 0), [(-1, -1e-300), (1, -1e-300)],
        [(-1, 1e-300), (1, 1e-300)],
    )
    assert Fraction(tiny["witness"]["gauge_face"][
        "normal_parameter_mm_exact"
    ]) == Fraction(-1e-300)
    huge = recover_reference_frame(
        (0, 0), (1, 0), [(-1e308, -1e308), (1e308, -1e308)],
        [(-1e308, 1e308), (1e308, 1e308)],
    )
    assert Fraction(huge["witness"]["outer_face"][
        "normal_parameter_mm_exact"
    ]) == Fraction(1e308)
    for value in (near_parallel, tiny, huge):
        _placement(value)
        assert json.loads(json.dumps(value["witness"])) == value["witness"]
    return 4


def validate_rejections():
    """Reject malformed and ambiguous geometry at the domain boundary."""
    valid = [(0, 0), (1, 0), [(-2, -1), (2, -1)], [(-2, 1), (2, 1)]]
    cases = []
    for index, values in (
        (0, (None, (0,), (0, 0, 0), (True, 0), (float("inf"), 0),
             (float("nan"), 0), ("0", 0))),
        (1, (None, (0, 0), (2, 0), (1, 0.01), (False, 1),
             (float("inf"), 0), (float("nan"), 0))),
    ):
        cases.extend((index, value) for value in values)
    bad_faces = (
        None, [], [(0, 1)], [(0, 1), (0, 1)],
        [(0, 1), (1, float("nan"))], [(0, 1), (float("inf"), 1)],
        [(0, 1), (True, 1)], [(0, 1), (1,)], [(0, 1), ("1", 1)],
        [(1, 1), (2, 1)],  # no crossing
        [(1, 1), (1, 2)],  # parallel, separate line
        [(0, 1), (0, 2)],  # coincident line segment
        [(-1, 0), (1, 0)],  # centre on face
        [(-1, 1), (1, 1), (-1, 2)],  # two different crossings
        [(-1, 1), (1, 1), (-1, 1)],  # repeated interior crossing
        [(-1, 1), (0, 1), (-1, 2), (0, 1)],  # repeated remote vertex
    )
    cases.extend((index, value) for index in (2, 3) for value in bad_faces)
    for index, value in cases:
        args = copy.deepcopy(valid)
        args[index] = value
        original = copy.deepcopy(args)
        try:
            recover_reference_frame(*args)
        except ValueError:
            pass
        else:
            raise AssertionError(("Accepted invalid geometry", index, value))
        # NaN is not equal to itself; compare stable serialised input bytes.
        assert json.dumps(args) == json.dumps(original)
    same_side = copy.deepcopy(valid)
    same_side[2] = [(-2, 3), (2, 3)]
    try:
        recover_reference_frame(*same_side)
    except ValueError as error:
        assert "straddle" in str(error)
    else:
        raise AssertionError("Accepted faces on the same side")
    return len(cases) + 1


def main():
    print({
        "hand_cases": validate_hand_cases(),
        "rigid_invariants": validate_rigid_invariants(),
        "exact_topology": validate_exact_topology(),
        "rejections": validate_rejections(),
    })
    print("Phase 9B chair frame recovery standalone validation passed")


if __name__ == "__main__":
    main()
