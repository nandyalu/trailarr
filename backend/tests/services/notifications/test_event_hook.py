"""The dispatcher must receive every stored event.

Phase 7 Stage B inverted this link. The event manager used to import the
dispatcher, which broke the layering. Now the dispatcher registers a
listener with the event manager instead.

That kind of wiring fails quietly: nothing raises, notifications simply
stop. These tests make the link explicit.
"""

import importlib

from database.models.event import EventCreate, EventSource, EventType
from services.notifications import dispatcher

# `import database.manager.event.create` gives back the create FUNCTION, not
# the module: the package __init__ re-exports `create` and shadows the
# submodule name. Ask importlib for the module itself.
event_create = importlib.import_module("database.manager.event.create")


def _event(detail: str = "hook") -> EventCreate:
    return EventCreate(
        event_type=EventType.TRAILER_DOWNLOADED,
        source=EventSource.SYSTEM,
        media_id=7,
        new_value=detail,
    )


class TestDispatcherIsWiredToEvents:

    def test_dispatcher_registers_itself_on_import(self):
        """Importing the dispatcher is enough. main.py does this at startup,
        before anything can store an event."""
        assert dispatcher.on_event in event_create._listeners

    def test_subscribing_twice_registers_one_listener(self):
        before = list(event_create._listeners)
        event_create.subscribe(dispatcher.on_event)
        assert event_create._listeners == before

    def test_a_stored_event_reaches_the_queue(self):
        before = len(dispatcher._queue)
        event_create._notify(_event("queued-note"))
        assert len(dispatcher._queue) == before + 1
        note = dispatcher._queue[-1]
        assert note.event_type == "TRAILER_DOWNLOADED"
        assert note.source == "SYSTEM"
        assert note.media_id == 7
        assert note.detail == "queued-note"


class TestAListenerNeverBreaksEventStorage:

    def test_a_raising_listener_is_swallowed(self):
        """Storing an event must not fail because a listener did."""

        def boom(event):
            raise RuntimeError("listener exploded")

        event_create.subscribe(boom)
        try:
            event_create._notify(_event())  # must not raise
        finally:
            event_create._listeners.remove(boom)

    def test_later_listeners_still_run_after_one_raises(self):
        seen: list[str] = []

        def boom(event):
            raise RuntimeError("listener exploded")

        def record(event):
            seen.append(event.new_value or "")

        event_create.subscribe(boom)
        event_create.subscribe(record)
        try:
            event_create._notify(_event("still-delivered"))
        finally:
            event_create._listeners.remove(boom)
            event_create._listeners.remove(record)

        assert seen == ["still-delivered"]
