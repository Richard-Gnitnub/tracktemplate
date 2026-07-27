---
name: tracktemplate-task-automation
description: Design or implement safe, deterministic automation for repeated TrackTemplate development, CI, validation, evidence or packaging workflows. Use when pipeline orchestration, repeated commands or repeated repository discovery consume agent time or tokens and a stable workflow can be automated without expanding authority. Do not use for a one-off product failure whose cause is not established.
---

# TrackTemplate task automation

## Outcome

Replace proven repetitive work with a narrow, reviewable automation that is
safe on a dirty working tree, produces verifiable evidence and remains
recoverable when interrupted or rerun.

## Admission conditions

Automate only when all of these are known:

1. the workflow recurs and its trigger, inputs, steps, outputs and success
   condition are stable;
2. the canonical documents already define any affected policy or evidence
   meaning;
3. existing project tools cannot provide the result with a small composition
   or documented invocation;
4. automation reduces total operator/agent work without hiding review or
   shifting risk into an unattended process; and
5. the required implementation, validation, ownership and retirement boundary
   are explicit.

Use a checklist or existing command when the task is rare, still changing,
requires judgement at each step or would cost more to maintain than it saves.

## Preparation

1. Read `reference/PROJECT_PLAN.md` and the canonical owner of the workflow.
2. Inspect existing scripts, tests, validators and CI before designing another
   entry point.
3. Read `reference/RECOVERY_AND_BACKUP.md` before automation can delete, move,
   overwrite, mutate Git history, touch operator documents or process valuable
   ignored evidence.
4. Define the exact runtime/profile, inputs, outputs, side effects, external
   systems, credentials, concurrency and failure modes.
5. Capture the current manual result and cost as a repeatable baseline.

Read the [CI validation workflow](references/ci-validation.md) when automation
runs in a clean checkout, composes the standalone matrix or crosses between
tracked CI evidence and workstation-only evidence.

## Design rules

- Prefer a small standard-library Python tool or an extension to the existing
  owning tool. Use `$tracktemplate-python-writing` for retained Python.
- Keep policy and command catalogues in their canonical documents. A script
  enforces or composes them; it does not become a second authority.
- Accept explicit paths and typed configuration. Reject unresolved variables,
  broad roots, implicit home-directory state and ambiguous working directories.
- Make repeated equivalent runs safe. Use deterministic output, atomic staging,
  validation-before-commit and clear rollback or resume semantics.
- Preserve raw evidence and emit a concise stable summary with an explicit
  success sentinel. Link to large logs rather than loading them repeatedly.
- Validate inputs before mutation and revalidate outputs before reporting
  success.
- Detect concurrent execution where overlap could corrupt state.
- Provide a bounded manual invocation and a documented way to stop or bypass
  any retained automation.
- Add no third-party runtime dependency, daemon, watcher, scheduled job, CI
  mutation or external service without explicit project-owner approval.

Do not install cron entries, systemd units, file watchers, webhooks, API
pollers, IDE hooks or machine-global configuration as an inferred next step.
Those are separate external-state and maintenance decisions.

## Token- and context-efficiency rules

- Automate deterministic retrieval, validation and formatting; leave
  requirement, railway, legal and authority decisions visible to the agent or
  project owner.
- Prefer machine-readable focused output with stable identifiers so later
  agents can retrieve only the relevant section.
- Reuse canonical paths and identifiers instead of generating generic task
  summaries, memory files or duplicate plans.
- Cache only derived data whose complete input signature, invalidation,
  provenance and recovery behaviour are explicit.
- Measure improvement using reduced repeated work, smaller necessary context
  or faster equivalent execution—not fewer tokens in one artificial prompt.

## Implementation workflow

1. **Model the manual workflow.** Record its inputs, outputs, invariants,
   decision points and observed failure behaviour.
2. **Separate judgement.** Keep approvals and semantic decisions outside the
   automated core; make them explicit inputs or fail-closed stops.
3. **Pilot on disposable state.** Use temporary directories and copied FCStd or
   evidence inputs. Never test on the sole operator copy.
4. **Exercise failures.** Cover empty/corrupt inputs, partial writes,
   unavailable dependencies, permissions, interruption and repeated execution.
5. **Compare results.** Prove automated output and side effects match the
   accepted manual baseline.
6. **Integrate narrowly.** Retain only the smallest entry point and documentation
   required by its consumers.
7. **Validate and review.** Run the applicable standalone, FreeCAD, GUI,
   persistence, export, performance, provenance and recovery checks, then the
   normal quality review.

## Evaluation

When this skill, its description or its resource routing changes, exercise the
[routing and workflow cases](references/evaluation-cases.md). Check intended
activation, non-activation and composition using fresh task prompts where the
environment permits it; static frontmatter validation alone is not evidence
that routing or task execution works.

## Report

Report the repeated cost removed, retained judgement points, implementation
owner, inputs/outputs, idempotency and recovery behaviour, checks run, observed
failure cases, external actions not authorised and the measured efficiency
result.
