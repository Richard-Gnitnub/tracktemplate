"""Development-only dual-route oracle retained for Phase 3 reproduction.

Product composition no longer imports or exposes this switch.  It remains
under ``tools`` solely so the accepted legacy/modular parity evidence can be
rerun against the shared, fingerprinted B15 workflow-host loader.
"""

from tracktemplate.compatibility.b15_workflow_host import (
    CALLER_ROUTES,
    EXPECTED_CHECKPOINT,
    EXPECTED_CONTRACT_ID,
    EXPECTED_WORKFLOW_VERSION,
    FUNCTION_NAMES,
    B15WorkflowHostError,
    load_b15_workflow_host,
)


LEGACY_ROUTE = "legacy"
MODULAR_ROUTE = "modular"
CALCULATION_ROUTES = (LEGACY_ROUTE, MODULAR_ROUTE)
EXPECTED_LEGACY_VERSION = EXPECTED_WORKFLOW_VERSION

__all__ = (
    "CALCULATION_ROUTES",
    "CALLER_ROUTES",
    "EXPECTED_CHECKPOINT",
    "EXPECTED_CONTRACT_ID",
    "EXPECTED_LEGACY_VERSION",
    "FUNCTION_NAMES",
    "LEGACY_ROUTE",
    "MODULAR_ROUTE",
    "TransitionPilotError",
    "TransitionPilotSession",
    "load_transition_pilot_session",
)


class TransitionPilotError(RuntimeError):
    """The development-only comparison oracle could not be composed safely."""


class TransitionPilotSession:
    """One explicit development oracle with a guarded three-name route."""

    def __init__(self, host, legacy_functions, modular_functions):
        self._host = host
        self.module = host.module
        self.source_path = host.source_path
        self.source_sha256 = str(host.source_sha256)
        self._legacy_functions = dict(legacy_functions)
        self._modular_functions = dict(modular_functions)
        self._active_route = None
        self._validate_function_sets()

    @property
    def active_route(self):
        return self._active_route

    def _validate_function_sets(self):
        expected_names = set(FUNCTION_NAMES)
        for label, functions in (
            (LEGACY_ROUTE, self._legacy_functions),
            (MODULAR_ROUTE, self._modular_functions),
        ):
            if set(functions) != expected_names or not all(
                callable(functions[name]) for name in FUNCTION_NAMES
            ):
                raise TransitionPilotError(
                    "The {} transition route is incomplete.".format(label)
                )

        namespace = self.module.__dict__
        for name in FUNCTION_NAMES:
            if self._legacy_functions[name].__globals__ is not namespace:
                raise TransitionPilotError(
                    "The captured B15 function {!r} has an unexpected "
                    "namespace.".format(name)
                )

    def _route_functions(self, route):
        if route == LEGACY_ROUTE:
            return self._legacy_functions
        if route == MODULAR_ROUTE:
            return self._modular_functions
        raise TransitionPilotError(
            "Unknown transition calculation route {!r}; expected one of {}."
            .format(route, ", ".join(CALCULATION_ROUTES))
        )

    def apply_route(self, route):
        """Bind one complete comparison route and return its oracle record."""
        functions = self._route_functions(route)
        try:
            self._host.bind_transition_functions(route, functions)
        except B15WorkflowHostError as error:
            raise TransitionPilotError(str(error)) from error
        self._active_route = route
        return {
            "schema_version": 1,
            "route": route,
            "rollback_route": LEGACY_ROUTE,
            "function_names": list(FUNCTION_NAMES),
            "caller_names": [item[0] for item in CALLER_ROUTES],
            "legacy_version": EXPECTED_LEGACY_VERSION,
            "legacy_source_sha256": self.source_sha256,
            "mixed_route": False,
        }

    def launch_workflow(self):
        """Launch the host only after the development route is explicit."""
        if self._active_route not in CALCULATION_ROUTES:
            raise TransitionPilotError(
                "Select a complete transition calculation route before launch."
            )
        return self._host.launch_workflow()


def load_transition_pilot_session(repository_root, modular_api, contract):
    """Load one dual-route session for historical comparison tooling only."""
    try:
        modular_functions = {
            name: getattr(modular_api, name)
            for name in FUNCTION_NAMES
        }
    except AttributeError as error:
        raise TransitionPilotError(
            "The complete modular transition calculation route is unavailable."
        ) from error

    try:
        host = load_b15_workflow_host(repository_root, contract)
        legacy_functions = {
            name: host.module.__dict__[name]
            for name in FUNCTION_NAMES
        }
        return TransitionPilotSession(
            host,
            legacy_functions,
            modular_functions,
        )
    except (B15WorkflowHostError, KeyError) as error:
        if isinstance(error, B15WorkflowHostError):
            raise TransitionPilotError(str(error)) from error
        raise TransitionPilotError(
            "The complete legacy transition calculation route is unavailable."
        ) from error
