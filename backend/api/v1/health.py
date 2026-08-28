from fastapi import APIRouter, HTTPException, status

from api.v1.models import ErrorResponse
from services.diagnostics import cookies, health
from services.diagnostics.models import (
    CookiesStatus,
    CookiesUpload,
    HealthCheckResult,
    HealthReport,
)

health_router = APIRouter(prefix="/health", tags=["Health"])


@health_router.get("/checks")
async def get_health_checks() -> HealthReport:
    """The system health report.

    Returns the cached report when it is under 24 hours old, else runs
    the checks. The checks never run at startup. They run only from here.
    """
    cached = health.get_cached_report()
    if cached is not None:
        return cached
    return await health.run_health_checks()


@health_router.post("/checks/run")
async def run_health_checks() -> HealthReport:
    """Run all health checks now and return the fresh report."""
    return await health.run_health_checks()


@health_router.post("/checks/ytdlp-test")
async def run_ytdlp_test(force: bool = False) -> HealthCheckResult:
    """Test that yt-dlp can read a video from YouTube.

    Contacts YouTube once, so the UI asks for confirmation first. The
    result is cached for 24 hours. Pass ``force=true`` to re-run early.
    """
    if not force:
        cached = health.get_ytdlp_test_result()
        if cached is not None:
            return cached
    return await health.run_ytdlp_test()


@health_router.get("/cookies")
async def get_cookies_status() -> CookiesStatus:
    """Status of the YouTube cookies file. Cookie values are never returned."""
    return cookies.get_status()


@health_router.post(
    "/cookies",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Content is not a cookies file",
        },
    },
)
async def upload_cookies(upload: CookiesUpload) -> CookiesStatus:
    """Store an uploaded/pasted cookies.txt and point yt-dlp at it.

    The file is saved in the config folder with mode 600. The content
    is write-only: no endpoint returns it, and it is never logged.
    """
    try:
        return cookies.save(upload.content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@health_router.delete("/cookies")
async def delete_cookies() -> CookiesStatus:
    """Remove the cookies file from the configuration."""
    return cookies.delete()
