# Agent Workflows

Status: **repository guidance. It owns only agent-skill structure and maintenance.**

## Purpose

This document separates five different kinds of project control:

| Layer | Owns | Must not own |
| --- | --- | --- |
| `AGENTS.md` | Short, always-on, repository-wide invariants and routing | Detailed repository history, long command catalogues, live progress, or task-specific procedure |
| Canonical `reference/` documents | The applicable project requirement set, architecture, policy, and evidence interpretation in each named domain | Agent-product implementation details that do not change project policy |
| `.agents/skills/*/SKILL.md` | Repeatable, task-specific workflows and review methods | Project authority, the accepted requirement set, phase status, or automatic acceptance |
| Tests and scripts | Deterministic checks and safe automation | Subjective project decisions or unreviewed file rewriting |
| Git history and diffs | Source-state and change evidence | The applicable requirement set, rationale, acceptance, or current project status |

Skills complement `AGENTS.md`. They do not replace it. A skill can link to a
canonical document. It must not copy enough of that document to become a
second policy owner.

[`PRODUCT_VISION.md`](PRODUCT_VISION.md) owns product purpose, programme
horizons, and Core-migration completion. Architecture, plan, evidence, skills,
and source apply that direction within their narrower authority. None can
become an alternative product-vision owner without an owner decision.

## Session continuity

At the start of resumed work, reconstruct authority in this order:

1. Read the repository and applicable `AGENTS.md` files.
2. Read `reference/PRODUCT_VISION.md` and the accepted architectural invariants.
3. Read `reference/PROJECT_PLAN.md` for the authorised programme, phase, and exits.
4. Read `reference/current/PHASE_EVIDENCE.md` and the current JSON registers.
5. Read the canonical owner of the affected subject.
6. Use source, tests, Git history, and diffs as implementation evidence.

Use `$tracktemplate-context-recovery` when one of these events makes
reconstruction material: a new session, compaction, interrupted handoff, or
unfamiliar dirty worktree. Do not infer an applicable
requirement or accepted decision from implementation evidence. This evidence
includes a diff, commit message, branch name, test expectation, or comment.

Before an explicit transfer to a new chat, usage reset, or long pause, use
`$tracktemplate-handoff`. It writes one temporary navigation packet outside the
repository. The receiving session uses `$tracktemplate-context-recovery` with
that packet. It rechecks live repository, pull-request, and CI state. The
packet does not become project authority, current-phase evidence, or a durable
record.

Before ending work, put each accepted durable fact in its existing canonical
owner. Do not create generic per-task plans or chronicles that duplicate a
canonical document. This includes `PROJECT_PLAN.md` and the fixed current-phase
records. Report an incomplete task as incomplete. State its working-tree state,
completed evidence, unresolved decisions, and next safe check.

