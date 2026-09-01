---
name: tracktemplate-technical-author-lead
description: Author and deliver one complete TrackTemplate technical-documentation candidate from authoritative technical meaning, canonical terminology, documentation policy, and targeted STE retrieval. Use for material canonical technical prose before freeze and one independent Documentation Review. Do not use for technical implementation, the linguistic verdict, or project acceptance.
---

# TrackTemplate technical author lead

## Purpose

Own the authoring and delivery of one complete technical-documentation
candidate. Produce stable prose that is ready for candidate freeze and one
independent Documentation Review.

This skill owns no technical meaning or canonical subject. It also owns no
terminology, documentation policy, linguistic verdict, validation result,
publication, or project acceptance.

## Confirm the authoring boundary

Before drafting:

1. Confirm the exact bounded scope and mutation authority.
2. Get the applicable technical meaning from its canonical subject owner.
3. When a Technical Lead coordinates implementation, require the Technical
   Lead to supply that technical meaning and the preserved non-claims.
4. Read the
   [technical-term register](../../../reference/TERMINOLOGY.md#asd-ste100-project-terminology).
5. Resolve each technical noun and technical verb before drafting. Stop if a
   term is unresolved or its category is incorrect.
6. Identify each affected canonical document and its document class. Read the
   applicable policy in the canonical
   [Technical Documentation Profile](../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile).
7. Use
   [`$tracktemplate-documentation-alignment`](../tracktemplate-documentation-alignment/SKILL.md)
   when a claim must be reconciled with canonical authority.

Do not draft an unresolved technical meaning. Do not approve a technical noun
or technical verb in this skill. Route an unresolved term to the technical-term
register and its project owner.

## Run the authoring preflight

Use the active project Python environment. Run these existing STE lookup
operations before drafting:

```text
.venv/bin/python tools/ste100_lookup.py validate
.venv/bin/python tools/ste100_lookup.py word TERM --part-of-speech noun|verb
.venv/bin/python tools/ste100_lookup.py review descriptive-prose|procedural-prose|safety-prose
.venv/bin/python tools/ste100_lookup.py topic TOPIC
.venv/bin/python tools/ste100_lookup.py rule RULE_ID
```

Require the `TRACKTEMPLATE_STE100=` result for each operation. The `validate`
result must have `status: "verified-source-bound-cache"`. Run one `word`
lookup for each proposed project technical term. Its status must confirm the
term and its correct noun or verb category.

Select at least one applicable `review` category. Then run the targeted
`topic` or `rule` lookups that the result identifies. Stop authoring after a
nonzero process result or `TRACKTEMPLATE_STE100_ERROR=`. Also stop for
unresolved terminology or a category mismatch.

The lookup output changes the official source material that the author reads.
It does not narrow full applicability or give a conformance verdict. Do not
create a persistent authoring packet or a second review-state record.

## Author one complete candidate

Author the complete affected logical units. Coordinate all affected canonical
documents in the same bounded candidate. Use these controls:

- Preserve exact identifiers, commands, paths, hashes, schema values, and
  other exact content.
- Distinguish a fixed syntax identifier from ordinary prose.
- Use canonical TrackTemplate terms for all field values and explanations.
- Keep technical meaning, evidence, validation, review verdict, and owner
  acceptance distinct.
- State that an independent reviewer returns evidence and a verdict. Only an
  explicit project-owner decision gives project acceptance.
- Use an established approved construction when it expresses the same meaning.
- Keep unrelated accepted prose and frozen history unchanged.

Use the deterministic pre-check as an authoring aid when it applies. Resolve
all authoring findings before freeze. A `PASS` result does not show Issue 9
conformance.

## Freeze and deliver

Review the complete diff and confirm one stable candidate. Freeze it only when
the enclosing workflow has Git authority. Then:

1. Derive the frozen review scope from Git.
2. Give the complete scope to one independent
   [`$tracktemplate-documentation-review`](../tracktemplate-documentation-review/SKILL.md).
3. Treat `ACCEPT` as completion-permitting review evidence.
4. For `APPROVED_WITH_EXACT_CORRECTIONS`, apply only the exact replacements
   from that verdict, once, against verified preimages.
5. Treat `BLOCKED` as terminal for that candidate. A new owner instruction must
   establish a materially different lifecycle before more authoring.
6. Run the final deterministic validation after the review or exact correction.
7. Give the exact candidate, validation, verdict, limitations, and unchanged
   authority to the independent quality reviewer.

Documentation Review is read-only. In an
`APPROVED_WITH_EXACT_CORRECTIONS` verdict, the reviewer outputs all exact
replacement wording in that same verdict. The implementing agent applies the
wording. The reviewer never mutates the candidate. A finding creates no repair
authority. Do not run a second Documentation Review.

## Handoff

Report:

- the bounded document scope and canonical owners;
- the source of technical meaning;
- each terminology disposition;
- the STE source identity and targeted lookup operations;
- exact-content exclusions;
- the changed complete logical units;
- the frozen commit and tree, when available;
- the one Documentation Review verdict;
- deterministic validation and independent quality review; and
- every preserved limitation and owner decision still necessary.

Do not present the candidate, a reviewer verdict, or a validation result as
project acceptance.
