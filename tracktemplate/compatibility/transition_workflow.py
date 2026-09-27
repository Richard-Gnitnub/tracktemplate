"""Modular-only composition for the inherited B15 GUI workflow host."""

from dataclasses import dataclass

from tracktemplate.compatibility.b15_workflow_host import (
    EXPECTED_WORKFLOW_VERSION,
    FUNCTION_NAMES,
    B15WorkflowHostError,
    load_b15_workflow_host,
)


MODULAR_CALCULATION_ROUTE = "modular"
WORKFLOW_CONTRACT_ID = "tracktemplate:phase7:platform-top-heights:1"
CORE_LAYOUT_EXPORT_CONTRACT_ID = "tracktemplate:phase7:core-layout-export:1"
CORE_LAYOUT_EXPORT_HOST_BINDING = "run_production_export"
CORE_LAYOUT_EXPORT_HOST_OPERATIONS = (
    ("execute_export_tasks", "execute_export_tasks"),
    ("build_manifest_rows", "build_manifest_rows"),
    ("write_export_manifest", "write_export_manifest"),
    ("failed_export_report", "_failed_export_report"),
    ("skipped_export_report", "_skipped_export_report"),
)
PRODUCT_FUNCTION_NAMES = FUNCTION_NAMES + (
    "main_circle_centre", "clothoid_exit_displacement",
    "build_concentric_core", "add_common_straight_extensions",
    "build_straight_route",
    "alignment_station_data", "interpolate_alignment_station",
    "mirror_alignment_for_turn",
    "platform_transition_displacement",
    "platform_peak_curvature_factor",
    "solve_platform_shape_parameter",
    "build_platform_core",
    "signed_side_factor", "effective_constant_radius",
    "prepare_track_alignment", "validate_connected_straight_routes",
    "validate_platform_inputs",
    "resolve_platform_longitudinal_bounds",
    "calculate_platform_top_heights",
    "alignment_progress_at_station", "station_for_progress_heading",
    "platform_coverage_bounds",
)
PRODUCT_CALLER_ROUTES = (
    ("main_circle_centre", ("clothoid_entry_displacement",)),
    (
        "build_concentric_core",
        ("clothoid_entry_displacement", "clothoid_exit_displacement"),
    ),
    (
        "prepare_track_alignment",
        ("signed_side_factor", "effective_constant_radius",
         "transition_start_signed_offset", "solve_transition_length",
         "build_concentric_core", "solve_platform_shape_parameter",
         "build_platform_core"),
    ),
    (
        "build_platform_core",
        ("platform_transition_displacement",
         "platform_peak_curvature_factor"),
    ),
    (
        "run_macro",
        ("main_circle_centre", "build_concentric_core",
         "prepare_track_alignment", "signed_side_factor",
         "add_common_straight_extensions", "alignment_station_data",
         "interpolate_alignment_station", "mirror_alignment_for_turn",
         "validate_connected_straight_routes"),
    ),
    ("build_straight_routes", ("build_straight_route",)),
    (
        "alignment_progress_at_station",
        ("interpolate_alignment_station",),
    ),
    (
        "station_for_progress_heading",
        ("alignment_progress_at_station",),
    ),
    (
        "platform_coverage_bounds",
        ("alignment_station_data", "alignment_progress_at_station"),
    ),
    (
        "sample_station_interval",
        ("interpolate_alignment_station",),
    ),
    (
        "_project_centreline_to_reference_normal",
        ("interpolate_alignment_station",),
    ),
    (
        "_offset_point_towards_reference",
        ("interpolate_alignment_station",),
    ),
    (
        "calculate_platform_boundaries",
        ("alignment_station_data", "interpolate_alignment_station",
         "validate_platform_inputs", "resolve_platform_longitudinal_bounds",
         "calculate_platform_top_heights",
         "platform_coverage_bounds", "station_for_progress_heading",
         "alignment_progress_at_station"),
    ),
    (
        "create_between_alignments_face",
        ("alignment_station_data", "interpolate_alignment_station"),
    ),
    (
        "_project_formation_point_to_reference",
        ("interpolate_alignment_station",),
    ),
    (
        "_simple_formation_swept_face",
        ("alignment_station_data",),
    ),
    (
        "create_section_mask_face",
        ("alignment_station_data", "interpolate_alignment_station"),
    ),
    (
        "create_section_masks",
        ("alignment_station_data", "interpolate_alignment_station"),
    ),
    (
        "apply_registration_features",
        ("alignment_station_data", "interpolate_alignment_station"),
    ),
    (
        "find_section_number_origin",
        ("alignment_station_data", "interpolate_alignment_station"),
    ),
    (
        "alignment_station_at_cross_section",
        ("alignment_station_data",),
    ),
    (
        "calculate_template_section_stations",
        ("alignment_station_data", "interpolate_alignment_station"),
    ),
    (
        "apply_track_template_joints",
        ("alignment_station_data", "interpolate_alignment_station"),
    ),
    (
        "create_track_template_fixing_holes",
        ("alignment_station_data", "interpolate_alignment_station"),
    ),
    (
        "prepare_straight_route_production",
        ("alignment_station_data", "interpolate_alignment_station"),
    ),
    (
        "turnout_host_alignment",
        ("alignment_station_data",),
    ),
    (
        "map_turnout_local_point",
        ("interpolate_alignment_station",),
    ),
    (
        "_turnout_interval_samples",
        ("interpolate_alignment_station",),
    ),
    (
        "_crossover_nearest_point_on_alignment",
        ("interpolate_alignment_station",),
    ),
    (
        "_crossover_host_travel_vector",
        ("interpolate_alignment_station",),
    ),
    (
        "_crossover_automatic_hand",
        ("interpolate_alignment_station",),
    ),
    (
        "_crossover_orientation_b",
        ("interpolate_alignment_station",),
    ),
    (
        "solve_rea_c10_crossover_geometry",
        ("interpolate_alignment_station",),
    ),
    (
        "resolve_automatic_turnout_crossover_extension",
        ("interpolate_alignment_station",),
    ),
    (
        "_timber_record_from_layout",
        ("interpolate_alignment_station",),
    ),
    (
        "crossover_inherited_timber_records",
        ("interpolate_alignment_station",),
    ),
    (
        "crossover_shared_timber_envelope_context",
        ("interpolate_alignment_station",),
    ),
    (
        "_crossover_integration_alignment_signature",
        ("interpolate_alignment_station",),
    ),
    (
        "_chair_turnout_timber_records",
        ("interpolate_alignment_station",),
    ),
    (
        "CrossoverManagerPanel.use_picked_crossover_position",
        ("interpolate_alignment_station",),
    ),
)

