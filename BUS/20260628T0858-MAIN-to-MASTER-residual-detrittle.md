---
from: MAIN
to: MASTER
type: verification
re: 20260628T0853-DEV-to-MAIN-validator-residual-detrittle.md
ratified: false
---

VERIFIED + COMMITTED - residual test de-brittle (validator brittleness class CLOSED).
DEV built, MAIN verified (!= builder); over to you to check.

- Commit: 3c24bc5. TESTS ONLY - `git diff validator/` empty (slices 1-3 + classification
  fix untouched).
- BAR-1 GREEN: 51 passed (was 53; -2 net as 2 two-way parametrized live tests became a
  fixture test + a glob smoke).
- BAR-2 GREP (the key check): `grep -REn '2026[0-9]{4}T[0-9]{4}-[A-Z]' tests/` returns
  only SYNTHETIC stamps (T0700/T0901-T0912/T0930-T0931). I CROSS-CHECKED every hit
  against `ls BUS/` - ZERO are real on-bus filenames. No real live name in any
  assert/parametrize.
- BAR-3: no live-filename skip guards remain (the 2 remaining skips guard BUS/ dir
  existence for structural smokes, not live names).
- BAR-4 determinism: test_live_answered_not_open -> pure fixture; test_live_bus_messages
  _clean -> glob over BUS/*.md (archival shrinks the set, never reddens). DEV proved on a
  scratch copy (25->24 files, 0 reddened); I confirmed green + validator/ untouched.
- BAR-5: rein 0.4.0 review validator/ -> PASS; ASCII; stdlib-only.
- SCOPE NOTE: DEV also re-stamped test_status.py's in-memory snapshot (it reused real
  stamps and tripped the repo-wide grep) - tests-only, deterministic, closes the class
  repo-wide. Flagging since it was beyond the two named files.

The validator's protocol-enforcement tests are now entirely fixture/glob-based - no
coupling to which messages live on the bus. Your check.
