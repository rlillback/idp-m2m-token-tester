import pytest

from idp_m2m_token_tester.envfile import merged_environment
from idp_m2m_token_tester.errors import ConfigError


def test_env_file_loaded_and_real_env_wins(tmp_path):
    f = tmp_path / ".env"
    f.write_text('A=from_file\nB="quoted value"\n# comment\nexport C=3\n')
    f.chmod(0o600)
    out = merged_environment(f, {"A": "from_env"})
    assert out == {"A": "from_env", "B": "quoted value", "C": "3"}


def test_missing_default_ignored_missing_explicit_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert merged_environment(None, {"X": "1"}) == {"X": "1"}
    with pytest.raises(ConfigError):
        merged_environment(tmp_path / "nope.env", {})


def test_loose_permissions_warn(tmp_path, capsys):
    f = tmp_path / ".env"
    f.write_text("A=1\n")
    f.chmod(0o644)
    merged_environment(f, {})
    assert "chmod 600" in capsys.readouterr().err
