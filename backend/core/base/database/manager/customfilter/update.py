from sqlmodel import Session
from core.base.database.manager.customfilter.base import convert_to_read_item
from core.base.database.models.customfilter import (
    CustomFilter,
    CustomFilterCreate,
    CustomFilterRead,
)
from core.base.database.models.filter import Filter
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError


def __update_filters(
    cf_db: CustomFilter, cf_create: CustomFilterCreate, *, _session: Session
) -> None:
    """
    Update the filters of a custom filter.
    Args:
        cf_db (CustomFilter): CustomFilter Database object
        cf_create (CustomFilterCreate): CustomFilterCreate model
        _session (Session): A session to use for the database connection
    """
    # Get new filters as db objects
    new_filters = [
        Filter.model_validate(filter) for filter in cf_create.filters
    ]
    # Make a dictionary of new filters by id
    new_filters_ids = [filter.id for filter in new_filters if filter.id]
    # Get existing filters
    existing_filters = cf_db.filters
    existing_filters_dict = {filter.id: filter for filter in existing_filters}

    # Delete removed filters
    for db_filter in existing_filters[:]:  # Copy the list to avoid modifying
        if db_filter.id not in new_filters_ids:
            cf_db.filters.remove(db_filter)
            _session.delete(db_filter)

    for new_filter in new_filters:
        if new_filter.id:
            # Update existing filters
            if new_filter.id in existing_filters_dict:
                existing_filter = existing_filters_dict[new_filter.id]
                existing_filter.filter_by = new_filter.filter_by
                existing_filter.filter_condition = new_filter.filter_condition
                existing_filter.filter_value = new_filter.filter_value
                _session.add(existing_filter)
            # If new filter has an id, but it does not exist in the database \
            # then clear it's id and add it as a new filter
            else:
                new_filter.id = None
                new_filter.customfilter_id = cf_db.id
                cf_db.filters.append(new_filter)
        # Add new filters
        else:
            cf_db.filters.append(new_filter)
    return None


@manage_session
def update_customfilter(
    filter_id: int,
    filter_create: CustomFilterCreate,
    *,
    _session: Session = None,  # type: ignore
) -> CustomFilterRead:
    """
    Update an existing view filter.
    Args:
        filter_id (int): ID of the view filter
        filter_create (CustomFilterCreate): CustomFilterCreate model
        _session (Session, optional=None): A session to use for the \
            database connection. A new session is created if not provided.
    Returns:
        CustomFilterRead: CustomFilterRead object
    """

    db_filter = _session.get(CustomFilter, filter_id)
    if db_filter is None:
        raise ItemNotFoundError(model_name="CustomFilter", id=filter_id)
    # Update the customfilter from input
    _update_data = filter_create.model_dump(exclude_unset=True)
    db_filter.sqlmodel_update(_update_data)
    # Update the filters
    __update_filters(db_filter, filter_create, _session=_session)
    # Commit the changes to the database
    _session.add(db_filter)
    _session.commit()
    _session.refresh(db_filter)
    return convert_to_read_item(db_filter)
