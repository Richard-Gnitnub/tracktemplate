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
| One renderer accepted using correctness, editing, FreeCAD integration, maintainability and measured resource evidence | Pending — the Coin candidate has bounded selection, edit, Undo/Redo, save/reopen and an eight-object resource baseline; representative editing, maintainability and acceptance evidence remain |
| Small logical object/layer count with deterministic selection-to-domain mapping | Pending — one disposable object/layer, mouse-driven selection and stable mapping across an eight-object resource fixture are proved; representative editing scale remains |
| Normal edits avoid dense exact `Part` geometry | Pending — one bounded intent edit keeps one object and no `Part` shape; representative editing remains |
| Project owner accepts editing behaviour and documented limitations | Pending — editing behaviour has not yet been presented for owner acceptance |

Phase 6 retains complete exact-validation/export signatures and invalidation,
transient exact geometry, cleanup, output equivalence, rollback and end-to-end
performance. Phase 5 does not authorise those duties, operator migration,
production output, chair clearance or release work.

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

## Bounded Coin performance baseline

This Level 2 test-first tranche adds a deterministic workstation profiler for
the development-only Coin candidate. Three fresh isolated FreeCAD GUI processes
each attached eight logical transition objects with 32 preview segments from
prepared analysed canonical state and empty per-object caches. Each process
then performed one unmeasured warm-up and three unchanged-state measurements.
Process launch, screenshots, pointer selection, save/reopen, exact validation
and export are outside both measured boundaries.

On the qualified FreeCAD 1.1.1 Flatpak profile, cold attachment took a median
481.422 ms wall time (465.275–534.657 ms), 244.255 ms process CPU
(241.092–266.276 ms) and 14.340 MiB RSS growth
(14.340–29.398 MiB). Its one explicit recompute took a median 4.162 ms
(4.033–4.318 ms). Every run retained exactly eight `App::FeaturePython`
objects, eight current preview caches, eight display modes and eight stable
selection mappings, with no added root child or `Part` shape.

Across nine measured warm reuses, wall time was a median 30.798 ms
(2.093–32.795 ms), process CPU was 4.472 ms (2.089–5.734 ms), and median RSS
growth was 0.004 MiB (0–2.004 MiB). Every measurement reused all eight
preview artifacts, replaced no scene, added no object or recompute and
preserved all eight mappings. Cleanup left no retained cache, ViewProvider,
document object or open document. The raw profile hash is
`f3564e957e24062b5b9152b9a0b1095433b1809f8ec74a353606df5e8dab63c8`;
ignored raw samples remain under the dated local benchmark directory.

The operating-system file cache was uncontrolled and the warm series shared
its process and document after warm-up. This is a bounded eight-object
development fixture, not an accepted whole-product representative scale.
No numerical budget, optimisation claim, renderer acceptance, risk treatment,
authority decision or Phase 5 exit changes.

## Next bounded tranche

Measure one edit and atomic Undo/Redo within the retained eight-object fixture,
including affected and unaffected cache/scene identity, latency, RSS, object
and recompute behaviour. Keep automatic product load wiring, maintainability
review, renderer acceptance and owner editing-behaviour acceptance as separate
later tranches.

The current risk state is in [risks.json](risks.json). D-P5-001 remains the
only Phase 5 authority decision in [gate-decisions.json](gate-decisions.json).
