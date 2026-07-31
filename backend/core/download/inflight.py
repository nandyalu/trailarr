"""In-memory registry of in-flight trailer downloads (Phase 3).

DOWNLOADING is runtime state, never a stored status: this registry is the
single source of truth for "what is downloading right now". It is exposed
via `GET /api/v1/media/downloading` and pushed over the websocket with
`reload="downloading"`; the frontend overlays it on the computed status.
Being in-memory, it is empty on every boot by construction — a crash
mid-download can never leave a media item stuck in DOWNLOADING.
"""

import threading


class InflightRegistry:
    """Thread-safe map of media_id -> profile_id for in-flight downloads.

    Downloads run one at a time per task, but manual downloads can overlap
    the scheduled task, so entries for different media may coexist. If the
    same media is downloaded concurrently by two paths (manual + task), the
    later start overwrites and the earlier finish clears — the overlay
    self-corrects on the next broadcast; no locking beyond the dict guard.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._in_flight: dict[int, int] = {}

    def start(self, media_id: int, profile_id: int) -> None:
        with self._lock:
            self._in_flight[media_id] = profile_id

    def finish(self, media_id: int) -> None:
        with self._lock:
            self._in_flight.pop(media_id, None)

    def clear(self) -> None:
        with self._lock:
            self._in_flight.clear()

    def snapshot(self) -> dict[int, int]:
        with self._lock:
            return dict(self._in_flight)

    def is_downloading(self, media_id: int) -> bool:
        with self._lock:
            return media_id in self._in_flight


inflight_registry = InflightRegistry()
