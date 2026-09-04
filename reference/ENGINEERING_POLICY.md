# Engineering Policy

Status: **canonical governance, proportional-change, and delivery-control
policy.**

## Purpose and ownership

This document owns the project-wide rules for proportional change and the
governance budget. It also owns true gates, safety/risk panels, the
documentation lifecycle, and completion reports.

This document does not own product architecture or live phase status. It does
not own validation commands, recovery procedures, licence decisions, or agent
skill routing.

These documents own those subjects:

- [ARCHITECTURE.md](ARCHITECTURE.md) owns product architecture.
- [MODULARISATION_PLAN.md](MODULARISATION_PLAN.md) owns source organisation.
- [PROJECT_PLAN.md](PROJECT_PLAN.md) owns phase status.
- The [current phase records](current/) own current evidence and decisions.
- [VALIDATION.md](VALIDATION.md) and [TESTING_POLICY.md](TESTING_POLICY.md) own
  validation.
- [RECOVERY_AND_BACKUP.md](RECOVERY_AND_BACKUP.md) owns recovery procedures.
- [LICENSING_BOUNDARIES.md](LICENSING_BOUNDARIES.md) and
  [PROVENANCE.md](PROVENANCE.md) own rights and lineage.
- [AGENT_WORKFLOWS.md](AGENT_WORKFLOWS.md) owns agent skill routing.

## Three change levels

Classify each task before work starts. Use the highest level that its behaviour
or authority reaches. Diff size and phase association do not set the level.

### Level 1 — Routine

Level 1 includes a wording correction and an internal refactor that does not
change behaviour. It also includes test cleanup, non-authoritative tools, and a
small UI presentation change.

Run the relevant test. Review the complete diff. Use a short commit message.
Do not update current phase evidence or run a risk panel. Do not change the
project plan unless the task changes status. If status changes, reclassify the
task before retention.

A read-only task is Level 1. It does not require an artificial test or commit
when the repository does not change.

### Level 2 — Behavioural

Level 2 includes a railway calculation change and a canonical-state change. It
also includes persistence, invalidation, FreeCAD object behaviour, performance,
and an authorised workflow migration.

Use the relevant specialist skill. Run automated validation and each applicable
FreeCAD or GUI check. Add exactly one short entry to
[current/PHASE_EVIDENCE.md](current/PHASE_EVIDENCE.md). Review the complete
diff.

Do not update the project plan or run a risk panel for Level 2. If the change
transfers authority, reclassify it as Level 3 before retention.

### Level 3 — Authority or release

Level 3 includes phase closure and an enabled legacy migration. It includes
retirement of an accepted oracle. It also includes output clearance, chair
package clearance, and a governance or licence authority change.

Beta packaging and packaging for release qualification are Level 3. An irreversible or
destructive repository, data, or external operation is also Level 3.

Complete the full evidence review. Run a safety/risk panel. Get an explicit
project-owner decision. Update the project plan.

Record the panel and decision once in the current evidence. Record the decision
once in the structured decision register.

These levels control governance. They do not select technical evidence. For
example, a Level 1 UI change can still require a GUI check from
[VALIDATION.md](VALIDATION.md).

## Governance budget

For each implementation bounded cycle:

> Governance changes must not exceed the implementation change unless the task
> changes governance, licensing, safety, or release authority.

Policy, plan, risk, decision, evidence-template, and guidance changes are
governance changes. Direct implementation evidence belongs in one current
phase record. Do not repeat repository rules in that record.

If governance changes are larger, name the exception in the completion report.
State the authority that changed. “This is the current phase” is not a valid
exception.

## True gates and safety/risk panels

A gate transfers, expands, retires, or irreversibly changes project authority.
A bounded-cycle label or milestone label does not make a gate. A review packet or
current phase association also does not make a gate.

Every Level 3 task is a true gate. Each true gate requires a safety/risk panel.
Level 3 contains only these changes:

1. Phase or release closure, including beta packaging or packaging for release
   qualification.
2. Support for a legacy migration family or window.
3. Retirement of an accepted oracle or rollback authority.
4. Production-output or chair-package clearance.
5. A governance, licence, or provenance authority change.
6. An irreversible or destructive repository, data, or external operation.

Do not run a panel for Level 1 or Level 2. Removal of development-only
duplication is not retirement of an accepted oracle. The accepted oracle and
rollback evidence must remain.

The panel occurs before the authority transfer. The project owner chairs and
decides. The change owner presents. A QA/risk reviewer challenges the evidence.

Use a reviewer independent of implementation for Critical risk. Also use that
reviewer for destructive work, rights clearance, or a project-owner request.

The panel has only these outcomes:

- **Proceed**
- **Proceed with bounded conditions**
- **Do not proceed**

Record this information:

- The exact decision and source state.
- The participants, roles, and independence.
- The evidence that the panel reviewed.
- The due risks and changed control effectiveness.
- The unresolved dissent, unknowns, and exceptions.
- The recommendation and bounded conditions with owners and deadlines.
- The project-owner decision and date.
- The resulting authority and explicit exclusions.

Put the narrative once in
[current/PHASE_EVIDENCE.md](current/PHASE_EVIDENCE.md). Put the structured
decision in [current/gate-decisions.json](current/gate-decisions.json).
[PROJECT_PLAN.md](PROJECT_PLAN.md) contains only a short linked decision
summary.

<a id="tt-doc-001-tracktemplate-technical-documentation-profile"></a>

## TT-DOC-001 — TrackTemplate Technical Documentation Profile

Human understanding is a governance control. TrackTemplate uses this
information order for a substantial cycle:

> Owner view → canonical information → proof/provenance

The owner view is a short presentation from canonical records. It must agree
with those records. It must not give project authority independently.

Canonical documents contain rules, state, and decisions for their named
subjects. Proof/provenance contains detailed evidence, exact Git identities,
validation results, reviews, and preservation results.

If information occurs in more than one place, link to its one canonical owner.
Do not copy policy into a dashboard, evidence record, skill, or report.

Only a Level 3 project-owner decision can change this profile. That decision
can change its bounded scope or controlled status meanings.

### Normative controlled-writing standard

TrackTemplate uses
[ASD-STE100 Simplified Technical English, Issue 9](external/asd-ste100/README.md)
for canonical technical prose in English. Its identity is ASD-STE100 Simplified Technical
English, Issue 9, dated 2025-01-15. The official standard is the normative
external reference.

Public summaries, model knowledge, and automatic validators do not show
conformance. A reviewer uses the official standard for a linguistic conformance
review.

Use the [official-source instructions](external/asd-ste100/README.md) to get the
standard. Report the source that you use. Those instructions own the local path
and source priority. They do not own TrackTemplate documentation policy.

Do not copy the standard into this repository. Do not copy its controlled
general dictionary into this repository.

### Retrieval and assurance authority boundary

The STE lookup only makes retrieval faster. It does not define or limit the
applicable rule set. All applicable writing rules and the controlled vocabulary
are mandatory.

An agent must not claim conformance because of a lookup result. An agent must
not claim conformance because the deterministic pre-check has no finding. A
`PASS` result from automatic validation also does not show conformance.

The STE lookup selects the source text that an agent reads for a task. It does
not select the applicable writing rules.

