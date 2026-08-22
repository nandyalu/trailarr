"""System health checks — Milestone B of the Onboarding & Diagnostics track.

A small checks framework: every check is an async function with a hard
per-check timeout, so one hung mount or one offline service can never
hang the page or crash the app (wargame B4). The checks run together,
not one after the other, so the slowest check sets the wait, not the
sum of them. Checks run only on demand from the Health page — never at
startup (B1) — and the last report is cached in memory for a day, so
the page always has something to show.

The yt-dlp live test is NOT part of the normal run: it contacts YouTube,
so it runs only when the user asks (B3), and its result is cached for
24 hours.

NOTE (phase-07 move map): this package moves to `services/diagnostics/`
in the backend reorganization.
"""

import asyncio
import os
import shutil
from datetime import datetime, timedelta, timezone

from app_logger import ModuleLogger
from config.settings import app_settings
import core.base.database.manager.connection as connection_manager
import core.base.database.manager.media as media_manager
from core.diagnostics import connection_doctor
from core.diagnostics.models import (
    HealthCheckResult,
    HealthReport,
    ProbeStatus,
)

logger = ModuleLogger("HealthChecks")

DOCS_BASE = "https://nandyalu.github.io/trailarr/"
DOCS_HW_ACCEL = (
    DOCS_BASE + "getting-started/02-installation/hardware-acceleration/"
)
DOCS_COOKIES = DOCS_BASE + "user-guide/settings/health/"
DOCS_CONNECTIONS = DOCS_BASE + "user-guide/settings/connections/"

# Free-space thresholds. Trailers are small, but a disk this low is
# about to fail a download with an error that does not mention space.
_CONFIG_LOW_SPACE = 1 << 30  # 1 GiB
_MEDIA_LOW_SPACE = 5 << 30  # 5 GiB
_MAX_MEDIA_MOUNTS = 5

_CHECK_TIMEOUT_SECONDS = 10
# The connections check runs the Connection Doctor when no report is
# stored, and that talks to Radarr/Sonarr/Plex over the network.
_CHECK_TIMEOUT_OVERRIDES = {"connections": 30}
_REPORT_TTL = timedelta(hours=24)
_YTDLP_TEST_TTL = timedelta(hours=24)

# yt-dlp's long-standing designated test video (also used by its own CI)
_YTDLP_TEST_VIDEO = "https://www.youtube.com/watch?v=BaW_jenozKc"

_report: HealthReport | None = None
_ytdlp_test_result: HealthCheckResult | None = None


def get_cached_report() -> HealthReport | None:
    """Return the cached report while it is fresh (24h), else None."""
    if _report is None:
        return None
    if datetime.now(timezone.utc) - _report.checked_at > _REPORT_TTL:
        return None
    return _report


async def run_health_checks() -> HealthReport:
    """Run every check (except the yt-dlp live test) and cache the report."""
    global _report
    report = HealthReport()
    checks = [
        _check_ffmpeg,
        _check_hardware,
        _check_ytdlp,
        _check_app_version,
        _check_cookies,
        _check_connections,
        _check_images,
        _check_disk_space,
    ]
    # Run every check at once: a hung mount costs its own timeout, not
    # everyone else's wait as well.
    report.checks.extend(
        await asyncio.gather(*(_run_guarded(check) for check in checks))
    )
    if _ytdlp_test_result is not None:
        report.checks.append(_ytdlp_test_result)
    report.finalize()
    _report = report
    logger.info(f"Health checks complete: {report.status}")
    return report


