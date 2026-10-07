"""Validate five transient research components in one shared-frame compound.

Component identity survives composition. Pairwise Boolean measurements
describe overlaps; they do not fuse the components, heal geometry or
establish a production-ready connected chair.
"""

import itertools
import math

import FreeCAD as App
import Part

from tracktemplate.adapters.freecad.chair_base_exact import (
    construct_chair_base_shape,
)
from tracktemplate.adapters.freecad.chair_inner_jaw_exact import (
    construct_chair_inner_jaw_shape,
)
from tracktemplate.adapters.freecad.chair_key_exact import (
    construct_chair_key_shape,
)
from tracktemplate.adapters.freecad.chair_outer_jaw_exact import (
    construct_chair_outer_jaw_shape,
)
from tracktemplate.adapters.freecad.chair_seat_exact import (
    KERNEL_TOLERANCE_MM,
    NUMERICAL_LENGTH_TOLERANCE_MM,
    construct_chair_seat_shape,
)
from tracktemplate.application.chair_research import (
    prepare_chair_assembly_research,
    prepare_chair_l1_assembly_research,
)
from tracktemplate.domain.chair_assembly import CHAIR_ASSEMBLY_ROLES


class ChairAssemblyExactGeometryError(RuntimeError):
    """Recoverable exact failure with no document or filesystem mutation."""

    def __init__(self, code, message):
        self.code = code
        self.detail = message
        super().__init__("{}: {}".format(code, message))

    def diagnostic(self):
        """Return a host-neutral diagnostic."""
        return {
            "code": self.code, "message": self.detail, "recoverable": True,
            "document_mutation": False, "filesystem_mutation": False,
        }


def _require(condition, code, message):
    if not condition:
        raise ChairAssemblyExactGeometryError(code, message)


def _bounds(shape):
    box = shape.BoundBox
    return (box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax)


def _construct_components(research, *, l1=False):
    """Construct only after complete package validation has succeeded."""
    builders = (
        construct_chair_base_shape, construct_chair_seat_shape,
        construct_chair_key_shape, construct_chair_outer_jaw_shape,
        construct_chair_inner_jaw_shape,
    )
    shapes = []
    for role, builder, component in zip(
        CHAIR_ASSEMBLY_ROLES, builders, research.components,
    ):
        if l1 and role == "outer-jaw":
            shapes.append(Part.makeCompound([
                builder(geometry) for _name, geometry in component.geometry.parts
            ]))
        else:
            shapes.append(builder(component.geometry))
    return tuple(shapes)


