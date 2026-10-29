"""Inspect four separate private P-chair solids in their shared frame.

Existing component constructors supply the base, slide-seat, jaw spacer
and jaw body. Composition preserves each solid without Boolean work,
healing, document mutation, placement or a physical-fit claim.
"""

from dataclasses import replace
import math

import FreeCAD as App
import Part

from tracktemplate.adapters.freecad.chair_assembly_exact import (
    ChairAssemblyExactGeometryError,
    _bounds,
    _measure_component,
)
from tracktemplate.adapters.freecad.chair_base_exact import (
    ChairBaseExactGeometryError,
    construct_chair_base_shape,
)
from tracktemplate.adapters.freecad.chair_p_outer_jaw_exact import (
    ChairPOuterJawExactGeometryError,
    construct_chair_p_outer_jaw_shapes,
)
from tracktemplate.adapters.freecad.chair_p_seat_exact import (
    ChairPSeatExactGeometryError,
    construct_chair_p_seat_shape,
)
from tracktemplate.adapters.freecad.chair_seat_exact import (
    NUMERICAL_LENGTH_TOLERANCE_MM,
)
from tracktemplate.application.chair_research import (
    prepare_chair_p_assembly_research,
)
from tracktemplate.domain.chair_base import construct_chair_base
from tracktemplate.domain.chair_p_assembly import (
    CHAIR_P_ASSEMBLY_ROLES,
    ChairPAssemblyGeometry,
    assemble_p_chair_components,
)
from tracktemplate.domain.chair_p_outer_jaw import (
    construct_chair_p_outer_jaw,
)
from tracktemplate.domain.chair_p_seat import construct_chair_p_seat


_SOLID_IDS = (
    "base-plinth", "rail-seat", "outer-jaw:spacer", "outer-jaw:body",
)


class ChairPAssemblyExactGeometryError(RuntimeError):
    """Recoverable native refusal without document or file mutation."""

    def __init__(self, code, message):
        self.code = code
        self.detail = message
        super().__init__("{}: {}".format(code, message))

    def diagnostic(self):
        """Return the neutral failure boundary."""
        return {
            "code": self.code, "message": self.detail,
            "recoverable": True, "document_mutation": False,
            "filesystem_mutation": False,
        }


def _require(condition, code, message):
    if not condition:
        raise ChairPAssemblyExactGeometryError(code, message)


def construct_chair_p_assembly_shapes(geometry):
    """Recheck analytical boundaries, then return four named native solids.

    This composition helper requires an authorised research caller. It
    does not admit a package. All three component geometries and their
    shared-frame constraints are reconstructed before the first host
    shape is made. Forged or stale dataclasses cannot bypass those checks.
    """
    if not isinstance(geometry, ChairPAssemblyGeometry):
        raise TypeError("geometry must be ChairPAssemblyGeometry")
    try:
        reconstructed = assemble_p_chair_components(
            geometry.components,
            table_centre_from_inner_end_mm=(
                geometry.table_centre_from_inner_end_mm
            ),
        )
        builders = (construct_chair_base, construct_chair_p_seat,
                    construct_chair_p_outer_jaw)
        for (_role, component), builder in zip(geometry.components, builders):
            _require(
                builder(replace(component.parameters)) == component,
                "p-assembly-boundary-mismatch",
                "component differs from its parameters",
            )
        _require(
            reconstructed == geometry, "p-assembly-boundary-mismatch",
            "assembly differs from its components and shared parameters",
        )
    except (TypeError, ValueError, AttributeError) as error:
        raise ChairPAssemblyExactGeometryError(
            "p-assembly-boundary-invalid", str(error),
        ) from error
    try:
        base, seat, jaw = (component for _role, component
                           in geometry.components)
        base_shape = construct_chair_base_shape(base)
        seat_shape = construct_chair_p_seat_shape(seat)
        jaw_shapes = construct_chair_p_outer_jaw_shapes(jaw)
        _require(
            tuple(name for name, _shape in jaw_shapes) == ("spacer", "body"),
            "p-assembly-jaw-identity", "expected spacer then body",
        )
        return (
            ("base-plinth", base_shape),
            ("rail-seat", seat_shape),
            *(("outer-jaw:" + name, shape) for name, shape in jaw_shapes),
        )
    except (ChairBaseExactGeometryError, ChairPSeatExactGeometryError,
            ChairPOuterJawExactGeometryError, Part.OCCError,
            OverflowError, ValueError) as error:
        raise ChairPAssemblyExactGeometryError(
            "p-assembly-kernel-construction-failed", str(error),
        ) from error


