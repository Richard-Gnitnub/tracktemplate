# Agent Workflows

Status: **repository guidance; owns agent-skill structure and maintenance only.**

## Purpose

This document separates five different kinds of project control:

| Layer | Owns | Must not own |
| --- | --- | --- |
| `AGENTS.md` | Short, always-on, repository-wide invariants and routing | Detailed repository history, long command catalogues, live progress or task-specific procedure |
| Canonical `reference/` documents | Project requirements, architecture, policy, evidence interpretation and live status in their named domains | Agent-product implementation details that do not change project policy |
| `.agents/skills/*/SKILL.md` | Repeatable, task-specific workflows and review methods | Project authority, accepted requirements, phase status or automatic acceptance |
| Tests and scripts | Deterministic checks and safe automation | Subjective project decisions or unreviewed file rewriting |
| Git history and diffs | Source-state and change evidence | Requirements, rationale, acceptance or current project status |

Skills complement `AGENTS.md`; they do not replace it. A skill may link to a
canonical document, but it must not copy enough of that document to become a
second policy owner.

## Session continuity

At the start of resumed work, reconstruct authority in this order:

1. repository and scoped `AGENTS.md`;
2. `reference/PROJECT_PLAN.md`;
3. the canonical owner of the affected subject;
4. the named open-phase evidence record where relevant; and
5. source, tests, Git history and diffs as implementation evidence.

Use `$tracktemplate-context-recovery` when a new session, compaction,
interrupted handoff or unfamiliar dirty worktree makes that reconstruction
material. Do not infer a requirement or accepted decision from a diff, commit
message, branch name, test expectation or implementation comment.

Before ending work, put each accepted durable fact in its existing canonical
owner. Do not create generic per-task plans or chronicles that duplicate
`PROJECT_PLAN.md`, the open-phase evidence record or another canonical
document. A task that remains incomplete is reported as incomplete, with its
working-tree state, evidence already run, unresolved decisions and next safe
check made explicit.

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

### `tracktemplate-context-recovery`

Path: `.agents/skills/tracktemplate-context-recovery/SKILL.md`

Use it to resume TrackTemplate work after context may have been lost. It reloads
only the task-relevant current phase, subject authority and evidence before
inspecting the working tree as implementation state. It uses hot, warm and cold
context, an authority-ranked loss check and a transient context packet; it does
not turn Git history, diffs, tests or conversation summaries into project
authority.

### `tracktemplate-freecad-addon-research`

Path: `.agents/skills/tracktemplate-freecad-addon-research/SKILL.md`

Use it to answer a bounded FreeCAD Addon question from the current official
Addon Academy and related first-party sources. It records source freshness,
distinguishes guidance from runtime fact, and maps the result to the owning
TrackTemplate document and ontology boundary without turning upstream advice
into a project decision.

### `tracktemplate-license-analysis`

Path: `.agents/skills/tracktemplate-license-analysis/SKILL.md`

Use it to analyse exact licence, provenance and rights evidence for source,
dependencies, data, media, packages and generated output. It separates
copyright licensing from data, design, patent, trade-mark, contract and
contributor-authority questions, preserves unknowns and routes legal
interpretation to professional review. It cannot itself confer
`project-cleared` status or legal clearance.

### `tracktemplate-python-writing`

Path: `.agents/skills/tracktemplate-python-writing/SKILL.md`

Use it whenever creating or materially editing Python or FCMacro source. It
applies PEP 8 and PEP 257 as the writing baseline while preserving railway
behaviour, qualified FreeCAD compatibility, frozen B14/B15 evidence, public and
persisted identifiers, diagnostics and narrow diffs.

### `tracktemplate-api-design`

Path: `.agents/skills/tracktemplate-api-design/SKILL.md`

Use it before adding or changing a supported Python API, application command,
FreeCAD boundary, persistence/package schema, exporter contract or accepted
HTTP interface. It defines consumers, units, identities, errors, side effects,
compatibility, migration and evidence before implementation, without turning
internal helpers into public APIs or assuming a REST service exists.

### `tracktemplate-task-automation`

Path: `.agents/skills/tracktemplate-task-automation/SKILL.md`

