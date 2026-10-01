from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .config import resolve_settings
from .display import render
from .envfile import merged_environment
from .errors import ConfigError, TokenTesterError
from .jwt_decoder import decode_token
from .providers import PROVIDERS, IdpProvider, get_provider


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="idp-m2m",
        description="Get an OAuth2 client_credentials token from an IdP and decode it. "
        "Settings come from environment variables or a .env file, otherwise you are prompted. "
        "Nothing is stored.",
    )
    p.add_argument("--idp", choices=sorted(PROVIDERS), help="IdP to use (menu if omitted)")
    p.add_argument(
        "--env-file",
        type=Path,
        help="load settings from this .env file (default: ./.env if present). "
        "Real environment variables override it.",
    )
    p.add_argument("--verify", action="store_true", help="verify the JWT signature via JWKS")
    p.add_argument("-v", "--verbose", action="store_true", help="debug logging (no secrets)")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def choose_idp() -> str:
    names = list(PROVIDERS)
    print("Select an IdP:", file=sys.stderr)
    for i, n in enumerate(names, 1):
        print(f"  {i}) {PROVIDERS[n].display_name}", file=sys.stderr)
    choice = input("Number: ").strip()
    if not choice.isdigit() or not 1 <= int(choice) <= len(names):
        raise ConfigError("Invalid selection.")
    return names[int(choice) - 1]


def run(idp: str, verify: bool, env_file: Path | None = None) -> None:
    provider: IdpProvider = get_provider(idp)()
    values = resolve_settings(provider.settings(), merged_environment(env_file))
    response = provider.fetch_token(values)
    jwks = provider.jwks_uri(values) if verify else None
    decoded = decode_token(response.access_token, jwks_uri=jwks)
    render(response, decoded, sys.stdout)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)
    try:
        run(args.idp or choose_idp(), args.verify, args.env_file)
    except TokenTesterError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.", file=sys.stderr)
        return 130
    return 0
