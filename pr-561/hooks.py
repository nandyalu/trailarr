"""MkDocs hooks for custom macros and filters."""

# Version links mapping - UPDATE THESE WHEN VERSIONS ARE RELEASED
VERSION_LINKS: dict[str, str] = {
    "0.6.4": "2025.md/#v064-beta-december-28-2025",
    "0.6.5": "2026/#v065-beta-january-04-2026",
    "0.6.6": "2026/#v066-beta-january-09-2026",
    "0.6.7": "2026/#v067-beta-january-13-2026",
    "0.6.10": "2026/#v0610-beta-february-07-2026",
    "0.7.0": "2026/#v070-beta-february-11-2026",
    "0.8.0": "2026/#v080-beta-april-10-2026",
    "0.9.0": "2026/#v090-beta-april-30-2026",
    "0.9.1": "2026/#v091-beta-may-04-2026",
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

        # Use a raw <a> tag so MkDocs's link resolver does not mangle the URL.
        return (
            f'{_action["icon"]}{{ title="{_action["text"]} v{version}"'
            f' {_action["style"]} }} <a href="{link}">v{version}</a>'
        )
