"""Internal loader for the frozen B15 workflow host.

The host is still needed temporarily to exercise the inherited GUI workflow,
but it does not choose a calculation implementation.  Product composition and
development-only comparison tooling inject complete function sets explicitly.
"""

from dataclasses import dataclass
import ast
import hashlib
import pathlib
import sys
import types


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
EXPECTED_WORKFLOW_VERSION = "10.2A8A7B15"

__all__ = (
    "CALLER_ROUTES",
    "EXPECTED_CHECKPOINT",
    "EXPECTED_CONTRACT_ID",
    "EXPECTED_WORKFLOW_VERSION",
    "FUNCTION_NAMES",
    "B15WorkflowHost",
    "B15WorkflowHostError",
    "load_b15_workflow_host",
)


class B15WorkflowHostError(RuntimeError):
    """The frozen B15 workflow host could not be loaded or bound safely."""


@dataclass(frozen=True)
class B15WorkflowHost:
    """One validated B15 module with atomic transition-function binding."""

    module: object
    source_path: pathlib.Path
    source_sha256: str

    def bind_transition_functions(self, route_label, functions):
        """Atomically bind and verify one complete three-function closure."""
        route_label = str(route_label)
        functions = dict(functions)
        expected_names = set(FUNCTION_NAMES)
        if set(functions) != expected_names or not all(
            callable(functions[name]) for name in FUNCTION_NAMES
        ):
            raise B15WorkflowHostError(
                "The {} transition route is incomplete.".format(route_label)
            )

        namespace = self.module.__dict__
        missing = object()
        previous = {name: namespace.get(name, missing) for name in FUNCTION_NAMES}
        try:
            namespace.update(functions)
            _validate_active_closure(self.module, route_label, functions)
        except Exception:
            for name, value in previous.items():
                if value is missing:
                    namespace.pop(name, None)
                else:
                    namespace[name] = value
            raise

    def launch_workflow(self):
        """Launch the inherited GUI workflow after a verified binding."""
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
        raise B15WorkflowHostError(
            "The transition-pilot contract identity is invalid."
        )

    successor = contract.get("successor") or {}
    if successor.get("development_checkpoint_id") != EXPECTED_CHECKPOINT:
        raise B15WorkflowHostError(
            "The transition-pilot checkpoint is invalid."
        )

    boundary = contract.get("module_boundary") or {}
    function_names = tuple(
        item.get("name")
        for item in boundary.get("functions") or []
        if isinstance(item, dict)
    )
    caller_routes = tuple(
        (item.get("caller"), tuple(item.get("targets") or ()))
        for item in boundary.get("external_caller_routes") or []
        if isinstance(item, dict)
    )
    if function_names != FUNCTION_NAMES or caller_routes != CALLER_ROUTES:
        raise B15WorkflowHostError(
            "The frozen transition routing boundary drifted."
        )

    source = (contract.get("source_state") or {}).get("b15") or {}
    relative_path = source.get("path")
    expected_sha256 = source.get("sha256")
    if not isinstance(relative_path, str) or not isinstance(
        expected_sha256,
        str,
    ):
        raise B15WorkflowHostError(
            "The frozen B15 source record is incomplete."
        )

    root = pathlib.Path(repository_root).resolve()
    source_path = (root / relative_path).resolve()
    try:
        source_path.relative_to(root)
    except ValueError as error:
        raise B15WorkflowHostError(
            "The B15 source path escapes the repository."
        ) from error
    if not source_path.is_file():
        raise B15WorkflowHostError("The frozen B15 source file is missing.")

    observed_sha256 = _sha256(source_path)
    if observed_sha256 != expected_sha256:
        raise B15WorkflowHostError(
            "The frozen B15 source fingerprint drifted."
        )
    return source_path, observed_sha256


