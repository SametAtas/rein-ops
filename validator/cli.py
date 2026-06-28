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
from .status import actionable_open, human_queue, liveness_stalled, stale_open
from .turn import ROLES, open_messages, reply_problems, turn_for


def _read_bus(root: str) -> tuple[list, list[Problem]]:
    """Read+validate every BUS/*.md under *root*; return (parsed msgs, problems)."""
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
    return messages, problems


def _validate_bus(root: str) -> list[Problem]:
    """Validate every BUS/*.md under *root*, check reply legality, print the turn
    and open-message report. Returns the problems (caller sets the exit code)."""
    messages, problems = _read_bus(root)
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


def _status(root: str) -> list[Problem]:
    """Print the constellation status under *root*: the NEEDS-HUMAN open queue,
    the actionable (real pending) open messages, and the stale-open archival
    candidates. Returns the problems (caller sets the exit code)."""
    messages, problems = _read_bus(root)
    problems.extend(reply_problems(messages))

    human_path = os.path.join(root, "NEEDS-HUMAN.md")
    items: list = []
    try:
        with open(human_path, encoding="utf-8") as fh:
            items, human_probs = human_queue(fh.read())
        problems.extend(human_probs)
    except OSError as exc:
        problems.append(Problem("NEEDS-HUMAN.md", "io.unreadable", f"cannot read {human_path}: {exc}"))

    print(f"NEEDS-HUMAN open queue ({len(items)}):")
    for it in items:
        print(f"  [{it.stamp}] [{it.role}] {it.text}")

    actionable = actionable_open(messages)
    print(f"ACTIONABLE open messages ({len(actionable)}):")
    for m in actionable:
        print(f"  {m.filename} (type: {m.fields.get('type', '?')}, to: {m.fields.get('to', '?')})")

    stale = stale_open(messages)
    print(f"STALE-OPEN archival candidates ({len(stale)}):")
    for m in stale:
        print(f"  {m.filename} (type: {m.fields.get('type', '?')}, to: {m.fields.get('to', '?')})")

    # LIVENESS is advisory (chase / human-archive), not a fail-closed violation,
    # so it is reported but NOT added to the exit-determining problems.
    stalled = liveness_stalled(messages)
    print(f"LIVENESS stalled threads ({len(stalled)}):")
    for p in stalled:
        print(f"  {p.file}: {p.detail}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validator",
        description="Validate rein-ops BUS messages, STATE, and derived turns; fail-closed.",
    )
    parser.add_argument("files", nargs="*", help="BUS message .md files to validate")
    parser.add_argument("--state", metavar="ROOT", help="validate STATE/ under this rein-ops root")
    parser.add_argument("--bus", metavar="ROOT", help="validate BUS/ under this rein-ops root and report turns")
    parser.add_argument("--status", metavar="ROOT", help="report the NEEDS-HUMAN queue, actionable, and stale-open lists under this rein-ops root")
    args = parser.parse_args(argv)

    if not args.files and args.state is None and args.bus is None and args.status is None:
        parser.error("nothing to validate: pass message files and/or --state ROOT and/or --bus ROOT and/or --status ROOT")

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
    if args.status is not None:
        problems.extend(_status(args.status))

    for p in problems:
        print(f"{p.file}: {p.rule}: {p.detail}")
    if problems:
        print(f"FAIL: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print("OK: no problems")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
