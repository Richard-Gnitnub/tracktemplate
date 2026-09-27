#!/usr/bin/env python3
"""Report repository, backup, or worktree-retirement readiness read-only."""

import argparse
import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess

SENTINEL = "TRACKTEMPLATE_REPOSITORY_SAFETY="
RETIREMENT_SENTINEL = "TRACKTEMPLATE_WORKTREE_RETIREMENT="
ACCEPTED_MAIN_REF = "refs/remotes/origin/main"
RETIREMENT_CLASSIFICATIONS = (
    "authoritative-local-source",
    "retained-evidence",
    "rebuildable-cache-generated-state",
    "temporary-disposable-state",
    "ambiguous-or-uniquely-owned-state",
)
DISCARD_DISPOSITION = "discard-by-normal-worktree-removal"
PRESERVE_DISPOSITION = "preserve"
FREECAD_CLI_LOCAL_PATH = ".devtools/freecad-cli/"
FREECAD_CLI_LOCAL_TYPE = "freecad-cli-checkout"
FREECAD_CLI_SETUP_PATH = "tools/freecad_bridge/setup-freecad-cli"
FREECAD_CLI_PATCH_PATH = "tools/freecad_bridge/freecad-cli-tracktemplate.patch"
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
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        raise SafetyAuditError("file identity inspection failed") from None
    return digest.hexdigest()


def _git(root, *arguments, allow_failure=False):
    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith("GIT_"):
            del environment[name]
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=False,
            capture_output=True,
            env=environment,
            text=True,
        )
    except UnicodeDecodeError:
        raise SafetyAuditError("read-only Git inspection failed") from None
    if result.returncode and not allow_failure:
        raise SafetyAuditError("read-only Git inspection failed")
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


def _validate_checkout_root(root):
    root = pathlib.Path(root).resolve()
    if root == pathlib.Path(root.anchor) or root == pathlib.Path.home().resolve():
        raise SafetyAuditError("refusing to audit a filesystem or home root")
    top = pathlib.Path(
        _git(root, "rev-parse", "--show-toplevel").stdout.strip()
    ).resolve()
    if top != root:
        raise SafetyAuditError(
            "audit root is not the exact Git top-level checkout"
        )
    return root


def _worktree_records(root):
    """Return registered worktree metadata from Git's NUL-safe format."""
    output = _git(root, "worktree", "list", "--porcelain", "-z").stdout
    records = []
    for raw_record in output.split("\0\0"):
        fields = [field for field in raw_record.split("\0") if field]
        if not fields:
            continue
        if not fields[0].startswith("worktree "):
            raise SafetyAuditError("Git worktree inventory was malformed")
        record = {
            "path": pathlib.Path(fields[0][len("worktree ") :]).resolve(),
            "head": "",
            "branch": "",
            "detached": False,
            "locked": False,
            "prunable": False,
        }
        for field in fields[1:]:
            key, _, value = field.partition(" ")
            if key == "HEAD":
                record["head"] = value
            elif key == "branch":
                record["branch"] = value
            elif key == "detached":
                record["detached"] = True
            elif key == "locked":
                record["locked"] = True
            elif key == "prunable":
                record["prunable"] = True
        records.append(record)
    return records


def _local_state_paths(target):
    """Return ignored and non-ignored local-only paths without content."""
    untracked = {
        item
        for item in _git(
            target,
            "ls-files",
            "-z",
            "--others",
            "--exclude-standard",
        ).stdout.split("\0")
        if item
    }
    ignored = {
        item
        for item in _git(
            target,
            "ls-files",
            "-z",
            "--others",
            "--ignored",
            "--exclude-standard",
        ).stdout.split("\0")
        if item
    }
    overlap = untracked & ignored
    if overlap:
        raise SafetyAuditError("Git local-state inventories overlap")
    return tuple(
        sorted(
            [(path, "untracked") for path in untracked]
            + [(path, "ignored") for path in ignored]
        )
    )


