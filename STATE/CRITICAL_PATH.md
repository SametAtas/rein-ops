# CRITICAL PATH (MASTER writes; item 1 = now)

1. rein-engine 0.4.0 release - DONE. Engine `6067d73`; public accumulated to
   `f6a9cb9` (no force-push), tag `v0.4.0`; owner published the GitHub Release ->
   PyPI shipped 0.4.0.

2. PIN the Keystone rein arm - DONE (2026-06-28, "pin go"). Frozen worktree at
   `6067d73` non-editable-installed into the eval miniconda env; verified
   `rein.__file__` is in site-packages (NOT src/) and `rein.__version__ == 0.4.0`.
   The experiment no longer tracks the moving repo HEAD.

3. THROUGHPUT 429 fix (rein-steering-eval) - DONE + independently audited, LIVE in
   the working tree (per-day quota 429 now stops cleanly instead of churning).
   FOLLOW-UP: rein-steering-eval has NO git history; commit a leak-safe baseline
   (exclude .env/cache) so the experiment is reproducible.

4. RESTART clean Keystone runs under pinned 0.4.0 + fixed pacing; `window.sh` daily
   after 15:00 local; finalize at N>=50 -> aggregate/audit -> RESULTS.md -> paired
   stat test.

5. PARALLEL (unblocked once the arm is pinned):
   - rein-ops hardening: build the validator slices (parse/validate a BUS message +
     STATE file, fail-closed) so the protocol is mechanically enforced, not just
     chat-followed. DEV task once specced.
   - dup.function index cache (DECISIONS #47) when loop-latency evidence warrants.
