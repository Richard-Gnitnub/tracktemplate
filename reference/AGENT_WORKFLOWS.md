# Agent Workflows

Status: **repository guidance; owns agent-skill structure and maintenance only.**

## Purpose

This document separates four different kinds of project control:

| Layer | Owns | Must not own |
| --- | --- | --- |
| `AGENTS.md` | Short, always-on, repository-wide invariants and routing | Detailed repository history, long command catalogues, live progress or task-specific procedure |
| Canonical `reference/` documents | Project requirements, architecture, policy, evidence interpretation and live status in their named domains | Agent-product implementation details that do not change project policy |
| `.agents/skills/*/SKILL.md` | Repeatable, task-specific workflows and review methods | Project authority, accepted requirements, phase status or automatic acceptance |
| Tests and scripts | Deterministic checks and safe automation | Subjective project decisions or unreviewed file rewriting |

Skills complement `AGENTS.md`; they do not replace it. A skill may link to a
canonical document, but it must not copy enough of that document to become a
second policy owner.

## Instruction budget

Codex combines repository instruction files and applies a finite default byte
budget. Keep the root `AGENTS.md` comfortably below that limit so nested
instructions still have room.

Project target:

- aim for no more than **16 KiB** for the root `AGENTS.md`;
- treat **24 KiB** as a review threshold requiring deliberate justification;
- move repeatable procedures to skills and detailed facts to their canonical
  reference documents;
- do not raise the Codex instruction limit merely to avoid removing duplication.

Measure with:

```bash
wc -c AGENTS.md
```

## Current skill register

### `tracktemplate-documentation-review`

Path: `.agents/skills/tracktemplate-documentation-review/SKILL.md`

Use it when creating, reviewing, shortening or reorganising TrackTemplate
Markdown documentation, particularly where the change involves:

- duplicated status or technical explanation;
- verbose or repetitive prose;
- unclear document ownership;
- live status recorded outside `reference/PROJECT_PLAN.md`;
- material copied from another canonical owner;
- conclusions or operative requirements buried beneath background;
- frozen evidence, licensing, provenance or controlled wording;
- documentation that needs restructuring without changing its meaning.

Use this skill while making a material documentation change.

### `tracktemplate-change-validation`

Path: `.agents/skills/tracktemplate-change-validation/SKILL.md`

Use it to select, run and report the proportionate validation required for a
proposed or completed TrackTemplate change. It distinguishes:

- standalone parsing and analytical evidence;
- qualified FreeCAD document checks;
- real-GUI presentation and operator-workflow evidence;
- persistence, migration, rollback and recovery evidence;
- exact geometry and exporter evidence;
- performance measurement;
- provenance, licensing and output-clearance boundaries.

Use this skill after implementation or documentation editing and before the
final quality review whenever the applicable checks or evidence boundary are
not trivial.

### `tracktemplate-quality-review`

Path: `.agents/skills/tracktemplate-quality-review/SKILL.md`

Use it to review the complete relevant diff for:

- unnecessary complexity or speculative abstractions;
- duplicated authoritative logic;
- broad rewrites unrelated to the request;
- misleading, repetitive or stale comments;
- hidden failures or weakened diagnostics;
- behavioural drift in geometry, topology, tolerances, ordering, persistence,
  transactions or export;
- accidental public API, stored-state or compatibility changes;
- performance regressions and unsupported validation claims.

Use this skill before reporting completion of a non-trivial source or
documentation change. It judges the change using the available evidence; it
does not replace the validation skill.

All three skills are deliberately instruction-only. They do not perform
automatic cleanup, assign an “AI authenticity” score, ban phrases or rewrite
files in bulk. Those mechanisms can create false positives and remove legitimate
FreeCAD, railway, evidential or licensing context.

## Invocation

In Codex CLI or the IDE extension, invoke the relevant skill explicitly:

```text
$tracktemplate-documentation-review
```

```text
$tracktemplate-change-validation
```

```text
$tracktemplate-quality-review
```

Codex may also select a skill implicitly when the request clearly matches its
description.

Prefer explicit invocation for:

- release, phase-gate or authority-changing reviews;
- large refactors or architectural changes;
- persistence, migration, export, licensing or performance work;
- substantial documentation restructuring;
- changes involving canonical ownership, frozen evidence, provenance or
  validator-controlled wording.

For geometry, topology, persistence, migration, export, performance, provenance
or authority-changing work, `$tracktemplate-change-validation` may also be used
before implementation to define the required proof boundary. This does not
replace post-implementation validation.

## Normal workflow order

Validation determines what the evidence proves. Quality review determines
whether the implementation and scope are acceptable given that evidence.

For a source change:

```text
Implementation
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For a material documentation change:

```text
$tracktemplate-documentation-review
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For a review-only request, use `$tracktemplate-quality-review`. Add
`$tracktemplate-change-validation` when the review must determine whether the
available evidence supports the change or which checks remain outstanding.

## Agent-guidance validation

After changing `AGENTS.md`, `reference/AGENT_WORKFLOWS.md` or a repository skill,
run:

```bash
.venv/bin/python tests/validate_agent_guidance.py
```

The validator checks skill frontmatter, directory/name agreement, local links,
the skill register and root routing. It does not judge whether a skill's
instructions are substantively correct or whether project validation passed.

## Skill maintenance rules

- Give each skill one repeatable job and a concise trigger description.
- Default to instruction-only. Add scripts only when the task is deterministic,
  reviewable, safe on a dirty working tree and materially better than existing
  project tools.
- Never import executable code from a third-party skill without inspecting its
  licence, behaviour, dependencies and file-system scope.
- Do not add MCP merely because a skill exists. MCP is appropriate only when the
  workflow needs controlled access to an external system or live data source.
- Link to the canonical project document rather than copying its detailed rules.
- Treat new skill behaviour as repository guidance: review it like code, keep the
  diff narrow and run the documentation, link and agent-guidance controls.
- Keep the skill register aligned with the directories under `.agents/skills/`.
- Do not allow two skills to claim the same primary responsibility without
  clearly defining their order and boundary.
- When a skill uncovers a durable project lesson, append it to
  `reference/LEARNING_FROM_EXPERIENCE.md` only after the lesson has evidence and
  leads to an accepted reusable adaptation.

A clean implementation or prose style is not enough for completion. Railway
correctness, recoverability, evidence quality and project authority remain
controlling.
