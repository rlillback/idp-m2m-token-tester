from __future__ import annotations

from collections.abc import Mapping

from ..config import Setting
from .base import AUTH_METHODS, IdpProvider, TokenRequest, apply_client_auth


class OktaProvider(IdpProvider):
    name = "okta"
    display_name = "Okta"

    def settings(self) -> list[Setting]:
        return [
            Setting("domain", "OKTA_DOMAIN", "Okta domain (e.g. dev-123.okta.com)"),
            Setting("client_id", "OKTA_CLIENT_ID", "Client ID"),
            Setting("client_secret", "OKTA_CLIENT_SECRET", "Client secret", secret=True),
            Setting("scope", "OKTA_SCOPE", "Scope (required by Okta)"),
            Setting(
                "auth_server",
                "OKTA_AUTH_SERVER",
                "Authorization server ID, or 'org' for the org server",
                required=False,
                default="default",
            ),
            Setting(
                "auth_method",
                "OKTA_AUTH_METHOD",
                "Client auth method",
                required=False,
                default="client_secret_post",
                choices=AUTH_METHODS,
            ),
        ]

    def _base(self, values: Mapping[str, str]) -> str:
        server = values.get("auth_server", "default")
        prefix = "oauth2" if server == "org" else f"oauth2/{server}"
        return f"https://{values['domain']}/{prefix}/v1"

    def build_request(self, values: Mapping[str, str]) -> TokenRequest:
        form = {"grant_type": "client_credentials", "scope": values["scope"]}
        return apply_client_auth(f"{self._base(values)}/token", values, form)

    def jwks_uri(self, values: Mapping[str, str]) -> str | None:
        return f"{self._base(values)}/keys"
