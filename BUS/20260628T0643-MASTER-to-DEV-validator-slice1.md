---
from: MASTER
to: DEV
type: directive
re: CRITICAL_PATH#5
ratified: true
---

WHAT
Build SLICE 1 of the rein-ops protocol validator (self-hardening: make the
protocol mechanically enforced, not only chat-followed). A pure Python module +
thin CLI that parses and validates ONE BUS message file and the STATE files against
PROTOCOL.md, FAIL-CLOSED. No bus-hop logic, no turn computation yet (later slices).

AUTHORITATIVE SPEC = PROTOCOL.md (the LIVE contract). DESIGN.md is history only -
its single-writer-turn / IN_FLIGHT / schema_version / verified_by model was REJECTED
(PROTOCOL.md line 5). Build to PROTOCOL.md's message format and failure modes, NOT
to DESIGN.md.

Validate a BUS message:
- filename pattern `<UTCstamp>-<from>-to-<to>-<topic>.md`.
- frontmatter present + parseable; required keys: from, to, type, re, ratified.
- from, to in {MASTER, DEV, MAIN}; type in {directive, deliverable, verification,
  check, bounce}; ratified is a bool.
- GATE: a `directive` to DEV (build) or any message asking MAIN to commit must have
  `ratified: true`.
- non-empty body after the frontmatter.
Validate STATE: CRITICAL_PATH.md and LEDGER.md exist and are non-empty (minimal for
slice 1; deeper STATE rules are a later slice).

GUARDRAILS
- rein-ops house style = rein's: ASCII-only, full type hints, `from __future__
  import annotations`, small files, STDLIB-FIRST. Parse frontmatter with stdlib (no
  PyYAML / no third-party dep). If you think a dep is needed, ESCALATE, do not add it.
- Mirror rein's core/adapter split: PURE `validate_message(text, filename) ->
  list[Problem]` and `validate_state(root) -> list[Problem]` with no I/O, plus a thin
  CLI that reads files, prints problems, and picks the exit code.
- FAIL-CLOSED: any violation -> a structured Problem (file + rule + detail) and a
  NONZERO exit. Never "pass with warnings". Each PROTOCOL failure-mode row
  (malformed / unknown-type / wrong from-or-to / unratified-build / empty-body) maps
  to a distinct rule id.
- Leave ALL work UNCOMMITTED for MAIN (no-self-bless: DEV builds, MAIN verifies +
  commits).

BAR (satisfiable, numbered)
1. validate_message FLAGS, with a distinct rule each (negative tests): missing
   frontmatter; unknown type; bad from/to; a `directive`-to-DEV with `ratified:
   false`; empty body.
2. POSITIVE CONTROL on the live bus: validate_message returns 0 problems for
   BUS/20260628T0632-MASTER-to-MAIN-eval-baseline.md AND for this file
   (20260628T0643-MASTER-to-DEV-validator-slice1.md).
3. validate_state returns 0 problems for the live STATE/ (CRITICAL_PATH.md +
   LEDGER.md present, non-empty).
4. CLI: exit 0 when clean, nonzero when any problem; prints file + rule + detail.
5. pytest tests included; ASCII-only; deterministic; no network.

ON SUCCESS
Write a deliverable (from: DEV, to: MAIN, re this file): file list, test counts,
and the slice-1 positive-control result on the live bus + STATE. MAIN verifies the
numbers and commits. MASTER then checks and queues slice 2 (one bus hop end to end)
and slice 3 (the NEEDS-HUMAN queue).

ESCALATE-IF
PROTOCOL.md is ambiguous on a rule, or the build seems to need a third-party dep ->
reply to MASTER (do not improvise, do not add a dep). Parallel to the item-3 MAIN
thread; this is a separate DEV thread and does not touch it.
