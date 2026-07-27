---
name: tracktemplate-freecad-object-model
description: Design, implement or review TrackTemplate mappings between canonical railway records and FreeCAD document objects, properties, FeaturePython proxies and ViewProviders. Use for object creation, recompute, transactions, persistence, save/reopen, migration, Undo/Redo, selection mapping or App/Gui lifecycle changes.
---

# TrackTemplate FreeCAD object model

## Outcome

Create a compact, versioned and recoverable FreeCAD object mapping whose
document state reconstructs canonical railway intent and whose GUI
representation remains derived.

## Responsibility boundary

- Read `reference/PROJECT_PLAN.md`, `reference/ARCHITECTURE.md`,
  `reference/MODULARISATION_PLAN.md`, the qualified compatibility contract,
  `reference/VALIDATION.md` and `reference/TESTING_POLICY.md`.
- Use `$tracktemplate-freecad-addon-research` to retrieve current first-party
  guidance for FeaturePython objects, properties, proxies, serialization,
  ViewProviders and lifecycle callbacks. Qualify every runtime-specific claim
  against the supported FreeCAD profile.
- Use `$tracktemplate-api-design` before changing stored properties, payloads,
  schema versions, commands or compatibility contracts.
- Use `$tracktemplate-python-writing` for implementation and
  `$tracktemplate-occt-geometry` for exact `Part` shape construction.

This skill owns the adapter workflow, not canonical railway calculations,
presentation policy, migration acceptance or FreeCAD upstream behaviour.

## Mapping contract

Define the mapping in both directions:

```text
canonical record + stable domain identities
    ↕ versioned document properties or payload
small logical FreeCAD document object
    ↕ derived selection and display mapping
ViewProvider / Coin presentation
```

For each field, state its owner, type, units, frame, default, validation,
serialization form, schema version, migration rule and invalidation effect.
Identify which information is canonical, persisted compatibility state,
reconstructible derived state or GUI-only state.

Never use an object label, generated object name, `Shape`, Coin node, cache or
display property as independent railway truth.

## Object-lifecycle workflow

1. **Research the qualified API.** Record official sources, revision where
   material and the supported FreeCAD/Python profile. Remember that an FCStd
   file stores object state but not the addon's Python implementation.
2. **Choose the narrow backing type.** Justify `App::FeaturePython`,
   `Part::FeaturePython` or another supported type from the object's persistent
   responsibility. Do not select a shape-owning type merely for convenient
   display.
3. **Design stable persistence.** Use typed properties or a validated versioned
   payload. Preserve import paths or provide explicit compatibility shims when
   proxy classes move. Reject unknown, future, corrupt or conflicting state
   before mutation.
4. **Control callbacks and recompute.** Define initialization, property-change,
   restore and recompute behaviour. Guard partial initialization, re-entrancy,
   recursive writes and recompute storms. Keep `execute()` deterministic and
   free of dialogs or hidden transactions.
5. **Own mutations transactionally.** Put create, edit, migrate and delete
   operations behind application commands with explicit validation, transaction
   boundaries, rollback and clean-up. Prove Undo/Redo and failure recovery.
6. **Separate App and Gui.** Core modules and document reconstruction must work
   without `FreeCADGui`. ViewProviders own derived visibility, display modes,
   Coin nodes and stable visual-to-domain selection mapping.
7. **Bound object granularity.** Persistent object counts should scale with
   logical assemblies and layers, not rail segments, timbers, chairs, markers
   or generated export fragments.
8. **Prove persistence.** Test new creation, property edit, recompute,
   save/close/reopen, proxy restoration, copied-target migration, invalid or
   future schema rejection, Undo/Redo and aborted mutation in the qualified
   host. Add real-GUI evidence for display, selection or editing behaviour.

## Guardrails

- Do not embed executable code or untrusted dynamic imports in persisted data.
- Do not infer canonical identity from FreeCAD topology names, object order,
  labels or transient pointers.
- Do not mutate an operator's only document during automation.
- Do not rely on `onChanged()` callback order during property construction
  without qualified evidence and explicit guards.
- Do not save derived exact shapes merely to avoid deterministic regeneration
  unless the accepted architecture explicitly requires a retained production
  object.
- Do not treat a successful headless reopen as GUI, selection or Undo/Redo
  acceptance.

## Report

Report the mapping and object type, canonical versus derived fields, schema and
migration strategy, proxy/import compatibility, callback and recompute model,
transaction and rollback behaviour, object-count effect, App/Gui separation,
validation completed and every qualified-host, real-GUI or owner decision still
outstanding.
