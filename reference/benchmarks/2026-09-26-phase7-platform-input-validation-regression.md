# Phase 7 evidence for platform input validation

Status: **Level 2 evidence for one bounded calculation and B16 caller.**

The [API instructions](../contracts/phase7-platform-input-validation.md)
own the calculation and route. The
[current evidence](../current/PHASE_EVIDENCE.md) owns the task result. The
[Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns phase and
exit status. This record gives no exit or performance acceptance.

## Scope and source

This task started from clean protected main
`aeec41657c379531b939443619272270cb33cf31`, after PR #83. D-GOV-004
and the owner's 2026-09-26 continuation authorise one Level 2 result.
D-P7-001 keeps Phase 7 open for Core alignment, station and multiple-track
migration.

B14 and B15 have the same 3,753-byte definition of
`validate_platform_inputs`. Its SHA-256 is
`1547dff9a060054e89fe6502a73c4a7cfbfad96cc257ef7a23c672895a1c4d99`.
The source files stay unchanged. Their sole product caller is
`calculate_platform_boundaries`. The new calculation uses
`tracktemplate.domain.alignment` through `tracktemplate.api`. B16 binds the
Core function directly to the same host name. The selected caller uses it
after its enabled check and before platform-boundary geometry. The route has
schema `13`, twenty selected functions and 39 caller identities.

| Product file | SHA-256 |
| --- | --- |
| `tracktemplate/domain/alignment.py` | `a72bcd59e0333b6b3efb5d8fedc051d85934e9dbea123f77f365e5ba8b6867bd` |
| `tracktemplate/api.py` | `3a6aeab642cf83811a1db6ee9502706e3d39c87644e2a60c5f8437eec6a98eb4` |
| `tracktemplate/compatibility/transition_workflow.py` | `1eff5832b03b481d9b7106c9c36817b9499be1f8ec11097519319e8c286196eb` |

## Bounded proof

The original pre-implementation standalone baseline compared B14 and B15.
It gave a PASS result for 29 finite cases. Five paths recorded 1, 18, 22,
35 and 2 ordered reads. Each path also gave the same result after an
injected failure at each read. The candidate direct proof compared the
same cases and read sequence with the Core function. It checked exact error
text, input values and identities, a host-independent import, selected B16
caller and atomic binding rollback. The repaired mutation check also has a
negative test that changes a configuration field and an alignment field.
The repaired direct proof gave a PASS result.

The D-GOV-019 qualified FreeCAD proof compared the inherited host function
and the Core function with the same 29 cases and five read paths. It checked
selected B16 caller rejection, unchanged document state and binding rollback.
The original baseline and candidate gave PASS results. After the test-only
repair described below, the affected baseline and candidate proofs again
gave PASS results. The twelve affected previous qualified proofs also gave
PASS results with their required success sentinels. The complete local
`transition` profile then passed all seven gates: validation preflight and
Ruff, Python syntax, all 75 standalone validators, exact FreeCAD preflight,
transition persistence, Coin scene and Edit lifecycle. The complete raw
output remains under ignored
`benchmark-output/validation-pipeline/20260926T173227868496Z/`.

The paired real-GUI check used one fresh isolated process per state on the
same exact D-GOV-019 host. It copied the same fixture for each process.
Both processes completed platform Create and Edit, Undo/Redo, a selected
caller rejection for invalid clearance, Save, reopen and cleanup. The full
stable recipe has the same SHA-256 in both states:
`64d7f42b0544ec2a0f4f8e7149db1d133f2329a227a6a514dd39d045e8ced973`.
The comparison removed only the copied file path, timing and resource
fields from equality. The raw records keep those fields. The selected
rejection text and document and history state match. No FreeCAD document
remained open after either process.

## Failed proofs and repair limit

The first affected current-route proof stopped because its test expected
`complete nineteen-function` after the route grew to twenty functions.
This was a stale test expectation. Normal repair pass 1/2 changed eight
instances of that expected diagnostic. It changed no product source or
historical contract. The original FAIL remains in the retained manifest.
The failed main-circle proof then passed, followed by all eleven affected
Phase 7 standalone proofs. The Phase 4 route-retirement proof also passed.

The first independent source-and-test review then returned `BLOCKED`. Its
one `BLOCKER` was a test-harness defect: the standalone input snapshot did
not descend into the tuple that held the two mutable inputs. A read-only
mutation probe showed `mutation_assert_detects=false` for the original test
SHA-256 `8f5c1ddf908a74d727a533982c8344eec7e015cc9600214b597d19c53e55aeb9`.
Normal repair pass 2/2 changed only that snapshot and added a negative
mutation check. The repaired test SHA-256 is
`8f12c9b6f7121a7bb4587cc36928aea1646fd06170cd45a9a20c93dde53829e4`.
The standalone and qualified baseline and candidate proofs passed after
that repair. One FreeCADCmd command with an unsupported `--baseline-only`
option is retained as no-proof invocation evidence. The corrected command
used the test's baseline environment flag. The original review verdict
remains `BLOCKED`; it is not converted to acceptance. The normal repair
allowance for this outcome is now 2/2 exhausted. PR #83's separate 2/2 and
owner-authorised test-only exception remain historical evidence. A fresh
independent read-only source-and-test review accepted the repaired exact
candidate with no blocker. The original `BLOCKED` verdict remains in its
own retained receipt and is not changed by that final review.

## Retained evidence and limits

Full output and SHA-256 manifests remain in ignored
`tmp/phase7-platform-input-validation/` in the named worktree. The
original and repaired direct proof logs are in `baseline/`, `candidate/`
and `repair2/`. The original affected test FAIL and repair1 PASS records
are in `affected-current-route-tests/` and
`affected-current-route-tests-repair1/`. The exact qualified baseline and
candidate records are in `qualified/` and `repair2/`. The twelve-proof
qualified matrix has manifest SHA-256
`982325a07c9aa498f744baf4099738510ccb05d70d9684283a52a5ebe5041946`.
The GUI raw records are in ignored
`benchmark-output/freecad-bridge/phase7-platform-input-validation/`. Its
comparison manifest has SHA-256
`e8d443645d04a9d7024f6595baeb551ed0fcc42c436f972d888a401202381ec8`.
The original review and final repair receipts are in
`quality-review-original.json` and `repair2/manifest.json`.

The GUI has one sample per state. Cache and scheduling were not controlled.
Timing and resource values are descriptive and give no D-P6-008 credit.
The proof does not cover every custom Python container, all platform or
sectioning geometry, other Core layouts or export bytes. It does not remove
the legacy path or change its retirement conditions. It supplies bounded
evidence for Phase 7 Exits 1, 2 and 3, but accepts no exit. Phase 7 stays
Open at 0/4. Output remains at private-development status, and project
status stays `unknown`. D-P6-008 and all comparison and legacy-retirement
conditions stay in full.