def validate_chair_p_assembly_exact_geometry(package, manifest_text):
    """Reprepare original private inputs and inspect a four-solid compound.

    Full-size millimetres and identity placement in the chair frame apply.
    Every call constructs disposable shapes. The result contains neutral
    measurements only. Component volume sums are not Boolean-union volume
    or evidence of physical fit. No document or output file is created.
    """
    research = prepare_chair_p_assembly_research(package, manifest_text)
    geometry = research.geometry
    try:
        named_shapes = construct_chair_p_assembly_shapes(geometry)
        _require(
            tuple(name for name, _shape in named_shapes) == _SOLID_IDS,
            "p-assembly-solid-identities", "expected four ordered solids",
        )
        base, seat, jaw = research.components
        part_inputs = (
            (base, CHAIR_P_ASSEMBLY_ROLES[0], base.geometry),
            (seat, CHAIR_P_ASSEMBLY_ROLES[1], seat.geometry),
            *((jaw, "outer-jaw", boundary)
              for _name, boundary in jaw.geometry.parts),
        )
        parts = []
        for (solid_id, shape), (component, role, boundary) in zip(
            named_shapes, part_inputs,
        ):
            measurement = _measure_component(
                shape, component, role, geometry=boundary,
            )
            measurement["solid_id"] = solid_id
            parts.append(measurement)
        shapes = tuple(shape for _name, shape in named_shapes)
        compound = Part.makeCompound(shapes)
        _require(
            not compound.isNull() and compound.ShapeType == "Compound"
            and compound.isValid()
            and len(compound.Solids) == len(compound.Shells) == 4,
            "invalid-p-assembly-compound", "expected four separate solids",
        )
        children = compound.childShapes()
        _require(
            len(children) == 4
            and all(child.isSame(shape)
                    for child, shape in zip(children, shapes)),
            "p-assembly-child-identities", "compound changed its children",
        )
        bounds = _bounds(compound)
        residual = max(abs(actual - float(expected))
                       for actual, expected in zip(bounds, geometry.bounds_mm))
        _require(
            all(math.isfinite(value) for value in bounds)
            and residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
            "p-assembly-bounds-mismatch", "compound differs from chair frame",
        )
        volume_sum = sum(part["volume_mm3"] for part in parts)
        volume_budget = sum(part["numerical_volume_budget_mm3"]
                            for part in parts)
        analytical_sum = float(geometry.component_volume_sum_mm3)
        _require(
            math.isfinite(compound.Volume) and math.isfinite(volume_sum)
            and math.isfinite(analytical_sum) and math.isfinite(volume_budget)
            and abs(compound.Volume - volume_sum) <= volume_budget
            and abs(volume_sum - analytical_sum) <= volume_budget,
            "p-assembly-volume-sum-mismatch",
            "compound must preserve the separate component volume sum",
        )
        return {
            "contract_id": "tracktemplate.chair-p-assembly-exact-research.v1",
            "package_signature": package.content_signature,
            "manifest_signature": research.manifest_signature,
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "frame_id": package.to_record()["definition"]["frame"]["frame_id"],
            "length_unit": "mm", "length_basis": "full-size",
            "placement": "chair-frame-identity",
            "freecad_version": ".".join(App.Version()[:3]),
            "opencascade_version": Part.OCC_VERSION,
            "shape_type": "Compound", "solid_count": 4, "shell_count": 4,
            "component_count": 3, "parts": parts,
            "valid": True, "closed": True, "bounds_mm": bounds,
            "component_volume_sum_mm3": volume_sum,
            "maximum_bounds_residual_mm": residual,
            "numerical_volume_budget_mm3": volume_budget,
            "landmarks_mm": {name: tuple(float(value) for value in point)
                             for name, point in geometry.landmarks},
            "numerical_length_budget_mm": NUMERICAL_LENGTH_TOLERANCE_MM,
            "maximum_kernel_tolerance_mm": max(
                part["maximum_kernel_tolerance_mm"] for part in parts
            ),
            "document_mutation": False, "filesystem_mutation": False,
        }
    except ChairAssemblyExactGeometryError as error:
        raise ChairPAssemblyExactGeometryError(
            "p-" + error.code, error.detail,
        ) from error
    except (Part.OCCError, OverflowError, ValueError) as error:
        raise ChairPAssemblyExactGeometryError(
            "p-assembly-kernel-construction-failed", str(error),
        ) from error
