# Phase 5 Lightweight Editing Prototype and Renderer Decision Evidence

Status: **Open — project owner accepted Phase 5 opening on 2026-07-28; 0/4
exits evidenced.**
Phase 4 closed with all six revised exits accepted on 2026-07-28; its frozen
record is [PHASE4_CLOSEOUT.md](../history/phase-closeouts/PHASE4_CLOSEOUT.md).

This fixed live path records the open phase. Opening authorises bounded
lightweight editing prototypes and renderer evaluation, not renderer
acceptance or exit evidence.

## Opening architecture review

Phase 5 owns the visible lightweight editing decision: renderer and style
selection, deterministic visual-to-domain selection mapping, GUI parameter
editing and Undo/Redo behaviour, save/reopen behaviour, invalidation, resource
evidence and project-owner acceptance of the editing behaviour and limitations.

The existing transition preview scene is renderer-neutral, disposable and
derived from canonical state. Three routes were considered:

| Route | Disposition |
| --- | --- |
| Keep only the renderer-neutral scene | Rejected for Phase 5 progress because it cannot provide visible editing or selection evidence. |
| Prototype a Coin-backed FreeCAD ViewProvider | Preferred first reversible experiment because it follows the accepted FreeCAD presentation boundary and can keep one logical object with a small derived scene. |
| Prototype an embedded SVG/Qt view first | Retained only as a fallback if the Coin experiment cannot meet selection, editing, lifecycle or resource requirements. |

The recommendation does not select a renderer. The first implementation
tranche must remain a removable adapter for the selected transition slice,
consume the existing preview scene, add no railway model or persistent scene
state, and expose no operator or production route.

<a id="phase-5-opening-panel"></a>

## Phase 5 opening panel and owner decision

**Decision and source state:** This Level 3 opening starts from clean protected
`main` at `f2922b5fd1fc26179db302385e519913b2b90c6e`, after the
required pull-request and post-merge `validation` checks passed. On 2026-07-28
Richard directed: “lets start phase 5 development.”

