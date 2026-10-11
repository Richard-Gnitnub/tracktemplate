#!/usr/bin/env python3
"""Check the nominal base-plan primitive with invented dimensions only.

The asymmetric example is a 20 by 30 rectangle with corner radii
1, 2, 3 and 4. Its coordinates and metric coefficients below are
independently hand-calculated. They describe no prototype chair.
"""

from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.domain.chair_base_nominal import (  # noqa: E402
    ChairBaseNominalArc,
    ChairBaseNominalLine,
    ChairBaseNominalParameters,
    compute_chair_base_nominal_geometry,
)


def synthetic_parameters():
    """Return independently invented dimensions in full-size mm."""
    return ChairBaseNominalParameters(*map(Fraction, (20, 30, 1, 2, 3, 4)))


def _subtract(first, second):
    return tuple(a - b for a, b in zip(first, second))


def _tangent(segment, endpoint):
    if isinstance(segment, ChairBaseNominalLine):
        return _subtract(segment.end_mm, segment.start_mm)
    x, y, _z = _subtract(endpoint, segment.centre_mm)
    return -y, x, Fraction(0)


def _check_boundary(geometry):
    segments = geometry.segments
    assert len(segments) == 8
    assert len({segment.segment_id for segment in segments}) == 8
    assert len({segment.start_mm for segment in segments}) == 8
    assert tuple(type(segment) for segment in segments) == (
        ChairBaseNominalLine, ChairBaseNominalArc,
    ) * 4
    for segment, following in zip(segments, segments[1:] + segments[:1]):
        assert segment.end_mm == following.start_mm
        assert segment.start_mm != segment.end_mm
        assert all(isinstance(value, Fraction)
                   for point in (segment.start_mm, segment.end_mm)
                   for value in point)
        assert segment.start_mm[2] == segment.end_mm[2] == 0
        first = _tangent(segment, segment.end_mm)
        second = _tangent(following, following.start_mm)
        assert first[0] * second[1] - first[1] * second[0] == 0
        assert sum(a * b for a, b in zip(first, second)) > 0
        if isinstance(segment, ChairBaseNominalArc):
            assert segment.end_angle_turns - segment.start_angle_turns == (
                Fraction(1, 4)
            )
            cardinal = {
                Fraction(0): (1, 0, 0), Fraction(1, 4): (0, 1, 0),
                Fraction(1, 2): (-1, 0, 0), Fraction(3, 4): (0, -1, 0),
                Fraction(1): (1, 0, 0),
            }
            for angle, endpoint in (
                (segment.start_angle_turns, segment.start_mm),
                (segment.end_angle_turns, segment.end_mm),
            ):
                radial = _subtract(endpoint, segment.centre_mm)
                assert radial == tuple(
                    value * segment.radius_mm for value in cardinal[angle]
                )
                assert sum(value ** 2 for value in radial) == (
                    segment.radius_mm ** 2
                )


def validate_asymmetric_outline():
    """Compare every segment with an independent exact coordinate table."""
    parameters = synthetic_parameters()
    geometry = compute_chair_base_nominal_geometry(parameters)
    assert geometry.parameters == parameters
    assert geometry == compute_chair_base_nominal_geometry(parameters)
    assert geometry.bounds_mm == (-10, -15, 0, 10, 15, 0)
    assert tuple(segment.segment_id for segment in geometry.segments) == (
        "bottom", "bottom-right", "right", "top-right",
        "top", "top-left", "left", "bottom-left",
    )
    starts = (
        (-9, -15, 0), (8, -15, 0), (10, -13, 0), (10, 12, 0),
        (7, 15, 0), (-6, 15, 0), (-10, 11, 0), (-10, -14, 0),
    )
    assert tuple(segment.start_mm for segment in geometry.segments) == starts
    assert tuple(segment.end_mm for segment in geometry.segments) == (
        starts[1:] + starts[:1]
    )
    assert tuple((segment.centre_mm, segment.radius_mm)
                 for segment in geometry.segments[1::2]) == (
        ((8, -13, 0), 2), ((7, 12, 0), 3),
        ((-6, 11, 0), 4), ((-9, -14, 0), 1),
    )
    assert (geometry.area_constant_mm2, geometry.area_pi_coefficient_mm2,
            geometry.perimeter_constant_mm,
            geometry.perimeter_pi_coefficient_mm) == (
                570, Fraction(15, 2), 80, 5,
            )
    _check_boundary(geometry)
    for record, name in ((parameters, "x_span_mm"),
                         (geometry, "bounds_mm"),
                         (geometry.segments[0], "start_mm")):
        try:
            setattr(record, name, None)
        except FrozenInstanceError:
            pass
        else:
            raise AssertionError("nominal geometry record is mutable")


