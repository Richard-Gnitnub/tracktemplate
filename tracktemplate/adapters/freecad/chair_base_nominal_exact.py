"""Construct transient base-plan faces and isolated nominal hole surfaces.

This internal development primitive supplies no chair definition or rail datum.
It creates no document object, file, solid, plinth or production output.
Optional apertures describe one plane, not three-dimensional hole walls.
A separate explicit primitive constructs an open conical wall and tangent
toroidal mouth-round, with no relation to a plan face or chair placement.
The existing numerical checks do not establish a physical fit tolerance.
"""

import math

import FreeCAD as App
import Part

from tracktemplate.adapters.freecad.chair_seat_exact import (
    KERNEL_TOLERANCE_MM,
    NUMERICAL_LENGTH_TOLERANCE_MM,
)
from tracktemplate.domain.chair_base_nominal import (
    ChairBaseNominalArc,
    compute_chair_base_aperture_geometry,
    compute_chair_base_nominal_hole_profile,
    compute_chair_base_nominal_geometry,
)


class ChairBaseNominalExactGeometryError(RuntimeError):
    """Report a recoverable construction failure without external mutation."""

    def __init__(self, code, message):
        self.code = code
        self.detail = message
        super().__init__("{}: {}".format(code, message))

    def diagnostic(self):
        """Return a neutral diagnostic for the explicit validation boundary."""
        return {
            "code": self.code,
            "message": self.detail,
            "recoverable": True,
            "document_mutation": False,
            "filesystem_mutation": False,
        }


def _require(condition, code, message):
    if not condition:
        raise ChairBaseNominalExactGeometryError(code, message)


def _vector(point):
    values = tuple(float(value) for value in point)
    _require(
        all(math.isfinite(value) for value in values),
        "non-finite-host-coordinate", "coordinate is not finite in the host",
    )
    return App.Vector(*values)


def _make_face(geometry):
    """Build ordered straight edges and exact circle arcs without healing."""
    edges = []
    for segment in geometry.segments:
        if isinstance(segment, ChairBaseNominalArc):
            edge = Part.makeCircle(
                float(segment.radius_mm), _vector(segment.centre_mm),
                App.Vector(0, 0, 1), float(segment.start_angle_turns * 360),
                float(segment.end_angle_turns * 360),
            )
        else:
            edge = Part.makeLine(
                _vector(segment.start_mm), _vector(segment.end_mm),
            )
        _require(
            not edge.isNull() and edge.isValid(),
            "invalid-nominal-edge", segment.segment_id,
        )
        edges.append(edge)
    wire = Part.Wire(edges)
    _require(
        wire.isClosed() and wire.isValid(),
        "invalid-nominal-wire", "expected a closed valid gross outline",
    )
    return Part.Face(wire)


