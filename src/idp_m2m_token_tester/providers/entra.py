from __future__ import annotations

from collections.abc import Mapping

from ..config import Setting
from .base import IdpProvider, TokenRequest


class EntraProvider(IdpProvider):
    name = "entra"
    display_name = "Microsoft Entra ID"

    def settings(self) -> list[Setting]:
        return [
            Setting("tenant_id", "ENTRA_TENANT_ID", "Tenant ID"),
            Setting("client_id", "ENTRA_CLIENT_ID", "Client ID"),
            Setting("client_secret", "ENTRA_CLIENT_SECRET", "Client secret", secret=True),
            Setting("scope", "ENTRA_SCOPE", "Scope", required=False),
        ]

    def build_request(self, values: Mapping[str, str]) -> TokenRequest:
        scope = values.get("scope") or f"api://{values['client_id']}/.default"
        form = {
            "grant_type": "client_credentials",
            "client_id": values["client_id"],
            "client_secret": values["client_secret"],
            "scope": scope,
        }
        url = f"https://login.microsoftonline.com/{values['tenant_id']}/oauth2/v2.0/token"
        return TokenRequest(url, form=form)

    def jwks_uri(self, values: Mapping[str, str]) -> str | None:
        return f"https://login.microsoftonline.com/{values['tenant_id']}/discovery/v2.0/keys"
