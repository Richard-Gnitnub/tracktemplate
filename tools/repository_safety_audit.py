#!/usr/bin/env python3
"""Report repository checkpoint and local-backup readiness without mutation."""

import argparse
import hashlib
import json
import os
import pathlib
import subprocess


SENTINEL = "TRACKTEMPLATE_REPOSITORY_SAFETY="
SOURCE_ARCHIVE_PATH = pathlib.Path(
    "reference/t5_files_556b_06_feb_2025.zip"
)
SOURCE_ARCHIVE_SHA256 = (
    "2faddc9c1bc0ab3a60553f8a9ab14b9e04d7a14608f3404259cbf262f7309cf3"
)
LOCAL_ASSETS = (
    {
        "path": SOURCE_ARCHIVE_PATH,
        "kind": "source-evidence",
        "required": True,
        "expected_sha256": SOURCE_ARCHIVE_SHA256,
    },
    {
        "path": pathlib.Path("benchmark-output"),
        "kind": "raw-development-evidence",
        "required": False,
        "expected_sha256": "",
    },
    {
        "path": pathlib.Path("exports"),
        "kind": "generated-production-output",
        "required": False,
        "expected_sha256": "",
    },
    {
        "path": pathlib.Path("output"),
        "kind": "generated-production-output",
        "required": False,
        "expected_sha256": "",
    },
)


class SafetyAuditError(RuntimeError):
    """Raised when the requested location is not the intended Git checkout."""


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(root, *arguments, allow_failure=False):
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode and not allow_failure:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise SafetyAuditError(
            "read-only Git inspection failed for {}: {}".format(
                " ".join(arguments),
                detail,
            )
        )
    return result


def _repository_state(root):
    top = pathlib.Path(
        _git(root, "rev-parse", "--show-toplevel").stdout.strip()
    ).resolve()
    if top != root:
        raise SafetyAuditError(
            "audit root is not the exact Git top-level checkout"
        )

    status_lines = [
        line
        for line in _git(
            root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ).stdout.splitlines()
        if line
    ]
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    head = _git(root, "rev-parse", "HEAD").stdout.strip()
    upstream_result = _git(
        root,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        allow_failure=True,
    )
    upstream = (
        upstream_result.stdout.strip() if upstream_result.returncode == 0 else ""
    )
    ahead = None
    behind = None
    remote = ""
    remote_url = ""
    if upstream:
        counts = _git(
            root,
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...@{upstream}",
        ).stdout.split()
        if len(counts) != 2:
            raise SafetyAuditError("Git ahead/behind inspection was malformed")
        ahead, behind = (int(counts[0]), int(counts[1]))
        remote = upstream.split("/", 1)[0]
        remote_url = _git(root, "remote", "get-url", remote).stdout.strip()

    checkpoint_ready = bool(
        not status_lines
        and branch
        and branch != "HEAD"
        and upstream
        and ahead == 0
        and behind == 0
    )
    return {
        "branch": branch,
        "head": head,
        "upstream": upstream,
        "remote": remote,
        "remote_url": remote_url,
        "working_tree_clean": not status_lines,
        "working_tree_entry_count": len(status_lines),
        "ahead": ahead,
        "behind": behind,
        "checkpoint_ready": checkpoint_ready,
    }


def _directory_inventory(path):
    file_count = 0
    size_bytes = 0
    for candidate in path.rglob("*"):
        if candidate.is_symlink() or not candidate.is_file():
            continue
        file_count += 1
        size_bytes += candidate.stat().st_size
    return file_count, size_bytes


def _asset_record(root, specification):
    relative = specification["path"]
    path = (root / relative).resolve()
    if root != path and root not in path.parents:
        raise SafetyAuditError("local asset escaped the repository root")
    record = {
        "path": relative.as_posix(),
        "kind": specification["kind"],
        "required": specification["required"],
        "present": path.exists(),
        "type": "missing",
        "file_count": 0,
        "size_bytes": 0,
        "sha256": "",
        "expected_sha256": specification["expected_sha256"],
        "hash_matches": None,
    }
    if not path.exists():
        return record
    if path.is_file():
        record["type"] = "file"
        record["file_count"] = 1
        record["size_bytes"] = path.stat().st_size
        if specification["expected_sha256"]:
            record["sha256"] = _sha256(path)
            record["hash_matches"] = (
                record["sha256"] == specification["expected_sha256"]
            )
    elif path.is_dir():
        record["type"] = "directory"
        record["file_count"], record["size_bytes"] = _directory_inventory(path)
    else:
        record["type"] = "unsupported"
    return record


