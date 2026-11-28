import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

import httpx
import jwt
from pydantic import ValidationError

from actions_shared.config import Settings
from actions_shared.models import (
    Installation,
    InstallationToken,
    RepositoryFile,
)

GITHUB_API_URL = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"

logger = logging.getLogger(__name__)


class GitHubAPIError(RuntimeError):
    pass


class WorkflowNotAllowedError(ValueError):
    pass


def github_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def create_app_jwt(settings: Settings) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "iat": now - timedelta(seconds=60),
            "exp": now + timedelta(minutes=9),
            "iss": settings.github_client_id,
        },
        settings.github_app_private_key.get_secret_value(),
        algorithm="RS256",
    )


def github_request(
    client: httpx.Client,
    method: str,
    url: str,
    token: str,
    params: dict[str, str | int] | None = None,
    json: dict[str, object] | None = None,
) -> httpx.Response:
    request_arguments: dict[str, Any] = {
        "headers": github_headers(token),
        "params": params,
    }
    if json is not None:
        request_arguments["json"] = json
    try:
        response = client.request(method, url, **request_arguments)
        response.raise_for_status()
        return response
    except httpx.HTTPError as error:
        status_code = (
            error.response.status_code if isinstance(error, httpx.HTTPStatusError) else None
        )
        logger.error(
            "GitHub API request failed: method=%s url=%s status_code=%s error=%s",
            method,
            url,
            status_code,
            type(error).__name__,
        )
        raise GitHubAPIError("GitHub rejected the token request") from error


def get_repository_file(
    repository: str,
    path: str,
    ref: str,
    token: str,
    client: httpx.Client,
) -> RepositoryFile:
    response = github_request(
        client,
        "GET",
        f"/repos/{repository}/contents/{quote(path, safe='/')}",
        token,
        params={"ref": ref},
    )
    try:
        return RepositoryFile.model_validate_json(response.content)
    except ValidationError as error:
        raise GitHubAPIError("GitHub rejected the token request") from error


def get_installation(
    repository: str,
    app_token: str,
    client: httpx.Client,
) -> Installation:
    installation_response = github_request(
        client,
        "GET",
        f"/repos/{repository}/installation",
        app_token,
    )
    try:
        return Installation.model_validate_json(installation_response.content)
    except ValidationError as error:
        raise GitHubAPIError("GitHub rejected the token request") from error


def issue_installation_token(
    repository_id: int,
    installation_id: int,
    permissions: dict[str, str],
    app_token: str,
    client: httpx.Client,
) -> InstallationToken:
    token_response = github_request(
        client,
        "POST",
        f"/app/installations/{installation_id}/access_tokens",
        app_token,
        json={
            "repository_ids": [repository_id],
            "permissions": permissions,
        },
    )
    try:
        return InstallationToken.model_validate_json(token_response.content)
    except ValidationError as error:
        raise GitHubAPIError("GitHub rejected the token request") from error
