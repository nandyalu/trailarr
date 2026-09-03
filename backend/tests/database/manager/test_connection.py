import pytest

import database.manager.connection as db_manager
from database.models.connection import (
    ArrType,
    ConnectionCreate,
    ConnectionUpdate,
)
from exceptions import ItemNotFoundError

# Copied from backend/database/crud/connection.py
CREATE_SUCCESS_MSG = "Connection createded successfully! {}"
UPDATE_SUCCESS_MESSAGE = "Connection updated successfully!"
DELETE_SUCCESS_MESSAGE = "Connection deleted successfully!"
NO_CONN_MESSAGE = "Connection with id {} not found"

# Default connection object to use in tests
connection = ConnectionCreate(
    name="Connection Name",
    arr_type=ArrType.RADARR,
    url="http://example.com",
    api_key="API_KEY",
    monitor_new_media=True,
    path_mappings=[],
)

# Default connection update object to use in tests
connection_update = ConnectionUpdate(
    monitor_new_media=True, path_mappings=[]
)

# Note: connection ids are autoincrement and shared with every other test
# module in the session, so these tests use the id that `create` returns.
# Do not assume a connection gets id 1 — collection order decides who
# creates the first row.

# Note: these tests cover persistence only. Validating a connection against
# the server moved to services/connections/probe.py in Phase 7 Stage B, and
# the create/update order of work moved to services/connections/service.py.
# Their tests live in tests/services/connections/.


class TestConnectionDatabaseHandler:

    def _create_connection(self) -> int:
        """Save the default connection and give back its new id."""
        id = db_manager.create(connection)
        assert id >= 1
        return id

    def test_create_connection(self):
        self._create_connection()

    def test_create_connection_stores_machine_identifier(self):
        """A Plex caller passes the identifier it read; create stores it."""
        id = db_manager.create(connection, machine_identifier="abc123")
        assert db_manager.read(id).machine_identifier == "abc123"

    def test_create_connection_without_machine_identifier(self):
        """Arr connections have no machine identifier."""
        id = db_manager.create(connection)
        assert db_manager.read(id).machine_identifier is None

    def test_read_connection(self):
        # Call the create_connection method and assert the return value
        conn_id = self._create_connection()

        # Call the read_connection method and assert the return values match
        result = db_manager.read(conn_id)
        assert result.id == conn_id
        assert result.name == connection.name
        assert result.arr_type == connection.arr_type
        assert result.url == connection.url
        assert result.api_key == connection.api_key
        assert result.monitor_new_media == connection.monitor_new_media

    def test_read_connection_fail(self):
        # Call the read_connection method and assert an ItemNotFoundError is raised
        with pytest.raises(ItemNotFoundError) as exc_info:
            db_manager.read(1_000)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1_000)

    def test_read_connection_exists(self):
        # Call the create_connection method and assert the return value
        conn_id = self._create_connection()

        # Call the `exists` method and assert the return value
        result = db_manager.exists(conn_id)
        assert result is True

    def test_read_connection_not_exists(self):
        # Call the `exists` method and assert the return value
        result = db_manager.exists(1_000)
        assert result is False

    def test_update_connection(self):
        # Call the create_connection method and assert the return value
        conn_id = self._create_connection()

        # Call the update_connection method and assert the return value
        update_result = db_manager.update(conn_id, connection_update)

        # Call the read_connection method and assert the return values match
        assert update_result.id == conn_id
        assert update_result.name == connection.name
        assert update_result.arr_type == connection.arr_type
        assert update_result.url == connection.url
        assert update_result.api_key == connection.api_key
        assert update_result.monitor_new_media == connection_update.monitor_new_media

    def test_update_connection_stores_machine_identifier(self):
        """The caller passes a refreshed Plex identifier; update stores it."""
        conn_id = db_manager.create(connection, machine_identifier="old")
        db_manager.update(
            conn_id, connection_update, machine_identifier="new"
        )
        assert db_manager.read(conn_id).machine_identifier == "new"

    def test_update_connection_keeps_machine_identifier_when_not_given(self):
        """No identifier passed means the stored one is left alone."""
        conn_id = db_manager.create(connection, machine_identifier="keep-me")
        db_manager.update(conn_id, connection_update)
        assert db_manager.read(conn_id).machine_identifier == "keep-me"

    def test_update_connection_fail(self):
        # Call the create_connection method and assert the return value
        self._create_connection()

        # Call the update_connection method and assert the return value
        with pytest.raises(ItemNotFoundError) as exc_info:
            db_manager.update(1_000, connection_update)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1_000)

    def test_delete_connection(self):
        # Call the create_connection method and assert the return value
        self._create_connection()
        second_id = self._create_connection()
        self._create_connection()
        # Note: We are creating multiple connections and deleting the second one
        # to test the delete method so that it does not affect the other tests
        # that rely on the first connection being present (movie / series CRUD tests)

        # Call the delete_connection method and assert the return value
        delete_result = db_manager.delete(second_id)
        assert delete_result is True

        # Call the read_connection method and assert an ItemNotFoundError is raised
        with pytest.raises(ItemNotFoundError) as exc_info:
            db_manager.read(second_id)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(second_id)

    def test_delete_connection_fail(self):
        # Call the delete_connection method and assert an ItemNotFoundError is raised
        with pytest.raises(ItemNotFoundError) as exc_info:
            db_manager.delete(1000)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1000)
