# Railway Terminology

Status: the plain-line terminology decision was accepted on 2026-07-19. The
Phase 1 assurance control was accepted at closeout on 2026-07-22. Six later
reviews are still open.

## Assurance control

A lexical check cannot determine whether a railway term is correct in each
technical, prototype, regional, and historical context. The project therefore
uses four visible terminology-assurance states. It does not treat each familiar
word as authoritative.

- `accepted` is approved for the exact bounded project context and preferred
  forms in the register. It is not universal for each railway or era.
- `provisional` is a visible working description. It cannot become a production
  identifier or public factual claim until its evidence is accepted.
- `review-required` is ambiguous, source-specific, or possibly incorrect in the
  proposed context. It stops new public UI, schema, or API use.
- `frozen-legacy` remains only in immutable source, reproducibility evidence, or
  for compatibility. New replacement naming must not use it.

The machine-readable
[Phase 1 terminology-assurance contract](contracts/phase1-terminology-assurance.json)
owns the term states, known source findings, frozen path set, review owners, and
later gates. An accepted state records a project decision within its stated
controlled meaning. It is not a claim that the same word is correct in each
context.

### Human review workflow

When you write or change a railway-facing term, use this procedure.

1. Check the register for the term and its exact intended controlled meaning.
2. Use an accepted preferred form only within its bounded context.
3. If the controlled meaning is uncertain, preserve the observed wording. Add
   or update a provisional or review-required register entry with the exact
   location, proposed controlled meaning, necessary evidence, accountable
   reviewer, and later gate. Do not select a synonym to resolve uncertainty.
4. Mark development-only code or prose with
   `TERM-REVIEW[<term_id>]`. Add a
   matching open-review record. Do not expose that uncertain label as an
   unqualified production or publication claim.
5. Record a completed review with the accepted wording, rejected alternatives,
   semantic context, evidence, reviewer, decision date, and affected locations.
   Only the project owner may accept the project terminology decision.

This makes a possible terminology error a named review item. It is not a memory
test for a person. A contributor who is unsure must identify the term. The
contributor must not guess.

### Current contextual register

| Term family | State | Current control |
| --- | --- | --- |
| Plain line/plain-line | accepted | Track without S&C. It is never a synonym for straight. |
| Switches and crossings (S&C) | accepted | Infrastructure class. Retain more specific component meanings. |
| Straight/curve | accepted | Alignment descriptors independent of plain line/S&C |
| Easement/transition | accepted | State the mathematical subtype where behaviour depends on it |
| Chainage/station | accepted | State the owning centreline, origin, and direction. Avoid passenger-station ambiguity. |
| Multiple-track | accepted | Track count is independent of alignment shape and S&C class |
| Ordinary track/`ordinary_track` | frozen-legacy | Existing evidence and compatibility identifiers only |
| Ordinary single-road timbers | review-required | The exact support class is unresolved. Phase 8 owns the review. |
| Ordinary chair | review-required | The REA or Templot controlled meaning and independent evidence are unresolved. Phase 9 owns the review. |
| Sleeper/timber | review-required | Do not assume that these terms are always synonyms. Phase 8 owns the support-taxonomy review. |
| Switch/points/turnout | review-required | Distinguish the complete turnout, assembly, movable rail, and geometry vertices. |
| Crossing/vee/frog | review-required | `frog` cannot become the default project label without review |
| S1 chair designation | provisional | Working pilot description only. S1-07 remains open. |

### Automated limit

Run:

```bash
.venv/bin/python tests/validate_phase1_terminology.py
```

The validator protects the four states, B14/B15 fingerprints, exact known
legacy phrase counts, all ordinary-named evidence paths, open-review ownership,
and the replacement-product scan. It rejects known legacy terms in future
Workbench/UI/schema/API files unless a line-specific reviewed exception is
registered. It also rejects an unknown `TERM-REVIEW` marker.

Passing cannot prove semantic correctness. Contextual railway review remains
the authority for resolving a provisional or review-required item.

## ASD-STE100 project terminology

