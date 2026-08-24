#!/usr/bin/env python3
"""Validate deterministic recovery controls and optional workstation evidence."""

import argparse
import ast
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import repository_safety_audit as safety  # noqa: E402


POLICY_PATH = ROOT / "reference" / "RECOVERY_AND_BACKUP.md"
VALIDATION_PATH = ROOT / "reference" / "VALIDATION.md"
PROJECT_PLAN_PATH = ROOT / "reference" / "PROJECT_PLAN.md"
WORKFLOWS_PATH = ROOT / "reference" / "AGENT_WORKFLOWS.md"
LEARNING_PATH = ROOT / "reference" / "LEARNING_FROM_EXPERIENCE.md"
PHASE_EVIDENCE_PATH = ROOT / "reference/current/PHASE_EVIDENCE.md"
AGENTS_PATH = ROOT / "AGENTS.md"
GITIGNORE_PATH = ROOT / ".gitignore"
TOOL_PATH = ROOT / "tools" / "repository_safety_audit.py"
RECOVERY_SKILL_PATHS = {
    "context": ROOT / ".agents/skills/tracktemplate-context-recovery/SKILL.md",
    "handoff": ROOT / ".agents/skills/tracktemplate-handoff/SKILL.md",
    "ide": ROOT / ".agents/skills/tracktemplate-ide-workspace-alignment/SKILL.md",
    "quality": ROOT / ".agents/skills/tracktemplate-quality-review/SKILL.md",
    "validation": ROOT / ".agents/skills/tracktemplate-change-validation/SKILL.md",
}
LFE_001_TO_019_ROWS_SHA256 = (
    "ad7277d073439979470951990f0e02ad75de65cdaf81b5e4e5320e2e7aaa5f28"
)
READ_ONLY_GIT_ACTIONS = {"rev-list", "rev-parse", "status"}
READ_ONLY_GIT_SUBCOMMANDS = {
    "remote": {"get-url"},
}


def _validate_git_wrapper_shape(wrapper):
    """Bind the safety audit wrapper to one literal read-only Git prefix."""
    calls = [
        node
        for node in ast.walk(wrapper)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
    ]
    if len(calls) != 1:
        raise AssertionError("Git wrapper execution count drifted")
    command = calls[0].args[0] if calls[0].args else None
    valid = (
        isinstance(command, ast.List)
        and len(command.elts) == 4
        and isinstance(command.elts[0], ast.Constant)
        and command.elts[0].value == "git"
        and isinstance(command.elts[1], ast.Constant)
        and command.elts[1].value == "-C"
        and isinstance(command.elts[2], ast.Call)
        and isinstance(command.elts[2].func, ast.Name)
        and command.elts[2].func.id == "str"
        and len(command.elts[2].args) == 1
        and isinstance(command.elts[2].args[0], ast.Name)
        and command.elts[2].args[0].id == "root"
        and isinstance(command.elts[3], ast.Starred)
        and isinstance(command.elts[3].value, ast.Name)
        and command.elts[3].value.id == "arguments"
    )
    if not valid:
        raise AssertionError("Git wrapper command prefix drifted")


def _semantic_text(value):
    value = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", value)
    value = re.sub(r"[`*_>#|,:;.()/-]", " ", value)
    return " ".join(value.casefold().split())


