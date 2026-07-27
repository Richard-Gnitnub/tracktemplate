---
name: tracktemplate-railway-standards
description: Research, compare and admit traceable railway gauge, wheel-and-track, clearance, rail, switch-and-crossing, timbering or related prototype standards for TrackTemplate. Use before adding or changing a standards-derived dimension, tolerance, constraint, default, terminology claim or production rule.
---

# TrackTemplate railway standards

## Outcome

Produce a source-cited standards assessment or an admission-ready fact record
whose applicability, units, tolerance, revision, provenance and rights status
are explicit. Do not make the skill or an agent's memory a source of railway
authority.

## Responsibility boundary

- Read `reference/PROJECT_PLAN.md` and the canonical owner of the affected
  requirement, data contract or terminology before acting.
- Read `reference/LICENSING_BOUNDARIES.md` and `reference/PROVENANCE.md`.
- Use `$tracktemplate-license-analysis` before retaining or distributing
  third-party standards content, tables, drawings or datasets.
- Use `$tracktemplate-railway-mathematics` to derive or implement calculations
  from accepted standards inputs.
- Use `$tracktemplate-api-design` when an admitted value changes a public,
  stored, package or interchange contract.

This skill gathers and qualifies evidence. It does not accept a product
requirement, alter phase scope or confer `project-cleared` status.

## Standards workflow

1. **Define the exact question.** Name the dimension, relationship, tolerance
   or rule and the operator workflow or output it could affect. Distinguish
   nominal track gauge from check gauge, flangeway, wheel back-to-back,
   clearances and other coupled constraints.
2. **Bound applicability.** Record the issuing body, railway or jurisdiction,
   prototype or model practice, gauge family, scale, wheel-and-track system,
   era, construction method and intended use. Mark every unknown.
3. **Retrieve primary evidence.** Use the exact authoritative standard,
   drawing, specification or measurement source. Record title, identifier,
   edition/revision, publication date, clause/table/figure locator, retrieval
   date and source URL or controlled-file identity. Use secondary sources only
   to locate or corroborate primary evidence.
4. **Classify rights and provenance.** Separate individual engineering facts
   and methods from protected wording, drawings, tables, selection and
   arrangement. Preserve access, quotation, adaptation and redistribution
   limits; summarise and cite rather than copying a standard.
5. **Normalise without erasing origin.** Retain the exact source value,
   notation, units, stated tolerance and rounding. Record conversions,
   assumptions and uncertainty separately with reproducible arithmetic.
6. **Check the system of constraints.** Test related limits together and report
   contradictions, mixed revisions, incompatible wheel/track regimes and
   missing companion requirements. Do not admit one convenient dimension in
   isolation when its validity depends on another.
7. **Propose the narrow project effect.** Identify the canonical document,
   schema or data record that could own an accepted fact. Route terminology to
   `reference/TERMINOLOGY.md`, strategic requirements to
   `reference/ARCHITECTURE.md`, live timing to `reference/PROJECT_PLAN.md` and
   evidence identity to the provenance owners.
8. **Define disproof evidence.** Specify the calculation, dimensional,
   compatibility and production-output checks required before implementation
   or acceptance.

## Fail-closed rules

- Do not guess an unavailable dimension, tolerance, edition or railway term.
- Do not average conflicting standards, silently select the newest edition or
  combine values from incompatible systems.
- Do not turn a nominal gauge label into a complete wheel-and-track standard.
- Do not infer tolerance from displayed decimal places or a scaled drawing.
- Do not promote Templot reference data, media output or an unclassified value
  collection into canonical production input.
- Do not copy a protected table merely by relabelling its cells as facts.
- Do not describe research, a calculation or a passing test as project-owner
  acceptance.

## Report

Report the exact standards question, applicability envelope, primary sources
and freshness, extracted facts in original units, conversions and uncertainty,
rights/provenance classifications, conflicts and unknowns, proposed canonical
owner, implementation effect, required evidence and every owner or
professional-review decision still outstanding.
