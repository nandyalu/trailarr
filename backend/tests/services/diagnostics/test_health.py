"""Tests for the system health checks (Onboarding track, Milestone B).

Wargame coverage:
  B1 — checks run on demand and cache; nothing runs at import/startup.
  B2 — cookie values never appear in status output or logs.
  B4 — a hanging or crashing check reports itself instead of breaking
       the run; every other check still completes.
"""

import asyncio
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from config.settings import app_settings
from services.diagnostics import cookies, health
from services.diagnostics.models import (
    HealthCheckResult,
    HealthReport,
    ProbeStatus,
)
from utils.error_classify import (
    classified_error,
    classify_ytdlp_error,
)

PKG = "services.diagnostics.health"

# One valid Netscape cookie row (tab-separated, 7 fields)
_FUTURE = "9999999999"
_PAST = "1000000000"


def _cookie_line(
    domain=".youtube.com",
    expiry=_FUTURE,
    name="SECRET_NAME",
    value="SECRET_VALUE",
):
    return f"{domain}\tTRUE\t/\tTRUE\t{expiry}\t{name}\t{value}"


class TestHealthFramework:

    @pytest.mark.asyncio
    async def test_all_checks_report_something(self):
        report = await health.run_health_checks()
        keys = {c.key for c in report.checks}
        assert {
            "ffmpeg",
            "hardware",
            "ytdlp",
            "app_version",
            "cookies",
            "connections",
            "images",
            "disk_space",
        } <= keys

    @pytest.mark.asyncio
    async def test_crashing_check_reports_itself(self):
        """B4: one broken check must not break the run."""

        async def _check_boom():
            raise RuntimeError("boom")

        result = await health._run_guarded(_check_boom)
        assert result.status == ProbeStatus.ERROR
        assert "boom" in result.detail

    @pytest.mark.asyncio
    async def test_hanging_check_times_out(self):
        """B4: a hung mount cannot hang the page."""

        async def _check_hang():
            await asyncio.sleep(999)

        with patch(f"{PKG}._CHECK_TIMEOUT_SECONDS", 0.05):
            result = await health._run_guarded(_check_hang)
        assert result.status == ProbeStatus.ERROR
        assert "did not finish" in result.detail

    @pytest.mark.asyncio
    async def test_report_is_cached_and_expires(self):
        """B1: on-demand with a daily cache."""
        report = await health.run_health_checks()
        assert health.get_cached_report() is report
        # An aged report no longer counts as fresh
        from datetime import datetime, timedelta, timezone

        report.checked_at = datetime.now(timezone.utc) - timedelta(hours=25)
        assert health.get_cached_report() is None


class TestCookiesCheckAndManager:

    def _write(self, tmp_path, content: str) -> str:
        path = str(tmp_path / "cookies.txt")
        with open(path, "w") as f:
            f.write(content)
        return path

    @pytest.mark.asyncio
    async def test_no_cookies_configured_is_skipped(self):
        with patch.object(type(app_settings), "yt_cookies_path", ""):
            result = await health._check_cookies()
        assert result.status == ProbeStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_valid_cookies_pass_without_leaking_values(self, tmp_path):
        path = self._write(tmp_path, _cookie_line() + "\n")
        with patch.object(type(app_settings), "yt_cookies_path", path):
            result = await health._check_cookies()
        assert result.status == ProbeStatus.OK
        # B2: no cookie name or value may appear anywhere in the output
        text = result.detail + result.remediation
        assert "SECRET_NAME" not in text
        assert "SECRET_VALUE" not in text

    @pytest.mark.asyncio
    async def test_expired_cookies_warn(self, tmp_path):
        path = self._write(tmp_path, _cookie_line(expiry=_PAST) + "\n")
        with patch.object(type(app_settings), "yt_cookies_path", path):
            result = await health._check_cookies()
        assert result.status == ProbeStatus.WARNING
        assert "expired" in result.detail

    @pytest.mark.asyncio
    async def test_non_youtube_cookies_warn(self, tmp_path):
        path = self._write(
            tmp_path, _cookie_line(domain=".example.com") + "\n"
        )
        with patch.object(type(app_settings), "yt_cookies_path", path):
            result = await health._check_cookies()
        assert result.status == ProbeStatus.WARNING
        assert "no youtube.com cookies" in result.detail

    def test_save_rejects_non_cookie_content(self):
        with pytest.raises(ValueError):
            cookies.save("this is not a cookies file")

    def test_save_writes_mode_600_and_status_hides_values(self):
        content = "# Netscape HTTP Cookie File\n" + _cookie_line() + "\n"
        try:
            status = cookies.save(content)
            saved = os.path.join(app_settings.app_data_dir, "cookies.txt")
            assert os.path.isfile(saved)
            assert (os.stat(saved).st_mode & 0o777) == 0o600
            assert app_settings.yt_cookies_path == saved
            assert status.youtube_cookies == 1
            # B2: write-only — the status carries no cookie values
            dumped = status.model_dump_json()
            assert "SECRET_NAME" not in dumped
            assert "SECRET_VALUE" not in dumped
        finally:
            cookies.delete()

    def test_delete_clears_setting_and_removes_managed_file(self):
        cookies.save("# Netscape\n" + _cookie_line() + "\n")
        saved = os.path.join(app_settings.app_data_dir, "cookies.txt")
        assert os.path.isfile(saved)
        status = cookies.delete()
        assert not os.path.isfile(saved)
        assert app_settings.yt_cookies_path == ""
        assert status.configured is False

    def test_delete_keeps_user_managed_files(self, tmp_path):
        """A user-provided path outside the config dir is never deleted."""
        path = self._write(tmp_path, _cookie_line() + "\n")
        with patch.object(type(app_settings), "yt_cookies_path", path):
            cookies.delete()
            assert os.path.isfile(path)


