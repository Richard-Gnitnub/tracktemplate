"""Inspect retained private chair components without rebuilding geometry.

Only named B-reps from the verified catalogue are read. No FCStd document,
Python proxy, macro or external builder is restored or executed. Imported
shapes keep their source placements and remain disposable reference views.
"""

import math

import FreeCAD as App
import Part

from tracktemplate.adapters.freecad.chair_reference_preview import (
    _materialise_preview,
)
from tracktemplate.application.chair_catalogue import (
    prepare_catalogue_chair,
    verify_catalogue_sources,
)


# Native recompute can round placement coefficients.
# This bounds representation roundoff, not railway or manufacturing fit.
_PLACEMENT_SERIALISATION_ROUNDOFF = 1.0e-14


def _require(condition, message):
    if not condition:
        raise ValueError("Private chair catalogue preview: " + message)


def _solid_parts(shape):
    """Reject free topology while retaining every nested solid component."""
    if shape.ShapeType == "Solid":
        return (shape,)
    _require(shape.ShapeType == "Compound", "unsupported component shape")
    children = shape.childShapes()
    _require(bool(children), "empty component compound")
    return tuple(part for child in children for part in _solid_parts(child))


def _measure_shape(shape, *, full_check=False):
    """Measure the complete source component without repair or healing."""
    _require(not shape.isNull() and shape.isValid(), "invalid component")
    solids = _solid_parts(shape)
    _require(len(solids) == len(shape.Solids), "incomplete solid coverage")
    for solid in solids:
        if full_check:
            solid.check(True)
        _require(solid.isValid() and solid.isClosed()
                 and math.isfinite(solid.Volume) and solid.Volume > 0,
                 "component contains invalid or open solid material")
    box = shape.BoundBox
    bounds = (box.XMin, box.YMin, box.ZMin,
              box.XMax, box.YMax, box.ZMax)
    values = (*bounds, shape.Volume, shape.Area, shape.Length,
              shape.getTolerance(1), *shape.Placement.toMatrix().A)
    _require(all(math.isfinite(value) for value in values),
             "nonfinite component measurement")
    return {
        "shape_type": shape.ShapeType,
        "solid_count": len(shape.Solids),
        "shell_count": len(shape.Shells),
        "face_count": len(shape.Faces),
        "wire_count": len(shape.Wires),
        "edge_count": len(shape.Edges),
        "vertex_count": len(shape.Vertexes),
        "bounds_mm": bounds,
        "volume_mm3": shape.Volume,
        "area_mm2": shape.Area,
        "edge_length_mm": shape.Length,
        "maximum_kernel_tolerance_mm": shape.getTolerance(1),
        "placement_matrix": tuple(shape.Placement.toMatrix().A),
        "orientation": shape.Orientation,
        "valid": True,
        "all_solids_closed": True,
    }


def _import_component(component):
    """Read the saved native placement exactly once from its B-rep."""
    shape = Part.Shape()
    shape.importBrepFromString(component.brep_text)
    _require(not shape.isNull(), "source B-rep is empty")
    values = component.xml_placement
    placement = App.Placement(
        App.Vector(*values[:3]), App.Rotation(*values[3:]),
    )
    residual = max(abs(actual - expected) for actual, expected in zip(
        shape.Placement.toMatrix().A, placement.toMatrix().A,
    ))
    _require(math.isfinite(residual), "nonfinite placement comparison")
    # The hash-bound archives retain distinct XML object placements and B-rep
    # locations. Native restoration preserves both; they need not be identical.
    # Keep the XML value and its residual as evidence, not as a replacement.
    # Assigning the XML Placement again would move positioned fixings twice.
    measured = _measure_shape(shape, full_check=True)
    return shape, dict(measured, xml_placement=values,
                       xml_placement_matrix_residual=residual)


def _same_presented_shape(actual, expected):
    """Allow equivalent native locations, retaining geometry and direction."""
    actual_matrix = actual.Placement.toMatrix().A
    expected_matrix = expected.Placement.toMatrix().A
    return (
        actual.isPartner(expected)
        and actual.Orientation == expected.Orientation
        and all(math.isfinite(value)
                for value in (*actual_matrix, *expected_matrix))
        and max(abs(a - b) for a, b in zip(actual_matrix, expected_matrix))
        <= _PLACEMENT_SERIALISATION_ROUNDOFF
    )


