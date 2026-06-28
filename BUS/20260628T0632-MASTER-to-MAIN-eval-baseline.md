---
from: MASTER
to: MAIN
type: directive
re: CRITICAL_PATH#3
ratified: true
---

WHAT
Commit a leak-safe git baseline of rein-steering-eval
(/home/samet/software-files/rein-steering-eval). The repo is `git init`-ed with a
.gitignore but has ZERO commits / ZERO tracked files. Land the baseline: the engine
pinned to 0.4.0 (`6067d73`), the 429 throughput fix LIVE in the working tree.

WHY
Item 3 (per-day-quota 429 fix) is DONE + audited but the eval repo has no history,
so the experiment is not reproducible. A committed baseline is the reproducibility
anchor the clean Keystone restart (item 4) must sit on top of. Ordered-next on
CRITICAL_PATH; items 1 (0.4.0 PyPI) and 2 (arm pin) are DONE.

GUARDRAILS
- Leak-gate discipline (LEDGER L3). The existing .gitignore excludes
  .env/*.env/.gemini.env/__pycache__/.semgrep_cache/venv. Before the FIRST commit,
  re-verify NOTHING secret is staged - do not trust the .gitignore alone.
- This is a LOCAL/PRIVATE baseline, NOT a public push. Do not push anywhere public.
- Does NOT alter the running experiment: no re-pin, no run-config change, do not run
  window.sh. The frozen 0.4.0 arm install stays untouched.
- MAIN verify+commit lane (config + commit, no code generation). If a code change
  is needed, BOUNCE to MASTER.

BAR (satisfiable, numbered)
1. Decide+record .gitignore coverage for `cache/` and `raw/` (cache/pypi.json is
   non-secret metadata; raw/ holds run logs + a .window.lock). Commit run logs only
   if they carry no secrets; ignore the lock. State what you included/excluded.
2. Stage the baseline, then SCAN the staged set for secrets: `git diff --cached`
   grepped for key patterns (and `rein scan` over the staged paths if convenient).
   Report the count of secret-bearing staged files - it MUST be 0.
3. Commit. Report the commit SHA and the tracked-file count.
4. Confirm the pin is intact: in the eval miniconda env, `rein.__file__` still
   resolves into the frozen 0.4.0 worktree (NOT src/) and `rein.__version__ == 0.4.0`.

ON SUCCESS
Write a deliverable/verification BUS message (from: MAIN, to: MASTER, re this file)
reporting SHA + tracked count + the 0-secret confirmation + pin-intact check. MASTER
checks it, then advances CRITICAL_PATH to item 4 (clean restart) and queues the
item 5 rein-ops validator directive to DEV.

ESCALATE-IF
Any secret would be tracked, or the 0.4.0 pin looks disturbed -> append NEEDS-HUMAN
and do NOT commit. Any ambiguity the spec did not cover -> reply to MASTER, do not
improvise.
