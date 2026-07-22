"""Fail-closed B15/modular routing for the bounded transition pilot.

This adapter exists only while Phase 3 compares the successor calculation
with the accepted B15 workflow. It loads the exact frozen B15 source without
launching its dialog, captures the three legacy calculations, and binds the
complete legacy or modular closure before an existing caller can run.
"""

import ast
import hashlib
import pathlib
import sys
import types


LEGACY_ROUTE = "legacy"
MODULAR_ROUTE = "modular"
CALCULATION_ROUTES = (LEGACY_ROUTE, MODULAR_ROUTE)

FUNCTION_NAMES = (
    "clothoid_entry_displacement",
    "transition_start_signed_offset",
    "solve_transition_length",
)

CALLER_ROUTES = (
    ("main_circle_centre", ("clothoid_entry_displacement",)),
    ("build_concentric_core", ("clothoid_entry_displacement",)),
    (
        "prepare_track_alignment",
        ("transition_start_signed_offset", "solve_transition_length"),
    ),
)

EXPECTED_CONTRACT_ID = "tracktemplate:phase1:transition-pilot:1"
EXPECTED_CHECKPOINT = "10.2A8A7B16"
EXPECTED_LEGACY_VERSION = "10.2A8A7B15"

__all__ = (
    "CALCULATION_ROUTES",
    "LEGACY_ROUTE",
    "MODULAR_ROUTE",
    "TransitionPilotError",
    "load_transition_pilot_session",
)


class TransitionPilotError(RuntimeError):
    """The temporary transition route could not be composed safely."""


