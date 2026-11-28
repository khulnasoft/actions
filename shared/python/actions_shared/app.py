import logging
from collections.abc import Callable, Iterator
from typing import Annotated, Any

import httpx
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from actions_shared.config import Settings, get_settings
from actions_shared.github import (
    GITHUB_API_URL,
    GitHubAPIError,
    WorkflowNotAllowedError,
)
from actions_shared.models import TokenResponse
from actions_shared.security import (
    InvalidIdentityError,
    get_jwks_client,
    verify_oidc_token,
)

logger = logging.getLogger(__name__)

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_github_client() -> Iterator[httpx.Client]:
    with httpx.Client(base_url=GITHUB_API_URL, timeout=10) as client:
        yield client


GitHubClientDep = Annotated[
    httpx.Client,
    Depends(get_github_client, scope="function"),
]


def make_get_claims(
    claims_model: type[Any],
) -> Callable[..., Any]:
    def get_claims(
        settings: SettingsDep,
        jwks_client: Annotated[Any, Depends(get_jwks_client)],
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Depends(HTTPBearer(auto_error=False)),
        ],
    ) -> Any:
        if credentials is None:
            logger.warning("Token request rejected: OIDC bearer token is missing")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="A GitHub Actions OIDC bearer token is required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            return verify_oidc_token(credentials.credentials, settings, jwks_client, claims_model)
        except InvalidIdentityError as error:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(error),
            ) from error

    return get_claims


def create_app(
    title: str,
    version: str,
    get_claims: Callable[..., Any],
    create_token: Callable[[Any, Settings, httpx.Client], TokenResponse],
) -> FastAPI:
    app = FastAPI(title=title, version=version)

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {"name": app.title, "version": app.version}

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/token")
    def token(
        claims: Annotated[Any, Depends(get_claims)],
        settings: SettingsDep,
        github_client: GitHubClientDep,
        response: Response,
    ) -> TokenResponse:
        try:
            token_response = create_token(claims, settings, github_client)
        except WorkflowNotAllowedError as error:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The GitHub Actions workflow is not allowed",
            ) from error
        except GitHubAPIError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(error),
            ) from error
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        return token_response

    return app
