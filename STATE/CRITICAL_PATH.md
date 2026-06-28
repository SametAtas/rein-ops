# CRITICAL PATH (MASTER writes; item 1 = now)

1. rein-engine 0.4.0 release - DONE. Engine `6067d73`; public accumulated to
   `f6a9cb9` (no force-push), tag `v0.4.0`; owner published the GitHub Release ->
   PyPI shipped 0.4.0.

2. PIN the Keystone rein arm - DONE (2026-06-28, "pin go"). Frozen worktree at
   `6067d73` non-editable-installed into the eval miniconda env; verified
   `rein.__file__` is in site-packages (NOT src/) and `rein.__version__ == 0.4.0`.
   The experiment no longer tracks the moving repo HEAD.

3. THROUGHPUT 429 fix + leak-safe baseline - DONE. Baseline committed `5a39750`
   (23 files, source-only); MASTER CHECKED it 2026-06-28T0702Z
   (BUS/20260628T0702-MASTER-to-MAIN-eval-baseline-check.md): SHA/count match,
   secrets confined to securityeval_raw.jsonl, no real key, 0 remotes, pin intact
   (rein 0.4.0 in site-packages). LEDGER L6. Item 3 CLOSED.

4. RESTART clean Keystone runs under pinned 0.4.0 + fixed pacing - NOW (item 1).
   HUMAN GATE (consumes free Gemini quota, starts the multi-week clock): routed to
   NEEDS-HUMAN 2026-06-28T0702Z. Run `window.sh` daily after 15:00 local; finalize at
   N>=50 -> aggregate/audit -> RESULTS.md -> paired stat test. The baseline (5a39750)
   + the pinned 0.4.0 arm are the frozen config the run sits on.

5. PARALLEL (unblocked once the arm is pinned):
   - rein-ops hardening: validator SLICE 1 DISPATCHED to DEV 2026-06-28T0643Z
     (BUS/20260628T0643-MASTER-to-DEV-validator-slice1.md, ratified): pure
     parse/validate of a BUS message + STATE files vs PROTOCOL.md, fail-closed,
     live bus/STATE as positive control. Built to PROTOCOL.md (DESIGN.md v1 turn
     model is REJECTED, history only). Slices 2 (one bus hop) + 3 (NEEDS-HUMAN
     queue) follow. Awaiting DEV.
   - dup.function index cache (DECISIONS #47) when loop-latency evidence warrants.
