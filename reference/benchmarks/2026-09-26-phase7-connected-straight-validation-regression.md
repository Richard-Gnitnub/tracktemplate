# Phase 7 evidence for connected straight route validation

Status: **Level 2 evidence for one bounded calculation and B16 caller.**

The [API instructions](../contracts/phase7-connected-straight-validation.md)
own the calculation and routing contract. The
[current evidence](../current/PHASE_EVIDENCE.md) owns the current task result.
The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns phase and
exit status. This record gives no exit or performance acceptance.

## Scope and source

The source state is protected main
`1a9d1d679f75b0893a0351619f79b5fcb70adad2`, after integration of PR
#82. D-GOV-004 and the owner's 2026-09-26 continuation authorise this one
bounded Level 2 result. D-P7-001 keeps Phase 7 open for Core alignment,
station and multiple-track migration.

B14 and B15 have the same 3,235-byte definition of
`validate_connected_straight_routes`. Its SHA-256 is
`d31423808b7379f8b37682fe4e6396acdf953d36b9dafb91ee286478a56b2e9e`.
The source files remain unchanged. Their `run_macro` caller uses this check
after `build_straight_routes` and before
`prepare_straight_routes_production`.

The new calculation uses `tracktemplate.domain.alignment` through
`tracktemplate.api`. A compatibility adapter presents the existing FreeCAD
point coordinates through read-only X and Y views. It allocates no new
native vector. The selected B16 caller now uses that adapter. The routing
record uses schema `12`, nineteen selected functions and 39 caller
identities. After a selection error, it replaces selected values with their previous values.

| Product file | SHA-256 |
| --- | --- |
| `tracktemplate/domain/alignment.py` | `2f5414e9c3cb0f09fb025908ae3fdd388522f8539d6bbd8012f56641861988a3` |
| `tracktemplate/api.py` | `817be707ad65d822f137cd4fc5b49b72ecdffc8d7bc740722b4d57606359b4dd` |
| `tracktemplate/compatibility/transition_workflow.py` | `bf8c7c738ef349055b21c691550d4350983eeb2abed245090a31adc1feee616e` |

## Bounded proof

The standalone comparison has 71 cases. It compares B14, B15, the domain
calculation and the adapter. Cases include independent bypass, entrance and
exit routes, one and three tracks, exact tolerance boundaries, incomplete
records, native read failures and error precedence. It checks the return,
exact diagnostic, read order and unchanged input identities. Its direct
proof has a PASS result. The source import proof rejects FreeCAD and Qt
dependencies in the domain.

The complete standalone pipeline gave PASS results for its validation
preflight, Python syntax check and all 74 standalone validators. It used the
`ci` profile for the contract matrix. The full output remains in its ignored
run directory. The final exact-head CI result is still necessary.

The D-GOV-019 FreeCAD proof has 71 cases with actual `App.Vector` inputs.
The baseline and candidate have PASS results. The candidate proof checks
the selected `run_macro` call before production or a transaction. It also
checks unchanged document state on rejection, routing identity, closure
identity and recovery. The qualified headless matrix then gave PASS results
for its preflight, the new proof and all eleven affected previous proofs.
Each of its 13 gates had a zero exit and its required success sentinel.

The three remaining transition checks for persistence, Coin and Edit also
gave PASS results with their required sentinels. The project reused the
qualified preflight and standalone result for those distinct checks.

The isolated real-GUI comparison uses one connected-straight Generate and
Replace run for each state. The current-main baseline was recorded on
2026-09-20. The candidate ran on 2026-09-26. Both use the same D-GOV-019
profile, copied fixture and frozen protocol. The candidate completes Create,
Edit, Undo/Redo, rejection, Save, reopen and cleanup.

The complete product
comparison has zero differences and the same semantic SHA-256:
`25b5a51c4fbf73466533cc41d4d55dde5077c26e39d501a14a0214ee01842cff`.
The fixture SHA-256 remains
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.
No FreeCAD document remains open after the run.

## Failed proofs and repair limit

This outcome used its two normal source-and-test repair passes. Both are
consumed. The first corrected only a test's source-byte expectation: the
initial helper omitted the last line feed when it hashed the B14/B15
definition. It did not change the legacy source or the product. The second
pass corrected four current-route test expectations and synthetic-host
operations after the route grew from eighteen to nineteen functions.

