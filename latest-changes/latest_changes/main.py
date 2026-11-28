import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from github import Github
from github.Auth import Token
from github.PullRequest import PullRequest
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, SecretStr, field_validator
from pydantic_settings import BaseSettings

COMMIT_MESSAGE = """
📝 Update release notes

[skip ci]
""".strip()

REPOSITORY_RE = re.compile(r"^[^/]+/[^/]+$")


class LatestChangesError(RuntimeError):
    """Base error for latest-changes failures."""


class MissingHeaderError(LatestChangesError):
    """The latest changes header was not found in the target file."""


class AlreadyAddedError(LatestChangesError):
    """The rendered message is already present in the target file."""


class ConfigurationError(LatestChangesError):
    """Required configuration or input is missing or invalid."""


class Section(BaseModel):
    label: str
    header: str


class Settings(BaseSettings):
    github_repository: str
    github_event_path: Path
    github_event_name: str | None = None
    input_token: SecretStr
    input_latest_changes_file: Path = Path("README.md")
    input_latest_changes_header: str = "### Latest Changes"
    input_template_file: Path = Path(__file__).parent / "latest-changes.jinja2"
    input_end_regex: str = "(^### .*)|(^## .*)"
    input_debug_logs: bool | None = False
    input_labels: list[Section] = [
        Section(label="breaking", header="Breaking Changes"),
        Section(label="security", header="Security Fixes"),
        Section(label="feature", header="Features"),
        Section(label="bug", header="Fixes"),
        Section(label="refactor", header="Refactors"),
        Section(label="upgrade", header="Upgrades"),
        Section(label="docs", header="Docs"),
        Section(label="lang-all", header="Translations"),
        Section(label="infra", header="Infrastructure"),
        Section(label="internal", header="Internal"),
    ]
    input_label_header_prefix: str = "#### "

    @field_validator("github_repository")
    @classmethod
    def validate_repository(cls, value: str) -> str:
        if not REPOSITORY_RE.fullmatch(value):
            raise ValueError("github_repository must be in the form 'owner/repo'")
        return value

    @field_validator("input_latest_changes_header")
    @classmethod
    def validate_header(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("input_latest_changes_header must not be empty")
        return value


class PartialGitHubEventInputs(BaseModel):
    number: int


class PartialGitHubEvent(BaseModel):
    number: int | None = None
    inputs: PartialGitHubEventInputs | None = None


class TemplateDataUser(BaseModel):
    login: str
    html_url: str


class TemplateDataPR(BaseModel):
    number: int
    title: str
    html_url: str
    user: TemplateDataUser


class SectionContent(BaseModel):
    label: str
    header: str
    content: str
    index: int


logging.basicConfig(level=logging.INFO)


def render_message(*, settings: Settings, pr: PullRequest | TemplateDataPR) -> str:
    """Render the Jinja2 template for a pull request into a release-note line."""
    template_content = settings.input_template_file.read_text("utf-8")
    env = Environment(
        loader=FileSystemLoader(searchpath=str(settings.input_template_file.parent)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.from_string(template_content)
    return template.render(pr=pr)


def validate_settings(settings: Settings) -> None:
    """Fail fast on missing or invalid inputs before touching git or the API."""
    if not settings.input_token.get_secret_value():
        raise ConfigurationError("input_token must not be empty")
    if not settings.input_template_file.is_file():
        raise ConfigurationError(
            f"The template file doesn't seem to exist: {settings.input_template_file}"
        )
    try:
        re.compile(settings.input_end_regex)
    except re.error as error:
        raise ConfigurationError(
            f"input_end_regex is not a valid regular expression: {settings.input_end_regex}"
        ) from error
    try:
        re.compile(settings.input_latest_changes_header)
    except re.error as error:
        raise ConfigurationError(
            "input_latest_changes_header is not a valid regular expression: "
            f"{settings.input_latest_changes_header}"
        ) from error


def generate_content(
    *,
    content: str,
    settings: Settings,
    pr: PullRequest | TemplateDataPR,
    labels: list[str],
) -> str:
    """
    Generates updated release notes by inserting a rendered pull request message.

    This function takes the current release notes and updates them by rendering a
    message from a Jinja2 template using the pull request data. It first locates a
    header in the release notes based on a regex from the settings, then renders the
    template from a template file. The function checks that the message has not been
    previously added, extracts release note sections according to configured labels,
    and inserts the new message into the appropriate section or into the sectionless
    content. Finally, it reassembles and returns the updated release notes content.

    Args:
        content: The current release notes content.
        settings: A Settings instance containing configuration parameters such as file
            paths, header regex patterns, and label definitions.
        pr: A pull request object or TemplateDataPR providing data for template rendering.
        labels: A list of label identifiers indicating which sections should be updated.

    Returns:
        The updated release notes content as a string.
    """
    header_match = re.search(settings.input_latest_changes_header, content, flags=re.MULTILINE)
    if not header_match:
        raise MissingHeaderError(
            f"The latest changes file at: {settings.input_latest_changes_file} doesn't seem to contain the header RegEx: {settings.input_latest_changes_header}"
        )
    message = render_message(settings=settings, pr=pr)
    if message in content:
        raise AlreadyAddedError(
            f"It seems these PR's latest changes were already added: {pr.number}"
        )
    pre_header_content = content[: header_match.end()].strip()
    post_header_content = content[header_match.end() :].strip()
    next_release_match = re.search(
        settings.input_end_regex, post_header_content, flags=re.MULTILINE
    )
    release_end = (
        len(content) if not next_release_match else header_match.end() + next_release_match.start()
    )
    release_content = content[header_match.end() : release_end].strip()
    post_release_content = content[release_end:].strip()
    sections: list[SectionContent] = []
    sectionless_content = ""
    for label in settings.input_labels:
        label_match = re.search(
            f"^{settings.input_label_header_prefix}{label.header}",
            release_content,
            flags=re.MULTILINE,
        )
        if not label_match:
            continue
        next_label_match = re.search(
            f"^{settings.input_label_header_prefix}",
            release_content[label_match.end() :],
            flags=re.MULTILINE,
        )
        label_section_end = (
            len(release_content)
            if not next_label_match
            else label_match.end() + next_label_match.start()
        )
        label_content = release_content[label_match.end() : label_section_end].strip()
        section = SectionContent(
            label=label.label,
            header=label.header,
            content=label_content,
            index=label_match.start(),
        )
        sections.append(section)
    sections.sort(key=lambda x: x.index)
    sections_keys = {section.label: section for section in sections}
    if not sections:
        sectionless_content = release_content
    elif sections[0].index > 0:
        sectionless_content = release_content[: sections[0].index].strip()
    new_sections: list[SectionContent] = []
    found = False
    for label in settings.input_labels:
        if label.label in sections_keys:
            section = sections_keys[label.label]
        else:
            section = SectionContent(
                label=label.label,
                header=label.header,
                content="",
                index=-1,
            )
            sections_keys[label.label] = section
        if label.label in labels and not found:
            found = True
            section.content = f"{message}\n{section.content}".strip()
        new_sections.append(section)
    if not found:
        if sectionless_content:
            sectionless_content = f"{message}\n{sectionless_content}"
        else:
            sectionless_content = f"{message}"
    new_release_content = ""
    if sectionless_content:
        new_release_content = f"{sectionless_content}"
    use_sections = [
        f"{settings.input_label_header_prefix}{section.header}\n\n{section.content}"
        for section in new_sections
        if section.content
    ]
    updated_content = "\n\n".join(use_sections)
    if new_release_content:
        if updated_content:
            new_release_content += f"\n\n{updated_content}"
    else:
        new_release_content = updated_content

    new_content = (
        f"{pre_header_content}\n\n{new_release_content}\n\n{post_release_content}".strip() + "\n"
    )
    return new_content


def write_outputs(
    *,
    message: str,
    pr: PullRequest | TemplateDataPR,
    labels: list[str],
) -> None:
    """Publish the rendered change as GitHub Actions outputs when available."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    changes = {
        "number": pr.number,
        "title": pr.title,
        "url": pr.html_url,
        "labels": labels,
        "message": message,
    }
    with open(output_path, "a", encoding="utf-8") as output_file:
        output_file.write(f"message<<EOF\n{message}\nEOF\n")
        output_file.write(f"changes_json={json.dumps(changes)}\n")


def main() -> None:
    git_bin = shutil.which("git")
    if not git_bin:
        logging.error("git executable not found")
        sys.exit(1)
    # Ref: https://github.com/actions/runner/issues/2033
    logging.info(
        "GitHub Actions workaround for git in containers, ref: https://github.com/actions/runner/issues/2033"
    )
    safe_directory_config_content = "[safe]\n\tdirectory = /github/workspace"
    dotgitconfig_path = Path.home() / ".gitconfig"
    dotgitconfig_path.write_text(safe_directory_config_content)

    settings = Settings()  # type: ignore[call-arg]
    try:
        validate_settings(settings)
    except ConfigurationError as error:
        logging.error(str(error))
        sys.exit(1)
    if settings.input_debug_logs:
        logging.info(f"Using config: {settings.model_dump_json()}")
    g = Github(auth=Token(settings.input_token.get_secret_value()))
    repo = g.get_repo(settings.github_repository)
    if not settings.github_event_path.is_file():
        logging.error(f"No event file was found at: {settings.github_event_path}")
        sys.exit(1)
    contents = settings.github_event_path.read_text()
    event = PartialGitHubEvent.model_validate_json(contents)
    if event.number is not None:
        number = event.number
    elif event.inputs and event.inputs.number:
        number = event.inputs.number
    else:
        logging.error(
            f"No PR number was found (PR number or workflow input) in the event file at: {settings.github_event_path}"
        )
        sys.exit(1)

    pr = repo.get_pull(number)
    if not pr.merged:
        logging.info("The PR was not merged, nothing else to do.")
        sys.exit(0)
    if not settings.input_latest_changes_file.is_file():
        logging.error(
            f"The latest changes files doesn't seem to exist: {settings.input_latest_changes_file}"
        )
        sys.exit(1)

    labels = [label.name for label in pr.labels]
    message = render_message(settings=settings, pr=pr)
    write_outputs(message=message, pr=pr, labels=labels)

    logging.info("Setting up GitHub Actions git user")
    subprocess.run([git_bin, "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(
        [git_bin, "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
        check=True,
    )
    number_of_trials = 10
    logging.info(f"Number of trials (for race conditions): {number_of_trials}")
    for trial in range(number_of_trials):
        logging.info(f"Running trial: {trial}")
        logging.info("Pulling the latest changes, including the latest merged PR (this one)")
        subprocess.run([git_bin, "pull"], check=True)
        content = settings.input_latest_changes_file.read_text()

        try:
            new_content = generate_content(
                content=content,
                settings=settings,
                pr=pr,
                labels=labels,
            )
        except AlreadyAddedError:
            logging.info("The latest changes were already added, nothing else to do.")
            sys.exit(0)
        except MissingHeaderError as error:
            logging.error(str(error))
            sys.exit(1)
        settings.input_latest_changes_file.write_text(new_content)
        logging.info(f"Committing changes to: {settings.input_latest_changes_file}")
        subprocess.run([git_bin, "add", str(settings.input_latest_changes_file)], check=True)
        subprocess.run([git_bin, "commit", "-m", COMMIT_MESSAGE], check=True)
        logging.info(f"Pushing changes: {settings.input_latest_changes_file}")

        result = subprocess.run([git_bin, "push"])
        if result.returncode == 0:
            break
        # Didn't work, race condition, reset to try again
        logging.info("That didn't work, resetting before trying again")
        subprocess.run([git_bin, "reset", "HEAD^1"], check=True)
        subprocess.run([git_bin, "checkout", "."], check=True)

    logging.info("Finished")
