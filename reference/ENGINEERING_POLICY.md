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

<a id="tt-doc-001-tracktemplate-technical-documentation-profile"></a>

## TT-DOC-001 — TrackTemplate Technical Documentation Profile

Human comprehensibility is a governance control. TrackTemplate uses this
information order for work in a substantial cycle:

> Owner view → canonical information → proof/provenance

The owner view is a short presentation from canonical records. It must agree
with those records. The owner view must never give project authority
independently. Canonical documents contain requirements, state, and
decisions for their named subjects. Proof/provenance includes detailed
evidence, exact Git identities, validation results, reviews, and preservation
results.

If information occurs in more than one place, use a link to its one canonical
owner. Do not copy policy into a dashboard, evidence record, skill, or
report to make a competing owner. Only a Level 3 project-owner decision can
change the scope of this profile or its controlled status meanings.

### Normative controlled-writing standard

TrackTemplate uses
[ASD-STE100 Simplified Technical English, Issue 9](external/asd-ste100/README.md)
as the normative controlled-writing standard for English canonical technical
prose. The standard identity is ASD-STE100 Simplified Technical English,
Issue 9, dated 2025-01-15. The official standard is the normative external
reference.

Public summaries, model knowledge, and automatic validators do not show
conformance. A reviewer must use the official standard for a linguistic
conformance review.
Use the [official-source instructions](external/asd-ste100/README.md) to get
the standard. Report the source that you use. Those instructions own only the
local path and source priority. They do not own TrackTemplate documentation
policy.
Do not copy the standard or its controlled general dictionary into this
repository.

The standard applies to canonical technical prose that persons can read in:

- architecture
- engineering and governance policy
- current phase evidence
- decisions that use prose
- validation and recovery instructions
- technical procedures
- Learning from Experience
- documentation-profile requirements
- human-readable explanations in canonical registers
- substantial workflow and skill prose that gives technical instructions or
  requirements

Do not change exact machine data or externally controlled information only to
change its language. Keep these items exact when necessary:

- code
- API and schema identifiers
- JSON keys and machine values
- file and directory paths
- Git SHAs and hashes
- commands
- diagnostic strings and test sentinels
- external quotations
- standards titles and identifiers
- machine-generated logs and evidence

The text around these items must obey the applicable Issue 9 requirements.
Applicable TrackTemplate canonical prose must obey ASD-STE100 Issue 9.
TrackTemplate uses UK English spelling as its project spelling directive. This
directive uses the option in Issue 9 Rule 1.14. The directive changes spelling
only. It does not change the applicable Issue 9 vocabulary or grammar rules. It
does not change approved meanings, parts of speech, or technical-term controls.
Outside this scope, use concise UK English.

TrackTemplate uses applicable modular-information principles of ASD S1000D. It
does not claim S1000D conformance. This profile does not authorise this S1000D
infrastructure:

- S1000D XML
- a Common Source Database
- BREX
- data-module identifiers
- publication modules
- applicability engines
- XML migration
- a documentation database or service
- a generic content-management system

### Conformance terms

Use these conformance terms with their exact scopes:

| Term | Controlled meaning |
| --- | --- |
| **TT-DOC-001 conforming** | The named unit obeys all applicable TrackTemplate profile controls. New STE-governed prose and prose in a material edit must also have a recorded Issue 9 review. |
| **ASD-STE100 Issue 9 conforming** | A reviewer examined the named unit against the official Issue 9 standard. The conformance record gives the scope, result, technical terms, and limitations. |
| **ASD-STE100 Issue 9 conformance not verified** | No sufficient review against the official Issue 9 standard exists for the named unit. |
| **Externally certified or endorsed** | An external body gave the named certification or endorsement. TrackTemplate does not claim this state. |

A reviewer can use an automatic tool during a review. The tool cannot replace
the linguistic review or show Issue 9 conformance.

### Controlled governance meanings

Use these terms consistently. Keep a qualification beside the claim it limits.

