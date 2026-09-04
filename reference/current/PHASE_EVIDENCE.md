# Phase 6 Explicit Exact-Validation and Export Seam Evidence

Status: **Current — 2/5 accepted exits. The owner accepted Exit 2 under
D-P6-002 on 2026-08-02. The owner accepted Exit 3 under D-P6-005 on
2026-08-15. Exits 1, 4, and 5 remain Pending.**

Phase 5 closed at 4/4 under D-P5-003 on 2026-08-01. Its complete accepted
evidence, decisions and risk snapshot are frozen in the
[Phase 5 closeout](../history/phase-closeouts/PHASE5_CLOSEOUT.md). This fixed
live path owns current Phase 6 evidence and does not alter that frozen record.

## Opening architecture review

Phase 6 owns the explicit exact-validation and export seam. This seam includes
complete stage signatures, invalidation, transient exact geometry, cleanup,
output equivalence, and transactional export. It also includes rollback and
complete edit-through-export performance evidence.

The accepted B16 Entry/Exit slice supplies bounded canonical transition intent
and lightweight editing behaviour. The project has not accepted an exact
centreline result, exact oracle, export writer, output clearance, or Phase 6
performance result.

Three routes were reviewed:

| Route | Disposition |
| --- | --- |
| Keep Phase 6 unopened | Safe. It does not advance an accepted exact-validation or export exit. D-P6-001 supersedes this route. |
| Port the complete B14 export path | Rejected. It expands to whole-layout and later-family work. It retains exact legacy shapes instead of the B16 canonical state. It would transfer a characterised partial-output failure to the successor path. |
| Establish a narrow B16 Entry/Exit Validate/Export seam | Recommended as the smallest reversible route. It can prove one exact centreline result and oracle, transient FreeCAD geometry, private-development output, and complete cost. It accepts no migration or production clearance. |

<a id="phase-6-opening-panel"></a>

## Phase 6 opening panel and owner decision

