"""
Tests for apps.common.event_bus
================================
"""

import pytest
from unittest.mock import MagicMock, call

from apps.common.event_bus import DomainEvent, EventBus, EventTypes, event_bus


class TestDomainEvent:

    def test_creation(self):
        evt = DomainEvent(
            event_type=EventTypes.BOOK_CREATED,
            payload={"book_id": "abc"},
            metadata={"actor": "test"},
        )
        assert evt.event_type == EventTypes.BOOK_CREATED
        assert evt.payload["book_id"] == "abc"

    def test_to_dict(self):
        evt = DomainEvent(event_type="test.event", payload={"key": "val"})
        d = evt.to_dict()
        assert d["event_type"] == "test.event"
        assert d["payload"] == {"key": "val"}
        assert "occurred_at" in d

    def test_default_occurred_at(self):
        evt = DomainEvent(event_type="test.event")
        assert evt.occurred_at is not None


class TestEventBus:

    def setup_method(self):
        """Get a fresh event bus for each test."""
        event_bus.clear()

    def test_subscribe_and_publish(self):
        handler = MagicMock()
        event_bus.subscribe("test.event", handler)

        evt = DomainEvent(event_type="test.event")
        event_bus.publish(evt)

        handler.assert_called_once_with(evt)

    def test_multiple_handlers(self):
        h1 = MagicMock()
        h2 = MagicMock()
        event_bus.subscribe("test.event", h1)
        event_bus.subscribe("test.event", h2)

        evt = DomainEvent(event_type="test.event")
        event_bus.publish(evt)

        h1.assert_called_once()
        h2.assert_called_once()

    def test_wildcard_handler(self):
        handler = MagicMock()
        event_bus.subscribe("*", handler)

        evt = DomainEvent(event_type="any.event")
        event_bus.publish(evt)

        handler.assert_called_once_with(evt)

    def test_unsubscribe(self):
        handler = MagicMock()
        event_bus.subscribe("test.event", handler)
        event_bus.unsubscribe("test.event", handler)

        event_bus.publish(DomainEvent(event_type="test.event"))
        handler.assert_not_called()

    def test_no_handler_does_not_raise(self):
        """Publishing without subscribers should not raise."""
        event_bus.publish(DomainEvent(event_type="unhandled.event"))

    def test_handler_error_does_not_block_others(self):
        bad = MagicMock(side_effect=RuntimeError("boom"))
        good = MagicMock()
        event_bus.subscribe("test.event", bad)
        event_bus.subscribe("test.event", good)

        event_bus.publish(DomainEvent(event_type="test.event"))

        bad.assert_called_once()
        good.assert_called_once()

    def test_clear(self):
        handler = MagicMock()
        event_bus.subscribe("test.event", handler)
        event_bus.clear()

        event_bus.publish(DomainEvent(event_type="test.event"))
        handler.assert_not_called()

    def test_duplicate_subscribe_ignored(self):
        handler = MagicMock()
        event_bus.subscribe("test.event", handler)
        event_bus.subscribe("test.event", handler)

        event_bus.publish(DomainEvent(event_type="test.event"))
        handler.assert_called_once()


class TestEventTypes:

    def test_event_type_constants_are_strings(self):
        assert isinstance(EventTypes.BOOK_CREATED, str)
        assert isinstance(EventTypes.USER_REGISTERED, str)

    def test_event_types_have_context_prefix(self):
        assert EventTypes.BOOK_CREATED.startswith("catalog.")
        assert EventTypes.USER_REGISTERED.startswith("identity.")
        assert EventTypes.BOOK_BORROWED.startswith("circulation.")
        assert EventTypes.KP_AWARDED.startswith("engagement.")