| Term | Controlled meaning |
| --- | --- |
| **Pending** | The criterion or action does not have the necessary evidence or owner decision. Pending gives no authority. |
| **Evidenced** | The project admitted and keeps evidence for the named bounded criterion. Evidenced does not give wider acceptance or clearance. |
| **Accepted** | The project owner made an explicit decision. The decision applies only to its stated authority and exclusions. |
| **Blocked** | One or more stated conditions prevent the named action or decision. |
| **Finding** | A review or validation result must have a disposition. A finding does not change project state. |
| **Limitation** | A stated boundary applies to evidence, capability, or assurance. A limitation is not automatically a blocker. A reader must be able to see it. |
| **Unknown** | Evidence that the project keeps does not show the claim. Unknown does not mean accepted or rejected. |
| **Decision required** | The evidence or recommendation is ready for the named owner. The owner decision is absent. |

Keep facts, evidence, inferences, recommendations, and owner decisions
distinct. A fact is a state that a person can examine directly. Evidence is an
observation or result that the project keeps. An inference explains the
evidence. A
recommendation gives a proposed action or decision. Only an explicit owner
decision gives Level 3 authority.

Do not rename a persisted, API, schema, evidence or decision identifier for
readability.

### Controlled writing and owner view

Use the applicable Issue 9 rules and the approved project terminology. Keep
technical precision:

- use one principal requirement or fact in each sentence when possible
- use direct structures and identify the responsible actor
- use one controlled term for one governance concept
- place qualifications beside the claim they qualify
- use lists when conditions can fail separately
- do not use a vague reference when its subject is not clear
- use canonical links instead of copied authority
- label facts, evidence, inferences, recommendations, and owner decisions
  distinctly

For a substantial cycle, begin the result for the human owner with these
fields:

1. **Current state**
2. **What changed**
3. **What now works**
4. **Limitations/findings**
5. **Owner decision**
6. **Next action**

For a decision-relevant active-evidence entry, use this order:

1. Scope and current fact
2. Decisive evidence
3. Limitations or findings
4. Recommendation
5. Explicit owner decision and exclusions
6. Proof/provenance links

Omit an item only when it does not apply. Do not put different evidence and
authority states together to make the text shorter.

The owner must be able to see from this view whether the cycle succeeded,
the phase changed, a blocker exists, and a decision is necessary. The view must
also show whether another action has authority. Put applicable technical
provenance below the view. Short text must never change evidence or a
recommendation into acceptance.

### Terminology and migration boundary

[TERMINOLOGY.md](TERMINOLOGY.md) is the one project owner for TrackTemplate
technical nouns and technical verbs. Use an Issue 9 dictionary word or an
approved project technical term. Do not make a second terminology source.

These migration rules apply from the acceptance of TT-DOC-001:

- All new canonical technical prose in English must obey the applicable
  ASD-STE100 Issue 9 requirements.
- For a material edit, review the full logical unit that contains the change.
  Use the applicable Issue 9 requirements.
- Review live canonical prose in bounded migration cycles.
- Keep each non-conformance and readability finding in the record until a
  reviewer records its result.
- Do not change frozen history only to correct its Issue 9 style.
- Keep detailed technical provenance and all accepted limitations.

Before you add a skill or change its primary responsibility, map the
responsibility across the full skill catalogue. Add the behaviour to the
primary owner when possible. Add a skill only when one separate responsibility can
occur repeatedly and has no owner. Record its composition and non-ownership
boundaries.

Documentation simplification does not give a skill phase, production,
security, merge, release, acceptance, or project-owner authority. Semantic
validators prevent changes to these meanings. They do not freeze full
paragraphs. They do not use sentence-length checks as proof of linguistic
conformance.

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

Use the TT-DOC-001 owner view for a substantial cycle. Keep detailed evidence
below it. For compact technical provenance or a smaller change, use:

```text
Changed:
Validated:
GUI work outstanding:
Risks or authority changes:
```

Omit empty detail, but do not hide a failed, skipped or unavailable check. The
last field names any governance-budget exception and any owner decision still
required.
