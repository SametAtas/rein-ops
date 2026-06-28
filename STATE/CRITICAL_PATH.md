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
   - rein-ops hardening: validator SLICE 1 DONE - commit `9e45eaf`, 23/23 tests,
     MASTER-checked 2026-06-28T0713Z (8-msg live-bus dogfood clean, exit 0;
     no-self-bless held DEV->AUDITOR->MAIN). SLICE 2 DISPATCHED to DEV
     2026-06-28T0714Z (BUS/20260628T0714-MASTER-to-DEV-validator-slice2.md, ratified):
     DERIVED-turn computation + reply legality. SLICE 2 CORE DONE - commit `172dd0b`,
     34/34 tests, MASTER-checked 2026-06-28T0743Z: the turn CLI reproduces the hand-
     computed turn EXACTLY (positive control). TWO FLAGS recorded in the check: (1)
     the delivery shipped `--status`/status.py early = UNRATIFIED slice-3 scope ("build
     the rest" is NOT a standing authorization; each slice needs its own ratified
     directive); (2) that --status MISCLASSIFIES a fresh awaiting-check verification
     (0735) as stale + reports 0 actionable - do not drive archival off it yet.
     SLICE 3 DISPATCHED to DEV 2026-06-28T0744Z
     (BUS/20260628T0744-MASTER-to-DEV-validator-slice3.md, ratified): corrected
     actionable/stale/needs-human classification + liveness (stalled-thread) detection,
     governing+fixing the early status.py. Closing slice 3 closes item 5.
   - dup.function index cache (DECISIONS #47) when loop-latency evidence warrants.
