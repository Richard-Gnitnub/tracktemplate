# Phase 7 evidence for platform-transition calculations

Status: **Level 2 evidence for the bounded API and B16 caller scope.**

The [API instructions](../contracts/phase7-platform-transitions.md) define the
calculations and their sequence. The
[current evidence](../current/PHASE_EVIDENCE.md) owns the task result. The
[Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions) owns exit status.

## Scope and source

The owner authorised PR #78 head
`ba3fa532e7f0a32c1a9a6120bbc4cc4ec46a9c34`. Protected main merged it at
`0e6bd083f4ed1774685b6d3a463eb75f763c04aa`. The worktree then moved its
preserved local candidate and evidence to that exact main state without
loss of content.

The earlier platform-transition calculation was absent from Core. The
candidate moves its six-function analytical closure to
`tracktemplate.domain.alignment`. `tracktemplate.api` supplies the three public
functions. The existing `prepare_track_alignment` and `build_platform_core`
callers get those functions through the B16 workflow.

The product now selects fourteen functions together and validates 39 actual
caller routes. This result adds three selected functions and the
`build_platform_core` caller to the previous schema `8` record. The new record
uses schema `9` and contract identity
`tracktemplate:phase7:platform-transition:1`.

The composition check also validates the three internal calculation functions
and each call between the six functions. After a selection error, the workflow puts
all previous values back. It removes a supplied value when that name was
initially absent.

B14, B15, the launcher, the host loader, previous machine contracts and the
historical tools to compare results stay unchanged. Sixteen earlier tests
receive only the directly dependent schema, function and caller identities.
Two new tests supply the bounded proof with standalone Python and qualified
FreeCAD.

The primary repository keeps the non-overwriting preimplementation archive
with SHA-256
`2d1b35036e57d89f38db0f9dc231a123e0ed71fdb0db1c8fb30274b08c4bdad8`.
Its receipt has SHA-256
`75f3b86cc931ff3f826ce6f2c1815a82da3f27392b2bf0883b140544cf00c2da`.
The earlier B0 repair backup receipt has SHA-256
`71decb97051d23b7ab9a51975db3f3ac2617b75cb0e7dc094669500e9548479c`.
All local work, failed evidence and later receipts stay in their existing
worktrees and ignored evidence paths.

## Calculation and caller proof

The B14 and B15 definitions have the same content. The B14 definition starts
at line 7081, and the B15 definition starts at line 7495. Their combined
function fragment has SHA-256
`72c77c486bf4e72e15be1f43015cb98ca9e549fcebdaafad4578fa6019809ca4`.
The actual calls are in `prepare_track_alignment` and `build_platform_core`.

The baseline characterisation has a PASS result for both immutable sources.
For each source, it includes seven usual calculation groups, 22 boundary
groups, eight complete search grids and six usual solver groups. It also
includes nine
diagnostic groups, four complete call traces, nine complete preparation records
and six native builder records.

The candidate gives equal complete results in those groups. The proof keeps
parameter names and defaults, calculation order, Simpson weights, search
grids, stopping limits, diagnostics, input identities and mapping order. It
also keeps the existing host construction with native vectors and all caller
side effects.

The standalone candidate receipt has SHA-256
`a59672e7f39dbce9e4743a90ff0e2c1d9f9ddd19c9818fd979d2ed203203b64f`.
The result record has SHA-256
`128b9afeefe208b7a0230d90e6b585db7d378aaa530a7debef08c0baa1eab50e`.

