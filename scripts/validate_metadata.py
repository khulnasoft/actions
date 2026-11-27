#!/usr/bin/env python3
"""Validate action.yml metadata for all actions in the monorepo."""

import sys
from pathlib import Path

import yaml

ACTIONS = ["issue-manager", "label-approved", "latest-changes"]
VALID_RUNS_USING = {"docker", "node12", "node16", "node20", "node24", "composite"}
VALID_BRANDING_ICONS = {
    "activity",
    "airplay",
    "alert-circle",
    "alert-octagon",
    "alert-triangle",
    "align-center",
    "align-justify",
    "align-left",
    "align-right",
    "anchor",
    "aperture",
    "archive",
    "arrow-down",
    "arrow-down-circle",
    "arrow-down-left",
    "arrow-down-right",
    "arrow-left",
    "arrow-left-circle",
    "arrow-right",
    "arrow-right-circle",
    "arrow-up",
    "arrow-up-circle",
    "arrow-up-left",
    "arrow-up-right",
    "at-sign",
    "award",
    "bar-chart",
    "bar-chart-2",
    "battery",
    "battery-charging",
    "bell",
    "bell-off",
    "bluetooth",
    "bold",
    "book",
    "book-open",
    "bookmark",
    "box",
    "briefcase",
    "calendar",
    "camera",
    "check",
    "check-circle",
    "check-square",
    "chevron-down",
    "chevron-left",
    "chevron-right",
    "chevron-up",
    "chevrons-down",
    "chevrons-left",
    "chevrons-right",
    "chevrons-up",
    "circle",
    "clipboard",
    "clock",
    "cloud",
    "cloud-drizzle",
    "cloud-lightning",
    "cloud-off",
    "cloud-rain",
    "cloud-snow",
    "code",
    "codepen",
    "codesandbox",
    "coffee",
    "columns",
    "command",
    "compass",
    "copy",
    "corner-down-left",
    "corner-down-right",
    "corner-left-down",
    "corner-left-up",
    "corner-right-down",
    "corner-right-up",
    "corner-up-left",
    "corner-up-right",
    "cpu",
    "credit-card",
    "crop",
    "crosshair",
    "database",
    "delete",
    "disc",
    "divide",
    "divide-circle",
    "divide-square",
    "dollar-sign",
    "download",
    "dribbble",
    "droplet",
    "edit",
    "edit-2",
    "edit-3",
    "external-link",
    "eye",
    "eye-off",
    "facebook",
    "fast-forward",
    "feather",
    "figma",
    "file",
    "file-minus",
    "file-plus",
    "file-text",
    "film",
    "filter",
    "flag",
    "folder",
    "folder-minus",
    "folder-plus",
    "framer",
    "frown",
    "gift",
    "git-branch",
    "git-commit",
    "git-merge",
    "git-pull-request",
    "github",
    "gitlab",
    "globe",
    "grid",
    "hard-drive",
    "hash",
    "heading",
    "headphones",
    "heart",
    "help-circle",
    "hexagon",
    "home",
    "image",
    "inbox",
    "info",
    "instagram",
    "italic",
    "key",
    "layers",
    "layout",
    "life-buoy",
    "link",
    "link-2",
    "linkedin",
    "list",
    "loader",
    "lock",
    "log-in",
    "log-out",
    "mail",
    "map",
    "map-pin",
    "maximize",
    "maximize-2",
    "meh",
    "menu",
    "message-circle",
    "message-square",
    "mic",
    "mic-off",
    "minimize",
    "minimize-2",
    "minus",
    "minus-circle",
    "minus-square",
    "monitor",
    "moon",
    "more-horizontal",
    "more-vertical",
    "mouse-pointer",
    "move",
    "music",
    "navigation",
    "navigation-2",
    "octagon",
    "package",
    "paperclip",
    "pause",
    "pause-circle",
    "pen-tool",
    "percent",
    "phone",
    "phone-call",
    "phone-forwarded",
    "phone-incoming",
    "phone-missed",
    "phone-off",
    "phone-outgoing",
    "pie-chart",
    "play",
    "play-circle",
    "plus",
    "plus-circle",
    "plus-square",
    "pocket",
    "power",
    "printer",
    "radio",
    "refresh-ccw",
    "refresh-cw",
    "repeat",
    "rewind",
    "rotate-ccw",
    "rotate-cw",
    "rss",
    "save",
    "scissors",
    "search",
    "send",
    "server",
    "settings",
    "share",
    "share-2",
    "shield",
    "shield-off",
    "shopping-bag",
    "shopping-cart",
    "shuffle",
    "sidebar",
    "skip-back",
    "skip-forward",
    "slack",
    "slash",
    "sliders",
    "smartphone",
    "smile",
    "speaker",
    "square",
    "star",
    "stop-circle",
    "sun",
    "sunrise",
    "sunset",
    "tablet",
    "tag",
    "target",
    "terminal",
    "thermometer",
    "thumbs-down",
    "thumbs-up",
    "toggle-left",
    "toggle-right",
    "tool",
    "trash",
    "trash-2",
    "trello",
    "trending-down",
    "trending-up",
    "triangle",
    "truck",
    "tv",
    "twitch",
    "twitter",
    "type",
    "umbrella",
    "underline",
    "unlock",
    "upload",
    "user",
    "user-check",
    "user-minus",
    "user-plus",
    "user-x",
    "users",
    "video",
    "video-off",
    "voicemail",
    "volume",
    "volume-1",
    "volume-2",
    "volume-x",
    "watch",
    "wifi",
    "wifi-off",
    "wind",
    "x",
    "x-circle",
    "x-octagon",
    "x-square",
    "youtube",
    "zap",
    "zap-off",
    "zoom-in",
    "zoom-out",
}
VALID_BRANDING_COLORS = {"white", "yellow", "blue", "green", "orange", "red", "purple", "gray-dark"}