Read the
[procedure for visible recovery state](RECOVERY_AND_BACKUP.md#visible-recovery-state).
Use it for Git recovery and handoff state. A context packet gives the route to
named Git state. It is not planned preservation. Do not give the recovery gate
a complete result before the recovery workflow reconciles all stashes.

Before a worktree retirement, read the
[worktree retirement procedure](RECOVERY_AND_BACKUP.md#worktree-retirement).
During recovery, the implementing agent makes a local-state inventory. The
agent finds the canonical owner of each item. During workspace alignment,
the implementing agent makes sure that no person or process uses the worktree.
The agent also makes sure that a different location contains person-owned data.

The retirement audit returns the exact Git identity. The retirement audit
returns the SHA-256 of the local-state inventory. The retirement audit examines
the retirement plan.

The pull-request state `MERGED` gives no removal authority. Tracked cleanliness
gives no removal authority. The implementing agent stops if the retirement
plan has ambiguous or uniquely owned state. The agent also stops if the
preservation audit does not have a complete result.

## Instruction budget

Codex combines repository instruction files and applies a finite default byte
budget. Keep the root `AGENTS.md` comfortably below that limit so nested
instructions still have room.

Project target:

- Keep the root `AGENTS.md` at approximately **100–140 lines** and below **12 KiB**.
- Move repeatable procedures to skills and detailed facts to their canonical
  reference documents.
- Do not raise the Codex instruction limit only to retain duplicated wording.

Measure with:

```bash
wc -c AGENTS.md
```

## Progressive disclosure and composition

TrackTemplate uses the three skill-loading layers deliberately:

1. **Discovery metadata:** `name` and `description` state what the skill does
   and when it activates. Include concrete project and task concepts. Add a
   negative routing limit only where a real routing overlap exists.
2. **Triggered procedure:** `SKILL.md` contains the cohesive workflow,
   load-bearing gotchas and resource-selection rules needed on every activation.
   Keep it below 500 lines and avoid generic knowledge the agent already has.
3. **Conditional resources:** focused references, deterministic scripts and
   output assets load only when their named condition applies. Link every file
   directly from `SKILL.md`. A directory link or another resource is not a
   substitute. Keep references one filesystem level deep.

The project uses the portable `name` and `description` frontmatter core. The
current Codex validator supports this core. Do not add optional Agent Skills
fields unless the active client and a project need justify them.

A skill packages a repeatable procedure, not one tool call. Compose several
skills when a task crosses coherent responsibilities. Do not mirror each CLI,
MCP endpoint, or script as a separate skill. Put deterministic operations in
tested scripts. Keep the bounded scope, evidence interpretation, and authority
decisions visible to the agent and project owner.

## TT-DOC-001 workflow integration

The canonical
[TrackTemplate Technical Documentation Profile](ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile)
owns the owner-view order, controlled status meanings, and ASD-STE100 Issue 9
conformance scope.
[TERMINOLOGY.md](TERMINOLOGY.md#asd-ste100-project-terminology) owns the
TrackTemplate technical terms. Authors use links from skills to these owners.
The skills do not become policy or terminology owners.

The [source and retrieval procedure](external/asd-ste100/README.md) owns the
local path and official source sequence. It also owns the STE lookup operation
and rebuild route. It does not own full applicability or the technical-term
register. The documentation review workflow uses the official source only for
a conformance review. Agents in other workflows route the review to
documentation review. Agents do not read the PDF during usual work.

For canonical prose in the conformance scope, use this route:

1. Read the Technical Documentation Profile.
2. Read the technical-term register.
3. Use the `tracktemplate-documentation-review` skill for the one
   Documentation Review.
4. Author the canonical prose and freeze one clean exact candidate in Git.
5. Derive the frozen review scope from the last accepted document identity and Git.
6. Give the complete frozen review scope to one independent Documentation Reviewer.
7. Record one complete `ACCEPT`, `APPROVED_WITH_EXACT_CORRECTIONS`, or `BLOCKED`
   verdict. A `BLOCKED` verdict must record a complete, nonempty `BLOCKED`
   finding set.
   Bind each finding to its exact path, frozen logical-unit identity, and formal
   Issue 9 rule identifiers.
8. For `APPROVED_WITH_EXACT_CORRECTIONS`, apply all exact replacement wording
   once against verified preimages. Do not invent other canonical prose.
9. Run one final deterministic validation after the review or correction.
10. Complete only if that validation is green. Otherwise, stop for the owner.

The Documentation Review is the only linguistic conformance review. Do not run
a second Documentation Review. The STE lookup derives the frozen review scope.
It validates source, exact candidate, receipt, accepted state, and final-content
identity. It also detects unreviewed mutation. It does not give or change the
linguistic verdict. A deterministic pre-check is only a review aid.

Rule families in a lookup result are retrieval priorities. They are not the
applicable requirement set. Use complete-source inspection only for these bounded
conditions:

- The task is about the complete standard.
- The task validates the retrieval architecture.
- Targeted retrieval cannot resolve an ambiguity that the reviewer records.
- An owner decision makes complete-source inspection necessary.

| Workflow responsibility | Owner and authority boundary |
| --- | --- |
| Documentation review | One independent reviewer uses `tracktemplate-documentation-review` for the complete frozen review scope. The reviewer uses the official source and returns one complete verdict. For `APPROVED_WITH_EXACT_CORRECTIONS`, that review supplies all exact replacement wording. The skill owns linguistic-review responsibility. |
| Claim, status, and documentation alignment | `tracktemplate-documentation-alignment` compares canonical prose with canonical authority. It uses the STE lookup and PDF only as external references. It keeps unverified conformance and migration findings in the record. |
| Evidence and limitation reports | An implementing agent uses `tracktemplate-change-validation` to put proof and provenance below the owner view. When applicable, the agent validates source, frozen review scope, exact candidate, receipt, accepted state, and final-content identity. A validation tool does not give or change the Documentation Review verdict. |
| Independent review | After final deterministic validation, an independent reviewer uses `tracktemplate-quality-review`. The reviewer examines implementation quality, limitations, and authority boundaries. For an Issue 9 claim, the reviewer checks the recorded Documentation Review and its bindings. This non-linguistic review does not repeat Documentation Review or change its verdict. |
| Handoff from `tracktemplate-technical-lead` | An implementing agent uses `tracktemplate-technical-lead` only for an authorised Level 1 or Level 2 result. If a conformance review is necessary, the agent routes the task to documentation review. |
| Cycle result from `tracktemplate-continue` | An agent that uses `tracktemplate-continue` supplies the 6 owner-view fields and technical provenance. If a conformance review is necessary, the agent routes the task to documentation review. Project authority for Level 1/2 work and merge does not change. |
| Result after context recovery | An agent that uses `tracktemplate-context-recovery` makes a short report from canonical authority. The agent keeps technical provenance for recovery. If a conformance review is necessary, the agent routes the task to documentation review. |

The panel examined the complete skill catalogue for TT-DOC-001. One owner has
each separate responsibility that can occur repeatedly. Thus, the project adds
no documentation-profile or `tracktemplate-ste100` skill.

For a later workflow change, use an existing primary owner when possible. Add
a skill only for a separate repeatable responsibility without an owner. Record
the composition order, non-ownership boundary, and authority exclusions. Do
not keep two skills with competing primary responsibilities.

These workflows keep their different responsibilities:

- architecture review
- chief of staff
- explain change
- handoff
- publish
- changelog
- release readiness
- simplify
- task automation

They get no TT-DOC-001 primary responsibility or additional authority.

## Current skill register

### `tracktemplate-architecture-review`

Path: `.agents/skills/tracktemplate-architecture-review/SKILL.md`

Use it before a material system-structure, responsibility,
dependency-direction, canonical-state, or staged-migration decision. It
compares the status quo and reversible alternatives with the accepted
architecture. It routes exact API contracts to the API skill. It records an
accepted durable decision only in its existing canonical owner.

### `tracktemplate-context-recovery`

Path: `.agents/skills/tracktemplate-context-recovery/SKILL.md`

Use it to resume TrackTemplate work after context may have been lost. It reloads
only the task-relevant current phase, subject authority, and evidence. Then it
examines the working tree as implementation state. It uses hot, warm, and cold
context. It also uses an authority-ranked loss check and a transient context
packet. It does not turn implementation evidence into project authority. This
evidence includes Git history, diffs, tests, and conversation summaries.

### `tracktemplate-ide-workspace-alignment`

Path: `.agents/skills/tracktemplate-ide-workspace-alignment/SKILL.md`

Use it to compare the person-facing PyCharm project with Git-authoritative
worktrees, branches, heads, and pull-request state. It owns IDE project-path,
VCS-root, interpreter, virtual-environment, and run-directory alignment. Git
workflows remain authoritative for reachability and each Git mutation. The
skill detects stale merged branches. It separates file-backed evidence from
physical-window confirmation. It keeps active work out of disposable `/tmp`
state.

### `tracktemplate-handoff`

Path: `.agents/skills/tracktemplate-handoff/SKILL.md`

Use it only for an explicit session transfer. It creates one short temporary
packet outside the repository. The packet contains the owner’s requested
outcome and exact authority limits. It also contains current implementation
and validation state, and the next safe action. It grants no repository, Git,
gate, or product-change authority. Context recovery must consume the packet
and revalidate all live state.

### `tracktemplate-freecad-addon-research`

Path: `.agents/skills/tracktemplate-freecad-addon-research/SKILL.md`

Use it to answer a bounded FreeCAD Addon question from the current official
Addon Academy and related first-party sources. It records source freshness,
separates guidance from runtime fact, and identifies the owning TrackTemplate
document. It also identifies the ontology authority boundary. Upstream advice
does not become a project decision.

### `tracktemplate-freecad-object-model`

Path: `.agents/skills/tracktemplate-freecad-object-model/SKILL.md`

Use it to map canonical railway records and stable identities onto versioned
FreeCAD document objects. Keep the number of objects, properties, and
FeaturePython proxies small. It governs recompute, transactions, save/reopen,
migration, Undo/Redo, and App/Gui separation. ViewProvider and Coin state remain
derived.

### `tracktemplate-license-analysis`

Path: `.agents/skills/tracktemplate-license-analysis/SKILL.md`

Use it to analyse exact licence, provenance, and rights evidence. This evidence
can cover source, product runtime dependencies, data, media, packages, and
generated output. It separates copyright licensing from other rights
questions. These questions cover data, design, patent, trade-mark, contract
rights, and contributor authority. It preserves unknowns and routes legal interpretation to
professional review. It cannot confer `project-cleared` status or legal
clearance.

### `tracktemplate-occt-geometry`

Path: `.agents/skills/tracktemplate-occt-geometry/SKILL.md`

Use it for exact FreeCAD `Part` and Open CASCADE B-rep construction, topology,
booleans, offsets, fillets, healing, meshing and production-output geometry. It
requires an exact topology-and-tolerance contract. It validates railway
semantics beyond kernel validity. It keeps exact shapes derived and
demand-driven.

### `tracktemplate-railway-mathematics`

Path: `.agents/skills/tracktemplate-railway-mathematics/SKILL.md`

Use it to formulate, implement or review alignment, transition, station,
offset, multiple-track, turnout, crossover, intersection, sampling and solver
mathematics. It requires explicit units, frames, domains, invariants,
degenerate cases, numerical tolerances, and independent evidence. This
evidence stays inside the FreeCAD-independent domain product boundary.

### `tracktemplate-railway-standards`

Path: `.agents/skills/tracktemplate-railway-standards/SKILL.md`

Use it before a gauge, wheel-and-track, clearance, rail, switch-and-crossing,
timbering, or related standards-derived value becomes an applicable
requirement. Also use it before that value becomes a default or production
input. It records exact applicability, revision, original units,
tolerance, provenance, and rights. It does not copy standards tables or make
the skill a source of railway authority.

### `tracktemplate-security-review`

Path: `.agents/skills/tracktemplate-security-review/SKILL.md`

Use it to inspect actual trust limits for untrusted files and archives. It also
examines stored FreeCAD data, filesystem and subprocess handling, product
runtime dependencies, credentials, accepted network integrations, exports,
and packaging. It separates reachable weaknesses from pattern matches. It
routes rights questions to licence analysis. It has no publication authority
and cannot certify safe operation.

### `tracktemplate-python-writing`

Path: `.agents/skills/tracktemplate-python-writing/SKILL.md`

Use it whenever creating or making a material edit to Python or FCMacro source.
It applies PEP 8 and PEP 257 as the writing baseline while preserving railway
behaviour and qualified FreeCAD compatibility. It preserves frozen B14/B15
evidence, public and persisted identifiers, diagnostics, and narrow diffs.

### `tracktemplate-debugging`

Path: `.agents/skills/tracktemplate-debugging/SKILL.md`

Use it to reproduce, isolate, and diagnose unexpected behaviour. This includes
tracebacks, hangs, crashes, nondeterminism, and resource regressions. It can
examine standalone, FreeCAD, GUI, persistence, export, and performance product
boundaries. It separates symptoms from confirmed causes and uses disposable
probes. It has no source-change authority unless the person also requests a
fix. Formal evidence selection and failed-test classification remain with the
validation skill.

### `tracktemplate-api-design`

Path: `.agents/skills/tracktemplate-api-design/SKILL.md`

Use it before adding or changing a supported Python API, application command,
or FreeCAD product boundary. Also use it before changing a persisted-data
contract, chair-package schema, exact exporter contract, or accepted network
integration. It defines consumers,
units, identities, errors, side effects, compatibility, migration, and evidence
before implementation. A conditional reference adds external-product client,
OAuth, webhook, and GraphQL controls. Normal in-process API work does not load
these controls. The controls do not assume that a network service exists.

### `tracktemplate-task-automation`

Path: `.agents/skills/tracktemplate-task-automation/SKILL.md`

Use it when a stable repeated development, validation, evidence or packaging
workflow creates measurable person or agent toil. It prefers existing tools
and keeps judgement and approvals explicit. It requires deterministic,
idempotent, recoverable evidence. It does not authorise unattended schedulers,
watchers, hooks, external services, destructive mutation, or new product
runtime dependencies. Its conditional CI reference separates clean-checkout
validation contracts from workstation-only evidence. It defines the failed-run
repair loop.

### `tracktemplate-publish`

Path: `.agents/skills/tracktemplate-publish/SKILL.md`

Invoke `$tracktemplate-publish` explicitly to validate and publish the current
bounded change. The workflow uses intentional commits, an `agent/` branch, one
draft pull request, and exact-commit CI monitoring. That invocation supplies
commit, push, draft-PR, and bounded CI-repair authority. The authority applies
only to the current bounded scope. It never authorises merge, ready-for-review
conversion, tagging, release, destructive history operations, or gate
acceptance. It also does not authorise expansion beyond the bounded scope.

### `tracktemplate-chief-of-staff`

Path: `.agents/skills/tracktemplate-chief-of-staff/SKILL.md`

Use it when the owner says progress appears stuck, circular,
maintenance-heavy, evidence-heavy, or unclear. `$tracktemplate-continue` also
composes it when that workflow detects its defined loop conditions. It is a
vision-informed programme orchestrator. It reconciles programme, phase,
evidence, and pull-request state. It detects loops and controls task
accountability. It compares selected work with credible authorised
alternatives. These can include maintenance, evidence, and risk-reduction
work. It produces exactly one transient advisory assignment or stop brief.
Its assignment must state **Why this outranks maintenance alternatives**. A
highest-value label without that comparison is insufficient. It is read-only
and is not necessary for each routine change. It cannot implement work or
accept project authority.

### `tracktemplate-technical-lead`

Path: `.agents/skills/tracktemplate-technical-lead/SKILL.md`

Use it when the owner selects an accepted repository outcome that needs
cross-specialist implementation. Also use it when an explicit
`$tracktemplate-continue` cycle selects such an authorised Level 1 or Level 2
outcome. It defines the smallest
end-to-end vertical slice. It composes the existing specialist skills through
validation and a separate read-only quality review. It does not own general
prioritisation, independent review, debugging, publication mechanics, or Level
3 acceptance. Its composition does not replace any specialist.

### `tracktemplate-continue`

Path: `.agents/skills/tracktemplate-continue/SKILL.md`

Invoke `$tracktemplate-continue` explicitly for one complete repository-driven
Level 1 or Level 2 cycle. It integrates one previous exact-green pull request,
synchronises protected `main`, and reads the Product Vision and current
authority. It selects one repository-evidenced gap that traces to an exact
phase criterion. It composes bounded delivery, validation, and independent
review. It reconciles the result and publishes one new exact-green draft. It
can stop after integration when no worthwhile programme-moving task exists.
It never manufactures a tranche or merges the new draft in the same cycle. It
composes IDE workspace alignment before its first Git mutation. It repeats
alignment after protected `main` synchronisation. It gains no new Git or
IDE-setting authority.

Only a project-owner command containing the literal `$tracktemplate-continue`
invocation activates it. Natural-language equivalents, quotations and
descriptions do not supply its authority. Its metadata therefore retains
`allow_implicit_invocation: false`. The accepted standing authority boundary is
recorded by
[D-GOV-004](history/phase-closeouts/PHASE5_CLOSEOUT.md#repository-driven-continuation-authority-panel).
[D-GOV-005](current/PHASE_EVIDENCE.md#product-vision-and-execution-governance-panel)
adds vision-led selection and result accountability without changing that
invocation or Level 1/2 execution authority.

### `tracktemplate-performance-engineering`

Path: `.agents/skills/tracktemplate-performance-engineering/SKILL.md`

Use it to baseline, profile and improve runtime, memory, recompute or
interaction performance under `PERFORMANCE_SOP.md`. It requires equivalent
inputs, process and cache conditions, and a bounded correctness scope. It
checks displaced Validate/Export cost. It cannot invent budgets or accept
changed behaviour.

### `tracktemplate-simplify`

Path: `.agents/skills/tracktemplate-simplify/SKILL.md`

Before using it, establish the preserved behaviour and evidence limit. Then use
it for a bounded simplification pass over source, tests, documentation, or
agent guidance. It removes only proven accidental complexity. It routes each material
edit through the applicable writing, validation, and quality skills. It does
not authorise changed railway behaviour, weaker validation, or
frozen-identifier migration. It also does not authorise cleanup outside the
bounded scope.

### `tracktemplate-documentation-review`

Path: `.agents/skills/tracktemplate-documentation-review/SKILL.md`

Use it when creating, reviewing, shortening or reorganising TrackTemplate
Markdown documentation, particularly where the change involves:

- duplicated status or technical explanation
- verbose or repetitive wording
- unclear document ownership
- live evidence, risks, or decisions recorded outside `reference/current/`
- material copied from another canonical owner
- conclusions or the applicable requirement set buried beneath background
- frozen evidence, licensing, provenance, or controlled wording
- documentation that needs restructuring without changing its meaning.

Use this skill while making a material documentation change.

### `tracktemplate-documentation-alignment`

Path: `.agents/skills/tracktemplate-documentation-alignment/SKILL.md`

Use it to audit documentation claims against current repository authority,
implementation, and validation evidence. Use it after source, structure, phase,
workflow, or agent-guidance changes. It classifies verified, stale,
contradictory, duplicated, orphaned, and unverified claims before narrow
corrections. It does not rewrite the accepted requirement set to match code.
It does not update frozen history to current state or perform automatic corpus
cleanup.

### `tracktemplate-changelog`

Path: `.agents/skills/tracktemplate-changelog/SKILL.md`

Use it to add or derive short person-facing unreleased notes. Prepare a version
section only after the project-owner release gate and version decision. It
verifies each Git-discovered review candidate against canonical authority and
completed evidence. It does not duplicate live phase status or infer
acceptance. It does not change version files, commit, tag, push, or publish.

### `tracktemplate-release-readiness`

Path: `.agents/skills/tracktemplate-release-readiness/SKILL.md`

Use it to audit one exact beta or exact release candidate and distributable
file. Compare it with accepted gates, clean-build reproducibility, Addon
installation, upgrade, compatibility, notices, provenance, documentation, and
qualification evidence. It keeps technical readiness, version acceptance,
gate closeout, and publication as separate project-owner decisions.

### `tracktemplate-change-validation`

Path: `.agents/skills/tracktemplate-change-validation/SKILL.md`

Use it to select, run and report the proportionate validation required for a
proposed or completed TrackTemplate change. It distinguishes:

- standalone parsing and analytical evidence
- qualified FreeCAD document checks
- real-GUI presentation and operator-journey evidence
- persistence, migration, rollback, and recovery evidence
- exact geometry and exporter evidence
- performance measurement
- provenance, licensing, and output-clearance product boundaries.

Use this skill after implementation or a documentation change. Use it before
the final quality review when applicable checks or evidence limits are not
trivial. Invoke it immediately when a selected check fails so the raw
failure is preserved and classified under `reference/TESTING_POLICY.md` before
retained fixes.

### `tracktemplate-quality-review`

Path: `.agents/skills/tracktemplate-quality-review/SKILL.md`

Use it to review the complete relevant diff for:

- unnecessary complexity or speculative abstractions
- duplicated authoritative logic
- rewrites outside the request
- misleading, repetitive, or stale comments
- hidden failures or weakened diagnostics
- behavioural drift in geometry, topology, tolerances, ordering, persistence,
  transactions, or export
- accidental public API, stored-state, or compatibility changes
- performance regressions and unsupported validation claims.

Use this skill as the staff-level, read-only first review. Use it before
reporting completion of a non-trivial source or documentation change. Also use
it after a classified failed-test repair. It judges the change using the available
evidence. It does not replace the validation skill.

### `tracktemplate-explain-change`

Path: `.agents/skills/tracktemplate-explain-change/SKILL.md`

Use it to teach a bounded working-tree diff, commit range, PR, patch, validated
tranche, or review packet. Present the material in concept order with explicit
evidence limits. Its
optional visual mode creates only sanitised, self-contained temporary HTML and
does not execute production code or become validation evidence. Explanation
does not replace validation, quality review or project-owner acceptance.

All twenty-eight skills are deliberately instruction-only. They do not perform
automatic cleanup, assign an “AI authenticity” score, ban phrases or rewrite
files in bulk. Those mechanisms can create false positives and remove legitimate
FreeCAD, railway, evidential or licensing context.

### Lifecycle coverage review

The 2026-07-27 repository-wide review added four general decision surfaces:
architecture review, performance engineering, exact security review, and
release readiness. A later railway/FreeCAD review added four specialist proof
surfaces. They are standards admission, railway mathematics, FreeCAD
document-object lifecycle, and exact OCCT geometry. General workflows could not
safely absorb them. Testing, project management, documentation, product runtime
dependency rights, and change explanation remain with their existing owners.

## Invocation

In Codex CLI or the IDE extension, invoke the relevant skill explicitly:

```text
$tracktemplate-architecture-review
```

```text
$tracktemplate-context-recovery
```

```text
$tracktemplate-ide-workspace-alignment
```

```text
$tracktemplate-handoff
```

```text
$tracktemplate-freecad-addon-research
```

```text
$tracktemplate-freecad-object-model
```

```text
$tracktemplate-license-analysis
```

```text
$tracktemplate-occt-geometry
```

```text
$tracktemplate-railway-mathematics
```

```text
$tracktemplate-railway-standards
```

```text
$tracktemplate-security-review
```

```text
$tracktemplate-python-writing
```

```text
$tracktemplate-debugging
```

```text
$tracktemplate-api-design
```

```text
$tracktemplate-task-automation
```

```text
$tracktemplate-publish
```

```text
$tracktemplate-chief-of-staff
```

```text
$tracktemplate-technical-lead
```

```text
$tracktemplate-continue
```

```text
$tracktemplate-performance-engineering
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
$tracktemplate-release-readiness
```

```text
$tracktemplate-change-validation
```

```text
$tracktemplate-quality-review
```

```text
$tracktemplate-explain-change
```

Codex may also select a skill implicitly when the request clearly matches its
description and its metadata permits implicit invocation. The handoff and
continue skills require their literal project-owner invocations. Publish
requires its literal invocation or delegation from an active literal
`$tracktemplate-continue` cycle. Do not replace an explicit-only project skill
with a generic workflow.

Chief of staff activates for an unambiguous direct request to diagnose progress
or when an active `$tracktemplate-continue` cycle detects its loop conditions.
An incidental maintenance or review finding does not activate it. It is not
necessary for each routine change. Technical lead activates for a selected,
authorised Level 1 or Level 2 outcome that needs cross-specialist integration.
It composes specialist skills and does not replace them.

Natural routing examples preserve these authority boundaries:

| Request | Route |
| --- | --- |
| “I think Phase 5 is looping. Review recent progress and identify the single highest-value next outcome.” | Chief of staff: read-only progress diagnosis and one transient brief. |
| “Take the selected current-phase outcome and drive the smallest technically coherent vertical slice.” | Technical lead plus the applicable specialist skills. |
| “PyCharm is still showing a merged branch. Reconcile it with current main without losing worktree state.” | IDE workspace alignment compares the person-facing project with Git authority. The Git workflow owns each separately authorised switch or move. |
| `$tracktemplate-continue` | Continue owns one repository-driven integration, delivery, validation, review and draft-publication cycle. |
| “Merge the last green pull request and continue with whatever is next.” | Does not activate continue. Request the literal `$tracktemplate-continue` invocation before using its one-cycle authority. |
| “Diagnose this traceback.” | Use debugging only unless later evidence authorises a fix. Neither new role activates. |
| “Review this pull request without modifying it.” | Use read-only quality review. Technical lead does not activate. |
| `$tracktemplate-publish` | Publish owns the bounded validation, branch, commit, draft and exact-head CI workflow. |
| “Publish this already validated branch.” | Does not activate TrackTemplate publish. Request the literal `$tracktemplate-publish` invocation. Do not use another publication workflow. |

Current phase evidence is not an automatic task queue, and a staff-review
finding does not automatically become the next tranche. No skill can accept
Level 3 authority for the project owner. There is deliberately no separate
`tracktemplate-deliver-outcome` skill. Continue composes the existing roles.
Product vision informs the value of possible work. It never authorises
implementation or widens an active exit. Before delivery, trace the selection
from agent task to bounded work item. Continue through finding or exit,
programme, and vision. State regression evidence and explicit non-goals.

Classify the task under
[ENGINEERING_POLICY.md](ENGINEERING_POLICY.md) before selecting workflows.
Level 2 requires the relevant specialist skill. Level 3 adds the applicable
evidence-review and panel workflow. This addition does not make a skill an
acceptance authority.

Use `$tracktemplate-freecad-addon-research` before the source or documentation
sequence when work depends on current FreeCAD Addon guidance. Its output is
research evidence, not implementation, validation or project acceptance.

Prefer explicit invocation for these conditions:

- release, phase-closure, or true authority-transfer reviews
- large refactors or architectural changes
- persistence, migration, export, licensing, or performance work
- substantial documentation restructuring
- changes involving canonical ownership, frozen evidence, provenance or
  validator-controlled wording.

For geometry, topology, persistence, migration, export, performance, provenance
or authority-changing work, use `$tracktemplate-change-validation` before
implementation when necessary. It defines the required proof limit. It does
not replace post-implementation validation.

## Normal workflow order

Validation determines what the evidence proves. Quality review determines
whether the implementation and bounded scope are acceptable with that evidence.

For IDE workspace alignment:

```text
Git-owned read-only worktree, branch, reachability and pull-request evidence
    ↓
$tracktemplate-ide-workspace-alignment
    ↓
separately authorised Git reconciliation when needed
    ↓
repeat file/Git comparison and obtain any person-only UI confirmation
```

For a planned session transfer:

```text
$tracktemplate-handoff
    ↓
temporary packet outside the repository
    ↓
new session: $tracktemplate-context-recovery with the packet path
```

For interrupted work or a recovery gate:

```text
examine named branches, worktrees, commits and each stash
    ↓
use the procedure for visible recovery state in its canonical owner
    ↓
preserve unique content
    ↓
get applicable authority for the exact disposition
    ↓
review evidence for ownership, purpose, preservation and disposition
    ↓
after the stash inventory is empty, give the recovery gate a complete result
```

For worktree retirement:

```text
Show accepted-history containment
    ↓
Show tracked cleanliness
    ↓
Make a local-state inventory of all files that are not in the Git index
    ↓
Put the local-state type for each item in the retirement plan
    ↓
Show planned preservation
    ↓
For rebuildable cache/generated state, show the applicable `PASS` result
    ↓
For temporary disposable state, show the cause for removal
    ↓
If the retirement plan has ambiguous or uniquely owned state, stop
    ↓
Before removal, examine the retirement audit again
    ↓
Before removal, examine the removal authority again
    ↓
Use `git worktree remove` without `--force`
    ↓
Show that the accepted commit contains the branch tip
    ↓
Use Git to remove only the local branch in the retirement plan
```

For an architecture decision:

```text
$tracktemplate-architecture-review
    ↓
$tracktemplate-api-design when a public API or stored-data contract changes
    ↓
$tracktemplate-documentation-review for an accepted canonical update
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For a source change:

```text
$tracktemplate-python-writing during Python implementation
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For a direct progress-diagnosis request outside a continuation cycle:

```text
Product Vision, programme, phase, repository/PR evidence and latest review
    ↓
$tracktemplate-chief-of-staff
    ↓
one transient bounded assignment or stop brief
    ↓
project owner accepts, adjusts or stops before any later delivery request
```

A staff-review `BACKLOG` or `OPTIONAL` finding does not automatically become
the next tranche. Chief-of-staff advice changes no project authority. If the
selected outcome is Level 3, stop technical delivery and use its owning
evidence-review, panel and project-owner decision workflow.

For an API or schema change:

```text
$tracktemplate-api-design
    ↓
$tracktemplate-freecad-addon-research for a FreeCAD product boundary
    ↓
$tracktemplate-python-writing during implementation
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For a standards-derived railway change:

```text
$tracktemplate-railway-standards
    ↓
$tracktemplate-license-analysis when retained evidence or distribution is involved
    ↓
$tracktemplate-railway-mathematics
    ↓
$tracktemplate-api-design when a public API or stored-data contract changes
    ↓
$tracktemplate-python-writing
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For FreeCAD document-object or exact-geometry work:

```text
$tracktemplate-freecad-addon-research
    ↓
$tracktemplate-freecad-object-model
    ↓
$tracktemplate-railway-mathematics for analytical geometry
    ↓
$tracktemplate-occt-geometry for an explicit Validate/Export product boundary
    ↓
$tracktemplate-api-design and $tracktemplate-python-writing
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

For one complete repository-driven development cycle:

```text
Product Vision, governance, programme, phase, repository and PR evidence
    ↓
$tracktemplate-continue
    ↓
read-only $tracktemplate-ide-workspace-alignment before Git mutation
    ↓
verify and integrate one previous exact-green Level 1/2 pull request,
then synchronise protected main
    ↓
repeat IDE workspace alignment before branch creation
    ↓
select one authorised evidenced gap
    ↓
state outcome, criterion, level, regression risk and acceptance evidence
    ↓
state explicit non-goals
    ↓
state why it outranks credible authorised alternatives
    ↓
conditional $tracktemplate-chief-of-staff when loop conditions are met
    ↓
$tracktemplate-technical-lead when cross-specialist integration is needed
    ↓
applicable specialist skills
    ↓
$tracktemplate-change-validation
    ↓
separate read-only $tracktemplate-quality-review
    ↓
repair only a `BLOCKER` finding, with at most two passes
    ↓
reconcile claimed, present, validated and independently accepted state
against the exact phase exit
    ↓
preserve non-claims
    ↓
$tracktemplate-publish in review-frozen mode
    ↓
plain-English owner acceptance pack
```

A clear routine outcome can skip chief of staff. A trivial isolated material
edit can skip technical lead. When no worthwhile authorised phase-moving
outcome exists, continue stops on clean protected `main` before branch creation. A newly
published draft is never marked ready or merged in the same invocation.
Delegated publication cannot mutate the reviewed source. An exact-head CI
`BLOCKER` finding returns to the same two-pass validation-and-review loop.

For measured performance work:

```text
$tracktemplate-performance-engineering
    ↓
$tracktemplate-debugging when the cause is not established
    ↓
$tracktemplate-python-writing or $tracktemplate-simplify
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For a change that needs a security/recovery review:

```text
$tracktemplate-security-review
    ↓
$tracktemplate-api-design or $tracktemplate-license-analysis when applicable
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
$tracktemplate-documentation-review during material changes
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

For a beta or exact release-candidate audit:

```text
$tracktemplate-release-readiness
    ↓
$tracktemplate-freecad-addon-research when current packaging guidance is needed
    ↓
$tracktemplate-changelog and $tracktemplate-license-analysis
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
when available and proportionate. Give the reviewer the request, canonical
requirement set, complete diff, raw validation evidence, and known unperformed
checks. Do not prime the reviewer with the intended verdict. Disclose a
same-agent review or another independence limitation. After an adverse verdict,
separate authorised remediation from that pass. Rerun affected validation and
review the resulting complete diff again.

Disposition each actionable staff-review finding as `BLOCKER`,
`REQUIRED_BEFORE_EXIT`, `BACKLOG` or `OPTIONAL`. Only a `BLOCKER` returns
automatically to technical delivery. Outside an active
`$tracktemplate-continue` cycle, a `REQUIRED_BEFORE_EXIT` item may join the same
cycle only when it directly prevents the selected outcome or proof. During an
active continuation cycle, only a `BLOCKER` can return to implementation.
`REQUIRED_BEFORE_EXIT`, `BACKLOG` and `OPTIONAL` items do not join that cycle.
When progress is unclear or an active continuation cycle detects a loop, pass
the review as read-only chief-of-staff input. The reviewer does not select the
next objective.

For a failed test:

```text
preserve raw failure and identify the exact validation contract
    ↓
$tracktemplate-change-validation — classify under TESTING_POLICY.md
    ↓
repair only what the failure classification identifies and rerun the original proof
    ↓
$tracktemplate-quality-review — review source, tests and evidence
```

For an unexpected failure whose cause is not established:

```text
$tracktemplate-debugging — reproduce and isolate read-only
    ↓
$tracktemplate-change-validation — classify failed evidence
    ↓
$tracktemplate-python-writing — only when a fix is authorised
    ↓
$tracktemplate-change-validation
    ↓
$tracktemplate-quality-review
```

For a maintainer explanation after evidence is bounded:

```text
$tracktemplate-change-validation and $tracktemplate-quality-review evidence
    ↓
$tracktemplate-explain-change
```

Do not treat a failed test as automatic authority to change production code or
the test. `reference/TESTING_POLICY.md` owns the classifications and
test/oracle-change gate. Validation owns evidence and classification. Quality
review owns staff-level bounded scope and implementation judgement.

## External method and skill admission

External skill repositories are research inputs, not inherited project
authority. Before installing, copying or adapting one:

1. Pin and record the reviewed revision and licence.
2. Inspect its complete triggered instructions, hooks, scripts, product runtime
   dependencies, file-system extent, and external actions.
3. Compare its ownership model, terminology, approval gates and validation
   claims with `AGENTS.md` and the canonical documents.
4. Choose deliberately between adapting an idea, linking to upstream, vendoring
   reviewed content, installing a plugin, or rejecting it.
5. Preserve required notices for copied or substantially adapted material.
6. Give each admitted local skill one responsibility and remove or bound any
   overlap with an existing skill.
7. Run the repository guidance validator and the normal documentation and
   quality reviews.

Do not bulk-copy a catalogue or enable repository-writing hooks. Do not add a
product runtime dependency only because upstream describes it as universal or
ready to use. An upstream update requires a new review. It does not flow
automatically into this repository.

### Sources reviewed for this policy

The following sources were reviewed on 2026-07-27. No upstream file, hook,
script or runtime package was copied or installed by this review.

| Source and reviewed revision | Classification | TrackTemplate decision |
| --- | --- | --- |
| [`reidemeister94/development-skills`](https://github.com/reidemeister94/development-skills/tree/92922f58f037191f2ccc909a69cbe297fc49efae), `92922f58f037191f2ccc909a69cbe297fc49efae`, MIT | Coding-agent workflow plugin with session-start and change-time hooks | Adapt the useful standards-first, durable-rationale, and resume principles through the existing authority map and local recovery skill. Adapt its explicit handoff idea through a local skill. That skill writes only a temporary navigation packet and grants no Git, gate, or product authority. Adapt its documentation-drift audit, changelog curation, and bounded simplification ideas through the corresponding local skills. Preserve TrackTemplate's canonical owners, frozen evidence, and release gates. Adapt the explain-diff visual idea into a separate read-only explanation skill. Its sanitised HTML exists only in temporary storage and is never production evidence. Do not install its router, auto-formatter, mutation hooks, `docs/plans/`, or `docs/chronicles/` model. Do not grant automatic commit, tag, bulk-rewrite, or release authority to the adapted work. |
| [`seb1n/awesome-ai-agent-skills`](https://github.com/seb1n/awesome-ai-agent-skills/tree/a6c8c0ef3c240faefe1b0b5cabe1567beaea60fd), `a6c8c0ef3c240faefe1b0b5cabe1567beaea60fd`, MIT | Catalogue of generic instruction skills from the reviewed repository | Use it only as a discovery source. Admit each idea after project-specific review. Adapt stable-workflow automation without generic schedulers, watchers, destructive moves, or new product runtime dependencies. Adapt licence analysis through the existing fail-closed source, data, media, and output controls. Do not make categorical legal conclusions. Adapt the complete API and integration group into one local API-and-integration contract skill. Its conditional network reference covers client resilience, OAuth, webhooks, and GraphQL. It does not assume REST or install an SDK or service. Normal Python and FreeCAD product boundaries do not load the network guidance. From the code-and-development group, admit only systematic debugging as a separate causal-investigation skill. Code documentation, review, refactoring, and testing duplicate stronger local skills. Generic version-control guidance conflicts with repository recovery and Git-authority controls. Embedding and vector-retrieval infrastructure remains unjustified. |
| [`pydantic/pydantic-ai`](https://github.com/pydantic/pydantic-ai/tree/ed0f40c0e5061722f7d9f579ed7efff1b74e3ea5), `ed0f40c0e5061722f7d9f579ed7efff1b74e3ea5`, MIT | Python agent framework repository with root instructions, directory-specific instructions, and project-specific skills | Adapt its context-first, responsibility-to-project, and patch-as-evidence patterns. TrackTemplate already supplies the corresponding authority map and local skills. Add directory-specific `AGENTS.md` only where a directory has different rules. Do not add Pydantic AI as a TrackTemplate or FreeCAD product runtime dependency without a separately approved in-product agent capability. That approval also needs compatibility, exact security review, data, cost, and validation evidence. |
| A B Vijay Kumar, [Deep Dive SKILL.md Part 1](https://abvijaykumar.medium.com/deep-dive-skill-md-part-1-2-09fc9a536996) (published 2026-03-17) and [Part 2](https://abvijaykumar.medium.com/getting-deep-agents-to-work-with-skill-md-part-2-2-a65707eb5131) (published 2026-03-21), mutable web pages retrieved 2026-07-27, no reusable-content licence relied upon | Expository architecture and worked skill-building example, not project or platform authority | Adapt progressive disclosure, precise routing descriptions, conditional references, deterministic scripts, actionable diagnostics, validation loops, and real-task iteration. No wording, sample code, product runtime dependencies, optional frontmatter, or external package was copied. The unpinned pages remain research inputs only. |
| [Agent Skills specification](https://agentskills.io/specification) and [creator best practices](https://agentskills.io/skill-creation/best-practices), live open-standard pages retrieved 2026-07-27 | Primary format and design guidance. Client support still varies. | Enforce the below-500-line `SKILL.md` budget, direct one-level resource routing, and real-task evaluation. Retain the current Codex-compatible two-field frontmatter subset. Prefer project-specific gotchas to generic teaching. Do not create one skill for each tool. |

## Agent-guidance validation

Optional agent-skill tooling is pinned in `requirements-dev.txt`. It is not
imported by TrackTemplate, required by FreeCAD or included in the Addon
file. Install it into the project virtual environment with:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

After changing `AGENTS.md`, `reference/AGENT_WORKFLOWS.md` or a repository skill,
run:

```bash
.venv/bin/python tests/validate_agent_guidance.py
```

The validator checks skill frontmatter, directory/name agreement, the
below-500-line `SKILL.md` budget, and direct routing for each resource file. It
also checks scripts, asset files, one-level reference layout, local links, the
skill register, and root routing. Its progression-role checks have a specific
limit. They check required UI metadata, section structure, and direct
composition links. They do not duplicate skill wording. The validator does not
judge instruction quality or model routing. It also does not prove project
validation.

## Skill maintenance rules

- Give each skill one repeatable job and a short trigger description.
- Ground new or revised skills in a real TrackTemplate task, correction,
  failure, exact named contract, or review pattern. Do not use generic advice.
- Put what the skill does and when it activates in the description. Add
  non-activation wording only for evidenced overlap. Metadata consumes shared
  discovery context.
- Default to instruction-only. Add scripts only when the task is deterministic,
  reviewable, safe on a dirty working tree and materially better than existing
  project tools.
- Never import executable code from an external skill before the required
  review. Inspect its licence, behaviour, product runtime dependencies, and
  file-system extent.
- Do not add MCP merely because a skill exists. MCP is appropriate only when the
  workflow needs controlled access to an external system or live data source.
- Link to the canonical project document rather than copying its detailed rules.
- Link every conditional resource file directly from `SKILL.md`. State when to
  load or execute it. Keep references one filesystem level deep. A link to a
  directory or from another resource does not establish direct reachability.
- Treat new skill behaviour as repository guidance. Review it like code, keep
  the diff narrow, and run the documentation, link, and agent-guidance controls.
- Keep the skill register aligned with the directories under `.agents/skills/`.
- Do not allow two skills to claim the same primary responsibility without
  clearly defining their order and non-ownership boundary.
- For a new skill or material trigger/workflow change, exercise natural prompts.
  Include prompts that should activate, should not activate, and should compose.
  Inspect the execution path and the final answer. Static validation is necessary
  but not a routing or output-quality evaluation.
- When a skill uncovers a durable project lesson, confirm its evidence. Append
  it to `reference/LEARNING_FROM_EXPERIENCE.md` only after it leads to an
  accepted reusable adaptation.

A clean implementation or wording style is not enough for completion. Railway
correctness, recoverability, evidence quality and project authority remain
controlling.
