import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from actions_shared.models import (
    CollaboratorPermission,
    GitHubUser,
    Installation,
    InstallationToken,
    OIDCTokenResponse,
    PullRequest,
    PullRequestBase,
    PullRequestHead,
    PullRequestRepository,
    Repository,
    RepositoryFile,
    TokenRepository,
    TokenResponse,
    WorkflowConfig,
)

__all__ = [
    "CONFIG_PATH",
    "CollaboratorPermission",
    "GitHubUser",
    "Installation",
    "InstallationToken",
    "OIDCClaims",
    "OIDCTokenResponse",
    "PullRequest",
    "PullRequestBase",
    "PullRequestHead",
    "PullRequestRepository",
    "Repository",
    "RepositoryFile",
    "TokenRepository",
    "TokenResponse",
    "WorkflowConfig",
]

CONFIG_PATH = ".github/pr-push.yml"


class OIDCClaims(BaseModel):
    repository: str = Field(pattern=r"^[^/]+/[^/]+$")
    repository_id: int
    actor: str
    actor_id: int
    workflow_ref: str
    workflow_sha: str
    event_name: Literal["pull_request", "workflow_dispatch"]
    ref: str
    exp: int
    iat: int
    nbf: int

    @model_validator(mode="after")
    def validate_event_ref(self) -> OIDCClaims:
        if self.event_name == "pull_request":
            if not re.fullmatch(r"refs/pull/[1-9][0-9]*/merge", self.ref):
                raise ValueError("Unexpected pull request ref")
        elif not re.fullmatch(r"refs/heads/.+", self.ref):
            raise ValueError("Unexpected workflow dispatch ref")
        return self

    @property
    def workflow_path(self) -> str:
        prefix = f"{self.repository}/"
        if not self.workflow_ref.startswith(prefix):
            raise ValueError("Unexpected workflow repository")
        path_and_ref = self.workflow_ref.removeprefix(prefix)
        path, separator, _ = path_and_ref.rpartition("@")
        if not separator or not path.startswith(".github/workflows/"):
            raise ValueError("Unexpected workflow path")
        return path

    @property
    def pull_request_number(self) -> int:
        if self.event_name != "pull_request":
            raise ValueError("Identity is not for a pull request")
        return int(self.ref.removeprefix("refs/pull/").removesuffix("/merge"))

    @property
    def branch_name(self) -> str:
        if self.event_name != "workflow_dispatch":
            raise ValueError("Identity is not for a workflow dispatch")
        return self.ref.removeprefix("refs/heads/")
