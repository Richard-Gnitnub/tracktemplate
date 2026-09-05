---
name: tracktemplate-occt-geometry
description: Design, make, or review exact TrackTemplate geometry through FreeCAD Part and Open CASCADE Technology. Find causes of defects. Use for edges, wires, faces, shells, solids, B-rep validity, booleans, offsets, fillets, transformations, healing, or meshing. Use for topology mappings or exact export geometry.
---

# TrackTemplate OCCT geometry

## Purpose

At an explicit Validate or Export boundary, make the smallest necessary
exact B-rep. Prove its railway dimensions, topology, tolerance, and suitability
for the intended output. Do not make the shape canonical state.

## Responsibility boundary

Before FreeCAD or OCCT host work, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage freecad`

Before work with the real-GUI bridge, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage freecad-gui`

Read these authorities:

- `reference/PROJECT_PLAN.md`.
- `reference/ARCHITECTURE.md`.
- `reference/MODULARISATION_PLAN.md`.
- `reference/VALIDATION.md`.
- `reference/TESTING_POLICY.md`.

For analytical geometry, use `$tracktemplate-railway-mathematics`. If a result
becomes a retained FreeCAD document object, use
`$tracktemplate-freecad-object-model`.

For current official FreeCAD and Addon guidance, use
`$tracktemplate-freecad-addon-research`. Retrieve the official OCCT
documentation for the applicable version from Open CASCADE. Distinguish the
FreeCAD `Part` Python wrapper from the OCCT C++ API. Check each call against
the supported host.

Before use of external geometry information, read the licensing and provenance
owners. Such information includes profiles, tables, CAD bodies, and source
evidence that affects output.

FreeCAD/OCCT edges, faces, solids, tessellations, and generated topology remain
derived. They do not replace canonical parameters, semantic component
records, or production intent.

## Exact geometry contract

Before construction, record these items:

1. Canonical input record and the complete signature for its cache or request.
2. Units, coordinate frame, placement, and handedness.
3. Railway and model acceptance tolerances, recorded independently of
   numerical and OCCT modelling tolerances.
4. Expected geometry and topology, as specified below.
5. Stable semantic identities and the connection from generated subshapes to
   those identities.
6. Supported FreeCAD and OCCT versions, and output format.
7. Failure, rollback, and disposal behaviour.

The expected geometry and topology include these items:

- Curve and surface kinds.
- Vertices, edges, wires, faces, shells, and solids.
- Connectivity, closure, and orientation.
- Manifold requirements.

## Construction procedure

1. **Plan topology.** Define the construction of ordered edges, closed wires,
   oriented faces, shells, solids, and compounds from analytical component
   boundaries. Do not infer intended topology from a rendered result.
2. **Make geometry in small steps.** Check each intermediate result. Preserve
   placements and transformations explicitly. Avoid repeated coordinate
   conversion. Prevent uncontrolled tolerance accumulation.
3. **Validate risky operations.** After each operation listed below, check
   the result against the geometry contract. Check null or empty results,
   kernel validity, type, count, closure, orientation, connectivity,
   degeneracy, dimensions, and railway invariants.
4. **Check Boolean and feature results.** Detect unchanged, fragmented,
   missing, or dimensionally incorrect results. These failures can occur
   without an exception.
5. **Control tolerances.** Record input and resulting tolerances. Limit
   permitted growth. Distinguish local subshape tolerance from acceptance
   tolerance. Never widen tolerance globally only to get validity.
6. **Use healing with care.** Find the cause of the defect first. Select the
   smallest repair. After repair, validate the semantic meaning again. Healing can
   change, remove, or make topology. It can also increase tolerances.
7. **Preserve semantic identity.** Do not persist generated topology names or
   list positions as domain identity. Examples include `Face1` and `Edge7`.
   Use construction records and stable semantic component IDs. After an
   operation changes topology, its previous mapping becomes invalid.
8. **Validate output.** Exercise the intended FreeCAD object, STEP/STL/DXF,
   or other exact output. Include the output checks listed below.
9. **Measure the complete cost.** Keep exact work dependent on an explicit
   request. Dispose of transient geometry. If construction, tessellation, or
   reuse changes, measure Validate/Export cost.

The risky operations include these items:

- Wire or face creation.
- Sweeping, lofting, offsetting, and filleting.
- Boolean operations.
- Healing and import.

The output checks include these items:

- Round-trip checks, where necessary.
- Scale and placement.
- Deterministic naming.
- Manifest dependencies.
- Overwrite handling.
- Transactional cleanup.

## Constraints

A visible shape, non-null result, successful Boolean, or `isValid()` result
can supply one check. None alone proves the railway contract.

- Do not use tessellation bytes as proof of exact B-rep or semantic equality.
- Do not silently remove short or degenerate edges.
- Do not silently change wire order or face direction.
- Do not silently select the largest Boolean fragment.
- Do not assume that FreeCAD's Python wrapper exposes OCCT C++ examples
  unchanged.
- Do not use shape healing to hide an analytical or construction defect.
- Without an accepted requirement and performance/persistence evidence, do not
  keep dense exact geometry in the routine editing document.
- Do not claim real-GUI or production-export acceptance from a headless shape
  check.

## Report

Report these results:

- Exact geometry contract, qualified host, and APIs.
- Topology plan and construction steps.
- Input, resulting, and permitted tolerances.
- Validation and railway invariants.
- Boolean and healing effects.
- Semantic mappings.
- Output and round-trip evidence.
- Performance, disposal, and failures.
- Necessary GUI, production, and project-owner decisions that are still absent.
