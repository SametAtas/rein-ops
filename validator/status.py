"""Slice 3: NEEDS-HUMAN queue render + liveness / stale-thread detection.

Pure logic only - no filesystem access (the CLI does the reads, mirroring the
slice-1/2 split). Two concerns:

  - human_queue(text): parse NEEDS-HUMAN.md and return only the OPEN items (the
    lines above/outside the "Resolved" section). Fail-closed: a malformed open
    line yields a `human.bad-line` Problem, never a silent drop.
  - actionable_open / stale_open: classify slice-2's OPEN set into the messages
    that still await real work versus archival candidates (terminal acks and
    messages superseded by a newer open message to the same role).

PROTOCOL.md is the contract: directive/deliverable/bounce are the types that
hold a real pending turn; check/verification are terminal acknowledgments that
need no reply and are archive candidates.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .core import Msg, Problem
from .turn import open_messages

# Types that still await someone's real work when OPEN:
#   directive  -> awaits the addressed DEV/MAIN
#   deliverable-> awaits MAIN's verify
#   bounce     -> awaits MASTER's re-direction
ACTIONABLE_TYPES = ("directive", "deliverable", "bounce")
# Terminal acknowledgments - open-by-design, no reply expected, archive candidates.
TERMINAL_TYPES = ("check", "verification")

# `- [<stamp>] [<role>] <action> - <how to respond>` ; action/how span multiple
# wrapped lines, so the line-joining happens before this matches a single item.
_HUMAN_LINE_RE = re.compile(r"^- \[([^\]]+)\] \[([^\]]+)\] (.+)$", re.DOTALL)


@dataclass(frozen=True)
class HumanItem:
    """One OPEN NEEDS-HUMAN entry: when it was raised, by whom, and the ask."""

    stamp: str
    role: str
    text: str


def _open_item_blocks(text: str) -> list[str]:
    """Split the NEEDS-HUMAN body ABOVE the 'Resolved' section into item blocks.

    A block starts at a `- ` bullet and absorbs following indented continuation
    lines (the format wraps the action/how across lines). The header, blank lines,
    and everything from the first `## ...Resolved...` heading onward are dropped.
    """
    blocks: list[str] = []
    current: list[str] | None = None
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("## ") and "resolved" in stripped.lower():
            break  # Resolved section onward is closed; ignore it entirely.
        if stripped.startswith("- "):
            if current is not None:
                blocks.append(" ".join(current))
            current = [stripped]
        elif current is not None and stripped != "":
            current.append(stripped)  # continuation of the open item
        elif current is not None and stripped == "":
            blocks.append(" ".join(current))
            current = None
    if current is not None:
        blocks.append(" ".join(current))
    return blocks


def human_queue(text: str) -> tuple[list[HumanItem], list[Problem]]:
    """Parse NEEDS-HUMAN.md; return (open items, problems), fail-closed.

    Only items above/outside the Resolved section are considered. A bullet that
    does not match `- [<stamp>] [<role>] <text>` becomes a `human.bad-line`
    Problem rather than being dropped.
    """
    items: list[HumanItem] = []
    problems: list[Problem] = []
    for block in _open_item_blocks(text):
        m = _HUMAN_LINE_RE.match(block)
        if m is None:
            problems.append(Problem(
                "NEEDS-HUMAN.md", "human.bad-line",
                f"open item is not '- [<stamp>] [<role>] <action> - <how>': {block!r}",
            ))
            continue
        stamp, role, rest = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        items.append(HumanItem(stamp=stamp, role=role, text=rest))
    return items, problems


def _superseded(msg: Msg, opens: list[Msg]) -> bool:
    """True if a different OPEN message to the same `to:` role is strictly newer.

    'Newer' = a later UTC-stamp filename (filenames sort by time). Such a message
    has overtaken *msg* as the live one for that role, so *msg* is an archival
    candidate, not a real pending turn.
    """
    to = msg.fields.get("to")
    if to is None:
        return False
    return any(
        other.filename != msg.filename
        and other.fields.get("to") == to
        and other.filename > msg.filename
        for other in opens
    )


def actionable_open(messages: list[Msg]) -> list[Msg]:
    """OPEN messages that still await real work (directive/deliverable/bounce).

    A directive/deliverable/bounce that is superseded by a newer open message to
    the same role is NOT actionable - it has been overtaken and belongs in
    stale_open instead.
    """
    opens = open_messages(messages)
    return [
        m for m in opens
        if m.fields.get("type") in ACTIONABLE_TYPES and not _superseded(m, opens)
    ]


def stale_open(messages: list[Msg]) -> list[Msg]:
    """OPEN messages that are archival candidates, oldest-first.

    Two cases:
      - terminal acknowledgments (check/verification) - open by design, no reply
        is expected;
      - any open message superseded by a newer open message to the same `to:`
        role.
    """
    opens = open_messages(messages)
    return [
        m for m in opens
        if m.fields.get("type") in TERMINAL_TYPES or _superseded(m, opens)
    ]
