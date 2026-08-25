# Agent Workflows

Status: **repository guidance; owns agent-skill structure and maintenance only.**

## Purpose

This document separates five different kinds of project control:

| Layer | Owns | Must not own |
| --- | --- | --- |
| `AGENTS.md` | Short, always-on, repository-wide invariants and routing | Detailed repository history, long command catalogues, live progress or task-specific procedure |
| Canonical `reference/` documents | Project requirements, architecture, policy and evidence interpretation in their named domains | Agent-product implementation details that do not change project policy |
| `.agents/skills/*/SKILL.md` | Repeatable, task-specific workflows and review methods | Project authority, accepted requirements, phase status or automatic acceptance |
| Tests and scripts | Deterministic checks and safe automation | Subjective project decisions or unreviewed file rewriting |
| Git history and diffs | Source-state and change evidence | Requirements, rationale, acceptance or current project status |

Skills complement `AGENTS.md`; they do not replace it. A skill may link to a
canonical document, but it must not copy enough of that document to become a
second policy owner.

[`PRODUCT_VISION.md`](PRODUCT_VISION.md) owns product purpose, programme
horizons and Core-migration completion. Architecture, plan, evidence, skills and
source apply that direction within their narrower authority; none may silently
become an alternative product-vision owner.

## Session continuity

At the start of resumed work, reconstruct authority in this order:

1. repository and scoped `AGENTS.md`;
2. `reference/PRODUCT_VISION.md` and accepted architectural invariants;
3. `reference/PROJECT_PLAN.md` for the authorised programme, phase and exits;
4. `reference/current/PHASE_EVIDENCE.md` and the current JSON registers;
5. the canonical owner of the affected subject; and
6. source, tests, Git history and diffs as implementation evidence.

Use `$tracktemplate-context-recovery` when a new session, compaction,
interrupted handoff or unfamiliar dirty worktree makes that reconstruction
material. Do not infer a requirement or accepted decision from a diff, commit
message, branch name, test expectation or implementation comment.

Before an explicit transfer to a new chat, usage reset or long pause, use
`$tracktemplate-handoff` to write one temporary navigation packet outside the
repository. The receiving session uses `$tracktemplate-context-recovery` with
that packet and rechecks live repository, pull-request and CI state. The packet
does not become project authority, current-phase evidence or a durable record.

Before ending work, put each accepted durable fact in its existing canonical
owner. Do not create generic per-task plans or chronicles that duplicate
`PROJECT_PLAN.md`, the fixed current-phase records or another canonical
document. A task that remains incomplete is reported as incomplete, with its
working-tree state, evidence already run, unresolved decisions and next safe
check made explicit.

