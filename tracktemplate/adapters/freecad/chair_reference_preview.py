"""Materialise private chair reference previews in isolated documents.

Validated model components remain separate, centrally keyed and
reference-only. Display layers have no production/export tags, live source
binding, stored schema or automatic regeneration behaviour.
"""

from copy import deepcopy
from dataclasses import replace
import json
import math
import uuid

import FreeCAD as App
import Part

from tracktemplate.adapters.freecad.chair_assembly_exact import (
    _bounds,
    _measure_component,
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
from tracktemplate.adapters.freecad.chair_model_exact import (
    _construct_components,
)
from tracktemplate.adapters.freecad.chair_outer_jaw_exact import (
    construct_chair_outer_jaw_shape,
)
from tracktemplate.adapters.freecad.chair_seat_exact import (
    NUMERICAL_LENGTH_TOLERANCE_MM,
    construct_chair_seat_shape,
)
from tracktemplate.adapters.freecad.core_export_document import (
    _active_document,
    _cleanup,
    _preselection_snapshot,
    _restore_preselection,
    _restore_selection,
    _same_registry,
    _selection_snapshot,
)
from tracktemplate.application.chair_model_research import (
    prepare_chair_l1_model_research,
    prepare_chair_model_research,
    prepare_chair_s1j_model_research,
)
from tracktemplate.domain.chair_assembly import CHAIR_ASSEMBLY_ROLES
from tracktemplate.domain.chair_placement import S1Placement, S1JPlacement


_LAYERS = (
    ("ReferenceRails", "rail context", (0.65, 0.65, 0.65)),
    ("ReferenceTimbers", "timber context", (0.55, 0.40, 0.25)),
    ("S1BasePlinth", "base/plinth", (0.70, 0.45, 0.20)),
    ("S1RailSeat", "rail seat", (0.35, 0.65, 0.85)),
    ("S1CentralKey", "central key", (0.95, 0.80, 0.20)),
    ("S1OuterJaw", "outer jaw", (0.35, 0.70, 0.45)),
    ("S1InnerJaw", "inner jaw", (0.75, 0.40, 0.65)),
)


def _require(condition, message):
    if not condition:
        raise RuntimeError("S1 reference preview: " + message)


def _placements(values, placement_type=S1Placement):
    """Revalidate caller records without trusting a frozen instance alone."""
    if not isinstance(values, tuple) or not values:
        raise ValueError("S1 preview placements must be a nonempty tuple")
    if any(type(value) is not placement_type for value in values):
        family = "S1J" if placement_type is S1JPlacement else "S1"
        raise TypeError(
            f"{family} preview requires {placement_type.__name__} records"
        )
    result = tuple(placement_type(
        value.position_id, value.rail_id, value.timber_id,
        value.origin_mm, value.x_axis, value.y_axis,
    ) for value in values)
    if len({value.position_id for value in result}) != len(result):
        raise ValueError("S1 preview placement identities are duplicated")
    return tuple(sorted(result, key=lambda value: value.position_id))


def _host_placement(placement):
    x, y, origin = placement.x_axis, placement.y_axis, placement.origin_mm
    return App.Placement(App.Matrix(
        x[0], y[0], 0.0, origin[0],
        x[1], y[1], 0.0, origin[1],
        0.0, 0.0, 1.0, origin[2],
        0.0, 0.0, 0.0, 1.0,
    ))


def _world_geometry(geometry, placement):
    vertices = tuple((name, *placement.transform_point(tuple(map(float, xyz))))
                     for name, *xyz in geometry.vertices)
    points = tuple(vertex[1:] for vertex in vertices)
    bounds = tuple(min(point[axis] for point in points) for axis in range(3))
    bounds += tuple(max(point[axis] for point in points) for axis in range(3))
    return replace(
        geometry, vertices=vertices, bounds_mm=bounds,
        landmarks=tuple((name, placement.transform_point(tuple(map(float, p))))
                        for name, p in geometry.landmarks),
    )


def _measure_layer(shape):
    _require(not shape.isNull() and shape.isValid(), "invalid display layer")
    bounds = _bounds(shape)
    _require(all(math.isfinite(value) for value in bounds),
             "nonfinite layer bounds")
    _require(math.isfinite(shape.Volume) and math.isfinite(shape.Length),
             "nonfinite layer measurement")
    return {
        "bounds_mm": bounds, "volume_mm3": shape.Volume,
        "edge_length_mm": shape.Length, "solid_count": len(shape.Solids),
        "edge_count": len(shape.Edges), "valid": True,
    }


def _context_layers(context_shapes):
    if not isinstance(context_shapes, tuple) or len(context_shapes) != 2:
        raise ValueError("S1 preview requires rail and timber context shapes")
    result = []
    for source in context_shapes:
        source_measurement = _measure_layer(source)
        _require(source.Edges, "empty context edge geometry")
        # Existing context can contain faces. Display only copied edges.
        shape = Part.makeCompound([edge.copy() for edge in source.Edges])
        measured = _measure_layer(shape)
        _require(not shape.Solids and not shape.Faces,
                 "context must remain a wire display")
        _require(measured["edge_count"] == source_measurement["edge_count"],
                 "context edge count changed")
        _require(max(abs(a - b) for a, b in zip(
            measured["bounds_mm"], source_measurement["bounds_mm"],
        )) <= NUMERICAL_LENGTH_TOLERANCE_MM, "context bounds changed")
        result.append(shape)
    return tuple(result)


def _build_layers(model, placements, context_shapes):
    """Build five prototypes once, then validate every rigidly placed copy."""
    builders = (
        construct_chair_base_shape, construct_chair_seat_shape,
        construct_chair_key_shape, construct_chair_outer_jaw_shape,
        construct_chair_inner_jaw_shape,
    )
    _require(tuple(c.role for c in model.components) == CHAIR_ASSEMBLY_ROLES,
             "unexpected component identity or order")
    prototypes = tuple(
        builder(component.geometry)
        for builder, component in zip(builders, model.components)
    )
    prototype_measurements = tuple(
        _measure_component(shape, component, component.role)
        for shape, component in zip(prototypes, model.components)
    )
    placed_by_role = [[] for _ in prototypes]
    measurements = []
    for placement in placements:
        rigid = _host_placement(placement)
        placed_components = []
        for index, (prototype, component) in enumerate(
            zip(prototypes, model.components)
        ):
            shape = prototype.copy()
            shape.Placement = rigid.multiply(prototype.Placement)
            geometry = _world_geometry(component.geometry, placement)
            measured = _measure_component(
                shape, component, component.role, geometry=geometry,
            )
            landmark_residuals = {}
            for name, point in component.geometry.landmarks:
                original = tuple(map(float, point))
                observed = tuple(rigid.multVec(App.Vector(*original)))
                expected = placement.transform_point(original)
                residual = math.dist(observed, expected)
                _require(residual <= NUMERICAL_LENGTH_TOLERANCE_MM,
                         "host landmark placement differs: " + name)
                landmark_residuals[name] = residual
            measured["landmarks_mm"] = dict(geometry.landmarks)
            measured["landmark_residuals_mm"] = landmark_residuals
            placed_components.append(measured)
            placed_by_role[index].append(shape)
        measurements.append({
            "position_id": placement.position_id,
            "rail_id": placement.rail_id, "timber_id": placement.timber_id,
            "origin_mm": placement.origin_mm,
            "x_axis": placement.x_axis, "y_axis": placement.y_axis,
            "components": placed_components,
        })
    compounds = []
    for index, shapes in enumerate(placed_by_role):
        compound = Part.makeCompound(shapes)
        measured = _measure_layer(compound)
        children = compound.childShapes()
        _require(measured["solid_count"] == len(placements)
                 and len(children) == len(shapes)
                 and all(a.isSame(b) for a, b in zip(children, shapes)),
                 "component compound identity or order changed")
        budget = sum(m["components"][index]["numerical_volume_budget_mm3"]
                     for m in measurements)
        _require(
            abs(compound.Volume - sum(s.Volume for s in shapes)) <= budget,
            "component compound volume changed",
        )
        compounds.append(compound)
    # Copy placement must never alter the shared prototype.
    _require(prototype_measurements == tuple(
        _measure_component(shape, component, component.role)
        for shape, component in zip(prototypes, model.components)
    ), "prototype changed during placement")
    layers = _context_layers(context_shapes) + tuple(compounds)
    return layers, measurements


def _verify_stored_layers(stored_layers, layers, model, placements):
    """Verify geometry after recompute can replace OCCT shape identities."""
    for index, (stored, original) in enumerate(zip(stored_layers, layers)):
        measured = _measure_layer(stored)
        expected = _measure_layer(original)
        _require(stored.ShapeType == original.ShapeType
                 and all(len(getattr(stored, name))
                         == len(getattr(original, name)) for name in (
                             "Vertexes", "Edges", "Wires", "Faces",
                             "Shells", "Solids",
                         )), "stored layer topology changed")
        _require(max(abs(a - b) for a, b in zip(
            measured["bounds_mm"], expected["bounds_mm"],
        )) <= NUMERICAL_LENGTH_TOLERANCE_MM, "stored layer bounds changed")
        # Keep edge order and endpoints as well as aggregate topology. The
        # context contains copied source edges; components are remeasured
        # below against each analytical world placement.
        for edge, source in zip(stored.Edges, original.Edges):
            _require(type(edge.Curve) is type(source.Curve)
                     and len(edge.Vertexes) == len(source.Vertexes)
                     and abs(edge.Length - source.Length)
                     <= NUMERICAL_LENGTH_TOLERANCE_MM
                     and all(math.dist(tuple(a.Point), tuple(b.Point))
                             <= NUMERICAL_LENGTH_TOLERANCE_MM
                             for a, b in zip(edge.Vertexes, source.Vertexes)),
                     "stored edge geometry or order changed")
        children = stored.childShapes()
        _require(len(children) == len(original.childShapes()),
                 "stored layer child count changed")
        if index < 2:
            _require(not stored.Faces and not stored.Solids
                     and all(child.ShapeType == "Edge" for child in children)
                     and stored.Volume == original.Volume == 0.0,
                     "stored context is no longer a wire display")
            continue
        component = model.components[index - 2]
        _require(len(children) == len(placements),
                 "stored component placement count changed")
        checked = [
            _measure_component(
                child, component, component.role,
                geometry=_world_geometry(component.geometry, placement),
            ) for child, placement in zip(children, placements)
        ]
        _require(abs(stored.Volume - original.Volume) <= sum(
            item["numerical_volume_budget_mm3"] for item in checked
        ), "stored layer volume changed")


def _create_reference_preview(
    package, manifest_text, model_request, placements, context_shapes,
    source_receipt, verify_source, *, family, placement_type, prepare_model,
    layer_specs,
):
    """Create a private seven-layer snapshot, preserving source documents.

    The caller supplies current analysed family placements and a callback that
    raises if the complete source context has changed. The callback runs
    immediately before commit. On failure, only the invocation-owned
    preview is aborted/closed; prior registry, active document and exact GUI
    selection/preselection are restored. Success activates the new normal,
    unsaved document, with one undoable seven-object transaction.

    Returned measurements are neutral reference evidence. They grant no
    package, fit, key-direction, production, persistence or export authority.
    """
    if not callable(verify_source):
        raise TypeError(
            f"{family} preview requires a source verification callback"
        )
    placements = _placements(placements, placement_type)
    json.dumps(source_receipt, allow_nan=False)
    receipt = deepcopy(source_receipt)
    model = prepare_model(package, manifest_text, model_request)

    def prepare_layers():
        layers, placed = _build_layers(model, placements, context_shapes)
        layer_measurements = [dict(
            _measure_layer(shape), name=spec[0], role=spec[1],
        ) for spec, shape in zip(layer_specs, layers)]
        result = {
            "source_receipt": receipt,
            "package_signature": package.content_signature,
            "manifest_signature": model.manifest_signature,
            "request_signature": model.request_signature,
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "key_placement": "central-reference-only",
            "length_unit": "mm", "length_basis": "model",
            "numerical_length_budget_mm": NUMERICAL_LENGTH_TOLERANCE_MM,
            "placement_count": len(placements), "layer_count": len(layers),
            "placements": placed, "layers": layer_measurements,
            "limits": [
                "Private reference; no production or export authority.",
                "Central key; no directional-key or physical-fit acceptance.",
                "Snapshot only; no live invalidation or persistence contract.",
            ],
        }

        def verify_layers(stored):
            _verify_stored_layers(stored, layers, model, placements)

        return layers, result, verify_layers

    return _materialise_preview(
        family, receipt, layer_specs, prepare_layers, verify_source,
    )


def _materialise_preview(
    family, receipt, layer_specs, prepare_layers, verify_source,
):
    """Apply one prepared snapshot through the shared document lifecycle."""
    gui = None
    if App.GuiUp:
        import FreeCADGui as gui
    previous = dict(App.listDocuments())
    active = _active_document(App)
    _require(active is None or previous.get(active.Name) is active,
             "previous active document is unregistered")
    selection = _selection_snapshot(App, gui)
    preselection = _preselection_snapshot(App, gui)
    name = "TrackTemplate" + family + "Reference_" + uuid.uuid4().hex
    _require(name not in previous, "preview document name already exists")
    owned = None
    transaction = False
    try:
        layers, result, verify_layers = prepare_layers()
        result = {"document_name": name, **result}
        _require(len(layers) == len(layer_specs),
                 "unexpected prepared layer count")
        _require(_same_registry(dict(App.listDocuments()), previous),
                 "document registry changed during preparation")
        document = App.newDocument(
            name, f"Private {family} - " + receipt.get(
                "coverage_summary", "reference only",
            ) + " - central keys", False, False,
        )
        observed = dict(App.listDocuments())
        if (document is not None and observed.get(name) is document
                and all(document is not item for item in previous.values())):
            owned = (name, document)
        expected = dict(previous, **{name: document})
        _require(owned is not None and document.Name == name
                 and not document.FileName and document.Temporary is False
                 and _same_registry(observed, expected),
                 "new document ownership is unclear")
        document.UndoMode = 1
        document.openTransaction(f"Create private {family} reference preview")
        transaction = True
        for (object_name, label, colour), shape in zip(layer_specs, layers):
            obj = document.addObject("Part::Feature", object_name)
            _require(document.getObject(object_name) is obj,
                     "display object ownership is unclear")
            obj.Label = f"Private {family} reference - " + label
            obj.Shape = shape
            if gui is not None:
                obj.ViewObject.ShapeColor = colour
                obj.ViewObject.LineColor = colour
                if not shape.Solids:
                    obj.ViewObject.DisplayMode = "Wireframe"
        _require(document.recompute() is not False, "preview recompute failed")
        _require(len(document.Objects) == len(layer_specs),
                 "unexpected preview object count")
        verify_layers(tuple(
            document.getObject(spec[0]).Shape for spec in layer_specs
        ))
        _restore_selection(App, gui, selection)
        _restore_preselection(App, gui, preselection)
        App.setActiveDocument(name)
        if gui is not None:
            view = gui.getDocument(name).activeView()
            view.viewAxonometric()
            view.fitAll()
        _require(_active_document(App) is document
                 and _same_registry(dict(App.listDocuments()), expected)
                 and _selection_snapshot(App, gui) == selection
                 and _preselection_snapshot(App, gui) == preselection,
                 "preview changed unrelated document or selection state")
        verify_source()
        document.commitTransaction()
        transaction = False
        return result
    except BaseException as error:
        if transaction and owned is not None:
            try:
                owned[1].abortTransaction()
            except BaseException as abort_error:
                error.add_note(
                    f"{family} preview abort failed: " + str(abort_error)
                )
        errors, interruption = _cleanup(
            App, gui, owned, previous, active, selection, preselection,
        )
        if errors:
            error.add_note(
                f"{family} preview cleanup failed: " + "; ".join(errors)
            )
        if interruption is not None:
            error.add_note(f"{family} preview cleanup was interrupted.")
        raise


def create_l1_reference_preview(package, manifest_text, model_request):
    """Inspect one private L1 model at its canonical origin and axes.

    Validate original inputs before creating five named component layers
    in one undoable transaction. The outer jaw retains three separate
    solids. Reuse the shared isolated-document lifecycle and return neutral
    measurements only. No track placement, fit or production claim follows.
    """
    model = prepare_chair_l1_model_research(
        package, manifest_text, model_request,
    )
    layer_specs = tuple(("L1" + name[2:], role, colour)
                        for name, role, colour in _LAYERS[2:])

    def measure_components(shapes):
        _require(len(shapes) == len(model.components) == 5,
                 "L1 requires five semantic components")
        _require(tuple(c.role for c in model.components)
                 == CHAIR_ASSEMBLY_ROLES, "L1 component order changed")
        return [
            _measure_component(
                shape, component, component.role,
                l1_outer=component.role == "outer-jaw",
            ) for shape, component in zip(shapes, model.components)
        ]

    def prepare_layers():
        layers = _construct_components(model, l1=True)
        components = measure_components(layers)
        result = {
            "contract_id": "tracktemplate.private-l1-reference-preview.v1",
            "package_signature": model.package.content_signature,
            "manifest_signature": model.manifest_signature,
            "request_signature": model.request_signature,
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "key_placement": "central-reference-only",
            "length_unit": "mm", "length_basis": "model",
            "scale_denominator": "76.2",
            "placement": "same-chair-origin-and-axes-central-key",
            "component_count": 5, "solid_count": 7, "layer_count": 5,
            "components": components,
            "layers": [dict(_measure_layer(shape), name=spec[0], role=spec[1])
                       for spec, shape in zip(layer_specs, layers)],
            "limits": [
                "Private reference; no production or export authority.",
                "Central key; no directional-key or physical-fit acceptance.",
                "Snapshot only; no live invalidation or persistence contract.",
                "Model origin only; no track placement or source-scale claim.",
            ],
        }
        return layers, result, measure_components

    def verify_inputs():
        _require(prepare_chair_l1_model_research(
            package, manifest_text, model_request,
        ) == model, "L1 inputs changed during preview creation")

    return _materialise_preview(
        "L1", {"coverage_summary": "one model at its origin"},
        layer_specs, prepare_layers, verify_inputs,
    )


def create_s1_reference_preview(
    package, manifest_text, model_request, placements, context_shapes,
    source_receipt, verify_source,
):
    """Create the existing private seven-layer S1 snapshot transaction."""
    return _create_reference_preview(
        package, manifest_text, model_request, placements, context_shapes,
        source_receipt, verify_source, family="S1",
        placement_type=S1Placement, prepare_model=prepare_chair_model_research,
        layer_specs=_LAYERS,
    )


def create_s1j_reference_preview(
    package, manifest_text, model_request, placements, context_shapes,
    source_receipt, verify_source,
):
    """Create a private S1J snapshot through the same seven-layer lifecycle.

    Reject another family's package or placements before document creation.
    Preserve source and foreign documents, selection and rollback semantics.
    The result is a derived research view, with no production, persistence,
    physical-fit, directional-key or export authority.
    """
    layer_specs = tuple(
        (name.replace("S1", "S1J", 1), label, colour)
        for name, label, colour in _LAYERS
    )
    return _create_reference_preview(
        package, manifest_text, model_request, placements, context_shapes,
        source_receipt, verify_source, family="S1J",
        placement_type=S1JPlacement,
        prepare_model=prepare_chair_s1j_model_research,
        layer_specs=layer_specs,
    )


def create_s1_s1j_reference_preview(
    s1_package, s1_manifest_text, s1j_package, s1j_manifest_text,
    model_request, s1_placements, s1j_placements, context_shapes,
    source_receipt, verify_source,
):
    """Create one private S1/S1J snapshot with one undoable transaction.

    Both fixed families must prepare successfully before document creation.
    Context wires are shared; each family's five component layers, package
    signatures and stable placement identities remain separate. Any failure
    closes only the invocation-owned document and restores prior GUI state.
    No production, export, fit or persistence authority follows.
    """
    if not callable(verify_source):
        raise TypeError("S1/S1J preview requires a source verification callback")
    s1_placements = _placements(s1_placements, S1Placement)
    s1j_placements = _placements(s1j_placements, S1JPlacement)
    if {item.position_id for item in s1_placements}.intersection(
        item.position_id for item in s1j_placements
    ):
        raise ValueError("S1/S1J preview placement identities overlap")
    json.dumps(source_receipt, allow_nan=False)
    receipt = deepcopy(source_receipt)
    layer_specs = _LAYERS[:2] + tuple(
        (name, "S1 " + label, colour)
        for name, label, colour in _LAYERS[2:]
    ) + tuple(
        (name.replace("S1", "S1J", 1), "S1J " + label, colour)
        for name, label, colour in _LAYERS[2:]
    )

    def prepare_layers():
        s1_model = prepare_chair_model_research(
            s1_package, s1_manifest_text, model_request,
        )
        s1j_model = prepare_chair_s1j_model_research(
            s1j_package, s1j_manifest_text, model_request,
        )
        s1_layers, s1_placed = _build_layers(
            s1_model, s1_placements, context_shapes,
        )
        s1j_layers, s1j_placed = _build_layers(
            s1j_model, s1j_placements, context_shapes,
        )
        layers = s1_layers + s1j_layers[2:]
        families = []
        for family, model, placed in (
            ("S1", s1_model, s1_placed), ("S1J", s1j_model, s1j_placed),
        ):
            families.append({
                "family": family,
                "package_signature": model.package.content_signature,
                "manifest_signature": model.manifest_signature,
                "request_signature": model.request_signature,
                "placement_count": len(placed), "placements": placed,
            })
        result = {
            "source_receipt": receipt, "families": families,
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "key_placement": "central-reference-only",
            "length_unit": "mm", "length_basis": "model",
            "numerical_length_budget_mm": NUMERICAL_LENGTH_TOLERANCE_MM,
            "placement_count": len(s1_placements) + len(s1j_placements),
            "layer_count": len(layers),
            "layers": [dict(
                _measure_layer(shape), name=spec[0], role=spec[1],
            ) for spec, shape in zip(layer_specs, layers)],
            "limits": [
                "Private reference; no production or export authority.",
                "Central key; no directional-key or physical-fit acceptance.",
                "Snapshot only; no live invalidation or persistence contract.",
            ],
        }

        def verify_layers(stored):
            _verify_stored_layers(
                stored[:7], s1_layers, s1_model, s1_placements,
            )
            _verify_stored_layers(
                stored[:2] + stored[7:], s1j_layers,
                s1j_model, s1j_placements,
            )

        return layers, result, verify_layers

    return _materialise_preview(
        "S1S1J", receipt, layer_specs, prepare_layers, verify_source,
    )