This section is the one project register for TrackTemplate technical nouns and
technical verbs. The
[Technical Documentation Profile](ENGINEERING_POLICY.md#tt-doc-001-tracktemplate-technical-documentation-profile)
owns the ASD-STE100 Issue 9 conformance scope and rules. This register does not
copy the official controlled general dictionary.

Use these technical nouns only with their stated project meanings:

| Term group | Approved technical nouns and meaning |
| --- | --- |
| Product and tools | **TrackTemplate**, **TrackTemplate Core**, and **Layout Editor** are product names. **FreeCAD**, **Coin**, **Python**, **Git**, **GitHub**, **Ruff**, **Templot**, and **PyCharm** are tool names. **IDE**, **Addon**, **Workbench**, and **FCMacro** are software terms. A **product** is TrackTemplate or a TrackTemplate component that a person operates. A **tool** is software that does a specified operation. **Software** is a TrackTemplate product or tool. |
| Product operation | **Product behaviour** is a product operation or result that a person examines. **Host integration** is the product connection to FreeCAD. The Product Vision and Engineering Policy define **railway behaviour**, **export behaviour**, **product performance**, **production**, and **physical output**. |
| Project concepts | A **programme** is the current TrackTemplate Core programme or the later Layout Editor programme. **Architecture** is the accepted design and ownership structure in `reference/ARCHITECTURE.md`. **Persistence** is the architecture-owned FreeCAD data and document boundary that remains through save and reopen. **Dependency direction** is the permitted direction in which one TrackTemplate source layer or component can depend on another. |
| Project state and profiles | **Private-development status** is the existing Phase 6 output state for output with no production clearance. A **measurement profile** is the D-GOV performance-method identity for an accepted measurement. An **operating system** supplies the D-P6-004 process and file-operation boundary. |
| Terminology assurance | A **terminology-assurance state** is one exact value in the Phase 1 terminology-assurance contract. The values are `accepted`, `provisional`, `review-required`, and `frozen-legacy`. |
| Authority | **Governance** includes project authority, status, evidence, and decisions. The Engineering Policy defines **Owner view**, **canonical information**, **proof/provenance**, **governance control**, **project authority**, **project owner**, and **competing owner**. A **sequence nonconformance** is a record for an operation that did not have the necessary governance sequence first. **Retrospective authority** is project authority for a previous operation without the authority. D-GOV-012 contains no retrospective authority. |
| Owner-view fields | `TT-DOC-001` defines six **owner-view field** terms. They are Current state, **What changed**, **What now works**, **Limitations/findings**, **Owner decision**, and **Next action**. |
| Governance state | **Status**, **phase**, **phase exit**, **risk**, **decision**, **decision register**, and **phase evidence** have the meanings in the current records. **Finding**, **limitation**, **disposition**, **controlled meaning**, and **acceptance** also use their current-record meanings. A **safety/risk panel** is the Level 3 review in the Engineering Policy. |
| Risk data | A **risk register** is the canonical record for risks. **Severity**, **treatment**, **deadline**, and **control effectiveness** are risk terms. **Critical**, **High**, **Medium**, and **Low** are severity values. **Remove**, **Mitigate**, **Tolerate**, and **Accept** are treatment values. A **risk owner** is the person in the `owner` value. A **panel recommendation** is the result from a safety/risk panel. |
| Current state | **Current state**, **current phase**, **current evidence**, **current record**, **current owner view**, **current repository-evidence map**, and **status dashboard** are TrackTemplate status terms. **Accepted project state** has acceptance from the project owner. |
| Canonical authority | **Canonical owner**, **canonical authority**, **canonical record**, **canonical state**, **canonical link**, **canonical policy**, and **canonical heading** are TrackTemplate authority terms. An **object mapping** connects a stable identity to one canonical FreeCAD object. A **route** is a sequence of product operations in one journey. |
| Bounded claim | **Bounded scope**, **bounded cycle**, **bounded migration**, **bounded criterion**, **bounded decision**, **bounded condition**, and **bounded review** identify a limit in a canonical record. A **directly dependent test** examines the named product boundary or its direct caller. |
| Identity | An **identity** identifies an item without ambiguity. An **exact state** identifies all data in an exact candidate. An **exact Git identity** identifies a Git object without ambiguity. An **exact candidate** has a stable identity for all files in its bounded scope. The author freezes the candidate as a Git commit and tree. A **stable identity** does not change when a tool operates again. |
| Documentation structure | **Technical Documentation Profile** is the title for `TT-DOC-001`. **Documentation profile**, **document class**, **canonical document**, **canonical prose**, **changed prose**, and **live document** are TrackTemplate document terms. **Frozen history**, **logical unit**, **complete logical unit**, **writing checklist**, **project plan**, and **technical provenance** are also document terms. |
| Documentation change | **Migration**, **concision**, **wording**, **controlled writing**, **human interface**, **material edit**, **documentation simplification**, **readability**, **Learning from Experience (LFE)**, and **LFE record** are TrackTemplate change terms. |
| STE access | An **STE lookup** gives source material for one **lookup query**. A **word lookup**, **rule lookup**, and **topic lookup** are lookup queries. **Targeted retrieval** uses the STE lookup for one task. A **lookup result** contains only the source material for its lookup query. **Concise lookup output** is a lookup result with a small text quantity. **Recognised STE vocabulary** has an approved STE dictionary entry. |
| STE index | A **retrieval contract** contains the source manifest and retrieval index. A **retrieval index** maps a **rule identifier** to a **rule family** and a **source location**. A **topic tag** maps a topic to a rule family. A **retrieval priority** is a rule family that the agent reads first. A **source-derived index** contains writing rule and STE dictionary metadata from the **authorised source**. The **retrieval architecture** keeps source authority, full applicability, and targeted retrieval in different authority boundaries. |
| STE source | **Source material** comes from the authorised source. A **source page** is one page in that source. **Source text** is its text. **Extracted source text** is source text that a PDF extractor gives. A **source manifest** records the authorised **source identity**. |
| STE source tools | A **PDF extractor** reads **verified source bytes**. **Source mode** gives a **bounded source excerpt**. The STE lookup binds a **derived cache** to the source identity. The STE lookup can rebuild it. The **source and retrieval procedure** owns the source path and the STE lookup operation. |
| STE vocabulary | The **STE dictionary** is the controlled general dictionary in Issue 9 Part 2. A **writing rule** is one rule in Issue 9 Part 1. A **controlled vocabulary** is the applicable STE dictionary requirement set. A reviewer must use the STE dictionary for a **dictionary-inspection candidate**. |
| STE review aid | A **pre-check** is a **deterministic pre-check**. It gives a **review candidate**. A **content category** identifies `descriptive`, `procedural`, or `safety` content. A **construction candidate** identifies a writing rule for review. |
| STE review record | A **review receipt** records review evidence without certification or endorsement. A **Documentation Review receipt** binds one verdict to a **frozen review scope**, source, exact candidate, and final content. An **exact-content exclusion** identifies data or an **exact title** that the conformance review does not include. A **review category** identifies part of the conformance review. The `path`, `start_line`, `end_line`, and `sha256` values identify a logical unit in the review. |
| STE evidence record | An **evidence claim** reports a fact. An **evidence type** identifies a command result, Git state, source identity, **historical operation**, or **governance record**. An author records the **actual result** and source. A command result also identifies its command invocation, validation profile, and command-output SHA-256. |
| STE review control | **Full applicability** applies to a review that examines the complete applicable Issue 9 **requirement set**. The **applicable rule set** contains all writing rules that apply. **Complete-source inspection** is a review from the first page to the last page of the standard. **Source efficiency** applies when an agent reads less source material and keeps the same requirement set. **Retrieval optimisation** increases source efficiency only. An **ambiguity** has more than one possible **term meaning**. |
| STE term authority | The **technical-term register** is this canonical TrackTemplate term owner. A **term** identifies one TrackTemplate item with one term meaning. |
| STE term status | **Technical-term status** records an approved term, a dictionary-inspection candidate, or **unresolved terminology**. An **applicable requirement** is part of the applicable rule set for the logical unit. A **technical-term category** is `noun` or `verb`. |
| STE unresolved state | Unresolved terminology has no accepted status. A reviewer must resolve it. An **unresolved finding** has no accepted disposition. **Unverified conformance** has no accepted conformance review evidence. |
| STE retrieval limit | **Partial retrieval** has a bounded limit. It does not contain the complete applicable requirement set. An agent must not claim **partial conformance** from partial retrieval. A **drift control** stops a change that narrows canonical policy or retrieval architecture. |
| Rights control | A **rights state** records evidence for **copyright**, a **licence**, **ASD permission**, **eligibility**, **extraction**, **reproduction**, **publication**, and an **endorsement**. A **positive rights claim** shows that a specified right applies. A **certification** is an external assurance result. A **professional rights review** is a review by a rights professional. A **supply claim** shows that a person can supply specified external material. A **distributable output** has a positive rights state for supply. |
| Evidence detail | **Detailed technical provenance**, **detailed evidence**, **detailed proof**, and **detailed validation** identify information below the canonical information. **Implementation evidence** is source, test, commit, or diff information. It gives no project authority. |
| Assurance roles | **Evidence**, **validation**, **validator**, **reviewer**, **author**, **implementing agent**, and **agent** are TrackTemplate review terms. **Documentation reviewer**, **independent reviewer**, **independent quality reviewer**, **independent security/recovery reviewer**, and **independent documentation reviewer** are also review terms. **Independent review**, **quality review**, **security/recovery review**, **documentation review**, and **documentation alignment** are review terms. The **Technical Author Lead** is the canonical workflow owner for material technical-documentation authoring and delivery. This role consumes the applicable technical meaning, canonical terminology, documentation policy, and targeted STE retrieval. It authors one complete candidate for independent Documentation Review. It gives no subject, terminology, policy, review-verdict, validation, project-acceptance, publication, or Level 3 authority. A **recovery validator** validates each recovery control. An **assurance** connects evidence and review to a specified claim. **Agent context** is text that an agent uses for a task. |
| Assurance workflow | **Workflow**, **Git workflow**, **context recovery**, **routing**, **handoff**, **skill**, **skill catalog**, and **documentation skill routing** are workflow terms. **Workflow responsibility**, **competing responsibility**, **authority boundary**, and **non-ownership boundary** are also workflow terms. The **Documentation Review lifecycle** is `author → freeze scope → one Documentation Review → optional exact reviewed correction once → one final deterministic validation → complete or owner stop`. The Documentation Review is the only linguistic conformance review. |
| Assurance result | **Conformance review**, **conformance scope**, **semantic control**, **preservation audit**, **complete result**, **review result**, **assessment**, and **machine-verifiable assurance** are assurance terms. A Documentation Review result has one **verdict**. It is `ACCEPT`, `APPROVED_WITH_EXACT_CORRECTIONS`, or `BLOCKED`. An **exact correction** supplies reviewed replacement wording for a verified **preimage**. An **accepted document identity** is the last reviewed document content. |
| Assurance state | The **review-state register** keeps durable document-level identities. Git derives changed complete logical units. A **semantic mutation** is a change that a semantic control must reject. A **regression test** examines a previous problem. An **unresolved disposition** has no accepted result. A **substantial cycle** changes project state, adds a decision, or adds detailed validation. |
| Validation result | A **PASS result** shows that the specified validator accepted its inputs. A **FAIL result** shows that the specified validator rejected its inputs. A **failure class** identifies the cause for a FAIL result. An **invalid state** is an input for which the validator must give a FAIL result. The testing policy owns **failure classification**. |
| Recovery state | An **interruption** is a sudden stop to a task. **Unfinished work** does not have acceptance from the project owner. **Interrupted work** is unfinished work after an interruption. A **dirty path** contains work that is not in a commit. **Recovery** is the procedure that keeps repository work available after an interruption. **Recovery state** is repository information that this procedure examines or keeps. |
| Recovery checkpoint | A **checkpoint** is named Git state that is necessary before a repository operation with recovery risk. A **clean checkpoint** has tracked cleanliness. A **pushed checkpoint** has a branch on GitHub that contains the checkpoint commit. A **snapshot** is a copy of repository data and evidence. The recovery policy is the canonical owner for snapshots. |
| Visible recovery state | **Unresolved recovery state** does not have a necessary recovery result. **Visible recovery state** and **named Git state** use a branch, worktree, or commit with a recorded project owner and **recovery purpose**. The recovery purpose records the cause for the state. **Planned preservation** keeps work for handoff or the next task. A **feature branch**, **recovery branch**, **recovery worktree**, **recovery commit**, and **explicit commit** are named Git state. A **context packet** records the route to named Git state but does not preserve named Git state. |
| Recovery evidence | **Sensitive evidence** is evidence that **recovery policy** keeps local. **Local evidence** is evidence that recovery policy does not put in Git. A **checksum manifest** records hashes for local evidence. **Independent preservation** uses a device with project authority. **Off-device preservation** is independent preservation on a different device. A **recovery label** identifies recovery state. |
| Stash identity | A **stash** is one entry that the `git stash list` command reports. An **emergency stash** keeps work available and stays temporary. A **stash selector** is the `stash@{n}` name, and its value can change. A **stash commit SHA** identifies one stash, and its value does not change. |
| Stash topology | A **stash component** is one commit or tree in the **stash topology**. A **stash inventory** records the **base commit**, **base tree**, **index parent**, **index tree**, **worktree tree**, and optional **untracked-files parent** and **U tree**. An **untracked file** is not in the index. A **Git ignore rule** selects an **ignored file**. The U tree contains these files when the applicable stash command includes them. |
| Stash reconciliation | **Stash reconciliation** compares the base tree with the index tree and worktree tree. It examines each path, blob, **deletion**, and **file-mode difference**. It also examines each path and blob in the U tree. **Unique content** is a **tree difference** or file in the U tree that no named Git state or approved independent preservation contains. A **retained stash** is unresolved recovery state until its disposition with applicable authority is complete. |
| Stash disposition | A **retained unexplained stash** has missing **stash ownership**, recovery purpose, stash reconciliation, or **stash disposition**. Stash ownership records the project owner. Stash disposition records the result for the stash commit SHA for which the project owner gave authority. A disposition that removes a stash first validates the same stash inventory again. |
| Stash result | A completed stash disposition removes the stash only after its unique content stays available. A **recovery inventory** contains named Git state and the stash inventory. A **recovery audit** examines the recovery inventory. A **recovery gate** does not have a complete result while the stash inventory contains a retained stash. A **preservation diff** compares two recovery inventories. |
| Workspace recovery | A **workspace** is a worktree that workspace alignment examines. **Workspace alignment** compares a workspace with named Git state. A **worktree map** identifies each worktree in `git worktree list`. **Accepted product state** has acceptance from the project owner. The recovery policy is the canonical owner. |
| Worktree retirement | **Worktree retirement** is the procedure that an implementing agent uses for removal of a worktree. Git gives **accepted-history containment** when the accepted commit contains the specified commit. **Removal authority** is project authority for a specified worktree or branch operation. |
| Worktree retirement evidence | **Tracked cleanliness** is a Git state with no tracked change in the Git index or worktree. In tracked cleanliness, the Git index has no `assume-unchanged` or `skip-worktree` value. A **local-state inventory** identifies each local file that is not in the Git index. A **retirement plan** contains a local-state type for each item and the SHA-256 for the local-state inventory. A **retirement audit** examines the retirement plan without removal. |
| Local-state types | Worktree retirement has 5 **local-state types**. They are **authoritative local source**, **retained evidence**, **rebuildable cache/generated state**, **temporary disposable state**, and **ambiguous or uniquely owned state**. |
| Historical losslessness | **Historical losslessness** means that an operation kept all tracked files, authoritative local source, retained evidence, and files with no other copy. |
| Git state | **Git state** is repository information from Git. **Repository**, **worktree**, **branch**, **branch tip**, **branch on GitHub**, **commit**, and **accepted commit** are terms for software. **Git object**, **blob**, **tree**, **merge**, and **Git index** are terms for software. **HEAD**, **parent commit**, **pull request**, **pull-request state**, **draft pull request**, and **merge commit** are terms for software. **Tracked file**, **tracked change**, **protected main**, **SHA**, **hash**, **path**, **diff**, and **continuous integration (CI)** are terms for software. |
| Branch tip | A branch tip is the commit at HEAD of the specified branch. An accepted commit is the commit that the project owner selects for accepted-history containment. A draft pull request has no project authority for a merge into protected main. |
| Software data | **File**, **filename**, **directory**, **symbolic link**, **symbolic link loop**, **byte**, **byte size**, **bytecode**, and **metadata** are software terms. **Prefix**, **UTF-8**, **JSON key**, **duplicate key**, **input**, **test**, and **caller** are also software terms. A symbolic link loop has no end. |
| External source data | A **PDF** is an **external source file**. A **source archive** is a local file from Templot. A **source path** is the local path for the authorised source. |
| Software operation | A **command invocation** contains an **executable**, **arguments**, and a **working directory**. A tool process uses a **command** to start a local operation. A **version** identifies a tool, schema, or source state. A **development tool** is not a **product runtime dependency**. A **diagnostic** contains information about a tool result. **Application cancellation** stops one TrackTemplate application command at an explicit **cancellation point**. It does not stop the application process. A cancellation point is a caller-owned check at which the command can stop. |
| Run configuration | A **run configuration** contains data for a PyCharm tool operation. A **validation profile** contains specified validation commands. The validation profile for **standalone Python** does not use FreeCAD. An **environment variable** supplies a specified value to a tool process. A **VCS root** connects a PyCharm project to a repository. |
| Software result | **Command output** contains information that a tool returns. A **process exit status** is the number that a process returns when it stops. A **Git error** is a Git result for an operation with no complete result. A **file-system error** is a local result with no complete result. A **validation tool** validates specified inputs. |
| Ontology | An **ontology** maps stable product terms. It gives no project authority. |
| IDE data | An **SDK** identifies the active Python environment for PyCharm. **IDE data**, **user data**, **PyCharm data**, and **window title** are local interface terms. |
| Local access state | The file system uses a **file owner** and **file mode** to control **local file access**. The **current user** starts the STE lookup. **Authentication data** gives access to a system. The **root user** can read and write all local files. |
| Local tool state | An **active Python environment** supplies Python to the tool. **Memory** is local data for one tool process. An **input identity** is the SHA-256 identity of one tool input. A **profile identity** is the SHA-256 identity of the documentation profile. |
| Local cache identity | A **cache schema** defines the derived cache structure. A **supported cache schema** has a version that the tool accepts. A **stale cache** does not have the current input identities. A **cache identity** contains the source and input identities for one derived cache. An **automatic update** is a source or cache change without a rebuild command. |
| Local output bounds | An **output limit** is the maximum quantity that a tool can return. A **shown count** is the number of lookup results in concise lookup output. A **truncation status** shows if the tool did not show all lookup results. |
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
| Performance result | A **journey remainder** is the full-journey CPU or wall time minus the measured stage times. **Cleanup** is product work that releases temporary resources and leaves the required retained state after an operation. A **cleanup result** is that retained state. Cleanup can occur in a measured journey or during Teardown; it is not a synonym for Teardown. A **discrete invariant** is an exact object, recompute, cache, lifecycle, or cleanup result. **Measurement noise** is variation that the product change does not cause. |
| Performance journey | A **cold journey** starts in a new process. A **warm cycle** does the accepted journey again in the same process. **Warm reuse** and **deterministic reuse** keep their performance-record meanings. |
| Performance boundaries | An **unmeasured boundary** is product work that the measurement profile does not measure. An **application span** is a measurement interval for one application command. **Setup** is product work before the measured operator journey. **Teardown** is product work after that journey. |
| Performance investigation | **Retained negative evidence** is preserved evidence from a candidate with a FAIL comparison result or a required invariant difference. An **exhausted performance direction** is a performance hypothesis that has sufficient retained negative evidence to stop new product work in that direction. A **baseline-attribution investigation** measures one accepted operator journey and reports each **measurement area** without a product change. An **attribution series** is a set of process samples from that investigation. |
| Attribution statistics | Three values give the **attribution noise floor**. They are the Edit CPU MAD for the baseline, the Edit CPU MAD for attribution, and the maximum of the calibrated instrumentation overhead. The noise floor is the highest of these three values. The **attribution materiality rule** gives PASS when the first quartile for an applicable measurement area is higher than that floor. An **unattributed remainder** is measured journey time that is not part of a different measurement area. |
| Attribution evidence | A **same-host baseline** uses one exact host profile. **Test-owned instrumentation** is measurement logic that is not product source. **Instrumentation overhead** is the measured cost that test-owned instrumentation adds. An **attribution collector** records the attribution series. An **attribution corpus** is the retained method, baseline, instrumentation, result, failure classification, and checksum manifest for one investigation. A **live read** reads current FreeCAD property state. |
| Attribution source | A **repeated read** reads all data from the same live record again in one Edit. **Selected-record data** is all canonical data for the selected record. A **pre-registered method** records measurement and decision rules before measurements start. A **fixture-failure classification** identifies a retained fixture or harness failure. |
| Export | **Sentinel**, **DXF**, **manifest**, **schema**, **API**, and **JSON** keep their meanings from software or export specifications. |
| Railway | **Centreline**, **plain line**, **chainage**, **station**, **turnout**, **crossover**, and railway behaviour use the canonical railway meanings below. TrackTemplate approves the spelling **Centreline** for this railway context. |
| Official sources | A **standard** is an external reference that has a requirement set. **ASD-STE100 Issue 9**, **Simplified Technical English (STE)**, and **S1000D** identify standards. **Technical noun**, **technical verb**, **normative standard**, **official standard**, **official source**, **external reference**, **conformance**, **official conformance assessment**, and **linguistic conformance** are standards terms. |

Use these technical verbs only with their stated project meanings:

| Technical verb | Project meaning |
| --- | --- |
| **Validate** | Do a named check and examine its result in the stated bounded scope. |
| **Reconcile** | Compare a presentation or record with its canonical authority. Correct or report a difference. |
| **Authorize** | Give the exact authority in an explicit owner decision. |
| **Admit** | Accept named evidence for a bounded criterion without wider authority. |
| **Freeze** | Record one exact candidate and its exact content state for validation and review. |
| **Adopt** | Make a named standard or policy the normative standard for its stated bounded scope. |
| **Approve** | Add a TrackTemplate technical noun or technical verb to the canonical technical-term register. |
| **Bind** | Connect derived retrieval data to one authorised source identity. |
| **Claim** | Tell readers that a named capability, status, or assurance applies. |
| **Own** | Be the one canonical source for a specified item. |
| **Review** | Examine a named logical unit or review candidate against stated criteria. |
| **Preserve** | Keep specified repository data, local source, evidence, or project authority available without a change. |
| **Map** | Connect a responsibility to its canonical document or workflow owner. |
| **Rebuild** | Regenerate the derived cache after source and input validation. |
| **Retrieve** | Give source material for a lookup query. Do not change full applicability. |
| **Optimise** | Increase source efficiency without a decrease to the requirement set. |
| **Resolve** | Give one accepted status to a specified finding or ambiguity. |
| **Return** | Give a result from a local tool operation. |
| **Extract** | Use the PDF extractor to get source text from verified source bytes. |
| **Reproduce** | Make a copy of external source material. |
| **Fail closed** | Stop the operation if an identity is missing. Stop it after a `FAIL` validation result. |
| **Narrow** | Remove part of a requirement set or bounded claim. |
| **Migrate** | Move information or behaviour between specified states or limits. |
| **Report** | Give a result or limitation without project authority. |
| **Record** | Put specified evidence or data in its canonical owner. |
| **Name** | Give the exact identifier or term for a specified project item. |
| **Define** | Record the exact bounded scope, controlled meaning, or condition in a canonical authority. |
| **Bound** | Limit a claim, decision, task, or review to an explicit bounded scope. |
| **Copy**, **stage**, **commit**, **push**, **publish**, **merge**, **rebase**, and **squash** | Do the related Git or GitHub operation. |
| **Route** | Send a responsibility or task to its named canonical document or workflow owner. |
| **Qualify** | Accept one exact host profile after the specified compatibility evidence and owner decision. |
| **Requalify** | Qualify a different exact host profile against the same compatibility contract. |
| **Classify** | Put a validation result with `FAIL` in a failure class that the testing policy defines. Put a local-state inventory item in a local-state type that the recovery policy defines. |
| **Regenerate** | Do an evidence workflow again. Replace its retained result. |

Do not use different technical terms for the same project concept. Do not use
a technical noun as a verb unless this register also approves the verb. Add a
new term only when it is necessary for a specified TrackTemplate item. The applicable
Issue 9 category must permit the term. Do not change established identifiers.

## Canonical track terms

- **Plain line** is railway track without switches and crossings (S&C). Use
  **plain line track** on first mention where the audience may not know the
  term, and **plain-line** when it modifies another noun, such as
  "plain-line workflow" or "plain-line fixture".
- Plain line may be straight, circular, transitioned/eased, single-track or
  multiple-track. **Plain** classifies the absence of S&C. It does not mean
  geometrically straight.
- **Switches and crossings (S&C)** is the contrasting infrastructure class.
  In this project, turnouts and crossovers are S&C or **special trackwork**.
- **Straight**, **curve**, **easement/transition**, **station/chainage** and
  **multiple-track** describe alignment or layout properties independently of
  whether the track is plain line or contains S&C.

This usage follows the Office of Rail and Road definition of
[plain line as track without switches and crossings](https://www.orr.gov.uk/glossary)
and its definition of
[plain line track as sections without switches and crossings](https://www.orr.gov.uk/media/28096/download).
ORR also describes the track as plain line, consisting of fixed rails,
or S&C, containing the movable rails that permit a train to move between plain
lines, in its
[Track and Lineside strategy](https://www.orr.gov.uk/sites/default/files/om/safety-strategy-chapter-6a-track.pdf).

## Project writing and naming

- Do not use **ordinary track** as a railway category in new prose,
  UI wording,
  tests, filenames, schema fields, or APIs.
- Prefer **routine editing** for the normal interactive path and
  **standalone Python** for Python running outside FreeCAD. Those meanings are
  unrelated to plain line.
- New Python names should use `plain_line`, not `ordinary_track`.
- Do not replace every occurrence of *ordinary* mechanically. Existing chair,
  timber, and component classifications require their own source-based review.
  They are not automatically synonyms for plain line.

## Compatibility and evidence

B14 is the immutable legacy comparison oracle. B15 is the accepted Phase 1
behavioural reference. Their source text and hashes remain unchanged by this
terminology decision.

- B14 SHA-256:
  `51dc8cc1b3803b870649cb6292fbb1ae6bfbd5dc10733c1e5611892cdaa4e088`
- B15 SHA-256:
  `3ac26e395a8d4eacb1ae6108c12986932fbce94bb2f8d398ee0ec80c0706a848`

Phase 1 filenames, import names, recipe IDs, JSON keys, output directories, and
paths that contain both `benchmark` and `ordinary` in their names are legacy
evidence identifiers. Keep them stable so committed reports and contracts that
require reproducibility do not drift. Live canonical prose should describe the railway
item as plain line. It can label the identifier as legacy where necessary. New modular
interfaces must use the canonical terminology. Compatibility adapters can
retain or translate a legacy identifier until its retirement gate is accepted.

## Deferred source correction

The accepted macros contain at least these track-context phrases:

- `ordinary parallel tracks`
- `ordinary single-road timbers`

The first should become plain-line terminology in an approved replacement
version. The second needs a focused timber-language review to establish
whether it means plain-line, independent single-road, non-shared, or another
specific support class before its wording changes. The macros also contain
several `ordinary chair` labels. Review those against their REA/Templot source
controlled meaning separately. Do not change them as part of the track-category
correction.

Any replacement-macro wording change must have an approved version bounded
scope. It must include proportionate tests for affected UI or persisted values.
It must also include updated source fingerprints. The evidence must confirm
that geometry, ordering, identities, production data, and exports are
unchanged.
