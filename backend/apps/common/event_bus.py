"""
Nova — Domain Event Bus
=========================
Simple synchronous event bus for intra-process domain events.
Events are dispatched synchronously within the same transaction.
For async processing, handlers can enqueue Celery tasks.
"""

import logging
from typing import Any, Callable, Dict, List, Type
from dataclasses import dataclass, field
from datetime import datetime

from django.utils import timezone

logger = logging.getLogger('nova')


@dataclass
class DomainEvent:
    """
    Base class for all domain events.

    Attributes:
        event_type: String identifier for the event type.
        occurred_at: When the event occurred.
        payload: Event-specific data.
        metadata: Additional context (actor_id, ip_address, etc.)
    """
    event_type: str
    occurred_at: datetime = field(default_factory=timezone.now)
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize event to dictionary for storage or transmission."""
        return {
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'payload': self.payload,
            'metadata': self.metadata,
        }


class _EventBusMeta(type):
    """Metaclass that delegates class-level method calls to the singleton."""

    _DELEGATED = frozenset(('subscribe', 'unsubscribe', 'publish', 'clear'))

    def __getattribute__(cls, name):
        if name in type.__getattribute__(cls, '_DELEGATED'):
            instance = cls()
            return getattr(instance, name)
        return type.__getattribute__(cls, name)


class EventBus(metaclass=_EventBusMeta):
    """
    In-process domain event bus.

    Supports:
    - Registering handlers for event types
    - Publishing events to all registered handlers
    - Wildcard handlers (subscribe to all events)

    Can be used via the class (``EventBus.subscribe(...)``) or the
    module-level singleton (``event_bus.subscribe(...)``).
    """

    _instance = None
    _handlers: Dict[str, List[Callable]] = {}

    def __new__(cls):
        """Singleton pattern — one event bus per process."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers = {}
        return cls._instance

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]):
        """
        Register a handler for a specific event type.

        Args:
            event_type: The event type string to listen for. Use '*' for all events.
            handler: Callable that accepts a DomainEvent.
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(f'Handler {getattr(handler, "__name__", repr(handler))} subscribed to {event_type}')

    def unsubscribe(self, event_type: str, handler: Callable):
        """Remove a handler for an event type."""
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def publish(self, event: DomainEvent):
        """
        Publish an event to all registered handlers.

        Handlers are called synchronously in registration order.
        Errors in one handler do not prevent others from executing.

        Args:
            event: The domain event to publish.
        """
        handlers = self._handlers.get(event.event_type, [])
        wildcard_handlers = self._handlers.get('*', [])
        all_handlers = handlers + wildcard_handlers

        if not all_handlers:
            logger.debug(f'No handlers for event: {event.event_type}')
            return

        for handler in all_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f'Error in event handler {getattr(handler, "__name__", repr(handler))} '
                    f'for event {event.event_type}: {e}',
                    exc_info=True
                )

    def clear(self):
        """Remove all handlers. Useful for testing."""
        self._handlers.clear()

    @classmethod
    def reset(cls):
        """Reset the singleton. Useful for testing."""
        cls._instance = None
        cls._handlers = {}


# =============================================================================
# Global event bus instance
# =============================================================================

event_bus = EventBus()


# =============================================================================
# Predefined Event Types
# =============================================================================

class EventTypes:
    """Centralized event type constants."""

    # Identity Events
    USER_REGISTERED = 'identity.user_registered'
    USER_ACTIVATED = 'identity.user_activated'
    USER_SUSPENDED = 'identity.user_suspended'
    USER_LOGIN = 'identity.user_login'
    USER_LOGGED_IN = 'identity.user_login'          # alias
    USER_LOGIN_FAILED = 'identity.user_login_failed'
    USER_LOGGED_OUT = 'identity.user_logged_out'
    USER_PROFILE_UPDATED = 'identity.user_profile_updated'
    USER_ROLE_CHANGED = 'identity.user_role_changed'
    PASSWORD_CHANGED = 'identity.password_changed'
    VERIFICATION_SUBMITTED = 'identity.verification_submitted'
    VERIFICATION_APPROVED = 'identity.verification_approved'
    VERIFICATION_REJECTED = 'identity.verification_rejected'
    VERIFICATION_MANUAL_REVIEW = 'identity.verification_manual_review'

    # Catalog Events
    BOOK_CREATED = 'catalog.book_created'
    BOOK_ADDED = 'catalog.book_created'             # alias
    BOOK_UPDATED = 'catalog.book_updated'
    BOOK_DELETED = 'catalog.book_deleted'
    STOCK_ADJUSTED = 'catalog.stock_adjusted'
    COPY_ADDED = 'catalog.copy_added'
    BOOK_REVIEWED = 'catalog.book_reviewed'

    # Circulation Events
    BOOK_BORROWED = 'circulation.book_borrowed'
    BOOK_RETURNED = 'circulation.book_returned'
    BOOK_RESERVED = 'circulation.book_reserved'
    BORROW_EXTENDED = 'circulation.borrow_extended'
    BORROW_RENEWED = 'circulation.borrow_extended'  # alias
    FINE_GENERATED = 'circulation.fine_generated'
    FINE_ISSUED = 'circulation.fine_generated'       # alias
    FINE_PAID = 'circulation.fine_paid'
    FINE_WAIVED = 'circulation.fine_waived'
    OVERDUE_DETECTED = 'circulation.overdue_detected'
    BORROW_OVERDUE = 'circulation.overdue_detected'  # alias
    DUE_DATE_REMINDER = 'circulation.due_date_reminder'

    # Digital Content Events
    ASSET_UPLOADED = 'digital_content.asset_uploaded'
    SESSION_STARTED = 'digital_content.session_started'
    READING_SESSION_STARTED = 'digital_content.session_started'  # alias
    SESSION_ENDED = 'digital_content.session_ended'
    READING_SESSION_ENDED = 'digital_content.session_ended'      # alias
    HEARTBEAT_RECEIVED = 'digital_content.heartbeat_received'
    SESSION_TIMED_OUT = 'digital_content.session_timed_out'
    NOTE_CREATED = 'digital_content.note_created'
    BOOKMARK_CREATED = 'digital_content.bookmark_created'

    # Engagement Events
    KP_AWARDED = 'engagement.kp_awarded'
    KP_DEDUCTED = 'engagement.kp_deducted'
    LEVEL_UP = 'engagement.level_up'
    STREAK_EXTENDED = 'engagement.streak_extended'
    STREAK_BROKEN = 'engagement.streak_broken'
    ACHIEVEMENT_UNLOCKED = 'engagement.achievement_unlocked'
    IDLE_DETECTED = 'engagement.idle_detected'
    ABUSE_DETECTED = 'engagement.abuse_detected'

    # Intelligence Events
    EMBEDDING_GENERATED = 'intelligence.embedding_generated'
    RECOMMENDATION_GENERATED = 'intelligence.recommendation_generated'
    PREDICTION_COMPUTED = 'intelligence.prediction_computed'

    # Governance Events
    AUDIT_ENTRY_CREATED = 'governance.audit_entry_created'
    SECURITY_EVENT_RAISED = 'governance.security_event_raised'