class TestErrorClassification:

    def test_sign_in_error_names_cookies_fix(self):
        raw = "ERROR: Sign in to confirm you're not a bot. Use --cookies"
        reason = classify_ytdlp_error(raw)
        assert reason is not None
        assert "cookies" in reason
        assert "Settings > Health" in reason

    def test_403_maps_to_rate_limit_reason(self):
        assert "rate-limiting" in classify_ytdlp_error(
            "HTTP Error 403: Forbidden"
        )

    def test_format_error_names_js_runtime(self):
        assert "JavaScript runtime" in classify_ytdlp_error(
            "ERROR: Requested format is not available"
        )

    def test_unknown_error_passes_through(self):
        assert classify_ytdlp_error("some brand new failure") is None
        assert (
            classified_error("some brand new failure")
            == "some brand new failure"
        )

    def test_classified_error_keeps_raw_line(self):
        raw = "yt-dlp said:\nERROR: HTTP Error 403: Forbidden"
        stored = classified_error(raw)
        assert stored.startswith("YouTube is rate-limiting")
        assert "[ERROR: HTTP Error 403: Forbidden]" in stored

    def test_attempt_record_stores_classified_reason(self):
        """The stored last_error leads with the plain-language reason."""
        import uuid

        import database.manager.downloadattempt as attempt_manager
        import database.manager.media as media_manager
        from database.models.media import MediaCreate
        from tests.services.diagnostics.test_connection_doctor import (
            _make_conn,
        )

        conn_id = _make_conn(f"Cls-{uuid.uuid4().hex[:8]}")
        media = media_manager.create(
            MediaCreate(
                connection_id=conn_id,
                arr_id=77001,
                is_movie=True,
                title="Classify Movie",
                txdb_id=f"cls-{uuid.uuid4().hex[:8]}",
            )
        )
        attempt = attempt_manager.record_failure(
            media.id, 1, "ERROR: Sign in to confirm you're not a bot"
        )
        assert attempt.last_error is not None
        assert attempt.last_error.startswith("YouTube requires a sign-in")


class TestChecksRunConcurrently:
    """The checks run together: the slowest one sets the wait."""

    @pytest.mark.asyncio
    async def test_slow_checks_do_not_add_up(self):
        async def _slow():
            await asyncio.sleep(0.3)
            return health.HealthCheckResult(
                key="slow", name="Slow", status=ProbeStatus.OK, detail=""
            )

        loop = asyncio.get_running_loop()
        started = loop.time()
        with patch.object(health, "_CHECK_TIMEOUT_SECONDS", 5):
            await asyncio.gather(
                *(health._run_guarded(_slow) for _ in range(6))
            )
        elapsed = loop.time() - started
        # Sequential would be ~1.8s; concurrent stays near one check.
        assert elapsed < 1.0, f"checks did not overlap ({elapsed:.2f}s)"

    @pytest.mark.asyncio
    async def test_a_check_may_have_a_longer_timeout(self):
        assert (
            health._CHECK_TIMEOUT_OVERRIDES["connections"]
            > health._CHECK_TIMEOUT_SECONDS
        )


