# Railway Terminology

Status: accepted plain-line terminology decision, 2026-07-19; Phase 1
assurance control implemented for closeout review, 2026-07-22.

## Assurance control

A lexical check cannot determine whether a railway term is correct in its
technical, prototype, regional and historical context. The project therefore
uses four visible assurance states instead of treating every familiar-looking
word as authoritative:

- `accepted`: approved for the exact bounded project context and preferred
  forms recorded in the register, not universally for every railway or era;
- `provisional`: a visible working description that cannot become a production
  identifier or public factual claim until its evidence is accepted;
- `review-required`: ambiguous, source-specific or plausibly incorrect in the
  proposed context, so new public UI/schema/API use is blocked; and
- `frozen-legacy`: retained only in immutable source, reproducibility evidence
  or a compatibility boundary and prohibited from spreading into successor
  naming.

The machine-readable
[Phase 1 terminology-assurance contract](contracts/phase1-terminology-assurance.json)
owns the term states, known source findings, frozen path set, review owners and
later gates. An accepted state records a project decision within its stated
meaning; it is not a claim that the same word is correct in every context.

### Human review workflow

When writing or changing a railway-facing term:

1. Check the register for the term and the exact intended meaning, not merely
   its spelling.
2. Use an accepted preferred form only within its bounded context.
3. If the meaning is uncertain, preserve the observed wording and add or
   update a provisional or review-required register entry with the exact
   location, proposed meaning, evidence needed, accountable reviewer and later
   gate. Do not resolve uncertainty by choosing the most plausible synonym.
4. Mark development-only code or prose with `TERM-REVIEW[<term_id>]` and add a
   matching open-review record. Do not expose that uncertain label as an
   unqualified production or publication claim.
5. Record a completed review with the accepted wording, rejected alternatives,
   semantic context, evidence, reviewer, decision date and affected locations.
   Only the project owner may accept the project terminology decision.

This makes a possible terminology error a named review item rather than a
memory test for the user. A contributor who is unsure is expected to flag the
term; they are not expected to guess.

### Current contextual register

| Term family | State | Current control |
| --- | --- | --- |
| Plain line/plain-line | accepted | Track without S&C; never a synonym for straight |
| Switches and crossings (S&C) | accepted | Infrastructure class; retain more specific component meanings |
| Straight/curve | accepted | Alignment descriptors independent of plain line/S&C |
| Easement/transition | accepted | State the mathematical subtype where behaviour depends on it |
| Chainage/station | accepted | State owning centreline, origin and direction; avoid passenger-station ambiguity |
| Multiple-track | accepted | Track count is independent of alignment shape and S&C class |
| Ordinary track/`ordinary_track` | frozen-legacy | Existing evidence and compatibility identifiers only |
| Ordinary single-road timbers | review-required | Exact support class unresolved; Phase 8 owner |
| Ordinary chair | review-required | REA/Templot-derived meaning and independent evidence unresolved; Phase 9 owner |
| Sleeper/timber | review-required | Do not assume universal synonymy; Phase 8 support-taxonomy review |
| Switch/points/turnout | review-required | Distinguish complete asset, assembly, movable rail and geometry vertices |
| Crossing/vee/frog | review-required | `frog` cannot become the default project label without review |
| S1 chair designation | provisional | Working pilot description only; S1-07 remains open |

### Automated boundary

Run:

```bash
.venv/bin/python tests/validate_phase1_terminology.py
```

The validator protects the four states, B14/B15 fingerprints, exact known
legacy phrase counts, all ordinary-named evidence paths, open-review ownership
and the successor product scan. It rejects known legacy terms in future
Workbench/UI/schema/API files unless a line-specific reviewed exception is
registered. It also rejects an unknown `TERM-REVIEW` marker.

Passing cannot prove semantic correctness. Contextual railway review remains
the authority for resolving a provisional or review-required item.

## Canonical track terms

- **Plain line** is railway track without switches and crossings (S&C). Use
  **plain line track** on first mention where the audience may not know the
  term, and **plain-line** when it modifies another noun, such as
  "plain-line workflow" or "plain-line fixture".
- Plain line may be straight, circular, transitioned/eased, single-track or
  multiple-track. **Plain** classifies the absence of S&C; it does not mean
  geometrically straight.
- **Switches and crossings (S&C)** is the contrasting infrastructure class.
  In this project, turnouts and crossovers are S&C or **special trackwork**.
- **Straight**, **curve**, **easement/transition**, **station/chainage** and
  **multiple-track** describe alignment or layout properties independently of
  whether the track is plain line or contains S&C.

This usage follows the Office of Rail and Road definition of
[plain line as track without switches and crossings](https://www.orr.gov.uk/glossary)
and its asset definition of
[plain line track as sections without switches and crossings](https://www.orr.gov.uk/media/28096/download).
ORR also describes the track asset as plain line, consisting of fixed rails,
or S&C, containing the movable rails that permit a train to move between plain
lines, in its
[Track and Lineside strategy](https://www.orr.gov.uk/sites/default/files/om/safety-strategy-chapter-6a-track.pdf).

## Project writing and naming

- Do not use **ordinary track** as a railway category in new prose, UI text,
  tests, filenames, schema fields or APIs.
- Prefer **routine editing** for the normal interactive path and
  **standalone Python** for Python running outside FreeCAD. Those meanings are
  unrelated to plain line.
- New Python names should use `plain_line`, not `ordinary_track`.
- Do not replace every occurrence of *ordinary* mechanically. Existing chair,
  timber and component classifications require their own source-based review;
  they are not automatically synonyms for plain line.

## Compatibility and evidence

B14 is the immutable legacy comparison oracle and B15 is the accepted Phase 1
behavioural reference. Their source text and hashes remain unchanged by this
terminology decision:

- B14 SHA-256:
  `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088`
- B15 SHA-256:
  `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848`

Phase 1 filenames, import names, recipe IDs, JSON keys, output directories and
benchmark paths containing `ordinary` are legacy evidence identifiers. Keep
them stable so committed reports and reproducibility contracts do not drift.
Living prose should describe their subject as plain line and may label the
identifier as legacy where needed. New modular interfaces must use the
canonical terminology; compatibility adapters may retain or translate a
legacy identifier until its retirement gate is accepted.

## Deferred source correction

The accepted macros contain at least these track-context phrases:

- `ordinary parallel tracks`
- `ordinary single-road timbers`

The first should become plain-line terminology in an approved successor
version. The second needs a focused timber-language review to establish
whether it means plain-line, independent single-road, non-shared, or another
specific support class before its wording changes. The macros also contain
several `ordinary chair` labels; review those against their REA/Templot source
meaning separately rather than changing them as part of the track-category
correction.

Any successor-macro wording change must include an approved version scope,
proportionate tests for affected UI or persisted values, updated source
fingerprints and explicit confirmation that geometry, ordering, identities,
production data and exports are unchanged.
