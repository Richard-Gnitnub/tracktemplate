#!/usr/bin/env python3
"""Verify declared development tools before a dependent workflow stage."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
import pathlib
import platform
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from urllib.parse import urlparse


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "reference" / "contracts" / "development-toolchain-v1.json"
)
SENTINEL = "TRACKTEMPLATE_TOOLCHAIN_PREFLIGHT="
RUFF_SENTINEL = "TRACKTEMPLATE_RUFF="
STAGES = (
    "development",
    "validation",
    "documentation",
    "freecad",
    "freecad-gui",
    "publication",
)
CHECK_IDS = {
    "flatpak",
    "freecad_cli_checkout",
    "gh",
    "git",
    "github_access",
    "gui_bridge_python",
    "gui_shell_tools",
    "pdftotext",
    "project_python",
    "qualified_freecad",
    "repository",
    "requirements_file",
    "ruff",
    "ste_source",
}
FALLBACK_CHECK_IDS = {"ruff_trusted_user_path"}
GUI_SHELL_COMPONENTS = (
    "bash",
    "chmod",
    "dirname",
    "env",
    "grep",
    "kill",
    "mkdir",
    "mktemp",
    "openssl",
    "rm",
    "seq",
    "sleep",
    "tr",
)
MAX_CONTRACT_BYTES = 256 * 1024
MAX_COMMAND_OUTPUT = 1024 * 1024


class PreflightError(RuntimeError):
    """Describe one non-sensitive, fail-closed preflight result."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


@dataclass
class Context:
    """Hold the fixed checkout and injectable read-only system operations."""

    root: pathlib.Path = ROOT
    python_executable: pathlib.Path = pathlib.Path(sys.executable)
    requested_profile: str | None = None
    environ: dict[str, str] = field(default_factory=lambda: os.environ.copy())
    resolved: dict[str, str] = field(default_factory=dict)
    run: object = subprocess.run
    which: object = shutil.which


def _read_json(path):
    try:
        status = path.stat()
        if not stat.S_ISREG(status.st_mode):
            raise PreflightError("contract-invalid", "Contract is not a file.")
        if status.st_size > MAX_CONTRACT_BYTES:
            raise PreflightError("contract-invalid", "Contract is too large.")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PreflightError(
            "contract-invalid",
            "Contract is not valid bounded UTF-8 JSON.",
        ) from error
    if not isinstance(value, dict):
        raise PreflightError("contract-invalid", "Contract root is invalid.")
    return value


def _exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise PreflightError(
            "contract-invalid",
            "{} fields do not match the schema.".format(label),
        )


def _safe_relative_path(value, label):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PreflightError(
            "contract-invalid",
            "{} is invalid.".format(label),
        )
    path = pathlib.PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise PreflightError(
            "contract-invalid",
            "{} is not relative.".format(label),
        )
    return value


def _reject_sensitive_material(value, key=""):
    sensitive_key = re.compile(
        r"(?:credential|password|private[_-]?key|secret|token)",
        re.IGNORECASE,
    )
    sensitive_value = re.compile(
        r"(?:github_pat_|gh[opsu]_[A-Za-z0-9]|-----BEGIN .*PRIVATE KEY-----)",
        re.IGNORECASE,
    )
    if sensitive_key.search(key):
        raise PreflightError(
            "contract-sensitive-material",
            "Contract contains a prohibited sensitive field.",
        )
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            if not isinstance(child_key, str):
                raise PreflightError(
                    "contract-invalid",
                    "Contract keys must be text.",
                )
            _reject_sensitive_material(child_value, child_key)
    elif isinstance(value, list):
        for child_value in value:
            _reject_sensitive_material(child_value, key)
    elif isinstance(value, str):
        if (
            sensitive_value.search(value)
            or value.startswith(("/home/", "~/", ".ssh/"))
            or "\n" in value
            or "\r" in value
        ):
            raise PreflightError(
                "contract-sensitive-material",
                "Contract contains prohibited private or command material.",
            )


