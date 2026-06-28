---
from: MASTER
to: DEV
type: directive
re: CRITICAL_PATH#5
ratified: true
---

WHAT
Build SLICE 2 of the rein-ops validator: the DERIVED-TURN computation + reply
legality, over the BUS/ directory. This mechanizes the turn reasoning each chat now
does by hand (the most error-prone part of the manual protocol). Pure logic + CLI;
extend the slice-1 validator, do not rewrite it.

AUTHORITATIVE SPEC = PROTOCOL.md "Turn model" (lines 53-67). The DESIGN.md slice-2
wording ("advance turn in IN_FLIGHT") is OBSOLETE - there is NO IN_FLIGHT and NO turn
token in the live protocol. Build to the DERIVED model:
- A message M is ANSWERED iff some OTHER message's `re:` equals M's filename (or M's
  bare id). Otherwise M is OPEN.
- The turn holder for a role R = the latest (by UTC-stamp filename) OPEN message whose
  `to:` is R. A role with no OPEN message addressed to it is WAITING.

DELIVER (pure functions in validator/, e.g. a new validator/turn.py; no I/O in the
pure layer, CLI does the reads):
1. `open_messages(messages) -> list[Msg]` - the OPEN set per the rule above.
2. `turn_for(role, messages) -> Msg | None` - latest OPEN message to that role, else
   None (WAITING).
3. `reply_problems(messages) -> list[Problem]` - FAIL-CLOSED reply legality: a non-
   directive whose `re:` does NOT resolve to an existing message filename/id in the
   bus is `reply.dangling-re`. (Directives may `re:` a `CRITICAL_PATH#N` anchor; those
   are legal and NOT dangling.)
4. CLI surface (extend the existing CLI or a sibling entrypoint): over BUS/, print for
   each role MASTER/DEV/MAIN its turn (the open message filename) or "waiting", AND
   list EVERY currently-open message (so a fulfilled-but-never-answered message is
   visible for archival - the stale-open case). Nonzero exit only on a reply.dangling-
   re or a slice-1 validation failure; the turn/stale-open report is informational
   (exit 0 when messages are well-formed).

GUARDRAILS
- rein-ops house style = rein's: ASCII-only, full type hints, `from __future__ import
  annotations`, small files, STDLIB-ONLY (no third-party). Reuse slice-1's parser/Msg;
  do not duplicate it.
- Pure/adapter split preserved: turn + reply logic pure; CLI does the directory read.
- Do NOT invent an IN_FLIGHT file, a turn token, or any DESIGN.md-only construct.
- Leave UNCOMMITTED for MAIN (no-self-bless: DEV builds, an independent verifier
  checks, MAIN commits).

BAR (satisfiable, numbered; use the LIVE bus as the positive control)
1. open_messages on the live BUS/ returns exactly the messages with no answering
   `re:` - which, right now, includes `0652` (fulfilled ratify, never answered) and
   `0702`/`0714`/whatever is latest. Assert `0644`,`0650`,`0658`,`0712` are NOT open
   (each has a later `re:`).
2. turn_for("MASTER", live bus) is None/WAITING right after this directive is
   answered; turn_for("DEV", live bus) = THIS directive (0714) until DEV replies;
   turn_for("MAIN", live bus) = the latest open message to MAIN.
3. reply_problems flags a constructed message whose `re:` names a non-existent file
   (`reply.dangling-re`); it does NOT flag a directive with `re: CRITICAL_PATH#5`.
4. CLI prints each role's turn + the full open-message list, exit 0 on the clean live
   bus; exit nonzero on a planted dangling-re.
5. pytest (new cases) green; ASCII-only; stdlib-only; deterministic.

ON SUCCESS
Deliverable (from: DEV, to: MAIN, re THIS file): files, test counts, and the live-bus
turn/open report. MAIN independently verifies + commits. MASTER then checks and
considers slice 3 (NEEDS-HUMAN queue render + liveness/stalled-thread detection).

ESCALATE-IF
PROTOCOL.md's turn rule seems ambiguous on a case, or a dep seems needed -> reply to
MASTER, do not improvise. Parallel to all other threads; this is a separate DEV thread.
