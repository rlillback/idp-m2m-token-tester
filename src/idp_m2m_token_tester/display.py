"""Render results. The access token is printed on a single line and never written to disk."""

from __future__ import annotations

import json
from typing import TextIO

from .models import DecodedToken, TokenResponse


def render(response: TokenResponse, decoded: DecodedToken, out: TextIO) -> None:
    def line(text: str = "") -> None:
        print(text, file=out)

    line("== Token response ==")
    line(f"token_type : {response.token_type or '-'}")
    line(f"expires_in : {response.expires_in if response.expires_in is not None else '-'}")
    line(f"scope      : {response.scope or '-'}")
    line()
    line("== Access token (single line) ==")
    line(response.access_token)
    line()
    if not decoded.is_jwt:
        line("Token is not a JWT (opaque token); nothing to decode.")
        return
    status = "signature VERIFIED" if decoded.signature_verified else "signature NOT verified"
    line(f"== Header ({status}) ==")
    line(json.dumps(decoded.header, indent=2))
    line()
    line("== Payload ==")
    line(json.dumps(decoded.payload, indent=2))
    line()
    line("== Times ==")
    for claim, text in decoded.times.items():
        line(f"{claim:<9}: {text}")
    if decoded.lifetime_seconds is not None:
        line(f"lifetime : {decoded.lifetime_seconds}s")
    if decoded.expired is not None:
        line(f"expired  : {'YES' if decoded.expired else 'no'}")
