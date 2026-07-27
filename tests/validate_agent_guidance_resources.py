#!/usr/bin/env python3
"""Validate fail-closed routing for bundled skill resources."""

from __future__ import annotations

import tempfile
from pathlib import Path

import validate_agent_guidance as guidance


def write_file(path: Path, content: str = "fixture\n") -> None:
    """Write one disposable resource fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def require_failure(action, expected_fragment: str) -> None:
    """Require an assertion containing the expected diagnostic."""
    try:
        action()
    except AssertionError as error:
        if expected_fragment not in str(error):
            raise AssertionError(
                "unexpected validation diagnostic: {!r}".format(str(error))
            ) from error
    else:
        raise AssertionError(
            "validation unexpectedly accepted {!r}".format(expected_fragment)
        )


def validate_direct_resource_routing() -> None:
    """Exercise direct, orphaned, indirect and nested resource routes."""
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-skill-routing-"
    ) as temporary:
        fixture_root = Path(temporary)
        skill_directory = fixture_root / "skill"
        write_file(skill_directory / "references" / "schema.json")
        write_file(skill_directory / "scripts" / "check.py")
        write_file(skill_directory / "assets" / "template" / "icon.svg")

        complete_routes = "\n".join(
            (
                "[Schema](references/schema.json)",
                "[Check script](scripts/check.py)",
                "[Icon asset](assets/template/icon.svg)",
            )
        )
        guidance.validate_skill_resource_routing(
            skill_directory,
            complete_routes,
            fixture_root,
        )

        for orphan_path in (
            "references/schema.json",
            "scripts/check.py",
            "assets/template/icon.svg",
        ):
            require_failure(
                lambda path=orphan_path: guidance.validate_skill_resource_routing(
                    skill_directory,
                    complete_routes.replace(
                        next(
                            line
                            for line in complete_routes.splitlines()
                            if path in line
                        ),
                        "",
                    ),
                    fixture_root,
                ),
                orphan_path,
            )

        require_failure(
            lambda: guidance.validate_skill_resource_routing(
                skill_directory,
                "[Asset directory](assets/)",
                fixture_root,
            ),
            "assets/template/icon.svg",
        )

    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-skill-indirect-routing-"
    ) as temporary:
        fixture_root = Path(temporary)
        skill_directory = fixture_root / "skill"
        write_file(
            skill_directory / "references" / "primary.md",
            "[Secondary](secondary.md)\n",
        )
        write_file(skill_directory / "references" / "secondary.md")
        require_failure(
            lambda: guidance.validate_skill_resource_routing(
                skill_directory,
                "[Primary](references/primary.md)",
                fixture_root,
            ),
            "references/secondary.md",
        )

    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-skill-nested-reference-"
    ) as temporary:
        fixture_root = Path(temporary)
        skill_directory = fixture_root / "skill"
        write_file(skill_directory / "references" / "nested" / "rules.md")
        require_failure(
            lambda: guidance.validate_skill_resource_routing(
                skill_directory,
                "[Rules](references/nested/rules.md)",
                fixture_root,
            ),
            "references/nested/rules.md",
        )


def validate_line_budget() -> None:
    """Exercise the requirement that each skill remain below 500 lines."""
    with tempfile.TemporaryDirectory(
        prefix="tracktemplate-skill-line-budget-"
    ) as temporary:
        fixture_root = Path(temporary)
        skill_file = fixture_root / "skill" / "SKILL.md"
        guidance.validate_skill_line_budget(
            skill_file,
            "\n".join(
                "line" for _ in range(guidance.MAX_SKILL_LINES - 1)
            ),
            fixture_root,
        )
        require_failure(
            lambda: guidance.validate_skill_line_budget(
                skill_file,
                "\n".join(
                    "line" for _ in range(guidance.MAX_SKILL_LINES)
                ),
                fixture_root,
            ),
            "must remain below 500 lines",
        )


def main() -> None:
    validate_direct_resource_routing()
    validate_line_budget()
    print("TrackTemplate skill resource-routing validation passed")


if __name__ == "__main__":
    main()
