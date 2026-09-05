---
name: tracktemplate-freecad-object-model
description: Design, make, or review TrackTemplate object mappings in FreeCAD. Use for properties, proxies, ViewProviders, recompute, transactions, persistence, save/reopen, migration, Undo/Redo, selection, or App/Gui changes.
---

# TrackTemplate FreeCAD object model

## Purpose

Make a compact, versioned object mapping with recovery. The software must use its document
state to make canonical railway intent again. Its GUI representation must
stay derived.

## Responsibility boundary

Before qualified host work, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage freecad`

Before work with the real-GUI bridge, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage freecad-gui`

Read these authorities:

- `reference/PROJECT_PLAN.md`
- `reference/ARCHITECTURE.md`
- `reference/MODULARISATION_PLAN.md`
- The qualified compatibility contract
- `reference/VALIDATION.md`
- `reference/TESTING_POLICY.md`.

For current official guidance, use `$tracktemplate-freecad-addon-research`.
Include FeaturePython objects, properties, proxies, serialization,
ViewProviders, and lifecycle callbacks. Examine each claim about runtime
behaviour against the supported FreeCAD profile.

Before changes to these items, use `$tracktemplate-api-design`:

- Stored properties and payloads
- Schema versions
- Commands
- Compatibility contracts.

For implementation, use `$tracktemplate-python-writing`. For exact `Part`
shapes, use `$tracktemplate-occt-geometry`.

This skill owns the workflow for the adapter. It does not own canonical
railway calculations, presentation policy, migration acceptance, or FreeCAD
behaviour.

## Mapping contract

Define the mapping in both directions:

```text
canonical record + stable domain identities
    ↕ versioned document properties or payload
small FreeCAD object for a logical document component
    ↕ derived selection and display mapping
ViewProvider / Coin presentation
```

For each field, record these items:

- Owner and type
- Units and frame
- Default and validation
- Serialization form and schema version
- Migration rule
- Effect on invalidation.

Identify canonical information, persisted compatibility state, derived state
that the software can make again, and state that only the GUI uses. Never use a
derived item as independent railway truth. Such items include labels,
generated object names, `Shape`, Coin nodes, caches, and display properties.

## Object lifecycle procedure

1. **Examine the qualified API.** Record official sources and material revisions.
   Record the supported FreeCAD/Python profile. An FCStd file stores object
   state. It does not store the Addon's Python implementation.
2. **Select the object type.** Justify `App::FeaturePython`,
   `Part::FeaturePython`, or another supported type from its persistence
   responsibility. Do not select a type that owns shapes only for convenient
   display.
3. **Design persistence.** Use typed properties or a validated, versioned
   payload. If proxy classes move, preserve import paths or supply explicit
   compatibility shims. Before mutation, reject unknown, future, corrupt, or
   conflicting state.
4. **Control callbacks and recompute.** Define initialization, property
   changes, restore, and recompute behaviour. Prevent failures from partial
   initialization, re-entrancy, recursive writes, and excessive recompute.
   Keep `execute()` deterministic. Do not put dialogs or hidden transactions
   in `execute()`.
5. **Use transactions for mutations.** Put creation, edit, migration, and deletion
   operations behind application commands. Give each command explicit
   validation, transaction boundaries, rollback, and cleanup. Prove Undo/Redo
   and failure recovery.
6. **Separate App and Gui.** Core modules and document reconstruction must
   operate without `FreeCADGui`. ViewProviders own derived visibility, display
   modes, and Coin nodes. They also own stable mappings from visual selections
   to domain identities.
7. **Limit object counts.** The number of persistent objects should depend on logical
   assemblies and layers. It should not depend on individual rail segments,
   timbers, chairs, markers, or generated export fragments.
8. **Prove persistence.** In the qualified host, do a test of all applicable operations
   in the list below. For display, selection, or editing behaviour, add
   real-GUI evidence.

The persistence tests include these operations:

- New creation, property edit, and recompute
- Save, close, and reopen
- Proxy restoration
- Migration of copied targets
- Rejection of invalid or future schemas
- Undo/Redo
- Aborted mutation.

## Constraints

- Do not embed executable code or untrusted dynamic imports in persisted data.
- Do not infer canonical identity from topology names, object order, labels,
  or transient pointers.
- During automation, do not mutate an operator's only document.
- Without qualified evidence and explicit guards, do not rely on `onChanged()`
  callback order during property construction.
- Without an explicit architecture requirement to keep a production
  object, do not save derived exact shapes to prevent regeneration.
- Do not claim GUI, selection, or Undo/Redo acceptance from a successful
  headless reopen.

## Report

Report these results:

- Object mapping and object type
- Canonical fields and derived fields
- Schema and migration strategy
- Proxy and import compatibility
- Callback and recompute behaviour
- Transactions, rollback, and object counts
- App/Gui separation
- Completed validation
- Necessary qualified-host evidence, real-GUI evidence, and owner decisions
  that are still absent.