def evaluate_backup_location(
    *,
    configured,
    exists,
    is_directory,
    inside_repository,
    repository_device,
    target_device,
    writable,
):
    """Return a path-free assessment; this does not claim backup completion."""
    different_device = (
        configured
        and exists
        and repository_device is not None
        and target_device is not None
        and repository_device != target_device
    )
    ready = bool(
        configured
        and exists
        and is_directory
        and not inside_repository
        and different_device
        and writable
    )
    if not configured:
        reason = "not-configured"
    elif not exists:
        reason = "target-does-not-exist"
    elif not is_directory:
        reason = "target-is-not-a-directory"
    elif inside_repository:
        reason = "target-is-inside-repository"
    elif not different_device:
        reason = "target-is-on-the-same-filesystem"
    elif not writable:
        reason = "target-is-not-writable"
    else:
        reason = "location-ready-backup-not-proven"
    return {
        "configured": bool(configured),
        "exists": bool(exists),
        "is_directory": bool(is_directory),
        "inside_repository": bool(inside_repository),
        "different_device": bool(different_device),
        "writable": bool(writable),
        "location_ready": ready,
        "reason": reason,
        "backup_completed": False,
        "restore_tested": False,
    }


def _backup_target_state(root, target):
    if target is None:
        return evaluate_backup_location(
            configured=False,
            exists=False,
            is_directory=False,
            inside_repository=False,
            repository_device=root.stat().st_dev,
            target_device=None,
            writable=False,
        )
    target = pathlib.Path(target).expanduser().resolve()
    exists = target.exists()
    is_directory = exists and target.is_dir()
    inside_repository = target == root or root in target.parents
    target_device = target.stat().st_dev if exists else None
    writable = bool(is_directory and os.access(target, os.W_OK | os.X_OK))
    return evaluate_backup_location(
        configured=True,
        exists=exists,
        is_directory=is_directory,
        inside_repository=inside_repository,
        repository_device=root.stat().st_dev,
        target_device=target_device,
        writable=writable,
    )


def audit_repository(root, backup_target=None):
    """Return a non-sensitive, JSON-compatible, read-only safety report."""
    root = pathlib.Path(root).resolve()
    if root == pathlib.Path(root.anchor) or root == pathlib.Path.home().resolve():
        raise SafetyAuditError("refusing to audit a filesystem or home root")
    repository = _repository_state(root)
    assets = [_asset_record(root, item) for item in LOCAL_ASSETS]
    critical_assets_ready = all(
        item["present"]
        and item["type"] == "file"
        and item["hash_matches"] is not False
        for item in assets
        if item["required"]
    )
    backup = _backup_target_state(root, backup_target)

    findings = []
    if not repository["working_tree_clean"]:
        findings.append("working-tree-not-clean")
    if not repository["upstream"]:
        findings.append("upstream-not-configured")
    elif repository["ahead"] or repository["behind"]:
        findings.append("local-and-upstream-not-synchronised")
    for asset in assets:
        if asset["required"] and not asset["present"]:
            findings.append("required-local-asset-missing:" + asset["path"])
        if asset["hash_matches"] is False:
            findings.append("required-local-asset-hash-mismatch:" + asset["path"])
    if not backup["location_ready"]:
        findings.append("backup-target:" + backup["reason"])

    return {
        "schema_version": 1,
        "repository_root": ".",
        "repository": repository,
        "local_assets": assets,
        "backup_target": backup,
        "readiness": {
            "checkpoint_ready": repository["checkpoint_ready"],
            "critical_assets_ready": critical_assets_ready,
            "backup_target_location_ready": backup["location_ready"],
            "backup_completed": False,
            "restore_tested": False,
        },
        "findings": findings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parents[1],
    )
    parser.add_argument(
        "--backup-target",
        type=pathlib.Path,
        default=None,
        help="Mounted candidate destination; its path is never printed.",
    )
    parser.add_argument("--require-checkpoint", action="store_true")
    parser.add_argument("--require-critical-assets", action="store_true")
    parser.add_argument("--require-backup-target", action="store_true")
    arguments = parser.parse_args(argv)

    report = audit_repository(arguments.root, arguments.backup_target)
    requirements = {
        "checkpoint": (
            not arguments.require_checkpoint
            or report["readiness"]["checkpoint_ready"]
        ),
        "critical_assets": (
            not arguments.require_critical_assets
            or report["readiness"]["critical_assets_ready"]
        ),
        "backup_target": (
            not arguments.require_backup_target
            or report["readiness"]["backup_target_location_ready"]
        ),
    }
    report["requested_requirements"] = requirements
    print(
        SENTINEL + json.dumps(report, sort_keys=True, separators=(",", ":")),
        flush=True,
    )
    return int(not all(requirements.values()))


if __name__ == "__main__":
    raise SystemExit(main())
