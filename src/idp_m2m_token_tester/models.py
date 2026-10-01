from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TokenResponse:
    access_token: str
    token_type: str | None = None
    expires_in: int | None = None
    scope: str | None = None


@dataclass(frozen=True)
class DecodedToken:
    is_jwt: bool
    header: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    times: dict[str, str] = field(default_factory=dict)
    lifetime_seconds: int | None = None
    expired: bool | None = None
    signature_verified: bool = False
