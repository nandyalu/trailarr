from unittest import TestCase
from unittest.mock import patch
from backend.exceptions import InvalidResponseError
from backend.services.arr_manager.base import BaseArrManager


class TestBaseArrManager(TestCase):

    @patch.object(BaseArrManager, "_request")
    def test_api_version_success(self, mock_request):
        # Arrange
        mock_request.return_value = {"current": "v3"}
        arr_manager = BaseArrManager("url", "api_key")

        # Act
        result = arr_manager.api_version()

        # Assert
        self.assertEqual(result, "v3")

    @patch.object(BaseArrManager, "_request")
    def test_api_version_empty_response(self, mock_request):
        # Arrange
        mock_request.return_value = {}
        arr_manager = BaseArrManager("url", "api_key")

        # Act
        result = arr_manager.api_version()

        # Assert
        self.assertEqual(result, "")

    @patch.object(BaseArrManager, "_request")
    def test_api_version_non_dict_response(self, mock_request):
        # Arrange
        mock_request.return_value = "v3"
        arr_manager = BaseArrManager("url", "api_key")

        # Act
        result = arr_manager.api_version()

        # Assert
        self.assertEqual(result, "v3")

    @patch.object(BaseArrManager, "_request")
    def test_api_version_no_current_response(self, mock_request):
        # Arrange
        mock_request.return_value = {"abc": "abc"}
        arr_manager = BaseArrManager("url", "api_key")
        # mock_request.side_effect = Exception()

        # Act
        result = arr_manager.api_version()

        # Assert
        self.assertEqual(result, "")

    @patch.object(BaseArrManager, "_request")
    def test_api_version_no_response(self, mock_request):
        # Arrange
        mock_request.return_value = None
        arr_manager = BaseArrManager("url", "api_key")
        # mock_request.side_effect = Exception()

        # Act
        result = arr_manager.api_version()

        # Assert
        self.assertEqual(result, "")

    @patch.object(BaseArrManager, "_request")
    def test_get_system_status_success(self, mock_request):
        # Arrange
        mock_request.return_value = {"appName": "TestApp", "version": "1.0.0"}
        arr_manager = BaseArrManager("url", "api_key")

        # Act
        result = arr_manager._get_system_status("TestApp")

        # Assert
        self.assertEqual(result, "TestApp Connection Successful! Version: 1.0.0")

    @patch.object(BaseArrManager, "_request")
    def test_get_system_status_invalid_app_name(self, mock_request):
        # Arrange
        mock_request.return_value = {"appName": "WrongApp", "version": "1.0.0"}
        arr_manager = BaseArrManager("url", "api_key")

        # Act
        with self.assertRaises(InvalidResponseError) as e:
            arr_manager._get_system_status("TestApp")

        # Assert
        self.assertEqual(
            str(e.exception),
            "Invalid Host (url) or API Key (api_key), not a TestApp instance.",
        )

    @patch.object(BaseArrManager, "_request")
    def test_get_system_status_empty_app_name(self, mock_request):
        # Arrange
        mock_request.return_value = {"appName": "", "version": "1.0.0"}
        arr_manager = BaseArrManager("url", "api_key")

        # Act
        with self.assertRaises(InvalidResponseError) as e:
            arr_manager._get_system_status("TestApp")

        # Assert
        self.assertEqual(
            str(e.exception),
            "Invalid Host (url) or API Key (api_key), not a TestApp instance.",
        )

    @patch.object(BaseArrManager, "_request")
    def test_get_system_status_empty_version(self, mock_request):
        # Arrange
        mock_request.return_value = {"appName": "testApp", "version": ""}
        arr_manager = BaseArrManager("url", "api_key")

        # Act
        with self.assertRaises(InvalidResponseError) as e:
            arr_manager._get_system_status("TestApp")

        # Assert
        self.assertEqual(
            str(e.exception),
            "Invalid Host (url) or API Key (api_key), not a TestApp instance.",
        )

    @patch.object(BaseArrManager, "_request")
    def test_get_system_status_str_response(self, mock_request):
        # Arrange
        mock_request.return_value = "Version: v3"
        arr_manager = BaseArrManager("url", "api_key")

        # Act
        with self.assertRaises(InvalidResponseError) as e:
            arr_manager._get_system_status("TestApp")

        # Assert
        self.assertEqual(
            str(e.exception),
            "Version: v3",
        )

    @patch.object(BaseArrManager, "_request")
    def test_get_system_status_error_status(self, mock_request):
        # Arrange
        mock_request.side_effect = ValueError("Some Error message")
        arr_manager = BaseArrManager("url", "api_key")

        # Act
        with self.assertRaises(ValueError) as e:
            arr_manager._get_system_status("TestApp")

        # Assert
        self.assertEqual(str(e.exception), "Some Error message")

    @patch.object(BaseArrManager, "_request")
    def test_get_system_status_unknown_error(self, mock_request):
        # Arrange
        mock_request.return_value = 123  # not a dict or a string
        arr_manager = BaseArrManager("url", "api_key")

        # Act
        with self.assertRaises(InvalidResponseError) as e:
            arr_manager._get_system_status("TestApp")

        # Assert
        self.assertEqual(str(e.exception), "Unknown Error")

    @patch.object(BaseArrManager, "_request")
    def test_get_system_status_no_response(self, mock_request):
        # Arrange
        mock_request.return_value = None
        arr_manager = BaseArrManager("url", "api_key")

        # Act
        with self.assertRaises(InvalidResponseError) as e:
            arr_manager._get_system_status("TestApp")

        # Assert
        self.assertEqual(str(e.exception), "Unknown Error")

    @patch.object(BaseArrManager, "_request")
    def test_ping_success(self, mock_request):
        # Arrange
        mock_request.return_value = "Pong"
        arr_manager = BaseArrManager("url", "api_key")

        # Act
        result = arr_manager.ping()

        # Assert
        self.assertEqual(result, "Pong")

    @patch.object(BaseArrManager, "_request")
    def test_ping_error(self, mock_request):
        # Arrange
        mock_request.side_effect = Exception("Error message")
        arr_manager = BaseArrManager("url", "api_key")

        # Act & Assert
        with self.assertRaises(Exception) as e:
            arr_manager.ping()

        self.assertEqual(str(e.exception), "Error message")
