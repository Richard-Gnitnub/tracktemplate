#!/usr/bin/env python3
"""Fail-closed validation for TrackTemplate Codex agent guidance."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
WORKFLOWS = ROOT / "reference" / "AGENT_WORKFLOWS.md"
AGENTS = ROOT / "AGENTS.md"

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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: Path) -> str:
    require(path.is_file(), f"missing required agent guidance: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


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


def main() -> None:
    require(SKILLS_ROOT.is_dir(), "missing .agents/skills directory")

    skill_directories = sorted(path for path in SKILLS_ROOT.iterdir() if path.is_dir())
    require(skill_directories, "no repository skills found")

    names: list[str] = []
    markdown_documents: list[Path] = [AGENTS, WORKFLOWS]

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
        names.append(name)
        markdown_documents.extend(sorted(directory.rglob("*.md")))

    require(len(names) == len(set(names)), "duplicate skill names")

    workflows = read(WORKFLOWS)
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
