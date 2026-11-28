import httpx

from actions_shared.action import (
    ActionError,
    ActionSettings,
    get_installation_token,
    get_oidc_token,
)
from actions_shared.action import main as _main
from actions_shared.action import (
    run as _run,
)

DEFAULT_SERVICE_URL = "https://pr-push.khulnasoft.com"
SERVICE_NAME = "PR Push"

__all__ = [
    "DEFAULT_SERVICE_URL",
    "ActionError",
    "ActionSettings",
    "get_installation_token",
    "get_oidc_token",
    "main",
    "run",
]


def run(settings: ActionSettings, client: httpx.Client) -> None:
    _run(settings, client, SERVICE_NAME)


def main() -> None:
    _main(SERVICE_NAME, DEFAULT_SERVICE_URL)
