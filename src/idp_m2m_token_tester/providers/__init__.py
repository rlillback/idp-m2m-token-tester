from __future__ import annotations

from ..errors import ConfigError
from .auth0 import Auth0Provider
from .base import IdpProvider
from .entra import EntraProvider
from .keycloak import KeycloakProvider
from .okta import OktaProvider
from .ping import PingProvider

PROVIDERS: dict[str, type[IdpProvider]] = {
    p.name: p for p in (Auth0Provider, EntraProvider, KeycloakProvider, OktaProvider, PingProvider)
}


def get_provider(name: str) -> type[IdpProvider]:
    try:
        return PROVIDERS[name]
    except KeyError:
        raise ConfigError(f"Unknown IdP '{name}'. Choose from: {', '.join(PROVIDERS)}.") from None


__all__ = ["PROVIDERS", "IdpProvider", "get_provider"]
