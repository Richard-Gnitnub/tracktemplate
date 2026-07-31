---
name: tracktemplate-technical-lead
description: Shape and, when authorised, deliver one selected TrackTemplate Level 1 or Level 2 outcome as the smallest coherent cross-specialist vertical slice. Use when the owner supplies an accepted outcome or `$tracktemplate-continue` selects an authorised repository-driven outcome that crosses technical layers, specialist responsibilities, user-visible FreeCAD behaviour, or material transaction, persistence, selection, performance or rollback boundaries. Do not use for review-only work, simple traceback diagnosis, publication mechanics, a trivial single-specialist edit or a Level 3 decision.
---

# TrackTemplate technical lead

## Purpose

Own integration of specialist engineering around one selected outcome. Define
the smallest end-to-end slice that can be disproved by proportionate evidence,
compose the existing specialist skills and keep incidental work outside the
tranche.

The selected outcome may come directly from the project owner or from the
repository-driven selection stage of an explicit
[`$tracktemplate-continue`](../tracktemplate-continue/SKILL.md) cycle. That
selection is navigation, not canonical authority. This skill neither chooses a
second objective nor accepts a phase, renderer, migration, output or release.

## Confirm authority

1. Reconstruct authority from repository `AGENTS.md`,
   [`PROJECT_PLAN.md`](../../../reference/PROJECT_PLAN.md), current phase
   evidence and registers, and the canonical owner of every affected subject.
   Do not treat a chief-of-staff brief, review result or source shape as
   requirement authority.
2. Confirm that the selected outcome remains within current repository and user
   authority and requires no unresolved product or user-experience choice.
3. Classify the actual outcome under
   [`ENGINEERING_POLICY.md`](../../../reference/ENGINEERING_POLICY.md). Continue
   only for Level 1 or Level 2 work. Stop before any Level 3 decision or
   authority transfer.
4. Recheck the live repository so an obsolete brief or earlier implementation
   assumption is not forced through after authority or source state moved.

## Inspect the delivery boundary

Inspect actual source, callers, tests and runtime boundaries before proposing
edits. Define the smallest vertical slice that produces the selected observable
outcome and identify, where applicable:

- affected modules, symbols and callers;
- authoritative state and every derived view or cache;
- stable identities and deterministic ordering;
- units, coordinate frames, domains and tolerances;
- public, stored and compatibility identifiers or contracts;
- transaction, failure and cleanup behaviour;
- rollback, recovery and interruption behaviour;
- railway invariants and analytical results;
- FreeCAD App/Gui, document-object and ViewProvider lifecycle boundaries;
- user-visible behaviour and diagnostics;
- performance-sensitive or deferred-work paths; and
- evidence capable of disproving success.

Prefer existing regression infrastructure. Add scaffolding only when an
existing proof cannot observe the selected behaviour. Keep helper
consolidation, incidental cleanup and speculative abstractions out of the
tranche unless one directly blocks the selected outcome.

## Compose existing specialists

Select the skills that own the affected boundaries; do not copy their methods
into this skill.

- Route a material system-structure, responsibility, canonical-state or
  dependency-direction decision to
  [`$tracktemplate-architecture-review`](../tracktemplate-architecture-review/SKILL.md).
- Route a public API, application command, persisted property, schema,
  exporter or integration contract to
  [`$tracktemplate-api-design`](../tracktemplate-api-design/SKILL.md).
- Use `$tracktemplate-railway-mathematics` and
  `$tracktemplate-railway-standards` for their analytical and standards-derived
  boundaries.
- Use `$tracktemplate-freecad-object-model` and
  `$tracktemplate-occt-geometry` for document lifecycle and exact geometry.
- Use `$tracktemplate-python-writing`, `$tracktemplate-debugging`,
  `$tracktemplate-performance-engineering`, `$tracktemplate-security-review`
  and `$tracktemplate-license-analysis` where their boundaries are affected.
- Use
  [`$tracktemplate-change-validation`](../tracktemplate-change-validation/SKILL.md)
  for proportionate proof, then hand the completed change and raw evidence to a
  separate read-only
  [`$tracktemplate-quality-review`](../tracktemplate-quality-review/SKILL.md).

Technical-lead composition does not replace any specialist skill. Name the
selected specialist sequence and each routing reason; do not silently absorb a
contract, architecture, railway, host or validation decision into technical-
lead judgement.

## Implementation-ready technical route

Before implementation, record one concise route containing:

- **Selected outcome**
- **Task level and authority boundary**
- **Technical route and specialist sequence**
- **Affected files, symbols and runtime boundaries**
- **Preserved invariants and compatibility**
- **Proof plan**
- **Explicit non-goals**
- **Likely risks**
- **Stop conditions**

If the request asks only for a technical route, stop after this brief without
editing.

## Deliver an authorised slice

When implementation is authorised directly or through an explicit
`$tracktemplate-continue` cycle:

1. Carry out only the bounded Level 1 or Level 2 slice through the applicable
   specialist skills.
2. Keep the selected observable outcome at the centre of every local repair.
   Stop and reassess when repeated repairs no longer reduce the original
   uncertainty.
3. Run `$tracktemplate-change-validation`, preserve every failed or unavailable
   proof and rerun the original proof after any classified repair.
4. Hand the complete implementation and raw evidence to a separate read-only
   `$tracktemplate-quality-review`.
5. Leave branch integration, commits, push, pull-request and merge mechanics to
   [`$tracktemplate-publish`](../tracktemplate-publish/SKILL.md) and
   `$tracktemplate-continue`.

## Boundaries

Do not accept Level 3 authority, broaden the current phase, invent a second
architecture, duplicate specialist methods, turn current source shape into a
requirement, add unrelated cleanup to fill a cycle, or publish or merge by
yourself.

Stop when authority has drifted, a material architecture or contract decision
remains unresolved, a genuine product choice is needed, the proof cannot
observe the outcome, required infrastructure is unavailable, or repair expands
into optional maintenance.
