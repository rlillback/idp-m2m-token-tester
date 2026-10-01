"""Decode a JWT. Decoding is unverified unless a signing key is supplied."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

import jwt

from .errors import VerificationError
from .models import DecodedToken

TIME_CLAIMS = ("iat", "nbf", "auth_time", "exp")


def looks_like_jwt(token: str) -> bool:
    return token.count(".") == 2 and all(token.split("."))


def format_time(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    try:
        return datetime.fromtimestamp(value, UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    except (OverflowError, OSError, ValueError):
        return None


def decode_token(token: str, jwks_uri: str | None = None, now: float | None = None) -> DecodedToken:
    """Decode `token`. If `jwks_uri` is given, also verify the signature (audience not checked)."""
    if not looks_like_jwt(token):
        return DecodedToken(is_jwt=False)
    try:
        header = jwt.get_unverified_header(token)
        payload = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError:
        return DecodedToken(is_jwt=False)

    verified = False
    if jwks_uri:
        try:
            key = jwt.PyJWKClient(jwks_uri).get_signing_key_from_jwt(token).key
            jwt.decode(
                token,
                key,
                algorithms=[header.get("alg", "RS256")],
                options={"verify_aud": False},
            )
            verified = True
        except jwt.PyJWTError as exc:
            raise VerificationError(f"Signature verification failed: {exc}") from exc

    times = {c: t for c in TIME_CLAIMS if (t := format_time(payload.get(c))) is not None}
    exp, iat = payload.get("exp"), payload.get("iat")
    lifetime = (
        int(exp - iat) if isinstance(exp, int | float) and isinstance(iat, int | float) else None
    )
    expired = (
        (exp < (time.time() if now is None else now)) if isinstance(exp, int | float) else None
    )
    return DecodedToken(True, header, payload, times, lifetime, expired, verified)
