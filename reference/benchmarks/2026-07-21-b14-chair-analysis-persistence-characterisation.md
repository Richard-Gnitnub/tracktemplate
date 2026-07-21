# B14 chair-analysis persistence and reuse characterisation

Recorded: 2026-07-21

Phase: 1 — product, dependency, correctness and performance inventory

Status: fixed post-B4 `XO-001` path characterised; successor fixes and wider
matrix not started

## Outcome

The logical chair-analysis stage now has a reproducible, copied-document
oracle independent of the real manager panel. For the fixed curved-host
`XO-001`, cold calculation, immediate unchanged reuse and save/close/reopen all
preserve the accepted 355 positions, 269 findings, geometry signature and
semantic digest. The two diagnostic display identities and their 710-edge
marker compound also remain stable.

The investigation confirms four related B14/B15 defects rather than accepting
them as future behaviour:

1. unchanged reuse still rebuilds every rail and timber record before checking
   the cache, then rewrites a roughly 1.5 MB result inside a new transaction;
2. persisted timings are written too early and omit metadata, display,
   recompute, commit and total work;
3. each effective-status query independently repeats record extraction and
   signature calculation; and
4. the active panel refreshes itself inside `_refresh_parent()` and again after
   the command, in addition to its parent callback.

Neither macro was changed. The exact machine-readable boundary is
[`phase1-chair-analysis-persistence.json`](../contracts/phase1-chair-analysis-persistence.json).

## Reproducible state

| Item | Value |
| --- | --- |
| B14 source | `AdvancedTurnout.FCMacro`, `10.2A8A7B14` |
| B14 SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| B15 source | accepted behavioural reference, `10.2A8A7B15` |
| B15 SHA-256 | `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848` |
| FreeCAD | 1.1.1 Flatpak, revision 44874 |
| Base fixture | ignored `b14-default-base-regenerated.FCStd` |
| Fixture SHA-256 | `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` |
| Fixture semantic SHA-256 | `a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e` |
| Placement | Host A chainage `746.298 mm`; crossover `XO-001` |
| Prerequisite B4 signature | `9ae269b05624df83a3b789986b10c301f7423f3ff92f2adf9b11c65d9927f51d` |

The oracle copies the nine-object fixture to a temporary directory, creates
the crossover and its 86-record B4 arrangement only in that copy, then invokes
the captured B14 analysis boundary directly. It closes the document and
requires the ignored source fixture to remain byte-identical. B15 inherits the
same analysis implementation through its captured alias and adds workflow
instrumentation only; existing complete inherited-module parity remains the
broader source guard.

## Fixed logical result

| Result | Value |
| --- | ---: |
| Rails analysed | 30 |
| Effective timbers analysed | 86 |
| Logical chair positions | 355 |
| Mandatory positions | 170 |
| Confirmed ordinary/turnout assignments | 183 |
| Deferred special-chair assignments | 124 |
| Deliberately omitted/shared supports | 48 |
| Advisories | 269 |
| Production conflicts | 0 |
| Production-critical conflicts | 0 |

The geometry signature is
`9d7d978ecb0cbbf145e8e5288222efafc7cfa037d05a4f53a5b30c8e61665e3e`.
The canonical analysis-core SHA-256 is
`7e1a5e1a0e5d225377752db2962d42f664266ff72fa4b865ab025964b5902470`,
matching the accepted B14-to-B15 GUI evidence. The ordered stable-position
identity digest is
`4444903ad30ee1f971e93726deb17eb20b500a03d231c2395b3ccf8d85089d10`;
the complete findings digest is
`face3ec848d53c8cb049e78cd73731ffae5b596704af1be4e8aa0dde2aaefef5`.

These values are legacy behavioural oracles. They do not project-clear a chair
definition, dimension, family classification, code table or production
output. The first-S1, core rail/timber, other-S&C and output-manifest controls
remain authoritative for provenance.

## Persistence and history

