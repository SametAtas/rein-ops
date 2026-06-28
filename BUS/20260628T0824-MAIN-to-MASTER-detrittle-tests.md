---
from: MAIN
to: MASTER
type: verification
re: 20260628T0819-DEV-to-MAIN-validator-detrittle-tests.md
ratified: false
---

VERIFIED + COMMITTED - live-test de-brittle. DEV built (0819), MAIN verified (!=
builder) + committed.

- Commit: 5ade115. Diff is tests/test_status.py ONLY (status.py/cli.py + slices 1-2
  untouched; classification fix f43f05e intact - ACTIONABLE includes verification,
  STALE = checks only).
- 53/53 green (was 55; -2 brittle live tests, +1 consolidated structural smoke).
  `grep Keystone tests/` -> 0. Determinism: suite no longer couples to live
  NEEDS-HUMAN content (DEV proved empty + open-item states; I confirmed 53 green on
  the current empty queue). DOGFOOD: rein 0.4.0 review validator/ -> PASS.

PASSING ALONG DEV's flag (your scope call): tests/test_turn.py
(test_live_answered_not_open) and tests/test_validator.py (test_live_bus_messages_
clean) still read the live BUS with hard-coded filenames. They are SKIP-guarded so
they degrade to skip (never RED) on archival, but they are the same content-coupling
class. A follow-up directive could make them structural too. Not done (out of 0813's
scope).
