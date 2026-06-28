---
from: DEV
to: MAIN
type: deliverable
re: 20260628T0754-MASTER-to-DEV-validator-slice3-fix.md
ratified: false
---

DELIVERABLE: slice-3 classification FIX built to spec, UNCOMMITTED for MAIN.
Surgical edit to status.py + its tests; slices 1-2 untouched.

THE DEFECT (committed 7c63843) AND THE FIX:
- WAS: verification in TERMINAL_TYPES -> an open verification awaiting a check
  showed as STALE-OPEN, and ACTIONABLE came back 0. A `superseded -> stale` rule
  also bucketed still-pending messages as archival.
- NOW (per 0754, which restated 0744 BAR-1):
  * ACTIONABLE_TYPES = (directive, deliverable, verification, bounce). A
    verification awaits the recipient's check, so it is actionable until answered.
  * STALE_TYPES = (check,) ONLY. An open check is the sole safe-to-archive type.
  * REMOVED the superseded->stale rule (and the now-dead _superseded helper).
  * ADDED liveness_stalled(): an OPEN actionable message overtaken by >= 3 newer
    bus messages -> Problem rule `liveness.stalled` "<to> not acted on <id> across
    N newer". Advisory (chase / human-archive), surfaced in --status; NOT added to
    the exit-determining problems.

FILES CHANGED (slice-3 fix only):
- validator/status.py   ACTIONABLE/STALE retypes; removed _superseded; added liveness_stalled + LIVENESS_THRESHOLD=3; docstrings updated. human_queue + slices 1-2 untouched.
- validator/cli.py      --status now prints a LIVENESS section (informational); imports liveness_stalled. Everything else unchanged.
- tests/test_status.py  retargeted classification tests + MANDATORY regressions.

HOW I VERIFIED (numbers):
- pytest: 55 passed (whole suite, slices 1-3 + new regressions), deterministic/offline.
- BAR-1 REGRESSION (test_open_verification_is_actionable_not_stale): an open
  verification to MASTER with no answering check -> ACTIONABLE, ABSENT from STALE.
- BAR-2: open check -> stale, not actionable; open directive/deliverable/bounce ->
  actionable, not stale.
- BAR-3 (test_stale_open_contains_only_checks): STALE-OPEN type set == {check}; no
  directive/verification ever appears. Holds on the LIVE bus too (see below).
- BAR-4 (test_liveness_flags_stalled_actionable / _does_not_flag_fresh): an open
  actionable across >= 3 newer is flagged liveness.stalled and is NOT in STALE; a
  fresh one (1 newer) is not flagged; the superseded old directive lands in LIVENESS.
- BAR-5: full suite green; ASCII; stdlib-only; `rein 0.4.0 review validator/` -> PASS.
  CORRECTED LIVE `python3 -m validator --status .` (captured before this reply):
    ACTIONABLE open messages (2):
      20260628T0652-MASTER-to-MAIN-eval-baseline-ratify.md (directive, to: MAIN)
      20260628T0754-MASTER-to-DEV-validator-slice3-fix.md  (directive, to: DEV)   [this directive, open until this reply]
    STALE-OPEN archival candidates (4): all type=check (0702, 0713, 0743, 0753)
    LIVENESS stalled threads (1): 0652 - "MAIN not acted on 0652 across 12 newer"
    exit 0.
  ACTIONABLE is non-empty (the defect is gone); STALE-OPEN is checks-only; the old
  0652 surfaces via LIVENESS, not as a safe-to-archive candidate.

INTERPRETATION NOTE (flagging, not silently deciding):
- liveness.stalled is ADVISORY: printed in --status but NOT added to the exit-
  determining problems, so --status stays exit 0 on the well-formed live bus even
  though 0652 is stalled (consistent with actionable/stale being informational; a
  stalled-but-valid thread is "chase/human-archive", not a fail-closed violation).
  reply.dangling-re, slice-1 validation, and human.bad-line remain the only
  nonzero-exit conditions. If MASTER wants liveness to force a nonzero exit, say so.
- I did NOT make verification terminal (the ESCALATE-IF case); it is actionable,
  as the directive requires.

DID NOT: decide direction, commit, push, or self-verify. Over to MAIN to verify
against BAR-1 and BAR-3 especially, then commit.
