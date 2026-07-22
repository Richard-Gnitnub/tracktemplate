# Phase 4 Canonical State, Signatures, and Persistence Evidence

Status: **Active.** The project owner explicitly instructed the project to
start Phase 4 on 2026-07-22. Three of six Phase 4 exit conditions now have
recorded technical evidence; phase closeout and owner acceptance remain open.

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

## Provisional transition schema v1

`tracktemplate.application.transition_state` owns the provisional development
schema. The writer emits version 1 and the reader currently accepts exactly
version 1. This is not yet the owner-agreed complete Phase 4 schema/version
window: the chair-definition version window, legacy family migrations and
FreeCAD property envelope remain open.

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

This detector cannot return write authority. `SUPPORTED_MIGRATION_FAMILIES` is
deliberately empty, so even an exact outer-window match remains
`inspection-only` with `migration-family-not-qualified`. Family-specific
schema recognition, stable-identity sufficiency, canonical conversion and a
copied-target transaction must each gain an accepted fixture before a later
migrator can advertise that family. The closed Phase 1 contract remains the
historical accepted policy record; implementing this Phase 4 reader does not
rewrite its earlier status text.

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

## Phase 4 chair-definition package contract

The neutral v1 contract is now implemented by
`tracktemplate.application.chair_definition`, exposed only through the narrow
`tracktemplate.api` façade, and published portably as
[`chair-definition-v1.schema.json`](schemas/chair-definition-v1.schema.json).
It is a TrackTemplate schema, not a Templot format, FreeCAD document schema,
mesh container or production chair.

The contract records the logical boundaries accepted in
[S1_PILOT_PLAN.md](S1_PILOT_PLAN.md): package and definition identity/version,
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
validator remains the separate semantic clearance gate. Phase 9 production
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

Observed on 2026-07-22 from the repository root:

| Check | Result |
| --- | --- |
| Parse B14, B15, B16 launcher and all new/changed Python | Passed |
| Every `tests/validate_*.py` standalone validator | 37/37 passed |
| Dedicated Phase 4 canonical-state validator | Passed |
| Deterministic modular structure | Passed; declared application boundary, permitted inward edges, no cycle, forbidden domain dependency or warning |
| Isolated API/domain/application import with FreeCAD, Part, Qt and pivy blocked | Passed; no host import attempted |
| B15 FreeCAD 1.1 headless smoke | Passed |
| Accepted Phase 2 FreeCAD loading smoke | Passed |
| Retained Phase 3 FreeCAD routing smoke | Passed |
| Phase 4 FreeCAD 1.1 canonical-state smoke | Passed; exact round-trip and zero document mutation |
| Phase 4 qualified FreeCAD persistence lifecycle | Passed; disposable create/update, Undo/Redo, abort, stale/corrupt rejection and FCStd save/reopen |
| Phase 4 standalone B14/B15 detector matrix | Passed; B14, B15, mixed, foreign, unsupported, versionless, malformed and conflicting cases |
| Phase 4 FreeCAD legacy detector lifecycle | Passed; zero-mutation inspection and identical mixed report after FCStd save/reopen |
| Phase 4 chair-definition package validator | Passed; exact deterministic round-trip, signed manifest linkage, unit/reference/lineage failure matrix and hard production-admission block |
| Phase 4 chair-definition qualified-FreeCAD compatibility | Passed; exact package round-trip with zero document mutation and production admission disabled |

The dedicated qualified-FreeCAD smoke is intentionally limited to type/runtime
compatibility, exact JSON round-trip and zero document mutation; it is not
FreeCAD property, transaction, Undo/Redo or FCStd save/reopen evidence. No
real-GUI workflow or performance run is claimed because this tranche does not
alter an operator route, document, renderer, exact geometry or export path.

## Current Phase 4 gate disposition

| Exit condition | Current disposition |
| --- | --- |
| Selected-slice save/reopen without result or identity drift | Evidenced: exact canonical payload, result and identity pass disposable qualified-FreeCAD save/close/reopen |
| Exact parameter invalidation including cold/reuse/change-back | Active: transition analysis cases are directly tested; downstream preview, exact-validation and export propagation remain due |
| Undo/redo and failed updates leave a valid document | Evidenced: atomic create/update, no-op, Undo/Redo, preflight rejection and injected post-write abort all pass |
| Preview/exact geometry can be deleted and regenerated from canonical state | Pending: no Phase 5/6 renderer or exact adapter is being invented here |
| Deterministic, fail-closed chair-definition package | Evidenced: neutral schema v1, immutable review record, exact decimals/units, constituent/procedure/interface/manufacturing separation, lineage, signed manifest linkage and failure matrix pass without enabling production; S1 evidence remains blocked |
| Supported schema/version window agreed and tested | Active: exact transition v1, chair-package v1 and read-only B14/B15/mixed outer detection are tested; owner agreement and family migration schemas remain due |

## Remaining risks and next bounded tranche

- Stable identity mapping to one logical transition object is implemented, but
  identity generation remains the responsibility of the later owning entity
  workflow; adapters must not invent IDs from object order or labels.
- The outer B14/B15 detector exists, but no legacy entity family is qualified
  for migration. Family schema/identity validation and copied-target migration
  fixtures remain mandatory; an accepted version set must not imply that a
  whole legacy document is migratable.
- Preview, exact-validation and export signatures cannot be completed until
  those derived-result contracts exist; adapters must not invent partial keys.
- Chair-package v1 is technically evidenced but remains provisional until the
  project owner accepts the Phase 4 schema window. Family completeness,
  numerical S1 data, exact generation and production admission remain Phase 9
  work, not implicit consequences of this contract fixture.
- The provisional v1 window requires explicit project-owner acceptance before
  it can satisfy the Phase 4 schema/version exit condition.

The next Phase 4 decision is project-owner review of the tested transition and
chair-package v1 read window. The independent backup/restore prerequisite in
[RECOVERY_AND_BACKUP.md](RECOVERY_AND_BACKUP.md) is satisfied for the owner-
confirmed complete scope under its active cadence. Copied-target legacy-family
migration remains blocked by its family-specific schema/identity fixture; no
migrator is authorised by backup readiness alone.
