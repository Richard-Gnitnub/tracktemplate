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

## B16 Entry/Exit edit-through-export performance

This bounded Level 2 performance-evidence tranche starts from protected-main
merge
`a5b6a79bf3e73e1673d440077bd65000986bb4c7`. It changes no product source. A
test-owned profiler composes the accepted two-object Entry/Exit editor, the
explicit exact-validation contract and transient FreeCAD wire, and the
private-development DXF exporter as one reconciled action. Three fresh
isolated FreeCAD 1.1.1/OpenCASCADE 7.8.1 processes each applied the selected
Exit edit, validated exact geometry, created the two-file output, then ran one
untimed warm-up and three measured unchanged Validate/Export reuse cycles.

The complete cold journey was 219.127 ms median (112.567–239.585), comprising
103.827 ms edit, 73.026 ms Validate and 41.259 ms created-export medians, with a
per-run uncovered median of 0.768 ms. End-minus-start RSS grew 4.180 MiB median
and the process high-water mark grew 3.918 MiB. Across nine measured reuse
cycles, Validate/Export was 8.972 ms median (8.525–9.997), with zero median
RSS and process-high-water delta. Each cycle still rebuilt and disposed exact
geometry; it did not hide deferred work by skipping validation.

Every run preserved the two compact editable objects, stable mapping, 16
active test-scene nodes and zero `Shape` properties; created one Undo unit;
returned the same 24-vertex/23-edge exact-wire signature from Validate and
Export; left no transient document or staging entry; and produced the same
1,426-byte DXF and 6,829-byte `unknown`-status manifest. The raw and sanitised
method, hashes, individual values, failed-proof classifications and limits are
in the
[performance report](../benchmarks/2026-08-02-phase6-transition-pipeline-performance.md).

Retained validation compiled the changed Python, passed the focused profiler
contract, all 58 standalone validators, qualified exact-contract, transient
exact-geometry and DXF-export checks, and all six `transition-gui` pipeline
steps including the isolated real-GUI ViewProvider proof. No product visual
behaviour changed, so no screenshot evidence was required.

The measured edit range overlaps the accepted Phase 5 one-set edit range, so
this tranche does not establish an improvement beyond normal noise. The B14
plain-line actions are not equivalent in document, exact-geometry or output
scope and are not used to claim a speed-up. The evidence populates the Phase 1
explicit Validate, export-from-validated and complete-journey slots for this
slice, improving PR-15/QA-R04 decision readiness without changing their
Partial controls. It accepts no numerical budget, B14 equivalence, output
clearance, product capacity, operator route, legacy retirement or Phase 6
exit. Under D-P6-002, Phase 6 remains 1/5 with Exit 2 alone Evidenced and
owner-accepted; this evidence does not satisfy Exit 4, which remains Pending.

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

<a id="b16-entry-exit-durable-dxf-recovery"></a>

## B16 Entry/Exit durable DXF recovery

This bounded Level 2 tranche starts from protected `main` at
`7acdab4f925592d49394960c76f7552e1b47be9d`. It changes only the accepted
Entry/Exit private-development DXF route and its validation. The existing DXF
and manifest names, bytes, schema, collision policy, deliberately `unknown`
project status and transient exact-geometry boundary remain unchanged.

The exporter now locks and binds the validated output directory to one real
descriptor and performs journal, staging, inspection, hard-link commit,
rollback and cleanup operations relative to that descriptor. A versioned
internal journal is published and synchronised before the owned staging
directory exists. Staged files and directories are synchronised before commit;
each final link is synchronised before success. The original implementation
also attempted next-invocation rollback or complete-set reuse from a persisted
journal. The later ownership reviews recorded below showed that a
first-observed journal cannot prove its own or an output file's creation
ownership, so that automatic recovery claim is withdrawn.

The standalone validator passed with
`Phase 6 transition DXF export validation passed`. It terminates a child
process immediately after the first and second final links. At the original
source state it observed one-file rollback/recreation and complete-pair reuse,
but those observations did not establish creation-bound authority for the
persisted journal and are not current recovery evidence. It also replaces the requested
directory with a symbolic link during exact validation, after the first link
and after transaction cleanup, proving the redirected directory receives no
file and the bound original directory is rolled back and cleaned. Abrupt
termination after the first late-identity rollback unlink retains newly
published journal and staging controls. The corrected proof below requires
every later invocation to preserve and reject that first-observed residue.
Existing deterministic repeat, zero-length, collision, cancellation,
staged-failure and in-process rollback proofs remain green.

