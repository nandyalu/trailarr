import asyncio
from random import randint
import re

from app_logger import ModuleLogger


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
    downloading_count: int, logger: ModuleLogger
) -> None:
    """Sleep for a calculated amount of time between downloads to avoid rate limiting. \n
    Args:
        downloading_count (int): Number of trailers being downloaded in this session. \n
        logger (ModuleLogger): Logger instance for logging. \n
    Returns:
        None"""
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
    logger.info(f"Sleeping for {_sleep_for} seconds before next download...")
    await asyncio.sleep(_sleep_for)
