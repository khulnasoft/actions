import logging
from typing import Any, Literal

from github import Github
from github.Auth import Token
from github.PullRequestReview import PullRequestReview
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings


class LabelSettings(BaseModel):
    await_label: str | None = None
    number: int


default_config = {"approved-2": LabelSettings(await_label="awaiting-review", number=2)}


class Settings(BaseSettings):
    github_repository: str
    input_token: SecretStr
    input_debug: bool | None = False
    input_config: dict[str, LabelSettings] | Literal[""] = default_config


def latest_reviews_by_user(reviews: list[Any]) -> dict[str, Any]:
    """Deduplicate reviews per user, keeping the latest submission."""
    review_by_user: dict[str, PullRequestReview] = {}
    for review in reviews:
        if review.user is None:
            continue
        if review.submitted_at is None:
            continue
        login = review.user.login
        if login in review_by_user:
            stored_review = review_by_user[login]
            if review.submitted_at >= stored_review.submitted_at:
                review_by_user[login] = review
        else:
            review_by_user[login] = review
    return review_by_user


def approved_count(reviews: list[Any]) -> int:
    review_by_user = latest_reviews_by_user(reviews)
    return sum(1 for review in review_by_user.values() if review.state == "APPROVED")


def apply_config(
    pr: Any, config: dict[str, LabelSettings], approved_reviews_count: int
) -> list[str]:
    """Apply label rules to a PR. Returns list of labels applied."""
    applied: list[str] = []
    pr_labels = list(pr.get_labels())
    pr_label_by_name = {label.name: label for label in pr_labels}
    for approved_label, conf in config.items():
        if (
            conf.await_label is None or conf.await_label in pr_label_by_name
        ) and approved_reviews_count >= conf.number:
            pr.add_to_labels(approved_label)
            applied.append(approved_label)
            if conf.await_label:
                pr.remove_from_labels(conf.await_label)
    return applied


def main() -> None:
    settings = Settings()  # type: ignore[call-arg]
    if settings.input_debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.debug(f"Using config: {settings.model_dump_json()}")
    g = Github(auth=Token(settings.input_token.get_secret_value()))
    repo = g.get_repo(settings.github_repository)
    config = settings.input_config or default_config
    for pr in repo.get_pulls(state="open"):
        logging.info(f"Checking PR: #{pr.number}")
        reviews = list(pr.get_reviews())
        count = approved_count(reviews)
        applied = apply_config(pr, config, count)
        logging.debug(f"Applied labels to PR #{pr.number}: {applied}")
    logging.info("Finished")


if __name__ == "__main__":
    main()
