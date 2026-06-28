"""Slice 3: NEEDS-HUMAN queue render + actionable / stale / liveness split.

Pure logic only - no filesystem access (the CLI does the reads, mirroring the
slice-1/2 split). Three concerns:

  - human_queue(text): parse NEEDS-HUMAN.md and return only the OPEN items (the
    lines above/outside the "Resolved" section). Fail-closed: a malformed open
    line yields a `human.bad-line` Problem, never a silent drop.
  - actionable_open / stale_open: classify slice-2's OPEN set into the messages
    that still await real work versus the one terminal type that is safe to
    archive.
  - liveness_stalled: surface an OPEN actionable message that newer traffic has
    overtaken without an answer - a thread to chase / hand to a human, NOT an
    archival candidate.

PROTOCOL.md is the contract. The split that makes archival safe:
  - ACTIONABLE = directive / deliverable / verification / bounce. A verification
    AWAITS the recipient's check, so it is actionable until that check answers it;
    treating it as terminal is what let an awaiting-check verification be
    mis-archived.
  - STALE-OPEN = open `check` ONLY. A check expects no reply, so it is the single
    unconditionally-safe archival candidate. A still-pending actionable message is
    never bucketed safe-to-archive; if it has gone stale, LIVENESS surfaces it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .core import Msg, Problem
from .turn import open_messages

# Open types that still await someone's real work:
#   directive   -> awaits the addressed DEV/MAIN
#   deliverable -> awaits MAIN's verify
#   verification-> awaits the recipient's check (NOT terminal)
#   bounce      -> awaits MASTER's re-direction
ACTIONABLE_TYPES = ("directive", "deliverable", "verification", "bounce")
# The only terminal type: a check expects no reply, so an open check is the one
# safe-to-archive case. Nothing else belongs in stale-open.
STALE_TYPES = ("check",)
# An open actionable message overtaken by this many newer bus messages is stalled.
LIVENESS_THRESHOLD = 3

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


def actionable_open(messages: list[Msg]) -> list[Msg]:
    """OPEN messages that still await real work, oldest-first.

    directive/deliverable/verification/bounce: each is pending until answered. A
    verification is included because it awaits the recipient's check. Supersession
    does NOT remove a message here - a still-pending message is never silently
    dropped; liveness_stalled flags it if it has gone stale.
    """
    return [m for m in open_messages(messages) if m.fields.get("type") in ACTIONABLE_TYPES]


def stale_open(messages: list[Msg]) -> list[Msg]:
    """OPEN `check` messages - the only terminal, safe-to-archive type, oldest-first."""
    return [m for m in open_messages(messages) if m.fields.get("type") in STALE_TYPES]


def liveness_stalled(messages: list[Msg]) -> list[Problem]:
    """OPEN actionable messages overtaken by >= LIVENESS_THRESHOLD newer bus
    messages without an answer: a stalled thread to chase / investigate / hand to
    a human, NOT an archival candidate. PROTOCOL.md LIVENESS, mechanized.
    """
    problems: list[Problem] = []
    for m in actionable_open(messages):
        newer = sum(1 for other in messages if other.filename > m.filename)
        if newer >= LIVENESS_THRESHOLD:
            to = m.fields.get("to", "?")
            problems.append(Problem(
                m.filename, "liveness.stalled",
                f"{to} not acted on {m.filename} across {newer} newer",
            ))
    return problems