def _validate_relative_path(value, *, directory_prefix=False):
    if not isinstance(value, str) or not value:
        raise SafetyAuditError("retirement selector must be a relative path")
    if directory_prefix:
        if not value.endswith("/"):
            raise SafetyAuditError("retirement prefix must end with slash")
        value = value[:-1]
    candidate = pathlib.PurePosixPath(value)
    if (
        candidate.is_absolute()
        or value in {".", ".."}
        or ".." in candidate.parts
        or candidate.as_posix() != value
    ):
        raise SafetyAuditError("retirement selector is not a safe relative path")
    return value + "/" if directory_prefix else value


def _freecad_cli_tree_identity(checkout):
    """Hash the complete one approved nested checkout without following links."""
    if checkout.is_symlink() or not (checkout / ".git").is_dir():
        raise SafetyAuditError("FreeCAD CLI checkout identity is unsupported")
    if (checkout / ".git").is_symlink():
        raise SafetyAuditError("FreeCAD CLI checkout identity is unsupported")
    records = []
    size_bytes = 0
    pending = [checkout]
    while pending:
        directory = pending.pop()
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name)
        except OSError:
            raise SafetyAuditError("FreeCAD CLI checkout inspection failed") from None
        for child in children:
            try:
                metadata = child.lstat()
            except OSError:
                raise SafetyAuditError(
                    "FreeCAD CLI checkout inspection failed"
                ) from None
            relative = child.relative_to(checkout).as_posix()
            mode = stat.S_IMODE(metadata.st_mode)
            if stat.S_ISDIR(metadata.st_mode):
                records.append((relative, "directory", mode, 0, ""))
                pending.append(child)
            elif stat.S_ISREG(metadata.st_mode):
                records.append(
                    (relative, "file", mode, metadata.st_size, _sha256(child))
                )
                size_bytes += metadata.st_size
            else:
                raise SafetyAuditError(
                    "FreeCAD CLI checkout contains unsupported local state"
                )
    encoded = json.dumps(
        sorted(records), separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), size_bytes


def _local_state_entry(target, relative, git_state):
    nested_checkout = relative == FREECAD_CLI_LOCAL_PATH
    if not nested_checkout:
        relative = _validate_relative_path(relative)
    path = _preserved_entry_path(target, relative.rstrip("/"))
    if path is None:
        raise SafetyAuditError("local-state path has a non-directory parent")
    try:
        metadata = path.lstat()
        if nested_checkout:
            if not stat.S_ISDIR(metadata.st_mode):
                raise SafetyAuditError("FreeCAD CLI checkout is not a directory")
            kind = FREECAD_CLI_LOCAL_TYPE
            identity, size_bytes = _freecad_cli_tree_identity(path)
        elif stat.S_ISREG(metadata.st_mode):
            kind = "file"
            identity = _sha256(path)
            size_bytes = metadata.st_size
        elif stat.S_ISLNK(metadata.st_mode):
            kind = "symlink"
            identity = hashlib.sha256(
                os.fsencode(path.readlink())
            ).hexdigest()
            size_bytes = metadata.st_size
        else:
            kind = "unsupported"
            identity = ""
            size_bytes = metadata.st_size
    except SafetyAuditError:
        raise
    except OSError:
        raise SafetyAuditError("local-state inspection failed") from None
    return {
        "path": relative,
        "git_state": git_state,
        "type": kind,
        "size_bytes": size_bytes,
        "sha256": identity,
    }


def _retirement_inventory(target):
    entries = [
        _local_state_entry(target, relative, git_state)
        for relative, git_state in _local_state_paths(target)
    ]
    encoded = json.dumps(
        entries,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "entries": entries,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "file_count": len(entries),
        "size_bytes": sum(item["size_bytes"] for item in entries),
        "ignored_count": sum(
            item["git_state"] == "ignored" for item in entries
        ),
        "untracked_count": sum(
            item["git_state"] == "untracked" for item in entries
        ),
    }


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SafetyAuditError("retirement plan contains a duplicate key")
        result[key] = value
    return result


