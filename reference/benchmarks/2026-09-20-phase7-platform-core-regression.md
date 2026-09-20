# Phase 7 evidence for the platform-core calculation

Status: **Level 2 evidence for the bounded API and B16 caller scope.**

The [API instructions](../contracts/phase7-platform-core.md) define the
calculation, result and host conversion. The
[current evidence](../current/PHASE_EVIDENCE.md) owns the task result. The
[Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Scope and source

Protected main was
`009ca95e4412477a1c09639793c13b1a6adad496` when this task started. The
owner's `$tracktemplate-continue` instruction authorised one subsequent
repository-evidenced Phase 7 result with authority from D-GOV-004 and D-P7-001.

The B14 and B15 `build_platform_core` definitions start at line 7498 and end at
line 7676. Their exact source segments are equal. The source-segment SHA-256 is
`9d8c270c673617279fb88abddab1db4f6d21b8855d9d79017a56f196e37ef9f2`.
Their normalised AST SHA-256 is
`7d90b2aeb2e63904d08e8bad91c4d5a98399e5df6eadb268d0031e55b5c44322`.
B14 and B15 stay unchanged.

The candidate moves the complete calculation to
`tracktemplate.domain.alignment`. `tracktemplate.api` supplies the public
function. The B16 `prepare_track_alignment` caller uses it through one
compatibility object. That object changes only new XY point pairs to native
`App.Vector` values.

The product now selects fifteen functions and validates 39 caller routes. The
routing record uses schema `10` and contract ID
`tracktemplate:phase7:platform-core:1`. It rejects a mixed set of selected
values. After a selection error, it puts each previous value back and removes
each name that was initially missing.

The task changes no B14 or B15 source, launcher or frozen host loader.
It changes no persistence contract, output contract, phase criterion, risk,
decision or condition to remove a legacy path.

## Pre-change characterisation

The pre-change proof has a PASS result for the two immutable references. For
each reference, it records these groups:

- Seven usual calculation groups.
- Twenty-two calculation boundary groups.
- Eight complete parameter grids.
- Six usual solver groups and nine solver diagnostics.
- Four controlled solver records.
- Nine complete `prepare_track_alignment` records.
- Six native builder records.

The records for B14 and B15 are equal. The characterisation record has
SHA-256
`054f7ec0ee6076bb30ecf2febb89ad325a9fd1b8bdfbf8b96046037cfc066be4`.
The non-overwriting pre-change manifest has SHA-256
`cc6fc81949d788331a511db9e199818f4f4348187b827b23fe2333e96b1f69b9`.

## Calculation and caller proof

The standalone proof compares B14, B15 and the candidate. It checks seven
complete results for valid inputs and four results for invalid inputs. The
proof keeps the eight-parameter signature with no defaults. It also keeps
these items:

- Local left-turn XY values in millimetres and headings in radians.
- The exact named-item sequence in the result.
- The 3 mm point spacing and 480-step endpoint displacement calculation.
- Geometry and straight-curvature tolerances.
- Endpoint corrections and calculation sequence.
- Complete diagnostic type and text.
- New result, list and point identities for each call.
- Translation of points without a change to headings.
- Minimum-radius metadata.
- Host-independent import.

The standalone proof also checks the exact compatibility-object identity
and the `prepare_track_alignment` edge. It checks fifteen selected functions,
39 callers, selected calculation dependencies, mixed-route rejection and
complete recovery after a setup error. The last bounded log has SHA-256
`8e546e234134fd0936c9771fa7ed85e742f4a3894570956b989abe8fb8d17c6c`.

The qualified proof uses
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2`, the exact profile that
D-GOV-019 qualifies for functional compatibility. It checks the B16 launcher,
schema `10`, all fifteen selected functions and all 39 callers. It compares
seven native builder results, four invalid results and the complete B16 caller
records with the retained host. All new points are exact `App.Vector` values
with Z equal to zero. FreeCAD document state stays unchanged.

The qualified result has a PASS result and SHA-256
`1097eed88b965c0edb04b1affe257da2585b3ea2e575a14e90718a86d44053eb`.
The qualified routing matrix has a PASS result in nine of nine new FreeCAD
processes. Its manifest has SHA-256
`9edc6b586d6a8769fc5397679e033cede84ae730ad94bc274654188d3fe469c8`.

The complete transition regression pipeline has a PASS result for all seven
checks. It includes the validation preflight, Ruff, Python syntax, standalone
contracts, the qualified-host preflight, persistence, the Coin scene and the
Edit lifecycle. Its top-level log has SHA-256
`85273b417faa204f40848b2d86f4eb27ed8d2dabf4a06710104f042144a9caab`.

## Real-GUI lifecycle and descriptive measurements

The real-GUI proof uses the accepted PR #79 candidate run as the current-main
baseline. It does not do that run again. The baseline uses schema `9`, fourteen
functions and 39 callers. The new candidate uses schema `10`, fifteen
functions and 39 callers. The two runs use the D-GOV-019 qualified profile,
bridge pin `660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7` and the same source fixture.
The fixture SHA-256 stays
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.

The candidate completes this B16 Generate/Replace sequence in one new isolated
GUI process:

1. Create a platform-widening track with 40 mm start and finish spacing.
2. Complete Undo and Redo for creation.
3. Edit start spacing to 41 mm.
4. Complete Undo and Redo for the Edit operation.
5. Reject an infeasible 10,000 mm start spacing without a document or history
   change.
6. Save, close and reopen the document.
7. Restore preferences, close all documents and stop the exact Flatpak
   instance.

The complete product-semantic records are equal with zero differences. The two
records have this digest:
`66dd4bc2b76c3c732db519d003c440e12194004cfad210e380cb5fc7cba4187e`.
The comparison record has SHA-256
`6d69732dea7b660e75ce3319fae1c584f9c8f57e72e24e720f13eca2e4dea5ff`.
The completion record has SHA-256
`12e3443eee634923cc19a6b98e54db0cdc37e92b8441bb2878e46dacf2269465`.

The next table gives one descriptive sample for each state. Time values use
milliseconds. RSS changes use MiB.

| Action | Retained current-main wall | Candidate wall | Retained current-main CPU | Candidate CPU | Retained current-main RSS change | Candidate RSS change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Create widening | 13477.823 | 2770.682 | 2489.856 | 2606.785 | 161.840 | 162.914 |
| Edit widening | 13154.773 | 2048.499 | 2212.067 | 2174.326 | 56.242 | 49.734 |
| Reject infeasible spacing | 2151.076 | 350.971 | 243.988 | 304.644 | 0.375 | 0.395 |
| Save, close and reopen | 469.751 | 829.965 | 825.340 | 928.100 | Not recorded | Not recorded |

The two runs occurred at different times. The method does not control operating
system cache or scheduling. Each state has one GUI sample. Endpoint RSS
includes all memory in the loaded FreeCAD process. It does not isolate
allocations. Thus, the
values do not show typical cost, a performance result or an optimisation
direction.

The proof does not compare physical screen pixels, physical-platform results,
sectioning results or export bytes.

## Preserved failures and bounded corrections

The first pre-change evidence command used `.venv/bin/python` before the new
worktree had its necessary virtual-environment link. It ran no proof. The
environment classification and subsequent run preserve this no-proof result.

The first bounded standalone proof used literal set braces in a formatted
isolated-import script. Repair pass 1 escaped only those braces. The second
bounded proof compared two `namedtuple` vector types from different constructor
calls.
Repair pass 2 changed only that assertion to use the exact host vector type.

The third bounded proof showed that the product correctly rejected a corrupted
dependency. That test used an internal dependency spelling as the expected
result. The stable platform diagnostic was the correct expected result. Repair
accounting was 2/2 before this exception. The owner
authorised one test-only exception to use the stable diagnostic as the expected
result. The subsequent bounded run had a PASS result.

The first qualified proof included a retained expected-rejection input in a
success-only loop. The earlier complete caller comparison showed the same
rejection. The owner authorised a second test-only exception to assert that
exact retained rejection. The subsequent bounded qualified run had a PASS
result.

The raw classification receipts use the phrase `test-harness defect`. The
canonical failure class for these three test defects is
`fixture-or-harness-defect`. This record keeps the raw receipts unchanged. It
identifies `fixture-or-harness-defect` as the canonical failure class for that
phrase.

Source-and-test repair accounting stays 2/2. The two owner-authorised test-only
exceptions are consumed. The exceptions do not reset or extend the repair
limit. The diagnostic read that followed the first qualified failure had its
own command defect and supplies no proof.

The first real-GUI preflight found no pinned `freecad-cli` checkout in the
new worktree. No GUI or product operation ran. The setup workflow installed the
exact retained bridge pin in the ignored worktree path. The exact-profile
preflight then had a PASS result. The recovery receipt has
SHA-256
`2ea095b067e87f0749cd47ad79ab7a70c0aba70330cab50e3a2c4cd1d7da1596`.

The first ignored GUI preparation guard rejected a historical recipe
identifier after it correctly changed all output paths. The canonical
classification is `fixture-or-harness-defect`. The correction changed only
that ignored guard. It kept the historical recipe identifier and continued at
the first preparation file that was not complete. It changed no product,
tracked test or source file. It is not part of the 2/2 source-and-test repair
accounting. The
classification record has SHA-256
`eea2c84199107e3c0897da6533fbbb3c27569244a882a2e0ebee8b9a05964b5d`.

## Independent quality review

A new independent reviewer completed the first pass read-only. The reviewer
examined the complete diff, source, tests, raw failures, classifications,
manifests, qualified-host logs and real-GUI records. The verdict is PASS. The
review has no `BLOCKER`, `REQUIRED_BEFORE_EXIT`, `BACKLOG`, `OPTIONAL`,
`MISSING`, `EXTRA` or `CANNOT_VERIFY` finding.

The review gives a PASS result for the B14/B15 provenance, host-independent
boundary, native point conversion, exact caller edge, routing, recovery,
exclusions and repair accounting. The reviewer changed no file and gave no
phase, performance, output, migration or release acceptance. The review
receipt has SHA-256
`36ccfc7d4d7699769cb46ff0c4f5049a6b92a56341787b50e64d9d82280eb00d`.

## Evidence identities

The active worktree is `TrackTemplateMacro-worktrees/phase7-platform-core` on
branch `agent/phase7-platform-core`.

| Repository path | SHA-256 |
| --- | --- |
| `tracktemplate/domain/alignment.py` | `27cbb4e7cdb600cc64fb2eac957e64ee1b143e2c863b2821a3dc156466bddb08` |
| `tracktemplate/api.py` | `89b8ebcafabc6c9e6f715cad67e91850e6cddb79e3b88d482d77394e405dc005` |
| `tracktemplate/compatibility/transition_workflow.py` | `e6c0f97f07367e478cc5539029e50054d33e71635bc1746f5fabfca2457da216` |
| `tests/validate_phase7_platform_core.py` | `bd142e3a9344a527750d4363a2ad4d8947acbc85fdc7590eb32df8f33dc9dcdb` |
| `tests/freecad_validate_phase7_platform_core.py` | `ed58f6e48f234e0eaf1e414253d078ef712dfa0190ca77e0a65d6bb6f194ea86` |

The next records are in the worktree's ignored
`tmp/phase7-platform-core/` directory. They preserve the initial and subsequent
results in different files.

| Record | SHA-256 |
| --- | --- |
| `selection-and-route.json` | `cf1162f0020f3b06fbe5e522764cc782041db1142216f3b1e04d55a8c1e92708` |
| `prechange-01/prechange-manifest.json` | `cc6fc81949d788331a511db9e199818f4f4348187b827b23fe2333e96b1f69b9` |
| `prechange-01/b14-b15-platform-core-characterisation.json` | `054f7ec0ee6076bb30ecf2febb89ad325a9fd1b8bdfbf8b96046037cfc066be4` |
| `test-exception-01/authority.json` | `4a11b1f53f1c17cf811c80f2e10477312736c97454125cac2a84d1e5801c1e9f` |
| `test-exception-01/focused-standalone.log` | `8e546e234134fd0936c9771fa7ed85e742f4a3894570956b989abe8fb8d17c6c` |
| `qualified-exception-02/authority.json` | `0bcc17db70736804376f7a2efa988bf1f5f75bbd9ac95ba6ecfee7d5eddb4894` |
| `qualified-exception-02/candidate-qualified-platform-core.json` | `1097eed88b965c0edb04b1affe257da2585b3ea2e575a14e90718a86d44053eb` |
| `qualified-routing-matrix-01/matrix.json` | `9edc6b586d6a8769fc5397679e033cede84ae730ad94bc274654188d3fe469c8` |
| `regression-01/transition-regression.log` | `85273b417faa204f40848b2d86f4eb27ed8d2dabf4a06710104f042144a9caab` |
| `gui-fixed-protocol.json` | `7ffcc23a9028e65d25c2ef321b107aae0bab22008d1b2160c9acaf8382d5a82e` |
| `gui-full-comparison.json` | `6d69732dea7b660e75ce3319fae1c584f9c8f57e72e24e720f13eca2e4dea5ff` |
| `gui-completion.json` | `12e3443eee634923cc19a6b98e54db0cdc37e92b8441bb2878e46dacf2269465` |
| `independent-quality-review.json` | `36ccfc7d4d7699769cb46ff0c4f5049a6b92a56341787b50e64d9d82280eb00d` |

## Acceptance boundary

This migration supplies bounded evidence for the API without FreeCAD or Qt in
Exit 3. It supplies equal-result evidence in Exit 2 and B16 workflow evidence
in Exit 1. It accepts no Phase 7 exit. Phase 7 stays Open at 0/4, with all four
exits Pending.

D-P6-008 stays in full as a deferred, unmet obligation before Phase 10 beta
acceptance. The descriptive GUI values give no performance acceptance and
select no optimisation. All recorded limitations and all conditions to compare
results and remove legacy paths stay in full.

The task gives no physical-platform, sectioning, export-byte, production,
output or release acceptance. Project status stays `unknown`, and output keeps
private-development status. The exact-green draft must have its own owner
decision before integration.