def _measure_face(face, geometry):
    """Check the exact boundary against its analytical construction records."""
    epsilon = NUMERICAL_LENGTH_TOLERANCE_MM
    _require(
        not face.isNull() and face.ShapeType == "Face" and face.isValid()
        and (len(face.Vertexes), len(face.Edges), len(face.Wires),
             len(face.Faces), len(face.Shells), len(face.Solids))
        == (8, 8, 1, 1, 0, 0) and face.OuterWire.isClosed(),
        "unexpected-nominal-topology",
        "expected eight edges in one planar face with no solid",
    )
    _require(
        isinstance(face.Surface, Part.Plane)
        and math.dist(tuple(face.normalAt(0, 0)), (0, 0, 1)) <= epsilon,
        "nominal-face-orientation", "expected a plane with positive Z normal",
    )
    tolerance = face.getTolerance(1)
    _require(
        tolerance <= KERNEL_TOLERANCE_MM or math.isclose(
            tolerance, KERNEL_TOLERANCE_MM, rel_tol=1e-12, abs_tol=0,
        ),
        "nominal-tolerance-growth",
        "kernel tolerance grew during construction",
    )
    unmatched = list(face.Edges)
    edge_measurements = []
    matched_edges = []
    for segment in geometry.segments:
        start = tuple(map(float, segment.start_mm))
        end = tuple(map(float, segment.end_mm))
        candidates = [edge for edge in unmatched if (
            math.dist(tuple(edge.valueAt(edge.FirstParameter)), start)
            <= epsilon
            and math.dist(tuple(edge.valueAt(edge.LastParameter)), end)
            <= epsilon
        )]
        _require(
            len(candidates) == 1, "nominal-edge-endpoint-mismatch",
            segment.segment_id,
        )
        edge = candidates[0]
        unmatched.remove(edge)
        matched_edges.append(edge)
        residual = max(
            math.dist(tuple(edge.valueAt(edge.FirstParameter)), start),
            math.dist(tuple(edge.valueAt(edge.LastParameter)), end),
        )
        if isinstance(segment, ChairBaseNominalArc):
            _require(
                isinstance(edge.Curve, Part.Circle),
                "nominal-curve-kind-mismatch", segment.segment_id,
            )
            radius = float(segment.radius_mm)
            expected_length = math.pi * radius / 2
            _require(
                abs(edge.Curve.Radius - radius) <= epsilon
                and math.dist(tuple(edge.Curve.Center), tuple(map(
                    float, segment.centre_mm,
                ))) <= epsilon
                and abs(edge.Length - expected_length) <= epsilon,
                "nominal-circle-mismatch", segment.segment_id,
            )
            kind = "circle"
        else:
            _require(
                isinstance(edge.Curve, Part.Line),
                "nominal-curve-kind-mismatch", segment.segment_id,
            )
            _require(
                abs(edge.Length - math.dist(start, end)) <= epsilon,
                "nominal-line-length-mismatch", segment.segment_id,
            )
            kind = "line"
        edge_measurements.append({
            "segment_id": segment.segment_id, "curve_kind": kind,
            "length_mm": edge.Length, "endpoint_residual_mm": residual,
        })
    for index, edge in enumerate(matched_edges):
        following = matched_edges[(index + 1) % len(matched_edges)]
        # Unit tangent agreement is tested as a positional difference over
        # one millimetre, using the existing numerical length check.
        _require(
            math.dist(tuple(edge.tangentAt(edge.LastParameter)), tuple(
                following.tangentAt(following.FirstParameter),
            )) <= epsilon,
            "nominal-tangent-mismatch", geometry.segments[index].segment_id,
        )
    box = face.BoundBox
    bounds = (box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax)
    residual = max(
        abs(a - float(b)) for a, b in zip(bounds, geometry.bounds_mm)
    )
    _require(
        residual <= epsilon, "nominal-bounds-mismatch",
        "native bounds differ from the nominal plan",
    )
    expected_area = (float(geometry.area_constant_mm2)
                     + math.pi * float(geometry.area_pi_coefficient_mm2))
    expected_perimeter = (
        float(geometry.perimeter_constant_mm)
        + math.pi * float(geometry.perimeter_pi_coefficient_mm)
    )
    area_budget = max(face.Length * epsilon, abs(expected_area) * 1e-12)
    _require(
        math.isfinite(expected_area) and math.isfinite(face.Area)
        and face.Area > 0 and math.isfinite(area_budget)
        and abs(face.Area - expected_area) <= area_budget,
        "nominal-area-mismatch",
        "native area differs from the analytical plan",
    )
    _require(
        math.isfinite(expected_perimeter) and math.isfinite(face.Length)
        and abs(face.Length - expected_perimeter) <= len(face.Edges) * epsilon,
        "nominal-perimeter-mismatch",
        "native perimeter differs from the analytical plan",
    )
    return {
        "frame_id": "geometric-base-plan-centre",
        "length_unit": "mm", "length_basis": "full-size",
        "freecad_version": ".".join(App.Version()[:3]),
        "opencascade_version": Part.OCC_VERSION,
        "vertex_count": 8, "edge_count": 8, "wire_count": 1,
        "face_count": 1, "solid_count": 0, "shell_count": 0,
        "valid": True, "closed": True, "normal": (0.0, 0.0, 1.0),
        "bounds_mm": bounds, "area_mm2": face.Area,
        "perimeter_mm": face.Length, "edges": edge_measurements,
        "maximum_bounds_residual_mm": residual,
        "numerical_length_budget_mm": epsilon,
        "numerical_area_budget_mm2": area_budget,
        "maximum_kernel_tolerance_mm": tolerance,
        "production_geometry_authorized": False,
        "document_mutation": False, "filesystem_mutation": False,
    }


