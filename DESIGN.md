# rein-ops DESIGN (v1)

STATUS: SUPERSEDED by PROTOCOL.md (owner decision 2026-06-28). The LIVE model is
the poll-loop file bus in PROTOCOL.md: three real chats poll this shared dir and
WAIT for each other's output. This file's single-writer IN_FLIGHT/turn-token model
was rejected by the audit (below); PROTOCOL.md replaces it with a DERIVED turn
(turn = `to` of the latest unanswered message) which removes the single-writer
contradiction, the turn-token race, and the deadlock. Kept as the rationale record.

PRIOR STATUS (superseded): SHELVED. The file-bus was NOT being built. An
independent two-agent audit found (1) a file bus cannot self-trigger across separate
chat sessions, so it does not remove the human-as-scheduler - only a single
orchestrator driving role sub-agents achieves true auto-communication; (2) structural
blockers in this draft (IN_FLIGHT single-writer vs the turn model, crash/no-output
deadlock, message-id allocation race). The owner ratified the ORCHESTRATOR model
instead: one driver chat spawns the roles as sub-agents (see the constellation memory
note "ORCHESTRATOR PIVOT"). This file is kept only as the record of why the file-bus
was rejected. Do NOT implement it. rein-ops, if created later, persists an audit trail
of loop runs - it is not the comms layer.

SUBORDINATION: rein-ops is subordinate to the Keystone chain. Its tasks NEVER
preempt CRITICAL PATH items 1-4 (0.4.0 release, arm pin, 429 fix, clean Keystone
restart). DEV builds rein-ops only AFTER this design is FROZEN AND the Keystone
chain is executing.

## Purpose

Lower handoff friction between the constellation chats (MASTER, MAIN, DEVELOPMENT,
AUDITOR) by replacing copy-paste with a structured, file-based message bus, while
preserving every guardrail that currently keeps rein clean. Automate the BUS (how
work is handed off and surfaced); never automate the JUDGMENT (ratification,
independent verification, direction). Automation level (a): file-bus plus the human
as trigger and ratifier. No cross-session autonomy.

## Non-goals (frozen)

- NOT part of the rein engine and NOT a sellable product. It is internal build
  tooling. The engine/Ringo is the product, on its own track.
- NO ratification, independent-verify, direction, or public/PyPI action is
  automated. Those stay human and mechanically gated.
- NO engine code, no rein import, no dependency coupling to rein/.

## Repo boundary (the anti-mess rule)

rein-ops is a SEPARATE repo. The rein engine repo stays pure and dependency-free.
No orchestration code, bus files, or loop scripts ever land in rein/. House style
matches rein: ASCII-only, terse, factual, type-hinted code, small files.

## Roles and lanes

Lane = the kind of work; routing is by lane, not by name.

| Role        | Lane    | May do                                                |
|-------------|---------|-------------------------------------------------------|
| MASTER      | ratify  | direction, route tasks, ratify, own CRITICAL_PATH+LEDGER |
| DEVELOPMENT | build   | generate/edit code to a frozen spec                   |
| MAIN        | verify  | verify with numbers, commit, doc/memory maintenance   |
| AUDITOR     | audit   | independent cross-check of directives AND outputs     |

A chat acts ONLY on a message whose `to` is its role and whose `lane` matches its
lane. Anything else is bounced (see lane-as-routing).

## Directory layout

```
rein-ops/
  DESIGN.md            this file (frozen contract)
  STATE/
    CRITICAL_PATH.md   single-writer: MASTER. The one ordered list, item 1 = now.
    LEDGER.md          single-writer: MASTER. Append-only ratified decisions.
    IN_FLIGHT.md       single-writer: MAIN. Active item, holder, turn token.
  BUS/
    <NNNN>-<from>-<to>-<topic>.md   one message per file, monotonic NNNN
  NEEDS-HUMAN.md       append-only by any chat. The only file the human watches.
  ARCHIVE/             closed BUS messages moved here (keeps BUS small)
```

## BUS message schema (versioned, self-contained, typed)

Each message is one file, self-contained (a fresh chat continues from it plus the
repo, never from chat history). YAML frontmatter then a markdown body.

```
---
schema_version: 1
id: 0007                 # monotonic, zero-padded, matches filename prefix
from: MASTER             # MASTER | MAIN | DEV | AUDITOR
to: DEV                  # the single recipient role
lane: build              # build | verify | audit | ratify  (must match `to`'s lane)
type: directive          # directive | deliverable | verification | ratification | bounce
re: "CRITICAL_PATH#1"    # the item this concerns; or a prior message id
ratified: true           # MASTER-set; build/commit only proceed when true
verified_by: null        # role that independently verified (no-self-bless gate)
status: open             # open | done
---

WHAT / WHY / GUARDRAILS / numbered BAR / on-success / escalate-if.
(For a directive, the BAR must be SATISFIABLE by the stated slice.)
```

Field rules:
- `type` must match the lane: a `build` directive is `type: directive` to DEV; a
  `deliverable` flows DEV -> MAIN; a `verification` is written by a role != the
  builder; a `ratification` is MASTER-only.
- `verified_by` MUST be set and MUST differ from the builder before MAIN commits.
- `ratified: true` is required before DEV builds or MAIN commits a directive's work.

## STATE files (single-writer each)

Single-writer eliminates write races. A non-owner editing a STATE file is treated
as tampering (fail-closed, see failure modes) - the same tamper-guard discipline
rein applies to its own config.

