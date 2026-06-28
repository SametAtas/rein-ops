# LEDGER (append-only ratified decisions; reversal = a new entry citing it)

- L1 (2026-06-28) CONSTELLATION = THREE REAL CHATS + POLL-LOOP FILE BUS. Owner
  ratified: MASTER (decisions/new features/ratify/check MAIN), DEV (code), MAIN
  (verify+commit). They coordinate via this rein-ops shared bus; each runs a poll
  loop and WAITS for the others' output (no human content-relay). Supersedes both
  the four-separate-chats manual relay and the single-orchestrator sub-agent model.
  Cost accepted (idle polling burns tokens; chats stay open).

- L2 (2026-06-28) CODE-GEN LANE. Only DEV generates/edits code. MAIN verifies +
  commits + docs. A build task reaching MAIN bounces to MASTER. No chat blesses its
  own work (builder != verifier).

- L3 (2026-06-28) PUBLIC REPO ACCUMULATES. `scripts/publish.sh` commits a sanitized
  export on top of public history and PLAIN-pushes (never force). Leak-gate intact.

- L4 (2026-06-28) KEYSTONE REPRODUCIBILITY. The rein arm must be pinned to one fixed
  engine commit (0.4.0 = `6067d73`) via a non-editable frozen install; the editable
  install that tracked HEAD is the bug. (DECISIONS #48 in the engine repo.)

- L5 ENGINE REPO STAYS PURE. rein-ops and rein-steering-eval are separate repos;
  no orchestration or experiment code ever lands in rein/. Monetization = the
  engine/Ringo, never the internal tooling.

- L6 (2026-06-28) BENCHMARK SAMPLE-SECRETS ARE COMMITTABLE FIXTURES. The
  rein-steering-eval baseline commits `benchmarks/securityeval_raw.jsonl` AS-IS even
  though it carries fake/sample keys (e.g. CWE-321 `sk-Hn0...`): it is the
  SecurityEval input corpus (121 intentionally-vulnerable tasks), required for
  reproducibility, and the repo is private with NO remote. Same call rein makes for
  its own committed sample-secret test fixtures. MAIN bounced on the 0-secret gate;
  MASTER independently verified the literals are confined to that one corpus file, no
  real key file is staged (the real `.gemini.env` is outside the repo), and there is
  no remote - then ratified. CONDITION: publishing rein-steering-eval (adding a public
  remote / pushing) is a NEW human gate; it first needs rein's sample-secret handling
  (documented exemption + push-protection OFF), never a bare push.
