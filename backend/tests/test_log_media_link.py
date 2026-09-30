"""Linking a log line to its media item.

The logs page turns a log line into a link when its `mediaid` column is
set. That column used to be filled in one way only: the database handler
searched the message for the first `[123]` and used that number.

Two problems came with it. The number had to be the media id and had to be
first, so `Setting profile [7] on download [12] for media [42]` stored 7 and
linked the line to the wrong title. And it tied the wording of every log
line to a parsing rule, which blocks rewriting them.

A caller now passes the id with `logger.media(id)`. v0.13.1 removed the
search (hygiene H14).
"""

import logging

import pytest

from app_logger import ModuleLogger


@pytest.fixture
def captured():
    """Capture the records a ModuleLogger emits."""
    records: list[logging.LogRecord] = []

    class Probe(logging.Handler):
        def emit(self, record):
            records.append(record)

    log = ModuleLogger("LinkTest")
    probe = Probe()
    log.logger.addHandler(probe)
    log.logger.setLevel(logging.DEBUG)
    yield log, records
    log.logger.removeHandler(probe)


def _mediaid(record) -> object:
    return getattr(record, "mediaid", None)


class TestTaggingALineWithItsMedia:

    def test_the_id_reaches_the_record(self, captured):
        log, records = captured
        log.info("Trailarr downloaded the trailer.", **log.media(42))
        assert _mediaid(records[0]) == 42

    def test_the_message_needs_no_brackets(self, captured):
        """The whole point: wording and linking are now independent."""
        log, records = captured
        log.info("Trailarr downloaded the trailer for Inception.", **log.media(42))
        assert "[" not in records[0].getMessage()
        assert _mediaid(records[0]) == 42

    def test_a_line_with_no_media_carries_no_id(self, captured):
        log, records = captured
        log.info("Trailarr started a disk scan.")
        assert _mediaid(records[0]) is None

    def test_a_none_id_adds_nothing(self, captured):
        """So a caller can pass an optional id without a branch."""
        log, records = captured
        log.info("A line about nothing in particular.", **log.media(None))
        assert _mediaid(records[0]) is None

    def test_plain_extra_still_works(self, captured):
        """The adapter used to throw away whatever the caller passed."""
        log, records = captured
        log.info("Tagged the long way.", extra={"mediaid": 7})
        assert _mediaid(records[0]) == 7

    def test_other_extra_fields_survive(self, captured):
        log, records = captured
        log.info("With more fields.", extra={"mediaid": 1, "custom": "kept"})
        assert _mediaid(records[0]) == 1
        assert getattr(records[0], "custom") == "kept"


class TestTheDatabaseHandler:
    """What `DatabaseLoggingHandler` stores in the mediaid column.

    Until v0.13.1 the handler read the first `[123]` in the message when a
    line had no tag, so `Setting profile [7] on download [12] for media [42]`
    linked to media 7. The fallback is gone (hygiene H14): only the tag
    links a line.
    """

    @staticmethod
    def _stored_mediaid(record: logging.LogRecord):
        from contextlib import contextmanager
        from unittest.mock import MagicMock, patch

        from config.logs.db_handler import DatabaseLoggingHandler

        session = MagicMock()

        @contextmanager
        def fake_session():
            yield session

        with patch("config.logs.db_handler.get_logs_session", fake_session):
            DatabaseLoggingHandler().emit(record)
        session.add.assert_called_once()
        return session.add.call_args.args[0].mediaid

    @staticmethod
    def _record(message: str, mediaid: int | None = None):
        record = logging.LogRecord(
            "LinkTest", logging.INFO, __file__, 1, message, None, None
        )
        if mediaid is not None:
            record.mediaid = mediaid
        return record

    def test_the_tag_is_stored(self):
        record = self._record("Trailarr downloaded the trailer.", mediaid=42)
        assert self._stored_mediaid(record) == 42

    def test_a_bracketed_number_is_not_read_as_the_media_id(self):
        record = self._record(
            "Setting profile [7] on download [12] for media [42]"
        )
        assert self._stored_mediaid(record) is None

    def test_the_tag_wins_over_brackets(self):
        record = self._record("Profile [7] changed.", mediaid=42)
        assert self._stored_mediaid(record) == 42
