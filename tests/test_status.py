"""Tests for slice 3: NEEDS-HUMAN queue render + liveness / stale-thread split.

Deterministic and offline. The bus- and NEEDS-HUMAN-dependent assertions run on
in-memory fixtures (the live files mutate as chats reply); skip-guarded tests pin
the stable live facts the BAR names so they verify the real repo without rotting.
"""

from __future__ import annotations

import os

import pytest

from validator.cli import main
from validator.core import Msg, parse_message
from validator.status import (
    actionable_open,
    human_queue,
    stale_open,
)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _m(name: str, frm: str, to: str, typ: str, re: str) -> Msg:
    return Msg(filename=name, fields={"from": frm, "to": to, "type": typ, "re": re}, body="b")


# -- human_queue (BAR row 1) --------------------------------------------------

_NEEDS_HUMAN = """\
# NEEDS-HUMAN (the only file you must watch)

Format: `- [<UTCstamp>] [<role>] <action> - <how to respond>`

- [20260628T0702] [MASTER] Start the clean Keystone N>=50 run (CRITICAL_PATH#4) -
  the frozen config is ready: reply "running" once the first window is in.

## Resolved

- [20260628] [MAIN] Publish rein-engine 0.4.0 to PyPI - DONE (owner published v0.4.0).
- [20260628] [MAIN] Confirm the Keystone arm pin - DONE ("pin go").
"""


def test_human_queue_returns_only_open_item() -> None:
    items, problems = human_queue(_NEEDS_HUMAN)
    assert problems == []
    assert len(items) == 1
    only = items[0]
    assert only.stamp == "20260628T0702"
    assert only.role == "MASTER"
    assert only.text.startswith("Start the clean Keystone N>=50 run")


def test_human_queue_excludes_resolved_section() -> None:
    items, _ = human_queue(_NEEDS_HUMAN)
    joined = " ".join(it.text for it in items)
    assert "DONE" not in joined  # the two Resolved DONE lines are dropped
    assert all(it.stamp != "20260628" for it in items)


def test_human_queue_continuation_lines_joined() -> None:
    items, _ = human_queue(_NEEDS_HUMAN)
    # The wrapped second physical line is folded into the one item's text.
    assert "frozen config is ready" in items[0].text


def test_human_queue_malformed_open_line_is_bad_line() -> None:
    text = (
        "# NEEDS-HUMAN\n\n"
        "- [20260628T0702] [MASTER] a good one - respond X\n"
        "- this open bullet has no [stamp] [role] prefix\n"
        "\n## Resolved\n- [x] [MAIN] something - DONE\n"
    )
    items, problems = human_queue(text)
    assert len(items) == 1  # the good one survives
    assert len(problems) == 1
    assert problems[0].rule == "human.bad-line"


def test_human_queue_empty_and_header_only() -> None:
    items, problems = human_queue("# NEEDS-HUMAN\n\nFormat: `...`\n\n## Resolved\n")
    assert items == [] and problems == []


# -- actionable_open / stale_open (BAR row 2) ---------------------------------