def _load_retirement_plan(plan_path, target):
    path = pathlib.Path(plan_path)
    if path.is_symlink():
        raise SafetyAuditError("retirement plan must not be a symbolic link")
    path = path.resolve()
    if target == path or target in path.parents:
        raise SafetyAuditError("retirement plan must stay outside its target")
    if not path.is_file():
        raise SafetyAuditError("retirement plan must be one regular JSON file")
    try:
        plan = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SafetyAuditError("retirement plan is not valid UTF-8 JSON") from error
    if not isinstance(plan, dict):
        raise SafetyAuditError("retirement plan must be one JSON object")
    expected_keys = {
        "schema_version",
        "target",
        "accepted_history",
        "inventory_sha256",
        "activity",
        "authority",
        "classifications",
    }
    if set(plan) != expected_keys or plan.get("schema_version") != 1:
        raise SafetyAuditError("retirement plan schema is unsupported")
    return plan


def _required_text(mapping, key, context):
    if not isinstance(mapping, dict):
        raise SafetyAuditError(context + " must be one JSON object")
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SafetyAuditError(context + " lacks " + key)
    return value.strip()


def _validated_ref(value):
    if value != ACCEPTED_MAIN_REF:
        raise SafetyAuditError("accepted-history ref is not accepted remote main")
    return value


def _validated_sha(value, context):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise SafetyAuditError(context + " must be one complete commit SHA")
    return value


def _group_selectors(group):
    paths = group.get("paths")
    prefixes = group.get("prefixes")
    if not isinstance(paths, list) or not isinstance(prefixes, list):
        raise SafetyAuditError("classification selectors must be JSON arrays")
    selectors = [
        ("path", _validate_relative_path(value)) for value in paths
    ] + [
        ("prefix", _validate_relative_path(value, directory_prefix=True))
        for value in prefixes
    ]
    if not selectors or len(set(selectors)) != len(selectors):
        raise SafetyAuditError(
            "classification selectors must be non-empty and unique"
        )
    return selectors


def _selector_matches(relative, selector):
    kind, value = selector
    if kind == "path":
        return relative == value
    return relative.startswith(value)


def _preserved_entry_path(destination, relative):
    parts = pathlib.PurePosixPath(relative).parts
    parent = destination
    for part in parts[:-1]:
        parent /= part
        try:
            metadata = parent.lstat()
        except OSError:
            return None
        if not stat.S_ISDIR(metadata.st_mode):
            return None
    return parent / parts[-1]


def _freecad_cli_tracked_entries(output, *, index):
    """Parse the complete raw HEAD or stage-zero index of this checkout."""
    if output and not output.endswith("\0"):
        return None
    entries = {}
    pattern = (
        r"(100644|100755) ([0-9a-f]{40}) 0"
        if index else r"(100644|100755) blob ([0-9a-f]{40})"
    )
    for raw in output.split("\0"):
        if not raw:
            continue
        metadata, separator, relative = raw.partition("\t")
        match = re.fullmatch(pattern, metadata)
        if not separator or not match or relative in entries:
            return None
        try:
            _validate_relative_path(relative)
        except SafetyAuditError:
            return None
        entries[relative] = match.groups()
    return entries


