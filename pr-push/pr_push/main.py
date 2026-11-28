from pathlib import Path

import httpx

from actions_shared.app import create_app, get_github_client, make_get_claims
from actions_shared.config import Settings, get_settings
from actions_shared.models import TokenResponse
from pr_push.github import create_token
from pr_push.models import OIDCClaims

__all__ = [
    "app",
    "get_claims",
    "get_github_client",
    "get_settings",
]

app_version = (Path(__file__).parent.parent / "version.txt").read_text(encoding="utf-8").strip()

get_claims = make_get_claims(OIDCClaims)


def _create_token(
    claims: OIDCClaims,
    settings: Settings,
    client: httpx.Client,
) -> TokenResponse:
    return create_token(claims, settings, client)


app = create_app("PR Push", app_version, get_claims, _create_token)
