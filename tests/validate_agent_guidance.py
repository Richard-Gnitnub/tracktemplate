#!/usr/bin/env python3
"""Fail-closed validation for TrackTemplate Codex agent guidance."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

from governance_markdown import direct_section_content


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
WORKFLOWS = ROOT / "reference" / "AGENT_WORKFLOWS.md"
AGENTS = ROOT / "AGENTS.md"
PRODUCT_VISION = ROOT / "reference" / "PRODUCT_VISION.md"
ENGINEERING_POLICY = ROOT / "reference" / "ENGINEERING_POLICY.md"
TERMINOLOGY = ROOT / "reference" / "TERMINOLOGY.md"

TT_DOC_PROFILE_LINK = (
    "../../../reference/ENGINEERING_POLICY.md"
    "#tt-doc-001-tracktemplate-technical-documentation-profile"
)
TT_DOC_SKILL_NAMES = {
    "tracktemplate-change-validation",
    "tracktemplate-context-recovery",
    "tracktemplate-continue",
    "tracktemplate-documentation-alignment",
    "tracktemplate-documentation-review",
    "tracktemplate-quality-review",
    "tracktemplate-technical-lead",
}
TT_DOC_TERM_SKILL_NAMES = {
    "tracktemplate-change-validation",
    "tracktemplate-documentation-alignment",
    "tracktemplate-documentation-review",
    "tracktemplate-quality-review",
}
TT_DOC_TERMINOLOGY_LINK = (
    "../../../reference/TERMINOLOGY.md"
    "#asd-ste100-project-terminology"
)
TT_DOC_SOURCE_LINK = (
    "../../../reference/external/asd-ste100/README.md"
)
TT_DOC_DESCRIPTION_FRAGMENTS = {
    "tracktemplate-change-validation": (
        "proportionate TrackTemplate validation",
        "classify failed tests",
    ),
    "tracktemplate-context-recovery": (
        "authority-ranked",
        "loss-checked",
    ),
    "tracktemplate-continue": (
        "one complete repository-driven TrackTemplate development cycle",
        "Never use it for Level 3 acceptance",
    ),
    "tracktemplate-documentation-alignment": (
        "Reconcile TrackTemplate documentation claims",
        "current repository authority",
    ),
    "tracktemplate-documentation-review": (
        "Create, review, shorten or reorganise",
        "canonical document",
    ),
    "tracktemplate-quality-review": (
        "staff-level review",
        "read-only independent review",
    ),
    "tracktemplate-technical-lead": (
        "Level 1 or Level 2 outcome",
        "Do not use for",
        "Level 3 decision",
    ),
}

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REGISTER_HEADING_RE = re.compile(r"^### `([a-z0-9]+(?:-[a-z0-9]+)*)`$", re.MULTILINE)
REGISTER_PATH_RE = re.compile(
    r"^Path: `(\.agents/skills/([a-z0-9]+(?:-[a-z0-9]+)*)/SKILL\.md)`$",
    re.MULTILINE,
)
VALID_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_SKILL_ENTRIES = {
    "SKILL.md",
    "agents",
    "assets",
    "references",
    "scripts",
}
MAX_SKILL_LINES = 500
RESOURCE_DIRECTORY_NAMES = ("assets", "references", "scripts")
REQUIRED_SKILL_METADATA_NAMES = {
    "tracktemplate-chief-of-staff",
    "tracktemplate-ide-workspace-alignment",
    "tracktemplate-technical-lead",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: Path) -> str:
    require(path.is_file(), f"missing required agent guidance: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def semantic_text(value: str) -> str:
    """Normalise only line wrapping and Markdown presentation."""
    value = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "-", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = value.replace("**", "").replace("`", "")
    return " ".join(value.split())


def semantic_paragraphs(text: str) -> list[str]:
    """Return local semantic paragraphs independent of Markdown wrapping."""
    return [
        semantic_text(block)
        for block in re.split(r"\n[ \t]*\n", text)
        if block.strip()
    ]


def bullet_items(text: str) -> list[str]:
    """Return top-level bullet items with wrapped continuation lines joined."""
    items: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("- "):
            if current:
                items.append(semantic_text("\n".join(current)))
            current = [line[2:]]
        elif current and (line.startswith("  ") or not line.strip()):
            if line.strip():
                current.append(line.strip())
        elif current:
            items.append(semantic_text("\n".join(current)))
            current = []
    if current:
        items.append(semantic_text("\n".join(current)))
    return items


def validate_explicit_agent_safeguards(agents: str) -> None:
    """Protect every accepted no-silent-change and terminology boundary."""
    change_items = bullet_items(
        direct_section_content(agents, "Proportional change discipline")
    )
    expected_change = semantic_text(
        "Do not silently change geometry, units, frames, sampling, tolerances, "
        "topology, timbering, chairs, stable identities, ordering, schemas, "
        "stored properties, visibility, transactions, rollback, cache invalidation "
        "or output."
    )
    require(
        expected_change in change_items,
        "AGENTS lost or weakened an explicit no-silent-change safeguard",
    )

    terminology_items = bullet_items(
        direct_section_content(
            agents,
            "Railway, rights and persistence safeguards",
        )
    )
    expected_terminology = semantic_text(
        "Use plain line for track without switches and crossings. Do not introduce "
        "ordinary track in new prose, UI, schemas or APIs; existing identifiers "
        "are frozen compatibility evidence."
    )
    require(
        expected_terminology in terminology_items,
        "AGENTS lost or weakened its explicit terminology-surface boundary",
    )


def validate_chief_comparative_priority(chief: str, workflows: str) -> None:
    """Require comparative priority in both the brief and workflow contract."""
    brief = direct_section_content(chief, "Next-outcome brief")
    required_explanation = semantic_text(
        "The brief must compare the selected work with credible maintenance, "
        "evidence, risk-reduction and other authorised alternatives. Calling an "
        "item \"highest-value\" without that comparative rationale is insufficient."
    )
    require(
        required_explanation in semantic_paragraphs(brief),
        "Chief of Staff lost its comparative-rationale rule",
    )
    require(
        "Why this outranks maintenance alternatives" in bullet_items(brief),
        "Chief of Staff brief lost its comparative-priority assignment field",
    )

    workflow_section = direct_section_content(
        workflows,
        "`tracktemplate-chief-of-staff`",
        level=3,
    )
    combined_priority_text = semantic_text(
        brief + "\n" + workflow_section
    ).lower()
    prohibited_priority_polarities = (
        "comparison is optional",
        "comparison may be omitted",
        "comparison can be omitted",
        "comparison need not be made",
        "highest value is sufficient",
        "highest-value is sufficient",
        "alternatives need not be considered",
        "alternatives may be ignored",
    )
    require(
        not any(
            phrase in combined_priority_text
            for phrase in prohibited_priority_polarities
        ),
        "Chief of Staff comparative priority became optional or unnecessary",
    )
    required_workflow_clause = semantic_text(
        "Use it when the owner says progress appears stuck, circular, "
        "maintenance/evidence-heavy or unclear, and compose it from "
        "$tracktemplate-continue when that workflow detects its defined loop "
        "conditions. It is a vision-informed programme orchestrator: it "
        "reconciles programme, "
        "phase, evidence and pull-request state; detects loops; controls task "
        "accountability; compares the selected work with credible maintenance, "
        "evidence, risk-reduction and other authorised alternatives; and produces "
        "exactly one transient, advisory assignment or stop brief. Its assignment "
        "must state Why this outranks maintenance alternatives; a highest-value "
        "label without that comparison is insufficient. It is read-only, is not "
        "required for every routine change and cannot implement or accept project "
        "authority."
    )
    require(
        required_workflow_clause in semantic_paragraphs(workflow_section),
        "AGENT_WORKFLOWS lost the comparative-priority contract",
    )


def parse_frontmatter(path: Path, text: str) -> dict[str, str]:
    require(text.startswith("---\n"), f"{path.relative_to(ROOT)} lacks YAML frontmatter")
    parts = text.split("---\n", 2)
    require(len(parts) == 3, f"{path.relative_to(ROOT)} has unterminated YAML frontmatter")

    fields: dict[str, str] = {}
    for raw_line in parts[1].splitlines():
        line = raw_line.strip()
        require(bool(line), f"{path.relative_to(ROOT)} has a blank frontmatter entry")
        require(":" in line, f"{path.relative_to(ROOT)} has invalid frontmatter: {raw_line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        require(key not in fields, f"{path.relative_to(ROOT)} repeats frontmatter key {key!r}")
        require(bool(value), f"{path.relative_to(ROOT)} has empty frontmatter key {key!r}")
        fields[key] = value

    require(
        set(fields) == {"name", "description"},
        f"{path.relative_to(ROOT)} frontmatter must contain only name and description",
    )
    return fields


def markdown_target(
    document: Path,
    raw_target: str,
    repository_root: Path = ROOT,
) -> Path | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1:target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]

    if not target or target.startswith("#"):
        return None
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith("//"):
        return None

    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    require(
        not target.startswith("/"),
        (
            "non-portable absolute Markdown target in "
            f"{document.relative_to(repository_root)}: {target}"
        ),
    )

    resolved = (document.parent / target).resolve()
    try:
        resolved.relative_to(repository_root)
    except ValueError as error:
        raise AssertionError(
            "repository-external Markdown target in "
            f"{document.relative_to(repository_root)}: {target}"
        ) from error
    return resolved


def direct_markdown_targets(
    document: Path,
    text: str,
    repository_root: Path = ROOT,
) -> set[Path]:
    """Return repository-local targets linked directly from one document."""
    targets = set()
    for raw_target in LINK_RE.findall(text):
        target = markdown_target(document, raw_target, repository_root)
        if target is not None:
            targets.add(target)
    return targets


def validate_skill_line_budget(
    skill_file: Path,
    text: str,
    repository_root: Path = ROOT,
) -> None:
    """Require one skill file to remain within its loading budget."""
    require(
        len(text.splitlines()) < MAX_SKILL_LINES,
        (
            f"{skill_file.relative_to(repository_root)} must remain below "
            f"{MAX_SKILL_LINES} lines for progressive disclosure"
        ),
    )


def validate_skill_resource_routing(
    directory: Path,
    text: str,
    repository_root: Path = ROOT,
) -> None:
    """Require every bundled resource to be linked directly from SKILL.md."""
    skill_file = directory / "SKILL.md"
    linked_targets = direct_markdown_targets(
        skill_file,
        text,
        repository_root,
    )

    resource_files = []
    for resource_directory_name in RESOURCE_DIRECTORY_NAMES:
        resource_root = directory / resource_directory_name
        if resource_root.is_dir():
            resource_files.extend(
                path
                for path in resource_root.rglob("*")
                if path.is_file()
            )

    references_root = directory / "references"
    nested_references = [
        path
        for path in resource_files
        if references_root in path.parents and path.parent != references_root
    ]
    require(
        not nested_references,
        "skill references must remain one filesystem level from SKILL.md:\n"
        + "\n".join(
            path.relative_to(repository_root).as_posix()
            for path in sorted(nested_references)
        ),
    )

    unlinked_resources = [
        path
        for path in resource_files
        if path.resolve() not in linked_targets
    ]
    require(
        not unlinked_resources,
        "skill resource is not linked directly from SKILL.md:\n"
        + "\n".join(
            path.relative_to(repository_root).as_posix()
            for path in sorted(unlinked_resources)
        ),
    )


def validate_progress_skill_metadata(directory: Path, name: str) -> None:
    """Require selected skills to expose valid generated UI metadata."""
    if name not in REQUIRED_SKILL_METADATA_NAMES:
        return

    metadata_path = directory / "agents" / "openai.yaml"
    metadata = read(metadata_path)
    values: dict[str, str] = {}
    for key in ("display_name", "short_description", "default_prompt"):
        match = re.search(
            rf'^  {key}: "([^"\n]+)"$',
            metadata,
            re.MULTILINE,
        )
        require(match is not None, f"{metadata_path.relative_to(ROOT)} lacks {key}")
        values[key] = match.group(1)

    require(
        25 <= len(values["short_description"]) <= 64,
        f"{metadata_path.relative_to(ROOT)} short_description is not 25-64 chars",
    )
    require(
        f"${name}" in values["default_prompt"],
        f"{metadata_path.relative_to(ROOT)} default_prompt lacks ${name}",
    )


def validate_progress_delivery_structure() -> None:
    """Protect the new role separation without duplicating skill prose."""
    skill_root = ROOT / ".agents" / "skills"
    expected_headings = {
        "tracktemplate-chief-of-staff": {
            "Read-only authority boundary",
            "Reconstruct current progress",
            "Classify recent tranches",
            "Vision-led selection",
            "Execution control and accountability",
            "Loop prevention",
            "Delegated-result reconciliation",
            "Next-outcome brief",
        },
        "tracktemplate-technical-lead": {
            "Confirm authority",
            "Inspect the delivery boundary",
            "Compose existing specialists",
            "Boundaries",
        },
        "tracktemplate-continue": {
            "Reconstruct repository authority",
            "Select one outcome or stop",
            "Validate and review",
            "Owner acceptance pack",
        },
        "tracktemplate-ide-workspace-alignment": {
            "Responsibility boundary",
            "Evidence boundary",
            "Alignment workflow",
            "Steady-state convention",
            "Composition with TrackTemplate continue",
            "Report",
        },
    }
    expected_links = {
        "tracktemplate-chief-of-staff": {"tracktemplate-continue"},
        "tracktemplate-technical-lead": {
            "tracktemplate-api-design",
            "tracktemplate-architecture-review",
            "tracktemplate-change-validation",
            "tracktemplate-continue",
            "tracktemplate-publish",
            "tracktemplate-quality-review",
        },
        "tracktemplate-continue": {
            "tracktemplate-change-validation",
            "tracktemplate-chief-of-staff",
            "tracktemplate-ide-workspace-alignment",
            "tracktemplate-publish",
            "tracktemplate-quality-review",
            "tracktemplate-technical-lead",
        },
        "tracktemplate-ide-workspace-alignment": {
            "tracktemplate-context-recovery",
            "tracktemplate-continue",
        },
    }

    for name, required_headings in expected_headings.items():
        skill_file = skill_root / name / "SKILL.md"
        text = read(skill_file)
        headings = set(re.findall(r"^## (.+)$", text, re.MULTILINE))
        require(
            required_headings <= headings,
            f"{name} lacks required sections: {sorted(required_headings - headings)}",
        )
        targets = direct_markdown_targets(skill_file, text)
        linked_skills = {
            target.parent.name
            for target in targets
            if target.name == "SKILL.md" and target.parent.parent == skill_root
        }
        require(
            expected_links[name] <= linked_skills,
            f"{name} lacks composition links: "
            f"{sorted(expected_links[name] - linked_skills)}",
        )

    require(
        not (skill_root / "tracktemplate-deliver-outcome").exists(),
        "continuation must not be duplicated by tracktemplate-deliver-outcome",
    )


def validate_ide_workspace_alignment_contract(
    ide_skill: str,
    continuation: str,
) -> None:
    """Protect the IDE/Git authority and loss-safe workspace contract."""
    responsibility = direct_section_content(
        ide_skill,
        "Responsibility boundary",
    )
    required_git_boundary = semantic_text(
        "Keep Git workflows authoritative for branches, worktrees, commits, "
        "upstreams, pull requests, reachability and every safe Git operation. "
        "This skill may ask for that evidence and describe the required end "
        "state, but it does not grant checkout, move, removal, prune, "
        "deletion, "
        "commit, push or merge authority."
    )
    require(
        required_git_boundary in semantic_paragraphs(responsibility),
        "IDE workspace alignment lost its Git-only authority boundary",
    )

    evidence = direct_section_content(ide_skill, "Evidence boundary")
    required_operator_boundary = semantic_text(
        "Treat these as operator-confirmed unless the active host environment "
        "can prove them directly:"
    )
    require(
        required_operator_boundary in semantic_paragraphs(evidence),
        "IDE workspace alignment lost its operator-only evidence boundary",
    )
    evidence_items = bullet_items(evidence)
    for required_item in (
        "which physical PyCharm window is visible and focused;",
        (
            "the branch indicator and project path presently shown in that "
            "window;"
        ),
        "unsaved editor buffers or Local History not represented on disk;",
        "the run/debug configuration selected in the UI; and",
        (
            "whether PyCharm has refreshed its VCS state after an external "
            "Git action."
        ),
    ):
        require(
            semantic_text(required_item) in evidence_items,
            "IDE workspace alignment lost operator-only UI evidence: "
            + required_item,
        )
    required_no_inference = semantic_text(
        "Never infer the Git branch from a run-configuration name, coverage "
        "filename, recent-file entry, window title or SDK label. Resolve it "
        "from the backing Git worktree."
    )
    require(
        required_no_inference in semantic_paragraphs(evidence),
        "IDE workspace alignment permits non-Git branch inference",
    )

    steady_state = semantic_text(
        direct_section_content(ide_skill, "Steady-state convention")
    )
    required_steady_state = semantic_text(
        "Primary PyCharm project clean accepted main stable interpreter "
        "operator's canonical project view Named persistent worktrees one per "
        "active implementation or PR branch opened as separate PyCharm "
        "projects when needed Temporary /tmp worktrees disposable review and "
        "integration "
        "only never the sole location of active, uncommitted or unpushed work"
    )
    require(
        required_steady_state in steady_state,
        "IDE workspace alignment lost its primary/persistent/temporary model",
    )

    pre_mutation = semantic_text(
        direct_section_content(
            continuation,
            "Align the operator-facing workspace",
        )
    )
    require(
        "Before the first checkout, branch or worktree mutation, compose "
        "$tracktemplate-ide-workspace-alignment" in pre_mutation
        and "The IDE skill supplies no Git authority and must never infer a "
        "branch from a run-configuration or window name." in pre_mutation,
        "tracktemplate-continue lost its pre-mutation IDE alignment boundary",
    )
    post_sync = semantic_text(
        direct_section_content(
            continuation,
            "Verify and integrate the previous pull request",
        )
    )
    require(
        "Repeat the IDE comparison after synchronisation." in post_sync,
        "tracktemplate-continue lost its post-synchronisation IDE comparison",
    )


def require_ide_contract_mutation_rejected(
    ide_skill: str,
    continuation: str,
    mutation: str,
) -> None:
    """Require one representative IDE-contract mutation to fail closed."""
    try:
        validate_ide_workspace_alignment_contract(ide_skill, continuation)
    except AssertionError:
        return
    raise AssertionError(
        "IDE workspace contract mutation escaped: " + mutation
    )


def validate_ide_workspace_alignment_mutations(
    ide_skill: str,
    continuation: str,
) -> None:
    """Exercise representative deletion and inversion mutations."""
    for mutation, original, replacement in (
        ("Git authority inversion", "does not grant", "grants"),
        ("operator evidence inversion", "operator-confirmed", "file-proved"),
        ("branch inference inversion", "Never infer", "Infer"),
        (
            "temporary-worktree safeguard deletion",
            "never the sole location of active, uncommitted or unpushed work",
            "",
        ),
    ):
        require(
            original in ide_skill,
            "IDE mutation target drifted: " + mutation,
        )
        require_ide_contract_mutation_rejected(
            ide_skill.replace(original, replacement, 1),
            continuation,
            mutation,
        )

    for mutation, original, replacement in (
        (
            "pre-mutation comparison inversion",
            "Before the first checkout",
            "After the first checkout",
        ),
        (
            "post-synchronisation comparison deletion",
            "Repeat the IDE comparison after synchronisation.",
            "",
        ),
    ):
        require(
            original in continuation,
            "IDE mutation target drifted: " + mutation,
        )
        require_ide_contract_mutation_rejected(
            ide_skill,
            continuation.replace(original, replacement, 1),
            mutation,
        )


def validate_continue_invocation_policy(workflows: str) -> None:
    """Protect the accepted explicit trigger and blocker-only repair boundary."""
    skill_file = SKILLS_ROOT / "tracktemplate-continue" / "SKILL.md"
    skill_text = read(skill_file)
    description = parse_frontmatter(skill_file, skill_text)["description"]
    metadata_path = skill_file.parent / "agents" / "openai.yaml"
    metadata = read(metadata_path)
    publish_root = SKILLS_ROOT / "tracktemplate-publish"
    publish_text = read(publish_root / "SKILL.md")
    publish_metadata = read(publish_root / "agents" / "openai.yaml")
    quality_text = read(SKILLS_ROOT / "tracktemplate-quality-review" / "SKILL.md")
    normalized_skill_text = " ".join(skill_text.split())
    normalized_workflows = " ".join(workflows.split())
    normalized_publish_text = " ".join(publish_text.split())
    normalized_quality_text = " ".join(quality_text.split())

    require(
        "Use only when the project owner explicitly invokes the literal "
        "`$tracktemplate-continue` command; natural-language equivalents do not "
        "activate it."
        in description,
        "tracktemplate-continue description lost its literal-only trigger",
    )
    require(
        re.search(
            r"^  allow_implicit_invocation: false$",
            metadata,
            re.MULTILINE,
        )
        is not None,
        "tracktemplate-continue must remain unavailable to implicit routing",
    )
    require(
        re.search(
            r"^  allow_implicit_invocation: false$",
            publish_metadata,
            re.MULTILINE,
        )
        is not None,
        "tracktemplate-publish must remain unavailable to implicit routing",
    )
    require(
        "Only a project-owner command containing the literal "
        "`$tracktemplate-continue` invocation activates it."
        in normalized_workflows,
        "AGENT_WORKFLOWS lost the explicit continuation boundary",
    )
    require(
        "description and its metadata permits implicit invocation. The handoff "
        "and continue skills require their literal project-owner invocations; "
        "publish requires either its literal invocation or delegation from an "
        "active literal `$tracktemplate-continue` cycle."
        in normalized_workflows
        and "Does not activate TrackTemplate publish; request the literal "
        "`$tracktemplate-publish` invocation"
        in normalized_workflows,
        "AGENT_WORKFLOWS lost an explicit-only project-skill boundary",
    )
    require(
        "Do not repair `REQUIRED_BEFORE_EXIT`, `BACKLOG` or `OPTIONAL` findings "
        "in this cycle."
        in normalized_skill_text,
        "tracktemplate-continue no longer limits repair to blockers",
    )
    require(
        "no more than two total repair-and-review passes"
        in normalized_skill_text
        and "another separate read-only staff review of the complete repaired "
        "source before publication"
        in normalized_skill_text,
        "tracktemplate-continue lost its shared repair or final-review limit",
    )
    require(
        "It does not delegate this skill's repair authority."
        in normalized_publish_text
        and "without changing source or Git state" in normalized_publish_text,
        "delegated publication can mutate final-reviewed source",
    )
    require(
        "During an active continuation cycle, only a `BLOCKER` may return to "
        "implementation; `REQUIRED_BEFORE_EXIT`, `BACKLOG` and `OPTIONAL` "
        "findings do not join that cycle."
        in normalized_quality_text
        and "During an active continuation cycle, only a `BLOCKER` may return "
        "to implementation; `REQUIRED_BEFORE_EXIT`, `BACKLOG` and `OPTIONAL` "
        "items do not join that cycle."
        in normalized_workflows,
        "non-blocking review findings can enter a continuation repair pass",
    )


def validate_vision_led_workflows(workflows: str) -> None:
    """Protect authority routing without duplicating the governing prose."""
    agents = read(AGENTS)
    vision = read(PRODUCT_VISION)
    chief = read(SKILLS_ROOT / "tracktemplate-chief-of-staff" / "SKILL.md")
    continuation = read(SKILLS_ROOT / "tracktemplate-continue" / "SKILL.md")
    normalized_chief = " ".join(chief.split())
    normalized_continuation = " ".join(continuation.split())
    normalized_workflows = " ".join(workflows.split())

    validate_explicit_agent_safeguards(agents)
    validate_chief_comparative_priority(chief, workflows)

    require(
        "reference/PRODUCT_VISION.md" in agents
        and "PRODUCT_VISION.md" in workflows,
        "agent guidance does not route through the canonical Product Vision",
    )
    require(
        "Vision and execution authority" in vision
        and "Current programme: TrackTemplate Core migration" in vision
        and "Subsequent programme: TrackTemplate Layout Editor" in vision,
        "canonical Product Vision lacks programme or execution authority",
    )
    require(
        "vision-informed programme orchestrator, not a task-list iterator"
        in normalized_chief
        and "Which active phase criterion does it advance?" in chief
        and "Work claimed, work actually present, work validated and work "
        "independently accepted are four different states."
        in normalized_chief,
        "chief of staff lost vision-led selection or result accountability",
    )
    for changed_basis in (
        "new repository evidence",
        "a changed and testable hypothesis",
        "newly authorised scope or method",
        "a corrected environment or fixture",
        "an independently identified defect",
        "a narrower task with different acceptance evidence",
    ):
        require(
            changed_basis in normalized_chief,
            "chief of staff lost loop-prevention basis: " + changed_basis,
        )
    require(
        "find something unfinished and continue coding"
        in normalized_continuation
        and "D-GOV-004" in continuation
        and "D-GOV-005" in continuation
        and "does not invoke this skill, widen execution authority"
        in normalized_continuation,
        "continue lost its vision-led selection or standing authority boundary",
    )
    require(
        "agent task → bounded work item → finding/exit → current programme → "
        "vision" in normalized_workflows
        and "claimed, present, validated and independently accepted"
        in normalized_workflows,
        "agent workflows lost assignment traceability or acceptance separation",
    )


def validate_links(documents: list[Path]) -> None:
    broken: list[str] = []
    for document in documents:
        text = read(document)
        for raw_target in LINK_RE.findall(text):
            target = markdown_target(document, raw_target)
            if target is not None and not target.exists():
                broken.append(
                    f"{document.relative_to(ROOT)} -> {target.relative_to(ROOT)}"
                )
    require(not broken, "broken agent-guidance Markdown targets:\n" + "\n".join(broken))


def validate_documentation_profile_routing(
    names: list[str],
    workflows: str,
) -> None:
    """Keep TT-DOC-001 with one policy owner and existing workflows."""
    engineering = read(ENGINEERING_POLICY)
    anchor = 'id="tt-doc-001-tracktemplate-technical-documentation-profile"'
    require(
        engineering.count(anchor) == 1,
        "TT-DOC-001 canonical profile anchor is missing or duplicated",
    )
    require(
        not (ROOT / "reference" / "DOCUMENTATION_PROFILE.md").exists(),
        "TT-DOC-001 gained a competing canonical document",
    )
    competing_names = [
        name
        for name in names
        if "documentation-profile" in name or "ste100" in name
    ]
    require(
        not competing_names,
        "TT-DOC-001 gained an overlapping profile or STE skill: "
        + ", ".join(competing_names),
    )

    normalized_workflows = semantic_text(workflows)
    for fragment in (
        "TT-DOC-001 workflow integration",
        "Skills apply these owners by reference",
        "Each separate responsibility that can occur repeatedly has one "
        "owner",
        "use the primary owner that is already in the skill catalog",
        "Do not keep two skills with competing primary responsibilities",
        "adds no documentation-profile or tracktemplate-ste100 skill",
    ):
        require(
            semantic_text(fragment) in normalized_workflows,
            "AGENT_WORKFLOWS lost TT-DOC-001 overlap control: " + fragment,
        )

    for name in sorted(TT_DOC_SKILL_NAMES):
        skill_file = SKILLS_ROOT / name / "SKILL.md"
        skill_text = read(skill_file)
        require(
            TT_DOC_PROFILE_LINK in skill_text,
            f"{name} does not reference the canonical TT-DOC-001 owner",
        )
        if name in TT_DOC_TERM_SKILL_NAMES:
            require(
                TT_DOC_TERMINOLOGY_LINK in skill_text,
                f"{name} does not reference the canonical project terms",
            )
        description = parse_frontmatter(skill_file, skill_text)["description"]
        for fragment in TT_DOC_DESCRIPTION_FRAGMENTS[name]:
            require(
                fragment in description,
                f"{name} description lost its primary responsibility: {fragment}",
            )
        require(
            not (
                all(
                    term in skill_text
                    for term in (
                        "Pending",
                        "Evidenced",
                        "Accepted",
                        "Blocked",
                        "Finding",
                        "Limitation",
                        "Unknown",
                        "Decision required",
                    )
                )
                and "Owner view → canonical information → proof/provenance"
                in skill_text
            ),
            f"{name} duplicates the complete TT-DOC-001 policy",
        )

    documentation_review = read(
        SKILLS_ROOT / "tracktemplate-documentation-review" / "SKILL.md"
    )
    writing_checklist = read(
        SKILLS_ROOT
        / "tracktemplate-documentation-review"
        / "references"
        / "writing-checklist.md"
    )
    for path_name, guidance in (
        ("documentation-review skill", documentation_review),
        ("documentation writing checklist", writing_checklist),
    ):
        guidance_flat = semantic_text(guidance)
        require(
            "TrackTemplate UK English spelling directive" in guidance_flat,
            path_name + " lost the canonical spelling directive",
        )
        require(
            "Do not change other Issue 9 requirements" in guidance_flat,
            path_name + " weakened non-spelling Issue 9 requirements",
        )
        require(
            "priority over the usual UK-English convention" not in guidance_flat
            and "UK-English convention applies outside" not in guidance_flat,
            path_name + " restored the superseded American-only rule",
        )

    continuation = read(
        SKILLS_ROOT / "tracktemplate-continue" / "SKILL.md"
    )
    owner_pack = direct_section_content(continuation, "Owner acceptance pack")
    for field in (
        "Current state",
        "What changed",
        "What now works",
        "Limitations/findings",
        "Owner decision",
        "Next action",
    ):
        require(
            f"**{field}**" in owner_pack,
            "continue owner view lost field: " + field,
        )
    require(
        "presentation from canonical records" in owner_pack
        and "formal status" in owner_pack
        and "validation" in owner_pack
        and "staff-review" in owner_pack,
        "continue owner view lost its derivation or technical provenance",
    )

    documentation_review = read(
        SKILLS_ROOT / "tracktemplate-documentation-review" / "SKILL.md"
    )
    require(
        "official source" in documentation_review
        and "full logical unit that contains the change" in documentation_review
        and "Do not claim Issue 9 conformance" in documentation_review,
        "documentation review lost its official Issue 9 assessment boundary",
    )
    change_validation = read(
        SKILLS_ROOT / "tracktemplate-change-validation" / "SKILL.md"
    )
    require(
        "validator as proof of linguistic conformance" in change_validation,
        "change validation lets automation prove linguistic conformance",
    )
    quality_review = read(
        SKILLS_ROOT / "tracktemplate-quality-review" / "SKILL.md"
    )
    quality_review_flat = semantic_text(quality_review)
    require(
        "reviewer used the official standard" in quality_review_flat
        and "validator result alone is not sufficient evidence"
        in quality_review_flat,
        "quality review lost its Issue 9 evidence boundary",
    )

    source_skill_names = {
        "tracktemplate-change-validation",
        "tracktemplate-documentation-alignment",
        "tracktemplate-documentation-review",
        "tracktemplate-quality-review",
    }
    for name in names:
        skill_text = read(SKILLS_ROOT / name / "SKILL.md")
        require(
            "ASD-STE100_ISSUE9.pdf" not in skill_text,
            name + " duplicates the canonical ASD-STE100 local path",
        )
        if name in source_skill_names:
            require(
                TT_DOC_SOURCE_LINK in skill_text,
                name + " lost the canonical ASD-STE100 source routing",
            )
        else:
            require(
                TT_DOC_SOURCE_LINK not in skill_text,
                name + " duplicates ASD-STE100 source resolution",
            )

    documentation_review_flat = semantic_text(documentation_review)
    for fragment in (
        "Use the local official PDF when it is available",
        "Otherwise, use the official ASD/STEMG source when it is available",
        "Report the official source that you used",
        "If no official source is available, do not claim conformance",
    ):
        require(
            fragment in documentation_review_flat,
            "documentation review lost source-resolution behavior: " + fragment,
        )

    documentation_alignment = read(
        SKILLS_ROOT / "tracktemplate-documentation-alignment" / "SKILL.md"
    )
    documentation_alignment_flat = semantic_text(documentation_alignment)
    require(
        "TT-DOC-001 and TT-DOC-002 are policy authority"
        in documentation_alignment_flat
        and "PDF is not repository policy" in documentation_alignment_flat,
        "documentation alignment confused policy with the external PDF",
    )

    change_validation_flat = semantic_text(change_validation)
    require(
        "review reports an official source" in change_validation_flat
        and "Normal repository validation does not use the ignored PDF"
        in change_validation_flat,
        "change validation lost its official-source or no-PDF-CI boundary",
    )
    require(
        "identify the official source" in quality_review_flat
        and "Keep TrackTemplate policy different from the external "
        "normative reference" in quality_review_flat
        and "Keep evidence that the reviewer examined the named logical unit"
        in quality_review_flat,
        "quality review lost the policy/source/assessment distinction",
    )

    routine_routes = {
        "tracktemplate-context-recovery": (
            "Do not read the ASD-STE100 PDF during usual recovery"
        ),
        "tracktemplate-continue": (
            "Do not read the external PDF during a usual continuation cycle"
        ),
        "tracktemplate-technical-lead": (
            "Do not read the external PDF during usual technical-lead work"
        ),
    }
    for name, boundary in routine_routes.items():
        skill_text = read(SKILLS_ROOT / name / "SKILL.md")
        require(
            "tracktemplate-documentation-review" in skill_text
            and boundary in semantic_text(skill_text),
            name + " lost ASD-STE100 specialist routing",
        )


def main() -> None:
    require(SKILLS_ROOT.is_dir(), "missing .agents/skills directory")

    skill_directories = sorted(path for path in SKILLS_ROOT.iterdir() if path.is_dir())
    require(skill_directories, "no repository skills found")

    names: list[str] = []
    markdown_documents: list[Path] = [
        AGENTS,
        WORKFLOWS,
        PRODUCT_VISION,
        ENGINEERING_POLICY,
        TERMINOLOGY,
    ]

    for directory in skill_directories:
        skill_file = directory / "SKILL.md"
        text = read(skill_file)
        fields = parse_frontmatter(skill_file, text)
        name = fields["name"]
        description = fields["description"]

        require(
            1 <= len(name) <= 64,
            f"skill name must contain between 1 and 64 characters: {name!r}",
        )
        require(
            1 <= len(description) <= 1024,
            (
                f"{skill_file.relative_to(ROOT)} description must contain "
                "between 1 and 1024 characters"
            ),
        )
        require(VALID_NAME_RE.fullmatch(name) is not None, f"invalid skill name: {name}")
        require(
            name == directory.name,
            f"skill name {name!r} does not match directory {directory.name!r}",
        )
        validate_skill_line_budget(skill_file, text)
        unexpected_entries = sorted(
            path.name
            for path in directory.iterdir()
            if path.name not in ALLOWED_SKILL_ENTRIES
        )
        require(
            not unexpected_entries,
            (
                f"{directory.relative_to(ROOT)} has unsupported skill entries: "
                + ", ".join(unexpected_entries)
            ),
        )
        validate_skill_resource_routing(directory, text)
        validate_progress_skill_metadata(directory, name)
        names.append(name)
        markdown_documents.extend(sorted(directory.rglob("*.md")))

    require(len(names) == len(set(names)), "duplicate skill names")

    workflows = read(WORKFLOWS)
    validate_progress_delivery_structure()
    ide_skill = read(
        SKILLS_ROOT / "tracktemplate-ide-workspace-alignment" / "SKILL.md"
    )
    continuation = read(SKILLS_ROOT / "tracktemplate-continue" / "SKILL.md")
    validate_ide_workspace_alignment_contract(ide_skill, continuation)
    validate_ide_workspace_alignment_mutations(ide_skill, continuation)
    validate_continue_invocation_policy(workflows)
    validate_vision_led_workflows(workflows)
    validate_documentation_profile_routing(names, workflows)
    registered_headings = REGISTER_HEADING_RE.findall(workflows)
    registered_paths = REGISTER_PATH_RE.findall(workflows)
    path_names = [name for _, name in registered_paths]

    require(
        len(registered_headings) == len(set(registered_headings)),
        "duplicate skill heading in reference/AGENT_WORKFLOWS.md",
    )
    require(
        len(path_names) == len(set(path_names)),
        "duplicate skill path in reference/AGENT_WORKFLOWS.md",
    )
    require(
        set(registered_headings) == set(names),
        "skill register headings do not match .agents/skills directories",
    )
    require(
        set(path_names) == set(names),
        "skill register paths do not match .agents/skills directories",
    )

    for path_text, name in registered_paths:
        expected = ROOT / path_text
        require(expected.is_file(), f"registered skill path is missing: {path_text}")
        require(
            expected.parent.name == name,
            f"registered skill path/name mismatch: {path_text}",
        )

    agents = read(AGENTS)
    require(
        "reference/AGENT_WORKFLOWS.md" in agents,
        "AGENTS.md does not route to reference/AGENT_WORKFLOWS.md",
    )
    require(
        "reference/ENGINEERING_POLICY.md" in agents,
        "AGENTS.md does not route to reference/ENGINEERING_POLICY.md",
    )
    require(
        "reference/current/PHASE_EVIDENCE.md" in agents,
        "AGENTS.md does not route to the fixed current phase record",
    )
    require(
        "reference/PRODUCT_VISION.md" in agents,
        "AGENTS.md does not route to the canonical Product Vision",
    )
    require(
        100 <= len(agents.splitlines()) <= 140,
        "AGENTS.md must remain within its 100-140 line always-on budget",
    )
    require(
        len(agents.encode("utf-8")) < 12 * 1024,
        "AGENTS.md exceeded its 12 KiB always-on budget",
    )
    for name in names:
        require(
            f"${name}" in workflows,
            f"reference/AGENT_WORKFLOWS.md lacks invocation for ${name}",
        )
        require(
            f"${name}" not in agents,
            f"AGENTS.md duplicates specialist routing for ${name}",
        )

    validate_links(sorted(set(markdown_documents)))
    print("TrackTemplate agent-guidance validation passed")


if __name__ == "__main__":
    main()
