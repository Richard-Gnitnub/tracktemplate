# Railway Terminology

Status: accepted plain-line terminology decision, 2026-07-19; Phase 1
assurance control accepted at closeout on 2026-07-22, with six later reviews
still open.

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

## ASD-STE100 project terminology

This section is the one project register for TrackTemplate technical nouns and
technical verbs. The
[Technical Documentation Profile](ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile)
owns the ASD-STE100 Issue 9 scope and conformance rules. This register does not
copy the official controlled general dictionary.

Use these technical nouns only with their stated project meanings:

| Term group | Approved technical nouns and meaning |
| --- | --- |
| Product and tools | **TrackTemplate**, **TrackTemplate Core**, **Layout Editor**, **FreeCAD**, **Coin**, **Python**, **Git**, **GitHub**, **Addon**, and **Workbench** are product and tool names. **Product behavior** means a product operation or result that a person can examine. **Host integration** is the product connection to FreeCAD. |
| Authority | **Owner view**, **canonical information**, **proof/provenance**, **governance control**, **project authority**, **project owner**, and **competing owner** have the meanings in the Engineering Policy. |
| Governance state | **Status**, **phase**, **phase exit**, **risk**, **decision**, **decision register**, and **phase evidence** have the meanings in the current records. **Finding**, **limitation**, **disposition**, **controlled meaning**, and **acceptance** also use their current-record meanings. |
| Current state | **Current state**, **current phase**, **current evidence**, **current record**, **current owner view**, **current repository-evidence map**, and **status dashboard** are TrackTemplate status terms. |
| Canonical authority | **Canonical owner**, **canonical authority**, **canonical record**, **canonical state**, **canonical link**, **canonical policy**, and **canonical heading** are TrackTemplate authority terms. |
| Bounded claim | **Bounded scope**, **bounded cycle**, **bounded migration**, **bounded criterion**, **bounded decision**, **bounded condition**, and **bounded review** identify a limit in a canonical record. |
| Exact identity | **Exact state**, **exact path**, **exact data**, and **exact result** identify a required equality or identity. **Exact check**, **exact output**, **exact Git identity**, and **exact candidate** have the same function. |
| Documentation structure | **Documentation profile**, **canonical document**, **canonical prose**, **live document**, **frozen history**, **logical unit**, and **technical provenance** are TrackTemplate document terms. |
| Documentation change | **Migration**, **concision**, **wording**, **controlled writing**, **human interface**, **material edit**, **documentation simplification**, **readability**, and **Learning from Experience (LFE)** are TrackTemplate change terms. |
| Evidence detail | **Detailed technical provenance**, **detailed evidence**, **detailed proof**, and **detailed validation** identify supporting information below the canonical information. |
| Assurance process | **Evidence**, **validation**, **validator**, **reviewer**, **workflow**, **routing**, **handoff**, **skill catalog**, **competing responsibility**, and **non-ownership boundary** are TrackTemplate assurance-process terms. |
| Assurance result | **Conformance review**, **conformance scope**, **semantic control**, **preservation audit**, **review result**, **assessment**, and **machine-verifiable assurance** are TrackTemplate assurance-result terms. A **substantial cycle** has a result that changes project state, a formal decision, or detailed validation. |
| Git and repository | **Repository**, **worktree**, **branch**, **commit**, **pull request**, **merge commit**, **protected main**, **SHA**, **hash**, **path**, and **continuous integration (CI)** keep their Git meanings. |
| Release | **Packaging**, **release**, **tagging**, **licensing**, and **compatibility** keep their project meanings. |
| Host compatibility | A **host profile** is a named set of host and platform data. An **exact host profile** has data equal to the `exact_match` data in its contract record. A **qualified host profile** has accepted compatibility evidence and an owner decision. A **bundled stack** is the Python, Qt/PySide, OpenCASCADE, and Coin set in a host profile. A **host matrix** is the set of compatibility checks for one host profile. **Requalification** is a new compatibility assessment for a different host version. |
| Host compatibility tools | A **runtime guard** stops a supported composition before it can change a document on a host profile that the contract does not qualify. An **evaluator** examines host data against the compatibility contract. A **runtime probe** reports evaluator results. A **launcher** starts a TrackTemplate workflow in a host. A **fixture** is a controlled test input. **Legacy ingress** is the controlled input of data from a legacy file or macro. |
| Host compatibility authority | **Functional compatibility** is conformance to the TrackTemplate compatibility contract. It is not a security endorsement. |
| Performance direction | A **comparison baseline** is the accepted source state, host profile, method, and performance record for a paired comparison. A **performance hypothesis** names one cause of a measured cost and one bounded product change. A **comparison rule** gives the conditions for a PASS or FAIL result before the product change. A **performance optimisation** is a product change that must make a measured cost lower. **Zero-origin integration** calculates clothoid displacement from station zero for each target station. |
| Preview performance | A **preview sampler** calculates the preview points for one transition. A **preview regeneration** calculates that preview again after an Edit. A **preview batch function** calculates all preview displacement values in one function. **Simpson integration** is numerical integration by Simpson's rule. An **interior station** is a preview station between the two ends of a transition. An **endpoint calculation** calculates displacement at an end of a transition. |
| Performance statistics | A **paired block** has one baseline sample and one candidate sample. A **paired difference** is the candidate value minus the baseline value in one paired block. If an ordered sample has an odd number of values, its **median** is the middle value. If an ordered sample has an even number of values, its median is the sum of the two middle values divided by two. A **median absolute deviation (MAD)** is the median of the absolute differences from the sample median. A **no-displacement rule** uses the MAD and paired-difference limits for all measured non-target costs. |
| Performance measurement | A **warm block value** is the median of the three measured warm cycles in one sample. **High-water RSS** is the maximum RSS that the profiler records. A **resource metric** is an RSS, RSS change, high-water RSS, or high-water RSS change in a performance record. A **journey remainder** is the full-journey CPU or wall time minus the measured stage times. A **discrete invariant** is an exact object, recompute, cache, lifecycle, or cleanup result. **Measurement noise** is variation that the product change does not cause. |
| Performance boundaries | An **unmeasured boundary** is product work that the measurement profile does not measure. **Setup** is product work before the measured operator journey. **Teardown** is product work after that journey. |
| Performance investigation | **Retained negative evidence** is preserved evidence from a candidate with a FAIL comparison result or a required invariant difference. An **exhausted performance direction** is a performance hypothesis that has sufficient retained negative evidence to stop new product work in that direction. A **baseline-attribution investigation** measures one accepted operator journey and reports each **measurement area** without a product change. An **unattributed remainder** is measured journey time that is not part of a different measurement area. |
| Export | **Sentinel**, **DXF**, **manifest**, **schema**, **API**, and **JSON** keep their meanings from software or export specifications. |
| Railway | **Centreline**, **plain line**, **chainage**, **station**, **turnout**, **crossover**, and **railway behavior** use the canonical railway meanings below. TrackTemplate approves the spelling **Centreline** for this subject. |
| Standards | **ASD-STE100 Issue 9**, **Simplified Technical English (STE)**, and **S1000D** identify standards. **Technical noun**, **technical verb**, **normative standard**, **official standard**, **official conformance assessment**, and **linguistic conformance** keep their standards meanings. |

