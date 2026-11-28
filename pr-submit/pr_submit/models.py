from typing import Literal

from pydantic import BaseModel, Field

from actions_shared.models import (
    CollaboratorPermission,
    GitHubUser,
    Installation,
    InstallationToken,
    OIDCTokenResponse,
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
    "Repository",
    "RepositoryFile",
    "TokenRepository",
    "TokenResponse",
    "WorkflowConfig",
]

CONFIG_PATH = ".github/pr-submit.yml"


class OIDCClaims(BaseModel):
    repository: str
    repository_id: int
    actor: str
    actor_id: int
    workflow_ref: str
    workflow_sha: str
    event_name: Literal["schedule", "workflow_dispatch"]
    ref: str = Field(pattern=r"^refs/heads/.+$")
    exp: int
    iat: int
    nbf: int

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
