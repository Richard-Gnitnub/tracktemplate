# B16 Transition Routed-Workflow Parity

Status: **controlled correctness series passed on 2026-07-22. This is real-GUI
workflow evidence, not the contracted Phase 3 performance profile.**

## Scope

The series exercised the exact B15 operator workflow under the B16
transition-pilot `legacy` and `modular` calculation routes. It reused the
established Phase 1 lifecycle drivers rather than introducing reduced Phase 3
scenarios:

- plain-line handed replacement, complete Undo/Redo, explicit change-back,
  save/reopen, zero-angle rejection and an injected failure after generated
  output removal; and
- controlled curve-entrance/curve-exit straight creation, complete Undo/Redo,
  length editing with unchanged curve geometry, and save/reopen.

Each workflow/route pair ran in a separate isolated FreeCAD GUI process against
its own copy of the fixed nine-object fixture. The source fixture remained
byte-identical.

## Controlled source and environment

| Item | Evidence |
| --- | --- |
| Starting Git checkpoint | `3ab42b138e2f3a84cf413c2b434fb74f2565a597` |
| B14 immutable source | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| B15 routed workflow source | `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848` |
| B16 launcher | `8852d27002b444a37cdb5df56b9f31f9a9313c70276b89d18ea86198b06037fe` |
| Frozen transition contract | `1f4c50f6edb327c5bfbd947c4953ee51cf606c9a676bec1c8ee7c224d5f5b139` |
| Source fixture | `b14-default-base-regenerated.FCStd`, SHA-256 `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` |
| Qualified runtime | `linux-x86_64-flatpak-freecad-1.1.1` |
| Process/cache state | Fresh isolated GUI process per route/workflow; persistent isolated preferences; OS file cache uncontrolled |

The route loader parsed the B16 composition root without its final automatic
launch, used its `_load_foundation` and `_load_transition_pilot` boundaries,
required the exact qualified runtime, and then exposed only the routed B15
module to the existing GUI driver. It checked that all three selected function
bindings retained object identity throughout the workflow and revalidated the
complete route afterwards.

The retained harness source used for this final series had these fingerprints:

| File | SHA-256 |
| --- | --- |
| `phase3_transition_workflow_recipe.py` | `03dbca3030e89c5702c2787c3c7e7c4dc176390032b4df516831110906dc8cc2` |
| `load_phase3_transition_workflow.py` | `582dd5bfa833628efbf24179c71c470d7fa118a419e738d1d0af00140f6c367f` |
| `finish_phase3_transition_workflow.py` | `877ccec41ccceb38d7fa006c991e67830801962ef54b3f85a189fa88c0aca163` |
| `run_phase3_transition_workflow.py` | `1da3a5ba5755c9d14cbc293495890f5cfbef18bcb3779908b1f78c1080def90e` |
| `run_phase3_transition_workflow_series.py` | `5de230e9786a162e672c5afbdb7f8e9f616556bffb280af89b795edaaebb3a3c` |
| Plain-line lifecycle driver | `62ae62702155200e01576463145bb0de018bfcf7a0aae0c42b0782aabfde2c58` |
| Connected-straight lifecycle driver | `b949204b64f00f7258368431973d202d24b0b7121cc82e5cf738c3784d926d9c` |

## Comparison boundary

The fixed fixture was created by B14, while the routed workflow identifies as
B15. The historical drivers therefore retain their strict B14 defaults, but
the Phase 3 loader explicitly declares B15 as the reader/generator and disables
only the frozen B14 whole-snapshot digest checks. All field-level, shape,
identity, ordering, dialog, history, persistence and failure assertions still
run.

For the expected B14-to-B15 label update, the handed mirror permits only
`GeneratorVersion` identity changes and `ProductionRecordIndexJSON` as an
additional changed persisted field. Explicit change-back normalises only
`GeneratorVersion` and `macro_version` string values beginning with the exact
B14 or B15 prefixes, then recomputes the derived semantic hash. Its normalised
comparison had zero differences. The complete raw legacy/modular comparison
still retains both unnormalised workflow snapshots.

