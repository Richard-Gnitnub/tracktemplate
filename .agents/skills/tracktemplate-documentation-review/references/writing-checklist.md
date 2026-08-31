# TrackTemplate documentation writing checklist

First, identify the document class and its canonical owner. Then, use this
checklist.

Use the [Technical Documentation Profile](../../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile).
Use ASD-STE100 Issue 9. Use the official source that the Technical Documentation
Profile identifies. Use the technical terms in
[`reference/TERMINOLOGY.md`](../../../../reference/TERMINOLOGY.md#asd-ste100-project-terminology).

## Documentation Review for ASD-STE100 Issue 9

Use this procedure for each complete logical unit in the frozen review scope:

1. Identify the document class.
2. Identify the content category.
3. Identify all applicable Issue 9 requirements.
4. Identify each word as controlled vocabulary or a technical term.
5. For controlled vocabulary, examine its controlled meaning and part of speech.
6. Examine each applicable requirement in Rule 1.
7. Use the wording for each technical term in the technical-term register.
8. Examine each technical term for its technical-term category.
9. When no technical term is necessary, use approved STE vocabulary.
10. If the controlled vocabulary does not identify the TrackTemplate item, add a technical term.
11. Identify the person, tool, or system that does each operation.
12. Make sure each operation has the correct person, tool, or system.
13. For each pronoun, make sure the noun to which it refers is clear.
14. Name the correct item for each state and result.
15. Examine each noun group against Rule 2.
16. In a procedure, use a different instruction for each operation.
17. In a procedure, put each condition before its instruction.
18. Use Rules 3, 4, 5, 6, 7, and 8 to examine sentence construction.
19. Use Rules 3, 4, 5, 6, 7, and 8 to examine paragraph structure.
20. Examine all other applicable Issue 9 requirements.
21. Compare each evidence claim with its source.
22. Identify every linguistic or semantic finding.
23. Resolve all unresolved terminology in the verdict.
24. For each BLOCKED finding, record its exact path and frozen logical-unit
    identity. Also record the finding and applicable formal Issue 9 rule
    identifiers.
25. Make sure that the set contains all BLOCKED findings. For a `BLOCKED`
    verdict, make sure that this set is not empty.
26. Examine the complete frozen logical unit before you give the verdict.

A deterministic pre-check can identify source text for review. The STE lookup can
give source material. The pre-check does not give a result from a conformance
review. The STE lookup also does not give a result from a conformance review.
The independent Documentation Reviewer completes the conformance review. Give
one complete `ACCEPT`, `APPROVED_WITH_EXACT_CORRECTIONS`, or `BLOCKED` verdict.
For `APPROVED_WITH_EXACT_CORRECTIONS`, give all exact replacement wording in
the same review. Identify each path, byte range, frozen preimage, and
replacement. Do not defer or add wording later. Do not run a second
Documentation Review.

The STE lookup validates source, exact candidate, frozen review scope, receipt,
accepted state, and final-content identity. It validates exact reviewed
corrections against frozen preimages and derives the expected final bytes. The
implementing agent applies those corrections once. The lookup does not examine
canonical prose for conformance or change the verdict. After the review or
correction, one final deterministic validation proves that no unreviewed
mutation occurred. A remaining failure returns to the owner.

## Ownership and structure

- Duplicated facts have one canonical owner. Other documents refer to it.
- Live status appears only in `/reference/PROJECT_PLAN.md`. A named current
  phase-evidence document can also record evidence.
- The document does not copy detail from another canonical owner.
- Background does not hide conclusions or applicable requirements.
- Headings are necessary and describe distinct content.
- Paragraphs do not cover several unrelated subjects.
- Generic summaries do not repeat the next section.
- The owner view for a substantial cycle agrees with canonical records.
  Technical provenance follows it. The view does not establish project state.

## Accuracy and evidence

- Each claim has a specific bounded scope and evidence for the claim.
- The document does not say that the project did planned work.
- The document does not describe headless validation as GUI acceptance.
- The document does not rewrite historical records with later knowledge.
- Exact validator-required wording stays intact where necessary.
- A material edit does not remove or weaken controlled terminology to make the
  wording short.
- Pending, Evidenced, Accepted, Blocked, Finding, Limitation, Unknown, and
  Decision required are distinct in governance wording.
- The document keeps facts, evidence, inferences, recommendations, and owner
  decisions distinct.
- The conformance record names the full logical unit and the official
  Issue 9 source.
- An automatic validator result does not replace the conformance review.
- Exact machine data and externally controlled information stay exact when
  necessary.

## Concision and tone

- The material edit removes repeated introductions and conclusions.
- The wording has one warning for each warning scope.
- The material edit removes unnecessary words and praise of the writer.
- The material edit removes unnecessary wording without an arbitrary
  word-count target.
- Use ASD-STE100 Issue 9 for canonical prose. TrackTemplate uses UK English in
  that canonical prose. Do not change other Issue 9 requirements.

## Do not shorten when controlled meaning would be lost

Do not shorten wording when doing so would remove the following information.

- exact evidence.
- qualification limits.
- provenance or licence status.
- test conditions.
- risk ownership or deadlines.
- objective closure criteria.
- stable identifiers.
- railway controlled meaning.
- compatibility requirements.
- validator-required wording.

## Post-edit survival check

- Load-bearing names, paths, commands, identifiers, classifications and
  controlled railway terms still appear where required.
- Incoming and outgoing links remain valid after headings, sections or files
  are moved.
- Material removed from one document was either unnecessary or relocated to
  its canonical owner.

## Removal review

Report proposed deletions separately when they can change history, law, safety,
licence, or the controlled meaning of evidence. Do not remove that material
with an automatic rewrite.
