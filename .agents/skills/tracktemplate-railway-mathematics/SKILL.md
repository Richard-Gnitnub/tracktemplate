---
name: tracktemplate-railway-mathematics
description: Formulate, implement or review TrackTemplate railway geometry and numerical calculations with explicit units, frames, domains, invariants and error controls. Use for alignments, curves, easements, station mapping, offsets, multiple-track geometry, turnouts, crossovers, intersections, sampling, root solving or tolerance-sensitive analytical changes.
---

# TrackTemplate railway mathematics

## Outcome

Produce a mathematically specified, numerically stable and independently
checkable railway calculation while preserving accepted geometry, topology,
ordering and compatibility.

## Responsibility boundary

- Read `reference/PROJECT_PLAN.md`, `reference/ARCHITECTURE.md`,
  `reference/MODULARISATION_PLAN.md`, `reference/VALIDATION.md` and
  `reference/TESTING_POLICY.md`.
- Use `$tracktemplate-railway-standards` for external standard values and
  applicability. This skill consumes only accepted or explicitly provisional
  inputs; it does not source gauge requirements.
- Use `$tracktemplate-python-writing` for retained Python or FCMacro edits.
- Use `$tracktemplate-occt-geometry` only after a pure analytical result crosses
  the explicit exact-geometry boundary.

Keep reusable mathematics in the domain layer. Do not import `FreeCAD`, `Part`,
`FreeCADGui`, Qt/PySide or pivy into a railway calculation.

## Mathematical contract

Before implementation, state:

1. inputs and outputs with dimensions, units, coordinate frames and handedness;
2. curve orientation, station or chainage convention, parameter domain and
   endpoint inclusion;
3. required geometric continuity, topology, stable identities and ordering;
4. valid range, preconditions and all known singular, ambiguous or degenerate
   cases;
5. model tolerance, numerical solver tolerance and comparison tolerance as
   separate quantities;
6. failure result and diagnostic when no valid railway solution exists; and
7. the accepted legacy, analytical, standards-derived or independently
   calculated comparison oracle.

Do not let implicit global defaults or FreeCAD display precision define this
contract.

## Engineering workflow

1. **Formulate from the contract.** Write the governing relationships and
   dimensional checks before choosing an algorithm. Identify exact results,
   approximations and empirical inputs separately.
2. **Select a stable numerical method.** Consider conditioning, cancellation,
   parameter scaling, convergence, bracketing and iteration limits. Prefer a
   bounded deterministic method whose failure is observable.
3. **Define invariants.** Apply those relevant to the calculation: rigid
   transformation invariance, reversal, reflection, change-back, symmetry,
   monotonic station progression, endpoint agreement, continuity, dimensional
   consistency and limiting cases.
4. **Handle invalid and limiting cases explicitly.** Reject NaN, infinity,
   impossible radii, zero-length domains, unbracketed roots, non-unique
   intersections and topology-changing near-degeneracy unless the contract
   defines a supported result.
5. **Build independent evidence.** Use hand-checkable examples, analytical
   identities, high-precision or independently implemented references where
   justified, plus property or metamorphic tests across representative and
   boundary domains.
6. **Compare accepted behaviour.** Preserve B14/B15 roles and compare complete
   observable outputs, including units, identities, ordering, diagnostics and
   invalid cases. Do not tune tolerances merely to hide a mismatch.
7. **Implement narrowly.** Separate mechanical extraction, formula change,
   numerical-method change, cleanup and optimisation. Keep one authoritative
   implementation behind a cohesive domain interface.
8. **Validate at the consuming boundary.** Run direct domain evidence first,
   then the applicable FreeCAD, persistence, presentation, exact-geometry and
   export checks selected by `$tracktemplate-change-validation`.

## Numerical guardrails

- Do not use equality on computed floating-point geometry where the contract
  requires a bounded comparison.
- Do not round intermediate values for presentation or serialization.
- Do not confuse OCCT modelling tolerance with railway acceptance tolerance.
- Do not increase sampling density as a substitute for proving the underlying
  curve or solver.
- Do not silently clamp, choose one of several roots or return a visually
  plausible solution.
- Do not claim correctness from one nominal example, source-code similarity or
  agreement between two implementations sharing the same formula or data.
- Treat a tolerance change as a behaviour and compatibility decision.

## Report

Report the mathematical contract, equations or method, source and status of
inputs, invariants, numerical strategy, invalid and degenerate cases, tolerance
budget, oracle independence, implementation boundary, evidence completed,
mismatches and all FreeCAD, GUI, exact-output or owner acceptance still
required.
