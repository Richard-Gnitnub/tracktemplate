# Agent Workflows

Status: **repository guidance; owns agent-skill structure and maintenance only.**

## Purpose

This document separates four different kinds of project control:

| Layer                            | Owns                                                                                                       | Must not own                                                                                   |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `AGENTS.md`                      | Short, always-on, repository-wide invariants and routing                                                   | Detailed repository history, long command catalogues, live progress or task-specific procedure |
| Canonical `reference/` documents | Project requirements, architecture, policy, evidence interpretation and live status in their named domains | Agent-product implementation details that do not change project policy                         |
| `.agents/skills/*/SKILL.md`      | Repeatable, task-specific workflows and review methods                                                     | Project authority, accepted requirements, phase status or automatic acceptance                 |
| Tests and scripts                | Deterministic checks and safe automation                                                                   | Subjective project decisions or unreviewed file rewriting                                      |

Skills complement `AGENTS.md`; they do not replace it. A skill may link to a canonical document, but it must not copy enough of that document to become a second policy owner.

## Instruction budget

Codex combines repository instruction files and applies a finite default byte budget. Keep the root `AGENTS.md` comfortably below that limit so nested instructions still have room.

Project target:

* aim for no more than **16 KiB** for the root `AGENTS.md`;
* treat **24 KiB** as a review threshold requiring deliberate justification;
* move repeatable procedures to skills and detailed facts to their canonical reference documents;
* do not raise the Codex instruction limit merely to avoid removing duplication.

Measure with:

```bash
wc -c AGENTS.md
```

## Current skill register

### `tracktemplate-quality-review`

Path: `.agents/skills/tracktemplate-quality-review/SKILL.md`

Use it to review a proposed or completed TrackTemplate source change for:

* unnecessary complexity or speculative abstractions;
* duplicated authoritative logic;
* broad rewrites unrelated to the request;
* misleading, repetitive or stale comments;
* hidden failures or weakened diagnostics;
* behavioural drift in geometry, topology, tolerances, ordering, persistence, transactions or export;
* accidental public API, stored-state or compatibility changes;
* performance regressions and unsupported validation claims.

Use this skill before reporting completion of a non-trivial source change. It may also provide the final complete-diff review after a material documentation change.

### `tracktemplate-documentation-review`

Path: `.agents/skills/tracktemplate-documentation-review/SKILL.md`

Use it when creating, reviewing, shortening or reorganising TrackTemplate Markdown documentation, particularly where the change involves:

* duplicated status or technical explanation;
* verbose or repetitive prose;
* unclear document ownership;
* live status recorded outside `reference/PROJECT_PLAN.md`;
* material copied from another canonical owner;
* conclusions or operative requirements buried beneath background;
* frozen evidence, licensing, provenance or controlled wording;
* documentation that needs restructuring without changing its meaning.

Use this skill during documentation editing. For a material documentation change, follow it with `tracktemplate-quality-review` before reporting completion.

Both skills are deliberately instruction-only. They do not perform automatic cleanup, assign an “AI authenticity” score, ban phrases or rewrite files in bulk. Those mechanisms can create false positives and remove legitimate FreeCAD, railway, evidential or licensing context.

## Invocation

In Codex CLI or the IDE extension, invoke the relevant skill explicitly:

```text
$tracktemplate-quality-review
```

```text
$tracktemplate-documentation-review
```

Codex may also select a skill implicitly when the request clearly matches its description.

Prefer explicit invocation for:

* release, phase-gate or authority-changing reviews;
* large refactors or architectural changes;
* persistence, export, licensing or performance work;
* substantial documentation restructuring;
* changes involving canonical ownership, frozen evidence, provenance or validator-controlled wording.

## Skill maintenance rules

* Give each skill one repeatable job and a concise trigger description.
* Default to instruction-only. Add scripts only when the task is deterministic, reviewable, safe on a dirty working tree and materially better than existing project tools.
* Never import executable code from a third-party skill without inspecting its licence, behaviour, dependencies and file-system scope.
* Do not add MCP merely because a skill exists. MCP is appropriate only when the workflow needs controlled access to an external system or live data source.
* Link to the canonical project document rather than copying its detailed rules.
* Treat new skill behaviour as repository guidance: review it like code, keep the diff narrow and run the documentation and link controls.
* Keep the skill register aligned with the directories under `.agents/skills/`.
* Do not allow two skills to claim the same primary responsibility without clearly defining their order and boundary.
* When a skill uncovers a durable project lesson, append it to `reference/LEARNING_FROM_EXPERIENCE.md` only after the lesson has evidence and leads to an accepted reusable adaptation.

## Documentation-review result

A documentation-skill review should report:

1. **Document classification and canonical responsibility.**
2. **Changes made or proposed**, with the reason for each material change.
3. **Material moved or linked**, naming its canonical owner.
4. **Material proposed for removal requiring explicit review** because it could affect historical, legal, safety, licensing or evidential meaning.
5. **Validation completed**, including local link checks and any validator-required wording reviewed.
6. **Residual uncertainty**, including evidence or authority still required.

Concise prose alone is not sufficient. Historical meaning, evidence boundaries, controlled terminology and canonical ownership must remain intact.

## Quality-review result

A quality-skill review should report:

1. **Decision:** pass, pass with findings, or blocked.
2. **Confirmed defects:** ordered by impact, with exact paths or symbols and supporting evidence.
3. **Unnecessary complexity:** only where its lack of purpose has been established.
4. **Behavioural risks:** including the affected architectural and railway boundaries.
5. **Checks completed:** commands, inspections and evidence actually reviewed.
6. **Checks still required:** especially real-GUI FreeCAD, export, performance, provenance, licensing or compatibility evidence.
7. **Scope check:** confirmation that unrelated files and behaviour remained unchanged, or an explicit exception.

A clean implementation or prose style is not enough for a pass. Railway correctness, recoverability, evidence quality and project authority remain controlling.
