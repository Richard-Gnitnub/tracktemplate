# B14 crossover preview/commit feasibility characterisation

Recorded: 2026-07-21

Phase: 1 — product, dependency, correctness and performance inventory

Status: mismatch characterised; successor alignment not implemented

## Outcome

The controlled B14 crossover preview is not an authoritative feasibility
decision. At Host A chainage `500.000 mm` it accepts a connector-feasible
placement whose complete mapped crossover minimum radius is only
`540.848374541 mm`, below the requested `600.000 mm`. The existing commit path
calculates that complete minimum only after constructing both turnout modules
and the connector's exact FreeCAD shapes.

The documented cold-series placement at Host A chainage `746.298 mm` remains
valid. Its complete minimum is `676.178669189 mm`, limited by the connector.

This tranche changes no product source. It freezes the evidence and the
successor acceptance boundary in
[`phase1-crossover-feasibility.json`](../contracts/phase1-crossover-feasibility.json).

## Reproducible state

| Item | Value |
| --- | --- |
| B14 source | `AdvancedTurnout.FCMacro`, `10.2A8A7B14` |
| B14 SHA-256 | `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088` |
| B15 SHA-256 | `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848` |
| FreeCAD | 1.1.1 Flatpak, revision 44874 |
| Base fixture | ignored `b14-default-base.FCStd`, reproduced by `tools/freecad_bridge/build-b14-base` |
| Fixture SHA-256 | `59d06cf57d65d9560dd53915fce2bef19130c534d214f92c9699066060dc4357` |
| Fixture semantic SHA-256 | `a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e` |
| Fixture objects | 9 before and after |
| Hosts | `SET-001` Main Track and `SET-001` Track 2, resolved by persisted identity |
| Request | Facing crossover; Automatic handing; 16.5 mm gauge; 1.0 mm flangeway; 600.0 mm minimum radius |

The fixture was opened in memory, queried analytically, closed without saving
and verified byte-identical afterwards. No crossover objects, Part shapes,
transactions or exports were created by the oracle.

## Analytical witnesses

The complete rule is:

`minimum(mapped turnout A road, mapped turnout B road, connector) >= requested radius`

| Host A chainage | Current preview | Host B chainage | Turnout A | Turnout B | Connector | Complete minimum | Complete rule |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 500.000 mm | accepts | 1341.223827 mm | 606.584743 mm | 540.848375 mm | 621.083336 mm | 540.848375 mm | reject |
| 746.298 mm | accepts | 1590.068084 mm | 696.907920 mm | 887.199391 mm | 676.178669 mm | 676.178669 mm | accept |

All recorded comparisons use an absolute `0.000001 mm` tolerance. The first
row is the bounded defect witness; the second is the existing controlled
recipe and positive witness.

## Source-path finding

`CrossoverManagerPanel.preview_geometry()` calls
`solve_rea_c10_crossover_geometry()` and caches its result. That solver
validates the requested connector solution, occupied host intervals and
conflicts, but it does not call `turnout_mapping_metrics()` for either mapped
turnout road and does not apply `_crossover_minimum_radius_value()`.

Creation, editing and turnout extension pass the cached preview as
`pre_solved`. `_build_rea_c10_crossover_geometry()` then:

1. builds both curve-inheriting C10 turnout modules;
2. builds and fuses the connector and exact plan/solid geometry;
3. reads each built turnout configuration's sampled mapped-road radius;
4. takes the minimum of both turnout roads and the connector; and
5. rejects the result if it is below the request.

The document transaction remains recoverable, but the operator-visible
preview can promise a placement that later fails and the failure consumes
avoidable Part-construction time. `turnout_mapping_metrics()` already provides
the required mapped-road radius from analytical host station data, so the
successor does not need document objects or exact Part geometry to make the
complete decision.

## Successor gate

The successor must return one signature-bound shared preflight result covering
host identities and geometry signatures, every request value, resolved placement,
both mapped turnout-road radii, connector radius, complete minimum and the
decision diagnostic. Preview and create/edit/extend must use that same result.

The `500.000 mm` witness must be rejected before Part construction, a document
transaction, object or history creation, recompute, or metadata persistence.
The `746.298 mm` witness must be accepted, and later exact construction must
agree with its analytical component radii within the declared tolerance.
Changing any host or request signature input must invalidate the result.

This characterisation closes only the Phase 1 evidence gap. It does not fix
B14/B15, approve a migration, or replace the future real-GUI zero-mutation and
valid-commit regression.

## Validation

Fast source/contract check:

```bash
.venv/bin/python tests/validate_phase1_crossover_feasibility.py
```

Read-only FreeCAD analytical oracle after reproducing the ignored fixture:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase1_crossover_feasibility.py
```

The earlier cold evidence records both a real lower-bound preview/commit
mismatch and the valid transactional commit used by the controlled series:
[`2026-07-19-b14-crossover-xo-001-automated-cold-01.md`](2026-07-19-b14-crossover-xo-001-automated-cold-01.md)
and
[`2026-07-19-b14-crossover-xo-001-automated-cold-series.md`](2026-07-19-b14-crossover-xo-001-automated-cold-series.md).
