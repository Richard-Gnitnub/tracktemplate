# TrackTemplate documentation writing checklist

First, identify the document class and its canonical owner. Then, use this
checklist.

Use the [Technical Documentation Profile](../../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile).
Use ASD-STE100 Issue 9. Use the official source that the Technical Documentation
Profile identifies. Use the technical terms in
[`reference/TERMINOLOGY.md`](../../../../reference/TERMINOLOGY.md#asd-ste100-project-terminology).

## Author-side assurance for ASD-STE100 Issue 9

For each logical unit with a material edit, use this procedure:

1. Identify the document class.
2. Identify the content category.
3. Identify all applicable Issue 9 requirements.
4. Identify each word as controlled vocabulary or a technical term.
5. For controlled vocabulary, examine its approved meaning and part of speech.
6. Examine each applicable requirement in Rule 1.
7. Use the wording for each technical term in the technical-term register.
8. Examine each technical term for its technical-term category.
9. Use approved STE vocabulary when no technical term is necessary.
10. If the controlled vocabulary does not identify the TrackTemplate item, add a technical term.
11. Identify the person, tool, or system that does each operation.
12. Make sure each operation has the correct person, tool, or system.
13. For each pronoun, make sure the noun to which it refers is clear.
14. Name the correct item for each state and result.
15. Examine each noun group against Rule 2.
16. In a procedure, use a different instruction for each operation.
17. In a procedure, put each condition before its instruction.
18. Examine sentence construction under Rules 3 through 8.
19. Examine paragraph construction under Rules 3 through 8.
20. Examine all other applicable Issue 9 requirements.
21. Compare each evidence claim with its source.
22. Record each finding and its disposition.
23. Resolve all unresolved terminology.
24. After the last wording change, review the complete logical unit again.

A deterministic pre-check can identify text for review. The STE lookup can
give source material. The pre-check gives no conformance review result. The STE
lookup also gives no conformance review result. The author completes the
conformance review.

### Temporary author-review worklist

The worklist records only this information for the validation tool:

- Exact candidate and source identity
- Conformance scope for changed prose
- SHA-256 for each path and logical unit
- Applicable review categories
- Findings and their dispositions
- Source for each evidence claim
- Author-side assurance result and unresolved findings
- Read-only challenge result.

For a command result, record the command invocation and working directory.
Record the validation profile and process exit status. Record the actual result.
Record the command-output SHA-256. If the command has a sentinel, record it.

The STE lookup validates the source identity, exact candidate, conformance
scope, and SHA-256 values. It also validates unresolved findings. It validates
each command result against its evidence source. It does not examine prose for
conformance.

Before the author freezes the exact candidate, give the author-review worklist
to a different documentation reviewer. Give the reviewer all changed prose.
Get a read-only challenge. The challenge has no acceptance.

## Ownership and structure

- Duplicated facts have one canonical owner. Other documents refer to it.
- Live status appears only in `/reference/PROJECT_PLAN.md`. A named current
  phase-evidence document can also record evidence.
- The document does not copy detail from another canonical owner.
- Background does not hide conclusions or operative requirements.
- Headings are necessary and describe distinct content.
- Paragraphs do not cover several unrelated subjects.
- Generic summaries do not repeat the next section.
- The owner view for a substantial cycle agrees with canonical records.
  Technical provenance follows it. The view does not establish project state.

## Accuracy and evidence

- Each claim has a specific scope and evidence for the claim.
- The document does not say that the project did planned work.
- The document does not describe headless validation as GUI acceptance.
- The document does not rewrite historical records with later knowledge.
- Exact validator-required wording stays intact where necessary.
- The edit does not remove or weaken controlled terminology to make text short.
- Pending, Evidenced, Accepted, Blocked, Finding, Limitation, Unknown and
  Decision required are distinct in governance text.
- The document keeps facts, evidence, inferences, recommendations, and owner
  decisions distinct.
- The conformance record names the full logical unit and the official
  Issue 9 source.
- An automatic validator result does not replace the conformance review.
- Exact machine data and externally controlled information stay exact when
  necessary.

## Concision and tone

- The edit removes repeated introductions and conclusions.
- The text has one warning for each warning scope.
- The edit removes unnecessary words and praise of the writer.
- The edit removes unnecessary text without an arbitrary word-count target.
- Use ASD-STE100 Issue 9 for STE prose. Use the TrackTemplate UK English
  spelling directive in that prose. Do not change other Issue 9 requirements.

## Do not shorten when meaning would be lost

Do not shorten text when doing so would remove:

- exact evidence;
- qualification boundaries;
- provenance or licensing status;
- test conditions;
- risk ownership or deadlines;
- objective closure criteria;
- stable identifiers;
- railway meaning;
- compatibility requirements;
- validator-required wording.

## Post-edit survival check

- Load-bearing names, paths, commands, identifiers, classifications and
  controlled railway terms still appear where required.
- Incoming and outgoing links remain valid after headings, sections or files
  are moved.
- Material removed from one document was either unnecessary or relocated to
  its canonical owner.

## Removal review

Report proposed deletions separately when they could change historical, legal, safety, licensing or evidential meaning. Do not remove that material through automatic cleanup.