def validate_action(action_dir: Path) -> list[str]:
    errors: list[str] = []
    action_yml = action_dir / "action.yml"
    if not action_yml.exists():
        return [f"{action_dir}: missing action.yml"]

    try:
        meta = yaml.safe_load(action_yml.read_text())
    except yaml.YAMLError as e:
        return [f"{action_dir}/action.yml: invalid YAML: {e}"]

    if not isinstance(meta, dict):
        return [f"{action_dir}/action.yml: top level must be a mapping"]

    for field in ("name", "description", "runs"):
        if field not in meta:
            errors.append(f"{action_dir}/action.yml: missing required field '{field}'")

    runs = meta.get("runs")
    if isinstance(runs, dict):
        using = runs.get("using")
        if using not in VALID_RUNS_USING:
            errors.append(f"{action_dir}/action.yml: runs.using {using!r} is not a valid value")
        if using == "docker" and "image" not in runs:
            errors.append(
                f"{action_dir}/action.yml: runs.using is 'docker' but runs.image is missing"
            )
        if using in {"node12", "node16", "node20", "node24"} and "main" not in runs:
            errors.append(
                f"{action_dir}/action.yml: runs.using is {using!r} but runs.main is missing"
            )

    inputs = meta.get("inputs") or {}
    if not isinstance(inputs, dict):
        errors.append(f"{action_dir}/action.yml: 'inputs' must be a mapping")
    else:
        for name, spec in inputs.items():
            if not isinstance(spec, dict):
                errors.append(f"{action_dir}/action.yml: input '{name}' must be a mapping")
                continue
            if "description" not in spec:
                errors.append(f"{action_dir}/action.yml: input '{name}' is missing 'description'")
            if "required" not in spec and "default" not in spec:
                errors.append(
                    f"{action_dir}/action.yml: input '{name}' has neither 'required' nor 'default'"
                )

    branding = meta.get("branding")
    if branding is not None:
        if not isinstance(branding, dict):
            errors.append(f"{action_dir}/action.yml: 'branding' must be a mapping")
        else:
            icon = branding.get("icon")
            if icon is not None and icon not in VALID_BRANDING_ICONS:
                errors.append(
                    f"{action_dir}/action.yml: branding.icon {icon!r} is not a valid icon"
                )
            color = branding.get("color")
            if color is not None and color not in VALID_BRANDING_COLORS:
                errors.append(
                    f"{action_dir}/action.yml: branding.color {color!r} is not a valid color"
                )

    if using == "docker":
        dockerfile = action_dir / "Dockerfile"
        if not dockerfile.exists():
            errors.append(f"{action_dir}: runs.using is 'docker' but Dockerfile is missing")

    return errors


def main() -> int:
    all_errors: list[str] = []
    for action in ACTIONS:
        all_errors.extend(validate_action(Path(action)))
    if all_errors:
        for e in all_errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"Validated action.yml for {len(ACTIONS)} actions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
