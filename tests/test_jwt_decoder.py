import jwt

from idp_m2m_token_tester.jwt_decoder import decode_token


def make(claims):
    return jwt.encode(claims, "secret-secret-secret-secret-1234", algorithm="HS256")


def test_decodes_claims_and_times():
    d = decode_token(make({"sub": "a", "iat": 1000, "exp": 1600}), now=2000)
    assert d.is_jwt and d.payload["sub"] == "a" and d.header["alg"] == "HS256"
    assert d.lifetime_seconds == 600 and d.expired is True
    assert d.times["exp"].startswith("1970-01-01") and not d.signature_verified


def test_not_expired():
    assert decode_token(make({"exp": 5000}), now=1).expired is False


def test_opaque_token():
    assert decode_token("abc123").is_jwt is False
    assert decode_token("a.b.c").is_jwt is False