- CRITICAL_PATH.md (MASTER): the one ordered list; item 1 is the only "now". Every
  directive restates item 1. Displacing it needs an explicit MASTER LEDGER entry.
- LEDGER.md (MASTER): append-only; a ratified decision cannot be silently dropped;
  reversal is a NEW entry citing the reversal.
- IN_FLIGHT.md (MAIN): `active_item`, `holder` (role currently working), `turn`
  (whose move it is), `awaiting` (what output unblocks the next turn).

## Turn-taking (chats wait for the working chat's output)

There is at most ONE active item and ONE turn holder at a time. A chat that is not
the current `turn` holder on the `active_item` WAITS - it does not start work on
that item. The turn advances only when the working chat emits its BUS output:

```
MASTER (route, ratified directive) -> DEV (build) -> deliverable
  -> AUDITOR (independent verify) -> verification
  -> MAIN (verify + commit) -> done
  -> MASTER (advance CRITICAL_PATH)
```

MAIN, as the single writer of IN_FLIGHT.md, advances `turn` based on the arriving
BUS message. No chat self-advances its own turn. A chat acting out of turn is a
violation (failure mode below). Parallel non-blocking work (e.g. Keystone on DEV)
runs on a SEPARATE active item track, never sharing a turn token with the main item.

## Core mechanics

- FAIL-CLOSED: on any malformed, missing, unknown-version, or wrong-lane input, a
  chat does NOT proceed and does NOT guess. It writes NEEDS-HUMAN and halts that hop.
  Silence over a wrong action (mirrors rein's fail-closed profile loading).
- LANE-AS-ROUTING: a chat executes only messages whose `to`+`lane` are its own. A
  build task that lands on MAIN (verify lane) is BOUNCED (type: bounce) to MASTER for
  re-routing; it is never executed. (This encodes the code-gen role boundary.)
- NO-SELF-BLESS: the builder is never the sole verifier. MAIN may not commit work
  whose `verified_by` is null or equals the builder role. An independent verify
  (AUDITOR or a non-builder) is mandatory.

## Failure modes (required behavior - frozen)

| Condition                                  | Required behavior                                   |
|--------------------------------------------|-----------------------------------------------------|
| Malformed message (bad/missing frontmatter)| Fail-closed: do not act; NEEDS-HUMAN `malformed <id>`; halt hop |
| Missing referenced message / STATE file    | Fail-closed: do not infer; NEEDS-HUMAN; halt        |
| Unknown schema_version (> supported)       | Fail-closed: no parse-guessing; NEEDS-HUMAN; halt   |
| Wrong lane (lane/`to` != this chat)        | BOUNCE (type: bounce) to MASTER; do not execute     |
| Unratified directive (`ratified: false`)   | Do not build/commit; BOUNCE to MASTER for ratify    |
| Self-bless (`verified_by` null or == builder)| Reject; commit blocked; NEEDS-HUMAN / request independent verify |
| Acting out of turn                         | Prohibited; WAIT; if detected, NEEDS-HUMAN          |
| Non-owner edit of a STATE file (tamper)    | Fail-closed: treat as tampering; NEEDS-HUMAN        |
| Duplicate / stale directive (already done) | Re-confirm against STATE; if done, BOUNCE, do not redo |

## NEEDS-HUMAN.md queue

The single place the human watches. Append-only, one line per item:

```
- [0007] [MASTER] ratify Keystone arm pin commit - reply b0a52f9 or 0.4.0
- [0008] [MAIN] malformed BUS 0006 from DEV - inspect or re-send
```

Format: `- [<msg-id>] [<chat that needs you>] <action> - <how to respond>`. The
human resolves and strikes the line. Nothing blocks silently.

## Lifecycle of one task (end to end)

1. MASTER writes a `ratified: true` build directive (lane build, to DEV), restates
   CRITICAL_PATH item 1, sets IN_FLIGHT via... (MASTER asks MAIN to open IN_FLIGHT,
   or MASTER's directive is the trigger and MAIN opens it). turn -> DEV.
2. DEV builds the frozen slice, writes a `deliverable` (DEV -> MAIN). turn -> AUDITOR.
3. AUDITOR independently verifies, writes a `verification` (`verified_by: AUDITOR`).
   turn -> MAIN.
4. MAIN runs the numbered BAR, confirms `verified_by != builder`, commits, marks the
   directive `status: done`, closes BUS messages to ARCHIVE. turn -> MASTER.
5. MASTER advances CRITICAL_PATH. If any gate fails: BOUNCE, never rationalize past it.

## What DEV builds (deferred until FROZEN + Keystone executing)

Thin, independently verifiable slices, in order:
1. format + parse + validate a BUS message and a STATE file (schema_version,
   required fields, lane/type match); fail-closed on every failure-mode row.
2. one bus hop end to end (write -> read -> validate -> advance turn in IN_FLIGHT).
3. the NEEDS-HUMAN queue (append + render).

Each slice ships with tests, ASCII-clean, and is verified by a non-builder before
commit (the protocol applies to rein-ops itself).

## Freeze criteria

This design is freezable when MASTER confirms: the BUS schema, the single-writer
STATE assignment, the turn model, the three core mechanics, and every failure-mode
row are correct and complete. On freeze: change the STATUS header to FROZEN (vN),
then MAIN creates the rein-ops repo and lands this file as commit 1.
```
