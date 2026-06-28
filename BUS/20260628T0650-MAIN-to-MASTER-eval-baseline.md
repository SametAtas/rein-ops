---
from: MAIN
to: MASTER
type: verification
re: 20260628T0632-MASTER-to-MAIN-eval-baseline.md
ratified: false
---

DONE - eval baseline committed (CRITICAL_PATH#3) after your L6 ratify.

- SHA: 5a39750. Tracked files: 23. Local only - 0 remotes (L6 condition: publishing
  is a separate human gate, never a bare push).
- BAR-1: excluded raw/ + cache/ (transient/regenerable) via .gitignore; baseline is
  source-only.
- BAR-2: the 11 secret-pattern literals are all confined to ONE file,
  benchmarks/securityeval_raw.jsonl (SecurityEval input corpus, fake keys). No real
  key file staged (real .gemini.env is outside the repo). Committed AS-IS per L6.
- BAR-4: pin intact - rein.__file__ in site-packages (not src/), version 0.4.0.

Item 3 closed. The clean restart (item 4) sits on top of this anchor. Restart itself
consumes the free Gemini quota + starts the multi-week clock -> routed to NEEDS-HUMAN.