The qualified proof uses
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2`, the exact profile
qualified by D-GOV-019. It checks the B16 launcher, schema `9`, all fourteen
selected functions, all 39 callers and the existing native preparation for
40 mm and 41 mm start spacing. The complete candidate result equals the B15
result. All points are exact `App.Vector` values with Z equal to zero. FreeCAD
document state stays unchanged. The result record has SHA-256
`843b64dd94041f6b706aece5ef87749f19e16a3b9edaea0a3ad29b0776904cfa`.

Thirteen selected standalone test sets have PASS results. They include Phase 1,
Phase 2, Phase 3 routing and workflows, Phase 4 route removal, all seven earlier
Phase 7 results and this candidate. The manifest has SHA-256
`01dc3f36ce94dd3e67a44edf2837d3b0ff090c75590a4e4db768b633eff2f9f7`.

Eight new qualified FreeCAD processes and the completed candidate proof also
have PASS results. They include the Phase 3 caller and all eight Phase 7
calculation boundaries. Each new process has exit status zero and its necessary
success sentinel. Their completion receipt has SHA-256
`2bf0570a570c6d2b2d574c4287a1d7d235da415b66e0cb785cf61fff58e5e53d`.

The complete transition regression pipeline has a PASS result for all seven
stages. It includes the validation preflight, Ruff, syntax, 70 standalone
contracts, the qualified-host preflight, persistence, the Coin scene and the
Edit lifecycle. Its top-level log has SHA-256
`cfbec8fc8d81d4e5d5a154ad478356f4b658db62142dbb3a67d89b9ccc13ded2`.
Standalone checks use Python 3.12.3 and Ruff 0.16.4.

## Direct result and cost evidence

The fixed direct plan uses different FreeCAD processes in this sequence:
`B0`, `C0`, `C1`, `B1`, `B2`, `C2`. Each state has three processes. Each
process has one initial call and ten subsequent calls for each of two cases.
The case order alternates for the second pair.

Each measured call contains one complete `prepare_track_alignment` operation.
It includes both shape solvers and the retained native `build_platform_core`
construction. The inputs use 600 mm entry and exit transitions, a 600 mm main
radius, a 655 mm platform radius and a 90-degree turn. The `create-40-40` case
has 497 points. The `edit-41-40` case has 500 points.

All six samples have PASS results. The 132 calls give 132 true results for each
of these invariants:

- Complete results are equal.
- The main alignment is unchanged.
- Metadata identities are preserved.
- Configuration input is unchanged.
- Native points are valid.

The complete input and retained first output are equal for each case in all six
samples. All later calls have a true complete-comparison result. The completion
record has SHA-256
`b131cbe2e2d57f17acc6eaabf5cd683aa3c8d433ff3f5fa2c8a70562b3c64edc`.

The first B0 sample finished 4,001.454889 seconds before C0 started. Product
work and recovery occurred in this interval. The plan does not control the
operating system file cache or scheduling. Thus, these measurements do not
show typical workflow cost or performance acceptance.

The next table gives medians and [minimum, maximum] from the thirty subsequent
calls for each case and state. Times use microseconds. The paired change uses
the medians from the three related process pairs.

| Case and metric | Baseline median [minimum, maximum], microseconds | Candidate median [minimum, maximum], microseconds | Paired median change [minimum, maximum], microseconds | Paired median change, % |
| --- | --- | --- | --- | --- |
| `create-40-40` wall | 88132.1675 [86020.3890, 90421.8740] | 87245.6305 [85859.3540, 92451.2370] | +157.0730 [-3335.7500, +369.9120] | +0.1807 |
| `create-40-40` CPU | 88125.4030 [86009.1020, 90416.2680] | 87217.3490 [85859.9440, 92453.6110] | +136.8295 [-3336.3635, +358.8310] | +0.1575 |
| `edit-41-40` wall | 89395.3755 [86523.8250, 92410.5010] | 87550.0830 [85816.7230, 90391.1050] | -1046.4515 [-2964.6520, -43.3060] | -1.1701 |
| `edit-41-40` CPU | 89383.7315 [86524.7170, 92387.1060] | 87525.7400 [85778.2210, 90368.0880] | -1052.3690 [-2956.8775, +113.5120] | -1.1768 |

The next table gives the initial call in each process. The first case in a
process is its first platform-preparation operation. The raw record identifies
the order for each sample.

| Case and metric | Baseline median [minimum, maximum], microseconds | Candidate median [minimum, maximum], microseconds | Paired median change [minimum, maximum], microseconds |
| --- | --- | --- | --- |
| `create-40-40` wall | 87550.513 [85025.390, 89415.533] | 85779.873 [85668.291, 87705.487] | +154.974 [-3635.660, +642.901] |
| `create-40-40` CPU | 87543.013 [85027.736, 89408.243] | 85757.011 [85650.972, 87705.877] | +162.864 [-3651.232, +623.236] |
| `edit-41-40` wall | 87718.241 [86044.064, 91816.482] | 87449.643 [86126.220, 87691.300] | -26.941 [-5690.262, +1405.579] |
| `edit-41-40` CPU | 87701.449 [86029.019, 91806.099] | 87432.707 [86120.942, 87667.734] | -33.715 [-5685.157, +1403.688] |

RSS and high-water RSS include the loaded application, untimed preparation and
result records. They do not isolate the maximum memory use of one operation.
The paired median RSS difference is +1,216 KiB, with a range from +1,020 KiB to
+2,168 KiB. The paired median high-water RSS difference is -36 KiB, with a
range from -620 KiB to +304 KiB. All recorded within-call RSS and high-water
changes are zero.

The direct evidence shows small changes in both directions. It gives no
performance acceptance, performance hypothesis or authority to change the
measurement rule. D-P6-008 stays unchanged.

## Human-interface proof

The fixed GUI protocol uses one baseline and one candidate sample. The
baseline is protected main at the start of this task. Its route has schema `8`,
eleven functions and 38 callers. The candidate has schema `9`, fourteen
functions and 39 callers. Both use the D-GOV-019 qualified host and bridge pin
`660ed03f5dc6aeb2dd0e623cc4ed5880b4c90cb7`.

Each sample starts in a new isolated FreeCAD GUI session with a copy of the
same source fixture. The fixture SHA-256 stays
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`
before and after the two runs.

