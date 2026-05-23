import asyncio
from random import randint
import re

from app_logger import ModuleLogger


def extract_youtube_id(url: str) -> str | None:
    regex = re.compile(
        r"^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*"
    )
    match = regex.match(url)
    if match and len(match.group(2)) == 11:
        return match.group(2)
    return None


async def sleep_between_downloads(downloading_count: int, logger: ModuleLogger) -> None:
    _sleep_for = randint(0, 60)
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