__all__ = (
    "MODULAR_CALCULATION_ROUTE",
    "ModularTransitionWorkflowSession",
    "TransitionWorkflowError",
    "load_modular_transition_workflow_session",
)


class TransitionWorkflowError(RuntimeError):
    """The modular-only inherited workflow could not be composed safely."""


@dataclass(frozen=True)
class _ConcentricCoreAdapter:
    """Convert only fresh core points for the temporary inherited host."""

    calculation: object
    vector_factory: object

    def __call__(
        self,
        circle_centre,
        radius,
        entry_transition,
        exit_transition,
        total_angle,
        label,
    ):
        result = self.calculation(
            circle_centre, radius, entry_transition, exit_transition,
            total_angle, label,
        )
        result["points"] = [
            self.vector_factory(float(x), float(y), 0.0)
            for x, y in result["points"]
        ]
        return result


@dataclass(frozen=True)
class _PlatformCoreAdapter:
    """Convert only fresh platform-core points for the inherited host."""

    calculation: object
    vector_factory: object

    def __call__(
        self,
        circle_centre,
        radius,
        entry_transition,
        exit_transition,
        entry_shape_parameter,
        exit_shape_parameter,
        total_angle,
        label,
    ):
        result = self.calculation(
            circle_centre,
            radius,
            entry_transition,
            exit_transition,
            entry_shape_parameter,
            exit_shape_parameter,
            total_angle,
            label,
        )
        result["points"] = [
            self.vector_factory(float(x), float(y), 0.0)
            for x, y in result["points"]
        ]
        return result


@dataclass(frozen=True)
class _PrepareTrackAlignmentAdapter:
    """Convert only fresh prepared-alignment points for the inherited host."""

    calculation: object
    vector_factory: object

    def __call__(
        self,
        config,
        circle_centre,
        main_radius,
        total_angle,
        main_alignment,
    ):
        result = self.calculation(
            config,
            circle_centre,
            main_radius,
            total_angle,
            main_alignment,
        )
        result["points"] = [
            self.vector_factory(float(x), float(y), 0.0)
            for x, y in result["points"]
        ]
        return result


@dataclass(frozen=True)
class _CommonStraightExtensionsAdapter:
    """Apply neutral extension results to the existing inherited records."""

    calculation: object
    vector_factory: object

    def __call__(self, alignments, total_angle):
        if not alignments:
            return
        inputs = [
            {
                "start": item["start"], "end": item["end"],
                "core_length": item["core_length"],
            }
            for item in alignments
        ]
        results = self.calculation(inputs, total_angle)
        for item, result in zip(alignments, results):
            points = item["points"]
            headings = item["headings"]
            if result["entry_point"] is not None:
                x, y = result["entry_point"]
                points.insert(0, self.vector_factory(float(x), float(y), 0.0))
                headings.insert(0, 0.0)
            if result["exit_point"] is not None:
                x, y = result["exit_point"]
                points.append(self.vector_factory(float(x), float(y), 0.0))
                headings.append(total_angle)
            item["entry_extension"] = result["entry_extension"]
            item["exit_extension"] = result["exit_extension"]
            item["total_length"] = result["total_length"]
            item["extended_start"] = result["extended_start"]
            item["extended_end"] = result["extended_end"]


@dataclass(frozen=True)
class _StraightRouteAdapter:
    """Keep host normalization and fresh-vector construction at composition."""

    calculation: object
    vector_factory: object
    config_cloner: object
    connected_template_thickness: object

    def __call__(self, config, curve_alignments):
        config = self.config_cloner(config)
        inputs = []
        if (
            config["enabled"]
            and (config["create_template"] or config["show_centreline"])
            and config["connection_mode"] != "Independent datum"
            and curve_alignments
        ):
            for source in curve_alignments:
                points = list(source.get("points", []))
                headings = list(source.get("headings", []))
                valid_counts = len(points) >= 2 and len(points) == len(headings)
                item = {
                    "point_count": len(points),
                    "heading_count": len(headings),
                    "start": (points[0].x, points[0].y) if valid_counts else None,
                    "end": (points[-1].x, points[-1].y) if valid_counts else None,
                    "start_heading": headings[0] if valid_counts else None,
                    "end_heading": headings[-1] if valid_counts else None,
                }
                for key in (
                    "name", "width", "create_template", "show_centreline",
                ):
                    if key in source:
                        item[key] = source[key]
                inputs.append(item)
        result = self.calculation(
            config, inputs, self.connected_template_thickness,
        )
        if result is None:
            return None
        for item in result["alignments"]:
            first, second = item["points"]
            # The inherited exit allocates its remote endpoint before its join.
            if config["connection_mode"] == "Curve exit":
                finish = self.vector_factory(
                    float(second[0]), float(second[1]), 0.0,
                )
                start = self.vector_factory(
                    float(first[0]), float(first[1]), 0.0,
                )
            else:
                start = self.vector_factory(
                    float(first[0]), float(first[1]), 0.0,
                )
                finish = self.vector_factory(
                    float(second[0]), float(second[1]), 0.0,
                )
            item["points"] = [start, finish]
        return result


