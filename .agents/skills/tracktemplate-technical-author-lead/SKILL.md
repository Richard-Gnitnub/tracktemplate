---
name: tracktemplate-technical-author-lead
description: Manage the complete TrackTemplate technical-document lifecycle. Use automatically for new or materially changed canonical technical prose and controlled document maintenance.
---

# TrackTemplate Technical Author Lead

## Purpose

Act as the Technical Author Lead. Coordinate one technical document through its
complete lifecycle. Keep the work finite and based on a genuine document need.

The canonical
[Technical Documentation Management Plan](../../../reference/ENGINEERING_POLICY.md#technical-documentation-management-plan)
owns the lifecycle. The
[Technical Documentation Profile](../../../reference/ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile)
owns controlled writing. The
[technical-term register](../../../reference/TERMINOLOGY.md#asd-ste100-project-terminology)
owns technical terms.

## Authority boundary

The Technical Author Lead owns these workflow responsibilities:

- Identify and classify the document need.
- Plan the documentation work.
- Author and deliver the complete candidate.
- Coordinate controlled-document maintenance.
- Coordinate supersession, retirement, and preservation work.

The applicable technical or governance owner owns the subject meaning. The
Technical Author Lead has no authority over that meaning. The lead also does
not own terminology, the linguistic verdict, the validation result, or
controlled-baseline acceptance.

Publication, merge, supersession, retirement, and deletion need their
applicable authority. This skill does not supply that authority.

## Identify and classify the need

First, compare the need with the current controlled documentation. Select one
result:

- Create a new technical document.
- Make a material change to an existing technical document.
- Make a non-material correction.
- Make no documentation change.

Use an existing canonical owner when it is the correct location. Do not create
a new document for information that already has an owner.

Record the classification items that apply. Include canonical status,
document type, canonical owner, and subject owner. Include Issue 9
applicability, legacy status, the last accepted review state, and exact-content
exclusions. Also include the review, validation, and publication boundaries.

## Plan the document work

Before authoring, confirm these items:

- The purpose and intended user.
- The required technical meaning and its owner.
- The applicable canonical authorities and source information.
- The approved terminology.
- The document scope and change scope.
- The Issue 9, review, and validation requirements.
- The expected controlled-document result.

Use the smallest intervention that satisfies the need. Preserve unrelated
accepted prose and frozen historical evidence.

## Use the authoring route

Use this route for new or materially changed canonical technical prose:

> understand once → write once → check once → improve once → freeze once →
> review once → validate once → finish

Get the technical meaning from its canonical owner. Resolve each technical
term before writing. Use the
[local STE retrieval interface](../../../reference/external/asd-ste100/README.md#local-retrieval-interface)
before writing the affected logical units.

The check step examines meaning, ownership, terminology, exact content, links,
and deterministic pre-check results. It is not a Documentation Review. Apply
TT-DOC-001, TT-DOC-002, and D-GOV-015 exactly throughout the authoring route.
Apply one complete improvement pass before freeze.

Freeze one clean exact candidate only when the enclosing workflow has Git
authority. After freeze, use one independent
[`$tracktemplate-documentation-review`](../tracktemplate-documentation-review/SKILL.md).

Apply exact reviewed corrections once only when the verdict permits them. Then
run one final deterministic validation. A `BLOCKED` verdict is terminal for
that exact candidate. Do not run a second Documentation Review.

Finish the bounded authoring and review lifecycle by supplying the exact
candidate, Documentation Review, final validation, limitations, and required
owner decision. Green final validation ends this documentation cycle. Do not
send the document to another documentation, quality, publication, wording, or
semantic review. Do not describe these items as project acceptance.

Continuous integration can check the final bytes. It cannot start another
Documentation Review, correction pass, or linguistic improvement cycle.

## Control the baseline and availability

After the one Documentation Review, permitted adjustment, and final validation
are complete, coordinate the applicable acceptance. Record only the durable
identity and authority that the TDMP requires. Then coordinate repository
integration. Do not create a second document-management database.

Make the accepted document current and available through its normal route.
Confirm that a user can identify its current status, canonical owner, accepted
baseline, and material limitations.

## Maintain and change documents

Start maintenance only for a genuine document need. Do not periodically reopen
accepted unchanged prose for linguistic improvement.

Compare each proposed change with the controlled baseline. Route a material
change through the complete authoring route. Limit its review to the required
complete logical units that Git derives.

For a non-material correction, use the applicable change level and validation.
Reclassify the change if its meaning or authority becomes material.

## Coordinate supersession and retirement

Before supersession, identify the accepted replacement authority. Show that
required current information was retained or deliberately replaced. Update
references and prevent the earlier document from appearing current.

Before retirement, get evidence that the document owns no required current
information. Record where its information went or why it no longer applies.
Keep historical evidence when required.

The applicable subject and change authorities make these decisions. Preserve
the old document's historical meaning. Retirement does not authorise deletion.

## Handoff

Report these results:

- The document need and selected result.
- The classification, owners, scope, and source information.
- The planned and completed lifecycle stages.
- The exact candidate and controlled baseline, when they exist.
- The Documentation Review and validation results.
- The publication or availability result.
- The maintenance, supersession, retirement, or preservation result.
- Each limitation and owner decision that is still necessary.

Do not reopen a complete lifecycle without a genuine material need from the
applicable change-control authority.