def validate_safety_audit_git_commands(source):
    """Permit only read-only Git and stash inspection in the safety audit."""
    tree = ast.parse(source)
    wrappers = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_git"
    ]
    if len(wrappers) > 1:
        raise AssertionError("safety audit defines more than one Git wrapper")
    if wrappers:
        _validate_git_wrapper_shape(wrappers[0])
    wrapper_nodes = set(ast.walk(wrappers[0])) if wrappers else set()

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module in {"os", "subprocess"}
        ):
            raise AssertionError("safety audit aliases process-capable modules")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in {"os", "subprocess"} and alias.asname:
                    raise AssertionError(
                        "safety audit aliases process-capable modules"
                    )
        if (
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and isinstance(node.value, ast.Name)
            and node.value.id in {"os", "subprocess"}
        ):
            raise AssertionError("safety audit aliases process-capable modules")
        if (
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and isinstance(node.value, ast.Attribute)
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id in {"os", "subprocess"}
        ):
            raise AssertionError("safety audit aliases process-capable modules")
        if (
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and isinstance(node.value, ast.Name)
            and node.value.id == "_git"
        ):
            raise AssertionError("safety audit aliases the Git wrapper")
        if not isinstance(node, ast.Call):
            continue

        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
        ):
            if node not in wrapper_nodes or node.func.attr != "run":
                raise AssertionError("safety audit bypasses the Git wrapper")
            if not (
                node.args
                and isinstance(node.args[0], ast.List)
                and node.args[0].elts
                and isinstance(node.args[0].elts[0], ast.Constant)
                and node.args[0].elts[0].value == "git"
            ):
                raise AssertionError("Git wrapper command is not literal Git")
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "os"
            and node.func.attr != "access"
        ):
            raise AssertionError("safety audit bypasses the Git wrapper")

        if not (
            isinstance(node.func, ast.Name) and node.func.id == "_git"
        ):
            continue
        if not (
            len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            raise AssertionError(
                "safety audit contains an uninspectable Git action"
            )
        action = node.args[1].value
        if action in READ_ONLY_GIT_ACTIONS:
            continue
        if action == "stash":
            exact_inventory = (
                len(node.args) == 4
                and isinstance(node.args[2], ast.Constant)
                and node.args[2].value == "list"
                and isinstance(node.args[3], ast.Constant)
                and node.args[3].value == "--format=%H"
            )
            if exact_inventory:
                continue
            inspection_subcommand = (
                len(node.args) >= 3
                and isinstance(node.args[2], ast.Constant)
                and node.args[2].value in {"list", "show"}
            )
            if inspection_subcommand:
                raise AssertionError(
                    "safety audit contains a non-private stash command"
                )
            raise AssertionError(
                "safety audit contains a non-read-only Git command"
            )
        subcommands = READ_ONLY_GIT_SUBCOMMANDS.get(action)
        if not (
            subcommands
            and len(node.args) >= 3
            and isinstance(node.args[2], ast.Constant)
            and node.args[2].value in subcommands
        ):
            raise AssertionError(
                "safety audit contains a non-read-only Git command"
            )

def _stash_tree(repository, revision):
    """Return one exact tree identity from a disposable stash fixture."""
    return _run(
        ["git", "rev-parse", revision + "^{tree}"],
        cwd=repository,
    ).stdout.strip()


def _make_stash_fixture(temp_root, option):
    """Create a disposable stash with tracked, untracked, and ignored data."""
    repository = temp_root / "repository"
    repository.mkdir()
    _run(["git", "init", "-b", "main"], cwd=repository)
    _run(["git", "config", "user.name", "Stash Fixture"], cwd=repository)
    _run(
        ["git", "config", "user.email", "stash-fixture@example.invalid"],
        cwd=repository,
    )
    _run(["git", "config", "core.filemode", "true"], cwd=repository)
    (repository / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    (repository / "deleted.txt").write_text("delete me\n", encoding="utf-8")
    (repository / "index.txt").write_text("base index\n", encoding="utf-8")
    (repository / "mode.txt").write_text("mode\n", encoding="utf-8")
    (repository / "partial.txt").write_text("base partial\n", encoding="utf-8")
    (repository / "tracked.txt").write_text("base\n", encoding="utf-8")
    _run(["git", "add", "."], cwd=repository)
    _run(["git", "commit", "-m", "Initial state"], cwd=repository)

    (repository / "index.txt").write_text("staged index\n", encoding="utf-8")
    (repository / "partial.txt").write_text("staged partial\n", encoding="utf-8")
    _run(["git", "add", "index.txt", "partial.txt"], cwd=repository)
    (repository / "partial.txt").write_text("worktree partial\n", encoding="utf-8")
    (repository / "deleted.txt").unlink()
    (repository / "mode.txt").chmod(0o755)
    (repository / "tracked.txt").write_text("changed\n", encoding="utf-8")
    (repository / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    (repository / "ignored.txt").write_text("ignored\n", encoding="utf-8")
    arguments = ["git", "stash", "push", "-m", "topology fixture"]
    if option:
        arguments.insert(3, option)
    _run(arguments, cwd=repository)
    return repository


def _validate_stash_topology(errors):
    """Prove B/I/W/U topology and tracked-delta recovery in real Git."""
    for option, expected_parent_count in (("", 2), ("-u", 3), ("-a", 3)):
        with tempfile.TemporaryDirectory(
            prefix="tracktemplate-stash-topology-"
        ) as temporary:
            repository = _make_stash_fixture(
                pathlib.Path(temporary), option
            )
            stash = _run(
                ["git", "rev-parse", "refs/stash"], cwd=repository
            ).stdout.strip()
            parents = _run(
                ["git", "rev-list", "--parents", "-n", "1", stash],
                cwd=repository,
            ).stdout.split()
            if len(parents) - 1 != expected_parent_count:
                errors.append(
                    "stash parent topology drifted for "
                    + (option or "default")
                )
                continue
            base_tree = _stash_tree(repository, stash + "^1")
            index_tree = _stash_tree(repository, stash + "^2")
            worktree_tree = _stash_tree(repository, stash)
            if len({base_tree, index_tree, worktree_tree}) != 3:
                errors.append(
                    "stash B/I/W topology drifted for "
                    + (option or "default")
                )
            index_differences = set(
                _run(
                    [
                        "git",
                        "diff",
                        "--name-status",
                        stash + "^1",
                        stash + "^2",
                    ],
                    cwd=repository,
                ).stdout.splitlines()
            )
            if index_differences != {"M\tindex.txt", "M\tpartial.txt"}:
                errors.append(
                    "stash B-to-I delta drifted for "
                    + (option or "default")
                )
            worktree_differences = set(
                _run(
                    [
                        "git",
                        "diff",
                        "--name-status",
                        stash + "^2",
                        stash,
                    ],
                    cwd=repository,
                ).stdout.splitlines()
            )
            expected_worktree_differences = {
                "D\tdeleted.txt",
                "M\tmode.txt",
                "M\tpartial.txt",
                "M\ttracked.txt",
            }
            if worktree_differences != expected_worktree_differences:
                errors.append(
                    "stash I-to-W delta drifted for "
                    + (option or "default")
                )
            differences = _run(
                ["git", "diff", "--name-status", stash + "^1", stash],
                cwd=repository,
            ).stdout.splitlines()
            if "D\tdeleted.txt" not in differences:
                errors.append("stash reconciliation lost a tracked deletion")
            summary = _run(
                ["git", "diff", "--summary", stash + "^1", stash],
                cwd=repository,
            ).stdout
            if "mode change 100644 => 100755 mode.txt" not in summary:
                errors.append("stash reconciliation lost a file-mode change")
            expected_contents = {
                (stash + "^1", "index.txt"): "base index\n",
                (stash + "^2", "index.txt"): "staged index\n",
                (stash, "index.txt"): "staged index\n",
                (stash + "^1", "partial.txt"): "base partial\n",
                (stash + "^2", "partial.txt"): "staged partial\n",
                (stash, "partial.txt"): "worktree partial\n",
            }
            for (revision, path), expected in expected_contents.items():
                actual = _run(
                    ["git", "show", revision + ":" + path],
                    cwd=repository,
                ).stdout
                if actual != expected:
                    errors.append(
                        "stash B/I/W blob drifted for "
                        + (option or "default")
                        + ":"
                        + path
                    )
            if expected_parent_count == 2:
                continue
            u_paths = set(
                _run(
                    ["git", "ls-tree", "-r", "--name-only", stash + "^3"],
                    cwd=repository,
                ).stdout.splitlines()
            )
            expected_paths = {"untracked.txt"}
            if option == "-a":
                expected_paths.add("ignored.txt")
            if u_paths != expected_paths:
                errors.append("stash U-tree contents drifted for " + option)
            for path in expected_paths:
                actual = _run(
                    ["git", "show", stash + "^3:" + path],
                    cwd=repository,
                ).stdout
                if actual != path.removesuffix(".txt") + "\n":
                    errors.append(
                        "stash U-tree blob drifted for " + option + ":" + path
                    )


def _section(text, heading):
    match = re.search(
        r"^## " + re.escape(heading) + r"\s*$\n(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("recovery policy section is missing: " + heading)
    return match.group(1)


def validate_visible_recovery_policy(policy):
    """Keep the visible-state and emergency-stash meanings canonical."""
    section = _semantic_text(_section(policy, "Visible recovery state"))
    fragments = (
        "must not use git stash for planned preservation recovery or handoff",
        "usual unfinished work on a feature branch and its worktree",
        "interrupted work on a recovery branch",
        "recovery worktree when it is available",
        "recovery commit that keeps the recovery state",
        "for local evidence use a checksum manifest",
        "checksum manifest",
        "independent preservation method with project authority",
        "do not stage sensitive evidence or local evidence",
        "do not commit sensitive evidence or local evidence",
        "do not push sensitive evidence or local evidence",
        "keep a checksum manifest with sensitive paths local",
        "use git stash only in an emergency to keep work available",
        "temporary unresolved recovery state",
        "do not use it for planned preservation or handoff",
        "stash@{n} selector and full stash commit sha",
        "do not put sensitive evidence or local evidence in a stash",
        "when they can put such evidence in git",
        "use approved independent preservation directly",
        "stash contains such evidence do not stage that evidence",
        "do not commit that evidence",
        "do not push that evidence",
        "preserve it only with the approved independent method",
        "stash disposition removes the stash from the inventory",
        "it does not remove its git commits trees or blobs",
        "git can keep those objects when the stash inventory is empty",
        "procedure does not control git object removal",
        "do not remove git objects automatically",
        "stash contains sensitive evidence or local evidence keep the recovery "
        "gate open",
        "stop this procedure",
        "get project owner direction before more git work",
        "use $tracktemplate security review before more git work",
        "inventory the stash topology",
        "base commit sha and base tree",
        "index parent commit sha and index tree",
        "worktree tree",
        "optional untracked files parent commit sha and u tree",
        "u tree contains each untracked file",
        "same u tree also contains each ignored file",
        "git keeps those files only in u",
        "stash has unique content that git can contain preserve it on a "
        "recovery branch or recovery worktree",
        "make a recovery commit",
        "compare the base tree with the index tree and worktree tree",
        "review each path file mode difference and deletion",
        "unique content is sensitive evidence or local evidence do not put it "
        "in a recovery commit",
        "compare each path and blob for that evidence with approved independent "
        "preservation",
        "preserve it only with that method",
        "compare each other path and blob in the u tree with the named git state "
        "or approved independent preservation",
        "stash has no unique content validate each stash tree difference",
        "validate each path in the u tree",
        "get the applicable authority for the stash that the stash commit sha "
        "identifies",
        "stash selector identifies the same stash commit sha and component inventory",
        "complete only that stash disposition",
        "record the preservation diff",
        "do not use drop clear overwrite pop rewrite git stash branch or "
        "other operation that removes a stash without a report and "
        "applicable authority",
        "tool must not remove a stash only to get empty git stash list output",
        "examine the output of git stash list",
        "project owner recovery purpose stash selector and full stash commit sha",
        "record the b i w u inventory for each retained stash",
        "compare the base tree with the index tree and worktree tree",
        "review each path blob deletion and file mode",
        "review each path and blob in the u tree",
        "preserve unique content that git can contain in named git state",
        "preserve sensitive evidence and local evidence only with approved "
        "independent preservation",
        "before the disposition make sure that the stash selector stash commit "
        "sha and component inventory did not change",
        "a retained stash is unresolved recovery state",
        "stash ownership recovery purpose component inventory unique content "
        "or stash disposition is missing or changed fail closed",
        "completed recovery cycle has no retained stash and no unresolved "
        "finding about sensitive evidence or local evidence",
        "recovery commit is not product acceptance evidence acceptance or "
        "merge authority",
    )
    for fragment in fragments:
        if fragment not in section:
            raise AssertionError("visible recovery policy lacks: " + fragment)


def validate_visible_recovery_routing(workflows, skills):
    """Require concise application of the canonical owner across workflows."""
    workflow = _semantic_text(workflows)
    workflow_fragments = (
        "visible recovery state procedure",
        "context packet gives the route to named git state",
        "it is not planned preservation",
        "keep the recovery gate open",
        "recovery workflow completes stash reconciliation",
        "inventory named branches worktrees commits and every stash",
        "preserve unique content and obtain authority for exact disposition",
        "close the recovery gate only after ownership purpose preservation and "
        "disposition are proved and no stash stays in the inventory",
    )
    for fragment in workflow_fragments:
        if fragment not in workflow:
            raise AssertionError("agent workflow recovery routing lacks: " + fragment)
    if "RECOVERY_AND_BACKUP.md#visible-recovery-state" not in workflows:
        raise AssertionError("agent workflow does not route to recovery policy")

    required = {
        "context": (
            "branches worktrees and commits in named git state for unfinished "
            "work or interrupted work",
            "examine the complete stash inventory",
            "if the inventory has a retained stash",
            "keep the recovery gate open",
        ),
        "handoff": (
            "context packet is not planned preservation",
            "complete stash inventory",
            "use named git state when applicable authority is available",
        ),
        "ide": (
            "complete stash inventory",
            "map interrupted work to its recovery branch recovery worktree "
            "and recovery commit",
            "stop for a retained stash",
            "not accepted product state",
            "do not end workspace alignment while an emergency stash stays "
            "in the stash inventory",
        ),
        "validation": (
            "stash inventory unique content and stash disposition controls",
            "semantic control validation and preservation diff",
        ),
        "quality": (
            "complete stash inventory and unique content",
            "validate exact git identity and stash disposition authority",
            "review the preservation diff",
            "not accepted product state",
        ),
    }
    for name, fragments in required.items():
        text = skills[name]
        semantic = _semantic_text(text)
        if "RECOVERY_AND_BACKUP.md#visible-recovery-state" not in text:
            raise AssertionError(name + " skill bypasses the recovery owner")
        for fragment in fragments:
            if fragment not in semantic:
                raise AssertionError(name + " recovery routing lacks: " + fragment)


def validate_recovery_policy_owner(markdown):
    """Reject a second Git recovery-policy owner or copied core rule."""
    canonical = "reference/RECOVERY_AND_BACKUP.md"
    if canonical not in markdown:
        raise AssertionError("canonical recovery owner is missing")
    core_rule = "must not use git stash for planned preservation recovery or handoff"
    for path, text in markdown.items():
        if path == canonical:
            continue
        semantic = _semantic_text(text)
        if core_rule in semantic:
            raise AssertionError(
                "recovery policy was duplicated outside its owner: " + path
            )
        for heading in re.findall(r"^#{1,6}\s+(.+)$", text, re.MULTILINE):
            value = _semantic_text(heading)
            hidden_state = "git" in value or "stash" in value
            owner_claim = any(
                marker in value
                for marker in ("policy owner", "canonical policy", "owns policy")
            )
            if hidden_state and owner_claim:
                raise AssertionError("competing recovery policy owner: " + path)


def _lfe_rows(text):
    return [
        line for line in text.splitlines(keepends=True) if line.startswith("| LFE-")
    ]


def validate_recovery_lfe(text):
    """Protect the append-only visible-recovery lesson and its owner links."""
    rows = _lfe_rows(text)
    identifiers = [re.match(r"\| (LFE-\d{3})", row).group(1) for row in rows]
    expected = ["LFE-{:03d}".format(number) for number in range(1, 21)]
    if identifiers != expected:
        raise AssertionError("LFE identifiers are not unique through LFE-020")
    earlier = "".join(rows[:19]).encode("utf-8")
    if hashlib.sha256(earlier).hexdigest() != LFE_001_TO_019_ROWS_SHA256:
        raise AssertionError("an LFE row before LFE-020 was modified")
    if text.count("| LFE-020 /") != 1:
        raise AssertionError("LFE-020 must occur exactly once")
    cells = [cell.strip() for cell in rows[19].strip().strip("|").split("|")]
    if len(cells) != 4:
        raise AssertionError("LFE-020 row structure drifted")
    row = _semantic_text(rows[19])
    fragments = (
        "stash with a recovery label stayed",
        "merge commit on main contained its work",
        "usual branch and worktree commands did not show the stash",
        "stayed after tracktemplate completed the recovery cycle",
        "initial recovery audit found the work in named git state",
        "did not identify and reconcile the stash components or disposition",
        "independent review",
        "kept the recovery gate open for the retained unexplained stash",
        "recovery evidence records the b i w u reconciliation",
        "each git object in independent preservation",
        "no unique content stayed only in the stash",
        "project owner gave authority for its disposition",
        "uses feature branches recovery branches recovery worktrees and "
        "explicit commits as named git state",
        "checksum manifest",
        "independent preservation",
        "emergency stash only as temporary recovery state",
        "stash inventory",
        "stash ownership recovery purpose unique content and stash disposition",
        "cannot complete stash reconciliation or a stash stays in the inventory",
        "fails closed",
    )
    for fragment in fragments:
        if fragment not in row:
            raise AssertionError("LFE-020 lacks: " + fragment)
    reusable = _semantic_text(cells[3])
    for fragment in (
        "use visible recovery state",
        "feature branches recovery branches recovery worktrees and explicit commits",
        "use an emergency stash only as temporary recovery state",
        "keep the recovery gate open while a retained stash stays in the "
        "inventory or has no stash ownership recovery purpose or stash disposition",
        "reconcile each stash",
        "preserve unique content in named git state or independent preservation",
        "validate that unique content stays available and get applicable authority",
    ):
        if fragment not in reusable:
            raise AssertionError("LFE-020 reusable rule lacks: " + fragment)
    for link in (
        "RECOVERY_AND_BACKUP.md#visible-recovery-state",
        "AGENT_WORKFLOWS.md#session-continuity",
        "current/PHASE_EVIDENCE.md#visible-recovery-state-workflow-migration",
    ):
        if link not in rows[19]:
            raise AssertionError("LFE-020 lacks canonical link: " + link)
    for prohibited in (
        "git stash is unsafe",
        "git stash is forbidden",
        "this lfe owns",
        "lfe 020 owns",
    ):
        if prohibited in row:
            raise AssertionError(
                "LFE-020 exceeds its historical boundary: " + prohibited
            )


def validate_recovery_phase_evidence(text):
    """Bind the historical stash disposition to exact preservation proof."""
    section = _section(text, "Visible recovery-state workflow migration")
    semantic = _semantic_text(section)
    for fragment in (
        "merge commit dd768006c83b9bc26e3d2e6d6e13b2cebed40173 on main "
        "contained that state",
        "second parent is commit 6f88f5c522f089e33dc895ca00adaf1035604b0b",
        "stash topology was b i w u",
        "b and i have the same tree",
        "tree difference between b and w contained seven changed paths in git",
        "u contains four files",
        "files in those commits have different bytes from some stash blobs",
        "approved independent preservation for each identified git object",
        "stash had no repository information that named state or approved "
        "preservation did not contain",
        "stash@{0} identified the same stash commit and b i w u inventory",
        "authority for that stash only",
        "next stash inventory was empty and no other stash was changed",
        "inspection after disposition found no stash inventory or "
        "refs stash",
        "it did not change git",
        "git has the b i w u commits although the stash inventory is empty",
        "w tree contains seven paths for agent guidance and validation",
        "u tree contains four paths for skills and skill metadata",
        "named git state contains all these paths",
        "no current record identifies their content as sensitive evidence or "
        "local evidence",
        "current evidence identifies no incident with sensitive evidence or "
        "local evidence in this repository",
        "git objects stay for a future bounded $tracktemplate security review "
        "and recovery task",
        "does not define a procedure to remove git objects replace a repository "
        "or change independent preservation",
        "no authority for automatic or destructive git object removal",
    ):
        if fragment not in semantic:
            raise AssertionError("recovery phase evidence lacks: " + fragment)
    for identity in (
        "6f88f5c522f089e33dc895ca00adaf1035604b0b",
        "dd768006c83b9bc26e3d2e6d6e13b2cebed40173",
        "3dc9e7fcb0596752bcd2bd39a2dfee2d0f31e9c0",
        "397ad614cfc1764a7ca94b0705c6e448eba5b78a",
        "bf9f53c37c20690572a3970a78fa56a46a26ae12",
        "865037c60a47eb7428d0881de2c1df3aa92d67be",
        "cff63f011ddbe3bd7e762121b0a817fe4a5684bd",
        "2416cd8cd81d2a38a570b45c9d871f5a0d287e92",
        "5ef7ee84959ccb15c7ca20c447f3268eb488285c",
    ):
        if identity not in section:
            raise AssertionError(
                "recovery phase evidence lacks exact identity: " + identity
            )
    merge_parents = _run(
        [
            "git",
            "show",
            "-s",
            "--format=%P",
            "dd768006c83b9bc26e3d2e6d6e13b2cebed40173",
        ],
        cwd=ROOT,
    ).stdout.split()
    if (
        len(merge_parents) != 2
        or merge_parents[1]
        != "6f88f5c522f089e33dc895ca00adaf1035604b0b"
    ):
        raise AssertionError("recovery named-state merge topology drifted")
    if (
        "../backup-records/2026-08-01-phase5-closeout-snapshot.md"
        not in section
    ):
        raise AssertionError(
            "recovery phase evidence lacks independent-preservation linkage"
        )


def _load_tracked_markdown():
    result = _run(["git", "ls-files", "-z", "*.md"], cwd=ROOT)
    paths = [item for item in result.stdout.split("\0") if item]
    return {
        path: (ROOT / path).read_text(encoding="utf-8")
        for path in paths
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
    stash_inventory = _run(
        ["git", "stash", "list", "--format=%H"],
        cwd=ROOT,
    ).stdout
    if stash_inventory.strip():
        errors.append("live recovery gate has retained stash state")


def _validate_missing_critical_asset(errors):
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-missing-critical-asset-"
    ) as temporary:
        repository = _git_fixture(pathlib.Path(temporary))
        report = safety.audit_repository(repository.resolve())
        source = next(
            item
            for item in report["local_assets"]
            if item["path"] == safety.SOURCE_ARCHIVE_PATH.as_posix()
        )
        expected_finding = (
            "required-local-asset-missing:"
            + safety.SOURCE_ARCHIVE_PATH.as_posix()
        )
        if (
            source["present"]
            or report["readiness"]["critical_assets_ready"]
            or expected_finding not in report["findings"]
        ):
            errors.append("missing critical asset did not fail closed")

        result = _run(
            [
                sys.executable,
                str(TOOL_PATH),
                "--root",
                str(repository),
                "--require-critical-assets",
            ],
            cwd=ROOT,
            check=False,
        )
        records = [
            line[len(safety.SENTINEL):]
            for line in result.stdout.splitlines()
            if line.startswith(safety.SENTINEL)
        ]
        if result.returncode != 1 or len(records) != 1:
            errors.append("critical-asset CLI did not reject a clean fixture")
        elif json.loads(records[0])["requested_requirements"][
            "critical_assets"
        ]:
            errors.append("critical-asset CLI overstated fixture readiness")


def _validate_static_controls(errors):
    policy = POLICY_PATH.read_text(encoding="utf-8")
    agents = AGENTS_PATH.read_text(encoding="utf-8")
    validation = VALIDATION_PATH.read_text(encoding="utf-8")
    project_plan = PROJECT_PLAN_PATH.read_text(encoding="utf-8")
    workflows = WORKFLOWS_PATH.read_text(encoding="utf-8")
    learning = LEARNING_PATH.read_text(encoding="utf-8")
    phase_evidence = PHASE_EVIDENCE_PATH.read_text(encoding="utf-8")
    skills = {
        name: path.read_text(encoding="utf-8")
        for name, path in RECOVERY_SKILL_PATHS.items()
    }
    gitignore = GITIGNORE_PATH.read_text(encoding="utf-8")
    policy_flat = " ".join(policy.split())
    policy_markers = (
        "Independent project-data backup",
        "Operational for the complete declared project-data scope",
        "Passed and owner-accepted for the complete declared scope on 2026-07-22",
        "Active and verified again 2026-08-01",
        "QA-R01 remains closed",
        "retain the initial accepted snapshot plus at least four recent successful",
        "never delete snapshots automatically",
        "restore drill at least monthly",
        "2026-07-22-initial-repository-backup-restore.md",
        "2026-07-27-pre-phase4-family-support-snapshot.md",
        "2026-08-01-phase5-closeout-snapshot.md",
        "git clean",
        "different storage device",
        "restore into a new empty directory",
        "Timeshift system snapshots",
        "--require-backup-target",
        "Active and verified 2026-07-28",
        "Strict, up-to-date `validation` from GitHub Actions app `15368` is required",
        "force pushes and branch deletion remain blocked",
        "positive recovery evidence for the complete valuable project-data scope",
        "review backup currency and declared scope at every phase closeout",
        "Missing the cadence, changing the valuable-data scope or failing a later run",
    )
    for marker in policy_markers:
        if marker not in policy_flat:
            errors.append("recovery policy marker is missing: " + marker)
    for marker in (
        "## Repository and System Safety",
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

    for check in (
        lambda: validate_visible_recovery_policy(policy),
        lambda: validate_visible_recovery_routing(workflows, skills),
        lambda: validate_recovery_policy_owner(_load_tracked_markdown()),
        lambda: validate_recovery_lfe(learning),
        lambda: validate_recovery_phase_evidence(phase_evidence),
    ):
        try:
            check()
        except AssertionError as error:
            errors.append(str(error))

    try:
        validate_safety_audit_git_commands(
            TOOL_PATH.read_text(encoding="utf-8")
        )
        validate_safety_audit_git_commands(
            "def inspect(root):\n"
            "    return _git(root, 'stash', 'list', '--format=%H')\n"
        )
    except AssertionError as error:
        errors.append(str(error))
    for command in (
        "_git(root, 'stash', 'drop', 'stash@{0}')",
        "_git(root, 'stash', 'branch', 'recovery/test', 'stash@{0}')",
        "_git(root, 'stash', 'show', '-p', 'stash@{0}')",
        "_git(root, 'stash', 'list', '--format=%gs')",
        "_git(root, 'reflog', 'delete', 'refs/stash@{0}')",
        "_git(root, 'update-ref', '-d', 'refs/stash')",
        "_git(root, 'remote', 'remove', 'origin')",
        "_git(root, 'worktree', 'remove', '/tmp/example')",
        "_git(root, action, 'drop', 'stash@{0}')",
        "subprocess.run(['git', 'stash', 'drop', 'stash@{0}'])",
        "subprocess.getoutput('git stash drop stash@{0}')",
        "subprocess.getstatusoutput('git stash drop stash@{0}')",
        "os.system('git stash drop stash@{0}')",
        "os.fork()",
        "os.popen('git stash show -p stash@{0}')",
    ):
        source = "def mutate(root):\n    return {}\n".format(command)
        try:
            validate_safety_audit_git_commands(source)
        except AssertionError:
            continue
        errors.append("safety audit accepted a mutating Git command: " + command)
    aliased_subprocess = (
        "def mutate(root):\n"
        "    runner = subprocess.run\n"
        "    return runner(['git', 'stash', 'drop', 'stash@{0}'])\n"
    )
    try:
        validate_safety_audit_git_commands(aliased_subprocess)
    except AssertionError:
        pass
    else:
        errors.append("safety audit accepted an aliased Git subprocess")
    subprocess_module_alias = (
        "import subprocess\n"
        "runner = subprocess\n"
        "def mutate(root):\n"
        "    return runner.getoutput('git stash drop stash@{0}')\n"
    )
    try:
        validate_safety_audit_git_commands(subprocess_module_alias)
    except AssertionError:
        pass
    else:
        errors.append("safety audit accepted a subprocess module alias")
    aliased_os = (
        "import os as runner_os\n"
        "def mutate(root):\n"
        "    return runner_os.system('git stash drop stash@{0}')\n"
    )
    try:
        validate_safety_audit_git_commands(aliased_os)
    except AssertionError:
        pass
    else:
        errors.append("safety audit accepted aliased OS execution")
    os_module_alias = (
        "import os\n"
        "runner_os = os\n"
        "def mutate(root):\n"
        "    return runner_os.system('git stash drop stash@{0}')\n"
    )
    try:
        validate_safety_audit_git_commands(os_module_alias)
    except AssertionError:
        pass
    else:
        errors.append("safety audit accepted an OS module alias")
    mutating_wrapper = (
        "import subprocess\n"
        "def _git(root, *arguments, allow_failure=False):\n"
        "    return subprocess.run(\n"
        "        ['git', '-C', str(root), 'stash', 'drop', *arguments]\n"
        "    )\n"
    )
    try:
        validate_safety_audit_git_commands(mutating_wrapper)
    except AssertionError:
        pass
    else:
        errors.append("safety audit accepted a mutating Git wrapper prefix")


def validate(include_live_workstation=False):
    errors = []
    _validate_repository_state(errors)
    _validate_stash_topology(errors)
    _validate_backup_assessment(errors)
    _validate_missing_critical_asset(errors)
    if include_live_workstation:
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live-workstation",
        action="store_true",
        help=(
            "also require this checkout's ignored source archive, main branch "
            "and origin/main workstation evidence"
        ),
    )
    arguments = parser.parse_args(argv)
    validate(include_live_workstation=arguments.live_workstation)


if __name__ == "__main__":
    main()
