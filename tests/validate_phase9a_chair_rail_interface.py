#!/usr/bin/env python3
"""Prove rail-interface consistency with invented, signed chair inputs.

These planes describe the finite research source construction. The tests
establish no physical rail fit or manufacturing acceptance tolerance.
"""

import copy
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
import hashlib
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from tracktemplate.application import (  # noqa: E402
    chair_definition as definitions,
    chair_model_research,
    chair_rail_research,
    chair_research,
)
from tracktemplate.domain.chair_rail_interface import (  # noqa: E402
    prove_chair_rail_interface,
)
import validate_phase9a_chair_assembly as assembly_tests  # noqa: E402
from validate_phase9a_chair_model_scale import (  # noqa: E402
    LENGTH_FACTOR,
    REQUEST,
    assert_diagnostic,
    request_rejections,
)
from validate_phase9a_chair_seat import (  # noqa: E402
    canonical_json,
    resign_package,
)


SENTINEL = "Phase 9A chair rail interface standalone validation passed"
MISMATCH = "research-rail-interface-inconsistent"
# Derived before reading the new proof: rail top Z=32; web depths 6.5,
# 13.5; fish ratio=2; half-web=1 and half-foot=4, all lengths in mm.
# Each plane obeys a*x+b*y+c*z=offset; residuals are not distances.
EXPECTED_PLANES = {
    "rail-bottom": ((0, 0, 1), Fraction(8)),
    "field-web": ((0, 1, 0), Fraction(1)),
    "field-under-head": ((0, Fraction(-1, 2), 1), Fraction(51, 2)),
    "field-foot-upper": ((0, Fraction(1, 2), 1), Fraction(37, 2)),
    "gauge-web": ((0, 1, 0), Fraction(-1)),
    "gauge-under-head": ((0, Fraction(1, 2), 1), Fraction(51, 2)),
    "gauge-foot-upper": ((0, Fraction(-1, 2), 1), Fraction(37, 2)),
    "gauge-foot-side": ((0, 1, 0), Fraction(-4)),
}
EXPECTED_RELATIONS = (
    ("seat-bottom", "rail-seat", "seat-top", "rail-bottom"),
    ("key-web", "key", "web-pad", "field-web"),
    ("key-under-head", "key", "top-pad", "field-under-head"),
    ("key-foot", "key", "bottom-pad", "field-foot-upper"),
    ("inner-web-upper", "inner-jaw", "grip-back-upper", "gauge-web"),
    ("inner-web-lower", "inner-jaw", "grip-back-lower", "gauge-web"),
    ("inner-foot", "inner-jaw", "grip-bottom", "gauge-foot-upper"),
    ("inner-under-head-edge", "inner-jaw", None, "gauge-under-head"),
    ("inner-foot-side", "inner-jaw", "lower-mid-to-seat-00",
     "gauge-foot-side"),
)
# Hand-calculated vertices, independent of either production constructor
# or interface proof. Inner widths: 7+(24-25)/8, 7+(24-22)/8,
# 7+(24-18)/8, 8+(18-16.5)/5. X reverses in the source frame.
EXPECTED_POINTS = {
    "rail-seat": {
        "top-gauge-negative": (-10, -4, 8),
        "top-gauge-positive": (10, -4, 8),
        "top-foot-positive": (10, 4, 8),
        "top-foot-negative": (-10, 4, 8),
        "top-outer-positive": (3, 9, 8),
        "top-outer-negative": (-3, 9, 8),
    },
    "key": {
        "negative-pad-web-top": (-3, 1, 26),
        "positive-pad-web-top": (3, 1, 26),
        "negative-pad-web-bottom": (-3, 1, 18),
        "positive-pad-web-bottom": (3, 1, 18),
        "negative-pad-apex": (-3, 3, 27),
        "positive-pad-apex": (3, 3, 27),
        "negative-pad-toe": (-3, 3, 17),
        "positive-pad-toe": (3, 3, 17),
    },
    "inner-jaw": {
        "grip-negative-top-web": (Fraction(-55, 8), -1, 26),
        "grip-positive-top-web": (Fraction(55, 8), -1, 26),
        "grip-negative-stand-web": (Fraction(-29, 4), -1, 22),
        "grip-positive-stand-web": (Fraction(29, 4), -1, 22),
        "grip-negative-upper-mid-web": (Fraction(-31, 4), -1, 18),
        "grip-positive-upper-mid-web": (Fraction(31, 4), -1, 18),
        "lower-mid-01": (Fraction(-83, 10), -4, Fraction(33, 2)),
        "lower-mid-00": (Fraction(83, 10), -4, Fraction(33, 2)),
        "seat-01": (-9, -4, 8),
        "seat-00": (9, -4, 8),
    },
}