async def _run_guarded(check) -> HealthCheckResult:
    """Run one check with a hard timeout; a broken check reports itself."""
    key = check.__name__.replace("_check_", "")
    timeout = _CHECK_TIMEOUT_OVERRIDES.get(key, _CHECK_TIMEOUT_SECONDS)
    try:
        return await asyncio.wait_for(check(), timeout=timeout)
    except asyncio.TimeoutError:
        return HealthCheckResult(
            key=key,
            name=key.replace("_", " ").title(),
            status=ProbeStatus.ERROR,
            detail=(
                f"The check did not finish in {timeout} seconds."
                " A mount or a service may be hanging."
            ),
        )
    except Exception as e:
        logger.error(f"Health check '{key}' failed: {e}")
        return HealthCheckResult(
            key=key,
            name=key.replace("_", " ").title(),
            status=ProbeStatus.ERROR,
            detail=f"The check failed: {e}",
        )


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


async def _run_command(*args: str) -> tuple[int, str]:
    """Run a command and return (returncode, first line of output)."""
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    output, _ = await process.communicate()
    first_line = output.decode(errors="replace").splitlines()
    return process.returncode or 0, first_line[0] if first_line else ""


async def _check_ffmpeg() -> HealthCheckResult:
    path = app_settings.ffmpeg_path
    try:
        code, line = await _run_command(path, "-version")
    except FileNotFoundError:
        return HealthCheckResult(
            key="ffmpeg",
            name="FFmpeg",
            status=ProbeStatus.ERROR,
            detail=f"FFmpeg was not found at '{path}'.",
            remediation=(
                "Install FFmpeg, or set FFMPEG_PATH to the full path of"
                " the executable."
            ),
        )
    if code != 0:
        return HealthCheckResult(
            key="ffmpeg",
            name="FFmpeg",
            status=ProbeStatus.ERROR,
            detail=f"'{path} -version' failed: {line}",
            remediation="Reinstall FFmpeg or fix FFMPEG_PATH.",
        )
    return HealthCheckResult(
        key="ffmpeg",
        name="FFmpeg",
        status=ProbeStatus.OK,
        detail=line,
    )


async def _check_hardware() -> HealthCheckResult:
    """Surface the GPU detection that is otherwise invisible."""
    vendors = [
        (
            "NVIDIA",
            app_settings.gpu_available_nvidia,
            app_settings.gpu_enabled_nvidia,
        ),
        (
            "Intel",
            app_settings.gpu_available_intel,
            app_settings.gpu_enabled_intel,
        ),
        ("AMD", app_settings.gpu_available_amd, app_settings.gpu_enabled_amd),
    ]
    found = [
        f"{name} ({'enabled' if enabled else 'disabled in settings'})"
        for name, available, enabled in vendors
        if available
    ]
    if found:
        return HealthCheckResult(
            key="hardware",
            name="Hardware acceleration",
            status=ProbeStatus.OK,
            detail="Detected: " + ", ".join(found) + ".",
            docs_url=DOCS_HW_ACCEL,
        )
    return HealthCheckResult(
        key="hardware",
        name="Hardware acceleration",
        status=ProbeStatus.SKIPPED,
        detail=(
            "No GPU detected. Conversions use the CPU, which works but"
            " is slower."
        ),
        remediation=(
            "To use a GPU, pass the device to the container and check"
            " the hardware acceleration guide."
        ),
        docs_url=DOCS_HW_ACCEL,
    )


async def _check_ytdlp() -> HealthCheckResult:
    version = app_settings.ytdlp_version
    channel = "nightly" if app_settings.ytdlp_nightly else "stable"
    if not version or version == "0.0.0":
        return HealthCheckResult(
            key="ytdlp",
            name="yt-dlp",
            status=ProbeStatus.ERROR,
            detail="yt-dlp was not found.",
            remediation=(
                "Install yt-dlp, or set YTDLP_PATH to the full path of"
                " the executable."
            ),
        )
    if app_settings.update_available_ytdlp:
        return HealthCheckResult(
            key="ytdlp",
            name="yt-dlp",
            status=ProbeStatus.WARNING,
            detail=(
                f"Version {version} ({channel} channel) — a newer"
                " version is available."
            ),
            remediation=(
                "YouTube changes often break old versions. Update the"
                " Trailarr image (Docker) or run the updater (bare"
                " metal) to get the newest yt-dlp."
            ),
        )
    return HealthCheckResult(
        key="ytdlp",
        name="yt-dlp",
        status=ProbeStatus.OK,
        detail=f"Version {version} ({channel} channel).",
    )


