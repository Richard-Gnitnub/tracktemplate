#!/usr/bin/env python3
"""Validate the stage-specific development-toolchain preflight contract."""

from __future__ import annotations

import ast
import copy
import json
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import tomllib


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import development_toolchain_preflight as preflight  # noqa: E402
from tools import run_regression_pipeline as pipeline_module  # noqa: E402


EXPECTED_STAGES = {
    "development": {"git", "repository", "project_python"},
    "documentation": {
        "git",
        "pdftotext",
        "project_python",
        "repository",
        "ste_source",
    },
    "freecad": {"flatpak", "git", "qualified_freecad", "repository"},
    "freecad-gui": {
        "flatpak",
        "freecad_cli_checkout",
        "git",
        "gui_bridge_python",
        "gui_shell_tools",
        "qualified_freecad",
        "repository",
        "requirements_file",
    },
    "publication": {"gh", "git", "github_access", "repository"},
    "validation": {
        "git",
        "project_python",
        "repository",
        "requirements_file",
        "ruff",
    },
}


def _expect_error(function, code):
    try:
        function()
    except preflight.PreflightError as error:
        assert error.code == code, (error.code, code)
    else:
        raise AssertionError("Expected preflight error: {}".format(code))


def _validate_declaration(contract):
    assert set(contract["stages"]) == set(preflight.STAGES)
    assert {
        stage: set(tool_ids)
        for stage, tool_ids in contract["stages"].items()
    } == EXPECTED_STAGES
    assert set(contract["tools"]) == preflight.CHECK_IDS
    assert {
        value["check"] for value in contract["tools"].values()
    } == preflight.CHECK_IDS
    assert set(preflight.CHECKS) == preflight.CHECK_IDS
    assert contract["fallbacks"] == {
        "ruff-trusted-user-path": {
            "authority": "reference/VALIDATION.md#developer-tool-boundary",
            "check": "ruff_trusted_user_path",
            "tool": "ruff",
        }
    }
    assert contract["tools"]["ruff"]["fallbacks"] == [
        "ruff-trusted-user-path"
    ]
    assert all(
        not specification["fallbacks"]
        for tool_id, specification in contract["tools"].items()
        if tool_id != "ruff"
    )

    dependencies = {
        item["name"]: (item["pin"], tuple(item["stages"]), item["tool"])
        for item in contract["python_dependencies"]
    }
    assert dependencies == {
        "click": ("8.1.6", ("freecad-gui",), "gui_bridge_python"),
        "ruff": ("0.16.4", ("validation",), "ruff"),
    }
    requirements = [
        line.strip()
        for line in (ROOT / contract["requirements_file"])
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert requirements == ["click==8.1.6", "ruff==0.16.4"]
    assert all(
        "==" in requirement
        and not any(
            marker in requirement
            for marker in ("://", "git+", " -e ", ";", "@")
        )
        for requirement in requirements
    )


def _validate_ruff_contract(contract):
    configuration = tomllib.loads(
        (ROOT / contract["ruff_config"]).read_text(encoding="utf-8")
    )
    assert configuration["required-version"] == "==0.16.4"
    assert configuration["target-version"] == "py312"
    assert configuration["lint"]["select"] == ["E9", "F63", "F7", "F82"]
    assert configuration["lint"]["per-file-ignores"] == {
        "tools/freecad_bridge/probes/finish_phase3_transition_workflow.py": [
            "F821"
        ]
    }
    assert "AdvancedTurnout.FCMacro" in configuration["extend-exclude"]
    assert any(
        item.endswith("chair_performance_and_representation.FCMacro")
        for item in configuration["extend-exclude"]
    )

    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-wrong-ruff-"
    ) as temporary:
        root = pathlib.Path(temporary)
        preferred = root / ".venv" / "bin" / "ruff"
        preferred.parent.mkdir(parents=True)
        preferred.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        preferred.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        (root / "ruff.toml").write_text("", encoding="utf-8")
        fallback_used = []

        def run(arguments, **kwargs):
            del kwargs
            assert pathlib.Path(arguments[0]).resolve() == preferred.resolve()
            return subprocess.CompletedProcess(
                arguments,
                0,
                stdout="ruff 99.0.0\n",
                stderr="",
            )

        def which(name, path=None):
            fallback_used.append((name, path))
            return "/unexpected/fallback"

        context = preflight.Context(root=root, run=run, which=which)
        _expect_error(
            lambda: preflight.check_ruff(
                contract,
                contract["tools"]["ruff"],
                context,
            ),
            "ruff-version-mismatch",
        )
        assert fallback_used == []


