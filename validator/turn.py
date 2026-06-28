"""Derived-turn computation and reply legality over a set of BUS messages.

Mechanizes PROTOCOL.md's "Turn model" (no IN_FLIGHT, no turn token - the turn is
DERIVED from the bus):
  - A message M is ANSWERED iff some OTHER message's `re:` equals M's filename or
    its bare id (filename without `.md`). Otherwise M is OPEN.
  - The turn holder for a role R is the latest (by UTC-stamp filename) OPEN
    message addressed `to: R`; a role with no open message to it is WAITING.

Pure: operates on parsed Msg objects, never touches the filesystem. The CLI reads
BUS/ and feeds the messages in.
"""

from __future__ import annotations

from .core import Msg, Problem

ROLES = ("MASTER", "DEV", "MAIN")


def _bare_id(filename: str) -> str:
    return filename[:-3] if filename.endswith(".md") else filename


def _answers(answerer: Msg, target: Msg) -> bool:
    """True if *answerer* is a different message whose re: points at *target*."""
    re_val = answerer.fields.get("re")
    if not re_val or answerer.filename == target.filename:
        return False
    return re_val.strip() in (target.filename, _bare_id(target.filename))


def open_messages(messages: list[Msg]) -> list[Msg]:
    """The OPEN subset: messages no other message answers, oldest-first."""
    ordered = sorted(messages, key=lambda m: m.filename)
    return [m for m in ordered if not any(_answers(other, m) for other in messages)]


def turn_for(role: str, messages: list[Msg]) -> Msg | None:
    """The latest OPEN message addressed to *role*, or None when WAITING."""
    candidates = [m for m in open_messages(messages) if m.fields.get("to") == role]
    if not candidates:
        return None
    return max(candidates, key=lambda m: m.filename)  # UTC-stamp prefix sorts by time


def reply_problems(messages: list[Msg]) -> list[Problem]:
    """Fail-closed reply legality.

    A NON-directive whose `re:` does not resolve to an existing message on the bus
    is `reply.dangling-re`. Directives are exempt: they may anchor to a
    `CRITICAL_PATH#N` rather than a prior message. A missing `re:` is a slice-1
    concern (message.missing-key), not a dangling reference.
    """
    known: set[str] = set()
    for m in messages:
        known.add(m.filename)
        known.add(_bare_id(m.filename))
    problems: list[Problem] = []
    for m in messages:
        if m.fields.get("type") == "directive":
            continue
        re_val = m.fields.get("re")
        if not re_val:
            continue
        re_val = re_val.strip()
        if re_val not in known:
            problems.append(Problem(
                m.filename, "reply.dangling-re",
                f"re: {re_val!r} does not resolve to any message on the bus",
            ))
    return problems
