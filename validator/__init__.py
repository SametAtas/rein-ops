"""rein-ops protocol validator (slice 1): pure checks + a thin CLI."""

from __future__ import annotations

from .core import Problem, validate_message, validate_state

__all__ = ["Problem", "validate_message", "validate_state"]
