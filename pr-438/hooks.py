"""MkDocs hooks for custom macros and filters."""

import re

# Version links mapping - UPDATE THESE WHEN VERSIONS ARE RELEASED
VERSION_LINKS: dict[str, str] = {
    "0.6.4": "/trailarr/release-notes/2025/#v064-beta-december-28-2025",
    "0.6.5": "/trailarr/release-notes/2026/#v065-beta-january-04-2026",
    # Add more versions as needed
}

# Action type mappings for version badges
ACTIONS: dict[str, dict[str, str]] = {
    "add": {
        "text": "Added in",
        "icon": ":material-creation:",
        "style": ".golden",
    },
    "upd": {
        "text": "Updated in",
        "icon": ":material-update:",
        "style": ".orange",
    },
    "del": {
        "text": "Removed in",
        "icon": ":material-delete:",
        "style": ".red",
    },
}


def on_page_markdown(markdown: str, **kwargs) -> str:  # noqa: ARG001
    """Process markdown to replace version comments with badges."""

    def replace_version(match: re.Match) -> str:
        action_type = match.group(1) or "add"
        version = match.group(2)
        _action = ACTIONS.get(action_type, ACTIONS["add"])
        action_text = _action["text"]
        action_icon = _action["icon"]
        action_style = _action["style"]
        link = VERSION_LINKS.get(version, "/trailarr/release-notes/2026/")
        return (
            f'{action_icon}{{ title="{action_text} v{version}"'
            f" {action_style} }} [v{version}]({link})"
        )

    # Replace <!-- md:version[:action] X.X.X --> with version badge
    # action can be: add (default), upd, del
    pattern = r"<!-- md:version(?::(\w+))? (\d+\.\d+\.\d+) -->"
    return re.sub(pattern, replace_version, markdown)