async def _check_app_version() -> HealthCheckResult:
    version = app_settings.version
    if app_settings.update_available:
        return HealthCheckResult(
            key="app_version",
            name="Trailarr version",
            status=ProbeStatus.WARNING,
            detail=f"Version {version} — a newer version is available.",
            remediation="Update the container image to the latest tag.",
        )
    return HealthCheckResult(
        key="app_version",
        name="Trailarr version",
        status=ProbeStatus.OK,
        detail=f"Version {version}.",
    )


async def _check_cookies() -> HealthCheckResult:
    path = app_settings.yt_cookies_path
    if not path:
        return HealthCheckResult(
            key="cookies",
            name="YouTube cookies",
            status=ProbeStatus.SKIPPED,
            detail=(
                "No cookies file is set up. Cookies are needed only"
                " when YouTube asks for a sign-in or rate-limits"
                " downloads."
            ),
            docs_url=DOCS_COOKIES,
        )
    if not os.path.isfile(path):
        return HealthCheckResult(
            key="cookies",
            name="YouTube cookies",
            status=ProbeStatus.ERROR,
            detail=f"The cookies file '{path}' does not exist.",
            remediation=(
                "Upload a new cookies file on the Health page, or clear"
                " the setting."
            ),
            docs_url=DOCS_COOKIES,
        )
    from core.diagnostics.cookies import _file_stats

    youtube, expired = _file_stats(path)
    if youtube == 0:
        return HealthCheckResult(
            key="cookies",
            name="YouTube cookies",
            status=ProbeStatus.WARNING,
            detail=(
                f"'{path}' contains no youtube.com cookies. yt-dlp"
                " cannot use it for YouTube."
            ),
            remediation=(
                "Export cookies while signed in to youtube.com and"
                " upload the file again."
            ),
            docs_url=DOCS_COOKIES,
        )
    if expired:
        return HealthCheckResult(
            key="cookies",
            name="YouTube cookies",
            status=ProbeStatus.WARNING,
            detail=f"{expired} of {youtube} youtube.com cookies are expired.",
            remediation="Export a fresh cookies file and upload it again.",
            docs_url=DOCS_COOKIES,
        )
    return HealthCheckResult(
        key="cookies",
        name="YouTube cookies",
        status=ProbeStatus.OK,
        detail=f"{youtube} youtube.com cookies, none expired.",
        docs_url=DOCS_COOKIES,
    )


async def _run_doctor_for_all() -> list:
    """Run the Connection Doctor for every connection, all at once.

    Used when no report is stored yet (a fresh install, or the first
    Health page visit). A connection that fails to check is skipped:
    the health check reports on what it could get.
    """
    try:
        connections = connection_manager.read_all()
    except Exception as e:
        logger.error(f"Could not read the connections: {e}")
        return []
    if not connections:
        return []
    results = await asyncio.gather(
        *(connection_doctor.run_doctor(c.id) for c in connections),
        return_exceptions=True,
    )
    reports = []
    for connection, result in zip(connections, results):
        if isinstance(result, BaseException):
            logger.error(f"Doctor failed for '{connection.name}': {result}")
            continue
        reports.append(result)
    return reports