def _fake_checks(calls, failing=None):
    def make(check_id):
        def check(contract, specification, context):
            del contract, specification, context
            calls.append(check_id)
            if check_id == failing:
                raise preflight.PreflightError(
                    "fixture-missing",
                    "Fixture tool is missing.",
                )
            return {"fixture": "passed"}

        return check

    return {check_id: make(check_id) for check_id in preflight.CHECK_IDS}


def _validate_stage_isolation_and_failure(contract):
    for stage, expected in EXPECTED_STAGES.items():
        calls = []
        payload, _context = preflight.evaluate_stage(
            stage,
            contract,
            checks=_fake_checks(calls),
        )
        assert payload["status"] == "passed"
        assert calls == contract["stages"][stage]
        assert set(calls) == expected

    calls = []
    payload, context = preflight.evaluate_stage(
        "validation",
        contract,
        checks=_fake_checks(calls, failing="ruff"),
    )
    assert payload["status"] == "failed"
    assert payload["checks"][-1]["code"] == "fixture-missing"
    assert calls[-1] == "ruff"
    _expect_error(
        lambda: preflight.run_required_ruff(contract, context),
        "ruff-preflight-missing",
    )

    changed = copy.deepcopy(contract)
    changed["tools"]["git"]["fallbacks"] = ["improvised-git"]
    _expect_error(
        lambda: preflight.validate_contract(changed),
        "contract-invalid",
    )
    changed = copy.deepcopy(contract)
    changed["tools"]["git"]["check"] = "shell_command"
    _expect_error(
        lambda: preflight.validate_contract(changed),
        "contract-invalid",
    )


def _validate_exact_host(contract):
    compatibility = json.loads(
        (ROOT / contract["compatibility_contract"]).read_text(encoding="utf-8")
    )
    qualified = {
        item["profile_id"]
        for item in compatibility["runtime_baseline"]["qualified_profiles"]
        if item["status"].startswith("qualified")
    }
    assert qualified
    support_rule = compatibility["runtime_baseline"]["support_rule"]
    assert "exact_match" in support_rule
    assert "different host is not qualified" in support_rule

    unknown = "linux-x86_64-flatpak-freecad-arbitrary"
    calls = []

    def run(arguments, **kwargs):
        del kwargs
        calls.append(arguments)
        payload = {
            "compatibility_evaluation": {
                "matched_profile_id": unknown,
                "mismatches": [],
                "status": "qualified",
            }
        }
        return subprocess.CompletedProcess(
            arguments,
            0,
            stdout=(
                compatibility["evidence"]["probe_sentinel"]
                + json.dumps(payload)
                + "\n"
            ),
            stderr="",
        )

    context = preflight.Context(root=ROOT, run=run)
    context.resolved["flatpak"] = "/usr/bin/flatpak"
    _expect_error(
        lambda: preflight.check_qualified_freecad(
            contract,
            contract["tools"]["qualified_freecad"],
            context,
        ),
        "freecad-unqualified",
    )
    assert len(calls) == 1

    no_run_calls = []
    context = preflight.Context(
        root=ROOT,
        requested_profile=unknown,
        run=lambda *args, **kwargs: no_run_calls.append((args, kwargs)),
    )
    context.resolved["flatpak"] = "/usr/bin/flatpak"
    _expect_error(
        lambda: preflight.check_qualified_freecad(
            contract,
            contract["tools"]["qualified_freecad"],
            context,
        ),
        "freecad-profile-undeclared",
    )
    assert no_run_calls == []


