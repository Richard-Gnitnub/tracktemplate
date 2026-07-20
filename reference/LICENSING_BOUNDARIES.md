# Licensing, Data Provenance, and Output Boundaries

Status: **Accepted project-control policy — 2026-07-20. Phase 1 lineage
audit remains open.**

This document defines how TrackTemplateMacro distinguishes software source,
engineering knowledge, factual data, external evidence, Templot-specific
material, canonical chair definitions, and generated output. It is a
repository policy, not legal advice or a ruling on ownership, copyright,
database right, design right, patent, contract, or derivative-work status.

The policy is deliberately prospective. It does not retroactively certify all
current B14/B15 output for unrestricted publication or commercial use. That
status requires the Phase 1 lineage audit defined below.

## Responsibilities of the project documents

- [PROVENANCE.md](PROVENANCE.md) records what source and licence evidence was
  actually found, including the exact Templot5 snapshot and historical output
  notices.
- This document owns the operational classification, separation, collaboration,
  package-licensing, and output-clearance rules.
- [ARCHITECTURE.md](ARCHITECTURE.md) owns the neutral canonical data model and
  adapter direction.
- [PROJECT_PLAN.md](PROJECT_PLAN.md) owns the audit timing and release gates.
- [`NOTICE.md`](../NOTICE.md) states the project licence and the clarification
  applicable to ordinary generated output.

## Evidence boundary already established

The exact reviewed Templot5 revision 556b archive is identified in
[PROVENANCE.md](PROVENANCE.md). Its Pascal source headers state GNU GPL version
3 or later, and its print/PDF paths add a notice asserting copyright in design
elements and data contained in the drawing.

The reviewed archive contains no general CC BY-NC-SA licence or general
non-commercial licence for Templot5 output. Its Creative Commons wording
concerns imported National Library of Scotland map material, not all Templot
output. Historical Templot2 terms made a broader output assertion, but they
predate Templot5 and are recorded as historical evidence rather than silently
treated as the current Templot5 licence.

