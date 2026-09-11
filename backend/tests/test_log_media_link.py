"""Linking a log line to its media item.

The logs page turns a log line into a link when its `mediaid` column is
set. That column used to be filled in one way only: the database handler
searched the message for the first `[123]` and used that number.

Two problems came with it. The number had to be the media id and had to be
first, so `Setting profile [7] on download [12] for media [42]` stored 7 and
linked the line to the wrong title. And it tied the wording of every log
line to a parsing rule, which blocks rewriting them.

A caller can now pass the id, and the search stays as a fallback.
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


class TestTheMessageSearchFallback:
    """The database handler's rule, checked here so its limits are written
    down. Lines that pass the id explicitly do not depend on any of this."""

    @staticmethod
    def _mediaid_from_message(message: str):
        import re

        match = re.search(r"\[([0-9]+)\]", message)
        return int(match.group(1)) if match else None

    def test_a_single_bracketed_id_is_found(self):
        assert self._mediaid_from_message("Downloaded 'Film' [42]") == 42

    def test_the_first_bracket_wins_even_when_it_is_the_wrong_number(self):
        """This is the bug the explicit tag removes. Kept as a test so
        nobody 'fixes' a message back into this shape by accident."""
        message = "Setting profile [7] on download [12] for media [42]"
        assert self._mediaid_from_message(message) == 7  # not 42

    def test_a_message_with_no_brackets_finds_nothing(self):
        assert self._mediaid_from_message("Trailarr downloaded a trailer.") is None
