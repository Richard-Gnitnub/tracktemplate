# Phase 6 Explicit Exact-Validation and Export Seam Evidence

Status: **Current — 1/5 evidenced. Exit 2 was owner-accepted under D-P6-002
on 2026-08-02; exits 1, 3, 4 and 5 remain Pending.**

Phase 5 closed at 4/4 under D-P5-003 on 2026-08-01. Its complete accepted
evidence, decisions and risk snapshot are frozen in the
[Phase 5 closeout](../history/phase-closeouts/PHASE5_CLOSEOUT.md). This fixed
live path owns current Phase 6 evidence and does not alter that frozen record.

## Opening architecture review

Phase 6 owns the explicit exact-validation and export seam: complete
stage-specific signatures and invalidation, transient exact geometry and
cleanup, output equivalence, transactional export and rollback, and complete
edit-through-export performance evidence. The accepted B16 Entry/Exit slice
supplies bounded canonical transition intent and lightweight editing behaviour,
but no exact artifact, exact oracle, export writer, output clearance or Phase 6
performance result has yet been accepted.

Three routes were reviewed:

| Route | Disposition |
| --- | --- |
| Keep Phase 6 unopened | Safe but does not advance an accepted exact-validation or export exit; superseded by D-P6-001. |
| Port the complete B14 export path | Rejected because it expands to whole-layout and later-family work, retains exact legacy shapes rather than the B16 canonical boundary, and would carry a characterised partial-output failure into the successor path. |
| Establish a narrow B16 Entry/Exit Validate/Export seam | Recommended as the smallest reversible route that can prove one exact artifact and oracle, transient FreeCAD geometry, transactional private-development output and complete cost without accepting migration or production clearance. |

<a id="phase-6-opening-panel"></a>

## Phase 6 opening panel and owner decision