async def _check_connections() -> HealthCheckResult:
    reports = connection_doctor.get_all_reports()
    if not reports:
        # Never tell the user to go and collect this themselves -- the
        # doctor is one call away, so run it for every connection.
        reports = await _run_doctor_for_all()
    if not reports:
        return HealthCheckResult(
            key="connections",
            name="Connections",
            status=ProbeStatus.SKIPPED,
            detail=(
                "No connections are set up yet. Add a Radarr, Sonarr,"
                " or Plex connection to start."
            ),
            docs_url=DOCS_CONNECTIONS,
        )
    issues = [r for r in reports if r.status != "healthy"]
    if issues:
        names = ", ".join(r.connection_name for r in issues)
        return HealthCheckResult(
            key="connections",
            name="Connections",
            status=ProbeStatus.ERROR,
            detail=(
                f"{len(issues)} of {len(reports)} connection(s) report"
                f" issues: {names}."
            ),
            remediation=(
                "Open the Connections page and follow the Connection"
                " Doctor's fixes."
            ),
            docs_url=DOCS_CONNECTIONS,
        )
    return HealthCheckResult(
        key="connections",
        name="Connections",
        status=ProbeStatus.OK,
        detail=f"All {len(reports)} checked connection(s) are healthy.",
        docs_url=DOCS_CONNECTIONS,
    )


async def _check_images() -> HealthCheckResult:
    images_dir = os.path.join(app_settings.app_data_dir, "web", "images")
    if not os.path.isdir(images_dir):
        return HealthCheckResult(
            key="images",
            name="Image cache",
            status=ProbeStatus.WARNING,
            detail=f"The images folder '{images_dir}' does not exist yet.",
            remediation=(
                "It is created on the first image refresh. Run the"
                " Image Refresh task if posters do not show."
            ),
        )
    test_file = os.path.join(images_dir, ".trailarr-write-test")
    try:
        with open(test_file, "w"):
            pass
        os.remove(test_file)
    except OSError as e:
        return HealthCheckResult(
            key="images",
            name="Image cache",
            status=ProbeStatus.ERROR,
            detail=f"Cannot write to '{images_dir}': {e}",
            remediation=(
                "Fix the permissions on the config volume so Trailarr"
                " can store posters."
            ),
        )
    count = sum(1 for _ in os.scandir(images_dir))
    return HealthCheckResult(
        key="images",
        name="Image cache",
        status=ProbeStatus.OK,
        detail=f"'{images_dir}' is writable ({count} entries).",
    )


