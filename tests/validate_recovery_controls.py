#!/usr/bin/env python3
"""Validate the recovery policy and read-only repository safety audit."""

import ast
import json
import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import repository_safety_audit as safety  # noqa: E402


POLICY_PATH = ROOT / "reference" / "RECOVERY_AND_BACKUP.md"
VALIDATION_PATH = ROOT / "reference" / "VALIDATION.md"
PROJECT_PLAN_PATH = ROOT / "reference" / "PROJECT_PLAN.md"
AGENTS_PATH = ROOT / "AGENTS.md"
GITIGNORE_PATH = ROOT / ".gitignore"
TOOL_PATH = ROOT / "tools" / "repository_safety_audit.py"
BANNED_GIT_ACTIONS = {
    "clean",
    "reset",
    "checkout",
    "restore",
    "push",
    "branch",
    "tag",
    "rebase",
    "merge",
    "commit",
    "add",
    "rm",
}


def _run(arguments, cwd=None, check=True):
    result = subprocess.run(
        arguments,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode:
        raise AssertionError(
            "command failed: {}\n{}".format(" ".join(arguments), result.stderr)
        )
    return result


def _git_fixture(temp_root):
    repository = temp_root / "repository"
    remote = temp_root / "remote.git"
    repository.mkdir()
    _run(["git", "init", "--bare", str(remote)])
    _run(["git", "init", "-b", "main"], cwd=repository)
    _run(["git", "config", "user.name", "Safety Fixture"], cwd=repository)
    _run(
        ["git", "config", "user.email", "safety-fixture@example.invalid"],
        cwd=repository,
    )
    (repository / "tracked.txt").write_text("checkpoint\n", encoding="utf-8")
    _run(["git", "add", "tracked.txt"], cwd=repository)
    _run(["git", "commit", "-m", "Initial checkpoint"], cwd=repository)
    _run(["git", "remote", "add", "origin", str(remote)], cwd=repository)
    _run(["git", "push", "-u", "origin", "main"], cwd=repository)
    return repository


def _validate_repository_state(errors):
    with tempfile.TemporaryDirectory(prefix="tracktemplate-safety-") as temp:
        repository = _git_fixture(pathlib.Path(temp))
        clean = safety._repository_state(repository.resolve())
        if not clean["checkpoint_ready"] or clean["ahead"] != 0 or clean[
            "behind"
        ] != 0:
            errors.append("clean pushed fixture was not checkpoint-ready")

        untracked = repository / "untracked.txt"
        untracked.write_text("not protected\n", encoding="utf-8")
        if safety._repository_state(repository.resolve())["checkpoint_ready"]:
            errors.append("untracked data did not block checkpoint readiness")
        untracked.unlink()

        (repository / "tracked.txt").write_text("ahead\n", encoding="utf-8")
        _run(["git", "add", "tracked.txt"], cwd=repository)
        _run(["git", "commit", "-m", "Ahead checkpoint"], cwd=repository)
        ahead = safety._repository_state(repository.resolve())
        if ahead["checkpoint_ready"] or ahead["ahead"] != 1:
            errors.append("unpushed commit did not block checkpoint readiness")
        _run(["git", "push"], cwd=repository)
        if not safety._repository_state(repository.resolve())["checkpoint_ready"]:
            errors.append("pushed fixture did not return to checkpoint readiness")


def _validate_backup_assessment(errors):
    ready = safety.evaluate_backup_location(
        configured=True,
        exists=True,
        is_directory=True,
        inside_repository=False,
        repository_device=1,
        target_device=2,
        writable=True,
    )
    if not ready["location_ready"] or ready["backup_completed"] or ready[
        "restore_tested"
    ]:
        errors.append("different-device target readiness was overstated or lost")

    cases = (
        {
            "configured": False,
            "exists": False,
            "is_directory": False,
            "inside_repository": False,
            "repository_device": 1,
            "target_device": None,
            "writable": False,
            "reason": "not-configured",
        },
        {
            "configured": True,
            "exists": True,
            "is_directory": True,
            "inside_repository": True,
            "repository_device": 1,
            "target_device": 1,
            "writable": True,
            "reason": "target-is-inside-repository",
        },
        {
            "configured": True,
            "exists": True,
            "is_directory": True,
            "inside_repository": False,
            "repository_device": 1,
            "target_device": 1,
            "writable": True,
            "reason": "target-is-on-the-same-filesystem",
        },
    )
    for case in cases:
        expected_reason = case.pop("reason")
        result = safety.evaluate_backup_location(**case)
        if result["location_ready"] or result["reason"] != expected_reason:
            errors.append("backup target rejection drifted: " + expected_reason)


def _validate_live_audit(errors):
    before = _run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
    ).stdout
    report = safety.audit_repository(ROOT)
    after = _run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
    ).stdout
    if before != after:
        errors.append("repository safety audit mutated the working tree")
    if report.get("schema_version") != 1 or report.get("repository_root") != ".":
        errors.append("repository safety report identity drifted")
    if report["repository"].get("branch") != "main" or report[
        "repository"
    ].get("upstream") != "origin/main":
        errors.append("live repository branch/upstream identity drifted")
    source = next(
        item
        for item in report["local_assets"]
        if item["path"] == safety.SOURCE_ARCHIVE_PATH.as_posix()
    )
    if (
        not source["present"]
        or source["sha256"] != safety.SOURCE_ARCHIVE_SHA256
        or source["hash_matches"] is not True
    ):
        errors.append("ignored Templot source evidence is missing or changed")
    if report["backup_target"] != safety._backup_target_state(ROOT, None):
        errors.append("unconfigured backup target does not fail closed")

    result = _run(
        [sys.executable, str(TOOL_PATH), "--require-critical-assets"],
        cwd=ROOT,
    )
    records = [
        line[len(safety.SENTINEL):]
        for line in result.stdout.splitlines()
        if line.startswith(safety.SENTINEL)
    ]
    if len(records) != 1 or not json.loads(records[0])["requested_requirements"][
        "critical_assets"
    ]:
        errors.append("critical-asset CLI requirement did not pass")

    blocked = _run(
        [sys.executable, str(TOOL_PATH), "--require-backup-target"],
        cwd=ROOT,
        check=False,
    )
    if blocked.returncode == 0:
        errors.append("missing independent backup target did not fail closed")


