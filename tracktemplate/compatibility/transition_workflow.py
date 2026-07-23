"""Modular-only composition for the inherited B15 GUI workflow host."""

from tracktemplate.compatibility.b15_workflow_host import (
    CALLER_ROUTES,
    EXPECTED_WORKFLOW_VERSION,
    FUNCTION_NAMES,
    B15WorkflowHostError,
    load_b15_workflow_host,
)


MODULAR_CALCULATION_ROUTE = "modular"

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
        self._bind_modular()

    def _bind_modular(self):
        try:
            self._host.bind_transition_functions(
                MODULAR_CALCULATION_ROUTE,
                self._modular_functions,
            )
        except B15WorkflowHostError as error:
            raise TransitionWorkflowError(str(error)) from error

    @property
    def module(self):
        return self._host.module

    def routing_record(self):
        """Return the non-switchable composition record."""
        return {
            "schema_version": 1,
            "route": MODULAR_CALCULATION_ROUTE,
            "comparison_route_available": False,
            "function_names": list(FUNCTION_NAMES),
            "caller_names": [item[0] for item in CALLER_ROUTES],
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
            for name in FUNCTION_NAMES
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