def _construct_and_measure(parameters):
    geometry = compute_chair_base_nominal_geometry(parameters)
    try:
        face = _make_face(geometry)
        return face, _measure_face(face, geometry)
    except (Part.OCCError, OverflowError, ValueError) as error:
        raise ChairBaseNominalExactGeometryError(
            "nominal-kernel-construction-failed", str(error),
        ) from error


def construct_chair_base_nominal_face(parameters):
    """Validate explicit lengths and return one transient, checked plan face.

    This adapter helper is not a production package or output admission route.
    The caller owns its input provenance and any later display or disposal.
    """
    face, _measurements = _construct_and_measure(parameters)
    return face


def validate_chair_base_nominal_exact_geometry(parameters):
    """Construct a fresh face and return neutral numerical measurements."""
    _face, measurements = _construct_and_measure(parameters)
    return measurements


def _make_aperture_face(geometry):
    """Add clockwise circular inner wires to the gross outline plane."""
    gross = _make_face(geometry.outline)
    wires = [gross.OuterWire]
    for aperture in geometry.apertures:
        edge = Part.makeCircle(
            float(aperture.radius_mm), _vector(aperture.centre_mm),
            App.Vector(0, 0, 1),
        )
        wire = Part.Wire([edge])
        wire.reverse()
        _require(
            wire.isClosed() and wire.isValid(),
            "invalid-aperture-wire", aperture.aperture_id,
        )
        wires.append(wire)
    return Part.Face(wires)


def _measure_aperture_face(face, geometry):
    """Check the outer boundary, each aperture and the net planar region."""
    epsilon = NUMERICAL_LENGTH_TOLERANCE_MM
    count = len(geometry.apertures)
    _require(
        not face.isNull() and face.ShapeType == "Face" and face.isValid()
        and (len(face.Vertexes), len(face.Edges), len(face.Wires),
             len(face.Faces), len(face.Shells), len(face.Solids))
        == (8 + count, 8 + count, 1 + count, 1, 0, 0)
        and all(wire.isClosed() for wire in face.Wires),
        "unexpected-aperture-topology",
        "expected one face with an outer wire and separate circular holes",
    )
    _require(
        isinstance(face.Surface, Part.Plane)
        and math.dist(tuple(face.normalAt(0, 0)), (0, 0, 1)) <= epsilon,
        "aperture-face-orientation", "expected a plane with positive Z normal",
    )
    measurements = _measure_face(Part.Face(face.OuterWire), geometry.outline)
    tolerance = face.getTolerance(1)
    _require(
        tolerance <= KERNEL_TOLERANCE_MM or math.isclose(
            tolerance, KERNEL_TOLERANCE_MM, rel_tol=1e-12, abs_tol=0,
        ),
        "aperture-tolerance-growth", "kernel tolerance grew at an aperture",
    )
    unmatched = [wire for wire in face.Wires
                 if not wire.isSame(face.OuterWire)]
    aperture_measurements = []
    for aperture in geometry.apertures:
        centre = tuple(map(float, aperture.centre_mm))
        radius = float(aperture.radius_mm)
        candidates = [wire for wire in unmatched if (
            len(wire.Edges) == 1
            and isinstance(wire.Edges[0].Curve, Part.Circle)
            and math.dist(tuple(wire.Edges[0].Curve.Center), centre)
            <= epsilon
        )]
        _require(
            len(candidates) == 1, "aperture-centre-mismatch",
            aperture.aperture_id,
        )
        wire = candidates[0]
        unmatched.remove(wire)
        edge = wire.Edges[0]
        _require(
            wire.Orientation == "Reversed"
            and abs(edge.Curve.Radius - radius) <= epsilon
            and abs(edge.Length - 2 * math.pi * radius) <= epsilon
            and math.dist(tuple(edge.Curve.Axis), (0, 0, 1)) <= epsilon
            and not face.isInside(_vector(aperture.centre_mm), epsilon, True),
            "aperture-circle-mismatch", aperture.aperture_id,
        )
        aperture_measurements.append({
            "aperture_id": aperture.aperture_id,
            "centre_mm": tuple(edge.Curve.Center),
            "radius_mm": edge.Curve.Radius, "perimeter_mm": edge.Length,
        })
    expected_area = (float(geometry.area_constant_mm2)
                     + math.pi * float(geometry.area_pi_coefficient_mm2))
    expected_perimeter = (
        float(geometry.perimeter_constant_mm)
        + math.pi * float(geometry.perimeter_pi_coefficient_mm)
    )
    area_budget = max(face.Length * epsilon, abs(expected_area) * 1e-12)
    _require(
        math.isfinite(expected_area) and math.isfinite(face.Area)
        and face.Area > 0 and math.isfinite(area_budget)
        and abs(face.Area - expected_area) <= area_budget,
        "aperture-area-mismatch", "native net area differs from the plan",
    )
    _require(
        math.isfinite(expected_perimeter) and math.isfinite(face.Length)
        and abs(face.Length - expected_perimeter)
        <= len(face.Edges) * epsilon,
        "aperture-perimeter-mismatch",
        "native perimeter differs from the plan with apertures",
    )
    measurements.update({
        "vertex_count": 8 + count, "edge_count": 8 + count,
        "wire_count": 1 + count, "aperture_count": count,
        "apertures": aperture_measurements, "area_mm2": face.Area,
        "perimeter_mm": face.Length, "numerical_area_budget_mm2": area_budget,
        "maximum_kernel_tolerance_mm": tolerance,
    })
    return measurements


