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
The `research_reports` records in the map identify the two versions of the bibliography that the project owner supplied:
*TrackTemplate: independent railway engineering reference bibliography*.
The 9 October 2026 report contains 12 entries. The changed report of 11 October contains 16 groups.
Each record keeps the report filename, byte hash and connections to source records.

The 11 October report adds evidence for these items:

- Plain-line sleeper arrangements.
- Chair families.
- Switches and crossings.
- Diamonds, crossovers, slips and scissors.
- Timbering.

The frozen S1 quantity assessment does not change when the map adds these sources.
The map preserves the source identifiers from the baseline. The other source records stay the same.
They include C&L, British Steel, NIST and BIPM.

The inspection statements below come from the changed report of 11 October.
The registration author did not examine the drawings again or examine access at the registration date.
After a drawing inspection, detailed transcription, revision checks and engineering assessment can be necessary.
Catalogue inspection gives no evidence for a drawing dimension.

| 11 October report group | Source and reported inspection |
| --- | --- |
| 1 | LMS compilation, cover dated 1928: specified SRE sheets examined. Other titles mapped without full inspection. The compilation includes a 1943 rider. |
| 2 | GWR/Western Region staff notes: seven sheets examined, with dates from 1937 to 1959. Some changes to the sheets are not clear. |
| 3 | Worthington report: plates 6, 23 and 35–36 examined. The 1900 congress and 1901 proceedings have different dates. |
| 4 | MSLR/GCR drawings: Types 39A, 39B, 44 and 39 left half examined. The through-crossing companion has a missing left part. |
| 5 | Hunt report: plates 3, 5, 8, 11 and 12 examined. The report gives no values for some small fractions that the researcher could not read or did not record. |
| 6 | REA rail-joint report, 1905: drawing leaves 2, 32 and 52 examined. The complete report was not examined. |
| 7 | LSWR: switch drawing 2, crossing drawing 4c and a double-slip fragment examined. The fragment has no verified drawing number. |
| 8 | NERA 1926 facsimile: publisher description only. Related plates were not examined. |
| 9 | NERA NER 1912 standards: publisher description only. Related plates were not examined. |
| 10 | NRM collection 2009-7071, Box 246: catalogue entries examined. Drawings not examined. Blank references stay blank. Retracing dates do not show initial design dates. |
| 11 | Allen, 1915, GERS product RE042: supplier description only. No figure or dimension examined. The supplier gives personal-use restrictions. |
| 12 | GCR check-chair drawing 40A: sheet examined. That number alone does not show that the rail drawing is applicable to this chair. |
| 13 | BS 9:1935: publisher record only in this report. The earlier contents-preview record stays a different record. |
| 14 | BS 11:2015: publisher description only. Profile figures and tolerances not examined. |
| 15 | BS 47-1:1991: publisher description only. Individual profiles not examined. |
| 16 | PWI bullhead supplement: holding catalogue only. The reported 1943/1991 publication relationship stays unverified. |

The machine-readable records keep drawing references, page numbers, printed callouts, engineering findings and limitations from the two reports.
They preserve previous observations and links that the 11 October report does not repeat.
Printed callouts stay as reported source findings. They are not accepted parameters or measurements from scans.

Related sheets in one drawing family are complementary evidence. Reproductions of one sheet do not supply independent confirmations.
No evidence shows that the LMS, NERA and NRM copies have the same revision.
Western Region references to SRE designs do not supply independent confirmation of those designs.
Oldpway and CNAM reproductions of the same publication also do not supply independent confirmations.

The 11 October report gives joint-end sleeper intervals with their applicable company, rail and direction.
These sequences do not give one spacing rule for all railways.
An overall rail diagram, an obtuse-crossing unit and a complete timbering plan give different information.
The LMS No.48 jaw-template allowance belongs to an inspection gauge. It is not a chair dimension or manufacturing compensation.

The rider on PDF page 80 has the drawing identifier No.46E. The report does not identify a separate parent drawing.
Scan order gives no authority to change E to B.

Each report gives access conditions and prices for its date.
These conditions and prices give no third-party permission and do not show whether the material is available now.
Reported provider permissions do not show the legal chain for those permissions or project clearance.
The GERS personal-use restriction stays recorded. Registration gives no permission to redistribute the RE042 publication.

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

The changed report of 11 October gives this sequence for later inspection and transcription.
The report gives remote access to all five sheets in the LMS compilation.

| Sequence | Drawing and PDF page | Engineering question |
| --- | --- | --- |
| 1 | [No.1, p.3](https://www.lmssociety.org.uk/assets/pdfs/PermanentWay1928.pdf#page=3) | Joint, end and interior sleeper intervals, sizes, keys and fastenings. Compare No.49. |
| 2 | [No.38B, p.63](https://www.lmssociety.org.uk/assets/pdfs/PermanentWay1928.pdf#page=63) | Junction and crossover timbering, chair positions and joint support. Compare Nos.38C/38D. |
| 3 | [No.32, p.49](https://www.lmssociety.org.uk/assets/pdfs/PermanentWay1928.pdf#page=49) | Common-crossing and check geometry, timber intervals and fastenings. Use the applicable chair sheets. |
| 4 | [No.45B, p.75](https://www.lmssociety.org.uk/assets/pdfs/PermanentWay1928.pdf#page=75) | Full slip diagrams and detailed part-arrangements. Compare No.46B. |
| 5 | [No.45C, p.76](https://www.lmssociety.org.uk/assets/pdfs/PermanentWay1928.pdf#page=76) | Scissors arrangement, through timbers and specialist supports. Compare No.46C. |

These five drawings belong to one source family. The records keep the previous component evidence with its initial sequence.
Nos.4, 2, 18A and 38 keep their component roles. No.48 adds inspection-datum evidence.
The other company drawings supply comparisons in their reported prototype scopes.

Complete fixed-diamond and tandem construction records stay unresolved.
The separate 1:10 switch-diamond rider, parent No.46E and a dimensioned spring-steel-key drawing also stay unresolved.
The report gives only some evidence for steel and concrete sleepers.

NRM references stay optional archival leads. A physical visit or archive request is not necessary for remote drawing assessment.
The NERA facsimiles, Allen publication and PWI holding are also optional sources.
Registration authorises no purchase, visit or external contact.
The derivative NRM list's suggested numbers do not replace blank references in the official catalogue.

In subsequent engineering work, record prototype geometry, model adaptations and manufacturing compensation as different types of data.
This registration includes no drawing transcription, geometry change, physical measurement or evidence promotion.
There is no exit-admission proposal. The project plan owns current phase status.

At the recorded baseline, Phase 9A stays at `1/4`. Exits 9A-1–3 stay Pending.
Phase 9B stays unopened. This map gives no definition, tolerance, pilot, package,
production, release or rights acceptance.
