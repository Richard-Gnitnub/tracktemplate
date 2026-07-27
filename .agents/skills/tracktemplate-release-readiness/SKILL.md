---
name: tracktemplate-release-readiness
description: Audit a TrackTemplate beta or release candidate against its accepted gates and distributable artifact. Use for version readiness, clean-build reproducibility, Addon packaging, install or upgrade qualification, release notes, notices, compatibility evidence or a go/no-go review before publication.
---

# TrackTemplate release readiness

## Outcome

Produce a fail-closed go/no-go audit for one exact candidate and artifact. Keep
technical evidence, project-owner acceptance and external publication as
separate authority boundaries.

## Responsibility boundary

- `reference/PROJECT_PLAN.md` owns phase, beta and release-candidate gates.
- `$tracktemplate-freecad-addon-research` supplies current first-party Addon and
  Addon Index guidance when required.
- `$tracktemplate-changelog` owns user-facing release notes.
- `$tracktemplate-license-analysis` owns licence, provenance, notices and output
  classifications.
- `$tracktemplate-change-validation` selects and interprets the qualification
  evidence; `$tracktemplate-quality-review` judges the complete candidate.

This skill audits and prepares. It does not choose a version, close a gate,
commit, tag, push, upload, publish or change an Addon Index entry without
explicit project-owner authority.

## Candidate definition

Record:

- exact commit and working-tree state;
- candidate version and whether it is proposed or owner-accepted;
- qualified FreeCAD, Python and platform matrix;
- artifact path, checksum and reproducible assembly procedure;
- included source, resources, dependencies, notices and excluded local
  evidence; and
- supported install, upgrade, migration and rollback boundaries.

## Readiness workflow

1. **Read the gates.** Load only the applicable Phase 10, Phase 11, milestone,
   risk and current-phase evidence sections.
2. **Freeze the candidate boundary.** Reject a moving source tree, unrecorded
   generated payload or artifact assembled from a different state.
3. **Audit the artifact.** Verify package metadata, version consistency,
   dependency declarations, licences/notices, provenance manifests, ignored
   evidence exclusion and source-to-artifact correspondence.
4. **Qualify from a clean environment.** Exercise supported installation,
   first run, representative creation/editing, persistence, migration,
   Validate/Export, GUI interaction, uninstall or rollback, and reinstall or
   upgrade as required by the accepted matrix.
5. **Check non-functional gates.** Include repeated performance budgets,
   recovery, security-sensitive packaging, documentation usability and
   compatibility evidence where required.
6. **Prepare communication.** Derive release notes from accepted validated
   changes and retain known limitations, unsupported paths and rights
   boundaries.
7. **Classify every gate.** Use `PASS`, `BLOCKED` or `CANNOT_VERIFY`; never
   upgrade a partial, headless or unavailable check.
8. **Require explicit decisions.** Separate technical readiness, version
   acceptance, gate closeout and publication approval.

## Guardrails

- Do not publish from a dirty tree or qualify a different artifact from the one
  proposed for distribution.
- Do not call local comparison evidence, restricted data or an unresolved
  dependency distributable.
- Do not substitute headless checks for real-GUI or operator-workflow evidence.
- Do not infer release readiness from elapsed time, story points, changelog
  completion or a green subset of tests.
- Preserve a recoverable previous version and documented rollback route.

## Report

Report the exact candidate, artifact identity, gate matrix, completed evidence,
blocked and unverified items, compatibility and rights boundaries, rollback
readiness, proposed release communication and the explicit owner decisions
still required.
