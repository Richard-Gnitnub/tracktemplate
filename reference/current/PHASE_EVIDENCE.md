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
| One renderer accepted using correctness, editing, FreeCAD integration, maintainability and measured resource evidence | Pending — the Coin candidate has bounded GUI evidence; editing, resource and acceptance evidence remain |
| Small logical object/layer count with deterministic selection-to-domain mapping | Pending — one disposable object/layer and mouse-driven selection mapping are proved; representative scale remains |
| Normal edits avoid dense exact `Part` geometry | Pending — the fixture creates no `Part` shape, but no edit workflow is proved |
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

## Next bounded tranche

Add the smallest application-command edit seam with one atomic Undo/Redo unit
and transactional failure recovery. Keep the fixture development-only and
continue to exclude a product command, persisted schema and save route until
those separate proofs are complete.

The current risk state is in [risks.json](risks.json). D-P5-001 remains the
only Phase 5 authority decision in [gate-decisions.json](gate-decisions.json).
