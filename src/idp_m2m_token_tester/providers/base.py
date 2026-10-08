from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar

import requests

from ..config import Setting, mask
from ..errors import TokenRequestError
from ..models import TokenResponse

TIMEOUT = 15

AUTH_METHODS = ("client_secret_post", "client_secret_basic")


@dataclass(frozen=True)
class TokenRequest:
    url: str
    form: dict[str, str] | None = None
    json_body: dict[str, str] | None = None
    basic_auth: tuple[str, str] | None = None
    headers: dict[str, str] = field(default_factory=dict)


class IdpProvider(ABC):
    """One subclass per IdP. Subclasses declare their settings and build the token request."""

    name: ClassVar[str]
    display_name: ClassVar[str]

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

    @abstractmethod
    def settings(self) -> list[Setting]: ...

    @abstractmethod
    def build_request(self, values: Mapping[str, str]) -> TokenRequest: ...

    def jwks_uri(self, values: Mapping[str, str]) -> str | None:
        """Where to find signing keys for --verify. None if unknown."""
        return None

    def discovery_url(self, values: Mapping[str, str]) -> str | None:
        """OIDC/OAuth metadata document for this IdP. None if unknown."""
        return None

    def connection_info(
        self, values: Mapping[str, str], issuer: str | None = None
    ) -> dict[str, str]:
        """Settings a client app needs to connect, derived from the real token request.

        The client secret is masked; it is never printed.
        """
        req = self.build_request(values)
        body = req.json_body or req.form or {}
        info = {"Provider": self.display_name}
        if discovery := self.discovery_url(values):
            info["Discovery URL"] = discovery
        if issuer:
            info["Issuer"] = issuer
        info["Token endpoint"] = req.url
        if jwks := self.jwks_uri(values):
            info["JWKS URI"] = jwks
        info["Grant type"] = body.get("grant_type", "client_credentials")
        info["Client ID"] = values["client_id"]
        info["Client secret"] = f"{mask(values['client_secret'])} (not shown)"
        info["Client auth"] = "client_secret_basic" if req.basic_auth else "client_secret_post"
        if req.json_body is not None:
            info["Client auth"] += " (JSON body)"
        for k in ("audience", "resource", "scope"):
            if body.get(k):
                info[k.capitalize()] = body[k]
        return info

    def fetch_token(self, values: Mapping[str, str]) -> TokenResponse:
        req = self.build_request(values)
        try:
            resp = self.session.post(
                req.url,
                data=req.form,
                json=req.json_body,
                auth=req.basic_auth,
                headers={"Accept": "application/json", **req.headers},
                timeout=TIMEOUT,
            )
        except requests.RequestException as exc:
            raise TokenRequestError(f"Could not reach {req.url}: {exc}") from exc
        body = _json_or_none(resp)
        if not resp.ok:
            detail = _error_detail(body) or resp.text[:300]
            raise TokenRequestError(
                f"{self.display_name} returned HTTP {resp.status_code}: {detail}"
            )
        if not isinstance(body, dict) or not body.get("access_token"):
            raise TokenRequestError(f"{self.display_name} response had no access_token.")
        expires = body.get("expires_in")
        return TokenResponse(
            access_token=str(body["access_token"]),
            token_type=body.get("token_type"),
            expires_in=int(str(expires)) if str(expires).isdigit() else None,
            scope=body.get("scope"),
        )


def apply_client_auth(url: str, values: Mapping[str, str], form: dict[str, str]) -> TokenRequest:
    """Attach client credentials per `auth_method` (post body by default, or HTTP Basic)."""
    if values.get("auth_method") == "client_secret_basic":
        return TokenRequest(
            url, form=form, basic_auth=(values["client_id"], values["client_secret"])
        )
    form = {**form, "client_id": values["client_id"], "client_secret": values["client_secret"]}
    return TokenRequest(url, form=form)


def _json_or_none(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except ValueError:
        return None


def _error_detail(body: Any) -> str | None:
    if isinstance(body, dict):
        parts = [str(body[k]) for k in ("error", "error_description", "message") if body.get(k)]
        return ": ".join(parts) or None
    return None