def _rational(value):
    """Keep rational chord coordinates exact; refuse discarded radicals."""
    if hasattr(value, "coefficients"):
        assert not any(value.coefficients[1:])
        return value.coefficients[0]
    return Fraction(value)


def _clip_polygon(points, normal, offset):
    """Clip to a closed half-space with rational crossing denominators."""
    if not points:
        return ()
    result = []
    for a, b in zip(points, points[1:] + points[:1]):
        da, db = (sum(n * v for n, v in zip(normal, p)) - offset
                  for p in (a, b))
        if da <= 0:
            result.append(a)
        if (da < 0 < db) or (db < 0 < da):
            weight = da / _rational(da - db)
            result.append(tuple(x + weight * (y - x)
                                for x, y in zip(a, b)))
    return tuple(result)


def _area_squared(points):
    """Square the polygon vector area without square-root rounding."""
    vector = [Fraction(0)] * 3
    for a, b in zip(points, points[1:] + points[:1]):
        for axis in range(3):
            j, k = (axis + 1) % 3, (axis + 2) % 3
            vector[axis] += (a[j] * b[k] - a[k] * b[j]) / 2
    return _rational(sum(value * value for value in vector))


def finite_contact_measurements(assembly, profile):
    """Measure finite research contacts in full-size mm, never fit limits.

    The rail is a longitudinal prism spanning the complete assembly.
    Fishing surfaces and the bottom are finite transverse segments.
    A top-corner cut only removes material above these contact regions.
    No source values or measured stock data are embedded here. These
    predicates establish no physical acceptance.
    """
    geometries = dict(assembly.components)
    vertices = {role: {name: (x, y, z) for name, x, y, z in g.vertices}
                for role, g in geometries.items()}

    def face(role, name):
        ids = dict(geometries[role].faces)[name]
        return tuple(vertices[role][identity] for identity in ids)

    p = profile
    seat = p.seat_thickness_mm
    foot, head, web = (width / 2 for width in (
        p.rail_foot_width_mm, p.rail_head_width_mm, p.rail_web_width_mm,
    ))
    slope = 1 / p.rail_fish_ratio
    top = seat + p.rail_depth_mm - p.rail_web_top_depth_mm
    bottom = seat + p.rail_depth_mm - p.rail_web_bottom_depth_mm
    planes = {
        "seat-bottom": ((0, 0, 1), seat, -foot, foot),
        "inner-web-upper": ((0, 1, 0), -web, -web, -web),
        "inner-web-lower": ((0, 1, 0), -web, -web, -web),
        "inner-foot": ((0, -slope, 1), bottom, -foot, -web),
        "inner-foot-side": ((0, 1, 0), -foot, -foot, -foot),
    }
    names = (
        ("seat-bottom", "rail-seat", "seat-top"),
        ("inner-web-upper", "inner-jaw", "grip-back-upper"),
        ("inner-web-lower", "inner-jaw", "grip-back-lower"),
        ("inner-foot", "inner-jaw", "grip-bottom"),
        ("inner-foot-side", "inner-jaw", "lower-mid-to-seat-00"),
    )
    points = {}
    for identity, role, name in names:
        normal, offset, low, high = planes[identity]
        polygon = face(role, name)
        assert all(sum(a * v for a, v in zip(normal, point)) == offset
                   for point in polygon), identity
        polygon = _clip_polygon(polygon, (0, -1, 0), -low)
        points[identity] = _clip_polygon(polygon, (0, 1, 0), high)
    for name, _ids in geometries["key"].faces:
        polygon = face("key", name)
        for normal, offset, low, high in (
            ((0, 1, 0), web, web, web),
            ((0, -slope, 1), top, web, head),
            ((0, slope, 1), bottom, web, foot),
        ):
            if all(sum(a * v for a, v in zip(normal, point)) == offset
                   for point in polygon):
                clipped = _clip_polygon(polygon, (0, -1, 0), -low)
                clipped = _clip_polygon(clipped, (0, 1, 0), high)
                if _area_squared(clipped):
                    points[name] = clipped
    grip = face("inner-jaw", "grip-top")
    gaps = tuple(top - slope * y - z for _x, y, z in grip)
    assert min(gaps) == 0 and max(gaps) > 0
    edge = tuple(point for point, gap in zip(grip, gaps) if gap == 0)
    assert len(edge) == 2
    key = tuple(vertices["key"].values())
    key_residuals = tuple((y - web, top + slope * y - z,
                          z - bottom + slope * y) for _x, y, z in key)
    assert all(min(row) >= 0 for row in key_residuals)
    # The convex key lies wholly in the rail cavity. For the concave
    # inner jaw, clip EVERY boundary face into the rail's Z bands.
    # Each band has one linear gauge-side limit, not a vertex-only test.
    upper_web, lower_web = top + slope * web, bottom - slope * web
    bands = (
        (seat, bottom - slope * foot, 0, -foot),
        (bottom - slope * foot, lower_web,
         -p.rail_fish_ratio, -p.rail_fish_ratio * bottom),
        (lower_web, upper_web, 0, -web),
        (upper_web, top + slope * head,
         p.rail_fish_ratio, p.rail_fish_ratio * top),
        (top + slope * head, seat + p.rail_depth_mm, 0, -head),
    )
    for name, _ids in geometries["inner-jaw"].faces:
        for low, high, z_coefficient, offset in bands:
            clipped = _clip_polygon(face("inner-jaw", name),
                                    (0, 0, -1), -low)
            clipped = _clip_polygon(clipped, (0, 0, 1), high)
            assert all(y + z_coefficient * z <= offset
                       for _x, y, z in clipped), name
    assert max(z for _x, _y, z in vertices["rail-seat"].values()) == seat
    assert max(z for _x, _y, z in vertices["base-plinth"].values()) < seat
    assert min(y for _x, y, _z in vertices["outer-jaw"].values()) > max(
        head, foot,
    )
    taper = tuple(vertices["key"][end + "-web-top"]
                  for end in ("negative-end", "positive-end"))
    web_gap = max(y - web for _x, y, _z in taper)
    fish_gap = max(top + slope * y - z for _x, y, z in taper)
    return {
        "area_squared_mm4": {name: _area_squared(polygon)
                             for name, polygon in points.items()},
        "points_mm": points,
        "seat_top_area_squared_mm4": _area_squared(face(
            "rail-seat", "seat-top",
        )),
        "under_head_edge_length_squared_mm2": _rational(sum(
            (a - b) * (a - b) for a, b in zip(*edge)
        )),
        "under_head_max_vertical_gap_mm": _rational(max(gaps)),
        "under_head_contact_area_squared_mm4": Fraction(0),
        "key_clearance": {
            "web_max_mm": web_gap,
            "fish_residual_max_mm": fish_gap,
            "fish_normal_max_squared_mm2": fish_gap ** 2 / (1 + slope ** 2),
        },
        "key_nonpenetration": True,
        "rail_nonpenetration": True,
    }


