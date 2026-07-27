---
name: tracktemplate-license-analysis
description: Analyse licence, provenance and rights evidence for TrackTemplate source, dependencies, data, media, chair packages and generated outputs. Use before admitting or distributing third-party material, changing licence expressions or notices, assessing dependency compatibility, or claiming an intended output use.
---

# TrackTemplate licence analysis

## Outcome

Produce a source-cited, scope-bounded compliance assessment that preserves
unknowns and identifies decisions requiring the project owner or professional
legal review. This skill does not provide legal advice or confer legal
clearance.

## Authority

Read both `reference/LICENSING_BOUNDARIES.md` and `reference/PROVENANCE.md`
before analysis.

- The first document owns project classifications, admission rules, manifest
  statuses, intended-use checks and non-copyright-rights review.
- The second records source identity and licence evidence actually found.
- `reference/PROJECT_PLAN.md` owns timing, live risks and acceptance gates.
- `LICENSE`, `NOTICE.md`, contributor declarations, package manifests and
  upstream terms are evidence; none silently overrides the project owners.

Do not replace these controls with a generic permissive/copyleft matrix.

## Scope the legal question

Identify:

1. the exact item, version, revision, file, component or field;
2. whether it is source expression, engineering method/fact, project
   measurement/derivation, user design, external evidence, reference data,
   media or generated output;
3. how it enters or interacts with the project;
4. the proposed access, modification, combination, distribution, publication,
   commercial or production-output use;
5. the artifact and territory being assessed; and
6. every direct, transitive, embedded or output-affecting dependency.

An analysis for local comparison does not answer a distribution or commercial
use question.

## Evidence workflow

1. **Inventory exact evidence.** Record origin, creator, acquisition date,
   locator, version/revision, hashes, notices and complete applicable terms.
2. **Use primary sources.** For current legal or licence facts, retrieve the
   authoritative licence text, upstream repository/release terms, official
   registry or legislation. Record retrieval date and revision. Do not rely on
   package metadata alone when it conflicts with shipped terms.
3. **Represent expressions accurately.** Use canonical SPDX identifiers and
   `AND`, `OR`, `WITH`, `LicenseRef-*` or `NOASSERTION` according to the
   [official SPDX expression guidance](https://spdx.dev/learn/handling-license-info/).
   Preserve copyright notices separately.
4. **Classify at the smallest useful boundary.** A repository, archive or chair
   package may contain source, data, media and components with different terms.
5. **Map obligations to the actual use.** Record attribution, notice, source
   offer, modification, relinking, disclosure, redistribution or other
   conditions supported by the text and integration facts.
6. **Assess other rights separately.** Preserve the project's design, patent,
   trade-mark, database, contract and contributor-authority checks. A copyright
   licence result does not settle them.
7. **Propagate status.** Update or propose the applicable provenance record and
   dependency manifest without promoting `unknown`, `reference-only`,
   `restricted` or `NOASSERTION` material.

## Finding states

Use one supported state for each question:

- `CONFIRMED` — primary evidence directly supports the bounded fact.
- `CONDITION` — the use is contingent on a recorded obligation or permission.
- `CONFLICT` — recorded terms and the declared use cannot both be satisfied on
  the available evidence.
- `UNKNOWN` — identity, terms, relationship, output effect or permission is
  missing or ambiguous.
- `PROFESSIONAL_REVIEW_REQUIRED` — the decision depends on a legal
  interpretation or rights search outside project competence.

These findings inform the canonical project statuses; they do not replace
them. Only the accepted manifest gate may produce `project-cleared`, and that
term remains an internal control status rather than a legal opinion.

## Fail-closed rules

- Do not use “copyleft infection” as analysis or assume that a licence family
  alone determines the result.
- Do not make categorical linking, derivative-work, database-right, design,
  patent or trade-mark conclusions without supported authority.
- Do not assume program licensing automatically covers ordinary generated
  output or that accessible material may be copied or redistributed.
- Do not relabel a table as isolated facts, external work as project-authored,
  AI output as provenance-free or source-informed work as clean-room.
- Do not apply CC0 or another package licence to rights the project does not
  control.
- Do not remove notices, weaken attribution or convert missing licence evidence
  into a permissive default.
- Treat an upstream version or licence change as a new review boundary.

## Report

Report the exact scope and intended use, evidence inventory, classification,
SPDX expression, conditions, finding states, source/data/media/output
separation, non-copyright-rights status, manifest impact, unresolved questions,
professional-review needs and every claim that remains blocked.
