from sqlmodel import Session
from core.base.database.manager.customfilter.base import convert_to_read_item
from core.base.database.models.customfilter import (
    CustomFilter,
    CustomFilterCreate,
    CustomFilterRead,
)
from core.base.database.models.filter import Filter
from core.base.database.utils.engine import manage_session


@manage_session
def create_customfilter(
    filter_create: CustomFilterCreate,
    *,
    _session: Session = None,  # type: ignore
) -> CustomFilterRead:
    """
    Create a new custom filter.
    Args:
        filter_create (CustomFilterCreate): CustomFilterCreate model
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        CustomFilterRead: CustomFilterRead object
    """
    db_filters: list[Filter] = []
    for filter in filter_create.filters:
        db_filters.append(Filter.model_validate(filter))
    filter_create.filters = []
    db_filter = CustomFilter.model_validate(filter_create)
    db_filter.filters = db_filters
    _session.add(db_filter)
    _session.commit()
    _session.refresh(db_filter)
    return convert_to_read_item(db_filter)
