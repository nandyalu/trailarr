from contextlib import contextmanager
from functools import wraps
from importlib import reload
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

# from backend.database.crud.connection import connectionCRUD.ConnectionDatabaseHandler
import backend.database.crud.connection as connectionCRUD
from backend.database.models.connection import (
    ArrType,
    ConnectionBase,
    ConnectionCreate,
    ConnectionUpdate,
    MonitorType,
)
from backend.exceptions import InvalidResponseError


# Copied from backend/database/crud/connection.py
CREATE_SUCCESS_MSG = "Connection createded successfully! {}"
UPDATE_SUCCESS_MESSAGE = "Connection updated successfully!"
DELETE_SUCCESS_MESSAGE = "Connection deleted successfully!"
NO_CONN_MESSAGE = "Connection not found. Connection id: {} does not exist!"

VALIDATE_SUCCESS_MSG = "Success message"
VALIDATE_FAIL_MESSAGE = "Some Value is invalid!"

# Default connection object to use in tests
connection = ConnectionCreate(
    name="Connection Name",
    type=ArrType.RADARR,
    url="http://example.com",
    api_key="API_KEY",
    monitor=MonitorType.MONITOR_NEW,
)

# Default connection update object to use in tests
connection_update = ConnectionUpdate(monitor=MonitorType.MONITOR_ALL)

# Default Connection id for create
CONN_ID_1 = 1

# Default Connection id for failed read/update/delete
CONN_ID_2 = 2

# Setup the in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)
SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()


def mock_manage_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check if a '_session' keyword argument was provided
        if kwargs.get("_session") is None:
            # If not, create a new session and add it to kwargs
            with get_session() as _session:
                kwargs["_session"] = _session
                return func(*args, **kwargs)
        else:
            # If a session was provided, just call the function
            return func(*args, **kwargs)

    return wrapper


class TestConnectionDatabaseHandler:
    db_handler = connectionCRUD.ConnectionDatabaseHandler()

    @pytest.fixture(autouse=True)
    def session_fixture(self, monkeypatch):
        # Monkeypatch the manage_session decorator
        monkeypatch.setattr(
            "backend.database.utils.engine.manage_session",
            mock_manage_session,
        )
        # Reload the connectionCRUD module to apply the monkeypatch to decorator
        reload(connectionCRUD)
        self.db_handler = connectionCRUD.ConnectionDatabaseHandler()

        def mock_result_success(connection: ConnectionBase):
            return "Success message"

        # Mock the validate_connection function to return a success message
        monkeypatch.setattr(
            "backend.database.crud.connection.validate_connection",
            mock_result_success,
        )

    def test_create_connection(self):

        # Call the create_connection method and assert the return value
        result = self.db_handler.create(connection)
        assert result == CREATE_SUCCESS_MSG.format(VALIDATE_SUCCESS_MSG)

    def test_create_connection_fail(self, monkeypatch):
        def mock_result_fail(connection: ConnectionBase):
            raise InvalidResponseError(VALIDATE_FAIL_MESSAGE)

        # Mock the validate_connection function to raise an InvalidResponseError
        # This overrides the previous mock that was set in the autouse fixture
        monkeypatch.setattr(
            "backend.database.crud.connection.validate_connection",
            mock_result_fail,
        )
        # Call the create_connection method and assert the return value
        with pytest.raises(Exception) as exc_info:
            self.db_handler.create(connection)

        assert str(exc_info.value) == VALIDATE_FAIL_MESSAGE
        assert exc_info.type.__name__ == "InvalidResponseError"

    def test_read_connection(self):
        # Call the create_connection method and assert the return value
        with get_session() as session:
            self.db_handler.create(connection, _session=session)
            # self.test_create_connection()

            # Call the read_connection method and assert the return values match
            result = self.db_handler.read(CONN_ID_1, _session=session)
        assert result.id == CONN_ID_1
        assert result.name == connection.name
        assert result.type == connection.type
        assert result.url == connection.url
        assert result.api_key == connection.api_key
        assert result.monitor == connection.monitor

    def test_read_connection_fail(self):
        # Call the read_connection method and assert an ItemNotFoundError is raised
        with pytest.raises(Exception) as exc_info:
            self.db_handler.read(1_000)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1_000)
        assert exc_info.type.__name__ == "ItemNotFoundError"

    def test_read_connection_exists(self):
        # Call the create_connection method and assert the return value
        self.test_create_connection()

        # Call the check_if_exists method and assert the return value
        result = self.db_handler.check_if_exists(CONN_ID_1)
        assert result is True

    def test_read_connection_not_exists(self):
        # Call the check_if_exists method and assert the return value
        result = self.db_handler.check_if_exists(1_000)
        assert result is False

    def test_update_connection(self):
        # Call the create_connection method and assert the return value
        self.test_create_connection()

        # Call the update_connection method and assert the return value
        update_result = self.db_handler.update(CONN_ID_1, connection_update)
        assert update_result == UPDATE_SUCCESS_MESSAGE

        # Call the read_connection method and assert the return values match
        read_result = self.db_handler.read(CONN_ID_1)
        assert read_result.id == CONN_ID_1
        assert read_result.name == connection.name
        assert read_result.type == connection.type
        assert read_result.url == connection.url
        assert read_result.api_key == connection.api_key
        assert read_result.monitor == connection_update.monitor

    def test_update_connection_fail(self):
        # Call the create_connection method and assert the return value
        self.test_create_connection()

        # Call the update_connection method and assert the return value
        with pytest.raises(Exception) as exc_info:
            self.db_handler.update(1_000, connection_update)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(1_000)
        assert exc_info.type.__name__ == "ItemNotFoundError"

    def test_delete_connection(self):
        # Call the create_connection method and assert the return value
        self.test_create_connection()

        # Call the delete_connection method and assert the return value
        delete_result = self.db_handler.delete(CONN_ID_1)
        assert delete_result == DELETE_SUCCESS_MESSAGE

        # Call the read_connection method and assert an ItemNotFoundError is raised
        with pytest.raises(Exception) as exc_info:
            self.db_handler.read(CONN_ID_1)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(CONN_ID_1)
        assert exc_info.type.__name__ == "ItemNotFoundError"

    def test_delete_connection_fail(self):
        # Call the delete_connection method and assert an ItemNotFoundError is raised
        with pytest.raises(Exception) as exc_info:
            self.db_handler.delete(CONN_ID_1)

        assert str(exc_info.value) == NO_CONN_MESSAGE.format(CONN_ID_1)
        assert exc_info.type.__name__ == "ItemNotFoundError"
