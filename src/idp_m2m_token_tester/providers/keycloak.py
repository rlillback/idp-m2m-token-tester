from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import requests

from ..config import Setting
from ..errors import TokenRequestError
from .base import TIMEOUT, IdpProvider, TokenRequest


class KeycloakProvider(IdpProvider):
    name = "keycloak"
    display_name = "Keycloak"

    def __init__(self, session: requests.Session | None = None) -> None:
        super().__init__(session)
        self._meta_cache: dict[str, tuple[str, dict[str, Any]]] = {}

    def settings(self) -> list[Setting]:
        return [
            Setting("base_url", "KC_BASE", "Keycloak base URL (e.g. https://kc.example.com)"),
            Setting("realm", "KC_REALM", "Realm"),
            Setting("client_id", "KC_CLIENT_ID", "Client ID"),
            Setting("client_secret", "KC_CLIENT_SECRET", "Client secret", secret=True),
            Setting("scope", "KC_SCOPE", "Scope", required=False),
        ]

    def _metadata(self, values: Mapping[str, str]) -> dict[str, Any]:
        return self._discover(values)[1]

    def _discover(self, values: Mapping[str, str]) -> tuple[str, dict[str, Any]]:
        """Return (metadata URL, metadata), fetched once per realm."""
        realm_url = f"{values['base_url'].rstrip('/')}/realms/{values['realm']}"
        if realm_url in self._meta_cache:
            return self._meta_cache[realm_url]
        last = "no response"
        for path in ("oauth-authorization-server", "openid-configuration"):
            url = f"{realm_url}/.well-known/{path}"
            try:
                resp = self.session.get(url, timeout=TIMEOUT)
            except requests.RequestException as exc:
                last = str(exc)
                continue
            if resp.ok:
                meta = resp.json()
                if isinstance(meta, dict):
                    self._meta_cache[realm_url] = (url, meta)
                    return url, meta
            last = f"HTTP {resp.status_code} from {url}"
        raise TokenRequestError(f"Keycloak discovery failed: {last}")

    def build_request(self, values: Mapping[str, str]) -> TokenRequest:
        endpoint = self._metadata(values).get("token_endpoint")
        if not endpoint:
            raise TokenRequestError("Keycloak metadata has no token_endpoint.")
        form = {
            "grant_type": "client_credentials",
            "client_id": values["client_id"],
            "client_secret": values["client_secret"],
        }
        if values.get("scope"):
            form["scope"] = values["scope"]
        return TokenRequest(str(endpoint), form=form)

    def jwks_uri(self, values: Mapping[str, str]) -> str | None:
        uri = self._metadata(values).get("jwks_uri")
        return str(uri) if uri else None

    def discovery_url(self, values: Mapping[str, str]) -> str | None:
        return self._discover(values)[0]
