# Phase 7 evidence for platform length and position

Status: **Level 2 candidate evidence for one bounded calculation and B16 caller.**

The [API instructions](../contracts/phase7-platform-longitudinal-bounds.md)
own the calculation and route. The
[current evidence](../current/PHASE_EVIDENCE.md) owns the task result. The
[Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns phase and
exit status. This record gives no exit or performance acceptance.

## Scope and source

The protected-main baseline is
`365cc49684f40ddfa3ac586112425d30ae6292c6`, after PR #84. D-GOV-004
and the owner's 2026-09-26 continuation authorise one Level 2 result.
D-P7-001 keeps Phase 7 Open at 0/4. The technical candidate is
`1180133c63026766369da3e33b69dd7c9869663e`.

B14 and B15 have the same 2,505-byte definition of
`resolve_platform_longitudinal_bounds`. Its SHA-256 is
`0b2a8eeed70008fce640ad3f4bb56d4c87a70dd1b447002da99db7751c20362d`.
The source files stay unchanged. Their sole direct product caller is
`calculate_platform_boundaries`.

The candidate exposes the calculation from `tracktemplate.domain.alignment`
through `tracktemplate.api`. B16 selects the Core function directly for the
same host name. The caller uses its result after the selected start and
finish stations are known and before later platform geometry. The route
has schema `14`, 21 selected functions and 39 caller identities.

| Product file | SHA-256 |
| --- | --- |
| `tracktemplate/domain/alignment.py` | `09f59fba8fb5362522ed896b06176f4c7b96f82e0dcf14a45d24f9951656d014` |
| `tracktemplate/api.py` | `db3b250a542ba4d74482308907260729a578472e752d4dae30fcfa8b9e82c862` |
| `tracktemplate/compatibility/transition_workflow.py` | `dcfe63b31a0ddbb1b6021f40ae3321ae9a99498643dca3e5db9f9d7d231f09d3` |

## Bounded proof

The retained pre-implementation standalone baseline compares B14 and B15.
It has a PASS result for 34 cases and five ordered-read paths, including an
injected failure at each read. Its raw JSON is in ignored
`tmp/phase7-post84-capability-and-core/platform-bounds-b14-b15-baseline.json`.
The file SHA-256 is
`5fc4daca398a473b27f441b169a829d826eebe6d3c2e76cf522398538ce950ac`.

The candidate standalone proof compares the Core function with the same
cases, returned key order, values, errors and read paths. It also checks
input non-mutation, a FreeCAD-independent import, the selected B16 caller
and rollback after a setup error. It has a PASS result. The raw JSON is
`tmp/phase7-post84-capability-and-core/platform-bounds-candidate-standalone.json`.
Its SHA-256 is
`2faeea9cb5b3fdf8aabe95829a3982eeb461c23d5f0be27868494efb585c7390`.

The D-GOV-019 qualified FreeCAD proof compares B14, the native B16 host
function and the selected Core function for the same 34 cases and five
read paths. It checks a selected-caller rejection, unchanged document
state and route rollback. It has a PASS result with its required sentinel.
The raw log is `tmp/phase7-post84-capability-and-core/platform-bounds-qualified.log`
with SHA-256
`ffeca5de9ad2d7ee0133a81f5a1ba31b84e405d2c8220ae8a3c9fde886749eab`.
The exact-host preflight and all 14 affected qualified proofs have PASS
results. The 14-proof manifest is
`tmp/phase7-post84-capability-and-core/qualified-matrix/manifest.json`.
Its SHA-256 is
`de55af0390a0be31f7a51b55db36142e8e04039d7e2333a4744663372aab4185`.

The complete local `standalone` profile has a PASS result for validation
preflight and Ruff, tracked Python syntax and standalone contracts. The
full output is in ignored
`benchmark-output/validation-pipeline/20260926T192644999425Z/`.

The first affected existing-route proof has a FAIL result because its test
expects `twenty-function` where the new route gives
`twenty-one-function`. A directly dependent test-only correction is repair
pass 1/2. The same proof and the other affected existing-route proofs have
PASS results after that correction. The first failed invocation did not
keep a complete run identity.

A validation-only disposable reconstruction
reproduces the FAIL and candidate PASS. It does not replace the historical
invocation. The reconstruction manifest is
`tmp/phase7-post84-capability-and-core/repair1-reconstruction/manifest.json`.
Its SHA-256 is
`2c34a90dff7b0dfe2568f34daf8a9c29e7d16630fa3ac854977d199e6a31b9ba`.

The paired isolated real-GUI jobs have PASS results on the same exact
D-GOV-019 host. They cover platform Create and Edit, Undo/Redo, two
selected length-and-position rejections, Save, reopen and cleanup. The
product-semantic results match. The comparison has SHA-256
`1050a5aa23fdfe13ced36d98eeca560c8445ae562b33fdd9e94323ce8427f47e`
at `tmp/phase7-post84-capability-and-core/gui-full-comparison.json`.
Both semantic records have SHA-256
`8949ef7be3d85a5940368286749d5158da24d0228310880d90225ef8c81ed9c7`.
The raw GUI records remain in ignored
`benchmark-output/freecad-bridge/phase7-post84-capability-and-core/`.

An independent read-only source-and-test review found no blocker in exact
technical candidate `1180133c63026766369da3e33b69dd7c9869663e`.
Its PASS verdict depends on the affected qualified matrix and complete
transition profile. Both now have PASS results. The primary verdict is in
the collaboration transcript.
The parent transcription at ignored
`tmp/phase7-post84-capability-and-core/quality-review-summary.json` has
SHA-256 `a90b3629abb1ed361ac77c2903e10a58862d790030d1985db7bd893f0391b48c`.
It is not a reviewer-authored receipt.
The first attempted `transition` profile has a FAIL result at its
standalone-contracts gate. The new draft benchmark had no frozen-record
manifest entry. Its full output remains in ignored
`benchmark-output/validation-pipeline/20260926T193426777916Z/`. The
second attempted profile also has a FAIL result at that gate because a
governance mutation proof targeted the prior PR #84 owner-view sentence.
Its full output remains in ignored
`benchmark-output/validation-pipeline/20260926T194409027034Z/`. Neither
attempt reached a FreeCAD gate. The directly dependent evidence identity
and test guard then aligned with the draft. The affected governance proof
rejected all 399 negative mutations and let none escape.

The stable assembled-state complete `transition` profile has a PASS
result for all seven gates. It covers validation preflight and Ruff,
Python syntax, 76 standalone validators and qualified FreeCAD preflight.
It also covers transition persistence, Coin scene and Edit lifecycle.
The full output remains in ignored
`benchmark-output/validation-pipeline/20260926T194901380643Z/`.
The wrapper log at
`tmp/phase7-post84-capability-and-core/transition-profile-stable-draft.log`
has SHA-256
`f153f12fb1c6d2aa08bc6ce62bd2411f6662b2e1419c7ff4e6aa69c3c72596e6`.
The frozen-record manifest binds this benchmark's final byte identity.
Final deterministic validation checks the binding.

## Limits

The candidate does not compare all platform geometry, other Core layouts
or export bytes. It does not remove the legacy path.
GUI resource values from one sample per state are descriptive and give no
D-P6-008 performance credit. The earlier PR #84 2/2 repair accounting and
historical review evidence stay unchanged. This new result is at 1/2 after
the classified test-identity repair.

Phase 7 stays Open at 0/4, all exits Pending. Output remains at
private-development status and project status stays `unknown`.
D-P6-008, all comparison requirements and all legacy-retirement conditions
stay in full.
