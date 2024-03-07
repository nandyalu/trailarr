from unittest import TestCase
from unittest.mock import patch
from backend.services.arr_manager.sonarr import SonarrManager


class TestSonarrManager(TestCase):

    @patch.object(SonarrManager, "_get_system_status")
    def test_get_system_status_success(self, mock_get_system_status):
        # Arrange
        mock_get_system_status.return_value = (
            "Sonarr Connection Successful! Version: 1.0.0"
        )
        sonarr_manager = SonarrManager("url", "api_key")

        # Act
        result = sonarr_manager.get_system_status()

        # Assert
        mock_get_system_status.assert_called_once_with(sonarr_manager.APPNAME)
        self.assertEqual(result, "Sonarr Connection Successful! Version: 1.0.0")

    @patch.object(SonarrManager, "_get_system_status")
    def test_get_system_status_exception(self, mock_get_system_status):
        # Arrange
        mock_get_system_status.side_effect = Exception(
            "Invalid Host (url) or API Key (api_key), not a Sonarr instance."
        )
        sonarr_manager = SonarrManager("url", "api_key")

        # Act
        with self.assertRaises(Exception) as e:
            sonarr_manager.get_system_status()

        # Assert
        mock_get_system_status.assert_called_once_with(sonarr_manager.APPNAME)
        self.assertEqual(
            str(e.exception),
            "Invalid Host (url) or API Key (api_key), not a Sonarr instance.",
        )