| Boundary | Objects | Result/display state |
| --- | ---: | --- |
| B4 complete, before analysis | 20 | no cached result or chair display |
| Cold analysis | 22 | new result; group plus marker compound |
| Immediate unchanged reuse | 22 | logical result and both display identities reused |
| Undo of unchanged reuse | 22 | cold persisted payload restored |
| Redo of unchanged reuse | 22 | reuse persisted payload restored |
| Save/close/reopen | 22 | reuse payload, result and display preserved |
| Reopened unchanged reuse | 22 | calculation/display reported reused again |

The Undo/Redo witness matters: an unchanged cache hit is not a read-only
return. It opens and commits a document transaction whose observable change is
mostly fresh timing metadata. The settings object becomes touched, and a save
is required despite unchanged railway and presentation semantics.

The persisted cold timing payload contains only record extraction, signature
lookup, calculation/core and transaction-open values. The returned cold result
also contains metadata update, diagnostic display, recompute, commit and total
values. Reuse repeats the same defect with a shorter four-key persisted
payload. Save/reopen faithfully preserves that truncated payload; another
reuse rewrites it with different measurements.

The successor requirement is one canonical final payload, written only after
all work it claims to measure. An unchanged current result and presentation
must return before record extraction, serialisation, mutation, history or
recompute.

## Diagnostic timing observations — not budgets

Two disposable repetitions on the qualified profile produced these direct
function observations:

| Boundary | Observed range |
| --- | ---: |
| Cold direct analysis wall | `8.228–8.732 s` |
| Immediate direct reuse wall | `8.161–8.318 s` |
| Reopened direct reuse wall | `8.059–8.118 s` |
| Rail/timber record extraction | `7.226–7.859 s` |
| Cold logical calculation | `87.0–89.5 ms` |
| Reused logical calculation | `0.004–0.014 ms` |
| Metadata rewrite, where returned | `712.0–815.0 ms` |

The cache successfully avoids the roughly 90 ms logical calculation, but does
not avoid the dominant record extraction or result serialisation. These are
focused diagnostic repetitions, not a controlled performance series and not
human-use targets.

The accepted real B15 panel action remains the operator-visible owner: it took
`120.415 s` while reporting chair-analysis reuse. That interval and these
direct calls came from different controlled boundaries and must not be
arithmetically subtracted. Static inspection nevertheless identifies the
extra path: `run_analysis()` calls `_refresh_parent()`; that method calls the
parent callback and `self.refresh()`; `run_analysis()` then calls
`self.refresh()` again. Each refresh can trigger the independent effective-
status record/signature scans. The successor must compute one command result
and refresh the manager/panel once from a shared state snapshot.

## Representation boundary

The legacy diagnostic display is one `App::DocumentObjectGroup` and one
`Part::Feature`. The marker has 710 edges, no faces or solids, and the exact
rounded bounds recorded in the contract. It is derived presentation, not
authoritative railway state. Freezing its current shape makes migration
comparison possible; it does not endorse a retained OpenCASCADE compound for
routine editing. The accepted architecture still requires a lightweight
presentation adapter and defers exact chair solids to Validate/Export.

## Scope and next gate

This closes the fixed `XO-001` logical-analysis persistence/reuse
characterisation gap. It does not fix B14/B15, complete the calculation-input
invalidation matrix, cover standalone turnout or plain line, qualify the B15
bounded-support/layout/solid chain, select the lightweight renderer or clear
chair data provenance.

The next chair tranche should exercise every signature input class and the
presentation-only controls against the shared-state successor rules, then
extend entity coverage. The existing separate supported-solid late-reuse and
B15 2D-layout gates remain open.

## Validation

Fast contract and source-boundary check:

```bash
.venv/bin/python tests/validate_phase1_chair_analysis_persistence.py
```

Disposable real-FreeCAD lifecycle oracle:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase1_chair_analysis_persistence.py
```

The latter must print
`Phase 1 chair analysis persistence FreeCAD oracle passed`.