def validate_contract(contract):
    """Validate the closed toolchain schema and all cross-references."""
    _reject_sensitive_material(contract)
    _exact_keys(
        contract,
        {
            "authority",
            "compatibility_contract",
            "consumers",
            "contract_id",
            "fallbacks",
            "python_dependencies",
            "repository",
            "requirements_file",
            "ruff_config",
            "schema_version",
            "stages",
            "tools",
        },
        "Top-level contract",
    )
    if (
        contract["schema_version"] != 1
        or contract["contract_id"]
        != "tracktemplate-development-toolchain-v1"
        or contract["authority"]
        != "reference/VALIDATION.md#developer-tool-boundary"
    ):
        raise PreflightError(
            "contract-invalid",
            "Contract identity or authority is invalid.",
        )
    for name in (
        "compatibility_contract",
        "requirements_file",
        "ruff_config",
    ):
        _safe_relative_path(contract[name], name)

    _exact_keys(
        contract["repository"],
        {"default_branch", "github", "remote"},
        "Repository",
    )
    repository = contract["repository"]
    if (
        re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository["github"])
        is None
        or repository["default_branch"] != "main"
        or repository["remote"] != "origin"
    ):
        raise PreflightError(
            "contract-invalid",
            "Repository identity is invalid.",
        )

    stages = contract["stages"]
    if not isinstance(stages, dict) or tuple(stages) != tuple(sorted(STAGES)):
        raise PreflightError(
            "contract-invalid",
            "Stage declarations are missing or out of order.",
        )
    tools = contract["tools"]
    if not isinstance(tools, dict) or not tools:
        raise PreflightError(
            "contract-invalid",
            "Tool declarations are invalid.",
        )
    referenced_tools = set()
    for stage, tool_ids in stages.items():
        if (
            not isinstance(tool_ids, list)
            or not tool_ids
            or len(tool_ids) != len(set(tool_ids))
            or any(tool_id not in tools for tool_id in tool_ids)
        ):
            raise PreflightError(
                "contract-invalid",
                "The {} stage has an invalid tool list.".format(stage),
            )
        referenced_tools.update(tool_ids)
    if referenced_tools != set(tools):
        raise PreflightError(
            "contract-invalid",
            "Each declared tool must have one consuming stage.",
        )

    fallbacks = contract["fallbacks"]
    if not isinstance(fallbacks, dict):
        raise PreflightError(
            "contract-invalid",
            "Fallback declarations are invalid.",
        )
    referenced_fallbacks = set()
    for tool_id, specification in tools.items():
        expected = {"authority", "check", "classification", "fallbacks"}
        if tool_id == "gui_shell_tools":
            expected.add("components")
        _exact_keys(specification, expected, "Tool {}".format(tool_id))
        if (
            specification["check"] not in CHECK_IDS
            or specification["check"] != tool_id
            or not isinstance(specification["classification"], str)
            or not specification["classification"]
            or not isinstance(specification["fallbacks"], list)
            or len(specification["fallbacks"])
            != len(set(specification["fallbacks"]))
        ):
            raise PreflightError(
                "contract-invalid",
                (
                    "Tool {} has an invalid check or classification."
                ).format(tool_id),
            )
        _safe_relative_path(
            specification["authority"].split("#", 1)[0],
            "tool authority",
        )
        for fallback_id in specification["fallbacks"]:
            if fallback_id not in fallbacks:
                raise PreflightError(
                    "contract-invalid",
                    "Tool {} names an undeclared fallback.".format(tool_id),
                )
            referenced_fallbacks.add(fallback_id)
        if tool_id == "gui_shell_tools" and tuple(
            specification["components"]
        ) != GUI_SHELL_COMPONENTS:
            raise PreflightError(
                "contract-invalid",
                "GUI shell components do not match the supported workflow.",
            )
    if referenced_fallbacks != set(fallbacks):
        raise PreflightError(
            "contract-invalid",
            "Each fallback must have one declared consumer.",
        )
    for fallback_id, specification in fallbacks.items():
        _exact_keys(
            specification,
            {"authority", "check", "tool"},
            "Fallback {}".format(fallback_id),
        )
        if (
            specification["check"] not in FALLBACK_CHECK_IDS
            or specification["tool"] not in tools
            or fallback_id not in tools[specification["tool"]]["fallbacks"]
        ):
            raise PreflightError(
                "contract-invalid",
                "Fallback {} is not bound to its tool.".format(fallback_id),
            )
        _safe_relative_path(
            specification["authority"].split("#", 1)[0],
            "fallback authority",
        )

    dependencies = contract["python_dependencies"]
    if not isinstance(dependencies, list) or not dependencies:
        raise PreflightError(
            "contract-invalid",
            "Python dependency declarations are invalid.",
        )
    dependency_names = []
    for dependency in dependencies:
        _exact_keys(
            dependency,
            {"name", "pin", "stages", "tool"},
            "Python dependency",
        )
        name = dependency["name"]
        pin = dependency["pin"]
        dependency_stages = dependency["stages"]
        if (
            re.fullmatch(r"[a-z][a-z0-9_.-]*", name) is None
            or re.fullmatch(r"[0-9]+(?:\.[0-9]+)+(?:[a-z0-9.+-]*)?", pin)
            is None
            or not isinstance(dependency_stages, list)
            or not dependency_stages
            or dependency_stages != sorted(set(dependency_stages))
            or any(stage not in stages for stage in dependency_stages)
            or dependency["tool"] not in tools
            or any(
                dependency["tool"] not in stages[stage]
                for stage in dependency_stages
            )
        ):
            raise PreflightError(
                "contract-invalid",
                "Python dependency {} is invalid.".format(name),
            )
        dependency_names.append(name)
    if dependency_names != sorted(set(dependency_names)):
        raise PreflightError(
            "contract-invalid",
            "Python dependencies must be unique and ordered.",
        )

    consumers = contract["consumers"]
    if not isinstance(consumers, dict) or not consumers:
        raise PreflightError(
            "contract-invalid",
            "Consumer declarations are invalid.",
        )
    if list(consumers) != sorted(consumers):
        raise PreflightError(
            "contract-invalid",
            "Consumer declarations must be ordered.",
        )
    for path, consumer_stages in consumers.items():
        _safe_relative_path(path, "consumer path")
        if (
            not isinstance(consumer_stages, list)
            or not consumer_stages
            or consumer_stages != sorted(set(consumer_stages))
            or any(stage not in stages for stage in consumer_stages)
        ):
            raise PreflightError(
                "contract-invalid",
                "Consumer stages are invalid.",
            )
    return contract


