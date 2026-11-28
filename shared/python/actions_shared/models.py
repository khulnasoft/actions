import base64
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Repository(BaseModel):
    default_branch: str


class Installation(BaseModel):
    id: int
    app_slug: str | None = None


class TokenRepository(BaseModel):
    id: int


class InstallationToken(BaseModel):
    token: str
    expires_at: datetime
    permissions: dict[str, str]
    repository_selection: str
    repositories: list[TokenRepository]


class RepositoryFile(BaseModel):
    type: Literal["file"]
    sha: str
    encoding: Literal["base64"]
    content: str

    def decoded_content(self) -> bytes:
        return base64.b64decode(self.content)


class WorkflowConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflows: list[str] = Field(min_length=1)


class GitHubUser(BaseModel):
    id: int


class CollaboratorPermission(BaseModel):
    permission: Literal["admin", "write", "read", "none"]
    user: GitHubUser


class PullRequestRepository(BaseModel):
    id: int


class PullRequestHead(BaseModel):
    sha: str
    repo: PullRequestRepository


class PullRequestBase(BaseModel):
    sha: str


class PullRequest(BaseModel):
    number: int
    state: Literal["open", "closed"]
    head: PullRequestHead
    base: PullRequestBase


class OIDCTokenResponse(BaseModel):
    value: str


class TokenResponse(BaseModel):
    token: str
    expires_at: datetime
    repository: str
    permissions: dict[str, str]