def _import_components(prepared):
    """Return ordered detached shapes and their complete import metrics."""
    imported = tuple(_import_component(component)
                     for component in prepared.components)
    return (
        tuple(shape for shape, _measured in imported),
        tuple(measured for _shape, measured in imported),
    )


def _component_colour(label):
    """Distinguish reference parts visually without assigning identity."""
    text = label.casefold()
    if "display-rail" in text or "display-check-rail" in text:
        return (0.55, 0.58, 0.62)
    if "key" in text:
        return (0.90, 0.70, 0.20)
    if any(word in text for word in ("screw", "bolt", "nut", "washer")):
        return (0.65, 0.67, 0.70)
    if "base-plinth" in text:
        return (0.70, 0.45, 0.20)
    if "seat" in text:
        return (0.35, 0.65, 0.85)
    if "inner" in text:
        return (0.75, 0.40, 0.65)
    return (0.35, 0.70, 0.45)


def create_private_catalogue_preview(catalogue_path, label, *, run=None):
    """Create one unsaved, undoable view of a verified catalogue model.

    All named parts, source placements and context remain unchanged. The
    source and prior documents are preserved. Invalid input fails before
    document creation; later failure removes only this owned preview.
    No geometry is regenerated, placed on track or admitted for production.
    """
    prepared = prepare_catalogue_chair(catalogue_path, label, run=run)
    components = prepared.components
    names = tuple(component.name for component in components)
    _require(bool(names) and len(set(names)) == len(names),
             "component identities are empty or repeated")
    layer_specs = tuple(
        (component.name, component.label, _component_colour(component.label))
        for component in components
    )

    def prepare_layers():
        layers, measurements = _import_components(prepared)
        measured = tuple(dict(
            metrics, source_name=component.name,
            source_label=component.label,
            source_identity=(prepared.model_sha256, component.name),
        ) for component, metrics in zip(components, measurements))
        result = {
            "contract_id": "tracktemplate.private-chair-catalogue-preview.v1",
            "label": prepared.label,
            "run": prepared.run,
            "context": prepared.context,
            "catalogue_sha256": prepared.catalogue_sha256,
            "source_model_sha256": prepared.model_sha256,
            "source_model_path": prepared.model_path,
            "source_bindings": [
                {"path": binding.path, "sha256": binding.sha256}
                for binding in prepared.bindings
            ],
            "source_metadata": prepared.metadata,
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "length_unit": "mm",
            "length_basis": "model",
            "scale_denominator": "76.2",
            "placement": "unchanged-retained-model-coordinates",
            "component_count": len(components),
            "layer_count": len(layers),
            "solid_count": sum(item["solid_count"] for item in measured),
            "components": measured,
            "geometry_rebuilt": False,
            "track_placements_added": 0,
            "limits": [
                *prepared.limitations,
                "Private catalogue inspection; no production or export authority.",
                "Derived snapshot; no canonical definition or live regeneration.",
                "Saved XML placements remain separate from native B-rep locations.",
                "No track placement, physical-fit or phase acceptance.",
            ],
        }

        def verify_layers(stored):
            _require(len(stored) == len(layers),
                     "stored component count changed")
            for actual, expected in zip(stored, layers):
                _require(_same_presented_shape(actual, expected),
                         "stored component geometry or placement changed")
                observed = _measure_shape(actual)
                original = _measure_shape(expected)
                # Shared native topology fixes local geometry. Recompute may
                # round its outer rotation, so derived floating measurements
                # need not be bit-identical. Keep every discrete invariant.
                fields = (
                    "shape_type", "solid_count", "shell_count", "face_count",
                    "wire_count", "edge_count", "vertex_count",
                    "maximum_kernel_tolerance_mm", "orientation", "valid",
                    "all_solids_closed",
                )
                _require(all(observed[key] == original[key] for key in fields),
                         "stored component topology or validity changed")

        return layers, result, verify_layers

    return _materialise_preview(
        prepared.label,
        {"coverage_summary": prepared.run + "; reference only"},
        layer_specs,
        prepare_layers,
        lambda: verify_catalogue_sources(prepared),
        title_suffix="catalogue inspection",
    )
