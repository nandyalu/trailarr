from unittest import TestCase
from unittest.mock import Mock

import requests
from backend.exceptions import ConnectionTimeoutError, InvalidResponseError
from backend.services.arr_manager.request_manager import RequestManager


class TestRequestManager(TestCase):
    def setUp(self):
        self.request_manager = RequestManager("http://example.com", "API_KEY")
        # Mock the session object
        self.request_manager.session = Mock()

    def test_request_get(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        self.request_manager.session.get.return_value = mock_response

        # Set up the expected parameters and data
        method = "GET"
        path = "example"
        params = {"param1": "value1"}
        data = None

        # Call the _request method
        response = self.request_manager._request(method, path, params, data)

        # Assert that the session's get method was called with the correct arguments
        self.request_manager.session.get.assert_called_once_with(
            "http://example.com/example",
            headers={"X-Api-Key": "API_KEY"},
            params={"param1": "value1"},
            json=None,
        )

        # Assert that the response is processed correctly
        self.assertEqual(
            response, self.request_manager._process_response(mock_response)
        )

    def test_request_post(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        self.request_manager.session.post.return_value = mock_response

        # Set up the expected parameters and data
        method = "POST"
        path = "example"
        params = {"param1": "value1"}
        data = None

        # Call the _request method
        response = self.request_manager._request(method, path, params, data)

        # Assert that the session's post method was called with the correct arguments
        self.request_manager.session.post.assert_called_once_with(
            "http://example.com/example",
            headers={"X-Api-Key": "API_KEY"},
            params={"param1": "value1"},
            json=None,
        )

        # Assert that the response is processed correctly
        self.assertEqual(
            response, self.request_manager._process_response(mock_response)
        )

    def test_request_put(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        self.request_manager.session.put.return_value = mock_response

        # Set up the expected parameters and data
        method = "PUT"
        path = "example"
        params = {"param1": "value1"}
        data = None

        # Call the _request method
        response = self.request_manager._request(method, path, params, data)

        # Assert that the session's put method was called with the correct arguments
        self.request_manager.session.put.assert_called_once_with(
            "http://example.com/example",
            headers={"X-Api-Key": "API_KEY"},
            params={"param1": "value1"},
            json=None,
        )

        # Assert that the response is processed correctly
        self.assertEqual(
            response, self.request_manager._process_response(mock_response)
        )

    def test_request_delete(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        self.request_manager.session.delete.return_value = mock_response

        # Set up the expected parameters and data
        method = "DELETE"
        path = "example"
        params = {"param1": "value1"}
        data = None

        # Call the _request method
        response = self.request_manager._request(method, path, params, data)

        # Assert that the session's get method was called with the correct arguments
        self.request_manager.session.delete.assert_called_once_with(
            "http://example.com/example",
            headers={"X-Api-Key": "API_KEY"},
            params={"param1": "value1"},
            json=None,
        )

        # Assert that the response is processed correctly
        self.assertEqual(
            response, self.request_manager._process_response(mock_response)
        )

    def test_request_get_connection_error(self):
        # Mock the session object to raise a ConnectionError
        self.request_manager.session.get.side_effect = requests.ConnectionError

        # Set up the expected parameters and data
        method = "GET"
        path = "example"
        params = {"param1": "value1"}
        data = None

        # Call the _request method
        with self.assertRaises(ConnectionError) as e:
            self.request_manager._request(method, path, params, data)

        # Assert that the response is processed correctly
        self.assertEqual(
            str(e.exception), "Connection Refused while connecting to API."
        )

    def test_request_get_timeout_error(self):
        # Mock the session object to raise a Timeout
        self.request_manager.session.get.side_effect = requests.Timeout

        # Set up the expected parameters and data
        method = "GET"
        path = "example"
        params = {"param1": "value1"}
        data = None

        # Call the _request method
        with self.assertRaises(ConnectionTimeoutError) as e:
            self.request_manager._request(method, path, params, data)

        # Assert that the response is processed correctly
        self.assertEqual(str(e.exception), "Timeout occurred while connecting to API.")

    def test_process_response_200_json(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}

        # Call the _process_response method
        response = self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(response, {"key": "value"})

    def test_process_response_200_text(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = Exception
        mock_response.headers = {"content-type": "text/plain; charset=utf-8"}
        mock_response.text = "Some Text Response"

        # Call the _process_response method
        response = self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(response, "Some Text Response")

    def test_process_response_200_html(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = Exception
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.text = "<html><body>Some HTML Response</body></html>"

        # Call the _process_response method
        with self.assertRaises(InvalidResponseError) as e:
            self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(
            str(e.exception),
            "Invalid Response from server! Check if http://example.com is a valid API endpoint.",
        )

    def test_process_response_400(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.content = "Couldn't process the request."

        # Call the _process_response method
        with self.assertRaises(ConnectionError) as e:
            self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(
            str(e.exception),
            "Bad Request, possibly a bug. Couldn't process the request.",
        )

    def test_process_response_401(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 401

        # Call the _process_response method
        with self.assertRaises(ConnectionError) as e:
            self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(
            str(e.exception),
            "Unauthorized. Please ensure valid API Key is used: API_KEY",
        )

    def test_process_response_403(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 403

        # Call the _process_response method
        with self.assertRaises(ConnectionError) as e:
            self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(
            str(e.exception),
            "Access restricted. Please ensure API Key 'API_KEY' has correct permissions",
        )

    def test_process_response_404(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.url = "http://example.com/invalid"

        # Call the _process_response method
        with self.assertRaises(ConnectionError) as e:
            self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(
            str(e.exception), "Resource not found: http://example.com/invalid"
        )

    def test_process_response_405(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 405
        mock_response.url = "http://example.com/invalid"

        # Call the _process_response method
        with self.assertRaises(ConnectionError) as e:
            self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(
            str(e.exception), "The endpoint http://example.com/invalid is not allowed"
        )

    def test_process_response_500(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"message": "Server Error"}

        # Call the _process_response method
        with self.assertRaises(ConnectionError) as e:
            self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(str(e.exception), "Internal Server Error: Server Error")

    def test_process_response_500_no_message(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Some Error"
        mock_response.json.side_effect = KeyError

        # Call the _process_response method
        with self.assertRaises(ConnectionError) as e:
            self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(str(e.exception), "Internal Server Error: Some Error")

    def test_process_response_500_no_json(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Some Error"
        mock_response.json.side_effect = ValueError

        # Call the _process_response method
        with self.assertRaises(ConnectionError) as e:
            self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(str(e.exception), "Internal Server Error: Some Error")

    def test_process_response_500_no_json_or_text(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = ""
        mock_response.json.side_effect = ValueError

        # Call the _process_response method
        with self.assertRaises(ConnectionError) as e:
            self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(
            str(e.exception), "Internal Server Error: Unknown Error Occurred."
        )

    def test_process_response_502(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.url = "http://example.com/invalid"

        # Call the _process_response method
        with self.assertRaises(ConnectionError) as e:
            self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(
            str(e.exception),
            "Bad Gateway. Check if your server at http://example.com/invalid is accessible.",
        )

    def test_process_response_other(self):
        # Mock the response object
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.url = "http://example.com/invalid"

        # Call the _process_response method
        with self.assertRaises(ConnectionError) as e:
            self.request_manager._process_response(mock_response)

        # Assert that the response is processed correctly
        self.assertEqual(
            str(e.exception),
            "Invalid Host (http://example.com) or API Key (API_KEY), "
            "not a Radarr or Sonarr instance.",
        )