def _format_size(size: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PiB"


async def _check_disk_space() -> HealthCheckResult:
    """Free space on the config volume and on every media mount.

    A full media disk is the painful one: downloads fail with a raw
    FFmpeg or yt-dlp error and nothing says the disk is full. Each
    distinct mount is reported once, and a low one is a warning.
    """
    parts: list[str] = []
    status = ProbeStatus.OK
    remediations: list[str] = []

    try:
        usage = shutil.disk_usage(app_settings.app_data_dir)
        parts.append(f"Config: {_format_size(usage.free)} free")
        if usage.free < _CONFIG_LOW_SPACE:
            status = ProbeStatus.WARNING
            remediations.append(
                "The config volume is nearly full. The database and"
                " logs need free space to work."
            )
    except OSError as e:
        status = ProbeStatus.WARNING
        parts.append(f"Config: cannot be read ({e})")

    low_mounts: list[str] = []
    for folder in _media_mounts():
        try:
            usage = shutil.disk_usage(folder)
        except OSError:
            parts.append(f"'{folder}': not reachable")
            status = ProbeStatus.WARNING
            remediations.append(
                f"The storage behind '{folder}' does not answer. Check"
                " the mount."
            )
            continue
        parts.append(f"'{folder}': {_format_size(usage.free)} free")
        if usage.free < _MEDIA_LOW_SPACE:
            low_mounts.append(folder)
    if low_mounts:
        status = ProbeStatus.WARNING
        remediations.append(
            "Free up space on "
            + ", ".join(f"'{m}'" for m in low_mounts)
            + ". Trailers cannot be saved on a full disk."
        )

    return HealthCheckResult(
        key="disk_space",
        name="Disk space",
        status=status,
        detail=". ".join(parts) + "." if parts else "No storage to check.",
        remediation=" ".join(remediations),
    )


def _config_device() -> int | None:
    """Device id of the config volume, or None when it cannot be read."""
    try:
        return os.stat(app_settings.app_data_dir).st_dev
    except OSError:
        return None


def _media_mounts() -> list[str]:
    """One existing folder per distinct media mount.

    Media libraries are commonly split over several disks (movies on
    one, TV on another). Reporting only the first one hides a full
    second disk, so every distinct device gets its own entry. Folders
    checked by the Connection Doctor come first, because those are the
    library roots; recent media folders fill in the rest.
    """
    candidates: list[str] = []
    for report in connection_doctor.get_all_reports():
        for probe in report.probes:
            if probe.kind != "permissions":
                continue
            # "Write permissions: /media/movies" names the folder
            _, _, folder = probe.name.partition(": ")
            if folder:
                candidates.append(folder)
    try:
        for media in media_manager.read_recent(limit=50):
            if media.folder_path:
                candidates.append(media.folder_path)
    except Exception:
        pass

    mounts: list[str] = []
    seen_devices: set[int] = set()
    for folder in candidates:
        if not folder or not os.path.isdir(folder):
            continue
        try:
            device = os.stat(folder).st_dev
        except OSError:
            continue
        if device in seen_devices:
            continue
        # The config volume is reported separately.
        if device == _config_device():
            continue
        seen_devices.add(device)
        mounts.append(folder)
        if len(mounts) >= _MAX_MEDIA_MOUNTS:
            break
    return mounts


# ---------------------------------------------------------------------------
# yt-dlp live test (user-triggered only — B3)
# ---------------------------------------------------------------------------


def get_ytdlp_test_result() -> HealthCheckResult | None:
    """Return the cached live-test result while it is fresh (24h)."""
    if _ytdlp_test_result is None:
        return None
    age = datetime.now(timezone.utc) - _ytdlp_test_result.checked_at
    if age > _YTDLP_TEST_TTL:
        return None
    return _ytdlp_test_result


async def run_ytdlp_test() -> HealthCheckResult:
    """Contact YouTube once with yt-dlp and report whether it works.

    Uses --simulate: it exercises the extraction path (the part that
    fails with sign-in and bot checks) and downloads nothing.
    """
    global _ytdlp_test_result
    args = [app_settings.ytdlp_path, "--simulate", "--quiet"]
    if app_settings.yt_cookies_path:
        args += ["--cookies", app_settings.yt_cookies_path]
    args.append(_YTDLP_TEST_VIDEO)
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        output, _ = await asyncio.wait_for(process.communicate(), timeout=60)
        code = process.returncode or 0
        text = output.decode(errors="replace").strip()
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()  # reap it, do not leave a zombie behind
        code, text = 1, "The test did not finish in 60 seconds."
    except FileNotFoundError:
        code, text = 1, f"yt-dlp was not found at '{app_settings.ytdlp_path}'."
    if code == 0:
        result = HealthCheckResult(
            key="ytdlp_test",
            name="YouTube download test",
            status=ProbeStatus.OK,
            detail="yt-dlp reached YouTube and read a test video.",
        )
    else:
        from core.download.error_classify import classify_ytdlp_error

        classified = classify_ytdlp_error(text)
        last_line = text.splitlines()[-1] if text else "unknown error"
        result = HealthCheckResult(
            key="ytdlp_test",
            name="YouTube download test",
            status=ProbeStatus.ERROR,
            detail=classified or f"The test failed: {last_line}",
            remediation=(
                "Set up a cookies file on this page if YouTube asks for"
                " a sign-in. Update yt-dlp if it is outdated."
            ),
            docs_url=DOCS_COOKIES,
        )
    _ytdlp_test_result = result
    _refresh_report_test_entry(result)
    return result


def _refresh_report_test_entry(result: HealthCheckResult) -> None:
    """Reflect the newest live-test result in the cached report."""
    if _report is None:
        return
    _report.checks = [c for c in _report.checks if c.key != "ytdlp_test"] + [
        result
    ]
    _report.finalize()
