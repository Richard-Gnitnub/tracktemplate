"""Modular-only composition for the inherited B15 GUI workflow host."""

from tracktemplate.compatibility.b15_workflow_host import (
    CALLER_ROUTES,
    EXPECTED_WORKFLOW_VERSION,
    FUNCTION_NAMES,
    B15WorkflowHostError,
    load_b15_workflow_host,
)


MODULAR_CALCULATION_ROUTE = "modular"
WORKFLOW_CONTRACT_ID = "tracktemplate:phase7:main-circle-centre:1"
PRODUCT_FUNCTION_NAMES = FUNCTION_NAMES + ("main_circle_centre",)
PRODUCT_CALLER_ROUTES = CALLER_ROUTES + (
    ("run_macro", ("main_circle_centre",)),
)

__all__ = (
    "MODULAR_CALCULATION_ROUTE",
    "ModularTransitionWorkflowSession",
    "TransitionWorkflowError",
    "load_modular_transition_workflow_session",
)


class TransitionWorkflowError(RuntimeError):
    """The modular-only inherited workflow could not be composed safely."""


class ModularTransitionWorkflowSession:
    """One inherited GUI host permanently bound to the modular calculation."""

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
                "The complete four-function modular workflow is unavailable."
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
            namespace["main_circle_centre"] = self._modular_functions[
                "main_circle_centre"
            ]
            self._host.bind_transition_functions(
                MODULAR_CALCULATION_ROUTE,
                {
                    name: self._modular_functions[name]
                    for name in FUNCTION_NAMES
                },
            )
            self._validate_binding()
        except Exception as error:
            for name, value in previous.items():
                if value is missing:
                    namespace.pop(name, None)
                else:
                    namespace[name] = value
            if isinstance(error, B15WorkflowHostError):
                raise TransitionWorkflowError(str(error)) from error
            raise

    def _validate_binding(self):
        """Verify every live edge without repairing a changed binding."""
        namespace = self.module.__dict__
        for name in PRODUCT_FUNCTION_NAMES:
            if namespace.get(name) is not self._modular_functions[name]:
                raise TransitionWorkflowError(
                    "The modular workflow has a mixed {!r} binding.".format(
                        name,
                    )
                )

        # The frozen host binder still owns its original three-function
        # mutation. Product reports additionally verify the complete live
        # closure, including the new centre and the inherited entry point.
        routes = (
            (
                "transition_start_signed_offset",
                ("clothoid_entry_displacement",),
            ),
            ("solve_transition_length", ("transition_start_signed_offset",)),
        ) + PRODUCT_CALLER_ROUTES
        for caller_name, targets in routes:
            caller = namespace.get(caller_name)
            caller_globals = getattr(caller, "__globals__", None)
            code = getattr(caller, "__code__", None)
            if (
                not callable(caller)
                or not isinstance(caller_globals, dict)
                or code is None
                or not set(targets) <= set(code.co_names)
                or (
                    caller_name == "run_macro"
                    and caller_globals is not namespace
                )
            ):
                raise TransitionWorkflowError(
                    "The modular workflow caller {!r} is unavailable.".format(
                        caller_name,
                    )
                )
            for target in targets:
                if caller_globals.get(target) is not self._modular_functions[
                    target
                ]:
                    raise TransitionWorkflowError(
                        "The modular workflow caller {!r} does not use its "
                        "selected {!r}.".format(caller_name, target)
                    )

    @property
    def module(self):
        return self._host.module

    def routing_record(self):
        """Return the non-switchable composition record."""
        self._validate_binding()
        return {
            "schema_version": 2,
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
