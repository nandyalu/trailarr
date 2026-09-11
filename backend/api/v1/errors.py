"""Turning an exception into an HTTP response.

Handlers used to catch every exception and answer 404 with `str(e)`. That
gave the wrong status for a failure that is not a missing item, and it put
whatever the exception said into the response — which can be a file path, an
SQL statement with its parameters, or a URL with a token in it.

This module keeps one list of exceptions whose message is written for the
user, and answers everything else with a generic line while the real cause
goes to the log.
"""

from fastapi import HTTPException, status

from exceptions import (
    ConnectionTimeoutError,
    FolderNotFoundError,
    FolderPathEmptyError,
    InvalidResponseError,
    ItemExistsError,
    ItemNotFoundError,
)

# Exceptions whose message is meant for the user. Most of them report what
# a server said when Trailarr asked, and the user needs that text to fix
# the problem — "connection refused" is the answer, not an internal detail.
SAFE_TO_REPORT = (
    ConnectionError,
    ConnectionTimeoutError,
    FolderNotFoundError,
    FolderPathEmptyError,
    InvalidResponseError,
    ItemExistsError,
    ValueError,
)


def as_http_error(
    exc: Exception,
    *,
    logger,
    action: str,
    safe_status: int = status.HTTP_400_BAD_REQUEST,
    not_found_status: int = status.HTTP_404_NOT_FOUND,
) -> HTTPException:
    """Give back the HTTPException to raise for `exc`.

    An HTTPException that a handler raised on purpose passes through
    unchanged. A missing item becomes a 404. An exception from the list
    above keeps its message. Anything else is logged with its traceback and
    becomes a 500 that says only what failed.

    Args:
        exc (Exception): The exception the handler caught.
        logger: The module logger, so the traceback lands in the right place.
        action (str): What the handler was doing, such as "Read media". It
            becomes the 500 message and the start of the log line.
        safe_status (int): The status for an exception from SAFE_TO_REPORT.
        not_found_status (int): The status for a missing item.

    Returns:
        HTTPException: The error to raise.
    """
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, ItemNotFoundError):
        return HTTPException(status_code=not_found_status, detail=str(exc))
    if isinstance(exc, SAFE_TO_REPORT):
        return HTTPException(status_code=safe_status, detail=str(exc))
    logger.exception(f"{action} failed: {exc}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"{action} failed",
    )
