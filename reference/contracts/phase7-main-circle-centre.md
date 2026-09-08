# Main circle centre calculation and routing contract

Status: **Bounded Level 2 contract under D-P7-001.**

The [contract data](phase7-main-circle-centre.json) identifies the API,
formula, units, references, fixture and product routing record.
This document owns their human-readable requirements.
The [opening decision](../current/PHASE_EVIDENCE.md#phase-7-opening-panel)
owns the task authority and exclusions.

## Calculation

Move the main circle centre calculation into the domain API.
Use it in the existing B16 Generate/Replace workflow.
The result is a tuple of two floats: local X and Y in millimetres.
The frame is the canonical local left-turn frame.
The private left-normal helper must stay private.

Keep the inherited endpoint calculation, operation order, input behaviour and
diagnostics. Add no type conversion or finite-value rule.
Direct negative transition inputs remain compatibility evidence only.
The calculation uses no FreeCAD, Qt, document, stored state or cache.
It has no side effects.

Keep both frozen references and all comparison tolerances unchanged.
Compare calculation results, diagnostics and the actual caller results.

## Product composition

Require all four callable functions before binding.
Preserve all four previous host entries.
Select the new centre, then use the unchanged three-function host binder.
Validate the complete selected binding before launch.

If binding or closure validation raises `Exception`, restore all four entries.
Translate `B15WorkflowHostError` with its cause. Other exceptions propagate
after restoration. Binding must not change a document.

The centre must use the selected clothoid function.
The actual `run_macro` must use the selected centre in the host namespace.
Keep all previous function and caller checks.
Validate the current binding before reporting it.
Apply and validate the complete selected binding again before launch.

The versioned record describes migration composition.
It is not a stored document schema or a stable Workbench API.
Keep the frozen three-function host binder and development comparison record
unchanged.

## Validation and preservation

Use analytical and caller parity with unchanged downstream construction.
Keep identity, ordering, metadata and shape checks.
Shape summaries alone do not prove complete geometric equality or exported
byte equality.

Exercise the affected GUI, history, failure and copied-document reopen paths.
Compare the accepted and candidate B16 modular paths on the same host and
fixture. Keep the legacy comparison separate.

No centre cache exists. Warm centre-cache reuse is inapplicable.
Report repeated calculation separately.

The B15 compatibility host owns the inherited definitions for comparison and
migration. Keep the comparison paths until family parity, recovery and explicit
owner acceptance permit retirement.
This task accepts no Phase 7 exit or performance result.
D-P6-008 stays in full. Output and release clearance stay unchanged.
This task removes no legacy path.
