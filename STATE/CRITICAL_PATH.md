# CRITICAL PATH (MASTER writes; item 1 = now)

1. rein-engine 0.4.0 release.
   - DONE locally + public: engine commit `6067d73`; public repo accumulated to
     `f6a9cb9` (no force-push), tag `v0.4.0` pushed.
   - PENDING (human): create the GitHub Release for `v0.4.0` -> fires `publish.yml`
     (OIDC) -> approve the `pypi` environment -> PyPI ships 0.4.0. See NEEDS-HUMAN.

2. PIN the Keystone rein arm to the 0.4.0 engine commit `6067d73` (MAIN ops, on
   human confirm - alters the running experiment): replace the editable install
   with a frozen `git worktree` + non-editable `pip install` in the eval miniconda
   env; clear the stub run log; VERIFY `rein.__file__` resolves into the frozen
   worktree (not src/) and `rein.__version__ == 0.4.0`.

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
