from __future__ import annotations

from collections.abc import Mapping

from ..config import Setting
from .base import IdpProvider, TokenRequest


class Auth0Provider(IdpProvider):
    name = "auth0"
    display_name = "Auth0"

    def settings(self) -> list[Setting]:
        return [
            Setting("domain", "AUTH0_DOMAIN", "Auth0 domain (e.g. tenant.us.auth0.com)"),
            Setting("client_id", "AUTH0_CLIENT_ID", "Client ID"),
            Setting("client_secret", "AUTH0_CLIENT_SECRET", "Client secret", secret=True),
            Setting("audience", "AUTH0_AUDIENCE", "API audience"),
            Setting("scope", "AUTH0_SCOPE", "Scope", required=False),
        ]

    def build_request(self, values: Mapping[str, str]) -> TokenRequest:
        body = {
            "grant_type": "client_credentials",
            "client_id": values["client_id"],
            "client_secret": values["client_secret"],
            "audience": values["audience"],
        }
        if values.get("scope"):
            body["scope"] = values["scope"]
        return TokenRequest(f"https://{values['domain']}/oauth/token", json_body=body)

    def jwks_uri(self, values: Mapping[str, str]) -> str | None:
        return f"https://{values['domain']}/.well-known/jwks.json"

    def discovery_url(self, values: Mapping[str, str]) -> str | None:
        return f"https://{values['domain']}/.well-known/openid-configuration"
