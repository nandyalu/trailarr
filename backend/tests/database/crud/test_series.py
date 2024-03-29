import asyncio
import pytest

import backend.database.crud.connection as connectionCRUD
import backend.database.crud.series as seriesCRUD
from backend.database.models.connection import ArrType, ConnectionCreate, MonitorType
from backend.database.models.series import (
    # SeriesBase,
    SeriesCreate,
    SeriesUpdate,
    # SeriesRead,
)

# Copied from backend/database/crud/series.py
NO_SERIES_MESSAGE = "Series not found. Series id: {} does not exist!"


class TestSeriesDatabaseHandler:

    @pytest.fixture(autouse=True, scope="function")
    def session_fixture(self, monkeypatch):
        self.series_handler = seriesCRUD.SeriesDatabaseHandler()
        self.conn_handler = connectionCRUD.ConnectionDatabaseHandler()

        async def mock_result_success(connection: ConnectionCreate):
            return "Success message"

        # Mock the validate_connection function to return a success message
        monkeypatch.setattr(
            "backend.database.crud.connection.validate_connection",
            mock_result_success,
        )

        # Default connection object to use in tests
        connection = ConnectionCreate(
            name="Connection Name",
            arr_type=ArrType.SONARR,
            url="http://example.com",
            api_key="API_KEY",
            monitor=MonitorType.MONITOR_NEW,
        )
        # Call the create_connection method to use in tests
        asyncio.run(self.conn_handler.create(connection))

    def test_create_success(self):
        # Create a series to update later
        series = SeriesCreate(
            connection_id=1, sonarr_id=1, title="Series Title 1", tvdb_id="12345"
        )
        assert self.series_handler.create_or_update_bulk([series]) is True

    def test_create_or_update_bulk_success(self):
        # Create/update a series
        series = SeriesCreate(
            connection_id=1, sonarr_id=1, title="Series Title 1 Upd", tvdb_id="12345"
        )
        assert self.series_handler.create_or_update_bulk([series]) is True

        # Create another SeriesCreate object to add
        series2 = SeriesCreate(
            connection_id=1, sonarr_id=2, title="Series Title 2", tvdb_id="12346"
        )
        # Call the create method and assert the return value
        assert self.series_handler.create_or_update_bulk([series, series2]) is True

    def test_create_or_update_bulk_failed(self):
        # Create/update a series
        series = SeriesCreate(
            connection_id=1, sonarr_id=1, title="Series Title 1", tvdb_id="12345"
        )
        assert self.series_handler.create_or_update_bulk([series]) is True

        # Call the create method and assert the return value
        # Set the connection_id to 2 to raise an ItemNotFoundError
        series2 = series.model_copy()
        series2.connection_id = 2000

        with pytest.raises(Exception) as exc_info:
            self.series_handler.create_or_update_bulk([series, series2])
        assert exc_info.type.__name__ == "ItemNotFoundError"

    def test_create_or_update_bulk_failed2(self):
        # Create a series with sonarr_id = None to raise an error
        series3 = SeriesCreate(
            connection_id=1, sonarr_id=3, title="Series Title 3", tvdb_id="12347"
        )
        series3.sonarr_id = None  # type: ignore

        with pytest.raises(Exception) as exc_info:
            self.series_handler.create_or_update_bulk([series3])
        assert exc_info.type.__name__ == "ValidationError"

    def test_read_success(self):
        # Create a series to read
        series = SeriesCreate(
            connection_id=1, sonarr_id=1, title="Series Title 1", tvdb_id="12345"
        )
        assert self.series_handler.create_or_update_bulk([series]) is True

        # Call the read_series method and assert the return value
        series_read = self.series_handler.read(1)
        assert series_read is not None
        assert series_read.connection_id == series.connection_id
        assert series_read.sonarr_id == series.sonarr_id
        assert series_read.title == series.title
        assert series_read.year == series.year
        assert series_read.imdb_id == series.imdb_id
        assert series_read.tvdb_id == series.tvdb_id
        assert series_read.monitor is False

    def test_read_failed(self):
        # Call the read_series method and assert the return value
        with pytest.raises(Exception) as exc_info:
            self.series_handler.read(2000)
        assert exc_info.type.__name__ == "ItemNotFoundError"
        assert str(exc_info.value) == NO_SERIES_MESSAGE.format(2000)

    def test_read_all_success(self):
        # Create a series to read
        series = SeriesCreate(
            connection_id=1, sonarr_id=1, title="Series Title 1", tvdb_id="12345"
        )
        series2 = SeriesCreate(
            connection_id=1, sonarr_id=2, title="Series Title 2", tvdb_id="12346"
        )
        assert self.series_handler.create_or_update_bulk([series, series2]) is True

        # Call the read_all_series method and assert the return value
        series_read = self.series_handler.read_all()
        assert len(series_read) >= 1

    def test_read_all_by_connection_success(self):
        # Create a series to read
        series = SeriesCreate(
            connection_id=1, sonarr_id=1, title="Series Title 1", tvdb_id="12345"
        )
        series2 = SeriesCreate(
            connection_id=1, sonarr_id=2, title="Series Title 2", tvdb_id="12346"
        )
        assert self.series_handler.create_or_update_bulk([series, series2]) is True

        # Call the read_all_series method and assert the return value
        series_read = self.series_handler.read_all_by_connection(series.connection_id)
        assert len(series_read) >= 1
        assert series_read[0].connection_id == series.connection_id

    def test_read_recent_success(self):
        # Create a series to read
        series = SeriesCreate(
            connection_id=1, sonarr_id=1, title="Series Title 1", tvdb_id="12345"
        )
        series2 = SeriesCreate(
            connection_id=1, sonarr_id=2, title="Series Title 2", tvdb_id="12346"
        )
        assert self.series_handler.create_or_update_bulk([series, series2]) is True

        # Call the read_recent_series method and assert the return value
        series_read = self.series_handler.read_recent()
        assert len(series_read) >= 1

    def test_search_success(self):
        # Create a series to read
        series = SeriesCreate(
            connection_id=1, sonarr_id=1, title="Series Title 1", tvdb_id="12345"
        )
        series2 = SeriesCreate(
            connection_id=1, sonarr_id=2, title="Series Title 2", tvdb_id="12346"
        )
        assert self.series_handler.create_or_update_bulk([series, series2]) is True

        # Call the search_series method and assert the return value
        series_read = self.series_handler.search(series.title)
        assert len(series_read) == 1
        assert series_read[0].connection_id == series.connection_id
        assert series_read[0].sonarr_id == series.sonarr_id
        assert series_read[0].title == series.title
        assert series_read[0].year == series.year
        assert series_read[0].imdb_id == series.imdb_id
        assert series_read[0].tvdb_id == series.tvdb_id
        assert series_read[0].monitor is False

    def test_search_imdb_id_success(self):
        # Create a series to read
        series1 = SeriesCreate(
            connection_id=1,
            sonarr_id=1,
            title="Series Title 1",
            tvdb_id="12345",
            imdb_id="tt1234567",
        )
        series2 = SeriesCreate(
            connection_id=1,
            sonarr_id=2,
            title="Series Title 2",
            tvdb_id="12346",
            imdb_id="tt1234568",
        )
        assert self.series_handler.create_or_update_bulk([series1, series2]) is True

        # Call the search_series method and assert the return value
        series_read = self.series_handler.search(
            f"{series1.title} {series1.imdb_id} {series1.tvdb_id} {series1.year}"
        )
        assert len(series_read) == 1
        assert series_read[0].connection_id == series1.connection_id
        assert series_read[0].sonarr_id == series1.sonarr_id
        assert series_read[0].title == series1.title
        assert series_read[0].year == series1.year
        assert series_read[0].imdb_id == series1.imdb_id
        assert series_read[0].tvdb_id == series1.tvdb_id
        assert series_read[0].monitor is False

    def test_search_tvdb_id_success(self):
        # Create a series to read
        series1 = SeriesCreate(
            connection_id=1,
            sonarr_id=1,
            title="Series Title 1",
            tvdb_id="12345",
            imdb_id="tt1234567",
        )
        series2 = SeriesCreate(
            connection_id=1,
            sonarr_id=2,
            title="Series Title 2",
            tvdb_id="12346",
            imdb_id="tt1234568",
        )
        assert self.series_handler.create_or_update_bulk([series1, series2]) is True

        # Call the search_series method and assert the return value
        series_read = self.series_handler.search(
            f"{series1.title} {series1.tvdb_id} {series1.year}"
        )
        assert len(series_read) == 1
        assert series_read[0].connection_id == series1.connection_id
        assert series_read[0].sonarr_id == series1.sonarr_id
        assert series_read[0].title == series1.title
        assert series_read[0].year == series1.year
        assert series_read[0].imdb_id == series1.imdb_id
        assert series_read[0].tvdb_id == series1.tvdb_id
        assert series_read[0].monitor is False

    def test_search_year_success(self):
        # Create a series to read
        series1 = SeriesCreate(
            connection_id=1,
            sonarr_id=1,
            title="Series Title 1",
            tvdb_id="12345",
            imdb_id="tt1234567",
            year=2021,
        )
        series2 = SeriesCreate(
            connection_id=1,
            sonarr_id=2,
            title="Series Title 2",
            tvdb_id="12346",
            imdb_id="tt1234568",
            year=2022,
        )
        assert self.series_handler.create_or_update_bulk([series1, series2]) is True

        # Call the search_series method and assert the return value
        series_read = self.series_handler.search(f"{series1.title} {series1.year}")
        assert len(series_read) >= 1
        assert series_read[0].year == series1.year

    def test_search_fail_no_query(self):
        # Call the search_series method and assert the return value
        series_read = self.series_handler.search("")
        assert len(series_read) == 0

    def test_search_fail_no_results(self):
        # Create a series to read
        self.test_create_success()

        # Call the search_series method and assert the return value
        series_read = self.series_handler.search("No Results")
        assert len(series_read) == 0

    def test_update_success(self):
        # Create a series to update
        series1 = SeriesCreate(
            connection_id=1,
            sonarr_id=1,
            title="Series Title 1",
            tvdb_id="12345",
            imdb_id="tt1234567",
            year=2021,
        )
        assert self.series_handler.create_or_update_bulk([series1]) is True

        series_update1 = SeriesUpdate(sonarr_monitored=True, monitor=True)
        # Call the update_series method and assert the return value
        assert self.series_handler.update(1, series_update1) is True

        # Call the read_series method and assert the return value
        series_read = self.series_handler.read(1)
        assert series_read is not None
        assert series_read.monitor is series_update1.monitor
        assert series_read.sonarr_monitored is series_update1.sonarr_monitored

    def test_update_failed(self):
        series_update1 = SeriesUpdate(sonarr_monitored=True, monitor=True)
        # Call the update_series method and assert the return value
        with pytest.raises(Exception) as exc_info:
            self.series_handler.update(20001, series_update1)
        assert exc_info.type.__name__ == "ItemNotFoundError"
        assert str(exc_info.value) == NO_SERIES_MESSAGE.format(20001)

    def test_update_failed_no_connection(self):
        series1 = SeriesCreate(
            connection_id=1,
            sonarr_id=1,
            title="Series Title 1",
            tvdb_id="12345",
            imdb_id="tt1234567",
            year=2021,
        )
        assert self.series_handler.create_or_update_bulk([series1]) is True
        series_update1 = SeriesUpdate(
            connection_id=20002, sonarr_monitored=True, monitor=True
        )
        # Call the update_series method and assert the return value
        with pytest.raises(Exception) as exc_info:
            self.series_handler.update(1, series_update1)
        assert exc_info.type.__name__ == "ItemNotFoundError"

    def test_delete_success(self):
        # Create a series to delete
        self.test_create_success()

        # Call the delete_series method and assert the return value
        assert self.series_handler.delete(1) is True

        # Call the read_series method and assert an ItemNotFoundError is raised
        with pytest.raises(Exception) as exc_info:
            self.series_handler.read(1)
        assert exc_info.type.__name__ == "ItemNotFoundError"
        assert str(exc_info.value) == NO_SERIES_MESSAGE.format(1)

    def test_delete_failed(self):
        # Call the delete_series method and assert the return value
        with pytest.raises(Exception) as exc_info:
            self.series_handler.delete(2010)
        assert exc_info.type.__name__ == "ItemNotFoundError"
        assert str(exc_info.value) == NO_SERIES_MESSAGE.format(2010)

    def test_delete_bulk_success(self):
        # Create a series to delete
        series1 = SeriesCreate(
            connection_id=1,
            sonarr_id=1,
            title="Series Title 1",
            tvdb_id="12345",
            imdb_id="tt1234567",
            year=2021,
        )
        assert self.series_handler.create_or_update_bulk([series1]) is True

        # Call the read_all to get some series ids
        series_read = self.series_handler.read_all()
        series_ids = set([series.id for series in series_read])

        # Call the delete_series method and assert the return value
        assert self.series_handler.delete_bulk(series_ids) is True

        # Call the read_series method and assert an ItemNotFoundError is raised
        with pytest.raises(Exception) as exc_info:
            self.series_handler.read(1)
        assert exc_info.type.__name__ == "ItemNotFoundError"
        assert str(exc_info.value) == NO_SERIES_MESSAGE.format(1)

    def test_delete_bulk_failed(self):
        # Call the read_all to get some series ids
        series_read = self.series_handler.read_all()
        series_ids = set([series.id for series in series_read])

        # Delete all series
        assert self.series_handler.delete_bulk(series_ids) is True
        series_ids.add(2011)

        # Call the delete_series again method and assert exception
        with pytest.raises(Exception) as exc_info:
            self.series_handler.delete_bulk(series_ids)
        assert exc_info.type.__name__ == "ItemNotFoundError"
        assert str(exc_info.value) == NO_SERIES_MESSAGE.format(2011)
