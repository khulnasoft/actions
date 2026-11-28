import jwt

from actions_shared.config import Settings
from actions_shared.security import (
    GITHUB_ACTIONS_ISSUER,
    GITHUB_ACTIONS_JWKS_URL,
    InvalidIdentityError,
    get_jwks_client,
)
from actions_shared.security import verify_oidc_token as _verify_oidc_token
from pr_push.models import OIDCClaims

__all__ = [
    "GITHUB_ACTIONS_ISSUER",
    "GITHUB_ACTIONS_JWKS_URL",
    "InvalidIdentityError",
    "get_jwks_client",
    "verify_oidc_token",
]


def verify_oidc_token(
    token: str,
    settings: Settings,
    jwks_client: jwt.PyJWKClient,
) -> OIDCClaims:
    return _verify_oidc_token(token, settings, jwks_client, OIDCClaims)
