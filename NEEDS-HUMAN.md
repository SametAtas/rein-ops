# NEEDS-HUMAN (the only file you must watch)

Format: `- [<UTCstamp>] [<role>] <action> - <how to respond>`

- [20260628T0702] [MASTER] Start the clean Keystone N>=50 run (CRITICAL_PATH#4) -
  the frozen config is ready: baseline committed `5a39750`, arm pinned to rein 0.4.0
  (site-packages, not src/). This consumes the free Gemini quota and starts the
  multi-week clock, so it is your call to begin. To start: run `window.sh` daily
  after 15:00 local (the 429 fix now stops cleanly at the daily quota and resumes
  next day); reply "running" once the first clean window is in. Finalize at N>=50.

## Resolved

- [20260628] [MAIN] Publish rein-engine 0.4.0 to PyPI - DONE (owner published v0.4.0).
- [20260628] [MAIN] Confirm the Keystone arm pin - DONE ("pin go"; arm pinned to the
  frozen 0.4.0 install, rein.__file__ in site-packages not src/, version 0.4.0).
