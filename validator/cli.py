"""Thin CLI adapter for the rein-ops validator.

Reads message files, a rein-ops root, and/or a BUS directory, runs the pure
validators, prints one `file: rule: detail` line per problem plus (for --bus) the
derived turn/open report, and picks the exit code. All logic lives in core/turn;
this only does I/O and exit codes.

Exit is nonzero on any slice-1 validation failure or a reply.dangling-re; the
turn/open report itself is informational (a stale-open message is shown, not an
error).
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

from .core import Problem, parse_message, validate_message, validate_state
from .turn import ROLES, open_messages, reply_problems, turn_for


def _validate_bus(root: str) -> list[Problem]:
    """Validate every BUS/*.md under *root*, check reply legality, print the turn
    and open-message report. Returns the problems (caller sets the exit code)."""
    bus = os.path.join(root, "BUS")
    paths = sorted(glob.glob(os.path.join(bus, "*.md")))
    problems: list[Problem] = []
    messages = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            problems.append(Problem(os.path.basename(path), "io.unreadable", f"cannot read {path}: {exc}"))
            continue
        problems.extend(validate_message(text, path))
        messages.append(parse_message(text, path))

    problems.extend(reply_problems(messages))

    print("TURN (latest open message per role):")
    for role in ROLES:
        holder = turn_for(role, messages)
        print(f"  {role}: {holder.filename if holder else 'waiting'}")
    opens = open_messages(messages)
    print(f"OPEN messages ({len(opens)}):")
    for m in opens:
        to = m.fields.get("to", "?")
        print(f"  {m.filename} (to: {to})")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validator",
        description="Validate rein-ops BUS messages, STATE, and derived turns; fail-closed.",
    )
    parser.add_argument("files", nargs="*", help="BUS message .md files to validate")
    parser.add_argument("--state", metavar="ROOT", help="validate STATE/ under this rein-ops root")
    parser.add_argument("--bus", metavar="ROOT", help="validate BUS/ under this rein-ops root and report turns")
    args = parser.parse_args(argv)

    if not args.files and args.state is None and args.bus is None:
        parser.error("nothing to validate: pass message files and/or --state ROOT and/or --bus ROOT")

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
    if args.bus is not None:
        problems.extend(_validate_bus(args.bus))

    for p in problems:
        print(f"{p.file}: {p.rule}: {p.detail}")
    if problems:
        print(f"FAIL: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print("OK: no problems")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
