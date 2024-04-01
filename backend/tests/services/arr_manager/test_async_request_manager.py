from unittest.mock import AsyncMock, Mock
from aiohttp import ClientConnectionError, ServerTimeoutError
import pytest
from backend.exceptions import ConnectionTimeoutError, InvalidResponseError
from backend.core.base.arr_manager.request_manager import AsyncRequestManager
import backend.tests.conftest as conftest


class TestAsyncRequestManager:
    # Set up the expected url, path, parameters and data
    url = conftest.TEST_AIOHTTP_URL
    api_key = conftest.TEST_AIOHTTP_APIKEY
    path = conftest.TEST_AIOHTTP_PATH
    params = conftest.TEST_AIOHTTP_PARAMS
    data = None
    response_value = conftest.TEST_AIOHTTP_RESPONSE
    final_url = conftest.TEST_AIOHTTP_FINAL_URL

    @pytest.fixture(autouse=True)
    def request_manager(self):
        return AsyncRequestManager(self.url, self.api_key)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
    async def test_async_request(
        self, method: str, request_manager: AsyncRequestManager, debug_aiohttp_200
    ):
        # Now call your method which uses session.request
        response = await request_manager._request(
            method, self.path, self.params, self.data
        )
        # Now you can make assertions about the response
        assert response == self.response_value

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "exception_occurred, exception_raised, message",
        [
            (
                ServerTimeoutError,
                ConnectionTimeoutError,
                "Timeout occurred while connecting to API.",
            ),
            (
                ClientConnectionError,
                ConnectionError,
                "Connection Refused while connecting to API.",
            ),
            (
                Exception,
                ConnectionError,
                "Unable to connect to API. Check your connection.",
            ),
        ],
    )
    async def test_request_get_connection_error1(
        self,
        debug_aiohttp,
        exception_occurred,
        exception_raised,
        message,
        request_manager,
    ):
        debug_aiohttp.get(self.final_url, exception=exception_occurred)
        method = "GET"
        # Now call your method which uses session.request
        with pytest.raises(Exception) as e:
            await request_manager._request(method, self.path, self.params, self.data)
        # Now you can make assertions about the response
        assert e.type == exception_raised
        assert str(e.value) == message

    @pytest.mark.asyncio
    async def test_process_response_200_json(
        self, request_manager: AsyncRequestManager, debug_aiohttp_200
    ):
        response = await request_manager._request(
            "GET", self.path, self.params, self.data
        )
        assert response == self.response_value

    @pytest.mark.asyncio
    async def test_process_response_200_text_content(
        self, request_manager: AsyncRequestManager
    ):
        # Mock the response object
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json.side_effect = Exception
        mock_response.headers = {"content-type": "application/response; charset=utf-8"}
        mock_response.text = AsyncMock(return_value="Some Text Response")

        # Call the _process_response method
        response = await request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        assert response == "Some Text Response"

    @pytest.mark.asyncio
    async def test_process_response_200_text_response(
        self, request_manager: AsyncRequestManager
    ):

        # Mock the response object
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json.side_effect = Exception
        mock_response.headers = {"content-type": "text/plain; charset=utf-8"}
        mock_response.text = "Some Text Response"

        # Call the _process_response method
        with pytest.raises(Exception) as e:
            await request_manager._process_response(mock_response)

        # Assert that an exception is raised
        error_msg = (
            "Invalid Response from server! Check if "
            f"{request_manager.host_url} is a valid API endpoint."
        )
        assert str(e.value) == error_msg
        assert e.type == InvalidResponseError

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "status, msg",
        [
            (400, "Bad Request, possibly a bug. Some Error Text"),
            (401, "Unauthorized. Please ensure valid API Key is used: API_KEY"),
            (
                403,
                "Access restricted. Please ensure API Key 'API_KEY' has correct permissions",
            ),
            (404, "Resource not found: http://example.com/example"),
            (405, "The endpoint http://example.com/example is not allowed"),
            (
                502,
                "Bad Gateway. Check if your server at http://example.com/example is accessible.",
            ),
            (
                503,
                "Invalid Host (http://example.com) or API Key (API_KEY), "
                "not a Radarr or Sonarr instance.",
            ),
        ],
    )
    async def test_process_response_not_200(
        self, request_manager: AsyncRequestManager, status, msg
    ):

        # Mock the response object
        mock_response = Mock()
        mock_response.url = "http://example.com/example"
        mock_response.status = status
        mock_response.text = AsyncMock(return_value="Some Error Text")

        # Call the _process_response method
        with pytest.raises(Exception) as e:
            await request_manager._process_response(mock_response)

        # Assert that an exception is raised
        assert msg == str(e.value)
        assert e.type == ConnectionError

    @pytest.mark.asyncio
    async def test_process_response_500_json(
        self, request_manager: AsyncRequestManager
    ):
        # Mock the response object
        mock_response = Mock()
        mock_response.status = 500
        mock_response.json = AsyncMock(return_value={"message": "Some Error Text"})

        # Call the _process_response method
        with pytest.raises(Exception) as e:
            await request_manager._process_response(mock_response)

        # Assert that an exception is raised
        assert "Internal Server Error: Some Error Text" == str(e.value)
        assert e.type == ConnectionError

    @pytest.mark.asyncio
    async def test_process_response_500_text(
        self, request_manager: AsyncRequestManager
    ):
        # Mock the response object
        mock_response = Mock()
        mock_response.status = 500
        mock_response.json.side_effect = Exception
        mock_response.text = AsyncMock(return_value="")

        # Call the _process_response method
        with pytest.raises(Exception) as e:
            await request_manager._process_response(mock_response)

        # Assert that an exception is raised
        assert "Internal Server Error: Unknown Error Occurred." == str(e.value)
        assert e.type == ConnectionError

        # Change the mock response to return some error text
        mock_response.text = AsyncMock(return_value="Some Error Text")
        # Call the _process_response method
        with pytest.raises(Exception) as e:
            await request_manager._process_response(mock_response)

        # Assert that an exception is raised
        assert "Internal Server Error: Some Error Text" == str(e.value)
        assert e.type == ConnectionError
