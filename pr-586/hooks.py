"""Zensical macros for custom version badges."""

import re
from pathlib import Path


def _slugify(text: str) -> str:
    """Replicate MkDocs' default anchor slugify."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def _build_version_links() -> dict[str, str]:
    """Build VERSION_LINKS automatically from release-notes headings.

    Scans every *.md file under docs/release-notes/, extracts headings of the
    form '## **vX.Y.Z[-suffix]** - _Month DD, YYYY_', and maps the numeric
    version to a fragment URL.  No manual updates needed when new versions are
    added to the release notes.
    """
    links: dict[str, str] = {}
    notes_dir = Path(__file__).parent / "release-notes"
    heading_re = re.compile(
        r'^##\s+\*\*(v[\d.]+[^*]*)\*\*\s+-\s+_([^_]+)_',
        re.MULTILINE,
    )
    for md_file in sorted(notes_dir.glob("*.md")):
        year = md_file.stem  # "2025", "2026", …
        for match in heading_re.finditer(md_file.read_text(encoding="utf-8")):
            version_tag = match.group(1)   # e.g. "v0.9.7-beta"
            date_str = match.group(2)      # e.g. "June 09, 2026"
            # Strip leading 'v' and any pre-release suffix to get "0.9.7"
            version = re.sub(r'^v', '', version_tag)
            version = re.sub(r'[-+].*$', '', version)
            anchor = _slugify(f"{version_tag} - {date_str}")
            links[version] = f"{year}/#{anchor}"
    return links


# Built automatically from release-notes headings — no manual updates needed.
VERSION_LINKS: dict[str, str] = _build_version_links()


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


def define_env(env):
    """Register the macro with the Zensical environment."""

    @env.macro
    def version_badge(action_type, version):
        """Usage in Markdown: {{ version_badge('add', '0.9.1') }}"""

        _action = ACTIONS.get(action_type, ACTIONS["add"])
        link = VERSION_LINKS.get(version, "2026/")
        link = (  # Prepend /trailarr to the link
            f"/trailarr/release-notes/{link}"
        )

        # Use a raw <a> tag so Zensical's link resolver does not mangle the URL.
        return (
            f'{_action["icon"]}{{ title="{_action["text"]} v{version}"'
            f' {_action["style"]} }} <a href="{link}">v{version}</a>'
        )
