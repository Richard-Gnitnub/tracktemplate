---
name: tracktemplate-occt-geometry
description: Design, construct, diagnose or review exact TrackTemplate geometry through FreeCAD Part and the Open CASCADE Technology kernel. Use for edges, wires, faces, shells, solids, B-rep validity, booleans, offsets, fillets, transformations, shape healing, meshing, topology mapping or exact production-export geometry.
---

# TrackTemplate OCCT geometry

## Outcome

Construct the smallest exact B-rep required at an explicit Validate or Export
boundary and prove its railway dimensions, topology, tolerance and output
fitness without making the shape canonical state.

## Responsibility boundary

- Run `.venv/bin/python tools/development_toolchain_preflight.py --stage freecad`
  before FreeCAD or OCCT host work. Run
  `.venv/bin/python tools/development_toolchain_preflight.py --stage freecad-gui`
  before work that uses the real-GUI bridge.
- Read `reference/PROJECT_PLAN.md`, `reference/ARCHITECTURE.md`,
  `reference/MODULARISATION_PLAN.md`, `reference/VALIDATION.md` and
  `reference/TESTING_POLICY.md`.
- Use `$tracktemplate-railway-mathematics` for analytical geometry and
  `$tracktemplate-freecad-object-model` when a result becomes a retained
  FreeCAD document object.
- Use `$tracktemplate-freecad-addon-research` for the current first-party
  FreeCAD wrapper and Addon boundary. Retrieve version-matched official OCCT
  documentation separately from the Open CASCADE project. Distinguish
  FreeCAD's `Part` Python wrapper from the underlying OCCT C++ API and qualify
  calls against the supported host.
- Read licensing and provenance owners before geometry uses external profiles,
  tables, CAD bodies or output-affecting source evidence.

FreeCAD/OCCT edges, faces, solids, tessellations and generated topology remain
derived. They do not replace canonical parameters, semantic component records
or production intent.

## Exact-geometry contract

Before construction, state:

1. the canonical input record and complete cache or request signature;
2. units, coordinate frame, placement and handedness;
3. railway/model acceptance tolerances separately from numerical and OCCT
   modelling tolerances;
4. expected geometry and topology: curve/surface kinds, vertices, edges, wires,
   faces, shells, solids, connectivity, closure, orientation and manifold
   requirements;
5. stable semantic identities and how generated subshapes map back to them;
6. supported FreeCAD and OCCT versions and output format; and
7. failure, rollback and disposal behaviour.

## Construction workflow

1. **Plan topology before calls.** Define how analytical curves and component
   boundaries become ordered edges, closed wires, oriented faces, shells,
   solids and compounds. Do not infer intended topology from a rendered result.
2. **Construct incrementally.** Build and check the smallest intermediates.
   Preserve placements and transformations explicitly; avoid repeated
   coordinate conversion and uncontrolled tolerance accumulation.
3. **Validate every risky boundary.** After wire/face creation, sweeping,
   lofting, offsetting, filleting, Boolean operations, healing and import,
   check for null or empty results, kernel validity, expected type/count,
   closure, orientation, connectivity, degeneracy, dimensions and
   application-specific railway invariants.
4. **Treat Boolean and feature operations as fallible.** Detect unchanged,
   fragmented, missing or dimensionally wrong results even when no exception
   was raised.
5. **Control tolerances.** Record input and resulting tolerances, cap permitted
   growth and distinguish local subshape tolerance from acceptance tolerance.
   Never widen tolerance globally merely to obtain validity.
6. **Use healing deliberately.** Diagnose first, select the smallest repair and
   revalidate semantics afterwards. Healing may modify, remove or construct
   topology and may increase tolerances; it is not neutral cleanup.
7. **Preserve semantic mapping.** Do not persist `Face1`, `Edge7`, list position
   or other generated topological names as domain identity. Use construction
   records and stable semantic component IDs, and treat topology-changing
   operations as mapping invalidation boundaries.
8. **Validate the output path.** Exercise the intended FreeCAD object,
   STEP/STL/DXF or other exact-output boundary, including round-trip where
   required, scale, placement, deterministic naming, manifest dependencies,
   overwrite handling and transactional cleanup.
9. **Measure complete cost.** Keep exact work demand-driven, dispose of
   transient geometry and measure Validate/Export cost when construction,
   tessellation or reuse changes.

## Guardrails

- A visible shape, non-null result, successful Boolean or `isValid()` result
  may provide one check; none proves the railway contract alone.
- Do not compare tessellation bytes as exact B-rep or semantic equality.
- Do not silently drop short or degenerate edges, reorder wires, reverse faces
  or select the largest Boolean fragment.
- Do not assume OCCT C++ examples are exposed unchanged by FreeCAD's Python
  wrapper.
- Do not use shape healing to conceal an upstream analytical or construction
  defect.
- Do not retain dense exact geometry in the routine editing document unless an
  accepted requirement and performance/persistence evidence permit it.
- Do not claim real-GUI or production-export acceptance from a headless shape
  check.

## Report

Report the exact-geometry contract, qualified host and APIs, topology plan,
construction stages, tolerance ledger, validation and railway invariants,
Boolean/healing effects, semantic mapping, output and round-trip evidence,
performance/disposal result, failures and every GUI, production or
project-owner decision still outstanding.
