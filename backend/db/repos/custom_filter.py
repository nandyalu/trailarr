from sqlmodel import Session, select

from db.engine import read_session, write_session
from db.models.customfilter import CustomFilter, CustomFilterCreate, CustomFilterRead, FilterType
from db.models.filter import Filter
from exceptions import ItemNotFoundError


def _to_read(db: CustomFilter) -> CustomFilterRead:
    return CustomFilterRead.model_validate(db)


def _sync_filters(
    cf_db: CustomFilter,
    cf_create: CustomFilterCreate,
    *,
    session: Session,
) -> None:
    """Sync nested Filter rows: add new, update existing, delete removed."""
    new_filters = [Filter.model_validate(f) for f in cf_create.filters]
    new_ids = [f.id for f in new_filters if f.id]
    existing = cf_db.filters
    existing_dict = {f.id: f for f in existing}

    for db_f in existing[:]:
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
def create(filter_create: CustomFilterCreate, *, _session: Session = None) -> CustomFilterRead:  # type: ignore
    db_filters = [Filter.model_validate(f) for f in filter_create.filters]
    filter_create.filters = []
    db_cf = CustomFilter.model_validate(filter_create)
    db_cf.filters = db_filters
    _session.add(db_cf)
    _session.commit()
    _session.refresh(db_cf)
    return _to_read(db_cf)


@read_session
def read_all(*, _session: Session = None) -> list[CustomFilterRead]:  # type: ignore
    return [_to_read(c) for c in _session.exec(select(CustomFilter)).all()]


@read_session
def read_by_type(filter_type: FilterType, *, _session: Session = None) -> list[CustomFilterRead]:  # type: ignore
    return [
        _to_read(c)
        for c in _session.exec(
            select(CustomFilter).where(CustomFilter.filter_type == filter_type)
        ).all()
    ]


@write_session
def update(filter_id: int, filter_create: CustomFilterCreate, *, _session: Session = None) -> CustomFilterRead:  # type: ignore
    db_cf = _session.get(CustomFilter, filter_id)
    if db_cf is None:
        raise ItemNotFoundError("CustomFilter", filter_id)
    db_cf.sqlmodel_update(filter_create.model_dump(exclude_unset=True))
    _sync_filters(db_cf, filter_create, session=_session)
    _session.add(db_cf)
    _session.commit()
    _session.refresh(db_cf)
    return _to_read(db_cf)


@write_session
def delete(filter_id: int, *, _session: Session = None) -> bool:  # type: ignore
    db_cf = _session.get(CustomFilter, filter_id)
    if not db_cf:
        return False
    for f in db_cf.filters:
        _session.delete(f)
    _session.delete(db_cf)
    _session.commit()
    return True
