---
name: tracktemplate-changelog
description: Prepare or update TrackTemplate's user-facing changelog from accepted, validated project changes. Use when adding an unreleased note, deriving notable changes from a bounded Git range, preparing release notes or cutting an explicitly authorised version section.
---

# TrackTemplate changelog

## Outcome

Maintain a concise human-readable record of notable user and operator changes.
Use Git as discovery evidence, not as the source of project requirements,
acceptance or release status.

## Responsibility boundary

- `CHANGELOG.md` is user-facing release history. It must not duplicate live
  phase status, tranche evidence, decision rationale or validation detail.
- `reference/PROJECT_PLAN.md` owns current phases, gates, live risks, release
  scope and the Phase 11 version/publication decision.
- The open-phase evidence record owns current tranche evidence.
- Canonical reference documents own architecture, compatibility, validation,
  licensing, provenance and other project requirements.

Do not create `CHANGELOG.md` merely because the skill exists. Create it when
the user asks to start or maintain the changelog and no accepted release policy
supersedes this workflow.

## Supported actions

Resolve one action from the request:

- **Add:** add one notable item to `[Unreleased]`.
- **Derive:** propose entries from an explicit commit, tag, branch or diff
  range.
- **Prepare release:** turn accepted unreleased entries into a proposed version
  section after the project-owner release gate is satisfied.

If the action or range is material and ambiguous, inspect the repository first,
then ask for the missing decision rather than selecting all history.

## Preparation

1. Resolve the repository root and inspect `CHANGELOG.md`, if present.
2. Read the relevant current phase and release boundary in
   `reference/PROJECT_PLAN.md`.
3. Read the canonical owners and accepted evidence needed to substantiate each
   proposed entry.
4. Inspect the bounded source diff, tests and validation evidence. Use commit
   subjects and bodies to find candidates, then verify them against the actual
   change.
5. Preserve the existing changelog format when one exists. For a new file, use
   [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) with an
   `[Unreleased]` section; do not invent a released version history.

## Entry rules

Record changes that are notable to users, operators, integrators or downstream
data consumers, including:

- new or changed supported workflows;
- fixed observable defects;
- public API, schema, persistence or migration changes;
- compatibility, installation or dependency changes;
- deprecations, removals, security changes or breaking behaviour;
- material performance improvements supported by comparable evidence; and
- licensing or output-status changes that alter permitted or advertised use.

Skip routine internal work unless it changes a supported outcome:

- commits, merges and mechanical file movement;
- tests, fixtures or evidence that only confirm unchanged behaviour;
- internal refactors, formatting, comments and typo-only documentation;
- prototypes, unaccepted diffs and reverted unshipped work; and
- phase progress or risk detail owned by `reference/PROJECT_PLAN.md`.

Use short, specific descriptions in the project's terminology. Aggregate one
user-visible outcome across its implementation commits. Keep the standard
category order `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`,
`Security`, and omit empty categories.

## Derive from a change range

1. Name the exact baseline and endpoint. Do not silently use the repository's
   complete history when no accepted release baseline exists.
2. Inspect subjects, bodies and diffs, including breaking-change or migration
   details not visible in the subject.
3. Map candidates to user-visible outcomes and verify each against canonical
   authority and completed validation.
4. Deduplicate and aggregate related commits.
5. Show proposed entries, skipped candidates and reasons before editing when
   the user's request did not already approve the exact entries.

## Prepare a release

Treat release preparation as unavailable until the project owner has accepted
the applicable gate and selected the release version. In particular, do not
infer a Phase 11 version or publication decision from Git tags, changelog
content, dates or passing tests.

When the decision exists:

1. verify that `[Unreleased]` contains accepted entries;
2. verify the declared public API before applying
   [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html);
3. recommend a version only from the accepted compatibility impact and ask the
   user to confirm it;
4. add the confirmed version and ISO date while preserving older releases; and
5. update existing compare-link footers in their established form, if present.

Edit only the changelog under this action. Never commit, tag, push, publish,
change a package version or declare a release accepted unless the user
separately authorises that exact external action.

## Safety and correction rules

- Do not rewrite a released section except for an explicit, evidenced factual
  correction; keep the original release meaning visible.
- Do not describe planned, partial, headless-only or unaccepted behaviour as
  shipped.
- Preserve compatibility, provenance, licensing and output qualifications that
  affect whether a change is usable.
- Report conflicting source, evidence and authority instead of choosing the
  most convenient release claim.

## Report

Report the action, evidence range, entries added or proposed, candidates
skipped or aggregated, release decisions still required and checks performed.
