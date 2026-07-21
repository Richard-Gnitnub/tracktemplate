# B14 chair-analysis invalidation characterisation

Recorded: 2026-07-21

Phase: 1 — product, dependency, correctness and performance inventory

Status: fixed `XO-001` input matrix characterised; successor fixes not started

## Outcome

The legacy logical chair-analysis cache is not safe for migration as written.
For the controlled post-B4 crossover, several output-affecting configuration,
rail and timber fields are absent from `_chair_geometry_signature`. An actual
application-cache witness changed both timber axes, reported a cache hit and
returned the old payload instead of the independently recalculated result.

This tranche changes no B14 or B15 product source. It freezes the defect and
defines the successor boundary before extraction or optimisation.

## Exact boundary

- B14: `10.2A8A7B14`, SHA-256
  `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088`
- B15: `10.2A8A7B15`, SHA-256
  `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848`
- Ignored regenerated fixture SHA-256:
  `0a655275f30aa75c6c5de61e99ca675a832870fe705bfa3b8b448ef38002ab8c`
- Fixture semantic SHA-256:
  `a3486db6f02370e61432a480bfb6c9261bc9357cc2af5111f93135e3372d0a4e`
- Controlled crossover: `XO-001`, Host A chainage `746.298 mm`
- B4 resolution signature:
  `9ae269b05624df83a3b789986b10c301f7423f3ff92f2adf9b11c65d9927f51d`
- Extracted input: 30 rail records and 86 timber records
- Runtime: FreeCAD 1.1.1 headless

The fixture was copied to a temporary directory. Only the copy was changed and
the source fixture remained byte-identical.

## Method

The oracle extracted the fixed rail and timber records once, then exercised
the pure logical calculation. It classified all 23 normalised settings, all 11
emitted rail fields and all 40 emitted timber fields. Representative mutations
then established whether signature and logical output changed.

For application evidence, the oracle patched only the two record-extractor
boundaries with deterministic copies of those records. This allowed a real
`analyse_entity_chair_positions` cache hit/miss and presentation sequence
without changing persisted production source or the fixture.

The output digest removes timing, cache/display flags, the geometry signature
and the echoed settings. It therefore detects a change in logical output rather
than merely detecting the changed input echoed into the result.

Every emitted field is classified, but the representative mutation set is not
a claim that every possible field value or entity arrangement has been tested.

## Fixed baseline

| Signal | Value |
| --- | --- |
| Status | `Ordinary and turnout assignments validated` |
| Geometry signature | `9d7d978ecb0cbbf145e8e5288222efafc7cfa037d05a4f53a5b30c8e61665e3e` |
| Deterministic result SHA-256 | `d370cfecae4b455aaaaf9b14ce67a492e9390e0885bbbe8873068ffc5e62dd2d` |
| Logical output without settings SHA-256 | `e5d2565e1241da19d0ff3c4fe5560a51187aaa91ea6c112868909891ce3655f4` |
| Chair positions | 355 |
| Findings | 269 |

These are legacy comparison semantics. They are not project-cleared chair
definitions, dimensions or production data.

## Complete field classification

| Input record | Signature-included | Omitted but output-affecting | Omitted and unused by the current logical core |
| --- | ---: | ---: | ---: |
| Direct configuration after extraction | 2 identity alternatives | 1 (`template_set_id`) | 1 fixed-record witness (`handing`) |
| Rail record | 3 | 6 | 2 |
| Timber record | 6 | 11 | 23 |

The handing witness holds the already extracted records fixed. It means only
that handing is not read directly by the pure core. A normal handing edit can
still change the extracted rail/timber geometry and must invalidate through a
complete upstream or record signature.

The 23 setting keys divide into:

- five presentation-only controls excluded from the logical signature;
- one execution policy (`cache_enabled`) excluded from it;
- eleven current logical-result settings included in it;
- four later support/physical settings currently included even though the
  fixed logical output excluding settings is unchanged; and
- two normaliser-forced identity fields (`schema_version` and
  `rail_profile_id`) included in it.

The exact field lists and mutation outcomes are machine-readable in
[`phase1-chair-analysis-invalidation.json`](../contracts/phase1-chair-analysis-invalidation.json).

## Under-invalidation witnesses

The following representative changes altered logical output without altering
the current geometry signature:

| Mutation | Recalculated output SHA-256 | Findings | Status |
| --- | --- | ---: | --- |
| `template_set_id` | `3de53f62a2eadc91414d46a13a5715f373bb78a47f460dbb21a78c5f2f77da98` | 269 | validated |
| Rail name | `581dc1c9183f818202090adf1c3fb466240a0ba6d5d63b684916bd29d8e20661` | 269 | validated |
| Rail parent-turnout identity | `7c067c61e4e56150d9504990de586d3bfafa906b2bb0adf74ef959b474554d12` | 274 | production-critical conflicts |
| Rail source configuration | `49df102102726e6fe4e04ab6fb79c556eead9bd96a5554208904b80cb26d18dc` | 269 | validated |
| Rail supported feature | `464e5e7b9c13f0e7ec5b210d36f51dd4a73aa610f57896a40acc57288867c550` | 271 | validated |
| Timber width/length axes | `957aa3cd438e82a6dd8c9aa109dc9dc9c608cb78e7aff6b7d1b34d5eb36cf91b` | 275 | validated |
| Timber identifier | `72975b69ef3d7348f0d6fabe02dd698e322e8db2e8a1fdf50cc932a7687f0a5b` | 269 | validated |
| Timber protected features | `8b065559461f475eb9c70e8149a8cc4b170e233caa02089e64a3d7292bb34cf4` | 269 | validated |
| Timber source configuration | `ab8636b6cbc30d7ca08d9b50264aa34f1c3cd65b02af308297fcc945b7ee89bd` | 269 | validated |
| Timber support requirements | `94b5cc1f03ac10b19ce4a6db6adf44d529f598e2d9be3d5b954d3fd1af67eb47` | 267 | validated |
| Crossing suffix inside timber source configuration | `f63cb69f9709a98982e7cfd3388ca103095bd73398c0cdec8c6b3b45bbaaf03a` | 269 | validated |

The most severe witness is the omitted parent-turnout identity: the stale key
can conceal a transition from the accepted baseline status to production-
critical conflicts.

## Actual stale-cache witness

After the baseline had been cached through the application function, the
extractor returned records with changed timber axes:

| Signal | Value |
| --- | --- |
| `cache_reused` | `true` |
| Returned geometry signature | unchanged |
| Actual returned output | baseline `e5d256…55f4` |
| Independently recalculated output | changed-axes `957aa3…f91b` |
| Stale result returned | `true` |

This is a correctness defect, not merely an inefficient cache boundary.

## Precision and ordering

Rail coordinates are rounded to five decimal places in the signature but are
consumed at higher precision. Adding `0.000004 mm` to one rail coordinate kept
the signature unchanged while changing the logical digest to
`ee909b5f70d3c32c2effb37547810bcef2d57476213cc16da5acc31bc5fdd4bd`.
The successor must hash the actual consumed value or calculate and return from
the same declared quantised canonical value.

Reversing all rail records or all timber records changed the signature while
the fixed deterministically sorted logical output remained identical. The
successor must state whether order is semantic and treat calculation and
signature consistently.

## Presentation-control sequence

All presentation and execution-control steps preserved the baseline logical
digest and geometry signature.

| Step | Calculation reused | Display reused | Objects | Diagnostic layers |
| --- | --- | --- | ---: | --- |
| Baseline | No | No | 22 | position markers: 710 edges |
| Hide/restore position markers | Yes | Yes | 22 | retained position layer |
| Show protected positions | Yes | No | 23 | position 710 + protected 708 |
| Hide protected positions | Yes | Yes | 23 | protected layer retained |
| Show footprints | Yes | No | 23 | position 710 + footprints 1,228 |
| Hide footprints | Yes | Yes | 23 | footprint layer retained |
| Change physical/unresolved controls | Yes | Yes | 23 | no analysis-layer change |
| Disable cache | No | No | 22 | position layer rebuilt |

Requesting a missing protected or footprint layer clears and rebuilds the
legacy exact `Part` diagnostic compounds. Hiding it keeps the object. These are
observed legacy mechanics, not the accepted lightweight presentation design.

FreeCADCmd reported every `ViewObject.Visibility` as false, including requested
visible layers. Headless visibility is therefore deliberately excluded as an
authority. Real-GUI visibility, selection mapping, one-command history and
refresh behavior remain open acceptance evidence.

## Successor consequence

The modular application boundary needs distinct signatures for logical
analysis, downstream model support/solids, execution policy and presentation.
Each must cover the exact canonical inputs consumed by its result. A
presentation-only change must not rewrite the authoritative result or create
history, while a calculation mutation must never reuse stale output.

The complete rules are in the contract. Migration of this path remains blocked
until the advertised entity scope passes them and the required GUI evidence is
accepted.

## Reproduction

Fast contract/source checks:

```bash
.venv/bin/python tests/validate_phase1_chair_analysis_invalidation.py
```

Disposable real-FreeCAD oracle:

```bash
flatpak run --command=FreeCADCmd org.freecad.FreeCAD \
  tests/freecad_validate_phase1_chair_analysis_invalidation.py
```

The FreeCAD command must print
`Phase 1 chair analysis invalidation FreeCAD oracle passed` and leave the
ignored source fixture byte-identical.