@dataclass(frozen=True)
class _StationXYPointView:
    """Read one live host coordinate without passing its point to the API."""

    _point: object

    def __getitem__(self, component):
        if component == 0:
            return self._point.x
        if component == 1:
            return self._point.y
        raise IndexError(component)


@dataclass(frozen=True)
class _StationPointSequenceView:
    """Wrap only the host point selected by the inherited integer index."""

    _points: object

    def __getitem__(self, index):
        return _StationXYPointView(self._points[index])


class _StationAlignmentView:
    """Keep the inherited snapshot and defer optional field access."""

    def __init__(self, alignment):
        self._alignment = alignment
        self.points = None

    def get(self, key, default):
        value = self._alignment.get(key, default)
        if key == "points":
            self.points = list(value)
            return (_StationXYPointView(point) for point in self.points)
        return value


@dataclass(frozen=True)
class _ConnectedStraightAlignmentsView:
    """Expose curve records without reading their native points early."""

    _alignments: object

    def __len__(self):
        return len(self._alignments)

    def __iter__(self):
        for alignment in self._alignments:
            yield _StationAlignmentView(alignment)


@dataclass(frozen=True)
class _ConnectedStraightRouteView:
    """Snapshot only the alignment list read by the selected check."""

    _route: object

    def get(self, key, *default):
        value = self._route.get(key, *default)
        if key == "alignments":
            return (
                _StationAlignmentView(alignment) for alignment in list(value)
            )
        return value


@dataclass(frozen=True)
class _ConnectedStraightRoutesView:
    """Defer route iteration until after the inherited curve count."""

    _routes: object

    def __iter__(self):
        for route in self._routes:
            yield _ConnectedStraightRouteView(route)


@dataclass(frozen=True)
class _ConnectedStraightRoutesValidationAdapter:
    """Read native coordinates without allocating or changing vectors."""

    calculation: object

    def __call__(self, straight_routes, curve_alignments):
        return self.calculation(
            _ConnectedStraightRoutesView(straight_routes),
            _ConnectedStraightAlignmentsView(curve_alignments),
        )


@dataclass(frozen=True)
class _StationDataView:
    """Expose neutral component reads in the original data lookup order."""

    _data: object

    def __getitem__(self, key):
        value = self._data[key]
        if key == "points":
            return _StationPointSequenceView(value)
        return value


@dataclass(frozen=True)
class _AlignmentStationDataAdapter:
    """Restore original alignment and shallow point identities after indexing."""

    calculation: object

    def __call__(self, alignment):
        view = _StationAlignmentView(alignment)
        result = self.calculation(view)
        result["alignment"] = alignment
        result["points"] = view.points
        return result


@dataclass(frozen=True)
class _AlignmentStationInterpolationAdapter:
    """Allocate the host point before evaluating the captured heading."""

    calculation: object
    vector_factory: object

    def __call__(self, data, station):
        result = self.calculation(_StationDataView(data), station)
        x, y = result.point
        point = self.vector_factory(float(x), float(y), 0.0)
        heading = result.heading
        return point, heading


@dataclass(frozen=True)
class _AlignmentProgressAdapter:
    """Keep the inherited point allocation before reading turn progress."""

    calculation: object
    interpolation: object

    def __call__(self, data, station, turn_sign):
        def heading_at_station(_view, selected_station):
            _point, heading = self.interpolation(data, selected_station)
            return heading

        return self.calculation(
            _StationDataView(data), station, turn_sign,
            _heading_at_station=heading_at_station,
        )


@dataclass(frozen=True)
class _StationForProgressAdapter:
    """Keep the selected host interpolation at every bisection point."""

    calculation: object
    progress: object

    def __call__(self, data, target_progress, turn_sign):
        def progress_at_station(_view, station, selected_sign):
            return self.progress(data, station, selected_sign)

        return self.calculation(
            _StationDataView(data), target_progress, turn_sign,
            _progress_at_station=progress_at_station,
        )


@dataclass(frozen=True)
class _CoverageAlignmentView:
    """Expose only inherited mapping reads to the Core coverage rule."""

    alignment: object

    def get(self, key, default):
        return self.alignment.get(key, default)


@dataclass(frozen=True)
class _CoverageAlignmentsView:
    """Preserve the original truth test and lazy alignment iteration."""

    alignments: object

    def __bool__(self):
        return bool(self.alignments)

    def __iter__(self):
        for alignment in self.alignments:
            yield _CoverageAlignmentView(alignment)


@dataclass(frozen=True)
class _PlatformCoverageAdapter:
    """Keep host points outside Core and reuse selected station adapters."""

    calculation: object
    station_data: object
    progress: object

    def _station_data(self, alignment):
        return _StationDataView(self.station_data(alignment.alignment))

    def _progress_at_station(self, data, station, turn_sign):
        return self.progress(data._data, station, turn_sign)

    def __call__(self, alignments, coverage, turn_sign):
        return self.calculation(
            _CoverageAlignmentsView(alignments), coverage, turn_sign,
            _station_data=self._station_data,
            _progress_at_station=self._progress_at_station,
        )


@dataclass(frozen=True)
class _MirrorAlignmentView:
    """Read neutral points lazily while retaining inherited mapping access."""

    _alignment: object

    def __getitem__(self, key):
        value = self._alignment[key]
        if key == "points":
            return (_StationXYPointView(point) for point in value)
        return value

    def __contains__(self, key):
        return key in self._alignment


@dataclass(frozen=True)
class _MirrorAlignmentForTurnAdapter:
    """Apply each reflection stage before reading the next inherited field."""

    calculation: object
    vector_factory: object

    def __call__(self, alignment, turn_sign):
        updates = self.calculation(_MirrorAlignmentView(alignment), turn_sign)
        for key, value in updates:
            if key == "points":
                value = [
                    self.vector_factory(float(x), float(y), 0.0)
                    for x, y in value
                ]
            alignment[key] = value


