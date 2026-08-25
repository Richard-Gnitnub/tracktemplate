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
| Product and tools | **TrackTemplate**, **TrackTemplate Core**, **Layout Editor**, **FreeCAD**, **Coin**, **Python**, **Git**, **GitHub**, **Addon**, and **Workbench** are **product names** and **tool names**. A **product** is TrackTemplate or a TrackTemplate component that a person operates. A **tool** is software that does one bounded operation. **Software** is a TrackTemplate product or tool. **Product behavior** is a product operation or result that a person can examine. **Host integration** is the product connection to FreeCAD. |
| Authority | **Owner view**, **canonical information**, **proof/provenance**, **governance control**, **project authority**, **project owner**, and **competing owner** have the meanings in the Engineering Policy. |
| Governance state | **Status**, **phase**, **phase exit**, **risk**, **decision**, **decision register**, and **phase evidence** have the meanings in the current records. **Finding**, **limitation**, **disposition**, **controlled meaning**, and **acceptance** also use their current-record meanings. A **sequence nonconformance** records an authorised action that did not complete its mandatory governance sequence. **Retrospective authority** would make a record after an action falsely satisfy a prior authority condition. |
| Current state | **Current state**, **current phase**, **current evidence**, **current record**, **current owner view**, **current repository-evidence map**, and **status dashboard** are TrackTemplate status terms. |
| Canonical authority | **Canonical owner**, **canonical authority**, **canonical record**, **canonical state**, **canonical link**, **canonical policy**, and **canonical heading** are TrackTemplate authority terms. An **object mapping** connects a stable identity to one canonical FreeCAD object. A **route** is a sequence of product operations in one journey. |
| Bounded claim | **Bounded scope**, **bounded cycle**, **bounded migration**, **bounded criterion**, **bounded decision**, **bounded condition**, and **bounded review** identify a limit in a canonical record. A **directly dependent test** examines the named product boundary or its direct caller. |
| Exact identity | **Exact state**, **exact path**, **exact data**, and **exact result** identify a required equality or identity. **Exact check**, **exact output**, **exact Git identity**, and **exact candidate** have the same function. |
| Documentation structure | **Documentation profile**, **canonical document**, **canonical prose**, **live document**, **frozen history**, **logical unit**, and **technical provenance** are TrackTemplate document terms. |
| Documentation change | **Migration**, **concision**, **wording**, **controlled writing**, **human interface**, **material edit**, **documentation simplification**, **readability**, and **Learning from Experience (LFE)** are TrackTemplate change terms. |
| STE access | An **STE lookup** gives source material for one **lookup query**. A **word lookup**, **rule lookup**, and **topic lookup** are lookup queries. **Targeted retrieval** uses the STE lookup for one task. A **lookup result** contains only the source material for its lookup query. **Concise lookup output** is a lookup result with a small text quantity. **Recognised STE vocabulary** has an approved STE dictionary entry. |
| STE index | A **retrieval contract** contains the source manifest and retrieval index. A **retrieval index** maps a **rule identifier** to a **rule family** and a **source location**. A **topic tag** maps a topic to a rule family. A **retrieval priority** is a rule family that the agent reads first. A **source-derived index** contains writing rule and STE dictionary metadata from the **authorised source**. The **retrieval architecture** keeps source authority, full applicability, and targeted retrieval in different authority boundaries. |
| STE source | **Source material** comes from the authorised source. A **source page** is one page in that source. **Source text** is its text. **Extracted source text** is source text that a PDF extractor gives. A **source manifest** records the authorised **source identity**. |
| STE source tools | A **PDF extractor** reads **verified source bytes**. **Source mode** gives one **bounded source excerpt**. The tool binds a **derived cache** to the source identity and can rebuild it. |
| STE vocabulary | The **STE dictionary** is the controlled general dictionary in Issue 9 Part 2. A **writing rule** is one rule in Issue 9 Part 1. A **controlled vocabulary** is the applicable STE dictionary requirement set. A reviewer must use the STE dictionary for a **dictionary-inspection candidate**. |
| STE review aid | A **pre-check** is a **deterministic pre-check**. It gives a **review candidate**. A **content category** identifies `descriptive`, `procedural`, or `safety` content. **Sentence length** is the Issue 9 **word count** for one sentence. A **construction candidate** identifies a writing rule for review. |
| STE review record | A **review receipt** records review evidence without certification or endorsement. An **exact-content exclusion** identifies data or an **exact title**. The conformance review does not include that data. |
| STE review control | **Full applicability** applies to a review that examines the complete applicable Issue 9 **requirement set**. The **applicable rule set** contains all writing rules that apply. **Complete-source inspection** is a review from the first page to the last page of the standard. **Source efficiency** applies when an agent reads less source material and keeps the same requirement set. **Retrieval optimisation** increases source efficiency only. An **ambiguity** has more than one possible **term meaning**. |
| STE term authority | The **technical-term register** is this canonical TrackTemplate term owner. A **term** identifies one TrackTemplate item with one term meaning. |
| STE term status | **Technical-term status** records an approved term, a dictionary-inspection candidate, or **unresolved terminology**. An **applicable requirement** is one Issue 9 requirement that applies to the logical unit. A **technical-term category** is noun or verb. |
| STE term use | A **term use** is one term in canonical prose. A **contextual term review** compares a term use with its approved category and term meaning. A **category mismatch** occurs when a term use has a different category. |
| STE unresolved state | Unresolved terminology has no accepted status. A reviewer must resolve it. An **unresolved finding** has no accepted disposition. |
| STE retrieval limit | **Partial retrieval** has a bounded limit. It does not contain the complete applicable requirement set. An agent must not claim **partial conformance** from partial retrieval. A **drift control** stops a change that narrows canonical policy or retrieval architecture. |
| Rights control | A **rights state** records evidence for **copyright**, a **licence**, **ASD permission**, **eligibility**, **extraction**, **reproduction**, **publication**, and an **endorsement**. A **positive rights claim** shows that a specified right applies. A **certification** is an external assurance result. A **professional rights review** is a review by a rights professional. A **supply claim** shows that a person can supply specified external material. A **distributable output** has a positive rights state for supply. |
| Evidence detail | **Detailed technical provenance**, **detailed evidence**, **detailed proof**, and **detailed validation** identify supporting information below the canonical information. |
| Assurance roles | **Evidence**, **validation**, **validator**, **reviewer**, **agent**, **independent review**, **documentation review**, and **documentation alignment** are TrackTemplate review terms. An **assurance** connects evidence and review to one specified claim. **Agent context** is the text that an agent uses for one task. **Unverified conformance** has no accepted conformance review evidence. |
| Assurance workflow | **Workflow**, **routing**, **handoff**, **skill catalog**, **documentation skill routing**, **workflow responsibility**, **competing responsibility**, **authority boundary**, and **non-ownership boundary** are TrackTemplate workflow terms. |
| Assurance result | **Conformance review**, **conformance scope**, **semantic control**, **preservation audit**, **review result**, **assessment**, and **machine-verifiable assurance** are TrackTemplate assurance-result terms. A **substantial cycle** has a result that changes project state, a formal decision, or detailed validation. A **snapshot** is a recoverable copy of repository and evidence state. The recovery policy defines its controls. |
| Recovery state | An **interruption** is a sudden stop to a task. **Unfinished work** does not have acceptance from the project owner. **Interrupted work** is unfinished work after an interruption. A **dirty path** contains work that is not in a commit. **Recovery** is the procedure that keeps repository work available after an interruption. **Recovery state** is repository information that this procedure examines or keeps. |
| Visible recovery state | **Unresolved recovery state** does not have a necessary recovery result. **Visible recovery state** and **named Git state** use a branch, worktree, or commit with a recorded project owner and **recovery purpose**. The recovery purpose records the cause for the state. **Planned preservation** keeps work for handoff or the next task. A **feature branch**, **recovery branch**, **recovery worktree**, **recovery commit**, and **explicit commit** are named Git state. A **context packet** records the route to named Git state but does not preserve named Git state. |
| Recovery evidence | **Sensitive evidence** is evidence that **recovery policy** keeps local. **Local evidence** is evidence that recovery policy does not put in Git. A **checksum manifest** records hashes for local evidence. **Independent preservation** uses a device with project authority. **Off-device preservation** is independent preservation on a different device. A **recovery label** identifies recovery state. |
| Stash identity | A **stash** is one entry that the `git stash list` command reports. An **emergency stash** keeps work available and stays temporary. A **stash selector** is the `stash@{n}` name, and its value can change. A **stash commit SHA** identifies one stash, and its value does not change. |
| Stash topology | A **stash component** is one commit or tree in the **stash topology**. A **stash inventory** records the **base commit**, **base tree**, **index parent**, **index tree**, **worktree tree**, and optional **untracked-files parent** and **U tree**. An **untracked file** is not in the index. A **Git ignore rule** selects an **ignored file**. The U tree contains these files when the applicable stash command includes them. |
| Stash reconciliation | **Stash reconciliation** compares the base tree with the index tree and worktree tree. It examines each path, blob, **deletion**, and **file-mode difference**. It also examines each path and blob in the U tree. **Unique content** is a **tree difference** or file in the U tree that no named Git state or approved independent preservation contains. A **retained stash** is unresolved recovery state until its disposition with applicable authority is complete. |
| Stash disposition | A **retained unexplained stash** has missing **stash ownership**, recovery purpose, stash reconciliation, or **stash disposition**. Stash ownership records the project owner. Stash disposition records the result for the stash commit SHA for which the project owner gave authority. A disposition that removes a stash first validates the same stash inventory again. |
| Stash result | A completed stash disposition removes the stash only after its unique content stays available. A **recovery inventory** contains named Git state and the stash inventory. A **recovery audit** examines the recovery inventory. A **recovery gate** does not have a complete result while the stash inventory contains a retained stash. A **preservation diff** compares two recovery inventories. |
| Workspace recovery | A **workspace** is one worktree that workspace alignment examines. **Workspace alignment** compares a workspace with named Git state. **Accepted product state** has acceptance from the project owner. The [recovery policy](RECOVERY_AND_BACKUP.md#visible-recovery-state) is the canonical owner. |
| Worktree retirement | **Worktree retirement** removes one registered worktree after the recovery policy gives a complete procedure. **Accepted-history containment** shows that the accepted commit contains the target commit. **Tracked cleanliness** means that the target has no tracked index or worktree change and no `assume-unchanged` or `skip-worktree` index flag. A **local-state inventory** identifies each local-only file, a **retirement plan** classifies that exact inventory, and a **retirement audit** examines the plan without removal. The classifications are **authoritative local source**, **retained evidence**, **rebuildable cache/generated state**, **temporary disposable state**, and **ambiguous or uniquely owned state**. **Historical losslessness** means that a completed operation kept all authoritative or unique local state. |
| Git state | **Repository**, **worktree**, **branch**, **commit**, **Git object**, **blob**, **Git index**, **parent commit**, **pull request**, **merge commit**, and **protected main** are software terms. **SHA**, **hash**, **path**, and **continuous integration (CI)** are also software terms. |
| Software data | **File**, **filename**, **directory**, **byte**, **byte size**, **metadata**, and **test** are software terms. A **PDF** is an external source file. A **command** starts one local tool operation. A **version** identifies a tool, schema, or source state. A **development tool** is not a **product runtime dependency**. A **diagnostic** gives information about a tool result. |
| Local access state | A **file owner** and **file mode** control local file access. A **user** identifies who starts a local tool. The **current user** starts the lookup tool. **root** is the user with all local access. |
| Local tool state | An **active Python environment** supplies Python to the tool. **Memory** is local data for one tool process. An **input identity** is the SHA-256 identity of one tool input. A **profile identity** is the SHA-256 identity of the documentation profile. |
| Local cache identity | A **cache schema** defines the derived cache structure. A **supported cache schema** has a version that the tool accepts. A **stale cache** does not have the current input identities. A **cache identity** contains the source and input identities for one derived cache. An **automatic update** is a source or cache change without a rebuild command. |
| Local output bounds | An **output limit** is the maximum quantity that a tool can return. A **shown count** is the number of lookup results in concise output. A **truncation status** shows if the tool did not show all lookup results. |
| Release | **Packaging**, **release**, **tagging**, **licensing**, and **compatibility** keep their project meanings. |
| Host compatibility | A **host profile** is a named set of host and platform data. An **exact host profile** has data equal to the `exact_match` data in its contract record. A **qualified host profile** has accepted compatibility evidence and an owner decision. A **bundled stack** is the Python, Qt/PySide, OpenCASCADE, and Coin set in a host profile. A **host matrix** is the set of compatibility checks for one host profile. **Requalification** is a new compatibility assessment for a different host version. |
| Host compatibility tools | A **runtime guard** stops a supported composition before it can change a document on a host profile that the contract does not qualify. An **evaluator** examines host data against the compatibility contract. A **runtime probe** reports evaluator results. A **launcher** starts a TrackTemplate workflow in a host. A **fixture** is a controlled test input. **Legacy ingress** is the controlled input of data from a legacy file or macro. |
| Host compatibility authority | **Functional compatibility** is conformance to the TrackTemplate compatibility contract. It is not a security endorsement. |
| Performance direction | A **comparison baseline** is the accepted source state, host profile, method, and performance record for a paired comparison. A **performance hypothesis** names one cause of a measured cost and one bounded product change. A **comparison rule** gives the conditions for a PASS or FAIL result before the product change. A **performance optimisation** is a product change that must make a measured cost lower. **Zero-origin integration** calculates clothoid displacement from station zero for each target station. |
| Performance evidence | **Current-cost evidence** reports the measured cost of an accepted source state. **Direction-selection evidence** connects a measured cost to one bounded performance hypothesis. **Improvement evidence** is a PASS result from the recorded comparison rule. **Exit evidence** is evidence that an owner decision admits to one phase exit. |
| Preview performance | A **preview sampler** calculates the preview points for one transition. A **preview regeneration** calculates that preview again after an Edit. A **preview batch function** calculates all preview displacement values in one function. **Simpson integration** is numerical integration by Simpson's rule. An **interior station** is a preview station between the two ends of a transition. An **endpoint calculation** calculates displacement at an end of a transition. |
| Comparison statistics | A **paired block** has one baseline sample and one candidate sample. A **paired difference** is the candidate value minus the baseline value in one paired block. If an ordered sample has an odd number of values, its **median** is the middle value. If an ordered sample has an even number of values, its median is the sum of the two middle values divided by two. A **baseline-first block** measures the baseline before the candidate. A **candidate-first block** measures the candidate before the baseline. |
| Performance limits | Python `statistics.quantiles(..., method='inclusive')` gives a **first quartile**. A **median absolute deviation (MAD)** is the median of the absolute differences from the sample median. A **no-displacement rule** uses the MAD and paired-difference limits for all measured non-target costs. |
| Performance measurement | A **process** is one FreeCAD execution for a sample. A **warm block value** is the median of the three measured warm cycles in one sample. **High-water RSS** is the maximum RSS that the profiler records. A **resource metric** is an RSS, RSS change, high-water RSS, or high-water RSS change in a performance record. |
| Performance result | A **journey remainder** is the full-journey CPU or wall time minus the measured stage times. A **discrete invariant** is an exact object, recompute, cache, lifecycle, or cleanup result. **Measurement noise** is variation that the product change does not cause. |
| Performance journey | A **cold journey** starts in a new process. A **warm cycle** does the accepted journey again in the same process. **Warm reuse** and **deterministic reuse** keep their performance-record meanings. |
| Performance boundaries | An **unmeasured boundary** is product work that the measurement profile does not measure. An **application span** is a measurement interval for one application command. **Setup** is product work before the measured operator journey. **Teardown** is product work after that journey. |
| Performance investigation | **Retained negative evidence** is preserved evidence from a candidate with a FAIL comparison result or a required invariant difference. An **exhausted performance direction** is a performance hypothesis that has sufficient retained negative evidence to stop new product work in that direction. A **baseline-attribution investigation** measures one accepted operator journey and reports each **measurement area** without a product change. An **attribution series** is a set of process samples from that investigation. |
| Attribution statistics | Three values give the **attribution noise floor**. They are the Edit CPU MAD for the baseline, the Edit CPU MAD for attribution, and the maximum of the calibrated instrumentation overhead. The noise floor is the highest of these three values. The **attribution materiality rule** gives PASS when the first quartile for an applicable measurement area is higher than that floor. An **unattributed remainder** is measured journey time that is not part of a different measurement area. |
| Attribution evidence | A **same-host baseline** uses one exact host profile. **Test-owned instrumentation** is measurement logic that is not product source. **Instrumentation overhead** is the measured cost that test-owned instrumentation adds. An **attribution collector** records the attribution series. An **attribution corpus** is the retained method, baseline, instrumentation, result, failure classification, and checksum manifest for one investigation. A **live read** reads current FreeCAD property state. |
| Attribution source | A **repeated read** reads all data from the same live record again in one Edit. **Selected-record data** is all canonical data for the selected record. A **pre-registered method** records measurement and decision rules before measurements start. A **fixture-failure classification** identifies a retained fixture or harness failure. |
| Export | **Sentinel**, **DXF**, **manifest**, **schema**, **API**, and **JSON** keep their meanings from software or export specifications. |
| Railway | **Centreline**, **plain line**, **chainage**, **station**, **turnout**, **crossover**, and **railway behavior** use the canonical railway meanings below. TrackTemplate approves the spelling **Centreline** for this subject. |
| Official sources | A **standard** is an external reference that has a requirement set. **ASD-STE100 Issue 9**, **Simplified Technical English (STE)**, and **S1000D** identify standards. **Technical noun**, **technical verb**, **normative standard**, **official standard**, **official source**, **external reference**, **conformance**, **official conformance assessment**, and **linguistic conformance** are standards terms. |

Use these technical verbs only with their stated project meanings:

| Technical verb | Project meaning |
| --- | --- |
| **Validate** | Do a named check and examine its result in the stated scope. |
| **Reconcile** | Compare a presentation or record with its canonical authority. Correct or report a difference. |
| **Authorize** | Give the exact authority in an explicit owner decision. |
| **Admit** | Accept named evidence for a bounded criterion without wider authority. |
| **Freeze** | Record one candidate and its exact content state for validation and review. |
| **Adopt** | Make a named standard or policy the normative standard for its stated scope. |
| **Approve** | Add a TrackTemplate technical noun or technical verb to the canonical technical-term register. |
| **Bind** | Connect derived retrieval data to one authorised source identity. |
| **Claim** | Tell readers that a named capability, status, or assurance applies. |
| **Own** | Be the one canonical source for a named subject. |
| **Review** | Examine a named logical unit or candidate against stated criteria. |
| **Preserve** | Keep accepted repository content and authority without a change. |
| **Map** | Connect a responsibility to its canonical document or workflow owner. |
| **Rebuild** | Regenerate the derived cache after source and input validation. |
| **Retrieve** | Give source material for a lookup query. Do not change full applicability. |
| **Optimise** | Increase source efficiency without a decrease to the requirement set. |
| **Resolve** | Give one accepted status to a specified finding or ambiguity. |
| **Return** | Give one bounded result from a local tool operation. |
| **Extract** | Use the PDF extractor to get source text from verified source bytes. |
| **Reproduce** | Make a copy of external source material. |
| **Fail closed** | Stop the operation if an identity is missing. Stop it after a `FAIL` validation result. |
| **Narrow** | Remove part of a requirement set or bounded claim. |
| **Migrate** | Move content or behavior between named states or boundaries. |
| **Report** | Record a result or limitation without authority. |
| **Record** | Put specified evidence or data in its canonical owner. |
| **Name** | Give the exact identifier or term for a project subject. |
| **Define** | Record the exact scope, meaning, or condition in a canonical authority. |
| **Bound** | Limit a claim, decision, task, or review to an explicit scope. |
| **Copy**, **stage**, **commit**, **push**, **publish**, **merge**, **rebase**, and **squash** | Perform the related Git or GitHub operation. |
| **Route** | Send a responsibility or task to its named canonical document or workflow owner. |
| **Qualify** | Accept one exact host profile after the specified compatibility evidence and owner decision. |
| **Requalify** | Qualify a different exact host profile against the same compatibility contract. |
| **Classify** | Assign a failed check to one failure class that the testing policy gives. Assign one worktree-retirement inventory item to one classification that the recovery policy gives. |
| **Regenerate** | Do an evidence workflow again. Replace its retained result. |

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
