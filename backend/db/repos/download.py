from sqlmodel import Session, desc, select, text

from db.engine import read_session, write_session
from db.models.download import Download, DownloadCreate, DownloadRead
from exceptions import ItemNotFoundError


def _get_or_404(download_id: int, session: Session) -> Download:
    obj = session.get(Download, download_id)
    if obj is None:
        raise ItemNotFoundError("Download", download_id)
    return obj


def _to_read(db: Download) -> DownloadRead:
    return DownloadRead.model_validate(db)


@write_session
def create(download_create: DownloadCreate, *, _session: Session = None) -> DownloadRead:  # type: ignore
    db = Download.model_validate(download_create)
    _session.add(db)
    _session.commit()
    _session.refresh(db)
    return _to_read(db)


@read_session
def read(download_id: int, *, _session: Session = None) -> DownloadRead:  # type: ignore
    return _to_read(_get_or_404(download_id, _session))


@read_session
def read_all(*, _session: Session = None) -> list[DownloadRead]:  # type: ignore
    dbs = _session.exec(select(Download).order_by(desc(Download.added_at))).all()
    return [_to_read(d) for d in dbs]


@read_session
def read_all_raw(*, _session: Session = None) -> list[dict]:  # type: ignore
    result = _session.execute(text("SELECT * FROM download ORDER BY added_at DESC"))
    return [dict(r) for r in result.mappings()]


@read_session
def read_by_media_id(media_id: int, *, _session: Session = None) -> list[DownloadRead]:  # type: ignore
    dbs = _session.exec(
        select(Download).where(Download.media_id == media_id).order_by(desc(Download.added_at))
    ).all()
    return [_to_read(d) for d in dbs]


@read_session
def read_by_profile_id(profile_id: int, *, _session: Session = None) -> list[DownloadRead]:  # type: ignore
    dbs = _session.exec(
        select(Download).where(Download.profile_id == profile_id).order_by(desc(Download.added_at))
    ).all()
    return [_to_read(d) for d in dbs]


@write_session
def update(download_id: int, download_create: DownloadCreate, *, _session: Session = None) -> DownloadRead:  # type: ignore
    db = _get_or_404(download_id, _session)
    db.sqlmodel_update(download_create.model_dump(exclude_unset=True))
    Download.model_validate(db)
    _session.commit()
    _session.refresh(db)
    return _to_read(db)


@write_session
def mark_as_deleted(download_id: int, *, _session: Session = None) -> None:  # type: ignore
    db = _get_or_404(download_id, _session)
    db.file_exists = False
    _session.add(db)
    _session.commit()


@write_session
def delete(download_id: int, *, _session: Session = None) -> bool:  # type: ignore
    db = _get_or_404(download_id, _session)
    _session.delete(db)
    _session.commit()
    return True


@write_session
def delete_all_for_media(media_id: int, *, _session: Session = None) -> int:  # type: ignore
    downloads = _session.exec(select(Download).where(Download.media_id == media_id)).all()
    count = len(downloads)
    for d in downloads:
        _session.delete(d)
    _session.commit()
    return count
