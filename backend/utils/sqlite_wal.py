"""Empty the write-ahead log (WAL) of a SQLite database.

`PRAGMA wal_checkpoint(TRUNCATE)` copies the WAL into the database and
cuts the WAL file to zero bytes. When another connection holds a read or
write transaction, SQLite cannot finish, but it does not raise. It
reports that in the first column of its result row ("busy"), and the WAL
keeps its size. These helpers read that column, so a caller knows whether
the WAL is really empty.

Each attempt can already wait for `busy_timeout`. So the default is one
attempt: a shutdown must finish inside the stop grace period of Docker.
"""

import asyncio
import time

from sqlalchemy import Connection, text
from sqlalchemy.ext.asyncio import AsyncConnection

_CHECKPOINT = text("PRAGMA wal_checkpoint(TRUNCATE)")


def _is_done(row) -> bool:
    """True when the checkpoint finished. A missing row is not busy."""
    return row is None or row[0] == 0


def truncate_wal(
    connection: Connection, attempts: int = 1, pause: float = 0.5
) -> bool:
    """Checkpoint and empty the WAL, trying again while it is busy.

    Args:
        connection (Connection): A connection to the database.
        attempts (int): How many times to try. Defaults to 1.
        pause (float): Seconds to wait between attempts.

    Returns:
        bool: True when the WAL is empty. False when another connection
            kept it busy on every attempt.
    """
    for attempt in range(max(1, attempts)):
        if attempt:
            time.sleep(pause)
        if _is_done(connection.execute(_CHECKPOINT).fetchone()):
            return True
    return False


async def truncate_wal_async(
    connection: AsyncConnection, attempts: int = 1, pause: float = 0.5
) -> bool:
    """The same as `truncate_wal`, for an async connection."""
    for attempt in range(max(1, attempts)):
        if attempt:
            await asyncio.sleep(pause)
        result = await connection.execute(_CHECKPOINT)
        if _is_done(result.fetchone()):
            return True
    return False