class ModularTransitionWorkflowSession:
    """One inherited GUI host permanently bound to modular calculations."""

    def __init__(self, host, modular_functions):
        self._host = host
        self._modular_functions = dict(modular_functions)
        if (
            set(self._modular_functions) != set(PRODUCT_FUNCTION_NAMES)
            or not all(
                callable(self._modular_functions[name])
                for name in PRODUCT_FUNCTION_NAMES
            )
        ):
            raise TransitionWorkflowError(
                "The complete twenty-five-function modular workflow is unavailable."
            )
        platform_globals = getattr(
            self._modular_functions["solve_platform_shape_parameter"],
            "__globals__",
            None,
        )
        if (
            not isinstance(platform_globals, dict)
            or any(
                getattr(self._modular_functions[name], "__globals__", None)
                is not platform_globals
                for name in (
                    "platform_transition_displacement",
                    "platform_peak_curvature_factor",
                    "build_platform_core",
                )
            )
        ):
            raise TransitionWorkflowError(
                "The platform-transition domain closure is unavailable."
            )
        self._platform_transition_angle = platform_globals.get(
            "platform_transition_angle"
        )
        self._platform_line_offset = platform_globals.get(
            "platform_line_offset"
        )
        self._platform_parameter_grid = platform_globals.get(
            "_platform_parameter_grid"
        )
        if not all(
            callable(function)
            and getattr(function, "__globals__", None) is platform_globals
            for function in (
                self._platform_transition_angle,
                self._platform_line_offset,
                self._platform_parameter_grid,
            )
        ):
            raise TransitionWorkflowError(
                "The platform-transition domain closure is unavailable."
            )
        preparation_calculation = self._modular_functions[
            "prepare_track_alignment"
        ]
        preparation_globals = getattr(
            preparation_calculation, "__globals__", None,
        )
        preparation_code = getattr(preparation_calculation, "__code__", None)
        self._preparation_left_normal = (
            preparation_globals.get("_left_normal")
            if isinstance(preparation_globals, dict)
            else None
        )
        self._preparation_dot_xy = (
            preparation_globals.get("_dot_xy")
            if isinstance(preparation_globals, dict)
            else None
        )
        if (
            preparation_globals is not platform_globals
            or preparation_code is None
            or not {"_left_normal", "_dot_xy"} <= set(
                preparation_code.co_names
            )
            or not all(
                callable(function)
                and getattr(function, "__globals__", None)
                is preparation_globals
                for function in (
                    self._preparation_left_normal,
                    self._preparation_dot_xy,
                )
            )
        ):
            raise TransitionWorkflowError(
                "The track-preparation domain closure is unavailable."
            )
        validation = self._modular_functions[
            "validate_connected_straight_routes"
        ]
        validation_globals = getattr(validation, "__globals__", None)
        validation_code = getattr(validation, "__code__", None)
        self._connected_heading_delta = (
            validation_globals.get("_straight_heading_delta")
            if isinstance(validation_globals, dict) else None
        )
        if (
            validation_globals is not preparation_globals
            or validation_code is None
            or not {"_dot_xy", "_straight_heading_delta"} <= set(
                validation_code.co_names
            )
            or not callable(self._connected_heading_delta)
            or getattr(self._connected_heading_delta, "__globals__", None)
            is not validation_globals
            or validation_globals.get("_dot_xy")
            is not self._preparation_dot_xy
        ):
            raise TransitionWorkflowError(
                "The connected-straight validation domain closure is "
                "unavailable."
            )
        vector_factory = getattr(
            getattr(self.module, "App", None), "Vector", None,
        )
        if not callable(vector_factory):
            raise TransitionWorkflowError(
                "The inherited host vector constructor is unavailable."
            )
        self._host_functions = dict(self._modular_functions)
        self._host_functions["build_concentric_core"] = _ConcentricCoreAdapter(
            self._modular_functions["build_concentric_core"], vector_factory,
        )
        self._host_functions["build_platform_core"] = _PlatformCoreAdapter(
            self._modular_functions["build_platform_core"], vector_factory,
        )
        self._host_functions["prepare_track_alignment"] = (
            _PrepareTrackAlignmentAdapter(
                self._modular_functions["prepare_track_alignment"],
                vector_factory,
            )
        )
        self._host_functions["add_common_straight_extensions"] = (
            _CommonStraightExtensionsAdapter(
                self._modular_functions["add_common_straight_extensions"],
                vector_factory,
            )
        )
        config_cloner = getattr(self.module, "clone_straight_config", None)
        if not callable(config_cloner) or not hasattr(
            self.module, "TEMPLATE_THICKNESS",
        ):
            raise TransitionWorkflowError(
                "The inherited straight-route configuration is unavailable."
            )
        self._host_functions["build_straight_route"] = _StraightRouteAdapter(
            self._modular_functions["build_straight_route"], vector_factory,
            config_cloner, self.module.TEMPLATE_THICKNESS,
        )
        self._host_functions["validate_connected_straight_routes"] = (
            _ConnectedStraightRoutesValidationAdapter(
                self._modular_functions["validate_connected_straight_routes"],
            )
        )
        self._host_functions["alignment_station_data"] = (
            _AlignmentStationDataAdapter(
                self._modular_functions["alignment_station_data"],
            )
        )
        self._host_functions["interpolate_alignment_station"] = (
            _AlignmentStationInterpolationAdapter(
                self._modular_functions["interpolate_alignment_station"],
                vector_factory,
            )
        )
        self._host_functions["alignment_progress_at_station"] = (
            _AlignmentProgressAdapter(
                self._modular_functions["alignment_progress_at_station"],
                self._host_functions["interpolate_alignment_station"],
            )
        )
        self._host_functions["station_for_progress_heading"] = (
            _StationForProgressAdapter(
                self._modular_functions["station_for_progress_heading"],
                self._host_functions["alignment_progress_at_station"],
            )
        )
        self._host_functions["platform_coverage_bounds"] = (
            _PlatformCoverageAdapter(
                self._modular_functions["platform_coverage_bounds"],
                self._host_functions["alignment_station_data"],
                self._host_functions["alignment_progress_at_station"],
            )
        )
        self._host_functions["mirror_alignment_for_turn"] = (
            _MirrorAlignmentForTurnAdapter(
                self._modular_functions["mirror_alignment_for_turn"],
                vector_factory,
            )
        )
        self._bind_modular()

    def _bind_modular(self):
        namespace = self.module.__dict__
        missing = object()
        previous = {
            name: namespace.get(name, missing)
            for name in PRODUCT_FUNCTION_NAMES
        }
        try:
            namespace.update(self._host_functions)
            self._validate_binding()
        except Exception:
            for name, value in previous.items():
                if value is missing:
                    namespace.pop(name, None)
                else:
                    namespace[name] = value
            raise

    def _validate_binding(self):
        """Verify selected domain and host edges without repairing them."""
        namespace = self.module.__dict__
        for name in PRODUCT_FUNCTION_NAMES:
            if namespace.get(name) is not self._host_functions[name]:
                raise TransitionWorkflowError(
                    "The modular workflow has a mixed {!r} binding.".format(
                        name,
                    )
                )

        adapter = namespace["build_concentric_core"]
        if (
            type(adapter) is not _ConcentricCoreAdapter
            or adapter.calculation is not self._modular_functions[
                "build_concentric_core"
            ]
            or adapter.vector_factory is not getattr(
                getattr(self.module, "App", None), "Vector", None,
            )
        ):
            raise TransitionWorkflowError(
                "The modular workflow core adapter is unavailable."
            )

        platform_core = namespace["build_platform_core"]
        if (
            type(platform_core) is not _PlatformCoreAdapter
            or platform_core.calculation is not self._modular_functions[
                "build_platform_core"
            ]
            or platform_core.vector_factory is not getattr(
                getattr(self.module, "App", None), "Vector", None,
            )
        ):
            raise TransitionWorkflowError(
                "The modular workflow platform-core adapter is unavailable."
            )

        preparation = namespace["prepare_track_alignment"]
        if (
            type(preparation) is not _PrepareTrackAlignmentAdapter
            or preparation.calculation is not self._modular_functions[
                "prepare_track_alignment"
            ]
            or preparation.vector_factory is not getattr(
                getattr(self.module, "App", None), "Vector", None,
            )
        ):
            raise TransitionWorkflowError(
                "The modular workflow track-preparation adapter is "
                "unavailable."
            )
        preparation_calculation = self._modular_functions[
            "prepare_track_alignment"
        ]
        preparation_globals = getattr(
            preparation_calculation, "__globals__", None,
        )
        preparation_code = getattr(preparation_calculation, "__code__", None)
        if (
            not isinstance(preparation_globals, dict)
            or preparation_code is None
            or not {"_left_normal", "_dot_xy"} <= set(
                preparation_code.co_names
            )
            or preparation_globals.get("_left_normal")
            is not self._preparation_left_normal
            or preparation_globals.get("_dot_xy")
            is not self._preparation_dot_xy
        ):
            raise TransitionWorkflowError(
                "The track-preparation domain closure is unavailable."
            )

        extensions = namespace["add_common_straight_extensions"]
        if (
            type(extensions) is not _CommonStraightExtensionsAdapter
            or extensions.calculation is not self._modular_functions[
                "add_common_straight_extensions"
            ]
            or extensions.vector_factory is not getattr(
                getattr(self.module, "App", None), "Vector", None,
            )
        ):
            raise TransitionWorkflowError(
                "The modular workflow straight-extension adapter is "
                "unavailable."
            )

        straight = namespace["build_straight_route"]
        if (
            type(straight) is not _StraightRouteAdapter
            or straight.calculation is not self._modular_functions[
                "build_straight_route"
            ]
            or straight.vector_factory is not getattr(
                getattr(self.module, "App", None), "Vector", None,
            )
            or straight.config_cloner is not getattr(
                self.module, "clone_straight_config", None,
            )
            or straight.connected_template_thickness is not getattr(
                self.module, "TEMPLATE_THICKNESS", None,
            )
        ):
            raise TransitionWorkflowError(
                "The modular workflow straight-route adapter is unavailable."
            )

        validation = namespace["validate_connected_straight_routes"]
        if (
            type(validation) is not _ConnectedStraightRoutesValidationAdapter
            or validation.calculation is not self._modular_functions[
                "validate_connected_straight_routes"
            ]
        ):
            raise TransitionWorkflowError(
                "The modular workflow connected-straight validation adapter "
                "is unavailable."
            )
        validation_globals = getattr(
            validation.calculation, "__globals__", None,
        )
        if (
            validation_globals is not preparation_globals
            or validation_globals.get("_dot_xy")
            is not self._preparation_dot_xy
            or validation_globals.get("_straight_heading_delta")
            is not self._connected_heading_delta
        ):
            raise TransitionWorkflowError(
                "The connected-straight validation domain closure is "
                "unavailable."
            )

        platform_input_validation = namespace["validate_platform_inputs"]
        platform_input_globals = getattr(
            platform_input_validation, "__globals__", None,
        )
        platform_input_code = getattr(
            platform_input_validation, "__code__", None,
        )
        platform_input_constants = (
            "GEOMETRY_TOLERANCE", "TEMPLATE_THICKNESS",
            "PLATFORM_BETWEEN", "PLATFORM_OUTSIDE",
            "PLATFORM_END_TAPERED", "PLATFORM_EDGES_ONLY",
            "PLATFORM_SOLID",
        )
        if (
            platform_input_validation is not self._modular_functions[
                "validate_platform_inputs"
            ]
            or platform_input_globals is not preparation_globals
            or platform_input_code is None
            or not set(platform_input_constants) <= set(
                platform_input_code.co_names
            )
            or any(
                type(platform_input_globals.get(name))
                is not type(getattr(self.module, name, None))
                or platform_input_globals.get(name)
                != getattr(self.module, name, None)
                for name in platform_input_constants
            )
        ):
            raise TransitionWorkflowError(
                "The platform-input validation domain closure is unavailable."
            )

        platform_bounds = namespace["resolve_platform_longitudinal_bounds"]
        platform_bounds_globals = getattr(platform_bounds, "__globals__", None)
        platform_bounds_code = getattr(platform_bounds, "__code__", None)
        if (
            platform_bounds is not self._modular_functions[
                "resolve_platform_longitudinal_bounds"
            ]
            or platform_bounds_globals is not preparation_globals
            or platform_bounds_code is None
            or "GEOMETRY_TOLERANCE" not in platform_bounds_code.co_names
            or type(platform_bounds_globals.get("GEOMETRY_TOLERANCE"))
            is not type(getattr(self.module, "GEOMETRY_TOLERANCE", None))
            or platform_bounds_globals.get("GEOMETRY_TOLERANCE")
            != getattr(self.module, "GEOMETRY_TOLERANCE", None)
        ):
            raise TransitionWorkflowError(
                "The platform longitudinal-bounds domain closure is "
                "unavailable."
            )

        platform_heights = namespace["calculate_platform_top_heights"]
        platform_heights_globals = getattr(
            platform_heights, "__globals__", None,
        )
        platform_heights_code = getattr(platform_heights, "__code__", None)
        platform_height_constants = (
            "GEOMETRY_TOLERANCE", "TEMPLATE_THICKNESS",
            "PLATFORM_END_TAPERED", "PLATFORM_SOLID",
        )
        if (
            platform_heights is not self._modular_functions[
                "calculate_platform_top_heights"
            ]
            or platform_heights_globals is not preparation_globals
            or platform_heights_code is None
            or not set(platform_height_constants) <= set(
                platform_heights_code.co_names
            )
            or any(
                type(platform_heights_globals.get(name))
                is not type(getattr(self.module, name, None))
                or platform_heights_globals.get(name)
                != getattr(self.module, name, None)
                for name in platform_height_constants
            )
        ):
            raise TransitionWorkflowError(
                "The platform top-height domain closure is unavailable."
            )

        station_data = namespace["alignment_station_data"]
        if (
            type(station_data) is not _AlignmentStationDataAdapter
            or station_data.calculation is not self._modular_functions[
                "alignment_station_data"
            ]
        ):
            raise TransitionWorkflowError(
                "The modular workflow station-data adapter is unavailable."
            )

        interpolation = namespace["interpolate_alignment_station"]
        if (
            type(interpolation) is not _AlignmentStationInterpolationAdapter
            or interpolation.calculation is not self._modular_functions[
                "interpolate_alignment_station"
            ]
            or interpolation.vector_factory is not getattr(
                getattr(self.module, "App", None), "Vector", None,
            )
        ):
            raise TransitionWorkflowError(
                "The modular workflow station-interpolation adapter is "
                "unavailable."
            )

        progress = namespace["alignment_progress_at_station"]
        station_for_progress = namespace["station_for_progress_heading"]
        coverage = namespace["platform_coverage_bounds"]
        if (
            type(progress) is not _AlignmentProgressAdapter
            or progress.calculation is not self._modular_functions[
                "alignment_progress_at_station"
            ]
            or progress.interpolation is not interpolation
            or type(station_for_progress) is not _StationForProgressAdapter
            or station_for_progress.calculation is not self._modular_functions[
                "station_for_progress_heading"
            ]
            or station_for_progress.progress is not progress
            or type(coverage) is not _PlatformCoverageAdapter
            or coverage.calculation is not self._modular_functions[
                "platform_coverage_bounds"
            ]
            or coverage.station_data is not station_data
            or coverage.progress is not progress
        ):
            raise TransitionWorkflowError(
                "The modular workflow platform station adapters are unavailable."
            )
        constants = (
            "PLATFORM_CORE", "PLATFORM_CONSTANT", "PLATFORM_ENTRY",
            "PLATFORM_EXIT",
        )
        coverage_globals = getattr(coverage.calculation, "__globals__", None)
        if (
            coverage_globals is not preparation_globals
            or any(
                type(coverage_globals.get(name))
                is not type(getattr(self.module, name, None))
                or coverage_globals.get(name) != getattr(self.module, name, None)
                for name in constants
            )
        ):
            raise TransitionWorkflowError(
                "The platform coverage domain constants are unavailable."
            )

        mirror = namespace["mirror_alignment_for_turn"]
        if (
            type(mirror) is not _MirrorAlignmentForTurnAdapter
            or mirror.calculation is not self._modular_functions[
                "mirror_alignment_for_turn"
            ]
            or mirror.vector_factory is not getattr(
                getattr(self.module, "App", None), "Vector", None,
            )
        ):
            raise TransitionWorkflowError(
                "The modular workflow handedness adapter is unavailable."
            )

        platform_solver = self._modular_functions[
            "solve_platform_shape_parameter"
        ]
        platform_globals = getattr(platform_solver, "__globals__", None)
        platform_core_calculation = self._modular_functions[
            "build_platform_core"
        ]
        if getattr(
            platform_core_calculation, "__globals__", None,
        ) is not platform_globals:
            raise TransitionWorkflowError(
                "The platform-core domain closure is unavailable."
            )
        line_offset = self._platform_line_offset
        line_offset_code = getattr(line_offset, "__code__", None)
        if (
            not isinstance(platform_globals, dict)
            or getattr(line_offset, "__globals__", None) is not platform_globals
            or line_offset_code is None
            or "platform_transition_displacement"
            not in line_offset_code.co_names
            or platform_globals.get("platform_transition_displacement")
            is not self._modular_functions[
                "platform_transition_displacement"
            ]
        ):
            raise TransitionWorkflowError(
                "The modular platform line-offset route does not use its "
                "selected displacement calculation."
            )

        solver_code = getattr(platform_solver, "__code__", None)
        if (
            solver_code is None
            or not {
                "_platform_parameter_grid",
                "platform_line_offset",
                "platform_transition_angle",
                "platform_peak_curvature_factor",
            } <= set(solver_code.co_names)
            or platform_globals.get("_platform_parameter_grid")
            is not self._platform_parameter_grid
            or platform_globals.get("platform_line_offset")
            is not self._platform_line_offset
            or platform_globals.get("platform_transition_angle")
            is not self._platform_transition_angle
            or platform_globals.get("platform_peak_curvature_factor")
            is not self._modular_functions[
                "platform_peak_curvature_factor"
            ]
        ):
            raise TransitionWorkflowError(
                "The modular platform solver does not use its selected "
                "domain calculations."
            )
        nested_residuals = [
            item for item in solver_code.co_consts
            if isinstance(item, type(solver_code))
            and item.co_name == "squared_residual"
        ]
        if (
            len(nested_residuals) != 1
            or "platform_line_offset" not in nested_residuals[0].co_names
        ):
            raise TransitionWorkflowError(
                "The modular platform solver residual route is unavailable."
            )

        # Product composition owns all twenty-five current bindings. The frozen
        # three-function binder remains solely on the comparison route.
        domain_routes = (
            (
                "transition_start_signed_offset",
                ("clothoid_entry_displacement",),
            ),
            ("solve_transition_length", ("transition_start_signed_offset",)),
        ) + PRODUCT_CALLER_ROUTES[:4] + tuple(
            route for route in PRODUCT_CALLER_ROUTES[4:]
            if route[0] in {
                "alignment_progress_at_station", "station_for_progress_heading",
                "platform_coverage_bounds",
            }
        )
        host_routes = tuple(
            route for route in PRODUCT_CALLER_ROUTES[4:]
            if route[0] not in {
                "alignment_progress_at_station", "station_for_progress_heading",
                "platform_coverage_bounds",
            }
        )
        routes = [
            (
                name, self._modular_functions[name], targets,
                self._modular_functions, False,
            )
            for name, targets in domain_routes
        ] + [
            (
                name,
                getattr(
                    namespace.get("CrossoverManagerPanel"),
                    "use_picked_crossover_position", None,
                ) if name == (
                    "CrossoverManagerPanel.use_picked_crossover_position"
                ) else namespace.get(name),
                targets, self._host_functions, True,
            )
            for name, targets in host_routes
        ]
        for caller_name, caller, targets, selected, is_host in routes:
            caller_globals = getattr(caller, "__globals__", None)
            code = getattr(caller, "__code__", None)
            if (
                not callable(caller)
                or not isinstance(caller_globals, dict)
                or code is None
                or not set(targets) <= set(code.co_names)
                or (is_host and caller_globals is not namespace)
            ):
                raise TransitionWorkflowError(
                    "The modular workflow route caller {!r} is "
                    "unavailable.".format(caller_name)
                )
            if caller_name == "_project_centreline_to_reference_normal":
                nested = [
                    item for item in code.co_consts
                    if isinstance(item, type(code))
                    and item.co_name == "point_at_station"
                ]
                if (
                    len(nested) != 1
                    or "interpolate_alignment_station"
                    not in nested[0].co_names
                ):
                    raise TransitionWorkflowError(
                        "The modular workflow route caller "
                        "'_project_centreline_to_reference_normal."
                        "point_at_station' is unavailable."
                    )
            for target in targets:
                if caller_globals.get(target) is not selected[target]:
                    raise TransitionWorkflowError(
                        "The modular workflow route caller {!r} does not use "
                        "its selected {!r}.".format(caller_name, target)
                    )

    @property
    def module(self):
        return self._host.module

    def routing_record(self):
        """Return the non-switchable composition record."""
        self._validate_binding()
        return {
            "schema_version": 16,
            "contract_id": WORKFLOW_CONTRACT_ID,
            "route": MODULAR_CALCULATION_ROUTE,
            "comparison_route_available": False,
            "function_names": list(PRODUCT_FUNCTION_NAMES),
            "caller_names": [item[0] for item in PRODUCT_CALLER_ROUTES],
            "workflow_version": EXPECTED_WORKFLOW_VERSION,
            "workflow_source_sha256": self._host.source_sha256,
            "mixed_route": False,
        }

    def launch_workflow(self):
        """Launch the inherited workflow through its modular binding."""
        self._bind_modular()
        return self._host.launch_workflow()


