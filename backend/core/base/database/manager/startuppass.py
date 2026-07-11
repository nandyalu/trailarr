from sqlmodel import Session, select

from config.settings import app_settings
from core.base.database.models.startuppass import StartupPass
from core.base.database.utils.engine import read_session, write_session


@read_session
def is_completed(
    name: str,
    *,
    _session: Session = None,  # type: ignore
) -> bool:
    """Whether the named startup pass has a completion record."""
    return _session.get(StartupPass, name) is not None


@read_session
def completed_names(
    *,
    _session: Session = None,  # type: ignore
) -> set[str]:
    """Names of all completed startup passes."""
    return {p.name for p in _session.exec(select(StartupPass)).all()}


@write_session
def mark_completed(
    name: str,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Record the named startup pass as completed (idempotent)."""
    if _session.get(StartupPass, name) is not None:
        return
    _session.add(
        StartupPass(name=name, app_version=app_settings.version or "")
    )
    _session.commit()
