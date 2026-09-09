"""Modular-only composition for the inherited B15 GUI workflow host."""

from dataclasses import dataclass

from tracktemplate.compatibility.b15_workflow_host import (
    EXPECTED_WORKFLOW_VERSION,
    FUNCTION_NAMES,
    B15WorkflowHostError,
    load_b15_workflow_host,
)


MODULAR_CALCULATION_ROUTE = "modular"
WORKFLOW_CONTRACT_ID = "tracktemplate:phase7:common-straight-extensions:1"
PRODUCT_FUNCTION_NAMES = FUNCTION_NAMES + (
    "main_circle_centre", "clothoid_exit_displacement",
    "build_concentric_core", "add_common_straight_extensions",
)
PRODUCT_CALLER_ROUTES = (
    ("main_circle_centre", ("clothoid_entry_displacement",)),
    (
        "build_concentric_core",
        ("clothoid_entry_displacement", "clothoid_exit_displacement"),
    ),
    (
        "prepare_track_alignment",
        ("transition_start_signed_offset", "solve_transition_length",
         "build_concentric_core"),
    ),
    (
        "run_macro",
        ("main_circle_centre", "build_concentric_core",
         "add_common_straight_extensions"),
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
                "The complete seven-function modular workflow is unavailable."
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
        self._host_functions["add_common_straight_extensions"] = (
            _CommonStraightExtensionsAdapter(
                self._modular_functions["add_common_straight_extensions"],
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

        # Product composition owns all seven current bindings. The frozen
        # three-function binder remains solely on the comparison route.
        domain_routes = (
            (
                "transition_start_signed_offset",
                ("clothoid_entry_displacement",),
            ),
            ("solve_transition_length", ("transition_start_signed_offset",)),
        ) + PRODUCT_CALLER_ROUTES[:2]
        routes = [
            (
                name, self._modular_functions[name], targets,
                self._modular_functions, False,
            )
            for name, targets in domain_routes
        ] + [
            (name, namespace.get(name), targets, self._host_functions, True)
            for name, targets in PRODUCT_CALLER_ROUTES[2:]
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
            "schema_version": 5,
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
    return ModularTransitionWorkflowSession(host, modular_functions)
