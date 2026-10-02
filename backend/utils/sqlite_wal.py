"""Empty the write-ahead log (WAL) of a SQLite database.

`PRAGMA wal_checkpoint(TRUNCATE)` copies the WAL into the database and
cuts the WAL file to zero bytes. When another connection holds a read or
write transaction, SQLite cannot finish, but it does not raise. It
reports that in the first column of its result row ("busy"), and the WAL
keeps its size. These helpers read that column, so a caller knows whether
the WAL is really empty.

A checkpoint waits for the readers and writers of the database, for as
long as the `busy_timeout` of its connection allows. The connections of
Trailarr allow 20 seconds, and Docker stops a container 10 seconds after
it asks. So a checkpoint at the start or the stop of the app gets a short
timeout of its own, and the default is one attempt.
"""

import asyncio
from contextlib import asynccontextmanager, contextmanager
import time

from sqlalchemy import Connection, text
from sqlalchemy.ext.asyncio import AsyncConnection

_CHECKPOINT = text("PRAGMA wal_checkpoint(TRUNCATE)")
_READ_BUSY_TIMEOUT = text("PRAGMA busy_timeout")

# How long a checkpoint at the start or the stop of the app waits for a busy
# database, in milliseconds. Two databases are checkpointed, so both finish
# well inside the 10 seconds that Docker gives a container to stop.
STOP_BUSY_TIMEOUT_MS = 2000


def _is_done(row) -> bool:
    """True when the checkpoint finished. A missing row is not busy."""
    return row is None or row[0] == 0


def _set_busy_timeout(timeout_ms: int):
    # A PRAGMA takes no bound parameter, so the value goes into the text.
    return text(f"PRAGMA busy_timeout={int(timeout_ms)}")


@contextmanager
def _busy_timeout(connection: Connection, timeout_ms: int | None):
    """Give the connection a `busy_timeout`, and put the old one back.

    The connection comes from a pool and is used again later, so the
    change must not stay.
    """
    if timeout_ms is None:
        yield
        return
    before = connection.execute(_READ_BUSY_TIMEOUT).scalar() or 0
    connection.execute(_set_busy_timeout(timeout_ms))
    try:
        yield
    finally:
        connection.execute(_set_busy_timeout(before))


@asynccontextmanager
async def _busy_timeout_async(
    connection: AsyncConnection, timeout_ms: int | None
):
    """The same as `_busy_timeout`, for an async connection."""
    if timeout_ms is None:
        yield
        return
    result = await connection.execute(_READ_BUSY_TIMEOUT)
    before = result.scalar() or 0
    await connection.execute(_set_busy_timeout(timeout_ms))
    try:
        yield
    finally:
        await connection.execute(_set_busy_timeout(before))


def truncate_wal(
    connection: Connection,
    attempts: int = 1,
    pause: float = 0.5,
    busy_timeout_ms: int | None = None,
) -> bool:
    """Checkpoint and empty the WAL, trying again while it is busy.

    Args:
        connection (Connection): A connection to the database.
        attempts (int): How many times to try. Defaults to 1.
        pause (float): Seconds to wait between attempts.
        busy_timeout_ms (int | None): How long one attempt waits for the
            readers and writers of the database, in milliseconds. None
            keeps the timeout of the connection. A start or a stop passes
            `STOP_BUSY_TIMEOUT_MS`.

    Returns:
        bool: True when the WAL is empty. False when another connection
            kept it busy on every attempt.
    """
    with _busy_timeout(connection, busy_timeout_ms):
        for attempt in range(max(1, attempts)):
            if attempt:
                time.sleep(pause)
            if _is_done(connection.execute(_CHECKPOINT).fetchone()):
                return True
    return False


async def truncate_wal_async(
    connection: AsyncConnection,
    attempts: int = 1,
    pause: float = 0.5,
    busy_timeout_ms: int | None = None,
) -> bool:
    """The same as `truncate_wal`, for an async connection."""
    async with _busy_timeout_async(connection, busy_timeout_ms):
        for attempt in range(max(1, attempts)):
            if attempt:
                await asyncio.sleep(pause)
            result = await connection.execute(_CHECKPOINT)
            if _is_done(result.fetchone()):
                return True
    return False
