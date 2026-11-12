"""Small helpers for the download flow."""

import asyncio
from random import randint
import re
import threading
import time

from quiv import JobCancelledError

from app_logger import ModuleLogger

# How long one slice of the wait between two downloads lasts. The stop
# event is checked between the slices, as `run_tool` does.
_POLL_SECONDS = 0.5


def extract_youtube_id(url: str) -> str | None:
    """Extract youtube video id from url. \n
    Args:
        url (str): URL of the youtube video. \n
    Returns:
        str|None: Youtube video id / None if invalid URL."""
    regex = re.compile(
        r"^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*"
    )
    match = regex.match(url)
    if match and len(match.group(2)) == 11:
        return match.group(2)
    else:
        return None


async def sleep_between_downloads(
    downloading_count: int,
    logger: ModuleLogger,
    stop_event: threading.Event | None = None,
) -> None:
    """Sleep for a calculated amount of time between downloads to avoid rate limiting. \n
    The wait can be 11 minutes. It stops when the stop event is set, so a
    stop of Trailarr or of the task does not wait for it. \n
    Args:
        downloading_count (int): Number of trailers being downloaded in this session. \n
        logger (ModuleLogger): Logger instance for logging. \n
        stop_event (threading.Event, optional=None): The stop event of the job. \n
    Returns:
        None
    Raises:
        JobCancelledError: If the stop event was set during the wait."""
    _sleep_for = randint(0, 60)  # Random sleep between 0 and 60 seconds
    # Increase the sleep time as more trailers are being downloaded
    if downloading_count < 10:
        _sleep_for += 120
    elif downloading_count < 50:
        _sleep_for += 240
    elif downloading_count < 100:
        _sleep_for += 360
    elif downloading_count < 200:
        _sleep_for += 420
    elif downloading_count < 500:
        _sleep_for += 540
    elif downloading_count < 1000:
        _sleep_for += 600
    logger.info(
        f"Trailarr waits {_sleep_for} seconds before the next download."
    )
    deadline = time.monotonic() + _sleep_for
    while (remaining := deadline - time.monotonic()) > 0:
        if stop_event is not None and stop_event.is_set():
            logger.info(
                "Trailarr stopped the wait before the next download. A stop"
                " was requested."
            )
            raise JobCancelledError(
                "The wait between two downloads was stopped: the job's stop"
                " event was set"
            )
        await asyncio.sleep(min(_POLL_SECONDS, remaining))
