"""Validate finite S1 and L1 model comparisons in transient FreeCAD solids.

Fresh named boundaries come from the projected analytical result. Full-size
canonical inputs remain unchanged. This path has no document, persistence,
manufacturing, export or production-acceptance side effect.
"""

import json
import math

import FreeCAD as App
import Part

from tracktemplate.adapters.freecad.chair_assembly_exact import (
    ChairAssemblyExactGeometryError,
    _bounds,
    _measure_component,
    _measure_contacts,
)
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
    NUMERICAL_LENGTH_TOLERANCE_MM,
    construct_chair_seat_shape,
)
from tracktemplate.application.chair_model_research import (
    prepare_chair_l1_model_research,
    prepare_chair_model_research,
)
from tracktemplate.domain.chair_assembly import CHAIR_ASSEMBLY_ROLES


class ChairModelExactGeometryError(ChairAssemblyExactGeometryError):
    """Recoverable model comparison failure without mutation."""


def _require(condition, code, message):
    if not condition:
        raise ChairModelExactGeometryError(code, message)


def _construct_components(model, *, l1=False):
    """Build fresh model boundaries after complete input validation."""
    builders = (
        construct_chair_base_shape, construct_chair_seat_shape,
        construct_chair_key_shape, construct_chair_outer_jaw_shape,
        construct_chair_inner_jaw_shape,
    )
    shapes = []
    for role, builder, component in zip(
        CHAIR_ASSEMBLY_ROLES, builders, model.components,
    ):
        if l1 and role == "outer-jaw":
            shapes.append(Part.makeCompound([
                builder(geometry) for _name, geometry in component.geometry.parts
            ]))
        else:
            shapes.append(builder(component.geometry))
    return tuple(shapes)


def validate_chair_model_exact_geometry(package, manifest_text, request):
    """Measure the explicit 4 mm/ft comparison about the same chair origin.

    The unchanged full-size preparation validates the original package first.
    The model request then controls exact analytical projection. Existing
    assembly numerical guards also apply in model millimetres; they are not
    physical fit limits or accepted Templot comparison tolerances. Results
    contain neutral measurements only. No first construction is retained.
    """
    model = prepare_chair_model_research(package, manifest_text, request)
    return _validate_model(
        model, "tracktemplate.chair-model-scale-exact-research.v1",
    )


def validate_chair_l1_model_exact_geometry(package, manifest_text, request):
    """Measure seven L1 model solids grouped in five named components.

    Revalidate the original full-size package and explicit model request
    before host construction. Keep all three outer-jaw parts separate.
    Return neutral measurements without document or file mutation, fit,
    package, source-scale fidelity or production acceptance.
    """
    model = prepare_chair_l1_model_research(package, manifest_text, request)
    return _validate_model(
        model, "tracktemplate.chair-l1-model-scale-exact-research.v1", l1=True,
    )


def _validate_model(model, contract_id, *, l1=False):
    """Apply existing numerical guards after finite family preparation."""
    package = model.package
    try:
        shapes = (_construct_components(model, l1=True) if l1
                  else _construct_components(model))
        _require(len(shapes) == 5, "assembly-component-count", "expected five")
        components = [
            _measure_component(
                shape, component, role, l1_outer=l1 and role == "outer-jaw",
            )
            for shape, component, role in zip(
                shapes, model.components, CHAIR_ASSEMBLY_ROLES,
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
            bounds, model.geometry.bounds_mm,
        ))
        _require(
            residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
            "assembly-bounds-mismatch", "compound differs from model frame",
        )
        volume_sum = sum(shape.Volume for shape in shapes)
        volume_budget = sum(c["numerical_volume_budget_mm3"] for c in components)
        _require(
            math.isfinite(volume_sum)
            and abs(compound.Volume - volume_sum) <= volume_budget,
            "assembly-volume-mismatch", "compound must preserve component sum",
        )
        contacts = _measure_contacts(shapes, model.components)
        scale_request = json.loads(model.request_json)
        return {
            "contract_id": contract_id,
            "package_signature": package.content_signature,
            "manifest_signature": model.manifest_signature,
            "request_signature": model.request_signature,
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "source_frame_id": scale_request["source_frame_id"],
            "frame_id": scale_request["source_frame_id"],
            "source_origin": scale_request["origin_datum"],
            "length_unit": "mm", "length_basis": "model",
            "source_length_basis": "full-size",
            "scale_denominator": scale_request["scale_denominator"],
            "placement": "same-chair-origin-and-axes-central-key",
            "manufacturing_compensation_applied": False,
            "shape_type": "Compound", "component_count": 5,
            "solid_count": solid_count,
            "valid": True, "fused": False, "bounds_mm": bounds,
            "component_volume_sum_mm3": volume_sum,
            "maximum_bounds_residual_mm": residual,
            "numerical_length_budget_mm": NUMERICAL_LENGTH_TOLERANCE_MM,
            "numerical_volume_budget_mm3": volume_budget,
            "landmarks_mm": {
                name: tuple(map(float, point))
                for name, point in model.geometry.landmarks
            },
            "components": components, "contacts": contacts,
            "freecad_version": ".".join(App.Version()[:3]),
            "opencascade_version": Part.OCC_VERSION,
            "document_mutation": False, "filesystem_mutation": False,
        }
    except ChairModelExactGeometryError:
        raise
    except ChairAssemblyExactGeometryError as error:
        raise ChairModelExactGeometryError(error.code, error.detail) from error
    except (Part.OCCError, OverflowError, ValueError) as error:
        raise ChairModelExactGeometryError(
            "research-model-kernel-construction-failed", str(error),
        ) from error
