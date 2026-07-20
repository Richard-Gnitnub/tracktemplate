# Licensing, Data Provenance, and Output Boundaries

Status: **Base policy accepted by the project owner on 2026-07-20. The
red-team executable-control amendments are implemented for owner review, and
the scoped Phase 1 lineage audit remains open.**

This document defines how TrackTemplateMacro distinguishes software source,
engineering knowledge, factual data, external evidence, Templot-specific
material, canonical chair definitions, and generated output. It is a
repository policy, not legal advice or a ruling on ownership, copyright,
database right, design right, patent, contract, or derivative-work status.

The acceptance status records the project owner's explicit approval of the
policy direction and requested implementation on 2026-07-20. It is not an
approval asserted by the authoring tool and does not turn this internal review
into professional legal clearance.

The policy is deliberately prospective. It does not retroactively certify all
current B14/B15 output for unrestricted publication or commercial use. That
status requires the Phase 1 lineage audit defined below.

## Responsibilities of the project documents

- [PROVENANCE.md](PROVENANCE.md) records what source and licence evidence was
  actually found, including the exact Templot5 snapshot and historical output
  notices.
- This document owns the operational classification, separation, collaboration,
  package-licensing, and output project-status rules.
- [ARCHITECTURE.md](ARCHITECTURE.md) owns the neutral canonical data model and
  adapter direction.
- [PROJECT_PLAN.md](PROJECT_PLAN.md) owns the audit timing and release gates.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) owns the prospective DCO sign-off and
  project data/evidence declaration.
- [`NOTICE.md`](../NOTICE.md) states the project licence and the clarification
  applicable to ordinary generated output.
- [`schemas/dependency-manifest-v1.schema.json`](schemas/dependency-manifest-v1.schema.json)
  is the portable manifest structure;
  [`tools/validate_dependency_manifest.py`](../tools/validate_dependency_manifest.py)
  applies the fail-closed project-status rules.

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