def _snapshot() -> list[Msg]:
    """Mirrors the live bus shape: 4 open, 0 actionable, 4 stale."""
    return [
        _m("20260628T0632-MASTER-to-MAIN-eval-baseline.md", "MASTER", "MAIN", "directive", "CRITICAL_PATH#3"),
        _m("20260628T0643-MASTER-to-DEV-validator-slice1.md", "MASTER", "DEV", "directive", "CRITICAL_PATH#5"),
        _m("20260628T0644-MAIN-to-MASTER-eval-baseline.md", "MAIN", "MASTER", "bounce", "20260628T0632-MASTER-to-MAIN-eval-baseline.md"),
        _m("20260628T0650-MAIN-to-MASTER-eval-baseline.md", "MAIN", "MASTER", "verification", "20260628T0632-MASTER-to-MAIN-eval-baseline.md"),
        _m("20260628T0652-MASTER-to-MAIN-eval-baseline-ratify.md", "MASTER", "MAIN", "directive", "20260628T0644-MAIN-to-MASTER-eval-baseline.md"),
        _m("20260628T0658-DEV-to-MAIN-validator-slice1.md", "DEV", "MAIN", "deliverable", "20260628T0643-MASTER-to-DEV-validator-slice1.md"),
        _m("20260628T0702-MASTER-to-MAIN-eval-baseline-check.md", "MASTER", "MAIN", "check", "20260628T0650-MAIN-to-MASTER-eval-baseline.md"),
        _m("20260628T0712-MAIN-to-MASTER-validator-slice1.md", "MAIN", "MASTER", "verification", "20260628T0658-DEV-to-MAIN-validator-slice1.md"),
        _m("20260628T0713-MASTER-to-MAIN-validator-slice1-check.md", "MASTER", "MAIN", "check", "20260628T0712-MAIN-to-MASTER-validator-slice1.md"),
        _m("20260628T0714-MASTER-to-DEV-validator-slice2.md", "MASTER", "DEV", "directive", "CRITICAL_PATH#5"),
        _m("20260628T0726-DEV-to-MAIN-validator-slice2.md", "DEV", "MAIN", "deliverable", "20260628T0714-MASTER-to-DEV-validator-slice2.md"),
        _m("20260628T0735-MAIN-to-MASTER-validator-slice2.md", "MAIN", "MASTER", "verification", "20260628T0726-DEV-to-MAIN-validator-slice2.md"),
    ]


def _names(msgs) -> set[str]:
    return {m.filename for m in msgs}


def test_actionable_open_pending_directive() -> None:
    # A fresh, unanswered, non-superseded directive is actionable.
    msgs = [_m("20260628T0900-MASTER-to-DEV-x.md", "MASTER", "DEV", "directive", "CRITICAL_PATH#7")]
    assert _names(actionable_open(msgs)) == {"20260628T0900-MASTER-to-DEV-x.md"}
    assert stale_open(msgs) == []


def test_terminal_ack_is_stale_not_actionable() -> None:
    # An open check/verification awaits no reply -> stale, never actionable.
    chk = _m("20260628T0901-MASTER-to-MAIN-x.md", "MASTER", "MAIN", "check", "CRITICAL_PATH#1")
    ver = _m("20260628T0902-MAIN-to-MASTER-y.md", "MAIN", "MASTER", "verification", "CRITICAL_PATH#1")
    msgs = [chk, ver]
    assert actionable_open(msgs) == []
    assert _names(stale_open(msgs)) == {chk.filename, ver.filename}


def test_superseded_directive_is_stale_not_actionable() -> None:
    # Two open directives to the same role: the older is superseded -> stale.
    old = _m("20260628T1000-MASTER-to-MAIN-a.md", "MASTER", "MAIN", "directive", "CRITICAL_PATH#1")
    new = _m("20260628T1100-MASTER-to-MAIN-b.md", "MASTER", "MAIN", "directive", "CRITICAL_PATH#2")
    msgs = [old, new]
    assert _names(actionable_open(msgs)) == {new.filename}  # only the newer is live
    assert _names(stale_open(msgs)) == {old.filename}


def test_supersede_is_per_to_role() -> None:
    # Different `to:` roles never supersede each other.
    a = _m("20260628T1000-MASTER-to-DEV-a.md", "MASTER", "DEV", "directive", "CRITICAL_PATH#1")
    b = _m("20260628T1100-MAIN-to-MASTER-b.md", "MAIN", "MASTER", "bounce", "CRITICAL_PATH#2")
    msgs = [a, b]
    assert _names(actionable_open(msgs)) == {a.filename, b.filename}
    assert stale_open(msgs) == []


def test_snapshot_matches_live_split() -> None:
    snap = _snapshot()
    assert actionable_open(snap) == []  # nothing awaits real work
    stale = _names(stale_open(snap))
    # the 0702/0713 checks the BAR names, plus the superseded ratify + slice2 verification
    assert stale == {
        "20260628T0652-MASTER-to-MAIN-eval-baseline-ratify.md",
        "20260628T0702-MASTER-to-MAIN-eval-baseline-check.md",
        "20260628T0713-MASTER-to-MAIN-validator-slice1-check.md",
        "20260628T0735-MAIN-to-MASTER-validator-slice2.md",
    }


