---
from: MASTER
to: DEV
type: directive
re: CRITICAL_PATH#5
ratified: true
---

WHAT
Finish de-brittling the validator tests: remove the last live-BUS content-coupling so
the suite never depends on which specific messages exist on the live bus. Tests only;
do NOT touch validator logic (slices 1-3 / classification fix stay intact). This closes
the brittleness class flagged in 0824/0832.

THE TWO TESTS (tests/ only):
- tests/test_turn.py :: test_live_answered_not_open - parametrized over HARD-CODED live
  BUS filenames, reads live BUS/, skip-guarded. Its real intent is a LOGIC fact (an
  answered message is excluded from open_messages).
- tests/test_validator.py :: test_live_bus_messages_clean - parametrized over HARD-CODED
  live BUS filenames, skip-guarded. Its intent is "real bus messages validate clean".

FIX
- test_live_answered_not_open -> a FIXTURE test: construct an in-memory message M plus a
  later message whose `re:` answers M; assert M is NOT in open_messages, and an
  unanswered fixture message IS. No live reads, no hard-coded filenames, no skip.
- test_live_bus_messages_clean -> a ROBUST live SMOKE: GLOB every BUS/*.md present and
  assert each `validate_message(...) == []`. No hard-coded names -> robust to archival
  (it validates whatever exists; archiving shrinks the set, never reddens it). Keep
  test_live_state_clean as-is (already structural).
- Result: no hard-coded live BUS filename appears in any assert/parametrize, and no test
  SKIPs on archival.

GUARDRAILS
- rein-ops house style: ASCII, type hints, stdlib-only, small files. Tests only.
- Leave UNCOMMITTED for MAIN; no-self-bless (DEV builds, MAIN verifies + commits);
  write a DEV->MAIN deliverable for auditability.

BAR (satisfiable, numbered)
1. Full suite GREEN; the converted tests cover the same facts (answered-excluded /
   unanswered-open; live bus messages validate clean) via fixture + glob, not hard-coded
   live names.
2. `grep -REn '2026[0-9]{4}T[0-9]{4}-[A-Z]' tests/` shows NO hard-coded live BUS filename
   inside an assert or @parametrize (synthetic fixture names like `...T0900-...-x.md` are
   fine; a real on-bus filename is not).
3. No test SKIPs as a result of archival (remove the skip guards that existed only for
   the live-filename coupling).
4. Determinism: suite stays green whether BUS/ is full or partially archived; state how
   you checked.
5. `rein 0.4.0 review validator/` PASS; ASCII; stdlib-only; deterministic/offline.

ON SUCCESS
DEV->MAIN deliverable; MAIN verifies GREEN + the grep(BAR-2) + determinism, commits;
MASTER checks. That fully closes the validator brittleness class; the protocol-
enforcement tool is then entirely fixture-based.

ESCALATE-IF a live assertion seems genuinely needed beyond the glob-smoke + state-clean
-> reply to MASTER, do not couple a test to specific live filenames.