The qualified FreeCAD 1.1.1 profile passed with
`Phase 6 transition DXF qualified FreeCAD validation passed`. In addition to
the existing non-zero `LWPOLYLINE`, isolation, cancellation and injected
rollback checks, FreeCAD imported the zero-length `POINT` as one vertex at the
exact bounded coordinate without changing the editable document, active
document or Undo/Redo history. The stable command and sentinel are now owned by
[`VALIDATION.md`](../VALIDATION.md#verified-commands-and-ci).

| Exit 3 required-before-exit condition | Present evidence after this tranche |
| --- | --- |
| Recoverable DXF-and-manifest transaction | **Open technical gap** — durable live-invocation controls and in-process rollback are present, but no independently trusted creation authority supports cross-process automatic recovery |
| Descriptor-relative rename and symbolic-link control | Present — all transaction operations use the bound directory descriptor and focused replacement proofs fail closed; not yet admitted by a Level 3 panel |
| Interruption, partial-commit and recovery proof | **Open technical gap** — abrupt one-link and two-link termination now prove exact residue preservation and fail-closed rejection, not automatic recovery |
| Qualified zero-length `POINT` import | Present — qualified FreeCAD imports one exact vertex and restores host state; not yet admitted by a Level 3 panel |
| Durable qualified command and sentinel | Present in `reference/VALIDATION.md`; not yet admitted by a Level 3 panel |
| Fresh Level 3 evidence-admission review | **Open** — required before Exit 3 can be recommended or accepted |

The interruption harness proves preservation after abrupt process termination,
not automatic recovery, a physical power-cut or every filesystem failure mode.
The descriptor controls
and directory synchronisation are qualified only on the accepted Linux/FreeCAD
profile; the advisory lock serialises cooperating exporter calls, while
detected same-user interference is handled fail-closed and active racing is
not prevented. No GUI or
operator workflow, broader template family, output equivalence, production or
physical-output clearance, `project-cleared` status, performance improvement,
legacy retirement, packaging, release or Exit 3 acceptance is claimed. Phase 6
therefore remains 1/5 with Exit 3 Pending. PR-09, PR-13, PR-16 and QA-R03 retain
their recorded states; no risk treatment or effectiveness changes.

## B16 Entry/Exit staging-ownership repair

This bounded Level 2 repair starts from protected `main` at
`284695784004320d541cd3fc5def4369e43c7f5c`. The fresh Exit 3 evidence-
admission panel reproduced one implementation defect: after recovery but
before staging creation, a foreign directory could appear at the deterministic
stage name with the exact expected filenames and bytes. `mkdir` then failed
before the exporter captured identity, but live cleanup treated matching
content as ownership and deleted the foreign directory while reporting
complete cleanup. The panel therefore recommended **Do not proceed** for Exit
3 at that source state.

The first repair candidate at
`25360f23fc8393517d8c3ab7145cf7812193dc94` correctly refused a pre-existing
stage, but fresh exact-head review found a remaining `mkdir`-to-first-open
ownership interval. A targeted disposable probe replaced the newly created
directory during that interval with a same-user foreign directory containing
the exact expected filenames and bytes. The candidate deleted the foreign
state and falsely reported `destination_changed=False`,
`cleanup_complete=True` and `recoverable=True`. Content equivalence, owner UID,
permissions and an inode first observed after creation do not establish
creation ownership.

The first independent review of the anonymous-file candidate found the same
principle still violated by cross-process recovery. A pre-existing, valid v2
journal could self-report the live snapshot of one foreign final file; the next
invocation trusted that first-observed record and deleted both the foreign file
and journal. A lone v1 journal was preserved but read before rejection, which
changed its access time. The candidate was therefore blocked again before
publication. There is no independently trusted cross-process root by which a
same-user writable destination can distinguish such a journal from one created
by an earlier invocation.

The supported Python/POSIX surface has no operation that both creates a
directory and returns its descriptor atomically, so another pathname check
cannot close that interval. The corrected candidate eliminates directory
staging. It creates each output in an anonymous regular staging file with
`O_TMPFILE`, captures the device/inode identity immediately from the descriptor
returned by that creation operation, then writes, synchronises and validates
the same descriptor. The internal v2 interruption journal records the exact
creation-bound snapshots. That journal is also created anonymously and linked
from its still-open descriptor before `linkat(AT_EMPTY_PATH)` commits either
output file; `.new` remains only a reserved ambiguity detector.
Normal stage cleanup is descriptor close; there is no staging pathname or
directory removal. At invocation start, any existing journal, temporary-journal
link or legacy deterministic stage pathname is detected by descriptor-relative
non-reading metadata inspection, preserved unchanged and rejected as
unclaimable. Only controls created and identity-bound during the live
invocation may enter its in-process cleanup.

The retained public-export regression fails against `25360f23...` because the
foreign directory is deleted and the false diagnostic is returned. Against the
corrected candidate, substitution before atomic staging, during durable journal
binding and immediately before cleanup preserves the foreign directory, every
file, their identities, metadata and bytes. No final output survives, and no
file appears in the process working directory; the diagnostic reports
`destination_changed=True`,
`cleanup_complete=False` and `recoverable=False`; and a later invocation again
fails closed without altering the foreign state. A normal invocation proves
both anonymous files have zero links before commit and cleans them without any
directory-removal call. Existing cancellation, injected failure, one- and two-
link interruption, in-process rollback, rename, symbolic-link, deterministic-
reuse and collision cases remain passing. The interruption cases now prove
that one-file, two-file and late-rollback residue plus its journal remain exact
and are rejected on the next invocation. They do not claim automatic recovery.
Focused foreign-control cases likewise preserve a self-attesting v2 journal,
matching partial DXF, lone v1 journal and `.new` control, including access time,
without reading their content or creating working-directory files.

The focused standalone exporter validator passes with
`Phase 6 transition DXF export validation passed`. The final DXF and manifest
names, bytes and public schema, collision policy, qualified-import contract and
deliberately `unknown` project status remain unchanged. The earlier qualified
FreeCAD import evidence is retained evidence rather than a fresh host run; this
repair changes internal filesystem transaction behaviour, not the imported DXF
contract. Filesystems or hosts without the required anonymous-file and
descriptor-link primitives fail closed. All pre-existing transaction-control
residue remains preserved for external disposition rather than unsafe
automatic recovery. An independently trusted recoverable transaction protocol
and corresponding interruption/recovery proof therefore remain open Exit 3
technical gaps.

This repair supplies present technical evidence only. It does not accept Exit
3, satisfy the required fresh post-repair Level 3 evidence-admission panel,
alter another exit or risk state, or grant GUI, operator, production, physical-
output, `project-cleared`, equivalence, legacy-retirement, packaging or release
authority. Phase 6 remains 1/5 with Exit 2 alone Evidenced and owner-accepted;
Exit 3 remains Pending.

## IDE workspace-alignment workflow maintenance

This bounded Level 2 governance/tooling tranche starts from protected `main` at
`695627441edcc52ce719fc77902da6f06db66c84` and changes no TrackTemplate
product, railway, FreeCAD or export behaviour. Read-only Git, GitHub,
filesystem and PyCharm metadata showed that the primary project remained on
merged PR #33 while clean accepted `main` was not checked out, and that active
uncommitted recovery-authority work existed solely in a `/tmp` worktree. PR
#33's exact tip and every unique commit were proved contained in accepted
`main` before the primary checkout changed.

The Git-owned reconciliation moved the dirty worktree intact to a named
persistent project location; its seven-path status and binary patch SHA-256
`dab531699189437c07ffbbb07c281e26098338cf4748adb9e2c3b878db2f0543`
remained exact. The primary PyCharm directory now backs clean `main` at exact
`origin/main`; the configured project virtual environment, VCS root and run
working directory remain unchanged. The physical PyCharm branch indicator
still requires operator confirmation because it cannot be observed from the
agent sandbox.

The new instruction-only
[`tracktemplate-ide-workspace-alignment`](../../.agents/skills/tracktemplate-ide-workspace-alignment/SKILL.md)
skill separates file-backed IDE comparison from Git authority and operator-only
UI evidence. `$tracktemplate-continue` composes it before Git mutation and
again after protected-main synchronisation. The agent-guidance validator
fails closed on the new metadata, structure and composition links, and
[LFE-016](../LEARNING_FROM_EXPERIENCE.md) records the reusable lesson.

The skill-structure check, tracked Python/FCMacro parsing, focused agent-
guidance and resource-routing checks, project-progress control, repository QA
and documentation controls all passed. Governance mutation validation rejected
95/95 mutations with zero escapes, and the complete standalone CI profile
passed 58/58. No FreeCAD or GUI rerun was selected because neither product nor
host behaviour changed.

This maintenance has no Phase 6 exit contribution. Phase 6 remains 1/5; Exit
2 alone remains Evidenced and owner-accepted; exits 1, 3, 4 and 5 remain
Pending. Risk states, output authority, accepted evidence and all product
boundaries remain unchanged.

<a id="phase-6-exit-3-recovery-authority-contract-panel"></a>

## Phase 6 Exit 3 recovery-authority contract panel and owner decision

This bounded Level 3 correction cycle starts from accepted `main` at
`cee78cff84618c6a5be3be99714682f5822c814f`. Its product outcome is a safe,
reviewable cross-process recovery contract for the private-development B16
Entry/Exit DXF-and-manifest pair. It assesses only the architecture and
authority needed to address Exit 3 conditions 1 and 3; it changes no product
source, admits no implementation evidence and accepts no Phase 6 exit.

The project owner's 2026-08-02 instructions first authorised selection of the
safest recovery-authority contract and then authorised this correction after
the initial unaccepted draft failed independent review. That draft allowed a
live invocation to verify and then unlink a published pathname. The
filesystem-security and architecture/API reviews rejected the separate
verification-to-unlink interval: even a link initially created by this process
can be substituted before pathname deletion, and POSIX supplies no
expected-inode atomic condition for that deletion. The rejected draft remains
preserved source evidence; it is not decision authority.

The corrected successor was reconstructed on current accepted `main`, retaining
the accepted PR #37 IDE-workspace evidence. Fresh read-only
filesystem-security, architecture/API, governance and staff-level quality
reviewers assessed the complete successor diff. None implemented the decision
or holds owner acceptance authority.

**Why this decision outranks maintenance alternatives:** PR #35 and PR #36
already supply bounded descriptor-relative path control, anonymous payload
creation, no-overwrite publication, durability and foreign-state preservation
evidence. The remaining technical gap is a safe cross-process recovery rule,
not another replay of those proofs. Selecting a non-destructive rule removes
the design loop before implementation without adding an operator workflow,
trust service or output representation.

**Present evidence considered:**

| Evidence | Panel disposition |
| --- | --- |
| Accepted `main` exporter | Anonymous `O_TMPFILE` payloads, no-overwrite descriptor-relative links and directory synchronisation are present; the current verify-then-unlink rollback path is not accepted as post-publication recovery authority, and persisted controls are deliberately not trusted for deletion |
| Application contract | The deterministic two-file result, final names and bytes, manifest schema and contract IDs, `reuse-identical-or-fail` collision policy and `created`/`reused` receipt dispositions are current public constraints |
| Repository consumer inventory | Current validators and profilers are the only repository consumers of the concrete export result; no accepted consumer treats exact-partial collision failure as a required outcome |
| Retained interruption and ownership evidence | One- and two-link termination, collision, substitution, rollback and foreign-control preservation evidence is present, but current source rejects residue rather than recovering it |
| Rejected initial decision draft | Authenticating a final and then unlinking its pathname has an exploitable substitution interval; content, UID, permissions, hashes, xattrs and first-observed identity cannot repair that authority defect |
| POSIX/Linux primitive contract | Anonymous creation supplies a live creation-bound descriptor, no-overwrite `linkat` can add an absent name, and file plus directory `fsync` supplies the bounded durability order; pathname deletion has no expected-inode atomic condition |
| Fresh independent reviews | Strict add-only, journal-free monotonic completion is the narrowest compatible rule and needs no new receipt or manifest schema; post-publication pathname rollback is excluded |

This is present design and implementation evidence, not accepted Exit 3
evidence. D-P6-003 accepts only the recovery-authority contract and later
Level 2 boundary recorded below. The current source still implements the PR
#36 preserve-and-reject behaviour, including the verify-then-unlink path that
the corrected decision forbids after publication; automatic recovery is not
present.

**Options and disposition:**

| Option | Disposition |
| --- | --- |
| Preserve all interruption residue and stop | Safe as the current fallback, but cannot satisfy recovery conditions 1 and 3; rejected as the final contract |
| Trust a destination-local journal, owner UID, permissions, hashes, xattrs or first-observed identity | Rejected; the same-UID actor can forge or replace every proposed authority source |
| Verify an invocation-created link and then unlink its pathname | Rejected; verification and pathname deletion are separate operations, so substitution defeats the claimed ownership condition |
| Add an external key, replay ledger, helper service or long-lived broker | Rejected for this slice; it adds credential lifecycle, platform dependencies and a larger trust boundary |
| Quarantine or recover through an operator decision | Retained only as optional future disposition; it adds an unauthorised GUI/operator workflow and is unnecessary for deterministic completion |
| Publish a generation directory, selector or single bundle | Retained only as a fallback if this protocol is disproved; it changes the output layout or requires protocol-aware consumers |
| Strict add-only, journal-free monotonic completion | Selected; it recovers only by preserving compatible state and adding an absent exact member, never by deleting published or foreign state |

**Selected contract:** Strict add-only, journal-free monotonic completion is
defined by all of these mandatory invariants:

1. Every invocation recomputes the exact expected pair from current signed
   inputs, binds the real destination directory by descriptor and prepares all
   unpublished payloads in anonymous, creation-bound descriptors.
2. Before publication, abandonment consists only of closing owned anonymous
   descriptors; no pathname cleanup authority is inferred.
3. Publication may only add an absent deterministic final pathname, without
   overwrite, from its synchronised anonymous descriptor.
4. No published final file may be unlinked, renamed, rewritten, truncated,
   replaced or otherwise claimed by TrackTemplate.
5. Pathname-based rollback ends permanently at the first successful final
   link.
6. After any post-publication failure, every published final is preserved,
   including an exact partial or complete output pair.
7. A later invocation may add only an absent exact counterpart; it may not
   reconstruct, replace or remove the member already present.
8. Existing finals are inspected descriptor-relatively for regular-file type
   and exact bytes, but that inspection grants no deletion or replacement
   authority.
9. Success is reported only after the complete final pair and required
   durability state are independently revalidated as exact.
10. Substitution, ambiguity, collision, replay, inconsistency, a symbolic link
    or non-regular member fails closed without further mutation.
11. A race discovered after an addition leaves every published file untouched
    and reports failure truthfully, even if an exact pair is then observed.
12. `cleanup_complete`, `recoverable`, `destination_changed` and related
    diagnostics describe the state actually retained, not an intended
    rollback.
13. Identical complete-pair reuse, deterministic bytes and filenames, manifest
    schema, contract IDs, no-overwrite behaviour and collision refusal remain
    unchanged.
14. A host or filesystem without every required anonymous-file,
    descriptor-relative no-overwrite link and durability primitive fails
    closed.

Historical journals, `.new` links and stage artifacts are inert foreign
residue: they are never opened, parsed, modified or deleted and their presence
neither permits nor blocks final-set completion. If neither final exists, the
exporter may add both. If exactly one exact regular member exists, it preserves
that member's inode, metadata and bytes and adds only the missing exact
counterpart. If both exact regular members exist, it independently revalidates
and reuses the pair. Any other state fails unchanged.

These security statements are absolute within the bounded contract:
authenticating or verifying a pathname does not create authority to delete it;
POSIX pathname deletion has no expected-inode atomic condition; rollback ends
permanently at the first publication link; cross-process recovery means safe
monotonic completion, not destructive cleanup; and foreign or uncertain
destination state is never removed by TrackTemplate.

Diagnostics remain conservative. `destination_changed=True` after any
successful addition, and uncertainty caused by interference must not be
reported as an unchanged destination. `cleanup_complete=True` may describe
only a clean pre-publication failure after every invocation-owned unpublished
resource is closed. A surviving published final on a failed invocation requires
`cleanup_complete=False`; it was not rolled back. `recoverable=True` requires
an independently revalidated exact zero-member, partial or complete destination
with safe retry or remaining add-only authority; ambiguity, mismatch, uncertain
durability or an unsupported primitive is not recoverable. Content equivalence
establishes compatibility for reuse or addition only; it never grants
ownership, deletion or replacement authority.

This preserves the final filenames, DXF and manifest bytes, manifest schema
and contract IDs, two-file layout, deterministic generation, no-overwrite
behaviour and `reuse-identical-or-fail` policy. It accepts one narrow observable
refinement: an exact regular partial pair may be completed instead of rejected
as a collision. `created` continues to mean that the invocation published at
least one member; `reused` continues to mean that the complete pair already
existed. The collision policy is therefore defined per final member: reuse an
exact regular member, create only its absent deterministic counterpart and fail
on a non-identical or non-regular existing member. No material owner choice
remains because this refinement is inside the owner-delegated contract
selection and introduces no UI, configuration, dependency, trust root or
output representation.

**Bounded later Level 2 authority and conditions:**

| Accountable owner | Required work before publication |
| --- | --- |
| Export adapter owner | Implement only the strict add-only, journal-free monotonic state machine in `tracktemplate/adapters/export/transition_dxf.py`; retain bound-directory, anonymous-file and no-overwrite controls, close owned descriptors before publication on failure, and remove every post-publication pathname rollback path |
| Application-contract owner | Define `reuse-identical-or-fail` per final member in narrowly necessary wording in `tracktemplate/application/transition_export.py`; freeze both export contract/result IDs, the collision-policy value and receipt dispositions; stop for a separate API decision if an accepted consumer depends on exact-partial failure or truthful implementation needs another public change |
| Validation owner | Retain focused zero-member, DXF-only, manifest-only, complete-pair, mismatch, symlink, non-regular, cancellation, injected-failure, rename and substitution cases; prove pre-publication descriptor abandonment, interruption after each addition, post-addition races and next-invocation monotonic completion; prove fresh and partial creation have identical output fingerprints and `created` result signatures |
| Filesystem-security owner | Prove pre-existing exact members and inert controls retain inode identity, metadata and bytes; prove equality and pathname verification never authorise deletion; prove no published final is unlinked or otherwise mutated after any failure, race or later invocation; and prove diagnostics match exact retained states |
| Documentation and governance owner | Record the implemented evidence without changing Phase 6 from 1/5 or implying that Exit 3 is Evidenced; retain exact output fingerprints and deliberately `unknown` project status |
| Independent reviewers | Review the exact Level 2 head for architecture/API, filesystem-security and quality; after merge, leave Exit 3 Pending for a fresh bounded Level 3 evidence-admission panel |

The authorised implementation remains limited to the exporter, narrowly
necessary application-contract wording, its focused retained validator, one
concise current-evidence entry and directly dependent governance controls. It
must stop without publication if it would read or delete legacy controls,
unlink, rename, rewrite, truncate or replace a published final, derive deletion
authority from content, metadata or pathname verification, change final
names/bytes/schema/layout, weaken collision refusal, change contract/result IDs
or the collision-policy value, or add an operator workflow, secret store,
helper service, generic storage framework or runtime dependency.

**Residual limitations and risk panel:** The pair is recoverable rather than
simultaneously visible through one namespace operation. A partial exact set
may remain until another invocation; there is no background or operator
recovery. Changed expected bytes correctly leave an old partial as a preserved
collision. Detected active same-UID interference fails closed, but the exporter
cannot prevent mutation after its final observation. Historical controls may
remain as inert hidden residue. Descriptor-link and durability evidence remains
bounded to the qualified Linux/filesystem profile. Additional physical-power-
loss matrices, malformed or orphaned controls, lock contention, unpublished-
journal interruption and bounded residue reads remain optional future
hardening rather than new mandatory blockers for this bounded contract.

PR-09 remains Critical/Remove/Partial, PR-13 remains
Critical/Mitigate/Effective within its current scope, PR-16 remains
High/Mitigate/Partial, PR-22 remains High/Remove/Effective within its current
scope and QA-R03 remains High/Remove/Partial. The contract reduces the design's
need for destructive cross-process authority but supplies no implementation
evidence or risk closure, so no risk state, treatment or effectiveness changes.
Phase 6 remains 1/5 with Exit 2 alone Evidenced and owner-accepted; Exit 3 and
exits 1, 4 and 5 remain Pending.

**Panel recommendation:** **Proceed with bounded conditions.** The fresh
filesystem-security and architecture/API reviewers accept the strict add-only
contract and later Level 2 boundary; the governance and staff-level quality
review finds no status, evidence or authority contradiction. No material owner
choice or dissent remains.

Under the authority explicitly delegated in the project owner's 2026-08-02
instruction, the resulting decision is:

> **D-P6-003 — Select strict add-only, journal-free monotonic completion for
> Exit 3 recovery**
>
> At accepted `main` source state `cee78cff84618c6a5be3be99714682f5822c814f`,
> select strict add-only, journal-free monotonic completion as the required
> cross-process recovery-authority contract for the bounded B16 Entry/Exit
> DXF-and-manifest pair. A later bounded Level 2 tranche is authorised to
> recompute the exact expected pair, create unpublished payloads only in
> anonymous creation-bound descriptors, abandon unpublished work only by
> closing those descriptors, inspect existing finals without acquiring
> mutation authority, and publish only by adding an absent final pathname
> without overwrite. The first successful final link permanently ends
> rollback. No published final may be unlinked, renamed, rewritten, truncated
> or replaced; authenticating or verifying a pathname does not grant deletion
> authority, and POSIX pathname deletion has no expected-inode atomic
> condition. After any post-publication failure, all published finals are
> preserved, including any exact partial or complete output pair. A later
> invocation may add only an absent exact counterpart, and success may be
> reported only after the complete final pair is independently revalidated as
> exact. Mismatch, non-regular finals, symbolic links, collision, replay,
> substitution, inconsistency, ambiguity or unsupported primitives fail closed
> without further mutation. Foreign or uncertain destination state is never
> removed, and `cleanup_complete`, `recoverable`, `destination_changed` and
> related diagnostics must describe the state actually retained.
> `recoverable=True` is permitted only after independently revalidating an
> exact zero-member, partial or complete destination with safe retry or
> remaining add-only authority; ambiguity, mismatch, uncertain durability or
> an unsupported primitive remains non-recoverable. Any successful addition
> requires `destination_changed=True`, and any surviving published final on a
> failed invocation requires `cleanup_complete=False`. Identical complete-pair
> reuse, deterministic filenames and bytes, manifest schema and contract IDs,
> the two-file layout, no-overwrite behaviour and
> `reuse-identical-or-fail` collision refusal remain unchanged; one exact
> regular partial member may now be completed rather than treated as a
> collision. Phase 6 remains 1/5 and Exit 3 remains Pending until
> implementation, focused interruption/recovery evidence and a fresh Level 3
> evidence-admission review.
>
> No product code is changed by this decision. It does not mark Exit 3 or
> another exit `Evidenced` or owner-accepted; grant production,
> physical-output, `project-cleared`, equivalence, GUI, operator, wider-family,
> performance, legacy-retirement, packaging or release authority; or change a
> risk state. It does not authorise post-publication unlink, rename, rewrite,
> truncation, replacement or pathname-based rollback; reading or deleting
> pre-existing controls; mutation of any foreign or uncertain destination
> state; deriving deletion authority from equality, metadata or pathname
> verification; changing output names/bytes/schema/layout, contract/result IDs
> or the collision-policy value; or adding a trust service, generic storage
> framework or runtime dependency.

## B16 Entry/Exit add-only DXF monotonic recovery

This bounded Level 2 tranche starts from accepted `main` at
`ccacb5ca638b1e3a79fb59107a97d90e9434f0d5` and implements only the
D-P6-003 recovery contract for the private-development B16 Entry/Exit
DXF-and-manifest pair. Before the source change, the retained focused
regression failed because an exact regular partial pair raised
`transition-dxf-export-collision` instead of adding its absent counterpart.

The exporter now recomputes and validates the exact pair, binds the destination
directory by descriptor, stages only absent payloads in anonymous
creation-bound descriptors and publishes through no-overwrite `linkat`.
Existing exact regular members are inspected without mutation authority and
retain inode identity, metadata and bytes. Historical journals, `.new` files
and stage directories are inert: the exporter neither reads nor changes them,
and their presence does not block completion. The source contains no
post-publication rollback, journal cleanup or final-path unlink route.

The retained standalone validator passed with its required
`Phase 6 transition DXF export validation passed` sentinel. It covers fresh,
DXF-only, manifest-only and complete states; exact partial completion with the
same `created` result signature as fresh creation; interruption after each
addition; next-invocation completion only after required directory
synchronisation; fail-closed complete-pair preservation when that
synchronisation fails; cancellation and injected failure after one addition;
uncertain durability; unsupported primitives; resolve-to-bind removal and
substitution; post-lock, initial-member and post-addition substitution;
directory rename and symbolic-link races; active-lock ambiguity; non-regular
and byte-collision refusal; inert foreign controls; observed descriptor closure on
pre-publication abandonment; and a sentinel proving no unlink, rename, replace
or rmdir call over normal publication. It freezes the accepted-main output
hashes:

| Fixture | DXF SHA-256 | Manifest SHA-256 |
| --- | --- | --- |
| 300 mm transition | `6861d0565a737615ec5b242aaa8d2b3efd51b0e22aad9d93fb929489a25fd861` | `16de67625d952e9bb0c7c3f7891b30987f78d7c5878a9838999ab0909f131552` |
| zero-length transition | `7b2757bc3559013a2399df7efe6c25721288f8dad56b6cc05d93c2938c86c2b1` | `8cff21c710de1da266d0a0c590cd90dc4edf46c37403275c146e2ffe5a9b3e9f` |

The qualified FreeCAD 1.1.1 profile also passed with
`Phase 6 transition DXF qualified FreeCAD validation passed`. It retained
editable-document and active-document isolation, imported both the
`LWPOLYLINE` and zero-length `POINT`, preserved an exact partial after an
injected second-addition failure and completed it on the next invocation.

This is present Level 2 implementation and focused recovery evidence, not an
Exit 3 evidence-admission or owner-acceptance decision. Conditions 1 and 3 now
have bounded evidence; descriptor-relative path control, qualified `POINT`
import and durable command registration remain retained evidence for
conditions 2, 4 and 5. Condition 6 remains open: a fresh Level 3 panel must
distinguish criterion requirements, accepted bounded limitations and optional
hardening before any Exit 3 recommendation.

The pair remains sequentially visible rather than namespace-atomic; an exact
partial may remain until a later invocation. There is no background or operator
recovery, and changed expected bytes leave old partial output as a preserved
collision. Evidence remains bounded to the qualified Linux/filesystem profile
and the accepted Entry/Exit slice. Phase 6 remains 1/5 with only Exit 2
Evidenced and owner-accepted; Exit 3 remains Pending. PR-09, PR-13, PR-16,
PR-22 and QA-R03 retain their existing states, and no production, physical
output, `project-cleared`, GUI, release, packaging or legacy-retirement
authority changes.

## B16 Entry/Exit surviving-host interruption cleanup

This bounded Level 2 repair starts from protected `main` at
`49d9a85ee3f942a801c65f1cd051a2586ffa10d8`. A fresh Exit 3 admission probe
showed that a cancellation callback raising `KeyboardInterrupt` after both
anonymous payloads were staged bypassed the `Exception`-only cleanup path and
left both descriptors open in a surviving host. The retained focused
regression failed against that source with `anonymous staging descriptor
remained open`, classified `implementation-defect` under D-P6-003 invariant 2.
A first independent security review then blocked retention: injected descriptor
close failure replaced the direct interruption, and a direct interruption after
`linkat` but before directory `fsync` could be reported recoverable. The added
close-failure regression failed against that first reviewed state by receiving
`TransitionDxfExportError` instead of the original `CleanupInterruption`; both
findings were classified at the same implementation boundary.
A second independent security review confirmed those paths but blocked
retention because a first direct interruption during normal-success descriptor
cleanup stopped the remaining closes, and a bound-directory close error could
replace an already propagating interruption. Its disposable probe observed both
anonymous descriptors still open; the retained regression reproduced
`[True, True]` against that second reviewed state. These were again classified
at the same resource-ownership boundary.

The exporter now catches `BaseException` only at its anonymous-resource and
bound-operation ownership scopes. Each descriptor enters the outer ownership
map immediately after open. Cleanup attempts every observed invocation-owned
anonymous descriptor even when one close raises a direct `BaseException`, and
preserves the original `KeyboardInterrupt`, `SystemExit` or custom direct
`BaseException` type and value. The completion and bound-directory cleanup
routers also preserve an active direct interruption; failed or uncertain close
is reported cleanup-incomplete and non-recoverable through the existing chained
`TransitionDxfExportError`. Publication is marked durability-uncertain before
`linkat` until the directory `fsync` returns, so interruption in that interval
is also non-recoverable. Before publication with successful cleanup the
diagnostic is unchanged/clean/recoverable; after a durable addition it is
changed/not-clean/recoverable, the exact final remains untouched and a later
invocation adds only its missing counterpart. No exception class, public ID,
receipt, filename, output byte, schema or collision policy changes.

The focused standalone validator passed with `Phase 6 transition DXF export
validation passed`, covering interruption inside staging, between staged
payloads, before publication, after one durable addition, through injected
descriptor-close failure, during normal-success close iteration, through a
bound-directory close failure and in the post-link/pre-sync interval. The
qualified FreeCAD 1.1.1 validator passed with `Phase 6 transition DXF qualified
FreeCAD validation passed`; the same `KeyboardInterrupt` propagated after
descriptor cleanup, the editable host state remained exact and a later export
succeeded. Process-kill, `os._exit` and a second asynchronous interruption
during cleanup remain outside this surviving-host proof. This is repair
evidence only: Exit 3 remains Pending for a fresh Level 3 panel, Phase 6 remains
1/5 and no risk or output authority changes.

<a id="current-phase-6-exit-condition-disposition"></a>

## Current Phase 6 exit-condition disposition

The accepted current state is 1/5 under D-P6-002:

| Exit condition | Current disposition |
| --- | --- |
| The selected slice has equivalent exact validation and production output for the agreed scope | Pending — exact-validation and private-development DXF evidence exists, but agreed output equivalence and production clearance remain absent |
| No transient production objects leak into the editable document | Evidenced and owner-accepted under D-P6-002 — bounded to the accepted B16 Entry/Exit exact-validation and export routes with the recorded limitations |
| Export is deterministic and failure-safe | Pending — the bounded D-P6-003 add-only implementation and focused condition 1/3 proof are present; conditions 2, 4 and 5 retain bounded evidence, while condition 6 still requires a fresh Level 3 evidence-admission review and explicit owner acceptance |
| Editing resource use improves beyond normal noise, with complete end-to-end cost accounted for | Pending — PR #33 accounts for complete cold/warm Edit, Validate and Export cost, but the edit range overlaps Phase 5 and demonstrates no improvement beyond normal measurement noise; it does not satisfy Exit 4 |
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
D-P6-001, D-GOV-005, D-P6-002 and D-P6-003. Only Exit 2 receives Evidenced and
owner-accepted status; D-P6-003 selects a recovery contract and later Level 2
boundary only. Every other exit, clearance, support, schema,
oracle-retirement, budget, packaging, release and later-phase decision remains
separately controlled.
