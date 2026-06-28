"""Tests for the rein-ops protocol validator (slice 1).

Deterministic and offline: negative controls use inline messages, STATE tests use
tmp_path, and the live-bus positive control reads the real BUS/STATE when present.
"""

from __future__ import annotations

import os

import pytest

from validator.cli import main
from validator.core import validate_message, validate_state

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_BASE = {
    "from": "MASTER",
    "to": "DEV",
    "type": "directive",
    "re": "CRITICAL_PATH#5",
    "ratified": "true",
}
_NAME = "20260628T0643-MASTER-to-DEV-validator-slice1.md"


def _msg(fields: dict[str, str], body: str = "\nBuild the thing.\n") -> str:
    fm = "".join(f"{k}: {v}\n" for k, v in fields.items())
    return "---\n" + fm + "---\n" + body


def _rules(problems) -> set[str]:
    return {p.rule for p in problems}


# -- positive controls --------------------------------------------------------

def test_well_formed_directive_passes() -> None:
    assert validate_message(_msg(_BASE), _NAME) == []


def test_well_formed_deliverable_passes() -> None:
    # A deliverable is not a build/commit directive, so ratified: false is fine.
    fields = {"from": "DEV", "to": "MAIN", "type": "deliverable",
              "re": _NAME, "ratified": "false"}
    name = "20260628T0700-DEV-to-MAIN-validator-slice1.md"
    assert validate_message(_msg(fields), name) == []


# -- negative controls (each a distinct rule) ---------------------------------

def test_missing_frontmatter() -> None:
    assert "message.no-frontmatter" in _rules(validate_message("just a body\n", _NAME))


def test_unterminated_frontmatter() -> None:
    text = "---\nfrom: MASTER\nto: DEV\n"
    assert "message.bad-frontmatter" in _rules(validate_message(text, _NAME))


def test_unknown_type() -> None:
    assert "message.unknown-type" in _rules(validate_message(_msg({**_BASE, "type": "memo"}), _NAME))


def test_bad_from() -> None:
    assert "message.bad-from" in _rules(validate_message(_msg({**_BASE, "from": "BOSS"}), _NAME))


def test_bad_to() -> None:
    assert "message.bad-to" in _rules(validate_message(_msg({**_BASE, "to": "BOSS"}), _NAME))


def test_unratified_directive_to_dev() -> None:
    assert "message.unratified-build" in _rules(validate_message(_msg({**_BASE, "ratified": "false"}), _NAME))


def test_unratified_directive_to_main() -> None:
    fields = {**_BASE, "to": "MAIN", "ratified": "false"}
    name = "20260628T0632-MASTER-to-MAIN-eval-baseline.md"
    assert "message.unratified-build" in _rules(validate_message(_msg(fields), name))


def test_bad_ratified_value() -> None:
    assert "message.bad-ratified" in _rules(validate_message(_msg({**_BASE, "ratified": "yes"}), _NAME))


def test_empty_body() -> None:
    assert "message.empty-body" in _rules(validate_message(_msg(_BASE, body=""), _NAME))


def test_missing_required_key() -> None:
    fields = {k: v for k, v in _BASE.items() if k != "re"}
    assert "message.missing-key" in _rules(validate_message(_msg(fields), _NAME))


def test_bad_filename() -> None:
    assert "message.bad-filename" in _rules(validate_message(_msg(_BASE), "notes.md"))


def test_hash_in_value_preserved() -> None:
    # `re: CRITICAL_PATH#5` must not be truncated at '#'.
    assert validate_message(_msg(_BASE), _NAME) == []


# -- STATE --------------------------------------------------------------------

def _state(tmp_path, cp: str = "1. now\n", ledger: str = "- L1\n") -> str:
    state = tmp_path / "STATE"
    state.mkdir()
    (state / "CRITICAL_PATH.md").write_text(cp, encoding="utf-8")
    (state / "LEDGER.md").write_text(ledger, encoding="utf-8")
    return str(tmp_path)


def test_state_ok(tmp_path) -> None:
    assert validate_state(_state(tmp_path)) == []


def test_state_missing(tmp_path) -> None:
    assert _rules(validate_state(str(tmp_path))) == {"state.missing"}


def test_state_empty(tmp_path) -> None:
    assert _rules(validate_state(_state(tmp_path, cp="   \n", ledger=""))) == {"state.empty"}


# -- CLI ----------------------------------------------------------------------

def test_cli_clean_exit_zero(tmp_path) -> None:
    f = tmp_path / _NAME
    f.write_text(_msg(_BASE), encoding="utf-8")
    assert main([str(f)]) == 0


def test_cli_problem_exit_nonzero(tmp_path) -> None:
    f = tmp_path / _NAME
    f.write_text(_msg({**_BASE, "type": "memo"}), encoding="utf-8")
    assert main([str(f)]) == 1


def test_cli_state_flag(tmp_path) -> None:
    assert main(["--state", _state(tmp_path)]) == 0


# -- live-bus positive control (skips if the bus has been archived) -----------

@pytest.mark.parametrize("name", [
    "20260628T0632-MASTER-to-MAIN-eval-baseline.md",
    "20260628T0643-MASTER-to-DEV-validator-slice1.md",
])
def test_live_bus_messages_clean(name) -> None:
    path = os.path.join(_ROOT, "BUS", name)
    if not os.path.isfile(path):
        pytest.skip(f"{name} no longer on the live bus")
    with open(path, encoding="utf-8") as fh:
        assert validate_message(fh.read(), path) == []


def test_live_state_clean() -> None:
    assert validate_state(_ROOT) == []
