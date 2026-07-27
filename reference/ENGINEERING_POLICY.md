# Engineering Policy

Status: **canonical governance, proportional-change and delivery-control
policy.**

## Purpose and ownership

This document owns the project-wide rules for proportional change, governance
budget, true gates, safety/risk panels, documentation lifecycle and completion
reporting. It does not own product architecture, live phase status, validation
commands, recovery procedure, licensing decisions or agent-skill routing.

Those subjects remain with:

- [ARCHITECTURE.md](ARCHITECTURE.md) and
  [MODULARISATION_PLAN.md](MODULARISATION_PLAN.md);
- [PROJECT_PLAN.md](PROJECT_PLAN.md) and the
  [current phase records](current/);
- [VALIDATION.md](VALIDATION.md) and [TESTING_POLICY.md](TESTING_POLICY.md);
- [RECOVERY_AND_BACKUP.md](RECOVERY_AND_BACKUP.md);
- [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md) and
  [PROVENANCE.md](PROVENANCE.md); and
- [AGENT_WORKFLOWS.md](AGENT_WORKFLOWS.md).

## Three change levels

Classify every task before work begins. Use the highest level reached by its
actual behaviour or authority, not its diff size or phase association.

### Level 1 — Routine

Examples include a typo or wording correction, an internal refactor with no
behaviour change, test cleanup, non-authoritative tooling and a small UI
presentation change.

Required: the relevant test, complete diff review and a concise commit message.
Do not update current phase evidence, run a risk panel or change the project
plan unless the task genuinely changes status; if it does, reclassify it before
retaining that change. A read-only task is Level 1, but creates no artificial
test or commit when no repository change is retained.

### Level 2 — Behavioural

Examples include a railway calculation change, canonical-state change,
persistence or invalidation change, new FreeCAD object behaviour, performance
optimisation and workflow migration within already accepted authority.

Required: the relevant specialist skill, automated and applicable FreeCAD/GUI
validation, exactly one concise entry in
[current/PHASE_EVIDENCE.md](current/PHASE_EVIDENCE.md), and complete diff
review. A Level 2 task does not update the project plan or run a risk panel; a
change that transfers authority must be reclassified as Level 3 first.

### Level 3 — Authority or release

Examples include closing a phase, enabling legacy migration, retiring an
accepted oracle, declaring an output or chair package cleared, changing
governance or licensing authority, packaging a beta or release candidate, and
an irreversible repository or data operation.

Required: full evidence review, a safety/risk panel, an explicit project-owner
decision and a project-plan update. Record the panel and decision once in the
current evidence and structured decision register.

The levels control governance, not technical evidence selection. For example,
a Level 1 UI presentation change still requires any GUI check selected by
[VALIDATION.md](VALIDATION.md).

## Governance budget

For each implementation tranche:

> Governance changes must not exceed the implementation change unless the task
> itself changes governance, licensing, safety or release authority.

Count policy, plan, risk, decision, evidence-template and guidance changes as
governance. Direct implementation evidence in the one current phase record is
not an invitation to restate all repository invariants.

When the governance side is larger, the completion report must name the
exception and explain which authority changed. “This is the current phase” is
not a valid exception.

## True gates and safety/risk panels

A gate is a decision that transfers, expands, retires or irreversibly changes
project authority. A tranche label, milestone label, review packet or current
phase association does not make work a gate.

Every Level 3 task is a true gate and requires a safety/risk panel. Level 3
covers only:

1. phase or release closure, including beta or release-candidate packaging;
2. a legacy migration family or window becoming supported;
3. retirement of an accepted oracle or rollback authority;
4. production-output or chair-package clearance;
5. governance, licensing or provenance authority changes; or
6. irreversible or destructive repository, data or external operations.

Do not run a panel for Level 1 or Level 2 work. Retiring development-only
duplication while the accepted oracle and rollback evidence remain is not
accepted-oracle retirement and is not a Level 3 gate.

The panel occurs before the authority transfer. The project owner chairs and
decides; the change owner presents; a QA/risk reviewer challenges the evidence.
Use a reviewer independent of implementation for Critical risk, destructive
work, rights clearance or when the project owner requires one.

The only outcomes are **Proceed**, **Proceed with bounded conditions**, and
**Do not proceed**. Record:

- exact decision and source state;
- participants, roles and independence;
- linked evidence reviewed;
- due risks and changed control effectiveness;
- unresolved dissent, unknowns and exceptions;
- recommendation and bounded conditions with owners/deadlines;
- project-owner decision and date; and
- the resulting authority and explicit exclusions.

The narrative belongs once in
[current/PHASE_EVIDENCE.md](current/PHASE_EVIDENCE.md). The structured decision
belongs in [current/gate-decisions.json](current/gate-decisions.json).
[PROJECT_PLAN.md](PROJECT_PLAN.md) carries only a short linked decision summary.

## Documentation lifecycle

The live control paths are fixed:

- [PROJECT_PLAN.md](PROJECT_PLAN.md) — phase status, exit-condition status, live
  risk summary, owner-decision summary and evidence links only;
- [current/PHASE_EVIDENCE.md](current/PHASE_EVIDENCE.md) — all detailed evidence
  for the open phase;
- [current/risks.json](current/risks.json) — detailed live risks; and
- [current/gate-decisions.json](current/gate-decisions.json) — structured
  current owner decisions.

A Level 1 change updates only its implementation, relevant test and any document
that directly owns the corrected wording; it does not update current phase
evidence or the plan. A Level 2 change adds exactly one concise current-evidence
entry. A Level 3 change records its full evidence review, panel and owner
decision, updates the structured registers, and updates the project-plan
dashboard. Change another reference document only when its owned policy,
contract or responsibility changes.

At phase close:

1. finish and accept the current evidence;
2. move it to `reference/history/phase-closeouts/PHASE<N>_CLOSEOUT.md`;
3. archive closed risk and decision records as applicable; and
4. create clean current records for the next phase.

Historical inventories, foundations, closeouts, dated audits and benchmark
reports are frozen evidence. Routine alignment must not rewrite them to resemble
the current project. Validate only their continued existence, required internal
links, accepted hashes and accepted status. Correct a frozen record only for a
demonstrated factual error or an explicitly accepted scope change.

Physical archive moves are separate migrations because paths and accepted
hashes may change. Until such a migration is accepted, historical records may
remain frozen at their existing paths; see [history/README.md](history/README.md).

## CI and manual evidence

Tracked CI owns repeatable clean-run checks for:

- Python and macro parsing;
- the standalone test and contract matrix;
- dependency direction;
- frozen-oracle and frozen-record hashes;
- Markdown links; and
- project-progress/current-register consistency.

Normal reports do not restate each automated invariant. Report the CI result or
the equivalent local matrix once. CI does not replace qualified FreeCAD,
real-GUI, operator workflow, exact-output, performance, backup/restore,
licensing judgement or owner acceptance where those boundaries apply.

## Completion report

Use this compact form:

```text
Changed:
Validated:
GUI work outstanding:
Risks or authority changes:
```

Omit empty detail, but do not hide a failed, skipped or unavailable check. The
last field names any governance-budget exception and any owner decision still
required.
