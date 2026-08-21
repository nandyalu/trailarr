"""Report models for the Connection Doctor.

These are API/response models only — reports are not stored in the
database. The last report per connection lives in memory and is rebuilt
on demand (a check takes well under a second for local folders).
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ProbeStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


class SuggestedMapping(BaseModel):
    """A concrete path mapping the user can apply with one click."""

    path_from: str
    """The root folder as the Arr/Plex application reports it."""
    path_to: str
    """The equivalent folder as Trailarr sees it."""
    corroborations: int = 1
    """Number of probed paths that resolve under this mapping. 1 means
    the match is based on the folder name only — check before applying."""
    updates_existing: bool = False
    """True when the connection already has a mapping for this root —
    applying changes that mapping's target instead of adding a row."""


class ProbeResult(BaseModel):
    """Outcome of one check, with the fix when one is known."""

    kind: str
    """Probe type: 'reachability', 'path_visibility', 'permissions',
    or 'path_style'."""
    name: str
    """Short display label, e.g. "Folder: /data/movies"."""
    status: ProbeStatus
    detail: str
    """What the probe found. One or two short sentences."""
    remediation: str = ""
    """What the user can do about it. Empty when status is ok."""
    docs_url: str = ""
    """Docs anchor with the full fix instructions."""
    suggested_mapping: SuggestedMapping | None = None
    """Set on path_visibility failures when the doctor found a likely
    local equivalent of the remote path."""


class HealthCheckResult(BaseModel):
    """Outcome of one system health check."""

    key: str
    """Stable identifier: 'ffmpeg', 'hardware', 'ytdlp', 'app_version',
    'cookies', 'connections', 'images', 'disk_space', 'ytdlp_test'."""
    name: str
    """Display label, e.g. "FFmpeg"."""
    status: ProbeStatus
    detail: str
    remediation: str = ""
    docs_url: str = ""
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class HealthReport(BaseModel):
    """All health checks, with the overall state."""

    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: str = "healthy"
    """'healthy' when every check is ok/skipped, else 'issues'."""
    checks: list[HealthCheckResult] = []

    def finalize(self) -> "HealthReport":
        has_issue = any(
            c.status in (ProbeStatus.ERROR, ProbeStatus.WARNING)
            for c in self.checks
        )
        self.status = "issues" if has_issue else "healthy"
        return self


class CookiesStatus(BaseModel):
    """Status of the YouTube cookies file — never its content."""

    configured: bool = False
    path: str = ""
    exists: bool = False
    youtube_cookies: int = 0
    expired: bool = False
    detail: str = ""


class CookiesUpload(BaseModel):
    """Cookies file content, write-only (accepted, never returned)."""

    content: str


class DoctorReport(BaseModel):
    """All probe results for one connection."""

    connection_id: int
    connection_name: str
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: str = "healthy"
    """'healthy' when every probe is ok/skipped, else 'issues'."""
    probes: list[ProbeResult] = []

    def finalize(self) -> "DoctorReport":
        """Set the overall status from the probe results."""
        has_issue = any(
            p.status in (ProbeStatus.ERROR, ProbeStatus.WARNING)
            for p in self.probes
        )
        self.status = "issues" if has_issue else "healthy"
        return self
