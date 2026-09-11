"""The first-run setup guide — plans/track-onboarding-diagnostics.md, C.

Wargame C1 is the one that matters most: an installation that is already
in use must NEVER be sent to the guide. Someone who removes their last
connection is not a new user.
"""

from unittest.mock import MagicMock, patch

import pytest

from services import setup as setup_service

PKG = "services.setup"


@pytest.fixture
def settings():
    """Patch the settings object the service reads.

    Patching the property on the real object leaks: the service assigns to
    `setup_completed`, which puts a plain value in the instance dictionary
    that outlives the patch and shadows it in the next test.
    """
    with patch(f"{PKG}.app_settings") as fake:
        fake.setup_completed = False
        fake.downloads_enabled = True
        fake.tmdb_api_key = ""
        yield fake


class TestStatus:

    def test_a_fresh_installation_needs_the_guide(self, settings):
        with patch(f"{PKG}.counts", return_value=(0, 0)):
            status = setup_service.status()

        assert status.needed is True
        assert status.completed is False

    def test_a_completed_installation_does_not(self, settings):
        settings.setup_completed = True
        with patch(f"{PKG}.counts", return_value=(0, 0)):
            status = setup_service.status()

        assert status.needed is False

    def test_the_status_carries_what_the_guide_shows(self, settings):
        settings.downloads_enabled = False
        settings.tmdb_api_key = "k"
        with patch(f"{PKG}.counts", return_value=(2, 40)):
            status = setup_service.status()

        assert (status.connections, status.media) == (2, 40)
        assert status.downloads_enabled is False
        assert status.tmdb_key_set is True

    def test_a_broken_count_does_not_break_the_page(self, settings):
        """The guide is a helper. It must not be what stops the app."""
        with patch(f"{PKG}.connection_manager") as connections:
            connections.read_all.side_effect = OSError("database is locked")
            assert setup_service.counts()[0] == 0


class TestExistingInstallations:
    """Wargame C1."""

    def test_an_installation_with_a_connection_is_marked_set_up(
        self, settings
    ):
        with patch(f"{PKG}.counts", return_value=(1, 0)):
            assert setup_service.mark_existing_installation() is True
        assert settings.setup_completed is True

    def test_an_installation_with_media_is_marked_set_up(self, settings):
        """A Plex-only install can have media before a connection row is
        counted, and any media at all means someone used this already."""
        with patch(f"{PKG}.counts", return_value=(0, 12)):
            assert setup_service.mark_existing_installation() is True
        assert settings.setup_completed is True

    def test_an_empty_installation_is_left_alone(self, settings):
        with patch(f"{PKG}.counts", return_value=(0, 0)):
            assert setup_service.mark_existing_installation() is False
        assert settings.setup_completed is False

    def test_it_does_nothing_once_the_guide_is_behind_you(self, settings):
        settings.setup_completed = True
        with patch(f"{PKG}.counts", return_value=(5, 500)) as counts:
            assert setup_service.mark_existing_installation() is False
        counts.assert_not_called()

    def test_removing_the_last_connection_does_not_bring_the_guide_back(
        self, settings
    ):
        """The point of recording the decision instead of counting rows."""
        settings.setup_completed = True
        with patch(f"{PKG}.counts", return_value=(0, 0)):
            assert setup_service.status().needed is False


class TestCompleting:

    def test_finishing_records_it(self, settings):
        with patch(f"{PKG}.counts", return_value=(1, 1)):
            setup_service.complete()

        assert settings.setup_completed is True


class TestTheUpgradeWindow:
    """Wargame C1, the case the startup pass alone cannot cover.

    The pass runs a minute after start. An upgraded installation whose
    owner opens the web UI in that minute must not be sent to the guide,
    so the status itself records the decision.
    """

    def test_an_existing_installation_is_recorded_when_first_asked(
        self, settings
    ):
        with patch(f"{PKG}.counts", return_value=(3, 3704)):
            status = setup_service.status()

        assert status.needed is False
        assert settings.setup_completed is True

    def test_a_fresh_installation_is_still_offered_the_guide(self, settings):
        with patch(f"{PKG}.counts", return_value=(0, 0)):
            status = setup_service.status()

        assert status.needed is True
        assert settings.setup_completed is False
