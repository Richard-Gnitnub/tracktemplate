# ASD-STE100 Issue 9 local reference

Status: **canonical local official source and STE lookup procedure only.**

## Local reference

Put the official ASD-STE100 Simplified Technical English, Issue 9 PDF at:

`reference/external/asd-ste100/ASD-STE100_ISSUE9.pdf`

ASD has the copyright for this external reference. Do not commit the PDF to
the TrackTemplate repository. Get the official document from the
[ASD Simplified Technical English Maintenance Group](https://www.asd-ste100.org/).
The official site records Issue 9, dated 2025-01-15, and supplies the
[official Issue 9 PDF](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf).

Reviewers use the local file for documentation review and linguistic
conformance assessment. The PDF is not necessary for TrackTemplate product
execution or normal repository CI. The PDF is not a canonical TrackTemplate document. The
[TT-DOC-001 profile](../../ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile)
and [TT-DOC-002 decision](../../current/PHASE_EVIDENCE.md#tt-doc-002-uk-english-spelling-correction-panel)
are the TrackTemplate project authority.

## Official source sequence

Use official sources in this order for an ASD-STE100 conformance review:

1. Use the local official PDF when it is available at the path above.
2. If the local PDF is absent, use the official ASD/STEMG Issue 9 source when
   network access is available.
3. Do not use a third-party summary, search-result text, blog, or derived
   guidance as normative conformance evidence.

The review record must report which official source the reviewer used. If
neither official source is available, do not claim that the prose is
ASD-STE100 Issue 9 conforming. Work that does not need linguistic conformance
assessment can continue.

## Source identity and copyright boundary

[`source-manifest.json`](source-manifest.json) records data for an exact check
of source identity. It includes the Issue 9 filename, date, page count, byte size,
and SHA-256 identity. It also records the source-derived index identity. Review
a new source identity before the manifest changes. The STE lookup does not
accept a different source as an automatic update.

[`retrieval-index.json`](retrieval-index.json) contains rule identifiers, rule family
metadata, topic tags, and source locations. It contains no complete
source text for a writing rule or complete STE dictionary. The retrieval index
has no authority to change full applicability. The
[Technical Documentation Profile](../../ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile)
owns full applicability.

The PDF and its source material have external copyright. Keep them local. Do
not add them to version control.

The ignored `.cache/` directory contains the
derived cache. The derived cache contains only STE dictionary metadata,
writing rule source locations, source metadata, and technical-term status. It
does not keep source page text, the complete STE dictionary, or complete
extracted source text. Source mode extracts one source page from verified source bytes in memory.
It returns only a bounded source excerpt.

The source identity is proof/provenance. It does not give a licence to
reproduce or supply ASD source material. TrackTemplate has no positive ASD
permission or eligibility evidence. Thus, the rights state stays **unknown**.
Do not publish the PDF, derived cache, bounded source excerpts, or extracted
source text as TrackTemplate material.

Get a professional rights review or ASD permission before a positive rights claim
about reproduction or supply. The canonical record is
[`PROVENANCE.md`](../../PROVENANCE.md#asd-ste100-issue-9-reference).

## Local retrieval interface

The local interface is [`tools/ste100_lookup.py`](../../../tools/ste100_lookup.py).
It uses local `pdftotext` as a development tool during a rebuild. It reads the
authorised source PDF one time. It calculates the source identity from those bytes. It
sends only verified source bytes to the PDF extractor.

It records the PDF extractor path, file owner, file mode, version, and SHA-256
identity. It also validates the source-derived index identity. It does not add
a TrackTemplate product runtime dependency.

Rebuild and validate the ignored derived cache with:

```bash
.venv/bin/python tools/ste100_lookup.py rebuild
.venv/bin/python tools/ste100_lookup.py validate
.venv/bin/python tools/ste100_lookup.py status
```

Each command validates the source byte size and source identity before it uses
derived data. A lookup query stops if the source is missing or its identity
changes. It also stops if derived cache metadata is different. It stops if the
source-derived index identity or cache schema version is different. Source mode
also stops if the PDF extractor identity is different. The tool does not rebuild
the stale cache without the rebuild command.

Follow the diagnostic. Put the
authorised PDF at the canonical path or use the `rebuild` command.

Use concise lookup output:

```bash
.venv/bin/python tools/ste100_lookup.py word install
.venv/bin/python tools/ste100_lookup.py word "plain line" --part-of-speech noun
.venv/bin/python tools/ste100_lookup.py rule 6.3
.venv/bin/python tools/ste100_lookup.py topic terminology
.venv/bin/python tools/ste100_lookup.py review descriptive-prose
```

Add `--source` to a word lookup or rule lookup only when a bounded source
excerpt is necessary. Add `--verbose` to a topic lookup query only when you must
read all rule families for its topic tag. A query does not show the complete
source text.

Word lookup examines the TrackTemplate technical-term register first. An
approved technical-term result gives its technical-term category and term
meaning. Always compare a technical term in the logical unit with the term
meaning that the technical-term register gives. After you identify the
technical-term category, use
`--part-of-speech`. If its category differs from the register, do not approve
the technical term. Do not approve a term that is missing from the
technical-term register. The lookup then classifies recognised STE vocabulary,
a dictionary-inspection candidate, or unresolved terminology. The tool cannot
add or approve a technical noun or technical verb.
[`TERMINOLOGY.md`](../../TERMINOLOGY.md#asd-ste100-project-terminology) is the
technical-term register.

## Pre-check and review receipt

Use the deterministic pre-check with one content category:

```bash
.venv/bin/python tools/ste100_lookup.py precheck DOCUMENT --category descriptive
```

The pre-check reports sentence length, controlled vocabulary, technical-term
status, and construction candidates. Each bounded result reports its total
count, shown count, and truncation status. Add `--verbose` to return all
deterministic findings. It is not a conformance review. No finding and no empty
result shows conformance. A `PASS` command result also does not show conformance.

After a reviewer examines the complete applicable requirement set, the tool can
write an ignored review receipt. It uses `tmp/ste100-review-receipts/`.
For changed prose, bind the receipt to one previous Git commit:

```bash
git show BASELINE:DOCUMENT | \
  .venv/bin/python tools/ste100_lookup.py receipt DOCUMENT \
    --baseline-stdin --baseline-revision BASELINE \
    --category descriptive --full-applicability-considered
```

Use the complete commit SHA for `BASELINE`. The receipt records the canonical
document from the previous Git commit and from the worktree. It also records
the changed canonical prose that the pre-check examines. The receipt records
source and profile identities, targeted retrieval, exact-content exclusions,
technical-term status, and unresolved terminology. It is not an external
certification or endorsement. Do not keep all review receipts for usual work.
Keep one only when project authority makes this necessary.

For a material change to canonical prose, first freeze a clean Git commit. Use
the complete SHA for its accepted baseline:

```bash
.venv/bin/python tools/ste100_lookup.py freeze-review \
  --baseline-revision BASELINE --author-id AUTHOR_ID
```

The command writes a content-addressed scope file under
`tmp/ste100-review-scopes/`. Review results use
`tmp/ste100-review-results/`, and accepted-state proposals use
`tmp/ste100-review-state-proposals/`. The command compares the source with the manifest
and derives scope from the accepted document identities and Git. It excludes
untouched legacy documents. It includes the complete document for a first edit
and only changed complete logical units after an accepted document identity.

Give that frozen scope to one independent Documentation Reviewer. The reviewer
must use the official source and return one complete `ACCEPT`,
`APPROVED_WITH_EXACT_CORRECTIONS`, or `BLOCKED` result. For
`APPROVED_WITH_EXACT_CORRECTIONS`, the result must contain all exact replacement
wording. Record the result with:

```bash
.venv/bin/python tools/ste100_lookup.py record-review SCOPE RESULT
```

For a `BLOCKED` result, stop for the owner. The command gives no accepted-state
proposal. For `ACCEPT`, use the proposed document-level review state. For
`APPROVED_WITH_EXACT_CORRECTIONS`, apply each exact replacement once against
its verified preimage, and use the proposed state. Do not invent other prose.
Do not run a second Documentation Review.

Commit the reviewed content and `reference/ste-review-state.json`. Then run the
one final deterministic validation:

```bash
.venv/bin/python tools/ste100_lookup.py final-validate SCOPE RECEIPT
```

Require the `TRACKTEMPLATE_STE100_FINAL=` success sentinel. This command proves
source, candidate, scope, receipt, accepted-state, and final-content identity.
It detects unreviewed mutation. It does not judge linguistic conformance.

The usual agent route and bounded conditions for complete-source inspection are
in the
[TT-DOC-001 workflow](../../AGENT_WORKFLOWS.md#tt-doc-001-workflow-integration).
Targeted retrieval changes the source text that the agent reads for this task.
It does not narrow the applicable Issue 9 requirement set.
