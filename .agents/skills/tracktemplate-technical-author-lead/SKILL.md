---
name: tracktemplate-technical-author-lead
description: Manage the complete TrackTemplate technical-document lifecycle. Use automatically for new or materially changed canonical technical prose and maintenance of controlled technical documents.
---

# TrackTemplate Technical Author Lead

## Purpose

Act as the Technical Author Lead. Manage one technical document through its
complete technical-document lifecycle. Keep the work finite and based on a
document need.

The canonical
[Technical Documentation Management Plan](../../../reference/ENGINEERING_POLICY.md#technical-documentation-management-plan)
owns the technical-document lifecycle. The
[Technical Documentation Profile](../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile)
owns controlled writing. The
[technical-term register](../../../reference/TERMINOLOGY.md#asd-ste100-project-terminology)
owns technical terms.

## Authority boundary

The Technical Author Lead owns these workflow responsibilities:

- Identification and classification of the document need.
- Planning of documentation work.
- Authoring and delivery of the complete candidate.
- Coordination of maintenance for controlled technical documents.
- Coordination of supersession, retirement, and preservation.

The applicable technical or governance owner owns the controlled meaning. The
Technical Author Lead has no authority over that controlled meaning. The lead does not
own terminology, the linguistic verdict, the validation result, or acceptance
of the controlled baseline.

Publication, merge, supersession, retirement, and deletion need their applicable
authority. This skill does not supply that authority.

## Identify the need and document class

First, compare the need with current controlled documentation. Select one
result:

- Make a new technical document.
- Make a material change to an existing technical document.
- Make a non-material correction.
- Make no documentation change.

If an existing canonical owner is the correct location, use it. Do not make
a new document for information that already has an owner.

Record the classification items that apply:

- Canonical status and document type.
- Canonical owner and subject owner.
- Issue 9 applicability.
- Legacy status and last accepted review state.
- Exact-content exclusions.
- Review, validation, and publication boundaries.

## Plan the document work

Before you author the candidate, make sure of these items:

- Purpose and intended user.
- Necessary controlled meaning and its owner.
- Applicable canonical authorities and source information.
- Approved terminology.
- Bounded scope of the document and the change.
- Issue 9, review, and validation requirements.
- Expected result for the controlled technical document.

Use the smallest intervention that satisfies the need. Preserve unrelated
accepted prose and frozen historical evidence.

## Procedure for the exact candidate

For new or materially changed canonical technical prose, use this sequence:

> understand once → write once → check once → improve once → freeze once →
> review once → validate once → finish

Get the controlled meaning from its canonical owner. Before you author the
candidate, resolve each technical term. Before source retrieval or candidate
work, use this command:

`.venv/bin/python tools/development_toolchain_preflight.py --stage documentation`

If the development-toolchain preflight does not pass, stop before you author
the candidate. Before you author affected logical units, use the
[local STE retrieval interface](../../../reference/external/asd-ste100/README.md#local-retrieval-interface).

The check step examines meaning, ownership, terminology, exact content, links,
and deterministic pre-check results. It is not a Documentation Review. Apply
TT-DOC-001, TT-DOC-002, and D-GOV-015 exactly during the procedure.
Before freeze, apply one complete improvement pass.

Only with Git authority from the enclosing workflow, freeze one clean exact
candidate. After freeze, use one independent
[`$tracktemplate-documentation-review`](../tracktemplate-documentation-review/SKILL.md).

Only if the verdict permits exact corrections, apply them one time. Then do one
final deterministic validation. A `BLOCKED` verdict is terminal for that exact
candidate. Do not do a second Documentation Review.

To finish the work within the frozen review scope, supply these results:

- Exact candidate.
- Documentation Review.
- Final validation.
- Limitations.
- Necessary owner decision.

Green final validation ends this documentation cycle. Do not send the document
to another documentation, quality, publication, wording, or semantic review.
Do not report these results as project acceptance.

Continuous integration can check the final bytes. It cannot start another
Documentation Review, correction pass, or linguistic improvement cycle.

## Control the baseline and availability

After the Documentation Review, permitted adjustment, and final validation,
manage the applicable acceptance procedure. Record only the durable identity
and authority specified by the TDMP. Then manage repository integration. Do
not make a second database for document management.

Make the accepted document current and available through its normal route.
Make sure that a user can identify these items:

- Current status.
- Canonical owner.
- Accepted baseline.
- Material limitations.

## Maintain and change documents

Start maintenance only for a document need. Do not periodically reopen
accepted unchanged prose for linguistic improvement.

Compare each proposed change with the controlled baseline. For a material
change, use the complete procedure above. Limit its review to the necessary
complete logical units that Git derives.

For a non-material correction, use the applicable change level and validation.
If the meaning or authority becomes material, reclassify the change.

## Manage supersession and retirement

Before supersession, identify the accepted replacement authority. Show which
necessary current information was retained or deliberately replaced. Update
references. Prevent the earlier document from appearing current.

Before retirement, get evidence that the document owns no necessary current
information. Record where its information went or why it no longer applies.
Where necessary, keep historical evidence.

The applicable subject and change authorities make these decisions. Preserve
the old document's historical meaning. Retirement does not authorise deletion.

## Handoff

Report these results:

- Document need and selected result.
- Classification, owners, bounded scope, and source information.
- Planned and completed steps of the technical-document lifecycle.
- Exact candidate and controlled baseline, where they exist.
- Documentation Review and validation results.
- Publication or availability result.
- Maintenance, supersession, retirement, or preservation result.
- Each limitation and owner decision that is still necessary.

Without a material need from the applicable change-control authority,
do not reopen a complete technical-document lifecycle.
