"""Test-only B14/B15 comparison for bounded canonical Euler centrelines.

This module reads fingerprinted legacy functions without launching either
macro. It keeps their 3 mm sampling and distinguishes the actual sampled
output from their independent endpoint calculation used at B16 stations.
No fixture, numerical bound, or result is a production-clearance decision.
"""

import ast
import bisect
from dataclasses import dataclass
import hashlib
import math
import pathlib

from tracktemplate import api


ROOT = pathlib.Path(__file__).resolve().parents[1]
NUMERICAL_TOLERANCE_MM = 1.0e-8
IMPORT_TRANSPORT_TOLERANCE_MM = 1.0e-7
SOURCE_HASHES = {
    "AdvancedTurnout.FCMacro": (
        "51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088"
    ),
    (
        "model_railway_curve_template_multitrack_v10_2a8a7b15_"
        "chair_performance_and_representation.FCMacro"
    ): "3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848",
}
LEGACY_FUNCTIONS = (
    "left_normal",
    "rotate_xy",
    "integrate_path_segment",
    "clothoid_entry_displacement",
    "clothoid_exit_displacement",
    "transition_start_signed_offset",
    "solve_transition_length",
    "build_concentric_core",
)


@dataclass(frozen=True)
class TestVector:
    """Only the numeric x/y/z fields consumed by the legacy calculation."""

    x: float
    y: float
    z: float = 0.0


@dataclass(frozen=True)
class EquivalenceCase:
    """A finite test design in millimetres and canonical left-turn space."""

    case_id: str
    end_name: str
    radius_mm: float
    requested_length_mm: float | None = None
    target_signed_offset_mm: float | None = None
    maximum_chord_error_mm: float = 0.05
    maximum_segment_count: int = 64
    circle_centre_y_mm: float = 624.7779655573173
    total_angle_rad: float = math.pi / 2.0


def equivalence_cases():
    """Return recorded examples plus finite analytical boundary examples."""
    return (
        EquivalenceCase("representative-entry", "Entry", 655.0, 300.0),
        EquivalenceCase("representative-exit", "Exit", 655.0, 420.0),
        EquivalenceCase(
            "recorded-outside-entry", "Entry", 655.0,
            target_signed_offset_mm=-50.0,
        ),
        EquivalenceCase(
            "recorded-inside-exit", "Exit", 545.0,
            target_signed_offset_mm=50.0,
        ),
        EquivalenceCase("short-entry", "Entry", 2000.0, 50.0),
        EquivalenceCase(
            "long-exit", "Exit", 400.0, 1000.0,
            maximum_segment_count=128,
        ),
        EquivalenceCase("zero-entry", "Entry", 655.0, 0.0),
        EquivalenceCase("zero-exit", "Exit", 655.0, 0.0),
    )


def load_legacy_oracles(root=ROOT):
    """Load only the frozen mathematical closure; never execute a macro."""
    oracles = {}
    for relative_path, expected_hash in SOURCE_HASHES.items():
        path = pathlib.Path(root) / relative_path
        source = path.read_bytes()
        assert hashlib.sha256(source).hexdigest() == expected_hash, path
        tree = ast.parse(source, filename=str(path))
        functions = [
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name in LEGACY_FUNCTIONS
        ]
        assert len(functions) == len(LEGACY_FUNCTIONS)
        assert {node.name for node in functions} == set(LEGACY_FUNCTIONS)
        namespace = {"math": math, "vector_xy": TestVector}
        for name, expected in (
            ("SAMPLE_SPACING", 3.0),
            ("GEOMETRY_TOLERANCE", NUMERICAL_TOLERANCE_MM),
        ):
            assignments = [
                node for node in tree.body
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == name
                    for target in node.targets
                )
            ]
            assert len(assignments) == 1
            value = ast.literal_eval(assignments[0].value)
            assert value == expected
            namespace[name] = value
        selected = ast.Module(body=functions, type_ignores=[])
        exec(compile(selected, str(path), "exec"), namespace)
        oracles[relative_path] = namespace
    return oracles


