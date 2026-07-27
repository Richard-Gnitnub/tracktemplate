# TrackTemplate context packet

Use this transient packet before compaction, handoff, a long pause or recovery.
It preserves task state without becoming another plan, evidence record or
canonical owner.

## Packet

```text
Task and requested outcome:
Exact current user decisions:
Authority and current phase boundary:
Must-retain requirements, identifiers and invariants:

Hot context:
- dirty path — owner or attribution — intended purpose
- active failure — exact command/profile/sentinel — classification
- completed validation — exact command/profile/sentinel/result

Warm context:
- canonical source and section — reason loaded
- open-phase evidence and section — reason loaded
- applicable live risk IDs — required treatment or proof

Cold or excluded context:
- source — exclusion reason — trigger for retrieval

Contradictions or unresolved decisions:
Unverified claims or unavailable evidence:
Next safe action and nearest proof:
Packet prepared or verified:
```

## Retention rules

- Preserve explicit user decisions, stable identifiers, file paths, version
  numbers, units, risk IDs and controlled classifications exactly.
- Preserve the exact failing command, environment or profile, required
  sentinel, first relevant failure and primary classification.
- Distinguish user-owned or unattributed dirty changes from the current task.
- Summarise background and completed narrative; link to its canonical source.
- Mark a summary as compressed. It is navigation aid, not authority.
- Recheck live status, external revisions and the working tree after a new
  session rather than trusting packet age.
- Do not place secrets, credentials, unnecessary personal data or whole tool
  logs in the packet.

## Selective plan retrieval

From `reference/PROJECT_PLAN.md`, retrieve:

1. the document status and roadmap entry for the current phase;
2. the current phase gate register and named evidence record;
3. principal or QA risk rows relevant to the task; and
4. a closed-phase decision only when the task depends on that decision,
   accepted oracle or historical evidence.

Record other phase sections as excluded cold context. Do not create a second
live-status summary in another repository file.

## Loss-check questions

- Can every claimed requirement be traced to the current user, `AGENTS.md` or a
  canonical owner?
- Are the exact dirty paths, failures, checks and remaining actions present?
- Did compression change a qualifier such as proposed, active, evidenced,
  accepted, blocked or project-cleared?
- Does each sub-question have at least one authoritative source?
- Was any lower-authority or newer source allowed to displace a controlling
  source?
- Is every plausible omitted source either genuinely irrelevant or recorded
  with a retrieval trigger?