class TestConnectionsCheckRunsTheDoctor:
    """The Health page collects the data itself instead of asking."""

    @pytest.mark.asyncio
    async def test_no_stored_reports_triggers_a_doctor_run(self):
        fake = [
            type(
                "R",
                (),
                {"status": "healthy", "connection_name": "Radarr"},
            )()
        ]
        with (
            patch.object(
                health.connection_doctor, "get_all_reports", return_value=[]
            ),
            patch.object(
                health, "_run_doctor_for_all", return_value=fake
            ) as ran,
        ):
            result = await health._check_connections()
        ran.assert_awaited()
        assert result.status == ProbeStatus.OK

    @pytest.mark.asyncio
    async def test_no_connections_says_so_without_instructions(self):
        with (
            patch.object(
                health.connection_doctor, "get_all_reports", return_value=[]
            ),
            patch.object(health, "_run_doctor_for_all", return_value=[]),
        ):
            result = await health._check_connections()
        assert result.status == ProbeStatus.SKIPPED
        assert "Add a Radarr" in result.detail
        # It must not tell the user to go and run the checks by hand.
        assert "run the checks" not in result.detail.lower()

    @pytest.mark.asyncio
    async def test_a_failing_doctor_does_not_break_the_check(self):
        conns = [type("C", (), {"id": 1, "name": "Radarr"})()]
        with (
            patch.object(
                health.connection_manager, "read_all", return_value=conns
            ),
            patch.object(
                health.connection_doctor,
                "run_doctor",
                side_effect=RuntimeError("boom"),
            ),
        ):
            assert await health._run_doctor_for_all() == []


class TestDiskSpace:
    """A full media disk is reported, not just the config volume."""

    @pytest.mark.asyncio
    async def test_low_media_space_warns(self, tmp_path):
        media = tmp_path / "movies"
        media.mkdir()

        def _usage(path):
            free = (
                100 << 30
                if str(path) == app_settings.app_data_dir
                else 1 << 30
            )
            return (
                os.terminal_size((0, 0))
                and type("U", (), {"total": 0, "used": 0, "free": free})()
            )

        with (
            patch.object(health, "_media_mounts", return_value=[str(media)]),
            patch.object(health.shutil, "disk_usage", side_effect=_usage),
        ):
            result = await health._check_disk_space()
        assert result.status == ProbeStatus.WARNING
        assert str(media) in result.detail
        assert "Free up space" in result.remediation

    @pytest.mark.asyncio
    async def test_healthy_when_everything_has_room(self, tmp_path):
        media = tmp_path / "movies"
        media.mkdir()
        big = type("U", (), {"total": 0, "used": 0, "free": 500 << 30})()
        with (
            patch.object(health, "_media_mounts", return_value=[str(media)]),
            patch.object(health.shutil, "disk_usage", return_value=big),
        ):
            result = await health._check_disk_space()
        assert result.status == ProbeStatus.OK

    def test_mounts_are_deduplicated_by_device(self, tmp_path):
        """Two folders on one disk are reported once."""
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        media = [
            type("M", (), {"folder_path": str(a)})(),
            type("M", (), {"folder_path": str(b)})(),
        ]
        with (
            patch.object(
                health.connection_doctor, "get_all_reports", return_value=[]
            ),
            patch.object(
                health.media_manager, "read_recent", return_value=media
            ),
            patch.object(health, "_config_device", return_value=None),
        ):
            mounts = health._media_mounts()
        assert len(mounts) == 1


class TestDiskSpaceNamesADisk:
    """The disk report must name a disk, not one title folder.

    The fallback took the folder of a recent media item, so the page said
    `'/media/movies/all/Varavu (2026) {imdb-tt37963237}': 3.9 TiB free`.
    The number was right and the name was not: that is one film, and it
    reads like a report about that film.
    """

    def test_a_library_root_wins_over_a_title_folder(self, tmp_path):
        root = tmp_path / "movies"
        title = root / "Varavu (2026) {imdb-tt37963237}"
        title.mkdir(parents=True)
        mapping = SimpleNamespace(path_from="/data/movies", path_to=str(root))
        connection = SimpleNamespace(path_mappings=[mapping])
        media = [type("M", (), {"folder_path": str(title)})()]

        with (
            patch.object(
                health.connection_doctor, "get_all_reports", return_value=[]
            ),
            patch.object(
                health.connection_manager, "read_all", return_value=[connection]
            ),
            patch.object(
                health.media_manager, "read_recent", return_value=media
            ),
            patch.object(health, "_config_device", return_value=None),
        ):
            mounts = health._media_mounts()

        assert mounts == [str(root)]

    def test_a_title_folder_is_reduced_to_its_disk(self, tmp_path):
        """With no connection to ask, the report names the mount."""
        title = tmp_path / "movies" / "Varavu (2026) {imdb-tt37963237}"
        title.mkdir(parents=True)
        media = [type("M", (), {"folder_path": str(title)})()]

        with (
            patch.object(
                health.connection_doctor, "get_all_reports", return_value=[]
            ),
            patch.object(
                health.connection_manager, "read_all", return_value=[]
            ),
            patch.object(
                health.media_manager, "read_recent", return_value=media
            ),
            patch.object(health, "_config_device", return_value=None),
        ):
            mounts = health._media_mounts()

        assert len(mounts) == 1
        assert mounts[0] != str(title), "the report named one film"
        assert str(title).startswith(mounts[0])

    def test_the_mount_point_stops_at_the_disk_boundary(self):
        """`_mount_point` walks up while the disk stays the same."""
        devices = {
            "/media/movies/all/Varavu (2026)": 42,
            "/media/movies/all": 42,
            "/media/movies": 42,
            "/media": 7,
            "/": 7,
        }

        def fake_stat(path):
            return SimpleNamespace(st_dev=devices[str(path)])

        with patch.object(health.os, "stat", side_effect=fake_stat):
            found = health._mount_point("/media/movies/all/Varavu (2026)")

        assert found == "/media/movies"

    def test_a_folder_that_cannot_be_read_is_given_back_as_it_is(self):
        with patch.object(health.os, "stat", side_effect=OSError("gone")):
            assert health._mount_point("/media/movies") == "/media/movies"