After the second pass, two synthetic-host rollback tests still stopped with
`KeyError`. They tried to delete the new selected name from a host where
that name had never existed. The primary classification is
`fixture-or-harness-defect`. The original rollback assertion remains valid.

The owner authorised one test-only exception for those two tests. Each now
deletes the name only when it exists. The two original proofs then passed
with their required sentinels. The exception gives no product-source repair
authority and does not change the exhausted 2/2 accounting. The project
keeps all initial failures, corrections and rerun logs. PR #82's separate
2/2 accounting and five consumed exceptions remain historical evidence.

## Resource observations and limits

One frozen same-host micro check used three groups of 10,000 fresh calls for
each of four route cases. The candidate took 2.68 to 2.94 times the
baseline CPU time per call. The additional time is approximately 5 to 12
microseconds per call.

The GUI used one sample per state at different times.
Its wall time was lower in the candidate run, but operating-system cache
and scheduling were not controlled. These values are descriptive. They do
not prove a performance improvement or satisfy D-P6-008.

The independent source-and-test quality review found no blocker. It recorded
the micro-call cost and the need for final standalone, documentation and
exact-head CI checks. The review does not accept an exit.

The proof does not cover physical-platform results, sectioning, all Core
layouts or export bytes. No legacy path is removed. Output stays at
private-development status and project status stays `unknown`. Phase 7
remains Open at 0/4 with all four exits Pending. D-P6-008, every comparison
requirement and every legacy-retirement condition stay in full.

## Retained evidence

Except for the path that starts with `benchmark-output/`, the paths below
are relative to ignored
`tmp/phase7-connected-straight-validation/` in the
`phase7-connected-straight-validation` worktree. The complete output is
available there for targeted retrieval. The dated baseline and candidate
GUI records are under ignored
`benchmark-output/freecad-bridge/phase7-connected-straight-validation/`.

| Evidence | Path | SHA-256 |
| --- | --- | --- |
| Gap selection | `gap-audit.md` | `d14624f3522519c74db989d0dad7141b24f613e348285feb8c2c98f9923a5aae` |
| Direct standalone candidate | `standalone-candidate-01.log` | `1e93ed4ea2507ae6ba13605e4248e39c23fb7f6c7a7d2725b62799a6acf254e1` |
| Complete standalone profile | `benchmark-output/validation-pipeline/20260926T161401205288Z/03-standalone-contracts.log` | `e2fa7b368fb6779b5779ef4e6878d0b89721c2e43c35bca6b91cfcaf129eba06` |
| Direct qualified candidate | `native-candidate-01-result.json` | `c8693241fa59ae721832489a4614c5bc106786e01032bc933a2f1fe4c8d68ec2` |
| Test-only exception | `exception-synthetic-host-rollback-20260926/receipt.json` | `c95ee6eb7c53322cb61dfcbcd1c833d4d4ce3c1e22da2b113e30c6363ec9cb74` |
| Qualified headless matrix | `qualified-headless-matrix-20260926T160333173898Z/manifest.json` | `966ad044b173fb31bc19f9f6a34483381d19e1ce966d3a1b1de382746baacf5f` |
| Remaining transition checks | `remaining-transition-steps-20260926T161737820058Z/receipt.json` | `6405642aec9dbb86455e9088146c17811714245f5c79651b1cd827be629f28ad` |
| GUI comparison | `gui-full-comparison.json` | `c167a5bd7f16ca99a315d3e200dc97963f91983fa5a15b957ed75d9b8d3b91f8` |
| Resource comparison | `measurement-comparison.json` | `d813e37b3385ab3debf54871ecfb7ddd2dffdb95322d635a024b935f0f67d1f3` |
| Independent source-and-test review | `independent-quality-review-20260926T160936844597Z.json` | `9722941867b5c612cdb856d33bb05edb1ed50291afd2997e0f2f76a2bfd67912` |

The current candidate still needs final document validation and
successful exact-head CI before the owner can decide whether to integrate
the draft. Neither check can accept a Phase 7 exit or performance result.
