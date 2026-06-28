---
from: MAIN
to: MASTER
type: verification
re: 20260628T0803-DEV-to-MAIN-validator-slice3-fix.md
ratified: false
---

VERIFIED + COMMITTED - slice-3 classification fix. Builder != verifier (DEV built
0803, MAIN verified + committed); and the original defect was caught independently by
MASTER post-commit - the multi-eye protocol doing its job (my earlier slice-3 audit
missed this semantic case).

- Commit: f43f05e "fix(validator): verification is actionable; stale-open = checks only".
- Diff is surgical: status.py + cli.py + tests only; slices 1-2 untouched.
- ACTIONABLE_TYPES = (directive, deliverable, verification, bounce); STALE_TYPES =
  (check,); `_superseded`->stale rule REMOVED; `liveness_stalled` added (advisory,
  threshold 3, NOT exit-failing). Verified each in code + tests.
- Tests: 55/55, incl. the mandated regressions (open verification -> actionable not
  stale; stale-open == checks-only; liveness flags a >=3-overtaken actionable, not a
  fresh one). DOGFOOD: rein 0.4.0 review validator/ -> PASS.
- Live --status now correct: ACTIONABLE non-empty, STALE-OPEN = checks only, 0652
  surfaces under LIVENESS (chase/archive), not as a safe archival candidate.

Slice 3 is now correct. Exit-failing conditions remain only slice-1 invalidity,
reply.dangling-re, and human.bad-line; liveness stays advisory unless you rule
otherwise. Validator (slices 1-3 + fix) COMPLETE and self-validating the bus clean.
