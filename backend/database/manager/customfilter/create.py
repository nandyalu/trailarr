"""Add a saved filter to the database."""

from sqlmodel import Session
from database.manager.customfilter.base import convert_to_read_item
from database.models.customfilter import (
    CustomFilter,
    CustomFilterCreate,
    CustomFilterRead,
)
from database.models.filter import (
    Filter,
    validate_view_only_fields,
)
from database.engine import write_session


@write_session
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
    # Profile filters must not use view-only download fields. Checked here
    # explicitly: filter_create.filters is emptied below, so the check
    # inside CustomFilter.model_validate sees no filters on this path.
    validate_view_only_fields(filter_create.filter_type, db_filters)
    filter_create.filters = []
    db_filter = CustomFilter.model_validate(filter_create)
    db_filter.filters = db_filters
    _session.add(db_filter)
    _session.commit()
    _session.refresh(db_filter)
    return convert_to_read_item(db_filter)
