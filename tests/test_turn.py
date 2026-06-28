"""Tests for slice 2: derived turn computation and reply legality.

Deterministic and offline. Turn assertions use constructed snapshots (the live
bus mutates as chats reply); a skip-guarded test pins the permanently-answered
live messages.
"""

from __future__ import annotations

import os

import pytest

from validator.cli import main
from validator.core import Msg, parse_message
from validator.turn import open_messages, reply_problems, turn_for

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _m(name: str, frm: str, to: str, typ: str, re: str) -> Msg:
    return Msg(filename=name, fields={"from": frm, "to": to, "type": typ, "re": re}, body="b")


# A snapshot mirroring the live bus shape at the moment slice 2 is the DEV turn.
def _snapshot() -> list[Msg]:
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
    ]


def _names(msgs) -> set[str]:
    return {m.filename for m in msgs}


def test_open_set_matches_bar() -> None:
    opens = _names(open_messages(_snapshot()))
    assert {"20260628T0652-MASTER-to-MAIN-eval-baseline-ratify.md",
            "20260628T0702-MASTER-to-MAIN-eval-baseline-check.md",
            "20260628T0713-MASTER-to-MAIN-validator-slice1-check.md",
            "20260628T0714-MASTER-to-DEV-validator-slice2.md"} == opens
    # BAR row 1: these each have a later re: and must NOT be open.
    for answered in ("0644", "0650", "0658", "0712"):
        assert not any(answered in n for n in opens)


def test_turn_for_roles() -> None:
    snap = _snapshot()
    assert turn_for("DEV", snap).filename == "20260628T0714-MASTER-to-DEV-validator-slice2.md"
    assert turn_for("MAIN", snap).filename == "20260628T0713-MASTER-to-MAIN-validator-slice1-check.md"
    assert turn_for("MASTER", snap) is None  # waiting


def test_turn_waiting_after_reply() -> None:
    snap = _snapshot()
    snap.append(_m("20260628T0720-DEV-to-MAIN-validator-slice2.md", "DEV", "MAIN", "deliverable",
                   "20260628T0714-MASTER-to-DEV-validator-slice2.md"))
    assert turn_for("DEV", snap) is None  # 0714 now answered
    assert turn_for("MAIN", snap).filename == "20260628T0720-DEV-to-MAIN-validator-slice2.md"


def test_answered_by_bare_id() -> None:
    a = _m("20260628T0800-MASTER-to-DEV-x.md", "MASTER", "DEV", "directive", "CRITICAL_PATH#1")
    # reply references the bare id (no .md) - still answers.
    b = _m("20260628T0801-DEV-to-MAIN-x.md", "DEV", "MAIN", "deliverable", "20260628T0800-MASTER-to-DEV-x")
    assert _names(open_messages([a, b])) == {"20260628T0801-DEV-to-MAIN-x.md"}


def test_reply_problems_clean_on_snapshot() -> None:
    assert reply_problems(_snapshot()) == []


def test_reply_problems_flags_dangling() -> None:
    msgs = [_m("20260628T0900-DEV-to-MAIN-x.md", "DEV", "MAIN", "deliverable", "20260628T0000-MASTER-to-DEV-nope.md")]
    probs = reply_problems(msgs)
    assert len(probs) == 1 and probs[0].rule == "reply.dangling-re"


def test_directive_anchor_re_not_dangling() -> None:
    msgs = [_m("20260628T0901-MASTER-to-DEV-x.md", "MASTER", "DEV", "directive", "CRITICAL_PATH#7")]
    assert reply_problems(msgs) == []


# -- CLI (BAR row 4) ----------------------------------------------------------

def test_cli_bus_clean_exit_zero(capsys) -> None:
    bus = os.path.join(_ROOT, "BUS")
    if not os.path.isdir(bus):
        pytest.skip("live BUS/ archived")
    rc = main(["--bus", _ROOT])
    out = capsys.readouterr().out
    assert "TURN (latest open message per role):" in out
    assert "OPEN messages" in out
    assert rc == 0


def test_cli_bus_planted_dangling_re_exit_nonzero(tmp_path, capsys) -> None:
    bus = tmp_path / "BUS"
    bus.mkdir()
    (bus / "20260628T0100-MASTER-to-DEV-x.md").write_text(
        "---\nfrom: MASTER\nto: DEV\ntype: directive\nre: CRITICAL_PATH#1\nratified: true\n---\nbody\n",
        encoding="utf-8")
    (bus / "20260628T0200-DEV-to-MAIN-x.md").write_text(
        "---\nfrom: DEV\nto: MAIN\ntype: deliverable\nre: 20260628T9999-nope.md\nratified: false\n---\nbody\n",
        encoding="utf-8")
    rc = main(["--bus", str(tmp_path)])
    out = capsys.readouterr().out
    assert "reply.dangling-re" in out
    assert rc == 1


# -- live-bus stable facts (skip if archived) ---------------------------------

@pytest.mark.parametrize("answered", [
    "20260628T0644-MAIN-to-MASTER-eval-baseline.md",
    "20260628T0658-DEV-to-MAIN-validator-slice1.md",
])
def test_live_answered_not_open(answered) -> None:
    bus = os.path.join(_ROOT, "BUS")
    if not os.path.isfile(os.path.join(bus, answered)):
        pytest.skip(f"{answered} no longer on the live bus")
    import glob
    msgs = [parse_message(open(p, encoding="utf-8").read(), p) for p in glob.glob(os.path.join(bus, "*.md"))]
    assert answered not in _names(open_messages(msgs))
