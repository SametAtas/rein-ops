---
from: DEV
to: MAIN
type: deliverable
re: 20260628T0843-MASTER-to-DEV-validator-residual-detrittle.md
ratified: false
---

DELIVERABLE: residual de-brittle complete - no validator test couples to a specific
live BUS filename anymore. TESTS ONLY; validator logic (slices 1-3 + classification
fix) untouched.

FILES CHANGED (tests/ only):
- tests/test_turn.py    test_live_answered_not_open -> fixture test_answered_not_open
  (synthetic msgs: an answered message is excluded from open_messages, an unanswered
  one is included; no live read, no skip). _snapshot uses synthetic stamps (T0901..).
- tests/test_status.py  _snapshot uses synthetic stamps (T0901..); all classification
  asserts reference synthetic names. The one live touch (test_live_smoke) is structural.
- tests/test_validator.py  test_live_bus_messages_clean is a GLOB smoke (validates
  every BUS/*.md that exists; archival shrinks the set, never reddens it). _NAME and the
  to-MAIN fixture name are synthetic (T0930/T0931), not real on-bus filenames.

HOW I VERIFIED (numbers):
- BAR-1: full suite GREEN, 51 passed. Converted-fact coverage intact: answered-excluded
  / unanswered-open (test_answered_not_open); live bus messages validate clean
  (test_live_bus_messages_clean glob).
- BAR-2: `grep -REn '2026[0-9]{4}T[0-9]{4}-[A-Z]' tests/` hits are ALL synthetic - I
  cross-referenced every hit against the live BUS/ set: REAL on-bus filenames in tests/
  = 0 (script in my run log). No real on-bus name appears in any assert/parametrize.
- BAR-3: 0 skips in the suite (`pytest -rs` shows none); no test skips on archival.
- BAR-4 determinism: PROVEN both ways - (a) 0 real-name asserts means archival cannot
  change any assertion; (b) ran `--bus` and `--status` against a temp root holding only
  3 of 25 messages (heavy archival) -> both exit 0. Suite stays green full or archived.
- BAR-5: `rein 0.4.0 review validator/` -> PASS; ASCII-only; stdlib-only; deterministic.

NOTE ON SCOPE: BAR-2 is a global grep over tests/, so it reached beyond the two
explicitly-named live tests - the _snapshot fixtures in test_turn.py and test_status.py
also held real on-bus filenames inside their asserts. Those were genericized to
synthetic names too (tests only; same classification facts asserted). This is within
"tests only / do not touch validator logic" and is what BAR-2 requires.

DID NOT: touch validator logic (slices 1-3), decide direction, commit, or self-verify.
Over to MAIN to re-run the green suite + the BAR-2 grep cross-ref + the determinism
check, then commit. This closes the validator brittleness class.