Route equivalence removes only these five development-host observations:
`measurement`, `memory_bytes`, `path`, `source_document`, and `wall_ms`.
Everything else is compared with exact Python container type, scalar value and
list order through `tools.semantic_compare`.

## Result

| Workflow | Legacy contract SHA-256 | Modular contract SHA-256 | Differences | Final document semantic SHA-256 | Harness elapsed observation |
| --- | --- | --- | ---: | --- | --- |
| Plain-line edit lifecycle | `85976aa1a154ab5afce8d51a89f7674e655b7b5d91f61795580e67f3980fc7f0` | `85976aa1a154ab5afce8d51a89f7674e655b7b5d91f61795580e67f3980fc7f0` | 0 | `13f707976ab749b92b768b766db58ec080e6aa7e81c9607a83849a24b644a370` | legacy `35.512 s`; modular `34.793 s` |
| Connected-straight lifecycle | `2eec8269c52b8491ac546650cad1c0c6975bc620ab3a4a845f4778d8a1379517` | `2eec8269c52b8491ac546650cad1c0c6975bc620ab3a4a845f4778d8a1379517` | 0 | `8ef264901e67c8bcd8dc3305352c2efbd365fe5b04f31f2a30042cf0aa79659c` | legacy `19.189 s`; modular `19.418 s` |

Both routes retained their selected route, the routed function bindings,
isolated preferences and source-fixture hash. Every process closed its copied
document and the isolated FreeCAD instance stopped.

The plain-line failure paths both retained right-hand semantic SHA-256
`13f707976ab749b92b768b766db58ec080e6aa7e81c9607a83849a24b644a370`:
the zero-angle input was rejected before a transaction, and the injected first
tagging failure after old-output removal aborted without document corruption.

The original strict B14 commands were rerun after the driver seam was added.
They retained their accepted final hashes:

- plain-line edit lifecycle:
  `4c8bf8dfc10bda8e91e7d479b630bbce2c12df576700f23e6b5bdbc276cc69d4`;
- connected-straight lifecycle:
  `430d5f134e20789ee22c7f5549b64611a067646f1d24e038d4fbbc473d6b7666`.

## Raw-artifact provenance

Raw artifacts remain ignored under
`benchmark-output/freecad-bridge/phase3-transition-workflow-runs/20260722T170252269939Z-series/`.
They contain local paths and are not committed.

| Raw artifact | SHA-256 |
| --- | --- |
| `comparison.json` | `fcff030d106b748eaa2887cd80810ed9b0b0393701e95d6827869e54df776532` |
| Connected-straight legacy `run.json` | `54ffd00f0fd3729ca67d33da620e1b3d2b743ee7f4f618b7c06c0283afa5d68a` |
| Connected-straight modular `run.json` | `59a1c15921cd17a5b2ed331a3ac1dde9d1b4bac7750eb386f6ef9c483f84265a` |
| Plain-line legacy `run.json` | `5076a24c976d2390a0a4544cd64157f80eb3fd352acc1df60ba783f090d71c1f` |
| Plain-line modular `run.json` | `fbd7107e2a41a350d8d65808e69fdb4b2bfb162e47f0ce9d1db7ce2b638e2ad8` |

The route-specific FCStd byte hashes differ because FreeCAD serialisation is
not the equivalence oracle. The complete normalised workflow contracts and
their embedded semantic snapshots are the accepted comparison boundary.

## Limitations and decision

This series establishes routed full-workflow, real-GUI, persistence, history
and failure-recovery parity for the selected transition calculation slice. It
does not retire the legacy route or close Phase 3.

The elapsed values above are single correctness runs enclosing dialog driving,
history operations, deep snapshot validation, save/reopen and RPC polling.
They are not equivalent warm/cold samples, medians, budgets or evidence of an
optimisation. Contracted calculation and comparable workflow performance
profiles remain the active Phase 3 gate. Export, turnout/crossover, renderer,
canonical persistence and wider migration behaviour remain owned by their
named later gates.
