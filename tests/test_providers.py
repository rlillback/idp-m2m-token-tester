from urllib.parse import parse_qs

import pytest
import responses

from idp_m2m_token_tester.errors import TokenRequestError
from idp_m2m_token_tester.providers import PROVIDERS, get_provider

OK = {"access_token": "tok", "token_type": "Bearer", "expires_in": 3600}


def body(call):
    return {k: v[0] for k, v in parse_qs(call.request.body).items()}


@responses.activate
def test_auth0_json_body():
    responses.post("https://t.auth0.com/oauth/token", json=OK)
    r = get_provider("auth0")().fetch_token(
        {"domain": "t.auth0.com", "client_id": "i", "client_secret": "s", "audience": "aud"}
    )
    assert r.access_token == "tok" and r.expires_in == 3600
    assert responses.calls[0].request.body == (
        b'{"grant_type": "client_credentials", "client_id": "i", '
        b'"client_secret": "s", "audience": "aud"}'
    )


@responses.activate
def test_entra_default_scope():
    responses.post("https://login.microsoftonline.com/ten/oauth2/v2.0/token", json=OK)
    get_provider("entra")().fetch_token(
        {"tenant_id": "ten", "client_id": "cid", "client_secret": "s"}
    )
    assert body(responses.calls[0])["scope"] == "api://cid/.default"


@responses.activate
def test_keycloak_discovery_fallback():
    base = "https://kc/realms/r/.well-known/"
    responses.get(base + "oauth-authorization-server", status=404)
    responses.get(base + "openid-configuration", json={"token_endpoint": "https://kc/tok"})
    responses.post("https://kc/tok", json=OK)
    get_provider("keycloak")().fetch_token(
        {"base_url": "https://kc/", "realm": "r", "client_id": "i", "client_secret": "s"}
    )
    assert body(responses.calls[-1])["grant_type"] == "client_credentials"


@responses.activate
def test_okta_basic_auth_and_org_server():
    responses.post("https://o.okta.com/oauth2/v1/token", json=OK)
    get_provider("okta")().fetch_token(
        {
            "domain": "o.okta.com",
            "client_id": "i",
            "client_secret": "s",
            "scope": "x",
            "auth_server": "org",
            "auth_method": "client_secret_basic",
        }
    )
    req = responses.calls[0].request
    assert req.headers["Authorization"].startswith("Basic ")
    assert "client_secret" not in body(responses.calls[0])


@responses.activate
def test_ping_flavors():
    responses.post("https://auth.pingone.eu/env/as/token", json=OK)
    responses.post("https://pf:9031/as/token.oauth2", json=OK)
    p = get_provider("ping")()
    common = {"client_id": "i", "client_secret": "s"}
    p.fetch_token({**common, "flavor": "pingone", "env_id": "env", "region": "eu"})
    p.fetch_token({**common, "flavor": "pingfederate", "host": "pf:9031"})
    assert body(responses.calls[1])["client_id"] == "i"


@responses.activate
def test_error_response():
    responses.post(
        "https://t.auth0.com/oauth/token",
        status=401,
        json={"error": "access_denied", "error_description": "bad"},
    )
    with pytest.raises(TokenRequestError, match="access_denied: bad"):
        get_provider("auth0")().fetch_token(
            {"domain": "t.auth0.com", "client_id": "i", "client_secret": "s", "audience": "a"}
        )


def test_registry_has_all_five():
    assert set(PROVIDERS) == {"auth0", "entra", "keycloak", "okta", "ping"}


def test_connection_info_auth0_masks_secret():
    info = get_provider("auth0")().connection_info(
        {"domain": "t.auth0.com", "client_id": "i", "client_secret": "s3cr3t", "audience": "aud"},
        issuer="https://t.auth0.com/",
    )
    assert info["Discovery URL"] == "https://t.auth0.com/.well-known/openid-configuration"
    assert info["Issuer"] == "https://t.auth0.com/"
    assert info["Token endpoint"] == "https://t.auth0.com/oauth/token"
    assert info["JWKS URI"] == "https://t.auth0.com/.well-known/jwks.json"
    assert info["Client auth"] == "client_secret_post (JSON body)"
    assert info["Audience"] == "aud" and "Scope" not in info
    assert "s3cr3t" not in str(info)


def test_connection_info_entra_default_scope():
    info = get_provider("entra")().connection_info(
        {"tenant_id": "ten", "client_id": "cid", "client_secret": "s"}
    )
    assert info["Scope"] == "api://cid/.default"
    assert info["Discovery URL"] == (
        "https://login.microsoftonline.com/ten/v2.0/.well-known/openid-configuration"
    )


def test_connection_info_okta_servers_and_basic_auth():
    p = get_provider("okta")()
    common = {"domain": "o.okta.com", "client_id": "i", "client_secret": "s", "scope": "x"}
    org = p.connection_info({**common, "auth_server": "org", "auth_method": "client_secret_basic"})
    assert org["Discovery URL"] == "https://o.okta.com/.well-known/oauth-authorization-server"
    assert org["Token endpoint"] == "https://o.okta.com/oauth2/v1/token"
    assert org["Client auth"] == "client_secret_basic"
    custom = p.connection_info({**common, "auth_server": "default"})
    assert custom["Discovery URL"] == (
        "https://o.okta.com/oauth2/default/.well-known/oauth-authorization-server"
    )
    assert custom["JWKS URI"] == "https://o.okta.com/oauth2/default/v1/keys"


def test_connection_info_ping_flavors():
    p = get_provider("ping")()
    common = {"client_id": "i", "client_secret": "s"}
    one = p.connection_info({**common, "flavor": "pingone", "env_id": "env", "region": "eu"})
    assert one["Discovery URL"] == (
        "https://auth.pingone.eu/env/as/.well-known/openid-configuration"
    )
    assert one["JWKS URI"] == "https://auth.pingone.eu/env/as/jwks"
    pf = p.connection_info({**common, "flavor": "pingfederate", "host": "pf:9031"})
    assert pf["Token endpoint"] == "https://pf:9031/as/token.oauth2"
    assert pf["Discovery URL"] == "https://pf:9031/.well-known/openid-configuration"


@responses.activate
def test_connection_info_keycloak_discovers_once():
    base = "https://kc/realms/r/.well-known/"
    responses.get(base + "oauth-authorization-server", status=404)
    meta = responses.get(
        base + "openid-configuration",
        json={"token_endpoint": "https://kc/tok", "jwks_uri": "https://kc/certs"},
    )
    responses.post("https://kc/tok", json=OK)
    p = get_provider("keycloak")()
    values = {"base_url": "https://kc/", "realm": "r", "client_id": "i", "client_secret": "s"}
    p.fetch_token(values)
    info = p.connection_info(values)
    assert info["Discovery URL"] == base + "openid-configuration"
    assert info["Token endpoint"] == "https://kc/tok"
    assert info["JWKS URI"] == "https://kc/certs"
    assert meta.call_count == 1
