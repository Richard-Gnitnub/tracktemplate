# Phase 4 Canonical State, Signatures, and Persistence Evidence

Status: **Active — revised scope 6/6 evidenced.** The project owner explicitly
instructed the project to start Phase 4 on 2026-07-22. All six revised Phase 4
exit conditions now have recorded evidence; a separate owner closeout decision
remains required.

## Bounded opening tranche

The first tranche establishes a FreeCAD-independent canonical-state boundary
for the parity-proven transition-length slice. It does not yet write a FreeCAD
property, migrate a legacy document, create preview or exact geometry, define a
chair package, or remove the retained Phase 3 comparison route.

The tranche started from pushed Phase 3 closeout commit
`bf4e64e1a82f13b86ceba0f678d5a5d84c49bf84`. B14 and B15 remain immutable:

- B14: `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088`
- B15: `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848`

## Canonical record boundary

`tracktemplate.domain.transition.TransitionIntent` is an immutable standard-
library record. It contains only durable parametric intent and metadata needed
by the accepted solver:

| Field | Meaning |
| --- | --- |
| `transition_id` | Caller-supplied, non-empty stable identity; replacement of an existing record cannot change it |
| `circle_centre_y_mm` | Finite millimetres in canonical local left-turn model space |
| `radius_mm` | Finite model-space millimetres; the mechanically preserved solver still owns its positive-radius diagnostic |
| `target_signed_offset_mm` | Finite signed model-space millimetres in canonical local Y |
| `total_angle_rad` | Finite radians; positive angle remains the accepted caller precondition rather than a silently added solver rule |
| `track_name`, `end_name` | Diagnostic labels, not stable identities and not numerical-result inputs |

The record normalises accepted integer or float inputs to finite Python
`float` values and rejects booleans, NaN and infinities. That validation belongs
to the new canonical-state boundary; the three mechanically extracted Phase 3
functions remain byte-for-byte AST-equivalent to B15.

## Transition schema v1

`tracktemplate.application.transition_state` owns the development schema. The
writer emits version 1 and the reader accepts exactly version 1. The project
owner accepted this as part of the bounded Phase 4 read window on 2026-07-22;
that decision does not qualify a legacy entity-family writer or broaden the
FreeCAD property envelope.

The deterministic JSON object contains exactly:

- schema identity `tracktemplate.transition-state` and integer version `1`;
- one intent object with explicit `mm` and `rad` units, coordinate frame
  `canonical-local-left-turn-v1`, algorithm identity and tolerance-profile
  identity; and
- either no analytical result or one result containing the transition length,
  complete analysis-input signature and result-integrity signature.

Keys are serialised in deterministic lexical order with standard JSON numbers.
Duplicate fields, missing or unexpected canonical fields, non-standard numbers,
unknown schemas, unsupported versions, units, frames, algorithms and tolerance
profiles fail closed with a structured non-mutating diagnostic. No `Part`
shape, mesh, preview path or exact geometry is stored.

The tolerance profile identifies the exact accepted B15 behaviour:

| Rule | Value |
| --- | ---: |
| Zero-length geometry tolerance | `1e-8 mm` |
| Default Simpson integration steps | `240` |
| Maximum-length guard | `1e-6 mm` |
| Achievable-range slack | `1e-6 mm` |
| Endpoint residual | `1e-8 mm` |
| Bisection residual | `1e-10 mm` |
| Bisection interval | `1e-7 mm` |
| Maximum bisection iterations | `72` |

## Signature and dirty-state rules

The application layer is the one authoritative owner of transition signatures:

- the analysis signature includes all four numerical inputs, units, coordinate
  frame, algorithm identity and tolerance profile;
- stable identity and diagnostic labels are deliberately excluded because they
  do not change the successful numerical value;
- changing either diagnostic label retains a current successful result;
- changing any numerical input drops the result and records
  `analysis-invalidated`;
- changing the stable identity through replacement is rejected;
- analysis reuses the same immutable state object when its signatures are
  current; and
- a numerical A-B-A sequence recomputes on each numerical change and returns
  the exact original result/signatures after change-back.

The result-integrity signature covers the complete analysis signature, result
value and result unit. The writer refuses a stale or unverifiable result. The
reader preserves valid canonical intent but discards stale or damaged derived
analysis with the ordered finding `stale-analysis-discarded` or
`corrupt-analysis-discarded`. Therefore a damaged cache cannot become railway
truth and does not make valid intent unrecoverable.

## Source and dependency boundary

The new package locations are the minimum justified by this tranche:

- `tracktemplate.domain.transition` owns the immutable domain intent;
- `tracktemplate.application.transition_state` owns the application command,
  signatures, invalidation and adapter-neutral JSON contract; and
- `tracktemplate.api` remains the narrow migration façade.

The application layer depends inward on the two transition domain modules.
Neither domain nor application imports FreeCAD, Part, Qt, pivy or a third-party
package. The opening tranche created no adapter, presentation, UI or chair
package tree. The persistence tranche below adds only its now-proven concrete
FreeCAD boundary.

## FreeCAD persistence tranche

`tracktemplate.adapters.freecad.transition_state` now provides the smallest
qualified-host adapter required by the selected slice. It creates one logical
`App::FeaturePython` with no `Shape` and exactly two project properties:

| Property | Purpose |
| --- | --- |
| `TrackTemplateRecordType` | Read-only discovery index equal to `tracktemplate.transition-state` |
| `TrackTemplateStateJSON` | Read-only deterministic schema-v1 canonical intent and accepted analysis |

The schema/version remains inside the payload. The index does not contain or
replace stable identity. Identity resolution parses the canonical payload and
uses `transition_id`; FreeCAD object name, label and document order are never
identity inputs. Names are only deterministic adapter hints and labels remain
operator-editable metadata. Foreign objects and other Track Template record
types are ignored and preserved.

Read-only inspection does not require write authority. Construction of
`FreeCADTransitionStore`, and therefore every create/update, requires the
qualification record returned by the existing authoritative bootstrap. The
adapter rejects unqualified evidence, evidence for a different live FreeCAD
version and documents with Undo disabled before mutation.

Create and changed update each open and commit exactly one FreeCAD transaction.
An exact no-op creates no history entry. Inputs, ownership, stable identity,
duplicate identity and serialisability are preflighted before the transaction.
Any exception after object or property mutation aborts the transaction; an
abort failure is separately reported as potentially mutating and non-
recoverable. No document recompute, `Part` import, shape, renderer or exact
geometry is introduced.

The disposable qualified-FreeCAD fixture proves:

- create and update each add exactly one Undo unit;
- update Undo/Redo restores the exact prior/new canonical payload while an
  operator-modified label remains independent;
