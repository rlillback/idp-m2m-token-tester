import jwt
import responses

from idp_m2m_token_tester import cli


@responses.activate
def test_end_to_end_prints_single_line_token(monkeypatch, capsys, tmp_path):
    claims = {"sub": "me", "iat": 1, "exp": 2, "iss": "https://t.auth0.com/"}
    token = jwt.encode(claims, "k" * 32, algorithm="HS256")
    responses.post("https://t.auth0.com/oauth/token", json={"access_token": token})
    for k, v in {
        "AUTH0_DOMAIN": "t.auth0.com",
        "AUTH0_CLIENT_ID": "i",
        "AUTH0_CLIENT_SECRET": "very-secret",
        "AUTH0_AUDIENCE": "a",
        "AUTH0_SCOPE": "",
    }.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr("builtins.input", lambda _: "")
    monkeypatch.chdir(tmp_path)
    assert cli.main(["--idp", "auth0"]) == 0
    out = capsys.readouterr().out
    assert token in out.splitlines()
    assert '"sub": "me"' in out
    connection = out.split("== Connection configuration ==")[1]
    assert "Token endpoint" in connection and "https://t.auth0.com/oauth/token" in connection
    assert "Issuer" in connection and "Client ID" in connection
    assert "very-secret" not in out
    assert list(tmp_path.iterdir()) == []  # nothing written to disk


def test_error_exit_code(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "")
    monkeypatch.setattr("getpass.getpass", lambda _: "")
    for k in ("AUTH0_DOMAIN",):
        monkeypatch.delenv(k, raising=False)
    assert cli.main(["--idp", "auth0"]) == 1
    assert "required" in capsys.readouterr().err