@dataclass(frozen=True)
class _CoreLayoutExportAdapter:
    """Supply inherited export operations to the modular application command."""

    calculation: object
    execute_export_tasks: object
    build_manifest_rows: object
    write_export_manifest: object
    failed_export_report: object
    skipped_export_report: object

    def __call__(
        self,
        doc,
        plan,
        config,
        set_id,
        platform_config,
        formation_config,
        registration_config,
        template_assembly_config,
        exporter_override=None,
    ):
        return self.calculation(
            doc,
            plan,
            config,
            set_id,
            platform_config,
            formation_config,
            registration_config,
            template_assembly_config,
            exporter_override,
            execute_export_tasks=self.execute_export_tasks,
            build_manifest_rows=self.build_manifest_rows,
            write_export_manifest=self.write_export_manifest,
            failed_export_report=self.failed_export_report,
            skipped_export_report=self.skipped_export_report,
        )


class ModularCoreLayoutWorkflowSession:
    """Add one modular export command to the selected calculation session."""

    def __init__(self, calculation_session, export_calculation):
        self._calculation_session = calculation_session
        self._host = calculation_session._host
        namespace = self.module.__dict__
        operations = {}
        for field_name, host_name in CORE_LAYOUT_EXPORT_HOST_OPERATIONS:
            operation = namespace.get(host_name)
            if not callable(operation):
                raise TransitionWorkflowError(
                    "The inherited core-layout export operation {!r} is "
                    "unavailable.".format(host_name)
                )
            operations[field_name] = operation
        if not callable(export_calculation):
            raise TransitionWorkflowError(
                "The modular core-layout export command is unavailable."
            )
        self._export_calculation = export_calculation
        self._export_adapter = _CoreLayoutExportAdapter(
            calculation=export_calculation,
            **operations,
        )
        self._bind_core_layout_export()

    @property
    def module(self):
        return self._calculation_session.module

    def _bind_core_layout_export(self):
        namespace = self.module.__dict__
        missing = object()
        previous = namespace.get(CORE_LAYOUT_EXPORT_HOST_BINDING, missing)
        try:
            namespace[CORE_LAYOUT_EXPORT_HOST_BINDING] = self._export_adapter
            self._validate_core_layout_export_binding()
        except Exception:
            if previous is missing:
                namespace.pop(CORE_LAYOUT_EXPORT_HOST_BINDING, None)
            else:
                namespace[CORE_LAYOUT_EXPORT_HOST_BINDING] = previous
            raise

    def _validate_core_layout_export_binding(self):
        namespace = self.module.__dict__
        adapter = namespace.get(CORE_LAYOUT_EXPORT_HOST_BINDING)
        if (
            type(adapter) is not _CoreLayoutExportAdapter
            or adapter is not self._export_adapter
            or adapter.calculation is not self._export_calculation
        ):
            raise TransitionWorkflowError(
                "The modular core-layout export route has a mixed binding."
            )
        for field_name, host_name in CORE_LAYOUT_EXPORT_HOST_OPERATIONS:
            operation = getattr(adapter, field_name)
            if (
                namespace.get(host_name) is not operation
                or getattr(operation, "__globals__", None) is not namespace
            ):
                raise TransitionWorkflowError(
                    "The inherited core-layout export operation {!r} "
                    "changed.".format(host_name)
                )
        caller = namespace.get("run_macro")
        code = getattr(caller, "__code__", None)
        if (
            not callable(caller)
            or getattr(caller, "__globals__", None) is not namespace
            or code is None
            or CORE_LAYOUT_EXPORT_HOST_BINDING not in code.co_names
        ):
            raise TransitionWorkflowError(
                "The inherited run_macro export caller is unavailable."
            )
        if caller.__globals__.get(
            CORE_LAYOUT_EXPORT_HOST_BINDING
        ) is not adapter:
            raise TransitionWorkflowError(
                "The inherited run_macro export caller has a mixed binding."
            )

    def routing_record(self):
        """Return the unchanged accepted calculation-routing record."""
        record = self._calculation_session.routing_record()
        self._validate_core_layout_export_binding()
        return record

    def core_layout_export_routing_record(self):
        """Return the separate modular application-command route record."""
        self._validate_core_layout_export_binding()
        return {
            "schema_version": 1,
            "contract_id": CORE_LAYOUT_EXPORT_CONTRACT_ID,
            "route": MODULAR_CALCULATION_ROUTE,
            "comparison_route_available": False,
            "command_name": "run_core_layout_export",
            "host_binding_name": CORE_LAYOUT_EXPORT_HOST_BINDING,
            "caller_name": "run_macro",
            "workflow_version": EXPECTED_WORKFLOW_VERSION,
            "workflow_source_sha256": self._host.source_sha256,
            "mixed_route": False,
        }

    def launch_workflow(self):
        """Launch after restoring and checking both selected route groups."""
        self._bind_core_layout_export()
        return self._calculation_session.launch_workflow()


