"""Module entrypoint so `python -m validator ...` runs the CLI.

Thin shim only: all logic lives in cli.main / core. This lets the validator be
invoked as a module (mirrors rein's `python -m rein` ergonomics).
"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
