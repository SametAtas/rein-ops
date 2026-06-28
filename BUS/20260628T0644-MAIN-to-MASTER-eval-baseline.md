---
from: MAIN
to: MASTER
type: bounce
re: 20260628T0632-MASTER-to-MAIN-eval-baseline.md
ratified: false
---

BLOCKED at BAR-2 (fail-closed on a secret pattern) - NOT committed. Need a MASTER
ratify decision before I commit.

WHAT I FOUND
- BAR-1 (done): excluded `raw/` (per-run logs + .window.lock) and `cache/` (grader
  cache) via .gitignore - transient/regenerable; baseline tracks source only. 23
  files staged.
- BAR-2 secret scan: 11 secret-pattern hits, ALL inside ONE file -
  `benchmarks/securityeval_raw.jsonl`. They are FAKE keys in the SecurityEval
  benchmark dataset's `Insecure_code` samples (e.g. CWE-321 hardcoded-key:
  `openai.api_key = "sk-Hn0..."`). This jsonl IS the experiment's input corpus (the
  121 intentionally-vulnerable tasks). NOT real credentials. Directly analogous to
  rein's own committed sample-secret test fixtures.
- NO real env/key file staged. The real Gemini key lives at
  `/home/samet/software-files/.gemini.env`, OUTSIDE the repo - never stageable.
- BAR-4 (pass): pin intact - `rein.__file__` in site-packages (not src/),
  `rein.__version__ == 0.4.0`.

WHY THIS NEEDS YOU (ambiguity the spec did not cover)
The benchmark corpus is REQUIRED for the baseline (it is the input the clean restart
runs on), so excluding it would break reproducibility - but it inherently contains
sample secrets because it is a security benchmark. BAR-2 says "0 secret-bearing
staged files" and ESCALATE-IF says "any secret would be tracked -> do not commit";
both fired. This is the test-corpus case, not a leak, and the baseline is LOCAL/
PRIVATE (no public push).

RECOMMENDATION
Ratify "commit as-is": these are public-benchmark fixture keys in a private repo,
the same call rein makes for its own sample-secret fixtures. Excluding the jsonl is
the wrong fix (it makes the experiment unrunnable/unreproducible). On your ratify I
commit the 23-file baseline unchanged and reply with SHA + tracked count.

ALTERNATIVE (if you reject): tell me what to exclude; I will not improvise.

STATE: files staged, NOT committed. Pin untouched. No NEEDS-HUMAN raised yet -
routing to you first per "ambiguity -> reply to MASTER, do not improvise".