The sample completes these operations with the actual B16 Generate/Replace
workflow:

1. Create a platform-widening track with 40 mm start and finish spacing.
2. Edit its start spacing to 41 mm.
3. Complete two Undo/Redo cycles.
4. Reject an infeasible 10,000 mm start spacing without a document or history
   change.
5. Save, close and reopen the document.

The checks include complete product-semantic data, shapes, stable identities,
stored inputs, history, persistence, preference restoration and cleanup. Both
samples keep the modular route active, preserve all binding identities and
close their document.

The complete semantic records are equal with zero differences. Their common
digest is
`66dd4bc2b76c3c732db519d003c440e12194004cfad210e380cb5fc7cba4187e`.
The comparison record has SHA-256
`2fc4b0aec281b0c66b2c7986420addd93f4c8d16dfafb3404f20d02f3838f948`.
The complete GUI receipt has SHA-256
`fbe3c937663bf79068f8d87ee305eeed6f0f0ac0f92ef756d9617c2941ec088f`.

The next values are one sample per state. They are descriptive measurements.
Wall and CPU values use milliseconds. RSS changes use MiB.

| Action | Baseline wall | Candidate wall | Baseline CPU | Candidate CPU | Baseline RSS change | Candidate RSS change |
| --- | --- | --- | --- | --- | --- | --- |
| Create widening | 13145.538 | 13477.823 | 2514.270 | 2489.856 | 158.344 | 161.840 |
| Edit widening | 13162.014 | 13154.773 | 2156.439 | 2212.067 | 55.242 | 56.242 |
| Reject infeasible spacing | 2189.588 | 2151.076 | 255.857 | 243.988 | 0.379 | 0.375 |
| Save, close and reopen | 555.843 | 469.751 | 795.529 | 825.340 | Not recorded | Not recorded |

The create wall time is higher by 332.286 ms, or 2.5277%. Its RSS change is
higher by 3.496 MiB. The Edit CPU time is higher by 55.628 ms, and its RSS
change is higher by 1.000 MiB. The other time differences have both signs.

The GUI protocol records endpoint RSS for the loaded application. It records no
GUI process high-water value and does not isolate allocations. The operating
system cache and scheduling are uncontrolled. These single-sample results do
not show typical cost or give performance acceptance. They also do not prove
equal export bytes or a physical screen result.

## Preserved failures and bounded corrections

