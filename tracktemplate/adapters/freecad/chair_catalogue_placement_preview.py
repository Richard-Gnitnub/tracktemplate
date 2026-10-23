"""Place the retained private P chair without rebuilding its geometry.

The fixed catalogue supplies chair-local model-mm B-reps. Each copied
component receives one outer proper track-frame transform. The source
display rail is accounted for but is not placed as part of the chair.
"""

import json
import math

import Part

from tracktemplate.adapters.freecad.chair_catalogue_preview import (
    _component_colour,
    _import_components,
    _measure_shape,
    _same_presented_shape,
)
from tracktemplate.adapters.freecad.chair_reference_preview import (
    _context_layers,
    _host_placement,
    _materialise_preview,
    _measure_layer,
    _placements,
)
from tracktemplate.application.chair_catalogue import (
    prepare_catalogue_chair,
    verify_catalogue_sources,
)
from tracktemplate.domain.chair_placement import PPlacement


_P_MODEL_SHA256 = (
    "939ddccacbea0605048277a6f207957a31fe76684a039a6c2bd0f41f3bc94ae7"
)
_P_SOURCE_NAMES = (
    "base_plinth", "slide_seat", "outer", "display_rail",
    "SourceFixing", "SourceFixing001", "SourceFixing002", "SourceFixing003",
    "SourceFixing004", "SourceFixing005", "SourceFixing006",
    "SourceFixing007", "SourceFixing008", "SourceFixing009",
    "SourceFixing010", "SourceFixing011", "SourceFixing012",
    "SourceFixing013", "SourceFixing014", "SourceFixing015",
    "SourceFixing016", "SourceFixing017", "SourceFixing018",
)
_DISCRETE_FIELDS = (
    "shape_type", "solid_count", "shell_count", "face_count", "wire_count",
    "edge_count", "vertex_count", "maximum_kernel_tolerance_mm",
    "orientation", "valid", "all_solids_closed",
)


def _require(condition, message):
    if not condition:
        raise ValueError("Private P catalogue placement: " + message)


def _prototype_state(shape):
    """Keep geometry metrics independent of shared display triangulation."""
    measured = _measure_shape(shape)
    # GUI tessellation changes shared face caches. Shape.BoundBox can use
    # those polygons; geometry-based bounds retain the source invariant.
    box = shape.optimalBoundingBox(False, False)
    bounds = (box.XMin, box.YMin, box.ZMin,
              box.XMax, box.YMax, box.ZMax)
    _require(all(math.isfinite(value) for value in bounds),
             "nonfinite geometry-based prototype bounds")
    return dict(measured, bounds_mm=bounds)


def _verify_component(actual, expected):
    """Retain native topology, direction, location and validity."""
    _require(_same_presented_shape(actual, expected),
             "component geometry, orientation or placement changed")
    observed = _measure_shape(actual)
    original = _measure_shape(expected)
    _require(all(observed[key] == original[key]
                 for key in _DISCRETE_FIELDS),
             "component topology or validity changed")
    return observed


def _source_identity(prepared, component):
    return {
        "source_name": component.name,
        "source_label": component.label,
        "source_identity": (prepared.model_sha256, component.name),
    }


