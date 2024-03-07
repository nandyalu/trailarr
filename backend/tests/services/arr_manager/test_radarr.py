from unittest import TestCase
from unittest.mock import patch
from backend.services.arr_manager.radarr import RadarrManager


class TestRadarrManager(TestCase):

    @patch.object(RadarrManager, "_get_system_status")
    def test_get_system_status_success(self, mock_get_system_status):
        # Arrange
        mock_get_system_status.return_value = (
            "Radarr Connection Successful! Version: 1.0.0"
        )
        radarr_manager = RadarrManager("url", "api_key")

        # Act
        result = radarr_manager.get_system_status()

        # Assert
        mock_get_system_status.assert_called_once_with(radarr_manager.APPNAME)
        self.assertEqual(result, "Radarr Connection Successful! Version: 1.0.0")

    @patch.object(RadarrManager, "_get_system_status")
    def test_get_system_status_exception(self, mock_get_system_status):
        # Arrange
        mock_get_system_status.side_effect = Exception(
            "Invalid Host (url) or API Key (api_key), not a Radarr instance."
        )
        radarr_manager = RadarrManager("url", "api_key")

        # Act
        with self.assertRaises(Exception) as e:
            radarr_manager.get_system_status()

        # Assert
        mock_get_system_status.assert_called_once_with(radarr_manager.APPNAME)
        self.assertEqual(
            str(e.exception),
            "Invalid Host (url) or API Key (api_key), not a Radarr instance.",
        )