def _validate_system_tool_resolution(contract):
    observed_paths = []

    def which(name, path=None):
        observed_paths.append((name, path))
        return "/usr/bin/{}".format(name)

    versions = {
        "flatpak": "Flatpak 1.14.6\n",
        "gh": "gh version 2.100.0\n",
        "git": "git version 2.43.0\n",
    }

    def run(arguments, **kwargs):
        del kwargs
        return subprocess.CompletedProcess(
            arguments,
            0,
            stdout=versions[pathlib.Path(arguments[0]).name],
            stderr="",
        )

    context = preflight.Context(
        root=ROOT,
        environ={"PATH": os.defpath},
        run=run,
        which=which,
    )
    for tool_id, check in (
        ("git", preflight.check_git),
        ("flatpak", preflight.check_flatpak),
        ("gh", preflight.check_gh),
    ):
        check(contract, contract["tools"][tool_id], context)
    assert observed_paths == [
        ("git", os.defpath),
        ("git", os.defpath),
        ("flatpak", os.defpath),
        ("flatpak", os.defpath),
        ("gh", os.defpath),
        ("gh", os.defpath),
    ]

    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-adversarial-path-"
    ) as temporary:
        attacker = pathlib.Path(temporary) / "git"
        attacker.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        attacker.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

        def adversarial_which(name, path=None):
            assert name == "git"
            if path == "/attacker/bin":
                return str(attacker)
            return "/usr/bin/git"

        context = preflight.Context(
            root=ROOT,
            environ={"PATH": "/attacker/bin"},
            run=run,
            which=adversarial_which,
        )
        _expect_error(
            lambda: preflight.check_git(
                contract,
                contract["tools"]["git"],
                context,
            ),
            "executable-path-mismatch",
        )


def _validate_isolated_system_python(contract):
    hostile = {
        "HOME": "/attacker/home",
        "PATH": "/attacker/bin",
        "PYTHONHOME": "/attacker/python",
        "PYTHONPATH": "/attacker/modules",
    }
    calls = []

    def run(arguments, **kwargs):
        calls.append((arguments, kwargs))
        return subprocess.CompletedProcess(
            arguments,
            0,
            stdout="8.1.6",
            stderr="",
        )

    context = preflight.Context(root=ROOT, environ=hostile, run=run)
    result = preflight.check_gui_bridge_python(
        contract,
        contract["tools"]["gui_bridge_python"],
        context,
    )
    assert result == {"click_version": "8.1.6"}
    arguments, keywords = calls[0]
    assert arguments[1:4] == ["-I", "-S", "-B"]
    assert keywords["env"] == {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    assert all(key not in keywords["env"] for key in hostile)


def _validate_bridge_tree_integrity(contract):
    del contract
    patch = ROOT / "tools" / "freecad_bridge" / (
        "freecad-cli-tracktemplate.patch"
    )
    blobs = preflight._reviewed_patch_blobs(patch)
    assert len(blobs) == 6
    expected_paths = [item[0] for item in blobs]

    def make_run(
        *,
        extra_changed="",
        extra_ignored="",
        extra_untracked="",
    ):
        def run(arguments, **kwargs):
            del kwargs
            if "diff" in arguments:
                output = "\0".join(expected_paths + [extra_changed]) + "\0"
            elif "rev-parse" in arguments:
                relative = arguments[-1].split(":", 1)[1]
                output = next(
                    before for path, before, _after in blobs
                    if path == relative
                ) + "\n"
            elif "hash-object" in arguments:
                relative = arguments[-1]
                output = next(
                    after for path, _before, after in blobs
                    if path == relative
                ) + "\n"
            elif "ls-files" in arguments:
                value = (
                    extra_ignored
                    if "--ignored" in arguments
                    else extra_untracked
                )
                output = value + ("\0" if value else "")
            else:
                raise AssertionError(arguments)
            return subprocess.CompletedProcess(
                arguments,
                0,
                stdout=output,
                stderr="",
            )

        return run

    bridge = ROOT / ".devtools" / "freecad-cli"
    context = preflight.Context(root=ROOT, run=make_run())
    assert preflight._check_bridge_tree(
        "/usr/bin/git", bridge, patch, context
    ) == 6

    context = preflight.Context(
        root=ROOT,
        run=make_run(extra_changed="src/freecad_cli/extra.py"),
    )
    _expect_error(
        lambda: preflight._check_bridge_tree(
            "/usr/bin/git", bridge, patch, context
        ),
        "freecad-cli-tree-mismatch",
    )

    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-bridge-tree-"
    ) as temporary:
        isolated_bridge = pathlib.Path(temporary)
        extra = isolated_bridge / "extra.py"
        extra.write_text("raise RuntimeError('must not run')\n", encoding="utf-8")
        context = preflight.Context(
            root=ROOT,
            run=make_run(extra_untracked="extra.py"),
        )
        _expect_error(
            lambda: preflight._check_bridge_tree(
                "/usr/bin/git", isolated_bridge, patch, context
            ),
            "freecad-cli-tree-mismatch",
        )

        cache = isolated_bridge / "__pycache__" / "extra.pyc"
        cache.parent.mkdir()
        cache.write_bytes(b"unreviewed bytecode")
        context = preflight.Context(
            root=ROOT,
            run=make_run(extra_ignored="__pycache__/extra.pyc"),
        )
        _expect_error(
            lambda: preflight._check_bridge_tree(
                "/usr/bin/git", isolated_bridge, patch, context
            ),
            "freecad-cli-tree-mismatch",
        )

    driver = (
        ROOT / "tools" / "freecad_bridge" / "test_freecad_cli_checkout.py"
    ).read_text(encoding="utf-8")
    assert "TEST_FILES = (" in driver
    assert '.glob("test_*.py")' not in driver
    source = (
        ROOT / "tools" / "development_toolchain_preflight.py"
    ).read_text(encoding="utf-8")
    assert source.index("patched_file_count = _check_bridge_tree(") < source.index(
        '"test_freecad_cli_checkout.py"'
    )
    assert '"pycache_prefix={}"' in source
    setup = (
        ROOT / "tools" / "freecad_bridge" / "setup-freecad-cli"
    ).read_text(encoding="utf-8")
    launcher = (
        ROOT / "tools" / "freecad_bridge" / "launch-freecad"
    ).read_text(encoding="utf-8")
    isolated = (
        ROOT / "tools" / "freecad_bridge" / "run-isolated"
    ).read_text(encoding="utf-8")
    client = (
        ROOT / "tools" / "freecad_bridge" / "freecad-cli"
    ).read_text(encoding="utf-8")
    gui_wrapper = (
        ROOT
        / "tools"
        / "freecad_bridge"
        / "run-phase5-transition-viewprovider"
    ).read_text(encoding="utf-8")
    gui_runner = (
        ROOT
        / "tools"
        / "freecad_bridge"
        / "run_phase5_transition_viewprovider.py"
    ).read_text(encoding="utf-8")
    patch_text = patch.read_text(encoding="utf-8")
    assert (
        ".venv/bin/python tools/development_toolchain_preflight.py "
        "--stage freecad-gui"
    ) in setup
    assert '--env="PYTHONDONTWRITEBYTECODE=1"' in launcher
    assert '--env="PYTHONPYCACHEPREFIX=' in launcher
    assert "export PYTHONDONTWRITEBYTECODE PYTHONPYCACHEPREFIX" in isolated
    assert "/usr/bin/python3 -I -S -B" in client
    assert "/usr/bin/env -i LANG=C.UTF-8 LC_ALL=C.UTF-8" in gui_wrapper
    assert "/usr/bin/python3 -I -S -B" in gui_wrapper
    assert "PYTHONPATH" not in gui_wrapper
    assert 'sys.path.append("/usr/lib/python3/dist-packages")' in gui_runner
    assert "sys.dont_write_bytecode = True" in patch_text


