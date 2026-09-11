"""Tests for api/v1/errors.py.

The handlers used to answer 404 with str(e) for every exception. That gave
the wrong status and returned whatever the exception said, which can be a
path, an SQL statement with its parameters, or a URL with a token in it.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from api.v1 import errors
from exceptions import (
    ConnectionTimeoutError,
    InvalidResponseError,
    ItemExistsError,
    ItemNotFoundError,
)


@pytest.fixture
def logger():
    return MagicMock()


class TestSafeExceptionsKeepTheirMessage:

    @pytest.mark.parametrize(
        "exc",
        [
            ConnectionError("Connection refused"),
            ConnectionTimeoutError("The server did not answer"),
            InvalidResponseError("Invalid API key"),
            ItemExistsError("A connection with that name exists"),
            ValueError("That is not a valid URL"),
        ],
    )
    def test_the_user_still_sees_what_the_server_said(self, exc, logger):
        """These messages are the answer to the user's problem."""
        result = errors.as_http_error(exc, logger=logger, action="Test the connection")

        assert result.status_code == status.HTTP_400_BAD_REQUEST
        assert result.detail == str(exc)
        logger.exception.assert_not_called()

    def test_the_safe_status_can_be_changed_per_handler(self, logger):
        result = errors.as_http_error(
            ValueError("nope"),
            logger=logger,
            action="Read the folder",
            safe_status=status.HTTP_404_NOT_FOUND,
        )
        assert result.status_code == status.HTTP_404_NOT_FOUND


class TestMissingItems:

    def test_a_missing_item_is_a_404_with_its_message(self, logger):
        result = errors.as_http_error(
            ItemNotFoundError("Connection", 7), logger=logger, action="Read"
        )
        assert result.status_code == status.HTTP_404_NOT_FOUND
        assert "7" in result.detail

    def test_a_missing_item_is_not_logged_as_a_failure(self, logger):
        """Asking for something that is not there is not a server fault."""
        errors.as_http_error(
            ItemNotFoundError("Media", 1), logger=logger, action="Read"
        )
        logger.exception.assert_not_called()


class TestUnexpectedExceptions:

    @pytest.mark.parametrize(
        "exc",
        [
            RuntimeError("/config/secrets.env is unreadable"),
            KeyError("api_key"),
            OSError("[Errno 13] Permission denied: '/root/.ssh/id_rsa'"),
        ],
    )
    def test_the_message_is_not_returned_to_the_caller(self, exc, logger):
        result = errors.as_http_error(exc, logger=logger, action="Read media")

        assert result.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert result.detail == "Read media failed"
        # Whatever the exception said must not reach the response
        assert str(exc) not in result.detail

    def test_the_real_cause_goes_to_the_log(self, logger):
        exc = RuntimeError("the actual cause")
        errors.as_http_error(exc, logger=logger, action="Read media")

        logger.exception.assert_called_once()
        assert "the actual cause" in logger.exception.call_args.args[0]


class TestDeliberateHttpExceptions:

    def test_an_httpexception_passes_through_unchanged(self, logger):
        """A handler that already decided the status keeps it. `except
        Exception` catches HTTPException too, so this must not be turned
        into a 500."""
        raised = HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Invalid YouTube ID!"
        )
        result = errors.as_http_error(raised, logger=logger, action="Update")

        assert result is raised
        assert result.status_code == status.HTTP_406_NOT_ACCEPTABLE
        assert result.detail == "Invalid YouTube ID!"
        logger.exception.assert_not_called()