def assert_finite_contacts(result):
    """Compare invented trapezoids/rectangles with independent areas."""
    measured = finite_contact_measurements(
        result.model_research.full_size_research.geometry,
        result.proof.profile,
    )
    n = result.proof.profile.rail_fish_ratio
    # Invented lengths: seat 20 by 8; web heights 4+4, widths
    # 55/4, 29/2 and 31/2; foot width in Y=3. The lower grip
    # half-width is 8+3/(5*n). No constructor output supplies these.
    foot_width = Fraction(189, 4) + Fraction(9, 5) / n
    foot_side = (17 + Fraction(3, 5) / n) * (10 - 3 / n)
    expected = {
        "seat-bottom": Fraction(160 ** 2),
        "inner-web-upper": Fraction(113, 2) ** 2,
        "inner-web-lower": Fraction(60 ** 2),
        "inner-foot": foot_width ** 2 * (1 + 1 / n ** 2),
        "inner-foot-side": foot_side ** 2,
        "web-pad": Fraction(48 ** 2),
        # Key pad 6 by 2; each end triangle has projected area 7.
        "top-pad": 144 * (1 + 1 / n ** 2),
        "bottom-pad": 144 * (1 + 1 / n ** 2),
        **{side + "-" + level + "-ridge": 49 * (1 + 1 / n ** 2)
           for side in ("negative", "positive")
           for level in ("top", "bottom")},
    }
    assert measured["area_squared_mm4"] == expected
    assert measured["seat_top_area_squared_mm4"] == 225 ** 2
    assert measured["under_head_edge_length_squared_mm2"] == (
        Fraction(55, 4) ** 2
    )
    assert measured["under_head_max_vertical_gap_mm"] == Fraction(3, 2) / n
    assert measured["under_head_contact_area_squared_mm4"] == 0
    assert measured["key_clearance"] == {
        "web_max_mm": 1, "fish_residual_max_mm": 1 / n,
        "fish_normal_max_squared_mm2": 1 / (n ** 2 + 1),
    }
    return measured


