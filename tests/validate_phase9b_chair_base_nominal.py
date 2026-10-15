#!/usr/bin/env python3
"""Check the nominal base-plan primitive with invented dimensions only.

The asymmetric example is a 20 by 30 rectangle with corner radii
1, 2, 3 and 4. Its coordinates and metric coefficients below are
independently hand-calculated. They describe no prototype chair.
"""

from dataclasses import FrozenInstanceError, fields, replace
from decimal import Context, Decimal, ROUND_UP, localcontext
from fractions import Fraction
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tracktemplate.domain.chair_base_nominal import (  # noqa: E402
    ChairBaseNominalArc,
    ChairBaseNominalAperture,
    ChairBaseNominalLine,
    ChairBaseNominalParameters,
    ChairBaseNominalHoleParameters,
    compute_chair_base_aperture_geometry,
    compute_chair_base_nominal_hole_profile,
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


def _aperture(name, centre, radius):
    return ChairBaseNominalAperture(
        name, tuple(map(Fraction, centre)), Fraction(radius),
    )


def validate_aperture_metrics_and_invariants():
    """Check independent net metrics, empty parity and exact transforms."""
    parameters = synthetic_parameters()
    apertures = (
        _aperture("a", (-4, -3, 0), 2),
        _aperture("b", (4, 6, 0), Fraction(3, 2)),
        _aperture("c", (3, -8, 0), 1),
    )
    result = compute_chair_base_aperture_geometry(parameters, apertures)
    assert result.outline == compute_chair_base_nominal_geometry(parameters)
    assert result.apertures == apertures
    assert result == compute_chair_base_aperture_geometry(
        parameters, apertures,
    )
    assert (result.area_constant_mm2, result.area_pi_coefficient_mm2,
            result.perimeter_constant_mm,
            result.perimeter_pi_coefficient_mm) == (
                570, Fraction(1, 4), 80, 14,
            )
    metrics = (
        "area_constant_mm2", "area_pi_coefficient_mm2",
        "perimeter_constant_mm", "perimeter_pi_coefficient_mm",
    )
    empty = compute_chair_base_aperture_geometry(parameters, ())
    reversed_result = compute_chair_base_aperture_geometry(
        parameters, apertures[::-1],
    )
    assert empty.apertures == ()
    assert reversed_result.apertures == apertures[::-1]
    for name in metrics:
        assert getattr(empty, name) == getattr(result.outline, name)
        assert getattr(reversed_result, name) == getattr(result, name)
    for record, name in ((result, "apertures"),
                         (apertures[0], "centre_mm")):
        try:
            setattr(record, name, None)
        except FrozenInstanceError:
            pass
        else:
            raise AssertionError("aperture geometry record is mutable")

    for factor in (Fraction(1, 10 ** 40), Fraction(7, 3),
                   Fraction(10 ** 40)):
        scaled_parameters = ChairBaseNominalParameters(**{
            field.name: getattr(parameters, field.name) * factor
            for field in fields(parameters)
        })
        scaled_apertures = tuple(replace(
            item, centre_mm=tuple(v * factor for v in item.centre_mm),
            radius_mm=item.radius_mm * factor,
        ) for item in apertures)
        scaled = compute_chair_base_aperture_geometry(
            scaled_parameters, scaled_apertures,
        )
        assert scaled.apertures == scaled_apertures
        for name in metrics:
            exponent = 2 if name.startswith("area_") else 1
            assert getattr(scaled, name) == getattr(result, name) * (
                factor ** exponent
            )
    for axis, radii in ((0, (2, 1, 4, 3)), (1, (4, 3, 2, 1))):
        reflected = compute_chair_base_aperture_geometry(
            ChairBaseNominalParameters(
                Fraction(20), Fraction(30), *map(Fraction, radii),
            ),
            tuple(replace(item, centre_mm=tuple(
                -value if index == axis else value
                for index, value in enumerate(item.centre_mm)
            )) for item in apertures),
        )
        assert tuple(item.aperture_id for item in reflected.apertures) == (
            "a", "b", "c",
        )
        for name in metrics:
            assert getattr(reflected, name) == getattr(result, name)


def _expect_aperture_failure(apertures, error_type, message):
    try:
        compute_chair_base_aperture_geometry(
            synthetic_parameters(), apertures,
        )
    except error_type as error:
        assert message in str(error)
    else:
        raise AssertionError("invalid aperture input was accepted")


def validate_aperture_boundaries():
    """Use exact straight, circular and pair tangencies as boundary proof."""
    parameters = synthetic_parameters()
    epsilon = Fraction(1, 10 ** 40)
    # Each circle has one exact tangent: four straight sides, then four
    # arcs. Arc centre offsets use the rational 3:4:5 triangle.
    tangent_cases = (
        ((0, -14, 0), 1), ((9, 0, 0), 1),
        ((0, 14, 0), 1), ((-9, 0, 0), 1),
        ((Fraction(43, 5), Fraction(-69, 5), 0), 1),
        ((Fraction(38, 5), Fraction(64, 5), 0), 2),
        ((Fraction(-33, 5), Fraction(59, 5), 0), 3),
        ((Fraction(-93, 10), Fraction(-72, 5), 0), Fraction(1, 2)),
        # Arc/line join and the arc centre itself exercise endpoints and
        # the zero radial vector without a division or angular choice.
        ((7, 13, 0), 2), ((7, 12, 0), 3),
    )
    for centre, radius in tangent_cases:
        valid = _aperture("boundary", centre, Fraction(radius) - epsilon)
        compute_chair_base_aperture_geometry(parameters, (valid,))
        for delta in (Fraction(0), epsilon):
            _expect_aperture_failure((replace(
                valid, radius_mm=Fraction(radius) + delta,
            ),), ValueError, "strictly inside")

    # A large central circle can exceed an individual corner radius.
    compute_chair_base_aperture_geometry(
        parameters, (_aperture("central", (0, 0, 0), 5),),
    )
    for centre in ((-11, 0, 0), (11, 0, 0), (0, -16, 0), (0, 16, 0),
                   (-10, -15, 0), (10, -15, 0),
                   (10, 15, 0), (-10, 15, 0),
                   (Fraction(99, 10), Fraction(149, 10), 0)):
        _expect_aperture_failure(
            (_aperture("outside", centre, Fraction(1, 100)),),
            ValueError, "strictly inside",
        )
    first = _aperture("first", (0, 0, 0), 2)
    # Separation is exactly 5 through a second 3:4:5 triangle; the sum
    # of radii is 5. This also rejects concentric/nested openings.
    second = _aperture("second", (3, 4, 0), 3)
    compute_chair_base_aperture_geometry(parameters, (
        first, replace(second, radius_mm=Fraction(3) - epsilon),
    ))
    for other in (second, replace(second, radius_mm=Fraction(3) + epsilon),
                  _aperture("second", (0, 0, 0), 1),
                  _aperture("second", (1, 0, 0), 4)):
        _expect_aperture_failure(
            (first, other), ValueError, "touch or overlap",
        )


def validate_aperture_input_contract():
    """Reject mutable containers, ambiguous identities and inexact units."""
    original = _aperture("a", (0, 0, 0), 1)
    for value in (None, [], {}, [original]):
        _expect_aperture_failure(value, TypeError, "immutable tuple")
    for value in (None, {}, (), "a"):
        _expect_aperture_failure((value,), TypeError,
                                 "ChairBaseNominalAperture")
    for value, error_type in ((None, TypeError), (1, TypeError),
                              ("", ValueError), ("  ", ValueError)):
        _expect_aperture_failure(
            (replace(original, aperture_id=value),),
            error_type, "aperture_id",
        )
    _expect_aperture_failure(
        (original, replace(original, centre_mm=(
            Fraction(4), Fraction(0), Fraction(0),
        ))), ValueError, "unique",
    )
    for centre in (None, [], [Fraction(0)] * 3, (Fraction(0),) * 2,
                   (Fraction(0),) * 4, (0, Fraction(0), Fraction(0)),
                   (Fraction(0), 0.0, Fraction(0)),
                   (Fraction(0), Fraction(0), True)):
        _expect_aperture_failure(
            (replace(original, centre_mm=centre),), TypeError, "centre_mm",
        )
    _expect_aperture_failure((replace(
        original, centre_mm=(Fraction(0), Fraction(0), Fraction(1)),
    ),), ValueError, "Z=0")
    for radius in (0, 1.0, True, "1", Decimal("1"), None,
                   float("nan"), float("inf")):
        _expect_aperture_failure(
            (replace(original, radius_mm=radius),), TypeError, "radius_mm",
        )
    for radius in (Fraction(0), Fraction(-1)):
        _expect_aperture_failure(
            (replace(original, radius_mm=radius),), ValueError, "positive",
        )


def validate_hole_profile():
    """Prove the actual-mouth section from a hand-solvable 3-4-5 triangle."""
    parameters = ChairBaseNominalHoleParameters(
        Fraction(2), Fraction(17, 2), Fraction(8), Fraction(1),
    )
    profile = compute_chair_base_nominal_hole_profile(parameters)
    assert profile.parameters == parameters
    assert profile.wall_slope == Decimal("0.75")
    assert profile.wall_secant == Decimal("1.25")
    assert profile.lower_mm == (2, 0, 0)
    assert profile.tangent_mm == (Decimal("7.7"), 0, Decimal("7.6"))
    assert profile.mouth_mm == (Decimal("8.5"), 0, 8)
    assert profile.round_centre_mm == (Decimal("8.5"), 0, 7)
    with localcontext(Context(prec=110)):
        root5 = Decimal(5).sqrt()
        expected = (Decimal("8.5") - 1/root5, 0, 7 + 2/root5)
        assert max(abs(a-b) for a, b in zip(
            profile.round_midpoint_mm, expected,
        )) < Decimal("1e-77")
    for record, attribute in ((parameters, "mouth_radius_mm"),
                              (profile, "tangent_mm")):
        try:
            setattr(record, attribute, None)
        except FrozenInstanceError:
            pass
        else:
            raise AssertionError("hole record is mutable")
    # A caller's low precision and rounding mode cannot change the result.
    with localcontext(Context(prec=6, rounding=ROUND_UP)):
        assert profile == compute_chair_base_nominal_hole_profile(parameters)
    with localcontext(Context(prec=100)):
        for factor in (Fraction(1, 73), Fraction(7, 3), Fraction(10**40)):
            scaled = ChairBaseNominalHoleParameters(**{
                field.name: getattr(parameters, field.name) * factor
                for field in fields(parameters)
            })
            result = compute_chair_base_nominal_hole_profile(scaled)
            multiplier = Decimal(factor.numerator) / factor.denominator
            assert abs(result.wall_slope - profile.wall_slope) < (
                Decimal("1e-77")
            )
            for name in ("lower_mm", "tangent_mm", "mouth_mm",
                         "round_centre_mm", "round_midpoint_mm"):
                for before, after in zip(getattr(profile, name),
                                         getattr(result, name)):
                    assert abs(after-before*multiplier) <= (
                        abs(multiplier)*Decimal("1e-76")
                    )


def validate_hole_radical_and_boundaries():
    """Use a separate quadratic root and strict-domain boundary cases."""
    parameters = ChairBaseNominalHoleParameters(*map(Fraction, (3, 7, 5, 1)))
    result = compute_chair_base_nominal_hole_profile(parameters)
    # d=h=4, f=1 gives 15*k^2 - 32*k + 15 = 0. The smaller
    # root alone satisfies the original unsquared equation with k>0.
    with localcontext(Context(prec=120)):
        expected = (Decimal(16) - Decimal(31).sqrt()) / 15
        assert abs(result.wall_slope-expected) < Decimal("1e-78")
        k, q = result.wall_slope, result.wall_secant
        tr, _y, tz = result.tangent_mm
        assert abs(4 - 4*k - q) < Decimal("1e-77")
        assert abs(tr - 3 - k*tz) < Decimal("1e-77")
        assert abs((tr-7)*k + tz-4) < Decimal("1e-77")
        assert abs((tr-7)**2 + (tz-4)**2 - 1) < Decimal("1e-77")
    for field in fields(parameters):
        for invalid in (0, 1.0, True, "1", Decimal(1), None,
                        float("nan"), float("inf")):
            try:
                compute_chair_base_nominal_hole_profile(replace(
                    parameters, **{field.name: invalid},
                ))
            except TypeError:
                pass
            else:
                raise AssertionError("non-Fraction hole length accepted")
        for invalid in (Fraction(0), Fraction(-1)):
            try:
                compute_chair_base_nominal_hole_profile(replace(
                    parameters, **{field.name: invalid},
                ))
            except ValueError:
                pass
            else:
                raise AssertionError("nonpositive hole length accepted")
    for invalid in (
        replace(parameters, top_height_mm=Fraction(1)),
        replace(parameters, top_height_mm=Fraction(1, 2)),
        replace(parameters, mouth_radius_mm=Fraction(4)),
        replace(parameters, mouth_radius_mm=Fraction(7, 2)),
    ):
        try:
            compute_chair_base_nominal_hole_profile(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("unsupported hole section accepted")
    for invalid in (None, (), synthetic_parameters()):
        try:
            compute_chair_base_nominal_hole_profile(invalid)
        except TypeError:
            pass
        else:
            raise AssertionError("wrong parameter record accepted")
    for near in (
        replace(parameters, mouth_radius_mm=4+Fraction(1, 10**30)),
        replace(parameters, top_height_mm=1+Fraction(1, 10**30)),
        replace(parameters, top_height_mm=Fraction(2)),  # h=f, no pole
    ):
        profile = compute_chair_base_nominal_hole_profile(near)
        assert profile.wall_slope > 0
        assert profile.lower_mm[0] < profile.tangent_mm[0]
        assert profile.tangent_mm[2] < profile.mouth_mm[2]


def main():
    """Run pure analytical evidence without importing a CAD host."""
    validate_asymmetric_outline()
    validate_scale_and_reflection()
    validate_invalid_and_near_boundary_inputs()
    validate_aperture_metrics_and_invariants()
    validate_aperture_boundaries()
    validate_aperture_input_contract()
    validate_hole_profile()
    validate_hole_radical_and_boundaries()
    forbidden = {"FreeCAD", "Part", "FreeCADGui", "PySide", "pivy"}
    assert not forbidden.intersection(sys.modules)
    print("Phase 9B nominal chair-base standalone validation passed")


if __name__ == "__main__":
    main()