def _load_b15_module(source_path, source_sha256):
    source = pathlib.Path(source_path).read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError as error:
        raise B15WorkflowHostError(
            "The frozen B15 source no longer parses."
        ) from error

    launch = tree.body[-1] if tree.body else None
    if not (
        isinstance(launch, ast.Expr)
        and isinstance(launch.value, ast.Call)
        and isinstance(launch.value.func, ast.Name)
        and launch.value.func.id == "run_macro"
        and not launch.value.args
        and not launch.value.keywords
    ):
        raise B15WorkflowHostError(
            "The frozen B15 launch boundary is not the expected final "
            "run_macro() call."
        )
    tree.body.pop()
    ast.fix_missing_locations(tree)

    module_name = "_tracktemplate_b15_workflow_{}".format(
        source_sha256[:12]
    )
    previous_module = sys.modules.get(module_name)
    module = types.ModuleType(module_name)
    module.__file__ = str(source_path)
    module.__package__ = ""
    sys.modules[module_name] = module
    try:
        exec(compile(tree, str(source_path), "exec"), module.__dict__)
        if (
            str(module.__dict__.get("MACRO_VERSION_NUMBER"))
            != EXPECTED_WORKFLOW_VERSION
        ):
            raise B15WorkflowHostError(
                "The loaded B15 version identity drifted."
            )
    except Exception as error:
        _restore_module(module_name, previous_module)
        if isinstance(error, B15WorkflowHostError):
            raise
        raise B15WorkflowHostError(
            "The frozen B15 definitions could not load."
        ) from error
    return module, previous_module


def _restore_module(module_name, previous_module):
    if previous_module is None:
        sys.modules.pop(module_name, None)
    else:
        sys.modules[module_name] = previous_module


def _validate_host_boundary(module):
    namespace = module.__dict__
    for name in FUNCTION_NAMES:
        function = namespace.get(name)
        if (
            not callable(function)
            or getattr(function, "__globals__", None) is not namespace
        ):
            raise B15WorkflowHostError(
                "The frozen B15 function {!r} is unavailable.".format(name)
            )

    for caller_name, target_names in CALLER_ROUTES:
        caller = namespace.get(caller_name)
        if (
            not callable(caller)
            or getattr(caller, "__globals__", None) is not namespace
        ):
            raise B15WorkflowHostError(
                "The frozen B15 caller {!r} is unavailable.".format(
                    caller_name
                )
            )
        referenced_names = set(caller.__code__.co_names)
        if not set(target_names) <= referenced_names:
            raise B15WorkflowHostError(
                "The frozen B15 caller {!r} no longer references {}.".format(
                    caller_name,
                    ", ".join(target_names),
                )
            )

    runner = namespace.get("run_macro")
    if (
        not callable(runner)
        or getattr(runner, "__globals__", None) is not namespace
    ):
        raise B15WorkflowHostError(
            "The frozen B15 workflow entry point is unavailable."
        )


def _validate_active_closure(module, route_label, functions):
    namespace = module.__dict__
    for name in FUNCTION_NAMES:
        if namespace.get(name) is not functions[name]:
            raise B15WorkflowHostError(
                "The {} transition route left {!r} on a mixed path.".format(
                    route_label,
                    name,
                )
            )

    displacement = functions["clothoid_entry_displacement"]
    signed_offset = functions["transition_start_signed_offset"]
    solver = functions["solve_transition_length"]
    if (
        signed_offset.__globals__.get("clothoid_entry_displacement")
        is not displacement
    ):
        raise B15WorkflowHostError(
            "The {} signed-offset route does not use its selected "
            "displacement.".format(route_label)
        )
    if (
        solver.__globals__.get("transition_start_signed_offset")
        is not signed_offset
    ):
        raise B15WorkflowHostError(
            "The {} solver route does not use its selected signed offset."
            .format(route_label)
        )

    for caller_name, target_names in CALLER_ROUTES:
        caller_namespace = namespace[caller_name].__globals__
        for target_name in target_names:
            if caller_namespace.get(target_name) is not functions[target_name]:
                raise B15WorkflowHostError(
                    "The {} caller {!r} is not wholly routed through "
                    "{!r}.".format(route_label, caller_name, target_name)
                )


def load_b15_workflow_host(repository_root, contract):
    """Load and validate the frozen host without selecting a route."""
    source_path, source_sha256 = _contract_boundary(
        repository_root,
        contract,
    )
    module, previous_module = _load_b15_module(
        source_path,
        source_sha256,
    )
    try:
        _validate_host_boundary(module)
    except Exception:
        _restore_module(module.__name__, previous_module)
        raise
    return B15WorkflowHost(module, source_path, source_sha256)