def validate_finite_mutations(result):
    """Plane-coincident mutations must fail the stronger finite checks."""
    original = result.model_research.full_size_research.geometry
    expected = assert_finite_contacts(result)
    for mutation in ("short-seat", "end-in-rail", "top-area", "lost-ridge"):
        components = []
        for role, geometry in original.components:
            points = []
            for identity, x, y, z in geometry.vertices:
                if mutation == "short-seat" and role == "rail-seat":
                    x /= 2
                if (mutation == "end-in-rail" and role == "key"
                        and identity == "positive-end-web-top"):
                    y = Fraction(1, 2)
                if (mutation == "top-area" and role == "inner-jaw"
                        and identity.endswith("-top-front")):
                    z = Fraction(51, 2) - y / 2
                points.append((identity, x, y, z))
            faces = geometry.faces
            if mutation == "lost-ridge" and role == "key":
                faces = tuple((name, ids) for name, ids in faces
                              if name != "positive-top-ridge")
            components.append((role, replace(
                geometry, vertices=tuple(points), faces=faces,
            )))
        changed = replace(original, components=tuple(components))
        # These changes escape all nine existing rail-plane equalities.
        prove_chair_rail_interface(changed, Fraction(381, 5))
        try:
            observed = finite_contact_measurements(
                changed, result.proof.profile,
            )
            assert observed == expected
        except AssertionError:
            pass
        else:
            raise AssertionError(mutation + ": finite regression escaped")


def change_quantity(record, role, purpose, value):
    """Change one invented canonical quantity with its matching source."""
    identity = "quantity:test:{}:{}".format(role, purpose)
    quantity = next(item for item in record["definition"]["quantities"]
                    if item["quantity_id"] == identity)
    quantity["source_value"] = quantity["canonical_value"] = value


def synthetic_rail_package_records(ratio="2"):
    """Keep old fixtures unchanged; declare a coherent new mock source."""
    record, manifest = assembly_tests.synthetic_assembly_package_records()
    # Three hand-solvable profiles share top=18 and bottom=10 above seat.
    top, bottom, foot = {
        "1": ("7", "13", "7"),
        "2": ("6.5", "13.5", "8.5"),
        "4": ("6.25", "13.75", "9.25"),
    }[ratio]
    for role, purpose, value in (
        ("key", "rail_web_top_depth_mm", top),
        ("key", "rail_web_bottom_depth_mm", bottom),
        ("key", "rail_fish_ratio", ratio),
        ("inner-jaw", "rail_foot_depth_mm", foot),
    ):
        change_quantity(record, role, purpose, value)
    quantities = {q["quantity_id"]: q
                  for q in record["definition"]["quantities"]}
    digests = {}
    for dependency in manifest["dependencies"]:
        suffix = dependency["identifier"].removeprefix("dependency:test:")
        quantity = quantities.get("quantity:test:" + suffix)
        value = quantity["source_value"] if quantity else "context"
        description = "Invented rail-interface source: {}={}".format(
            suffix, value,
        )
        digest = hashlib.sha256(description.encode("utf-8")).hexdigest()
        dependency["name"] = description
        dependency["source"].update({
            "creator_or_supplier": "TrackTemplate synthetic rail test",
            "locator": "synthetic-test-double://chair-rail/" + suffix,
            "evidence_sha256": digest,
        })
        dependency["contribution_attestation"]["reference"] = (
            "Invented metadata in "
            "tests/validate_phase9a_chair_rail_interface.py"
        )
        digests[suffix] = digest
    for lineage in record["lineage"]:
        suffix = lineage["lineage_id"].removeprefix("lineage:test:")
        lineage["source_file_sha256s"] = [digests[suffix]]
    return resign_package(record, manifest), manifest


def load_package(record, manifest):
    """Load original neutral bytes, preserving the complete manifest."""
    text = canonical_json(manifest)
    return definitions.chair_definition_package_from_json(
        canonical_json(record), text,
    ), text