def load_modular_transition_workflow_session(
    repository_root,
    modular_api,
    contract,
):
    """Load the inherited host and bind only the modular implementation."""
    try:
        modular_functions = {
            name: getattr(modular_api, name)
            for name in PRODUCT_FUNCTION_NAMES
        }
    except AttributeError as error:
        raise TransitionWorkflowError(
            "The complete modular transition calculation route is "
            "unavailable."
        ) from error

    try:
        host = load_b15_workflow_host(repository_root, contract)
    except B15WorkflowHostError as error:
        raise TransitionWorkflowError(str(error)) from error
    calculation_session = ModularTransitionWorkflowSession(
        host, modular_functions,
    )
    namespace = calculation_session.module.__dict__
    export_names = {
        CORE_LAYOUT_EXPORT_HOST_BINDING,
        *(host_name for _field_name, host_name
          in CORE_LAYOUT_EXPORT_HOST_OPERATIONS),
    }
    present = {name for name in export_names if name in namespace}
    caller = namespace.get("run_macro")
    caller_code = getattr(caller, "__code__", None)
    caller_uses_export = (
        caller_code is not None
        and CORE_LAYOUT_EXPORT_HOST_BINDING in caller_code.co_names
    )
    if not present and not caller_uses_export:
        return calculation_session
    if present != export_names or not caller_uses_export:
        raise TransitionWorkflowError(
            "The inherited core-layout export route is incomplete."
        )
    try:
        export_calculation = modular_api.run_core_layout_export
    except AttributeError as error:
        raise TransitionWorkflowError(
            "The modular core-layout export command is unavailable."
        ) from error
    return ModularCoreLayoutWorkflowSession(
        calculation_session, export_calculation,
    )