Read the
[procedure for visible recovery state](RECOVERY_AND_BACKUP.md#visible-recovery-state)
in its canonical owner. Use it for Git recovery and handoff state. A context
packet gives the route to named Git state. It is not planned preservation.
Until the recovery workflow completes stash reconciliation, do not give the
recovery gate a complete result.

Before a worktree retirement, read the
[deliberate worktree retirement procedure](RECOVERY_AND_BACKUP.md#deliberate-worktree-retirement).
Context recovery makes an inventory of local state and identifies its owner.
IDE/workspace alignment shows that the worktree is inactive and has no sole
operator state. The read-only safety audit records the exact Git and local-state
identities and examines the reviewed classification plan. A merge and tracked cleanliness give no
disposal authority in these workflows. They stop when ignored or local-only
state has ambiguous ownership or lacks preservation proof.

## Instruction budget

Codex combines repository instruction files and applies a finite default byte
budget. Keep the root `AGENTS.md` comfortably below that limit so nested
instructions still have room.

Project target:

- keep the root `AGENTS.md` at roughly **100–140 lines** and below **12 KiB**;
- move repeatable procedures to skills and detailed facts to their canonical
  reference documents;
- do not raise the Codex instruction limit merely to avoid removing duplication.

Measure with:

```bash
wc -c AGENTS.md
```

## Progressive disclosure and composition

TrackTemplate uses the three skill-loading layers deliberately:

1. **Discovery metadata:** `name` and `description` state what the skill does
   and when it should activate. Include concrete project/task concepts; add a
   negative boundary only where a real routing overlap exists.
2. **Triggered procedure:** `SKILL.md` contains the cohesive workflow,
   load-bearing gotchas and resource-selection rules needed on every activation.
   Keep it below 500 lines and avoid generic knowledge the agent already has.
3. **Conditional resources:** focused references, deterministic scripts and
   output assets load only when their named condition applies. Link every file
   directly from `SKILL.md`; a directory link or another resource is not a
   substitute. Keep references one filesystem level deep.

The project uses the portable `name`/`description` frontmatter core supported by
the current Codex validator. Optional fields from the wider Agent Skills
specification are not added unless the active client and a project need justify
them.

A skill packages a repeatable procedure, not one tool call. Compose several
skills when a task crosses coherent responsibilities; do not mirror each CLI,
MCP endpoint or script as a separate skill. Put deterministic operations in
tested scripts and leave scope, evidence interpretation and authority decisions
visible to the agent and project owner.

## TT-DOC-001 workflow integration

The canonical
[TrackTemplate Technical Documentation Profile](ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile)
owns the owner-view order, controlled status meanings, and ASD-STE100 Issue 9
scope. [TERMINOLOGY.md](TERMINOLOGY.md#asd-ste100-project-terminology) owns the
TrackTemplate technical terms. Skills apply these owners by reference. They do
not become policy or terminology owners.

The [ASD-STE100 Issue 9 local source and STE lookup procedure](external/asd-ste100/README.md)
owns the local path and official source sequence. It also owns the STE lookup
operation and rebuild route. It does not own full applicability. It does not
own the technical-term register. The documentation review workflow uses the
official source only for a linguistic conformance assessment. Other workflows
route that assessment to documentation review. They do not read the PDF during
usual work.

For documentation in the STE conformance scope, use this route:

1. Read the canonical Technical Documentation Profile.
2. Read the canonical TrackTemplate technical-term register.
3. Classify the changed canonical prose and identify the applicable rule families.
4. Do the deterministic pre-check when it can help the review.
5. Use targeted retrieval for writing rules, dictionary-inspection candidates, and ambiguities.
6. Read a bounded source excerpt when the STE lookup does not give sufficient information.
7. Review the complete logical unit against the complete applicable requirement set.
8. Record the technical-term status. Record each unresolved finding.
9. Get an independent review when the change level or risk makes it necessary.

The selected rule families are retrieval priorities. They are not the complete
applicable rule set. Do not start each review at the first source page and read
to the last source page. Use complete-source inspection only for these bounded conditions:

- The task is about the complete standard.
- The task validates the retrieval architecture.
- Targeted retrieval cannot resolve an ambiguity that the reviewer records.
- An owner decision makes complete-source inspection necessary.

| Workflow responsibility | Owner and boundary |
| --- | --- |
| Documentation structure and Issue 9 review | `tracktemplate-documentation-review` reviews the full logical unit that contains the change. It uses the STE lookup for targeted retrieval, reports the official standard source, and uses the canonical workflow responsibility. |
| Claim, status, and documentation alignment | `tracktemplate-documentation-alignment` compares canonical prose with canonical authority. It uses the STE lookup and the PDF as external references only. It keeps unverified conformance and migration findings in the record. |
| Evidence and limitation reports | `tracktemplate-change-validation` keeps proof/provenance below the owner view. It validates source identity and derived cache identity and a review receipt when applicable. It makes sure the conformance record reports an official source. Automatic validation does not show linguistic conformance. |
| Independent review | `tracktemplate-quality-review` keeps canonical policy, the external standard, lookup results, and the complete logical unit different. It validates that the reviewer examines the complete applicable requirement set. Then, it gives an independent review of limitations and authority boundaries. It does not do validation again. |
| Cross-specialist delivery handoff | `tracktemplate-technical-lead` uses the owner view for an authorised Level 1 or Level 2 outcome only. It routes a necessary linguistic assessment to documentation review. |
| Repository-driven cycle result | Literal `tracktemplate-continue` supplies the six-field owner view and technical provenance. It routes a necessary linguistic assessment to documentation review. Its Level 1/2 and merge limits do not change. |
| Recovered-session result | `tracktemplate-context-recovery` makes its short report from verified authority. It keeps the exact recovery provenance. It routes a necessary linguistic assessment to documentation review. |

The panel examined the full skill catalog for TT-DOC-001. Each
separate responsibility that can occur repeatedly has one owner. Thus, the
project adds no documentation-profile or `tracktemplate-ste100` skill.

For a future workflow change, use the primary owner that is already in the
skill catalog when possible. Add a skill only when the skill catalog finds a
separate responsibility that can occur repeatedly and has no owner. Record the
composition order, non-ownership, and authority exclusions. Do not keep two
skills with competing primary responsibilities.

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
dependency-direction, canonical-state or staged-migration decision. It compares
the status quo and reversible alternatives against the accepted architecture,
routes detailed contracts to the API skill and records an accepted durable
decision only in its existing canonical owner.

### `tracktemplate-context-recovery`

Path: `.agents/skills/tracktemplate-context-recovery/SKILL.md`

Use it to resume TrackTemplate work after context may have been lost. It reloads
only the task-relevant current phase, subject authority and evidence before
inspecting the working tree as implementation state. It uses hot, warm and cold
context, an authority-ranked loss check and a transient context packet; it does
not turn Git history, diffs, tests or conversation summaries into project
authority.

### `tracktemplate-ide-workspace-alignment`

Path: `.agents/skills/tracktemplate-ide-workspace-alignment/SKILL.md`

Use it to compare the operator-facing PyCharm project with Git-authoritative
worktrees, branches, heads and pull-request state. It owns IDE project-path,
VCS-root, interpreter, virtual-environment and run-directory alignment while
Git workflows remain authoritative for reachability and every Git mutation. It
detects stale merged branches, distinguishes file-backed evidence from physical
window confirmation and keeps active work out of disposable `/tmp` state.

### `tracktemplate-handoff`

Path: `.agents/skills/tracktemplate-handoff/SKILL.md`

Use it only for an explicit session transfer. It creates one concise temporary
packet outside the repository containing the owner’s requested outcome, exact
authority limits, current implementation and validation state, and the next
safe action. It grants no repository, Git, gate or product-change authority and
must be consumed through context recovery, which revalidates all live state.

### `tracktemplate-freecad-addon-research`

Path: `.agents/skills/tracktemplate-freecad-addon-research/SKILL.md`

Use it to answer a bounded FreeCAD Addon question from the current official
Addon Academy and related first-party sources. It records source freshness,
distinguishes guidance from runtime fact, and maps the result to the owning
TrackTemplate document and ontology boundary without turning upstream advice
into a project decision.

### `tracktemplate-freecad-object-model`

Path: `.agents/skills/tracktemplate-freecad-object-model/SKILL.md`

Use it to map canonical railway records and stable identities onto a small
number of versioned FreeCAD document objects, properties and FeaturePython
proxies. It governs recompute, transactions, save/reopen, migration, Undo/Redo
and App/Gui separation while keeping ViewProvider and Coin state derived.

### `tracktemplate-license-analysis`

Path: `.agents/skills/tracktemplate-license-analysis/SKILL.md`

Use it to analyse exact licence, provenance and rights evidence for source,
dependencies, data, media, packages and generated output. It separates
copyright licensing from data, design, patent, trade-mark, contract and
contributor-authority questions, preserves unknowns and routes legal
interpretation to professional review. It cannot itself confer
`project-cleared` status or legal clearance.

### `tracktemplate-occt-geometry`

Path: `.agents/skills/tracktemplate-occt-geometry/SKILL.md`

Use it for exact FreeCAD `Part` and Open CASCADE B-rep construction, topology,
booleans, offsets, fillets, healing, meshing and production-output geometry. It
requires an explicit topology and tolerance contract, validates railway
semantics beyond kernel validity and keeps exact shapes derived and
demand-driven.

### `tracktemplate-railway-mathematics`

Path: `.agents/skills/tracktemplate-railway-mathematics/SKILL.md`

Use it to formulate, implement or review alignment, transition, station,
offset, multiple-track, turnout, crossover, intersection, sampling and solver
mathematics. It requires explicit units, frames, domains, invariants,
degenerate cases, numerical tolerances and independent evidence in a
FreeCAD-independent domain boundary.

### `tracktemplate-railway-standards`

Path: `.agents/skills/tracktemplate-railway-standards/SKILL.md`

Use it before a gauge, wheel-and-track, clearance, rail, switch-and-crossing,
timbering or related standards-derived value becomes a requirement, default or
production input. It records exact applicability, revision, original units,
tolerance, provenance and rights without copying standards tables or making
the skill a source of railway authority.

### `tracktemplate-security-review`

Path: `.agents/skills/tracktemplate-security-review/SKILL.md`

Use it to inspect actual trust boundaries for untrusted files and archives,
stored FreeCAD data, filesystem and subprocess handling, dependencies,
credentials, accepted network integrations, exports and packaging. It
distinguishes reachable weaknesses from pattern matches and routes rights
questions to licence analysis; it is not publication authority or a security
certification.

### `tracktemplate-python-writing`

Path: `.agents/skills/tracktemplate-python-writing/SKILL.md`

Use it whenever creating or materially editing Python or FCMacro source. It
applies PEP 8 and PEP 257 as the writing baseline while preserving railway
behaviour, qualified FreeCAD compatibility, frozen B14/B15 evidence, public and
persisted identifiers, diagnostics and narrow diffs.

### `tracktemplate-debugging`

Path: `.agents/skills/tracktemplate-debugging/SKILL.md`

Use it to reproduce, isolate and diagnose unexpected behaviour, tracebacks,
hangs, crashes, nondeterminism and resource regressions across standalone,
FreeCAD, GUI, persistence, export and performance boundaries. It separates
symptoms from confirmed causes, uses disposable probes and owns no authority to
edit source unless the user also requests a fix. Formal evidence selection and
failed-test classification remain with the validation skill.

### `tracktemplate-api-design`

Path: `.agents/skills/tracktemplate-api-design/SKILL.md`

Use it before adding or changing a supported Python API, application command,
FreeCAD boundary, persistence/package schema, exporter contract or accepted
network integration. It defines consumers, units, identities, errors, side
effects, compatibility, migration and evidence before implementation. A
conditional reference adds third-party client, OAuth, webhook and GraphQL
controls without loading them for normal in-process API work or assuming a
network service exists.

### `tracktemplate-task-automation`

Path: `.agents/skills/tracktemplate-task-automation/SKILL.md`

Use it when a stable repeated development, validation, evidence or packaging
workflow creates measurable operator or agent toil. It prefers existing tools,
keeps judgement and approvals explicit, and requires deterministic,
idempotent, recoverable evidence. It does not authorise unattended schedulers,
watchers, hooks, external services, destructive mutation or new dependencies.
Its conditional CI reference separates clean-checkout contracts from
workstation-only evidence and defines the failed-run repair loop.

### `tracktemplate-publish`

Path: `.agents/skills/tracktemplate-publish/SKILL.md`

Invoke `$tracktemplate-publish` explicitly to validate and publish the current
bounded change through intentional commits, an `agent/` branch, one draft pull
request and exact-commit CI monitoring. That invocation supplies commit, push,
draft-PR and bounded CI-repair authority for the current scope only. It never
authorises merge, ready-for-review conversion, tagging, release, destructive
history operations, gate acceptance or scope expansion.

### `tracktemplate-chief-of-staff`

Path: `.agents/skills/tracktemplate-chief-of-staff/SKILL.md`

Use it when the owner says progress appears stuck, circular,
maintenance/evidence-heavy or unclear, and compose it from
`$tracktemplate-continue` when that workflow detects its defined loop
conditions. It is a vision-informed programme orchestrator: it reconciles
programme, phase, evidence and pull-request state; detects loops; controls task
accountability; compares the selected work with credible maintenance, evidence,
risk-reduction and other authorised alternatives; and produces exactly one
transient, advisory assignment or stop brief. Its assignment must state **Why
this outranks maintenance alternatives**; a highest-value label without that
comparison is insufficient. It is read-only, is not required for every routine
change and cannot implement or accept project authority.

### `tracktemplate-technical-lead`

Path: `.agents/skills/tracktemplate-technical-lead/SKILL.md`

Use it when the owner selects an accepted repository outcome or an explicit
`$tracktemplate-continue` cycle selects an authorised Level 1 or Level 2
outcome that needs a cross-specialist implementation route. It defines one
smallest end-to-end vertical slice and composes the existing specialist skills
through validation and separate read-only quality review. It does not own
general prioritisation, independent review, debugging, publication mechanics
or Level 3 acceptance, and its composition does not replace any specialist.

### `tracktemplate-continue`

Path: `.agents/skills/tracktemplate-continue/SKILL.md`

Invoke `$tracktemplate-continue` explicitly for one complete repository-driven
Level 1 or Level 2 cycle. It integrates one previous exact-green pull request,
synchronises protected `main`, reads the Product Vision and current authority,
selects one repository-evidenced gap traceable to an exact phase criterion,
composes bounded delivery/validation/independent review, reconciles the result
and publishes one new exact-green draft. It may stop after integration when no
worthwhile programme-moving task exists, and never manufactures a tranche or
merges the newly published draft in the same cycle. It composes IDE workspace
alignment before its first Git mutation and again after protected `main`
synchronisation, without inheriting new Git or IDE-setting authority.

Only a project-owner command containing the literal `$tracktemplate-continue`
invocation activates it. Natural-language equivalents, quotations and
descriptions do not supply its authority; its metadata therefore retains
`allow_implicit_invocation: false`. The accepted standing boundary is recorded
by [D-GOV-004](history/phase-closeouts/PHASE5_CLOSEOUT.md#repository-driven-continuation-authority-panel).
[D-GOV-005](current/PHASE_EVIDENCE.md#product-vision-and-execution-governance-panel)
adds vision-led selection and result accountability without changing that
invocation or Level 1/2 execution authority.

### `tracktemplate-performance-engineering`

Path: `.agents/skills/tracktemplate-performance-engineering/SKILL.md`

Use it to baseline, profile and improve runtime, memory, recompute or
interaction performance under `PERFORMANCE_SOP.md`. It requires equivalent
inputs, process/cache conditions and correctness scope, checks displaced
Validate/Export cost and cannot invent budgets or accept changed behaviour.

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
- live evidence, risks or decisions recorded outside `reference/current/`;
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

### `tracktemplate-release-readiness`

Path: `.agents/skills/tracktemplate-release-readiness/SKILL.md`

Use it to audit one exact beta or release candidate and distributable artifact
against accepted gates, clean-build reproducibility, Addon installation and
upgrade, compatibility, notices, provenance, documentation and qualification
evidence. It keeps technical readiness, version acceptance, gate closeout and
publication as separate project-owner decisions.

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

### `tracktemplate-explain-change`

Path: `.agents/skills/tracktemplate-explain-change/SKILL.md`

Use it to teach a bounded working-tree diff, commit range, PR, patch, validated
tranche or review packet in concept order with explicit evidence limits. Its
optional visual mode creates only sanitised, self-contained temporary HTML and
does not execute production code or become validation evidence. Explanation
does not replace validation, quality review or project-owner acceptance.

All twenty-eight skills are deliberately instruction-only. They do not perform
automatic cleanup, assign an “AI authenticity” score, ban phrases or rewrite
files in bulk. Those mechanisms can create false positives and remove legitimate
FreeCAD, railway, evidential or licensing context.

### Lifecycle coverage review

The 2026-07-27 repository-wide review added four general decision surfaces:
architecture review, performance engineering, security review and release
readiness. A subsequent railway/FreeCAD review added the four specialist proof
surfaces that general workflows could not safely absorb: standards admission,
railway mathematics, FreeCAD document-object lifecycle and exact OCCT geometry.
Testing, project management, documentation, dependency rights and change
explanation remain with their existing skills and canonical owners.

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
continue skills require their literal project-owner invocations; publish
requires either its literal invocation or delegation from an active literal
`$tracktemplate-continue` cycle. Do not substitute a generic workflow for an
explicit-only project skill.

Chief of staff activates for an unambiguous direct request to diagnose progress
or when an active `$tracktemplate-continue` cycle detects its loop conditions;
an incidental maintenance or review finding alone does not activate it. It is
not required for every routine change. Technical lead activates for a selected,
authorised Level 1 or Level 2 outcome that needs cross-specialist integration;
it composes rather than replaces specialist skills.

Natural routing examples preserve these boundaries:

| Request | Route |
| --- | --- |
| “I think Phase 5 is looping. Review recent progress and identify the single highest-value next outcome.” | Chief of staff: read-only progress diagnosis and one transient brief. |
| “Take the selected current-phase outcome and drive the smallest technically coherent vertical slice.” | Technical lead plus the applicable specialist skills. |
| “PyCharm is still showing a merged branch; reconcile it with current main without losing worktree state.” | IDE workspace alignment compares the operator project with Git authority; the Git workflow owns any separately authorised switch or move. |
| `$tracktemplate-continue` | Continue owns one repository-driven integration, delivery, validation, review and draft-publication cycle. |
| “Merge the last green pull request and continue with whatever is next.” | Does not activate continue; request the literal `$tracktemplate-continue` invocation before using its one-cycle authority. |
| “Diagnose this traceback.” | Debugging only unless later evidence authorises a fix; neither new role activates. |
| “Review this pull request without modifying it.” | Read-only quality review; technical lead does not activate. |
| `$tracktemplate-publish` | Publish owns the bounded validation, branch, commit, draft and exact-head CI workflow. |
| “Publish this already validated branch.” | Does not activate TrackTemplate publish; request the literal `$tracktemplate-publish` invocation and do not substitute another publication workflow. |

Current phase evidence is not an automatic task queue, and a staff-review
finding does not automatically become the next tranche. No skill can accept
Level 3 authority for the project owner. There is deliberately no separate
`tracktemplate-deliver-outcome` skill; continue composes the existing roles.
Product vision informs candidate value but never authorises implementation or
widens an active exit. Selection must trace agent task → bounded work item →
finding/exit → current programme → vision and state regression evidence and
explicit non-goals before delivery.

Classify the task under
[ENGINEERING_POLICY.md](ENGINEERING_POLICY.md) before selecting workflows.
Level 2 requires the relevant specialist skill; Level 3 adds the applicable
evidence-review and panel workflow without making a skill an acceptance
authority.

Use `$tracktemplate-freecad-addon-research` before the source or documentation
sequence when work depends on current FreeCAD Addon guidance. Its output is
research evidence, not implementation, validation or project acceptance.

Prefer explicit invocation for:

- release, phase-closure or true authority-transfer reviews;
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

For IDE workspace alignment:

```text
Git-owned read-only worktree, branch, reachability and pull-request evidence
    ↓
$tracktemplate-ide-workspace-alignment
    ↓
separately authorised Git reconciliation when needed
    ↓
repeat file/Git comparison and obtain any operator-only UI confirmation
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

For deliberate worktree retirement:

```text
show accepted-history containment and tracked cleanliness
    ↓
make an inventory of ignored and other local-only state
    ↓
classify every item and show necessary preservation or disposal basis
    ↓
stop for ambiguous or uniquely owned state
    ↓
examine the exact read-only audit and authority again
    ↓
use normal Git worktree removal without force
    ↓
afterwards, remove only the merged local branch that is safe
```

For an architecture decision:

```text
$tracktemplate-architecture-review
    ↓
$tracktemplate-api-design when a public or stored contract changes
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
$tracktemplate-freecad-addon-research when the boundary is FreeCAD-specific
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
$tracktemplate-api-design when a public or stored contract changes
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
$tracktemplate-occt-geometry for an explicit Validate/Export boundary
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
select one authorised evidenced gap; state outcome, criterion, level,
regression risk, acceptance evidence, explicit non-goals and why it outranks
credible maintenance, evidence, risk-reduction and authorised alternatives
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
bounded blocker repair only, at most two passes
    ↓
reconcile claimed, present, validated and independently accepted state
against the exact phase exit; preserve non-claims
    ↓
$tracktemplate-publish in review-frozen mode
    ↓
plain-English owner acceptance pack
```

A clear routine outcome may skip chief of staff, and a trivial isolated edit may
skip technical lead. When no worthwhile authorised phase-moving outcome exists,
continue stops on clean protected `main` before branch creation. A newly
published draft is never marked ready or merged in the same invocation.
Delegated publication may not mutate the reviewed source; an exact-head CI
blocker returns to the same two-pass validation-and-review loop.

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

For a security-sensitive change:

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

For a beta or release-candidate audit:

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
when available and proportionate; provide the request, canonical requirements,
complete diff, raw validation evidence and known unperformed checks. Do not
prime the reviewer with the intended verdict. Disclose same-agent review or
another independence limitation. After an adverse verdict, separate authorised
remediation from that pass, rerun affected validation and review the resulting
complete diff again.

Disposition each actionable staff-review finding as `BLOCKER`,
`REQUIRED_BEFORE_EXIT`, `BACKLOG` or `OPTIONAL`. Only a `BLOCKER` returns
automatically to technical delivery. Outside an active
`$tracktemplate-continue` cycle, a `REQUIRED_BEFORE_EXIT` item may join the same
cycle only when it directly prevents the selected outcome or proof. During an
active continuation cycle, only a `BLOCKER` may return to implementation;
`REQUIRED_BEFORE_EXIT`, `BACKLOG` and `OPTIONAL` items do not join that cycle.
When progress is unclear or an active continuation cycle detects a loop, pass
the review as read-only chief-of-staff input rather than allowing the reviewer
to choose the next objective.

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
| [`reidemeister94/development-skills`](https://github.com/reidemeister94/development-skills/tree/92922f58f037191f2ccc909a69cbe297fc49efae), `92922f58f037191f2ccc909a69cbe297fc49efae`, MIT | Coding-agent workflow plugin with session-start and edit-time hooks | Adapt the useful standards-first, durable-rationale and resume principles through the existing authority map and local recovery skill. Adapt its explicit handoff idea through a local skill that writes only a temporary navigation packet and grants no Git, gate or product authority. Adapt its documentation-drift audit, changelog curation and bounded simplification ideas through the corresponding local skills, while preserving TrackTemplate's canonical owners, frozen evidence and release gates. Adapt explain-diff's visual idea into a separate read-only explanation skill whose sanitised HTML exists only in temporary storage and is never production evidence. Do not install its router, auto-formatter, mutation hooks, `docs/plans/` or `docs/chronicles/` model, and do not grant handoff, changelog, simplification or explanation work automatic commit, tag, bulk-rewrite or release authority. |
| [`seb1n/awesome-ai-agent-skills`](https://github.com/seb1n/awesome-ai-agent-skills/tree/a6c8c0ef3c240faefe1b0b5cabe1567beaea60fd), `a6c8c0ef3c240faefe1b0b5cabe1567beaea60fd`, MIT | Broad catalogue of generic instruction skills | Use only as a discovery source and admit each idea after project-specific review. Adapt stable-workflow automation without generic schedulers, watchers, destructive moves or new dependencies; adapt licence analysis through the existing fail-closed source/data/media/output controls without categorical legal conclusions; and adapt the complete API/integration group into one local contract skill. Its conditional network reference covers client resilience, OAuth, webhooks and GraphQL without assuming REST, installing an SDK or service, or loading network guidance for ordinary Python/FreeCAD boundaries. From the code-and-development group, admit only systematic debugging as a separate causal-investigation skill. Code documentation, review, refactoring and testing duplicate stronger local skills; generic version-control guidance conflicts with repository recovery and Git-authority controls. Embedding/vector retrieval infrastructure remains unjustified. |
| [`pydantic/pydantic-ai`](https://github.com/pydantic/pydantic-ai/tree/ed0f40c0e5061722f7d9f579ed7efff1b74e3ea5), `ed0f40c0e5061722f7d9f579ed7efff1b74e3ea5`, MIT | Python agent framework repository with root/scoped instructions and project-specific skills | Adapt its context-first, responsibility-to-project and patch-as-evidence patterns. TrackTemplate already supplies the corresponding authority map and local skills; add scoped `AGENTS.md` only where a directory has genuinely different rules. Do not add the Pydantic AI package as a TrackTemplate or FreeCAD runtime dependency without a separately approved in-product agent capability and compatibility, security, data, cost and validation evidence. |
| A B Vijay Kumar, [Deep Dive SKILL.md Part 1](https://abvijaykumar.medium.com/deep-dive-skill-md-part-1-2-09fc9a536996) (published 2026-03-17) and [Part 2](https://abvijaykumar.medium.com/getting-deep-agents-to-work-with-skill-md-part-2-2-a65707eb5131) (published 2026-03-21), mutable web pages retrieved 2026-07-27, no reusable-content licence relied upon | Expository architecture and worked skill-building example, not project or platform authority | Adapt progressive disclosure, precise routing descriptions, conditional references, deterministic scripts, actionable diagnostics, validation loops and real-task iteration. No prose, sample code, dependencies, optional frontmatter or external package was copied. The unpinned pages remain research inputs only. |
| [Agent Skills specification](https://agentskills.io/specification) and [creator best practices](https://agentskills.io/skill-creation/best-practices), live open-standard pages retrieved 2026-07-27 | Primary format and design guidance; client support still varies | Enforce the below-500-line `SKILL.md` budget, direct one-level resource routing and real-task evaluation. Retain the current Codex-compatible two-field frontmatter subset, prefer project-specific gotchas over generic teaching, and do not create one skill per tool. |

## Agent-guidance validation

Optional agent-skill tooling is pinned in `requirements-dev.txt`. It is not
imported by TrackTemplate, required by FreeCAD or included in the Addon
artifact. Install it into the project virtual environment with:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

After changing `AGENTS.md`, `reference/AGENT_WORKFLOWS.md` or a repository skill,
run:

```bash
.venv/bin/python tests/validate_agent_guidance.py
```

The validator checks skill frontmatter, directory/name agreement, the
below-500-line `SKILL.md` budget, direct routing for every reference, script and
asset file, one-level reference layout, local links, the skill register and root
routing. Its progression-role checks are limited to required UI metadata,
section structure and direct composition links; they do not duplicate the skill
prose. The validator does not judge whether instructions are substantively
correct, route correctly under a model or prove project validation.

## Skill maintenance rules

- Give each skill one repeatable job and a concise trigger description.
- Ground new or revised skills in a real TrackTemplate task, correction,
  failure, contract or review pattern rather than generic advice.
- Put what the skill does and when it activates in the description. Add
  non-activation wording only for evidenced overlap; metadata consumes shared
  discovery context.
- Default to instruction-only. Add scripts only when the task is deterministic,
  reviewable, safe on a dirty working tree and materially better than existing
  project tools.
- Never import executable code from a third-party skill without inspecting its
  licence, behaviour, dependencies and file-system scope.
- Do not add MCP merely because a skill exists. MCP is appropriate only when the
  workflow needs controlled access to an external system or live data source.
- Link to the canonical project document rather than copying its detailed rules.
- Link every conditional resource file directly from `SKILL.md`, state when to
  load or execute it, and keep references one filesystem level deep. A link to
  a directory or from another resource does not establish direct reachability.
- Treat new skill behaviour as repository guidance: review it like code, keep the
  diff narrow and run the documentation, link and agent-guidance controls.
- Keep the skill register aligned with the directories under `.agents/skills/`.
- Do not allow two skills to claim the same primary responsibility without
  clearly defining their order and boundary.
- For a new skill or material trigger/workflow change, exercise natural prompts
  that should activate, should not activate and should compose. Inspect the
  execution path as well as the final answer; static validation is necessary
  but not a routing or output-quality evaluation.
- When a skill uncovers a durable project lesson, append it to
  `reference/LEARNING_FROM_EXPERIENCE.md` only after the lesson has evidence and
  leads to an accepted reusable adaptation.

A clean implementation or prose style is not enough for completion. Railway
correctness, recoverability, evidence quality and project authority remain
controlling.
