---
from: DEV
to: MAIN
type: deliverable
re: 20260628T0813-MASTER-to-DEV-validator-detrittle-tests.md
ratified: false
---

DELIVERABLE: de-brittled the validator's live positive-control tests. TESTS ONLY;
status.py/cli.py and slices 1-2 untouched. The classification fix (f43f05e) stays.

WHAT CHANGED (tests/test_status.py only):
- REMOVED the two brittle live tests:
  * test_live_human_queue_open_item - asserted a specific live NEEDS-HUMAN item
    ("Keystone"); reddened the moment that gate was resolved (the observed failure).
  * test_live_stale_includes_known_checks - asserted hard-coded live check filenames;
    would rot on archival.
- CONSOLIDATED the live touch into ONE robust STRUCTURAL smoke (test_live_smoke):
  `validator --status .` exits 0 AND human_queue(live NEEDS-HUMAN) returns no
  problems. It asserts NO specific item, filename, or count.
- Neutralized "Keystone" in the in-memory _NEEDS_HUMAN fixture (generic ask) so a
  literal grep is clean.
- Removed the now-unused parse_message import.
- Coverage the removed live tests provided is fixture-based and intact:
  open item rendered + Resolved excluded -> test_human_queue_returns_only_open_item /
  _excludes_resolved_section; stale == checks -> test_open_check_is_stale_not_actionable
  / test_stale_open_contains_only_checks / test_snapshot_matches_live_split; an
  actionable surfaced -> test_directive_deliverable_bounce_open_are_actionable;
  liveness on an overtaken actionable -> test_liveness_flags_stalled_actionable.

HOW I VERIFIED (numbers):
- BAR-1: full suite GREEN, 53 passed (was 55: removed the 2 brittle live tests; the
  live smoke is one consolidated test). 0 failed.
- BAR-2 DETERMINISM PROOF: the suite's green-ness no longer depends on live
  NEEDS-HUMAN content. Verified BOTH states:
  * EMPTY live queue (current real state): `pytest -q` -> 53 passed.
  * OPEN-item queue: ran test_live_smoke's assertions against a temp root whose
    NEEDS-HUMAN has one open item -> `--status` exit 0, human_queue items=1,
    problems=0 (and empty-queue -> problems=0). No live file was mutated.
- BAR-3: `grep Keystone tests/test_status.py` -> none. The only live-reading test is
  test_live_smoke and it is structural (no specific item/filename/count asserted).
  (_snapshot remains an IN-MEMORY fixture, not a live read - the directive-sanctioned
  pattern; it does not couple to live BUS/STATE.)
- BAR-4: `rein 0.4.0 review validator/` -> PASS; ASCII-only; stdlib-only;
  deterministic/offline.

FLAGGING (not acting - outside this directive's scope, your call):
- tests/test_turn.py (test_live_answered_not_open) and tests/test_validator.py
  (test_live_bus_messages_clean) still read the live BUS with hard-coded filenames.
  They are SKIP-guarded, so they degrade to skip (never RED) on archival, but they are
  the same content-coupling class. This directive scoped the fix to test_status.py, so
  I left them; flagging in case MASTER wants a follow-up to make them structural too.

DID NOT: touch status.py/cli.py/slices 1-2, decide direction, commit, or self-verify.
Over to MAIN to verify the green suite + the determinism proof, then commit.
