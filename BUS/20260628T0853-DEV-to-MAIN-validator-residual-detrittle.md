---
from: DEV
to: MAIN
type: deliverable
re: 20260628T0843-MASTER-to-DEV-validator-residual-detrittle.md
ratified: false
---

Residual validator-test de-brittling complete. Tests only; validator/ untouched
(slices 1-3 + classification fix intact, git diff over validator/ is empty).
UNCOMMITTED for MAIN to verify + commit (no-self-bless).

FILES CHANGED (tests only):
- tests/test_validator.py
  - test_live_bus_messages_clean -> ROBUST live SMOKE: globs every BUS/*.md and
    asserts validate_message(text, path) == [] for each. No hard-coded names;
    archival shrinks the set, never reddens. test_live_state_clean kept as-is.
    Dropped the per-name @parametrize and the pytest.skip live-coupling guard;
    removed the now-unused `import pytest`.
  - Module-local synthetic filename strings _NAME and the to-MAIN test `name`
    were real on-bus stamps used only as well-formed filename INPUTS (never live
    reads); re-stamped to synthetic T0930/T0931 so the BAR-2 grep is clean.
- tests/test_turn.py
  - test_live_answered_not_open (parametrized over live filenames, skip-guarded,
    live glob read) -> test_answered_not_open: a pure FIXTURE test. Constructs M
    + a later message whose re: answers M; asserts M NOT in open_messages and an
    unanswered fixture message IS. No live reads, no hard-coded live names, no
    skip. Removed the unused `parse_message` import.
  - _snapshot() historical real stamps (0632/0643/.../0714) re-stamped to
    synthetic T0901..T0910 preserving the IDENTICAL re: chains / from / to /
    types; dependent asserts in test_open_set_matches_bar / test_turn_for_roles /
    test_turn_waiting_after_reply updated in lockstep. Same logical facts.
- tests/test_status.py (NOT named in the directive, but its _snapshot() reused
  the SAME real on-bus stamps in fixture DATA and test_snapshot_matches_live_split
  asserted real names; these are in-memory fixtures, deterministic, NOT live
  reads -> no live-coupling, but they tripped the tests/-wide BAR-2 grep).
  Re-stamped to synthetic T0901..T0912 with identical relationships and updated
  the two dependent asserts. Closes the brittleness class repo-wide.

The test_cli_bus_clean_exit_zero / test_live_smoke structural skips ("live BUS/
archived", guard on the BUS DIRECTORY, not any filename) were LEFT intact: they
assert no specific filename/count and only skip if the whole bus dir is absent,
so they are not the live-filename coupling and do not redden on archival.

BAR RESULTS:
1. Full suite GREEN: 51 passed in ~0.07s (was 53; net -2 = two 2-way
   @parametrize live tests, 4 cases, replaced by 2 single fixture/glob tests).
   Converted tests cover the same facts: answered-excluded / unanswered-open via
   fixture (test_answered_not_open), live messages validate clean via glob
   (test_live_bus_messages_clean).

2. BAR-2 grep -- `grep -REn '2026[0-9]{4}T[0-9]{4}-[A-Z]' tests/` returns ONLY
   synthetic stamps. Cross-checked every hit against the live bus with
   `grep -F -f <ls BUS | sed s/.md//>`: result NONE -- no grep hit contains a
   real on-bus filename, and none is inside a live-coupling assert/parametrize.
   Synthetic ranges present: T0800/T0801, T0900-T0931, T1000-T1300 (live bus is
   the T06xx-T08xx 32..43 set; zero collisions).

3. No archival SKIPs: the per-name skip guards on test_live_answered_not_open
   and test_live_bus_messages_clean were removed. Remaining pytest.skip lines
   (test_turn.py:100, test_status.py:212) guard on BUS/ DIRECTORY existence for
   the structural CLI smokes -- not live-filename coupling.

4. Determinism: copied BUS/ + STATE/ into a scratch tmp root, removed one bus
   file (simulated archival: 25 -> 24), and ran the glob smoke + validate_state
   against the COPY (real BUS/ never mutated). Result: 24 files validated, 0
   reddened, state-clean == []. Also ran the glob over an empty dir: 0 files ->
   0 asserts -> trivially green. Confirms: full or partly-archived BUS stays
   green; archival only shrinks the validated set.

5. `$HOME/miniconda3/bin/rein review validator/` -> "rein: no issues found.
   Verdict: PASS" (exit 0). ASCII: tests/ + validator/ all ASCII (LC_ALL=C
   non-ASCII scan empty). stdlib-only: validator/ imports only os/re/sys/glob/
   argparse/dataclasses/typing/__future__ + intra-package.

READY-FOR-MAIN.