def _measure_component(shape, component, role, *, l1_outer=False, geometry=None):
    geometry = component.geometry if geometry is None else geometry
    solid_count = 3 if l1_outer else 1
    closed = (all(solid.isClosed() for solid in shape.Solids)
              if l1_outer else shape.isClosed())
    _require(
        not shape.isNull()
        and shape.ShapeType == ("Compound" if l1_outer else "Solid")
        and shape.isValid() and closed
        and len(shape.Solids) == len(shape.Shells) == solid_count,
        "invalid-assembly-component", role,
    )
    edges = set()
    for _name, vertices in geometry.faces:
        edges.update(frozenset((a, b)) for a, b in zip(
            vertices, vertices[1:] + vertices[:1],
        ))
    _require(
        (len(shape.Vertexes), len(shape.Edges), len(shape.Faces))
        == (len(geometry.vertices), len(edges), len(geometry.faces)),
        "assembly-component-topology", role,
    )
    kernel_tolerance = shape.getTolerance(1)
    _require(
        math.isfinite(kernel_tolerance)
        and (kernel_tolerance <= KERNEL_TOLERANCE_MM or math.isclose(
            kernel_tolerance, KERNEL_TOLERANCE_MM,
            rel_tol=1.0e-12, abs_tol=0.0,
        )), "assembly-component-tolerance-growth", role,
    )
    unmatched = [tuple(vertex.Point) for vertex in shape.Vertexes]
    residuals = {}
    for name, *point in geometry.vertices:
        expected = tuple(map(float, point))
        closest = min(unmatched, key=lambda p: math.dist(p, expected))
        residual = math.dist(closest, expected)
        _require(
            residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
            "assembly-component-vertex-mismatch", role + ":" + name,
        )
        residuals[name] = residual
        unmatched.remove(closest)
    bounds = _bounds(shape)
    bound_residual = max(abs(a - float(b))
                         for a, b in zip(bounds, geometry.bounds_mm))
    _require(
        bound_residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
        "assembly-component-bounds-mismatch", role,
    )
    expected_volume = float(geometry.volume_mm3)
    volume_budget = max(shape.Area * NUMERICAL_LENGTH_TOLERANCE_MM,
                        expected_volume * 1.0e-12)
    volume_residual = abs(shape.Volume - expected_volume)
    _require(
        math.isfinite(shape.Volume) and shape.Volume > 0
        and math.isfinite(volume_budget) and volume_residual <= volume_budget,
        "assembly-component-volume-mismatch", role,
    )
    measurement = {
        "role": role, "component_id": component.component_id,
        "procedure_id": component.procedure_id, "valid": True, "closed": True,
        "solid_count": solid_count, "shell_count": solid_count,
        "vertex_count": len(shape.Vertexes), "edge_count": len(shape.Edges),
        "face_count": len(shape.Faces), "bounds_mm": bounds,
        "volume_mm3": shape.Volume, "volume_residual_mm3": volume_residual,
        "numerical_volume_budget_mm3": volume_budget,
        "vertex_residuals_mm": residuals,
        "maximum_vertex_residual_mm": max(residuals.values()),
        "maximum_bounds_residual_mm": bound_residual,
        "maximum_kernel_tolerance_mm": kernel_tolerance,
        "face_ids": tuple(name for name, _ids in geometry.faces),
    }
    if l1_outer:
        children = shape.childShapes()
        _require(
            tuple(name for name, _part in geometry.parts)
            == ("body", "bevel-negative", "bevel-positive")
            and len(children) == 3,
            "assembly-l1-outer-parts", "expected three named L1 outer pieces",
        )
        pieces = []
        for child, (name, part) in zip(children, geometry.parts):
            piece = _measure_component(
                child, component, role + ":" + name, geometry=part,
            )
            piece["piece_id"] = name
            pieces.append(piece)
        measurement.update(shape_type="Compound", pieces=pieces)
    return measurement


def _measure_contacts(shapes, components):
    contacts = []
    for left, right in itertools.combinations(range(5), 2):
        a, b = shapes[left], shapes[right]
        distance = a.distToShape(b)[0]
        _require(
            math.isfinite(distance) and distance >= 0,
            "assembly-contact-distance-invalid",
            "pairwise distance must be finite and nonnegative",
        )
        common = a.common(b)
        _require(
            not common.isNull() and common.isValid()
            and math.isfinite(common.Volume) and common.Volume >= 0,
            "assembly-common-invalid",
            "an invalid Boolean result is not evidence of zero overlap",
        )
        volume_budget = max(
            (a.Area + b.Area) * NUMERICAL_LENGTH_TOLERANCE_MM,
            min(a.Volume, b.Volume) * 1.0e-12,
        )
        _require(
            math.isfinite(volume_budget)
            and common.Volume <= min(a.Volume, b.Volume) + volume_budget,
            "assembly-common-volume-invalid",
            "common volume must fit inside both components",
        )
        contacts.append({
            "component_ids": (
                components[left].component_id, components[right].component_id,
            ),
            "distance_mm": distance, "common_volume_mm3": common.Volume,
            "common_solid_count": len(common.Solids),
            "common_face_count": len(common.Faces),
            "numerical_length_budget_mm": NUMERICAL_LENGTH_TOLERANCE_MM,
            "numerical_volume_budget_mm3": volume_budget,
        })
    return contacts