def create_private_catalogue_p_preview(
    catalogue_path, placements, context_shapes, source_receipt, verify_source,
):
    """Create one unsaved private P view from confirmed source placements.

    The caller binds proper model-mm frames and copied rail/timber context
    to an unchanged source document. The fixed P/basic-04 catalogue and
    that document are checked again before the single transaction commits.
    Invalid inputs fail before document creation; later failures dispose
    only of this preview. No fit, production or phase acceptance follows.
    """
    if not callable(verify_source):
        raise TypeError("P placement requires source verification")
    placements = _placements(placements, PPlacement)
    receipt = json.loads(json.dumps(source_receipt, allow_nan=False))
    _require(isinstance(receipt, dict), "source receipt must be a mapping")
    prepared = prepare_catalogue_chair(catalogue_path, "P", run="basic-04")
    _require(
        prepared.label == "P" and prepared.run == "basic-04"
        and prepared.context == "fixed-basic-source-context"
        and prepared.model_sha256 == _P_MODEL_SHA256
        and tuple(item.name for item in prepared.components)
        == _P_SOURCE_NAMES,
        "the fixed P catalogue component binding differs",
    )
    components = tuple(item for item in prepared.components
                       if item.name != "display_rail")
    excluded, = (item for item in prepared.components
                 if item.name == "display_rail")
    layer_specs = (
        ("ReferenceRails", "rail context", (0.55, 0.58, 0.62)),
        ("ReferenceTimbers", "timber context", (0.55, 0.40, 0.25)),
    ) + tuple((item.name, item.label, _component_colour(item.label))
              for item in components)

    def prepare_layers():
        all_shapes, all_measurements = _import_components(prepared)
        _require(len(all_shapes) == len(all_measurements)
                 == len(prepared.components),
                 "imported source component count changed")
        admitted = tuple(
            (component, shape, measured)
            for component, shape, measured in zip(
                prepared.components, all_shapes, all_measurements,
            ) if component.name != "display_rail"
        )
        prototypes = tuple(shape for _item, shape, _measured in admitted)
        original_metrics = tuple(_prototype_state(shape)
                                 for shape in prototypes)
        prototype_records = tuple(
            dict(measured, **_source_identity(prepared, component))
            for component, _shape, measured in admitted
        )
        by_component = [[] for _item in components]
        placed_records = []
        for placement in placements:
            rigid = _host_placement(placement)
            measurements = []
            for index, (component, prototype, _measured) in enumerate(
                admitted,
            ):
                # The shallow wrapper shares native geometry, not its location.
                # The B-rep already contains each fitting's local placement.
                shape = Part.Shape(prototype)
                shape.Placement = rigid.multiply(prototype.Placement)
                _require(shape.isPartner(prototype)
                         and shape.Orientation == prototype.Orientation,
                         "rigid placement changed native geometry")
                measured = _measure_shape(shape)
                _require(all(measured[key] == original_metrics[index][key]
                             for key in _DISCRETE_FIELDS),
                         "rigid placement changed component invariants")
                measurements.append(dict(
                    measured, **_source_identity(prepared, component),
                    placement_identity=(placement.position_id,
                                        prepared.model_sha256, component.name),
                ))
                by_component[index].append(shape)
            placed_records.append({
                "position_id": placement.position_id,
                "rail_id": placement.rail_id,
                "timber_id": placement.timber_id,
                "origin_mm": placement.origin_mm,
                "x_axis": placement.x_axis,
                "y_axis": placement.y_axis,
                "components": measurements,
            })
        compounds = []
        for expected in by_component:
            compound = Part.makeCompound(expected)
            _measure_shape(compound)
            children = compound.childShapes()
            _require(len(children) == len(expected),
                     "component compound child count changed")
            for actual, original in zip(children, expected):
                _verify_component(actual, original)
            compounds.append(compound)
        _require(original_metrics == tuple(
            _prototype_state(shape) for shape in prototypes
        ), "placement changed a shared source component")
        layers = _context_layers(context_shapes) + tuple(compounds)
        result = {
            "contract_id": "tracktemplate.private-catalogue-p-placement.v1",
            "label": prepared.label,
            "run": prepared.run,
            "context": prepared.context,
            "catalogue_sha256": prepared.catalogue_sha256,
            "source_model_sha256": prepared.model_sha256,
            "source_model_path": prepared.model_path,
            "source_bindings": [
                {"path": item.path, "sha256": item.sha256}
                for item in prepared.bindings
            ],
            "source_metadata": prepared.metadata,
            "source_limitations": list(prepared.limitations),
            "source_receipt": receipt,
            "components": prototype_records,
            "placements": placed_records,
            "excluded_source_components": [{
                **_source_identity(prepared, excluded),
                "reason": "Source display rail is context, not a chair part.",
            }],
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "length_unit": "mm",
            "length_basis": "model",
            "scale_denominator": "76.2",
            "placement": "outer-proper-planar-frame-on-retained-brep",
            "component_count": len(components),
            "placement_count": len(placements),
            "layer_count": len(layers),
            "solid_count": sum(len(shape.Solids) for shape in compounds),
            "layers": [dict(_measure_layer(shape), name=spec[0])
                       for spec, shape in zip(layer_specs, layers)],
            "geometry_rebuilt": False,
            "track_placements_added": len(placements),
            "limits": [
                "Private fixed-source P placement; no physical-fit "
                "acceptance.",
                "No production, export, persistence or phase acceptance.",
                "Source overlaps and hidden mating closures remain.",
                "No source XML placement, scale or frame conversion "
                "reapplied.",
                "Unresolved key direction and original exclusions remain.",
            ],
        }

        def verify_layers(stored):
            _require(len(stored) == len(layers), "stored layer count changed")
            for index, (actual, expected) in enumerate(zip(stored, layers)):
                _require(_same_presented_shape(actual, expected),
                         "stored layer geometry or placement changed")
                if index < 2:
                    _measure_layer(actual)
                    _require(not actual.Faces and not actual.Solids
                             and len(actual.Edges) == len(expected.Edges),
                             "stored context is no longer the copied wires")
                    continue
                _verify_component(actual, expected)
                children = actual.childShapes()
                originals = by_component[index - 2]
                _require(len(children) == len(originals),
                         "stored component child count changed")
                for child, original in zip(children, originals):
                    _verify_component(child, original)
            _require(original_metrics == tuple(
                _prototype_state(shape) for shape in prototypes
            ), "stored placement changed a shared source component")

        return layers, result, verify_layers

    def verify_inputs():
        verify_source()
        verify_catalogue_sources(prepared)

    return _materialise_preview(
        "P", receipt, layer_specs, prepare_layers, verify_inputs,
        title_suffix="catalogue placements",
    )
