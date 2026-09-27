# Phase 7 evidence for the core-layout export route

Status: **Level 2 evidence for one B16 product route.**

The [API instructions](../contracts/phase7-core-layout-export.md) own the
application operation and route. The [current evidence](../current/PHASE_EVIDENCE.md)
owns the task result. The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions)
owns phase and exit status. This record gives no exit, performance, output or
release acceptance.

## Current owner view

| Field | Result |
| --- | --- |
| **Current state** | Protected `main` includes PR #90 at `00e8ba747bca13ae979915f56c9daee9318c59ca`. The exact product-and-test candidate is `9a146f7cb9e435fbb28cd34389a114e011d7ded4`. It has no merge. Phase 7 stays Open at 3/4, and Exit 1 stays Pending. |
| **What changed** | The inherited B16 `run_macro` caller now uses `tracktemplate.api.run_core_layout_export` through an explicit compatibility adapter. The accepted calculation route stays at schema `16`, 25 functions and 40 callers. |
| **What now works** | Standalone, qualified FreeCAD and paired GUI checks show the same B14/B15 result for the supported prepared output plan. The paired GUI comparison covers Create, controlled failure, Save/reopen, DXF, SVG, STL, STEP, manifest output and cleanup. |
| **Limitations/findings** | The two usual repairs are completed (2/2). The final owner-controlled harness exception is completed (1/1). The first failures and the initial independent `BLOCKED` review stay as evidence. The paired GUI result uses normalized equality where route paths, times and serialization metadata differ. |
| **Owner decision** | The owner authorised this bounded Level 2 result through publication. The candidate has no integration or Phase 7 exit decision. |
| **Next action** | Complete the one Documentation Review lifecycle and final validation. If the exact candidate is green, publish one draft for the owner's integration decision. |

## Scope and source

The comparison baseline is protected `main` at
`00e8ba747bca13ae979915f56c9daee9318c59ca`, with tree
`7c756e889192716443ba88b4445704ff69a3ec71`. The exact product-and-test
candidate is `9a146f7cb9e435fbb28cd34389a114e011d7ded4`, with tree
`4ab06ebb42b7b021b7c5cfcebd04de86f7e74a1e`. D-GOV-004 and the project
owner's instruction on 2026-09-27 authorise this bounded Level 2 result.

The B14 and B15 definitions of `run_production_export` are equal. Each
definition has 2,542 bytes and SHA-256
`2de2b2283d550037c3ee0edecc5768ffc802f4c14870db1c326d6e3ff5c94a03`.
B14 and B15 stay unchanged at their accepted full-file identities.

The candidate adds `tracktemplate.application.core_layout_export` and exports
`run_core_layout_export` through `tracktemplate.api`. The B16 compatibility
session supplies the five inherited host operations and binds the existing
`run_production_export` name to the new command. It rejects incomplete,
changed or mixed bindings. The application module imports no FreeCAD or Qt
module.

The separate application-route record has schema `1`. The accepted D-P7-004
calculation route stays at schema `16`, 25 selected functions and 40 caller
identities. The candidate changes none of those functions or callers.

## Standalone and qualified checks

The standalone proof compares B14, B15 and the application command. It covers
a successful manifest, no requested manifest, an ordinary manifest exception
and a `BaseException`. It also checks host-independent import, exact adapter
and host-operation identities, mixed-route rejection and setup rollback.

The qualified FreeCAD proof uses the exact D-GOV-019 host profile. It compares
the native and modular operations for a successful four-format plan and an
injected final STEP failure. It checks the result, output bytes, manifest,
temporary-file cleanup and unchanged FreeCAD document state. The direct log is
a corroborating PASS record with SHA-256
`60033e2aca6ee010e27fc28144a154ea5bb812574803f1155929192976c206bf`.

The related qualified matrix has 17/17 PASS results. Its manifest SHA-256 is
`9160724f79b77092c459094a941f85b265dec323cd0e5457ce3797ae25d5b1f2`.
The direct log and matrix scenario 7 are byte-identical sentinel records. The
paired GUI evidence below supplies the detailed source and cleanup evidence.

