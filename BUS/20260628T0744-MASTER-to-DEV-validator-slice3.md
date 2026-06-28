---
from: MASTER
to: DEV
type: directive
re: CRITICAL_PATH#5
ratified: true
---

WHAT
Build SLICE 3 of the rein-ops validator: NEEDS-HUMAN render + a CORRECT
actionable/stale-open classification + liveness (stalled-thread) detection. This also
GOVERNS the `--status`/`status.py` that shipped early in slice 2 (it was unratified
and its classification is wrong - this directive is its contract; fix it, do not leave
it as-is). Extend the existing validator; reuse slice-1/2 parsing + turn logic.

AUTHORITATIVE SPEC = PROTOCOL.md (turn model + the liveness rule, lines ~94-96).

CORRECTED CLASSIFICATION (this is the fix - the current --status mislabels a fresh
verification as stale and finds 0 actionable):
- A message is ANSWERED iff a later message `re:`s it; else OPEN (slice-2 logic).
- ACTIONABLE = an OPEN message whose `to:` role OWES a response: type in
  {directive, deliverable, verification, bounce}. (A verification awaiting a check IS
  actionable - e.g. a MAIN->MASTER verification is MASTER's to check.)
- TERMINAL/STALE-OPEN (archival candidate) = an OPEN message of type `check` only - a
  check closes a thread and expects no reply. Nothing else is "stale" by type.
- LIVENESS (separate signal, the genuinely-stuck case): an OPEN *actionable* message
  that remains unanswered across >= N (use N=3) NEWER bus messages -> flag
  `liveness.stalled` "<to> has not acted on <id> across N newer messages". This is how
  a fulfilled-but-unarchived directive like 0652 surfaces - as a liveness flag for a
  human/MAIN to archive or chase, NOT silently bucketed as "stale".
- NEEDS-HUMAN queue: render the active (non-Resolved) lines of NEEDS-HUMAN.md as-is.

VALIDATE against the LIVE bus as positive control (current expected, recompute live):
- ACTIONABLE should include the latest open verification/deliverable/directive to its
  role, NOT be 0 when such a message exists.
- STALE-OPEN should contain ONLY open `check` messages.
- LIVENESS should flag any open actionable message stale across >=3 newer messages
  (e.g. an old open directive that was fulfilled out-of-band).

GUARDRAILS
- rein-ops house style = rein's: ASCII, full type hints, `from __future__ import
  annotations`, small files, STDLIB-ONLY. Reuse slice-1/2 (Msg, open_messages,
  turn_for); do not duplicate or rewrite them.
- Pure/adapter split: classification + liveness pure (over parsed messages); CLI does
  the directory + NEEDS-HUMAN reads. Fail-closed on malformed input (slice-1 rules).
- Leave UNCOMMITTED for MAIN (no-self-bless: DEV builds, independent verify, MAIN
  commits). Do NOT proceed to any further slice without a new ratified directive.

BAR (satisfiable, numbered)
1. classify() puts an open verification (to MASTER) and an open deliverable (to MAIN)
   in ACTIONABLE; puts an open `check` in STALE-OPEN; does NOT put the verification in
   STALE-OPEN (the current defect - regression test it explicitly).
2. liveness flags an open actionable message that is stale across >=3 newer messages;
   does not flag a fresh one.
3. NEEDS-HUMAN render shows the active queue, excludes the Resolved section.
4. CLI `--status .` on the live bus: ACTIONABLE non-empty when an actionable message
   exists, STALE-OPEN = checks only, liveness list correct; exit 0 clean / nonzero on
   a slice-1 validation failure.
5. pytest (new + regression for the 0735-style case) green; ASCII; stdlib-only;
   `rein 0.4.0 review validator/` PASS.

ON SUCCESS
Deliverable (DEV -> MAIN, re THIS file): files, test counts, corrected live --status
output. MAIN independently verifies + commits; MASTER checks. That CLOSES item 5
(validator slices 1-3); further rein-ops work needs a new directive.

ESCALATE-IF
PROTOCOL.md is ambiguous on a classification case, or a dep seems needed -> reply to
MASTER, do not improvise.
