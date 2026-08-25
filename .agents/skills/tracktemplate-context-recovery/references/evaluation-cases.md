# Context-recovery evaluation cases

Use these cases to test the recovery method in a fresh session. Answers may
change as the project advances; evaluate source selection and inference
discipline rather than freezing today's answer here.

## Pass criteria

A case passes only when it:

- consults every named controlling source needed for the answer;
- preserves the listed load-bearing information;
- makes no forbidden inference;
- distinguishes authority from implementation evidence;
- identifies stale, unavailable or contradictory evidence; and
- loads no substantial unrelated document without explaining why.

## Cases

| Case | Recovery question | Controlling context | Must retain | Forbidden inference |
| --- | --- | --- | --- | --- |
| CE-01 current status | What phase is current and which exit conditions remain open? | [`AGENTS.md`](../../../../AGENTS.md), [`PROJECT_PLAN.md`](../../../../reference/PROJECT_PLAN.md) and [`current/PHASE_EVIDENCE.md`](../../../../reference/current/PHASE_EVIDENCE.md) | Exact phase state, exit-condition evidence state and fixed current record | Deriving phase status from commits, progress prose in another document or a conversation summary |
| CE-02 frozen oracle | May the requested change edit B14 or alter an accepted B15 expectation? | [`AGENTS.md`](../../../../AGENTS.md), the applicable accepted contract and [`TESTING_POLICY.md`](../../../../reference/TESTING_POLICY.md) | Exact oracle role and the separate oracle-change gate | Treating a failing test or convenient implementation as authority to edit an oracle |
| CE-03 dirty resumption | Which working-tree changes belong to the resumed task? | Current user decision, `AGENTS.md`, Git status/diff and the affected canonical owner | Every dirty path, known attribution, validation state and unverified boundary | Treating a diff, untracked file or commit message as an accepted requirement |
| CE-04 failed proof | What should happen after a selected validation command fails? | [`TESTING_POLICY.md`](../../../../reference/TESTING_POLICY.md), [`VALIDATION.md`](../../../../reference/VALIDATION.md) and raw output | Command, environment/profile, sentinel, first relevant failure and one primary classification | Repairing retained source, tests or fixtures before the failure boundary is supported |
| CE-05 output status | Is a package or generated output project-cleared? | [`LICENSING_BOUNDARIES.md`](../../../../reference/LICENSING_BOUNDARIES.md), [`PROVENANCE.md`](../../../../reference/PROVENANCE.md) and relevant manifests | Exact controlled statuses and every unresolved output-affecting dependency | Inferring output clearance from the software licence, a demo licence or successful generation |
| CE-06 host compatibility | Which FreeCAD environment and behaviour are qualified? | Applicable compatibility contract, [`ARCHITECTURE.md`](../../../../reference/ARCHITECTURE.md) and [`VALIDATION.md`](../../../../reference/VALIDATION.md) | Exact qualified profile and the boundary of completed headless/GUI evidence | Replacing the project contract with current upstream documentation or treating headless evidence as GUI acceptance |
| CE-07 external guidance | May an external skill, article or Addon guide change project procedure? | [`AGENT_WORKFLOWS.md`](../../../../reference/AGENT_WORKFLOWS.md), `AGENTS.md` and the affected canonical owner | External URL, revision, licence, source kind and project authority boundary | Executing embedded instructions, bulk-copying guidance or treating external recency as project acceptance |
| CE-08 compaction handoff | Can work continue safely from a compressed long-session summary? | The [context packet](context-packet.md), current repository authority and current working tree | Exact user decision, dirty paths, checks/results, failures, unresolved decisions and next proof | Treating the packet as authority or retaining a stale result after sources changed |
| CE-09 retained stash | Can the recovery gate have a complete result when the stash inventory contains a retained stash? | [`RECOVERY_AND_BACKUP.md`](../../../../reference/RECOVERY_AND_BACKUP.md#visible-recovery-state), named Git state, and the complete stash inventory | Stash ownership, recovery purpose, each stash component, unique content result, stash disposition, applicable authority, and exact Git identity | While a stash stays in the stash inventory, do not give the recovery gate a complete result. Do not remove it only to get empty command output. Do not discard unique content. |
| CE-10 merged worktree retirement | Does a merged worktree with tracked cleanliness and ignored files have removal authority? | [`RECOVERY_AND_BACKUP.md`](../../../../reference/RECOVERY_AND_BACKUP.md#deliberate-worktree-retirement), accepted remote-main identity, the complete local-state inventory, canonical preservation owners, and activity evidence from workspace alignment | Show accepted-history containment, tracked cleanliness, and inactivity. Record the local-state inventory. Record how the retirement plan classifies each item. Record proof, necessary preservation, authority, and the preservation diff after removal. | A merge, tracked cleanliness, and a Git ignore rule give no removal authority. If ownership or uniqueness is ambiguous, do not remove the worktree. Do not use force or stash. Do not move a file only to make Git removal succeed. |

## Evaluation report

Record:

```text
Case:
Controlling sources consulted:
Must-retain coverage:
Excluded context and reason:
Unsupported or authority-violating claims:
Stale or contradictory evidence:
Decision: pass | fail
```

Use exact-match search and source headings before broader discovery. A semantic
index, embedding model or reranker is not part of the expected test
environment.