class TestErrorSignatures:
    """The failures users actually report are classified."""

    @pytest.mark.parametrize(
        "raw,expected_fragment",
        [
            (
                "ERROR: nsig extraction failed: Some formats may be missing",
                "player",
            ),
            ("WARNING: Signature extraction failed", "player"),
            ("ERROR: Failed to extract any player response", "player"),
            ("ERROR: [youtube] video is age-restricted", "age-restricted"),
            ("ERROR: HTTP Error 410: Gone", "unavailable"),
            ("ERROR: Sign in to confirm you're not a bot", "sign-in"),
        ],
    )
    def test_known_failures_get_a_reason(self, raw, expected_fragment):
        reason = classify_ytdlp_error(raw)
        assert reason is not None, f"unclassified: {raw}"
        assert expected_fragment in reason.lower()

    def test_unknown_errors_pass_through(self):
        assert classify_ytdlp_error("ERROR: something brand new") is None


class TestYoutubeTestTarget:
    """The live YouTube test must not rot, and must not blame the user.

    It used to ask for one hardcoded video id. That video was deleted, so
    every user's health page said their setup was broken. A search cannot
    go that way: it resolves to whatever YouTube has now, and it exercises
    the same extraction code — which is also the path Trailarr takes when
    it searches for a trailer.
    """

    @pytest.mark.asyncio
    async def test_a_working_setup_passes_on_the_first_target(self):
        with patch(
            f"{health.__name__}._run_ytdlp_simulate",
            new=AsyncMock(return_value=(0, "")),
        ) as run:
            result = await health.run_ytdlp_test()

        assert result.status == ProbeStatus.OK
        assert run.await_count == 1
        assert run.await_args.args[0].startswith("ytsearch1:")

    @pytest.mark.asyncio
    async def test_an_unreadable_video_makes_it_try_another(self):
        """Someone else deleting a video is not the user's problem."""
        with patch(
            f"{health.__name__}._run_ytdlp_simulate",
            new=AsyncMock(
                side_effect=[(1, "ERROR: This video is unavailable"), (0, "")]
            ),
        ) as run:
            result = await health.run_ytdlp_test()

        assert result.status == ProbeStatus.OK
        assert run.await_count == 2

    @pytest.mark.asyncio
    async def test_every_video_unreadable_warns_instead_of_failing(self):
        with patch(
            f"{health.__name__}._run_ytdlp_simulate",
            new=AsyncMock(return_value=(1, "ERROR: Video unavailable")),
        ):
            result = await health.run_ytdlp_test()

        assert result.status == ProbeStatus.WARNING
        assert "not about your setup" in result.detail

    @pytest.mark.asyncio
    async def test_a_sign_in_wall_is_still_an_error_straight_away(self):
        """The failure that matters must not be softened, or delayed by a
        retry that will hit the same wall."""
        with patch(
            f"{health.__name__}._run_ytdlp_simulate",
            new=AsyncMock(
                return_value=(1, "ERROR: Sign in to confirm you're not a bot")
            ),
        ) as run:
            result = await health.run_ytdlp_test()

        assert result.status == ProbeStatus.ERROR
        assert run.await_count == 1, "a sign-in wall is not worth retrying"
        assert result.remediation

    @pytest.mark.asyncio
    async def test_a_missing_ytdlp_is_an_error(self):
        with patch(
            f"{health.__name__}._run_ytdlp_simulate",
            new=AsyncMock(
                return_value=(1, "yt-dlp was not found at '/nope'.")
            ),
        ):
            result = await health.run_ytdlp_test()

        assert result.status == ProbeStatus.ERROR