**Decision and exact source state:** This Level 3 opening applies to clean
protected `main` at `35d4124c28d6be7e536a5f3773681ff0bf243283`, the merge
commit for [PR #27](https://github.com/Richard-Gnitnub/tracktemplate/pull/27).
This authority-only record changes no product source. All five Phase 6 exits
remain unevidenced at 0/5.

**Participants, evidence and independence:** Richard is project owner,
decision chair and accepting authority. Codex performed the separate fresh
read-only opening review and is the decision-record change owner. Codex had no
Phase 6 implementation role because no Phase 6 product implementation exists.
The same reviewer synthesised the architecture recommendation and risk
challenge, so those two review roles were not independent. This was an
engineering control review, not professional legal advice.

**Evidence reviewed:** The panel reviewed the
[project dashboard](../PROJECT_PLAN.md), the 24 live risks in
[risks.json](risks.json), the frozen
[Phase 5 handoff](../history/phase-closeouts/PHASE5_CLOSEOUT.md), and the
accepted
[exact-geometry and export architecture](../ARCHITECTURE.md#5-exact-geometry-adapter).
The panel also reviewed the
[validation boundary](../VALIDATION.md#5-exact-geometry-and-export-validation),
the [generated-output controls](../LICENSING_BOUNDARIES.md#generated-output-policy),
and the B16 Entry/Exit transition source and tests. It reviewed the
characterised B14 create-time export failure. At the exact source state, the
local standalone CI
profile passed 54/54 validators and the merged PR's protected GitHub Actions
check passed. No Phase 6 FreeCAD exact-geometry result exists. No target-format
export, real-GUI, or performance result exists. These absences are the correct
0/5 opening state.

**Risk disposition:** PR-09 remains Critical/Remove/Partial. Phase 6 may build
only a private-development output path. It may not advertise or clear output
while any dependency is restricted, reference-only, or unknown. PR-13 remains
Critical/Mitigate/Effective for the current bounded scope. Current checkpoints,
copied FreeCAD inputs, and disposable destinations remain necessary before
risky work. PR-17 remains Critical/Mitigate/Partial because this opening grants
no persistence or migration authority.

PR-15, PR-16, QA-R03, and QA-R04 remain Partial for deferred cost, signatures,
end-to-end evidence, and budgets. PR-20, PR-21, and PR-22 remain Effective for
the current bounded scope. This status applies only while the slice,
provenance, and structured challenge remain bounded. D-P5-002 and the retired
PR-14 exposure must reopen if later composition invalidates the accepted Coin
residual containment. No risk treatment or control-effectiveness value changes.

**Recommendation, bounded conditions and unknowns:** The separate review
recommended **Proceed with bounded conditions**:

| Accountable owner | Deadline | Condition |
| --- | --- | --- |
| Exact-validation and export owners | Before retaining exact or export behaviour | Define the selected exact centreline result, oracle, units, frame, tolerances, and equivalence contract. Prove that the current B16 transition intent is sufficient. Do not port the complete B14 exporter. |
| Signature owner | Before retaining reuse or caching | Cover every analysis, exact-validation, and export input with complete stage signatures. Prove miss, reuse, change, change-back, invalidation, and stale-result rejection. |
| FreeCAD exact-geometry owner | Before retaining transient geometry | Use a temporary or isolated FreeCAD document. Prove cleanup after success, failure, and cancellation. Prove that the editable document remains unchanged. |
| Export owner | Before retaining a target-format writer | Resolve safe destinations, deterministic names, collisions, and overwrite policy. Stage and validate the complete set. Commit atomically or roll back completely with a truthful summary. |
| API, licensing and provenance owners | Before any manifest-schema change or output-clearance proposal | Produce a dependency manifest for the selected output and keep it private-development unless its status supports the declared use. Give any required manifest-schema change separate API, licensing, validation and owner review. |
| Performance owner | Before a Phase 6 exit proposal | Measure comparable cold and warm Edit, Validate, Export, and complete end-to-end cost with correctness checks. Do not invent a numerical budget. |
| Recovery and bounded-scope owners | Before each risky host/export run and throughout Phase 6 | Use copied FCStd inputs, disposable output destinations, and a current recoverable checkpoint. Preserve the legacy oracle and the D-P5-002 reopen condition. |

The first exact centreline result and oracle remain Level 2 investigation
results. The target format also remains a Level 2 investigation result. The
same status applies to whether the current manifest schema can express the
successor transition data. There was no dissent from the bounded
recommendation.

**Governance-budget exception:** This task transfers phase authority. It does
not implement product behaviour. The required Level 3 panel and evidence
therefore exceed its zero product lines. The same applies to the decision
register, dashboard, and executable status-control changes. No policy or frozen
historical record changes.

**Owner decision and resulting authority:** On 2026-08-01 Richard stated,
“I accept D-P6-001 exactly as presented.” The accepted decision is:

> **D-P6-001 — Open Phase 6**
>
> At source state `35d4124c28d6be7e536a5f3773681ff0bf243283`, open Phase 6
> at 0/5 for bounded exact-validation and export-seam work on the accepted B16
> Entry/Exit transition slice. Separate Level 2 tranches may establish the
> exact centreline result, oracle, and contracts, complete stage signatures and
> invalidation, transient exact geometry in a disposable FreeCAD document,
> private-development target-format export with atomic staging and rollback,
> and complete edit/Validate/Export performance evidence.
>
> No Phase 6 exit, production-output clearance, or `project-cleared` status is
> accepted. No operator route, migration route, whole-layout work, or complete
> B14 export port is accepted. No persisted-schema change, retained production
> shape, or legacy-oracle retirement is accepted. No numerical performance
> budget, new runtime dependency, packaging, release, or later-phase authority
> is accepted. Any required manifest-schema change receives separate API,
> licensing, validation, and owner review.

## B16 Entry/Exit exact-centreline contract

This necessary-enabling Level 2 tranche starts from protected-main merge
`838f6b52389ea604fecceb307773077873ccfe40`. It adds one ephemeral,
adapter-neutral exact-validation profile for the accepted transition slice.
The caller supplies the maximum analytical chord error and a hard segment
ceiling. The signed v1 contract also fixes canonical local left-turn space,
millimetres/radians, the existing B15-parity numerical profile and its explicit
integration setting.

Equal arc-length stations use the conservative Euler
curvature interpolation bound `h^2 / (8R)`. They preserve both endpoints and
return one deterministic centreline. They also return an exact-centreline
signature and a validation-result signature for use as a later export-stage
dependency.

The focused standalone proof compares every retained point with an independent
high-precision Fresnel power series. It samples every chord against the
analytical limit. It covers zero length, invalid resolution, and segment-cap
rejection. It also covers miss, reuse, label-only reuse, numerical change, and
change-back. Stale-state rejection and failure atomicity are also included.

The qualified FreeCAD 1.1.1 smoke printed
`Phase 6 transition exact qualified FreeCAD validation passed`. It changed no
document, object, property, active document, or Undo/Redo state. At the final
source shape, 174 tracked Python/FCMacro files parsed. The complete standalone
CI profile passed 55/55 validators.

This tranche creates no `Part` geometry, target-format writer, dependency
manifest, or file output. It creates no editable-document mutation, persisted
property, schema, or GUI command.

It accepts no production clearance, product
tolerance default, legacy retirement, or phase exit. At tranche retention,
all five Phase 6 exits therefore remained Pending. D-P6-002 later accepts only
Exit 2. Transient exact FreeCAD geometry remained separate work. Transactional
private-development export and complete edit-through-export performance also
remained separate work.

## B16 Entry/Exit transient exact geometry

This exit-closing Level 2 tranche starts from protected-main merge
`1e812612c8eab818554bf0d5d0208ebcc79b2490`. The FreeCAD adapter verifies the
signed exact-centreline result. It allocates a per-invocation temporary name
that is absent from the pre-operation registry. Before it adds the sole
`Part::Feature`, it verifies the returned document as one newly registered
identity. Cleanup
closes only that positively owned document and fails closed when ownership is
ambiguous.

The adapter then validates ordered coordinates, bounds, polyline
length, topology, and kernel validity. After disposal, it returns only a
deterministic signed numeric receipt. Non-zero profiles are open wires. The
accepted zero-length analytical case becomes one vertex. The adapter introduces
no railway calculation or persistent truth.

The qualified FreeCAD 1.1.1/OpenCASCADE 7.8.1 proof exercised deterministic
repeat construction. It included an inactive and active pre-existing hidden
temporary document with the same name. It covered ambiguous ownership
rejection before object creation, nested construction, and zero length. It also
covered invalid exact-centreline result rejection, cancellation,
cancellation-check failure, and injected Part-build failure.

Every path closed only its owned temporary document. Each path restored an
existing or empty active-document state. Each path preserved all pre-existing
documents and objects. It also preserved their tested properties, values,
FileName, and Undo/Redo counts. At the final source shape, 176 tracked
Python/FCMacro files parsed. The complete standalone CI profile passed 55/55
validators.

This tranche provides technical evidence toward the transient-cleanup exit
gap. It accepts no Phase 6 exit. It adds no retained `Part` shape, persisted
property, schema, or GUI operation. It adds no export writer, file, manifest,
or overwrite policy. It accepts no output equivalence, output clearance,
legacy retirement, product tolerance default, or performance budget.
Transactional private-development export remains separate work. Complete
edit-through-export performance also remains separate work.

## B16 Entry/Exit private-development DXF export

This exit-closing Level 2 tranche starts from protected-main merge
`61237508b0c1fefedcf740afd230e5e563acab3e`. It adds one signed export-stage
contract for the current exact-validation result and one deterministic ASCII
DXF 2000 writer for the accepted Entry/Exit centreline. The contract binds the
format, canonical local frame, millimetres, layer, collision policy, generator
version, dependency-manifest schema and deliberately `unknown` project status.
The writer emits one open `LWPOLYLINE`, or one `POINT` at zero length, beside a
schema-v1 output dependency manifest. Its canonical-model digest and output-file
hashes are independently checkable.

Hidden staging and no-overwrite collision
handling contain the tested in-process failure paths. Byte-identical reuse,
identity-checked commit rollback, and ownership-aware cleanup also contain
those paths. These controls do not mutate canonical or editable-document
state. They do not make the two-file commit crash-atomic or close a pathname
race.

The standalone proof independently parsed the DXF group codes and ordered
coordinates. It accepted the manifest only as `unknown` and rejected it under
`--require-project-cleared`. It covered stale or corrupt input, zero length,
and unsafe or symbolic-link destinations. It also covered partial and different
collisions, external destination change, and cancellation at each pre-commit
stage. Staged corruption, injected write or commit failure, and ambiguous
rollback ownership were also included.

Qualified FreeCAD 1.1.1/OpenCASCADE 7.8.1 rebuilt and disposed the exact Part
geometry. It reopened the resulting `AC1015` file as one millimetre-scale
polyline with no unsupported feature. It preserved all pre-existing documents,
objects, tested properties, values, active-document state, and Undo/Redo counts.
This preservation covered success, reuse, cancellation, injected geometry-build
failure, truthful geometry-cleanup failure, and commit rollback.

At the final source shape, 181 Python/FCMacro files parsed. All 56 standalone
CI validators passed. The upstream exact-contract and transient-geometry
qualified checks also passed.

This tranche supplies bounded technical evidence toward exact target output
and deterministic, failure-safe export only. It selects no product-wide format
roster. It adds no operator, GUI, or migration route. It adds no persisted
schema or retained shape.

It accepts no production clearance, physical-output
clearance, or `project-cleared` status. It accepts no performance budget,
legacy retirement, Phase 6 exit, or later-phase authority.
At tranche retention the 0/5 exit disposition therefore remained unchanged
pending separate owner acceptance. D-P6-002 later accepts Exit 2 only. Exit 3
remains Pending with the required-before-exit conditions recorded below.

<a id="product-vision-and-execution-governance-panel"></a>

## Product vision and execution governance panel

**Decision and repository state:** This Level 3 governance decision applies to
accepted `main` at `61237508b0c1fefedcf740afd230e5e563acab3e`, the merge commit
for PR #30. PR #30 is therefore merged, not pending. Draft PR #31 and its
bounded transition-DXF branch remain separate, unaccepted Phase 6
implementation. This governance branch was created from accepted `main` and
does not alter, rebase, ready or merge that work. Phase 6 remains current at
0/5, and this panel admits no new phase-exit evidence.

**Options reviewed:** Three governance shapes were compared:

| Option | Disposition |
| --- | --- |
| Infer direction from the plan and select its next unchecked item | Rejected. Phase ordering is not product purpose. An unchecked entry is not bounded task authority. |
| Repeat the complete vision in `AGENTS.md`, skills and planning records | Rejected. Duplicated authority would worsen PR-12 and let the copies drift. |
| One canonical Product Vision, accepted architecture clauses and linked vision-led workflow controls | Recommended. It gives purpose one owner. It keeps programme, phase, evidence, assignment, and acceptance authorities distinct. |

**Participants, evidence and independence:** Richard is project owner,
decision chair and accepting authority for the governing direction. Codex is
the architecture-review presenter, risk challenger and governance-patch change
owner, so those roles are not independent. A fresh read-only quality review of
the complete final patch and raw validation is required before readiness can be
reported. That review cannot itself accept the Level 3 decision or a Phase 6
exit.

The review reconciled `AGENTS.md`, Engineering Policy, this live record, and
its risk/decision registers. It reconciled the Project Plan, the frozen Phase 5
closeout, Agent Workflows, and the Chief of Staff and continue skills.

It reconciled documentation-authority rules, architecture and modularisation
owners, and ViewProvider/Coin source and lifecycle tests. It also reconciled
exact-geometry/export limits and the Phase 1 legacy capability inventory and
fixtures. Accepted source/branch history and the open pull-request relationship
were included. Source and tests were treated as evidence rather than decision
authority.

**Risk disposition:** PR-12 remains Open/Mitigate/Partial. A single Product
Vision owner and link-based routing reduce product-direction and task-selection
ambiguity, but the enlarged governance surface can still drift. PR-20 remains
Open/Mitigate/Effective for the current bounded scope. Core and Layout Editor
horizons, task traceability, and explicit non-goals control contamination from
future work. Later implementation must continue to prove this separation.

PR-22 remains Open/Remove/Effective for the current bounded scope. The
structured decision controls this authority transfer. The separation of
claimed, present, validated, and independently accepted states also controls
it. Final patch review and owner acceptance remain separate. No implementation
risk is removed or downgraded.

**Recommendation and bounded conditions:** Proceed with the canonical vision,
architecture clauses and vision-led workflow under these conditions:

| Accountable owner | Condition |
| --- | --- |
| Documentation-control owner | Keep product purpose and programme horizons in `PRODUCT_VISION.md`. Link to them instead of copying them elsewhere. |
| Architecture owner | Treat D-GOV-005-A through D-GOV-005-G as direction and label every undemonstrated renderer, display, exact or performance capability honestly. |
| Chief of Staff or continuation owner | Trace each assignment to an evidenced finding or active exit. State regressions, evidence, and non-goals. Prevent unchanged loops. Reconcile claimed, present, validated, and accepted states. |
| Phase owner | Apply only the active phase authority. Future Layout Editor direction neither changes Phase 6 exits nor supplies implementation authority. |
| Quality reviewer and project owner | Keep implementation review independent where required. Do not let an implementer or validator become the sole acceptance authority. |

**Governance-budget exception:** This owner-authorised task changes product,
architecture, and workflow authority. Its canonical vision and Level 3 panel
therefore exceed the zero product-code change. The same applies to the decision
and risk records, dashboard links, and structural validators. It rewrites no
frozen history. It adds no production architecture only to demonstrate the
documentation.

**Owner authorisation and resulting decision:** On 2026-08-01 the project owner
explicitly authorised this Level 3 governance work and supplied the product and
execution limits recorded here. The resulting decision is:

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
> Vision supplies direction. It does not define a bounded scope or give task
> authority. D-GOV-004 continues to own literal
> continuation invocation and its one-cycle Level 1/2 execution limit. This
> decision changes no Phase 6 criterion or exit status. It implements no shared
> renderer, ViewProvider, exact-geometry expansion, output, persistence, or
> railway calculation. It authorises no Layout Editor feature. It accepts no
> pull request, migration completion, output clearance, package, release, or
> phase exit.
>
> Draft PR #31 remains separate and unaccepted.

## B16 Entry/Exit edit-through-export performance

This bounded Level 2 performance-evidence tranche starts from protected-main
merge
`a5b6a79bf3e73e1673d440077bd65000986bb4c7`. It changes no product source. A
test-owned profiler composes the accepted two-object Entry/Exit editor, the
explicit exact-validation contract, transient FreeCAD wire, and
private-development DXF exporter. It composes these parts as one reconciled
action.

Three fresh isolated FreeCAD 1.1.1/OpenCASCADE 7.8.1 processes applied
the selected Exit edit. Each process validated exact geometry and created the
two-file output. Each then ran one untimed warm-up and three measured unchanged
Validate/Export reuse cycles.

The complete cold journey was 219.127 ms median (112.567–239.585), comprising
103.827 ms edit, 73.026 ms Validate and 41.259 ms created-export medians, with a
per-run uncovered median of 0.768 ms. End-minus-start RSS grew 4.180 MiB median
and the process high-water mark grew 3.918 MiB. Across nine measured reuse
cycles, Validate/Export was 8.972 ms median (8.525–9.997), with zero median
RSS and process-high-water delta. Each cycle still rebuilt and disposed exact
geometry. It did not hide deferred work by skipping validation.

Every run preserved the two compact editable objects and stable mapping. It
also preserved 16 active test-scene nodes and zero `Shape` properties. Every
run created one Undo unit. Validate and Export returned the same
24-vertex/23-edge exact-wire signature. Each run left no transient document or
staging entry. Each produced the same 1,426-byte DXF and 6,829-byte
`unknown`-status manifest.

The raw and sanitised
method, hashes, individual values, failed-proof classifications and limits are
in the
[performance report](../benchmarks/2026-08-02-phase6-transition-pipeline-performance.md).

Retained validation compiled the changed Python. It passed the focused profiler
contract and all 58 standalone validators. The qualified exact-contract,
transient exact-geometry, and DXF-export checks passed. All six
`transition-gui` pipeline steps passed, including the isolated real-GUI
ViewProvider proof. No product visual
behaviour changed, so no screenshot evidence was required.

The measured edit range overlaps the accepted Phase 5 one-set edit range, so
this tranche does not establish an improvement beyond normal noise. The B14
plain-line actions are not equivalent in document, exact-geometry, or output
coverage. They are not used to claim a speed-up. The evidence populates the
Phase 1 explicit Validate, export-from-validated, and complete-journey slots
for this slice.

This improves PR-15/QA-R04 decision readiness without changing
their Partial controls. It accepts no numerical budget, B14 equivalence, output
clearance, product capacity, operator route, legacy retirement or Phase 6
exit. Under D-P6-002, Phase 6 remains 1/5 with Exit 2 alone Evidenced and
owner-accepted. This evidence does not satisfy Exit 4, which remains Pending.

<a id="phase-6-exits-2-and-3-evidence-admission-panel"></a>

## Phase 6 Exits 2 and 3 panel to admit evidence and owner decision

**Decision and exact source state:** This Level 3 panel to admit evidence
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
engineering risk reviewers challenged the panel evidence. Neither reviewer
implemented PR #30 or PR #31.

They independently agreed that Exit 2 was
sufficiently evidenced while Exit 3 was not. The panel review was read-only.
This later alignment changes only control documentation and its fail-closed
validator.

**Evidence reviewed:** The panel reviewed the exact accepted source and tests
from [PR #30](https://github.com/Richard-Gnitnub/tracktemplate/pull/30) and PR
#31. It reviewed their successful protected standalone CI runs and the retained
56/56 local standalone result. It also reviewed the qualified FreeCAD
1.1.1/OpenCASCADE 7.8.1 results. These results covered success, cancellation,
injected failure, cleanup, deterministic reuse, collision, and rollback.

The
panel also reviewed the exact/export architecture, current risks, and
output-status controls. Established qualified FreeCAD proofs were not repeated.
No GUI or operator proof was admitted.

**Exit 2 evidence admitted:** The signed exact adapter creates its sole
`Part::Feature` only in a UUID-named hidden temporary document whose identity
and ownership are checked before cleanup. It returns a signed numeric receipt,
not a `Part.Shape`. Qualified evidence covers success, deterministic repeat,
zero length, and active and inactive document-name collisions. It also covers
ambiguous ownership, nested construction, cancellation,
cancellation-check failure, and injected Part-build failure. Existing
documents, objects, tested properties, filenames, active-document state, and
Undo/Redo history remain unchanged. PR #31 also
proves that export stops when cleanup is incomplete.

**Exit 2 retained limitations:** The acceptance is confined to the assessed B16
Entry/Exit exact-validation and export routes. It does not cover GUI observers,
retained shapes, wider template families, operator workflows or product-wide
behaviour. Host-close failure or post-creation registry interference may leave
a separate temporary document while reporting `cleanup_complete=False` and
producing no output. The qualified-host raw stdout/status file and an
executable final-harness red replay against the pre-repair source were not
retained. These are accepted evidence limitations and do not widen or negate
the literal bounded criterion.

**Exit 3 evidence and finding:** Deterministic DXF/manifest bytes, hashes, and
filenames remain valid bounded evidence. The same applies to byte-identical
reuse, independent DXF parsing, and non-zero qualified FreeCAD import.
Collision refusal, cancellation, staged-failure handling, and caught
in-process rollback also remain valid.

This evidence is insufficient for Exit 3. The files commit through sequential
hard links without crash recovery or durable directory commit. Path operations
are not descriptor-relative. The zero-length `POINT` lacks qualified import
evidence. The qualified command and sentinel are not durably registered.

**Exit 3 required-before-exit conditions:**

| Accountable owner | Deadline | Condition |
| --- | --- | --- |
| Export transaction owner | Before another Exit 3 panel | Provide atomic durable commit or an explicit recoverable transaction protocol for the DXF-and-manifest set. |
| Export path-safety owner | Before another Exit 3 panel | Provide descriptor-relative path control sufficient to address rename and symbolic-link races. |
| Export validation owner | Before another Exit 3 panel | Provide focused interruption, partial-commit and recovery evidence. |
| Qualified FreeCAD validation owner | Before another Exit 3 panel | Import and validate the zero-length DXF `POINT` in the qualified FreeCAD profile. |
| Validation-document owner | Before another Exit 3 panel | Register the qualified command and required success sentinel durably in `reference/VALIDATION.md`. |
| Phase owner and independent reviewers | After the preceding conditions pass | Conduct a fresh Level 3 review to admit evidence before any Exit 3 acceptance. |

**Risk disposition:** PR-09 remains Critical/Remove/Partial. PR-13 remains
Critical/Mitigate/Effective for the current bounded scope. PR-16 remains
High/Mitigate/Partial, and QA-R03 remains High/Remove/Partial. PR-22 remains
Effective for the current bounded scope because independent challenge and owner decision are
separate. No risk treatment or control-effectiveness value changes.

**Panel recommendation:** Exit 2 was **Proceed with bounded conditions** and
sufficient to recommend `Evidenced`. Exit 3 was **Do not proceed** and must
remain Pending. There was no dissent between the independent reviewers.

**Governance-budget exception:** This task transfers one phase-exit authority.
Its Level 3 evidence and decision therefore exceed its zero product-source
lines. The same applies to the dashboard and executable status-control changes.
It changes no frozen history, product behaviour, risk register, or validation
contract.

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
> review to admit evidence recommends acceptance.
>
> No authority is granted for Phase 6 Exit 1, 3, 4, or 5. Production clearance,
> physical-output clearance, `project-cleared` status, and output equivalence
> are not granted. No product-wide export roster, GUI workflow, or operator
> workflow is granted. No persisted or retained exact geometry is granted.
>
> Whole-B14 parity, whole-layout parity, legacy retirement, and performance
> acceptance are not granted. No packaging, release authority, or risk
> downgrade is granted. The export remains private-development with deliberately
> `unknown` project status. PR #33 performance evidence does not satisfy Exit 4.

<a id="b16-entry-exit-durable-dxf-recovery"></a>

## B16 Entry/Exit durable DXF recovery

This bounded Level 2 tranche starts from protected `main` at
`7acdab4f925592d49394960c76f7552e1b47be9d`. It changes only the accepted
Entry/Exit private-development DXF route and its validation. The existing DXF
and manifest names, bytes, schema, collision policy, deliberately `unknown`
project status, and transient exact-geometry contract remain unchanged.

The exporter now locks and binds the validated output directory to one real
descriptor. It performs journal, staging, inspection, hard-link commit,
rollback, and cleanup operations relative to that descriptor. A versioned
internal journal is published and synchronised before the owned staging
directory exists. Staged files and directories are synchronised before commit.

Each final link is synchronised before success. The original implementation
also attempted next-invocation rollback or complete-set reuse from a persisted
journal. The later ownership reviews recorded below showed that a
first-observed journal cannot prove its creation ownership. It also cannot
prove the creation ownership of an output file. The automatic recovery claim
is therefore withdrawn.

The standalone validator passed with
`Phase 6 transition DXF export validation passed`. It terminates a child
process immediately after the first and second final links. At the original
source state, it observed one-file rollback/recreation and complete-pair reuse.
Those observations did not establish creation-bound authority for the
persisted journal. They are not current recovery evidence.

The validator also replaces the requested directory with a symbolic link
during exact validation.
It repeats the replacement after the first link and after transaction cleanup.
The redirected directory receives no file. The bound original directory is
rolled back and cleaned.

Abrupt
termination after the first late-identity rollback unlink retains newly
published journal and staging controls. The corrected proof below requires
every later invocation to preserve and reject that first-observed residue.
Existing deterministic repeat, zero-length, collision, cancellation,
staged-failure and in-process rollback proofs remain green.

The qualified FreeCAD 1.1.1 profile passed with
`Phase 6 transition DXF qualified FreeCAD validation passed`. In addition to
the existing non-zero `LWPOLYLINE`, isolation, cancellation, and injected
rollback checks, FreeCAD imported the zero-length `POINT`. It became one vertex
at the exact bounded coordinate. The import changed no editable document,
active document, or Undo/Redo history. The stable command and sentinel are now owned by
[`VALIDATION.md`](../VALIDATION.md#verified-commands-and-ci).

| Exit 3 required-before-exit condition | Present evidence after this tranche |
| --- | --- |
| Recoverable DXF-and-manifest transaction | **Open technical gap** — durable live-invocation controls and in-process rollback are present. No independently trusted creation authority supports cross-process automatic recovery. |
| Descriptor-relative rename and symbolic-link control | Present — all transaction operations use the bound directory descriptor. Focused replacement proofs fail closed. A Level 3 panel has not admitted this evidence. |
| Interruption, partial-commit and recovery proof | **Open technical gap** — abrupt one-link and two-link termination prove exact residue preservation and fail-closed rejection. They do not prove automatic recovery. |
| Qualified zero-length `POINT` import | Present — qualified FreeCAD imports one exact vertex and restores host state. A Level 3 panel has not admitted this evidence. |
| Durable qualified command and sentinel | Present in `reference/VALIDATION.md`. A Level 3 panel has not admitted this evidence. |
| Fresh Level 3 review to admit evidence | **Open** — required before Exit 3 can be recommended or accepted. |

The interruption harness proves preservation after abrupt process termination.
It does not prove automatic recovery, a physical power cut, or every file-system
failure mode. The descriptor controls and directory synchronisation are
qualified only on the accepted Linux/FreeCAD profile. The advisory lock
serialises cooperating exporter calls. Detected same-user interference causes
a fail-closed result, but the lock does not prevent active racing.

No GUI or operator workflow is claimed. No broader template family or output
equivalence is claimed. No production clearance, physical-output clearance,
`project-cleared` status, or performance improvement is claimed. No legacy
retirement, packaging, release, or Exit 3 acceptance is claimed. Phase 6
therefore remains 1/5 with Exit 3 Pending.

PR-09, PR-13, PR-16, and QA-R03
retain their recorded states. No risk treatment or effectiveness changes.

## B16 Entry/Exit staging-ownership repair

This bounded Level 2 repair starts from protected `main` at
`284695784004320d541cd3fc5def4369e43c7f5c`. The fresh Exit 3 panel to admit
evidence reproduced one implementation defect.

After recovery but
before staging creation, a foreign directory could appear at the deterministic
stage name with the exact expected filenames and bytes. `mkdir` then failed
before the exporter captured identity. Live cleanup treated matching content
as ownership. It deleted the foreign directory while it reported complete
cleanup. The panel therefore recommended **Do not proceed** for Exit 3 at that
source state.

The first repair candidate at
`25360f23fc8393517d8c3ab7145cf7812193dc94` correctly refused a pre-existing
stage. A fresh exact-head review found a remaining `mkdir`-to-first-open
ownership interval. A targeted disposable probe replaced the newly created
directory during that interval with a same-user foreign directory containing
the exact expected filenames and bytes. The candidate deleted the foreign
state and falsely reported `destination_changed=False`,
`cleanup_complete=True` and `recoverable=True`. Content equivalence, owner UID,
permissions and an inode first observed after creation do not establish
creation ownership.

The first independent review of the anonymous-file candidate found the same
principle still violated by cross-process recovery. A pre-existing, valid v2
journal could report the live snapshot of one foreign final file. The next
invocation trusted that first-observed record. It deleted both the foreign file
and journal.

A lone v1 journal was preserved but read before rejection. This
changed its access time. The review therefore returned `BLOCKED` again before
publication.

No independently trusted cross-process root exists for this same-user writable
destination. Thus, it cannot distinguish this journal from one created by an
earlier invocation.

The supported Python/POSIX surface has no operation that atomically creates a
directory and returns its descriptor. Thus, another pathname check cannot
close that interval. The corrected candidate eliminates directory staging. It
creates each output in an anonymous regular staging file with `O_TMPFILE`. It
immediately captures the device/inode identity from the descriptor returned by
that operation. It then writes, synchronises, and validates the same descriptor.

The internal v2 interruption journal records the exact creation-bound
snapshots. That journal is also created anonymously. Before
`linkat(AT_EMPTY_PATH)` commits either output file, the journal is linked from
its still-open descriptor. `.new` remains only a reserved ambiguity detector.
Normal stage cleanup is descriptor close. There is no staging pathname or
directory removal.

At invocation start, descriptor-relative non-reading metadata inspection
detects each existing journal, temporary-journal link, or legacy deterministic
stage pathname. The exporter preserves and rejects that item as unclaimable.
Only controls created and identity-bound during the live invocation may enter
its in-process cleanup.

The retained public-export regression fails against `25360f23...` because the
foreign directory is deleted and the false diagnostic is returned. Against the
corrected candidate, substitution preserves the foreign directory before
atomic staging, during durable journal binding, and immediately before cleanup.
It also preserves every file, identity, metadata value, and byte.

No final
output survives. No file appears in the process working directory. The
diagnostic reports `destination_changed=True`, `cleanup_complete=False`, and
`recoverable=False`. A later invocation again fails closed without altering
the foreign state.

A normal invocation proves both anonymous files have zero links before commit.
It cleans them without a directory-removal call. Existing cancellation,
injected failure, one-link and two-link interruption, and in-process rollback
cases remain passing. Rename, symbolic-link, deterministic-reuse, and collision
cases also remain passing.

The interruption cases prove that one-file,
two-file, and late-rollback residue remains exact with its journal. The next
invocation rejects that residue. The cases do not claim automatic recovery.

Focused foreign-control cases preserve a self-attesting v2 journal, matching
partial DXF, lone v1 journal, and `.new` control. They also preserve access
time. They do not read the content or create working-directory files.

The focused standalone exporter validator passes with
`Phase 6 transition DXF export validation passed`. The final DXF and manifest
names, bytes, public schema, collision policy, qualified-import contract, and
deliberately `unknown` project status remain unchanged. The earlier qualified
FreeCAD import evidence is retained evidence rather than a fresh host run.

This
repair changes internal file-system transaction behaviour, not the imported
DXF contract. File systems or hosts without the required anonymous-file and
descriptor-link primitives fail closed. All pre-existing transaction-control
residue remains preserved for external disposition rather than unsafe
automatic recovery. An independently trusted recoverable transaction protocol
and corresponding interruption/recovery proof therefore remain open Exit 3
technical gaps.

This repair supplies present technical evidence only. It does not accept Exit
3 or satisfy the required fresh post-repair Level 3 panel to admit evidence.
It does not alter another exit or risk state. It grants no GUI, operator,
production, physical-output, `project-cleared`, equivalence,
legacy-retirement, packaging, or release authority. Phase 6 remains 1/5 with
Exit 2 alone Evidenced and owner-accepted. Exit 3 remains Pending.

## IDE workspace-alignment workflow maintenance

This bounded Level 2 governance/tooling tranche starts from protected `main` at
`695627441edcc52ce719fc77902da6f06db66c84` and changes no TrackTemplate
product, railway, FreeCAD or export behaviour. Read-only Git, GitHub,
filesystem and PyCharm metadata showed that the primary project remained on
merged PR #33 while clean accepted `main` was not checked out. Active
uncommitted recovery-authority work existed solely in a `/tmp` worktree. The
project proved that accepted `main` contained PR #33's exact tip and every
unique commit before the primary checkout changed.

The Git-owned reconciliation moved the dirty worktree intact to a named
persistent project location. Its seven-path status and binary patch SHA-256
`dab531699189437c07ffbbb07c281e26098338cf4748adb9e2c3b878db2f0543`
remained exact. The primary PyCharm directory now backs clean `main` at exact
`origin/main`. The configured project virtual environment, VCS root, and run
working directory remain unchanged. The physical PyCharm branch indicator
still requires operator confirmation because it cannot be observed from the
agent sandbox.

The new instruction-only
[`tracktemplate-ide-workspace-alignment`](../../.agents/skills/tracktemplate-ide-workspace-alignment/SKILL.md)
skill separates file-backed IDE comparison from Git authority and operator-only
UI evidence. `$tracktemplate-continue` composes it before Git mutation and
again after protected-main synchronisation. The agent-guidance validator
fails closed on the new metadata, structure, and composition links.
[LFE-016](../LEARNING_FROM_EXPERIENCE.md) records the reusable lesson.

The skill-structure check, tracked Python/FCMacro parsing, focused agent-
guidance and resource-routing checks all passed. Project-progress control,
repository QA, and documentation controls also passed. Governance mutation
validation rejected 95/95 mutations with zero escapes. The complete standalone
CI profile passed 58/58. No FreeCAD or GUI rerun was selected because neither
product nor host behaviour changed.

This maintenance has no Phase 6 exit contribution. Phase 6 remains 1/5. Exit
2 alone remains Evidenced and owner-accepted. Exits 1, 3, 4, and 5 remain
Pending. Risk states, output authority, accepted evidence, and all product
constraints remain unchanged.

<a id="phase-6-exit-3-recovery-authority-contract-panel"></a>

## Phase 6 Exit 3 recovery-authority contract panel and owner decision

This bounded Level 3 correction cycle starts from accepted `main` at
`cee78cff84618c6a5be3be99714682f5822c814f`. Its product outcome is a safe,
reviewable cross-process recovery contract for the private-development B16
Entry/Exit DXF-and-manifest pair. It assesses only the architecture and
authority needed to address Exit 3 conditions 1 and 3. It changes no product
source, admits no implementation evidence, and accepts no Phase 6 exit.

The project owner's 2026-08-02 instructions first authorised selection of the
safest recovery-authority contract and then authorised this correction after
the initial unaccepted draft failed independent review. That draft allowed a
live invocation to verify and then unlink a published pathname. The
filesystem-security and architecture/API reviews rejected the separate
verification-to-unlink interval.

A different actor can substitute even a link
that this process initially created before pathname deletion. POSIX supplies
no expected-inode atomic condition for that deletion. The rejected draft
remains preserved source evidence. It is not decision authority.

The corrected successor was reconstructed on current accepted `main`. It
retains the accepted PR #37 IDE-workspace evidence. Fresh read-only
filesystem-security, architecture/API, governance, and staff-level quality
reviewers assessed the complete successor diff. None implemented the decision.
None holds owner acceptance authority.

**Why this decision outranks maintenance alternatives:** PR #35 and PR #36
already supply bounded descriptor-relative path control and anonymous payload
creation. They also supply no-overwrite publication, durability, and
foreign-state preservation evidence. The remaining technical gap is a safe
cross-process recovery rule,
not another replay of those proofs. Selecting a non-destructive rule removes
the design loop before implementation without adding an operator workflow,
trust service or output representation.

**Present evidence considered:**

| Evidence | Panel disposition |
| --- | --- |
| Accepted `main` exporter | Anonymous `O_TMPFILE` payloads, no-overwrite descriptor-relative links, and directory synchronisation are present. The current verify-then-unlink rollback path is not accepted post-publication recovery authority. Persisted controls are deliberately not trusted for deletion. |
| Application contract | The deterministic two-file result, final names and bytes, manifest schema, and contract IDs are current public constraints. The same applies to the `reuse-identical-or-fail` collision policy and `created` or `reused` receipt dispositions. |
| Repository consumer inventory | Current validators and profilers are the only repository consumers of the concrete export result. No accepted consumer requires exact-partial collision failure. |
| Retained interruption and ownership evidence | One-link and two-link termination evidence is present. Collision, substitution, rollback, and foreign-control preservation evidence is also present. Current source rejects residue instead of recovering it. |
| Rejected initial decision draft | Authenticating a final and then unlinking its pathname has an exploitable substitution interval. Content, UID, permissions, hashes, xattrs, and first-observed identity cannot repair that authority defect. |
| POSIX/Linux primitive contract | Anonymous creation supplies a live creation-bound descriptor. No-overwrite `linkat` can add an absent name. File and directory `fsync` supply the bounded durability order. Pathname deletion has no expected-inode atomic condition. |
| Fresh independent reviews | Strict add-only, journal-free monotonic completion is the narrowest compatible rule. It needs no new receipt or manifest schema. Post-publication pathname rollback is excluded. |

This is present design and implementation evidence, not accepted Exit 3
evidence. D-P6-003 accepts only the recovery-authority contract and later
bounded Level 2 work recorded below. The current source still implements the PR
#36 preserve-and-reject behaviour, including the verify-then-unlink path that
the corrected decision forbids after publication. Automatic recovery is not
present.

**Options and disposition:**

| Option | Disposition |
| --- | --- |
| Preserve all interruption residue and stop | Safe as the current fallback. It cannot satisfy recovery conditions 1 and 3. It is rejected as the final contract. |
| Trust a destination-local journal, owner UID, permissions, hashes, xattrs or first-observed identity | Rejected. The same-UID actor can forge or replace every proposed authority source. |
| Verify an invocation-created link and then unlink its pathname | Rejected. Verification and pathname deletion are separate operations. Substitution therefore defeats the claimed ownership condition. |
| Add an external key, replay ledger, helper service or long-lived broker | Rejected for this slice. It adds credential lifecycle, platform dependencies, and a larger authority surface. |
| Quarantine or recover through an operator decision | Retained only as an optional future disposition. It adds an unauthorised GUI/operator workflow. It is unnecessary for deterministic completion. |
| Publish a generation directory, selector or single bundle | Retained only as a fallback if this protocol is disproved. It changes the output layout or requires protocol-aware consumers. |
| Strict add-only, journal-free monotonic completion | Selected. It recovers only by preserving compatible state and adding an absent exact member. It never deletes published or foreign state. |

**Selected contract:** Strict add-only, journal-free monotonic completion is
defined by all of these mandatory invariants:

1. Every invocation recomputes the exact expected pair from current signed
   inputs. It binds the real destination directory by descriptor. It prepares
   all unpublished payloads in anonymous, creation-bound descriptors.
2. Before publication, abandonment consists only of closing owned anonymous
   descriptors. No pathname cleanup authority is inferred.
3. Publication may only add an absent deterministic final pathname, without
   overwrite, from its synchronised anonymous descriptor.
4. No published final file may be unlinked, renamed, rewritten, truncated,
   replaced or otherwise claimed by TrackTemplate.
5. Pathname-based rollback ends permanently at the first successful final
   link.
6. After any post-publication failure, every published final is preserved,
   including an exact partial or complete output pair.
7. A later invocation may add only an absent exact counterpart. It may not
   reconstruct, replace, or remove the member already present.
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

Historical journals, `.new` links, and stage files are inert foreign residue.
They are never opened, parsed, modified, or deleted. Their presence neither
permits nor prevents final-set completion.

If neither final exists, the
exporter may add both. If exactly one exact regular member exists, it preserves
that member's inode, metadata, and bytes. It adds only the missing exact
counterpart. If both exact regular members exist, it independently revalidates
and reuses the pair. Any other state fails unchanged.

These security statements are absolute within the bounded contract.
Authenticating or verifying a pathname does not create authority to delete it.
POSIX pathname deletion has no expected-inode atomic condition. Rollback ends
permanently at the first publication link. Cross-process recovery means safe
monotonic completion, not destructive cleanup. TrackTemplate never removes
foreign or uncertain destination state.

Diagnostics remain conservative. A successful addition requires
`destination_changed=True`. Uncertainty caused by interference must not be
reported as an unchanged destination.

`cleanup_complete=True` may describe
only a clean pre-publication failure after every invocation-owned unpublished
resource is closed. A surviving published final on a failed invocation requires
`cleanup_complete=False`. It was not rolled back.

`recoverable=True` requires
an independently revalidated exact zero-member, partial or complete destination
with safe retry or remaining add-only authority. Ambiguity, mismatch, uncertain
durability, or an unsupported primitive is not recoverable. Content equivalence
establishes compatibility for reuse or addition only. It never grants
ownership, deletion or replacement authority.

This preserves the final filenames, DXF and manifest bytes, manifest schema,
contract IDs, two-file layout, and deterministic generation. It also preserves
no-overwrite behaviour and the `reuse-identical-or-fail` policy.

It accepts one narrow observable refinement. An exact regular partial pair may
be completed instead of rejected
as a collision. `created` continues to mean that the invocation published at
least one member. `reused` continues to mean that the complete pair already
existed.

The collision policy is therefore defined per final member: reuse an
exact regular member. Create only its absent deterministic counterpart. Fail
on a non-identical or non-regular existing member. No material owner choice
remains. This refinement is inside the owner-delegated contract selection. It
introduces no UI, configuration, dependency, trust root, or output
representation.

**Bounded later Level 2 authority and conditions:**

| Accountable owner | Required work before publication |
| --- | --- |
| Export adapter owner | Implement only the strict add-only, journal-free monotonic state machine in `tracktemplate/adapters/export/transition_dxf.py`. Retain bound-directory, anonymous-file, and no-overwrite controls. Close owned descriptors before publication on failure. Remove every post-publication pathname rollback path. |
| Application-contract owner | Define `reuse-identical-or-fail` per final member in `tracktemplate/application/transition_export.py`. Freeze both export contract/result IDs, the collision-policy value, and receipt dispositions. Stop for a separate API decision if an accepted consumer depends on exact-partial failure. Also stop if truthful implementation needs another public change. |
| Validation owner | Retain focused zero-member, DXF-only, manifest-only, complete-pair, mismatch, symbolic-link, non-regular, cancellation, injected-failure, rename, and substitution cases. Prove pre-publication descriptor abandonment and interruption after each addition. Prove post-addition races and next-invocation monotonic completion. Prove that fresh and partial creation have identical output fingerprints and `created` result signatures. |
| Filesystem-security owner | Prove that pre-existing exact members and inert controls retain inode identity, metadata, and bytes. Prove that equality and pathname verification never authorise deletion. Prove that no failure, race, or later invocation mutates a published final. Prove that diagnostics match exact retained states. |
| Documentation and governance owner | Record the implemented evidence without changing Phase 6 from 1/5. Do not imply that Exit 3 is Evidenced. Retain exact output fingerprints and deliberately `unknown` project status. |
| Independent reviewers | Review the exact Level 2 head for architecture/API, file-system security, and quality. After merge, leave Exit 3 Pending for a fresh bounded Level 3 panel to admit evidence. |

The authorised implementation remains limited to the exporter and narrowly
necessary application-contract wording. It also includes the focused retained
validator, one concise current-evidence entry, and directly dependent
governance controls.

The implementation must stop without publication if it would read or delete
legacy controls. It must also stop before any unlink, rename, rewrite,
truncation, or replacement of a published final. It must not derive deletion
authority from content, metadata, or pathname verification. It must not change
final names, bytes, schema, layout, contract/result IDs, or the collision-policy
value. It must not weaken collision refusal. It must not add an operator
workflow, secret store, helper service, generic storage framework, or runtime
dependency.

**Residual limitations and risk panel:** The pair is recoverable rather than
simultaneously visible through one namespace operation. A partial exact set
may remain until another invocation. There is no background or operator
recovery. Changed expected bytes correctly leave an old partial as a preserved
collision.

Detected active same-UID interference fails closed. The exporter
cannot prevent mutation after its final observation. Historical controls may
remain as inert hidden residue.

Descriptor-link and durability evidence remains
bounded to the qualified Linux/filesystem profile. Additional physical-power-
loss matrices, malformed or orphaned controls, lock contention, unpublished-
journal interruption and bounded residue reads remain optional future
hardening. They are not new mandatory blocking conditions for this bounded
contract.

PR-09 remains Critical/Remove/Partial. PR-13 remains
Critical/Mitigate/Effective within its current bounded scope. PR-16 remains
High/Mitigate/Partial. PR-22 remains High/Remove/Effective within its current
bounded scope. QA-R03 remains High/Remove/Partial.

The contract reduces the design's need for destructive cross-process authority.
It supplies no implementation evidence or risk closure. No risk state,
treatment, or effectiveness changes. Phase 6 remains 1/5 with Exit 2 alone
Evidenced and owner-accepted. Exit 3 and exits 1, 4, and 5 remain Pending.

**Panel recommendation:** **Proceed with bounded conditions.** The fresh
filesystem-security and architecture/API reviewers accept the strict add-only
contract and later bounded Level 2 work. The governance and staff-level quality
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
> recompute the exact expected pair. It may create unpublished payloads only
> in anonymous creation-bound descriptors. It may abandon unpublished work
> only by closing those descriptors.
>
> It may inspect existing finals without
> acquiring mutation authority. It may publish only by adding an absent final
> pathname without overwrite. The first successful final link permanently ends
> rollback. No published final may be unlinked, renamed, rewritten, truncated
> or replaced. Authenticating or verifying a pathname does not grant deletion
> authority. POSIX pathname deletion has no expected-inode atomic condition.
>
> After any post-publication failure, all published finals are
> preserved, including any exact partial or complete output pair. A later
> invocation may add only an absent exact counterpart. Success may be reported
> only after independent revalidation shows that the complete final pair is
> exact. Mismatch, non-regular finals, symbolic links, collision, replay,
> substitution, inconsistency, ambiguity or unsupported primitives fail closed
> without further mutation. Foreign or uncertain destination state is never
> removed.
>
> The `cleanup_complete`, `recoverable`, `destination_changed`, and
> related diagnostics must describe the state actually retained.
> `recoverable=True` is permitted only after independently revalidating an
> exact zero-member, partial or complete destination with safe retry or
> remaining add-only authority. Ambiguity, mismatch, uncertain durability, or
> an unsupported primitive remains non-recoverable. Any successful addition
> requires `destination_changed=True`. Any surviving published final on a
> failed invocation requires `cleanup_complete=False`.
>
> Identical complete-pair
> reuse, deterministic filenames and bytes, manifest schema and contract IDs,
> the two-file layout, no-overwrite behaviour and
> `reuse-identical-or-fail` collision refusal remain unchanged. One exact
> regular partial member may now be completed rather than treated as a
> collision. Phase 6 remains 1/5 and Exit 3 remains Pending until
> implementation, focused interruption/recovery evidence and a fresh Level 3
> review to admit evidence.
>
> No product code is changed by this decision. It does not mark Exit 3 or
> another exit `Evidenced` or owner-accepted. It grants no production,
> physical-output, `project-cleared`, equivalence, GUI, operator, wider-family,
> performance, legacy-retirement, packaging, or release authority. It changes
> no risk state.
>
> It does not authorise post-publication unlink, rename,
> rewrite, truncation, replacement, or pathname-based rollback. It does not
> authorise reading or deleting pre-existing controls. It does not authorise
> mutation of foreign or uncertain destination state. It does not authorise
> deletion authority from equality, metadata, or pathname verification. It
> does not authorise output name, byte, schema, layout, contract/result ID, or
> collision-policy value changes. It adds no trust service, generic storage
> framework, or runtime dependency.

## B16 Entry/Exit add-only DXF monotonic recovery

This bounded Level 2 tranche starts from accepted `main` at
`ccacb5ca638b1e3a79fb59107a97d90e9434f0d5` and implements only the
D-P6-003 recovery contract for the private-development B16 Entry/Exit
DXF-and-manifest pair. Before the source change, the retained focused
regression failed because an exact regular partial pair raised
`transition-dxf-export-collision` instead of adding its absent counterpart.

The exporter now recomputes and validates the exact pair. It binds the
destination directory by descriptor. It stages only absent payloads in
anonymous creation-bound descriptors. It publishes through no-overwrite
`linkat`.

Existing exact regular members are inspected without mutation authority and
retain inode identity, metadata and bytes. Historical journals, `.new` files
and stage directories are inert. The exporter neither reads nor changes them.
Their presence does not prevent completion. The source contains no
post-publication rollback, journal cleanup or final-path unlink route.

The retained standalone validator passed with its required
`Phase 6 transition DXF export validation passed` sentinel. It covers fresh,
DXF-only, manifest-only, and complete states. It covers exact partial completion
with the same `created` result signature as fresh creation. It includes
interruption after each addition and next-invocation completion. Completion
occurs only after the required directory synchronisation.

The validator covers fail-closed complete-pair preservation when
synchronisation fails. It includes cancellation and injected failure after one
addition. It also covers uncertain durability, unsupported primitives,
resolve-to-bind removal, and substitution. Post-lock, initial-member, and
post-addition substitution are included. Directory rename, symbolic-link
races, and active-lock ambiguity are included.

Non-regular and byte-collision
refusal are included. The same applies to inert foreign controls and observed
descriptor closure during pre-publication abandonment.

A sentinel proves that normal publication makes no unlink, rename, replace, or
rmdir call. The validator freezes the accepted-main output hashes:

| Fixture | DXF SHA-256 | Manifest SHA-256 |
| --- | --- | --- |
| 300 mm transition | `6861d0565a737615ec5b242aaa8d2b3efd51b0e22aad9d93fb929489a25fd861` | `16de67625d952e9bb0c7c3f7891b30987f78d7c5878a9838999ab0909f131552` |
| zero-length transition | `7b2757bc3559013a2399df7efe6c25721288f8dad56b6cc05d93c2938c86c2b1` | `8cff21c710de1da266d0a0c590cd90dc4edf46c37403275c146e2ffe5a9b3e9f` |

The qualified FreeCAD 1.1.1 profile also passed with
`Phase 6 transition DXF qualified FreeCAD validation passed`. It retained
editable-document and active-document isolation. It imported both the
`LWPOLYLINE` and zero-length `POINT`. It preserved an exact partial after an
injected second-addition failure. The next invocation completed that partial.

This is present Level 2 implementation and focused recovery evidence. It is
not a decision to admit Exit 3 evidence or give owner acceptance. Conditions 1
and 3 now have bounded evidence. Descriptor-relative path control remains
retained evidence for condition 2. Qualified `POINT` import and durable command
registration remain retained evidence for conditions 4 and 5. Condition 6
remains open.

A fresh Level 3 panel must distinguish criterion requirements,
accepted bounded limitations, and optional hardening before an Exit 3
recommendation.

The pair remains sequentially visible rather than namespace-atomic. An exact
partial may remain until a later invocation. There is no background or operator
recovery. Changed expected bytes leave old partial output as a preserved
collision. Evidence is limited to the qualified Linux/file-system profile
and the accepted Entry/Exit slice.

Phase 6 remains 1/5 with only Exit 2
Evidenced and owner-accepted. Exit 3 remains Pending. PR-09, PR-13, PR-16,
PR-22, and QA-R03 retain their existing states. No production, physical-output,
`project-cleared`, GUI, release, packaging, or legacy-retirement authority
changes.

## B16 Entry/Exit surviving-host interruption cleanup

This bounded Level 2 repair starts from protected `main` at
`49d9a85ee3f942a801c65f1cd051a2586ffa10d8`. A fresh probe for Exit 3 evidence
showed that a cancellation callback raising `KeyboardInterrupt` after both
anonymous payloads were staged bypassed the `Exception`-only cleanup path and
left both descriptors open in a surviving host. The retained focused
regression failed against that source with `anonymous staging descriptor
remained open`, classified `implementation-defect` under D-P6-003 invariant 2.
A first independent security review then returned `BLOCKED` for retention.

Injected descriptor close failure replaced the direct interruption. A direct
interruption after `linkat` but before directory `fsync` could be reported
recoverable. The added close-failure regression received
`TransitionDxfExportError` instead of the original `CleanupInterruption`.
Both findings were classified in the same implementation area.

A second independent security review confirmed those paths but returned
`BLOCKED` for retention. A first direct interruption during normal-success
descriptor cleanup stopped the remaining closes. A bound-directory close error
could replace an interruption that was already propagating. Its disposable
probe observed both anonymous descriptors still open. The retained regression
reproduced `[True, True]` against that second reviewed state. These findings
were again classified under the same resource-ownership condition.

The exporter now catches `BaseException` only during its anonymous-resource and
bound-operation ownership operations. Each descriptor enters the outer ownership
map immediately after open. Cleanup attempts every observed invocation-owned
anonymous descriptor even when one close raises a direct `BaseException`. It
preserves the original `KeyboardInterrupt`, `SystemExit`, or custom direct
`BaseException` type and value. The completion and bound-directory cleanup
routers also preserve an active direct interruption.

A failed or uncertain close is reported as cleanup-incomplete and
non-recoverable. The existing chained `TransitionDxfExportError` contains this
report. Publication is marked durability-uncertain before `linkat`. It keeps
that status until the directory `fsync` returns. An interruption in that
interval is also non-recoverable.

Before publication, successful cleanup gives an unchanged, clean, and
recoverable diagnostic. After a durable addition, the diagnostic is changed,
not clean, and recoverable. The exact final remains untouched. A later
invocation adds only its missing counterpart. No exception class, public ID,
receipt, filename, output byte, schema, or collision policy changes.

The focused standalone validator passed with `Phase 6 transition DXF export
validation passed`. It covers interruption inside staging, between staged
payloads, and before publication. It covers interruption after one durable
addition and through injected descriptor-close failure. It also covers normal-
success close iteration, bound-directory close failure, and the
post-link/pre-sync interval.

The qualified FreeCAD 1.1.1 validator passed with
`Phase 6 transition DXF qualified FreeCAD validation passed`. The same
`KeyboardInterrupt` propagated after descriptor cleanup. The editable host
state remained exact, and a later export succeeded. Process-kill, `os._exit`,
and a second interruption
during cleanup remain outside this surviving-host proof.

This is repair
evidence only. Exit 3 remains Pending for a fresh Level 3 panel. Phase 6
remains 1/5, and no risk or output authority changes.

## B16 Entry/Exit systemic descriptor-and-lock ownership repair

This bounded Level 2 repair starts from protected `main` at
`d43ba79593f0b03cf7afa1155412d95818c7307c`. Retained pre-fix proof found a
directory descriptor still open after a direct interruption during its first
`fstat`, and an existing-final inspection descriptor still open with no
structured cause after interruption of its close. Both failures were
classified `implementation-defect` under the private transition-DXF
resource-ownership condition.

Every exporter-owned descriptor close now passes through one private
non-throwing close primitive. The acquiring operation closes output-directory
and existing-final descriptors until their ownership transfer or return. The
bound operation continues to own registered anonymous staging descriptors and
the returned locked directory descriptor.

Direct `KeyboardInterrupt`, `SystemExit`, and custom `BaseException` instances
remain the top-level object. Cleanup failure is bounded chained context. All
remaining owned closes are attempted. Every `__cause__` and `__context__` edge
has no repeated exception identity. The close-error detail remains
inspectable.

Before publication,
successful cleanup releases the lock and creates no final. A fresh invocation
may safely retry, while the interrupted invocation remains conservatively
changed/non-recoverable until exact destination state is independently
revalidated. After the first link, exact finals remain untouched and link-to-
directory-sync interruption remains durability-uncertain and non-recoverable.
A close whose outcome is itself interrupted is reported cleanup-incomplete
rather than claimed closed.

The focused standalone exporter validator passed with
`Phase 6 transition DXF export validation passed`. The qualified FreeCAD 1.1.1
exporter/import validator passed with
`Phase 6 transition DXF qualified FreeCAD validation passed`. The complete
standalone profile, project-progress control, governance mutation control, and
diff check also passed.

The regression matrix covers directory open, lock, and identity acquisition.
It covers existing-final inspection and close. It covers existing-final and
anonymous close failure during a direct interruption. It also covers anonymous
staging acquisition, normal and failed cleanup, and post-link/pre-sync
interruption. Exact-state preservation, safe or refused recovery diagnostics,
and deterministic retry are included.

Existing filenames, bytes, hashes, manifest schema, public identifiers,
receipt dispositions, and add-only/no-overwrite collision authority remain
unchanged.

This is surviving-host implementation evidence. It is not an owner decision to
admit Exit 3 evidence or give acceptance. Process kill, `os._exit`, and a
second interruption during cleanup remain outside the proof. Wider host or
file-system durability also remains outside the proof. The same applies to
GUI/operator recovery and production clearance.

Phase 6 remains 1/5. Exit 3
remains Pending, and no risk state or authority changes.

<a id="phase-6-exporter-fault-model-clarification-panel"></a>

## Phase 6 exporter fault-model clarification panel and owner decision

**Decision and exact source state:** This Level 3 governance cycle starts from
protected `main` at
`d8e2b640da412ec0aff0300cd7344e78cec0048b`. It defines the supported failure
model against which the existing private-development B16 Entry/Exit exporter
implementation and retained evidence may later be judged. It changes no
product source and does not admit or accept Exit 3 evidence. Phase 6 remains
1/5 and Exit 3 remains Pending. The next decision is a fresh Level 3 Exit 3
panel to admit evidence against the supported model.

**Participants, roles and independence:** Richard is project owner, panel chair
and accepting authority. Codex is the governance change owner and presents the
repository evidence. Retention requires exactly two fresh read-only reviewers
against one frozen candidate. One owns the architecture/API/governance/
documentation challenge. One owns the security/recovery/evidence-limit
challenge. Neither reviewer may edit the candidate or exercise owner
acceptance authority.

Any correction requires affected validation and both
reviews again.

**Evidence and contradiction check:** The panel reviewed D-P6-003 and its
strict add-only implementation evidence, the later surviving-host descriptor
and advisory-lock repairs. It reviewed the exact current Exit 3 disposition,
the export architecture and validation contract, and the recovery policy. It
also reviewed PR-09, PR-13, PR-16, PR-22, and QA-R03. Earlier independent
findings exposed material
descriptor, lock, recoverability, and diagnostic defects. They produced
retained systemic repairs.

Later probes increasingly targeted interruption at
arbitrary instructions during unobservable Python ownership-transfer
micro-windows. They did not demonstrate deletion, overwrite, corruption, or
unsafe mutation of a published final. No ordinary exception or explicit
cancellation point is excluded only to obtain Exit 3. No retained tested
interruption condition or accepted recovery path is excluded for that purpose.

**Options and disposition:** Continuing without a finite model leaves an
open-ended instruction-level review loop and cannot support a decidable safety
claim. The selected clarification defines one canonical supported model with
process-local cleanup and restart containment. It also keeps retained invariant
violations that prevent acceptance. This is the smallest compatible
clarification.

An isolated short-lived helper process is the future option if cleanup across
interruptions at every arbitrary instruction is later required. It is not
authorised or implemented here.

**Accepted ownership split:**

- [Supported exporter failure model](../ARCHITECTURE.md#supported-exporter-failure-model)
  owns supported and deliberately unsupported failures, mandatory invariants,
  restart containment and the non-authorised helper-process option.
- [Supported exporter interruption evidence](../VALIDATION.md#supported-exporter-interruption-evidence)
  owns mandatory retained evidence and the limit for exploratory probes.
- [Recovery after an abnormally interrupted export](../RECOVERY_AND_BACKUP.md#recovery-after-an-abnormally-interrupted-export)
  owns the close, restart, reopen, inspect and normal retry procedure.
- D-P6-003 remains authoritative for strict add-only, no-overwrite monotonic
  completion. The skills route to these owners and do not duplicate them.

**Safety/risk panel:** The outcome is **Proceed with bounded conditions**.
Deterministic files and identifiers remain mandatory. Descriptor-relative
access, add-only publication, and no-overwrite publication also remain
mandatory. Exact-only reuse/completion and fail-closed rejection remain
mandatory. Published-file preservation and conservative diagnostics remain
mandatory.

The qualified platform restriction and private-development
`unknown` output status remain mandatory. Restart containment grants no
deletion or replacement authority.

PR-09 remains Critical/Remove/Partial. PR-13 remains
Critical/Mitigate/Effective within its current bounded scope. PR-16 remains
High/Mitigate/Partial. PR-22 remains High/Remove/Effective within its current
bounded scope. QA-R03 remains High/Remove/Partial. No risk state, treatment,
effectiveness, or disposition changes.

**Governance-budget exception and retention conditions:** This task changes
architecture, validation, recovery, and review authority. Its governance record
therefore exceeds its zero product-source lines. Retention requires passing
final semantic controls, the complete standalone profile, and exact-head
protected CI. The two specified frozen-state reviews must also pass with no
blocking finding. Those controls do not themselves accept Exit 3.

Under the authority explicitly supplied by the project owner's 2026-08-15
instruction, the resulting decision is:

> **D-P6-004 — Define the supported exporter failure model and evidence
> boundary**
>
> At protected-main baseline
> `d8e2b640da412ec0aff0300cd7344e78cec0048b`, accept the canonical supported
> exporter failure model, corresponding interruption-evidence limit, and
> abnormal-interruption operator recovery procedure. The supported model
> includes ordinary Python exceptions and explicit application cancellation.
> It includes retained expressly tested `BaseException` conditions. Accepted
> staging, publication, cleanup, and durability failures are included.
>
> The
> same applies to D-P6-003 exact-partial and exact-complete next-invocation
> recovery. Process termination at the operating-system descriptor/advisory-
> lock limit is included. Qualified FreeCAD import and host execution within
> the documented platform/file-system profile are included.
>
> `BaseException` injection between every possible pair of bytecode
> instructions is deliberately unsupported. The same applies at every
> unobservable acquisition or ownership-transfer micro-window. Repeated
> injection during cleanup is also deliberately unsupported. Such a probe is
> not automatically a defect or a condition that prevents Exit 3. It prevents
> Exit 3 when it proves a retained mandatory-invariant violation. A supported-
> workflow or accepted-recovery-condition violation also prevents Exit 3.
>
> D-P6-003 remains authoritative. Deterministic names, bytes, hashes, schemas,
> identifiers, and receipt dispositions remain mandatory. Descriptor-relative
> access, add-only publication, and no-overwrite publication remain mandatory.
> Exact-only reuse and monotonic completion remain mandatory. Strict fail-
> closed rejection and preservation of every existing or published final
> remain mandatory. The prohibition on unlink, rename, rewrite, truncation, or
> replacement remains mandatory.
>
> Conservative diagnostics, the qualified
> platform restriction, and private-development `unknown` output status remain
> mandatory. Independent evidence and explicit owner acceptance also remain
> mandatory.
>
> When resource release is uncertain after an abnormal interruption, preserve
> output and close FreeCAD completely. Restart and reopen FreeCAD. Inspect
> normally and retry through the normal exporter. Restart restores the process
> isolation. It does not prove destination correctness or authorise destructive
> recovery.
>
> If absolute cleanup across arbitrary instruction-level interruption is later
> required, assess an isolated short-lived export helper process through a
> separate architecture, security, API, and Level 3 decision. This decision
> implements no helper process, subprocess exporter, service, external
> transaction manager, dependency, storage framework, or exporter redesign. It
> changes no product source, public or stored API, schema, manifest, output
> byte, fixture, or railway behaviour. It grants no production, physical-
> output, `project-cleared`, equivalence, GUI, or wider-family authority. It
> grants no persistence, exact-geometry, performance, legacy-retirement,
> packaging, release, or tagging authority. It changes no risk disposition.
>
> Phase 6 remains 1/5, and Exit 3
> remains Pending. The next decision is a fresh Level 3 Exit 3 evidence-
> review panel against this supported model.

<a id="phase-6-exit-3-supported-model-evidence-admission-panel"></a>

## Phase 6 Exit 3 supported-model panel to admit evidence and owner decision

**Decision and exact source state:** This Level 3 decision to admit evidence
applies to protected `main` at
`7198b05b6a4b7e4654b7d02d0bad4e5cf627a799`. Local `main`, `origin/main` and
live protected GitHub `main` were equal and the working tree was clean before
the panel. PR #42, D-P6-004 and its completed preservation audit remain
accepted governance state. The later preservation-manifest discrepancy is
retained as reconciled evidence.

The original 1,150-line manifest preceded an
intentional directly dependent validator addendum. The retained 1,160-line
manifest has the later hash. The sixteenth path was authorised. The merge tree
equals the reviewed head tree. All other tracked blobs were unchanged.

**Criterion, participants and independence:** The panel assessed Phase 6 Exit
3, “Export is deterministic and failure-safe”, against D-P6-003 and D-P6-004.
Richard is project owner, panel chair and accepting authority. Codex presented
the retained evidence. Two fresh read-only reviewers independently covered
architecture/API/governance and file-system security/recovery/failure safety.
Neither implemented the exporter or exercised owner authority.

Both returned
**PROCEED TO OWNER ACCEPTANCE WITH BOUNDED CONDITIONS**. There was no dissent.

**Admitted evidence:** The retained exact implementation and evidence prove
deterministic filenames, DXF/manifest bytes, hashes, schema, and identifiers.
They prove descriptor-relative destination access, locking, anonymous staging,
add-only publication, and no-overwrite publication. They prove exact-complete
reuse and exact-partial monotonic completion. They also prove strict fail-
closed handling of mismatched, symbolic-link, non-regular, substituted,
replayed, inconsistent, or ambiguous state. Every existing or published final
is preserved.

The supported matrix covers ordinary exceptions and explicit cancellation. It
covers retained tested `BaseException` conditions. It covers staging,
publication, cleanup, and durability failures. Process termination, next-
invocation recovery, and qualified FreeCAD import/host execution are included.
Retained protected CI and exact-source comparisons support the assessed state.
This panel did not generate arbitrary new fault injection.

**Conditions and assurance limitations:** Acceptance is confined to the
private-development B16 Entry/Exit two-file DXF-and-manifest route and the
qualified Linux x86_64 FreeCAD 1.1.1 profile. The file systems must provide the
tested `O_TMPFILE`, descriptor-relative `linkat`, advisory-lock, and
file/directory `fsync` primitives. Unsupported primitives fail closed.
Publication is sequentially visible rather than namespace-atomic. An exact
partial may remain.

Only a later independently validating normal invocation
may complete it. Advisory locking coordinates cooperating exporters.

Physical-power-loss durability and wider hosts or file systems are not
admitted. Background recovery is not admitted. Continuously active same-UID
external mutation after final observation is not admitted. When surviving-host
descriptor or lock release is uncertain, operators must preserve output and
close FreeCAD completely.

They must restart and reopen FreeCAD, inspect
normally, and retry through the normal exporter.
Restart grants no same-host, destructive or manual recovery authority. A
separate raw stdout file for the final qualified-host run was not located. The
exact command, environment, sentinel, and successful result remain durably
recorded. Both reviewers therefore classified this as an auditability
limitation instead of a supported-model evidence gap.

**Unsupported conditions and retained invariants:** Injection between every
bytecode instruction remains deliberately unsupported. The same applies during
every unobservable acquisition or ownership-transfer micro-window. Repeated
interruption of cleanup also remains deliberately unsupported.

Their absence is not an evidence gap. A probe becomes a blocking finding when
it proves deletion, overwrite, unsafe mutation, or unsafe retry. Another
retained-invariant or supported-workflow violation has the same effect.
D-P6-003 remains authoritative. No existing or published final may be unlinked,
renamed, rewritten, truncated, or replaced. Restart containment never
authorises such mutation.

**Safety/risk panel and retention:** No supported-model defect, unsafe recovery
path, material evidence gap, or contradiction with D-P6-003/D-P6-004 was found.
PR-09 remains Critical/Remove/Partial. PR-13 remains
Critical/Mitigate/Effective within its current bounded scope. PR-16 remains
High/Mitigate/Partial. PR-22 remains High/Remove/Effective within its current
bounded scope. QA-R03 remains High/Remove/Partial.

No risk state, treatment,
effectiveness, or disposition changes.

This decision changes governance status only. No product source, test oracle,
schema, manifest, output byte, identifier, or railway behaviour changes.
Retention requires proportionate governance validation and fresh independent
acceptance review. It also requires exact-head protected CI and preservation-
audited protected-main integration.

Under the project owner's explicit 2026-08-15 authority, the resulting
decision is:

> **D-P6-005 — Accept Phase 6 Exit 3 for the bounded B16 Entry/Exit exporter**
>
> At protected `main` `7198b05b6a4b7e4654b7d02d0bad4e5cf627a799`, I
> accept Phase 6 Exit 3, “Export is deterministic and failure-safe”, as
> Evidenced and owner-accepted only for the bounded B16 Entry/Exit
> private-development DXF-and-dependency-manifest route under D-P6-003 and
> D-P6-004. Phase 6 advances from 1/5 to 2/5.
>
> This acceptance covers deterministic names, bytes, hashes, schema, and
> identifiers. It covers descriptor-relative add-only/no-overwrite publication.
> It covers exact-complete reuse and exact-partial monotonic completion. It
> covers supported exception, cancellation, and retained interruption evidence.
> It also covers staging, publication, cleanup, durability, and process-
> termination evidence. Qualified FreeCAD import and host execution are
> included.
>
> Truthful conservative diagnostics are included. Restart-based
> containment with independent destination revalidation is also included.
>
> It does not extend assurance to interruption at every arbitrary instruction.
> It does not extend assurance to repeated interruption of cleanup, physical
> power loss, or unqualified hosts or file systems. Continuously active external
> mutation after final observation is not included. Destructive or manual
> recovery is not included.
>
> Existing and
> published finals must never be deleted, renamed, rewritten, truncated,
> replaced or manually altered to recover.
>
> Output remains private-development with project status `unknown`. No
> authority is granted for Exit 1, 4, or 5. No production or physical-output
> clearance is granted. No `project-cleared` status or output equivalence is
> granted. No GUI/operator or wider-family authority is granted. No persisted
> schema or retained exact geometry is granted. No performance acceptance,
> legacy retirement, packaging, or release authority is granted. No risk
> downgrade or later-phase authority is granted.

<a id="tt-doc-001-documentation-architecture-panel"></a>

## TT-DOC-001 documentation-architecture panel and owner decision

This Level 3 documentation-governance panel records the owner-authorized
TT-DOC-001 decision. The protected `main` baseline is
`f03818d71bce06c5cfb85da84d8f3f230e08b47c`.

The decision changes documentation architecture and presentation only. Phase 6
stays at 2/5. Exits 1, 4, and 5 stay Pending. No risk disposition or product
authority changes.

**Authority and evidence reviewed:**

| Question | Evidence and conclusion |
| --- | --- |
| Canonical owner | `reference/ENGINEERING_POLICY.md` owns the documentation lifecycle and completion reports. It is the correct owner for TT-DOC-001. |
| Information hierarchy | The order is owner view → canonical information → proof/provenance. The owner view gives no project authority. |
| Normative standard | The normative standard is official ASD-STE100 Simplified Technical English, Issue 9, dated 2025-01-15. It applies to canonical technical prose in English in the defined bounded scope. |
| Terminology owner | `reference/TERMINOLOGY.md` is the one project terminology owner. It records only necessary technical nouns and technical verbs for TrackTemplate. |
| Controlled status | Pending, Evidenced, Accepted, Blocked, Finding, Limitation, Unknown, and Decision required keep different meanings. Persisted and machine identifiers do not change. |
| Live documentation | `PROJECT_PLAN.md` is the current status dashboard. The change corrects stale Exit 3 text in `CAPABILITY_MATRIX.md`. Its `Partial` class does not change. |
| Skill ownership | The panel examined all 28 skills. Seven workflows own the applicable work. No new skill or competing primary responsibility is necessary. |
| S1000D limit | TrackTemplate uses applicable modular-information principles. It claims no S1000D conformance and authorizes no S1000D infrastructure. |
| Preservation baseline | The protected-main tree is `8c3ac7f340a676684b3bfec9d9aed9a3c3a708a1`. Frozen history, prior decisions, prior LFE rows, live risks, product source, schemas, APIs, and output contracts stay outside this change. |

**Architecture alternatives:**

| Option | Panel assessment |
| --- | --- |
| Keep distributed guidance without a profile | Rejected. The project does not record the human interface or controlled meanings. |
| Add the profile to `reference/ENGINEERING_POLICY.md` | Selected. It keeps the primary owner. Workflows refer to the policy. |
| Add `reference/DOCUMENTATION_PROFILE.md` or a similar skill | Rejected. This option divides a responsibility and increases competing-authority risk. |

**Bounded Issue 9 review of current live documentation:** The review used the
[official Issue 9 standard](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf).
The review included the current owner dashboard, current evidence and
registers, and the canonical policy documents. It also included agent workflow
and skill prose.

The review found these problems in live prose:

- Some descriptive sentences have more than 25 words.
- Some procedural sentences have more than 20 words or more than one
  instruction.
- Some prose uses semicolons, British spelling, long multi-word nouns, or
  unapproved word forms.
- Some prose uses passive voice when the agent is known.
- Some evidence records contain facts, limitations, recommendations, and
  decisions in dense logical units.

These findings identify the prose for bounded migration. They do not change
technical meaning or project authority. They do not cause a style change in
frozen history. Full Issue 9 conformance of the live corpus is not
verified.

**Issue 9 conformance assessment for this candidate:** The TT-DOC-001
documentation review used the official Issue 9 standard. The review examined
each full logical unit in this table.

| Path | Full logical unit |
| --- | --- |
| `AGENTS.md` | The completion-report requirement. |
| `reference/ENGINEERING_POLICY.md` | The TT-DOC-001 profile and the first paragraph of the completion-report section. |
| `reference/PROJECT_PLAN.md` | The preamble, current owner view, TT-DOC-001 decision row, and authority links. |
| `reference/CAPABILITY_MATRIX.md` | The first evidence limit and the DXF row. |
| `reference/TERMINOLOGY.md` | The ASD-STE100 project terminology section. |
| `reference/current/PHASE_EVIDENCE.md` | This TT-DOC-001 panel and the current-register paragraph. |
| `reference/current/gate-decisions.json` | The human-readable TT-DOC-001 record. Exact JSON data stays outside the linguistic assessment. |
| `reference/LEARNING_FROM_EXPERIENCE.md` | LFE-018 only. |
| `reference/AGENT_WORKFLOWS.md` | The TT-DOC-001 workflow-integration section. |
| `.agents/skills/tracktemplate-change-validation/SKILL.md` | The added profile preparation, Issue 9 validation rules, and full output section. |
| `.agents/skills/tracktemplate-context-recovery/SKILL.md` | The added owner-view guidance and recovery-report introduction. |
| `.agents/skills/tracktemplate-continue/SKILL.md` | The full Owner acceptance pack section. |
| `.agents/skills/tracktemplate-documentation-alignment/SKILL.md` | The added profile preparation and the full report section. |
| `.agents/skills/tracktemplate-documentation-review/SKILL.md` | The full preparation, editing-rules, and output sections. |
| `.agents/skills/tracktemplate-documentation-review/references/document-ownership.md` | The two changed ownership rows. |
| `.agents/skills/tracktemplate-documentation-review/references/writing-checklist.md` | The introduction and the full Ownership, Accuracy, and Concision sections. |
| `.agents/skills/tracktemplate-quality-review/SKILL.md` | The full preparation and output sections. |
| `.agents/skills/tracktemplate-technical-lead/SKILL.md` | The added profile guidance in preparation and final handoff. |

The internal result for these logical units is `ASD-STE100 Issue 9
conforming`. The review used the project terms in the
[terminology register](../TERMINOLOGY.md#asd-ste100-project-terminology).
These terms include the documentation, governance, assurance, product, Git,
export, railway, and standards terms that occur in the units.

This result is a TrackTemplate conformance assessment. It is not external ASD
certification, endorsement, or an official conformance assessment. It excludes
exact machine data and externally controlled information. It excludes unchanged
live prose outside the named logical units. It also excludes frozen history.

**Review state:** Two reviewers independently reviewed the exact candidate.
The architecture and Issue 9 review result was PASS WITH FINDINGS. The quality
review result was PASS WITH FINDINGS. No reviewer found a blocking condition.
The finding is that Issue 9 conformance is Unknown for unchanged live prose.

The reviewers did not change the candidate. The same reviewers also examined
previous candidate states.

**Risk panel:**

| Risk | Panel judgment | Result |
| --- | --- | --- |
| PR-12 — direction or task-selection drift | One canonical profile and canonical links prevent competing documents. | Medium / Mitigate / Partial. The disposition does not change. |
| PR-22 — authority transfer without challenge | An explicit owner decision is necessary. A different reviewer must challenge the evidence independently. | High / Remove / Effective for the current bounded scope. The disposition does not change. |
| PR-13 — repository or evidence loss | Exact-state publication and post-merge preservation controls are necessary. | Critical / Mitigate / Effective for the current bounded scope. The disposition does not change. |

**Panel recommendation:** **Proceed with bounded conditions.** Keep
`ENGINEERING_POLICY.md` as the sole owner of the canonical profile. Add no new
profile document or skill. Keep `TERMINOLOGY.md` as the sole project
terminology owner. Adopt Issue 9 as the normative standard for the defined
bounded scope. Keep phase, risk, and product state. Add only LFE-018.

Do semantic validation. Get fresh architecture and quality reviews. Reviewers
must do this work independently.

> **TT-DOC-001 — TrackTemplate Technical Documentation Profile**
>
> At protected `main` `f03818d71bce06c5cfb85da84d8f3f230e08b47c`, I
> accept human comprehensibility as a governance control.
>
> `reference/ENGINEERING_POLICY.md` is the sole canonical owner of the
> TrackTemplate Technical Documentation Profile. The information order is
> owner view → canonical information → proof/provenance. The owner view gives
> no project authority. Detailed technical provenance stays available below
> the canonical information.
>
> TrackTemplate adopts ASD-STE100 Simplified Technical English, Issue 9, dated
> 2025-01-15. It is the normative standard for canonical technical prose in
> English in the defined bounded scope. The official standard is the normative external
> reference.
> Issue 9 language requirements have priority over the UK-English convention
> in this bounded scope.
>
> All new prose in this bounded scope must obey the applicable ASD-STE100 Issue 9
> requirements. For a material edit, the full logical unit that contains the
> change must obey these requirements. A reviewer must use the official
> standard for the linguistic review. Automatic validators do not show
> linguistic conformance.
>
> `reference/TERMINOLOGY.md` is the one project terminology owner. It owns
> the necessary technical nouns and technical verbs for TrackTemplate. It does not
> copy the controlled general dictionary. Exact machine data and externally
> controlled information stay unchanged when necessary.
>
> TrackTemplate must migrate live documentation in bounded cycles. Full Issue 9
> conformance of the live corpus is not verified. Issue 9 style does
> not authorize a change to frozen history.
>
> The workflows apply the profile by reference. This decision adds no
> skill. It gives no skill new owner, acceptance, merge, phase, production, or
> release authority.
>
> TrackTemplate uses applicable ASD S1000D information-management principles.
> It claims no S1000D conformance and authorizes no S1000D infrastructure.
> TrackTemplate also claims no external ASD certification, endorsement, or
> official conformance assessment.
>
> This decision changes no phase or exit status. It changes no risk
> disposition, product source, or product behaviour. It changes no FreeCAD,
> Coin, exporter, persistence, schema, API, or output behaviour.
>
> This decision gives no production, physical-output, `project-cleared`,
> packaging, release, or tagging authority.
>
> Phase 6 stays at 2/5. Exits 1, 4, and 5 stay Pending. Output stays
> private-development. Project status stays `unknown`.

<a id="tt-doc-002-uk-english-spelling-correction-panel"></a>

## TT-DOC-002 UK English spelling-directive correction panel and owner decision

This Level 3 panel records a spelling-only correction to TT-DOC-001. The
protected `main` baseline is
`54d5d8312429ededff83084a3bc39c8756729d19`.

Phase 6 stays at 2/5. Exits 1, 4, and 5 stay Pending. Output stays
private-development. Project status stays `unknown`. This decision changes no
risk disposition, evidence acceptance, product authority, or release authority.

**Authority and evidence reviewed:**

| Question | Evidence and conclusion |
| --- | --- |
| Normative standard | Official ASD-STE100 Simplified Technical English, Issue 9, dated 2025-01-15, stays the normative standard for the defined canonical prose. |
| Spelling option | Issue 9 Rule 1.14 permits a different spelling when an official directive applies. The project owner gives the UK English spelling directive. |
| Canonical owner | `reference/ENGINEERING_POLICY.md` stays the one canonical owner of TT-DOC-001. The correction changes the spelling rule in that profile. |
| Terminology owner | `reference/TERMINOLOGY.md` stays the one project owner of technical nouns and technical verbs. The correction does not add spelling entries to that register. |
| Assurance limit | The directive changes spelling only. It does not change vocabulary, grammar, approved meaning, part-of-speech, technical-term, or linguistic-review requirements. |
| Historical record | The accepted TT-DOC-001 quotation and LFE-018 do not change. TT-DOC-002 changes only the previous spelling rule. |
| Project state | Phase, exits, risks, evidence acceptance, product, output, and release state stay unchanged. |

The original TT-DOC-001 panel records the review and owner wording that applied
before this correction. The panel keeps the UK-spelling finding from the
previous review. UK English spelling alone does not fail the current spelling
rule. American English spelling is not necessary after this correction.

**Issue 9 review for the correction:** The documentation review used the
[official Issue 9 standard](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf).
The 18-unit conformance table keeps the same path set. The previous result
applies to each unit that does not change. The review examines each full
logical unit that changed in this table.

| Path | Full logical unit that changed |
| --- | --- |
| `reference/ENGINEERING_POLICY.md` | The full TT-DOC-001 profile. |
| `reference/PROJECT_PLAN.md` | The current owner view and the TT-DOC-002 decision row. |
| `reference/current/PHASE_EVIDENCE.md` | This TT-DOC-002 panel and the current-register paragraph. |
| `reference/current/gate-decisions.json` | The human-readable TT-DOC-002 record. Exact JSON data stays outside the linguistic assessment. |
| `.agents/skills/tracktemplate-documentation-review/SKILL.md` | The full Editing rules section. |
| `.agents/skills/tracktemplate-documentation-review/references/writing-checklist.md` | The full Concision and tone section. |

The internal result for these six units is `ASD-STE100 Issue 9 conforming`
with the TrackTemplate UK English spelling directive. This result is a
TrackTemplate conformance assessment. It is not external ASD certification,
endorsement, or an official conformance assessment. Issue 9 conformance stays
Unknown for live prose outside the logical units in the TT-DOC-001 and
TT-DOC-002 tables. Frozen history also stays outside this assessment.

**Semantic controls:** The controls keep Issue 9 as the normative standard.
They keep the UK English spelling directive in its bounded scope. They reject a rule
that makes American English spelling necessary. They reject a change to other
Issue 9 requirements, the conformance scope, terminology ownership, or project
authority. They do not use a whole-paragraph equality check as proof of
linguistic conformance.

**Risk panel:**

| Risk | Panel judgement | Result |
| --- | --- | --- |
| PR-12 — direction or task-selection drift | One canonical profile prevents a second spelling-policy owner. | Medium / Mitigate / Partial. The disposition does not change. |
| PR-22 — authority transfer without challenge | The explicit owner correction and two new exact-state reviews prevent an authority change without review. | High / Remove / Effective for the current bounded scope. The disposition does not change. |
| PR-13 — repository or evidence loss | Exact-state publication and the post-merge preservation audit protect accepted content. | Critical / Mitigate / Effective for the current bounded scope. The disposition does not change. |

**Independent review state:** Two reviewers examined the exact candidate. The
ASD-STE100 review result was PASS WITH FINDINGS. That review found that the
candidate obeys Issue 9 with the TrackTemplate UK English spelling directive.
The governance review result was PASS WITH FINDINGS. That review examined
authority and preservation. No reviewer found a blocking condition. The reviewers did not
change the candidate.

The same reviewers also examined previous candidate states. The finding is
that Issue 9 conformance stays Unknown for live prose outside the logical units
in the two tables.

> **TT-DOC-002 — Correct the TT-DOC-001 UK English spelling directive**
>
> At protected `main` `54d5d8312429ededff83084a3bc39c8756729d19`, I
> correct the spelling directive in TT-DOC-001.
>
> ASD-STE100 Simplified Technical English, Issue 9, stays the normative
> controlled-writing standard for applicable TrackTemplate canonical prose.
> TrackTemplate uses UK English spelling as its project spelling directive in
> this bounded scope. This directive applies the spelling option in Issue 9 Rule 1.14.
>
> This correction changes spelling policy only. It does not change Issue 9
> vocabulary or grammar requirements. It does not change approved meanings,
> parts of speech, technical noun controls, technical verb controls, or the
> requirement for linguistic review.
>
> `reference/ENGINEERING_POLICY.md` stays the one canonical owner of TT-DOC-001.
> `reference/TERMINOLOGY.md` stays the one project terminology owner. The
> information order does not change: owner view → canonical information →
> proof/provenance. Skill routing and bounded migration do not change.
>
> The original 18-unit conformance scope does not expand. Issue 9 conformance
> stays Unknown for live prose outside the logical units in the TT-DOC-001 and
> TT-DOC-002 tables.
> This decision does not claim external certification, endorsement, or
> an official conformance assessment.
>
> This decision does not change the accepted TT-DOC-001 decision or LFE-018.
> TT-DOC-002 changes only the previous spelling rule. It does not change other
> TT-DOC-001 authority or exclusions.
>
> This decision changes no phase, exit, risk, or evidence acceptance. It
> changes no product source, product behaviour, FreeCAD behaviour, exporter
> behaviour, persistence, schema, API, output, or release state. It gives no
> production, physical-output, or `project-cleared` authority. It gives no
> packaging, release, or tagging authority.
>
> Phase 6 stays at 2/5. Exits 1, 4, and 5 stay Pending. Output stays
> private-development. Project status stays `unknown`.

<a id="freecad-1-1-3-compatibility-requalification-panel"></a>

## FreeCAD 1.1.3 compatibility requalification panel and owner decision

This Level 3 panel changes host-compatibility authority only. It uses protected
`main` `724a3b79ab5b71025041e84eac3501a457b3fb76` as its source state. Phase 6
stays at 2/5. Exits 1, 4, and 5 stay Pending. Output stays
private-development. Project status stays `unknown`.

### Owner view

| Field | Result |
| --- | --- |
| Current state | The exact Linux x86_64 Flatpak FreeCAD 1.1.1 profile is qualified. The installed 1.1.3 host was not qualified before this panel. |
| What changed | The panel also qualifies the exact host profile for FreeCAD 1.1.3. It changes no product source or product behaviour. |
| What now works | The host matrix gave the specified results for B16 loading, persistence, migration, GUI operation, exact geometry, and DXF on 1.1.3. |
| Limitations/findings | FreeCAD 1.1.2 and all other releases are not qualified. Only the recorded Linux x86_64 stable Flatpak bundled stack has this result. Phase 10 owns the packaged Workbench and `package.xml` evidence. FreeCAD recommends 1.1.3 for security. The 1.1.1 decision is not a security endorsement. |
| Owner decision | D-GOV-006 is Accepted for the exact 1.1.3 profile only. |
| Next action | Publish the exact reviewed change. Do not start a new development tranche in this cycle. |

### Official host review

The [FreeCAD 1.1.3 release](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.3)
is a maintenance and security release. The FreeCAD release record gives
changes that can have an effect on TrackTemplate. These changes include module discovery,
FCStd handling, Python-object loading, selection, visibility, and document save
behaviour. Thus, the panel used the host matrix in the compatibility contract.
The patch number was not compatibility evidence.

The FreeCAD release records security issues in FCStd and file handling. Each
FreeCAD release before 1.1.3 has one or more of these issues. FreeCAD recommends
that all users install 1.1.3. This does not remove the 1.1.1 functional
compatibility decision. That decision is not a security endorsement.

The installed host gave this exact runtime record:

| Component | FreeCAD 1.1.1 host profile | FreeCAD 1.1.3 host profile | Classification |
| --- | --- | --- | --- |
| FreeCAD | `1.1.1`, revision `44874`, commit `0108fd4b4850cc46e625b60e53cea7a7bbe69f8d` | `1.1.3`, revision `44987`, commit `145529fe741292ff0b3977a01195bf0247425794` | Expected host-version difference with no TrackTemplate contract effect |
| CPython | `3.13.14` | `3.13.14` | Unchanged |
| PySide6 / Qt | `6.10.3` / `6.10.3` | `6.10.3` / `6.10.3` | Unchanged |
| OpenCASCADE | `7.8.1` | `7.8.1` | Unchanged |
| Coin | `SIM Coin 4.0.8` | `SIM Coin 4.0.8` | Unchanged |
| Platform | Linux x86_64 stable `org.freecad.FreeCAD` Flatpak | Linux x86_64 stable `org.freecad.FreeCAD` Flatpak | Unchanged |

### Qualification evidence

The initial assessment used a temporary detached worktree. The temporary contract
in that worktree added only the exact 1.1.3 candidate profile. The primary
checkout did not change during that assessment. Each FreeCAD process used a new
document or a copied fixture. Source fixture hashes did not change.

| Evidence area | Command or runner | Result on 1.1.3 | Comparison |
| --- | --- | --- | --- |
| Exact host and bundled stack | `tools/runtime_compatibility_probe.py --pass --require-qualified` in FreeCADCmd | The probe qualified `linux-x86_64-flatpak-freecad-1.1.3`. | Only the exact host profile changed. The other bundled stack values did not change. |
| B16 package and launcher loading | `tests/freecad_validate_phase2_foundation.py` | The test gave PASS and its specified sentinel. It changed no document. | The result did not change. |
| Modular routing and legacy-host load | `tests/freecad_validate_phase3_transition_slice.py` | The test gave PASS and its specified sentinel. | The result did not change. |
| Canonical state and recompute area | `tests/freecad_validate_phase4_transition_state.py` | The test gave PASS and its specified sentinel. | The result did not change. |
| Document ownership, transactions, Undo/Redo, save/reopen, failure recovery, and cleanup | `tests/freecad_validate_phase4_transition_persistence.py` | The test gave PASS and its specified sentinel. | The result did not change. |
| B14/B15 ingress detection and read-only family assessment | `tests/freecad_validate_phase4_legacy_document_detection.py` and `tests/freecad_validate_phase4_plain_line_transition_assessment.py` | The two tests gave PASS and their specified sentinels. | The results did not change. |
| Accepted migration family | `tests/freecad_validate_phase4_plain_line_transition_migration.py` in FreeCADCmd and isolated real GUI | The two execution modes gave PASS and the specified sentinel. | The result did not change. |
| Python package and chair-definition import | `tests/freecad_validate_phase4_chair_definition.py` | The test gave PASS and its specified sentinel. It changed no document. | The result did not change. |
| Pivy/Coin, edit, ViewProvider, display, selection, and explicit activation | Phase 5 Coin/edit checks and `tools/freecad_bridge/run-phase5-transition-viewprovider` | The tests gave PASS and the specified headless and real-GUI sentinels. | Version and profile fields changed. Contract results did not change. |
| Entry/Exit parity workflow on a qualified host | `tools/freecad_bridge/run-phase3-transition-workflows` | All four routes gave PASS. | Contract results did not change. Timings are not qualification evidence. |
| Exact contract and transient Part lifecycle | Phase 6 exact-contract and exact-geometry FreeCADCmd checks | The two tests gave PASS and their specified sentinels. | The results did not change. |
| Deterministic DXF, manifest, import, failure, cleanup, and D-P6-003 recovery | Phase 6 standalone and FreeCADCmd DXF checks | The two tests gave PASS and their specified sentinels. | Names, bytes, hashes, schema, identifiers, and recovery results did not change. |

These raw records contain the qualification proof:

- `benchmark-output/validation-pipeline/20260815T195204447910Z/` contains the
  corrected standalone profile with 187 parsed files and 59 of 59 results.
- `benchmark-output/validation-pipeline/20260815T184826613031Z/` contains the
  1.1.3 transition host and GUI profile.
- `benchmark-output/freecad113-requalification/20260815T184944Z/`
- `benchmark-output/freecad-bridge/phase3-transition-workflow-runs/20260815T190953973316Z-series/`.

An initial invocation used `flatpak run --command=FreeCADCmd
org.freecad.FreeCAD tools/runtime_compatibility_probe.py --pass`. The `--pass`
option had no argument. FreeCADCmd stopped with exit code 1 before the script
started. The initial error was
`the required argument for option '--pass' is missing`. Codex session call
`call_aQfBr45aDcefyiKCYr3AToMc` contains the exact command and raw output.

The session call also contains the working directory, exit code, and initial
error. The invocation with exit code 1 did not produce a runtime record. Other
runtime checks show that the installed host is the exact 1.1.3 host profile.
The source state for the invocation with exit code 1 was the protected baseline.

The result for the invocation without a `--pass` argument is
`fixture-or-harness-defect`. The contract command `--pass --require-qualified`
was not the command with exit code 1. After that, an invocation of the contract
command qualified 1.1.3. The diagnostic command `--pass=--require-qualified`
gave the same result as the contract command. It does not replace the contract
command. The two result logs have SHA-256
`58bd07e3d79c706cdbb8c3cd41eb7cf2090c2d12437c197a05eb5a9945aeae69`.

The command correction changed no product requirement.

The panel found no TrackTemplate compatibility defect. It cannot examine a
packaged Workbench or Addon because Phase 10 does not have that evidence. It also
cannot examine Windows, macOS, non-Flatpak Linux, other architectures,
FreeCAD 1.1.2, other FreeCAD releases, or other bundled stacks. Timing
differences are not defects or Phase 6 Exit 4 evidence in this cycle.

### API, object-model, and preservation result

The public API, schemas, identifiers, canonical railway state, persistence
payloads, output formats, and generated bytes do not change. The runtime
evaluator accepts a list of exact profiles. This cycle changes no
`tracktemplate` product module. Host validators accept only the two named
profile IDs.

The 1.1.1 evidence and performance reports keep their host identity. The Phase
10 `package.xml` intent stays at exact 1.1.1. A version range includes
FreeCAD 1.1.2 without evidence. Phase 10 must select manifest metadata
from its current evidence.

### Issue 9 review

The documentation review used the
[official Issue 9 standard](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf)
and the TrackTemplate UK English spelling directive. It examined each full
logical unit in this table.

| Path | Full logical unit |
| --- | --- |
| `reference/TERMINOLOGY.md` | The three Host compatibility rows and the Qualify and Requalify technical-verb rows. |
| `reference/PROJECT_PLAN.md` | The current owner view, the D-GOV-006 summary, the D-GOV-006 decision row, and the compatibility authority link. |
| `reference/VALIDATION.md` | The full FreeCAD document validation unit and the Phase 1 runtime and legacy ingress compatibility unit. |
| `reference/contracts/phase1-compatibility.json` | The changed human-readable bounded-scope strings, security limit, 1.1.3 evidence strings, support rule, and evidence-gap string. |
| `reference/current/PHASE_EVIDENCE.md` | This full D-GOV-006 panel and the D-GOV-006 carried-control sentences. |
| `reference/current/gate-decisions.json` | The human-readable D-GOV-006 record. Exact JSON data stays outside the linguistic assessment. |

Before the final reviews, ASD-STE100 Issue 9 conformance was not verified for
these six corrected units. The final documentation review must examine this
exact state with the TrackTemplate UK English spelling directive. The pull
request and completion report must record the result. Exact identifiers, JSON
keys, commands, hashes, and machine values stay outside the linguistic review.
Issue 9 conformance stays Unknown
for live prose outside the TT-DOC-001, TT-DOC-002, and D-GOV-006 tables. Frozen
history also stays outside this assessment.

### Review state

The initial compatibility review examined FreeCAD and the API. Its result was
BLOCKED. The reviewer found no host-compatibility defect. It found that the
command record was not correct. The security limitation and Issue 9 review were
missing.

The initial quality review examined authority and preservation. Its result was
PASS WITH FINDINGS. It found no blocking condition in the supported bounded
scope.

The initial quality reviewer did not have the session call. The reviewers did not
change the candidate. The two reviewers must examine the final exact state. The
two final reviews must find no blocking condition before merge. The pull request
and completion report must record the two final results. This panel must not
change after the reviews.

### Risk panel

| Risk | Panel judgement | Result |
| --- | --- | --- |
| PR-01 — incomplete release workflow coverage | The current B16 host matrix gave the specified results. Phase 10 owns packaged Workbench and release coverage. | High / Remove / Partial. The disposition does not change. |
| PR-17 — persistence or migration corruption | Headless and real-GUI checks examined transactions, Undo/Redo, copied targets, save/reopen, failures, and source preservation on 1.1.3. | Critical / Mitigate / Partial. The disposition does not change. |
| PR-22 — authority transfer without independent challenge | The owner gave exact Level 3 authority. Two new read-only reviews and exact-head CI are necessary before merge. | High / Remove / Effective (current bounded scope). The disposition does not change. |
| PR-13 — repository or evidence loss | The cycle uses a clean baseline, bounded paths, protected-main merge, and a full post-merge preservation audit. | Critical / Mitigate / Effective (current bounded scope). The disposition does not change. |

**Panel recommendation:** **Continue with bounded conditions.** Qualify only
the exact recorded 1.1.3 profile. Keep 1.1.1 qualified. Do not qualify 1.1.2 or
any other host. Preserve all stated product, phase, output, risk,
packaging, and release limits.

> **D-GOV-006 — Qualify the exact FreeCAD 1.1.3 host profile**
>
> At protected `main` `724a3b79ab5b71025041e84eac3501a457b3fb76`, I
> qualify the exact Linux x86_64 stable `org.freecad.FreeCAD` Flatpak FreeCAD
> 1.1.3 profile. The bundled stack contains CPython 3.13.14, PySide6/Qt 6.10.3,
> OpenCASCADE 7.8.1, and Coin 4.0.8. The compatibility contract names only the
> exact 1.1.1 and 1.1.3 host profiles.
>
> FreeCAD 1.1.2 and all other FreeCAD releases, platforms, architectures,
> package channels, and bundled stacks are not qualified. The 1.1.1 evidence
> keeps its host identity. The Phase 10 `package.xml` intent does not change.
> Phase 10 must not use metadata that records support for 1.1.2.
>
> FreeCAD records security issues for all releases before 1.1.3. It recommends
> installation of 1.1.3. The 1.1.1 decision gives functional
> compatibility authority only. It is not a security endorsement.
>
> This decision changes compatibility authority only. It changes no product
> source, railway behaviour, canonical geometry, schema, persisted identifier,
> API, output format, generated output, risk disposition, phase, or exit.
>
> Phase 6 stays at 2/5. Exits 1, 4, and 5 stay Pending. Output stays
> private-development. Project status stays `unknown`. It gives no production,
> physical-output, `project-cleared`, packaging, release, or tagging authority.

<a id="phase-6-performance-evidence-host-boundary-panel"></a>

## Panel and owner decision about hosts for Phase 6 performance evidence

**Decision and source state:** The source state for this Level 3 decision is
protected `main` `3f20de704a060ab37478c34b3a7cb3586a9b2220`. D-GOV-006 qualifies the
exact `linux-x86_64-flatpak-freecad-1.1.3` host profile. The exact
`linux-x86_64-flatpak-freecad-1.1.1` profile stays qualified. Phase 6 stays at
2/5 accepted exits. Exit 4 stays Pending.

**Authority before this decision:** The project admitted performance evidence
from only the exact 1.1.1 profile. The previous validator rejected a result
unless it recorded FreeCAD 1.1.1. A test command on the exact 1.1.3 profile
completed the Edit, Validate, and Export workflow. The previous validator then
rejected that result. The evidence file is
`benchmark-output/freecad-bridge/phase6-transition-pipeline-runs/20260815T214842401485Z-profile/sample-01.log`.
D-GOV-007 does not admit this test result as Exit 4 evidence.

**Host rule:** D-GOV-007 changes the
[rule for hosts in Phase 6 performance evidence](../PERFORMANCE_SOP.md#phase-6-performance-host-boundary).
D-GOV-007 authorises only these two exact host profiles to supply candidate
evidence for Phase 6 performance:

- `linux-x86_64-flatpak-freecad-1.1.1`
- `linux-x86_64-flatpak-freecad-1.1.3`.

A later decision can admit a performance result only if it comes from one of
these exact host profiles. Each new schema-2 result has exact host identity.
It records the ID and FreeCAD version of its exact host profile. The validator
rejects a result that names a different host profile or FreeCAD version. It
also rejects a result set that contains two host profiles.

If the project qualifies a subsequent host profile, this does not authorise
performance evidence from that profile.

To compare TrackTemplate performance, use one exact host profile. A different
method can compare the two host profiles only if it independently shows the
effect of the host profile and the TrackTemplate effect. The different results
do not show that TrackTemplate performance became better.

**Evidence and validator change:** The
[1.1.1 performance report](../benchmarks/2026-08-02-phase6-transition-pipeline-performance.md)
does not have a `host_profile_id` field. It records FreeCAD 1.1.1, platform
data, and the qualified-runtime contract hash. These data identify the exact
host profile for FreeCAD 1.1.1. D-GOV-007 keeps this report as 1.1.1 evidence.

The 1.1.1 report is a schema-1 report. New samples and performance records use
schema 2. The `schema_version` value identifies the structure of the evidence
record. The `profile_id` value is
`phase6-transition-edit-validate-export-profile-v1`. It identifies the
measurement method and not the record schema.

The Phase 6 profiler records the ID of the exact host profile in each new
sample and summary. The standalone validator has the two exact ID/version
mappings.

It rejects schema 1 and FreeCAD 1.1.2. It rejects a result unless its ID/version
pair is one of the two mappings. It rejects a `host_profile_id` value that is
not a string. It rejects an exact-geometry receipt that records a different
FreeCAD version. It also rejects a result set with two host profiles.

This cycle does not measure performance. It admits no performance result. It
does not admit the test result. It defines no value for a performance budget.
It does not claim that performance became better.

It changes the schema for internal performance-evidence records from 1 to 2.
It changes no TrackTemplate product behaviour, product output, product schema,
public API, or set of qualified host profiles.

**Risk panel:** The decision changes which host profile can supply evidence. It is
Level 3 and `necessary-enabling` progress.

| Risk | Panel judgement | Result |
| --- | --- | --- |
| PR-15 — deferred cost | The method must use one exact host profile and record its exact data. Thus, a host difference cannot be evidence of a TrackTemplate or deferred-cost change. | High / Mitigate / Partial. The disposition does not change. |
| QA-R04 — no value for a performance budget | The decision defines no budget and admits no performance result. | High / Mitigate / Partial. The disposition does not change. |
| PR-22 — authority transfer | The owner gives the exact Level 3 authority. A reviewer who did not make the change must examine it. The reviewer must not change files. | High / Remove / Effective (current bounded scope). The disposition does not change. |
| PR-13 — repository or evidence loss | Bounded paths, exact-state publication, and the post-merge audit preserve accepted content. | Critical / Mitigate / Effective (current bounded scope). The disposition does not change. |

### Documentation conformance

The documentation review uses the
[official Issue 9 standard](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf)
and the TrackTemplate UK English spelling directive. It examines each full
logical unit in this table.

| Path | Full logical unit |
| --- | --- |
| `reference/PERFORMANCE_SOP.md` | The full section with the heading `Hosts for Phase 6 performance evidence`. |
| `reference/VALIDATION.md` | The full compatibility unit for Phase 1 runtime and legacy ingress. |
| `reference/PROJECT_PLAN.md` | The current owner view, the D-GOV-007 phase summary, and the D-GOV-007 decision row. |
| `reference/current/PHASE_EVIDENCE.md` | This full D-GOV-007 panel. The reviewed material also includes the changed Exit 4 disposition and the D-GOV-007 carried-control sentences. |
| `reference/current/gate-decisions.json` | The human-readable D-GOV-007 record. Exact JSON data is not part of the linguistic assessment. |

Before the conformance review, no reviewer verified ASD-STE100 Issue 9
conformance for these five changed units. The conformance review must examine
this exact candidate.
The pull request and completion report must record the result. Exact identifiers,
paths, commands, hashes, JSON keys, and machine values are not part of the
linguistic review. Issue 9 conformance stays Unknown for other live prose.

### Review state

A reviewer who did not make this change must examine the exact candidate.
The reviewer must not change files. The review must include the host rule for
performance, the decision to admit evidence, authority, preservation, and the
Issue 9 assessment. It must find no blocking condition before the project
merges the candidate.
The pull request and completion report record the result. This panel must not
change after the review.

**Panel recommendation:** **Continue with bounded conditions.** Authorise the
exact 1.1.3 profile for Phase 6 performance evidence. Use one exact host
profile in each result set. Admit no performance result. Accept no phase exit
in this cycle.

> **D-GOV-007 — Authorise the exact 1.1.3 profile for Phase 6 performance evidence**
>
> At protected `main` `3f20de704a060ab37478c34b3a7cb3586a9b2220`, I
> change the host rule for Phase 6 performance evidence. D-GOV-007 authorises
> the exact `linux-x86_64-flatpak-freecad-1.1.1` profile and the exact
> `linux-x86_64-flatpak-freecad-1.1.3` profile to supply candidate evidence for
> Phase 6 performance. D-GOV-006 qualifies the 1.1.3 profile.
>
> A later decision can admit a performance result only if it comes from one of
> these exact host profiles. Each new schema-2 result must have exact host
> identity. It must record the ID and FreeCAD version of its exact host profile.
>
> The 1.1.1 report from 2026-08-02 is a schema-1 report. It does not have a
> `host_profile_id` field. It records FreeCAD 1.1.1, platform data, and the
> qualified-runtime contract hash. These data identify the exact host profile
> for FreeCAD 1.1.1. D-GOV-007 keeps this report as 1.1.1 evidence.
>
> Results from different host profiles must stay in different sets.
> To claim that TrackTemplate performance became better, compare results from
> one exact host profile. A different method can compare the two host
> profiles only if it independently shows the effect of the host profile and
> the TrackTemplate effect.
>
> If the project qualifies a subsequent host profile, this does not authorise
> performance evidence from that profile. A separate Level 3 decision from the
> owner is necessary.
>
> This decision changes only the host rule for Phase 6 performance evidence.
> It changes the schema for internal performance-evidence records to version 2.
> It does not accept Exit 4, define a value for a performance budget, claim
> better performance, or admit the rejected 1.1.3 test result. It does not
> qualify FreeCAD 1.1.2, a subsequent release, or a version range that includes
> another release.
>
> It changes no product behaviour, accepted-exit count, risk disposition,
> product output, product schema, public API, or release authority. Exit 4 stays
> Pending. Exits 1 and 5 stay Pending. Phase 6 stays at 2/5 accepted exits.
> Output stays private-development. Project status stays `unknown`.
>
> This decision gives no production, physical-output, `project-cleared`,
> packaging, release, or tagging authority.

<a id="phase-6-performance-evidence-on-freecad-1-1-3"></a>

## Performance evidence on FreeCAD 1.1.3

This Level 2 tranche starts from protected-main merge
`f370b029bb4c1ce34987dc025a741185e233df04`. It changes no product source,
performance method, schema, compatibility contract, or output contract.

The profiler used three new GUI processes on the exact
`linux-x86_64-flatpak-freecad-1.1.3` host profile. Each process did one cold
Edit, Validate, and Export journey. Each process then did one untimed warm-up
and three measured reuse cycles. All samples use evidence schema 2.

The full cold journey had a median of 142.912 ms (140.426–247.792). The edit
median was 22.106 ms. The Validate median was 73.570 ms. The created Export
median was 44.992 ms. The full warm cycle for Validate and Export had a median
of 10.417 ms (9.857–10.799).

The correctness checks found no failure in the three cold journeys or nine
warm cycles.
The runs kept stable mapping, compact editable objects, and one Undo unit.
Validate and Export returned the same exact result. All processes had equal
output hashes. The document count after cleanup was zero. The staging-entry
count after cleanup was zero.

The [full report](../benchmarks/2026-08-16-phase6-freecad-1.1.3-transition-pipeline-performance.md)
records the method, source hashes, ranges for each measurement, resource data,
and limitations. Git ignores the raw record at
`benchmark-output/freecad-bridge/phase6-transition-pipeline-runs/20260816T151429730281Z-profile/`.
Its `performance.json` SHA-256 is
`83deda4bdb01c5c5677f568ac62625572b19c3bce313af515ba4fa6b9840298a`.

The 1.1.1 report uses the exact FreeCAD 1.1.1 host profile. This report uses
the exact FreeCAD 1.1.3 host profile. The source states are different. The
project cannot use the difference between these reports to claim that
TrackTemplate performance became better. This schema-2 result gives evidence
for a subsequent performance investigation on one exact host profile.

This result adds evidence for subsequent decisions about PR-15 and QA-R04.
Their risk dispositions do not change.

This tranche admits no evidence for
Exit 4. It defines no performance budget. It accepts no phase exit. Phase 6
stays at 2/5 accepted exits. Exit 4 stays Pending.

<a id="phase-6-exit-4-performance-direction-panel"></a>

## Phase 6 Exit 4 performance-direction panel

**Source state:** The source state for this Level 3 decision is protected
`main` `9169b7e7beec5cf614b8a5284db0f97367728def`. Phase 6 has 2/5
accepted exits. Exit 4 is Pending. D-GOV-006 qualifies the exact FreeCAD 1.1.3
host profile. D-GOV-007 authorises that profile as a source of candidate
performance evidence for Phase 6.

No subsequent decision defines an Exit 4 comparison rule. No subsequent
decision selects a performance hypothesis. D-GOV-008 is the next decision
ID.

**Comparison baseline:** The
[PR #50 performance series](../benchmarks/2026-08-16-phase6-freecad-1.1.3-transition-pipeline-performance.md)
can be the comparison baseline. Its evidence source state is
`f370b029bb4c1ce34987dc025a741185e233df04`. Its raw `performance.json` has
SHA-256
`83deda4bdb01c5c5677f568ac62625572b19c3bce313af515ba4fa6b9840298a`.

The baseline uses the exact
`linux-x86_64-flatpak-freecad-1.1.3` host profile and measurement profile
`phase6-transition-edit-validate-export-profile-v1`. It records three new GUI
processes. Each process records one cold Edit, Validate, and Export journey.
It also records one warm-up and three warm reuse cycles.

The baseline records correctness, exact output, lifecycle, resource, and
cleanup results. It has only three cold samples. Thus, it records the source,
method, workload, and initial cost record. These samples do not show that
performance became better.

D-GOV-008 accepts this series as the comparison baseline. A Level 2 cycle must
collect new samples in paired blocks. Each block must have a baseline sample
and a candidate sample. The cycle must use the same host, method, workload,
bounded output work, and correctness conditions. It must not use the 1.1.1
report to claim that TrackTemplate performance became better.

**Edit-path finding:** The accepted Edit has one necessary preview
regeneration. The preview sampler calculates 33 stations. For each station, it
calculates clothoid displacement with the scalar API. For each of the 31
interior stations, the API does a 240-step Simpson integration from station
zero. The endpoint calculation also does an integration.

A temporary profile measured 50 preview regenerations. It measured 3.263 ms
of process CPU time for each preview regeneration. The profile recorded 0.144
seconds for integration and 0.163 seconds for the sampler. Thus, integration was
approximately 88% of the sampler time in the profile. The median for process
CPU time in PR #50 Edit is 19.653 ms.

The diagnostic identifies one measured Edit cost. It does not show all the
Edit costs. Source and diagnostic evidence give
evidence for one performance hypothesis. One preview batch function can
calculate all preview displacement values without zero-origin integration at
each interior station.

The initial temporary command stopped. The target code did not start. The
temporary script did not include the repository import path. The primary
failure class is `fixture-or-harness-defect`. The repair changed only the
temporary probe. The same command then reported the profile result.

**Selected hypothesis and bounded Level 2 work:** D-GOV-008 selects a performance
hypothesis for zero-origin integration in the preview sampler. One
preview batch function can make this Edit-path cost lower. The candidate must
do all new calculation work during measured Edit.

The candidate must add no work to Validate, Export, a warm cycle, cleanup, or
an unmeasured boundary. The profile does not measure process launch, module
import, fixture construction, dialog opening, or document disposal at the end.
The candidate must add no work to these areas. It must add no work to other
setup or teardown that the profile does not measure.

Code inspection must show that the candidate does all new product work during
measured Edit. If inspection does not give sufficient proof, stop the cycle.
The result is FAIL if measured Edit does not include all new candidate work.

The bounded Level 2 work includes the preview sampler and one preview batch
function if it is necessary. It also includes directly dependent tests,
performance evidence, and current evidence. The
[comparison-direction section](../PERFORMANCE_SOP.md#phase-6-exit-4-comparison-direction)
owns the full bounded work and comparison rule.

The change must keep the scalar alignment API, preview point oracle, segment
count, frame, and identities. It must keep source signatures, cache lifecycle,
and Coin mapping. It must keep canonical state, transaction, Undo/Redo,
save/reopen, and cleanup behaviour. Exact validation, DXF, manifest, hashes,
and diagnostics must not change.

The evidence does not authorise a new cache. It does not authorise a runtime
dependency or a public API. The Level 2 cycle must stop if it cannot keep all
invariants. It must also stop if its full comparison result is not PASS.

**Comparison rule:** The Level 2 cycle must use 12 paired blocks. Each block
has one baseline sample and one candidate sample. Each sample uses a new GUI
process. Six blocks use the baseline first. Six blocks use the candidate first.
The cycle must record the sequence before measurement starts.

Preserve all raw attempts. A product defect, invariant difference, or
correctness failure gives a FAIL result and stops the cycle. A replacement is
possible only for the failure class `fixture-or-harness-defect` or
`environment-or-profile-defect`. The attempt with this failure must give no
measurement for the comparison. Record the failure class before replacement.
For the replacement, use the same block and the same recorded sequence.

For each numeric warm metric, calculate the median of the three measured warm
cycles in one sample. This median is the warm block value for that sample.
All warm-cycle correctness results must be PASS.

For each metric, a paired difference is candidate minus baseline. Process CPU
time for Edit must have a negative difference in a minimum of 10 blocks. The
median of these differences must be negative. The median of the paired differences for
Edit wall time must be negative.

The medians of the paired differences for cold-journey CPU and wall time must
be negative. Use the no-displacement rule for Validate, Export, cleanup, all
warm block values, all resource metrics, and the journey remainder. The result
for a metric is FAIL if the median of its paired differences is more than its
baseline MAD. The result is also FAIL if 10 or more paired differences are
positive.

Use the same rule for RSS, RSS change, high-water RSS, and high-water RSS
change. Use it in each measured stage and the full journey. All discrete
invariants must have results equal to the baseline results. All correctness
and output results must stay unchanged.

One sample cannot give a PASS result. A missing condition gives a
FAIL result. The project must not select a new rule after it knows the
candidate results.

D-GOV-008 makes no product change. It does not admit the PR #50 baseline
or a subsequent result as Exit 4 evidence. It defines no product performance
budget and does not accept Exit 4. Exit 4 stays Pending. A subsequent decision
at Level 3 must admit the evidence before owner acceptance of Exit 4.

**Risk panel:** This Level 3 decision is `necessary-enabling` progress. It
changes performance direction and Level 2 authority only.

| Risk | Panel judgement | Result |
| --- | --- | --- |
| PR-15 — deferred cost | The rule examines Edit, Validate, Export, the full cold journey, warm reuse, resources, cleanup, and all unmeasured boundaries. A metric gives FAIL when the median of its paired differences is more than its baseline MAD. | High / Mitigate / Partial. The disposition does not change. |
| QA-R04 — no product performance budget | The decision defines a comparison rule and not a product budget. Representative whole-layout capacity stays Unknown. | High / Mitigate / Partial. The disposition does not change. |
| PR-22 — authority transfer | The owner gives the exact Level 3 authority. Two read-only reviewers must examine one exact candidate. | High / Remove / Effective for the current bounded scope. The disposition does not change. |
| PR-13 — repository or evidence loss | Bounded paths, exact-state publication, and the post-merge audit preserve accepted content. | Critical / Mitigate / Effective for the current bounded scope. The disposition does not change. |

### Documentation conformance

The documentation review uses the
[local Issue 9 source](../external/asd-ste100/README.md). This is the official
source. The review also uses the TrackTemplate UK English spelling directive.
It examines each full logical unit in this table.

| Path | Full logical unit |
| --- | --- |
| `reference/PERFORMANCE_SOP.md` | The full section with the heading `Phase 6 Exit 4 comparison direction`. |
| `reference/TERMINOLOGY.md` | The five new performance-term rows. |
| `reference/PROJECT_PLAN.md` | The current owner view, D-GOV-008 phase summary, and D-GOV-008 decision row. |
| `reference/current/PHASE_EVIDENCE.md` | This full D-GOV-008 panel, the changed Exit 4 disposition, and D-GOV-008 carried-control text. |
| `reference/current/gate-decisions.json` | The human-readable D-GOV-008 record. Exact JSON data is not part of the linguistic review. |

Before the conformance review, no reviewer verified ASD-STE100 Issue 9
conformance for these changed units. The conformance review must examine the
exact candidate. The pull request and completion report must record the
result. Issue 9 conformance stays Unknown for other live prose.

### Review state

Two reviewers who did not make the change must examine one exact candidate.
The performance reviewer must examine the baseline and performance hypothesis.
That reviewer must examine the comparison rule, no-displacement rule, and
unmeasured boundaries. The governance reviewer must examine authority,
evidence, documentation, and preservation. The reviewers must not change files.

The two reviews must find no blocking condition before the project merges the
candidate. The pull request and completion report must record the results.
This panel must not change after those reviews.

**Panel recommendation:** **Continue with bounded conditions.** Accept the
PR #50 series as the comparison baseline. Select the performance hypothesis
for zero-origin integration. Define the comparison rule and authorise only the
stated Level 2 cycle. Keep Exit 4 Pending.

> **D-GOV-008 — Accept the Exit 4 comparison baseline and performance direction**
>
> At protected `main` `9169b7e7beec5cf614b8a5284db0f97367728def`, I
> accept the PR #50 FreeCAD 1.1.3 series as the comparison baseline. The
> evidence source state is `f370b029bb4c1ce34987dc025a741185e233df04`.
> The exact host profile is
> `linux-x86_64-flatpak-freecad-1.1.3`. The measurement profile is
> `phase6-transition-edit-validate-export-profile-v1`.
>
> The baseline includes the full Edit, Validate, Export, warm-reuse,
> correctness, lifecycle, output, and cleanup conditions. A subsequent cycle
> at Level 2 must collect new samples in paired blocks. Each block must have a
> baseline sample and a candidate sample. It must not use the 1.1.1 report to
> claim that TrackTemplate performance became better.
>
> I select one performance hypothesis. The preview sampler calculates 33
> stations. It does zero-origin integration for each interior station. One
> preview batch function can calculate all preview displacement values without
> that work at each station.
>
> I authorise a Level 2 change in the preview sampler. The change can add one
> preview batch function if it is necessary. It can also change
> directly dependent tests and evidence. It must keep all stated railway,
> preview, canonical-state, transaction, persistence, exact-validation,
> export, diagnostic, and cleanup invariants.
>
> The rule uses 12 paired blocks on the exact 1.1.3 host profile. Six blocks
> use the baseline first. Six blocks use the candidate first. The paired
> difference for process CPU time in Edit must be negative in a minimum of 10
> blocks. The median of these differences must be negative.
>
> The medians of the paired differences for Edit wall time and cold-journey
> CPU and wall time must be negative. Use the no-displacement rule for
> Validate, Export, cleanup, warm block values, resource metrics, and the
> journey remainder. The result for a metric is FAIL if the median of its
> paired differences is more than its baseline MAD. The result is also FAIL if
> 10 or more paired differences are positive.
>
> Use the no-displacement rule for RSS, RSS change, high-water RSS, and
> high-water RSS change. Use it in each measured stage and the full journey.
> All discrete invariants, correctness, and output results must stay unchanged.
> All warm-cycle correctness results must be PASS.
>
> The candidate must add no work to an unmeasured boundary. This includes
> process launch, module import, fixture construction, dialog opening, document
> disposal at the end, and other unmeasured setup or teardown. Inspection must
> show that the candidate does all new product work during measured Edit. If
> inspection does not give sufficient proof, stop the cycle.
>
> A product defect, invariant difference, or correctness failure gives FAIL
> and stops the cycle. A replacement is possible only for the failure class
> `fixture-or-harness-defect` or `environment-or-profile-defect`. The attempt
> with this failure must give no measurement for the comparison.
>
> Preserve all attempts. Record the failure class before replacement. The
> Level 2 cycle must record the sequence before measurements start. For the
> replacement, use the same block and the same recorded sequence.
>
> This decision makes no product change. It does not admit the PR #50
> baseline or a subsequent result as Exit 4 evidence. It does not claim that
> performance became better, define a product performance budget, or accept
> Exit 4.
>
> It gives no authority for a new cache, a runtime dependency, or a public API.
> It gives no authority for changes that are not in the specified product
> boundary.
> It gives no authority to change railway intent, exact validation, export,
> output, or the measurement profile.
>
> Exit 4 stays Pending. Exits 1 and 5 stay Pending. Phase 6 stays at 2/5
> accepted exits. Output stays private-development. Project status stays
> `unknown`.
>
> This decision gives no production, physical-output, `project-cleared`,
> packaging, release, or tagging authority. A subsequent decision at Level 3
> must admit the evidence before owner acceptance of Exit 4.

<a id="phase-6-exit-4-d-gov-009-panel"></a>

## Phase 6 Exit 4 D-GOV-009 panel

This Level 3 panel records D-GOV-009 at protected `main`
`bbc90531813415ca966131351f668256cdca838f`. D-GOV-009 follows D-GOV-008.
It does not change D-GOV-008. It does not change a retained comparison.

Phase 6 has 2/5 accepted exits. Exit 4 is Pending. Project status is `unknown`.

### Participants and independence

| Participant | Role | Independence |
| --- | --- | --- |
| TrackTemplate project owner | Is the panel chair and makes D-GOV-009 on 2026-08-23. | The owner gives authority. The owner does not accept the change. |
| Codex change owner | Gives the exact repository state, evidence classes, risks, and bounded documentation change. | The change owner does not accept its own work. |
| `/root/direction_alignment_review` | Gives a new read-only QA, risk, evidence, validation, and documentation review of the exact candidate. | The reviewer does not make the change and must report no blocking condition before merge. |

### Evidence classification

| Evidence class | Repository evidence | Decision use |
| --- | --- | --- |
| Current-cost evidence | The temporary D-GOV-008 profile measured 50 preview regenerations. It recorded approximately `3.263 ms` of process CPU time for one regeneration. For the 50 regenerations, it recorded `0.144` seconds of integration process CPU time and `0.163` seconds of preview-sampling process CPU time. | This evidence showed a cost in Edit. It did not show that the preview sampler was the main cost of the complete Edit journey. |
| Hypothesis-selection evidence | D-GOV-008 selected repeated zero-origin integration in the preview sampler. It fixed the product boundary and comparison rule before product work. | D-GOV-008 stays Accepted as the authority for that selection. |
| First retained negative evidence | Candidate `6e1a0c755d7872fe631332d4d1ce4330febdd81b` has a retained local branch. Its comparison has SHA-256 `044244345ea65b8a5ed99548be8f2f1f9f34537eddf813dbb7f92f9c4696f936`. | The Edit CPU paired median difference was approximately `-2.620 ms`. Edit CPU was lower in only 9 of 12 paired blocks. Twenty-two metrics had FAIL results. The review also found that the fast path had no length limit and did not keep the `1.0e-10` mm preview-oracle tolerance in the full product domain. The measured workload stayed in tolerance, but that result did not remove the domain defect. |
| Second retained negative evidence | The replacement comparison has SHA-256 `64c167b424fefe604ada0b66deb435eaa32e924ff09c2265a3f9f9569382874b`. Its classification has SHA-256 `f402ef196ef78f287357f5484b47505a31a2799c3e6b2160053b6ae927d3a110`. Its source diff has SHA-256 `73a236a44ce39d4ac8aace714dcac0e4c9f400bf030561718a9c77bf1301ec8b`. | All 24 samples had PASS validation results. The supported-domain error was `4.547473508864641e-13` mm and the large-scale scalar fallback was exact. Edit CPU was lower in only 5 of 12 paired blocks. The paired median difference was `+2.923202` ms. The candidate median was approximately 10.71% higher. Ten metrics had FAIL results. |
| Improvement evidence | No retained candidate has a PASS result for the fixed correctness, Edit CPU, complete-journey, and no-displacement conditions. | The two retained results are not improvement evidence. |
| Evidence for a new Level 2 optimisation | Current measurements do not report a result for each area: state construction, preview construction, Coin binding, GUI processing, and the remainder. | The evidence does not show sufficient cost in a measurement area outside the D-GOV-008 preview-sampler boundary. |
| Evidence for a decision to admit Exit 4 evidence | The two retained comparisons do not have PASS results. No Level 3 decision admits one of the two results for Exit 4. | Exit 4 stays Pending. |

The local branch `agent/phase6-exit4-preview-batch-performance` contains the
first candidate. The second candidate is preserved in the exact source diff
and in the snapshot with checksum PASS results
`2026-08-23-phase6-exit4-simpson-polynomial-failed-comparison-01`. The snapshot
also preserves the raw comparisons, classification, source files, branch refs,
and commit objects. The preservation audit mounted the USB snapshot read-only.
The audit checks showed content identity. The audit unmounted the snapshot.

Do not change this retained state as part of D-GOV-009. Do not publish it. Do
not merge it. Do not remove it.

### Direction assessment and next action

The two retained negative results are sufficient to stop new product work in
the D-GOV-008 direction. That direction is an exhausted performance direction
for current Phase 6 Exit 4 work. This decision does not claim that no numerical
method can give a PASS result. It stops a third product change after
the project knows the fixed results.

Do not make a third preview sampler, polynomial, approximation, cache, or other
variation of the D-GOV-008 hypothesis. No measured evidence shows sufficient
cost in a measurement area outside the D-GOV-008 preview-sampler boundary.

The next action is a bounded baseline-attribution investigation at Level 1. It
can measure the accepted FreeCAD 1.1.3 Edit journey. It can report a result for
each of these measurement areas if the architecture and the measurement method
let it do this:

1. Canonical-state and state-construction work
2. Preview and sampler construction
3. Coin binding or scene-graph replacement
4. GUI processing
5. The unattributed remainder.

The investigation is attribution only. Do not change product source. Do not
make a performance optimisation. Do not select a candidate after the project
knows the results.

Do not define a product performance budget. Do not run the first retained
comparison again. Do not run the second retained comparison again. Do not
accept Exit 4. Do not start that investigation in this cycle.

A subsequent Level 3 owner decision is necessary before a new Level 2
optimisation. That decision must use measured evidence for a measurement area
outside the D-GOV-008 preview-sampler boundary. It must select one bounded
architecture and product boundary. It must define the qualified host, baseline,
complete-journey comparison rule, no-displacement conditions, invariants, and
permitted files before product work starts.

### Risk panel

This Level 3 decision changes governance direction. This cycle makes no product
change. Thus, the governance change is larger than the product change.

| Risk | Panel judgement | Result |
| --- | --- | --- |
| PR-12 — stale or repeated direction | D-GOV-009 removes the instruction to repeat D-GOV-008. It gives one bounded attribution-only next action. | Medium / Mitigate / Partial. The disposition does not change. |
| PR-13 — repository or evidence loss | Exact commits, paths, hashes, the retained branch, and the USB snapshot preserve the two negative results. Post-merge checks must make sure that the two results do not change. | Critical / Mitigate / Effective for the current bounded scope. The disposition does not change. |
| PR-15 — deferred cost | The next investigation uses the accepted complete Edit journey and reports the unattributed remainder. It does not move product work to a different stage. | High / Mitigate / Partial. The disposition does not change. |
| PR-16 — incomplete cache signature | D-GOV-009 gives no authority for a cache. It makes no product change. | High / Mitigate / Partial. The disposition does not change. |
| PR-22 — authority transfer | The owner makes the exact D-GOV-009 decision. A new reviewer who did not make the change must examine the exact candidate before merge. | High / Remove / Effective for the current bounded scope. The disposition does not change. |
| QA-R04 — no product performance budget | The decision defines no budget and admits no performance improvement or Exit 4 evidence. | High / Mitigate / Partial. The disposition does not change. |

No risk state, treatment, severity, owner, deadline, or control effectiveness
changes. There is no dissent. The exact Edit cost in each
measurement area stays Unknown until the baseline-attribution
investigation. A new Level 2 optimisation has no authority until the owner
makes the subsequent decision.

### Documentation conformance

The documentation review uses the
[local Issue 9 source](../external/asd-ste100/README.md). This is the official
source. The review also uses the TrackTemplate UK English spelling directive.
It examines each full logical unit in this table.

| Path | Full logical unit |
| --- | --- |
| `reference/PERFORMANCE_SOP.md` | The full section with the heading `Phase 6 Exit 4 baseline-attribution direction`. |
| `reference/TERMINOLOGY.md` | The new performance-investigation row. |
| `reference/PROJECT_PLAN.md` | The current owner view, D-GOV-009 phase summary, and D-GOV-009 decision row. |
| `reference/current/PHASE_EVIDENCE.md` | This full D-GOV-009 panel, the changed Exit 4 disposition, and D-GOV-009 carried-control text. |
| `reference/current/gate-decisions.json` | The human-readable D-GOV-009 record. Exact JSON data is not part of the linguistic review. |

The internal result for the D-GOV-009 logical units is `ASD-STE100 Issue 9
conforming`. The review uses the technical nouns in the terminology register.

This result is a TrackTemplate conformance assessment. It is not external ASD
certification, endorsement, or an official conformance assessment. It does not
include exact machine data. It does not include unchanged live prose outside
the named logical units. It does not include frozen history. Issue 9
conformance stays Unknown for other live prose.

### Review and bounded conditions

The reviewer who did not make the change must examine the evidence classes and
the two retained negative results. The reviewer must examine preservation,
authority, risk panel, documentation, and validation results. The reviewer must
also make sure that the change does not start the baseline-attribution
investigation. The reviewer must make sure that the change does not admit Exit
4.

The reviewer must not change files. The project must not merge the candidate if
the reviewer finds a blocking condition. This panel must not change after the
exact-candidate review.

The Phase 6 performance owner owns the future attribution record. The project
owner owns a subsequent Level 3 candidate-selection decision. These two
conditions are necessary before a new Level 2 optimisation starts. The Phase 6
evidence owner must preserve the two retained negative results during Phase 6.
The owner must also preserve them during the subsequent release audit.

**Panel recommendation:** **Proceed with bounded conditions.** Record D-GOV-009
after D-GOV-008. Stop new product work in the D-GOV-008 direction.
Do not change the two negative results. Make the bounded Level 1
baseline-attribution investigation the next action. Keep Exit 4 Pending.

> **D-GOV-009 — Record the D-GOV-008 direction as exhausted and select baseline attribution**
>
> At protected `main` `bbc90531813415ca966131351f668256cdca838f`, I record
> D-GOV-009 after D-GOV-008. D-GOV-008 stays Accepted as the
> authority for the PR #50 baseline, first preview-sampler hypothesis, fixed
> comparison rule, and first bounded Level 2 work.
>
> Preserve the two subsequent Level 2 attempts as retained negative evidence.
> Candidate
> `6e1a0c755d7872fe631332d4d1ce4330febdd81b` failed the fixed comparison and
> did not keep the preview-oracle tolerance in the full product domain. The
> Simpson-polynomial replacement kept the supported numerical limit and
> exact fallback, but its fixed comparison also failed. The two results are not
> improvement evidence. They are not Exit 4 evidence.
>
> The two results are sufficient to stop new product work in the D-GOV-008
> direction. Do not make a third preview sampler, polynomial, approximation,
> cache, or other variation of that hypothesis. Current measurements do not
> show sufficient cost in a measurement area outside the D-GOV-008
> bounded preview-sampler work.
>
> The next action is a bounded Level 1 baseline-attribution
> investigation on the accepted FreeCAD 1.1.3 Edit journey. It can report
> canonical-state and state-construction work, preview and sampler construction,
> Coin binding or scene-graph replacement, GUI processing, and the unattributed
> remainder. Report a result for each measurement area if the method lets the
> investigation do this.
>
> The investigation is attribution only. Do not change product source. Do not
> make a performance optimisation. Do not select a candidate after the project
> knows the results.
>
> Do not define a product performance budget. Do not run the first retained
> comparison again. Do not run the second retained comparison again. Do not
> accept Exit 4. Do not start the investigation in this cycle.
>
> A subsequent explicit Level 3 owner decision is necessary before a new Level
> 2 optimisation. That decision must use measured evidence for a measurement
> area outside the bounded D-GOV-008 preview-sampler work. It must define the bounded
> product boundary. It must define the comparison rule before product work
> starts.
>
> Phase 6 stays at 2/5 accepted exits. Exit 4 stays Pending. Exits 1 and 5 stay
> Pending. Project status stays `unknown`. No risk disposition changes.
>
> This decision changes no product source, public API, railway mathematics,
> persistence, export behaviour, performance threshold, qualified host profile,
> or retained evidence. It gives no production authority, physical-output
> authority, `project-cleared` status, packaging, release, or tagging authority.

<a id="freecad-1-1-3-py31313-qt6111-qualification-panel"></a>

## Qualification panel and owner decision for the new exact FreeCAD 1.1.3 host profile

This Level 3 panel uses protected `main`
`dc750df93682b3b0fd5fdf79fa6fe94296a10697` as its source state. It changes
host-compatibility authority. It also changes the related host controls. It
changes no TrackTemplate product source. Phase 6 has 2/5 accepted exits, and
Exit 4 is Pending. Project status is `unknown`.

### Owner view

| Field | Result |
| --- | --- |
| Current state | The exact FreeCAD 1.1.1 profile and the D-GOV-006 exact FreeCAD 1.1.3 profile are qualified. D-GOV-009 is the current Exit 4 direction. |
| What changed | D-GOV-010 qualifies only the profile for FreeCAD 1.1.3 that has CPython 3.13.13 and PySide6/Qt 6.11.1. It preserves the previous profiles and their evidence. |
| What now works | The runtime guard and the host matrix gave the specified results for the profile that D-GOV-010 qualifies. This profile can supply candidate evidence for performance in a subsequent cycle. Each comparison must use one profile with an exact identity. |
| Limitations/findings | The runtime guard does not examine the data about the Flatpak package that the contract records. Qualification gives no authority for a performance comparison between profiles that have different exact identities. This cycle records no performance result. |
| Owner decision | Accept D-GOV-010 for `linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1` only. Keep the previous qualified profiles and evidence. |
| Next action | In a new cycle, do the bounded investigation that D-GOV-009 specifies. Use the profile that D-GOV-010 qualifies. First, record a baseline for this profile. This qualification cycle does not start that investigation. |

### Exact host identity and runtime-guard limits

The candidate host reported this identity:

| Component | Recorded value | Contract use |
| --- | --- | --- |
| Operating system | Linux Mint 22.3, x86_64 | Linux and x86_64 are `exact_match` data. The Mint release is recorded provenance. |
| FreeCAD | 1.1.3, revision `44987 (Git)`, Git commit `145529fe741292ff0b3977a01195bf0247425794` | The version is `exact_match` data. The revision and Git commit are recorded provenance. |
| Flatpak package | `org.freecad.FreeCAD`, ref `app/org.freecad.FreeCAD/x86_64/stable` | The Flatpak ID and package type are `exact_match` data. The ref is recorded provenance. |
| Flatpak commits | Commit `fa3ef6bebc139083246bd4fb6b8baf6a032a3b5bbb0a57479cb14d52bad733ae`, parent `d7a54c855bce9f4fb7b00b33d43f0ecb1908af510f9147bcc9bc32f614a6bbad` | Recorded provenance. |
| Flatpak runtime and SDK | `org.kde.Platform/x86_64/6.11` and `org.kde.Sdk/x86_64/6.11` | Recorded provenance. |
| Flatpak source | Origin `flathub`, collection `org.flathub.Stable`, system installation | Recorded provenance. |
| Python | CPython 3.13.13 | `exact_match` data. |
| Qt binding | PySide6 6.11.1 with Qt 6.11.1 | `exact_match` data. |
| Geometry kernel | OpenCASCADE 7.8.1 | `exact_match` data. |
| Scene-graph library | SIM Coin 4.0.8 | `exact_match` data. |

The exact profile ID is
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`. The runtime guard
accepts this profile only when all of its `exact_match` data are equal to the
reported data. The runtime probe does not report the Flatpak ref, commits,
runtime, SDK, origin, or collection. It also does not report installation
details, the Mint release, or the FreeCAD revision.

Those data preserve the package provenance. They do not change the runtime
guard. They do not qualify a different Flatpak package.

### Qualification evidence

The assessment used a temporary worktree at the protected source state. Its
temporary contract added only the profile with the new ID. Each FreeCAD command used
a new document or a fixture copy. The source fixture SHA-256 was
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` before
and after the real-GUI routes.

| Evidence area | Validator or command | Result |
| --- | --- | --- |
| Exact runtime identity | `tools/runtime_compatibility_probe.py --pass --require-qualified` in FreeCADCmd | PASS. The probe reported only the profile that D-GOV-010 identifies and zero mismatches. |
| Package load, modular route, canonical state, and recompute | Phase 2, Phase 3, and Phase 4 FreeCADCmd validators | PASS with all specified sentinels. |
| Transactions, Undo/Redo, save/reopen, failure recovery, and cleanup | Phase 4 persistence validator | PASS with its specified sentinel. |
| Legacy ingress, family assessment, migration, and chair import | Phase 4 FreeCADCmd validators | PASS with all specified sentinels. |
| Coin scene and Edit lifecycle | Phase 5 headless validators | PASS with both specified sentinels. |
| Display, selection, Edit, Undo/Redo, save/reopen, failure recovery, and cleanup | Phase 5 real-GUI ViewProvider command | PASS with the specified real-GUI records and zero open documents after cleanup. |
| Plain-line and connected-straight Entry/Exit routes | Phase 3 four-route real-GUI command | PASS. Legacy and modular results were equal for both workflows. |
| Exact contract and transient exact geometry | Phase 6 FreeCADCmd validators | PASS with both specified sentinels. |
| Deterministic DXF, manifest, import, failure recovery, and cleanup | Phase 6 qualified DXF validator | PASS with its specified sentinel. |

The preserved detailed evidence is in
`benchmark-output/freecad113-requalification/20260823T171357Z-fa3ef6/`.
The runtime evidence file has SHA-256
`eff5df685a7b37b98cb23a2f853f186aa03a014bda0d2ac19754b8d8fa296e88`.
The evidence file for the headless matrix has SHA-256
`fcc98740aaaea626541d095f35d18e98a4b9bff72ce0968d71a5370e83f36865`.
The evidence file for the real-GUI ViewProvider has SHA-256
`0c06db37b9bdab8114fe600b34dd62a3beb7af1adc2edc8622fe1eff006fded3`.
The four-route evidence file has SHA-256
`e8bb482506b81ff0e328ffb64f3c37de820fe7a171e8247c866c2d1c38edaf77`.
The external-file SHA-256 manifest has SHA-256
`16fa438aba7fa967a134241087239a86c14f65a03ad48ea20ef086910cb80713`.

The first migration command in the real GUI stopped before the validator. The command
did not define `__file__`, and the validator reported a
`NameError`. This result is `fixture-or-harness-defect`. Its evidence file has SHA-256
`a4e7168492056439f78dde745b541dc778c82879ef5b8ef3f4568683a60bd54a`.
The new command file defines the validator path. It has SHA-256
`d132f439fd0a1f144f2891d2789bbb0cdebe376500c1fb62508d90113cc09cca`.

The subsequent proof gave PASS and has SHA-256
`adc996312467c3bb821f04f88024e62983418aae5b7977760a3612edb337c25b`.
The first command gave no qualification result and changed no product file.

### Preservation, architecture, and performance limits

The assessment status has SHA-256
`bab8889d4e0e920bf5c72fbda11a2d925c86385e450da689dd0730aa8a831306`.
The temporary source change has SHA-256
`6df27b7a89079588dfa5ca513ba7df42a7967edfb7ddf3c2eabad1fa017a78c7`.
The project recorded SHA-256 for these records and the external files. It
then removed the temporary worktree. The primary worktree stayed at the
protected source state during the host assessment.

The public API, railway state, persistence data, schemas, stored identifiers,
output contracts, and exact output do not change. The runtime
evaluator accepts a list of exact profiles. The host validators add one
profile ID. The Phase 5 GUI command now maps FreeCAD 1.1.3 to the IDs
of the two qualified profiles. No TrackTemplate product source changes.

D-GOV-006 and its exact CPython 3.13.14 and PySide6/Qt 6.10.3 profile do not
change. The exact FreeCAD 1.1.1 profile and its evidence do not change.
D-GOV-007 authority for its two named profiles does not change.
D-GOV-010 authorises this profile to supply candidate evidence for performance
in a subsequent cycle. Each comparison must use one profile with an exact
identity.

The performance records for the 1.1.1 and D-GOV-006 profiles stay frozen under
their exact provenance. A
result from one exact profile is not a TrackTemplate before/after comparison
with a result from a different exact profile. This cycle records no performance
measurement, comparison, or budget. This cycle makes no new measurement from
either D-GOV-008 result. Both results are retained negative evidence. Their
commits, files, failure records, and hashes do not change.

D-GOV-009 stays the current Exit 4 direction. Before the project claims that
TrackTemplate performance changed on this profile, the D-GOV-009 investigation
must record a baseline for this profile. This qualification does not start that
investigation. It does not select an optimisation candidate and does not accept
Exit 4.

### Risk panel

| Risk | Panel judgement | Result |
| --- | --- | --- |
| PR-01 — release workflow coverage | The host matrix gave the specified results for the current B16 constraints. Phase 10 still owns Workbench package and release evidence. | High / Remove / Partial. The disposition does not change. |
| PR-13 — repository or evidence loss | The source state, temporary source change, evidence files, and hashes preserve the assessment. Post-merge checks must examine them. The checks must also examine the retained negative evidence from D-GOV-008. | Critical / Mitigate / Effective for the current bounded scope. The disposition does not change. |
| PR-17 — persistence or migration corruption | Headless and real-GUI checks examined fixture copies, transactions, Undo/Redo, save/reopen, failure recovery, and cleanup. | Critical / Mitigate / Partial. The disposition does not change. |
| PR-22 — authority transfer | The project owner gives exact Level 3 authority. A new reviewer who did not make the change must examine the exact candidate before merge. | High / Remove / Effective for the current bounded scope. The disposition does not change. |
| QA-R03 — release GUI evidence | The exact host has real-GUI qualification evidence. The project does not have release or Workbench package evidence. | High / Remove / Partial. The disposition does not change. |
| QA-R04 — no product performance budget | D-GOV-010 records no performance result or budget. It keeps the rule that a comparison uses one exact host profile. It does not change D-GOV-009. | High / Mitigate / Partial. The disposition does not change. |

No risk state, treatment, severity, owner, deadline, or control effectiveness
changes.

### Documentation conformance

The conformance review must use the official local ASD-STE100 Issue 9
standard and the TrackTemplate UK English spelling directive. It must examine
each full logical unit in this table.

| Path | Full logical unit |
| --- | --- |
| `reference/PROJECT_PLAN.md` | The current owner view, D-GOV-010 summary, and D-GOV-010 decision row. |
| `reference/VALIDATION.md` | The Phase 1 runtime and legacy ingress compatibility unit. |
| `reference/PERFORMANCE_SOP.md` | The full section with the heading `Hosts for Phase 6 performance evidence`. |
| `reference/contracts/phase1-compatibility.json` | The changed human-readable status, bounded scope, profile, qualification, support, and evidence strings. Exact JSON data is not part of the linguistic review. |
| `reference/current/PHASE_EVIDENCE.md` | This full D-GOV-010 panel, the Exit 4 disposition addition, and the D-GOV-010 carried-control text. |
| `reference/current/gate-decisions.json` | The human-readable D-GOV-010 record. Exact JSON data is not part of the linguistic review. |

Before the conformance review, the Issue 9 result for these logical units is
Unknown. The conformance review must examine the exact candidate. Exact identifiers,
JSON keys, commands, hashes, and machine values are not part of the linguistic
review. Issue 9 conformance stays Unknown for frozen history and for live prose
that is not in the named logical units.

### Review and merge conditions

A new reviewer did not make the change. This reviewer must examine the exact
host identity, host matrix, failure disposition, and preservation. The reviewer must
examine the bounded work, risk panel, documentation, and validation results.
The reviewer must also make sure that the change does not start D-GOV-009
baseline attribution. The reviewer must make sure that the change does not
admit a performance result or Exit 4.

The reviewer must not change files. The project must not merge the candidate
after a BLOCK review result. This panel must not change after the exact-state
review.

**Panel recommendation:** **Continue with bounded conditions.** Qualify only the
profile that D-GOV-010 identifies. Keep the two previous profiles qualified.
Preserve all evidence. Keep D-GOV-009 as the current Exit 4 direction.
Keep Exit 4 Pending.

> **D-GOV-010 — Qualify the new exact FreeCAD 1.1.3 host profile**
>
> At protected `main` `dc750df93682b3b0fd5fdf79fa6fe94296a10697`, I
> qualify only
> `linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`. This profile has
> FreeCAD 1.1.3, revision `44987 (Git)`, Git commit
> `145529fe741292ff0b3977a01195bf0247425794`, and CPython 3.13.13. The profile
> also has PySide6/Qt 6.11.1, OpenCASCADE 7.8.1, and SIM Coin 4.0.8.
>
> The recorded Flatpak commit is
> `fa3ef6bebc139083246bd4fb6b8baf6a032a3b5bbb0a57479cb14d52bad733ae`.
> The runtime is `org.kde.Platform/x86_64/6.11`. The contract records the
> package identity and the provenance fields in this panel. The runtime guard
> qualifies the profile only from its `exact_match` data. It does not qualify
> all FreeCAD 1.1.3 hosts.
>
> Keep the exact FreeCAD 1.1.1 profile qualified. Keep the D-GOV-006 exact
> FreeCAD 1.1.3 profile qualified. Preserve their evidence and exact host
> identities. Do not change D-GOV-006 or D-GOV-007.
>
> D-GOV-010 authorises this profile to supply candidate evidence for performance
> in a subsequent cycle. Each comparison must use one profile with an exact
> identity. For a TrackTemplate before/after comparison, do not use results from
> profiles with different exact identities.
> Before the project claims that TrackTemplate performance changed on this
> profile, the D-GOV-009 investigation must record a baseline for this profile.
>
> This decision admits no performance result. It defines no performance budget.
> It does not start baseline attribution. It does not select an optimisation
> candidate. It does not accept Exit 4.
>
> This decision changes no product source, public API, railway mathematics,
> persistence, schema, export behaviour, qualified-host criterion, performance
> threshold, or evidence. It gives no production authority,
> physical-output authority, `project-cleared` status, packaging, release, or
> tagging authority.
>
> Phase 6 stays at 2/5 accepted exits. Exit 4 stays Pending. Exits 1 and 5 stay
> Pending. Project status stays `unknown`. No risk disposition changes.

<a id="phase-6-exit-4-d-gov-011-direction-selection-panel"></a>

## Phase 6 Exit 4 D-GOV-011 direction-selection panel

This Level 3 panel uses protected `main`
`bd0c87a9e1c034e538d1cda5f978d305fa0cfaa2` as its source state. D-GOV-011
follows D-GOV-009 and D-GOV-010. It changes performance direction only. It
changes no product source. Phase 6 has 2/5 accepted exits, and Exit 4 is
Pending. Project status is `unknown`.

### Owner view

| Field | Result |
| --- | --- |
| Current state | D-GOV-009 records the preview-sampler direction as exhausted. D-GOV-010 qualifies the exact host for this evidence. The D-GOV-009 attribution record is completed and preserved. |
| What changed | D-GOV-011 selects one subsequent hypothesis for the measured canonical area of Edit. The product boundary is one adapter file. |
| What now works | The retained measurement and source assessment identify two repeated reads of the selected record. A product change can remove these reads from the measured canonical area. |
| Limitations/findings | The attribution noise floor is `2.895891 ms`. The first quartile of the canonical area was only `0.0731425 ms` higher than that floor. The evidence does not report the cost of each operation in that area. This result is not improvement evidence or Exit 4 evidence. |
| Owner decision | Accept D-GOV-011. Authorise one subsequent product change at Level 2 in the named adapter file. The change reads the selected record one time before the write and uses that state again. |
| Next action | In a new cycle, first record a new same-host baseline on the D-GOV-010 host. The attribution materiality rule in D-GOV-009 must give a PASS result for the canonical area. If it does not, stop before product work. Do not start the product change in this cycle. |

### Attribution-evidence preservation

Before a repository change, the preservation audit examined the source state
and the ignored evidence. The primary worktree was clean `main`. Local `main`,
`origin/main`, and live protected `main` were equal at
`bd0c87a9e1c034e538d1cda5f978d305fa0cfaa2`. The repository had one registered
worktree.

The 77-entry `SHA256SUMS` check had a PASS result. These retained records also
had the specified SHA-256 results:

| Retained record | SHA-256 |
| --- | --- |
| Pre-registered method | `8e47cb21e4aa8fe4ec1706b60d0ec1c665e3a338d626e7d99fd62e105a31ba22` |
| Test-owned instrumentation | `196060f8d22ac3dcebec720beb77e779534d4371f1212e3da0849ee3f9826568` |
| Attribution collector | `9695a0d279a4f1472fcfd676a310a66382a0350b05b58b70a215d31cf9f0eee9` |
| Attribution result | `02525791c17fa5630be57608543b7c0dfa3c7254cc22c623ff79c007e0a94880` |
| New same-host baseline | `9928501e6460b68742f441f497be602de10596e33d772a65245efa1ee2549c71` |
| Retained baseline attempt 1 | `f706b4405db524d87bc50bfb36579482450ffa137c84546a502d66354a959d5c` |
| Fixture-failure classification | `8414286cf783789afc5c079541438e1ff129c9e012163396842bc1607ea33aee` |
| Checksum manifest | `52f141c5c45a9c5752d93d70aece9943e7b535bfde0804c53fc7b5d2cbad6388` |

The preservation audit made a new snapshot on the accepted backup device. This
is a different physical device. The snapshot name is
`2026-08-23-phase6-exit4-attribution-preservation-01`. The snapshot contains
6,519 files and 1,244 directories.

Its Git HEAD is `bd0c87a9e1c034e538d1cda5f978d305fa0cfaa2`. A byte check
found no difference between the source and snapshot in the declared bounded
scope. The 77-entry manifest had a PASS result in the snapshot. The audit
completed all writes to the device. The operating system then stopped its
connection to the device file system before the repository change.

The snapshot does not replace the retained negative-evidence snapshots. It
does not change an evidence file. It does not publish ignored evidence.

### Measurement result and area

The attribution record uses only
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`. D-GOV-010 qualifies
this exact host profile. The record uses clean `main`
`bd0c87a9e1c034e538d1cda5f978d305fa0cfaa2`. The retained source hashes are
equal to the current files at that source state.

The baseline series has 10 processes. The attribution series also has 10
processes. Each process starts FreeCAD. The accepted workload
has one Entry/Exit pair. It edits the selected Exit from `420.000 mm` to
`360.000 mm`. All correctness, deterministic-output, lifecycle, cleanup, and
host-identity checks had PASS results.

| Measurement area | Median for process CPU time | First quartile | Result use |
| --- | ---: | ---: | --- |
| Full Edit baseline | `29.571971 ms` | `21.0001125 ms` | Current-cost evidence only. |
| Canonical state and state construction | `3.126380 ms` | `2.9690335 ms` | Direction-selection evidence. |
| Preview and sampler construction | `1.9991765 ms` | `1.95987775 ms` | D-GOV-008 direction stays exhausted. |
| Coin or scene-graph work | `0.3987415 ms` | `0.38801125 ms` | The attribution materiality rule gave a FAIL result. |
| GUI processing | `20.109802 ms` | `19.804105 ms` | The TrackTemplate product boundary is Unknown. |
| Unattributed remainder | `2.5621155 ms` | `2.40463225 ms` | The evidence identifies no architecture area. |

The attribution noise floor is `2.895891 ms` of process CPU time. The
first quartile of the canonical area is `0.0731425 ms` higher than that floor.
The median of the calibrated instrumentation overhead is `0.01776712815 ms` of
process CPU time. Its maximum is `0.0187707963 ms`. The baseline and attribution
series are not paired.

Their median differences are `-1.0994865 ms` for process CPU time
and `+22.4718825 ms` for wall time. These values are method and noise
information. They are not a TrackTemplate before/after comparison.

The measured canonical area is the application span for
`tracktemplate/application/transition_edit.py::edit_transition_length_mm`. It
includes the FreeCAD transaction and property writes in
`tracktemplate/adapters/freecad/transition_state.py`. The measurement subtracts
the preview and ViewProvider refresh that occur in the application span. It
does not include Coin work or the two calls for GUI processing that the method
names.

### Read-only assessment of source and architecture

The assessment examined these operations in the measured canonical route:

1. The application command examines the length and makes replacement intent.
2. The application command calculates the current canonical analysis.
3. The edit port examines the stale edit base.
4. The store examines the current state, stable identity, and object mapping.
5. The store makes and compares the replacement JSON payload.
6. The FreeCAD transaction writes the canonical payload and then reads it.

The accepted Entry/Exit workload has two canonical records. For its selected
record, `apply_transition_edit` calls `read_transition_object` before the
write. `_update` then calls `read_transition_object` for that record. The
object-mapping scan calls it for the selected record for a third time. Each
call examines the live object, its record envelope, its JSON payload, its
schema, and its analysis data.

The read after the write is necessary for the write check. The scan of the
other canonical record is necessary for duplicate-identity rejection. The
FreeCAD transaction and the property write are necessary for persistence and
one-unit Undo/Redo. The preview refresh in that span is not part of the measured
canonical area.

The application command calculates a target offset from the new length. It
then calculates the canonical length from that offset. A product change must
not replace the accepted calculation with the input length. That change can
change canonical JSON and the deterministic result. Thus, it is not an
authorised performance hypothesis.

The assessment identifies only one hypothesis from the measured cost,
identified operation, and architecture. Keep one live read of the selected
record before the write. Use its state for the stale-base and stable-identity
checks. During object mapping, use the same state for the selected object. This
removes two repeated reads of all selected-record data from the measured Edit
route. It adds no replacement work in a different stage.

The hypothesis has a different product boundary from D-GOV-008. It changes
only the read route in the canonical FreeCAD adapter. It changes no preview
sampler, railway calculation, polynomial, approximation, cache, Coin route, or
GUI processing.

### Product boundary and comparison rule

The only permitted product file is
`tracktemplate/adapters/freecad/transition_state.py`. Directly dependent tests
and ignored performance evidence can change only when they are necessary for
this hypothesis. Do not change a public API or persistence schema. Do not
change `tracktemplate/application/transition_edit.py` or a preview, Coin, GUI,
exact-validation, export, or railway-mathematics file.

The subsequent product change must keep one live read before the write. It must
keep the `stale-edit-base` diagnostic. It must keep duplicate-identity and
object-mapping checks. It must keep the read after the write. It must not move
a record read to selection, setup, teardown, preview, Coin, or GUI processing.

Before product work, do the exact attribution method in D-GOV-009 again on clean
protected main. Use only the exact D-GOV-010 host. Record a new baseline
series of 10 processes and a new attribution series of 10 processes. The
attribution materiality rule in D-GOV-009 must give a PASS result for the
canonical measurement area. If it does not, stop before product work.

The subsequent cycle at Level 2 must record the 12-block sequence before
product work. Six blocks use the baseline first. Six blocks use the candidate
first. Each sample uses a new process and the full accepted journey.

The subsequent comparison uses the rule in
[the canonical-record direction](../PERFORMANCE_SOP.md#phase-6-exit-4-canonical-record-direction).
Process CPU time for Edit must be lower in at least 10 of 12 paired blocks. Its
median paired difference must be negative. Edit wall time and cold-journey CPU
and wall time must have negative median paired differences.

Apply the D-GOV-008 no-displacement rule to Validate, Export, cleanup, warm
block values, resource metrics, and the journey remainder. Apply it also to
preview and sampler construction, Coin or scene-graph work, GUI processing,
and the unattributed remainder. Record these measurement areas in both samples
of each paired block. Use the same test-owned instrumentation in both samples.
Record its overhead. A missing condition, host difference, product defect, or
invariant difference gives FAIL.

The candidate must preserve canonical state, transaction semantics, and one-unit
Undo/Redo. It must preserve identity, mapping, preview, Coin, persistence,
lifecycle, cleanup, exact validation, deterministic export, diagnostics, and
failure recovery. It must add no work to an unmeasured boundary.

### Risk panel

This Level 3 cycle changes governance direction. It makes no product change.
Thus, the governance change is larger than the product change.

| Risk | Panel judgement | Result |
| --- | --- | --- |
| PR-12 — stale or repeated direction | D-GOV-011 selects one measured and bounded hypothesis. It gives no authority to divide the route into more areas or to select a different candidate. | Medium / Mitigate / Partial. The disposition does not change. |
| PR-13 — repository or evidence loss | The checksum manifest and the new snapshot on a different physical device preserve the ignored attribution corpus before the repository change. The retained D-GOV-008 snapshots do not change. | Critical / Mitigate / Effective (current bounded scope). The disposition does not change. |
| PR-15 — deferred cost | The subsequent rule measures full Edit and all other areas. It gives FAIL if the candidate moves cost to a different stage or an unmeasured boundary. | High / Mitigate / Partial. The disposition does not change. |
| PR-17 — persistence or migration corruption | The only permitted product file is the canonical FreeCAD adapter. The transaction, identity, save/reopen, Undo/Redo, recovery, and cleanup checks stay necessary. | Critical / Mitigate / Partial. The disposition does not change. |
| PR-22 — authority transfer | The project owner makes D-GOV-011. A reviewer who did not make the change must examine the exact candidate before merge. | High / Remove / Effective (current bounded scope). The disposition does not change. |
| QA-R04 — no product performance budget | D-GOV-011 defines a comparison rule but no product performance budget. It admits no improvement or Exit 4 evidence. | High / Mitigate / Partial. The disposition does not change. |

No risk state, treatment, severity, owner, deadline, or control effectiveness
changes. The size of a subsequent improvement is Unknown. The hypothesis can
fail the comparison of the full journey.

### Documentation conformance

The documentation review uses the
[local Issue 9 source](../external/asd-ste100/README.md). This is the official
source. The review also uses the TrackTemplate UK English spelling directive.
It examines each full logical unit in this table.

| Path | Full logical unit |
| --- | --- |
| `reference/PERFORMANCE_SOP.md` | The baseline-attribution section in D-GOV-009 and the canonical-record direction in D-GOV-011. |
| `reference/TERMINOLOGY.md` | The changed canonical authority, assurance result, performance, attribution, and technical verb rows. |
| `reference/PROJECT_PLAN.md` | The current owner view, the phase summaries for D-GOV-009 and D-GOV-011, and the D-GOV-011 decision row. |
| `reference/current/PHASE_EVIDENCE.md` | This full D-GOV-011 panel, the changed Exit 4 disposition, and D-GOV-011 carried-control text. |
| `reference/current/gate-decisions.json` | The human-readable D-GOV-011 record. Exact JSON data is not part of the linguistic review. |

The internal result for the D-GOV-011 logical units is `ASD-STE100 Issue 9
conforming`. The review uses the technical terms in the terminology register.

This result is a TrackTemplate conformance assessment. It is not external ASD
certification, endorsement, or an official conformance assessment. It does not
include exact machine data. It does not include live prose that this cycle does
not change. It does not include frozen history. Issue 9
conformance stays Unknown for other live prose.

### Review and merge conditions

The reviewer who did not make the change must examine the preserved evidence,
measurement rule, source assessment, and selected hypothesis. The reviewer must
examine the permitted file, risk panel, documentation, and validation results.
The reviewer must make sure that the candidate starts no product change. The
reviewer must make sure that the candidate does not admit Exit 4.

The reviewer must not change files. The project must not merge the candidate
after a BLOCK review result. This panel must not change after the exact-state
review.

**Panel recommendation:** **Proceed with bounded conditions.** Record
D-GOV-011. Authorise one subsequent product change at Level 2 in the specified
adapter file. First record the new same-host baseline. Keep Exit 4 Pending.

> **D-GOV-011 — Select one canonical-record performance hypothesis**
>
> At protected `main` `bd0c87a9e1c034e538d1cda5f978d305fa0cfaa2`, I
> accept the retained attribution result in D-GOV-009 as direction-selection
> evidence only. The exact D-GOV-010 host is
> `linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`.
>
> The median for process CPU time in the canonical measurement area is `3.126380 ms`.
> Its first quartile is `2.9690335 ms`. This is only `0.0731425 ms` higher
> than the attribution noise floor, which is `2.895891 ms`. This result
> is not improvement evidence. It is not Exit 4 evidence.
>
> I select one performance hypothesis. Read the selected canonical record one
> time before the write. Use that state for the stale-base and stable-identity
> checks. During object mapping, use the same state for the selected object.
> Keep the scan of other canonical records. Keep the read after the write.
>
> The only permitted product file is
> `tracktemplate/adapters/freecad/transition_state.py`. Directly dependent
> tests and ignored performance evidence can change only when they are
> necessary for this hypothesis. Do not change a public API, persistence
> schema, railway calculation, preview sampler, Coin route, GUI route, exact
> validation, or export.
>
> Before product work, record a new ten-process baseline and ten-process
> attribution series on the exact D-GOV-010 host. The attribution materiality
> rule in D-GOV-009 must give a PASS result for the canonical area. If it does
> not, stop before product work. Record the 12-block sequence before product
> work.
>
> Process CPU time for Edit must be lower in at least 10 of 12 paired blocks. Its
> median paired difference must be negative. Edit wall time and cold-journey
> CPU and wall time must have negative median paired differences.
>
> Apply the D-GOV-008 no-displacement rule to all non-target stages, warm block
> values, resource metrics, and the journey remainder. Apply it to the other
> Edit measurement areas in D-GOV-009. The candidate must add no work to an
> unmeasured boundary.
>
> Preserve canonical state and transaction semantics. Preserve one-unit
> Undo/Redo, identity, mapping, preview, Coin, persistence, lifecycle, cleanup,
> exact validation, deterministic export, diagnostics, and failure recovery.
>
> I authorise one subsequent product change at Level 2 in this adapter file. Do
> not start it in this cycle. Preserve D-GOV-008, D-GOV-009, D-GOV-010, the two
> retained negative results, and the attribution corpus.
>
> This decision makes no product change. It admits no performance result. It
> defines no product performance budget. It does not accept Exit 4.
>
> Phase 6 stays at 2/5 accepted exits. Exit 4 stays Pending. Exits 1 and 5 stay
> Pending. Project status stays `unknown`. No risk disposition changes.
>
> This decision gives no production authority. It gives no physical-output
> authority. It gives no `project-cleared` status. It gives no packaging,
> release, or tagging authority.

<a id="visible-recovery-state-workflow-migration"></a>

## Workflow migration for visible recovery state

The start state for this Level 2 workflow migration is **protected main** at
SHA `65409493d741a5606543bd437e519f8efefb8680`. It changes the recovery policy,
agent routing, and semantic control validation only. The product and current
state do not change.

A stash with the recovery label
`codex-temporary-project-progression-recovery` stayed after TrackTemplate put
its work in named Git state. Merge commit
`dd768006c83b9bc26e3d2e6d6e13b2cebed40173` on `main` contained that state.
Parent commit 2 is `6f88f5c522f089e33dc895ca00adaf1035604b0b`.
The stash commit SHA was `3dc9e7fcb0596752bcd2bd39a2dfee2d0f31e9c0`.
The stash topology was B/I/W/U:

| Component | Commit identity | Tree identity | Reconciliation result |
| --- | --- | --- | --- |
| B | `397ad614cfc1764a7ca94b0705c6e448eba5b78a` | `bf9f53c37c20690572a3970a78fa56a46a26ae12` | B contains the initial tree |
| I | `865037c60a47eb7428d0881de2c1df3aa92d67be` | `bf9f53c37c20690572a3970a78fa56a46a26ae12` | B and I have the same tree |
| W | `3dc9e7fcb0596752bcd2bd39a2dfee2d0f31e9c0` | `cff63f011ddbe3bd7e762121b0a817fe4a5684bd` | The tree difference between B and W contained 7 changed paths in Git |
| U | `2416cd8cd81d2a38a570b45c9d871f5a0d287e92` | `5ef7ee84959ccb15c7ca20c447f3268eb488285c` | U contains 4 files |

TrackTemplate compared each path with commit
`6f88f5c522f089e33dc895ca00adaf1035604b0b` and merge commit
`dd768006c83b9bc26e3d2e6d6e13b2cebed40173`. Those commits contain the workflow
that `main` uses. The files in those commits have different bytes from some
stash blobs.

The accepted
[2026-08-01 repository snapshot](../backup-records/2026-08-01-phase5-closeout-snapshot.md)
includes Git. It is the approved independent preservation for each identified
Git object. The stash had no repository information that named state or
approved preservation did not contain.

Before disposition,
`stash@{0}` identified the same stash commit and stash inventory. The project
owner gave authority for that stash only. The next stash inventory was empty.
The disposition changed no other stash.

The recovery policy routes planned preservation and handoff to named Git
state. An emergency stash stays temporary. While the stash inventory contains
an emergency stash, the recovery gate does not have a complete result.
Stash reconciliation examines the B/I/W/U topology and each tree difference.
It validates the stash selector and stash inventory again.
It does this before a disposition with applicable authority.

The inspection after disposition found no stash inventory or `refs/stash`. It
did not change Git. Git has the B/I/W/U commits although the stash inventory is
empty. The W tree contains 7 workflow and validation paths. The U tree
contains 4 `.agents/skills/` paths.

Named Git state contains all these paths. No current record identifies these
Git objects as sensitive evidence or local evidence. Thus, current evidence
identifies no incident with sensitive evidence or local evidence in this
repository.

After this migration, a recovery task must examine these Git objects. The
recovery task must use `$tracktemplate-security-review`. The recovery policy
records that stash disposition does not remove Git objects.

This migration does not define a procedure to remove Git objects. It does not
define a procedure to replace a repository. It does not change independent
preservation. It gives no authority for automatic removal of Git objects. It
gives no authority for an operation that removes Git objects.

### Stash reconciliation

During independent review, a command made an emergency stash
`e52bd0409feee7dc7dce9fc853a3bed99081c948` by accident. The project owner was
the stash owner for this recovery cycle. Its recovery purpose was to preserve
the exact candidate in the Git index after the review accident.

The stash topology was B/I/W with no U parent:

| Component | Commit identity | Tree identity | Reconciliation result |
| --- | --- | --- | --- |
| B | `65409493d741a5606543bd437e519f8efefb8680` | `184b32f6a917287caa15349226eac238ebb54557` | B contains protected `main` at the cycle start |
| I | `bcc5fcca5a794d563a2a7ce9ec06732c04fff40c` | `6bd1b9aed0384d6007fc25e0509794fed41b5726` | I contains the exact candidate from before the accident |
| W | `e52bd0409feee7dc7dce9fc853a3bed99081c948` | `6bd1b9aed0384d6007fc25e0509794fed41b5726` | I and W have the same tree |
| U | None | None | The stash has no untracked-files parent or U tree and no other file |

TrackTemplate put the B/I/W state in the named worktree. Validation completed
before commit `1ca5b2d12ca2a2400b86126842c988b934d16194`. That commit has tree
`fcefb947aa1287ff3f9438ffa37081064a436093` and contains all 18 paths in this
change. Commit `1ca5b2d12ca2a2400b86126842c988b934d16194` and the W tree have
the same blobs at 14 of the 18 paths. These 4 paths contain the Rule 5.2 repair
that the owner authorised, its test changes, and this accident evidence:

- `reference/LEARNING_FROM_EXPERIENCE.md`
- `reference/RECOVERY_AND_BACKUP.md`
- `tests/validate_governance_semantics.py`
- `tests/validate_recovery_controls.py`

Before disposition, `stash@{0}` identified
`e52bd0409feee7dc7dce9fc853a3bed99081c948`. The stash inventory did not change.
It was the only stash. It had no untracked-files parent. The owner authority
applied only to this exact stash. The `git stash drop stash@{0}` result
identified this exact SHA.

The next stash inventory was empty. The next Git check found no `refs/stash`.
The named branch commit did not change. The disposition changed no other stash.

At disposition time, the named commit was local. The owner instruction gave
authority for this exact stash. This evidence does not show recovery if the
local repository is not available before publication.

Parse validation for Python and FCMacro files gave PASS for 189 files in Git.
The standalone CI result was PASS for 60/60 validators. The governance mutation
result was `271/271 rejected, zero escaped`. Validation for recovery, agent
routing, documentation review, LFE, repository QA, and the STE source and
derived cache gave PASS.

The initial independent review gave a `BLOCK` result for Level 2 evidence,
stash commit SHA controls, Issue 9 review, and wording that makes the procedure
fail closed. This change
corrects each finding. New independent reviews of this change are necessary
before publication.

This migration adds one control for PR-13. The state and disposition of PR-13
do not change. This entry does not change the canonical owner for recovery or
give authority to remove Git state.

Phase 6 stays at 2/5, and project status stays `unknown`. It gives no project
authority and does not change the product. The branch for D-GOV-009 and its
evidence do not change.

<a id="worktree-retirement-workflow-migration"></a>

## Workflow migration for worktree retirement

### Owner view

| Owner-view field | Result |
| --- | --- |
| Current state | The implementing agent added the worktree retirement procedure and semantic controls at Level 2. Worktree removal and branch removal are Level 3 operations. The project owner gave removal authority for the 2 operations. The safety/risk panel did not occur before the operations. The decision register did not contain D-GOV-012 before the operations. |
| What changed | The recovery policy owns the worktree retirement procedure. Each applicable agent must use the procedure during context recovery and workspace alignment. The retirement audit examines the retirement plan. The recovery validator examines the retirement audit result. The implementing agent used Git to remove the worktree and local branch for pull request #56. The project owner recorded the sequence nonconformance in D-GOV-012. |
| What now works | The accepted commit contained the branch tip `9f3b05d480971d197a57cb00f1811f6c1012f144`. The local-state inventory contained 144 files. The local-state inventory SHA-256 was `a7122a09eb5c25f02d606909b4539b35d98b882c3cf2051b7f4f9e575b1ad044`. The retirement plan contained 1 local-state type for each item. The retirement audit examined the retirement plan. The retirement audit gave no finding. |
| Limitations/findings | The retirement audit cannot select a canonical owner or give removal authority. Git ignored the retirement plan. After removal, the implementing agent cannot make a new local-state inventory for the worktree. After Git removed the Git index, a reviewer could not get new evidence for `assume-unchanged` or `skip-worktree`. A reviewer cannot show historical losslessness. |
| Owner decision | The project owner recorded the sequence nonconformance in D-GOV-012. The project owner gives no retrospective authority. The project owner accepts the preservation audit result for the authorised source. The project owner gives project authority for an exact candidate and draft pull request for Cycle 2. The project owner gives no project authority to merge into protected main. The project owner gives no project authority to start Cycle 3. |
| Next action | After the applicable validator gives a `PASS` result, the implementing agent must get new independent reviews. After all independent reviewers give `ACCEPT`, the implementing agent must publish a draft pull request. The implementing agent must not merge the pull request. The implementing agent must not start Cycle 3. If a mandatory finding has no disposition, the implementing agent must stop. |

### Evidence before worktree removal

Pull request #56 had the pull-request state `MERGED`. Its merge commit was
`65409493d741a5606543bd437e519f8efefb8680`. Local branch
`agent/ste100-retrieval-assurance` had branch tip
`9f3b05d480971d197a57cb00f1811f6c1012f144`.

Before removal, protected `main` had accepted commit
`d47518083768d34cf9b41566feaf132ac4562595`. Git showed that the accepted commit
contained the branch tip. GitHub kept the pull-request state, head, and merge
commit for pull request #56.

The retirement audit used `git status`. It found no tracked change. It found no
untracked file that a Git ignore rule did not select. The historical audit did not
examine `assume-unchanged` or `skip-worktree` values.

After the audit, Git
removed the worktree Git index. A reviewer cannot examine these values now.
The evidence does not show historical losslessness.

No person or process used the worktree. The primary PyCharm project used the
primary worktree on protected `main`.

### Local-state inventory and preservation

The local-state inventory contained 144 ignored files and 8,042,871 bytes. Its
SHA-256 was
`a7122a09eb5c25f02d606909b4539b35d98b882c3cf2051b7f4f9e575b1ad044`.

| Local-state type | Files | Bytes | Result and canonical owner |
| --- | ---: | ---: | --- |
| Authoritative local source | 1 | 3,316,157 | The source manifest records the PDF identity. The source and retrieval procedure owns the source path and the STE lookup operation. PROVENANCE.md owns the rights state. |
| Retained evidence | 0 | 0 | The retirement plan had no item in this local-state type. |
| Rebuildable cache/generated state | 82 | 3,026,397 | The retirement plan recorded the applicable tool and a `PASS` result for each file. |
| Temporary disposable state | 61 | 1,700,317 | The source and retrieval procedure owns temporary review receipts. The project owner gave removal authority for these files. |
| Ambiguous or uniquely owned state | 0 | 0 | The retirement plan had no item in this local-state type. |

The PDF in the worktree and the PDF at the primary source path had equal bytes.
Each file had byte size 3,316,157 and SHA-256
`d1f4ea9e7cd6e46b47aa9057209f99e78c0e9cfc4e27a5b07895b05c1a166431`.
The source path was the location for planned preservation.

The retirement plan had 1 local-state type for each item. It recorded the
canonical owner and result. For planned preservation, it recorded the source
and copy. The retirement audit examined all 144 items. It gave no finding and
returned no local path or file data.

### Removal and preservation audit

No operation occurred between the last retirement audit and removal. In the
last audit, the retirement audit examined the exact Git identity, local-state
inventory, retirement plan, and preservation audit result again.

The implementing agent used `git worktree remove` without `--force`. The
agent did not use `git stash` or `git worktree prune`. The agent did not move
files as a condition for removal. Git removed the worktree. After removal, the
file system did not contain the worktree directory. The output from
`git worktree list` did not contain the worktree.

After worktree removal, the accepted commit contained the branch tip
`9f3b05d480971d197a57cb00f1811f6c1012f144`. After Git showed this containment,
the implementing agent used `git branch -d`. Git removed only local branch
`agent/ste100-retrieval-assurance`.

The ASD-STE100 Issue 9 PDF stayed at the primary source path. The PDF kept its
source identity.
The output from `git worktree list` contained the other 3 worktrees. The
implementing agent did not remove a branch on GitHub. The `git stash list`
command returned no stash, and Git did not contain `refs/stash`.

### Validation of the retirement audit

If the `accepted_ref` value is different, the retirement audit fails closed. It
also fails closed for a duplicate JSON key or symbolic link in planned
preservation. It also fails closed for these states:

- An inventory item that the retirement plan does not contain
- More than 1 local-state type for an item
- An item without a canonical owner or result
- Ambiguous or uniquely owned state
- Evidence that a person or process uses the worktree
- Missing removal authority
- A change to the worktree, accepted commit, or local-state inventory
- A worktree without tracked cleanliness
- An `assume-unchanged` or `skip-worktree` value in the Git index
- A `GIT_INDEX_FILE` value from the caller
- A local-state type that is different from all 5 local-state types
- Different bytes in the source file and copy
- A filename with non-UTF-8 bytes
- A symbolic link loop in a location for planned preservation
- Local file data, Git error data, or a local path in command output.

For each Git command, the retirement audit removes each environment variable
with a `GIT_` prefix that the caller supplies. It then sets
`GIT_OPTIONAL_LOCKS` to `0`. If file inspection fails, the retirement audit
returns a `FAIL` result without a path.

After the author froze the exact candidate
`4803afe2325df604a51ab4276a2563cb2ee6dfad`, the implementing agent made no
change to `tools/repository_safety_audit.py` or the regression tests for the
tool. The independent quality reviewer and independent security/recovery reviewer
accepted the source and tests in exact candidate
`e3bddbae174097014fcdbc5e5b027d6aa962e88e`. The independent documentation
reviewer rejected the canonical prose in the candidate.

The record contains no command output from the `local` validation profile for
exact candidate `e3bddbae174097014fcdbc5e5b027d6aa962e88e`. Phase evidence
reports no result count for the candidate. For the next exact candidate, the
implementing agent must record new evidence from a command result.

<a id="d-gov-012-worktree-sequence-nonconformance"></a>

### D-GOV-012 decision

The project owner gave removal authority for the worktree. The owner also gave
removal authority for local branch `agent/ste100-retrieval-assurance`. The
project owner gave the branch-removal authority with this condition: Git must
remove the worktree first. The safety/risk panel did
not occur before these operations. The decision register did not contain
D-GOV-012 before the operations.

After the operations, the project owner recorded this sequence nonconformance
in D-GOV-012. The decision gives no retrospective authority. Because Git
removed the Git index, no evidence can show historical losslessness.

#### Safety/risk panel after removal

| Risk | Assessment | Result |
| --- | --- | --- |
| PR-12 — fragmented or stale direction | Phase evidence owns the complete result. D-GOV-012 and the project plan contain canonical links to phase evidence. | Medium / Mitigate. The disposition does not change. |
| PR-13 — repository or evidence loss | The accepted commit contained tracked files. The ASD-STE100 Issue 9 PDF stayed at the source path. Because Git removed the Git index, the evidence cannot show all index values. | Critical / Mitigate. The disposition does not change. |
| PR-22 — governance sequence | D-GOV-012 records the sequence nonconformance. New independent reviews are necessary before publication. | High / Remove. The disposition does not change. |

The panel occurred after the operations. It gives no retrospective authority.

**Panel recommendation:** **Continue with bounded conditions.**
After removal, keep D-GOV-012 as a record. Give no retrospective authority. Before
draft publication, get new independent reviews.

#### Owner decision D-GOV-012

At protected `main` `d47518083768d34cf9b41566feaf132ac4562595`, the project
owner recorded D-GOV-012. Exact candidate
`96063e9836748bbc5755db251fa8b66564e65a28` contained the evidence after removal.
The owner accepted the preservation audit result for the ASD-STE100 Issue 9
PDF.

The owner gave project authority for an exact candidate in Cycle 2. The owner
also gave project authority for a draft pull request. The owner gave no project
authority for a merge. The owner gave no project authority for Cycle 3.

Phase 6 stays at 2/5. Project status stays `unknown`. D-GOV-009 and its
evidence do not change. The decision gives no product or railway authority. It
gives no FreeCAD, export, schema, or API authority. It gives no performance,
production, release, or rights authority.

### Author-side assurance for ASD-STE100 Issue 9

The independent documentation reviewer rejected exact candidates
`c98e83cc968bcc784082e9cce208a5c107764e21` and
`e3bddbae174097014fcdbc5e5b027d6aa962e88e`. The author's conformance review did
not record all mandatory findings. The project owner then gave the validation
tools a bounded scope. The validation tools examine the source identity, exact
candidate, conformance scope, SHA-256 values, and unresolved findings. The
tools also examine command results and the read-only challenge result.

On 2026-08-26, the project owner narrowed the assurance workflow. The author
completes the conformance review. The author reviews each logical unit with a
material edit against all applicable Rules 1 through 9. The author uses the
official PDF with SHA-256
`d1f4ea9e7cd6e46b47aa9057209f99e78c0e9cfc4e27a5b07895b05c1a166431`.

The temporary author-review worklist records the exact candidate, source
identity, conformance scope for changed prose, and logical units that the author
reviewed. It records findings and dispositions. It also records evidence claims
where applicable. Before the author freezes the exact candidate, the author
resolves each unresolved finding.

The STE lookup validates the source identity, exact candidate, conformance
scope, and SHA-256 values. If the SHA-256 in the worklist differs from the
SHA-256 for the logical unit, the STE lookup rejects the worklist. It rejects a
worklist that does not contain all changed prose or that contains an unresolved finding. For a
command result, it compares the actual result with command output. It does not
examine prose for conformance.

Before the author freezes the exact candidate, a different documentation
reviewer must complete a read-only challenge. The reviewer examines the
author-review worklist and changed prose. The challenge has no acceptance.
After the author freezes the exact candidate, an independent documentation
reviewer completes a review with full applicability.

`tests/validate_governance_semantics.py` rejects a change that narrows these
assurance controls. The author cannot use a `PASS` result from a validation tool
as a conformance review. The author also cannot use a pre-check with no finding
as a conformance review.

The recovery policy owns the instruction that LFE-021 records. The
implementing agent added a semantic control for PR-13. The project owner made
no change to the risk, disposition, severity, treatment, or control
effectiveness.

The implementing agent made no change from LFE-001 to LFE-020. The
implementing agent made no change to D-GOV-009 or D-GOV-009 evidence. Phase 6
stays at 2/5. Project status stays `unknown`.

The implementing agent made no change to product behaviour or railway
behaviour. The implementing agent made no change to a FreeCAD operation or
result. The implementing agent made no change to export behaviour, a schema, or
an API. The project owner gives no project authority for product performance,
production, release, or a phase exit. The implementing agent made no change to
the rights state or acceptance. The project owner gives no project authority
for Cycle 3 or a merge of an exact candidate for Cycle 2 without review.

<a id="d-gov-015-simplified-ste-lifecycle"></a>

## D-GOV-015 simplified STE lifecycle

### Owner view

| Field | Current result |
| --- | --- |
| Current state | The interrupted three-path implementation at recovery checkpoint `ac5a7d7ae8c6bf72069b802ebe9e929faf27e789` is bounded implementation evidence. Its authorised protected-main baseline is `54176f5ae0fea1f72743f856fd9251a53d7e1dbf`. The checkpoint is not accepted project state. |
| What changed | D-GOV-015 adopts one lifecycle: author → freeze scope → one Documentation Review → optional exact reviewed correction once → one final deterministic validation → complete or owner stop. The existing Issue 9 retrieval and cache remain. |
| What now works | Git derives whole-document first review and later changed-complete-unit scope. One review returns one of three complete verdicts. Exact corrections bind to frozen preimages. Durable state records document identities. Final validation binds source, scope, receipt, state, and final bytes and detects unreviewed mutation. |
| Limitations/findings | The tool cannot authenticate a reviewer. Actual role separation remains necessary. One-shot ignored evidence requires independent preservation. Final validation does not judge linguistic conformance. The current backup condition must be proved before Documentation Review. |
| Owner decision | Accept D-GOV-015. Complete only the bounded lifecycle, canonical and skill alignment, Level 3 record, one review, and optional exact correction once. Then complete final deterministic validation, non-linguistic publication review, and one draft pull request if exact-green. Do not merge. |
| Next action | Complete fail-closed development validation. Freeze and preserve one exact candidate and its scope. Run the one Documentation Review. Preserve each resulting review file. Run the one final deterministic validation. Get the required non-linguistic independent review, and publish one draft pull request only if exact-green. |

### Bounded implementation and evidence

The exact `54176f5ae0fea1f72743f856fd9251a53d7e1dbf` to
`ac5a7d7ae8c6bf72069b802ebe9e929faf27e789` delta changes only
`tools/ste100_lookup.py`, `tests/validate_ste100_retrieval.py`, and
`reference/ste-review-state.json`. The lookup file keeps 66 existing functions
unchanged, modifies only parser and command routing, removes 17 functions for
the retired author-worklist design, and adds 44 lifecycle-specific functions.
The test replaces the retired worklist/challenge route with an end-to-end Git
fixture. The durable register is an empty schema-1 document map. The exact
three-path delta is 1,645 additions and 1,205 deletions, for net growth of 440
lines. No generic workflow state, grants, uses, completions, telemetry, or
ontology machinery remains.

At the recovery checkpoint, tracked Python parsing passed for 189 files. The
focused ASD-STE100 retrieval validator passed. Source/cache validation returned
the verified-source-bound-cache sentinel. The CI standalone profile passed all
60 validators. This evidence preceded alignment and trust-control hardening.
The project must rerun it before candidate freeze.

The safety/risk review found an incorrect temporary-directory instruction and
incomplete negative trust-control evidence. It also found inherited Git
execution surfaces and no current independent preservation result for the
ignored one-shot review files. The implementation corrected the directory
instruction. It resolves a protected system Git executable independently of
inherited `PATH`. It uses a minimal Git environment and disables replace
objects, fsmonitor, hooks, external diff, and text conversion. It keeps bounded
process output and timeout.

The negative tests prove rejection of self-review, tampered source, scope,
receipt, state, and final bytes. They also reject invalid corrections, a
hostile Git environment, fsmonitor, text conversion, replacement objects, and
unreviewed final mutation.
The candidate still requires the preservation conditions before review.

After alignment and trust-control hardening, tracked Python parsing passed for
189 files. The focused retrieval and lifecycle validator passed. Source/cache
validation returned the verified-source-bound-cache sentinel. The agent-guidance
and project-progress validators passed. The governance mutation validator
rejected all 328 mutations. The CI standalone profile passed all 60 validators.

No FreeCAD or GUI validation applies to this governance-and-tool change.

### Participants and reviewed evidence

| Participant | Role and independence |
| --- | --- |
| `owner:tracktemplate-project-owner` | Project owner, panel chair, and decision owner. The owner supplied the exact lifecycle, baseline, checkpoint, exclusions, completion route, draft-pull-request authority, and no-merge limit. |
| `agent:openai-codex-primary` | Change owner and presenter. This agent recovered, corrected, aligned, and validated the candidate. It cannot independently accept its own implementation or linguistic conformance. |
| `agent:aquinas-lifecycle-risk-panel` | QA/risk reviewer. This delegated reviewer examined the checkpoint, current implementation, tests, recovery controls, and alignment without mutation or linguistic Documentation Review. The reviewer is independent of implementation changes but shares the agent team and workspace. It is not an external organisational review. |

The panel reviewed the exact protected-main baseline and recovery checkpoint,
the three-path [lookup implementation](../../tools/ste100_lookup.py),
[lifecycle fixture](../../tests/validate_ste100_retrieval.py), and
[empty document-level state](../ste-review-state.json). It also reviewed the
[Engineering Policy](../ENGINEERING_POLICY.md#true-gates-and-safetyrisk-panels),
[validation owner](../VALIDATION.md#validation-of-the-retrieval-contract),
[recovery policy](../RECOVERY_AND_BACKUP.md), [current risks](risks.json),
[source and retrieval procedure](../external/asd-ste100/README.md), and the
development-validation results in this panel.

### Dissent, unknowns, and exceptions

The QA/risk reviewer recorded no dissent from the bounded recommendation. The
accepted backup device is not currently mounted, so independent preservation
for this gate remains unknown. The tool also cannot authenticate the declared
reviewer identity. The same-team and shared-workspace review is an independence
limitation, not an external organisational review. There is no exception to the
single-review lifecycle, preservation condition, owner-stop rule, Phase 6
limit, or hard exclusions.

### Bounded conditions and accountable owners

| Condition | Accountable owner | Deadline and current result |
| --- | --- | --- |
| Harden Git identity and add the fail-closed source, scope, receipt, state, correction, and mutation proofs. | `agent:openai-codex-primary` | Before candidate freeze — completed, focused and full development validation must remain green on the exact candidate. |
| Commit and push the exact candidate. | `agent:openai-codex-primary` | Before Documentation Review — pending candidate freeze. |
| Make the accepted independent backup device available. | `owner:tracktemplate-project-owner` | Before independent scope preservation and Documentation Review — pending. |
| Preserve the frozen scope and then each review result, receipt, and accepted-state proposal on the accepted device. | `agent:openai-codex-primary` | Preserve each review file before its next dependent operation — pending. |
| Return the sole linguistic verdict with actual role separation and all exact wording, if applicable. | Independent Documentation Reviewer | Once, after scope preservation and before any correction — pending. |
| Apply only exact approved corrections once, run one final deterministic validation, and return any failure to the owner. | `agent:openai-codex-primary` | After the sole Documentation Review and before publication review — pending. |

### Safety and risk panel

| Risk | Assessment | Result |
| --- | --- | --- |
| PR-12 — fragmented or stale direction | Policy, workflow, validation, terminology, source instructions, and the two directly responsible review skills align to D-GOV-015. Semantic controls must reject a return to the retired route. | Medium / Mitigate / Partial. The disposition does not change. |
| PR-13 — repository or evidence loss | The candidate needs a pushed exact Git identity. The ignored scope, result, receipt, and proposal need current independent preservation as each exists. No accepted backup evidence after 2026-08-01 proves this gate. | Critical / Mitigate. Control effectiveness is unverified for this gate until preservation passes. The disposition does not change. |
| PR-22 — authority transfer or self-acceptance | One independent Documentation Reviewer owns the sole linguistic verdict. A separate final review is non-linguistic. The tool compares declared author and reviewer identifiers but cannot authenticate persons. | High / Remove. Effectiveness requires actual role separation, this panel, and the owner decision. The disposition does not change. |

The safety/risk reviewer was read-only and did not conduct linguistic
Documentation Review. The reviewer shares the agent team and workspace, so the
review is independent from implementation mutation but is not an external
organisational review.

**Panel recommendation:** **Proceed with bounded conditions.** Before freeze,
complete the Git hardening and negative tests and rerun development validation.
Before Documentation Review, push the exact candidate and independently
preserve the scope. Preserve the result, receipt, and accepted-state proposal
before the next dependent operation. Any preservation, reviewer-separation,
source, scope, receipt, state, semantic, Git-identity, or final-byte failure
returns to the owner. Do not run a second Documentation Review.

### Owner decision D-GOV-015

On 2026-08-31, `owner:tracktemplate-project-owner` accepts the exact authority
and exclusions in [gate-decisions.json](gate-decisions.json). The earlier
author-side assurance section remains historical evidence of the retired
route. It is not current operating instruction after D-GOV-015.

Phase 6 stays at 2/5. Exits 1, 4, and 5 stay Pending. Project status stays
`unknown`. No risk disposition changes. D-GOV-015 gives no product, railway,
FreeCAD, GUI, persistence, export, schema, API, or performance authority. It
gives no production, physical-output, packaging, release, tagging,
legacy-retirement, or merge authority.

It gives no authority to resume D-GOV-014 or modify `aa6c506`. It gives no
authority to add generic repair authority, grants, uses, completions,
telemetry, or ontology work. It gives no authority for Cycle 3. It also gives
no authority for a second documentation-assurance framework or a second
Documentation Review.

### BLOCKED result evidence-contract correction

The preserved candidate `19a8942d11b9c31703c5525ccbf047aacfbc8492` has one
authoritative `BLOCKED` review result. The result has SHA-256
`18a23e6a3ea398d1b0b3857f4237ffb8b3c7d4c49ddf3aea72dfd76db5a94ccc`.
It contains no recorded blocking finding and cannot supply authoring input.
The candidate, scope, result, receipt, and their independent copies remain
unchanged.

This Level 2 correction requires schema 2 for each new review result and
receipt. Each result confirms that its set of blocking findings is complete. A
`BLOCKED` result records at least one blocking finding. Each blocking-finding
entry identifies the finding, formal Issue 9 rules, exact path, and frozen
logical unit. The scope and review-state schemas stay at version 1. The change
adds no persistent logical-unit workflow state and no second review mechanism.

Four changed Python files passed parsing. The focused lifecycle fixture and
the complete STE retrieval validator passed. The verified local source rebuilt
and validated the derived cache. The agent-guidance validator passed. The
governance validator rejected all 333 semantic mutations. The standalone
regression profile passed both steps with their required sentinels.

No FreeCAD or GUI validation applies to this evidence-contract correction.

Automatic validation proves that the blocking-finding list is nonempty. It
also proves reviewer attestation, binding to the frozen scope, and preservation
in the receipt. It cannot prove that a reviewer reported a finding that the
reviewer omitted. No prose repair starts from the deficient schema-1 result.
D-GOV-015, all risk dispositions, Phase 6 at 2/5, and project status `unknown`
do not change.

<a id="d-gov-017-whole-technical-document-lifecycle"></a>

## D-GOV-017 whole technical-document lifecycle

### Owner view

| Field | Current result |
| --- | --- |
| Current state | The project owner supplied the complete technical-document lifecycle requirement on 2026-09-04. Protected `main` and `origin/main` were equal at `22f0ef511ec841de46c14e645ea1ac210256a054` before this new candidate. Development checks pass for the current working tree. The candidate is not yet a controlled baseline. |
| What changed | The Engineering Policy now contains one complete Technical Documentation Management Plan. A new Technical Author Lead owns authoring, delivery, and maintenance coordination. D-GOV-015 remains authoritative for the bounded authoring, review, and final-validation part. |
| What now works | One route now controls the complete lifecycle. It identifies and classifies the need, assigns ownership, plans and authors the information, and establishes a controlled baseline. It controls later change, supersession, retirement, and historical preservation. Existing Git, review-state, evidence, and decision records supply traceability. |
| Limitations/findings | The draft still needs the D-GOV-015 freeze, preservation, one Documentation Review, final deterministic validation, a fresh post-validation non-linguistic quality and publication review, and acceptance before it can become a controlled baseline. Normal integration is then necessary for current repository use. The accepted backup condition is not yet proved. The Technical Author Lead has no subject, terminology, verdict, validation, acceptance, publication, supersession, retirement, deletion, or merge authority. |
| Owner decision | Accept D-GOV-017 and establish the complete TDMP and Technical Author Lead responsibility with the stated authority boundaries. Do not create another linguistic-review lifecycle or document-management database. Keep D-GOV-015 unchanged as the narrower lifecycle authority. |
| Next action | Freeze and preserve one exact candidate when the required Git and backup conditions can be met. Run the one Documentation Review and final deterministic validation. Then obtain a fresh post-validation non-linguistic quality and publication review. Establish a controlled baseline only after acceptance. Use normal repository integration to make it current and available. |

### Need, classification, and bounded result

The identified need is a material governance deficiency. The accepted policy
controlled only the narrower D-GOV-015 authoring and review lifecycle. It did
not define one coherent route for initiation, classification, ownership,
planning, controlled use, maintenance, change, supersession, retirement, and
historical preservation.

The selected result is a material change to the existing canonical
[Engineering Policy](../ENGINEERING_POLICY.md#technical-documentation-management-plan),
which already owns technical-documentation lifecycle policy. A separate TDMP
document would duplicate that owner. The change also adds one repeatable
Technical Author Lead skill, aligns the terminology and central skill routing,
and adds directly dependent semantic controls.

This is Level 3 because it changes governance responsibility and controlled
documentation authority. It is a governance-budget exception because the
policy and evidence change is larger than the skill implementation. No product
source or railway behaviour changes. No FreeCAD or GUI validation applies.

Development validation parsed all 189 Python and macro files. The 60-test
standalone CI profile passed. The directly dependent documentation, guidance,
resource, retrieval, progress, quality-assurance, and governance-semantic
checks passed. The governance-semantic check rejected all 343 inadmissible
mutations and retained 337 independent protections. The STE cache remains
bound to the accepted source. No FreeCAD or GUI validation applies.

Acceptance evidence also requires a complete diff review and independent
non-linguistic architecture, risk, and quality challenge. The current
pre-freeze challenge does not replace the fresh read-only quality and
publication review after final validation. D-GOV-015 separately controls the
one linguistic review of the frozen candidate.

### Prior candidate and preservation limit

Commit `00edbb331e5972b565a9fa70b3d85aa20754bce4` and tree
`52054d6bb857e38009f79f48d2896b4a1f6e583a` are preserved failed experimental
evidence. Its frozen review scope has SHA-256
`bd5375e2af7b003bf2e2dc5a5fb457a59ad7396ffa0784915859f6c26d04cfab`.
Its schema-2 `BLOCKED` result has SHA-256
`b525e3d9d3c55f5f685c2afe38af992181d9656c43de5b61a82971a576338c0e`
and records 28 blocking findings. It has no accepted-state proposal.

That exact candidate remains terminal under D-GOV-015. D-GOV-017 does not
repair, extend, accept, or make it current. This candidate starts again from
protected `main` because the project owner supplied a new whole-lifecycle
requirement. D-GOV-016 was never current authority and is not reused.

### Participants and independence

| Participant | Role and independence |
| --- | --- |
| `owner:tracktemplate-project-owner` | Project owner, panel chair, requirement owner, and accepting authority for D-GOV-017. |
| `agent:openai-codex-primary` | Governance change owner and Technical Author Lead for this candidate. It cannot independently accept its own prose, validation, or controlled baseline. |
| `agent:hume-governance-design` | Read-only architecture and responsibility reviewer. The reviewer recommended the existing Engineering Policy as TDMP owner and a separate Technical Author Lead responsibility. The reviewer shares the agent team and workspace. |
| `agent:kepler-lifecycle-gap-audit` | Read-only requirements-gap reviewer. The reviewer mapped the missing whole-lifecycle stages and confirmed the narrower D-GOV-015 boundary. The reviewer shares the agent team and workspace. |
| `agent:meitner-validation-surface` | Read-only validation reviewer. The reviewer selected existing semantic validators and rejected a new validator or state schema. The reviewer shares the agent team and workspace. |
| `agent:tdmp-final-quality-review` | Read-only pre-freeze QA/risk and implementation-quality reviewer. The reviewer challenged the Critical preservation risk, panel completeness, lifecycle sequence, and unrelated prose changes. The reviewer is independent of working-tree mutation and shares the agent team and workspace. |

The delegated reviews are independent from working-tree mutation. They are not
external organisational reviews. The current QA/risk review is a pre-freeze
implementation challenge. The frozen candidate still requires one independent
Documentation Reviewer under D-GOV-015 and one fresh read-only non-linguistic
quality and publication review after final validation.

### Safety and risk panel

| Risk | Assessment | Result |
| --- | --- | --- |
| PR-12 — fragmented or stale direction | The Engineering Policy remains the one TDMP owner. Central routing and one Technical Author Lead skill point to that owner. Existing Git and canonical records remain the trace. | Medium / Mitigate / Partial. The disposition does not change. |
| PR-13 — repository or evidence loss | Protected `main` preserves the accepted state, and the terminal failed candidate remains named. The new candidate and one-shot D-GOV-015 evidence still need the existing push and independent-preservation conditions. The fresh post-validation review must use the preserved exact candidate and evidence. | Critical / Mitigate. Effectiveness remains unverified for this gate until preservation passes. The disposition does not change. |
| PR-22 — authority transfer or self-acceptance | The Technical Author Lead coordinates the lifecycle but does not receive subject, verdict, validation, acceptance, publication, supersession, retirement, deletion, or merge authority. Independent review and owner acceptance remain separate. | High / Remove. The disposition does not change. |

**Panel recommendation:** **Proceed with bounded conditions.** Retain one TDMP
in the Engineering Policy, one Technical Author Lead responsibility, and the
existing D-GOV-015 review route. Add no document-management database, second
linguistic review, sentence-level workflow state, product change, or phase-exit
claim. Before a controlled baseline, complete the required freeze,
preservation, Documentation Review, final validation, fresh post-validation
quality and publication review, and acceptance. Then use normal repository
integration to make that baseline current and available.

### Dissent, unknowns, and exceptions

The pre-freeze QA/risk reviewer found missing panel records, an omitted
post-validation quality-review stage, and unrelated list-format changes. The
change owner accepted the findings, added the required controls, and reverted
the unrelated changes. No unresolved dissent remains.

The exact frozen candidate, independent preservation result, Documentation
Review verdict, final deterministic result, post-validation quality and
publication review, controlled-baseline identity, and integration result do
not yet exist. The accepted backup condition also remains unproved.

There is no exception or waiver to D-GOV-015, independent preservation,
required review, deterministic validation, baseline acceptance, or repository
integration. The governance-budget exception permits only the policy,
evidence, skill, routing, and semantic controls that implement D-GOV-017.

### Bounded conditions

| Condition | Accountable owner | Deadline |
| --- | --- | --- |
| Keep the TDMP in the Engineering Policy. Add no second policy owner, document database, or linguistic-review route. | Technical Author Lead | Before candidate freeze and throughout the lifecycle. |
| Keep subject meaning and terminology with their applicable canonical owners. | Technical Author Lead and applicable subject or terminology owner | Before candidate freeze and throughout the lifecycle. |
| Freeze a clean exact Git candidate, push its checkpoint when authorised, and preserve the candidate and one-shot evidence independently. | Project owner, Technical Author Lead, and independent preservation reviewer | Before Documentation Review. |
| Run one Documentation Review and one final deterministic validation. Finish the bounded D-GOV-015 lifecycle. Then run one fresh read-only non-linguistic quality and publication review. | Independent Documentation Reviewer, Independent Quality Reviewer, and Technical Author Lead | Before controlled-baseline acceptance. |
| Record acceptance only for the exact reviewed, validated, and quality-reviewed content. Then use normal repository integration to make it current. | Project owner and repository integration owner | Before current controlled use. |
| Preserve the terminal failed candidate, untouched legacy prose, and required history. | Technical Author Lead | Throughout this cycle and the later lifecycle. |

### Owner decision D-GOV-017

On 2026-09-04, `owner:tracktemplate-project-owner` accepts the lifecycle
requirement and authority boundaries in
[gate-decisions.json](gate-decisions.json). The TDMP owns the complete
technical-document lifecycle. The Technical Author Lead owns
technical-document authoring, delivery, and maintenance coordination. The
applicable canonical technical or governance owner continues to own the
documented subject.

D-GOV-015 remains authoritative for `author → freeze scope → one Documentation
Review → optional exact reviewed correction once → one final deterministic
validation → complete or owner stop`. It is the bounded authoring and review
part of the whole lifecycle. D-GOV-017 adds no second linguistic-review route
and does not reopen unchanged accepted prose or frozen history.

After the D-GOV-015 lifecycle finishes with green final validation, one fresh
read-only non-linguistic quality and publication review must give a passing
result for the exact validated candidate. This result is necessary before
controlled-baseline acceptance. The later review does not repeat Documentation
Review or change its verdict.

Phase 6 stays at 2/5. Exits 1, 4, and 5 stay Pending. Project status stays
`unknown`. No risk disposition changes. D-GOV-017 gives no product, railway,
FreeCAD, GUI, persistence, export, schema, API, performance, production,
physical-output, packaging, release, tagging, legacy-retirement, deletion, or
merge authority.

<a id="current-phase-6-exit-condition-disposition"></a>

## Current Phase 6 exit-condition disposition

The accepted current state is 2/5 under D-P6-002 and D-P6-005:

| Exit condition | Current disposition |
| --- | --- |
| The selected slice has equivalent exact validation and production output for the agreed bounded work | Pending. Exact-validation and private-development DXF evidence exists. Agreed output equivalence and production clearance remain absent. |
| No transient production objects leak into the editable document | Evidenced and owner-accepted under D-P6-002 — bounded to the accepted B16 Entry/Exit exact-validation and export routes with the recorded limitations |
| Export is deterministic and failure-safe | Evidenced and owner-accepted under D-P6-005. This is bounded to the private-development B16 Entry/Exit DXF-and-manifest route under D-P6-003 and D-P6-004. The recorded platform, recovery, and assurance limitations apply. Project status remains `unknown`. |
| Editing resource use improves beyond normal noise, with complete end-to-end cost accounted for | Pending — D-GOV-008 stays the authority for its baseline, hypothesis, and comparison rule. D-GOV-009 records the two results as retained negative evidence and stops work in that direction. Its attribution record gives a PASS result for the canonical area, which is only `0.0731425 ms` higher than the noise floor. D-GOV-010 qualifies the exact host for that evidence. D-GOV-011 selects one subsequent hypothesis for the canonical record and its comparison rule. It makes no product change, admits no performance result, and does not accept Exit 4. |
| The legacy path remains available until parity and project-owner acceptance permit removal | Pending. B14 remains available. Parity for the complete accepted work and retirement authority remain absent. |

## Carried controls and exclusions

The accepted Coin renderer and B16 Entry/Exit editing behaviour remain bounded
exactly by D-P5-002. D-P5-002 accepts explicit-only lifecycle activation,
exactly-once attachment, duplicate rejection, and owner-visible
selection/editing. It also accepts atomic Undo/Redo, save-time deactivation,
and reopen reconstruction. The one-empty-switch-child-per-object limitation
stays confined to the demonstrated work.

Reopen D-P5-002 and the retired PR-14 exposure before retaining a later
composition that invalidates the containment. Also reopen them before
permitting live mappings, caches, proxies, active Coin children, or additional
residual switch children to accumulate.

The 24 risks from the end of Phase 5 stay in
[risks.json](risks.json). The project owner used D-GOV-005 to change only the
control wording for PR-12, PR-20, and PR-22. The decision register at
[gate-decisions.json](gate-decisions.json) owns D-P6-001, D-GOV-005, D-P6-002,
D-P6-003, D-P6-004, D-P6-005, TT-DOC-001, and TT-DOC-002. It also owns
D-GOV-006, D-GOV-007, D-GOV-008, D-GOV-009, D-GOV-010, and D-GOV-011.

The D-GOV-012 decision records the sequence nonconformance in Cycle
2. It also records project authority for an exact candidate and draft pull
request in Cycle 2.

D-GOV-015 owns the current simplified STE lifecycle. It keeps the existing
retrieval architecture, requires one Documentation Review and one final
deterministic validation, and gives no phase, product, merge, or Cycle 3
authority.

D-GOV-017 owns the complete technical-document lifecycle and assigns the
Technical Author Lead responsibility. It keeps D-GOV-015 as the bounded
authoring and review authority. It creates no second review route or lifecycle
database and changes no phase, product, risk, or merge authority.

Exits 2 and 3 have Evidenced and owner-accepted status. D-P6-003 selects
recovery authority. D-P6-004 defines the supported fault/evidence boundary.
D-P6-005 accepts Exit 3 only in its bounded scope.

All other decisions about exits, clearance, support, schema, oracle retirement,
budgets, packaging, releases, and subsequent phases stay separately controlled.
TT-DOC-001 changes only documentation governance and presentation. TT-DOC-002
corrects only the spelling directive. D-GOV-006 qualifies only the exact
FreeCAD 1.1.3 profile. It preserves all other compatibility, product, phase,
risk, output, packaging, and release limits.

D-GOV-007 changes only the host rule and the directly dependent schema for
internal performance-evidence records. It admits no performance result and
defines no budget. It does not claim that performance became better, and it
does not accept Exit 4.

D-GOV-008 accepts the PR #50 series as the comparison baseline. It selects one
performance hypothesis and defines the comparison rule. It authorises one
Level 2 cycle but makes no performance optimisation. It admits no Exit 4
evidence and does not accept Exit 4.

D-GOV-009 keeps D-GOV-008 Accepted as the authority for that direction. It
records two subsequent results from Level 2 as retained negative evidence. It
stops new product work in that direction. It authorised the bounded
baseline-attribution investigation at Level 1. The project completed that
investigation. It admits no improvement or Exit 4 evidence.

It defines no budget and does not accept Exit 4.

D-GOV-010 qualifies only the profile with ID
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.13-qt6.11.1`. The two profiles that
the project qualified before D-GOV-010 stay qualified, and their evidence does
not change. D-GOV-010 authorises its profile to supply candidate evidence for
performance in a subsequent cycle. Each comparison must use one profile with
an exact identity. It admits no performance result and defines no budget. It
does not change D-GOV-009 or Exit 4.

D-GOV-011 accepts the D-GOV-009 attribution result as evidence for direction
selection only. It selects one subsequent hypothesis at Level 2 in
`tracktemplate/adapters/freecad/transition_state.py`. The hypothesis keeps one
live read of the selected record before the write. It uses that state again for
the named checks. It removes only two repeated reads.

D-GOV-011 defines the new same-host baseline and comparison rule for that
subsequent cycle. It makes no product change. It admits no performance result,
defines no budget, and does not accept Exit 4.
