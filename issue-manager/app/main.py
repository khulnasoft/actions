import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from github import Github
from github.Auth import Token
from github.Issue import Issue
from github.IssueEvent import IssueEvent
from pydantic import BaseModel, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class KeywordMeta(BaseModel):
    delay: timedelta = timedelta(days=10)
    message: str = "Assuming the original need was handled, this will be automatically closed now."
    remove_label_on_comment: bool = True
    remove_label_on_close: bool = False


def discard_schema(v: object) -> object:
    """Remove the $schema key from a config dict."""
    if isinstance(v, dict) and "$schema" in v:
        del v["$schema"]
    return v


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_ignore_empty=True)

    input_config: dict[str, KeywordMeta]
    github_repository: str
    input_token: SecretStr
    github_event_path: Path
    github_event_name: str | None = None

    @field_validator("input_config", mode="before")
    @classmethod
    def _discard_schema(cls, v: object) -> object:
        return discard_schema(v)


class PartialGitHubEventIssue(BaseModel):
    number: int


class PartialGitHubEvent(BaseModel):
    issue: PartialGitHubEventIssue | None = None
    pull_request: PartialGitHubEventIssue | None = None


def get_last_interaction_date(issue: Issue) -> datetime | None:
    last_date: datetime | None = None
    comments: list = list(issue.get_comments())
    interaction_dates: list[datetime] = []
    if issue.pull_request:
        pr = issue.as_pull_request()
        commits = list(pr.get_commits())
        reviews = list(pr.get_reviews())
        pr_comments = list(pr.get_comments())
        interactions = list(comments) + list(pr_comments)
        interaction_dates = [interaction.created_at for interaction in interactions]
        interaction_dates.extend(
            commit.commit.author.date
            for commit in commits
            if commit.commit.author and commit.commit.author.date
        )
        interaction_dates.extend(
            review.submitted_at for review in reviews if review.submitted_at is not None
        )
    else:
        interactions = comments
        interaction_dates = [interaction.created_at for interaction in interactions]
    for item_date in interaction_dates:
        if not last_date or item_date > last_date:
            last_date = item_date
    return last_date


def get_labeled_events(events: list[IssueEvent]) -> list[IssueEvent]:
    labeled_events = []
    for event in events:
        if event.event == "labeled":
            labeled_events.append(event)
    return labeled_events


def get_last_event_for_label(*, labeled_events: list[IssueEvent], label: str) -> IssueEvent | None:
    last_event: IssueEvent | None = None
    for event in labeled_events:
        if event.label and event.label.name == label:
            if not last_event:
                last_event = event
                continue
            if event.created_at > last_event.created_at:
                last_event = event
    return last_event


def close_issue(
    *, issue: Issue, keyword_meta: KeywordMeta, keyword: str, label_strs: set[str]
) -> None:
    logging.info(f"Closing issue: #{issue.number} with message: {keyword_meta.message}")
    issue.create_comment(keyword_meta.message)
    issue.edit(state="closed")
    if keyword_meta.remove_label_on_close and keyword in label_strs:
        issue.remove_from_labels(keyword)


def process_issue(*, issue: Issue, settings: Settings) -> None:
    logging.info(f"Processing issue: #{issue.number}")
    label_strs = set([label.name for label in issue.get_labels()])
    events = list(issue.get_events())
    labeled_events = get_labeled_events(events)
    last_date = get_last_interaction_date(issue)
    now = datetime.now(UTC)
    for keyword, keyword_meta in settings.input_config.items():
        # Check closable delay, if enough time passed and the issue could be closed
        closable_delay = last_date is None or (now - keyword_meta.delay) > last_date
        # Check label, optionally removing it if there's a comment after adding it
        if keyword in label_strs:
            logging.info(f'Keyword: "{keyword}" in issue labels')
            keyword_event = get_last_event_for_label(labeled_events=labeled_events, label=keyword)
            if last_date and keyword_event and last_date > keyword_event.created_at:
                logging.info(
                    f"Not closing as the last comment was written after adding the "
                    f'label: "{keyword}"'
                )
                if keyword_meta.remove_label_on_comment:
                    logging.info(f'Removing label: "{keyword}"')
                    issue.remove_from_labels(keyword)
            elif closable_delay:
                close_issue(
                    issue=issue,
                    keyword_meta=keyword_meta,
                    keyword=keyword,
                    label_strs=label_strs,
                )
                break
            else:
                logging.info(
                    f"Not closing issue: #{issue.number} as the delay hasn't been reached: {keyword_meta.delay}"
                )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = Settings()  # type: ignore[call-arg]
    logging.info(f"Using config: {settings.model_dump_json()}")
    g = Github(auth=Token(settings.input_token.get_secret_value()))
    repo = g.get_repo(settings.github_repository)
    github_event: PartialGitHubEvent | None = None
    if settings.github_event_path.is_file():
        contents = settings.github_event_path.read_text()
        github_event = PartialGitHubEvent.model_validate_json(contents)
    if (
        settings.github_event_name == "issues"
        or settings.github_event_name == "pull_request_target"
        or settings.github_event_name == "issue_comment"
    ):
        if github_event:
            issue_number: int | None = None
            if github_event.issue:
                issue_number = github_event.issue.number
            elif github_event.pull_request:
                issue_number = github_event.pull_request.number
            if issue_number is not None:
                issue = repo.get_issue(issue_number)
                if issue.state == "open":
                    process_issue(issue=issue, settings=settings)
    else:
        for keyword, _keyword_meta in settings.input_config.items():
            for issue in repo.get_issues(state="open", labels=[keyword]):
                process_issue(issue=issue, settings=settings)
    logging.info("Finished")


if __name__ == "__main__":
    main()
