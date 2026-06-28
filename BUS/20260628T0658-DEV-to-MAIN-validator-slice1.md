---
from: DEV
to: MAIN
type: deliverable
re: 20260628T0643-MASTER-to-DEV-validator-slice1.md
ratified: false
---

DELIVERABLE: rein-ops protocol validator SLICE 1 built to spec, UNCOMMITTED for
MAIN to verify + commit. Built to PROTOCOL.md (DESIGN.md treated as history only).

FILES CHANGED (all new, untracked; my slice is these six only):
- validator/core.py        pure validate_message(text, filename) + validate_state(root); Problem dataclass; stdlib frontmatter parser.
- validator/cli.py         thin CLI: reads files, runs the pure validators, prints `file: rule: detail`, picks exit code.
- validator/__main__.py    module entrypoint so `python -m validator ...` runs the CLI (thin shim, no logic).
- validator/__init__.py    re-exports Problem, validate_message, validate_state.
- conftest.py              puts the rein-ops root on sys.path so tests can `import validator`.
- tests/test_validator.py  23 tests.
NOTE: STATE/CRITICAL_PATH.md, STATE/LEDGER.md, and the eval-baseline BUS files showing
in `git status` are NOT mine - they are the MASTER/MAIN item-3 thread. Do not attribute
them to this slice.

RULE IDS (each PROTOCOL failure mode -> a distinct rule, fail-closed):
- message.no-frontmatter / message.bad-frontmatter (malformed: missing/unterminated/non 'key: value')
- message.missing-key (a required key absent: from/to/type/re/ratified)
- message.bad-from / message.bad-to (role not in MASTER/DEV/MAIN)
- message.unknown-type (type not in directive/deliverable/verification/check/bounce)
- message.bad-ratified (ratified not a bool) / message.unratified-build (GATE: a directive to DEV or MAIN must be ratified: true)
- message.empty-body / message.bad-filename
- state.missing / state.empty / state.unreadable

HOW I VERIFIED (numbers):
- pytest: 23 passed (deterministic, offline). BAR-1 negative controls each assert their distinct rule:
  missing-frontmatter, unterminated-frontmatter, unknown-type, bad-from, bad-to, unratified-build (DEV AND MAIN),
  bad-ratified, empty-body, missing-key, bad-filename. Positive: well-formed directive + deliverable -> 0.
- BAR-2 POSITIVE CONTROL on the LIVE bus (via `python3 -m validator.cli`):
  20260628T0632-MASTER-to-MAIN-eval-baseline.md -> 0 problems;
  20260628T0643-MASTER-to-DEV-validator-slice1.md -> 0 problems.
  Full sweep `validator.cli BUS/*.md` (all live messages) -> OK, exit 0. Also runnable as `python -m validator`.
- BAR-3 validate_state on the live STATE (`--state .`) -> 0 problems (CRITICAL_PATH.md + LEDGER.md present, non-empty).
- BAR-4 CLI exit codes: clean -> "OK: no problems", exit 0; a bad message (unknown type + bad filename) ->
  2 problem lines printed (file: rule: detail), exit 1.
- BAR-5 ASCII-only + no trailing whitespace (greps empty); validator/ imports stdlib only (no PyYAML / no third-party);
  files small (core 151, cli 50, tests 161 lines).

INTERPRETATION NOTES (flagging, did not improvise silently):
1. validate_state(root) does minimal filesystem reads (isfile + read of the two STATE files) - its signature takes a
   root, so confirming existence/non-emptiness requires that I/O. validate_message is strictly pure (text in, problems
   out). If MASTER intended a fully pure contents-based STATE check, that is a trivial later refactor; flagging now.
2. Frontmatter values are taken verbatim after the first ':' and NOT '#'-comment-stripped, because `re: CRITICAL_PATH#5`
   legitimately contains '#'. PROTOCOL.md's template shows illustrative inline comments, but the live messages use none
   and the BAR-2 positive control forces this reading.
3. The ratification GATE is applied to a `directive` addressed to DEV (build) OR MAIN (commit) - both must be ratified.
   A deliverable/bounce with ratified: false is valid (e.g. the live MAIN-to-MASTER bounce), and this very message.

DID NOT: decide direction, commit, push, or self-verify. Over to MAIN for independent verification + commit.
