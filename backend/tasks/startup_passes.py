"""Startup-pass registry — see plans/README.md → "Upgrade-safety rules".

Passes are idempotent boot-time reconciliation steps that must run (in
order) before dependent scheduled tasks. Completion is recorded per pass in
the `startuppass` table, which makes version-skipping upgrades safe by
construction: whatever passes a user skipped simply run on the first boot of
the new version. The download task gates on `downloads_ready()`.

Run policies:
- "always": runs every boot (convergent housekeeping); recorded on first
  successful completion for the audit trail and gating.
- "once": skipped on boots after its completion is recorded.
"""

import threading
from typing import Awaitable, Callable

from app_logger import ModuleLogger
import database.manager.startuppass as startuppass_manager
from tasks.download_attribution import run_attribution_pass

logger = ModuleLogger("StartupPasses")

PASS_ATTRIBUTE_DOWNLOADS = "attribute-downloads-v0.9.9"
PASS_FULL_SCAN_GUARD = "full-scan-before-downloads-v0.10"

# Passes the download engine depends on — it skips its run until these are
# recorded complete (upgrade guard against mass re-downloads on databases
# whose trailers were never tracked as download records).
DOWNLOADS_REQUIRED_PASSES = {
    PASS_ATTRIBUTE_DOWNLOADS,
    PASS_FULL_SCAN_GUARD,
}


async def _pass_attribute_downloads() -> None:
    """v0.9.9 attribution pass: claim unattributed downloads. Idempotent and
    convergent — runs every boot so profiles added later can claim older
    downloads."""
    await run_attribution_pass()


async def _pass_full_scan_guard() -> None:
    """Ensure the downloads table can be trusted before the downloads-driven
    engine ever runs: run one full disk scan so trailers already on disk are
    recorded as download rows.

    This matters for upgrades from versions before download tracking —
    without the scan, the engine would re-download trailers that already
    exist. Phase 5 dropped the stored mirror flags, so there is no cheap
    pre-check anymore: an unrecorded pass always scans once. On a fresh
    install the library is empty and the scan is a no-op.

    Recorded complete after one scan attempt even if some folders are
    unreachable: downloads must not be blocked forever, and later scheduled
    scans keep reconciling the remainder.
    """
    logger.info(
        "Trailarr runs one full disk scan before the first download."
        " The scan records the trailers that are already on disk."
    )
    # Import here to avoid a circular import (files_scan → profiles utils)
    from tasks.files_scan import scan_all_media_folders

    await scan_all_media_folders()


# Ordered registry — order is the dependency order.
REGISTRY: list[tuple[str, Callable[[], Awaitable[None]], str]] = [
    (PASS_ATTRIBUTE_DOWNLOADS, _pass_attribute_downloads, "always"),
    (PASS_FULL_SCAN_GUARD, _pass_full_scan_guard, "once"),
]


async def run_startup_passes(
    _stop_event: threading.Event | None = None,
) -> None:
    """Run unrecorded (and always-policy) passes in registry order.

    A pass failure stops the remaining passes — order is a dependency
    guarantee, and a later pass must not run on a foundation its
    predecessor failed to establish. The next boot retries.
    """
    completed = startuppass_manager.completed_names()
    for name, func, policy in REGISTRY:
        if _stop_event and _stop_event.is_set():
            logger.info("Trailarr stopped the startup passes. A stop was requested.")
            return
        recorded = name in completed
        if recorded and policy == "once":
            continue
        logger.info(f"Trailarr runs the startup pass '{name}'.")
        try:
            await func()
        except Exception as e:
            logger.exception(
                f"The startup pass '{name}' failed: {e}. Trailarr skipped"
                " the passes after it. They run again at the next start."
            )
            return
        if not recorded:
            startuppass_manager.mark_completed(name)
            logger.info(f"Trailarr completed the startup pass '{name}' and recorded it.")


def downloads_ready() -> bool:
    """Whether the download engine's required startup passes have completed
    on this database (possibly on an earlier boot)."""
    return DOWNLOADS_REQUIRED_PASSES <= startuppass_manager.completed_names()
