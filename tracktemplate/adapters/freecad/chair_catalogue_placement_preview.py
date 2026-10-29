"""Place retained private chair assemblies without rebuilding geometry.

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
from tracktemplate.application.chair_pair_catalogue import (
    CONTEXT_IDS,
    prepare_paired_catalogue,
    verify_paired_catalogue,
)
from tracktemplate.application.chair_crossing_pair_catalogue import (
    CROSSING_PAIR_CONTEXT_IDS,
    CROSSING_SPLIT_CONTEXT_IDS,
    prepare_crossing_pair_catalogue,
    prepare_crossing_split_catalogue,
    verify_crossing_pair_catalogue,
    verify_crossing_split_catalogue,
)
from tracktemplate.application.chair_crossing_zy_catalogue import (
    ZY_CONTEXT_IDS,
    prepare_zy_catalogue,
    verify_zy_catalogue,
)
from tracktemplate.domain.chair_placement import (
    PairedChairPlacement,
    PPlacement,
    S1JPlacement,
    S1Placement,
)
from tracktemplate.domain.central_check_placement import (
    CentralCheckPlacement,
    prepare_central_check_placements,
)
from tracktemplate.domain.check_end_placement import (
    CheckEndPlacement,
    prepare_check_end_placements,
)
from tracktemplate.domain.single_rail_placement import (
    SingleRailPlacement,
    prepare_single_rail_placements,
)


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
_S1J_MODEL_SHA256 = (
    "fd5cb5ffa9fa2004ef2930ab9280b4e906175b9233364448d07d8ef63c212c4b"
)
_S1J_SOURCE_NAMES = (
    "base_plinth", "seat", "outer", "inner", "key", "display_rail",
    "SourceFixing", "SourceFixing001", "SourceFixing002", "SourceFixing003",
    "SourceFixing004", "SourceFixing005", "SourceFixing006",
    "SourceFixing007", "SourceFixing008", "SourceFixing009",
    "SourceFixing010", "SourceFixing011",
)
_S1_MODEL_SHA256 = (
    "a3c8c99a67d9f18b0ee5668400a8bf94f9f39fa641a22da7477141b74cc120eb"
)
_L1_MODEL_SHA256 = (
    "a0289c046b6ae8cb1e2df88a8f6a1f3f0dc79f7a0ae1870d0b3b13154e0eb042"
)
_CC_MODEL_SHA256 = (
    "b28b574a517e677c86fc35e26cab9a966e41504cb2242968db45e7c07ac81637"
)
_CC_FIXING_NAMES = ("SourceFixing",) + tuple(
    f"SourceFixing{index:03d}" for index in range(1, 16)
)
_CHECK_END_MODELS = (
    ("CCL", "692a8cfbe6845fd9fce4e8b471f1ec37d5388366c6451f9bff2d65601dbccb3d"),
    ("CCR", "d594dfb2f387c2b2a0360863ea8dcc30cd2057ed06095f8eb1e49a9421282fa7"),
)
_CHECK_END_CONTEXT_SHA256 = (
    "4c6d059f99889cb292fc028783d2ee425b7493540e6b22b80f55961df543d2ef"
)
_CHECK_END_SEAT_KEY_NAMES = ("c06_CCSEATCK_CCSEATCK", "c07_CCKEY_CCKEY")
_CHECK_END_COMMON_NAMES = (
    "base_plinth", "c00_SCOUTJAW_SCOUTJAW", "c01_CCFIJAW_body",
    "c01_CCFIJAW_bevel_negative", "c01_CCFIJAW_bevel_positive",
    "c01_CCFIJAW_grip", "c01_CCFIJAW_stiffener",
    "c02_SCCCSEAT_SCCCSEAT", "c03_KEY_KEY",
)
_CHECK_END_NAMES = (
    ("CCL", _CHECK_END_COMMON_NAMES + (
        "c04_MA_body", "c04_MA_bevel_negative", "c04_MA_bevel_positive",
        "c04_MA_grip", "c04_MA_stiffener", "c05_MB_MB",
    ) + _CHECK_END_SEAT_KEY_NAMES + _CC_FIXING_NAMES),
    ("CCR", _CHECK_END_COMMON_NAMES + (
        "c04_MC_body", "c04_MC_bevel_negative", "c04_MC_bevel_positive",
        "c04_MC_grip", "c04_MC_stiffener", "c05_MD_MD",
    ) + _CHECK_END_SEAT_KEY_NAMES + _CC_FIXING_NAMES),
)
_S1_SOURCE_NAMES = (
    "Part_00", "Part_01", "Part_02", "Part_03", "Part_04",
    "SourceFixing", "SourceFixing001", "SourceFixing002", "SourceFixing003",
    "SourceFixing004", "SourceFixing005", "SourceFixing006",
    "SourceFixing007", "SourceFixing008", "SourceFixing009",
    "SourceFixing010", "SourceFixing011",
)
_L1_SOURCE_NAMES = tuple(f"Part_{index:02d}" for index in range(7)) + _CC_FIXING_NAMES
_CONTEXT_SPECS = (
    ("ReferenceRails", "rail context", (0.55, 0.58, 0.62)),
    ("ReferenceTimbers", "timber context", (0.55, 0.40, 0.25)),
)
_DISCRETE_FIELDS = (
    "shape_type", "solid_count", "shell_count", "face_count", "wire_count",
    "edge_count", "vertex_count", "maximum_kernel_tolerance_mm",
    "orientation", "valid", "all_solids_closed",
)


def _require(condition, message, *, family="P"):
    if not condition:
        raise ValueError(f"Private {family} catalogue placement: " + message)


def _prototype_state(shape, *, family="P"):
    """Keep geometry metrics independent of shared display triangulation."""
    measured = _measure_shape(shape)
    # GUI tessellation changes shared face caches. Shape.BoundBox can use
    # those polygons; geometry-based bounds retain the source invariant.
    box = shape.optimalBoundingBox(False, False)
    bounds = (box.XMin, box.YMin, box.ZMin,
              box.XMax, box.YMax, box.ZMax)
    _require(all(math.isfinite(value) for value in bounds),
             "nonfinite geometry-based prototype bounds", family=family)
    return dict(measured, bounds_mm=bounds)


def _verify_component(actual, expected, *, family="P"):
    """Retain native topology, direction, location and validity."""
    _require(_same_presented_shape(actual, expected),
             "component geometry, orientation or placement changed",
             family=family)
    observed = _measure_shape(actual)
    original = _measure_shape(expected)
    _require(all(observed[key] == original[key]
                 for key in _DISCRETE_FIELDS),
             "component topology or validity changed", family=family)
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
    return _create_private_catalogue_preview(
        catalogue_path, placements, context_shapes, source_receipt,
        verify_source, family="P", placement_type=PPlacement,
        model_sha256=_P_MODEL_SHA256, source_names=_P_SOURCE_NAMES,
    )


def create_private_catalogue_s1j_preview(
    catalogue_path, placements, context_shapes, source_receipt, verify_source,
):
    """Create one unsaved private S1J view from confirmed joint placements.

    Proper model-mm frames place the fixed S1J/basic-04 components once.
    Source checks, the transaction and preview disposal use the P lifecycle.
    No geometry is rebuilt and no fit or production acceptance follows.
    """
    return _create_private_catalogue_preview(
        catalogue_path, placements, context_shapes, source_receipt,
        verify_source, family="S1J", placement_type=S1JPlacement,
        model_sha256=_S1J_MODEL_SHA256, source_names=_S1J_SOURCE_NAMES,
    )


def _create_private_catalogue_preview(
    catalogue_path, placements, context_shapes, source_receipt, verify_source,
    *, family, placement_type, model_sha256, source_names,
):
    """Place one fixed family through the shared component lifecycle."""
    if not callable(verify_source):
        raise TypeError(f"{family} placement requires source verification")
    receipt = json.loads(json.dumps(source_receipt, allow_nan=False))
    prepared, layer_specs, prepare_layers = _prepare_catalogue_family(
        catalogue_path, placements, context_shapes, receipt,
        family=family, placement_type=placement_type,
        model_sha256=model_sha256, source_names=source_names,
    )

    def verify_inputs():
        verify_source()
        verify_catalogue_sources(prepared)

    return _materialise_preview(
        family, receipt, layer_specs, prepare_layers, verify_inputs,
        title_suffix="catalogue placements",
    )


def _prepare_catalogue_family(
    catalogue_path, placements, context_shapes, source_receipt,
    *, family, placement_type, model_sha256, source_names,
    run="basic-04", source_context="fixed-basic-source-context",
    prepared_selection=None,
):
    """Prepare one fixed assembly without creating a document.

    A whole-crossover caller supplies its shared context separately.
    Existing single-family callers keep their original context layers.
    """
    def require(condition, message):
        _require(condition, message, family=family)

    if placement_type is SingleRailPlacement:
        placements = prepare_single_rail_placements(placements)
        require(all(value.family == family for value in placements),
                "single-rail family differs from its component frames")
    elif placement_type is CheckEndPlacement:
        placements = prepare_check_end_placements(placements)
        require(all(value.family == family for value in placements),
                "check-end family differs from its component frames")
    else:
        placements = (prepare_central_check_placements(placements)
                      if placement_type is CentralCheckPlacement else
                      _placements(placements, placement_type))
    receipt = json.loads(json.dumps(source_receipt, allow_nan=False))
    require(isinstance(receipt, dict), "source receipt must be a mapping")
    # The whole-crossover caller obtains supplemental selections from the
    # repository-owned frozen reader. It verifies the complete set again
    # at the transaction boundary, with no caller-defined trust callback.
    prepared = (prepare_catalogue_chair(catalogue_path, family, run=run)
                if prepared_selection is None else prepared_selection)
    require(
        prepared.label == family and prepared.run == run
        and prepared.context == source_context
        and prepared.model_sha256 == model_sha256
        and tuple(item.name for item in prepared.components)
        == source_names,
        f"the fixed {family} catalogue component binding differs",
    )
    components = tuple(item for item in prepared.components
                       if item.name != "display_rail")
    excluded = tuple(item for item in prepared.components
                     if item.name == "display_rail")
    context_specs = _CONTEXT_SPECS if context_shapes is not None else ()
    layer_specs = context_specs + tuple(
        (item.name, item.label, _component_colour(item.label))
        for item in components
    )

    def prepare_layers():
        all_shapes, all_measurements = _import_components(prepared)
        require(len(all_shapes) == len(all_measurements)
                == len(prepared.components),
                "imported source component count changed")
        admitted = tuple(
            (component, shape, measured)
            for component, shape, measured in zip(
                prepared.components, all_shapes, all_measurements,
            ) if component.name != "display_rail"
        )
        prototypes = tuple(shape for _item, shape, _measured in admitted)
        original_metrics = tuple(_prototype_state(shape, family=family)
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
                component_frame = placement
                if (isinstance(placement, (CentralCheckPlacement, CheckEndPlacement,
                                           SingleRailPlacement))
                        and component.name in _CC_FIXING_NAMES):
                    fixing_index = _CC_FIXING_NAMES.index(component.name) // 4
                    component_frame = placement.fixing_frames[fixing_index]
                elif (isinstance(placement, CheckEndPlacement)
                      and component.name in _CHECK_END_SEAT_KEY_NAMES):
                    component_frame = placement.check_frame
                component_rigid = (rigid if component_frame is placement
                                   else _host_placement(component_frame))
                # The shallow wrapper shares native geometry, not its location.
                # The B-rep already contains each fitting's local placement.
                shape = Part.Shape(prototype)
                shape.Placement = component_rigid.multiply(prototype.Placement)
                require(shape.isPartner(prototype)
                        and shape.Orientation == prototype.Orientation,
                        "rigid placement changed native geometry")
                measured = _measure_shape(shape)
                require(all(measured[key] == original_metrics[index][key]
                            for key in _DISCRETE_FIELDS),
                        "rigid placement changed component invariants")
                measurements.append(dict(
                    measured, **_source_identity(prepared, component),
                    placement_identity=(placement.position_id,
                                        prepared.model_sha256, component.name),
                ))
                if isinstance(placement, (CentralCheckPlacement, CheckEndPlacement,
                                          SingleRailPlacement)):
                    measurements[-1].update(
                        origin_mm=component_frame.origin_mm,
                        x_axis=component_frame.x_axis,
                        y_axis=component_frame.y_axis,
                    )
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
            require(len(children) == len(expected),
                    "component compound child count changed")
            for actual, original in zip(children, expected):
                _verify_component(actual, original, family=family)
            compounds.append(compound)
        require(original_metrics == tuple(
            _prototype_state(shape, family=family) for shape in prototypes
        ), "placement changed a shared source component")
        context = (_context_layers(context_shapes)
                   if context_shapes is not None else ())
        layers = context + tuple(compounds)
        result = {
            "contract_id": (
                f"tracktemplate.private-catalogue-{family.lower()}-placement.v1"
            ),
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
                **_source_identity(prepared, item),
                "reason": "Source display rail is context, not a chair part.",
            } for item in excluded],
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
                f"Private fixed-source {family} placement; no physical-fit "
                "acceptance.",
                "No production, export, persistence or phase acceptance.",
                "Source overlaps and hidden mating closures remain.",
                "No source XML placement, scale or frame conversion "
                "reapplied.",
                "Unresolved key direction and original exclusions remain.",
            ],
        }
        if placement_type is CentralCheckPlacement:
            result.update(
                contract_id="tracktemplate.private-catalogue-cc-placement.v1",
                placement="source-central-check-component-frames.v1",
                fixing_head_rotation_rad=0.0, random_export_parity=False,
                fixing_angle_frame="uncurved-RH-source-before-common-host-rotation",
                templot_global_fixing_angle_parity=False,
            )
        if placement_type is CheckEndPlacement:
            result.update(
                placement="source-check-end-component-frames.v1",
                fixing_head_rotation_rad=0.0, random_export_parity=False,
                fixing_angle_frame="uncurved-RH-source-before-common-host-rotation",
                templot_global_fixing_angle_parity=False,
            )
        if placement_type is SingleRailPlacement:
            result.update(
                contract_id=f"tracktemplate.private-catalogue-{family.lower()}-source-placement.v1",
                placement="source-single-rail-component-frames.v1",
                fixing_head_rotation_rad=0.0, random_export_parity=False,
                fixing_angle_frame="uncurved-RH-source-before-common-host-rotation",
                templot_global_fixing_angle_parity=False,
            )

        def verify_layers(stored):
            require(len(stored) == len(layers), "stored layer count changed")
            for index, (actual, expected) in enumerate(zip(stored, layers)):
                require(_same_presented_shape(actual, expected),
                        "stored layer geometry or placement changed")
                if index < len(context):
                    _measure_layer(actual)
                    require(not actual.Faces and not actual.Solids
                            and len(actual.Edges) == len(expected.Edges),
                            "stored context is no longer the copied wires")
                    continue
                _verify_component(actual, expected, family=family)
                children = actual.childShapes()
                originals = by_component[index - len(context)]
                require(len(children) == len(originals),
                        "stored component child count changed")
                for child, original in zip(children, originals):
                    _verify_component(child, original, family=family)
            require(original_metrics == tuple(
                _prototype_state(shape, family=family) for shape in prototypes
            ), "stored placement changed a shared source component")

        return layers, result, verify_layers

    return prepared, layer_specs, prepare_layers


def create_private_catalogue_crossover_preview(
    catalogue_path, placements_by_family, context_shapes, source_receipt,
    verify_source,
    *, paired_contexts_path=None, include_central_cc=False,
    include_check_ends=False, include_single_rail=False, correct_heel_l1=False,
    include_r2_exit=False, include_r1_exit=False,
    crossing_zy_contexts_path=None, crossing_pair_contexts_path=None,
    crossing_split_contexts_path=None,
):
    """Create one unsaved crossover view with qualified retained assemblies.

    Each family keeps its existing proper model-mm placement contract.
    The caller records every source position and evidenced exclusion.
    All families share one transaction and copied rail/timber context.
    No geometry, scale, source frame or key-direction policy is changed.
    """
    family = "Crossover"

    def require(condition, message):
        _require(condition, message, family=family)

    require(crossing_split_contexts_path is None
            or include_single_rail is True,
            "crossing split coverage requires the single-rail supplement")
    require(crossing_pair_contexts_path is None
            or include_single_rail is True,
            "crossing pair coverage requires the single-rail supplement")
    require(crossing_zy_contexts_path is None or include_single_rail is True,
            "ZY crossing coverage requires the single-rail supplement")
    require(type(include_r1_exit) is bool,
            "include_r1_exit requires an actual Boolean")
    require(not include_r1_exit or include_single_rail is True,
            "R1 exit coverage requires the single-rail supplement")
    require(type(include_r2_exit) is bool,
            "include_r2_exit requires an actual Boolean")
    require(not include_r2_exit or include_single_rail is True,
            "R2 exit coverage requires the single-rail supplement")
    require(type(correct_heel_l1) is bool,
            "correct_heel_l1 requires an actual Boolean")
    require(not correct_heel_l1 or include_single_rail is True,
            "heel correction requires the single-rail supplement")
    require(type(include_single_rail) is bool,
            "include_single_rail requires an actual Boolean")
    require(not include_single_rail or (
        include_check_ends is True and include_central_cc is True
        and paired_contexts_path is not None
    ), "single-rail coverage requires check ends, central CC and pairs")
    require(type(include_check_ends) is bool,
            "include_check_ends requires an actual Boolean")
    require(not include_check_ends or (include_central_cc is True
                                     and paired_contexts_path is not None),
            "check-end preview requires central CC and the paired supplement")
    require(type(include_central_cc) is bool,
            "include_central_cc requires an actual Boolean")
    require(not include_central_cc or paired_contexts_path is not None,
            "central CC requires the paired supplement")
    if not callable(verify_source):
        raise TypeError("Crossover placement requires source verification")
    paired = (() if paired_contexts_path is None
              else prepare_paired_catalogue(paired_contexts_path))
    zy = (() if crossing_zy_contexts_path is None
          else prepare_zy_catalogue(crossing_zy_contexts_path))
    crossing_pairs = (() if crossing_pair_contexts_path is None
                      else prepare_crossing_pair_catalogue(
                          crossing_pair_contexts_path,
                      ))
    crossing_splits = (() if crossing_split_contexts_path is None
                       else prepare_crossing_split_catalogue(
                           crossing_split_contexts_path,
                       ))
    expected_groups = {"S1", "S1J", "P"}
    if paired:
        expected_groups.update(CONTEXT_IDS)
    if include_central_cc:
        expected_groups.add("CC")
    if include_check_ends:
        expected_groups.update(family for family, _digest in _CHECK_END_MODELS)
    if include_single_rail:
        expected_groups.update(("SupplementS1", "SupplementS1J", "L1"))
    if zy:
        expected_groups.update(ZY_CONTEXT_IDS)
    if crossing_pairs:
        expected_groups.update(CROSSING_PAIR_CONTEXT_IDS)
    if crossing_splits:
        expected_groups.update(CROSSING_SPLIT_CONTEXT_IDS)
    require(isinstance(placements_by_family, dict)
            and set(placements_by_family) == expected_groups,
            "the complete qualified placement groups are required")
    receipt = json.loads(json.dumps(source_receipt, allow_nan=False))
    require(isinstance(receipt, dict), "source receipt must be a mapping")
    specifications = (
        ("S1", S1Placement, _S1_MODEL_SHA256, _S1_SOURCE_NAMES,
         "existing-02", "retained-S1-L1-reference-package"),
        ("S1J", S1JPlacement, _S1J_MODEL_SHA256, _S1J_SOURCE_NAMES,
         "basic-04", "fixed-basic-source-context"),
        ("P", PPlacement, _P_MODEL_SHA256, _P_SOURCE_NAMES,
         "basic-04", "fixed-basic-source-context"),
    )
    selections = []
    identities = set()
    layer_specs = _CONTEXT_SPECS
    for label, placement_type, digest, names, run, context in specifications:
        placements = _placements(placements_by_family[label], placement_type)
        ids = {placement.position_id for placement in placements}
        require(not identities.intersection(ids),
                "placement identities overlap between families")
        identities.update(ids)
        prepared, specs, prepare = _prepare_catalogue_family(
            catalogue_path, placements, None, receipt,
            family=label, placement_type=placement_type,
            model_sha256=digest, source_names=names,
            run=run, source_context=context,
        )
        prefixed = tuple((label + "_" + name, title, colour)
                         for name, title, colour in specs)
        layer_specs += prefixed
        selections.append((label, prepared, prefixed, prepare))
    for prepared in paired:
        context_id = prepared.run
        placements = _placements(placements_by_family[context_id],
                                 PairedChairPlacement)
        ids = {placement.position_id for placement in placements}
        require(len(placements) == 2 and not identities.intersection(ids),
                "paired placements are incomplete or overlap another group")
        identities.update(ids)
        _prepared, specs, prepare = _prepare_catalogue_family(
            paired_contexts_path, placements, None, receipt,
            family=prepared.label, placement_type=PairedChairPlacement,
            model_sha256=prepared.model_sha256,
            source_names=tuple(item.name for item in prepared.components),
            run=context_id, source_context=prepared.context,
            prepared_selection=prepared,
        )
        prefix = context_id.replace("-", "_")
        prefixed = tuple((prefix + "_" + name, title, colour)
                         for name, title, colour in specs)
        layer_specs += prefixed
        selections.append((context_id, prepared, prefixed, prepare))
    for prepared in (*zy, *crossing_pairs, *crossing_splits):
        context_id = prepared.run
        placements = _placements(placements_by_family[context_id],
                                 PairedChairPlacement)
        ids = {placement.position_id for placement in placements}
        require(len(placements) == 2 and not identities.intersection(ids),
                "crossing placements are incomplete or overlap another group")
        identities.update(ids)
        _prepared, specs, prepare = _prepare_catalogue_family(
            (crossing_zy_contexts_path if context_id in ZY_CONTEXT_IDS
             else crossing_pair_contexts_path
             if context_id in CROSSING_PAIR_CONTEXT_IDS
             else crossing_split_contexts_path), placements, None, receipt,
            family=prepared.label, placement_type=PairedChairPlacement,
            model_sha256=prepared.model_sha256,
            source_names=tuple(item.name for item in prepared.components),
            run=context_id, source_context=prepared.context,
            prepared_selection=prepared,
        )
        prefix = context_id.replace("-", "_")
        prefixed = tuple((prefix + "_" + name, title, colour)
                         for name, title, colour in specs)
        layer_specs += prefixed
        selections.append((context_id, prepared, prefixed, prepare))
    if include_central_cc:
        prepared = prepare_catalogue_chair(
            catalogue_path, "CC", run="context-native-02",
        )
        placements = prepare_central_check_placements(placements_by_family["CC"])
        ids = {placement.position_id for placement in placements}
        require(len(placements) == 12 and not identities.intersection(ids),
                "central CC placements are incomplete or overlap another group")
        require(len(prepared.components) == 33
                and tuple(item.name for item in prepared.components[-16:])
                == _CC_FIXING_NAMES,
                "central CC component identities differ")
        identities.update(ids)
        _prepared, specs, prepare = _prepare_catalogue_family(
            catalogue_path, placements, None, receipt,
            family="CC", placement_type=CentralCheckPlacement,
            model_sha256=_CC_MODEL_SHA256,
            source_names=tuple(item.name for item in prepared.components),
            run="context-native-02", source_context=prepared.context,
        )
        prefixed = tuple(("CC_" + name, title, colour)
                         for name, title, colour in specs)
        layer_specs += prefixed
        selections.append(("CC", prepared, prefixed, prepare))

    if include_check_ends:
        for family, digest in _CHECK_END_MODELS:
            prepared = prepare_catalogue_chair(
                catalogue_path, family, run="context-native-02",
            )
            placements = prepare_check_end_placements(placements_by_family[family])
            ids = {placement.position_id for placement in placements}
            require(len(placements) == 4 and not identities.intersection(ids),
                    "check-end placements are incomplete or overlap another group")
            require(prepared.context["context_sha256"] == _CHECK_END_CONTEXT_SHA256,
                    "check-end source context differs")
            identities.update(ids)
            _prepared, specs, prepare = _prepare_catalogue_family(
                catalogue_path, placements, None, receipt,
                family=family, placement_type=CheckEndPlacement,
                model_sha256=digest, source_names=dict(_CHECK_END_NAMES)[family],
                run="context-native-02", source_context=prepared.context,
            )
            prefixed = tuple((family + "_" + name, title, colour)
                             for name, title, colour in specs)
            layer_specs += prefixed
            selections.append((family, prepared, prefixed, prepare))

    if include_single_rail:
        single_specs = (
            ("SupplementS1", "S1", 18 if include_r2_exit else 14,
             _S1_MODEL_SHA256, _S1_SOURCE_NAMES,
             "existing-02", "retained-S1-L1-reference-package"),
            ("SupplementS1J", "S1J", 6 if include_r1_exit else 4,
             _S1J_MODEL_SHA256, _S1J_SOURCE_NAMES,
             "basic-04", "fixed-basic-source-context"),
            ("L1", "L1", (26 if correct_heel_l1 else 16)
             + (2 if include_r1_exit else 0),
             _L1_MODEL_SHA256, _L1_SOURCE_NAMES,
             "existing-02", "retained-S1-L1-reference-package"),
        )
        for group, family, count, digest, names, run, context in single_specs:
            placements = prepare_single_rail_placements(placements_by_family[group])
            ids = {placement.position_id for placement in placements}
            require(len(placements) == count and not identities.intersection(ids),
                    "single-rail placements are incomplete or overlap another group")
            identities.update(ids)
            prepared, specs, prepare = _prepare_catalogue_family(
                catalogue_path, placements, None, receipt,
                family=family, placement_type=SingleRailPlacement,
                model_sha256=digest, source_names=names,
                run=run, source_context=context,
            )
            prefixed = tuple((group + "_" + name, title, colour)
                             for name, title, colour in specs)
            layer_specs += prefixed
            selections.append((group, prepared, prefixed, prepare))

    def prepare_layers():
        layers = _context_layers(context_shapes)
        families = {}
        verifiers = []
        for label, _prepared, specs, prepare in selections:
            components, result, verify = prepare()
            start = len(layers)
            layers += components
            verifiers.append((start, len(layers), verify))
            result.pop("source_receipt")
            result["family"] = label
            result["layers"] = [dict(_measure_layer(shape), name=spec[0])
                                for spec, shape in zip(specs, components)]
            families[label] = result
        result = {
            "contract_id": ("tracktemplate.private-catalogue-crossover.v8"
                            if crossing_splits else
                            "tracktemplate.private-catalogue-crossover.v7"
                            if crossing_pairs else
                            "tracktemplate.private-catalogue-crossover.v6"
                            if zy else
                            "tracktemplate.private-catalogue-crossover.v5"
                            if include_single_rail else
                            "tracktemplate.private-catalogue-crossover.v4"
                            if include_check_ends else
                            "tracktemplate.private-catalogue-crossover.v3"
                            if include_central_cc else
                            "tracktemplate.private-catalogue-crossover.v2"),
            "source_receipt": receipt,
            "families": families,
            "family_count": len({item["label"] for item in families.values()}),
            "assembly_group_count": len(families),
            "placement_count": len(identities),
            "component_count": sum(item["component_count"]
                                   for item in families.values()),
            "layer_count": len(layers),
            "solid_count": sum(item["solid_count"]
                               for item in families.values()),
            "layers": [dict(_measure_layer(shape), name=spec[0])
                       for spec, shape in zip(layer_specs, layers)],
            "project_status": "reference-only",
            "intended_uses": ["private-development"],
            "production_geometry_authorized": False,
            "length_unit": "mm",
            "length_basis": "model",
            "scale_denominator": "76.2",
            "placement": "outer-proper-planar-frame-on-retained-brep",
            "geometry_rebuilt": False,
            "track_placements_added": len(identities),
            "limits": [
                "Only source-supported qualified assemblies are placed.",
                "Every other source position keeps its evidenced exclusion.",
                "No physical-fit, production, export or phase acceptance.",
                "Source overlaps and hidden mating closures remain.",
                "No source XML placement, scale or frame conversion "
                "reapplied.",
                "Unresolved key direction remains.",
            ],
        }
        if include_central_cc:
            result["placement"] = "proper-source-component-frames-on-retained-brep"

        def verify_layers(stored):
            require(len(stored) == len(layers), "stored layer count changed")
            for actual, expected in zip(stored[:2], layers[:2]):
                require(_same_presented_shape(actual, expected),
                        "stored context geometry or placement changed")
                _measure_layer(actual)
                require(not actual.Faces and not actual.Solids
                        and len(actual.Edges) == len(expected.Edges),
                        "stored context is no longer the copied wires")
            for start, end, verify in verifiers:
                verify(stored[start:end])

        return layers, result, verify_layers

    def verify_inputs():
        verify_source()
        for _label, prepared, _specs, _prepare in selections:
            if (prepared.run not in CONTEXT_IDS
                    and not (zy and prepared.run in ZY_CONTEXT_IDS)
                    and not (crossing_pairs and prepared.run
                             in CROSSING_PAIR_CONTEXT_IDS)
                    and not (crossing_splits and prepared.run
                             in CROSSING_SPLIT_CONTEXT_IDS)):
                verify_catalogue_sources(prepared)
        if paired:
            verify_paired_catalogue(paired)
        if zy:
            verify_zy_catalogue(zy)
        if crossing_pairs:
            verify_crossing_pair_catalogue(crossing_pairs)
        if crossing_splits:
            verify_crossing_split_catalogue(crossing_splits)

    return _materialise_preview(
        family, receipt, layer_specs, prepare_layers, verify_inputs,
        title_suffix="retained catalogue assemblies",
    )