def _freecad_cli_canonical_state(root, checkout, accepted_commit):
    """Check this one nested tool against the accepted bridge authority."""
    setup = _git(
        root, "show", accepted_commit + ":" + FREECAD_CLI_SETUP_PATH
    ).stdout
    patch = _git(
        root, "show", accepted_commit + ":" + FREECAD_CLI_PATCH_PATH
    ).stdout
    commits = re.findall(
        r'^expected_commit="([0-9a-f]{40})"$', setup, re.MULTILINE
    )
    headers = re.findall(
        r"^diff --git a/([^\s]+) b/([^\s]+)\n"
        r"index ([0-9a-f]{40})\.\.([0-9a-f]{40}) 100644$",
        patch,
        re.MULTILINE,
    )
    if (
        len(commits) != 1
        or len(headers) != 6
        or any(before != after for before, after, _, _ in headers)
        or [item[0] for item in headers]
        != sorted({item[0] for item in headers})
    ):
        return False
    expected = commits[0]
    if (
        _git(checkout, "rev-parse", "--show-toplevel").stdout.strip()
        != str(checkout)
        or _git(checkout, "rev-parse", "HEAD").stdout.strip() != expected
        or _git(checkout, "rev-parse", "--is-bare-repository").stdout.strip()
        != "false"
        or (checkout / ".git/objects/info/alternates").exists()
    ):
        return False
    head_entries = _freecad_cli_tracked_entries(
        _git(checkout, "ls-tree", "-r", "-z", "HEAD").stdout,
        index=False,
    )
    index_entries = _freecad_cli_tracked_entries(
        _git(checkout, "ls-files", "-s", "-z").stdout,
        index=True,
    )
    if not head_entries or index_entries != head_entries:
        return False
    index_flags = [
        item for item in _git(checkout, "ls-files", "-v", "-z").stdout.split("\0")
        if item
    ]
    if (
        len(index_flags) != len(head_entries)
        or {item[2:] for item in index_flags} != set(head_entries)
        or any(
            len(item) < 3 or item[:2] != "H "
            or item[2:] not in head_entries
            for item in index_flags
        )
    ):
        return False
    approved = {
        path: (before_blob, after_blob)
        for path, _, before_blob, after_blob in headers
    }
    if not set(approved).issubset(head_entries):
        return False
    for path, (mode, before_blob) in head_entries.items():
        file_path = _preserved_entry_path(checkout, path)
        if file_path is None:
            return False
        try:
            metadata = file_path.lstat()
        except OSError:
            return False
        if (
            not stat.S_ISREG(metadata.st_mode)
            or bool(metadata.st_mode & 0o111) != (mode == "100755")
        ):
            return False
        expected_blob = before_blob
        if path in approved:
            approved_before, approved_after = approved[path]
            if mode != "100644" or before_blob != approved_before:
                return False
            expected_blob = approved_after
        if (
            _git(checkout, "hash-object", "--no-filters", "--", path)
            .stdout.strip()
            != expected_blob
        ):
            return False
    if (
        _git(checkout, "ls-files", "--others", "--exclude-standard", "-z").stdout
        or _git(
            checkout, "ls-files", "--others", "--ignored",
            "--exclude-standard", "-z",
        ).stdout
        or _git(checkout, "stash", "list", "--format=%H").stdout
    ):
        return False
    refs = _git(checkout, "show-ref", allow_failure=True)
    if refs.returncode not in {0, 1} or any(
        line.split(" ", 1)[0] != expected
        for line in refs.stdout.splitlines()
    ):
        return False
    unreachable = _git(
        checkout, "fsck", "--no-reflogs", "--unreachable", "--no-progress",
        allow_failure=True,
    )
    return unreachable.returncode == 0 and not unreachable.stdout.strip()


def _preservation_matches(entries, destination_root, target):
    try:
        destination = pathlib.Path(destination_root).resolve()
        home = pathlib.Path.home().resolve()
    except (OSError, RuntimeError, ValueError):
        return False
    if (
        destination == pathlib.Path(destination.anchor)
        or destination == home
        or destination == target
        or target in destination.parents
        or destination in target.parents
        or not destination.is_dir()
    ):
        return False
    for entry in entries:
        path = _preserved_entry_path(destination, entry["path"])
        if path is None:
            return False
        try:
            metadata = path.lstat()
        except OSError:
            return False
        try:
            if entry["type"] == "file" and stat.S_ISREG(metadata.st_mode):
                identity = _sha256(path)
            elif entry["type"] == "symlink" and stat.S_ISLNK(metadata.st_mode):
                identity = hashlib.sha256(
                    os.fsencode(path.readlink())
                ).hexdigest()
                source = _preserved_entry_path(target, entry["path"])
                if source is None:
                    return False
                current = _local_state_entry(
                    target, entry["path"], entry["git_state"]
                )
                if current != entry:
                    return False
                source_referent = source.resolve(strict=True)
                preserved_referent = path.resolve(strict=True)
                if (
                    source_referent != preserved_referent
                    or source_referent == target
                    or target in source_referent.parents
                ):
                    return False
            elif (
                entry["type"] == FREECAD_CLI_LOCAL_TYPE
                and entry["path"] == FREECAD_CLI_LOCAL_PATH
                and stat.S_ISDIR(metadata.st_mode)
            ):
                if destination.stat().st_dev == target.stat().st_dev:
                    return False
                source = _preserved_entry_path(
                    target, FREECAD_CLI_LOCAL_PATH.rstrip("/")
                )
                if source is None or _local_state_entry(
                    target, entry["path"], entry["git_state"]
                ) != entry:
                    return False
                identity, size_bytes = _freecad_cli_tree_identity(path)
                if identity != entry["sha256"] or size_bytes != entry["size_bytes"]:
                    return False
            else:
                return False
        except (OSError, RuntimeError, SafetyAuditError):
            return False
        if (
            (entry["type"] != FREECAD_CLI_LOCAL_TYPE
             and metadata.st_size != entry["size_bytes"])
            or identity != entry["sha256"]
        ):
            return False
    return True


