"""
Nova — Circulation Application Services
===========================================
Use cases for the reservation-first circulation flow:
  ReserveBook  →  ConfirmPickup  →  RenewBorrow  →  ConfirmReturn
Plus fines, abuse detection.
"""

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from django.conf import settings
from django.db import models as db_models, transaction
from django.utils import timezone

from apps.common.event_bus import DomainEvent, EventBus, EventTypes
from apps.common.exceptions import (
    BookUnavailableError,
    BorrowingError,
    BorrowLimitExceededError,
    NotFoundError,
    UnpaidFinesError,
)
from apps.common.utils import calculate_fine_amount

from apps.catalog.domain.models import Book, BookCopy
from apps.circulation.domain.models import (
    BorrowRecord,
    Fine,
    Reservation,
    ReservationBan,
)

logger = logging.getLogger('nova.circulation')


def _circ_config() -> dict:
    return getattr(settings, 'CIRCULATION_CONFIG', {})


def _is_banned(user) -> bool:
    """Check if the user is currently banned from reserving."""
    return ReservationBan.objects.filter(
        user=user,
        expires_at__gt=timezone.now(),
        lifted_at__isnull=True,
    ).exists()


# ---------------------------------------------------------------------------
# ReserveBookUseCase — the ONLY way to initiate a physical borrow
# ---------------------------------------------------------------------------

class ReserveBookUseCase:
    """
    Place a reservation on a book.
    - If copies are available → immediately assign one (READY, 12 h pickup)
    - If no copies → queue as PENDING
    """

    @transaction.atomic
    def execute(self, user, book_id: UUID) -> Reservation:
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            raise NotFoundError(resource_type='Book', resource_id=str(book_id))

        # --- Guard: active account ---
        if not user.is_active:
            raise BorrowingError(
                message='Inactive accounts cannot reserve.',
                code='ACCOUNT_INACTIVE',
            )

        # --- Guard: reservation ban ---
        if _is_banned(user):
            ban = ReservationBan.objects.filter(
                user=user,
                expires_at__gt=timezone.now(),
                lifted_at__isnull=True,
            ).first()
            raise BorrowingError(
                message=(
                    f'You are temporarily banned from reserving until '
                    f'{ban.expires_at.strftime("%Y-%m-%d %H:%M")}. '
                    f'Reason: {ban.reason}'
                ),
                code='RESERVATION_BANNED',
            )

        # --- Guard: duplicate reservation ---
        existing = Reservation.objects.filter(
            user=user,
            book=book,
            status__in=['PENDING', 'READY'],
        ).exists()
        if existing:
            raise BorrowingError(
                message='You already have an active reservation for this book.',
                code='DUPLICATE_RESERVATION',
            )

        # --- Guard: borrow limit (max 2 active borrows) ---
        cfg = _circ_config()
        max_borrows = cfg.get('MAX_CONCURRENT_BORROWS', 2)
        active_borrows = BorrowRecord.objects.filter(
            user=user, status__in=['ACTIVE', 'OVERDUE'],
        ).count()
        if active_borrows >= max_borrows:
            raise BorrowingError(
                message=(
                    f'You already have {active_borrows} active borrow(s). '
                    f'The maximum is {max_borrows}. Please return a book before reserving another.'
                ),
                code='BORROW_LIMIT_EXCEEDED',
            )

        # --- Guard: reservation limit (max 2 active reservations) ---
        max_reservations = cfg.get('MAX_CONCURRENT_RESERVATIONS', 2)
        active_reservations = Reservation.objects.filter(
            user=user, status__in=['PENDING', 'READY'],
        ).count()
        if active_reservations >= max_reservations:
            raise BorrowingError(
                message=(
                    f'You already have {active_reservations} active reservation(s). '
                    f'The maximum is {max_reservations}. Please cancel or pick up a reservation first.'
                ),
                code='RESERVATION_LIMIT_EXCEEDED',
            )

        # --- Guard: unpaid fines threshold ---
        unpaid_fines = Fine.objects.filter(
            user=user, status__in=['PENDING', 'PARTIALLY_PAID'],
        )
        if unpaid_fines.exists():
            total_unpaid = unpaid_fines.aggregate(
                total=db_models.Sum('amount') - db_models.Sum('paid_amount'),
            )['total'] or Decimal('0.00')
            threshold = Decimal(str(cfg.get('MAX_UNPAID_FINE_THRESHOLD', 25.00)))
            if total_unpaid > threshold:
                raise UnpaidFinesError(
                    amount=float(total_unpaid),
                    threshold=float(threshold),
                )

        # --- Try to assign a copy immediately ---
        available_copy = BookCopy.objects.select_for_update().filter(
            book=book, status='AVAILABLE',
        ).first()

        if available_copy:
            # Immediate assignment → READY with 12 h pickup window
            reservation = Reservation.objects.create(
                user=user,
                book=book,
                queue_position=0,
            )
            reservation.mark_ready(available_copy)  # sets READY + marks copy RESERVED
        else:
            # No copies available → queue
            position = Reservation.objects.filter(
                book=book, status='PENDING',
            ).count() + 1
            reservation = Reservation.objects.create(
                user=user,
                book=book,
                queue_position=position,
            )

        EventBus.publish(DomainEvent(
            event_type=EventTypes.BOOK_RESERVED,
            payload={
                'user_id': str(user.id),
                'book_id': str(book.id),
                'status': reservation.status,
                'queue_position': reservation.queue_position,
            },
            metadata={'aggregate_id': str(reservation.id)},
        ))

        logger.info('Book reserved', extra={
            'reservation_id': str(reservation.id),
            'user_id': str(user.id),
            'book': book.title,
            'status': reservation.status,
        })
        return reservation


