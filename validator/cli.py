"""Thin CLI adapter for the rein-ops validator.

Reads message files and/or a rein-ops root, runs the pure validators, prints one
`file: rule: detail` line per problem, and picks the exit code (0 clean, nonzero
on any problem). All logic lives in core; this only does I/O and exit codes.
"""

from __future__ import annotations

import argparse
import sys

from .core import Problem, validate_message, validate_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validator",
        description="Validate rein-ops BUS messages and STATE, fail-closed.",
    )
    parser.add_argument("files", nargs="*", help="BUS message .md files to validate")
    parser.add_argument("--state", metavar="ROOT", help="validate STATE/ under this rein-ops root")
    args = parser.parse_args(argv)

    if not args.files and args.state is None:
        parser.error("nothing to validate: pass message files and/or --state ROOT")

    problems: list[Problem] = []
    for path in args.files:
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            problems.append(Problem(path, "io.unreadable", f"cannot read {path}: {exc}"))
            continue
        problems.extend(validate_message(text, path))
    if args.state is not None:
        problems.extend(validate_state(args.state))

    for p in problems:
        print(f"{p.file}: {p.rule}: {p.detail}")
    if problems:
        print(f"FAIL: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print("OK: no problems")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
