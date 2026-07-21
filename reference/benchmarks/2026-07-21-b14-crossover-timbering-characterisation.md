# B14 crossover automatic-timbering characterisation

Recorded: 2026-07-21

Phase: 1 — product, dependency, correctness and performance inventory

Status: fixed B14 path characterised; successor fixes and wider matrix not started

## Outcome

The controlled curved-host `XO-001` automatic-timbering path now has a
machine-readable semantic and lifecycle oracle. On the fixed placement it
produces 86 effective timber records, including 16 shared-envelope records,
with no unresolved position, production conflict or production-critical
conflict. An unchanged second application reuses the result and object; one
Undo and Redo recover the exact pre- and post-application states; and the
accepted state survives save/close/reopen and remains reusable.

The same investigation found three bounded B14 defects:

1. the first returned nested analysis is richer than the result persisted for
   unchanged reuse and reopen;
2. changing only B4 display visibility reruns the complete pipeline and changes
   the resolution signature; and
3. an injected failure at the first B4 tagging call leaves one untagged
   `Part::Feature` after `abortTransaction()`.

These defects are observations, not successor behaviour. Neither macro was
changed. The exact contract is
[`phase1-crossover-timbering.json`](../contracts/phase1-crossover-timbering.json).

## Reproducible state

| Item | Value |
| --- | --- |
| B14 source | `AdvancedTurnout.FCMacro`, `10.2A8A7B14` |
| B14 SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| B15 SHA-256 | `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848` |
| FreeCAD | 1.1.1 Flatpak, revision 44874 |
| Base fixture | ignored `b14-default-base-regenerated.FCStd` |
| Fixture SHA-256 | `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c` |
| Fixture semantic SHA-256 | `a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e` |
| Hosts | persisted `SET-001` Main Track and Track 2 identities |
| Placement | Host A chainage `746.298 mm`; crossover identity `XO-001` |

The headless oracle copies the nine-object fixture to a temporary directory,
creates the crossover only in that copy, closes it and verifies the source
fixture remains byte-identical. Disposable investigation against both existing
base-fixture archives produced the same timber signatures, records, shape and
lifecycle findings.

## Fixed semantic result

| Result | Value |
| --- | ---: |
| Effective timbers | 86 |
| Inherited-side A | 36 |
| Inherited-side B | 34 |
| Shared-envelope records | 16 |
| Nominal connector sleepers | 0 |
| Interlaced pairs | 0 |
| Moved timbers | 0 |
| Unresolved positions | 0 |
| Production conflicts | 0 |
| Production-critical conflicts | 0 |

The 16 envelope records comprise four inherited A extensions towards Host B,
six inherited B extensions towards Host A and six shared
`CONNECTOR + HOST-A + HOST-B` timbers. The ordered record-identity SHA-256 is
`8513166935365fd6b821dbcb181c3b79a221711cb43c7f4bf7c52d675bd87d95`.
The rounded stable-record SHA-256, which also covers centres, angles, sizes,
polygons, movements and protected features, is
`aebb9e04bbf4816a130fc196c7c504cd9f45d787b57e5a85f41c855abdf1b326`.

The default resolution signature is
`9ae269b05624df83a3b789986b10c301f7423f3ff92f2adf9b11c65d9927f51d`.
Changing the B3 maximum timber movement from `1.5` to `2.0 mm` correctly
invalidates reuse and produces signature
`2e5be4d3ec0d4b4f8a8e2c609b3397c356e916397d4ddd1a35d5e062579d25bf`.
For this witness the records happen to remain identical because no timber
requires movement; that equality is not a general rule.

The legacy display is one 1,316-edge planar compound with no faces or solids.
Its exact rounded bounds are recorded in the contract. This is presentation
evidence only: the authoritative successor boundary is the resolved timber
record set, not a retained `Part` compound.

## Lifecycle evidence

| Boundary | Objects | Observation |
| --- | ---: | --- |
| Crossover geometry complete | 18 | B4 not applied |
| First automatic-timber apply | 20 | B4 object plus analysis-display group |
| Unchanged apply | 20 | cached result and same B4 object reused |
| Undo | 18 | exact pre-application semantic state |
| Redo | 20 | exact accepted semantic state |
| Save/close/reopen | 20 | exact accepted semantic state; reuse remains valid |
| Clear B4 | 20 | B4 removed; inherited-conflict display regenerated |

The earlier real-GUI cold series remains the performance and visible-workflow
owner. Its three-run automatic-timbering wall times were `1628.7`, `1589.6`
and `1592.3 ms`, with a `1592.3 ms` median. This tranche does not replace that
controlled timing series or introduce a new performance budget.

## Bounded defects

### Persisted analysis drift

After committing metadata, B14 enriches only the in-memory returned result's
`resolved_analysis` with its geometry signature, effective-arrangement basis,
production note and current integration reason. The previously persisted B4
result still contains the solver's earlier nested analysis. Therefore an
unchanged reuse or reopened reuse returns a different diagnostic payload even
though the timber records and resolution signature match.

The successor must persist and return one canonical result at every boundary.

### Display-only over-invalidation

`show_b4_geometry` is normalised inside `_b4_resolution_signature()`. Toggling
it false therefore returns `cache_reused=False`, rebuilds unchanged records and
shape, and changes the signature to
`1a60d1e4add7fd3d1881598ecd4cdd4e8cb3910eec6ca4157491bb322b33ba8f`.
Toggling it true repeats the rebuild and restores the default signature.

The successor must keep presentation controls outside calculation signatures
and update only derived visibility, with no solver, geometry, calculation-
metadata or history work.

### Incomplete abort cleanup

After clearing B4, the oracle replaces `tag_generated_object()` only for the
B4 role and raises `injected B4 tag failure`. Configuration and every existing
object remain unchanged, but the document grows from 20 to 21 objects. The
retained object is `CrossoverB4Timbering_XO_001`, an untagged `Part::Feature`
with no crossover identity and the already assigned 1,316-edge shape.

The standalone-turnout oracle proves exact abort recovery elsewhere in B14, so
this is a B4 mutation-boundary defect rather than an accepted FreeCAD-wide
limitation. The successor must restore the complete document and history after
failure, including removal of untagged partial objects.

## Scope and successor gate

This closes the focused `XO-001` automatic-timbering characterisation gap. It
does not project-clear the current timber data, fix B14/B15, cover standalone
turnout or plain-line timber decisions, complete every input-class invalidation
case, or qualify wider hosts, arrangements, gauges and chainages. Real-GUI
visibility/selection, host integration, chair interaction and production
export also remain under their existing owners.

Before migration, the successor must pass the seven rules and remaining matrix
in the machine-readable contract. In particular, it must preserve the
characterised fixed record semantics unless an engineering-rule change is
separately reviewed, while rejecting all three legacy defects.

## Validation

Fast contract and source-boundary check:

```bash
.venv/bin/python tests/validate_phase1_crossover_timbering.py
```

Disposable real-FreeCAD lifecycle oracle:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase1_crossover_timbering.py
```

The latter must print `Phase 1 crossover timbering FreeCAD oracle passed`.
The visible cold timing owner remains
[`2026-07-19-b14-crossover-xo-001-automated-cold-series.md`](2026-07-19-b14-crossover-xo-001-automated-cold-series.md).
