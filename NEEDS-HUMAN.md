# NEEDS-HUMAN (the only file you must watch)

Format: `- [<UTCstamp>] [<role>] <action> - <how to respond>`

(empty - nothing waiting on the human)

## Resolved

- [20260628T0702] [MASTER] Start the clean Keystone N>=50 run (CRITICAL_PATH#4) -
  DONE: first clean window running 2026-06-28 ~16:05 CST under pinned 0.4.0 (task 1
  CWE-020 done in 85s). Re-run window.sh daily until N>=50.

- [20260628] [MAIN] Publish rein-engine 0.4.0 to PyPI - DONE (owner published v0.4.0).
- [20260628] [MAIN] Confirm the Keystone arm pin - DONE ("pin go"; arm pinned to the
  frozen 0.4.0 install, rein.__file__ in site-packages not src/, version 0.4.0).
