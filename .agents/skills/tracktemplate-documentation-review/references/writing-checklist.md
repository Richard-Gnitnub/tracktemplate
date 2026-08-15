# TrackTemplate documentation writing checklist

First, select the document class. Identify its canonical responsibility. Then,
apply this checklist.

Apply the canonical [Technical Documentation Profile](../../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile).
For STE-governed prose, use the official ASD-STE100 Issue 9 standard that the
profile identifies. Also use the approved project terms in
[`reference/TERMINOLOGY.md`](../../../../reference/TERMINOLOGY.md#asd-ste100-project-terminology).

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