# ---------------------------------------------------------------------------
# ConfirmPickupUseCase — librarian confirms user physically picked up
# ---------------------------------------------------------------------------

class ConfirmPickupUseCase:
    """
    Librarian confirms physical pickup of a reserved copy.
    - Fulfills the reservation
    - Creates a BorrowRecord (ACTIVE)
    - Marks the copy as BORROWED
    """

    @transaction.atomic
    def execute(
        self,
        reservation_id: UUID,
        issued_by,
    ) -> BorrowRecord:
        try:
            reservation = Reservation.objects.select_related(
                'user', 'book', 'assigned_copy', 'assigned_copy__book',
            ).get(pk=reservation_id)
        except Reservation.DoesNotExist:
            raise NotFoundError(resource_type='Reservation', resource_id=str(reservation_id))

        if reservation.status != 'READY':
            raise BorrowingError(
                message=f'Reservation is {reservation.status}, not READY for pickup.',
                code='INVALID_RESERVATION_STATUS',
            )

        if not reservation.assigned_copy:
            raise BorrowingError(
                message='No copy assigned to this reservation.',
                code='NO_COPY_ASSIGNED',
            )

        copy = reservation.assigned_copy
        cfg = _circ_config()
        period_days = cfg.get('DEFAULT_BORROW_DAYS', 14)
        max_renewals = cfg.get('MAX_EXTENSIONS', 2)

        # Fulfill reservation
        reservation.fulfill()

        # Mark copy as BORROWED
        copy.mark_borrowed()

        # Increment borrow count
        copy.book.increment_borrow_count()

        # Create borrow record
        record = BorrowRecord.objects.create(
            user=reservation.user,
            book_copy=copy,
            reservation=reservation,
            due_date=timezone.now() + timedelta(days=period_days),
            condition_at_borrow=copy.condition,
            max_renewals=max_renewals,
            issued_by=issued_by,
        )

        EventBus.publish(DomainEvent(
            event_type=EventTypes.BOOK_BORROWED,
            payload={
                'user_id': str(reservation.user.id),
                'book_id': str(copy.book.id),
                'copy_id': str(copy.id),
                'due_date': record.due_date.isoformat(),
            },
            metadata={'aggregate_id': str(record.id)},
        ))

        logger.info('Pickup confirmed', extra={
            'borrow_id': str(record.id),
            'reservation_id': str(reservation.id),
            'user_id': str(reservation.user.id),
            'book': copy.book.title,
        })
        return record


# ---------------------------------------------------------------------------
# ReturnBookUseCase — librarian confirms physical return
# ---------------------------------------------------------------------------

