# Task-automation evaluation cases

Use these prompts as routing and execution probes. Do not reveal the expected
route to the agent under test.

## Should activate

- “Make GitHub Actions run the same complete standalone matrix as local
  development and show every failure.”
- “We repeatedly rebuild the same four FreeCAD bridge commands; make that
  workflow deterministic and recoverable.”
- “Create a safe script that validates all package manifests and emits one
  machine-readable summary.”
- “This evidence report is manually assembled every time; automate only the
  deterministic formatting.”

## Should not activate alone

- “The turnout geometry is wrong at the switch heel.” Route first to debugging
  and the railway/geometry specialists.
- “Correct this typo in the README.” Treat as a routine documentation change.
- “Approve Phase 4 closure.” Route to the Level 3 evidence and owner-decision
  workflow.
- “Run this one existing test once.” Use the existing command unless repetition
  or orchestration toil is demonstrated.

## Should compose

- “The CI matrix failed only on GitHub; diagnose it and make the repeated
  clean-checkout workflow reliable.” Compose GitHub log inspection,
  failed-test classification, task automation, Python writing, validation and
  quality review.
- “Automate exact-output packaging for a release candidate.” Compose task
  automation with output, licensing, release-readiness and Level 3 authority
  workflows; automation does not confer clearance.

## Assessment

Record whether the skill triggered, which other skills composed with it,
whether conditional CI guidance was loaded, unnecessary steps, unsupported
authority claims and the final validation boundary. Compare with a no-skill
baseline only when it helps establish what the skill adds.