Use it when a stable repeated development, validation, evidence or packaging
workflow creates measurable operator or agent toil. It prefers existing tools,
keeps judgement and approvals explicit, and requires deterministic,
idempotent, recoverable evidence. It does not authorise unattended schedulers,
watchers, hooks, external services, destructive mutation or new dependencies.

### `tracktemplate-simplify`

Path: `.agents/skills/tracktemplate-simplify/SKILL.md`

Use it to run a bounded simplification pass over source, tests, documentation or
agent guidance after establishing the preserved behaviour and evidence
boundary. It removes only proven accidental complexity and routes material
edits through the applicable writing, validation and quality skills. It does
not authorise changed railway behaviour, weaker validation, frozen-identifier
migration or broad cleanup.

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

### `tracktemplate-documentation-alignment`

Path: `.agents/skills/tracktemplate-documentation-alignment/SKILL.md`

Use it to audit documentation claims against current repository authority,
implementation and validation evidence after source, structure, phase, workflow
or agent-guidance changes. It classifies verified, stale, contradictory,
duplicated, orphaned and unverified claims before making narrow corrections.
It does not rewrite accepted requirements to match code, update frozen history
to current state or perform automatic corpus cleanup.

### `tracktemplate-changelog`

Path: `.agents/skills/tracktemplate-changelog/SKILL.md`

Use it to add or derive concise user-facing unreleased notes and to prepare a
version section only after the project-owner release gate and version decision.
It verifies Git-discovered candidates against canonical authority and completed
evidence; it does not duplicate live phase status, infer acceptance, edit
version files, commit, tag, push or publish.

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
not trivial. Invoke it immediately when a selected check fails so the raw
failure is preserved and classified under `reference/TESTING_POLICY.md` before
retained fixes.

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

Use this skill as the staff-level, read-only first review before reporting
completion of a non-trivial source or documentation change, and after a
classified failed-test repair. It judges the change using the available
evidence; it does not replace the validation skill.

All twelve skills are deliberately instruction-only. They do not perform
automatic cleanup, assign an “AI authenticity” score, ban phrases or rewrite
files in bulk. Those mechanisms can create false positives and remove legitimate
FreeCAD, railway, evidential or licensing context.

## Invocation

In Codex CLI or the IDE extension, invoke the relevant skill explicitly:

```text
$tracktemplate-context-recovery
```

```text
$tracktemplate-freecad-addon-research
```

```text
$tracktemplate-license-analysis
```

```text
$tracktemplate-python-writing
```

```text
$tracktemplate-api-design
```

```text
$tracktemplate-task-automation
```

```text
$tracktemplate-simplify
```

```text
$tracktemplate-documentation-review
```

```text
$tracktemplate-documentation-alignment
```

```text
$tracktemplate-changelog
```

```text
$tracktemplate-change-validation
```

```text
$tracktemplate-quality-review
```

Codex may also select a skill implicitly when the request clearly matches its
description.

Use `$tracktemplate-freecad-addon-research` before the source or documentation
sequence when work depends on current FreeCAD Addon guidance. Its output is
research evidence, not implementation, validation or project acceptance.

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
$tracktemplate-python-writing during Python implementation
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For an API or schema change:

```text
$tracktemplate-api-design
    ↓
$tracktemplate-freecad-addon-research when the boundary is FreeCAD-specific
    ↓
$tracktemplate-python-writing during implementation
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For retained task automation:

```text
$tracktemplate-task-automation
    ↓
$tracktemplate-python-writing
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

For a documentation-alignment task:

```text
$tracktemplate-documentation-alignment
    ↓
$tracktemplate-documentation-review during material corrections
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For a bounded simplification:

```text
$tracktemplate-simplify
    ↓
$tracktemplate-python-writing or $tracktemplate-documentation-review
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For a material changelog update:

```text
$tracktemplate-changelog
    ↓
$tracktemplate-documentation-review
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For a licence, provenance or output-use assessment:

```text
$tracktemplate-license-analysis
    ↓
$tracktemplate-documentation-review when canonical records change
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For a review-only request, use `$tracktemplate-quality-review`. Add
`$tracktemplate-change-validation` when the review must determine whether the
available evidence supports the change or which checks remain outstanding.

## Staff review and failed-test flow

