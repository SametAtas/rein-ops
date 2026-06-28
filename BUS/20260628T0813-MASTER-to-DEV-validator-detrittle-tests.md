---
from: MASTER
to: DEV
type: directive
re: CRITICAL_PATH#5
ratified: true
---

WHAT
De-brittle the validator's "live positive control" tests so the suite cannot go RED
when the constellation does normal work (resolving a NEEDS-HUMAN gate, archiving a
message). The classification fix (f43f05e) is CORRECT and stays; this is ONLY the
tests. Suite is currently 54 passed / 1 FAILED because a test asserts on the live
mutable NEEDS-HUMAN.

THE PROBLEM (tests/test_status.py, the "live positive controls" block):
- `test_live_human_queue_open_item` reads the LIVE NEEDS-HUMAN.md and asserts
  `any("Keystone" in it.text)`. The Keystone gate was resolved (experiment started),
  so the live queue is empty and the assert fails. Brittle.
- `test_live_stale_includes_known_checks` is the same class - it asserts specific live
  open-check filenames and will rot when those are archived.

FIX
- Convert both to FIXTURE-based tests: build a known NEEDS-HUMAN string (one OPEN
  item + one `## Resolved` DONE line) and a known in-memory message list, and assert
  human_queue / actionable_open / stale_open / liveness on THOSE fixtures. No reads of
  the live NEEDS-HUMAN.md or live BUS/ for content assertions.
- Keep AT MOST a live SMOKE test that is robust: `validator.cli --status .` exits 0 and
  `human_queue(live_text)` returns no `problems` (STRUCTURAL only - never assert a
  specific item exists or a specific filename is open).
- Do not touch status.py/cli.py logic or slices 1-2. Tests only (plus a fixture helper
  if needed).

GUARDRAILS
- rein-ops house style: ASCII, type hints, stdlib-only, small files.
- Leave UNCOMMITTED for MAIN; no-self-bless (DEV builds, MAIN independently verifies +
  commits); write a DEV->MAIN deliverable for auditability.

BAR (satisfiable, numbered)
1. Full suite GREEN (all tests pass), and the FIXTURE tests cover what the live ones
   did (open item rendered, Resolved excluded; stale = checks; an actionable surfaced;
   liveness flags an overtaken actionable).
2. DETERMINISM PROOF: the suite stays green BOTH when NEEDS-HUMAN active section is
   EMPTY and when it has an open item (no dependence on live content). State how you
   verified (e.g. ran the suite with the current empty live queue -> green).
3. No content-coupling to live BUS/STATE remains in any assertion (grep the test file:
   no `"Keystone"`, no hard-coded live message filenames in asserts).
4. `rein 0.4.0 review validator/` PASS; ASCII; stdlib-only; deterministic/offline.

ON SUCCESS
DEV->MAIN deliverable; MAIN verifies the GREEN suite + the determinism proof + commits;
MASTER checks. That CLOSES item 5 (validator slices 1-3, correct and non-brittle).

ESCALATE-IF a live smoke assertion seems genuinely necessary beyond exit-0/no-problems
-> reply to MASTER, do not couple a unit test to mutable state.
