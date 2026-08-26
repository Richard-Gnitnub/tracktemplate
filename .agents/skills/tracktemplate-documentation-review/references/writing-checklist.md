# TrackTemplate documentation writing checklist

First, select the document class. Identify its canonical responsibility. Then,
apply this checklist.

Apply the canonical [Technical Documentation Profile](../../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile).
For STE-governed prose, use the official ASD-STE100 Issue 9 standard that the
profile identifies. Also use the approved project terms in
[`reference/TERMINOLOGY.md`](../../../../reference/TERMINOLOGY.md#asd-ste100-project-terminology).

## Author-side assurance for ASD-STE100 Issue 9

Apply these checks to each new logical unit. Before you freeze an exact
candidate, also apply them to each logical unit with a material edit:

- Identify the document class for the logical unit.
- Identify the content category for the logical unit.
- Identify the applicable rule set.
- For each term use, identify the term use as ordinary vocabulary or a technical
  term.
- For each use of ordinary vocabulary, make sure that the approved meaning is
  correct.
- For each use of ordinary vocabulary, make sure that the approved part of
  speech is correct.
- For each technical term, use its registered form.
- Use a shorter form only if the technical-term register contains it.
- Do not add a technical term only to keep the wording.
- Do not use a technical noun as a technical verb.
- For each operation, identify the logical agent.
- The logical agent must be a person, tool, or system.
- If the logical agent is known, use the logical agent as the grammatical
  subject.
- Make sure that each pronoun has one clear pronoun antecedent.
- Identify the item that has each condition.
- Identify the item that has each result.
- Use the identified item as the grammatical subject.
- Examine each multi-word noun.
- Do not use more than 3 words in each multi-word noun.
- If a registered form has more than 3 words, use the registered form.
- In a procedure, give one instruction in each sentence.
- In a procedure, give one operation in each work step.
- If the work step has simultaneous actions, the work step can contain those
  operations.
- If an immediate result occurs, the work step can contain the operation and
  immediate result.
- If a condition must be known first, put the condition before its instruction.
- Resolve each dictionary-inspection candidate.
- Resolve all unresolved terminology.
- Resolve each applicable finding.
- If unresolved terminology stays, do not freeze an exact candidate.
- After the last wording change, review the complete logical unit against the
  applicable rule set.

Use the deterministic pre-check to find review candidates. Use the STE lookup
to retrieve source material. These tools give no conformance review result.
The author must examine term meaning and technical-term category. The author
must also examine sentence grammar and the logical agent. A deterministic
pre-check does not complete the author-side assurance.

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