The first baseline characterisation used 50 mm as a usual outside spacing.
Both immutable references rejected it. The retained classification identifies
a fixture defect. Repair pass 1 changed the usual values to the verified 40 mm
and 41 mm values. It kept 50 mm and 51 mm as rejected cases. Product source and
the comparison rule did not change.

The first B0 helper check used the default Python 3.13 AST representation. That
default omits empty fields and was different from the Python 3.12 identity in
the frozen plan. Repair pass 2 set `show_empty=True` and added suffix support to
preserve the initial receipts. The repair stopped before product composition
and changed no measurement rule or product source.

The repaired attempt then found an unqualified installed runtime. It stopped
before product composition. D-GOV-019 later qualified the exact installed
Python 3.13.15 and PySide6/Qt 6.11.2 profile for functional compatibility. A
separate Level 3 decision re-froze only the host identity for B0. The frozen
manifest has SHA-256
`a3657e3f983473b293320afe4afa2715794afb56aa31b2a780645779fb6f1386`.
The subsequent B0 has a PASS result.

Repair accounting stays 2/2. The host re-freeze and environment recovery are
not candidate repairs.

The first standalone candidate proof found literal set braces in the
`_host_independent_import` format string. The owner authorised one test-harness
exception to escape only those braces. The exception is consumed. The initial
FAIL result stays available. A mistyped command used a hyphenated test filename
that does not exist. It executed no proof and stays no-proof evidence.

The correct rerun has a PASS result. Repair accounting did not reset.

The first full regression run found mode `0664` on the ignored local STE cache
instead of required mode `0600`. Independent classification identified a local
environment-state defect. The recovery changed only the mode. Its bytes stayed
unchanged. The failed validator and then the complete regression pipeline had
PASS results. This was not a candidate repair.

The first GUI preflight found three ignored CPython bytecode files in the
reviewed bridge tree. Independent classification identified an environment or
profile defect. Recovery moved only those files without overwrite into retained
task evidence. It changed no product or test. The exact-profile GUI preflight
then had a PASS result. The baseline and candidate GUI runs were not repeated.

## Independent technical review

A different agent completed a read-only technical review after the product
proof was complete. The reviewer examined the raw diff, complete source, tests,
machine contract, failed evidence, recovery records, PASS results and frozen
methods. The verdict is PASS, with no `BLOCKER`, `REQUIRED_BEFORE_EXIT`,
`BACKLOG` or `OPTIONAL` findings. `MISSING`, `EXTRA` and `CANNOT_VERIFY` are
also empty for this bounded outcome.

The review confirms the candidate identities, 132 direct operations and the
selected standalone and qualified matrices. It also confirms the complete
regression pipeline, D-GOV-019 host, GUI comparison with zero differences,
repair accounting at 2/2, consumed harness exception and all stated exclusions.
The reviewer wrote no candidate source or test. The reviewer did not edit
files, run a different proof or review canonical prose. This verdict accepts no Phase 7 exit,
performance result, output state or wider migration claim.

## Evidence identities

The active worktree is `TrackTemplateMacro-worktrees/phase7-platform-transitions`
on branch `codex/phase7-platform-transitions`.

| Repository path | SHA-256 |
| --- | --- |
| `tracktemplate/domain/alignment.py` | `50da53b4cdcd6784f0701af5042910174604ee19ec28ccd04a9ac38255a52595` |
| `tracktemplate/api.py` | `202acaac6203f001a0d7b0bae49449774b1585d9b10678e90a81f97fde74c8aa` |
| `tracktemplate/compatibility/transition_workflow.py` | `c15aca1b0ea173683a1f9729f12d6f33e041245fb85708c4c8f65fee1f13cb8c` |
| `reference/contracts/phase7-platform-transitions.json` | `c0faaaed183a31e05865559c4fdf8edce30c58f007adf83c62f5cc84c7b51045` |
| `tests/validate_phase7_platform_transitions.py` | `09c00c721ca212a759d2fa7393a54eb6fb902b1e83c69db7f2887f564ee7eba9` |
| `tests/freecad_validate_phase7_platform_transitions.py` | `5a1cdf10a0034d1eb71721f794c3d85d7ff97d0589741519c0357a0adddd28c6` |