def validate_scale_and_reflection():
    """Check exact scale covariance and both geometric reflections."""
    original = synthetic_parameters()
    geometry = compute_chair_base_nominal_geometry(original)
    for factor in (Fraction(1, 73), Fraction(7, 3), Fraction(10 ** 40)):
        scaled = ChairBaseNominalParameters(**{
            field.name: getattr(original, field.name) * factor
            for field in fields(original)
        })
        result = compute_chair_base_nominal_geometry(scaled)
        assert result.bounds_mm == tuple(
            coordinate * factor for coordinate in geometry.bounds_mm
        )
        for before, after in zip(geometry.segments, result.segments):
            assert before.segment_id == after.segment_id
            assert after.start_mm == tuple(
                value * factor for value in before.start_mm
            )
            assert after.end_mm == tuple(v * factor for v in before.end_mm)
            if isinstance(before, ChairBaseNominalArc):
                assert after.centre_mm == tuple(
                    v * factor for v in before.centre_mm
                )
                assert after.radius_mm == before.radius_mm * factor
                assert after.start_angle_turns == before.start_angle_turns
                assert after.end_angle_turns == before.end_angle_turns
        for name in ("area_constant_mm2", "area_pi_coefficient_mm2"):
            assert getattr(result, name) == (
                getattr(geometry, name) * factor ** 2
            )
        for name in ("perimeter_constant_mm", "perimeter_pi_coefficient_mm"):
            assert getattr(result, name) == getattr(geometry, name) * factor
        _check_boundary(result)

    for axis, radii, names in (
        (0, (2, 1, 4, 3), {
            "bottom": "bottom", "right": "left", "top": "top",
            "left": "right", "bottom-right": "bottom-left",
            "top-right": "top-left", "top-left": "top-right",
            "bottom-left": "bottom-right",
        }),
        (1, (4, 3, 2, 1), {
            "bottom": "top", "right": "right", "top": "bottom",
            "left": "left", "bottom-right": "top-right",
            "top-right": "bottom-right", "top-left": "bottom-left",
            "bottom-left": "top-left",
        }),
    ):
        reflected = ChairBaseNominalParameters(
            Fraction(20), Fraction(30), *map(Fraction, radii),
        )
        result = compute_chair_base_nominal_geometry(reflected)
        by_name = {segment.segment_id: segment for segment in result.segments}

        def reflect(point):
            return tuple(-value if index == axis else value
                         for index, value in enumerate(point))

        for segment in geometry.segments:
            partner = by_name[names[segment.segment_id]]
            assert partner.end_mm == reflect(segment.start_mm)
            assert partner.start_mm == reflect(segment.end_mm)
            if isinstance(segment, ChairBaseNominalArc):
                assert partner.centre_mm == reflect(segment.centre_mm)
                assert partner.radius_mm == segment.radius_mm
        assert result.bounds_mm == geometry.bounds_mm
        for name in ("area_constant_mm2", "area_pi_coefficient_mm2",
                     "perimeter_constant_mm", "perimeter_pi_coefficient_mm"):
            assert getattr(result, name) == getattr(geometry, name)
        _check_boundary(result)


def validate_invalid_and_near_boundary_inputs():
    """Reject unsupported inputs, preserving strict but exact boundaries."""
    original = synthetic_parameters()
    for field in fields(original):
        for value in (0, 1.0, True, "1", Decimal("1"), None,
                      float("nan"), float("inf")):
            try:
                compute_chair_base_nominal_geometry(replace(
                    original, **{field.name: value},
                ))
            except TypeError as error:
                assert field.name in str(error)
            else:
                raise AssertionError("non-Fraction input was accepted")
        for value in (Fraction(0), Fraction(-1)):
            try:
                compute_chair_base_nominal_geometry(replace(
                    original, **{field.name: value},
                ))
            except ValueError as error:
                assert field.name in str(error)
            else:
                raise AssertionError("nonpositive input was accepted")

    # Distinct invented radius combinations isolate all four side guards.
    for side, values in (
        ("bottom", (10, 30, 4, 6, 1, 1)),
        ("top", (10, 30, 1, 1, 6, 4)),
        ("left", (30, 10, 4, 1, 1, 6)),
        ("right", (30, 10, 1, 4, 6, 1)),
    ):
        for excess in (Fraction(0), Fraction(1, 1000)):
            parameters = ChairBaseNominalParameters(*map(Fraction, values))
            name = "x_span_mm" if side in ("bottom", "top") else "y_span_mm"
            parameters = replace(
                parameters, **{name: getattr(parameters, name) - excess},
            )
            try:
                compute_chair_base_nominal_geometry(parameters)
            except ValueError as error:
                assert side in str(error)
            else:
                raise AssertionError(
                    "degenerate/overlapping corner accepted"
                )
        parameters = ChairBaseNominalParameters(*map(Fraction, values))
        parameters = replace(parameters, **{
            name: getattr(parameters, name) + Fraction(1, 10 ** 40),
        })
        _check_boundary(compute_chair_base_nominal_geometry(parameters))

    for value in (None, {}, tuple(fields(original))):
        try:
            compute_chair_base_nominal_geometry(value)
        except TypeError as error:
            assert "ChairBaseNominalParameters" in str(error)
        else:
            raise AssertionError("unsupported parameter record accepted")


def main():
    """Run pure analytical evidence without importing a CAD host."""
    validate_asymmetric_outline()
    validate_scale_and_reflection()
    validate_invalid_and_near_boundary_inputs()
    forbidden = {"FreeCAD", "Part", "FreeCADGui", "PySide", "pivy"}
    assert not forbidden.intersection(sys.modules)
    print("Phase 9B nominal chair-base standalone validation passed")


if __name__ == "__main__":
    main()
