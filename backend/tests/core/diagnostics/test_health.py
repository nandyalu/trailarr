"""Tests for the system health checks (Onboarding track, Milestone B).

Wargame coverage:
  B1 — checks run on demand and cache; nothing runs at import/startup.
  B2 — cookie values never appear in status output or logs.
  B4 — a hanging or crashing check reports itself instead of breaking
       the run; every other check still completes.
"""

import asyncio
import os
from unittest.mock import patch

import pytest

from config.settings import app_settings
from core.diagnostics import cookies, health
from core.diagnostics.models import ProbeStatus
from core.download.error_classify import (
    classified_error,
    classify_ytdlp_error,
)

PKG = "core.diagnostics.health"

# One valid Netscape cookie row (tab-separated, 7 fields)
_FUTURE = "9999999999"
_PAST = "1000000000"


def _cookie_line(domain=".youtube.com", expiry=_FUTURE, name="SECRET_NAME", value="SECRET_VALUE"):
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
            saved = os.path.join(
                app_settings.app_data_dir, "cookies.txt"
            )
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
        assert classified_error("some brand new failure") == (
            "some brand new failure"
        )

    def test_classified_error_keeps_raw_line(self):
        raw = "yt-dlp said:\nERROR: HTTP Error 403: Forbidden"
        stored = classified_error(raw)
        assert stored.startswith("YouTube is rate-limiting")
        assert "[ERROR: HTTP Error 403: Forbidden]" in stored

    def test_attempt_record_stores_classified_reason(self):
        """The stored last_error leads with the plain-language reason."""
        import uuid

        import core.base.database.manager.downloadattempt as attempt_manager
        import core.base.database.manager.media as media_manager
        from core.base.database.models.media import MediaCreate
        from tests.core.diagnostics.test_connection_doctor import _make_conn

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
