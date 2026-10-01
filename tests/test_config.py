import pytest

from idp_m2m_token_tester.config import Setting, resolve_settings
from idp_m2m_token_tester.errors import ConfigError


def fail(_: str) -> str:
    raise AssertionError("should not prompt")


def test_env_wins_no_prompt():
    out = resolve_settings([Setting("a", "A", "A")], {"A": "x"}, fail, fail)
    assert out == {"a": "x"}


def test_prompts_and_secret_uses_getpass():
    seen = []
    out = resolve_settings(
        [Setting("a", "A", "A"), Setting("s", "S", "S", secret=True)],
        {},
        lambda p: seen.append("input") or "v1",
        lambda p: seen.append("getpass") or "v2",
    )
    assert out == {"a": "v1", "s": "v2"} and seen == ["input", "getpass"]


def test_required_missing_raises():
    with pytest.raises(ConfigError):
        resolve_settings([Setting("a", "A", "A")], {}, lambda p: "", lambda p: "")


def test_default_optional_and_applies():
    out = resolve_settings(
        [
            Setting("k", "K", "K", default="d", required=False),
            Setting("o", "O", "O", required=False),
            Setting("x", "X", "X", applies=lambda v: v["k"] == "nope"),
        ],
        {},
        lambda p: "",
        lambda p: "",
    )
    assert out == {"k": "d"}


def test_choices_enforced():
    with pytest.raises(ConfigError):
        resolve_settings([Setting("a", "A", "A", choices=("x",))], {"A": "y"}, fail, fail)
