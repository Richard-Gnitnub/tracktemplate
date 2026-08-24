---
name: tracktemplate-handoff
description: Create a temporary, authority-ranked TrackTemplate session handoff packet for an explicit transfer to a new chat, usage reset, long pause or another agent. Use only when the project owner explicitly invokes `$tracktemplate-handoff`; do not use for ordinary completion reports, same-session compaction or a second project-status record.
---

# TrackTemplate handoff

## Outcome

Write one concise temporary packet that lets a fresh session recover the task
without asking the project owner to reconstruct it. The packet is navigation,
not project authority, evidence acceptance or durable documentation.

## Invocation authority

Explicit invocation authorises read-only repository and applicable pull-request
inspection plus creation of one temporary handoff file. It does not authorise a
repository edit, commit, push, merge, branch change, project-document update,
owner decision, gate action or product change.

If an accepted durable fact is absent from its canonical owner, report that
gap in the packet. Do not repair the canonical record merely to complete a
handoff.

## Prepare

1. Read the
   [context-packet contract](../tracktemplate-context-recovery/references/context-packet.md)
   completely.
2. Read `AGENTS.md`, the applicable current-phase sections and only the
   canonical owners needed for the active task.
Read the
[visible recovery state procedure](../../../reference/RECOVERY_AND_BACKUP.md#visible-recovery-state)
in the canonical owner. Apply the procedure. The context packet is not planned
preservation. Record all unfinished work. Use named Git state when applicable
authority is available. Examine the complete stash inventory.

3. Inspect the working tree, branch, exact HEAD and upstream. When a pull
   request is applicable and live access is available, resolve its exact head,
   draft/open/merged state, mergeability and required checks.
4. Use invocation arguments as the next-session focus. Without arguments,
   infer the nearest safe action from current authority and evidence; do not
   invent an owner decision.
5. Distinguish accepted state, validated-but-unmerged work, dirty or
   ownership-ambiguous files, failed evidence and unverified claims.

## Write

Create a dedicated directory with the host's safe temporary-directory facility
and write `HANDOFF.md` inside it. Never write the packet into the repository,
stage it, commit it or treat it as current-phase evidence. If temporary storage
is unavailable, report that no handoff was created rather than falling back to
a durable project path.

Render the context-packet fields in a human-first document whose first three
sections are:

1. `What the project owner wants`;
2. `Where things stand`; and
3. `Next action`.

Include later sections only when useful:

- exact decisions and authority exclusions that must survive;
- current branch, HEAD, upstream, pull request, CI and dirty-path state;
- completed validation and classified failures, with exact commands and
  sentinels where they matter;
- relevant canonical paths, risk/decision IDs and retrieval triggers;
- open questions or claims the next session must reverify; and
- suggested repository skills, led by `$tracktemplate-context-recovery`.

Also include the complete stash inventory and stash disposition.

Link to canonical owners, commits, pull requests and logs instead of copying
their contents. Summarise background and raw output. Preserve exact user
wording only when paraphrase could change an owner decision or authority
boundary.

Do not include the conversation transcript, raw tool logs, unrelated history,
the full project plan or risk register, secrets, credentials, private tokens or
unnecessary personal data.

## Verify and announce

Before reporting success:

1. trace each live claim to the user, a canonical owner or current
   implementation evidence;
2. confirm paths and identifiers are exact;
3. confirm no qualifier such as proposed, validated, accepted, merged or
   project-cleared was upgraded;
4. confirm the packet contains the next action and nearest proof; and
5. confirm the packet is outside the repository and contains no sensitive
   material.

Report:

```text
HANDOFF WRITTEN: <absolute path>
Next session: Use $tracktemplate-context-recovery, read <absolute path>, then
continue from "Next action".
```

The receiving session must recheck live repository and external state before
acting. A stale or missing packet never blocks recovery from canonical sources.
