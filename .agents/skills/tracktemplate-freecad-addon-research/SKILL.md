---
name: tracktemplate-freecad-addon-research
description: Extract current, source-cited FreeCAD Addon guidance for TrackTemplate from the official Addon Academy and related first-party sources. Use when researching workbench or addon structure, package.xml, commands, Qt/PySide, preferences, custom document objects or ViewProviders, local development and testing, dependencies, licensing, Addon Index publication, compatibility, schema migration, maintenance, or another FreeCAD Addon practice before planning or implementing project work.
---

# TrackTemplate FreeCAD Addon research

## Outcome

Answer the exact Addon question with the smallest current first-party source
set, visible source freshness and an explicit TrackTemplate authority boundary.
Do not turn external guidance into an accepted project decision.

## Retrieval workflow

1. State the exact FreeCAD Addon question and affected TrackTemplate boundary.
2. Read [source routing](references/source-routing.md) and select only the
   relevant Academy guide, topic or demo.
3. Retrieve the selected page from the published Academy and, when exact code,
   metadata or revision matters, inspect its GitHub source at the current
   default-branch commit.
4. Read [extraction contract](references/extraction-contract.md) and record the
   source URL, source path, retrieval date, revision when available, and source
   kind before drawing conclusions.
5. Cross-check a time-sensitive or runtime-specific claim against the relevant
   first-party FreeCAD source, API documentation, Addon Index or template.
6. Read [TrackTemplate mapping](references/tracktemplate-mapping.md) and compare
   the finding with the canonical project owner. Report agreement, conflict or
   missing authority; never silently overwrite the project rule.
7. Return a concise evidence-backed answer or implementation input. Separate
   upstream guidance, repository fact, inference and project decision.

## Retrieval rules

- Prefer the published Academy for navigation and prose, and GitHub source for
  exact paths, code, licence notices and revision evidence.
- Treat the Academy as evolving guidance: its own landing page says porting is
  still in progress.
- Use the page that owns the subject. Do not load every guide or copy the
  Academy into repository context.
- Cite the exact page or source file used. Record a commit SHA when the answer
  depends on code, manifest syntax, quality criteria or a changing example.
- Distinguish a recommendation, supported legacy option, quality requirement,
  runnable demo and FreeCAD runtime/API fact.
- Inspect the applicable file-local licence before copying code or prose.
  Summarise and link by default.
- Never infer qualified-host compatibility from current upstream guidance.
  TrackTemplate runtime qualification remains project-controlled.
- Do not describe an Academy example as production-ready without the
  TrackTemplate validation, recovery, persistence, performance and provenance
  evidence required for the affected boundary.

## Output contract

Report:

1. **Question and boundary** — the precise Addon concern and affected
   TrackTemplate layer or ontology concept.
2. **Sources and freshness** — first-party URLs, source paths, retrieval date
   and revision where material.
3. **Extracted guidance** — the minimum facts that answer the question,
   preserving qualifications and legacy/current distinctions.
4. **TrackTemplate interpretation** — the canonical owner, agreement or
   conflict, and any implementation consequence.
5. **Uncertainty** — missing upstream coverage, version ambiguity, unverified
   runtime behaviour or a decision still owned by the project owner.

Do not present research as implementation, validation or project acceptance.