The next records are under the worktree's ignored
`tmp/phase7-platform-transitions/` directory if the path does not give a
different location. They keep the initial FAIL and later PASS evidence in
different records.

| Record | SHA-256 |
| --- | --- |
| `proof-baseline-completion.json` | `6d1e44a0b08bbf7a16365675a5c7aaae9c0b452057b5f27b25263c38da674498` |
| `proof-baseline-failure-classification.json` | `469d753e90f83b98bdf57a281e5810ddabe368a54a9f8f79eda8fcb121b574bd` |
| `proof-direct-B0-repair-02-classification.json` | `b69763ee0530d1bba2e5c004524fb9272ea915717c1f7bc59f724922ec0914f4` |
| `proof-direct-B0-repair-02-failure-classification.json` | `aba46113f551bd3eef8da75bba71a1bbd912be5c853137879755806fb19d8709` |
| `current-main-alignment-after-01.json` | `0a27a1bab89934084a802c45c1eba3fadb782f700e42dee90a33a27635d768d4` |
| `proof-candidate-characterisation.log` | `a0ab5f7f36a3d02791bf5acb609089a71907dadf2e725062db7a952a90028697` |
| `proof-candidate-characterisation-exception-01.log` | `a8cc2949fa377e56e8740eff7c0eed460cb40bdcb0bf8e32fe2b09f7069f6cc4` |
| `proof-candidate-standalone-completion.json` | `a59672e7f39dbce9e4743a90ff0e2c1d9f9ddd19c9818fd979d2ed203203b64f` |
| `proof-native-characterisation.json` | `843b64dd94041f6b706aece5ef87749f19e16a3b9edaea0a3ad29b0776904cfa` |
| `targeted-standalone-validation-01/manifest.json` | `01dc3f36ce94dd3e67a44edf2837d3b0ff090c75590a4e4db768b633eff2f9f7` |
| `targeted-qualified-validation-01/completion.json` | `2bf0570a570c6d2b2d574c4287a1d7d235da415b66e0cb785cf61fff58e5e53d` |
| `run-bundles/dgov019-refreeze-01/frozen-manifest.json` | `a3657e3f983473b293320afe4afa2715794afb56aa31b2a780645779fb6f1386` |
| `run-bundles/dgov019-refreeze-01/tmp/phase7-platform-transitions/proof-direct-completion.json` | `b131cbe2e2d57f17acc6eaabf5cd683aa3c8d433ff3f5fa2c8a70562b3c64edc` |
| `ste100-cache-mode-recovery-01.json` | `c22f76bc325b08554473526ae5740ffaacb9114d01f1cce686807eed1db0b9ab` |
| `gui-preflight-environment-recovery-01.json` | `eb6bc8b36e9dc00b79d3217513cdf93f9cd7cc775f609652d313e6adcb7256f8` |
| `gui-full-comparison.json` | `2fc4b0aec281b0c66b2c7986420addd93f4c8d16dfafb3404f20d02f3838f948` |
| `gui-completion.json` | `fbe3c937663bf79068f8d87ee305eeed6f0f0ac0f92ef756d9617c2941ec088f` |
| `independent-technical-quality-review.md` | `36d58772c57a7d4a0616c6a687ca53521c4e6335f8588350057dadb54ec93ea6` |

## Acceptance boundary

This calculation migration supplies bounded evidence for the API without host
dependencies in Exit 3. It supplies bounded evidence of equal results in Exit
2 and B16 workflow evidence in Exit 1. It accepts no Phase 7 exit. Phase 7 stays
Open at 0/4, with all four exits Pending.

D-P6-008 stays in full as a deferred, unmet obligation before Phase 10 beta
acceptance. All earlier performance limitations and unknown causes stay
visible. The direct and GUI measurements in this record give no performance
acceptance and select no optimisation.

All conditions to compare results and remove legacy paths stay in full. This
task changes no phase criterion, risk, persistence contract, output contract or
release state. Output stays private-development. Project status stays
`unknown`. The new draft must have separate owner authority for integration.