The exact-candidate `transition` profile has 7/7 PASS results. Its log directory
is `benchmark-output/validation-pipeline/20260927T111745243239Z`. The standalone
profile log SHA-256 is
`7052a087e46a5284efd9fdaaf65938d873dc0b8e6af08171f1548e6a8d11159f`.

## Paired FreeCAD human-interface proof

The final proof uses the D-GOV-019 profile and one fresh isolated FreeCAD
process for each route. Both routes use the same fixed B14 plain-line fixture.
The fixture SHA-256 is
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.
All 57 recorded source identities match the exact candidate before and after
both routes.

The native B15 route and the modular B16 route both complete. The normalized
workflow comparison has zero differences. Both workflow digests are
`0aab5568f50ef53705cb69c2ac091c7b1d9d2949bbc79d124e76b80519dffd49`.
The proof covers the successful output set and an injected final STEP failure.
It also covers Save/reopen, restored preferences, unchanged source state and
document cleanup with no remaining document.

The comparison receipt has SHA-256
`43f2951b959180796d7310b8c6dccbe9e6cb5971c93c22281c8c4a40b1d7fd77`.
The native route receipt has SHA-256
`ac70eacebf27fb11f6875b66ea004f0dbde015fbfb1cd72fb27860df56877f02`.
The modular route receipt has SHA-256
`e6f68d045cbd94d194fd6eaf54c56592ec8434a21ded6f616fb0ec6578e98821`.

The equality is for the normalized workflow contract, logical output and
metrics. Raw route files can contain different paths, times and serialization
metadata. Only the STL bytes are equal without normalization. These differences
do not give output or release acceptance.

## Repair and review history

Repair 1 corrected only the new GUI proof. It made path normalization,
source-map validation, cleanup rejection and route-envelope checks complete.
The first paired proof then stopped because it applied the modular
schema-`16` route envelope to the retained native route.

Repair 2 corrected only that proof. It checks the retained native schema
`1` route with three functions and three callers, and it checks the modular
schema `16` route separately. The original failed comparison stays at
`20260927T095629483060Z-pair`. Its comparison receipt SHA-256 is
`c3b555301b2b8f3bc3adf540beabff2adf6e9d3060e8ddbeb0cae9160451712d`.
The two usual repairs are completed (2/2).

The first final independent review had a `BLOCKED` result. It found that a
nondefault bridge port could bypass the isolated launcher and could select a
different FreeCAD session. The project owner authorised one final 1/1
harness-only correction. The wrapper and Python runner now reject a nondefault
port before launch. The focused proof tests both command forms and proves that
neither launch path starts. This exception is completed and gives no further
correction authority. The retained initial review receipt has SHA-256
`78023014c8c4e73e2e85be5359bb0834f0e511b86ac8d569ba915a90a803cf21`.

One fresh independent read-only Quality Review inspected the exact final
product-and-test candidate. Its decision is PASS, with no blocker or required
follow-up. It confirms the inherited result and exception behaviour, route
closure, operation identities, rollback and fixed-port isolation. Normal
repair accounting stays 2/2 exhausted, and the owner exception stays consumed
at 1/1. The retained final review receipt has SHA-256
`70b3061b4a74c1984eba5119da062c5f62c91adca003e2ce58f56cd6093d88df`.

## Limits

The paired proof uses one B14 plain-line fixture and the recorded success and
final-task-failure cases. It does not compare every possible prepared plan or
platform arrangement. The direct qualified sentinel has limited provenance.
The paired GUI source map and receipts supply the detailed evidence.

This result supplies the previously missing modular export part of Phase 7
Exit 1. It does not admit or accept that exit. Phase 7 stays Open at 3/4 and
Exit 1 stays Pending. D-P6-008 and every comparison, adapter, caller, removal
and legacy-retirement condition stay in full. Output stays at
private-development status and project status stays `unknown`.
