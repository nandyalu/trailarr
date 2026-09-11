"""What the frontend needs to know about the first-run setup guide."""

from pydantic import BaseModel


class SetupStatus(BaseModel):
    """The state of the setup guide for this installation."""

    needed: bool
    """True while the guide has not been finished or skipped."""
    completed: bool
    connections: int
    """How many connections exist. The guide's first real step."""
    media: int
    """How many media items exist. Zero until the first sync finishes."""
    downloads_enabled: bool
    """False means preview mode: Trailarr shows what it would download."""
    tmdb_key_set: bool