def _validate_github_output_redaction(contract):
    secret = "ghp_fixture_secret_that_must_not_escape"

    def run(arguments, **kwargs):
        environment = kwargs["env"]
        if pathlib.Path(arguments[0]).name == "gh":
            assert environment["GH_HOST"] == "github.com"
            assert environment["GH_PROMPT_DISABLED"] == "1"
        if arguments[1:4] == ["remote", "get-url", "origin"]:
            return subprocess.CompletedProcess(
                arguments,
                0,
                stdout="https://github.com/Richard-Gnitnub/tracktemplate.git\n",
                stderr="",
            )
        if arguments[1:3] == ["auth", "status"]:
            return subprocess.CompletedProcess(
                arguments,
                0,
                stdout="",
                stderr="authenticated with {}\n".format(secret),
            )
        if arguments[1:3] == ["repo", "view"]:
            payload = {
                "defaultBranchRef": {"name": "main"},
                "nameWithOwner": "Richard-Gnitnub/tracktemplate",
                "viewerPermission": "ADMIN",
            }
            return subprocess.CompletedProcess(
                arguments,
                0,
                stdout=json.dumps(payload),
                stderr="",
            )
        raise AssertionError(arguments)

    context = preflight.Context(root=ROOT, run=run)
    context.resolved.update({"gh": "/usr/bin/gh", "git": "/usr/bin/git"})
    result = preflight.check_github_access(
        contract,
        contract["tools"]["github_access"],
        context,
    )
    assert secret not in json.dumps(result)
    assert result == {
        "default_branch": "main",
        "permission": "ADMIN",
        "repository": "Richard-Gnitnub/tracktemplate",
    }

    def failing_run(arguments, **kwargs):
        completed = run(arguments, **kwargs)
        if arguments[1:3] == ["auth", "status"]:
            completed.returncode = 1
        return completed

    context = preflight.Context(root=ROOT, run=failing_run)
    context.resolved.update({"gh": "/usr/bin/gh", "git": "/usr/bin/git"})
    try:
        preflight.check_github_access(
            contract,
            contract["tools"]["github_access"],
            context,
        )
    except preflight.PreflightError as error:
        assert error.code == "github-authentication-failed"
        assert secret not in str(error)
    else:
        raise AssertionError("Expected the failed authentication check to stop")