- create Undo removes the logical object and Redo restores its properties and
  canonical state, while the undone stale object handle is rejected;
- injected failures after a property write abort both create and update with
  unchanged object count, payload and history;
- invalid identity, duplicate identity, missing state, unsupported future
  schema and disabled Undo fail before an authorised write;
- stale or corrupt derived analysis is discarded on read without rewriting the
  payload and can be explicitly reanalysed and committed;
- one current transition survives real FCStd save/close/reopen with exact JSON,
  analysis, stable identity, `App::FeaturePython` type/name, read-only property
  modes and operator label; and
- foreign and other-record-type objects survive unchanged.

## Accepted comparison-route retirement

On 2026-07-23 the project owner authorised the bounded Phase 4 retirement of
the active Phase 3 B15 comparison switch. The accepted invariant makes B16
product composition modular-only, retains any inherited B15 GUI host as a lazy
compatibility dependency, moves dual-route comparison to development-only
oracle tooling, and keeps B14/B15 byte-identical. It does not authorise a
migration-support claim, operator migration, another entity family or
production output.

`tracktemplate.compatibility.b15_workflow_host` is the single internal owner of
the frozen source/contract checks, no-launch AST loading, caller-boundary
validation and atomic complete-function binding. Product composition uses
`tracktemplate.compatibility.transition_workflow`, which exposes only one
modular session and has no route switch or rollback field.
`tools.phase3_transition_pilot` retains legacy → modular → legacy selection
solely so the accepted Phase 3 oracle and benchmark tooling remain
reproducible; it is neither imported nor exported by the product package.

`TrackTemplate.FCMacro` now accepts only the boolean `launch_workflow` option.
Its default qualification path reports `modular-foundation-ready` without
loading the 2.3 MB B15 module. An explicit inherited-workflow launch lazily
loads the host and binds all three transition functions to `tracktemplate.api`
before the GUI entry point can run. Supplying the retired `"legacy"` positional
argument fails before host loading with no document mutation.

The qualified FreeCAD fixture proves the lazy default, rejected legacy
argument, exact historical all-caller parity through the development oracle,
and a separate product host whose three live bindings are all the modular API.
B14 and B15 retain their accepted hashes. The project owner accepted this
bounded retirement on 2026-07-27 under the panel conditions below. No numerical
startup-performance improvement is claimed from the structural lazy-load
proof.

The isolated real-GUI product-composition correctness run
`20260723T104629754109Z-plain-line-edit-modular` completed the full inherited
plain-line edit, rejection and rollback recipe in 35.22 seconds. Its routing
record states `comparison_route_available: false`; the modular binding identity
remained intact, the disposable run document was closed, the isolated process
stopped, and the source fixture remained SHA-256
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.
The ignored raw run is development evidence; its single uncontrolled-cache
duration is not a performance qualification or human-use budget.

The matching development-oracle run
`20260723T104739153208Z-plain-line-edit-legacy` completed in 34.77 seconds
with the same source and cleanup controls. The existing route-independent
comparator reported zero differences and exact shared semantic digest
`85976aa1a154ab5afce8d51a89f7674e655b7b5d91f61795580e67f3980fc7f0`.
This preserves reproducible comparison evidence without restoring a legacy
choice to product composition.

The inherited B15 GUI host remains a temporary development compatibility path,
not a release implementation. The Phase 10 integration owner must remove it no
later than the beta gate after equivalent modular Workbench workflows have
their named Phase 7–9 evidence. Until then it is lazy, modular-bound and
covered by the same frozen B15 fingerprint. The development oracle may remain
under `tools` for historical reproduction but must never be imported by
product composition.

Under the governance policy accepted later on 2026-07-27, this retirement did
not require a panel because the development oracle and rollback evidence
remain. The completed review below remains accepted additional challenge and
does not make an ordinary retirement condition a true gate.

<a id="comparison-route-retirement-review"></a>

### Safety/risk panel — 2026-07-27

**Decision and exact source:** Phase 4 comparison-route retirement review at
`466324ddeffa80daa950389868eb0d92f2b8421d`; implementation range
`8a57c24..40059fa`. The affected product source is unchanged after
`40059fa`.

**Participants and roles (including independence):** Richard, project owner,
chaired and accepted the recorded review on 2026-07-27. Codex acted as both
phase/slice owner and QA/risk reviewer; those roles overlapped and the challenge
was not independent. Independent challenge was not mandatory because no due
Critical risk, irreversible external action or project-cleared rights decision
was in this review.

