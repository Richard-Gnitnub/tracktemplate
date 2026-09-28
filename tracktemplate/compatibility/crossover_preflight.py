"""Product-only complete-radius preflight for the inherited crossover host."""

from dataclasses import dataclass
import hashlib
import inspect
import json

from tracktemplate.domain.crossover import complete_radius_decision


PREFLIGHT_KEY = "complete_radius_preflight"


def _bound_arguments(function, args, kwargs):
    bound = inspect.signature(function).bind(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


def _number(value):
    """Encode a numeric input without display rounding."""
    return float(value).hex()


def _digest(payload):
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CrossoverPreflightAdapter:
    """Bind one analytical decision to B15 preview and commit boundaries."""

    module: object
    original_solver: object
    original_builder: object
    original_editor: object
    original_diagnostics: object
    original_trace_text: object
    original_preview_signature: object

    def _host_identity(self, host):
        if host is None:
            return None
        module = self.module
        return {
            "object_name": str(getattr(host, "Name", "")),
            "template_set_id": module.object_string_property(
                host, "TemplateSetID", "",
            ),
            "track_number": module._integer_object_property(
                host, "TrackNumber", 0,
            ),
            "track_name": module.object_string_property(
                host, "TrackName", "",
            ),
            "route_id": module.object_string_property(
                host, "RouteID", "",
            ),
            "generated_by": module.object_string_property(
                host, "GeneratedBy", "",
            ),
            "generated_role": module.object_string_property(
                host, "GeneratedRole", "",
            ),
            "export_subtype": module.object_string_property(
                host, "ExportSubtype", "",
            ),
        }

    def _host_state(self, host, supplied_data=None):
        if host is None:
            return None
        identity = self._host_identity(host)
        try:
            data = (
                supplied_data if supplied_data is not None
                else self.module.turnout_host_alignment(host)
            )
            identity["geometry"] = {
                "total_mm": _number(data["total"]),
                "stations_mm": [_number(value) for value in data["stations"]],
                "headings_rad": [
                    _number(value) for value in data["headings"]
                ],
                "points_mm": [
                    [
                        _number(point.x),
                        _number(point.y),
                        _number(point.z),
                    ]
                    for point in data["points"]
                ],
            }
        except (
            AttributeError, KeyError, RuntimeError, TypeError, ValueError,
        ) as error:
            # The inherited solver owns the operator-facing invalid-host
            # diagnostic. A previously valid cache cannot match this state.
            identity["geometry_error"] = (
                type(error).__name__, str(error),
            )
        return identity

    def _occupancy(self, doc):
        module = self.module
        turnout_fields = (
            "turnout_id", "host_object", "toe_chainage", "orientation",
            "track_gauge", "flangeway",
        )
        crossover_fields = (
            "crossover_id", "host_a_object", "host_b_object",
            "host_a_station_interval", "host_b_station_interval",
        )
        return {
            "turnouts": [
                {key: item.get(key) for key in turnout_fields}
                for item in module.existing_turnout_configs(doc)
            ],
            "crossovers": [
                {key: item.get(key) for key in crossover_fields}
                for item in module.existing_crossover_configs(doc)
            ],
        }

    def input_signature(
        self,
        doc,
        host_a,
        host_b,
        reference_chainage,
        arrangement,
        handing,
        track_gauge,
        flangeway,
        minimum_radius,
        ignored_crossover_id=None,
        ignored_turnout_id=None,
        _host_a_data=None,
        _host_b_data=None,
    ):
        """Hash all current inputs that can change a placement decision."""
        payload = {
            "version": 1,
            "document_name": str(getattr(doc, "Name", "")),
            "host_a": self._host_state(host_a, _host_a_data),
            "host_b": self._host_state(host_b, _host_b_data),
            "reference_chainage_mm": _number(reference_chainage),
            "arrangement": str(arrangement),
            "handing": str(handing),
            "track_gauge_mm": _number(track_gauge),
            "flangeway_mm": _number(flangeway),
            "minimum_radius_mm": _number(minimum_radius),
            "ignored_crossover_id": str(ignored_crossover_id or ""),
            "ignored_turnout_id": str(ignored_turnout_id or ""),
            "occupancy": self._occupancy(doc),
        }
        return _digest(payload)

    def _request_signature(self, request, solved=None):
        return self.input_signature(
            request["doc"], request["host_a"], request["host_b"],
            request["reference_chainage"], request["arrangement"],
            request["handing"], request["track_gauge"],
            request["flangeway"], request["minimum_radius"],
            request["ignored_crossover_id"],
            request["ignored_turnout_id"],
            _host_a_data=(solved or {}).get("host_a_data"),
            _host_b_data=(solved or {}).get("host_b_data"),
        )

    def solve(self, *args, **kwargs):
        """Return one signature-bound analytical result or reject before Part."""
        request = _bound_arguments(self.original_solver, args, kwargs)
        solved = self.original_solver(*args, **kwargs)
        module = self.module
        metrics_a = module.turnout_mapping_metrics(
            solved["host_a_data"], solved["toe_chainage_a"],
            solved["orientation_a"], solved["handing"],
            solved["dimensions"],
        )
        metrics_b = module.turnout_mapping_metrics(
            solved["host_b_data"], solved["toe_chainage_b"],
            solved["orientation_b"], solved["handing"],
            solved["dimensions"],
        )
        decision = complete_radius_decision(
            metrics_a["turnout_minimum_radius"],
            metrics_b["turnout_minimum_radius"],
            solved["connector"].get("minimum_radius"),
            request["minimum_radius"],
        )
        decision["host_a_identity"] = self._host_identity(request["host_a"])
        decision["host_b_identity"] = self._host_identity(request["host_b"])
        decision["host_a_geometry_signature"] = _digest(
            self._host_state(
                request["host_a"], solved["host_a_data"],
            )["geometry"]
        )
        decision["host_b_geometry_signature"] = _digest(
            self._host_state(
                request["host_b"], solved["host_b_data"],
            )["geometry"]
        )
        decision["request"] = {
            "reference_chainage_mm": float(request["reference_chainage"]),
            "arrangement": str(request["arrangement"]),
            "handing": str(request["handing"]),
            "track_gauge_mm": float(request["track_gauge"]),
            "flangeway_mm": float(request["flangeway"]),
            "minimum_radius_mm": float(request["minimum_radius"]),
            "ignored_crossover_id": str(
                request["ignored_crossover_id"] or ""
            ),
            "ignored_turnout_id": str(request["ignored_turnout_id"] or ""),
        }
        decision["input_signature"] = self._request_signature(
            request, solved,
        )
        if not decision["accepted"]:
            raise ValueError(decision["diagnostic"])
        solved[PREFLIGHT_KEY] = decision
        return solved

    def _checked_result(self, request, pre_solved):
        if pre_solved is None:
            return self.solve(**request)
        if not isinstance(pre_solved, dict):
            raise ValueError("The cached crossover preflight is invalid.")
        decision = pre_solved.get(PREFLIGHT_KEY)
        if not isinstance(decision, dict) or not decision.get("accepted"):
            raise ValueError("The cached crossover preflight is invalid.")
        expected = self._request_signature(request)
        if decision.get("input_signature") != expected:
            raise ValueError(
                "The cached crossover preflight is stale; preview again."
            )
        self.module._crossover_validate_pre_solved_result(
            pre_solved,
            request["host_a"], request["host_b"],
            request["reference_chainage"], request["arrangement"],
            request["handing"], request["track_gauge"],
            request["flangeway"], request["minimum_radius"],
        )
        return pre_solved

    def build(self, *args, **kwargs):
        """Check any cached result before frozen exact-shape construction."""
        arguments = _bound_arguments(self.original_builder, args, kwargs)
        request = {
            key: arguments[key]
            for key in inspect.signature(self.original_solver).parameters
        }
        checked = self._checked_result(
            request, arguments["pre_solved"],
        )
        arguments["pre_solved"] = checked
        return self.original_builder(**arguments)

    def edit(self, *args, **kwargs):
        """Reject before frozen edit clears chair-analysis display objects."""
        arguments = _bound_arguments(self.original_editor, args, kwargs)
        identifier = str(arguments["crossover_id"] or "").strip()
        if self.module.crossover_config_by_id(
            arguments["doc"], identifier,
        ) is None:
            raise ValueError(
                "Crossover {} was not found.".format(
                    identifier or "selection",
                )
            )
        request = {
            key: arguments[key]
            for key in inspect.signature(self.original_solver).parameters
            if key not in ("ignored_crossover_id", "ignored_turnout_id")
        }
        request["ignored_crossover_id"] = identifier
        request["ignored_turnout_id"] = None
        arguments["pre_solved"] = self._checked_result(
            request, arguments["pre_solved"],
        )
        return self.original_editor(**arguments)

    def preview_signature(self, panel, values):
        """Invalidate the panel's early return on every preflight input."""
        return self.input_signature(
            panel.doc, *values,
            ignored_crossover_id=getattr(
                panel, "editing_crossover_id", None,
            ),
            ignored_turnout_id=getattr(
                panel, "extending_turnout_id", None,
            ),
        )

    def diagnostics(self, result):
        """Show the complete decision beside inherited connector details."""
        inherited = self.original_diagnostics(result)
        decision = result.get(PREFLIGHT_KEY)
        if not isinstance(decision, dict):
            return inherited
        return "{}\n\n{}".format(decision["diagnostic"], inherited)

    def trace_text(self):
        """Label the inherited solver's status as connector-only."""
        return self.original_trace_text().replace(
            "\nStatus: ", "\nConnector solver status: ", 1,
        )
