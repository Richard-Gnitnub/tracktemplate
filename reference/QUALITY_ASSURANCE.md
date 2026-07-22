# Quality Assurance

Status: **canonical QA audit completed on 2026-07-22 against start commit
`1bad4bf121a18ad0a82a2c7e259c14ad885fa01d`; residual risks remain open at
their named gates.**

## Audit boundary and verdict

This audit assessed repository controls, documentation ownership, source and
test health, the qualified FreeCAD runtime, local recovery readiness, Git and
GitHub safeguards, and the evidence supporting the current Phase 4 boundary.
The governing delivery status and live risk state remain in
[PROJECT_PLAN.md](PROJECT_PLAN.md); current implementation evidence remains in
[PHASE4_CANONICAL_STATE.md](PHASE4_CANONICAL_STATE.md).

Verdict: **operationally healthy for bounded Phase 4 foundation work, subject
to the existing fail-closed controls; not release-ready.** In particular, no
copied-target entity-family migrator may be enabled while QA-R01 is open, and
no later workflow, performance, output or release gate is waived by this
audit.

The audit directly executed the complete repository set of 35 standalone
validators and 10 headless FreeCAD validators present at its start. All
passed. The qualified runtime probe matched the exact accepted FreeCAD profile,
all three macro launchers parsed, the repository was clean and synchronized,
the required local source archive matched its accepted checksum, and the
internal Markdown-link audit found no broken file targets. The post-correction
validation adds one standalone QA control, bringing that set to 36.

This was not a new real-GUI workflow or performance-profile campaign, a legal
opinion, a backup/restore drill, or acceptance of a phase gate. Those
boundaries are retained under QA-R01, QA-R03 and QA-R04 below. Validation
obligations and evidence interpretation remain owned by
[VALIDATION.md](VALIDATION.md), [TESTING_POLICY.md](TESTING_POLICY.md), and
[PERFORMANCE_SOP.md](PERFORMANCE_SOP.md).

## What We Are Doing Well

| ID | Validated success | Evidence and pattern to standardise |
| --- | --- | --- |
| QA-W01 | Phase authority is explicit, evidence-gated and owner-accepted. | Keep live status in [PROJECT_PLAN.md](PROJECT_PLAN.md), accumulate evidence only in the open-phase record, and freeze accepted history. |
| QA-W02 | Railway correctness is protected by layered analytical, structural, FreeCAD, persistence, rollback and workflow oracles. | Continue selecting the applicable matrix from [VALIDATION.md](VALIDATION.md) and preserving oracle integrity under [TESTING_POLICY.md](TESTING_POLICY.md). |
| QA-W03 | Legacy references and the modular checkpoint are fingerprinted and separated by role. | Preserve the B14/B15/B16 roles and incremental parity boundary described in [ARCHITECTURE.md](ARCHITECTURE.md) and [MODULARISATION_PLAN.md](MODULARISATION_PLAN.md). |
| QA-W04 | Domain dependency direction and source growth have executable guards. | Run the structural controls before and after each extraction; treat metrics as warning signals rather than proof of maintainability. |
| QA-W05 | FreeCAD automation is isolated from everyday documents and verifies recoverable transactions and save/reopen behaviour. | Continue using disposable documents and copied fixtures under [RECOVERY_AND_BACKUP.md](RECOVERY_AND_BACKUP.md). |
| QA-W06 | Provenance, licensing, output status and railway terminology have distinct owners and fail-closed states. | Keep using [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md), [PROVENANCE.md](PROVENANCE.md), and [TERMINOLOGY.md](TERMINOLOGY.md) instead of informal assumptions. |
| QA-W07 | Git hygiene is strong: generated/private paths are excluded, the audited checkpoint was pushed, and protected `main` rejects force-push and deletion. | Retain narrow commits, review diffs, and use pushed checkpoints before risky work. |
| QA-W08 | Documentation already follows a single-owner/link-first lifecycle, and all internal Markdown file targets resolved during the audit. | Keep technical payloads in their owning documents and use the new QA validator to catch broken file links and risk-disposition drift. |

## What We Are Not Doing Well

Every item below is either corrected by the action matrix or represented in
the live QA risk log. A passing audit does not silently accept an open item.

