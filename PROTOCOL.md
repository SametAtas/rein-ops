# rein-ops PROTOCOL (v1, poll-loop file bus)

The LIVE operating contract for the constellation. Three real Claude Code chats
coordinate through this shared directory by polling - no human relays content.
(History/rationale and the rejected single-writer turn model: see DESIGN.md.)

NOT in the rein engine repo. Internal tooling, never sold.

## Roles (one real chat each)

- MASTER  (lane: ratify+audit) - direction, new features, ratifies decisions,
  CHECKS MAIN's commits. Sole writer of STATE/CRITICAL_PATH.md and STATE/LEDGER.md.
- DEV     (lane: build)        - writes/edits code to a ratified spec. Leaves work
  uncommitted for MAIN. Never decides direction, never self-verifies.
- MAIN    (lane: verify+commit)- verifies DEV's work with NUMBERS, commits, pushes,
  drives the path. Never generates code. Never self-blesses.

The human is above all three: ratifies anything in NEEDS-HUMAN (direction sign-off,
release, env changes) and starts each chat's loop once.

## Files

```
rein-ops/
  PROTOCOL.md            this contract (every chat reads it each loop)
  STATE/
    CRITICAL_PATH.md     ordered task list, item 1 = now (MASTER writes)
    LEDGER.md            append-only ratified decisions (MASTER writes)
  BUS/                   one message per file (each chat writes ONLY its own)
    <ts>-<from>-to-<to>-<topic>.md
  NEEDS-HUMAN.md         the only file the human watches (any chat appends)
  ARCHIVE/               answered messages may be moved here (optional, MAIN)
```

## Message format (self-contained, typed)

Filename: `<UTCstamp>-<from>-to-<to>-<topic>.md` (e.g.
`20260628T1530-MASTER-to-DEV-pin-arm.md`). The `<from>` in the name plus the
stamp make every filename unique, so two chats never collide (each writes only
its own messages). Frontmatter then a markdown body:

```
---
from: MASTER          # MASTER | DEV | MAIN
to: DEV               # the single recipient role
type: directive       # directive | deliverable | verification | check | bounce
re: <prior msg filename or "CRITICAL_PATH#1">
ratified: true        # MASTER-set; build/commit proceed only when true
---
WHAT / WHY / GUARDRAILS / numbered BAR (satisfiable) / on-success / escalate-if.
```

## Turn model (DERIVED - no shared mutable turn, no race, no deadlock)

There is NO central turn field. The turn is computed from the bus:

- A message M is ANSWERED if some later message has `re: M`. Otherwise M is OPEN.
- The turn holder of a thread = the `to:` of its latest OPEN message.
- Each chat's loop: scan BUS/. If the latest OPEN message addressed to MY role
  exists, it is MY turn - act, then write a REPLY (`from: me`, `to: <next role>`,
  `re: <that msg>`). If none is addressed to me, I WAIT (poll again).

Because every chat only ever CREATES its own message files (never edits another
chat's file, never writes a shared turn token), there is no write race and no
single-writer contradiction. Parallel threads (e.g. a Keystone track) are just
separate open messages to different roles - each chat serves its own, no shared
token to collide on.

## The poll loop (each chat, started once by the human)

Every cycle, in order, FAIL-CLOSED:
1. Read PROTOCOL.md, STATE/CRITICAL_PATH.md, STATE/LEDGER.md.
2. Scan BUS/ for the latest OPEN message addressed to my role.
3. If none: report "<ROLE> waiting" and end the cycle (loop will re-poll).
4. If one exists, VALIDATE it (frontmatter present, known type, lane matches my
   role, `ratified: true` if it asks me to build/commit). On ANY validation
   failure: append NEEDS-HUMAN, do NOT act, end cycle.
5. Act per my lane (below). Write my reply message. If I am MASTER, update
   STATE as needed. End cycle.

## Lane rules + gates

- LANE-AS-ROUTING: act only on messages whose `to:` is my role. A build need that
  somehow reaches MAIN is BOUNCED (type: bounce) to MASTER, never executed.
- NO-SELF-BLESS: a `verification` (MAIN of DEV) or `check` (MASTER of MAIN) must
  have a `from:` different from the work it judges. If asked to verify my own
  output, refuse and append NEEDS-HUMAN.
- RATIFICATION: DEV builds and MAIN commits only when the driving directive has
  `ratified: true`. Else BOUNCE to MASTER.
- HUMAN GATES (always NEEDS-HUMAN, never auto): direction sign-off, public
  release / PyPI, anything that alters the running Keystone experiment.
- FAIL-CLOSED: malformed / missing-referenced / unknown-type / wrong-lane /
  unratified-build -> append NEEDS-HUMAN and stop; never guess.
- LIVENESS: if I am the sender and my message stays OPEN across several of my own
  cycles (addressee not acting), append NEEDS-HUMAN "<to> stalled on <msg>". A
  stalled chat is thus visible, not a silent deadlock.

## Standard task flow

MASTER directive (ratified, to DEV) -> DEV deliverable (to MAIN) -> MAIN
verification+commit (to MASTER) -> MASTER check; on pass MASTER advances
CRITICAL_PATH and issues the next directive. Any gate fail -> NEEDS-HUMAN or a
bounce, never rationalized past.

## NEEDS-HUMAN.md

Append-only, one line: `- [<UTCstamp>] [<role>] <action> - <how to respond>`.
The human resolves and marks the line done. The single place to watch.

## Bootstrap

The human starts each chat's loop ONCE (the commands live in START-COMMANDS.md).
After that the chats hand off by polling; the human only touches NEEDS-HUMAN.