def exact_fixture(case, oracles=None):
    """Use legacy-derived input, then the unchanged public B16 exact route."""
    if oracles is None:
        oracles = load_legacy_oracles()
    oracle = next(iter(oracles.values()))
    target = case.target_signed_offset_mm
    if target is None:
        assert case.requested_length_mm is not None
        target = oracle["transition_start_signed_offset"](
            case.circle_centre_y_mm,
            case.radius_mm,
            case.requested_length_mm,
        )
    intent = api.TransitionIntent(
        transition_id="transition:phase6:equivalence:" + case.case_id,
        circle_centre_y_mm=case.circle_centre_y_mm,
        radius_mm=case.radius_mm,
        target_signed_offset_mm=target,
        total_angle_rad=case.total_angle_rad,
        track_name="Phase 6 equivalence fixture",
        end_name=case.end_name,
    )
    state = api.analyse_transition_state(api.TransitionState(intent))
    for legacy in oracles.values():
        length = legacy["solve_transition_length"](
            intent.circle_centre_y_mm,
            intent.radius_mm,
            intent.target_signed_offset_mm,
            intent.total_angle_rad,
            intent.track_name,
            intent.end_name,
        )
        assert length == state.analysis.transition_length_mm
    specification = api.TransitionExactSpecification(
        case.maximum_chord_error_mm,
        case.maximum_segment_count,
    )
    artifact = api.regenerate_transition_exact(
        api.TransitionDerivedCache(), state, specification,
    )
    return state, specification, artifact


def analytical_coordinates(oracle, state, stations_mm):
    """Evaluate the fixed Euler curve through the frozen endpoint function.

    At station s, an entry of length s and radius R*L/s has the same
    curvature law as the first s millimetres of the full entry (L, R).
    This uses the legacy Simpson function, not B16's station function.
    Both ends use canonical origin, increasing station, XY mm and z=0.
    """
    length = state.analysis.transition_length_mm
    radius = state.intent.radius_mm
    result = []
    for station in stations_mm:
        assert 0.0 <= station <= length
        local_radius = radius
        if 0.0 < station < length:
            local_radius = radius * length / station
        x_mm, y_mm, _heading = oracle["clothoid_entry_displacement"](
            station, local_radius, 240,
        )
        result.append((x_mm, y_mm, 0.0))
    return tuple(result)


def simpson_remainder_bound_mm(station, length, radius):
    """Bound truncation of the frozen 240-step Simpson integration.

    For g(u)=exp(i*alpha*u*u), alpha=s*s/(2*R*L), the fourth derivative
    is (-12*alpha**2 - 48j*alpha**3*u*u + 16*alpha**4*u**4)*g(u).
    Its norm on [0,1] is at most 12*alpha**2+48*alpha**3+16*alpha**4.
    Composite Simpson's remainder is at most s*max(abs(g''''))/(180*N**4).
    This bounds quadrature truncation, separately from floating-point error
    and from the fixed B14/B15-to-B16 parity comparison tolerance.
    """
    if station == 0.0:
        return 0.0
    assert 0.0 < station <= length and radius > 0.0
    alpha = station * station / (2.0 * radius * length)
    derivative_bound = 12.0 * alpha**2 + 48.0 * alpha**3 + 16.0 * alpha**4
    return station * derivative_bound / (180.0 * 240**4)


def legacy_polyline(oracle, state):
    """Return actual legacy sampled output as (station, x, y, z) tuples.

    The enclosing circular portion locates the selected transition but is
    excluded from the comparison. Stations are integration arc stations,
    not accumulated chord lengths. The macro's endpoint snaps stay intact.
    An Exit is traversed from its tangent end back to the circle. Subtract
    each point from the final endpoint, rotate by minus the final heading,
    then reflect Y. This gives canonical increasing left-turn curvature.
    """
    intent = state.intent
    length = state.analysis.transition_length_mm
    is_entry = intent.end_name == "Entry"
    assert is_entry or intent.end_name == "Exit"
    core = oracle["build_concentric_core"](
        (0.0, intent.circle_centre_y_mm),
        intent.radius_mm,
        length if is_entry else 0.0,
        0.0 if is_entry else length,
        intent.total_angle_rad,
        intent.end_name,
    )
    assert core["circular_length"] > 0.0
    count = math.ceil(length / oracle["SAMPLE_SPACING"])
    if is_entry:
        raw = core["points"][:count + 1]
        origin = raw[0]
        coordinates = tuple(
            (point.x - origin.x, point.y - origin.y, 0.0)
            for point in raw
        )
    else:
        raw = core["points"][-count - 1:]
        origin = raw[-1]
        coordinates = []
        for point in reversed(raw):
            x_mm, y_mm = oracle["rotate_xy"](
                origin.x - point.x,
                origin.y - point.y,
                -intent.total_angle_rad,
            )
            coordinates.append((x_mm, -y_mm, 0.0))
        coordinates = tuple(coordinates)
    assert len(coordinates) == count + 1
    stations = (
        tuple(length * index / count for index in range(count)) + (length,)
        if count else (0.0,)
    )
    return tuple(
        (station,) + coordinate
        for station, coordinate in zip(stations, coordinates)
    )