def _classification_state(plan, inventory, target):
    groups = plan.get("classifications")
    if not isinstance(groups, list):
        raise SafetyAuditError("classifications must be one JSON array")
    findings = []
    names = set()
    prepared = []
    for group_index, group in enumerate(groups, start=1):
        if not isinstance(group, dict):
            raise SafetyAuditError("each classification must be one JSON object")
        public_name = f"group-{group_index}"
        expected_keys = {
            "name",
            "classification",
            "paths",
            "prefixes",
            "proof",
            "disposition",
        }
        classification = _required_text(
            group,
            "classification",
            "classification",
        )
        if classification not in RETIREMENT_CLASSIFICATIONS:
            raise SafetyAuditError("retirement classification is unsupported")
        if classification in {
            "authoritative-local-source",
            "retained-evidence",
        }:
            expected_keys.add("preservation")
        if set(group) != expected_keys:
            raise SafetyAuditError("classification schema is unsupported")
        name = _required_text(group, "name", "classification")
        if name in names:
            raise SafetyAuditError("classification names must be unique")
        names.add(name)
        selectors = _group_selectors(group)
        proof = group.get("proof")
        proof_ready = bool(
            isinstance(proof, dict)
            and set(proof) == {"status", "owner", "basis"}
            and proof.get("status") == "passed"
            and isinstance(proof.get("owner"), str)
            and proof["owner"].strip()
            and isinstance(proof.get("basis"), str)
            and proof["basis"].strip()
        )
        if not proof_ready:
            findings.append("classification-proof-incomplete:" + public_name)
        prepared.append(
            {
                "group": group,
                "name": name,
                "public_name": public_name,
                "classification": classification,
                "selectors": selectors,
            }
        )

    assignments = {item["path"]: [] for item in inventory["entries"]}
    selector_hits = {
        (item["name"], selector): 0
        for item in prepared
        for selector in item["selectors"]
    }
    for entry in inventory["entries"]:
        for item in prepared:
            for selector in item["selectors"]:
                if _selector_matches(entry["path"], selector):
                    assignments[entry["path"]].append(item["name"])
                    selector_hits[(item["name"], selector)] += 1
    if any(count == 0 for count in selector_hits.values()):
        findings.append("classification-selector-has-no-inventory-match")
    if any(not names for names in assignments.values()):
        findings.append("local-state-classification-incomplete")
    if any(len(names) > 1 for names in assignments.values()):
        findings.append("local-state-classification-overlap")

    counts = {
        classification: {"file_count": 0, "size_bytes": 0}
        for classification in RETIREMENT_CLASSIFICATIONS
    }
    preservation_ready = True
    for item in prepared:
        entries = [
            entry
            for entry in inventory["entries"]
            if assignments[entry["path"]] == [item["name"]]
        ]
        summary = counts[item["classification"]]
        summary["file_count"] += len(entries)
        summary["size_bytes"] += sum(
            entry["size_bytes"] for entry in entries
        )
        group = item["group"]
        if item["classification"] in {
            "authoritative-local-source",
            "retained-evidence",
        }:
            preservation = group.get("preservation")
            valid_preservation = bool(
                isinstance(preservation, dict)
                and set(preservation) == {"method", "destination_root"}
                and preservation.get("method") == "identical-relative-tree"
                and isinstance(preservation.get("destination_root"), str)
                and preservation["destination_root"].strip()
                and group.get("disposition") == PRESERVE_DISPOSITION
                and _preservation_matches(
                    entries,
                    preservation["destination_root"],
                    target,
                )
            )
            if not valid_preservation:
                preservation_ready = False
                findings.append(
                    "required-preservation-not-proved:" + item["public_name"]
                )
        elif item["classification"] == "ambiguous-or-uniquely-owned-state":
            findings.append(
                "ambiguous-or-unique-local-state:" + item["public_name"]
            )
        elif group.get("disposition") != DISCARD_DISPOSITION:
            findings.append(
                "discard-disposition-not-explicit:" + item["public_name"]
            )

    unsupported = sum(
        entry["type"] not in {"file", "symlink", FREECAD_CLI_LOCAL_TYPE}
        for entry in inventory["entries"]
    )
    if unsupported:
        findings.append("unsupported-local-state-type")
    for entry in inventory["entries"]:
        if entry["type"] != "symlink":
            continue
        assigned = assignments[entry["path"]]
        if len(assigned) != 1:
            continue
        group = next(item for item in prepared if item["name"] == assigned[0])
        if group["classification"] not in {
            "authoritative-local-source", "retained-evidence"
        }:
            findings.append("symlink-preservation-required")
    for entry in inventory["entries"]:
        if entry["type"] != FREECAD_CLI_LOCAL_TYPE:
            continue
        assigned = assignments[entry["path"]]
        if len(assigned) != 1:
            continue
        group = next(item for item in prepared if item["name"] == assigned[0])
        if group["classification"] not in {
            "authoritative-local-source", "retained-evidence"
        }:
            findings.append("freecad-cli-preservation-required")
    return {
        "group_count": len(prepared),
        "counts": counts,
        "complete": not any(
            item in findings
            for item in (
                "classification-selector-has-no-inventory-match",
                "local-state-classification-incomplete",
                "local-state-classification-overlap",
            )
        ),
        "preservation_verified": preservation_ready,
        "unsupported_type_count": unsupported,
        "findings": findings,
    }


