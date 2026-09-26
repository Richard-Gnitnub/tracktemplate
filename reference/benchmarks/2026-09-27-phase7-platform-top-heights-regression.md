# Phase 7 evidence for platform height values

Status: **Level 2 evidence for one exact calculation and its B16 caller.**

The [API instructions](../contracts/phase7-platform-top-heights.md) own the
calculation and route. The [current evidence](../current/PHASE_EVIDENCE.md)
owns the task result. The [Project Plan](../PROJECT_PLAN.md#phase-7-exit-conditions)
owns phase and exit status. This record gives no exit or performance acceptance.

## Current owner view

| Field | Result |
| --- | --- |
| **Current state** | Protected `main` includes PR #86 at `7122dc2f6f8a4123adb039a8d22b0ac95728929c`. The exact product candidate is `8870ebd24e1479ffdc260e77f418fced72447b4f`. It has no merge. Phase 7 stays Open at 0/4. |
| **What changed** | The B14/B15 `calculate_platform_top_heights` calculation uses Core through the selected B16 caller. The route has schema `16`, 25 selected functions and 40 caller identities. |
| **What now works** | The direct and qualified comparisons have PASS results for 24 cases and five read paths. The related qualified proofs, full transition profile, paired FreeCAD human-interface comparison and independent source-and-test review have PASS results. |
| **Limitations/findings** | The two usual repairs are completed (2/2), and the first FAIL results stay as evidence. The GUI procedure covers only the named outside-one-track `PLATFORM_CONSTANT` operation. Its resource values are descriptive and give no D-P6-008 credit. |
| **Owner decision** | The owner authorised this bounded Level 2 result through publication. The candidate has no integration or Phase 7 exit decision. |
| **Next action** | Complete the one Documentation Review lifecycle and final validation. If the exact candidate is green, publish one draft for the owner's integration decision. |

## Scope and source

The comparison baseline is protected `main` at
`7122dc2f6f8a4123adb039a8d22b0ac95728929c`, with tree
`7bc9dd28f17532e4e9f1e42adea92a9e0c1d45e0`. The product candidate is
`8870ebd24e1479ffdc260e77f418fced72447b4f`, with tree
`80ed1c817bfeeed2cff758c9c4c04d035b320bd8`. D-GOV-004 and the project
owner's instruction on 2026-09-27 authorise this bounded Level 2 result.
D-P7-001 keeps Phase 7 Open at 0/4.

The B14 and B15 definitions of `calculate_platform_top_heights` are equal.
Each definition has 1,401 bytes and SHA-256
`1eda69de0e8abb22c14c9acb4d90b8de09476b0db506f13f07e866247a7df90f`.
B14 and B15 do not change. The selected B16 caller is
`calculate_platform_boundaries`.

The route uses `tracktemplate.domain.alignment` through `tracktemplate.api`.
It has schema `16`, 25 selected functions and 40 caller identities. It binds
the selected calculation directly and has no adapter for it.

| Product or test file | SHA-256 |
| --- | --- |
| `tracktemplate/domain/alignment.py` | `0da53a6ce2113e4fc3b256c5d5e5c20d0e0595154a0e1993b81d4a70dcc41958` |
| `tracktemplate/api.py` | `4618b724b6190e68613078366c95567fa0576f94e35d4b7041a3e944e341d029` |
| `tracktemplate/compatibility/transition_workflow.py` | `afbc13c76c24e648ee4316fcb73847f0122696789fab8fc16923c395a82a53f2` |
| `tests/validate_phase7_platform_top_heights.py` | `a911017565573529340af51c799f5a3b6f5ffa93f7df6fb0b97dc3651a949416` |
| `tests/freecad_validate_phase7_platform_top_heights.py` | `f95f705d938cee7c12cecc89d1008e659ccfa7a6f28f955e47349fb2c6b59c72` |

## Standalone comparison and repair 1

The standalone comparison uses 24 cases. It compares B14, B15 and Core. It
also compares five paths that record the sequence in which the calculation
reads inputs and gives inherited errors. It validates unchanged inputs,
host-independent import, exact route binding, incomplete and mixed route
rejection and recovery after a setup error.

The first run stopped in the test snapshot before candidate execution. The
snapshot iterated an instrumented station list and caused its injected error.
The full first output is
`tmp/phase7-platform-top-heights/focused-standalone.log`, with SHA-256
`7595cf590ed7a6727e1f52e3789afd398e5145793b7cd0f9a2f26564450645cc`.
The failure class is `test-or-oracle-defect`. Its record is `tmp/phase7-platform-top-heights/repair-1-classification.txt`, with SHA-256
`0fac846b55f2381d4015a4fb4b23ec8b601987016639d82d341b882c678246d5`.

Repair 1 changed only the pre-call snapshot in the new test. The calculation
kept the instrumented iteration. The same proof then had a PASS result. Its
full output has SHA-256
`607a65b28c2a331de2a718ee6616071255eb8eaceba499bd61d357f45ac22809`.
The necessary sentinel is `Phase 7 platform top heights validation passed`.
The original FAIL result stays as evidence.

The complete standalone profile also has a PASS result. Its command-output
SHA-256 is
`841bbee53434c66d2dadd58466465a01c720a39c713b38fd36916ba5687ad76a`.

## Qualified comparison and repair 2

The FreeCAD preflight has a PASS result for the exact D-GOV-019 profile. Its
command-output SHA-256 is
`6ea87e120344d8ed56ebc905321733bd584742795ed164bd5a4da1745f38c15d`.

The first qualified proof stopped before the selected calculation. Its
outside-platform fixture did not supply `outside_side`, which the inherited
caller reads first. The first output is
`tmp/phase7-platform-top-heights/candidate-qualified.log`, with SHA-256
`352a3b0a6a522fedaff3382586289b3f2be93356f5a226f17d77beb6ab54c0ee`.
The failure class is `fixture-or-harness-defect`. Its record is `tmp/phase7-platform-top-heights/repair-2-classification.txt`, with SHA-256
`9e5ad494e33259682f0098558b353d7b23f77086ec7866feee0d4985b6bf3bfd`.

Repair 2 supplied the inherited `PLATFORM_LEFT` value to that fixture only.
It changed no product source or accepted result. The same qualified proof then
had a PASS result. The result JSON has SHA-256
`15e360e30eecb97167dc7d4f592870773faa271923fe0a052bdf33441101e807`.
Its full command output has SHA-256
`de8eb3b6aad3355e9cd6fc5aaad75283d9342b834e32a3e4e5c971c30489b92d`.
The necessary sentinel is
`Phase 7 platform top heights FreeCAD validation passed`.

The two usual repairs are completed (2/2). No more usual repairs are
permitted. Both first FAIL results and their classifications stay as evidence.

## Related qualified proofs and complete validation

All 15 related Phase 7 qualified proofs have PASS results on the exact
D-GOV-019 profile. Their retained manifest has SHA-256
`386273c4488d1f1e156f447dbd926e5a4854fda88e844f33304984d103088e1c`.
The Phase 3 route proof also has a PASS result. Its command-output SHA-256 is
`4b4f1c2600eb1fef3c6e30652418930022eab408a5a1952a0bdc02f2e2564de9`.

The complete `transition` validation profile has a PASS result for all seven
steps. Its command-output SHA-256 is
`5e28852395303239bab10d4b68e075e6100a70a9ef0d04e6dff8ceea96cbea4d`.
The retained pipeline output identifies each complete step and its log.

## Tests with the FreeCAD human interface

One isolated FreeCAD process used protected `main`. A second isolated process
used the exact product candidate. Both used the D-GOV-019 profile
`linux-x86_64-flatpak-freecad-1.1.3-py3.13.15-qt6.11.2` and the same source
fixture. The fixture SHA-256 is
`0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`.

The procedure uses `PLATFORM_CONSTANT` outside one track, `PLATFORM_SOLID`,
both exact `PLATFORM_END_TAPERED` values, 50 mm end lengths and a 15 mm
platform height. It compares the first calculation and three subsequent
calculations with unchanged inputs. It also compares Create/Edit through B16
Generate/Replace, Undo/Redo, two inherited rejections, Save/reopen and cleanup.

Both processes have zero exit status and the necessary sentinel. The exact
product result is equal. Its SHA-256 for both routes is
`abc407ecedc90b3d81c0ae6384eace8251cfd13d8a1d3b57cc5cf8781ed257e2`.
The station and platform-height value record has SHA-256
`016d6234d22773bf938d53886a4ab8b50a6368aa030390fc14407fc3948a6909`
for both routes.

| Evidence | Protected-main SHA-256 | Exact-candidate SHA-256 |
| --- | --- | --- |
| Source manifest | `272b8be9a9cad4d030b9705b338f3f92fb32cd01c94d30fd6e8b2c557f30f06a` | `03dcc87ae9dd86ab3e79485931242742668525a3f95ad92cfcca2f122e016763` |
| Test receipt | `8ed130a1ad7d56bf61344069b6e6186386f8bab09974d2f06dcea4668cbc91e8` | `24195162b33aadf44df7dc25802da322c1b1fc6664b859628c0417fa330e2d5a` |
| Full record | `4a646deab94f64dee815bb7a15aa6966b0a8a8a4a92899fc479095dc58ddf3f1` | `240e12990a47fd6aedd4a02a8a83782d35c99c1f28699c69c4204c99ec275c6a` |

The fixed procedure has SHA-256
`9b410c894ecbadb97e74ba596b2b9bac196038ab69311d940e3468e44be0b4f0`.
The final comparison has a PASS result and SHA-256
`451fb27ae72158d4093981b4ce49e03a4d23c2814df1ad5178a30476388d4922`.
It excludes only the save path and descriptive time and memory values from
exact equality. It does not exclude stations, height values, platform inputs,
object identities, shapes, dimensions, persistence or history.

One process for each route gives no improvement evidence for D-P6-008. The
resource values are descriptive only. The procedure changes no measurement
rule.

## Independent source-and-test review

One independent read-only Quality Review inspected exact candidate
`8870ebd24e1479ffdc260e77f418fced72447b4f`. Its decision is PASS, with no
source or test finding. The review confirms the bounded extraction, inherited
calculation and read order, direct caller binding, route closure and recovery.
It confirms that repair accounting is 2/2 exhausted.

The review did not include governance prose. At review time it also did not
include the later paired GUI evidence. It gives no Phase 7 exit, integration,
performance, output, release or legacy-retirement decision. The retained
review receipt is
`tmp/phase7-platform-top-heights/independent-source-test-review.json`, with
SHA-256
`08593113c74bac85ccb7d1bfd2a0121da93d654345b78ab2382623d8465b78e0`.

## Limits

This exact candidate does not compare all platform arrangements, coverage
values, shapes, dimensions, positions, stored state or export bytes. It does
not establish performance improvement. It removes none of the paths that
D-P7-001 keeps.

Phase 7 stays Open at 0/4 with all exits Pending. Output stays at
private-development status and project status stays `unknown`. D-P6-008
applies in full. D-P7-001 still gives this instruction: “Preserve all
comparison and legacy-retirement conditions.”