def test_actionable_and_stale_are_disjoint() -> None:
    snap = _snapshot()
    assert _names(actionable_open(snap)).isdisjoint(_names(stale_open(snap)))


# -- CLI --status (BAR row 3) -------------------------------------------------

def test_cli_status_live_exit_zero(capsys) -> None:
    if not os.path.isdir(os.path.join(_ROOT, "BUS")):
        pytest.skip("live BUS/ archived")
    rc = main(["--status", _ROOT])
    out = capsys.readouterr().out
    assert "NEEDS-HUMAN open queue" in out
    assert "ACTIONABLE open messages" in out
    assert "STALE-OPEN archival candidates" in out
    assert rc == 0


def test_cli_status_planted_dangling_re_exit_nonzero(tmp_path, capsys) -> None:
    bus = tmp_path / "BUS"
    bus.mkdir()
    (tmp_path / "NEEDS-HUMAN.md").write_text("# NEEDS-HUMAN\n", encoding="utf-8")
    (bus / "20260628T0100-MASTER-to-DEV-x.md").write_text(
        "---\nfrom: MASTER\nto: DEV\ntype: directive\nre: CRITICAL_PATH#1\nratified: true\n---\nbody\n",
        encoding="utf-8")
    (bus / "20260628T0200-DEV-to-MAIN-x.md").write_text(
        "---\nfrom: DEV\nto: MAIN\ntype: deliverable\nre: 20260628T9999-nope.md\nratified: false\n---\nbody\n",
        encoding="utf-8")
    rc = main(["--status", str(tmp_path)])
    out = capsys.readouterr().out
    assert "reply.dangling-re" in out
    assert rc == 1


def test_cli_status_planted_bad_human_line_exit_nonzero(tmp_path, capsys) -> None:
    (tmp_path / "BUS").mkdir()
    (tmp_path / "NEEDS-HUMAN.md").write_text(
        "# NEEDS-HUMAN\n\n- this bullet has no stamp or role prefix\n", encoding="utf-8")
    rc = main(["--status", str(tmp_path)])
    out = capsys.readouterr().out
    assert "human.bad-line" in out
    assert rc == 1


def test_cli_status_planted_bad_message_exit_nonzero(tmp_path, capsys) -> None:
    bus = tmp_path / "BUS"
    bus.mkdir()
    (tmp_path / "NEEDS-HUMAN.md").write_text("# NEEDS-HUMAN\n", encoding="utf-8")
    # slice-1 invalid: unknown type.
    (bus / "20260628T0100-MASTER-to-DEV-x.md").write_text(
        "---\nfrom: MASTER\nto: DEV\ntype: bogus\nre: CRITICAL_PATH#1\nratified: true\n---\nbody\n",
        encoding="utf-8")
    rc = main(["--status", str(tmp_path)])
    out = capsys.readouterr().out
    assert "message.unknown-type" in out
    assert rc == 1


# -- live positive controls (skip if archived, BAR row 1/2) -------------------

def test_live_human_queue_open_item(capsys) -> None:
    path = os.path.join(_ROOT, "NEEDS-HUMAN.md")
    if not os.path.isfile(path):
        pytest.skip("NEEDS-HUMAN.md not present")
    with open(path, encoding="utf-8") as fh:
        items, problems = human_queue(fh.read())
    assert problems == []
    # the live OPEN item is the Keystone start ask; Resolved DONE lines excluded.
    assert any("Keystone" in it.text for it in items)
    assert all("DONE" not in it.text for it in items)


def test_live_stale_includes_known_checks() -> None:
    bus = os.path.join(_ROOT, "BUS")
    if not os.path.isdir(bus):
        pytest.skip("live BUS/ archived")
    import glob
    msgs = [parse_message(open(p, encoding="utf-8").read(), p) for p in glob.glob(os.path.join(bus, "*.md"))]
    stale = _names(stale_open(msgs))
    for known in ("0702-MASTER-to-MAIN-eval-baseline-check", "0713-MASTER-to-MAIN-validator-slice1-check"):
        if any(known in m.filename for m in msgs):
            assert any(known in n for n in stale), f"{known} should be a stale archive candidate"