def _validate_static_controls(errors):
    policy = POLICY_PATH.read_text(encoding="utf-8")
    agents = AGENTS_PATH.read_text(encoding="utf-8")
    validation = VALIDATION_PATH.read_text(encoding="utf-8")
    project_plan = PROJECT_PLAN_PATH.read_text(encoding="utf-8")
    gitignore = GITIGNORE_PATH.read_text(encoding="utf-8")
    policy_flat = " ".join(policy.split())
    policy_markers = (
        "Independent project-data backup",
        "Not configured — owner action required",
        "git clean",
        "different storage device",
        "restore into a new empty directory",
        "Timeshift system snapshots",
        "--require-backup-target",
        "Active and verified 2026-07-22",
        "force pushes and branch deletion are blocked",
        "intends to purchase one",
        "accepted temporary operational risk",
        "before Phase 4 document migration work",
    )
    for marker in policy_markers:
        if marker not in policy_flat:
            errors.append("recovery policy marker is missing: " + marker)
    for marker in (
        "## Repository and system safety",
        "Never run `git clean`",
        "tools/repository_safety_audit.py",
        "Timeshift system snapshots do not cover",
    ):
        if marker not in agents:
            errors.append("AGENTS safety marker is missing: " + marker)
    if "repository_safety_audit.py" not in validation:
        errors.append("validation strategy omits the repository safety audit")
    if "RECOVERY_AND_BACKUP.md" not in project_plan:
        errors.append("project plan omits the recovery/data-loss risk control")
    for marker in (
        "/reference/t5_files_556b_06_feb_2025.zip",
        "/benchmark-output/",
        "*.FCBak",
        "Never run `git clean`",
    ):
        if marker not in gitignore:
            errors.append("ignored local-data protection marker is missing: " + marker)

    tree = ast.parse(TOOL_PATH.read_text(encoding="utf-8"), filename=str(TOOL_PATH))
    inspected_git_actions = set()
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_git"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            continue
        inspected_git_actions.add(node.args[1].value)
    dangerous = BANNED_GIT_ACTIONS & inspected_git_actions
    if dangerous:
        errors.append(
            "safety audit contains mutating Git actions: {}".format(
                sorted(dangerous)
            )
        )


def validate():
    errors = []
    _validate_repository_state(errors)
    _validate_backup_assessment(errors)
    _validate_live_audit(errors)
    _validate_static_controls(errors)
    try:
        safety.audit_repository(pathlib.Path.home())
    except safety.SafetyAuditError:
        pass
    else:
        errors.append("safety audit accepted the home directory as a repository root")
    if errors:
        raise AssertionError("\n".join(errors))
    print("Repository recovery and backup controls validation passed")


if __name__ == "__main__":
    validate()