def validate_chair_assembly_exact_geometry(package, manifest_text):
    """Revalidate original inputs and measure a fresh five-solid assembly.

    Full-size mm and the central-key identity placement remain explicit.
    Results contain neutral measurements only; no shape, file, document
    object or cached first construction is kept by this operation.
    """
    research = prepare_chair_assembly_research(package, manifest_text)
    return _validate_research(
        research, "tracktemplate.chair-assembly-exact-research.v1",
    )


def validate_chair_l1_assembly_exact_geometry(package, manifest_text):
    """Measure a freshly constructed, reference-only L1 bounded body.

    The complete original package and manifest pass the finite L1 rules
    before any host construction. The five components remain separate
    in full-size mm. This operation keeps no shape, document or file and
    grants no physical-fit, package or production acceptance.
    """
    research = prepare_chair_l1_assembly_research(package, manifest_text)
    return _validate_research(
        research, "tracktemplate.chair-l1-assembly-exact-research.v1",
        l1=True,
    )


def _validate_research(research, contract_id, *, l1=False):
    """Apply the shared five-component host proof after family validation."""
    package = research.package
    try:
        shapes = (_construct_components(research, l1=True) if l1
                  else _construct_components(research))
        _require(len(shapes) == 5, "assembly-component-count", "expected five")
        components = [
            _measure_component(
                shape, component, role, l1_outer=l1 and role == "outer-jaw",
            )
            for shape, component, role in zip(
                shapes, research.components, CHAIR_ASSEMBLY_ROLES,
            )
        ]
        compound = Part.makeCompound(shapes)
        solid_count = 7 if l1 else 5
        _require(
            not compound.isNull() and compound.ShapeType == "Compound"
            and compound.isValid() and len(compound.Solids) == solid_count,
            "invalid-assembly-compound",
            ("expected seven solids in five named components" if l1
             else "expected five valid named solids"),
        )
        children = compound.childShapes()
        _require(
            len(children) == 5
            and all(child.isSame(shape)
                    for child, shape in zip(children, shapes)),
            "assembly-identity-mismatch",
            "compound children must preserve component identity and order",
        )
        bounds = _bounds(compound)
        residual = max(abs(a - float(b)) for a, b in zip(
            bounds, research.geometry.bounds_mm,
        ))
        _require(
            residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
            "assembly-bounds-mismatch", "compound differs from analytical frame",
        )
        volume_sum = sum(shape.Volume for shape in shapes)
        volume_budget = sum(c["numerical_volume_budget_mm3"] for c in components)
        _require(
            math.isfinite(volume_sum)
            and abs(compound.Volume - volume_sum) <= volume_budget,
            "assembly-volume-mismatch", "compound must preserve component sum",
        )
        contacts = _measure_contacts(shapes, research.components)
        return {
            "contract_id": contract_id,
            "package_signature": package.content_signature,
            "manifest_signature": research.manifest_signature,
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "frame_id": package.to_record()["definition"]["frame"]["frame_id"],
            "length_unit": "mm", "length_basis": "full-size",
            "placement": "central-key-identity",
            "shape_type": "Compound", "component_count": 5,
            "solid_count": solid_count,
            "valid": True, "fused": False, "bounds_mm": bounds,
            "component_volume_sum_mm3": volume_sum,
            "maximum_bounds_residual_mm": residual,
            "numerical_length_budget_mm": NUMERICAL_LENGTH_TOLERANCE_MM,
            "numerical_volume_budget_mm3": volume_budget,
            "landmarks_mm": {
                name: tuple(map(float, point))
                for name, point in research.geometry.landmarks
            },
            "components": components, "contacts": contacts,
            "freecad_version": ".".join(App.Version()[:3]),
            "opencascade_version": Part.OCC_VERSION,
            "document_mutation": False, "filesystem_mutation": False,
        }
    except (Part.OCCError, OverflowError, ValueError) as error:
        raise ChairAssemblyExactGeometryError(
            "assembly-kernel-construction-failed", str(error),
        ) from error
