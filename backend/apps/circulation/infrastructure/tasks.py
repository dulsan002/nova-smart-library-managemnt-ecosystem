"""
Nova — Circulation Celery Tasks
===================================
Background jobs for:
  - Overdue detection
  - Reservation expiry (12 h)
  - No-show abuse detection
  - Due-date reminders
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.common.event_bus import DomainEvent, EventBus, EventTypes

logger = logging.getLogger('nova.circulation')


@shared_task(name='circulation.check_overdue_borrows', queue='default')
def check_overdue_borrows():
    """Periodic task: mark ACTIVE borrows past due_date as OVERDUE."""
    from apps.circulation.domain.models import BorrowRecord

    now = timezone.now()
    overdue = BorrowRecord.objects.filter(
        status='ACTIVE',
        due_date__lt=now,
    )
    count = 0
    for record in overdue.iterator():
        record.mark_overdue()
        count += 1
        EventBus.publish(DomainEvent(
            event_type=EventTypes.BORROW_OVERDUE,
            payload={
                'user_id': str(record.user_id),
                'days_overdue': record.days_overdue,
            },
            metadata={'aggregate_id': str(record.id)},
        ))

    if count:
        logger.info('Overdue check complete', extra={'marked_overdue': count})


@shared_task(name='circulation.expire_reservations', queue='default')
def expire_reservations():
    """
    Expire READY reservations that have passed their 12 h pickup deadline.
    Releases the assigned copy and triggers abuse detection.
    """
    from apps.circulation.application import CheckAbuseUseCase
    from apps.circulation.domain.models import Reservation

    now = timezone.now()
    expired_qs = Reservation.objects.filter(
        status='READY',
        expires_at__lt=now,
    ).select_related('assigned_copy', 'user')

    abuse_checker = CheckAbuseUseCase()
    count = 0
    for resv in expired_qs.iterator():
        resv.expire()  # releases the assigned copy back to AVAILABLE
        count += 1
        # Check if this user should be banned
        abuse_checker.execute(resv.user)

    if count:
        logger.info('Reservation expiry check', extra={'expired_count': count})


@shared_task(name='circulation.send_due_date_reminders', queue='default')
def send_due_date_reminders():
    """Notify users whose books are due within 24 hours."""
    from apps.circulation.domain.models import BorrowRecord

    now = timezone.now()
    upcoming = BorrowRecord.objects.filter(
        status='ACTIVE',
        due_date__range=(now, now + timedelta(hours=24)),
    ).select_related('user', 'book_copy__book')

    count = 0
    for record in upcoming.iterator():
        EventBus.publish(DomainEvent(
            event_type=EventTypes.DUE_DATE_REMINDER,
            payload={
                'user_id': str(record.user_id),
                'book_title': record.book_copy.book.title,
                'due_date': record.due_date.isoformat(),
            },
            metadata={'aggregate_id': str(record.id)},
        ))
        count += 1

    if count:
        logger.info('Due date reminders sent', extra={'count': count})


@shared_task(name='circulation.send_pickup_reminders', queue='default')
def send_pickup_reminders():
    """Remind users with READY reservations expiring in the next 3 hours."""
    from apps.circulation.domain.models import Reservation

    now = timezone.now()
    soon = now + timedelta(hours=3)
    reservations = Reservation.objects.filter(
        status='READY',
        expires_at__range=(now, soon),
        notification_sent=False,
    ).select_related('user', 'book', 'assigned_copy')

    count = 0
    for resv in reservations.iterator():
        EventBus.publish(DomainEvent(
            event_type=EventTypes.BOOK_RESERVED,
            payload={
                'user_id': str(resv.user_id),
                'book_title': resv.book.title,
                'pickup_location': resv.pickup_location,
                'expires_at': resv.expires_at.isoformat(),
                'reminder': True,
            },
            metadata={'aggregate_id': str(resv.id)},
        ))
        resv.notification_sent = True
        resv.save(update_fields=['notification_sent', 'updated_at'])
        count += 1

    if count:
        logger.info('Pickup reminders sent', extra={'count': count})