**Decision and exact source state:** This Level 3 opening applies to clean
protected `main` at `35d4124c28d6be7e536a5f3773681ff0bf243283`, the merge
commit for [PR #27](https://github.com/Richard-Gnitnub/tracktemplate/pull/27).
This authority-only record changes no product source; all five Phase 6 exits
remain unevidenced at 0/5.

**Participants, evidence and independence:** Richard is project owner,
decision chair and accepting authority. Codex performed the separate fresh
read-only opening review and is the decision-record change owner; it had no
Phase 6 implementation role because no Phase 6 product implementation exists.
The same reviewer synthesised the architecture recommendation and risk
challenge, so those two review roles were not independent. This was an
engineering control review, not professional legal advice.

**Evidence reviewed:** The panel reviewed the
[project dashboard](../PROJECT_PLAN.md), the 24 live risks in
[risks.json](risks.json), the frozen
[Phase 5 handoff](../history/phase-closeouts/PHASE5_CLOSEOUT.md), the accepted
[exact-geometry and export architecture](../ARCHITECTURE.md#5-exact-geometry-adapter),
the [validation boundary](../VALIDATION.md#5-exact-geometry-and-export-validation),
the [generated-output controls](../LICENSING_BOUNDARIES.md#generated-output-policy),
the B16 Entry/Exit transition source and tests, and the characterised B14
create-time export failure. At the exact source state, the local standalone CI
profile passed 54/54 validators and the merged PR's protected GitHub Actions
check passed. No Phase 6 FreeCAD exact-geometry, target-format export, real-GUI
or performance result exists; that absence is the correct 0/5 opening state.

**Risk disposition:** PR-09 remains Critical/Remove/Partial; Phase 6 may build
only a private-development output path and may not advertise or clear output
while any dependency is restricted, reference-only or unknown. PR-13 remains
Critical/Mitigate/Effective (current scope), subject to current checkpoints,
copied FreeCAD inputs and disposable destinations before risky work. PR-17
remains Critical/Mitigate/Partial because this opening grants no persistence or
migration authority. PR-15, PR-16, QA-R03 and QA-R04 remain Partial for deferred
cost, signatures, end-to-end evidence and budgets. PR-20, PR-21 and PR-22 remain
Effective (current scope) only while the slice, provenance and structured
challenge remain bounded. D-P5-002 and the retired PR-14 exposure must reopen
if later composition invalidates the accepted Coin residual containment. No
risk treatment or control-effectiveness value changes.

**Recommendation, bounded conditions and unknowns:** The separate review
recommended **Proceed with bounded conditions**:

| Accountable owner | Deadline | Condition |
| --- | --- | --- |
| Exact-validation and export owners | Before retaining exact or export behaviour | Define the selected exact artifact, oracle, units, frame, tolerances and equivalence contract; prove the current B16 transition intent is sufficient; do not port the complete B14 exporter. |
| Signature owner | Before retaining reuse or caching | Cover every analysis, exact-validation and export input with complete stage signatures; prove miss, reuse, change, change-back, invalidation and stale-result rejection. |
| FreeCAD exact-geometry owner | Before retaining transient geometry | Use temporary or isolated FreeCAD scope; prove success, failure and cancellation cleanup and that the editable document remains unchanged. |
| Export owner | Before retaining a target-format writer | Resolve safe destinations, deterministic names, collisions and overwrite policy; stage and validate the complete set; commit atomically or roll back completely with a truthful summary. |
| API, licensing and provenance owners | Before any manifest-schema change or output-clearance proposal | Produce a dependency manifest for the selected output and keep it private-development unless its status supports the declared use. Give any required manifest-schema change separate API, licensing, validation and owner review. |
| Performance owner | Before a Phase 6 exit proposal | Measure comparable cold and warm Edit, Validate, Export and complete end-to-end cost with correctness checks; do not invent a numerical budget. |
| Recovery and scope owners | Before each risky host/export run and throughout Phase 6 | Use copied FCStd inputs, disposable output destinations and a current recoverable checkpoint; preserve the legacy oracle and the D-P5-002 reopen condition. |

The first exact artifact/oracle, target format and whether the current manifest
schema can express the successor transition scope remain Level 2 investigation
results. There was no dissent from the bounded recommendation.

**Governance-budget exception:** This task transfers phase authority rather
than implementing product behaviour, so the required Level 3 panel, evidence,
decision register, dashboard and executable status-control changes necessarily
exceed its zero product lines. No policy or frozen historical record changes.

**Owner decision and resulting authority:** On 2026-08-01 Richard stated,
“I accept D-P6-001 exactly as presented.” The accepted decision is:

> **D-P6-001 — Open Phase 6**
>
> At source state `35d4124c28d6be7e536a5f3773681ff0bf243283`, open Phase 6
> at 0/5 for bounded exact-validation and export-seam work on the accepted B16
> Entry/Exit transition slice. Separate Level 2 tranches may establish the
> exact artifact/oracle and contracts, complete stage signatures and
> invalidation, transient exact geometry in disposable FreeCAD scope,
> private-development target-format export with atomic staging and rollback,
> and complete edit/Validate/Export performance evidence.
>
> No Phase 6 exit, production-output clearance, `project-cleared` status,
> operator or migration route, whole-layout or complete B14 export port,
> persisted-schema change, retained production shape, legacy-oracle retirement,
> numerical performance budget, new runtime dependency, packaging, release, or
> later-phase authority is accepted. Any required manifest-schema change
> receives separate API, licensing, validation, and owner review.

## B16 Entry/Exit exact-centreline contract

This necessary-enabling Level 2 tranche starts from protected-main merge
`838f6b52389ea604fecceb307773077873ccfe40`. It adds one ephemeral,
adapter-neutral exact-validation profile for the accepted transition slice.
The caller supplies the maximum analytical chord error and a hard segment
ceiling; the signed v1 contract also fixes canonical local left-turn space,
millimetres/radians, the existing B15-parity numerical profile and its explicit
integration setting. Equal arc-length stations use the conservative Euler
curvature interpolation bound `h^2 / (8R)`, preserve both endpoints and return
one deterministic centreline, artifact signature and validation-result
signature suitable as a later export-stage dependency.

The focused standalone proof compares every retained point with an independent
high-precision Fresnel power series, samples every chord against the analytical
bound, and covers zero length, invalid resolution, segment-cap rejection,
miss/reuse, label-only reuse, numerical change, change-back, stale-state
rejection and failure atomicity. The qualified FreeCAD 1.1.1 smoke printed
`Phase 6 transition exact qualified FreeCAD validation passed` and changed no
document, object, property, active document or Undo/Redo state. At the final
source shape, 174 tracked Python/FCMacro files parsed and the complete
standalone CI profile passed 55/55 validators.

This tranche creates no `Part` geometry, target-format writer, dependency
manifest, file output, editable-document mutation, persisted property or
schema, GUI command, production clearance, product tolerance default, legacy
retirement or exit acceptance. At tranche retention all five Phase 6 exits
therefore remained Pending; D-P6-002 later accepts only Exit 2. Transient exact
FreeCAD geometry, transactional private-development export and complete
edit-through-export performance remained separate work.

## B16 Entry/Exit transient exact geometry

This exit-closing Level 2 tranche starts from protected-main merge
`1e812612c8eab818554bf0d5d0208ebcc79b2490`. The FreeCAD adapter verifies the
signed exact-centreline artifact, allocates a per-invocation temporary name
absent from the pre-operation registry, and verifies the returned document as
one newly registered identity before adding its sole `Part::Feature`. Cleanup
closes only that positively owned document and fails closed when ownership is
ambiguous. The adapter then validates ordered coordinates, bounds, polyline
length, topology and kernel validity, and returns only a deterministic signed
numeric receipt after disposal. Non-zero profiles are open wires; the accepted
zero-length analytical boundary becomes one vertex. It introduces no railway
calculation or persistent truth.

The qualified FreeCAD 1.1.1/OpenCASCADE 7.8.1 proof exercised deterministic
repeat construction, a pre-existing same-named hidden temporary document while
inactive and active, ambiguous ownership rejection before object creation,
nested construction, zero length, invalid artifact rejection, cancellation,
cancellation-check failure and injected Part-build failure. Every path closed
only its owned temporary document, restored both an existing and an empty
active-document state, and preserved every pre-existing document and object,
their tested properties and values, FileName and Undo/Redo counts. At the final
source shape, 176 tracked Python/FCMacro files parsed and the complete
standalone CI profile passed 55/55 validators.

This tranche provides technical evidence toward the transient-cleanup exit
gap but accepts no Phase 6 exit. It adds no retained `Part` shape, persisted
property or schema, GUI operation, export writer, file, manifest, overwrite
policy, output equivalence or clearance, legacy retirement, product tolerance
default or performance budget. Transactional private-development export and
complete edit-through-export performance therefore remain separate work.

## B16 Entry/Exit private-development DXF export

This exit-closing Level 2 tranche starts from protected-main merge
`61237508b0c1fefedcf740afd230e5e563acab3e`. It adds one signed export-stage
contract for the current exact-validation result and one deterministic ASCII
DXF 2000 writer for the accepted Entry/Exit centreline. The contract binds the
format, canonical local frame, millimetres, layer, collision policy, generator
version, dependency-manifest schema and deliberately `unknown` project status.
The writer emits one open `LWPOLYLINE`, or one `POINT` at zero length, beside a
schema-v1 output dependency manifest whose canonical-model digest and artifact
hashes are independently checkable. Hidden staging, no-overwrite collision
handling, byte-identical reuse, identity-checked commit rollback and
ownership-aware cleanup contain the tested in-process failure paths without
mutating canonical or editable-document state. They do not make the two-file
commit crash-atomic or close a pathname race.

The standalone proof independently parsed the DXF group codes and ordered
coordinates; accepted the manifest only as `unknown`; rejected it under
`--require-project-cleared`; and covered stale/corrupt input, zero length,
unsafe or symbolic-link destinations, partial and different collisions,
external destination change, cancellation at each pre-commit boundary,
staged corruption, injected write/commit failure and ambiguous rollback
ownership. Qualified FreeCAD 1.1.1/OpenCASCADE 7.8.1 rebuilt and disposed the
exact Part geometry, reopened the resulting `AC1015` file as one millimetre-
scale polyline with no unsupported feature, and preserved all pre-existing
documents, objects, tested properties, values, active-document state and
Undo/Redo counts across success, reuse, cancellation, injected geometry-build
failure, truthful injected geometry-cleanup failure and commit rollback. At
the final source shape, 181 Python/FCMacro
files parsed, all 56 standalone CI validators passed, and the upstream exact-
contract and transient-geometry qualified checks also passed.

This tranche supplies bounded technical evidence toward exact target output
and deterministic, failure-safe export only. It selects no product-wide format
roster, adds no operator/GUI or migration route, persisted schema, retained
shape, production or physical-output clearance, `project-cleared` status,
performance budget, legacy retirement, Phase 6 exit or later-phase authority.
At tranche retention the 0/5 exit disposition therefore remained unchanged
pending separate owner acceptance. D-P6-002 later accepts Exit 2 only; Exit 3
remains Pending with the required-before-exit conditions recorded below.

<a id="product-vision-and-execution-governance-panel"></a>

## Product vision and execution governance panel

**Decision and repository state:** This Level 3 governance decision applies to
accepted `main` at `61237508b0c1fefedcf740afd230e5e563acab3e`, the merge commit
for PR #30. PR #30 is therefore merged, not pending. Draft PR #31 and its
bounded transition-DXF branch remain separate, unaccepted Phase 6
implementation; this governance branch was created from accepted `main` and
does not alter, rebase, ready or merge that work. Phase 6 remains current at
0/5, and this panel admits no new phase-exit evidence.

**Options reviewed:** Three governance shapes were compared:

| Option | Disposition |
| --- | --- |
| Infer direction from the plan and select its next unchecked item | Rejected: phase ordering is not product purpose, and an unchecked entry is not bounded task authority. |
| Repeat the complete vision in `AGENTS.md`, skills and planning records | Rejected: duplicated authority would worsen PR-12 and allow the copies to drift. |
| One canonical Product Vision, accepted architecture clauses and linked vision-led workflow controls | Recommended: it gives purpose one owner while keeping programme, phase, evidence, assignment and acceptance authorities distinct. |

**Participants, evidence and independence:** Richard is project owner,
decision chair and accepting authority for the governing direction. Codex is
the architecture-review presenter, risk challenger and governance-patch change
owner, so those roles are not independent. A fresh read-only quality review of
the complete final patch and raw validation is required before readiness can be
reported; that review cannot itself accept the Level 3 decision or a Phase 6
exit.

The review reconciled `AGENTS.md`, Engineering Policy, this live record and its
risk/decision registers, the Project Plan, the frozen Phase 5 closeout, Agent
Workflows, the Chief of Staff and continue skills, documentation-authority
rules, architecture and modularisation owners, ViewProvider/Coin source and
lifecycle tests, exact-geometry/export boundaries, the Phase 1 legacy
capability inventory and fixtures, accepted source/branch history, and the open
pull-request relationship. Source and tests were treated as evidence rather
than decision authority.

**Risk disposition:** PR-12 remains Open/Mitigate/Partial: a single Product
Vision owner and link-based routing reduce product-direction and task-selection
ambiguity, but the enlarged governance surface can still drift. PR-20 remains
Open/Mitigate/Effective (current scope): Core and Layout Editor horizons, task
traceability and explicit non-goals control future-scope contamination, but
later implementation must keep proving the boundary. PR-22 remains
Open/Remove/Effective (current scope): the structured decision and separation
of claimed, present, validated and independently accepted states control this
authority transfer, while final patch review and owner acceptance remain
separate. No implementation risk is removed or downgraded.

**Recommendation and bounded conditions:** Proceed with the canonical vision,
architecture clauses and vision-led workflow under these conditions:

| Accountable owner | Condition |
| --- | --- |
| Documentation-control owner | Keep product purpose and programme horizons in `PRODUCT_VISION.md`; link rather than copy them elsewhere. |
| Architecture owner | Treat D-GOV-005-A through D-GOV-005-G as direction and label every undemonstrated renderer, display, exact or performance capability honestly. |
| Chief of Staff or continuation owner | Trace each assignment to an evidenced finding or active exit, state regressions/evidence/non-goals, prevent unchanged loops and reconcile claimed, present, validated and accepted states. |
| Phase owner | Apply only the active phase authority. Future Layout Editor direction neither changes Phase 6 exits nor supplies implementation authority. |
| Quality reviewer and project owner | Keep implementation review independent where required; do not allow an implementer or validator to become sole acceptance authority. |

**Governance-budget exception:** This owner-authorised task changes product,
architecture and workflow authority, so its canonical vision, Level 3 panel,
decision/risk records, dashboard links and structural validators necessarily
exceed the zero product-code change. It rewrites no frozen history and adds no
production architecture merely to demonstrate the documentation.

**Owner authorisation and resulting decision:** On 2026-08-01 the project owner
explicitly authorised this Level 3 governance work and supplied the product and
execution boundaries recorded here. The resulting decision is:

> **D-GOV-005 — Adopt the TrackTemplate product vision and vision-led execution
> model**
>
> `PRODUCT_VISION.md` owns product purpose, the current TrackTemplate Core
> migration, the later Layout Editor horizon and migration-completion meaning.
> Architecture adopts D-GOV-005-A through D-GOV-005-G for canonical state,
> immutable snapshots, batched Coin presentation, lightweight normal editing,
> on-demand exact geometry, ViewProvider-owned display modes, presentation
> performance and product horizons. Work selection follows vision →
> architecture → programme → phase → evidence → bounded item → assignment →
> independent evidence and acceptance. The Chief of Staff and literal
> `$tracktemplate-continue` workflow apply that selection and accountability
> model.
>
> Vision supplies direction, not scope. D-GOV-004 continues to own literal
> continuation invocation and its one-cycle Level 1/2 execution limit. This
> decision changes no Phase 6 criterion or exit status; implements no shared
> renderer, ViewProvider, exact-geometry expansion, output, persistence or
> railway calculation; authorises no Layout Editor feature; accepts no pull
> request, migration completion, output clearance, package, release or phase
> exit; and leaves draft PR #31 separate and unaccepted.

<a id="phase-6-exits-2-and-3-evidence-admission-panel"></a>

## Phase 6 Exits 2 and 3 evidence-admission panel and owner decision

**Decision and exact source state:** This Level 3 evidence-admission panel
applies to accepted `main` at
`a5b6a79bf3e73e1673d440077bd65000986bb4c7`, the merge commit for
[PR #31](https://github.com/Richard-Gnitnub/tracktemplate/pull/31). It assesses
only Exit 2, “No transient production objects leak into the editable document”,
and Exit 3, “Export is deterministic and failure-safe”. Before the owner
decision all Phase 6 exits remained Pending at 0/5. PR #33 performance evidence
and the working tree on its draft branch were excluded.

**Participants, roles and independence:** Richard is project owner, panel chair
and accepting authority. Codex presented the repository evidence and is the
acceptance-alignment change owner. Separate fresh read-only quality and
engineering risk reviewers, neither of whom implemented PR #30 or PR #31,
challenged the panel evidence and independently agreed that Exit 2 was
sufficiently evidenced while Exit 3 was not. The panel review was read-only;
this later alignment changes control documentation and its fail-closed
validator only.

**Evidence reviewed:** The panel reviewed the exact accepted source and tests
from [PR #30](https://github.com/Richard-Gnitnub/tracktemplate/pull/30) and PR
#31, their successful protected standalone CI runs, the retained 56/56 local
standalone result, the qualified FreeCAD 1.1.1/OpenCASCADE 7.8.1 success,
cancellation, injected-failure, cleanup, deterministic-reuse, collision and
rollback records, the exact/export architecture, current risks and output-
status controls. Established qualified FreeCAD proofs were not repeated, and
no GUI or operator proof was admitted.

**Exit 2 evidence admitted:** The signed exact adapter creates its sole
`Part::Feature` only in a UUID-named hidden temporary document whose identity
and ownership are checked before cleanup. It returns a signed numeric receipt,
not a `Part.Shape`. Qualified evidence covers success, deterministic repeat,
zero length, active and inactive document-name collisions, ambiguous ownership,
nested construction, cancellation, cancellation-check failure and injected
Part-build failure. Existing documents, objects, tested properties, filenames,
active-document state and Undo/Redo history remain unchanged. PR #31 also
proves that export stops when cleanup is incomplete.

**Exit 2 retained limitations:** The acceptance is confined to the assessed B16
Entry/Exit exact-validation and export routes. It does not cover GUI observers,
retained shapes, wider template families, operator workflows or product-wide
behaviour. Host-close failure or post-creation registry interference may leave
a separate temporary document while reporting `cleanup_complete=False` and
producing no output. The qualified-host raw stdout/status artifact and an
executable final-harness red replay against the pre-repair source were not
retained. These are accepted evidence limitations and do not widen or negate
the literal bounded criterion.

**Exit 3 evidence and finding:** Deterministic DXF/manifest bytes, hashes and
filenames, byte-identical reuse, independent DXF parsing, non-zero qualified
FreeCAD import, collision refusal, cancellation, staged-failure handling and
caught in-process rollback remain valid bounded evidence. They are
insufficient for Exit 3 because the files commit through sequential hard links
without crash recovery or durable directory commit, path operations are not
descriptor-relative, the zero-length `POINT` lacks qualified import evidence,
and the qualified command/sentinel is not durably registered.

**Exit 3 required-before-exit conditions:**

| Accountable owner | Deadline | Condition |
| --- | --- | --- |
| Export transaction owner | Before another Exit 3 panel | Provide atomic durable commit or an explicit recoverable transaction protocol for the DXF-and-manifest set. |
| Export path-safety owner | Before another Exit 3 panel | Provide descriptor-relative path control sufficient to address rename and symbolic-link races. |
| Export validation owner | Before another Exit 3 panel | Provide focused interruption, partial-commit and recovery evidence. |
| Qualified FreeCAD validation owner | Before another Exit 3 panel | Import and validate the zero-length DXF `POINT` in the qualified FreeCAD profile. |
| Validation-document owner | Before another Exit 3 panel | Register the qualified command and required success sentinel durably in `reference/VALIDATION.md`. |
| Phase owner and independent reviewers | After the preceding conditions pass | Conduct a fresh Level 3 evidence-admission review before any Exit 3 acceptance. |

**Risk disposition:** PR-09 remains Critical/Remove/Partial; PR-13 remains
Critical/Mitigate/Effective (current scope); PR-16 remains
High/Mitigate/Partial; and QA-R03 remains High/Remove/Partial. PR-22 remains
Effective (current scope) because independent challenge and owner decision are
separate. No risk treatment or control-effectiveness value changes.

**Panel recommendation:** Exit 2 was **Proceed with bounded conditions** and
sufficient to recommend `Evidenced`. Exit 3 was **Do not proceed** and must
remain Pending. There was no dissent between the independent reviewers.

**Governance-budget exception:** This task transfers one phase-exit authority,
so its Level 3 evidence, decision, dashboard and executable status-control
changes necessarily exceed its zero product-source lines. It changes no frozen
history, product behaviour, risk register or validation contract.

**Owner decision and resulting authority:** On 2026-08-02 Richard explicitly
accepted the panel recommendation. The resulting decision is:

> **D-P6-002 — Accept Phase 6 Exit 2 and retain Exit 3 Pending**
>
> At accepted `main` source state
> `a5b6a79bf3e73e1673d440077bd65000986bb4c7`, accept Phase 6 Exit 2,
> “No transient production objects leak into the editable document”, as
> `Evidenced` and owner-accepted only for the accepted B16 Entry/Exit transition
> exact-validation and export routes assessed by this panel. Phase 6 advances
> from 0/5 to 1/5. Exit 3 remains Pending until its six recorded
> required-before-exit conditions are satisfied and a fresh Level 3
> evidence-admission review recommends acceptance.
>
> No Phase 6 exit 1, 3, 4 or 5; production or physical-output clearance;
> `project-cleared` status; output equivalence; product-wide export roster;
> GUI or operator workflow; persisted or retained exact geometry; whole-B14 or
> whole-layout parity; legacy retirement; performance acceptance; packaging or
> release authority; or risk downgrade is granted. The export remains
> private-development with deliberately `unknown` project status, and PR #33
> performance evidence does not satisfy Exit 4.

<a id="current-phase-6-exit-condition-disposition"></a>

## Current Phase 6 exit-condition disposition

The accepted current state is 1/5 under D-P6-002:

| Exit condition | Current disposition |
| --- | --- |
| The selected slice has equivalent exact validation and production output for the agreed scope | Pending — exact-validation and private-development DXF evidence exists, but agreed output equivalence and production clearance remain absent |
| No transient production objects leak into the editable document | Evidenced and owner-accepted under D-P6-002 — bounded to the accepted B16 Entry/Exit exact-validation and export routes with the recorded limitations |
| Export is deterministic and failure-safe | Pending — deterministic output and handled in-process rollback are evidenced, but the six required-before-exit conditions remain open |
| Editing resource use improves beyond normal noise, with complete end-to-end cost accounted for | Pending — no accepted beyond-normal-noise improvement evidence; PR #33 is excluded and does not satisfy this exit |
| The legacy path remains available until parity and project-owner acceptance permit removal | Pending — B14 remains available, but whole-scope parity and retirement authority remain absent |

## Carried controls and exclusions

The accepted Coin renderer and B16 Entry/Exit editing behaviour remain bounded
exactly by D-P5-002. Explicit-only lifecycle activation, exactly-once
attachment, duplicate rejection, owner-visible selection/editing, atomic
Undo/Redo, save-time deactivation, reopen reconstruction and the confined
one-empty-switch-child-per-object limitation remain accepted only for that
demonstrated boundary. Reopen D-P5-002 and the retired PR-14 exposure before
retaining any later composition that invalidates the containment or permits
live mappings, caches, proxies, active Coin children or additional residual
switch children to accumulate.

The 24 risks present at Phase 5 closeout remain live in
[risks.json](risks.json); D-GOV-005 updates only the control wording for PR-12,
PR-20 and PR-22. [gate-decisions.json](gate-decisions.json) owns structured
D-P6-001, D-GOV-005 and D-P6-002. Only Exit 2 receives the authority quoted
above; every other exit, clearance, support, schema, oracle-retirement, budget,
packaging, release and later-phase decision remains separately controlled.
