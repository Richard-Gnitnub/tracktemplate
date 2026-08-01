# TrackTemplate Product Vision

Status: **canonical product purpose, product-horizon and migration-completion
direction, accepted under D-GOV-005 on 2026-08-01.**

This document says what TrackTemplate is and what the current programme is
trying to establish. [ARCHITECTURE.md](ARCHITECTURE.md) owns the technical
invariants, [PROJECT_PLAN.md](PROJECT_PLAN.md) owns live phase and exit status,
and [CAPABILITY_MATRIX.md](CAPABILITY_MATRIX.md) records bounded repository
evidence. Product vision directs work; it does not independently authorise a
feature, phase exit, migration family, output clearance or release.

## Product definition

TrackTemplate is a FreeCAD-native Workbench for the parametric design,
visualisation and production of model railway track templates. It is intended
to make railway intent editable, inspectable, persistent and manufacturable
inside FreeCAD while retaining railway correctness, recoverability and
traceable production decisions.

Templot is the closest product analogy because both products centre on
parametric model-railway templates rather than generic drawing primitives.
The analogy communicates the intended railway breadth and template-led way of
working. It does not claim file-format compatibility, identical interaction,
shared implementation, transferred rights or feature parity at the current
repository state.

TrackTemplate's distinction is that FreeCAD is the host product boundary. The
normal result is an installable TrackTemplate Workbench backed by the modular
`tracktemplate` package, FreeCAD documents and transactions, FreeCAD-native
selection and task-panel workflows, and explicit use of FreeCAD/OpenCASCADE
where exact geometry is required. The accepted legacy macro remains comparison
and migration evidence; it must not be a runtime dependency of the completed
Addon.

## Vision and execution authority

Work is governed in this order:

1. this canonical product vision;
2. accepted architectural invariants;
3. the current authorised programme;
4. the active phase and its exact exit criteria;
5. current risks, findings and repository evidence;
6. one selected bounded work item;
7. one explicit delegated assignment; and
8. independent evidence and acceptance.

Every agent assignment must support a bounded work item that closes an
evidenced finding or advances an active exit criterion, advances the current
authorised programme and thereby helps establish this vision. A later horizon
may inform an extension point, but it cannot authorise present implementation.

## Canonical and derived authority

Canonical TrackTemplate state is the source of truth. It includes versioned
railway intent, stable identities, topology, analytical decisions, production
intent and accepted provenance-bearing definitions. It remains independent of
how a particular view or output is rendered.

The following are derived, disposable and replaceable representations:

- Coin nodes and scene graphs;
- ViewProvider state;
- transient FreeCAD `Part` geometry;
- generated exact-geometry objects;
- caches and previews; and
- export files, reports and manifests.

A derived artifact may carry a signature, validation result or audit record,
but it never becomes the canonical railway model. Deleting and regenerating a
derived representation from current canonical state must not change railway
intent.

## Normal design experience

Routine editing uses a clean, fast Coin-based 2D or pseudo-2D template view.
Its intended presentation pipeline is:

```text
canonical state
    -> railway geometry and analysis
    -> immutable presentation snapshot
    -> batched Coin representation
```

The view is intended to show running rails; switch, closure, check and crossing
rails; sleepers and turnout timbers; construction marks; template joints and
registration features; and optional chair, analysis and warning layers.
Selection maps visual elements back to stable canonical identities. Ordinary
selection, visibility and parameter editing must not depend on exact `Part`
geometry or rebuild it as a side effect.

## On-demand exact geometry and production

TrackTemplate will produce exact railway geometry explicitly and on demand,
including rail profiles, sleepers and timbers, procedural chairs and supports,
switch and crossing components, and fabrication or inspection geometry. Exact
geometry is derived from validated canonical state, is safe to dispose of and
regenerate, and is not stored as an alternative source of railway truth.

Authorised output boundaries may produce SVG, DXF, STL, STEP and other formats.
Output generation remains deterministic, validated, transactional,
provenance-aware and failure-safe. This vision does not clear any current
package or output for production use.

## Product horizons

### Current programme: TrackTemplate Core migration

The current programme faithfully converts the accepted legacy macro into a
modular, tested, maintainable, installable and operational FreeCAD Addon. It
preserves accepted behaviour, geometry, workflows, persistence and production
outputs while moving authority into the modular package.

Where present in the accepted baseline, the programme covers parametric curves
and Euler transitions, straight and parallel track, widening, turnouts and
crossovers, sleeper and timber analysis, chair analysis, platforms, formation
boards, document persistence, FreeCAD commands and task panels, ViewProviders,
lightweight presentation, exact geometry, SVG/DXF/STL/STEP output and
regression comparison with the accepted macro baseline.

### Subsequent programme: TrackTemplate Layout Editor

The later Layout Editor is part of the product vision, not the current Phase 6
scope. Its intended capabilities include calibrated maps and images, FreeCAD
sketch reference layers, placement and rotation of complete templates, track
endpoints and grouped interfaces, extension from a selected end, attaching and
detaching templates, connected-track construction, constituent template
editing, explicit parameter locks, fitting between fixed endpoints and
connected-layout dependency solving.

These capabilities are future until separately authorised. Recording their
direction does not add an implementation task or alter a current exit.

## Migration completion

TrackTemplate Core migration is complete only when all of the following are
accepted at their owning gates:

- the installable FreeCAD Workbench/Addon is the normal operator route;
- the modular `tracktemplate` package is the one authoritative runtime
  implementation;
- the Addon does not rely on the legacy macro at runtime;
- every advertised Core capability has accepted parity, lifecycle,
  persistence, presentation, exact-output and performance evidence applicable
  to its boundary;
- supported legacy documents use explicit, recoverable migration rather than
  live historical implementations;
- production outputs satisfy the applicable validation, provenance, licensing
  and transactional controls;
- the distribution artifact is reproducibly built from authoritative source;
  and
- release-candidate qualification and project-owner acceptance are complete.

Completion of one phase or one capability family is not macro-migration
completion. Layout Editor features are not prerequisites for Core migration.

## Present-programme non-goals

The Core programme does not authorise a whole-macro rewrite, a second
authoritative model in Coin or `Part`, exact geometry during routine editing,
one persistent FreeCAD object per sleeper or chair, speculative Layout Editor
features, silent expansion of supported legacy families, unvalidated output
clearance or early retirement of the accepted comparison path.

In particular, this vision record does not implement a shared Coin renderer,
replace a ViewProvider, add a map background, connect complete templates,
introduce a layout solver, change railway mathematics or output, close a phase
exit, accept a pull request, or declare the migration complete.

## Product acceptance journey

The accepted phase sequence remains the delivery journey. In outline, it
establishes the exact-validation/export seam, migrates core alignment and
multiple-track families, migrates switches/crossings and timbering, completes
chair definitions and authorised production outputs, packages the normal
Workbench/Addon route, and then qualifies a release candidate. Exact phase
status and exit wording remain solely in [PROJECT_PLAN.md](PROJECT_PLAN.md).

The Layout Editor begins only through a subsequent authorised programme. It
does not back-propagate requirements into an active Core phase without a new
Level 3 decision.