**Participants, evidence and independence:** Richard is project owner,
decision chair and accepting authority. Codex is change owner and presenter.
An independent reviewer performed a prospective read-only challenge and made
no repository or external-state change. The panel reviewed the
[current dashboard](../PROJECT_PLAN.md), [live risks](risks.json), frozen
[Phase 4 handoff](../history/phase-closeouts/PHASE4_CLOSEOUT.md#phase-4-exit-ownership-reassignment),
accepted [architecture](../ARCHITECTURE.md#4-lightweight-presentation-adapter)
and [dependency direction](../MODULARISATION_PLAN.md#presentation), the
[renderer-neutral transition scene](../history/phase-closeouts/PHASE4_CLOSEOUT.md#renderer-neutral-transition-preview-scene)
and the [presentation-validation boundary](../VALIDATION.md#4-presentation-validation).

**Risk disposition:** PR-14 remains Open/Remove/Not-yet-effective. PR-16,
PR-17, QA-R03 and QA-R04 remain Open with Partial controls. PR-20 and PR-22
remain Effective (current scope), provided every tranche stays bounded and
this decision remains linked. Opening the phase changes no treatment or
control-effectiveness value.

**Recommendation, conditions and unknowns:** The independent recommendation is
**Proceed with bounded conditions**:

| Accountable owner | Deadline | Condition |
| --- | --- | --- |
| Project owner | Before opening | Explicitly accept the opening at 0/4 without accepting a renderer or exit evidence. |
| Phase 5 change owner | Every implementation tranche | Limit work to the selected transition slice and keep renderer state derived, disposable and non-persistent. |
| Application/FreeCAD owner | Before retaining edit wiring | Route edits through application commands with one atomic Undo/Redo unit, stable identities and transactional failure recovery on copied/disposable documents. |
| PR-16 owner | Before retaining each renderer candidate | Cover renderer, style, visibility and selection inputs with complete signatures and prove miss, reuse, change, change-back, invalidation and failure behaviour. |
| Renderer and QA owners | Before renderer acceptance or Phase 5 exit | Prove real-GUI selection, editing, visibility, Undo/Redo, save/reopen and invalidation; record comparable cold/warm object-count, recompute, latency and resource evidence plus maintainability and limitations. |
| Scope owner | Throughout Phase 5 | Keep exact/export, migration-support expansion, production, chair, packaging/release, accepted-oracle retirement, persisted-schema and dependency authority excluded. |

The renderer, selection granularity, handle design and numerical resource
thresholds remain open investigation results. There was no dissent.

**Governance-budget exception:** This task transfers phase authority rather
than implementing product behaviour, so its required Level 3 panel, evidence,
decision register and dashboard changes necessarily exceed its zero product
lines. No policy or frozen historical record changes.

**Owner decision and resulting authority:** Richard's explicit instruction
accepts the recommendation and opens Phase 5 at 0/4. Bounded lightweight
renderer prototypes and GUI-editing evidence may now proceed through separate
Level 2 tranches. No renderer is accepted. Exact geometry/export, operator
migration or support expansion, production output, chair clearance,
packaging/release, accepted-oracle retirement, a persisted-schema change or a
new runtime dependency remain excluded and require their owning authority.

<a id="current-phase-5-exit-condition-disposition"></a>

## Current Phase 5 exit-condition disposition

The current exit state is 0/4:

| Exit condition | Current disposition |
| --- | --- |
| One renderer accepted using correctness, editing, FreeCAD integration, maintainability and measured resource evidence | Pending — the Coin candidate has bounded selection, edit, Undo/Redo, save/reopen and a 32-object resource observation; representative suitability, maintainability and acceptance remain |
| Small logical object/layer count with deterministic selection-to-domain mapping | Pending — one-object mouse mapping and a bounded 32-object/layer fixture are proved; representative selection suitability is not accepted |
| Normal edits avoid dense exact `Part` geometry | Pending — one bounded intent edit keeps one object and no `Part` shape; representative editing remains |
| Project owner accepts editing behaviour and documented limitations | Pending — editing behaviour has not yet been presented for owner acceptance |

Phase 6 retains complete exact-validation/export signatures and invalidation,
transient exact geometry, cleanup, output equivalence, rollback and end-to-end
performance. Phase 5 does not authorise those duties, operator migration,
production output, chair clearance or release work.

## Phase 5 decision-readiness map

This is an evidence map, not a second status system or an acceptance decision.
The formal state remains **0/4**, with every exit **Pending**.

| Exit condition | Formal status | Evidence already demonstrated | Remaining decision gap |
| --- | --- | --- | --- |
| One renderer accepted using correctness, editing, FreeCAD integration, maintainability and measured resource evidence | Pending | Renderer-neutral preview; disposable Coin scene and ViewProvider lifecycle; real pointer selection with stable visual-to-domain mapping; application-command editing, atomic Undo/Redo and failure recovery; retained-cache invalidation/reuse; save/close/reopen reconstruction through explicit post-open attachment; representative Entry/Exit selection, editing and reopen attachment; bounded 32-object observations; maintainability and dependency-direction review | Add an actual user-facing transition parameter-editing control and owner-visible selected/edited states; establish decision-usable interaction/resource ranges at representative scale; resolve product lifecycle/composition limits and the residual empty switch child; obtain project-owner renderer acceptance |
| Small logical object/layer count with deterministic selection-to-domain mapping | Pending | One-object and representative Entry/Exit pointer selection preserve stable mappings; the 32-object diagnostic retains 32 logical objects/layers and deterministic identities with measured active-node and resource observations | Prove representative interaction capacity rather than only the accepted fixture shape, agree decision-usable object/layer/interaction ranges and account for product composition and residual lifecycle limits |
| Normal edits avoid dense exact `Part` geometry | Pending | The application-command edit, representative Entry/Exit edit, Undo/Redo, recovery and cache-invalidation workflows retain compact logical objects/layers and zero `Shape` properties | Exercise an actual user-facing parameter control and representative interaction workflow through the intended product lifecycle, then obtain editing-behaviour acceptance |
| Project owner accepts editing behaviour and documented limitations | Pending | Retained GUI evidence can present pointer-selected, edited, Undo, Redo, recovered and reopened states together with the explicit post-open, fixture-scale, resource and empty-switch-child limitations | Present owner-visible selection and editing through a user-facing control, document decision-usable limits and obtain explicit project-owner editing-behaviour and renderer acceptance |

Unless a later change affects one of these boundaries or signals a regression,
phase progression need not repeat the retained preview, Coin lifecycle,
selection mapping, edit/Undo/Redo/recovery, cache, explicit reopen attachment,
representative Entry/Exit, 32-object or maintainability proofs. Their existing
regressions remain validation obligations; new work should close a remaining
decision gap.

## Coin scene-graph feasibility tranche

This Level 2 tranche adds an internal, product-route-disabled Coin scene
binding for the existing transition preview artifact. Renderer-owned colour
and line width have a complete deterministic signature. The binding constructs
one disposable Coin layer, maps its line node to the preview's stable visual
and domain identities, resolves real Pivy wrappers through the underlying Coin
node ID, and removes all retained nodes and mappings on discard. It imports no
FreeCAD, GUI, `Part`, Qt or Pivy module and creates no document object,
property, proxy, transaction, recompute or persistent state.

The focused proof first failed because the authorised module did not exist,
classified `implementation-defect`. After implementation it reached only this
intentionally absent evidence heading. The first qualified-host attempt lacked
its sentinel because FreeCAD uses a script namespace rather than `__main__`,
classified `fixture-or-harness-defect`. Once the harness ran, it exposed Pivy
wrapper identity as an implementation defect plus one incidental test-or-oracle
defect; underlying Coin node identity repaired both boundaries. The original
qualified FreeCAD 1.1.1 command then printed `Phase 5 transition Coin host
validation passed` with no document creation. The focused validator, adjacent
Phase 4 derived-state, preview-scene and persistence regressions, explicit
changed-file parsing, tracked-source parsing and governance controls passed.
The complete standalone CI profile then passed 46/46 validators. An independent
read-only review nevertheless blocked retention because failing Coin identity
access escaped the structured error boundary and a partial cleanup failure
could leave detached selection state live. Both paths were repaired with
fail-closed state, deterministic cleanup retry and focused fault injection.
The qualified-host check, parsers, adjacent regressions and complete 46/46
profile passed again after repair. Independent read-only re-review reran both
adversarial probes and accepted retention with no remaining defect, missing
work or extra scope inside this feasibility boundary.

No renderer or Phase 5 exit is accepted. Visible display, FreeCAD selection
events, a ViewProvider lifecycle, editing, Undo/Redo, save/reopen and measured
resource evidence remain unverified.

## Development-only ViewProvider fixture tranche

This Level 2 tranche attaches the existing derived Coin binding to one
disposable `App::FeaturePython` ViewObject through a named Coin-only display
mode. One `SoFCSelection` root maps the stable
`TransitionPreviewCentreline` subelement to its preview visual identity and
canonical transition identity. The internal fixture adds no application
command, product import, App proxy, custom property, `Part` shape, persisted
schema or save route. Disposal clears selectable and rendered children
fail-closed; deleting the disposable object owns final removal of the
registered empty display-mode node.

The focused standalone proof covers display-mode attachment, selection-path
mapping, structured rejection, partial-attach cleanup and retryable partial
disposal. A direct-root prototype rendered but crashed Pivy before FreeCAD
could invoke the selection callback, classified `implementation-defect`.
Registering the selection root as a display mode repaired the lifecycle. A
separate startup race was classified `fixture-or-harness-defect`; the retained
runner now waits for a visible main window and absent splash screen instead of
using a fixed delay.

The clean qualified FreeCAD 1.1.1 real-GUI command
`tools/freecad_bridge/run-phase5-transition-viewprovider` passed. It observed
one document object, one added display mode, no added root child and no
`Part` shape; the visible screenshot contained 4,188 red pixels and the hidden
screenshot zero. FreeCAD emitted a selection event for
`TransitionPreviewCentreline`, which mapped to
`transition:phase5:viewprovider-gui` and its stable preview visual identity.
Disposal and document removal left no open document. Both screenshots were
visually inspected.

An independent read-only review reran the focused scene, ViewProvider and
project-progress validators, parsed the changed Python, inspected both
screenshots and found no blocking defect. Its verdict was to retain this
development-only fixture without treating it as renderer or exit acceptance.

PR-14 remains Open/Remove but its control is now **Partial**: bounded display,
visibility and programmatic subelement selection work. Mouse-driven picking,
application-command editing, atomic Undo/Redo, failure recovery, save/reopen,
cache invalidation and representative resource measurements remain unproved.
No renderer or Phase 5 exit is accepted.

## Real pointer-selection tranche

This Level 2 tranche replaces the fixture's programmatic selection step with
an actual Qt pointer route. The qualified real-GUI proof finds a rendered red
centreline pixel in the active 3D view, resolves the containing
`QOpenGLWidget`, moves the pointer to that pixel and issues a left-button
click. Test-only instrumentation is reset after the hover event and before the
click, so the retained assertion proves that the click itself invoked
`getElementPicked`. The resulting FreeCAD selection event must carry
`TransitionPreviewCentreline` and resolve to the existing stable preview
visual identity and canonical transition identity.

The old proof first failed the new runner contract because it reported no
mouse input or pick callback. The initial Qt mouse-click harness could select
the whole object before the pointer/focus lifecycle was established,
classified `fixture-or-harness-defect`; activating the view, focusing its
OpenGL widget and moving the pointer before the measured click repaired that
boundary. A later five-session stress run exposed one more harness defect:
global `QApplication.widgetAt` lookup introduced a desktop exposure dependency
and found no widget in one session. Direct lookup inside the active FreeCAD
3D-view hierarchy removes that dependency. The first direct lookup used the
pre-Qt-6 namespace and failed under PySide6, also classified
`fixture-or-harness-defect`; importing `QOpenGLWidget` from
`QtOpenGLWidgets` repaired the qualified profile without changing product
behaviour.

The original real-GUI command then passed in six consecutive fresh FreeCAD
1.1.1 sessions. Each run clicked the `QOpenGLWidget`, invoked
`getElementPicked` at least once after instrumentation reset, emitted the
stable subelement selection event, mapped both identities, kept one disposable
object and display mode, created no `Part` shape, and closed the document.
The visible/hidden screenshot checks remained 4,188/0 red pixels.

PR-14 remains Open/Remove with **Partial** control: mouse-driven subelement
selection is now proved for this bounded fixture. Representative selection
scale, application-command editing, atomic Undo/Redo, failure recovery,
save/reopen, cache invalidation and resource measurements remain unproved.
No renderer or Phase 5 exit is accepted.

## Application-command edit and atomic Undo/Redo tranche

This Level 2 tranche adds an internal application command that replaces one
complete transition intent, preserves stable identity, refreshes its accepted
analysis and delegates the write through an injected edit port. The qualified
FreeCAD port uses the existing Phase 4 canonical properties and transaction;
it defers automatic ViewProvider callbacks while the write is open, swaps the
disposable Coin scene before commit and restores the prior canonical state and
preview after failure. `updateData` then handles valid Undo/Redo property
changes. An exact no-op creates no transaction. The command is absent from
`tracktemplate.api`, the product macro and operator UI.

The focused test first failed because the command module did not exist,
classified `implementation-defect`. Its first retained run then omitted the
standard-library import from a structural expectation, classified
`test-or-oracle-defect` and corrected without weakening the boundary. The
qualified headless proof likewise exposed the intentionally absent FreeCAD
edit port; FreeCADCmd returned zero but emitted an exception instead of the
required success sentinel, so the run remained failed and was classified
`implementation-defect`. Updating the exit wording later exposed a stale
exact-string progress expectation, classified `test-or-oracle-defect`; the
accepted 0/4 wording was updated and the original validator passed.

After implementation, the command, ViewProvider refresh and adjacent Phase 4
state/derived/preview regressions passed. Qualified FreeCAD 1.1.1 headless
proofs printed their required edit, persistence and Coin sentinels. The
complete standalone CI profile passed 48/48 validators. Three clean isolated
real-GUI runs passed through
`tools/freecad_bridge/run-phase5-transition-viewprovider`. Each retained one
`App::FeaturePython` object and one display mode, created no `Part` shape,
changed the preview signature and visible centreline from 4,188 to 4,740 red
pixels, recorded exactly one Undo unit and zero units for a no-op, restored
the 4,188-pixel image exactly on Undo and the 4,740-pixel image exactly on
Redo, and restored canonical state, history, identities and the 4,740-pixel
image after an injected preview-refresh failure. The captured initial, edited,
Undo and recovered states were visually inspected.

The implementation follows the first-party ViewProvider `updateData` lifecycle
and document transaction semantics reviewed on 2026-07-28 from the
[FreeCAD Addon Academy](https://freecad.github.io/Addon-Academy/Guides/Code/Document-Objects/)
at `833bb4852af825e1826b83d6b75872d18b433486` and the
[FreeCAD document API](https://freecad.github.io/SourceDoc/d8/d3e/classApp_1_1Document.html).
No save/reopen route, persisted-schema or custom-property change, product
command, cache-invalidation claim, exact geometry/export, renderer acceptance
or Phase 5 exit is included.

PR-14 remains Open/Remove with **Partial** control: one bounded
application-command edit, atomic Undo/Redo and transactional failure recovery
are now proved. Representative editing and selection scale, save/reopen,
cache invalidation, resource measurement and renderer acceptance remain open.

## Retained preview-cache regression tranche

This Level 2 test-led tranche retains one existing
`TransitionDerivedCache` for the development ViewProvider lifecycle and
injects its artifact function through the existing refresh seam. It adds no
cache implementation, public API, persisted state, custom property or product
wiring. The standalone regression covers cold creation, exact reuse,
edit/Undo/Redo/change-back invalidation, equal change-back payloads, failure
recovery and explicit cache disposal.

The first focused run reached the newly required GUI-runner fields and failed,
classified `fixture-or-harness-defect`; the repair remained inside the
development GUI fixture and runner. Qualified FreeCAD 1.1.1 headless
validation then printed its transition-edit sentinel with one-unit edit and
change-back history plus exact rollback. The first isolated GUI run exposed a
new assertion that compared Pivy wrapper identity rather than underlying Coin
node identity, classified `test-or-oracle-defect`. Comparing the accepted
node ID repaired that oracle, and the original command then passed in three
consecutive fresh isolated sessions.

Each retained GUI run used one cache for 11 requests, including two exact
reuses, and deterministically restored the initial and edited source
signatures through edit, Undo, Redo, change-back and injected failure. It kept
one `App::FeaturePython` object and one display mode, created no `Part` shape,
and restored the within-session 4,188/4,740-pixel visual states. Initial,
edited and change-back captures were visually inspected. These are semantic
within-session comparisons, not screenshot hashes or numerical timing gates.
The required standalone CI workflow remains unchanged and does not run the
GUI host.

The first-party ViewProvider and transaction guidance was rechecked on
2026-07-29 at the same Addon Academy revision
`833bb4852af825e1826b83d6b75872d18b433486`. No save/reopen route,
performance acceptance, renderer acceptance or Phase 5 exit is included.
PR-14 and PR-16 remain Open with **Partial** controls.

## Programmatic regression pipeline automation

This Level 2 tooling and validation-policy tranche makes retained regression
execution independent of phase closeout. One standard-library local runner
composes syntax and complete standalone checks by default, adds the qualified
headless transition lifecycle through a durable `transition` profile, and
adds the isolated real-GUI proof only through the explicit
`transition-gui` profile. Raw output remains in ignored per-run log
directories while the terminal emits concise step results and one structured
sentinel.

The focused runner contract first failed because the accepted tool did not
exist, classified `implementation-defect`; the repair boundary is limited to
the local runner, its direct test and the canonical testing/validation
documents. The contract covers profile composition, raw failure retention,
missing-sentinel rejection and fail-fast exclusion of later expensive layers.

The default pipeline passed tracked parsing and all 49 standalone validators.
The first `transition-gui` invocation then stopped before later layers when its
sandboxed subprocess could not connect to Flatpak, classified
`environment-or-profile-defect`. The exact command reran under the approved
qualified host and passed all six sentinels: parsing, standalone contracts,
transition persistence, Coin scene, edit lifecycle and the isolated real-GUI
ViewProvider regression.

Hosted CI remains the deterministic standalone matrix and no screenshot hash,
timing threshold or mandatory GUI-host workflow is added. These results do not
accept the renderer or a Phase 5 exit. Phase status, risks and decisions are
unchanged.

## Disposable preview save/reopen regression tranche

This Level 2 test-first tranche extends the development-only GUI fixture and
durable `transition-gui` profile. Before saving, the fixture disposes its Coin
graph and retained `TransitionDerivedCache`, clears the ViewObject proxy and
keeps the existing single `App::FeaturePython` object. After reopen, the proof
reads the same canonical state and manually constructs a new empty cache,
preview artifact and ViewProvider fixture. This is lifecycle evidence, not an
automatic product load hook.

The focused test first failed at the old runner requirement that the save route
remain unused, classified `fixture-or-harness-defect`. Qualified FreeCAD then
exposed two restore-only display-mode assumptions, both classified
`fixture-or-harness-defect`, plus its integer ViewObject proxy sentinel,
classified `test-or-oracle-defect`. Proxy assignment after restore also did
not replay `attach`, an `implementation-defect` in the development fixture; a
bounded explicit-attach fallback repairs it. Because product load wiring
remains excluded, the proof activates the rebuilt Coin switch child directly
rather than claiming restored display-mode registration.
Updating the current exit disposition then exposed one stale exact-string
progress expectation, classified `test-or-oracle-defect` and aligned without
changing the 0/4 count or accepting an exit.

FreeCAD 1.1.1 saved and reopened one object with the same name, stable identity,
canonical JSON, App and ViewObject property lists, and no `Shape`. The FCStd
archive contained none of the fixture, cache or ViewProvider module markers.
The replacement cache began `missing`, was a different instance, and rebuilt a
different artifact with the same source signature and preview payload. A new
ViewProvider and new Coin nodes rendered the reopened centreline with 4,188 red
pixels; the original and reopened captures were visually inspected.

The complete `transition-gui` regression passed all six layers, including
tracked parsing, 49/49 standalone validators, qualified persistence, Coin
scene, edit lifecycle and isolated real-GUI proof. Raw logs are retained under
`benchmark-output/validation-pipeline/20260729T135422090742Z/`. No persisted
schema, product command, operator route, screenshot hash, timing gate, renderer
acceptance, risk treatment, authority decision or Phase 5 exit changes.

## Continue development workflow automation

The project owner classified this as Level 2 and authorised
`$tracktemplate-continue` as one explicit clean-main development cycle. It may
integrate one previous green Level 1 or Level 2 pull request, synchronise
protected `main`, implement one next bounded tranche and delegate its
publication to `$tracktemplate-publish`. It stops for failed or non-exact CI,
blocking review, conflicts, scope drift or Level 3 authority, and never merges
the newly published draft in the same invocation.

The first agent-guidance proof failed because the initialised skill was not yet
registered, classified `implementation-defect`. After the complete skill,
register and delegated-publication route were added, the skill-creator,
agent-guidance and resource-routing validators plus the complete 49/49
standalone matrix passed. The authorised pilot verified PR #10 at green head
`7e7b37c`, marked it ready, merged it normally as `5cf7cc7` and fast-forwarded
clean local `main`. No phase status, exit, risk, decision, product behaviour or
release authority changes.

## Bounded Coin resource profile tranche

This Level 2 evidence-tooling tranche fixes one 32-logical-object candidate
fixture without changing product source. Each object keeps one compact
canonical `App::FeaturePython` record, one 32-segment renderer-neutral preview,
one disposable Coin layer, one selectable root, one display mode and one
retained cache. The profile starts three fresh isolated qualified FreeCAD GUI
processes, performs one cold construction per process, then one untimed
same-state warm-up and three measured unchanged refreshes per process.
Correctness invariants fail closed; wall time, process CPU, explicit recompute
duration and end-minus-start RSS remain descriptive observations without a
threshold.

The focused validator first failed because its text scan treated an embedded
bridge-code string as a host-side FreeCAD import, classified
`test-or-oracle-defect`; an AST import check repaired the oracle. An excluded
GUI attempt produced no sample and failed to retain the mutable launcher log,
so its within-session sandbox diagnosis is not used as independent evidence.
The repaired profiler now retains launcher output on child failure. The exact
command ran through the approved qualified host and all three fresh FreeCAD
1.1.1 samples passed.

Every cold process retained exactly 32 document objects, 32 logical preview
layers, 32 added display modes and 224 active Coin nodes below the selectable
roots, with no `Shape` property and the same stable identity digest. Cold wall
time was 852.459 ms median (850.431–867.260), explicit recompute was 3.939 ms
(3.841–3.992) and RSS grew 20.270 MiB (20.121–20.297). Across nine measured
warm observations, wall time was 16.247 ms median (15.225–20.511), explicit
recompute was 0.217 ms (0.212–0.327) and end-minus-start RSS was 0.007812 MiB
(0.003906–0.007812). Every warm action reused all 32 derived artifacts but also
built and discarded candidate Coin bindings; it regenerated no preview,
changed no active scene and preserved cross-process object, actual-layer,
active-node and identity counts. Active nodes and RSS are before/after, not
transient peaks. Each process disposed all proxies and caches and left no
document or isolated FreeCAD process.

The method, individual samples, raw hash and limits are in the
[sanitised profile](../benchmarks/2026-07-29-phase5-transition-coin-resource-profile.md).
The 32-object fixture is a bounded diagnostic scale, not accepted as
representative product capacity, interaction budget or renderer suitability.
It does not exercise representative multi-object pointer selection or editing,
and it adds no product load wiring, schema, exact/export path or runtime
dependency. Phase 5 remains 0/4; PR-14 remains Open/Remove with **Partial**
control and its structured risk record is unchanged.

The final `transition-gui` regression pipeline passed parsing, all 50
standalone validators, qualified transition persistence, Coin scene and edit
lifecycle checks, and the isolated real-GUI ViewProvider check with every
required sentinel. A fresh read-only reviewer then passed the complete tranche
with no missing, extra, unverifiable or defective finding after independently
checking the purpose and recompute contracts, raw/source/report/manifest
hashes, evidence wording and scope.

## Representative multi-object selection and edit tranche

This Level 2 test-and-evidence tranche defines the smallest complete
multi-object workload for the currently qualified
`plain-line-spacing-matched-transition-intent` family. One secondary track
produces exactly two canonical records, Entry and Exit, so that pair—not the
separate arbitrary 32-object resource fixture—is representative of the
accepted fixture-only family shape. The two deterministic transition lengths
make the local development previews visually distinct for pointer selection;
they are test inputs, not product defaults, capacity evidence or a whole-layout
population.

The retained product paths are unchanged. A new host-independent workload
definition supplies the stable `SET-001/curve-track/2/transition/entry` and
`.../exit` identities. The real-GUI proof creates both compact
`App::FeaturePython` records atomically, attaches the existing development-only
Coin ViewProvider and retained cache to each, then uses a real Qt mouse click
to select the red Exit subelement. It applies one existing internal
application-command edit to that selected object, follows it through one Undo
and Redo, and injects one pre-commit preview-refresh failure. Every stage must
preserve both stable mappings, the untouched Entry canonical state/cache, two
document objects, two logical Coin layers, 14 active selectable-scene nodes,
zero `Shape` properties and the exact Undo/Redo history. The failed edit must
restore the selected canonical state and cache without adding history.

The existing isolated ViewProvider runner executes this proof after its
single-object selection/edit/save-reopen regression from a new empty document
in the same qualified GUI process. The 2026-07-29
`transition-gui` regression profile passed all six requested steps, including
51/51 standalone validators and qualified FreeCAD 1.1.1 persistence, Coin
scene, edit-lifecycle and real-GUI proofs. The retained multi-object result
selected `SET-001/curve-track/2/transition/exit` through a real Qt mouse click
and preserved two objects, two layers, 14 active selectable-scene nodes, zero
`Shape` properties and both stable mappings. Edit, Undo, Redo and failed-edit
recovery caused exactly five selected-cache regenerations/requests with zero
reuse; the Entry cache recorded zero requests, regenerations or reuse.

During development, one exact-float expectation was classified as a
**test-or-oracle defect** because the accepted analytical round trip is
tolerance-bound; it now uses the existing `GEOMETRY_TOLERANCE`. Pointer
targets contaminated by viewport furniture or too close to the viewport edge
were classified as **fixture-or-harness defects**; the proof now chooses the
most interior uniquely hittable canonical segment and reconciles Qt and Coin
coordinates before clicking. No product selection logic was changed.

The exact pre-repair command, source state, sentinel, raw output and first
assertion were not preserved for either failure, contrary to the failed-test
adjudication policy. The classifications remain technically supported by the
retained tolerance and pointer-selection contracts, and the repaired exact
qualified profile passes, but their chronology and original failing runs are
not independently auditable. This is a process-evidence gap, not product
behaviour or acceptance evidence.

No product load hook, persisted schema, public API, exact/export path,
dependency, renderer acceptance, owner editing-behaviour acceptance or Phase 5
exit is included or accepted. PR-14 remains Open/Remove with **Partial**
control and the structured risk and decision records are unchanged.

## Development-only post-open attachment boundary tranche

This Level 2 tranche replaces manual per-object reconstruction in the
save/reopen fixture with one explicitly invoked, development-only document
attachment boundary. The FreeCAD adapter now has one read-only enumeration
operation that ignores foreign records, validates every canonical transition
record, rejects duplicate stable identities and returns `(object, state)`
pairs in transition-ID order. The presentation fixture consumes that operation
through injected callbacks, creates one new disposable preview cache and
ViewProvider per record, and clears every completed live binding and cache if
any attach fails. It rejects an existing non-default ViewProvider rather than
overwriting it and restores each original default proxy on failure or disposal.

The selected composition is deliberately post-open and explicit. Import-time
or global document-observer wiring was rejected for this tranche because the
qualified Python observer boundary has no reliable finish-restore callback,
callbacks may see partially restored properties, and global registration would
prematurely resemble a product default. The fixture is not imported by
`tracktemplate.api`, package initialisation or `TrackTemplate.FCMacro`; it
adds no observer, command, custom property, transaction, schema or persisted
proxy state.

The first focused command failed with an `ImportError` because the authorised
attachment module did not yet exist, classified `implementation-defect`.
The exact default regression pipeline retained that failure at
`benchmark-output/validation-pipeline/20260729T181635090648Z/`: tracked parsing
passed and 50/51 standalone validators passed, with only the new ViewProvider
proof failing. After implementation, the same focused proof passed. Its
host-independent two-record fixture supplies records out of order, proves
stable attachment order and independent refresh/reuse, restores both original
proxies and empties both caches on disposal, and rolls back the first completed
attachment's live contents, cache and proxy after an injected second-object
failure without changing either canonical state. The documented empty switch
child remains for that completed attachment.

A final adversarial diagnostic check first failed because an injected proxy
restoration failure hid the original attach failure from the structured error
text, classified `implementation-defect`. The cleanup owner now preserves the
primary failure and appends the secondary cleanup failure; the exact focused
proof passed without weakening either recovery assertion.

The qualified FreeCAD 1.1.1 persistence proof passed. It enumerated two
canonical records in stable-ID order while ignoring one operator object and
one other TrackTemplate record, and retained the exact object/property
inventory, payloads and Undo/Redo counts. Duplicate identities fail closed.
The isolated real-GUI command
`tools/freecad_bridge/run-phase5-transition-viewprovider` also passed. After
save/reopen, an injected Coin selection-root failure restored the original
integer-or-null host proxy and left canonical JSON, properties, object count,
history and view-node counts unchanged. A subsequent explicit attachment
enumerated the one existing record, rebuilt a new equivalent cache,
ViewProvider and Coin graph, reused an unchanged refresh and rendered 4,188 red
pixels. Disposal cleared the preview cache and selectable children, restored
the original host proxy and again left the stored snapshot and history
unchanged. FreeCAD exposes no Python operation to unregister a display mode,
so the proof also requires the known development-fixture limitation: the
original public display-mode list is restored but one empty switch child
remains until object deletion or document close/reopen. No live Coin child,
selection mapping or cache remains in that slot. An intermediate assertion
expected a retained public mode name and failed with `IndexError` in the
qualified host, classified `test-or-oracle-defect`; aligning it to the observed
public-list/switch-child split changed no product behaviour.

The final `transition-gui` regression profile passed all six layers: parsing
160 tracked Python/FCMacro files, 51/51 standalone validators, qualified
transition persistence, Coin scene, edit lifecycle and the isolated real-GUI
ViewProvider proof. Raw logs are retained under
`benchmark-output/validation-pipeline/20260729T184223671826Z/`. The original
and post-open 1000×700 captures from the final GUI run were visually inspected;
both show the same clean red transition centreline and each contains the
required 4,188 red pixels.

The lifecycle choices follow first-party guidance reviewed on 2026-07-29 from
the [FreeCAD Addon Academy document-object guide](https://freecad.github.io/Addon-Academy/Guides/Code/Document-Objects/)
at revision `833bb4852af825e1826b83d6b75872d18b433486`, the qualified
FreeCAD 1.1.1 `DocumentObserverPython` sources at
`0108fd4b4850cc46e625b60e53cea7a7bbe69f8d`, and the
[FreeCAD ViewProvider Python API](https://freecad.github.io/SourceDoc/d9/dbf/classGui_1_1ViewProviderPythonFeatureT.html).
This evidence accepts neither product load wiring nor supported migration.
No renderer, owner editing behaviour or Phase 5 exit is accepted; PR-14
remains Open/Remove with **Partial** control and the risk and decision
registers are unchanged.

## Representative save/reopen attachment tranche

This Level 2 test-and-evidence tranche extends only the existing representative
GUI fixture, its runner contract and the validation owners. After the retained
Entry/Exit pointer-selection and edit lifecycle, the proof disposes both manual
ViewProviders and caches, saves the two canonical `App::FeaturePython`
records, closes and reopens the FCStd, then invokes the existing
development-only document attachment explicitly. No product source, load hook,
observer, command, schema, property or runtime dependency changes.

The test-first standalone profile stopped at the newly required `saveAs`
contract with 50/51 validators passing, classified
`fixture-or-harness-defect` because the GUI proof had not yet implemented the
required exercise; the exact logs are under
`benchmark-output/validation-pipeline/20260731T065424831459Z/`. A static
assertion then required an incidental literal dictionary shape, classified
`test-or-oracle-defect` and replaced by the named payload-boundary check; that
failure is retained under
`benchmark-output/validation-pipeline/20260731T065825986959Z/`. The qualified
GUI proof subsequently exposed one deleted FreeCAD-wrapper access and one
restore-only `DisplayMode` assignment, both
`fixture-or-harness-defect`, plus an incorrect expectation that an unchanged
refresh return its artifact rather than `False`, a `test-or-oracle-defect`.
The repairs snapshot plain identifiers before close, relinquish the deleted
document handle, retain cache-identity assertions and activate the rebuilt
switch children through the already qualified route. Those three GUI attempts
left their FCStd artifacts under run directories
`20260731T065947200499Z`, `20260731T070056548727Z` and
`20260731T070154732864Z`, but their raw bridge output and exact interim
source-state packets were not retained. Their proposed classifications and
chronology are therefore not independently auditable, and none is treated as
passing evidence.

The subsequent six-layer profile under
`benchmark-output/validation-pipeline/20260731T070525796802Z/` stopped at the
project-progress assertion that the current Phase 5 exit evidence had drifted.
This was classified `implementation-defect` in the retained documentation: an
attempted evidence edit had changed the validator-controlled 0/4 exit
disposition without Level 3 authority. Restoring the accepted disposition
repaired the documentation scope; no validator or phase authority changed.

The exact qualified FreeCAD 1.1.1 command
`tools/freecad_bridge/run-phase5-transition-viewprovider` passed. The reopened
attachment enumerated
`SET-001/curve-track/2/transition/entry` then
`SET-001/curve-track/2/transition/exit`, rebuilt two new equivalent caches and
Coin layers, retained two objects, two logical layers, 14 active selectable
scene nodes and zero `Shape` properties, and preserved both pre-save stable
selection mappings. Refreshing unchanged Exit reused its artifact without
changing Entry state, visual source or mapping. Before that refresh, the proof
deliberately discarded Entry's cache artifact; it remained missing afterwards
while Entry's bound source signature and selection root stayed identical. This
observable trap establishes that the Exit request did not request or rebuild
the sibling cache. Batch disposal cleared both caches and selection roots,
restored both original host proxies and changed neither canonical JSON,
properties, object count nor reopened history.

The retained 1000×700 reopened capture contains 5,234 red pixels and was
visually inspected; it shows the two distinct representative centrelines. As
with the one-object proof, disposal restores each public display-mode list but
leaves one empty switch child per record until object deletion or document
close/reopen. The first-party document-object guidance was rechecked on
2026-07-31 at unchanged Addon Academy revision
`833bb4852af825e1826b83d6b75872d18b433486`; the qualified FreeCAD 1.1.1
revision remains `0108fd4b4850cc46e625b60e53cea7a7bbe69f8d`.

The complete `transition-gui` profile passed tracked parsing, all 51
standalone validators, qualified transition persistence, Coin-scene and edit
lifecycle checks, and the isolated real-GUI proof. Raw logs are retained under
`benchmark-output/validation-pipeline/20260731T072127239431Z/`.

This is representative evidence only for the accepted fixture-only family
shape. It establishes no whole-layout capacity, interaction budget, automatic
product load route, supported migration, renderer acceptance or owner
editing-behaviour acceptance. Phase 5 remains 0/4; PR-14 remains
Open/Remove with **Partial** control and the risk and decision registers are
unchanged.

## Coin maintainability and reuse review tranche

This Level 2 evidence-only review assesses the retained Coin candidate against
the renderer-neutral preview contract and accepted dependency direction. It
changes no source, supported interface, composition route or behaviour. The
review recommends retaining the current separation as the smallest reversible
option; it does not recommend product promotion or accept a renderer.

The current ownership map separates authoritative definitions from deliberate
validation at an injected boundary:

| Invariant or responsibility | Authoritative implementation and boundary |
| --- | --- |
| Canonical transition intent and stable-identity validation | `tracktemplate/domain/transition.py`; `TransitionIntent` owns the FreeCAD-independent inputs and validates `transition_id` |
| Transition and easement mathematics | `tracktemplate/domain/alignment.py`; the domain owns the railway calculation used by the application analysis |
| Versioned transition state and analysis lifecycle | `tracktemplate/application/transition_state.py`, exposed through the narrow `tracktemplate.api` façade; it owns state, analysis orchestration, signatures, status and JSON |
| Complete derived-stage signatures and disposable cache policy | `tracktemplate/application/transition_derived.py`, exposed through `tracktemplate.api`; adapters and renderers do not invent cache keys |
| Renderer-neutral centreline scene, units, frame, semantic layer and visual/domain identities | `tracktemplate/presentation/transition_preview.py`, exposed through `tracktemplate.api`; this is the only retained preview sampler |
| Coin style signature, node construction and node-to-domain mapping | `tracktemplate/presentation/transition_coin.py`; an internal presentation adapter that consumes a preview artifact and owns one disposable binding |
| Per-ViewObject display, selection, refresh and retryable cleanup | `tracktemplate/presentation/transition_coin_viewprovider.py`; a development-only fixture that owns its selection root and Coin binding |
| Explicit multi-record attachment, callback-boundary validation, cache/proxy ownership and batch rollback | `tracktemplate/presentation/transition_coin_attachment.py`; a development-only fixture that validates and normalises injected records before it attaches them |
| FreeCAD record enumeration and canonical persistence | `tracktemplate/adapters/freecad/transition_state.py`; `read_transition_objects()` owns document membership, record validation, duplicate rejection and stable-ID ordering |
| Validated edit intent and atomic FreeCAD transaction integration | `tracktemplate/application/transition_edit.py` owns the command. `FreeCADTransitionStore._update()` owns the property write, verification, commit and abort path; `FreeCADTransitionEditPort` coordinates that mutation with deferred preview refresh and recovery |

The adapter is authoritative for enumerating canonical FreeCAD records. The
attachment fixture deliberately rechecks document membership, duplicate object
and stable identities, and stable-ID order because its injected callback can
return arbitrary records; the standalone attachment validator supplies
reversed records to prove that boundary. This is adapter-neutral defensive
validation, not a second persistence or identity authority. Retire it only if
an accepted, typed composition contract guarantees validated and ordered
callback results.

The modular-structure guard reports no cycle, prohibited layer edge, forbidden
domain dependency or structural warning. Presentation imports only
presentation, application and domain modules. The Coin module is injected, the
ViewObject is capability-checked and the document adapter is supplied through
callbacks; retained presentation source imports neither `FreeCAD`,
`FreeCADGui`, Qt/PySide, `pivy` nor the FreeCAD adapter. Coin fixtures remain
absent from `tracktemplate.api`, package initialisation and
`TrackTemplate.FCMacro`.

Four options were reviewed:

| Option | Review disposition |
| --- | --- |
| Retain the layered, product-route-disabled Coin candidate | Recommended. It preserves the renderer-neutral contract, narrow lifecycle ownership and reversible composition while later evidence remains open. |
| Promote the current fixture into automatic product composition | Deferred. Explicit post-open invocation, restoration limits, product loading and owner editing-behaviour acceptance remain unresolved. |
| Extract all similar test code during this review | Deferred to separate mechanical tranches. Mixing helper movement with the evidence review would obscure whether GUI coverage changed. |
| Implement the SVG/Qt fallback for comparison | Not authorised or presently justified. No Coin failure has triggered the fallback and no SVG/Qt prototype exists. |

No second product implementation of transition geometry, derived signatures,
Coin construction or attachment lifecycle was found. The review identified
these test-owned duplication boundaries and retirement conditions:

| Fixture duplication | Owner and retirement condition |
| --- | --- |
| `_process_gui` was repeated in the one-object, representative and resource-profiler workflows; `_SelectionObserver` and `_ObservedTransitionCoinViewProviderFixture` were repeated in the two real-GUI proofs | Phase 5 GUI and performance QA owners. **Retired by the Coin GUI harness consolidation tranche below:** one test-owned helper now serves all three workflows after both real-GUI proofs and the resource profile retained their workloads, sentinels, correctness invariants and comparable measurement recipe and fields. Timing and RSS observations remain descriptive rather than exact-value gates. |
| Fake Coin field/group/node primitives occurred in both standalone Coin validators | Phase 5 presentation QA owner. **Retired by the Coin fake-protocol consolidation tranche below:** one minimal test-owned protocol now serves both validators after their scene-only and ViewProvider selection, replacement and failure regressions passed unchanged. |
| One-object, representative and resource fixtures each compose caches and ViewProviders manually | Their respective QA/performance owners. This is intentional lower-boundary instrumentation, not another renderer. Replace duplicated composition only after an accepted product composition boundary exposes equivalent selection, failure and measurement observations; retain distinct regressions that protect different behaviour. |

The explicit post-open boundary remains a limitation: there is no product load
hook or accepted observer lifecycle. The empty-switch-child behaviour also
remains: disposal clears every live Coin child, mapping and cache and restores
the original public display-mode list and host proxy, but FreeCAD provides no
qualified Python removal operation for the registered switch child. Closure
requires either a supported removal mechanism or an accepted product lifecycle
that confines the residual empty child to object deletion/document close and
presents that limitation for owner acceptance.

The SVG/Qt fallback has no implementation, selection mapping, editing,
Undo/Redo, save/reopen, cleanup, object/layer, resource or maintainability
evidence. The review therefore cannot make a relative renderer comparison.
The fallback remains available only if later Coin evidence fails; its missing
evidence is not converted into a requirement to build a second renderer.

Focused standalone preview, Coin-scene, ViewProvider, representative workload
and modular-foundation validators all passed. No GUI was rerun because this
review changes documentation only and relies on the existing retained
real-GUI evidence without upgrading it. The documentation-only delta is the
required review output itself, so its evidence necessarily exceeds its zero
implementation lines; no policy, phase, risk, decision or authority changes.
Phase 5 remains 0/4 and PR-14 remains Open/Remove with **Partial** control.

## Coin GUI harness consolidation tranche

This Level 2 test-only mechanical refactor moves the exactly shared
`_process_gui`, `_SelectionObserver` and
`_ObservedTransitionCoinViewProviderFixture` primitives to one helper. The
one-object, representative and resource-profiler workflows retain their
existing composition, workloads, sentinels and assertions; product source,
PySide/Qt compatibility, callback counts, screenshots, measurement fields and
timing/RSS interpretation are unchanged. A standalone structural contract now
requires the helper to remain the only definition owner and all three intended
workflow consumers to import it.

The focused structural proof stopped at the missing helper, classified
`fixture-or-harness-defect`, then passed after the bounded extraction. Its
exact failing output was observed in the working session but not retained in a
raw run directory, so the chronology is not independently auditable. The
complete `transition-gui` profile passed all six layers under
`benchmark-output/validation-pipeline/20260731T114226102952Z/`, including 161
parsed files, 51/51 standalone validators and the qualified real-GUI proofs.
The three-process Coin resource profile under
`benchmark-output/freecad-bridge/phase5-transition-coin-resource-runs/20260731T114159577093Z-profile/`
hashes the shared helper and retained 32 objects/layers, 224 active nodes, zero
`Shape` properties, nine unchanged warm observations with full cache reuse,
all measurement fields and complete cleanup; timings remain descriptive. The
one-object and representative captures were visually inspected. No renderer,
exit condition, risk treatment, product route or owner acceptance changes;
Phase 5 remains 0/4 and PR-14 remains Open/Remove with **Partial** control.

## Coin fake-protocol consolidation tranche

This Level 2 test-only mechanical refactor moves the union of the fake Coin
field, group, drawing-node and selection-root protocol to one helper shared by
the standalone scene and ViewProvider validators. A direct contract exercises
field values, group lookup/replacement/removal and selection-root creation,
requires one definition owner and requires both intended consumers to import
it. The existing scene construction, mapping, disposal and injected failures,
plus the ViewProvider selection, replacement, refresh, attachment and cleanup
regressions, remain distinct and unchanged. Product source and GUI workflows
do not import the helper.

The test-first standalone pipeline stopped only at the missing helper with
50/51 validators passing under
`benchmark-output/validation-pipeline/20260731T120146543494Z/`, classified
`fixture-or-harness-defect`. The first union omitted the ViewObject contract's
existing `getChild` capability; the exact focused failure is retained under
`benchmark-output/validation-focus/20260731T120348Z/`, also classified
`fixture-or-harness-defect`. Restoring that load-bearing fake capability made
the original command pass. The complete standalone pipeline then parsed 162
files and passed 51/51 validators under
`benchmark-output/validation-pipeline/20260731T120508110510Z/`. No FreeCAD or
real-GUI run applies because only host-independent test fakes changed; no
product source, renderer disposition, exit condition, risk treatment or owner
acceptance changes. Phase 5 remains 0/4 and PR-14 remains Open/Remove with
**Partial** control.

<a id="repository-driven-continuation-authority-panel"></a>

## Repository-driven continuation authority panel and owner decision

**Decision and source state:** This Level 3 governance decision starts from
branch `agent/automate-tracktemplate-continue` at
`5fa9da017a60ac1dee5a70d4c8ebb8fb97fc9052`; local `main` and `origin/main`
were at the same commit. The prospective panel reviewed the complete initial
working-tree proposal: seven modified guidance/test files and four new chief-
of-staff and technical-lead skill/metadata files. No product, FreeCAD,
railway, persistence, export or current-status file was changed in that source
state. A strictly read-only staff review classified repository-driven outcome
selection as Level 3 and blocked the alternate natural-language trigger.

**Participants, evidence and independence:** Richard is project owner,
decision chair and accepting authority. Codex is change owner and presenter. A
fresh independent QA/risk reviewer challenged the proposal and made no
implementation, repository or external-state change. The reviewer was given
the intended decision and prior blockers, but checked them against the raw
diff rather than treating them as accepted. The panel reviewed repository
`AGENTS.md`, the [engineering policy](../ENGINEERING_POLICY.md),
[dashboard](../PROJECT_PLAN.md), [live risks](risks.json), existing
[decisions](gate-decisions.json), [recovery policy](../RECOVERY_AND_BACKUP.md),
[agent workflow catalogue](../AGENT_WORKFLOWS.md), the continue, publish,
chief-of-staff, technical-lead, validation and quality-review skill contracts,
and the agent-guidance and project-progress validators. Focused agent-guidance,
project-progress, QA/link and whitespace checks passed against the prospective
source; complete final-source standalone validation and a fresh read-only
staff review remained conditions of retention.

**Risk disposition:** No risk state, treatment or control-effectiveness value
changes:

| Risk | Panel disposition |
| --- | --- |
| PR-12 — governance duplication/staleness | Remains Open/Mitigate/**Partial**. The skill surface grows from 25 to 27, but fixed owners, direct routing, structural validation and one canonical decision record bound the added surface. |
| PR-13 — destructive command/history/data exposure | Remains Open/Mitigate/**Effective (current scope)** while every cycle retains clean-tree ownership, exact-head CI, normal protected merge, idempotent recovery and all destructive-operation exclusions. The Critical severity required the independent challenger. |
| PR-20 — scope expansion | Remains Open/Mitigate/**Effective (current scope)** with one outcome, exact candidate classification, named contribution, maintenance non-promotion, a clean stop and a Level 3 stop. |
| PR-22 — unchallenged authority transfer | Remains Open/Remove/**Effective (current scope)** because this panel and the linked owner decision precede activation and delegate no later Level 3 decision. |
| PR-14, PR-15, PR-16, PR-17, QA-R03 and QA-R04 | Remain unchanged. Their product, GUI, performance, signature, persistence and recovery evidence applies only if a later authorised outcome reaches the affected boundary. |

**Recommendation, conditions and unknowns:** The independent recommendation is
**Proceed with bounded conditions**:

| Accountable owner | Deadline or trigger | Condition |
| --- | --- | --- |
| Project owner | Before authority transfer | Accept the exact explicit-only decision and all exclusions. |
| Agent-guidance owner | Before retention | Remove every alternate natural-language activation route, retain `allow_implicit_invocation: false` and protect the literal invocation contract with a focused check. |
| Agent-guidance owner | Before final validation | Allow only `BLOCKER` findings to return to implementation, with at most two repair-and-review passes; never repair other finding classes in that cycle. |
| Continuation agent | Before branch creation in every invocation | Reconstruct canonical authority, classify credible candidates, select at most one already-authorised Level 1/2 outcome or stop, and treat no next-tranche sentence, review finding or source shape as authority. |
| Continuation and publication agents | Before every Git or external mutation | Preserve clean-tree, exact-head, protected-base, review, conflict, recovery, no-bypass, no-destructive-operation and newly-published-draft non-merge boundaries. |
| Validation and review owners | Before retention or publication | Validate the final records, guidance, metadata, resources and complete standalone profile; exercise positive, negative and composition routing; then obtain a fresh independent read-only staff review. |

There was no dissent. Future outcome selection and its applicable FreeCAD/GUI
proof depend on repository state when the literal command is invoked. GitHub
mergeability, credentials and exact-head CI also remain live per-invocation
facts. This workflow adds no scheduler, watcher, recursive governance loop or
runtime dependency.

**Final routing evidence:** A fresh read-only evaluator exercised nine natural
activation and composition cases against the final guidance without invoking a
workflow, inspecting live pull-request state or making a repository or external
change:

| Probe | Result |
| --- | --- |
| Literal `$tracktemplate-continue` | Continue activates; protected `main` synchronisation, conditional chief/technical-lead composition, blocker-only review, shared two-pass repair and review-frozen publication remain in the execution path. |
| Natural-language merge-and-continue request | Continue does not activate; the literal command is required and no generic workflow may substitute. |
| Stuck/maintenance-heavy progress diagnosis | Chief of staff activates alone, read-only, and produces one transient brief or clean stop. |
| Already-authorised cross-specialist Level 2 outcome | Technical lead activates, composes applicable specialists and stops before Level 3 or an unresolved product choice. |
| `Next bounded tranche` cited as implementation authority | The sentence supplies no authority and does not activate a progression role by itself. |
| Read-only traceback diagnosis and pull-request review | Debugging and quality review route independently without continuation, delivery or publication authority. |
| Literal and natural-language publication requests | Literal `$tracktemplate-publish` activates direct publish; the natural-language variant activates no TrackTemplate or generic substitute. |

Earlier read-only probes exposed the natural-publication example, its generic
implicit-routing sentence and a composed non-blocker repair path. Those
`implementation-defect` findings were corrected before the final probe. The
final evaluator reported **PASS** with no remaining routing or execution-path
defect.

**Governance-budget exception:** This task deliberately changes governance
authority, so its skills, routing, panel, decision register, dashboard summary
and fail-closed checks necessarily exceed its zero product lines. The change
does not alter the engineering policy, frozen history or live risk register.

**Owner decision and resulting authority:** On 2026-07-31 Richard stated, “I
accept this exact Level 3 decision and authorise its implementation within the
stated boundaries and exclusions.” D-GOV-004 therefore authorises a cycle only
when the project owner invokes the literal `$tracktemplate-continue` command;
acceptance, discussion, quotation, description or a natural-language
equivalent does not invoke it. Each invocation may integrate one previous
exact-green authorised Level 1/2 pull request, synchronise protected `main`,
reconstruct canonical authority, classify credible candidates as
`exit-closing`, `necessary-enabling`, `maintenance` or
`governance-or-tooling`, and deliver one highest-value worthwhile outcome
already authorised at Level 1 or Level 2 or stop cleanly. It may compose the
read-only, transient chief of staff and the Level 1/2-only technical lead,
validate, obtain separate read-only staff review, repair only `BLOCKER`
findings through at most two shared passes, and repeat affected final validation
and a new separate read-only staff review after every repair. Publication is
review-frozen to the exact final-reviewed source; it has no independent repair
authority. The cycle may then publish one exact-green draft and provide the
plain-English acceptance pack.

D-GOV-004 does not make a `Next bounded tranche` sentence, review finding,
branch, test or source shape authoritative; does not promote maintenance,
governance/tooling or non-blocking findings automatically; and does not
authorise a Level 3 decision, renderer or phase acceptance, migration support,
production output or chair clearance, release or tagging, protection bypass,
force push, history rewrite, destructive reset/restore, `git clean`, branch
deletion, another destructive operation, unresolved product choice, or marking
ready or merging the newly published draft in the same invocation.

## Current outcome selection

The completed fake Coin field, group and node protocol consolidation above
retired its named test-maintenance finding. Completion neither closes a named
Phase 5 exit nor selects the next implementation outcome. D-GOV-004 permits a
future literal `$tracktemplate-continue` invocation to reconstruct current
authority and select one worthwhile authorised Level 1/2 outcome; the decision
itself does not invoke that cycle or create a task.

The current risk state is in [risks.json](risks.json). D-P5-001 remains the
Phase 5 opening and renderer-evaluation authority; D-GOV-004 is the separate
continuation-governance decision in [gate-decisions.json](gate-decisions.json).