class ReturnBookUseCase:
    """Process a physical book return (librarian only)."""

    @transaction.atomic
    def execute(
        self,
        borrow_id: UUID,
        condition: str = '',
        returned_to=None,
    ) -> BorrowRecord:
        try:
            record = BorrowRecord.objects.select_related(
                'book_copy', 'book_copy__book', 'user',
            ).get(pk=borrow_id)
        except BorrowRecord.DoesNotExist:
            raise NotFoundError(resource_type='BorrowRecord', resource_id=str(borrow_id))

        if record.status == 'RETURNED':
            raise BorrowingError(message='Book already returned.', code='ALREADY_RETURNED')

        was_overdue = record.is_overdue
        overdue_days = record.days_overdue

        record.mark_returned(condition=condition, returned_to=returned_to)
        record.book_copy.mark_returned()

        # Auto-generate overdue fine if applicable
        if was_overdue and overdue_days > 0:
            cfg = _circ_config()
            base_rate = Decimal(str(cfg.get('FINE_BASE_RATE_PER_DAY', 0.50)))
            escalation_tiers = cfg.get('FINE_ESCALATION_TIERS', {7: 1.0, 30: 1.5, 999: 2.0})
            fine_amount = calculate_fine_amount(overdue_days, base_rate, escalation_tiers)
            Fine.objects.create(
                user=record.user,
                borrow_record=record,
                reason='OVERDUE',
                amount=fine_amount,
                description=f'Overdue by {overdue_days} days',
            )
            EventBus.publish(DomainEvent(
                event_type=EventTypes.FINE_ISSUED,
                payload={
                    'user_id': str(record.user.id),
                    'amount': str(fine_amount),
                    'overdue_days': overdue_days,
                },
                metadata={'aggregate_id': str(record.id)},
            ))

        # Check if anyone is waiting for this book
        next_reservation = Reservation.objects.filter(
            book=record.book_copy.book,
            status='PENDING',
        ).order_by('queue_position', 'reserved_at').first()

        if next_reservation:
            next_reservation.mark_ready(record.book_copy)

        EventBus.publish(DomainEvent(
            event_type=EventTypes.BOOK_RETURNED,
            payload={
                'user_id': str(record.user.id),
                'book_id': str(record.book_copy.book.id),
                'was_overdue': was_overdue,
                'overdue_days': overdue_days,
            },
            metadata={'aggregate_id': str(record.id)},
        ))

        logger.info('Book returned', extra={
            'borrow_id': str(record.id),
            'overdue': was_overdue,
        })
        return record


# ---------------------------------------------------------------------------
# RenewBorrowUseCase — user can renew via app
# ---------------------------------------------------------------------------

class RenewBorrowUseCase:
    """Renew an active borrow record (user self-service)."""

    @transaction.atomic
    def execute(self, borrow_id: UUID, user=None) -> BorrowRecord:
        try:
            record = BorrowRecord.objects.select_related('book_copy__book').get(pk=borrow_id)
        except BorrowRecord.DoesNotExist:
            raise NotFoundError(resource_type='BorrowRecord', resource_id=str(borrow_id))

        # Ownership check — staff can renew on behalf of any user
        if user and record.user_id != user.id and not getattr(user, 'is_staff_member', False):
            raise BorrowingError(
                message='You can only renew your own borrows.',
                code='NOT_OWNER',
            )

        # Check no one is waiting
        has_reservation = Reservation.objects.filter(
            book=record.book_copy.book,
            status='PENDING',
        ).exists()
        if has_reservation:
            raise BorrowingError(
                message='Cannot renew — another user has reserved this book.',
                code='RESERVATION_BLOCKS_RENEWAL',
            )

        record.renew()

        EventBus.publish(DomainEvent(
            event_type=EventTypes.BORROW_RENEWED,
            payload={
                'user_id': str(record.user_id),
                'new_due_date': record.due_date.isoformat(),
                'renewal_count': record.renewal_count,
            },
            metadata={'aggregate_id': str(record.id)},
        ))
        return record


# ---------------------------------------------------------------------------
# CancelReservationUseCase
# ---------------------------------------------------------------------------

class CancelReservationUseCase:
    """Cancel a reservation (user or staff)."""

    @transaction.atomic
    def execute(self, reservation_id: UUID, user=None) -> Reservation:
        try:
            reservation = Reservation.objects.select_related(
                'assigned_copy',
            ).get(pk=reservation_id)
        except Reservation.DoesNotExist:
            raise NotFoundError(resource_type='Reservation', resource_id=str(reservation_id))

        if reservation.status not in ('PENDING', 'READY'):
            raise BorrowingError(
                message=f'Cannot cancel a {reservation.status} reservation.',
                code='INVALID_STATUS',
            )

        # Ownership check (staff can cancel anyone's)
        if user and reservation.user_id != user.id and not getattr(user, 'is_staff_member', False):
            from apps.common.exceptions import AuthorizationError
            raise AuthorizationError(message='Not allowed.', code='FORBIDDEN')

        reservation.cancel()
        return reservation