Copyright and data licensing do not exhaust the relevant rights. UK guidance
recognises separate registered and automatic unregistered protection for a
product's appearance, shape and configuration. Patent rights concern technical
inventions, while trade marks concern branding. CC0 itself does not waive
patent or trade-mark rights or clear rights held by other people. The manifest
therefore records these reviews independently. See the UK guidance on
[unregistered designs](https://www.gov.uk/unregistered-designs), the official
[registered-design search](https://www.gov.uk/search-registered-design),
[patent search](https://www.gov.uk/search-for-patent), and
[trade-mark search](https://www.gov.uk/search-for-trademark), plus the
[CC0 1.0 legal code](https://creativecommons.org/publicdomain/zero/1.0/legalcode.en).

## Mandatory provenance classifications

Every value collection, geometry definition, fixture, comparison source, or
external asset that can affect a production output must use one or more of the
following classifications. A source may contain a mixture; classification is
field- or component-level where package-level labelling would hide that fact.

| Classification | Meaning | Permitted project role |
| --- | --- | --- |
| `engineering_method` | Established mathematics, geometric relationship, railway method, functionality, or algorithmic idea | May be implemented in original project expression with an engineering citation; do not call it Templot data merely because Templot uses it |
| `engineering_fact` | An independently evidenced prototype dimension, gauge, angle, relationship, or other individual fact | May enter canonical data with its primary source and units recorded |
| `project_measurement` | A calibrated measurement made by or for this project from a physical object or project-cleared evidence | May enter canonical data with method, calibration, uncertainty, operator, and evidence hash |
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
   `third_party_evidence` do not enter a project-cleared production definition.
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
  redistribution, commercial-use and publication status;
- reviewer, validation evidence, residual result, and explicit acceptance;
- registered-design, unregistered-design, patent and trade-mark review status,
  territory, date, reviewer, evidence and unresolved findings; and
- the contributor/DCO or external-authority record that permits the project to
  accept the material under its stated package terms.

Project-authored factual chair-definition packages intended for unrestricted
reuse should use **CC0-1.0** as the default target where the project controls
all rights necessary to make that dedication. CC0 is applied only when the
individual package explicitly says so after review. It must never be applied
to Templot-derived, third-party, unknown, or mixed-rights material by
assumption. CC0 does not replace the separate design, patent and trade-mark
review, and it cannot grant rights held by somebody else. Raw scans, CAD
files, drawings, and photographs retain their own separately recorded terms
and need not be distributed with a definition.

Code contributed to TrackTemplateMacro remains GPL-3.0-or-later unless a file
states an accepted compatible alternative. Prospective contributions require
the unmodified DCO 1.1 sign-off and the separate data/evidence declaration in
[`CONTRIBUTING.md`](../CONTRIBUTING.md). A data contributor must confirm that
they created, lawfully measured, or have authority to contribute the material
under the package's stated terms, and must disclose rather than conceal an
upstream table, CAD model, drawing or other third-party source. An attribution
condition is not automatically disqualifying when the production path records
and satisfies it and the licence otherwise permits the declared commercial/
publication use. A package containing `NC`, `NOASSERTION`, reference-only,
unresolved, or otherwise incompatible dependencies cannot qualify for the
project-cleared release-candidate path.

## Templot compatibility adapter

Templot compatibility, if implemented, is an optional outward adapter:

```text
project-cleared evidence
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

No package or output may receive `project-cleared` status until its machine-
readable dependency manifest has been generated and passes the repository
validator with `--require-project-cleared`. This is an immediate fail-closed
project gate, not a future documentation aspiration. The existing B14/B15 CSV
production manifest is a legacy artifact inventory and does not by itself
satisfy this dependency/project-status gate.

Dependency manifests must identify:

- generating program/version and canonical-model signature;
- every chair-definition/package identifier, version, classification, and
  licence expression;
- external or restricted material deliberately embedded in the output;
- unresolved or reference-only dependencies; and
- the resulting project-control status.

For every output-affecting dependency, `project-cleared` requires permitted
access and production-output use, plus permitted or reasoned-not-applicable
adaptation. The declared-use list additionally requires explicit permitted
redistribution, commercial use and publication results when those uses are
claimed; one permission cannot stand in for another.

The permitted project statuses are:

| Status | Project meaning |
| --- | --- |
| `project-cleared` | All known dependencies have passed the project's documented provenance, licence, declared-use and non-copyright-rights checks for the stated use, with required conditions recorded; this is an internal release gate, not legal advice or a guarantee that no third-party rights exist |
| `restricted` | A recorded licence or right prevents the declared intended use or imposes a relevant condition that the production/publication path has not satisfied |
| `reference-only` | Material may be used to compare or validate locally but not as a production/publication dependency |
| `unknown` | Ownership, source, licence, output effect, or redistribution status is unresolved |

No current B14/B15 output receives `project-cleared` merely because this policy
was adopted. Until the Phase 1 audit closes, its project-control status is
`unknown` unless a narrower output has its own completed record.

The normative schema is
[`schemas/dependency-manifest-v1.schema.json`](schemas/dependency-manifest-v1.schema.json).
The standard-library validator is run with:

```bash
.venv/bin/python tools/validate_dependency_manifest.py \
  --require-project-cleared path/to/dependency-manifest.json
```

A structurally valid manifest may remain `unknown`, `restricted` or
`reference-only`; omitting `--require-project-cleared` validates the record
without promoting its status. The current deliberately blocked S1 control
record is
[`manifests/s1-chair-pilot.dependency-manifest.json`](manifests/s1-chair-pilot.dependency-manifest.json).

## Non-copyright-rights review

Every dependency and the package/output as a whole record four separate review
areas: `registered_designs`, `unregistered_designs`, `patents`, and
`trade_marks`. Each entry records status, territories, review date, reviewer,
evidence and notes. Permitted status vocabulary includes `not-performed`,
`not-applicable`, `no-known-conflict`, `permission-confirmed`,
`expired-or-lapsed-confirmed`, `potential-conflict`, `unresolved`, and
`professional-review-required`.

`project-cleared` requires a positive or reasoned-not-applicable status with
recorded evidence in all four areas. `No-known-conflict` means only that the
documented project search or assessment found no known conflict in its stated
scope; it is not a non-infringement opinion. A potential conflict or a question
outside the project's competence is recorded and escalated rather than
silently treated as absent.

## Publication and physical-production target

The release-candidate target is a documented path in which a user can create,
print, photograph, publish, exhibit, or use a TrackTemplateMacro-generated
turnout or chair commercially without seeking separate permission from Martin
Wynne merely because this project was informed by Templot. That target is met
only when the actual canonical inputs and embedded output materials qualify as
`project-cleared` for the declared use.

The target does not cover direct reproduction of a Templot PDF, screenshot,
drawing, mesh, data file, logo, or other Templot media output. Such material
retains its own recorded or unresolved status. A photograph or render of a
functional article generated solely from a project-cleared path is a
different case from reproducing the upstream drawing used as a comparison
oracle.

UK law contains a specific provision concerning functional articles made from
design documents, but artistic works and other rights require separate
analysis; the project does not rely on that provision as a blanket clearance.
See [Copyright, Designs and Patents Act 1988, section
51](https://www.legislation.gov.uk/ukpga/1988/48/section/51).

## Scoped Phase 1 lineage audit

Before the project describes ordinary production output as unrestricted or
project-cleared, the relevant audit scope must pass. Work is divided into four
explicit registers so the first reusable chair can progress without pretending
that the complete legacy macro has already been cleared:

1. **First S1 chair release path:** the definition, components, primary
   evidence, derivations, package licence, intended commercial/publication use,
   comparison oracles and non-copyright-rights review.
2. **Core rail and timber path used by S1:** rail-interface facts, timber and
   support inputs, shared profiles, transformations and export boilerplate that
   can affect an S1 package or its outputs.
3. **Other turnout and crossover output:** remaining special-trackwork tables,
   profiles, rules, assets and output paths, each blocked from
   `project-cleared` until its own record passes.
4. **Legacy B14/B15 output:** a bounded historical lineage register retaining
   `unknown`, `restricted` or `reference-only` where evidence is unresolved;
   this legacy audit need not be completed before an independently evidenced
   S1 package can be accepted, but it must close before legacy output is
   advertised as project-cleared.

The tracked implementation for the first two scopes is
[`lineage/phase1-s1-core-lineage.json`](lineage/phase1-s1-core-lineage.json).
It inventories the current B14/B15 S1 approximation and the rail/timber path
that can affect it, links exact source anchors and local comparison-evidence
hashes, and records a disposition, evidence need and owner for every group.
Both scopes are intentionally `blocked`; the register is an auditable account
of what is unresolved, not a positive rights or production decision. Its
status may change only with the evidence and acceptance required below, never
merely by editing the JSON.

For each applicable scope the project must:

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
6. maintain and test the machine-readable dependency/project-status manifest;
   and
7. obtain explicit owner acceptance of the first S1 package's evidence,
   licence, intended commercial/publication use and non-copyright-rights record
   before implementation.

Phase 1 must fully classify the first two scopes or leave the S1 pilot visibly
blocked. For the third and fourth scopes it must establish the bounded register,
current status, named owner and later release gate; unresolved legacy breadth
does not become an implicit assertion of clearance. The release and output
validators remain fail-closed for every individual package or output.

The audit may preserve Templot as a local numerical and geometric oracle. It
does not require disguising the project's source-informed history or removing
lawfully used GPL source. Its purpose is to ensure that validation evidence is
not mistaken for the rights basis of canonical production data.

## Acceptance record

The project owner explicitly accepted this source/data/output boundary and
asked for its implementation on 2026-07-20. The later red-team review prompted
the `project-cleared` terminology, immediate manifest gate, non-copyright-
rights fields, contributor declaration and scoped audit added here. Those
amendments are implemented for owner review within the accepted direction;
they do not claim professional legal review or retroactively alter the status
of B14/B15 output.
