from dataclasses import dataclass

from sqlmodel import Session, col, select

from db.engine import read_session, write_session
from db.models.customfilter import CustomFilter, CustomFilterCreate
from db.models.filter import Filter
from db.models.trailerprofile import TrailerProfile, TrailerProfileCreate, TrailerProfileRead
from exceptions import ItemNotFoundError


@dataclass
class TmdbRefreshConfig:
    movie_languages: list[str]
    series_languages: list[str]
    has_season_profile: bool


def _to_read(db: TrailerProfile) -> TrailerProfileRead:
    return TrailerProfileRead.model_validate(db)


def _get_or_404(profile_id: int, session: Session) -> TrailerProfile:
    obj = session.get(TrailerProfile, profile_id)
    if obj is None:
        raise ItemNotFoundError("TrailerProfile", profile_id)
    return obj


def _sync_filters(cf_db: CustomFilter, cf_create: CustomFilterCreate, *, session: Session) -> None:
    """Sync nested Filter rows: add new, update existing, delete removed."""
    new_filters = [Filter.model_validate(f) for f in cf_create.filters]
    new_ids = [f.id for f in new_filters if f.id]
    existing_dict = {f.id: f for f in cf_db.filters}

    for db_f in cf_db.filters[:]:
        if db_f.id not in new_ids:
            cf_db.filters.remove(db_f)
            session.delete(db_f)

    for new_f in new_filters:
        if new_f.id:
            if new_f.id in existing_dict:
                ex = existing_dict[new_f.id]
                ex.filter_by = new_f.filter_by
                ex.filter_condition = new_f.filter_condition
                ex.filter_value = new_f.filter_value
                session.add(ex)
            else:
                new_f.id = None
                new_f.customfilter_id = cf_db.id
                cf_db.filters.append(new_f)
        else:
            cf_db.filters.append(new_f)


@write_session
def create(profile_create: TrailerProfileCreate, *, _session: Session = None) -> TrailerProfileRead:  # type: ignore
    db = TrailerProfile.model_validate(profile_create)
    _session.add(db)
    _session.commit()
    _session.refresh(db)
    return _to_read(db)


@read_session
def read(profile_id: int, *, _session: Session = None) -> TrailerProfileRead:  # type: ignore
    return _to_read(_get_or_404(profile_id, _session))


@read_session
def read_all(*, _session: Session = None) -> list[TrailerProfileRead]:  # type: ignore
    return [_to_read(p) for p in _session.exec(select(TrailerProfile)).all()]


@read_session
def get_tmdb_refresh_config(*, _session: Session = None) -> TmdbRefreshConfig:  # type: ignore
    """Return language lists and season-profile flag for the TMDB refresh task."""
    rows = _session.exec(
        select(TrailerProfile.tmdb_language, TrailerProfile.for_movies)
    ).all()
    movie_langs: set[str] = {""}
    series_langs: set[str] = {""}
    for lang, for_movies in rows:
        (movie_langs if for_movies else series_langs).add(lang or "")

    has_season = _session.exec(
        select(TrailerProfile.id)
        .where(
            col(TrailerProfile.enabled).is_(True),
            col(TrailerProfile.download_season_videos).is_(True),
        )
        .limit(1)
    ).first() is not None

    return TmdbRefreshConfig(
        movie_languages=sorted(movie_langs),
        series_languages=sorted(series_langs),
        has_season_profile=has_season,
    )


@read_session
def get_trailer_folders(*, _session: Session = None) -> set[str]:  # type: ignore
    results = _session.exec(select(TrailerProfile.folder_name).distinct()).all()
    return {f.strip() for f in results if f and f.strip()}


@write_session
def update(profile_id: int, profile_create: TrailerProfileCreate, *, _session: Session = None) -> TrailerProfileRead:  # type: ignore
    db = _get_or_404(profile_id, _session)
    db.sqlmodel_update(profile_create.model_dump(exclude_unset=True))
    _sync_filters(db.customfilter, profile_create.customfilter, session=_session)
    TrailerProfile.model_validate(db)
    _session.commit()
    _session.refresh(db)
    return _to_read(db)


@write_session
def update_setting(profile_id: int, setting: str, value: str | int | bool, *, _session: Session = None) -> TrailerProfileRead:  # type: ignore
    db = _get_or_404(profile_id, _session)
    if not hasattr(db, setting):
        raise ValueError(f"Invalid setting '{setting}' for TrailerProfile.")
    if TrailerProfile.is_bool_field(setting):
        value = db.validate_bool(value)
    if TrailerProfile.is_int_field(setting):
        value = int(value)
    setattr(db, setting, value)
    TrailerProfile.model_validate(db)
    _session.commit()
    _session.refresh(db)
    return _to_read(db)


@write_session
def delete(profile_id: int, *, _session: Session = None) -> bool:  # type: ignore
    db = _get_or_404(profile_id, _session)
    try:
        for f in db.customfilter.filters:
            _session.delete(f)
        _session.delete(db.customfilter)
    except Exception:
        pass
    _session.delete(db)
    _session.commit()
    return True
