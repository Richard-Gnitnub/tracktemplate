# S1 independent engineering evidence map

This map records evidence for the 113 quantities in the current research
`ChairDefinition`. None of their values has an independent engineering reference chain.
An applicable chair drawing and evidence for the owner’s model rail are necessary.
The evidence is not sufficient for a decision to admit a phase exit.

The [S1 pilot plan](../phase-evidence/S1_PILOT_PLAN.md#chair-acceptance-evidence-under-d-p9-005)
owns the engineering requirements in D-P9-005. The
[project plan](../PROJECT_PLAN.md#phase-9a-and-9b-exit-conditions)
owns phase status. This map changes no requirement or acceptance.
It supplies evidence for Exits 9A-1 and 9A-2 at baseline
`8c49501e9998296be3edd5a8d66be21abb1e42c0`.

## Coverage and retained evidence

The [machine-readable map](s1-independent-engineering-evidence-map.json)
contains one record for each quantity. Its package and manifest hashes identify
the exact local inputs. The package, source values and generated output stay
local and untracked. Their Templot lineage and `reference-only` status stay.

| Item | Coverage |
| --- | --- |
| Quantity records | 113: 104 lengths and 9 quantities without a length unit |
| Component ownership | `base`: 14; `inner-jaw`: 29; `key`: 13; `outer-jaw`: 35; `seat`: 22 |
| Calculated quantities | 25 quantities with 75 declared input relationships |
| Constructor inputs | 93 different quantities; 20 more quantities supply inputs to calculated values |
| Construction records | 6 procedures, 5 datums and 5 components |
| Other relationships | 32 records, plus 9 rail relationships against 8 planes |
| Quantity values with an independent engineering reference chain | 0 of 113 |
| Recorded uncertainty and accepted engineering tolerances | Missing for all 113 quantities |

The count includes quantities that only supply inputs to calculated values.
It counts each quantity one time, also when different procedures use it.
The recorded inputs do not show that the loader calculates each value again.
Shared names do not show equal engineering meanings.

## How to read the map

Each quantity record connects its exact identifier to retained sources,
inputs to calculated values, procedures and relationships. Source records give locators
and hashes where retained files supply them. A null external-source hash means
that this task kept no source file. No hash verification of that content occurred.

`candidate_links` identify sources that might supply missing evidence.
`may-help` does not identify an applicable drawing or give evidence for a quantity value.
`independently_supported_value: false` records the missing independent engineering reference chain.
Null uncertainty and tolerance fields record missing evidence, not zero limits.

`relationship_ids` include relationships that use the quantity or one of its
procedures. A procedure connection does not show direct use in each relationship.
The relationship's `quantity_ids` give its named inputs.

`gap_routes` identify the necessary type of work:

| Route | Missing evidence |
| --- | --- |
| `prototype-source-research` | Applicable drawings, standards, dimensions, component interfaces and source revisions |
| `model-stock-measurement` | Identity of the actual model rail, measured dimensions and measurement uncertainty |
| `engineering-derivation-or-decision` | Engineering evidence for a calculated value or a construction method, followed by the applicable acceptance |
| `manufacturing-empirical-evidence` | Measurements and tests that separate manufacturing effects from prototype geometry and model rail fit |

A calculated quantity also requires evidence for its inputs.
Follow `input_quantity_ids` through the map for these gaps.
All routes keep the requirement for accepted numerical tolerances before
production acceptance. A source dimension or measurement alone supplies no
accepted project tolerance.

## Methods with independently evidenced results

The following methods have independently evidenced results, with these limits:

1. The [NIST conversion factors](https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8)
   and [SI prefixes](https://www.bipm.org/en/measurement-units/si-prefixes)
   give the exact inch-to-millimetre conversion: `1 in = 25.4 mm`.
2. With the declared research scale of `4 mm/ft`, the international foot gives
   the length ratio `4/304.8 = 1/76.2`. With the same ratio in each direction,
   the volume ratio is its cube. This arithmetic gives no acceptance to a scale or shape.
3. The [C&L explanation](https://www.clfinescale.co.uk/faq-s) gives rail height
   in thousandths of an inch from the rail code. The code does not specify the
   complete rail contour or measure the owner's rail.

These methods give no evidence for chair dimensions, contact, clearance or physical fit.
They do not give evidence for the measurement conventions of a historical drawing
that was not examined.

The Code 75 relationship gives `1.905 mm`. The three retained `rail_depth_mm`
quantities give `1.900 mm` at the declared research scale.
Their identifiers are `quantity:base:rail_depth_mm`,
`quantity:key:rail_depth_mm` and `quantity:seat:rail_depth_mm`.
The difference, retained value minus published code height, is `-0.005 mm`.
This difference gives no fit verdict. Measurements and accepted tolerances
are missing. This task changes none of these quantities.

## Sources that can supply more evidence

The source catalogue in the map records retrieval dates, exact locations,
access limits and unresolved rights. These sources have different uses:

| Source | Available evidence and missing evidence |
| --- | --- |
| [National Railway Museum catalogue](https://www.railwaymuseum.org.uk/sites/default/files/2018-03/North%20Eastern%20Railway%20Civil%20Engineering%20Drawings%20List.pdf) | PDF page 274, Box 246, shows “Common Chair S.I. 46 LB” with different views and sections. The drawing was not examined. Its designation, revision and applicability stay unresolved. |
| [NERA 1926 publication](https://ner.org.uk/product/standard-railway-equipment-permanent-way-1926/) | The publisher shows the drawing collection. The related plates and their changes were not examined. |
| C&L `4RA201A` and rail-code explanation | Supplier identity and the height relationship are available. The owner’s stock, complete contour, measurement uncertainty and tolerances stay unresolved. |
| BSI `BS 9:1935` and its contents preview | The catalogue identifies the standard. The preview gives the location of the `95R` plate: printed page 41. That plate and applicable tolerance clauses were not examined. |
| British Steel `RPGD:ENG:072026` | The manufacturer gives dimensions for `BS95RBH`. Evidence of its applicability to this historical chair is missing. The website also gives restrictions on content use. |

An adjacent catalogue entry does not select the rail section for this chair.
An available rail publication also does not select it. Catalogue access gives no drawing dimensions.
The [rights policy](../LICENSING_BOUNDARIES.md) and
[provenance policy](../PROVENANCE.md) own admission for each intended use.
This map grants no rights to external material or production output.

## Relationships that remain unsupported

The relationship records include component dimensions, shared inputs, frame
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
do not supply accepted engineering tolerances.

## Next evidence boundary

Recommendation: get the Box 246 chair drawing, its complete title information
and any companion sheets. The NERA collection is a different acquisition route.
Inspection must identify the designation, revision, applicable rail section,
dimension locations and permitted use before the drawing supplies evidence for quantities.
The catalogue spelling `S.I.` gives no independent evidence for the intended S1 prototype.

The supplier and batch identity of the owner’s model rail are also necessary.
A controlled contour where available, and measurements with recorded uncertainty, are necessary.
No purchase, source-holder contact or physical measurement occurred in this task.
Acquisition or access is the next boundary. There is no exit-admission proposal.

At the recorded baseline, Phase 9A stays at `1/4`. Exits 9A-1–3 stay Pending.
Phase 9B stays unopened. This map gives no definition, tolerance, pilot, package,
production, release or rights acceptance.
