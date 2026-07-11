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
import core.base.database.manager.startuppass as startuppass_manager
from core.tasks.download_attribution import (
    count_untracked_trailer_media,
    run_attribution_pass,
)

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
    """v0.9.9 attribution pass: claim unattributed downloads, heal stale
    trailer flags, report health. Idempotent and convergent — runs every
    boot so profiles added later can claim older downloads."""
    await run_attribution_pass()


async def _pass_full_scan_guard() -> None:
    """Ensure the downloads table can be trusted before the downloads-driven
    engine ever runs: if any media claims a trailer (trailer_exists=True)
    with no active download record — typical for upgrades from versions
    before download tracking — run one full disk scan first.

    Recorded complete after one scan attempt even if some media remain
    untracked (e.g. unreachable network folders): downloads must not be
    blocked forever, and the attribution health report keeps warning about
    the remainder on every boot.
    """
    untracked, total = count_untracked_trailer_media()
    if untracked == 0:
        logger.info(
            "Download records are consistent with trailer flags"
            f" ({total} media with trailers) — no pre-download scan needed."
        )
        return
    logger.warning(
        f"{untracked} of {total} media with trailer_exists=True have no"
        " tracked download record — running a full disk scan before the"
        " first download run to avoid re-downloading existing trailers."
    )
    # Import here to avoid a circular import (files_scan → profiles utils)
    from core.tasks.files_scan import scan_all_media_folders

    await scan_all_media_folders()
    remaining, _ = count_untracked_trailer_media()
    if remaining:
        logger.warning(
            f"{remaining} media still have untracked trailers after the"
            " scan (unreachable folders?). Downloads will proceed; the"
            " attribution health report will keep flagging these."
        )


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
            logger.info("Stop event set, aborting startup passes.")
            return
        recorded = name in completed
        if recorded and policy == "once":
            continue
        logger.info(f"Running startup pass '{name}'...")
        try:
            await func()
        except Exception as e:
            logger.exception(
                f"Startup pass '{name}' failed: {e} — remaining passes"
                " skipped; they will retry on next startup."
            )
            return
        if not recorded:
            startuppass_manager.mark_completed(name)
            logger.info(f"Startup pass '{name}' completed and recorded.")


def downloads_ready() -> bool:
    """Whether the download engine's required startup passes have completed
    on this database (possibly on an earlier boot)."""
    return DOWNLOADS_REQUIRED_PASSES <= startuppass_manager.completed_names()
