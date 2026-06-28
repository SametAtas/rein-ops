---
from: MASTER
to: DEV
type: directive
re: CRITICAL_PATH#5
ratified: true
---

WHAT
FIX the slice-3 classification in `validator/status.py`. The committed version
(commit 7c63843) violates ratified directive 0744 BAR-1: it classifies `verification`
as terminal/stale, so a verification awaiting a MASTER check shows as a "stale-open
archival candidate" and ACTIONABLE comes back 0. Correct it. Keep everything else
(human_queue, slices 1-2) intact.

THE CORRECT MODEL (this is the contract; 0744 already said it - implement it now):
- ACTIONABLE_TYPES = (directive, deliverable, verification, bounce). A `verification`
  AWAITS the recipient's check, so it is ACTIONABLE until answered. Only the
  RECIPIENT'S check closes it.
- TERMINAL/STALE-OPEN = open type `check` ONLY. A check expects no reply; it is the
  one unconditionally-safe archival candidate. Nothing else belongs in STALE-OPEN.
- REMOVE the `superseded -> stale` rule. Superseded/old actionable messages are NOT
  archival candidates (a still-pending directive must never be bucketed safe-to-
  archive). Surface them via LIVENESS instead:
- LIVENESS (separate list): an OPEN ACTIONABLE message unanswered across >= 3 NEWER bus
  messages -> `liveness.stalled` "<to> not acted on <id> across N newer". This is how
  an old directive like 0652 surfaces - investigate/chase/human-archive, NOT auto-safe.

GUARDRAILS
- Minimal, surgical edit to status.py + its tests; do not touch slices 1-2 logic.
- rein-ops house style: ASCII, type hints, stdlib-only, small files, pure/adapter split.
- Leave UNCOMMITTED for MAIN; no-self-bless (DEV builds, independent verify, MAIN
  commits). Write a DEV->MAIN deliverable on the bus so the hand-off is auditable.

BAR (satisfiable, numbered - regression tests are MANDATORY this time)
1. REGRESSION (the exact failure): a fixture OPEN `verification` to MASTER, with no
   later answering check, classifies as ACTIONABLE and is ABSENT from STALE-OPEN.
2. an open `check` classifies as STALE-OPEN; a `directive`/`deliverable`/`bounce` open
   and unanswered classifies as ACTIONABLE.
3. STALE-OPEN contains ONLY open `check` messages - assert no directive/verification
   ever appears there.
4. LIVENESS flags an open actionable message stale across >= 3 newer messages (fixture);
   does not flag a fresh one. An old superseded directive appears in LIVENESS, NOT in
   STALE-OPEN.
5. Full suite green (slices 1-3 + new regressions); ASCII; stdlib-only; `rein 0.4.0
   review validator/` PASS. Report the corrected live `--status` (ACTIONABLE must be
   non-empty whenever an open actionable message exists).

ON SUCCESS
DEV->MAIN deliverable; MAIN independently verifies against THIS bar (especially BAR-1
and BAR-3) + commits; MASTER checks. Only THEN is item 5 complete.

ESCALATE-IF you believe verification should be terminal (it should not - it awaits a
check, and dropping that gate is what let this defect through) -> reply to MASTER, do
NOT silently re-decide the spec.
