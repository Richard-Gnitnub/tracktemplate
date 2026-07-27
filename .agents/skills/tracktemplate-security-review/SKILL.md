---
name: tracktemplate-security-review
description: Review TrackTemplate trust boundaries and security-sensitive changes. Use for untrusted files or archives, stored FreeCAD data, path or subprocess handling, dynamic loading, dependencies, credentials, network integrations, export destinations, packaging or a reported security weakness.
---

# TrackTemplate security review

## Outcome

Identify credible security failures at the actual trust boundary, preserve raw
evidence and recommend the smallest fail-closed control without overstating
assurance.

## Responsibility boundary

- Use `$tracktemplate-license-analysis` separately for rights, notices,
  provenance and licence compatibility.
- Use `$tracktemplate-api-design` for network authentication, OAuth, webhook,
  GraphQL or other public contract design.
- Read `reference/RECOVERY_AND_BACKUP.md` before filesystem, archive,
  subprocess, destructive or operator-document work.
- Route implementation through `$tracktemplate-python-writing`, evidence
  through `$tracktemplate-change-validation`, and final judgement through
  `$tracktemplate-quality-review`.

This is an engineering review, not a penetration-test certification, legal
opinion or authority to publish a vulnerability.

## Threat-boundary workflow

1. **Define scope.** Name the asset to protect, entry point, trust boundary,
   plausible actor, supported environment and affected operator workflow.
2. **Trace data and authority.** Follow input through parsing, validation,
   canonical state, FreeCAD properties, temporary files, subprocesses, network
   calls and output. Record where privileges or filesystem reach increase.
3. **Inspect applicable hazards.**
   - path traversal, unsafe archive extraction, symlink and overwrite races;
   - unsafe deserialisation, dynamic evaluation, imports or executable content;
   - command construction, environment inheritance and subprocess failure;
   - malformed or oversized FCStd, JSON, package or export input;
   - credential exposure, insecure transport, replay, missing authentication or
     excessive scopes in an accepted network boundary;
   - dependency provenance, pinning, integrity and supported-runtime exposure;
   - secrets, private paths or operator data in logs, evidence or generated
     artifacts; and
   - fail-open validation, partial mutation, rollback or recovery gaps.
4. **Verify exploitability.** Distinguish a reachable weakness from a pattern
   match or theoretical concern. Use copied inputs and disposable temporary
   locations; never probe production or another party's system without explicit
   authority.
5. **Classify the finding.** Record impact, preconditions, affected versions,
   confidence, evidence and whether the issue is confirmed, suspected,
   mitigated or cannot be verified.
6. **Design the control.** Prefer strict parsing, allow-lists, bounded resource
   use, resolved paths, least privilege, atomic replacement, explicit failure
   and recoverable rollback. Preserve compatibility or require an accepted
   migration.
7. **Prove both paths.** Add focused evidence for accepted input and malicious
   or malformed rejection without weakening diagnostics.

## Guardrails

- Do not expose secrets, private operator data or an unredacted exploit in
  normal reports.
- Do not add a dependency, network service, credential store or automatic
  updater without explicit approval.
- Do not claim security from sandboxing, file extensions, a successful parse or
  lack of a known exploit alone.
- Do not mutate the only copy of an operator file or use production endpoints
  for testing.

## Report

Report scope and trust boundaries, confirmed findings ordered by impact,
reproduction limits, affected versions or paths, proposed controls, validation
completed, residual exposure, disclosure sensitivity and every decision or
external review still required.
