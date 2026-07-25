---
name: tracktemplate-quality-review
description: Review complete TrackTemplate source or documentation changes for unnecessary complexity, duplicated authority, misleading comments, hidden failures, behavioural drift, performance regressions and unsupported validation claims. Use before reporting completion of a non-trivial change.
---

# TrackTemplate quality review

## Purpose

Review a proposed or completed TrackTemplate source change without expanding its accepted scope or substituting personal preference for evidence.

## Required preparation

1. Read [`references/review-checklist.md`](references/review-checklist.md).
2. Inspect the complete relevant diff before reaching conclusions. Include connected changes, tests, documentation and generated interfaces that affect the same behaviour.
3. Identify the affected architectural boundary and railway boundary before assessing implementation quality.
4. Read only the canonical project documents relevant to the change. Do not copy their policy into this skill or treat this skill as a second authority.

## Review principles

- Preserve necessary FreeCAD compatibility code, diagnostics, transaction handling, geometry tolerances, stable identities and legacy evidence unless the change has specific evidence and authority to alter them.
- Check apparent duplication before removing it. It may protect FreeCAD lifecycle behaviour, compatibility, recovery, evidence continuity or performance.
- Distinguish verified defects and evidenced behavioural risks from stylistic preferences or possible future improvements.
- Reject broad mechanical cleanup, automatic “AI authenticity” scoring, phrase blacklists and repository-wide rewriting as substitutes for review.
- Avoid changing files unless the user explicitly requested implementation or fixes.
- Do not accept unsupported claims that FreeCAD, GUI, export, validation or performance testing succeeded.

## Review focus

Assess the relevant change for:

- unnecessary abstraction, speculative helpers or duplicated authoritative logic;
- misleading, repetitive or stale comments;
- hidden failures, broad exception handling and weakened diagnostics;
- behavioural drift in geometry, topology, tolerances, ordering, persistence, transactions or exporters;
- unnecessary metadata, repeated calculations and likely performance regressions;
- accidental public API, stored-state or compatibility changes;
- weakened validation, changed evidence boundaries or unsupported completion claims;
- unrelated formatting, refactoring or scope expansion.

## Output

Report:

1. **Decision:** pass, pass with findings, or blocked.
2. **Confirmed defects:** ordered by impact, with exact paths or symbols and the evidence supporting each finding.
3. **Unnecessary complexity:** only where its lack of purpose has been established.
4. **Behavioural risks:** including the affected architectural and railway boundaries.
5. **Checks completed:** commands, inspections and evidence actually reviewed.
6. **Checks still required:** especially real-GUI FreeCAD, export, performance, provenance, licensing or compatibility evidence that was not available.
7. **Scope:** whether unrelated files and behaviour remained unchanged.

Do not present preferences as defects, and do not imply that an unperformed check passed.