| Finding | Condition and impact | Disposition |
| --- | --- | --- |
| QA-F01 | There is no independent different-device/off-site project backup and no restore drill. GitHub does not protect ignored FreeCAD documents, raw evidence or production output. | Open as QA-R01. |
| QA-F02 | The validation estate is comprehensive but locally orchestrated; GitHub has no required pull-request or status-check gate and the repository has no CI workflow. A change can therefore be pushed without an independent automated result. | Open as QA-R02. |
| QA-F03 | Test depth is deliberately uneven: accepted slices are strong, while several release-critical GUI, migration, exact-output and chair workflows remain partial or blocked. Headless success is not GUI acceptance. | Open as QA-R03. |
| QA-F04 | Current performance evidence is bounded and the full modular edit-through-export pipeline has neither complete measurements nor frozen numerical budgets. | Open as QA-R04. |
| QA-F05 | The repository has no root reader/onboarding guide. `AGENTS.md` is effective for development agents, but it is not an installation or operator entry point. | Open as QA-R05. |
| QA-F06 | `AGENTS.md` instructed maintainers to update a Phase 1 registry/inventory pair that the documentation lifecycle correctly freezes. That could have rewritten accepted historical evidence. | Corrected by QA-A01. |
| QA-F07 | QA conclusions, accumulated process lessons and residual-risk linkage had no dedicated canonical controls before this tranche. | Corrected by QA-A02, QA-A03, QA-A04 and QA-A05. |
| QA-F08 | The principal-risk catalogue named useful controls but did not assign treatments, accountable owners, deadlines or evidence-based effectiveness, so a planned policy could be mistaken for an effective control. | Corrected by QA-A07. |

## Action Matrix

These corrections were executed in this audit tranche. They alter process
controls only; they do not advance the Phase 4 progress bar or accept a
delivery gate.

| Action | State | Correction and evidence |
| --- | --- | --- |
| QA-A01 | Completed | Corrected [AGENTS.md](../AGENTS.md) so the accepted Phase 1 workflow registry/inventory remains frozen and later closure evidence goes to the current owners. |
| QA-A02 | Completed | Created this canonical, dated QA record with a bounded verdict and explicit finding disposition. |
| QA-A03 | Completed | Created [LEARNING_FROM_EXPERIENCE.md](LEARNING_FROM_EXPERIENCE.md) as a historical, non-live lesson ledger. |
| QA-A04 | Completed | Appended the live QA risk log to [PROJECT_PLAN.md](PROJECT_PLAN.md), with an exact treatment, accountable owner, required resolution, objective closure evidence and mandatory deadline for every unresolved finding. |
| QA-A05 | Completed | Added [validate_quality_assurance.py](../tests/validate_quality_assurance.py) and its command to [VALIDATION.md](VALIDATION.md); it fails on broken internal file links, missing finding disposition, risk-log drift, document-role drift, the corrected instruction regressing, or immutable B14/B15 hash drift. |
| QA-A06 | Completed | Re-ran the complete standalone and headless FreeCAD sets after the corrections and reviewed the final diff and repository hygiene. |
| QA-A07 | Completed | Converted every principal risk in [PROJECT_PLAN.md](PROJECT_PLAN.md) into an ID-controlled treatment register and a linked preventive/detective/recovery assurance matrix with accountable owners, mandatory targets, current effectiveness and next evidence. |

## Residual risk disposition

This table is a stable audit-to-risk cross-reference, not a second live risk
register. State changes and closure evidence must be recorded only in the
[PROJECT_PLAN.md QA audit risk log](PROJECT_PLAN.md#qa-audit-risk-log).

| Risk | Audit finding |
| --- | --- |
| QA-R01 | Independent backup and restore readiness is absent. |
| QA-R02 | Automated remote status enforcement is absent. |
| QA-R03 | Release-critical workflow evidence remains incomplete or manual. |
| QA-R04 | Full-pipeline performance evidence and budgets remain incomplete. |
| QA-R05 | Reader, installation and operator onboarding is absent. |

Future QA audits should append a dated result or superseding report and update
the live risk log; they should not rewrite this audit to imply that later
evidence existed on 2026-07-22.
