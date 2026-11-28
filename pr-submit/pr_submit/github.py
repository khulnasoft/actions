import logging
from urllib.parse import quote

import httpx
import yaml
from pydantic import ValidationError

from actions_shared.config import Settings
from actions_shared.github import (
    GITHUB_API_URL,
    GitHubAPIError,
    WorkflowNotAllowedError,
    create_app_jwt,
    get_installation,
    get_repository_file,
    github_request,
    issue_installation_token,
)
from actions_shared.models import (
    CollaboratorPermission,
    InstallationToken,
    Repository,
    TokenResponse,
)
from pr_submit.models import CONFIG_PATH, OIDCClaims, WorkflowConfig

TOKEN_PERMISSIONS = {
    "contents": "write",
    "pull_requests": "write",
}
EXPECTED_TOKEN_PERMISSIONS = {**TOKEN_PERMISSIONS, "metadata": "read"}

logger = logging.getLogger(__name__)

__all__ = [
    "GITHUB_API_URL",
    "GitHubAPIError",
    "WorkflowNotAllowedError",
    "create_token",
]


def _validate_token_scope(claims: OIDCClaims, token: InstallationToken) -> None:
    if (
        token.permissions != EXPECTED_TOKEN_PERMISSIONS
        or token.repository_selection != "selected"
        or [repository.id for repository in token.repositories] != [claims.repository_id]
    ):
        logger.error(
            "Installation token has unexpected scope: repository=%s "
            "repository_id=%s permissions=%s repository_selection=%s "
            "repository_ids=%s",
            claims.repository,
            claims.repository_id,
            token.permissions,
            token.repository_selection,
            [repository.id for repository in token.repositories],
        )
        raise GitHubAPIError("GitHub rejected the token request")


def authorize_workflow(
    claims: OIDCClaims,
    token: str,
    client: httpx.Client,
) -> None:
    try:
        repository_response = github_request(client, "GET", f"/repos/{claims.repository}", token)
        repository = Repository.model_validate_json(repository_response.content)

        config_file = get_repository_file(
            claims.repository,
            CONFIG_PATH,
            repository.default_branch,
            token,
            client,
        )
        config = WorkflowConfig.model_validate(yaml.safe_load(config_file.decoded_content()))
        if claims.workflow_path not in config.workflows:
            raise WorkflowNotAllowedError("workflow is not listed in the configuration")

        if claims.ref != f"refs/heads/{repository.default_branch}":
            raise WorkflowNotAllowedError("workflow is not running from the default branch")

        if claims.event_name == "workflow_dispatch":
            permission_response = github_request(
                client,
                "GET",
                f"/repos/{claims.repository}/collaborators/{quote(claims.actor, safe='')}/permission",
                token,
            )
            permission = CollaboratorPermission.model_validate_json(permission_response.content)
            if permission.user.id != claims.actor_id:
                raise WorkflowNotAllowedError("actor ID does not match")
            if permission.permission not in {"admin", "write"}:
                raise WorkflowNotAllowedError("actor does not have write permission")

        trusted_workflow = get_repository_file(
            claims.repository,
            claims.workflow_path,
            repository.default_branch,
            token,
            client,
        )
        executed_workflow = get_repository_file(
            claims.repository,
            claims.workflow_path,
            claims.workflow_sha,
            token,
            client,
        )
        if trusted_workflow.sha != executed_workflow.sha:
            raise WorkflowNotAllowedError("workflow differs from the trusted version")
    except WorkflowNotAllowedError as error:
        logger.warning(
            "Workflow authorization rejected: reason=%s repository=%s "
            "repository_id=%s actor=%s actor_id=%s event=%s ref=%s workflow=%s",
            str(error),
            claims.repository,
            claims.repository_id,
            claims.actor,
            claims.actor_id,
            claims.event_name,
            claims.ref,
            claims.workflow_path,
        )
        raise
    except (ValidationError, ValueError, yaml.YAMLError) as error:
        logger.warning(
            "Workflow authorization data is invalid: repository=%s "
            "repository_id=%s actor_id=%s error=%s",
            claims.repository,
            claims.repository_id,
            claims.actor_id,
            type(error).__name__,
        )
        raise WorkflowNotAllowedError("The GitHub Actions workflow is not allowed") from error


def create_token(
    claims: OIDCClaims,
    settings: Settings,
    client: httpx.Client,
) -> TokenResponse:
    app_token = create_app_jwt(settings)
    installation = get_installation(claims.repository, app_token, client)
    installation_token = issue_installation_token(
        claims.repository_id,
        installation.id,
        TOKEN_PERMISSIONS,
        app_token,
        client,
    )
    _validate_token_scope(claims, installation_token)
    authorize_workflow(claims, installation_token.token, client)
    logger.info(
        "Installation token issued: repository=%s repository_id=%s actor=%s "
        "actor_id=%s event=%s ref=%s workflow=%s expires_at=%s",
        claims.repository,
        claims.repository_id,
        claims.actor,
        claims.actor_id,
        claims.event_name,
        claims.ref,
        claims.workflow_path,
        installation_token.expires_at.isoformat(),
    )
    return TokenResponse(
        token=installation_token.token,
        expires_at=installation_token.expires_at,
        repository=claims.repository,
        permissions=installation_token.permissions,
    )