Use the [STE lookup workflow](external/asd-ste100/README.md#local-retrieval-interface)
for targeted retrieval. Review the complete logical unit against the applicable
requirement set. Use the official source to resolve each material uncertainty.

### Documentation Review lifecycle

Use this lifecycle for each material change to canonical technical prose:

> author → freeze scope → one Documentation Review → optional exact reviewed
> correction once → one final deterministic validation → complete or owner stop

The author writes the exact candidate and freezes a clean Git commit. The STE
lookup derives the frozen review scope from Git.

One independent Documentation Reviewer reviews the complete frozen review
scope. The reviewer uses all applicable Issue 9 writing rules in the official
source. This Documentation Review is the only linguistic conformance review.

The reviewer returns one complete verdict. The verdict is `ACCEPT`,
`APPROVED_WITH_EXACT_CORRECTIONS`, or `BLOCKED`.

For `APPROVED_WITH_EXACT_CORRECTIONS`, the reviewer gives all exact replacement
wording in the same review. Apply those replacements once against verified
preimages. Do not add or change other wording. Do not run a second
Documentation Review.

A `BLOCKED` verdict creates no accepted-state proposal. Return the change to
the owner.

Each schema version 2 result records the complete `blockers` array. The result
confirms that the array is complete. `ACCEPT` and
`APPROVED_WITH_EXACT_CORRECTIONS` use an empty `blockers` array. `BLOCKED` uses
a nonempty `blockers` array.

Each item in `blockers` records its exact path and frozen logical-unit identity.
It also records the finding and applicable formal Issue 9 rule identifiers.

The review receipt preserves the complete `blockers` array. It also preserves
the exact candidate and frozen review scope bindings. A `BLOCKED` result with
an empty `blockers` array is invalid.

After the review or approved correction, run one final deterministic
validation. It proves these identities:

- Source.
- Exact candidate.
- Frozen review scope.
- Receipt.
- Accepted state.
- Final content.

It also proves that no unreviewed change remains. It does not judge linguistic
conformance. If a failure remains, return to the owner. This includes a failure
in wording, controlled meaning, identity, or bounded scope.

Use these rules for the frozen review scope:

- Do not review an untouched legacy document.
- For the first material edit of an unreviewed legacy document, review the
  complete document.
- After acceptance, use the last accepted document identity to find each
  material change.
- Review only the complete logical units that contain those changes.
- Do not review unchanged accepted canonical prose again.

Keep durable review state at document level. Record the last accepted document
identity, source identity, and review receipt.

Do not keep persistent sentence, paragraph, or logical-unit workflow state.
Git derives the frozen review scope from the last accepted document identity.

The standard applies to canonical technical prose that persons can read in:

- Architecture.
- Engineering and governance policy.
- Current phase evidence.
- Decisions that contain canonical prose.
- Validation and recovery instructions.
- Technical procedures.
- Learning from Experience.
- Documentation-profile rules.
- Human-readable explanations in canonical registers.
- Substantial workflow and skill wording that gives technical instructions.

Do not change exact machine data or externally controlled information only to
change its wording. Keep these items exact when necessary:

- Code.
- API and schema identifiers.
- JSON keys and machine values.
- File and directory paths.
- Git SHAs and hashes.
- Commands.
- Diagnostic strings and test sentinels.
- External quotations.
- Standards titles and identifiers.
- Machine-generated logs and evidence.

Wording around these items must obey the applicable writing rules. Applicable
TrackTemplate canonical technical prose must obey ASD-STE100 Issue 9.

TrackTemplate uses UK English. Rule 1.14 permits this instruction. It does not
change the applicable Issue 9 vocabulary or grammar rules. It does not change
approved meanings, parts of speech, or technical-term controls.

Outside this bounded scope, use short UK English.

TrackTemplate uses applicable modular-information principles of ASD S1000D. It
does not claim S1000D conformance. This profile does not authorise this S1000D
infrastructure:

- S1000D XML.
- A Common Source Database.
- BREX.
- Data-module identifiers.
- Publication modules.
- Applicability engines.
- XML migration.
- A documentation database or service.
- A generic content-management system.

### Conformance terms

Use these terms with their exact bounded scopes:

| Term | Controlled meaning |
| --- | --- |
| **TT-DOC-001 conforming** | The named unit obeys all TrackTemplate profile controls. New canonical technical prose and each material edit have a recorded Issue 9 review. |
| **ASD-STE100 Issue 9 conforming** | A reviewer examined the named unit against the official Issue 9 standard. The record gives the bounded scope, result, technical terms, and limitations. |
| **ASD-STE100 Issue 9 conformance not verified** | The named unit has no sufficient review against the official Issue 9 standard. |
| **Externally certified or endorsed** | An external body gave the named certification or endorsement. TrackTemplate does not claim this state. |

A reviewer can use an automatic tool during a review. The tool cannot replace
the linguistic conformance review. It cannot show Issue 9 conformance.

### Controlled governance meanings

Use these terms consistently. Keep each qualification beside the claim that it
limits.

| Term | Controlled meaning |
| --- | --- |
| **Pending** | Necessary evidence or an owner decision is absent. Pending gives no authority. |
| **Evidenced** | The project admitted and keeps evidence for the named bounded criterion. Evidenced gives no wider acceptance or clearance. |
| **Accepted** | The project owner made an explicit decision. The decision applies only to its stated authority and exclusions. |
| **Blocked** | One or more stated conditions prevent the named action or decision. |
| **Finding** | A review or validation result requires a disposition. A finding does not change project state. |
| **Limitation** | A stated limit applies to evidence, capability, or assurance. A limitation does not automatically prevent a named action or decision. The reader must see it. |
| **Unknown** | Kept evidence does not show the claim. Unknown does not mean accepted or rejected. |
| **Decision required** | Evidence or a recommendation is ready for the named owner. The owner decision is absent. |

Keep facts, evidence, inferences, recommendations, and owner decisions
separate:

- A fact is a state that a person can examine directly.
- Evidence is an observation or result that the project keeps.
- An inference explains the evidence.
- A recommendation proposes an action or decision.
- Only an explicit owner decision gives Level 3 authority.

Do not rename a persisted identifier for readability. This rule also applies to
API, schema, evidence, and decision identifiers.

### Controlled writing and owner view

Use the applicable Issue 9 writing rules and approved project terminology.
Keep technical precision:

- Use one principal requirement or fact in each sentence when possible.
- Use direct structures and identify the responsible actor.
- Use one controlled term for one governance concept.
- Put each qualification beside the claim that it limits.
- Use lists when conditions can fail separately.
- Do not use a vague reference when its subject is not clear.
- Use canonical links instead of copied authority.
- Identify facts, evidence, inferences, recommendations, and owner decisions.

For a substantial cycle, begin the result with this owner view:

1. **Current state**
2. **What changed**
3. **What now works**
4. **Limitations/findings**
5. **Owner decision**
6. **Next action**

For a decision-relevant current-evidence entry, use this order:

1. Bounded scope and current fact.
2. Decisive evidence.
3. Limitations or findings.
4. Recommendation.
5. Explicit owner decision and exclusions.
6. Proof/provenance links.

Omit an item only when it does not apply. Do not combine different evidence
and authority states to make the result shorter.

The owner view must show whether the cycle succeeded. It must show whether the
phase changed, the result is Blocked, or a decision is necessary. It
must also show whether another action has authority.

Put applicable technical provenance below the owner view. A short result must
not change evidence or a recommendation into acceptance.

### Terminology and migration authority boundary

[TERMINOLOGY.md](TERMINOLOGY.md) is the one project owner for TrackTemplate
technical nouns and technical verbs. Use an Issue 9 dictionary word or an
approved project technical term. Do not make a second terminology source.

These migration rules apply from the acceptance of TT-DOC-001:

- All new canonical technical prose in English must obey the applicable Issue 9 writing
  rules.
- For a material edit, review the complete logical unit that contains the
  change.
- Use the applicable requirement set for that review.
- Review live canonical prose in bounded migration cycles.
- Keep each non-conformance or readability finding until a reviewer records
  its result.
- Do not change frozen history only to correct its Issue 9 style.
- Keep detailed technical provenance and all accepted limitations.

Before adding a skill, map its responsibility across the full skill catalogue.
Do the same before changing a skill's primary responsibility.

Add the behaviour to the primary owner when possible. Add a skill only if one
separate responsibility can occur repeatedly and has no owner. Record its
composition and non-ownership authority boundaries.

Documentation simplification gives no security/recovery-review authority. It
gives no phase, production, merge, release, acceptance, or project-owner authority.

Semantic validators protect these controlled meanings. They do not freeze full
paragraphs. Sentence-length checks do not prove linguistic conformance.

<a id="technical-documentation-management-plan"></a>

## Technical Documentation Management Plan

This section is the TrackTemplate Technical Documentation Management Plan
(TDMP). It owns technical-documentation management for the complete life of a
technical document. It does not own the technical subject in that document.

The complete technical-document lifecycle is:

> identify the need → classify → assign ownership → plan → understand once →
> write once → check once → improve once → freeze once → review once →
> validate once → finish the D-GOV-015 lifecycle → complete the non-linguistic
> quality and publication review → establish a controlled baseline → make
> available → use → maintain → change under control → supersede or retire →
> preserve required history

The [Documentation Review lifecycle](#documentation-review-lifecycle) is one
bounded part of this lifecycle. D-GOV-015 remains authoritative for that part.
It supplies the one linguistic review and the final deterministic validation.
The TDMP does not create a second linguistic-review lifecycle.

### Document need and initiation

A technical-document need starts when one of these items changes or has a
documented deficiency:

- Product behaviour.
- Architecture.
- Engineering policy.
- Validation or recovery requirements.
- A project decision.
- A technical procedure.
- An accepted Learning from Experience adaptation.
- Controlled technical documentation.

The Technical Author Lead examines the need with the applicable subject owner.
They select one result:

- Create a new technical document.
- Make a material change to an existing technical document.
- Make a non-material correction.
- Make no documentation change.

Create a new document only when no existing canonical owner is correct. Put
new information in the existing canonical owner when that owner is correct.
Do not use routine linguistic improvement as a technical-document need.

### Document classification

Classify the technical document before work on its content starts. Record the
classification in the work item or existing evidence that controls the change.
Do not create a second document register for the classification.

The classification identifies these items when they apply:

- Canonical or non-canonical status.
- Technical-document type. Use the existing document class.
- Canonical owner.
- Technical or governance subject owner.
- ASD-STE100 Issue 9 applicability.
- Legacy status and the last accepted review state.
- Exact-content exclusions.
- Required review and validation.
- Repository integration or other publication boundary.

The technical-document type is its existing document class. Use one of these
classes:

- Live status.
- Architecture.
- Plan or policy.
- Procedure.
- Evidence or audit.
- Historical record.
- Specification or inventory.
- Closeout.
- Guidance.

The classification determines the applicable workflow.

Non-canonical material follows its existing evidence, transient-work, or
preservation route. It must link to the current canonical owner when readers
can mistake its status. It must not present itself as current authority.

A material change affects technical meaning, authority, required use,
ownership, scope, status, evidence, or a controlled instruction. A
non-material correction changes none of those items. Examples are a spelling
correction, a format correction, or a repaired link with unchanged meaning.
Use the highest applicable [change level](#three-change-levels).

### Ownership and authority

Every controlled technical document has one identified canonical owner. This
TDMP owns technical-documentation management. The Technical Author Lead owns
technical-documentation authoring, delivery, and maintenance coordination.

The applicable technical or governance owner continues to own the subject.
That owner supplies the required technical meaning and records its acceptance.
The Technical Author Lead does not become the technical authority for that
subject.

The Documentation Reviewer owns only the one linguistic verdict. Validation
owns only its stated result. The applicable change authority records
controlled-baseline acceptance. These roles cannot give their own work a
different authority unless existing authority expressly permits that result.

### Documentation planning

Before content work starts, the Technical Author Lead records or confirms:

- Purpose.
- Intended user or consumer.
- Required technical meaning.
- Applicable canonical authorities.
- Source information.
- Terminology.
- Document scope.
- Change scope.
- ASD-STE100 Issue 9 applicability.
- Review requirement.
- Validation requirement.
- Expected controlled-document result.

Use the smallest documentation intervention that satisfies the identified
need. Keep information in its canonical owner and use links to other owners.

### Authoring and review

For new or materially changed canonical technical prose, the Technical Author
Lead automatically owns this route:

> understand once → write once → check once → improve once → freeze once →
> review once → validate once → finish

The understand step confirms the plan, authority, meaning, and terms. The write
step produces all affected complete logical units. The check step examines
technical accuracy, ownership, terms, exact content, links, and deterministic
pre-check results. It is not a linguistic Documentation Review.

The improve step applies one complete author-side correction pass before
freeze. Apply TT-DOC-001, TT-DOC-002, and D-GOV-015 exactly throughout this
route. The Technical Author Lead then freezes one exact candidate.

One independent Documentation Reviewer examines the Git-derived frozen review
scope. The reviewer returns the one D-GOV-015 verdict. Apply exact reviewed
corrections once only when that verdict permits them. Then run the one final
deterministic validation. Do not run another linguistic review.

The finish step supplies the exact candidate, Documentation Review, final
validation, limitations, and required authority. It completes the bounded
D-GOV-015 lifecycle. It does not establish controlled-baseline acceptance.

After finish, give the exact validated candidate to one fresh read-only
non-linguistic quality and publication review. This review examines
implementation quality, limitations, authority boundaries, and publication
readiness. It does not repeat Documentation Review or change its verdict.

A non-material correction uses proportionate review and validation. If its
scope becomes material, reclassify it before retention and use the complete
route above.

### Lifecycle states

Use existing Git and canonical records to distinguish these states:

| State | Controlled meaning |
| --- | --- |
| **Draft** | Content work has no frozen exact candidate. It is not current controlled documentation. |
| **Frozen review candidate** | Git identifies the exact candidate and review scope. It is not current controlled documentation. |
| **Reviewed** | The one Documentation Review has a recorded verdict. The verdict alone does not establish a controlled baseline. |
| **Validated** | The applicable deterministic validation passed for the exact reviewed content. Validation alone does not establish a controlled baseline. |
| **Accepted/controlled baseline** | The applicable authority recorded acceptance of the exact content after all required reviews and final deterministic validation. This is the comparison point for later change. |
| **Superseded** | An accepted replacement owns the current information. The earlier document is historical evidence and is not current authority. |
| **Retired** | Evidence shows that the document owns no required current information. It is not current authority. |
| **Frozen historical evidence** | The repository preserves dated evidence and its accepted meaning. It is not live project authority. |
| **Failed experimental candidate** | The candidate did not become a current controlled baseline. Preserve its exact review receipt and accepted-state proposal status. It is not current authority. |

A draft, commit, review verdict, validation result, or pull request does not
establish an accepted/controlled baseline. The applicable authority must
record acceptance of the exact content.

### Controlled baseline

Establish the controlled baseline only after the Documentation Review, final
deterministic validation, and required post-validation non-linguistic quality
and publication review pass. The applicable change authority must record
acceptance of the exact document.

Record only durable data that existing authority requires. This can include:

- Document identity.
- Accepted Git commit or blob identity.
- Source identity.
- Documentation Review receipt.
- Applicable decision or adoption authority.

For D-GOV-015 review scope, `reference/ste-review-state.json` records the last
accepted document identity, source identity, and review receipt. Git and the
existing decision and evidence records supply the other necessary trace. Do
not add sentence, paragraph, or logical-unit workflow state. Do not create a
new document-management database when these records are sufficient.

### Publication and availability

Make an accepted technical document available through its normal repository
integration or publication route. Normal repository integration makes the
accepted baseline current and available for repository use. The classification
identifies that boundary. A separate external publication follows only when it
applies and has its own authority. An author-created or author-committed
document is not controlled for that reason alone.

The normal route keeps these states separate: draft, frozen review candidate,
reviewed, validated, accepted/controlled baseline, superseded, and retired.
Use protected repository state and applicable canonical records to identify
the current controlled document.

### Use

The controlled technical document is the applicable human-readable source for
its stated purpose. The authority hierarchy in this TDMP and the named subject
owners continue to apply.

A user or agent must be able to identify:

- Whether the document is current.
- Its canonical owner.
- A controlling higher authority, when one applies.
- Its accepted baseline.
- A material limitation that affects its use.

Use the document status, canonical links, accepted Git identity, review state,
and applicable decisions to supply this information. Keep a material
limitation beside the claim that it limits. Do not let an obsolete document or
a failed candidate appear to be current controlled documentation.

### Maintenance

The Technical Author Lead manages document maintenance. Start maintenance only
for a genuine technical-document need. Do not start it for routine linguistic
polishing.

Do not periodically review accepted unchanged prose because another reviewer
or model could change its wording. Keep the documentation estate aligned with
material changes to the product, architecture, governance, and technical
authorities. When another canonical owner makes a document stale, route the
resulting need through this TDMP.

### Change control

Compare every proposed change to the accepted controlled baseline. Use Git,
the accepted document identity, and the applicable canonical records for that
comparison. Classify the result as material or non-material before content
work starts.

For a material change to canonical technical prose:

1. Route the complete change through the Technical Author Lead.
2. Derive the required review scope from the accepted baseline and Git.
3. Review only the required complete logical units after a baseline exists.
4. Apply the one-review D-GOV-015 lifecycle.
5. Complete the required post-validation non-linguistic quality and publication
   review.
6. Establish a new controlled baseline only after review, validation, and
   applicable acceptance.

Do not reopen unrelated accepted prose. An improvement to an assurance method
does not give authority to reopen accepted history. A non-material correction
uses its proportionate change level and does not become routine re-review.

### Legacy technical documentation

Do not retrospectively rewrite an untouched legacy document. A first material
change can start a baseline review. If that document has no accepted
ASD-STE100 baseline, review the complete document as D-GOV-015 requires.

After acceptance, manage that document as controlled reviewed documentation.
Git then derives only the materially changed complete logical units for a later
review.

### Supersession

Supersede a controlled technical document only when an accepted replacement
owns its required current information. Before supersession:

1. Identify the replacement authority.
2. Show that required current information was retained or deliberately
   replaced.
3. Update applicable references.
4. Mark the earlier document so that it cannot appear to be current authority.
5. Preserve its historical meaning and evidence.

The applicable subject and change authorities decide supersession. The
Technical Author Lead coordinates the document work but does not make that
decision. Do not overwrite historical evidence to make a later replacement
appear retrospective.

### Retirement

Retire a technical document only with explicit evidence that it owns no
required current information. Before retirement, identify which result applies:

- Another canonical owner received the content.
- An accepted document superseded it.
- The content is no longer applicable.
- The document remains necessary as historical evidence.

Record the reason and applicable authority in an existing decision, evidence,
or Git record. Update current references and status. Retirement does not by
itself authorise deletion. Do not delete or rewrite material whose evidential
value depends on preservation.

### Historical preservation

Preserve required technical documents, decisions, reviews, accepted baselines,
and retirement or supersession evidence under
[RECOVERY_AND_BACKUP.md](RECOVERY_AND_BACKUP.md) and
[history/README.md](history/README.md).

A superseded or retired document can remain as historical evidence without
remaining current authority. Clearly distinguish current canonical
documentation, superseded documentation, retired documentation, frozen
historical evidence, and failed experimental candidates.

Do not rewrite a historical record only to apply a newer documentation
standard. Preserve the exact meaning, status, limitations, and accepted
identity that give the record evidential value.

### Traceability

Use existing evidence to answer these lifecycle questions:

| Question | Existing trace |
| --- | --- |
| Why does the document exist? | The initiating requirement, work item, decision, or documented deficiency. |
| Who owns it? | Its canonical owner and the applicable subject owner. |
| What technical authority does it consume? | Its canonical links and recorded source information. |
| What baseline is current? | The accepted Git identity and applicable review state or decision. |
| What review applies? | The classification, TT-DOC-001, TT-DOC-002, D-GOV-015, and its review receipt. |
| What changed? | The Git comparison with the accepted baseline. |
| What validated the accepted state? | The named validation result and its evidence. |
| What replaced it? | The supersession status, replacement link, and applicable decision. |
| Why was it retired? | The retirement evidence and applicable authority. |

Do not create a duplicate lifecycle record when Git or an existing canonical
record answers the question.

### Lifecycle completion and reopening

A completed documentation lifecycle remains complete until a genuine material
change creates a new technical-document need. Do not reopen a controlled
document only because:

- Another model is available.
- Another reviewer could use different wording.
- A later process is stronger.
- A new checker reports a stylistic preference.
- Further linguistic improvement is possible.

Only the applicable change-control authority can identify a material need that
reopens the lifecycle. The management objective is finite:

> identify the need → create the right information → establish its acceptance
> → maintain the controlled baseline → change it only when necessary → retire
> it deliberately → preserve what must remain

The objective is controlled technical information throughout its useful life.
It is not perpetual document improvement.

### Existing repository records

The live control paths are fixed:

- [PROJECT_PLAN.md](PROJECT_PLAN.md) contains phase status, exit status, risk
  summaries, decision summaries, and evidence links.
- [current/PHASE_EVIDENCE.md](current/PHASE_EVIDENCE.md) contains all detailed
  evidence for the open phase.
- [current/risks.json](current/risks.json) contains detailed live risks.
- [current/gate-decisions.json](current/gate-decisions.json) contains structured
  current owner decisions.

A Level 1 change updates its implementation and relevant test. It can also
update a document that directly owns corrected wording. It does not update
current phase evidence or the project plan.

A Level 2 change adds exactly one short current-evidence entry.

A Level 3 change records its full evidence review and panel. It records the
owner decision and updates the structured registers. It also updates the
project-plan dashboard.

Change another reference document only when its owned policy, contract, or
responsibility changes.

At phase close:

1. Finish and accept the current evidence.
2. Move it to `reference/history/phase-closeouts/PHASE<N>_CLOSEOUT.md`.
3. Archive closed risk and decision records when applicable.
4. Create clean current records for the next phase.

Historical inventories, foundations, closeouts, dated audits, and benchmark
reports are frozen evidence. Routine alignment must not rewrite them to match
the current project.

Validate only their continued existence, necessary internal links, accepted
hashes, and accepted status. Correct a frozen record only for a demonstrated
factual error or an explicitly accepted change to a bounded scope.

Physical archive moves are separate migrations because paths and accepted
hashes can change. Historical records can stay at their existing paths until
that migration is accepted. See [history/README.md](history/README.md).

## CI and manual evidence

Tracked CI owns these repeatable clean-run checks:

- Python and macro parsing.
- The standalone test and contract matrix.
- Dependency direction.
- Frozen-oracle and frozen-record hashes.
- Markdown links.
- Project-progress and current-register consistency.

Normal reports do not repeat each automated invariant. Report the CI result or
equivalent local matrix once.

CI does not replace evidence from a qualified FreeCAD host or real GUI. It does
not replace an operator journey, exact-output evidence, or performance evidence.
It also does not replace backup and restore evidence, licence judgement, or
owner acceptance.

## Completion report

Use the TT-DOC-001 owner view for a substantial cycle. Keep detailed evidence
below it. For a smaller change, use this compact technical provenance:

```text
Changed:
Validated:
GUI work outstanding:
Risks or authority changes:
```

Omit empty detail. Do not hide a failed, skipped, or unavailable check. The
last field records each governance-budget exception and each necessary owner
decision.