Use these technical verbs only with their stated project meanings:

| Technical verb | Project meaning |
| --- | --- |
| **Validate** | Do a named check and examine its result in the stated scope. |
| **Reconcile** | Compare a presentation or record with its canonical authority. Correct or report a difference. |
| **Authorize** | Give the exact authority in an explicit owner decision. |
| **Admit** | Accept named evidence for a bounded criterion without wider authority. |
| **Freeze** | Record one candidate and its exact content state for validation and review. |
| **Adopt** | Make a named standard or policy the normative standard for its stated scope. |
| **Claim** | Tell readers that a named capability, status, or assurance applies. |
| **Own** | Be the one canonical source for a named subject. |
| **Review** | Examine a named logical unit or candidate against stated criteria. |
| **Preserve** | Keep accepted repository content and authority without a change. |
| **Map** | Connect a responsibility to its canonical document or workflow owner. |
| **Migrate** | Move content or behavior between named states or boundaries. |
| **Report** | Record a result or limitation without authority. |
| **Name** | Give the exact identifier or term for a project subject. |
| **Define** | Record the exact scope, meaning, or condition in a canonical authority. |
| **Bound** | Limit a claim, decision, task, or review to an explicit scope. |
| **Copy**, **stage**, **commit**, **push**, **publish**, **merge**, **rebase**, and **squash** | Perform the related Git or GitHub operation. |
| **Route** | Send a responsibility or task to its named canonical document or workflow owner. |
| **Qualify** | Accept one exact host profile after the specified compatibility evidence and owner decision. |
| **Requalify** | Qualify a different exact host profile against the same compatibility contract. |

Do not use different technical terms for the same project concept. Do not use
a technical noun as a verb unless this register also approves the verb. Add a
new term only when it is necessary for a TrackTemplate subject. The applicable
Issue 9 category must permit the term. Do not change established identifiers.

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