def assert_proof(result, exact_points=True):
    """Check planes, named points, residuals, identities and projection."""
    proof, model = result.proof, result.model_research
    assert proof.scale_denominator == Fraction(381, 5)
    profile = proof.profile
    assert profile.rail_depth_mm == 24
    assert profile.rail_head_width_mm == 6
    assert profile.rail_foot_width_mm == 8
    assert profile.rail_web_width_mm == 2
    assert profile.seat_thickness_mm == 8
    assert profile.rail_web_face_top_from_rail_bottom_mm == 18
    assert profile.rail_web_face_bottom_from_rail_bottom_mm == 10
    assert tuple((r.relation_id, r.component_role, r.face_id, r.plane_id)
                 for r in proof.relations) == EXPECTED_RELATIONS
    geometries = dict(model.full_size_research.geometry.components)
    observed = 0
    for relation in proof.relations:
        geometry = geometries[relation.component_role]
        vertices = {name: point for name, *point in geometry.vertices}
        if relation.face_id is None:
            assert relation.vertex_ids == (
                "grip-negative-top-web", "grip-positive-top-web",
            )
        else:
            assert relation.vertex_ids == dict(geometry.faces)[
                relation.face_id
            ]
        assert relation.points_mm == tuple(
            tuple(vertices[name]) for name in relation.vertex_ids
        )
        assert len(relation.points_mm) == len(relation.residuals_mm)
        assert relation.residuals_mm == (Fraction(0),) * len(
            relation.points_mm,
        )
        assert relation.model_residuals_mm == relation.residuals_mm
        assert relation.model_plane_offset_mm == (
            relation.plane_offset_mm * LENGTH_FACTOR
        )
        assert relation.model_points_mm == tuple(
            tuple(v * LENGTH_FACTOR for v in point)
            for point in relation.points_mm
        )
        if exact_points:
            assert (relation.plane_coefficients,
                    relation.plane_offset_mm) == EXPECTED_PLANES[
                        relation.plane_id
                    ]
            for name, point in zip(relation.vertex_ids, relation.points_mm):
                assert point == EXPECTED_POINTS[
                    relation.component_role
                ][name], name
                observed += 1
        for point in relation.points_mm:
            assert sum(a * v for a, v in zip(
                relation.plane_coefficients, point,
            )) == relation.plane_offset_mm
    if exact_points:
        assert profile.rail_fish_ratio == 2
        assert profile.rail_web_top_depth_mm == Fraction(13, 2)
        assert profile.rail_web_bottom_depth_mm == Fraction(27, 2)
        assert profile.rail_foot_depth_mm == Fraction(17, 2)
        assert observed == 36


def mismatch_cases(record, manifest):
    """Small signed disagreements still pass the former assembly path."""
    for purpose, value in (
        ("rail_web_face_top_from_rail_bottom_mm", "18.001"),
        ("rail_web_face_bottom_from_rail_bottom_mm", "10.001"),
        ("rail_foot_depth_mm", "8.501"),
        # This difference is far below the existing native numeric budget.
        ("rail_web_face_top_from_rail_bottom_mm", "18.000000000000001"),
    ):
        bad, related = copy.deepcopy((record, manifest))
        change_quantity(bad, "inner-jaw", purpose, value)
        resign_package(bad, related)
        yield purpose + "=" + value, bad, related