def _construct_apertures_and_measure(parameters, apertures):
    geometry = compute_chair_base_aperture_geometry(parameters, apertures)
    try:
        face = _make_aperture_face(geometry)
        return face, _measure_aperture_face(face, geometry)
    except (Part.OCCError, OverflowError, ValueError) as error:
        raise ChairBaseNominalExactGeometryError(
            "aperture-kernel-construction-failed", str(error),
        ) from error


def construct_chair_base_aperture_face(parameters, apertures):
    """Return one checked plan face with explicit circular apertures.

    Input positions use the existing geometric frame. The caller owns
    provenance and the represented plane; this supplies no hole walls,
    placement in a chair, physical fit or production admission.
    """
    face, _measurements = _construct_apertures_and_measure(parameters, apertures)
    return face


def validate_chair_base_aperture_exact_geometry(parameters, apertures):
    """Construct a fresh aperture face and return neutral measurements."""
    _face, measurements = _construct_apertures_and_measure(parameters, apertures)
    return measurements


def _make_hole_shell(profile):
    """Revolve one connected open meridian, without sewing or healing."""
    wall = Part.makeLine(_vector(profile.lower_mm),
                         _vector(profile.tangent_mm))
    rounding = Part.Arc(
        _vector(profile.tangent_mm), _vector(profile.round_midpoint_mm),
        _vector(profile.mouth_mm),
    ).toShape()
    wire = Part.Wire([wall, rounding])
    _require(
        not wire.isNull() and wire.isValid() and not wire.isClosed(),
        "invalid-hole-meridian", "expected a connected open meridian",
    )
    shell = wire.revolve(App.Vector(), App.Vector(0, 0, 1), 360)
    # The lower-to-upper meridian revolves with outward/downward normals.
    # Reverse the whole shell to face into the bore and upwards at its lip.
    shell.reverse()
    return shell