The GNU GPL itself states that output from a covered work is covered only when
the output, given its content, constitutes a covered work. The program licence
and the rights in material embedded in an output must therefore be analysed
separately. See [GPLv3 section 2](https://www.gnu.org/licenses/gpl-3.0.html#section2)
and the [GNU GPL output FAQ](https://www.gnu.org/licenses/gpl-faq.html#WhatCaseIsOutputGPL).

Creative Commons terms likewise apply only to identified licensed material and
rights the licensor has authority to license. A notice or licence cannot, by
itself, convert an unprotected idea or fact into protected material. See the
[CC BY-NC-SA 4.0 legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en).

UK government guidance likewise distinguishes the protected expression of
software from its underlying ideas and recognises that identical results may
be produced through different code. That does not authorise copying expressive
source or a protected database. See the
[UK knowledge-assets guidance](https://www.gov.uk/government/publications/knowledge-asset-management-in-government/knowledge-assets-classes-and-types-annex-a).

## Mandatory provenance classifications

Every value collection, geometry definition, fixture, comparison source, or
external asset that can affect a production output must use one or more of the
following classifications. A source may contain a mixture; classification is
field- or component-level where package-level labelling would hide that fact.

| Classification | Meaning | Permitted project role |
| --- | --- | --- |
| `engineering_method` | Established mathematics, geometric relationship, railway method, functionality, or algorithmic idea | May be implemented in original project expression with an engineering citation; do not call it Templot data merely because Templot uses it |
| `engineering_fact` | An independently evidenced prototype dimension, gauge, angle, relationship, or other individual fact | May enter canonical data with its primary source and units recorded |
| `project_measurement` | A calibrated measurement made by or for this project from a physical object or rights-cleared evidence | May enter canonical data with method, calibration, uncertainty, operator, and evidence hash |
| `project_derivation` | A value or procedural parameter fitted or calculated by project tooling from recorded inputs | May enter canonical data with its complete derivation and input identities |
| `user_design` | Alignment, topology, parameter, layout, or other creative/engineering choice supplied by the user | May enter canonical state; retained third-party dependencies must still be recorded |
| `templot_source_expression` | Templot code, comments, close translation, expressive structure, or other GPL-covered source material | May inform or be adapted into GPL-compatible project source with notices and attribution; it is not canonical chair data merely because it computes geometry |
| `templot_reference_data` | A Templot-authored table, profile, dataset, selection, arrangement, or value collection without an independent accepted evidence chain | Reference/comparison use only until its exact licence, database-right, redistribution, and output status are accepted |
| `templot_media_output` | A Templot-generated PDF, screenshot, drawing, DXF, STL, data file, or similar media artifact | Local comparison oracle only unless a source-specific permission permits the intended redistribution and output use |
| `third_party_evidence` | An external scan, CAD body, drawing, photograph, standard, database, or measurement set | Use only within its recorded access, adaptation, output, and redistribution permissions |
| `generated_output` | SVG, DXF, STL, STEP, FreeCAD object, report, manifest, image, or physical-production record generated from canonical state | Carries the recorded rights dependencies of its inputs and any protected material deliberately embedded in it |

An individual factual value does not become `templot_reference_data` merely
because Templot agrees with it. Conversely, a systematically copied Templot
table must not be relabelled as independent facts simply because its entries
are numerical. UK database rights can protect substantial investment in a
database separately from copyright in its selection or arrangement; see the
[UK Intellectual Property Office guidance](https://www.gov.uk/guidance/sui-generis-database-rights).

“Independently evidenced” describes the provenance of a value. It does not
turn this source-informed project into a clean-room implementation, and it must
not be used to make that claim.

## Canonical-data admission rule

Production canonical state may contain only material whose source identity,
classification, intended use, and redistribution/output status are recorded
and accepted. In particular:

1. `engineering_fact`, `project_measurement`, and `project_derivation` values
   must identify their primary evidence rather than cite a Templot comparison
   as their origin.
2. `templot_reference_data`, `templot_media_output`, and unresolved
   `third_party_evidence` do not enter a rights-cleared production definition.
3. A comparison against Templot may record hashes, settings, numeric summaries,
   residuals, and pass/fail findings. The upstream media or dataset remains
   local and untracked unless redistribution is expressly accepted.
4. Reimplementing a mathematical result does not authorise close translation
   of expressive source. Source adaptation remains subject to GPL notices and
   the source-informed classification in [PROVENANCE.md](PROVENANCE.md).
5. Missing or ambiguous provenance is a finding, not an invitation to infer a
   convenient source or licence.

## Neutral chair-definition and collaboration boundary

The authoritative interchange is a TrackTemplateMacro `ChairDefinition`, not
“Templot data”. It is a neutral, versioned description of prototype facts,
constituent geometry, interfaces, relationships, manufacturing separation, and
provenance. Native definitions and assisted scan/CAD assimilation use this same
contract.

Each reusable package must record, at package, component, and material-field
level where applicable:

- stable source and component identifiers;
- creator or supplier, acquisition date, and precise source locator;
- original filename, format, byte hash, units, scale, coordinate frame, and
  calibration record;
- one of the mandatory classifications above;
- whether each value is measured, factual, fitted, derived, inferred,
  unresolved, or used only for comparison;
- uncertainty, tolerances, assumptions, and complete derivation inputs;
- licence expression or `NOASSERTION`, permitted use, output use, adaptation,
  and redistribution status;
- reviewer, validation evidence, residual result, and explicit acceptance.

Project-authored factual chair-definition packages intended for unrestricted
reuse should use **CC0-1.0** as the default target where the project controls
all rights necessary to make that dedication. CC0 is applied only when the
individual package explicitly says so after review. It must never be applied
to Templot-derived, third-party, unknown, or mixed-rights material by
assumption. Raw scans, CAD files, drawings, and photographs retain their own
separately recorded terms and need not be distributed with a definition.

Code contributed to TrackTemplateMacro remains GPL-3.0-or-later unless a file
states an accepted compatible alternative. A data contributor must confirm
that they have authority to contribute the material under the package's stated
terms. An attribution condition is not automatically disqualifying when the
production path records and satisfies it and the licence otherwise permits the
declared commercial/publication use. A package containing `NC`, `NOASSERTION`,
reference-only, unresolved, or otherwise incompatible dependencies cannot
qualify that rights-cleared release-candidate path.

## Templot compatibility adapter

Templot compatibility, if implemented, is an optional outward adapter:

```text
rights-cleared evidence
          |
          v
neutral ChairDefinition ----> TrackTemplate exact/export adapters
          |
          `------------------> optional Templot-format adapter
```

The adapter may map an accepted neutral definition into a documented Templot
format. It must not:

- make a Templot schema or file the canonical project state;
- import a Templot PDF, mesh, drawing, or opaque output as authoritative chair
  geometry;
- feed Templot-authored values back into the neutral definition without a new
  provenance and rights review; or
- change the source classification or ownership record of outward data merely
  because Templot consumed it.

If a neutral package is shared with Martin Wynne or the Templot project, the
same package may be used by both programs under its recorded data licence.
Templot may apply its own notices to media generated by Templot; that does not
automatically reclassify separate output generated by TrackTemplateMacro from
the original neutral package.

## Generated-output policy

TrackTemplateMacro is GPL-3.0-or-later, but the project does not assert control
over ordinary output merely because the program generated it. The project does
not apply CC BY-NC-SA or another non-commercial restriction to ordinary output
solely by execution of the program.

This clarification is not a warranty that every output is free of third-party
rights. Rights and conditions follow the user's inputs, definition packages,
embedded assets, output boilerplate, and other protected material actually
present. The project cannot grant rights it does not hold.

Production manifests must eventually identify:

- generating program/version and canonical-model signature;
- every chair-definition/package identifier, version, classification, and
  licence expression;
- external or restricted material deliberately embedded in the output;
- unresolved or reference-only dependencies; and
- the resulting project-control clearance status.

The permitted clearance statuses are:

| Status | Project meaning |
| --- | --- |
| `rights-cleared` | Every known output-affecting dependency has accepted terms compatible with the declared intended use, and every required condition such as attribution is recorded and satisfied; this is still not legal advice or a non-infringement warranty |
| `restricted` | A recorded licence or right prevents the declared intended use or imposes a relevant condition that the production/publication path has not satisfied |
| `reference-only` | Material may be used to compare or validate locally but not as a production/publication dependency |
| `unknown` | Ownership, source, licence, output effect, or redistribution status is unresolved |

No current B14/B15 output receives `rights-cleared` merely because this policy
was adopted. Until the Phase 1 audit closes, its project-control status is
`unknown` unless a narrower output has its own completed record.

## Publication and physical-production target

The release-candidate target is a documented path in which a user can create,
print, photograph, publish, exhibit, or use a TrackTemplateMacro-generated
turnout or chair commercially without seeking separate permission from Martin
Wynne merely because this project was informed by Templot. That target is met
only when the actual canonical inputs and embedded output materials qualify as
`rights-cleared` for the declared use.

The target does not cover direct reproduction of a Templot PDF, screenshot,
drawing, mesh, data file, logo, or other Templot media output. Such material
retains its own recorded or unresolved status. A photograph or render of a
functional article generated solely from a rights-cleared project path is a
different case from reproducing the upstream drawing used as a comparison
oracle.

UK law contains a specific provision concerning functional articles made from
design documents, but artistic works and other rights require separate
analysis; the project does not rely on that provision as a blanket clearance.
See [Copyright, Designs and Patents Act 1988, section
51](https://www.legislation.gov.uk/ukpga/1988/48/section/51).

## Phase 1 lineage audit

Before the project describes ordinary production output as unrestricted or
rights-cleared, Phase 1 must:

1. inventory every table, profile, constant, rule, asset, and generated
   boilerplate that can materially affect SVG, DXF, STL, STEP, retained
   FreeCAD objects, reports, manifests, or images;
2. classify each source at the smallest practical field/component granularity;
3. identify values supported only by Templot source or media output;
4. establish an accepted engineering, measurement, or separately licensed
   evidence chain for the release-candidate canonical path, or mark the
   dependency restricted/reference-only/unknown;
5. keep GPL source-expression compliance separate from data and output-rights
   analysis;
6. define and test the machine-readable dependency/clearance manifest; and
7. obtain explicit owner acceptance of the first S1 package's evidence,
   licence, and intended commercial/publication use before implementation.

The audit may preserve Templot as a local numerical and geometric oracle. It
does not require disguising the project's source-informed history or removing
lawfully used GPL source. Its purpose is to ensure that validation evidence is
not mistaken for the rights basis of canonical production data.