def load_contract(path=CONTRACT_PATH):
    """Load and validate the fixed repository toolchain contract."""
    return validate_contract(_read_json(path))


def _run(
    context,
    arguments,
    *,
    cwd=None,
    env=None,
    input_text=None,
    timeout=20,
):
    try:
        result = context.run(
            [str(argument) for argument in arguments],
            cwd=cwd or context.root,
            env=env or context.environ,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise PreflightError(
            "command-unavailable",
            "A declared read-only check could not run.",
        ) from error
    output_size = len(result.stdout.encode("utf-8", errors="replace")) + len(
        result.stderr.encode("utf-8", errors="replace")
    )
    if output_size > MAX_COMMAND_OUTPUT:
        raise PreflightError(
            "command-output-too-large",
            "A declared read-only check returned too much output.",
        )
    return result


def _which(context, name, *, system=False):
    def locate(path_value):
        try:
            return context.which(name, path=path_value)
        except TypeError:
            return context.which(name)

    inherited_path = context.environ.get("PATH", os.defpath)
    value = locate(os.defpath if system else inherited_path)
    if not value:
        raise PreflightError(
            "executable-missing",
            "The declared {} executable is unavailable.".format(name),
        )
    resolved = _trusted_executable(pathlib.Path(value), name)
    if system:
        inherited = locate(inherited_path)
        if not inherited or _trusted_executable(
            pathlib.Path(inherited), name
        ) != resolved:
            raise PreflightError(
                "executable-path-mismatch",
                (
                    "The caller PATH does not select the verified {} "
                    "executable."
                ).format(name),
            )
    return resolved


def _trusted_executable(path, label):
    try:
        resolved = path.resolve(strict=True)
        status = resolved.stat()
    except OSError as error:
        raise PreflightError(
            "executable-untrusted",
            "The declared {} executable cannot be inspected.".format(label),
        ) from error
    if (
        not stat.S_ISREG(status.st_mode)
        or not os.access(resolved, os.X_OK)
        or status.st_uid not in {0, os.getuid()}
        or status.st_mode & stat.S_IWOTH
        or (
            status.st_mode & stat.S_IWGRP
            and status.st_gid not in {0, os.getgid()}
        )
    ):
        raise PreflightError(
            "executable-untrusted",
            (
                "The declared {} executable has an unsupported owner or mode."
            ).format(label),
        )
    return resolved


def _first_line(result):
    lines = [
        line.strip()
        for line in (result.stdout + "\n" + result.stderr).splitlines()
        if line.strip()
    ]
    return lines[0][:160] if lines else ""


def _require_success(result, code, message):
    if result.returncode != 0:
        raise PreflightError(code, message)


def _dependency(contract, name):
    for item in contract["python_dependencies"]:
        if item["name"] == name:
            return item
    raise PreflightError(
        "contract-invalid",
        "The required Python dependency is undeclared.",
    )


def _parse_version(value):
    match = re.match(r"^(\d+(?:\.\d+)+)", value)
    if match is None:
        raise PreflightError(
            "version-invalid",
            "A declared version is invalid.",
        )
    return tuple(int(part) for part in match.group(1).split("."))


def check_git(contract, specification, context):
    del contract, specification
    path = _which(context, "git", system=True)
    result = _run(context, [path, "--version"])
    _require_success(
        result,
        "git-unavailable",
        "Git did not return its version.",
    )
    version = _first_line(result)
    if re.fullmatch(r"git version \S+", version) is None:
        raise PreflightError(
            "git-version-invalid",
            "Git returned an invalid version.",
        )
    context.resolved["git"] = str(path)
    return {"version": version}


def check_repository(contract, specification, context):
    del specification
    git = context.resolved.get("git")
    if not git:
        raise PreflightError(
            "check-order-invalid",
            "Git was not checked first.",
        )
    result = _run(context, [git, "rev-parse", "--show-toplevel"])
    _require_success(
        result,
        "repository-unavailable",
        "The current directory is not the declared Git checkout.",
    )
    try:
        top = pathlib.Path(result.stdout.strip()).resolve(strict=True)
    except OSError as error:
        raise PreflightError(
            "repository-unavailable",
            "The Git checkout root cannot be inspected.",
        ) from error
    if top != context.root.resolve():
        raise PreflightError(
            "repository-mismatch",
            "The current checkout is not the TrackTemplate repository root.",
        )
    context.resolved["repository"] = str(top)
    return {"root": "."}


def _compatibility_contract(contract, context):
    path = context.root / contract["compatibility_contract"]
    value = _read_json(path)
    try:
        floor = value["runtime_baseline"]["standalone_development_floor"]
        profiles = value["runtime_baseline"]["qualified_profiles"]
        evidence = value["evidence"]
    except (KeyError, TypeError) as error:
        raise PreflightError(
            "compatibility-contract-invalid",
            "The compatibility contract lacks required host data.",
        ) from error
    if not isinstance(profiles, list) or not profiles:
        raise PreflightError(
            "compatibility-contract-invalid",
            "The compatibility contract has no qualified host profile.",
        )
    return value, floor, profiles, evidence


def check_project_python(contract, specification, context):
    del specification
    expected_prefix = (context.root / ".venv").resolve()
    expected_python = _trusted_executable(
        expected_prefix / "bin" / "python",
        "project Python",
    )
    try:
        actual_python = context.python_executable.resolve(strict=True)
        actual_prefix = pathlib.Path(sys.prefix).resolve(strict=True)
    except OSError as error:
        raise PreflightError(
            "project-python-invalid",
            "The active Python environment cannot be inspected.",
        ) from error
    if actual_python != expected_python or actual_prefix != expected_prefix:
        raise PreflightError(
            "project-python-mismatch",
            "Run the preflight with the project .venv Python.",
        )
    _value, floor, _profiles, _evidence = _compatibility_contract(
        contract, context
    )
    try:
        required = _parse_version(floor["pythonmin"])
        implementation = floor["implementation"]
    except (KeyError, TypeError) as error:
        raise PreflightError(
            "compatibility-contract-invalid",
            "The standalone Python floor is invalid.",
        ) from error
    observed = sys.version_info[:3]
    if (
        platform.python_implementation() != implementation
        or observed < required
    ):
        raise PreflightError(
            "project-python-unqualified",
            "The project Python does not meet the declared development floor.",
        )
    context.resolved["project_python"] = str(expected_python)
    return {
        "implementation": implementation,
        "version": ".".join(str(part) for part in observed),
    }


def _requirements(contract, context):
    path = context.root / contract["requirements_file"]
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise PreflightError(
            "requirements-invalid",
            "The development requirements file cannot be read.",
        ) from error
    requirements = []
    for line in lines:
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        match = re.fullmatch(
            r"([A-Za-z][A-Za-z0-9_.-]*)==([0-9]+(?:\.[0-9]+)+(?:[a-z0-9.+-]*)?)",
            value,
        )
        if match is None:
            raise PreflightError(
                "requirements-unpinned",
                (
                    "Development requirements must contain exact package "
                    "pins only."
                ),
            )
        requirements.append((match.group(1).lower(), match.group(2)))
    expected = [
        (item["name"].lower(), item["pin"])
        for item in contract["python_dependencies"]
    ]
    if requirements != expected:
        raise PreflightError(
            "requirements-mismatch",
            "Development requirements do not match the toolchain contract.",
        )
    return requirements


def check_requirements_file(contract, specification, context):
    del specification
    requirements = _requirements(contract, context)
    return {"exact_pin_count": len(requirements)}


def _ruff_version(path, context):
    result = _run(context, [path, "--version"])
    _require_success(
        result,
        "ruff-unavailable",
        "Ruff did not return its version.",
    )
    match = re.fullmatch(r"ruff (\S+)", _first_line(result))
    if match is None:
        raise PreflightError(
            "ruff-version-invalid",
            "Ruff returned an invalid version.",
        )
    return match.group(1)


def _validate_ruff_config(path, ruff, context):
    if not path.is_file():
        raise PreflightError(
            "ruff-config-missing",
            "The Ruff configuration is missing.",
        )
    result = _run(
        context,
        [
            ruff,
            "check",
            "--config",
            path,
            "--no-cache",
            "--stdin-filename",
            "preflight.py",
            "-",
        ],
        input_text="",
    )
    _require_success(
        result,
        "ruff-config-invalid",
        "Ruff did not accept the repository configuration.",
    )


def check_ruff(contract, specification, context):
    required = _dependency(contract, "ruff")["pin"]
    preferred = context.root / ".venv" / "bin" / "ruff"
    if preferred.exists() or preferred.is_symlink():
        path = _trusted_executable(preferred, "Ruff")
        selected = "project-venv"
    else:
        fallback_ids = specification["fallbacks"]
        if fallback_ids != ["ruff-trusted-user-path"]:
            raise PreflightError(
                "fallback-invalid",
                "Ruff has no supported fallback for this state.",
            )
        fallback = contract["fallbacks"][fallback_ids[0]]
        if (
            fallback["tool"] != "ruff"
            or fallback["check"] != "ruff_trusted_user_path"
        ):
            raise PreflightError(
                "fallback-invalid",
                "The declared Ruff fallback is invalid.",
            )
        path = _which(context, "ruff")
        if context.root.resolve() in path.parents:
            raise PreflightError(
                "fallback-invalid",
                "The Ruff fallback must be outside the repository.",
            )
        selected = fallback_ids[0]
    version = _ruff_version(path, context)
    if version != required:
        raise PreflightError(
            "ruff-version-mismatch",
            "Ruff does not match the version in requirements-dev.txt.",
        )
    _validate_ruff_config(
        context.root / contract["ruff_config"],
        path,
        context,
    )
    context.resolved["ruff"] = str(path)
    return {"selection": selected, "version": version}


def check_pdftotext(contract, specification, context):
    del contract, specification
    path = _which(context, "pdftotext", system=True)
    result = _run(context, [path, "-v"])
    _require_success(
        result,
        "pdftotext-unavailable",
        "pdftotext did not return its version.",
    )
    version = _first_line(result)
    if "pdftotext version" not in version:
        raise PreflightError(
            "pdftotext-version-invalid",
            "pdftotext returned an invalid version.",
        )
    context.resolved["pdftotext"] = str(path)
    return {"version": version}


def _sentinel_payload(result, sentinel, status=None):
    matches = [
        line[len(sentinel) :]
        for line in result.stdout.splitlines()
        if line.startswith(sentinel)
    ]
    if result.returncode != 0 or len(matches) != 1:
        raise PreflightError(
            "success-sentinel-missing",
            (
                "A delegated prerequisite check did not return its success "
                "sentinel."
            ),
        )
    try:
        payload = json.loads(matches[0])
    except json.JSONDecodeError as error:
        raise PreflightError(
            "success-sentinel-invalid",
            "A delegated prerequisite check returned an invalid sentinel.",
        ) from error
    if not isinstance(payload, dict) or (
        status is not None and payload.get("status") != status
    ):
        raise PreflightError(
            "delegated-check-failed",
            "A delegated prerequisite check returned an invalid status.",
        )
    return payload


def check_ste_source(contract, specification, context):
    del contract, specification
    python = context.resolved.get("project_python")
    if not python:
        raise PreflightError(
            "check-order-invalid",
            "Project Python was not checked before the STE source.",
        )
    lookup = context.root / "tools" / "ste100_lookup.py"
    status_result = _run(context, [python, lookup, "status"], timeout=30)
    _sentinel_payload(
        status_result,
        "TRACKTEMPLATE_STE100=",
        "verified-source-bound-cache",
    )
    source_result = _run(
        context,
        [python, lookup, "rule", "1.1", "--source"],
        timeout=30,
    )
    source_payload = _sentinel_payload(
        source_result,
        "TRACKTEMPLATE_STE100=",
    )
    if not any("source" in key for key in source_payload):
        raise PreflightError(
            "ste-source-unverified",
            "The STE lookup did not return a verified source excerpt.",
        )
    return {"status": "verified-source-bound-cache-and-extractor"}


def check_flatpak(contract, specification, context):
    del contract, specification
    path = _which(context, "flatpak", system=True)
    result = _run(context, [path, "--version"])
    _require_success(
        result,
        "flatpak-unavailable",
        "Flatpak did not return its version.",
    )
    version = _first_line(result)
    if not version.startswith("Flatpak "):
        raise PreflightError(
            "flatpak-version-invalid",
            "Flatpak returned an invalid version.",
        )
    context.resolved["flatpak"] = str(path)
    return {"version": version}


def check_qualified_freecad(contract, specification, context):
    del specification
    _value, _floor, profiles, evidence = _compatibility_contract(
        contract, context
    )
    qualified_ids = {
        item.get("profile_id")
        for item in profiles
        if isinstance(item, dict)
        and str(item.get("status", "")).startswith("qualified")
    }
    requested = context.requested_profile
    if requested is not None and requested not in qualified_ids:
        raise PreflightError(
            "freecad-profile-undeclared",
            "The requested FreeCAD profile is not qualified.",
        )
    command_text = evidence.get("freecad_probe_command")
    if not isinstance(command_text, str):
        raise PreflightError(
            "compatibility-contract-invalid",
            "The compatibility contract has no FreeCAD probe command.",
        )
    command = shlex.split(command_text)
    allowed_prefix = [
        "flatpak",
        "run",
        "--command=FreeCADCmd",
        "org.freecad.FreeCAD",
        "tools/runtime_compatibility_probe.py",
    ]
    allowed_command = allowed_prefix + ["--pass", "--require-qualified"]
    if command != allowed_command:
        raise PreflightError(
            "compatibility-contract-invalid",
            "The FreeCAD probe command is outside the supported route.",
        )
    command[0] = context.resolved.get("flatpak", command[0])
    result = _run(context, command, timeout=90)
    sentinel = evidence.get("probe_sentinel")
    if not isinstance(sentinel, str):
        raise PreflightError(
            "compatibility-contract-invalid",
            "The compatibility contract has no runtime probe sentinel.",
        )
    payload = _sentinel_payload(result, sentinel)
    evaluation = payload.get("compatibility_evaluation")
    if not isinstance(evaluation, dict):
        raise PreflightError(
            "freecad-unqualified",
            "The FreeCAD probe returned no qualification result.",
        )
    matched = evaluation.get("matched_profile_id")
    if evaluation.get("status") != "qualified" or matched not in qualified_ids:
        raise PreflightError(
            "freecad-unqualified",
            "The FreeCAD host does not match an exact qualified profile.",
        )
    if requested is not None and matched != requested:
        raise PreflightError(
            "freecad-profile-mismatch",
            "The FreeCAD host does not match the requested qualified profile.",
        )
    context.resolved["qualified_freecad"] = str(matched)
    return {"profile_id": matched}


def check_gui_shell_tools(contract, specification, context):
    del contract
    if tuple(specification["components"]) != GUI_SHELL_COMPONENTS:
        raise PreflightError(
            "contract-invalid",
            "The GUI shell prerequisite list changed unexpectedly.",
        )
    exact_paths = {
        "env": pathlib.Path("/usr/bin/env"),
        "openssl": pathlib.Path("/usr/bin/openssl"),
    }
    for name in GUI_SHELL_COMPONENTS:
        if name in exact_paths:
            _trusted_executable(exact_paths[name], name)
        else:
            _which(context, name, system=True)
    return {"component_count": len(GUI_SHELL_COMPONENTS)}


def check_gui_bridge_python(contract, specification, context):
    del specification
    python = _trusted_executable(
        pathlib.Path("/usr/bin/python3"),
        "system Python",
    )
    required = _dependency(contract, "click")["pin"]
    code = (
        "import sys; "
        "sys.path.insert(0, '/usr/lib/python3/dist-packages'); "
        "import importlib.metadata as m; "
        "print(m.version('click'), end='')"
    )
    result = _run(
        context,
        [python, "-I", "-S", "-B", "-c", code],
        env={"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
    )
    _require_success(
        result,
        "gui-bridge-python-unavailable",
        "The GUI bridge system Python cannot import Click.",
    )
    if result.stdout.strip() != required:
        raise PreflightError(
            "gui-bridge-click-mismatch",
            (
                "The GUI bridge Click version does not match "
                "requirements-dev.txt."
            ),
        )
    context.resolved["gui_bridge_python"] = str(python)
    return {"click_version": required}


def _expected_bridge_commit(setup_path):
    try:
        text = setup_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise PreflightError(
            "freecad-cli-setup-invalid",
            "The tracked FreeCAD bridge setup cannot be read.",
        ) from error
    matches = re.findall(
        r'^expected_commit="([0-9a-f]{40})"$',
        text,
        re.MULTILINE,
    )
    if len(matches) != 1:
        raise PreflightError(
            "freecad-cli-setup-invalid",
            "The tracked FreeCAD bridge commit is invalid.",
        )
    return matches[0]


def _reviewed_patch_blobs(patch_path):
    try:
        text = patch_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise PreflightError(
            "freecad-cli-patch-invalid",
            "The reviewed FreeCAD GUI bridge patch cannot be read.",
        ) from error
    headers = re.findall(
        (
            r"^diff --git a/([^\s]+) b/([^\s]+)\n"
            r"index ([0-9a-f]{40})\.\.([0-9a-f]{40}) 100644$"
        ),
        text,
        re.MULTILINE,
    )
    if len(headers) != 6:
        raise PreflightError(
            "freecad-cli-patch-invalid",
            "The reviewed FreeCAD GUI bridge patch index is invalid.",
        )
    blobs = []
    for before_path, after_path, before_blob, after_blob in headers:
        if before_path != after_path:
            raise PreflightError(
                "freecad-cli-patch-invalid",
                "The reviewed FreeCAD GUI bridge patch renames a file.",
            )
        _safe_relative_path(before_path, "FreeCAD GUI bridge patch path")
        blobs.append((before_path, before_blob, after_blob))
    if [item[0] for item in blobs] != sorted(
        {item[0] for item in blobs}
    ):
        raise PreflightError(
            "freecad-cli-patch-invalid",
            "The reviewed FreeCAD GUI bridge patch paths are invalid.",
        )
    return blobs


def _null_paths(result):
    return [value for value in result.stdout.split("\0") if value]


def _check_bridge_tree(git, bridge, patch, context):
    blobs = _reviewed_patch_blobs(patch)
    expected_paths = [item[0] for item in blobs]
    changed = _run(
        context,
        [
            git,
            "-C",
            bridge,
            "diff",
            "--name-only",
            "--no-ext-diff",
            "-z",
            "HEAD",
            "--",
        ],
    )
    _require_success(
        changed,
        "freecad-cli-invalid",
        "The FreeCAD GUI bridge changes cannot be inspected.",
    )
    if _null_paths(changed) != expected_paths:
        raise PreflightError(
            "freecad-cli-tree-mismatch",
            "The FreeCAD GUI bridge has changes outside the reviewed patch.",
        )
    for path, before_blob, after_blob in blobs:
        baseline = _run(
            context,
            [git, "-C", bridge, "rev-parse", "HEAD:{}".format(path)],
        )
        observed = _run(
            context,
            [git, "-C", bridge, "hash-object", "--no-filters", "--", path],
        )
        if (
            baseline.returncode != 0
            or observed.returncode != 0
            or baseline.stdout.strip() != before_blob
            or observed.stdout.strip() != after_blob
        ):
            raise PreflightError(
                "freecad-cli-tree-mismatch",
                "The FreeCAD GUI bridge does not match the reviewed bytes.",
            )

    untracked = _run(
        context,
        [
            git,
            "-C",
            bridge,
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        ],
    )
    ignored = _run(
        context,
        [
            git,
            "-C",
            bridge,
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "-z",
        ],
    )
    _require_success(
        untracked,
        "freecad-cli-invalid",
        "The FreeCAD GUI bridge untracked files cannot be inspected.",
    )
    _require_success(
        ignored,
        "freecad-cli-invalid",
        "The FreeCAD GUI bridge ignored files cannot be inspected.",
    )
    for relative in _null_paths(untracked) + _null_paths(ignored):
        path = pathlib.PurePosixPath(relative)
        candidate = bridge / relative
        try:
            status = candidate.lstat()
        except OSError as error:
            raise PreflightError(
                "freecad-cli-tree-mismatch",
                "The FreeCAD GUI bridge has an unreadable extra file.",
            ) from error
        if (
            stat.S_ISLNK(status.st_mode)
            or path.suffix in {".py", ".pyc", ".pyo", ".pyd", ".so"}
            or status.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        ):
            raise PreflightError(
                "freecad-cli-tree-mismatch",
                "The FreeCAD GUI bridge has an undeclared executable input.",
            )
    return len(blobs)


def check_freecad_cli_checkout(contract, specification, context):
    del contract, specification
    git = context.resolved.get("git")
    python = context.resolved.get("gui_bridge_python")
    if not git or not python:
        raise PreflightError(
            "check-order-invalid",
            "The GUI bridge dependencies were not checked first.",
        )
    bridge = context.root / ".devtools" / "freecad-cli"
    if not (bridge / ".git").is_dir():
        raise PreflightError(
            "freecad-cli-missing",
            "The pinned FreeCAD GUI bridge checkout is unavailable.",
        )
    setup_path = (
        context.root
        / "tools"
        / "freecad_bridge"
        / "setup-freecad-cli"
    )
    expected = _expected_bridge_commit(setup_path)
    head = _run(context, [git, "-C", bridge, "rev-parse", "HEAD"])
    _require_success(
        head,
        "freecad-cli-invalid",
        "The FreeCAD GUI bridge checkout cannot be inspected.",
    )
    if head.stdout.strip() != expected:
        raise PreflightError(
            "freecad-cli-commit-mismatch",
            "The FreeCAD GUI bridge checkout is not at its pinned commit.",
        )
    patch = context.root / "tools" / "freecad_bridge" / (
        "freecad-cli-tracktemplate.patch"
    )
    patch_check = _run(
        context,
        [git, "-C", bridge, "apply", "--reverse", "--check", patch],
    )
    _require_success(
        patch_check,
        "freecad-cli-patch-mismatch",
        "The reviewed FreeCAD GUI bridge patch is not applied.",
    )
    patched_file_count = _check_bridge_tree(
        git,
        bridge,
        patch,
        context,
    )
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-bridge-pycache-"
    ) as pycache:
        checkout_test = _run(
            context,
            [
                python,
                "-I",
                "-S",
                "-B",
                "-X",
                "pycache_prefix={}".format(pycache),
                context.root
                / "tools"
                / "freecad_bridge"
                / "test_freecad_cli_checkout.py",
            ],
            env={"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
            timeout=30,
        )
    _require_success(
        checkout_test,
        "freecad-cli-tests-failed",
        "The pinned FreeCAD GUI bridge tests failed.",
    )
    if "22 bridge tests passed" not in checkout_test.stdout:
        raise PreflightError(
            "freecad-cli-sentinel-missing",
            "The FreeCAD GUI bridge tests returned no success sentinel.",
        )
    return {
        "commit": expected,
        "patched_file_count": patched_file_count,
        "test_count": 22,
    }


def check_gh(contract, specification, context):
    del contract, specification
    path = _which(context, "gh", system=True)
    result = _run(context, [path, "--version"])
    _require_success(
        result,
        "gh-unavailable",
        "GitHub CLI did not return its version.",
    )
    version = _first_line(result)
    if not version.startswith("gh version "):
        raise PreflightError(
            "gh-version-invalid",
            "GitHub CLI returned an invalid version.",
        )
    context.resolved["gh"] = str(path)
    return {"version": version}


def _github_slug(remote_url):
    remote_url = remote_url.strip()
    if remote_url.startswith("git@github.com:"):
        path = remote_url[len("git@github.com:") :]
    else:
        parsed = urlparse(remote_url)
        if (
            parsed.scheme not in {"https", "ssh"}
            or parsed.hostname != "github.com"
            or parsed.password is not None
            or parsed.username not in {None, "git"}
        ):
            return ""
        path = parsed.path.lstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return path


def check_github_access(contract, specification, context):
    del specification
    git = context.resolved.get("git")
    gh = context.resolved.get("gh")
    if not git or not gh:
        raise PreflightError(
            "check-order-invalid",
            "Git and GitHub CLI were not checked before repository access.",
        )
    repository = contract["repository"]
    remote_result = _run(
        context,
        [git, "remote", "get-url", repository["remote"]],
    )
    _require_success(
        remote_result,
        "github-origin-missing",
        "The expected Git remote is unavailable.",
    )
    if _github_slug(remote_result.stdout) != repository["github"]:
        raise PreflightError(
            "github-origin-mismatch",
            "The Git remote does not match the expected GitHub repository.",
        )
    environment = context.environ.copy()
    environment.update(
        {
            "GH_HOST": "github.com",
            "GH_PROMPT_DISABLED": "1",
            "NO_COLOR": "1",
        }
    )
    auth = _run(
        context,
        [gh, "auth", "status", "--hostname", "github.com"],
        env=environment,
    )
    _require_success(
        auth,
        "github-authentication-failed",
        "GitHub CLI authentication is unavailable.",
    )
    view = _run(
        context,
        [
            gh,
            "repo",
            "view",
            repository["github"],
            "--json",
            "nameWithOwner,defaultBranchRef,viewerPermission",
        ],
        env=environment,
    )
    _require_success(
        view,
        "github-access-failed",
        "GitHub repository access is unavailable.",
    )
    try:
        payload = json.loads(view.stdout)
        name = payload["nameWithOwner"]
        default_branch = payload["defaultBranchRef"]["name"]
        permission = payload["viewerPermission"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise PreflightError(
            "github-access-invalid",
            "GitHub returned an invalid repository-access record.",
        ) from error
    if (
        name != repository["github"]
        or default_branch != repository["default_branch"]
        or permission not in {"ADMIN", "MAINTAIN", "WRITE"}
    ):
        raise PreflightError(
            "github-access-insufficient",
            (
                "GitHub identity, default branch, or write access is "
                "insufficient."
            ),
        )
    return {
        "default_branch": default_branch,
        "permission": permission,
        "repository": name,
    }


CHECKS = {
    "flatpak": check_flatpak,
    "freecad_cli_checkout": check_freecad_cli_checkout,
    "gh": check_gh,
    "git": check_git,
    "github_access": check_github_access,
    "gui_bridge_python": check_gui_bridge_python,
    "gui_shell_tools": check_gui_shell_tools,
    "pdftotext": check_pdftotext,
    "project_python": check_project_python,
    "qualified_freecad": check_qualified_freecad,
    "repository": check_repository,
    "requirements_file": check_requirements_file,
    "ruff": check_ruff,
    "ste_source": check_ste_source,
}


def evaluate_stage(stage, contract, *, context=None, checks=None):
    """Evaluate one stage and stop at its first failed prerequisite."""
    validate_contract(contract)
    if stage not in STAGES:
        raise PreflightError(
            "stage-invalid",
            "The requested stage is undeclared.",
        )
    context = context or Context()
    checks = checks or CHECKS
    if set(checks) != CHECK_IDS:
        raise PreflightError(
            "handler-set-invalid",
            "The preflight check handler set is incomplete.",
        )
    results = []
    tool_ids = contract["stages"][stage]
    for index, tool_id in enumerate(tool_ids):
        specification = contract["tools"][tool_id]
        check_id = specification["check"]
        try:
            detail = checks[check_id](contract, specification, context)
        except PreflightError as error:
            results.append(
                {
                    "code": error.code,
                    "message": str(error),
                    "status": "failed",
                    "tool": tool_id,
                }
            )
            return {
                "checks": results,
                "contract_id": contract["contract_id"],
                "skipped": tool_ids[index + 1 :],
                "stage": stage,
                "status": "failed",
            }, context
        results.append(
            {
                "detail": detail,
                "status": "passed",
                "tool": tool_id,
            }
        )
    return {
        "checks": results,
        "contract_id": contract["contract_id"],
        "skipped": [],
        "stage": stage,
        "status": "passed",
    }, context


def _emit(sentinel, payload, *, stream=None):
    print(
        sentinel + json.dumps(payload, sort_keys=True, separators=(",", ":")),
        file=stream or sys.stdout,
        flush=True,
    )


def run_required_ruff(contract, context):
    """Run the fixed read-only Ruff check after validation preflight passes."""
    ruff = context.resolved.get("ruff")
    if not ruff:
        raise PreflightError(
            "ruff-preflight-missing",
            "Ruff cannot run before its validation preflight passes.",
        )
    result = _run(
        context,
        [
            ruff,
            "check",
            "--config",
            context.root / contract["ruff_config"],
            "--no-cache",
            ".",
        ],
        timeout=60,
    )
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, end="", file=sys.stderr)
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        raise PreflightError(
            "ruff-check-failed",
            "The required read-only Ruff check failed.",
        )
    return {
        "config": contract["ruff_config"],
        "status": "passed",
        "version": _dependency(contract, "ruff")["pin"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument(
        "--profile-id",
        help="Require one already-qualified exact FreeCAD profile.",
    )
    parser.add_argument(
        "--run-ruff",
        action="store_true",
        help="Run the fixed Ruff check after validation preflight.",
    )
    arguments = parser.parse_args(argv)
    if (
        arguments.profile_id
        and arguments.stage not in {"freecad", "freecad-gui"}
    ):
        parser.error("--profile-id requires a FreeCAD stage")
    if arguments.run_ruff and arguments.stage != "validation":
        parser.error("--run-ruff requires --stage validation")
    try:
        contract = load_contract()
        payload, context = evaluate_stage(
            arguments.stage,
            contract,
            context=Context(requested_profile=arguments.profile_id),
        )
    except PreflightError as error:
        _emit(
            SENTINEL,
            {
                "code": error.code,
                "message": str(error),
                "stage": arguments.stage,
                "status": "invalid",
            },
            stream=sys.stderr,
        )
        return 2
    _emit(SENTINEL, payload)
    if payload["status"] != "passed":
        return 1
    if arguments.run_ruff:
        try:
            ruff_payload = run_required_ruff(contract, context)
        except PreflightError as error:
            _emit(
                RUFF_SENTINEL,
                {
                    "code": error.code,
                    "message": str(error),
                    "status": "failed",
                },
                stream=sys.stderr,
            )
            return 1
        _emit(RUFF_SENTINEL, ruff_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
