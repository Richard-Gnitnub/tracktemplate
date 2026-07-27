# Addon guidance extraction contract

Use this record in conversation or working notes. Do not create a durable
repository evidence file unless the finding supports an accepted project
decision or the current phase explicitly requires it.

## Evidence fields

| Field | Required content |
| --- | --- |
| Question | One bounded FreeCAD Addon question |
| Published source | Exact first-party URL |
| Source path | GitHub repository path when available |
| Retrieved | ISO date |
| Revision | Commit SHA when code, syntax or changing criteria matter |
| Source kind | Guide, topic, demo, API/source, template or Addon Index |
| Guidance state | Recommendation, supported legacy option, requirement, example or runtime fact |
| Extracted facts | Minimal paraphrase with necessary qualifications |
| Project owner | Canonical TrackTemplate document |
| Project effect | Confirms, conflicts, informs, or requires a decision |
| Unverified | Version, host, GUI, packaging, licensing or behaviour still needing proof |

## Accuracy checks

- Open the selected page, not only a search result.
- Check whether the page is an index that delegates detail to child pages.
- Preserve words such as “recommended”, “supported”, “required”, “example” and
  version bounds; they change the force of a statement.
- If a claim depends on `package.xml`, a Python import layout, Qt binding,
  FreeCAD object lifecycle or Addon Index criterion, inspect the exact current
  source and record its revision.
- Distinguish an Academy statement from an inference. Name the evidence that
  supports the inference.
- Do not treat absence from an Academy page as proof that FreeCAD does not
  support a behavior.
- If two first-party sources disagree, report both revisions and defer the
  project consequence until the governing runtime or project authority settles
  it.

## Context budget

- Load one route index and the smallest number of leaf pages that answer the
  question.
- Quote only load-bearing syntax or wording; paraphrase the rest.
- Do not copy whole guides, demos or page inventories into the response.
- Link to canonical TrackTemplate documents instead of repeating their policy.
- Keep unrelated Addon lifecycle stages out of the extraction.
