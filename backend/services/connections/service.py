"""Create and update connections.

This module owns the order of work: probe the server first, then write to the
database. The database managers below it only persist rows.

Phase 7 Stage B moved this orchestration out of
`database/manager/connection/`. The old create and update functions did the
network calls themselves, and `update` made them inside an open write
transaction.
"""

import database.manager.connection as connection_db
from database.models.connection import (
    ArrType,
    ConnectionBase,
    ConnectionCreate,
    ConnectionRead,
    ConnectionUpdate,
)
from services.connections import probe


def _merged_for_validation(
    existing: ConnectionRead, connection_update: ConnectionUpdate
) -> ConnectionBase:
    """Build the connection as it will be after the update.

    Only the fields the probes read are needed: arr_type, url and api_key.
    An update sends a subset of the fields, so the rest come from the row
    that is already stored.

    Args:
        existing (ConnectionRead): The connection as it is stored now.
        connection_update (ConnectionUpdate): The fields the user changed.

    Returns:
        ConnectionBase: The merged connection, for probing only.
    """
    changed = connection_update.model_dump(exclude_unset=True)
    return ConnectionBase(
        name=changed.get("name", existing.name),
        arr_type=changed.get("arr_type", existing.arr_type),
        url=changed.get("url", existing.url),
        external_url=changed.get("external_url", existing.external_url),
        api_key=changed.get("api_key", existing.api_key),
        monitor_new_media=changed.get(
            "monitor_new_media", existing.monitor_new_media
        ),
    )


async def create(connection: ConnectionCreate) -> tuple[str, int]:
    """Create a new connection in the database \n
    Args:
        connection (Connection): The connection to create
    Returns:
        tuple(str, int): The status message of the connection with version if created. \
            and the id of the created connection. \n
    Raises:
        ConnectionError: If the connection is refused / response is not 200
        ConnectionTimeoutError: If the connection times out
        InvalidResponseError: If API response is invalid
        ValidationError: If the connection is invalid
    """
    # Validate the connection details, will raise an error if invalid
    status = await probe.validate_connection(connection)
    # For Plex connections, fetch the server machine identifier to store
    machine_identifier: str | None = None
    if connection.arr_type == ArrType.PLEX:
        machine_identifier = await probe.get_machine_identifier(connection)
    _id = connection_db.create(
        connection, machine_identifier=machine_identifier
    )
    return status, _id


async def update(
    connection_id: int, connection_update: ConnectionUpdate
) -> ConnectionRead:
    """Update an existing connection in the database\n
    Args:
        connection_id (int): The id of the connection to update
        connection (Connection): The connection to update \n
    Returns:
        ConnectionRead: The updated read-only connection object. \n
    Raises:
        ConnectionError: If the connection is refused / response is not 200
        ConnectionTimeoutError: If the connection times out
        InvalidResponseError: If API response is invalid
        ItemNotFoundError: If a connection with provided id does not exist
    """
    # Read the stored row first. This raises ItemNotFoundError for a bad id,
    # before any network call is made.
    existing = connection_db.read(connection_id)
    merged = _merged_for_validation(existing, connection_update)
    # Validate the connection details, will raise an error if invalid
    await probe.validate_connection(merged)
    # For Plex connections, refresh the machine identifier in case the server changed
    machine_identifier: str | None = None
    if merged.arr_type == ArrType.PLEX:
        machine_identifier = await probe.get_machine_identifier(
            merged, identifier=f"trailarr_{connection_id}"
        )
    return connection_db.update(
        connection_id,
        connection_update,
        machine_identifier=machine_identifier,
    )
