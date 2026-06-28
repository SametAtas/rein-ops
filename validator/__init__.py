"""rein-ops protocol validator: pure checks, derived-turn logic, and a thin CLI.

Slice 1 = per-message/STATE validation (core). Slice 2 = derived-turn and reply
legality over a set of messages (turn). Slice 3 = NEEDS-HUMAN render + liveness /
stale-thread detection (status).
"""

from __future__ import annotations

from .core import Msg, Problem, parse_message, validate_message, validate_state
from .status import HumanItem, actionable_open, human_queue, stale_open
from .turn import open_messages, reply_problems, turn_for

__all__ = [
    "HumanItem",
    "Msg",
    "Problem",
    "actionable_open",
    "human_queue",
    "open_messages",
    "parse_message",
    "reply_problems",
    "stale_open",
    "turn_for",
    "validate_message",
    "validate_state",
]
