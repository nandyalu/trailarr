"""MkDocs hooks for custom macros and filters."""

import re
import posixpath

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page

# Version links mapping - UPDATE THESE WHEN VERSIONS ARE RELEASED
VERSION_LINKS: dict[str, str] = {
    "0.6.4": "2025.md#v064-beta-december-28-2025",
    "0.6.5": "2026.md#v065-beta-january-04-2026",
    "0.6.6": "2026.md#v066-beta-january-09-2026",
    "0.6.7": "2026.md#v067-beta-january-13-2026",
    "0.6.10": "2026.md#v0610-beta-february-07-2026",
    "0.7.0": "2026.md#v070-beta-february-11-2026",
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


def on_page_markdown(
    markdown: str, *, page: Page, config: MkDocsConfig, files: Files
) -> str:  # noqa: ARG001
    """Process markdown to replace version comments with badges."""

    def replace_version(match: re.Match) -> str:
        action_type = match.group(1) or "add"
        version = match.group(2)
        _action = ACTIONS.get(action_type, ACTIONS["add"])
        action_text = _action["text"]
        action_icon = _action["icon"]
        action_style = _action["style"]
        link = VERSION_LINKS.get(version, "2026.md")
        link = f"release-notes/{link}"
        link = _resolve_path(link, page, files)
        return (
            f'{action_icon}{{ title="{action_text} v{version}"'
            f" {action_style} }} [v{version}]({link})"
        )

    # Replace <!-- md:version[:action] X.X.X --> with version badge
    # action can be: add (default), upd, del
    pattern = r"<!-- md:version(?::(\w+))? (\d+\.\d+\.\d+) -->"
    return re.sub(pattern, replace_version, markdown)


# -----------------------------------------------------------------------------
# MkDocs file path resolution helpers
# Copied from https://github.com/squidfunk/mkdocs-material/blob/master/material/overrides/hooks/shortcodes.py


# Resolve path of file relative to given page - the posixpath always includes
# one additional level of `..` which we need to remove
def _resolve_path(path: str, page: Page, files: Files):
    path, anchor, *_ = f"{path}#".split("#")
    path = _resolve(files.get_file_from_path(path), page)  # type: ignore
    return "#".join([path, anchor]) if anchor else path


# Resolve path of file relative to given page - the posixpath always includes
# one additional level of `..` which we need to remove
def _resolve(file: File, page: Page):
    path = posixpath.relpath(file.src_uri, page.file.src_uri)
    return posixpath.sep.join(path.split(posixpath.sep)[1:])


# -----------------------------------------------------------------------------