def _measure_hole_shell(shell, profile):
    """Check surface identities, connected topology and nominal geometry."""
    epsilon = NUMERICAL_LENGTH_TOLERANCE_MM
    _require(
        not shell.isNull() and shell.ShapeType == "Shell" and shell.isValid()
        and not shell.isClosed()
        and (len(shell.Vertexes), len(shell.Edges), len(shell.Wires),
             len(shell.Faces), len(shell.Shells), len(shell.Solids))
        == (3, 5, 2, 2, 1, 0),
        "unexpected-hole-topology", "expected one open two-face shell",
    )
    cones = [face for face in shell.Faces
             if isinstance(face.Surface, Part.Cone)]
    tori = [face for face in shell.Faces
            if isinstance(face.Surface, Part.Toroid)]
    _require(
        len(cones) == len(tori) == 1, "hole-surface-kind-mismatch",
        "expected one conical wall and one toroidal mouth-round",
    )
    wall, rounding = cones[0], tori[0]
    p = profile.parameters
    r0, mouth, height, radius = (
        float(getattr(p, name)) for name in (
            "lower_radius_mm", "mouth_radius_mm", "top_height_mm",
            "round_radius_mm",
        )
    )
    slope, secant = float(profile.wall_slope), float(profile.wall_secant)
    tr, _y, tz = map(float, profile.tangent_mm)
    centre_z = float(profile.round_centre_mm[2])
    cone, torus = wall.Surface, rounding.Surface
    _require(
        math.dist(tuple(cone.Center), (0, 0, 0)) <= epsilon
        and math.dist(tuple(cone.Axis), (0, 0, 1)) <= epsilon
        and abs(cone.Radius - r0) <= epsilon
        and abs(math.tan(cone.SemiAngle) - slope) <= epsilon
        and math.dist(tuple(torus.Center), (0, 0, centre_z)) <= epsilon
        and min(math.dist(tuple(torus.Axis), axis)
                for axis in ((0, 0, 1), (0, 0, -1))) <= epsilon
        and abs(torus.MajorRadius - mouth) <= epsilon
        and abs(torus.MinorRadius - radius) <= epsilon,
        "hole-surface-dimensions-mismatch",
        "native cone or torus differs from the analytical section",
    )
    # Axis-aligned circles identify the two open boundaries and the one
    # shared junction. The other two edges are periodic meridian seams.
    rings = [edge for edge in shell.Edges if (
        isinstance(edge.Curve, Part.Circle)
        and abs(abs(edge.Curve.Axis.z) - 1) <= epsilon
    )]
    _require(len(rings) == 3, "hole-ring-count-mismatch",
             "expected three coaxial circular edges")
    ring_measurements = []
    for identity, expected_radius, z, owners in (
        ("lower", r0, 0.0, (wall,)),
        ("wall-round-junction", tr, tz, (wall, rounding)),
        ("mouth", mouth, height, (rounding,)),
    ):
        matches = [edge for edge in rings if math.dist(
            tuple(edge.Curve.Center), (0, 0, z),
        ) <= epsilon]
        _require(len(matches) == 1, "hole-ring-position-mismatch", identity)
        edge = matches[0]
        rings.remove(edge)
        attached = [face for face in shell.Faces
                    if any(edge.isSame(other) for other in face.Edges)]
        _require(
            abs(edge.Curve.Radius - expected_radius) <= epsilon
            and abs(edge.Length - 2*math.pi*expected_radius) <= epsilon
            and len(attached) == len(owners)
            and all(any(face.isSame(owner) for face in attached)
                    for owner in owners),
            "hole-ring-connectivity-mismatch", identity,
        )
        ring_measurements.append({
            "boundary_id": identity, "radius_mm": edge.Curve.Radius,
            "height_mm": edge.Curve.Center.z,
            "attached_face_count": len(attached),
        })

    maximum_surface_residual = 0.0
    maximum_normal_residual = 0.0
    for face, points in (
        (wall, (profile.lower_mm, profile.tangent_mm)),
        (rounding, (profile.tangent_mm, profile.round_midpoint_mm,
                    profile.mouth_mm)),
    ):
        for point in points:
            r, _y, z = map(float, point)
            if face.isSame(wall):
                radial_normal, normal_z = -1/secant, slope/secant
            else:
                radial_normal = (r-mouth)/radius
                normal_z = (z-centre_z)/radius
            for angle in (0.0, math.pi/2, math.pi, 3*math.pi/2):
                c, s = math.cos(angle), math.sin(angle)
                expected = (r*c, r*s, z)
                u, v = face.Surface.parameter(App.Vector(*expected))
                maximum_surface_residual = max(
                    maximum_surface_residual,
                    math.dist(tuple(face.valueAt(u, v)), expected),
                )
                maximum_normal_residual = max(
                    maximum_normal_residual,
                    math.dist(tuple(face.normalAt(u, v)),
                              (radial_normal*c, radial_normal*s, normal_z)),
                )
    _require(
        maximum_surface_residual <= epsilon
        and maximum_normal_residual <= epsilon,
        "hole-surface-or-normal-mismatch",
        "expected tangent bore-facing surfaces and a positive Z mouth normal",
    )
    # Standard BoundBox can conservatively enclose a trimmed torus. Ask
    # the kernel for its exact-surface bounds, without mesh or tolerance.
    box = shell.optimalBoundingBox(False, False)
    bounds = (box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax)
    bounds_residual = max(abs(a-b) for a, b in zip(
        bounds, (-mouth, -mouth, 0, mouth, mouth, height),
    ))
    _require(bounds_residual <= epsilon, "hole-bounds-mismatch",
             "native bounds differ from the analytical section")
    alpha = math.atan2(1, slope)
    expected_areas = (
        math.pi*(r0+tr)*math.hypot(tr-r0, tz),
        2*math.pi*radius*(mouth*alpha - radius*(1-slope/secant)),
    )
    face_measurements = []
    for identity, kind, face, expected in zip(
        ("wall", "mouth-round"), ("cone", "torus"),
        (wall, rounding), expected_areas,
    ):
        area_budget = max(face.Length*epsilon, abs(expected)*1e-12)
        _require(
            math.isfinite(face.Area) and face.Area > 0
            and math.isfinite(expected) and math.isfinite(area_budget)
            and abs(face.Area-expected) <= area_budget,
            "hole-area-mismatch", identity,
        )
        face_measurements.append({
            "surface_id": identity, "surface_kind": kind,
            "area_mm2": face.Area, "numerical_area_budget_mm2": area_budget,
        })
    tolerance = shell.getTolerance(1)
    _require(
        tolerance <= KERNEL_TOLERANCE_MM or math.isclose(
            tolerance, KERNEL_TOLERANCE_MM, rel_tol=1e-12, abs_tol=0,
        ),
        "hole-tolerance-growth", "kernel tolerance grew during construction",
    )
    return {
        "frame_id": "geometric-hole-axis-underside",
        "length_unit": "mm", "length_basis": "full-size",
        "mouth_radius_semantics": "actual-rounded-opening",
        "freecad_version": ".".join(App.Version()[:3]),
        "opencascade_version": Part.OCC_VERSION,
        "vertex_count": 3, "edge_count": 5, "wire_count": 2,
        "face_count": 2, "shell_count": 1, "solid_count": 0,
        "valid": True, "closed": False, "normal_side": "into-bore",
        "bounds_mm": bounds, "area_mm2": shell.Area,
        "faces": face_measurements, "rings": ring_measurements,
        "wall_slope": slope, "wall_secant": secant,
        "maximum_surface_residual_mm": maximum_surface_residual,
        "maximum_normal_residual": maximum_normal_residual,
        "maximum_bounds_residual_mm": bounds_residual,
        "numerical_length_budget_mm": epsilon,
        "maximum_kernel_tolerance_mm": tolerance,
        "production_geometry_authorized": False,
        "document_mutation": False, "filesystem_mutation": False,
    }


def _construct_hole_and_measure(parameters):
    profile = compute_chair_base_nominal_hole_profile(parameters)
    try:
        shell = _make_hole_shell(profile)
        return shell, _measure_hole_shell(shell, profile)
    except (Part.OCCError, OverflowError, ValueError) as error:
        raise ChairBaseNominalExactGeometryError(
            "hole-kernel-construction-failed", str(error),
        ) from error


def construct_chair_base_nominal_hole_shell(parameters):
    """Return checked transient wall and round surfaces, without caps.

    This isolated primitive creates no document object or outer chair
    geometry. The caller owns provenance, placement and later disposal.
    """
    shell, _measurements = _construct_hole_and_measure(parameters)
    return shell


def validate_chair_base_nominal_hole_exact_geometry(parameters):
    """Construct a fresh hole shell and return neutral measurements."""
    _shell, measurements = _construct_hole_and_measure(parameters)
    return measurements