The normal source and documentation sequences above are the new-change paths.
Their first staff-review pass is read-only. Prefer a fresh reviewer or session
when available and proportionate; provide the request, canonical requirements,
complete diff, raw validation evidence and known unperformed checks. Do not
prime the reviewer with the intended verdict. Disclose same-agent review or
another independence limitation. After an adverse verdict, separate authorised
remediation from that pass, rerun affected validation and review the resulting
complete diff again.

For a failed test:

```text
preserve raw failure and identify the canonical contract
    ↓
$tracktemplate-change-validation — classify under TESTING_POLICY.md
    ↓
repair only the classified boundary and rerun the original proof
    ↓
$tracktemplate-quality-review — review source, tests and evidence
```

Do not treat a failed test as automatic authority to change production code or
the test. `reference/TESTING_POLICY.md` owns the classifications and
test/oracle-change gate; validation owns evidence and classification; quality
review owns staff-level scope and implementation judgement.

## External method and skill admission

External skill repositories are research inputs, not inherited project
authority. Before installing, copying or adapting one:

1. pin and record the reviewed revision and licence;
2. inspect its complete triggered instructions, hooks, scripts, dependencies,
   file-system scope and external actions;
3. compare its ownership model, terminology, approval gates and validation
   claims with `AGENTS.md` and the canonical documents;
4. choose deliberately between adapting an idea, linking to upstream, vendoring
   reviewed content, installing a plugin or rejecting it;
5. preserve required notices for copied or substantially adapted material;
6. give each admitted local skill one responsibility and remove or bound any
   overlap with an existing skill; and
7. run the repository guidance validator and the normal documentation and
   quality reviews.

Do not bulk-copy a catalogue, enable repository-writing hooks or add a runtime
dependency merely because upstream describes it as universal or ready to use.
An upstream update is a new review boundary; it does not flow automatically
into this repository.

### Sources reviewed for this policy

The following sources were reviewed on 2026-07-27. No upstream file, hook,
script or runtime package was copied or installed by this review.

| Source and reviewed revision | Classification | TrackTemplate decision |
| --- | --- | --- |
| [`reidemeister94/development-skills`](https://github.com/reidemeister94/development-skills/tree/92922f58f037191f2ccc909a69cbe297fc49efae), `92922f58f037191f2ccc909a69cbe297fc49efae`, MIT | Coding-agent workflow plugin with session-start and edit-time hooks | Adapt the useful standards-first, durable-rationale and resume principles through the existing authority map and local recovery skill. Adapt its documentation-drift audit, changelog curation and bounded simplification ideas through the corresponding local skills, while preserving TrackTemplate's canonical owners, frozen evidence and release gates. Do not install its router, auto-formatter, mutation hooks, `docs/plans/` or `docs/chronicles/` model, and do not grant changelog or simplification work automatic commit, tag, bulk-rewrite or release authority. |
| [`seb1n/awesome-ai-agent-skills`](https://github.com/seb1n/awesome-ai-agent-skills/tree/a6c8c0ef3c240faefe1b0b5cabe1567beaea60fd), `a6c8c0ef3c240faefe1b0b5cabe1567beaea60fd`, MIT | Broad catalogue of generic instruction skills | Use only as a discovery source and admit each idea after project-specific review. Adapt stable-workflow automation without generic schedulers, watchers, destructive moves or new dependencies; adapt licence analysis through the existing fail-closed source/data/media/output controls without categorical legal conclusions; and adapt API contract design to Python, FreeCAD, persistence, package and exporter boundaries without assuming REST. Generic code review overlaps the local quality skill, while embedding/vector retrieval infrastructure remains unjustified. |
| [`pydantic/pydantic-ai`](https://github.com/pydantic/pydantic-ai/tree/ed0f40c0e5061722f7d9f579ed7efff1b74e3ea5), `ed0f40c0e5061722f7d9f579ed7efff1b74e3ea5`, MIT | Python agent framework repository with root/scoped instructions and project-specific skills | Adapt its context-first, responsibility-to-project and patch-as-evidence patterns. TrackTemplate already supplies the corresponding authority map and local skills; add scoped `AGENTS.md` only where a directory has genuinely different rules. Do not add the Pydantic AI package as a TrackTemplate or FreeCAD runtime dependency without a separately approved in-product agent capability and compatibility, security, data, cost and validation evidence. |

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
