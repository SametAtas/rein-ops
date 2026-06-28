"""Pure validation of rein-ops BUS messages and STATE (fail-closed).

Slice 1 of the protocol validator: parse and check ONE message file and the
STATE files against PROTOCOL.md's message format and failure modes. No bus-hop
logic, no turn computation (later slices).

The authoritative contract is PROTOCOL.md. The role and type sets below are that
contract pinned as constants; every check maps a PROTOCOL failure mode to a
distinct rule id so a caller can act on the exact violation. validate_message is
strictly pure (text in, problems out). validate_state takes the rein-ops root
because its job is precisely to confirm the STATE files exist and are non-empty,
which the thin CLI then renders and turns into an exit code.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

ROLES = ("MASTER", "DEV", "MAIN")
TYPES = ("directive", "deliverable", "verification", "check", "bounce")
REQUIRED_KEYS = ("from", "to", "type", "re", "ratified")

# <UTCstamp>-<from>-to-<to>-<topic>.md, roles drawn from ROLES.
_FILENAME_RE = re.compile(
    r"^\d{8}T\d{4}-(?:MASTER|DEV|MAIN)-to-(?:MASTER|DEV|MAIN)-[A-Za-z0-9._-]+\.md$"
)

_STATE_FILES = ("CRITICAL_PATH.md", "LEDGER.md")


@dataclass(frozen=True)
class Problem:
    """A single fail-closed violation: where, which rule, and why."""

    file: str
    rule: str
    detail: str


@dataclass(frozen=True)
class Msg:
    """A parsed BUS message: its basename, frontmatter fields, and body.

    Shared by slice 2's turn/reply logic. Fields are raw strings (ratified stays
    a string here); the bool coercion lives in validate_message.
    """

    filename: str
    fields: dict[str, str]
    body: str


def _as_bool(value: str | None) -> bool | None:
    """Parse a frontmatter bool; None when the value is absent or not a bool."""
    if value is None:
        return None
    low = value.strip().lower()
    if low == "true":
        return True
    if low == "false":
        return False
    return None


def _split_frontmatter(
    text: str,
) -> tuple[dict[str, str] | None, str, str | None, str | None]:
    """Split `--- frontmatter --- body` with the stdlib only.

    Returns (fields, body, error_rule, error_detail). fields is None (and an
    error rule/detail is set) when the frontmatter is missing, unterminated, or
    has a line that is not `key: value`. Values are taken verbatim after the
    first colon and NOT comment-stripped, so a value like `CRITICAL_PATH#5`
    survives intact.
    """
    lines = text.splitlines()
    start = 0
    while start < len(lines) and lines[start].strip() == "":
        start += 1
    if start >= len(lines) or lines[start].strip() != "---":
        return None, "", "message.no-frontmatter", "missing opening '---' frontmatter fence"
    close = None
    for i in range(start + 1, len(lines)):
        if lines[i].strip() == "---":
            close = i
            break
    if close is None:
        return None, "", "message.bad-frontmatter", "unterminated frontmatter (no closing '---')"
    fields: dict[str, str] = {}
    for raw in lines[start + 1:close]:
        if raw.strip() == "":
            continue
        if ":" not in raw:
            return None, "", "message.bad-frontmatter", f"frontmatter line is not 'key: value': {raw.strip()!r}"
        key, value = raw.split(":", 1)
        fields[key.strip()] = value.strip()
    body = "\n".join(lines[close + 1:])
    return fields, body, None, None


def parse_message(text: str, filename: str) -> Msg:
    """Parse a BUS message into (basename, frontmatter fields, body).

    Reuses the slice-1 frontmatter parser. On unparseable frontmatter the fields
    are empty - such a message answers nothing and holds no turn, the safe
    degradation; validate_message is what flags the malformation.
    """
    fields, body, _rule, _detail = _split_frontmatter(text)
    return Msg(filename=os.path.basename(filename), fields=fields or {}, body=body)


def validate_message(text: str, filename: str) -> list[Problem]:
    """Check one BUS message's filename, frontmatter, and body, fail-closed."""
    base = os.path.basename(filename)
    problems: list[Problem] = []

    if not _FILENAME_RE.match(base):
        problems.append(Problem(
            base, "message.bad-filename",
            "filename must be '<UTCstamp>-<from>-to-<to>-<topic>.md' with roles in MASTER/DEV/MAIN",
        ))

    fields, body, err_rule, err_detail = _split_frontmatter(text)
    if fields is None:
        problems.append(Problem(base, err_rule or "message.bad-frontmatter", err_detail or "bad frontmatter"))
        return problems  # nothing further is checkable without frontmatter

    for key in REQUIRED_KEYS:
        if key not in fields:
            problems.append(Problem(base, "message.missing-key", f"missing required frontmatter key: {key}"))

    if "from" in fields and fields["from"] not in ROLES:
        problems.append(Problem(base, "message.bad-from", f"from must be one of {list(ROLES)}, got {fields['from']!r}"))
    if "to" in fields and fields["to"] not in ROLES:
        problems.append(Problem(base, "message.bad-to", f"to must be one of {list(ROLES)}, got {fields['to']!r}"))
    if "type" in fields and fields["type"] not in TYPES:
        problems.append(Problem(base, "message.unknown-type", f"type must be one of {list(TYPES)}, got {fields['type']!r}"))

    ratified = _as_bool(fields.get("ratified"))
    if "ratified" in fields and ratified is None:
        problems.append(Problem(base, "message.bad-ratified", f"ratified must be true/false, got {fields['ratified']!r}"))

    # GATE: a directive that tells DEV to build or MAIN to commit must be ratified.
    if fields.get("type") == "directive" and fields.get("to") in ("DEV", "MAIN") and ratified is not True:
        problems.append(Problem(
            base, "message.unratified-build",
            f"a directive to {fields.get('to')} requires ratified: true",
        ))

    if body.strip() == "":
        problems.append(Problem(base, "message.empty-body", "message body after the frontmatter is empty"))

    return problems


def validate_state(root: str) -> list[Problem]:
    """Confirm the STATE files under *root* exist and are non-empty (slice 1)."""
    problems: list[Problem] = []
    for name in _STATE_FILES:
        rel = os.path.join("STATE", name)
        path = os.path.join(root, "STATE", name)
        if not os.path.isfile(path):
            problems.append(Problem(rel, "state.missing", f"required STATE file is missing: {rel}"))
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
        except OSError as exc:
            problems.append(Problem(rel, "state.unreadable", f"cannot read {rel}: {exc}"))
            continue
        if content.strip() == "":
            problems.append(Problem(rel, "state.empty", f"STATE file is empty: {rel}"))
    return problems