**Evidence reviewed (links):** the [current Phase 4 exit-condition
disposition](#current-phase-4-exit-condition-disposition), the
[validation evidence](#validation-evidence), the accepted
[Phase 3 slice](../phase-evidence/PHASE3_TRANSITION_SLICE.md), the selected commands and evidence
boundaries in [VALIDATION.md](../VALIDATION.md), the live principal and QA risk
register in [risks.json](risks.json), and the copied-document and
recovery controls in
[RECOVERY_AND_BACKUP.md](../RECOVERY_AND_BACKUP.md). Review covered the complete
retirement diff, current source, standalone and qualified-FreeCAD raw results,
and the two retained real-GUI run records.

**Due principal/QA risks and control-effectiveness changes:** PR-10 remains
Partial because later legacy patches still have their own retirement
conditions. PR-18 becomes Effective (current scope) because product
composition is
modular-only and the reproducible dual route is development-only. PR-20 remains
Effective (current scope). PR-22 becomes Effective (current scope) through this
first prospective recorded panel. QA-R03 remains Open for the wider
release-critical workflow matrix; the affected plain-line edit workflow has
bounded headless and real-GUI evidence.

**Safety, recovery, correctness, rights and performance conclusions:** B14 and
B15 remain byte-identical; the default B16 path is lazy, modular-only and
non-mutating; rejected legacy selection fails before host loading; and the
recorded modular GUI workflow matches the development oracle with source-copy
preservation and clean shutdown. The retirement changes no persistence,
migration, exact output, provenance or licensing authority. Its single
uncontrolled-cache GUI timings are observations only, not a performance
qualification.

**Unresolved dissent, unknowns or exceptions:** No dissent or failed required
check. The temporary inherited B15 GUI host and development oracle remain
bounded obligations rather than release implementations.

**Recommendation:** **Proceed with bounded conditions.**

**Conditions, owners and deadlines:** The Phase 10 integration owner must
remove the inherited B15 GUI host after the equivalent modular Workbench
workflows obtain their Phase 7–9 evidence and no later than the Phase 10 beta
gate. Current and later slice owners must keep the dual-route oracle under
`tools`, outside product imports, immediately and for as long as it is retained.
They must not claim migration support or performance improvement from this
retirement.

**Project-owner decision and date:** **Accepted 2026-07-27** through explicit
recorded instruction.

## Legacy-document detection tranche

`tracktemplate.compatibility.legacy_document` now implements the contracted
outer B14/B15 ingress inspection without importing FreeCAD or exposing a write
path. It reads the accepted Phase 1 compatibility contract, rejects a malformed
or broadened contract, and deterministically reports only:

- objects whose `GeneratedBy` exactly matches
  `ModelRailwayCurveTemplate.IndependentEasements`;
- the first token of descriptive `GeneratorVersion` values;
- `macro_version` and `source_macro_version` evidence inside the exact 48 JSON
  property names present in both immutable B14 and B15 sources, including
  nested records; and
- owned object names, generated roles, template-set sufficiency, parsed JSON
  property paths and foreign-object count.

JSON inspection rejects duplicate keys, non-standard numbers, malformed text,
invalid version fields and invalid schema-version types. B14-only, B15-only and
the exact mixed B14/B15 set match the accepted outer window. Versionless,
unknown or future evidence remains inspection-only. Contradictory object/JSON
versions or malformed/corrupt payload evidence returns
`blocked-corrupt-or-conflicting`. Foreign objects do not classify the document
and their version or JSON content is not interpreted.

This detector cannot return write authority. At the 2026-07-22 detector
tranche, `SUPPORTED_MIGRATION_FAMILIES` was deliberately empty, so even an
exact outer-window match remained `inspection-only` with
`migration-family-not-qualified`. Family-specific schema recognition,
stable-identity sufficiency, canonical conversion and a copied-target
transaction each required an accepted fixture before a later migrator could
advertise that family. The closed Phase 1 contract remains the historical
accepted policy record; implementing this Phase 4 reader does not rewrite its
earlier status text.

Maintainability is bounded: this compatibility module is the sole outer
legacy-version reader, imports only `dataclasses` and `json`, is not re-exported
through the product API, and contains no FreeCAD or mutation call. Its 48-name
property tuple is compatibility data rather than a second implementation and
is mechanically checked against both immutable macros. Later family readers
must consume this report and add their own schema fixture instead of copying
its version scan.

The disposable real-FreeCAD fixture proves B14, B15 and mixed classification,
foreign-object exclusion, versionless/future handling, conflicting/malformed
blocking, zero object/property/history mutation and an identical report after
FCStd save/close/reopen. A separate read-only probe of a copied nine-object B14
base fixture (semantic SHA-256
`a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e`)
observed only `10.2A8A7B14`, all eight expected generated roles and 29
non-empty JSON properties. It returned an accepted outer version window but
inspection-only family status. Object count, Undo/Redo counts and the copied
FCStd SHA-256
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`
were unchanged.

## Bounded read-window acceptance and family assessment

On 2026-07-22 the project owner accepted exactly transition-state v1,
chair-definition package v1, and B14-only, B15-only or expected mixed B14/B15
read-only legacy ingress, with the fail-closed limits above. The same decision
explicitly withheld authority for entity-family migration and production
chair/output. At that read-window decision,
`SUPPORTED_MIGRATION_FAMILIES` remained empty and the production-admission hard
stop remained unchanged.

`tracktemplate.compatibility.plain_line_transition` is the first bounded
read-only family assessment. It consumes the outer detector rather than
reimplementing version discovery and examines only spacing-matched secondary
plain-line entry/exit transitions. For each complete settings set it requires
the exact persisted property types and ordered B14/B15 track record, then
replays the accepted transition solver. Stable candidate identity uses
`TemplateSetID`, the persisted semantic track ordinal and transition end; it
does not use FreeCAD object order or the operator-facing track name.

The assessment reports `canonical-inputs-sufficient` only when every selected
record is recognised and its replayed transition length exactly equals the
stored value. Missing inputs or an unsupported alignment mode remain
inspection-only; malformed types/data, duplicate settings identities or a
stored/replayed contradiction block the result. Any non-sufficient report
exposes no candidate states. Every report states that write, migration and
production output are unauthorised, and the module is not exported through the
product API.

The reproduced nine-object B14 base supplies the real-document fixture. Its
two secondary-track states replay exactly at `559.4102547270278 mm`, retain
stable entry/exit identities and leave object/property/history snapshots and
the source FCStd SHA-256 unchanged. Synthetic B14, B15 and mixed cases cover
direction normalisation, label independence, deterministic multi-set ordering,
missing/unsupported state and the corrupt/ambiguous failure matrix. This is
canonical-input sufficiency evidence only, not a migration fixture or document
conversion.

## Accepted copied-target migration fixture

On 2026-07-23 the project owner authorised one fixture-only migration exercise
for the already assessed spacing-matched secondary plain-line transition
family. The authority covers disposable B14, B15 and expected mixed copies or
new targets only. It does not permit source-document writes, another entity
family, advertised migration support, production chair/output, or a product
API.

`tracktemplate.compatibility.plain_line_transition_migration` owns the
host-independent preflight: source and target must be different document
objects, both assessments must be complete, and their deterministic family
reports must match exactly. It returns an immutable fixture plan and remains
outside `tracktemplate.api`. The physical-copy and full-document preservation
proof belongs to the qualified fixture, not to this family-level preflight.

`FreeCADTransitionStore.create_many()` is the one retained adapter addition. It
pre-serialises and checks every state and stable identity before opening one
transaction, creates the complete batch, reads every payload back before
commit, and aborts the whole transaction on failure. It creates no shape and
does not recompute. The existing one-record create/update paths are unchanged.

The isolated FreeCAD 1.1.1 fixture exercised the reproduced B14 FCStd plus
synthetic B15-only and expected mixed sources. Each target began as a byte copy,
received exactly the two assessed canonical transition records in one Undo
entry, returned exactly to its legacy state on Undo, restored both records on
Redo, rejected a duplicate batch without history, and preserved legacy object
properties, group relationships, shape topology/bounds and canonical state
through target save/reopen. Source files and the original B14 fixture remained
byte-identical. An injected failure after the second payload produced a
recoverable transaction error and restored target objects, history and bytes
exactly. `SUPPORTED_MIGRATION_FAMILIES` remains empty and both migration-
support and production-output flags remain false.

On 2026-07-23 the project owner accepted this bounded fixture evidence for
B14, B15 and expected mixed ingress. The acceptance explicitly does not
advertise migration support, authorise Workbench/operator wiring, migrate
another family, or enable production chair/output.

## Disabled copied-target orchestration tranche

On 2026-07-27 the fixture gained one disabled-by-default synchronous operation,
`execute_copied_plain_line_transition_migration_fixture()`. It completes the
same exact family-level preflight before calling the injected qualified
writer's one-batch `create_many()` operation. A rejected preflight makes no
writer call; adapter failures propagate without translation so its existing
rollback diagnostic remains authoritative. The operation is not imported by
the product API or composition.

Standalone evidence proves the successful call boundary, exact state batch,
rejected-copy zero-call case, unchanged source and target under a recording
writer, writer-error identity and invalid-writer diagnostic. Qualified FreeCAD
1.1.1 headless and isolated real-GUI runs both emitted
`Phase 4 copied-target transition migration fixture passed`. The GUI run
asserted `FreeCAD.GuiUp` and repeated the copied B14, B15 and mixed transaction,
Undo/Redo, persistence, duplicate and injected-rollback checks. The first GUI
bridge attempt used `execute-code --file`; it failed before a project assertion
because that bridge mode does not define `__file__`. This was classified
`fixture-or-harness-defect`, and the unchanged validator passed through
`runpy.run_path`.

`MIGRATION_SUPPORT_ADVERTISED` is now derived from
`SUPPORTED_MIGRATION_FAMILIES`, leaving one support authority. That registry
remained empty at this readiness boundary, production-output authority remained
false, and no Workbench/operator route existed. This readiness evidence changed
neither the accepted read window nor Phase 4 progress. The independent PR-17
challenge below recommended `Proceed with bounded conditions`; a separate
project-owner decision and reviewed exact-family enablement change were still
required before any supported-family claim, while operator wiring retained its
later separate authority decision.

<a id="pr17-support-readiness-panel"></a>

### Safety/risk panel — 2026-07-27 — PR-17 support readiness

**Gate and exact source:** prospective support-advertising gate for
`plain-line-spacing-matched-transition-intent`. The reviewed source is the
uncommitted disabled-tranche working-tree diff against clean, pushed base
`d5a3db45ab68a192e3d37f9fad5deb9f66f7de81`, comprising the compatibility
orchestrator, its standalone/FreeCAD tests, the directly affected recovery
control, and the current Phase 4, validation, plan, recovery and dated-backup
records. No support-enabling source is present.

**Participants and roles (including independence):** Richard, project owner,
chairs and owns any later decision. Codex implemented and presented the
tranche. A fresh Codex sub-agent independently performed the QA/risk challenge
read-only; it made no files, edits, commits, pushes or external-state changes.

**Evidence reviewed (links):** the disabled operation and support boundary in
this record; the copied-target commands and interpretation in
[VALIDATION.md](../VALIDATION.md); the transaction, persistence and failed-
write assertions in the linked migration tests; the current phase evidence and
PR-13/PR-17/PR-22 controls in [risks.json](risks.json); the
different-device repeat in
[2026-07-27-pre-phase4-migration-snapshot.md](../backup-records/2026-07-27-pre-phase4-migration-snapshot.md);
and the recovery, testing, architecture and dependency-direction controls.

**Due principal/QA risks and control-effectiveness changes:** PR-13 is
effective for this copied/disposable scope at a clean pushed and independently
backed-up checkpoint. PR-17 remains Partial overall but is effective at this
disabled component boundary. PR-22's independent challenge is satisfied for
this recommendation. PR-12 is Partial because the complete current standalone
matrix exposed two pre-existing documentation/fingerprint drifts outside this
tranche; the earlier `39/39` claim and two current-document statements were
corrected or qualified. QA-R03 remains open because no operator migration
workflow exists.

**Safety, recovery, correctness, rights and performance conclusions:** no
Critical or High implementation defect was found. Exact preflight precedes the
single qualified batch write; rejected input makes no writer call; the adapter
retains validation, readback, transaction and abort authority; and source hashes
remain unchanged. Support and production-output flags remain false, B14/B15
remain immutable, and no product/API/operator import exists. No external data,
rights status, geometry, output or performance behaviour changed.

**Unresolved dissent, unknowns or exceptions:** the real-GUI result is a host
lifecycle, not an operator workflow. B15-only and mixed sources are synthetic.
Invalid-writer validation precedes document preflight and combined-invalid
precedence is unspecified but fail-closed and non-mutating. The independent
reviewer did not rerun FreeCAD or GUI checks. The complete current 41-file
standalone run had the two pre-existing unrelated failures recorded in the
validation section at this review boundary; neither was in this tranche's
dependency path. Both were later adjudicated by the accepted governance
housekeeping and the latest complete matrix passes.

**Recommendation:** **Proceed with bounded conditions.**

**Conditions, owners and deadlines:**

- PR-12/PR-22 documentation condition — satisfied on 2026-07-27 by the Phase 4
  documentation-control and slice owner. Closure evidence is the exact `39/41`
  matrix record at that review boundary, corrected current-version/recovery
  statements, and passing project-progress, QA, recovery and diff checks. The
  two unrelated controls were later adjudicated and the latest matrix is 41/41.
- PR-17 support condition — before any supported-family claim, the Phase 4
  compatibility/migration owner must make support enablement a separate reviewed
  change limited to the exact family ID, keep production output false and keep
  product/API/operator wiring absent. Positive and negative support-authority,
  standalone, qualified-headless and real-GUI-host checks must pass; the project
  owner then accepts or rejects the bounded window.
- PR-17/QA-R03 operator condition — before any later operator wiring, its owner
  must add an approved physical-copy/path non-alias control, failed-target
  discard or quarantine, operator-visible diagnostics and a real operator GUI
  workflow proving source hashes, target recovery, Undo/Redo and save/reopen.

**Project-owner decision and date:** **Accepted 2026-07-27.** Richard accepted
the `Proceed with bounded conditions` recommendation and authorised the
separate exact-family support-enablement change. The decision is limited to
`plain-line-spacing-matched-transition-intent`; it does not authorise
Workbench/operator wiring, whole-document migration, another family or
production output. This accepted the recommendation and implementation
authority; the separate post-evidence bounded-window decision required by the
recommendation remains below.

## Exact-family support enablement

The separately authorised 2026-07-27 change makes
`plain-line-spacing-matched-transition-intent` the sole entry in
`SUPPORTED_MIGRATION_FAMILIES`. `MIGRATION_SUPPORT_ADVERTISED` is therefore
true for that exact fixture-only family, while
`PRODUCTION_OUTPUT_AUTHORIZED` remains false. No schema identifier, schema
version, stored property or canonical transition record changed.

The authority remains narrower than a document migrator. The outer
B14/B15 detector still always reports `inspection-only`; an accepted outer
window now carries `whole-document-migration-not-qualified`, while incomplete
or unsupported windows retain `migration-family-not-qualified`. The family
assessment remains read-only with `migration_authorized=False`. Only the
copied-target fixture can pass a complete, exactly matching family assessment
to the existing atomic writer, and its record remains `fixture_only=True`.

Structural evidence proves that no package module imports the fixture
operation and that `tracktemplate.api` exposes no compatibility migration
surface. The operator must not infer a product command, target-path safety,
failed-target quarantine or operator-visible diagnostic from this family
support flag. Those controls remain the separate PR-17/QA-R03 operator
authority decision.

The exact registry tuple and both positive and negative authority boundaries
pass the standalone detector and family-assessment validators. Qualified
FreeCAD 1.1.1 checks pass for outer detection, family assessment, copied-target
atomic migration and transition persistence. The copied-target fixture also
passes in an isolated real-GUI process with `FreeCAD.GuiUp` asserted. B14/B15
sources remain immutable; copied sources remain byte-identical; Undo/Redo,
save/reopen, duplicate preflight and injected rollback remain exact. The
pre-change recovery point is recorded in
[2026-07-27-pre-phase4-family-support-snapshot.md](../backup-records/2026-07-27-pre-phase4-family-support-snapshot.md).

### Independent post-change PR-17 challenge

A fresh Codex sub-agent independently reviewed the complete implementation,
tests, documentation, backup record and raw validation evidence read-only. It
made no edits, commits, pushes or external-state changes. It independently
reran the then-current standalone matrix at `39/41`, reproduced exactly the two
classified unrelated failures later repaired by governance housekeeping, and
passed the focused detector, family, recovery, project-progress, QA, parse and
diff checks. It reviewed but did not rerun the FreeCAD headless or real-GUI
evidence.

The reviewer found no Critical, High, Moderate or Low issue and returned
**Proceed with bounded conditions**. PR-13 is effective for this bounded
copied/disposable scope; the exact-family PR-17 support condition and PR-22
independent challenge are satisfied. PR-17 remains Partial overall and QA-R03
remains Open because other families, whole-document migration, operator target
lifecycle, operator-visible diagnostics and production output remain excluded.
B15-only and mixed fixtures remain synthetic, and the real-GUI result remains
a host lifecycle rather than an operator workflow.

**Final bounded-window project-owner decision:** **Accepted 2026-07-27.**
Richard accepted the validated exact-family window after the independent
post-change challenge. The acceptance remains limited to the fixture-only
`plain-line-spacing-matched-transition-intent` family. Outer detection remains
inspection-only; Workbench/operator wiring, whole-document migration, another
family and production output remain excluded.

## Phase 4 chair-definition package contract

The neutral v1 contract is now implemented by
`tracktemplate.application.chair_definition`, exposed only through the narrow
`tracktemplate.api` façade, and published portably as
[`chair-definition-v1.schema.json`](../schemas/chair-definition-v1.schema.json).
It is a TrackTemplate schema, not a Templot format, FreeCAD document schema,
mesh container or production chair.

The contract records the logical boundaries accepted in
[S1_PILOT_PLAN.md](../phase-evidence/S1_PILOT_PLAN.md): package and definition identity/version,
full-size exact source and canonical quantities, the fixed right-handed
chair-local frame and mandatory datums, rail interfaces, present or explicitly
absent constituents, ordered versioned procedural steps, manufacturing
profiles kept outside prototype definition, field/component lineage,
validation, acceptance, permissions and a signed dependency-manifest link.
Only exact decimal strings are accepted as output-affecting source values. V1
converts `mm`, `cm`, `m`, `in` and `ft` lengths exactly to full-size
millimetres; angles preserve an exact `deg` or `rad` value and dimensionless
values use unit `1`. Unknown fields, duplicate identities, ambiguous order,
bad references, missing datum/component/interface records, inconsistent units,
unsupported versions and content-signature damage fail with recoverable,
zero-mutation diagnostics.

Review parsing deliberately preserves an explicit `unresolved`, `inferred`,
`comparison-only`, `NOASSERTION`, blocked or unaccepted state so the problem
can be inspected rather than hidden. Such state is never admission. Exact
manifest identity, subject/version, content signature, package licence,
intended uses, project status and referenced dependency identities are checked
when the external manifest is supplied; the existing dependency-manifest
validator remains the separate semantic-clearance decision. Phase 9 production
admission remains disabled even when a package and manifest are otherwise
valid, so the current API authorises no production geometry, FreeCAD document
mutation or filesystem output.

V1 uses one directed integrity edge: the signed package links the canonical
manifest digest. The linked manifest therefore omits its optional
`subject.content_sha256`; accepting a reciprocal whole-package digest would
create an ambiguous circular hash. A future content-addressing change requires
a new accepted schema rule rather than silently redefining either digest.

The committed fixture pair under `tests/fixtures/` is explicitly labelled
`TEST-ONLY-NON-PROTOTYPE-CONTRACT-FIXTURE`. It contains artificial dimensions
and one artificial component solely to exercise schema mechanics; it is not an
S1 definition, railway evidence, a family-completeness precedent or a visual
artifact. Its separate synthetic dependency manifest passes the existing
strict project-clearance validator, which proves that the independent Phase 9
hard stop cannot be bypassed merely by presenting apparently complete rights
records. No B14/B15 source, production chair value, Templot value collection,
Part shape, mesh, GUI object or source evidence body was added.

## Validation evidence

The tranche validator directly covers immutable records, exact numerical
result parity, deterministic cold and analysed round-trips, valid reuse,
every numerical input invalidation, label-only reuse, A-B-A change-back,
stable-identity rejection, signed-zero representation, stale/corrupt derived
result recovery, duplicate/missing/extra fields, unsupported schema versions,
non-finite inputs, structured diagnostics, isolated imports and dependency
direction.

Observed through 2026-07-27 from the repository root:

| Check | Result |
| --- | --- |
| Parse B14, B15, B16 launcher and all new/changed Python | Passed |
| Every current `tests/validate_*.py` standalone validator | 41/41 passed after the two stale historical-control expectations below were adjudicated |
| Dedicated Phase 4 canonical-state validator | Passed |
| Deterministic modular structure | Passed; declared application boundary, permitted inward edges, no cycle, forbidden domain dependency or warning |
| Isolated API/domain/application import with FreeCAD, Part, Qt and pivy blocked | Passed; no host import attempted |
| B15 FreeCAD 1.1 headless smoke | Passed |
| Accepted Phase 2 FreeCAD loading smoke | Passed |
| Retained Phase 3/Phase 4 FreeCAD routing smoke | Passed; lazy modular-only product default, rejected legacy argument, development-oracle parity and forced modular product host |
| Phase 4 comparison-route retirement validator | Passed; no product switch/export, shared loader, development-only oracle and immutable B14/B15 hashes |
| Phase 4 isolated modular GUI workflow | Passed; complete plain-line edit/rejection/rollback recipe, binding identity, source-fixture preservation and cleanup |
| Phase 4 FreeCAD 1.1 canonical-state smoke | Passed; exact round-trip and zero document mutation |
| Phase 4 qualified FreeCAD persistence lifecycle | Passed; disposable create/update, Undo/Redo, abort, stale/corrupt rejection and FCStd save/reopen |
| Phase 4 standalone B14/B15 detector matrix | Passed; B14, B15, mixed, foreign, unsupported, versionless, malformed and conflicting cases |
| Phase 4 FreeCAD legacy detector lifecycle | Passed; zero-mutation inspection and identical mixed report after FCStd save/reopen |
| Phase 4 plain-line transition family assessment | Passed; exact B14/B15/mixed read-only matrix, stable semantic identities, exact replay and fail-closed ambiguity handling |
| Phase 4 reproduced-B14 FreeCAD family assessment | Passed; two exact canonical candidates with zero document/history or source-FCStd mutation |
| Phase 4 copied-target migration fixture | Passed standalone and headless; one synchronous preflight/write call, B14/B15/mixed atomic two-record batch, Undo/Redo, save/reopen, duplicate preflight and injected second-write rollback; sources unchanged, exact family advertised, production false and operator route absent |
| Phase 4 copied-target migration real-GUI host lifecycle | Passed after classified `execute-code --file` harness defect; `FreeCAD.GuiUp` asserted and the exact-family fixture passed through `runpy.run_path` without creating an operator workflow |
| Phase 4 chair-definition package validator | Passed; exact deterministic round-trip, signed manifest linkage, unit/reference/lineage failure matrix and hard production-admission block |
| Phase 4 chair-definition qualified-FreeCAD compatibility | Passed; exact package round-trip with zero document mutation and production admission disabled |

The latest complete 41-file standalone rerun on 2026-07-27 passed 41/41. The
two earlier `pre-existing-unrelated-failure` results were adjudicated as stale
test/contract expectations during the accepted governance housekeeping:

- the lineage validator now follows the detailed licensing/provenance owners
  instead of requiring their filename in the short always-on `AGENTS.md`; and
- the Phase 1 performance contract now records the benchmark's accepted
  post-`025cc19` hash after that commit repaired one internal link. The report's
  measurements and status did not change.

Both original validators and the complete matrix passed after those bounded
repairs.

The dedicated canonical-state qualified-FreeCAD smoke is intentionally limited
to type/runtime compatibility, exact JSON round-trip and zero document
mutation; it is not FreeCAD property, transaction, Undo/Redo or FCStd
save/reopen evidence. The route-retirement tranche separately reran one
isolated real-GUI development workflow because it changed that loader. It did
not alter an advertised operator route, renderer, exact geometry or export path,
and it makes no numerical performance claim.

<a id="three-level-governance-classification"></a>

## Three-level governance classification

**Decision and source boundary:** This Level 3 governance-only change replaces
the former four-level model at base `d5a3db45ab68a192e3d37f9fad5deb9f66f7de81`.
It classifies every task as Level 1 Routine, Level 2 Behavioural or Level 3
Authority/release. It changes no railway, persistence, migration, FreeCAD,
output or licensing behaviour and does not resume product implementation.

**Panel and evidence review:** Richard reviewed the proposed three levels,
chaired the authority decision and explicitly agreed to implementation on
2026-07-27. Codex is the change owner and same-agent QA reviewer; the review is
not independent. Review covers the engineering-policy owner, short agent
summary, PR-12/PR-22 controls, current decision register, dashboard, CI
consistency checks and complete working-tree diff. Independent review is not
required because this change is not Critical, destructive or rights clearance.

**Risk finding and recommendation:** The former model made routine work update
phase evidence and placed behavioural and authority changes in the wrong
classes. The replacement removes that over-governance while retaining
specialist and FreeCAD evidence for behavioural work and full review for
authority transfer. Recommendation: **Proceed with bounded conditions.**

**Conditions and owner decision:** Level 1 must not update phase evidence,
Level 2 receives exactly one concise current-evidence entry, and Level 3 alone
requires a panel, explicit owner decision and plan update. The existing
comparison-route retirement remains non-Level-3 because the accepted
development oracle and rollback evidence remain. Publication is conditional on
passing the complete standalone matrix and final diff review. The project owner
accepted these boundaries on 2026-07-27. The publication condition was then
satisfied locally: all 133 Python/FCMacro sources parsed, the complete
standalone matrix passed 41/41, and the final read-only diff review found no
blocking issue. Remote CI is now proven by the successful clean-checkout run
recorded below; at that point, QA-R02 remained open for deliberate-failure
evidence and branch protection.

## CI clean-checkout and skill workflow automation

This Level 2 workflow repair starts from failed GitHub Actions run
[`30310864619`](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/30310864619)
at commit `67d8c028c4f663d1029d1c7ceee0cce5194d602c`. Parsing passed, then
`tests/validate_recovery_controls.py` failed because the generic matrix required
an ignored workstation-only source archive that a clean checkout cannot
contain. The failure is classified `fixture-or-harness-defect`, with the
clean-checkout environment as a contributing cause; no product or safety
requirement changed.

The retained runner executes every standalone validator and reports all
failures with a structured sentinel. Its explicit `ci` profile proves tracked
clean-checkout contracts and expected fail-closed missing-asset behaviour; its
`local` profile additionally requires the real archive/hash and
branch/upstream evidence. The task-automation skill now conditionally routes to
the CI procedure and real routing/evaluation cases, while agent-guidance
validation enforces the 500-line body budget and direct one-level reference
links. No duplicate CI skill was added.

Pre-publication evidence: 135 tracked Python/FCMacro files parsed; the focused
runner, recovery, skill-guidance, progress and QA checks passed; both complete
profiles passed 42/42; and the `ci` profile also passed 42/42 in the disposable
clean clone that reproduced the original failure, without the ignored archive.
No product, FreeCAD, GUI, migration, output or authority boundary changed, and
the owner pause remains.

Post-publication evidence: commit
`bfcfab0c194b95a60a65fb1e8cda83a2e1d5a337` is on `main`, and
[Standalone CI run 30313014929](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/30313014929)
completed successfully for that exact SHA. Both remote parsing and the complete
43-validator matrix passed. At that point, QA-R02 remained open for
deliberate-failure evidence and branch protection.

<a id="qa-r02-ci-enforcement-closeout"></a>

## QA-R02 CI enforcement closeout

**Decision and source state:** This Level 3 governance change starts from clean
`main` at `5088c9bb050d6c2268f6fa487a53510be04e6978`. It transfers only
authority over updates to protected `main`: the GitHub Actions job
`validation`, bound to app ID `15368`, must pass against the latest base state.
Richard chaired the decision and accepted **Proceed with bounded conditions**
on 2026-07-28.

**Panel and evidence review:** Codex is change owner, presenter and same-agent
QA/risk reviewer; the review is not independent. The risk is Medium,
non-destructive and unrelated to rights clearance, so the policy does not
require an independent reviewer. The panel reviewed successful clean runs
[`30313014929`](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/30313014929)
and
[`30313143402`](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/30313143402),
the app identity of their `validation` checks, the official
[protected-branch contract](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches),
and disposable
[PR #1](https://github.com/Richard-Gnitnub/tracktemplate/pull/1) with deliberate
failure run
[`30380370420`](https://github.com/Richard-Gnitnub/tracktemplate/actions/runs/30380370420).
That run parsed successfully, executed the complete matrix, reported 43 passes
and the one intentional assertion failure, and emitted its failed summary
sentinel.

**Finding, conditions and risks:** Before enforcement, the failed draft PR was
mergeable with an unstable status. After enforcement, GitHub reported it
`BLOCKED` by the failed required check. QA-R02 therefore changes from Partial
to Effective and is closed; PR-22 remains Effective for the current scope.
There was no dissent. A workflow/job rename, app-source change or GitHub
Actions outage can block `main`; the integration owner must preserve the exact
check identity and reopen QA-R02 before weakening or replacing it.

**Result, rollback and exclusions:** Live protection now reports
`strict: true`, context `validation`, app ID `15368`, administrator enforcement
enabled, and force pushes and deletion disabled. The first request combined
legacy `contexts` with app-bound `checks`; GitHub rejected it with HTTP 422 and
made no change. The corrected app-bound request succeeded. PR #1 was then
closed without merge and its evidence branch retained. The focused recovery
control initially failed on two superseded pre-enforcement text markers; this
was classified `test-or-oracle-defect`, the validator was strengthened for the
new app-bound rule, and the exact check then passed. Rollback removes only the
required-status-check rule and reopens QA-R02. No pull-request review count,
conversation-resolution rule, linear-history rule, product work, migration
support, operator wiring, production output or release authority is added.

<a id="bounded-phase-4-resumption"></a>

## Bounded Phase 4 resumption

**Decision and source state:** This Level 3 governance decision starts from
clean `main` at `76041d1a378d90a0f0c5924f3cafeef9831a8639`. It supersedes
only the implementation pause in D-P4-006. On 2026-07-28 Richard explicitly
directed: “Resume Phase 4 product implementation for the bounded derived-state
lifecycle tranche under those exclusions.”

**Panel and evidence review:** Richard is project owner and decision chair.
Codex is change owner, presenter and same-agent QA/risk reviewer; the review is
not independent. The change is non-destructive and does not clear rights,
migration or output authority, so an independent reviewer is not required.
The review covered the clean protected-main checkpoint, successful required
CI, the four evidenced Phase 4 exits, the two remaining exit conditions and the
accepted architecture/dependency direction.

**Risks, recommendation and conditions:** PR-16 controls signature completeness
and stale reuse; PR-20 controls scope. PR-17 remains unchanged because no
migration family or operator path is added. The sequencing uncertainty is that
Phase 4 requires disposable regeneration while Phase 5 and Phase 6 own the
renderer and exact-production seams. Recommendation: **Proceed with bounded
conditions**—complete architecture review first, keep the contract
adapter-neutral, and do not claim either remaining exit condition without its
direct proof. There was no dissent.

**Resulting authority and exclusions:** The project owner accepted those
conditions. Phase 4 product work may resume only for an application-owned
derived-state signature, exact invalidation and disposable-regeneration
contract for the selected transition slice. Renderer choice, GUI or operator
wiring, `Part` production geometry, export, production output, additional
migration families and phase closeout remain excluded.

## Derived-state lifecycle contract

This Level 2 tranche starts from
`76041d1a378d90a0f0c5924f3cafeef9831a8639` and adds one
application-owned, ephemeral lifecycle for the selected transition slice.
Architecture review rejected persistence of derived artifacts and rejected
premature renderer, `Part` or exporter schemas. The retained contract combines
current canonical/analysis identity with a deterministic stage-owned contract
signature; export additionally requires an exact-validation result signature.

`TransitionDerivedCache` supports missing/current/stale status, current-result
reuse, atomic rebuild and explicit discard for `preview`, `exact-validation`
and `export`. Numerical changes invalidate all three stages. Diagnostic-label
changes invalidate preview/export while retaining exact validation. A builder
failure or invalid payload leaves the prior artifact intact. The cache and its
opaque adapter payloads are never serialized, added to a FreeCAD property or
made authoritative.

The focused validator was first observed failing because the accepted module
did not yet exist; this was classified `implementation-defect` against the new
owner-approved contract. A later exact-import assertion omitted the newly
required standard-library `math` dependency; this was classified
`fixture-or-harness-defect`, corrected without weakening the assertion, and the
original focused command passed. After implementation, 138 repository
Python/FCMacro files parsed, the derived-state, canonical-state,
persistence-structure and project-progress validators passed, and the complete
`ci` profile passed 44/44. Qualified FreeCAD 1.1.1 then printed `Phase 4
transition FreeCAD persistence validation passed`: disposable artifacts were
discarded and regenerated with identical source signatures after FCStd reopen,
without changing canonical JSON, properties, object count or Undo/Redo
history.

This is not preview or exact geometry, a renderer decision, an operator
workflow, export evidence or a performance claim. It does not close either
remaining Phase 4 exit condition.

## Renderer-neutral transition preview scene

This Level 2 tranche starts from merged protected-main checkpoint
`f7017e12b9d56e9ea23dd622f3e0e2b6ec280301`. The project owner accepted the
recommended next bounded tranche on 2026-07-28. It adds one ephemeral
`tracktemplate.presentation` contract for the selected transition centreline;
it does not select or implement a renderer.

`TransitionPreviewSpecification` makes the positive segment count a complete
stage-owned signature input. The resulting scene contains one
`track-centrelines` polyline in millimetres and
`canonical-local-left-turn-v1`, with endpoint-inclusive station ordering,
stable visual-to-transition identity, and non-identifying diagnostic labels.
The domain alignment boundary remains the sole railway-mathematics owner.
Endpoint sampling delegates to the unchanged B14/B15-parity calculation;
interior sampling uses the fixed total transition length. Frozen B14/B15
hashes, exact endpoint parity and independently evaluated analytical
power-series coordinates protect the retained numerical behaviour.

The actual preview payload now passes cold/current/reuse, numerical and
diagnostic-label invalidation, sampling-contract invalidation, A-B-A
change-back, zero-length, explicit discard and identical regeneration. The
focused test was first observed failing because the authorised presentation
module did not exist, classified `implementation-defect`. Its next run reached
only the intentionally absent current-evidence heading, also classified
`implementation-defect` at this tranche-record boundary. The first read-only
staff review then rejected the initially passing interior-point oracle: partial
stations had been treated as complete shorter clothoids. This was classified
`implementation-defect` with a contributing `test-or-oracle-defect`; the
fixed-length station calculation and independent analytical expectations
repaired both, and the original focused proof passed.

The qualified FreeCAD persistence fixture regenerates the same scene and source
signature after FCStd reopen without changing canonical JSON, properties,
object count or Undo/Redo history. No scene record is stored. In the final
candidate tree, 141 repository Python/FCMacro files parsed, the focused and
connected regressions passed, and the complete `ci` profile passed 45/45. This
is a renderer-neutral preview geometry contract, not visible GUI evidence, a
renderer decision, exact `Part` geometry, validation, export, production output
or a performance claim. It closes neither remaining Phase 4 exit condition.

<a id="phase-4-exit-ownership-reassignment"></a>

## Phase 4 exit-ownership reassignment

**Decision and source state:** This Level 3 responsibility transfer starts from
clean protected `main` at
`69db0df47c7aa992910c92e906576bb500c4ebdd`. Required pull-request and
post-merge `main` CI passed. On 2026-07-28 Richard directed the project to
“formally move those later-phase obligations to their owning phases and revise
the Phase 4 exits.”

**Panel and evidence review:** Richard is project owner and decision chair.
Codex is change owner and presenter. The existing PR-17 post-change reviewer
performed a fresh read-only challenge independent of both merged implementation
tranches and this wording change. The panel reviewed the current dashboard and
evidence, accepted architecture and modularisation boundaries, merged
implementation and tests, the original detailed Phase 4–6 gate allocation as
supporting history, and PR-14, PR-15, PR-16, PR-17, PR-20 and PR-22.

**Challenge, recommendation and conditions:** The reviewer found no Critical or
High issue and two Moderate record conditions: describe this as an explicit
transfer rather than evidence under the old combined wording, and change the
status-control tests only under the accepted requirement change. The
recommendation is **Proceed with bounded conditions**. Phase 5 must retain the
visible renderer, styles, selection mapping, GUI editing and resource evidence.
Phase 6 must retain complete stage-specific exact-validation/export signatures,
all output-affecting invalidation inputs, transient exact-geometry
regeneration/cleanup, output equivalence, rollback and end-to-end performance.
Phase 4 may become 6/6 evidenced, but this decision must not close it or start a
later phase. There was no unresolved dissent.

**Risk disposition and owner decision:** PR-14 remains
Open/Remove/Not-yet-effective; PR-15, PR-16 and PR-17 remain Open/Mitigate/Partial;
PR-20 remains effective for the bounded current scope. PR-22 is satisfied for
this transfer by the prospective panel, independent challenge and Richard's
explicit decision. No treatment or control-effectiveness value changes. Richard
accepted the transfer and revised Phase 4 boundary on 2026-07-28.

**Resulting authority and exclusions:** Phase 4 now owns invalidation proof for
its canonical analysis, derived lifecycle and actual renderer-neutral preview,
plus deletion and identical regeneration of that preview from canonical state.
Those revised exits are evidenced. Phase 4 remains current and awaits a
separate owner closeout decision; Phase 5 and Phase 6 remain not started. No
renderer choice, GUI or operator wiring, `Part`/exact geometry, validation,
export, production output, additional migration family or phase closeout is
authorised.

| Transferred obligation | Owning phase | Current status |
| --- | ---: | --- |
| Visible renderer, styles, selection mapping, GUI editing and resource evidence | 5 | Not started |
| Exact-validation/export signatures and invalidation; transient exact geometry, cleanup, equivalence, rollback and end-to-end cost | 6 | Not started |

## Current Phase 4 exit-condition disposition

| Exit condition | Current disposition |
| --- | --- |
| Selected-slice save/reopen without result or identity drift | Evidenced: exact canonical payload, result and identity pass disposable qualified-FreeCAD save/close/reopen |
| Canonical analysis and Phase 4 derived-preview invalidation including cold/reuse/change-back | Evidenced: analysis, the generic derived lifecycle and the actual renderer-neutral preview pass their applicable miss/reuse/change/change-back cases |
| Undo/redo and failed updates leave a valid document | Evidenced: atomic create/update, no-op, Undo/Redo, preflight rejection and injected post-write abort all pass |
| Renderer-neutral preview artifacts can be deleted and regenerated from canonical state | Evidenced: explicit discard and identical regeneration pass standalone and after qualified-FreeCAD save/reopen without persisting the scene |
| Deterministic, fail-closed chair-definition package | Evidenced: neutral schema v1, immutable review record, exact decimals/units, constituent/procedure/interface/manufacturing separation, lineage, signed manifest linkage and failure matrix pass without enabling production; S1 evidence remains blocked |
| Supported schema/version window agreed and tested | Evidenced: the read window, bounded B14/B15/mixed copied-target fixture and exact first-family support are accepted after independent challenge; operator wiring, whole-document migration, other families and production output remain excluded |

## Remaining risks and next bounded tranche

- Stable identity mapping for the assessed legacy spacing-matched transition
  uses template-set identity, persisted semantic track ordinal and end. Other
  entity workflows still own their identity rules; adapters must not invent IDs
  from FreeCAD object order or labels.
- The outer B14/B15 detector remains inspection-only. Exactly
  `plain-line-spacing-matched-transition-intent` is qualified at the
  fixture-only copied-target boundary; no other family or complete document is
  qualified, and the current support flag must not be treated as an operator
  command.
- Phase 5 retains the visible renderer/style, selection, GUI-editing and
  resource evidence. Phase 6 retains complete exact-validation/export
  signatures and invalidation, transient exact geometry, cleanup, equivalence,
  rollback and end-to-end cost; adapters must not supply partial keys.
- Chair-package v1 is accepted only inside the bounded read window. Family
  completeness, numerical S1 data, exact generation and production admission
  remain Phase 9 work, not implicit consequences of that acceptance.

The copied-target fixture advertises exactly one accepted family without
wiring an operator path or authorising production output. Either later action
requires its own explicit authority. The independent backup/restore
prerequisite in [RECOVERY_AND_BACKUP.md](../RECOVERY_AND_BACKUP.md) is
satisfied for the owner-confirmed complete scope under its active cadence, but
backup readiness alone does not authorise a migrator.