def validate_rejections(record, manifest, package, text):
    """Preserve inherited rejections and reject exact cross-input drift."""
    for name, bad, related in mismatch_cases(record, manifest):
        retained = copy.deepcopy((bad, related))
        other, other_text = load_package(bad, related)
        # Regression witness: former assembly and model paths still accept.
        old = chair_research.prepare_chair_assembly_research(other, other_text)
        assert len(old.components) == 5
        assert len(chair_model_research.prepare_chair_model_research(
            other, other_text, REQUEST,
        ).components) == 5
        try:
            chair_rail_research.prepare_chair_rail_research(
                other, other_text, REQUEST,
            )
        except chair_rail_research.ChairRailResearchError as error:
            assert_diagnostic(error, MISMATCH)
        else:
            raise AssertionError(name + ": signed mismatch accepted")
        assert (bad, related) == retained
    for name, request, code in request_rejections():
        try:
            chair_rail_research.prepare_chair_rail_research(
                package, text, request,
            )
        except definitions.ChairDefinitionError as error:
            assert_diagnostic(error, code)
        else:
            raise AssertionError(name + ": invalid model request accepted")
    corrupt = copy.deepcopy(record)
    corrupt["definition"]["description"] += " Unsigned corruption."
    unsupported = copy.deepcopy(record)
    unsupported["schema_version"] = 2
    resign_package(unsupported, manifest)
    for bad, code in (
        (corrupt, "content-signature-mismatch"),
        (unsupported, "unsupported-schema-version"),
    ):
        try:
            other, other_text = load_package(bad, manifest)
            chair_rail_research.prepare_chair_rail_research(
                other, other_text, REQUEST,
            )
        except definitions.ChairDefinitionError as error:
            assert_diagnostic(error, code)
        else:
            raise AssertionError(code + ": invalid package accepted")
    for name, bad, related in assembly_tests._mutations(record, manifest):
        resign_package(bad, related)
        try:
            other, other_text = load_package(bad, related)
            chair_rail_research.prepare_chair_rail_research(
                other, other_text, REQUEST,
            )
        except definitions.ChairDefinitionError as error:
            assert_diagnostic(
                error, assembly_tests.EXPECTED_REJECTION_CODES[name],
            )
        else:
            raise AssertionError(name + ": invalid signed package accepted")


def validate_exact_residuals(full_size):
    """A valid-looking boundary displaced below float precision must fail."""
    for role, identity, axis in (
        ("rail-seat", "top-foot-positive", 2),
        ("key", "positive-pad-web-top", 1),
        ("inner-jaw", "grip-positive-top-web", 2),
    ):
        components = []
        for component_role, geometry in full_size.geometry.components:
            if component_role == role:
                points = []
                for name, *point in geometry.vertices:
                    if name == identity:
                        point[axis] += Fraction(1, 10 ** 30)
                    points.append((name, *point))
                geometry = replace(geometry, vertices=tuple(points))
            components.append((component_role, geometry))
        changed = replace(full_size.geometry, components=tuple(components))
        try:
            prove_chair_rail_interface(changed, Fraction(381, 5))
        except ValueError:
            pass
        else:
            raise AssertionError(identity + ": nonzero exact residual passed")


def validate_rail_interface():
    record, manifest = synthetic_rail_package_records()
    retained = copy.deepcopy((record, manifest))
    package, text = load_package(record, manifest)
    encoded = definitions.chair_definition_package_to_json(package)
    previous = chair_model_research.prepare_chair_model_research(
        package, text, REQUEST,
    )
    result = chair_rail_research.prepare_chair_rail_research(
        package, text, REQUEST,
    )
    assert result.model_research == previous
    assert result.model_research.package is package
    assert_proof(result)
    assert_finite_contacts(result)
    validate_finite_mutations(result)
    try:
        result.proof.scale_denominator = Fraction(1)
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("rail proof is mutable")
    reopened = definitions.chair_definition_package_from_json(encoded, text)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("rail proof read a source file")

    with patch("builtins.open", forbidden), patch.object(Path, "open", forbidden):
        repeated = chair_rail_research.prepare_chair_rail_research(
            reopened, text, dict(reversed(tuple(REQUEST.items()))),
        )
    assert repeated == result
    assert definitions.chair_definition_package_to_json(reopened) == encoded
    assert reopened.content_signature == package.content_signature
    assert package.to_record() == record
    assert package.project_status == "reference-only"
    assert package.acceptance_status == "not-accepted"
    assert definitions.chair_definition_package_status(
        package, text,
    )["production_geometry_authorized"] is False
    validate_rejections(record, manifest, package, text)
    validate_exact_residuals(previous.full_size_research)
    for ratio, expected_foot in (("1", 7), ("4", Fraction(37, 4))):
        other_record, other_manifest = synthetic_rail_package_records(ratio)
        other, other_text = load_package(other_record, other_manifest)
        variant = chair_rail_research.prepare_chair_rail_research(
            other, other_text, REQUEST,
        )
        assert_proof(variant, exact_points=False)
        assert_finite_contacts(variant)
        assert variant.proof.profile.rail_fish_ratio == Fraction(ratio)
        assert variant.proof.profile.rail_foot_depth_mm == expected_foot
        assert variant.model_research.request_signature != (
            result.model_research.request_signature
        )
    assert (record, manifest) == retained


def main():
    validate_rail_interface()
    print(SENTINEL)


if __name__ == "__main__":
    main()
