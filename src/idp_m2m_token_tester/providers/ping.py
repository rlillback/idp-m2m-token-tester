from __future__ import annotations

from collections.abc import Mapping

from ..config import Setting
from .base import AUTH_METHODS, IdpProvider, TokenRequest, apply_client_auth


def _is(flavor: str):  # type: ignore[no-untyped-def]
    return lambda values: values.get("flavor") == flavor


class PingProvider(IdpProvider):
    """Supports PingOne (cloud) and PingFederate (self-hosted)."""

    name = "ping"
    display_name = "Ping Identity (PingOne / PingFederate)"

    def settings(self) -> list[Setting]:
        return [
            Setting(
                "flavor",
                "PING_FLAVOR",
                "Ping product",
                default="pingone",
                choices=("pingone", "pingfederate"),
                required=False,
            ),
            Setting("env_id", "PING_ENV_ID", "PingOne environment ID", applies=_is("pingone")),
            Setting(
                "region",
                "PING_REGION",
                "PingOne region TLD (com, eu, asia, ca, com.au)",
                required=False,
                default="com",
                applies=_is("pingone"),
            ),
            Setting(
                "host",
                "PING_HOST",
                "PingFederate host[:port] (e.g. pf.example.com:9031)",
                applies=_is("pingfederate"),
            ),
            Setting("client_id", "PING_CLIENT_ID", "Client ID"),
            Setting("client_secret", "PING_CLIENT_SECRET", "Client secret", secret=True),
            Setting("scope", "PING_SCOPE", "Scope", required=False),
            Setting(
                "auth_method",
                "PING_AUTH_METHOD",
                "Client auth method",
                required=False,
                default="client_secret_post",
                choices=AUTH_METHODS,
            ),
        ]

    def build_request(self, values: Mapping[str, str]) -> TokenRequest:
        form = {"grant_type": "client_credentials"}
        if values.get("scope"):
            form["scope"] = values["scope"]
        if values["flavor"] == "pingone":
            url = f"https://auth.pingone.{values['region']}/{values['env_id']}/as/token"
        else:
            url = f"https://{values['host']}/as/token.oauth2"
        return apply_client_auth(url, values, form)

    def jwks_uri(self, values: Mapping[str, str]) -> str | None:
        if values["flavor"] == "pingone":
            return f"https://auth.pingone.{values['region']}/{values['env_id']}/as/jwks"
        return f"https://{values['host']}/pf/JWKS"
