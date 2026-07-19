# Railway Terminology

Status: accepted project terminology decision, 2026-07-19.

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