# ---------------------------------------------------------------------------
# CheckAbuseUseCase — anti-abuse: ban frequent no-shows
# ---------------------------------------------------------------------------

class CheckAbuseUseCase:
    """
    Check a user's no-show history and impose a ban if they exceed the
    configured threshold.
    Called after a reservation expires (no-show).
    """

    def execute(self, user) -> Optional[ReservationBan]:
        cfg = _circ_config()
        lookback_days = cfg.get('ABUSE_LOOKBACK_DAYS', 30)
        max_no_shows = cfg.get('ABUSE_MAX_NO_SHOWS', 3)
        ban_days = cfg.get('ABUSE_BAN_DAYS', 7)

        since = timezone.now() - timedelta(days=lookback_days)
        no_show_count = Reservation.objects.filter(
            user=user,
            status='EXPIRED',
            updated_at__gte=since,
        ).count()

        if no_show_count >= max_no_shows:
            # Check if already banned
            if _is_banned(user):
                return None

            ban = ReservationBan.objects.create(
                user=user,
                no_show_count=no_show_count,
                reason=(
                    f'You had {no_show_count} no-show reservations in the last '
                    f'{lookback_days} days (limit: {max_no_shows}).'
                ),
                expires_at=timezone.now() + timedelta(days=ban_days),
            )

            logger.warning('Reservation ban imposed', extra={
                'user_id': str(user.id),
                'no_show_count': no_show_count,
                'ban_until': ban.expires_at.isoformat(),
            })
            return ban

        return None


# ---------------------------------------------------------------------------
# LiftBanUseCase — staff can lift a ban early
# ---------------------------------------------------------------------------

class LiftBanUseCase:
    """Staff lifts a reservation ban early."""

    def execute(self, ban_id: UUID, lifted_by) -> ReservationBan:
        try:
            ban = ReservationBan.objects.get(pk=ban_id)
        except ReservationBan.DoesNotExist:
            raise NotFoundError(resource_type='ReservationBan', resource_id=str(ban_id))

        ban.lift(lifted_by=lifted_by)
        logger.info('Reservation ban lifted', extra={
            'ban_id': str(ban.id),
            'user_id': str(ban.user_id),
            'lifted_by': str(lifted_by.id),
        })
        return ban


# ---------------------------------------------------------------------------
# PayFineUseCase
# ---------------------------------------------------------------------------

class PayFineUseCase:
    """Process fine payment."""

    @transaction.atomic
    def execute(self, fine_id: UUID, amount: Decimal = None) -> Fine:
        try:
            fine = Fine.objects.get(pk=fine_id)
        except Fine.DoesNotExist:
            raise NotFoundError(resource_type='Fine', resource_id=str(fine_id))

        if fine.status in ('PAID', 'WAIVED'):
            raise BorrowingError(message='Fine already settled.', code='FINE_SETTLED')

        fine.pay(amount)

        EventBus.publish(DomainEvent(
            event_type=EventTypes.FINE_PAID,
            payload={
                'user_id': str(fine.user_id),
                'amount_paid': str(amount or fine.outstanding),
                'status': fine.status,
            },
            metadata={'aggregate_id': str(fine.id)},
        ))
        return fine


# ---------------------------------------------------------------------------
# WaiveFineUseCase
# ---------------------------------------------------------------------------

class WaiveFineUseCase:
    """Waive a fine (admin action)."""

    @transaction.atomic
    def execute(self, fine_id: UUID, waived_by) -> Fine:
        try:
            fine = Fine.objects.get(pk=fine_id)
        except Fine.DoesNotExist:
            raise NotFoundError(resource_type='Fine', resource_id=str(fine_id))

        fine.waive(waived_by)

        EventBus.publish(DomainEvent(
            event_type=EventTypes.FINE_WAIVED,
            payload={
                'user_id': str(fine.user_id),
                'waived_by': str(waived_by.id),
                'amount': str(fine.amount),
            },
            metadata={'aggregate_id': str(fine.id)},
        ))
        return fine
