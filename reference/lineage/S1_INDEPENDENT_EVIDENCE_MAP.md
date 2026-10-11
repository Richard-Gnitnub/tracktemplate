# S1 independent engineering evidence map

This map preserves the assessment of 113 quantities in the frozen research
`ChairDefinition`. That assessment records no independent engineering reference chain for their values.
The research registration below adds source information. It changes none of those quantity records.
Source registration gives no acceptance for a dimension, model rail fit or phase exit.

The [S1 pilot plan](../phase-evidence/S1_PILOT_PLAN.md#chair-acceptance-evidence-under-d-p9-005)
owns the engineering requirements in D-P9-005. The
[project plan](../PROJECT_PLAN.md#phase-9a-and-9b-exit-conditions)
owns phase status. This map changes no requirement or acceptance.
It supplies evidence for Exits 9A-1 and 9A-2 at baseline
`8c49501e9998296be3edd5a8d66be21abb1e42c0`.

## Coverage and retained evidence

The [machine-readable map](s1-independent-engineering-evidence-map.json)
contains one record for each quantity. Its package and manifest hashes identify
the local input identities. The package, source values and generated output stay
local and untracked. Their Templot lineage and `reference-only` status stay.

| Item | Coverage |
| --- | --- |
| Quantity records | 113: 104 lengths and 9 quantities without a length unit |
| Component ownership | `base`: 14, `inner-jaw`: 29, `key`: 13, `outer-jaw`: 35, `seat`: 22 |
| Calculated quantities | 25 quantities with 75 recorded input relationships |
| Constructor inputs | 93 different quantities. 20 more quantities supply inputs to calculated values. |
| Construction records | 6 procedures, 5 datums and 5 components |
| Other relationships | 32 records, plus 9 rail relationships against 8 planes |
| Quantity values with an independent engineering reference chain | 0 of 113 |
| Recorded uncertainty and accepted numerical tolerances | Missing for all 113 quantities |

The count includes quantities that only supply inputs to calculated values.
It counts each quantity one time, also when different procedures use it.
The recorded inputs do not show that the loader calculates each value again.
The same names do not show equal engineering meanings.

## How to read the map

Each quantity record connects its identifier to sources that the project kept,
inputs to calculated values, procedures and relationships. Source records give locators
and hashes where files that the project kept supply them. A null external-source hash means
that this task kept no source file. No hash verification of that content occurred.

`candidate_links` identify sources that can supply missing evidence.
`may-help` does not identify an applicable drawing or give evidence for a quantity value.
`independently_supported_value: false` records the missing independent engineering reference chain.
Null uncertainty and tolerance fields record missing evidence, not zero limits.

`relationship_ids` include relationships that use the quantity or one of its
procedures. A procedure connection does not show direct use in each relationship.
The relationship's `quantity_ids` give its named inputs.

`gap_routes` identify the necessary type of work:

| Work type | Missing evidence |
| --- | --- |
| `prototype-source-research` | Applicable drawings, standards, dimensions, component interfaces and source revisions |
| `model-stock-measurement` | Identity of the owner’s model rail, measured dimensions and measurement uncertainty |
| `engineering-derivation-or-decision` | Engineering evidence for a calculated value or a construction method, followed by the applicable acceptance |
| `manufacturing-empirical-evidence` | Measurements and tests that separate manufacturing effects from prototype geometry and model rail fit |

For a calculated quantity, evidence for its inputs is also necessary.
Follow `input_quantity_ids` through the map for these gaps.
All types of work keep the requirement for accepted numerical tolerances before
production acceptance. A source dimension or measurement by itself supplies no
accepted numerical tolerance.

## Methods with independent evidence

The following methods have independent evidence for their results, with these limits:

1. The [NIST conversion factors](https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8)
   and [SI prefixes](https://www.bipm.org/en/measurement-units/si-prefixes)
   give the inch-to-millimetre conversion: `1 in = 25.4 mm`.
2. With the recorded research scale of `4 mm/ft`, the international foot gives
   the length ratio `4/304.8 = 1/76.2`. With the same ratio in each direction,
   the volume ratio is its cube. This arithmetic gives no acceptance to a scale or shape.
3. The [C&L explanation](https://www.clfinescale.co.uk/faq-s) gives rail height
   in thousandths of an inch from the rail code. The code does not specify the
   complete rail contour or measure the owner's rail.

These methods give no evidence for chair dimensions, contact, clearance or physical fit.
They do not give evidence for the measurement conventions of a historical drawing
that was not examined.

The Code 75 relationship gives `1.905 mm`. The three `rail_depth_mm`
quantities that the project kept give `1.900 mm` at the recorded research scale.
Their identifiers are `quantity:base:rail_depth_mm`,
`quantity:key:rail_depth_mm` and `quantity:seat:rail_depth_mm`.
The difference, the value that the project kept minus the published code height, is `-0.005 mm`.

This difference does not show whether physical fit is correct. Measurements and accepted tolerances
are missing. This task changes none of these quantities.

## Sources that can supply more evidence

The source catalogue in the map records source identities, locations, inspection limits and unresolved rights.
Its `research_reports` record identifies the complete bibliography that the project owner supplied:
*TrackTemplate: independent railway engineering reference bibliography*, dated 9 October 2026.
The record keeps the report filename, byte hash and all 12 numbered entries.
The map preserves the source identifiers from the baseline. The other source records stay the same.
They include C&L, British Steel, NIST and BIPM.

The inspection statements below come from that report.
The registration author did not examine the drawings again or examine access at the registration date.
After a drawing inspection, detailed transcription, revision checks and engineering assessment can be necessary.
Catalogue inspection gives no evidence for a drawing dimension.

| Report entry | Source and reported inspection |
| --- | --- |
| 1 | LMS compilation, cover dated 1928: specified SRE drawings examined. The cover date does not give the date of each sheet. |
| 2 | NERA 1926 facsimile: publisher catalogue only. Related plates were not examined. |
| 3 | NRM collection 2009-7071, Box 246: catalogue entries examined. Drawings not examined. Blank drawing references stay blank. |
| 4 | REA rail-joint report, 1905: drawing leaves 2, 32 and 52 examined. The complete report was not examined. |
| 5 | LSWR switch drawing 2, negative 2437: sheet examined. |
| 6 | LSWR crossing drawing 4c, negative 2474: sheet examined. |
| 7 | MSLR Type 44 and Type 39 left half: sheets examined, with different dimension coverage. |
| 8 | GCR check-chair drawing 40A: sheet examined. That number alone does not show that the rail drawing is applicable to this chair. |
| 9 | BS 9:1935: publisher record only in this report. The earlier contents-preview record stays a different record. |
| 10 | BS 11:2015: publisher description only. Profile figures and tolerances not examined. |
| 11 | BS 47-1:1991: publisher description only. Individual profiles not examined. |
| 12 | PWI bullhead supplement: holding catalogue only. The reported 1943/1991 publication relationship stays unverified. |

The machine-readable records keep drawing references, page numbers, printed callouts, engineering findings and limitations from the report.
Printed callouts stay as reported source findings. They are not accepted parameters or measurements from scans.
Related sheets in one drawing family are complementary evidence. Reproductions of one sheet do not supply independent confirmations.
No evidence shows that the LMS, NERA and NRM copies have the same revision.

The report gives access conditions and prices for its date.
These conditions and prices give no third-party permission and do not show whether the material is available now.
The reported Oldpway licence statement gives no evidence of its legal chain or project clearance.
The [rights policy](../LICENSING_BOUNDARIES.md) and
[provenance policy](../PROVENANCE.md) own admission for each intended use.
Registration includes no drawing files and gives no rights to external material or production output.

## Relationships with missing evidence

The relationship records include component dimensions, inputs with more than one use, frame
placement, contact checks and rail surfaces. Evidence for their engineering use is missing.
Eight infinite planes do not give the complete rail contour.
Distances between constructed components give no evidence for physical fit.

The map also identifies Templot sampling, Templot triangulation and Templot mark-grid
behaviour. Those implementation choices have no independent production
justification here. They do not become drawing requirements.

The source rail values include source printing allowances. Disabled optional
manufacturing controls do not remove those embedded effects.
The independent engineering reference chain must separate prototype geometry, model rail fit and
manufacturing compensation. Mathematical limits and software comparison limits
do not supply accepted numerical tolerances.

## Next evidence boundary

First, examine the historical drawings in the LMS compilation that the report identifies for remote access.
The report gives this sequence for detailed inspection and transcription:

| Sequence | Drawing and PDF page | Engineering question |
| --- | --- | --- |
| 1 | [No.4, p.6](https://www.lmssociety.org.uk/assets/pdfs/PermanentWay1928.pdf#page=6) | S.I. seat, jaws, key faces, base and fixing datums |
| 2 | [No.2, p.4](https://www.lmssociety.org.uk/assets/pdfs/PermanentWay1928.pdf#page=4) | Rail profile and fishplate interfaces |
| 3 | [No.1, p.3](https://www.lmssociety.org.uk/assets/pdfs/PermanentWay1928.pdf#page=3) | Key section, taper and fixing interfaces |
| 4 | [No.18A, p.26](https://www.lmssociety.org.uk/assets/pdfs/PermanentWay1928.pdf#page=26) | Revised P chair and supersession |
| 5 | [No.38, p.61](https://www.lmssociety.org.uk/assets/pdfs/PermanentWay1928.pdf#page=61) | Crossing-angle variants and the reported S.I. jaw relationship |

These five drawings belong to one source family. Nos.6, 7 and 18 supply related information.
Nos.36 and 37 can supply information for a selected crossing chair.
The other company drawings supply comparisons in their reported prototype scopes.
No dimensioned spring-steel-key drawing was verified in the report.

NRM references stay optional archival leads. A physical visit or archive request is not necessary for remote drawing assessment.
The NERA facsimile and PWI holding are also optional sources. Registration authorises no purchase, visit or external contact.
The derivative NRM list's suggested numbers do not replace blank references in the official catalogue.

In subsequent engineering work, record prototype geometry, model adaptations and manufacturing compensation as different types of data.
This registration includes no drawing transcription, geometry change, physical measurement or evidence promotion.
There is no exit-admission proposal. The project plan owns current phase status.

At the recorded baseline, Phase 9A stays at `1/4`. Exits 9A-1–3 stay Pending.
Phase 9B stays unopened. This map gives no definition, tolerance, pilot, package,
production, release or rights acceptance.
