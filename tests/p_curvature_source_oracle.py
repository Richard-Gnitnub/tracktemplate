"""Derive P reference poses from canonical rail and timber records.

This test oracle consumes no chair-analysis coordinates or product frame
calculation. Exact rational projection scans all raw polyline segments;
normal sections through the named faces determine the gauge side. Inputs
are model mm, in the current document XY frame, with a separate mounting Z.

The railway placement convention is the accepted B15
generate_chair_positions at lines 43479-43532: project each timber centre
onto its named rail. This independently evaluates that sampled-geometry
contract. It does not independently qualify the rail generator, discover
new assignments, certify continuous curves, or measure physical fit.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from numbers import Real
import sys


# Existing native P component comparison bound, not a fit allowance:
# tests/freecad_validate_phase9b_catalogue_p_placement.py:53.
COORDINATE_COMPARISON_MM = 1.0e-7
# Existing proper-frame arithmetic guard:
# tracktemplate/domain/chair_placement.py:17-20.
AXIS_ROUNDOFF = 32 * sys.float_info.epsilon


@dataclass(frozen=True)
class PSourceFrame:
    """One independently calculated proper frame and its source witness."""

    position_id: str
    rail_id: str
    timber_id: str
    parent_id: str
    origin_mm: tuple[float, float, float]
    x_axis: tuple[float, float]
    y_axis: tuple[float, float]
    evidence: dict


def _require(condition, message):
    if not condition:
        raise ValueError("P source oracle: " + message)


def _number(value):
    _require(isinstance(value, Real) and not isinstance(value, bool),
             "coordinates must be finite real numbers")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    _require(finite, "coordinates must be finite real numbers")
    return Fraction(value)


def _point(value):
    _require(isinstance(value, (list, tuple)) and len(value) == 2,
             "an XY point must have two coordinates")
    return tuple(_number(item) for item in value)


def _polyline(value):
    _require(isinstance(value, (list, tuple)) and len(value) >= 2,
             "a polyline needs at least two points")
    points = tuple(_point(item) for item in value)
    _require(all(first != second
                 for first, second in zip(points, points[1:])),
             "a raw source segment is collapsed")
    return points


def _indexed(records):
    _require(isinstance(records, (list, tuple)), "records must be a sequence")
    indexed = {}
    for record in records:
        _require(isinstance(record, Mapping), "a record must be a mapping")
        identity = record.get("stable_identity")
        _require(isinstance(identity, str) and identity.strip()
                 and identity not in indexed,
                 "source identities are ambiguous")
        indexed[identity] = record
    return indexed


def _projection(centre, points):
    """Find the exact minimum without product bins or float distances.

    Shared-vertex ties use the first segment in source order, matching
    accepted distance/station ordering. Different equally near support
    points are outside this bounded oracle's unambiguous evidence domain;
    they stop qualification rather than silently selecting a new rule.
    """
    candidates = []
    for index, (first, second) in enumerate(zip(points, points[1:])):
        vector = tuple(b - a for a, b in zip(first, second))
        square = sum(value * value for value in vector)
        parameter = sum((c - a) * d for c, a, d
                        in zip(centre, first, vector)) / square
        parameter = max(Fraction(0), min(Fraction(1), parameter))
        support = tuple(a + parameter * d for a, d in zip(first, vector))
        distance = sum((c - q) ** 2 for c, q in zip(centre, support))
        candidates.append((distance, index, parameter, support, vector))
    minimum = min(item[0] for item in candidates)
    nearest = [item for item in candidates if item[0] == minimum]
    _require(len({item[3] for item in nearest}) == 1,
             "distinct equal minima require separate qualification")
    _distance, index, parameter, support, vector = nearest[0]
    return support, vector, {
        "segment_index": index,
        "fraction_exact": str(parameter),
        "distance_squared_mm2_exact": str(minimum),
        "point_mm_exact": [str(value) for value in support],
        "equal_minimum_segments": [item[1] for item in nearest],
    }


def _normal_crossing(centre, direction, points):
    """Solve the normal section by rational dot products on every face."""
    roots = {}
    for index, (first, second) in enumerate(zip(points, points[1:])):
        start = sum(d * (a - c) for d, a, c
                    in zip(direction, first, centre))
        finish = sum(d * (b - c) for d, b, c
                     in zip(direction, second, centre))
        _require(not start == finish == 0,
                 "normal and face segment are coincident")
        if start == finish:
            continue
        parameter = -start / (finish - start)
        if 0 <= parameter <= 1:
            point = tuple(a + parameter * (b - a)
                          for a, b in zip(first, second))
            roots.setdefault(point, []).append({
                "segment_index": index, "fraction_exact": str(parameter),
            })
    _require(len(roots) == 1, "a named face has no unique normal crossing")
    point, segments = next(iter(roots.items()))
    signed = (direction[0] * (point[1] - centre[1])
              - direction[1] * (point[0] - centre[0]))
    _require(signed != 0, "the rail centre lies on its named face")
    return signed, {
        "point_mm_exact": [str(value) for value in point],
        "signed_cross_product_exact": str(signed), "segments": segments,
    }


def expected_p_frames(
    rail_records, timber_records, position_bindings, *, base_z_mm,
):
    """Return frames from explicit source IDs and raw geometry only.

    Each binding supplies position_id, rail_id and timber_id, optionally
    parent_id. Their qualification as P assignments belongs to the caller;
    this oracle checks the raw stock-rail/S1-S7 ownership independently.
    Small fixtures are permitted. The native caller must check the complete
    28-position/two-constituent source set, not infer it from this function.
    """
    rails, timbers = _indexed(rail_records), _indexed(timber_records)
    base_z = float(_number(base_z_mm))
    _require(isinstance(position_bindings, (list, tuple))
             and position_bindings, "bindings must be a nonempty sequence")
    frames, identities, pairs = [], set(), set()
    for binding in position_bindings:
        _require(isinstance(binding, Mapping)
                 and set(binding) <= {
                     "position_id", "rail_id", "timber_id", "parent_id",
                 }, "bindings must contain identities only")
        values = tuple(binding.get(key)
                       for key in ("position_id", "rail_id", "timber_id"))
        _require(all(isinstance(value, str) and value.strip()
                     for value in values),
                 "bindings need nonempty identities")
        identity, rail_id, timber_id = values
        _require(identity not in identities
                 and (rail_id, timber_id) not in pairs,
                 "a source position is duplicated")
        _require(rail_id in rails and timber_id in timbers,
                 "a named rail or timber is missing")
        rail, timber = rails[rail_id], timbers[timber_id]
        parent = rail.get("parent_turnout_identity")
        _require(isinstance(parent, str) and parent.strip()
                 and parent == timber.get("parent_turnout_identity")
                 and binding.get("parent_id", parent) == parent,
                 "rail and timber ownership disagree")
        identifier = timber.get("identifier")
        _require(identifier in ("S1", "S2", "S3", "S4", "S5", "S6", "S7")
                 and timber.get("prototype_reference") == identifier
                 and timber.get("section") == "switch"
                 and rail.get("rail_role") == "stock rail"
                 and rail.get("name") in (
                     "main-side stock rail", "turnout-side stock rail",
                 ), "only the named S1-S7 stock-rail P sources are supported")
        centre = _point(timber.get("centre"))
        points = _polyline(rail.get("points"))
        gauge_points = _polyline(rail.get("gauge_face_points"))
        outer_points = _polyline(rail.get("outer_face_points"))
        support, direction, projection = _projection(centre, points)
        gauge, gauge_witness = _normal_crossing(
            support, direction, gauge_points,
        )
        outer, outer_witness = _normal_crossing(
            support, direction, outer_points,
        )
        _require(gauge * outer < 0, "named faces do not straddle the rail")
        length = math.hypot(*(float(value) for value in direction))
        _require(math.isfinite(length) and length > 0,
                 "source direction cannot be normalised")
        dx, dy = (float(value) / length for value in direction)
        sign = 1 if gauge > 0 else -1
        y_axis = (sign * dy, -sign * dx)
        x_axis = (y_axis[1], -y_axis[0])
        raw_geometry = {
            "centre": [str(value) for value in centre],
            "points": [[str(value) for value in point] for point in points],
            "gauge": [[str(value) for value in point]
                      for point in gauge_points],
            "outer": [[str(value) for value in point]
                      for point in outer_points],
        }
        evidence = {
            "raw_geometry_sha256": hashlib.sha256(json.dumps(
                raw_geometry, sort_keys=True, separators=(",", ":"),
            ).encode()).hexdigest(),
            "projection": projection, "gauge_face": gauge_witness,
            "outer_face": outer_witness,
            "source_basis": "raw canonical rail vertices and timber centre",
            "analysis_coordinates_consumed": False,
            "physical_fit": "NOT_PROVED",
        }
        frames.append(PSourceFrame(
            identity, rail_id, timber_id, parent,
            (*map(float, support), base_z), x_axis, y_axis, evidence,
        ))
        identities.add(identity)
        pairs.add((rail_id, timber_id))
    return tuple(sorted(frames, key=lambda frame: frame.position_id))


def _field(frame, name):
    return frame[name] if isinstance(frame, Mapping) else getattr(frame, name)


def _frame_map(frames):
    result = {}
    for frame in frames:
        identity = _field(frame, "position_id")
        assert identity not in result, "Duplicate frame identity"
        result[identity] = frame
    assert result, "No frames supplied"
    return result


def _vector(frame, name):
    value = _field(frame, name)
    count = 3 if name == "origin_mm" else 2
    assert isinstance(value, (tuple, list)) and len(value) == count, name
    assert all(isinstance(item, Real) and not isinstance(item, bool)
               and math.isfinite(item) for item in value), name
    return value


def validate_p_frames(actual_frames, expected_frames):
    """Compare current poses within existing numerical comparison limits."""
    actual, expected = _frame_map(actual_frames), _frame_map(expected_frames)
    assert actual.keys() == expected.keys(), "P frame identities differ"
    maximum_origin, maximum_axis = 0.0, 0.0
    for identity, wanted in expected.items():
        observed = actual[identity]
        for field in ("rail_id", "timber_id"):
            assert _field(observed, field) == _field(wanted, field), (
                identity, field,
            )
        origin = math.dist(_vector(observed, "origin_mm"),
                           _vector(wanted, "origin_mm"))
        axis = max(math.dist(_vector(observed, name), _vector(wanted, name))
                   for name in ("x_axis", "y_axis"))
        assert origin <= COORDINATE_COMPARISON_MM, (
            identity, "source centre differs", origin,
        )
        assert axis <= AXIS_ROUNDOFF, (identity, "source axes differ", axis)
        maximum_origin = max(maximum_origin, origin)
        maximum_axis = max(maximum_axis, axis)
    return {
        "status": "PASS", "position_count": len(expected),
        "maximum_origin_residual_mm": maximum_origin,
        "maximum_axis_residual": maximum_axis,
        "coordinate_comparison_mm": COORDINATE_COMPARISON_MM,
        "axis_roundoff": AXIS_ROUNDOFF, "physical_fit": "NOT_PROVED",
    }


def assert_recalculated(before_frames, after_frames):
    """Require stable source identities and observable centre/axis changes."""
    before, after = _frame_map(before_frames), _frame_map(after_frames)
    assert before.keys() == after.keys(), "Recalculation changed position IDs"
    changed_centres, changed_axes = [], []
    for identity, current in after.items():
        previous = before[identity]
        for field in ("rail_id", "timber_id"):
            assert _field(previous, field) == _field(current, field), (
                identity, field,
            )
        if math.dist(_vector(previous, "origin_mm"),
                     _vector(current, "origin_mm")) > COORDINATE_COMPARISON_MM:
            changed_centres.append(identity)
        if max(math.dist(_vector(previous, name), _vector(current, name))
               for name in ("x_axis", "y_axis")) > AXIS_ROUNDOFF:
            changed_axes.append(identity)
    assert changed_centres, "No source centre was recalculated"
    assert changed_axes, "No source axis was recalculated"
    return {
        "changed_centre_ids": sorted(changed_centres),
        "changed_axis_ids": sorted(changed_axes),
        "position_count": len(after), "physical_fit": "NOT_PROVED",
    }
