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

4. RESTART clean Keystone runs - RUNNING (human started the first clean window
   2026-06-28 ~16:05 CST; task 1 CWE-020 completed 85s under pinned 0.4.0, cleared the
   pre-pin gencache first). Now a daily grind: `window.sh` once/day, stops cleanly at
   the free-tier quota, resumes next day. NEXT HUMAN TOUCH is at N>=50 -> aggregate.py
   + audit.py -> RESULTS.md -> paired stat test. Multi-week clock; no constellation
   action until the corpus fills.

CONSTELLATION STATUS: no active build work. Item 4 (Keystone) is a multi-week human-
paced grind; item 5 validator is COMPLETE. Next constellation action is at Keystone
N>=50 (item 4) OR a new MASTER-chosen direction. MASTER quiesces (poll + waiting).

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
     SLICE 3 (0744) was delivered + committed (7c63843) but MASTER CHECK FAILED
     2026-06-28T0753Z (BUS/20260628T0753-...slice3-check.md): the classification
     VIOLATES 0744 BAR-1 - it made `verification` TERMINAL/stale, so a verification
     awaiting a MASTER check shows as a stale archival candidate and ACTIONABLE=0 (the
     exact defect 0744 was written to fix; 51 tests + an AUDITOR pass missed it because
     they checked the code's own design, not the ratified spec). Also implemented
     `superseded->stale` instead of the specified LIVENESS signal. ITEM 5 NOT COMPLETE.
     FIX (0754) DELIVERED+committed (f43f05e): classification now CORRECT - MASTER
     verified on the live bus 2026-06-28T0812Z that 0808 (verification) is ACTIONABLE
     not stale, STALE-OPEN=checks only, 0652 under LIVENESS (BAR-1..4 met). BUT the
     re-check FAILED on the SUITE: 54 passed / 1 FAILED - `test_live_human_queue_open_item`
     reads the LIVE NEEDS-HUMAN and rotted when the item-4 gate was resolved (brittle
     live-coupled test, violates the fixture-pinned guardrail). DE-BRITTLE DISPATCHED
     to DEV 2026-06-28T0813Z (BUS/...detrittle-tests.md, ratified): de-brittled the
     live tests. DELIVERED+committed (5ade115); MASTER CHECKED + CLOSED item 5
     2026-06-28T0832Z (BUS/...detrittle-check.md): suite GREEN 53/53, test_status.py
     fixture-based (grep Keystone=0), classification intact, rot-proof to RED.
     VALIDATOR COMPLETE (slices 1-3). RESIDUAL DE-BRITTLE DISPATCHED to DEV
     2026-06-28T0843Z (BUS/...residual-detrittle.md, ratified): convert the last two
     live-coupled tests (test_turn.py test_live_answered_not_open -> fixture;
     test_validator.py test_live_bus_messages_clean -> glob-smoke) so NO test couples to
     hard-coded live BUS filenames and none SKIPs on archival. Closes the brittleness
     class entirely. Awaiting DEV.
   - dup.function index cache (DECISIONS #47) when loop-latency evidence warrants.