def audit_worktree_retirement(root, target, plan_path=None):
    """Return a path-free, read-only worktree-retirement assessment."""
    root = _validate_checkout_root(root)
    target = pathlib.Path(target).resolve()
    if target in {
        pathlib.Path(target.anchor),
        pathlib.Path.home().resolve(),
    }:
        raise SafetyAuditError("refusing to audit a broad retirement target")
    if target == root:
        raise SafetyAuditError("refusing to retire the audit checkout")
    records = [item for item in _worktree_records(root) if item["path"] == target]
    if len(records) != 1 or not target.is_dir():
        raise SafetyAuditError("retirement target is not one registered worktree")
    record = records[0]
    top = pathlib.Path(
        _git(target, "rev-parse", "--show-toplevel").stdout.strip()
    ).resolve()
    if top != target:
        raise SafetyAuditError("retirement target is not its exact Git top level")
    tracked_entries = [
        line
        for line in _git(
            target,
            "status",
            "--porcelain=v1",
            "--untracked-files=no",
        ).stdout.splitlines()
        if line
    ]
    index_flag_records = [
        record
        for record in _git(target, "ls-files", "-v", "-z").stdout.split("\0")
        if record
    ]
    malformed_index_flags = any(
        len(record) < 3 or record[1] != " "
        for record in index_flag_records
    )
    if malformed_index_flags:
        raise SafetyAuditError("Git index-flag inspection was malformed")
    non_default_index_flag_count = sum(
        record[0] == "S" or record[0].islower()
        for record in index_flag_records
    )
    inventory = _retirement_inventory(target)
    findings = []
    if tracked_entries:
        findings.append("target-tracked-state-not-clean")
    if non_default_index_flag_count:
        findings.append("target-index-flags-not-default")
    if record["detached"] == bool(record["branch"]):
        findings.append("target-branch-state-invalid")
    if record["locked"]:
        findings.append("target-worktree-locked")
    if record["prunable"]:
        findings.append("target-worktree-prunable")

    plan = _load_retirement_plan(plan_path, target) if plan_path else None
    classification = {
        "group_count": 0,
        "counts": {
            value: {"file_count": 0, "size_bytes": 0}
            for value in RETIREMENT_CLASSIFICATIONS
        },
        "complete": False,
        "preservation_verified": False,
        "unsupported_type_count": sum(
            item["type"] not in {"file", "symlink", FREECAD_CLI_LOCAL_TYPE}
            for item in inventory["entries"]
        ),
        "findings": ["retirement-plan-missing"],
    }
    identity = {
        "head": record["head"],
        "branch": record["branch"],
        "expected_head_matches": False,
        "expected_branch_matches": False,
        "accepted_ref": "",
        "accepted_commit": "",
        "accepted_commit_matches": False,
        "contained_in_accepted_history": False,
    }
    inventory_matches = False
    activity_confirmed = False
    authority_confirmed = False
    if plan is not None:
        target_plan = plan.get("target")
        if not isinstance(target_plan, dict) or set(target_plan) != {
            "branch",
            "head",
        }:
            raise SafetyAuditError("retirement target identity is malformed")
        expected_branch = target_plan["branch"]
        if expected_branch is not None:
            if (
                not isinstance(expected_branch, str)
                or not expected_branch.startswith("refs/heads/")
            ):
                raise SafetyAuditError(
                    "retirement target branch must be a local ref or null"
                )
        expected_head = _validated_sha(
            target_plan.get("head"),
            "retirement target head",
        )
        identity["expected_head_matches"] = record["head"] == expected_head
        identity["expected_branch_matches"] = (
            record["detached"] and not record["branch"]
            if expected_branch is None
            else not record["detached"] and record["branch"] == expected_branch
        )
        if not identity["expected_head_matches"]:
            findings.append("target-head-changed")
        if not identity["expected_branch_matches"]:
            findings.append("target-branch-changed")

        accepted = plan.get("accepted_history")
        if not isinstance(accepted, dict) or set(accepted) != {"ref", "commit"}:
            raise SafetyAuditError("accepted-history identity is malformed")
        accepted_ref = _validated_ref(
            _required_text(accepted, "ref", "accepted history")
        )
        expected_accepted = _validated_sha(
            accepted.get("commit"),
            "accepted-history commit",
        )
        accepted_result = _git(
            root,
            "rev-parse",
            "--verify",
            accepted_ref,
            allow_failure=True,
        )
        actual_accepted = (
            accepted_result.stdout.strip()
            if accepted_result.returncode == 0
            else ""
        )
        identity["accepted_ref"] = accepted_ref
        identity["accepted_commit"] = actual_accepted
        identity["accepted_commit_matches"] = (
            actual_accepted == expected_accepted
        )
        if not identity["accepted_commit_matches"]:
            findings.append("accepted-history-identity-changed")
        if actual_accepted:
            containment = _git(
                root,
                "merge-base",
                "--is-ancestor",
                record["head"],
                actual_accepted,
                allow_failure=True,
            )
            if containment.returncode not in {0, 1}:
                raise SafetyAuditError("accepted-history containment check failed")
            identity["contained_in_accepted_history"] = (
                containment.returncode == 0
            )
        if not identity["contained_in_accepted_history"]:
            findings.append("target-not-contained-in-accepted-history")

        inventory_matches = plan.get("inventory_sha256") == inventory["sha256"]
        if not inventory_matches:
            findings.append("local-state-inventory-changed")
        classification = _classification_state(plan, inventory, target)
        findings.extend(classification["findings"])
        nested_entries = [
            item for item in inventory["entries"]
            if item["type"] == FREECAD_CLI_LOCAL_TYPE
        ]
        if nested_entries:
            checkout = target / FREECAD_CLI_LOCAL_PATH.rstrip("/")
            if (
                not identity["accepted_commit_matches"]
                or not _freecad_cli_canonical_state(
                    root, checkout, actual_accepted
                )
                or _retirement_inventory(target)["sha256"]
                != inventory["sha256"]
            ):
                findings.append("freecad-cli-identity-not-proved")

        activity = plan.get("activity")
        activity_confirmed = bool(
            isinstance(activity, dict)
            and set(activity) == {"status", "evidence"}
            and activity.get("status") == "inactive"
            and isinstance(activity.get("evidence"), str)
            and activity["evidence"].strip()
        )
        if not activity_confirmed:
            findings.append("target-inactivity-not-confirmed")
        authority = plan.get("authority")
        authority_confirmed = bool(
            isinstance(authority, dict)
            and set(authority) == {"status", "owner", "scope"}
            and authority.get("status") == "authorised"
            and isinstance(authority.get("owner"), str)
            and authority["owner"].strip()
            and isinstance(authority.get("scope"), str)
            and authority["scope"].strip()
        )
        if not authority_confirmed:
            findings.append("retirement-authority-not-recorded")
    else:
        findings.append("retirement-plan-missing")

    ready = not findings
    return {
        "schema_version": 1,
        "report_kind": "worktree-retirement",
        "target": {
            **identity,
            "registered": True,
            "detached": record["detached"],
            "tracked_clean": (
                not tracked_entries and not non_default_index_flag_count
            ),
            "tracked_entry_count": len(tracked_entries),
            "non_default_index_flag_count": non_default_index_flag_count,
            "locked": record["locked"],
            "prunable": record["prunable"],
        },
        "inventory": {
            key: inventory[key]
            for key in (
                "sha256",
                "file_count",
                "size_bytes",
                "ignored_count",
                "untracked_count",
            )
        }
        | {"plan_identity_matches": inventory_matches},
        "classification": {
            key: classification[key]
            for key in (
                "group_count",
                "counts",
                "complete",
                "preservation_verified",
                "unsupported_type_count",
            )
        },
        "activity_confirmed": activity_confirmed,
        "authority_confirmed": authority_confirmed,
        "readiness": {"retirement_ready": ready},
        "findings": sorted(set(findings)),
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
    parser.add_argument(
        "--retirement-worktree",
        type=pathlib.Path,
        default=None,
        help="Exact registered worktree to inspect without removal.",
    )
    parser.add_argument(
        "--retirement-plan",
        type=pathlib.Path,
        default=None,
        help="Local JSON classification plan; its path is never printed.",
    )
    parser.add_argument("--require-retirement-ready", action="store_true")
    arguments = parser.parse_args(argv)

    retirement_mode = arguments.retirement_worktree is not None
    if arguments.retirement_plan is not None and not retirement_mode:
        parser.error("--retirement-plan requires --retirement-worktree")
    if arguments.require_retirement_ready and arguments.retirement_plan is None:
        parser.error(
            "--require-retirement-ready requires --retirement-plan and "
            "--retirement-worktree"
        )
    repository_requirements = any(
        (
            arguments.require_checkpoint,
            arguments.require_critical_assets,
            arguments.require_backup_target,
            arguments.backup_target is not None,
        )
    )
    if retirement_mode and repository_requirements:
        parser.error(
            "worktree-retirement inspection is separate from repository and "
            "backup requirements"
        )
    if retirement_mode:
        try:
            report = audit_worktree_retirement(
                arguments.root,
                arguments.retirement_worktree,
                arguments.retirement_plan,
            )
        except (OSError, SafetyAuditError):
            report = {
                "schema_version": 1,
                "report_kind": "worktree-retirement",
                "readiness": {"retirement_ready": False},
                "findings": ["retirement-audit-error"],
                "requested_requirements": {"retirement_ready": False},
            }
            print(
                RETIREMENT_SENTINEL
                + json.dumps(report, sort_keys=True, separators=(",", ":")),
                flush=True,
            )
            return 1
        requirement = bool(
            not arguments.require_retirement_ready
            or report["readiness"]["retirement_ready"]
        )
        report["requested_requirements"] = {
            "retirement_ready": requirement
        }
        print(
            RETIREMENT_SENTINEL
            + json.dumps(report, sort_keys=True, separators=(",", ":")),
            flush=True,
        )
        return int(not requirement)

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