def _interpolate(polyline, stations, station):
    if station == stations[-1]:
        return polyline[-1][1:]
    index = bisect.bisect_right(stations, station) - 1
    start, end = polyline[index:index + 2]
    fraction = (station - start[0]) / (end[0] - start[0])
    return tuple(
        start[axis] + fraction * (end[axis] - start[axis])
        for axis in (1, 2, 3)
    )


def maximum_correspondence_error(first, second):
    """Certify the complete common-station piecewise-linear discrepancy.

    On each interval in the union of breakpoints, the vector difference
    is affine. Its norm is convex, so its maximum is at an endpoint.
    This bounds Hausdorff distance without claiming identical sampling.
    """
    station_sets = []
    for polyline in (first, second):
        assert polyline
        assert all(
            len(point) == 4 and all(math.isfinite(v) for v in point)
            for point in polyline
        )
        stations = tuple(point[0] for point in polyline)
        assert stations[0] == 0.0
        assert all(a < b for a, b in zip(stations, stations[1:]))
        station_sets.append(stations)
    assert station_sets[0][-1] == station_sets[1][-1]
    return max(
        math.dist(
            _interpolate(first, station_sets[0], station),
            _interpolate(second, station_sets[1], station),
        )
        for station in set(station_sets[0] + station_sets[1])
    )


def _length_evidence(polyline, length, radius, node_error_terms):
    node_error = sum(node_error_terms.values())
    count = len(polyline) - 1
    measured = sum(
        math.dist(start[1:], end[1:])
        for start, end in zip(polyline, polyline[1:])
    )
    # Project each ideal chord onto its midpoint tangent. Since curvature
    # is at most 1/R and cos(t) >= 1-t*t/2, its deficit is at most
    # h**3/(24*R**2). Perturbed endpoints add at most 2*node_error per edge.
    deficit = sum(
        (end[0] - start[0]) ** 3 / (24.0 * radius * radius)
        for start, end in zip(polyline, polyline[1:])
    )
    transport = 2.0 * count * node_error
    assert length - deficit - transport <= measured <= length + transport
    return {
        "polyline_length_mm": measured,
        "node_error_terms_mm": node_error_terms,
        "node_error_bound_mm": node_error,
        "ideal_chord_deficit_bound_mm": deficit,
        "coordinate_perturbation_bound_mm": transport,
        "minimum_length_mm": length - deficit - transport,
        "maximum_length_mm": length + transport,
    }