class TransitionPilotSession:
    """One explicit B15 comparison session with a guarded three-name route."""

    def __init__(
        self,
        module,
        source_path,
        source_sha256,
        legacy_functions,
        modular_functions,
    ):
        self.module = module
        self.source_path = pathlib.Path(source_path)
        self.source_sha256 = str(source_sha256)
        self._legacy_functions = dict(legacy_functions)
        self._modular_functions = dict(modular_functions)
        self._active_route = None
        self._validate_static_boundary()

    @property
    def active_route(self):
        return self._active_route

    def _validate_static_boundary(self):
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
                    "The captured B15 function {!r} has an unexpected namespace."
                    .format(name)
                )

        for caller_name, target_names in CALLER_ROUTES:
            caller = namespace.get(caller_name)
            if (
                not callable(caller)
                or getattr(caller, "__globals__", None) is not namespace
            ):
                raise TransitionPilotError(
                    "The frozen B15 caller {!r} is unavailable.".format(caller_name)
                )
            referenced_names = set(caller.__code__.co_names)
            if not set(target_names) <= referenced_names:
                raise TransitionPilotError(
                    "The frozen B15 caller {!r} no longer references {}."
                    .format(caller_name, ", ".join(target_names))
                )

        runner = namespace.get("run_macro")
        if (
            not callable(runner)
            or getattr(runner, "__globals__", None) is not namespace
        ):
            raise TransitionPilotError(
                "The frozen B15 workflow entry point is unavailable."
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

    def _validate_active_closure(self, route, functions):
        namespace = self.module.__dict__
        for name in FUNCTION_NAMES:
            if namespace.get(name) is not functions[name]:
                raise TransitionPilotError(
                    "The {} transition route left {!r} on a mixed path."
                    .format(route, name)
                )

        displacement = functions["clothoid_entry_displacement"]
        signed_offset = functions["transition_start_signed_offset"]
        solver = functions["solve_transition_length"]
        if (
            signed_offset.__globals__.get("clothoid_entry_displacement")
            is not displacement
        ):
            raise TransitionPilotError(
                "The {} signed-offset route does not use its selected displacement."
                .format(route)
            )
        if solver.__globals__.get("transition_start_signed_offset") is not signed_offset:
            raise TransitionPilotError(
                "The {} solver route does not use its selected signed offset."
                .format(route)
            )

        for caller_name, target_names in CALLER_ROUTES:
            caller_namespace = namespace[caller_name].__globals__
            for target_name in target_names:
                if caller_namespace.get(target_name) is not functions[target_name]:
                    raise TransitionPilotError(
                        "The {} caller {!r} is not wholly routed through {!r}."
                        .format(route, caller_name, target_name)
                    )

    def apply_route(self, route):
        """Bind all three names together and return a serialisable route record."""
        functions = self._route_functions(route)
        namespace = self.module.__dict__
        missing = object()
        previous = {name: namespace.get(name, missing) for name in FUNCTION_NAMES}
        try:
            namespace.update(functions)
            self._validate_active_closure(route, functions)
        except Exception:
            for name, value in previous.items():
                if value is missing:
                    namespace.pop(name, None)
                else:
                    namespace[name] = value
            raise

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
        """Launch the captured B15 workflow only after an explicit route exists."""
        if self._active_route not in CALCULATION_ROUTES:
            raise TransitionPilotError(
                "Select a complete transition calculation route before launch."
            )
        return self.module.run_macro()


def _sha256(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _contract_boundary(repository_root, contract):
    if (
        not isinstance(contract, dict)
        or contract.get("contract_id") != EXPECTED_CONTRACT_ID
    ):
        raise TransitionPilotError("The transition-pilot contract identity is invalid.")

    successor = contract.get("successor") or {}
    if successor.get("development_checkpoint_id") != EXPECTED_CHECKPOINT:
        raise TransitionPilotError("The transition-pilot checkpoint is invalid.")

    boundary = contract.get("module_boundary") or {}
    function_names = tuple(
        item.get("name") for item in boundary.get("functions") or []
        if isinstance(item, dict)
    )
    caller_routes = tuple(
        (item.get("caller"), tuple(item.get("targets") or ()))
        for item in boundary.get("external_caller_routes") or []
        if isinstance(item, dict)
    )
    if function_names != FUNCTION_NAMES or caller_routes != CALLER_ROUTES:
        raise TransitionPilotError("The frozen transition routing boundary drifted.")

    source = (contract.get("source_state") or {}).get("b15") or {}
    relative_path = source.get("path")
    expected_sha256 = source.get("sha256")
    if not isinstance(relative_path, str) or not isinstance(expected_sha256, str):
        raise TransitionPilotError("The frozen B15 source record is incomplete.")

    root = pathlib.Path(repository_root).resolve()
    source_path = (root / relative_path).resolve()
    try:
        source_path.relative_to(root)
    except ValueError as error:
        raise TransitionPilotError(
            "The B15 source path escapes the repository."
        ) from error
    if not source_path.is_file():
        raise TransitionPilotError("The frozen B15 source file is missing.")

    observed_sha256 = _sha256(source_path)
    if observed_sha256 != expected_sha256:
        raise TransitionPilotError("The frozen B15 source fingerprint drifted.")
    return source_path, observed_sha256


def _load_legacy_module(source_path, source_sha256):
    source = pathlib.Path(source_path).read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError as error:
        raise TransitionPilotError("The frozen B15 source no longer parses.") from error

    launch = tree.body[-1] if tree.body else None
    if not (
        isinstance(launch, ast.Expr)
        and isinstance(launch.value, ast.Call)
        and isinstance(launch.value.func, ast.Name)
        and launch.value.func.id == "run_macro"
        and not launch.value.args
        and not launch.value.keywords
    ):
        raise TransitionPilotError(
            "The frozen B15 launch boundary is not the expected final "
            "run_macro() call."
        )
    tree.body.pop()
    ast.fix_missing_locations(tree)

    module_name = "_tracktemplate_b15_transition_{}".format(source_sha256[:12])
    previous_module = sys.modules.get(module_name)
    module = types.ModuleType(module_name)
    module.__file__ = str(source_path)
    module.__package__ = ""
    sys.modules[module_name] = module
    try:
        exec(compile(tree, str(source_path), "exec"), module.__dict__)
        if (
            str(module.__dict__.get("MACRO_VERSION_NUMBER"))
            != EXPECTED_LEGACY_VERSION
        ):
            raise TransitionPilotError("The loaded B15 version identity drifted.")
    except Exception as error:
        if previous_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous_module
        if isinstance(error, TransitionPilotError):
            raise
        raise TransitionPilotError("The frozen B15 definitions could not load.") from error
    return module, previous_module


def load_transition_pilot_session(repository_root, modular_api, contract):
    """Load exact B15 definitions and capture both complete calculation routes."""
    source_path, source_sha256 = _contract_boundary(repository_root, contract)
    try:
        modular_functions = {
            name: getattr(modular_api, name)
            for name in FUNCTION_NAMES
        }
    except AttributeError as error:
        raise TransitionPilotError(
            "The complete modular transition calculation route is unavailable."
        ) from error

    module, previous_module = _load_legacy_module(source_path, source_sha256)
    try:
        legacy_functions = {name: module.__dict__[name] for name in FUNCTION_NAMES}
        session = TransitionPilotSession(
            module,
            source_path,
            source_sha256,
            legacy_functions,
            modular_functions,
        )
    except (KeyError, TransitionPilotError) as error:
        if previous_module is None:
            sys.modules.pop(module.__name__, None)
        else:
            sys.modules[module.__name__] = previous_module
        if isinstance(error, TransitionPilotError):
            raise
        raise TransitionPilotError(
            "The complete legacy transition calculation route is unavailable."
        ) from error
    return session