def _validate_consumers(contract):
    command = ".venv/bin/python tools/development_toolchain_preflight.py"
    for relative_path, stages in contract["consumers"].items():
        if relative_path == "tools/run_regression_pipeline.py":
            continue
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for stage in stages:
            expected = "{} --stage {}".format(command, stage)
            assert expected in text, (relative_path, expected)

    publish = (
        ROOT / ".agents" / "skills" / "tracktemplate-publish" / "SKILL.md"
    ).read_text(encoding="utf-8")
    publish = " ".join(publish.split())
    publish_preflight = publish.index("--stage publication")
    assert publish_preflight < publish.index("Fetch remote state")
    assert publish_preflight < publish.index("make a descriptive `agent/")

    pipeline = (
        ROOT / "tools" / "run_regression_pipeline.py"
    ).read_text(encoding="utf-8")
    assert pipeline.index('"validation-preflight-and-ruff"') < pipeline.index(
        '"python-syntax"'
    )
    assert pipeline.index('"freecad-preflight"') < pipeline.index(
        '"transition-persistence"'
    )
    assert pipeline.index('"freecad-gui-preflight"') < pipeline.index(
        '"transition-viewprovider-gui"'
    )
    transition_steps = pipeline_module.build_steps(
        "transition",
        root=ROOT,
        python_executable="python-under-test",
    )
    freecad_command = next(
        step.command
        for step in transition_steps
        if step.name == "transition-persistence"
    )
    assert pathlib.Path(freecad_command[0]).is_absolute()

    for relative in (
        "tools/freecad_bridge/freecad-cli",
        "tools/freecad_bridge/launch-freecad",
        "tools/freecad_bridge/run-isolated",
        "tools/freecad_bridge/setup-freecad-cli",
    ):
        script = (ROOT / relative).read_text(encoding="utf-8")
        assert "PATH=/bin:/usr/bin\nexport PATH" in script, relative


def _validate_security_and_runtime_separation(contract):
    toolchain_configuration = (
        ROOT / "reference" / "contracts" / "development-toolchain-v1.json",
        ROOT / "requirements-dev.txt",
        ROOT / "ruff.toml",
    )
    for path in toolchain_configuration:
        lowered = path.read_text(encoding="utf-8").lower()
        assert all(
            marker not in lowered
            for marker in (
                "ghp_",
                "github_pat_",
                '"password"',
                '"secret"',
                '"token"',
                "/home/",
                "~/.ssh",
            )
        ), path
    changed = copy.deepcopy(contract)
    changed["token"] = "fixture"
    _expect_error(
        lambda: preflight.validate_contract(changed),
        "contract-sensitive-material",
    )

    source = (
        ROOT / "tools" / "development_toolchain_preflight.py"
    ).read_text(encoding="utf-8")
    assert "gh auth token" not in source
    assert "shell=True" not in source
    assert "pip install" not in source
    assert "uv add" not in source
    assert '"--fix"' not in source
    assert 'parser.add_argument("--contract"' not in source
    assert 'parser.add_argument("--root"' not in source

    development_packages = {
        item["name"].replace("-", "_")
        for item in contract["python_dependencies"]
    }
    product_paths = list((ROOT / "tracktemplate").rglob("*.py"))
    product_paths.append(ROOT / "TrackTemplate.FCMacro")
    imported = set()
    for path in product_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(
                    alias.name.split(".", 1)[0]
                    for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
    assert development_packages.isdisjoint(imported)
    assert not (ROOT / "package.xml").exists()


def validate():
    contract = preflight.load_contract()
    _validate_declaration(contract)
    _validate_ruff_contract(contract)
    _validate_stage_isolation_and_failure(contract)
    _validate_exact_host(contract)
    _validate_system_tool_resolution(contract)
    _validate_isolated_system_python(contract)
    _validate_bridge_tree_integrity(contract)
    _validate_github_output_redaction(contract)
    _validate_consumers(contract)
    _validate_security_and_runtime_separation(contract)
    print("Development toolchain preflight contract passed")


if __name__ == "__main__":
    validate()