def compare_output_coordinates(
    case, state, exact_result, coordinates, *,
    oracles=None, transport_tolerance_mm=0.0,
):
    """Compare ordered transported XYZ with both independent legacy routes.

    The fixed finite comparison envelope is B16's signed chord bound plus the
    legacy discretisation bound 5*h*h/(24*R), plus 1e-8 mm numerical error.
    Imported/Part transport error is separately bounded and reported.
    No comparison uses the default relative tolerance of math.isclose.
    The union-station comparison directly checks this envelope for each
    fixture. It is not a universal absolute analytical-error guarantee;
    the frozen Simpson method has a separate remainder diagnostic.
    """
    assert 0.0 <= transport_tolerance_mm <= IMPORT_TRANSPORT_TOLERANCE_MM
    if oracles is None:
        oracles = load_legacy_oracles()
    centreline = exact_result.centreline
    assert centreline.domain_id == state.intent.transition_id
    assert centreline.frame_id == "canonical-local-left-turn-v1"
    assert centreline.length_unit == "mm"
    assert centreline.angle_unit == "rad"
    assert centreline.maximum_chord_error_mm == case.maximum_chord_error_mm
    expected = tuple((p.x_mm, p.y_mm, 0.0) for p in centreline.points)
    coordinates = tuple(tuple(point) for point in coordinates)
    assert len(coordinates) == len(expected)
    assert all(
        len(point) == 3 and all(math.isfinite(v) for v in point)
        for point in coordinates
    )
    transport_error = max(map(math.dist, expected, coordinates))
    assert transport_error <= transport_tolerance_mm, "ordered transport"
    stations = tuple(p.station_mm for p in centreline.points)
    length = state.analysis.transition_length_mm
    radius = state.intent.radius_mm
    assert stations[0] == 0.0 and stations[-1] == length
    observed = tuple((s,) + p for s, p in zip(stations, coordinates))
    # Length bounds need absolute node error, not B14/B15 parity error.
    # Include the largest quadrature remainder at the actual B16 stations.
    output_remainder = max(
        simpson_remainder_bound_mm(station, length, radius)
        for station in stations
    )
    # The legacy Exit's snapped endpoint uses theta=alpha*(2*u-u*u).
    # Its fourth-derivative norm has the same bound as an Entry, with
    # u replaced by 1-u. Rotation and reflection preserve that error norm.
    endpoint_remainder = simpson_remainder_bound_mm(length, length, radius)
    reports = []
    for source_path, oracle in oracles.items():
        analytical = analytical_coordinates(oracle, state, stations)
        numerical_error = max(map(math.dist, expected, analytical))
        assert numerical_error <= NUMERICAL_TOLERANCE_MM, "legacy analytical"
        assert math.dist(coordinates[0], (0.0, 0.0, 0.0)) <= (
            transport_tolerance_mm
        )
        assert math.dist(coordinates[-1], analytical[-1]) <= (
            NUMERICAL_TOLERANCE_MM + transport_tolerance_mm
        )
        legacy = legacy_polyline(oracle, state)
        assert math.dist(legacy[-1][1:], analytical[-1]) <= (
            NUMERICAL_TOLERANCE_MM
        )
        count = len(legacy) - 1
        interval = length / count if count else 0.0
        # On one legacy midpoint-curvature step u in [0,h], the heading
        # error is u*(h-u)/(2*R*L). Integrating its absolute value over
        # the full length bounds vertex error by h*h/(12*R). Linear
        # interpolation adds h*h/(8*R), giving 5*h*h/(24*R).
        legacy_node_error = interval * interval / (12.0 * radius)
        legacy_bound = 5.0 * interval * interval / (24.0 * radius)
        bound = (
            centreline.chord_error_bound_mm + legacy_bound
            + NUMERICAL_TOLERANCE_MM
        )
        discrepancy = maximum_correspondence_error(legacy, observed)
        assert discrepancy <= bound + transport_tolerance_mm
        reports.append({
            "source": source_path,
            "source_sha256": SOURCE_HASHES[source_path],
            "legacy_vertex_count": len(legacy),
            "maximum_analytical_node_error_mm": numerical_error,
            "maximum_station_correspondence_error_mm": discrepancy,
            "legacy_discretisation_bound_mm": legacy_bound,
            "comparison_bound_mm": bound,
            "legacy_length": _length_evidence(
                legacy, length, radius,
                {
                    "midpoint_integration": legacy_node_error,
                    # Reversing the Exit from its snapped endpoint adds
                    # the endpoint quadrature error to interior nodes.
                    # The sum also bounds the Entry's snapped last node.
                    "endpoint_snap_simpson": endpoint_remainder,
                    "numerical_comparison": NUMERICAL_TOLERANCE_MM,
                },
            ),
        })
    return {
        "case_id": case.case_id,
        "end_name": case.end_name,
        "transition_length_mm": length,
        "radius_mm": radius,
        "output_vertex_count": len(coordinates),
        "b16_chord_error_bound_mm": centreline.chord_error_bound_mm,
        "numerical_tolerance_mm": NUMERICAL_TOLERANCE_MM,
        "maximum_transport_error_mm": transport_error,
        "transport_tolerance_mm": transport_tolerance_mm,
        "output_length": _length_evidence(
            observed, length, radius,
            {
                "simpson_remainder": output_remainder,
                "numerical_comparison": NUMERICAL_TOLERANCE_MM,
                "transport": transport_tolerance_mm,
            },
        ),
        "legacy_comparisons": reports,
    }
