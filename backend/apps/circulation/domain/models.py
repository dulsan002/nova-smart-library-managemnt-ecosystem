"""
Nova — Circulation Domain Models
====================================
BorrowRecord (aggregate root), Reservation, ReservationBan, Fine.

Flow:
  1. User reserves a book  →  Reservation (PENDING → READY)
  2. Copy assigned, 12 h pickup window
  3. Librarian confirms pickup  →  BorrowRecord (ACTIVE)
  4. User may renew via app
  5. Librarian confirms physical return  →  RETURNED
  6. Abuse tracking: no-shows may result in a temporary reservation ban
"""

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.base_models import UUIDModel


# ---------------------------------------------------------------------------
# BorrowRecord — created only when a librarian confirms physical pickup
# ---------------------------------------------------------------------------

class BorrowRecord(UUIDModel):
    """
    Aggregate root for the borrowing lifecycle.
    Created only when a librarian confirms physical pickup of a reserved copy.
    """

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
        ('LOST', 'Lost'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='borrow_records',
    )
    book_copy = models.ForeignKey(
        'catalog.BookCopy',
        on_delete=models.CASCADE,
        related_name='borrow_records',
    )
    reservation = models.OneToOneField(
        'Reservation',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='borrow_record',
        help_text='The reservation that was fulfilled to create this borrow.',
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', db_index=True)

    borrowed_at = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)

    renewal_count = models.PositiveSmallIntegerField(default=0)
    max_renewals = models.PositiveSmallIntegerField(default=2)

    # Condition tracking
    condition_at_borrow = models.CharField(max_length=20, blank=True, default='')
    condition_at_return = models.CharField(max_length=20, blank=True, default='')

    # Issued by (librarian who confirmed pickup)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='issued_borrows',
    )
    returned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='received_returns',
    )

    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'circulation_borrow_record'
        ordering = ['-borrowed_at']
        indexes = [
            models.Index(fields=['user', 'status'], name='idx_borrow_user_status'),
            models.Index(fields=['book_copy', 'status'], name='idx_borrow_copy_status'),
            models.Index(fields=['status', 'due_date'], name='idx_borrow_status_due'),
            models.Index(fields=['-borrowed_at'], name='idx_borrow_time'),
            models.Index(fields=['due_date'], name='idx_borrow_due'),
        ]

    def __str__(self):
        return f'{self.user} → {self.book_copy} ({self.status})'

    # -- Properties ----------------------------------------------------------

    @property
    def is_overdue(self) -> bool:
        if self.status == 'RETURNED':
            return False
        return timezone.now() > self.due_date

    @property
    def days_overdue(self) -> int:
        if not self.is_overdue:
            return 0
        return (timezone.now() - self.due_date).days

    @property
    def can_renew(self) -> bool:
        return (
            self.status == 'ACTIVE'
            and self.renewal_count < self.max_renewals
            and not self.is_overdue
        )

    # -- Commands ------------------------------------------------------------

    def renew(self):
        """Extend the due date by the configured borrow period."""
        if not self.can_renew:
            from apps.common.exceptions import BorrowingError
            raise BorrowingError(
                message='This borrow cannot be renewed.',
                code='RENEWAL_NOT_ALLOWED',
            )
        circ_config = getattr(settings, 'CIRCULATION_CONFIG', {})
        period_days = circ_config.get('DEFAULT_BORROW_DAYS', 14)
        self.due_date = timezone.now() + timedelta(days=period_days)
        self.renewal_count += 1
        self.save(update_fields=['due_date', 'renewal_count', 'updated_at'])

    def mark_returned(self, condition: str = '', returned_to=None):
        self.status = 'RETURNED'
        self.returned_at = timezone.now()
        self.condition_at_return = condition
        self.returned_to = returned_to
        self.save(update_fields=[
            'status', 'returned_at', 'condition_at_return',
            'returned_to', 'updated_at',
        ])

    def mark_lost(self):
        self.status = 'LOST'
        self.save(update_fields=['status', 'updated_at'])

    def mark_overdue(self):
        if self.status == 'ACTIVE':
            self.status = 'OVERDUE'
            self.save(update_fields=['status', 'updated_at'])


# ---------------------------------------------------------------------------
# Reservation — the primary entry point for the circulation flow
# ---------------------------------------------------------------------------

class Reservation(UUIDModel):
    """
    A reservation on a book. This is the ONLY way users interact with the
    physical circulation system.

    States:
      PENDING   - waiting for a copy to become available
      READY     - copy assigned, user has 12 h to pick up
      FULFILLED - librarian confirmed pickup, BorrowRecord created
      CANCELLED - user cancelled
      EXPIRED   - pickup deadline passed (no-show)
    """

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('READY', 'Ready for Pickup'),
        ('FULFILLED', 'Fulfilled'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
    )
    book = models.ForeignKey(
        'catalog.Book',
        on_delete=models.CASCADE,
        related_name='reservations',
    )
    assigned_copy = models.ForeignKey(
        'catalog.BookCopy',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='reservations',
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    reserved_at = models.DateTimeField(default=timezone.now)
    ready_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    queue_position = models.PositiveIntegerField(default=0)
    notification_sent = models.BooleanField(default=False)

    class Meta:
        db_table = 'circulation_reservation'
        ordering = ['queue_position', 'reserved_at']
        indexes = [
            models.Index(fields=['user', 'status'], name='idx_resv_user_status'),
            models.Index(fields=['book', 'status'], name='idx_resv_book_status'),
            models.Index(fields=['status', 'reserved_at'], name='idx_resv_status_time'),
            models.Index(fields=['expires_at'], name='idx_resv_expires'),
        ]
        # One active reservation per user per book
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                condition=models.Q(status__in=['PENDING', 'READY']),
                name='uniq_active_reservation',
            ),
        ]

    def __str__(self):
        return f'{self.user} reserved {self.book} ({self.status})'

    # -- Properties ----------------------------------------------------------

    @property
    def pickup_location(self) -> str:
        """Human-readable pickup location from the assigned copy."""
        if not self.assigned_copy:
            return ''
        copy = self.assigned_copy
        parts = []
        if copy.floor_number is not None:
            parts.append(f'Floor {copy.floor_number}')
        if copy.shelf_number:
            parts.append(f'Shelf {copy.shelf_number}')
        return ', '.join(parts) if parts else (copy.shelf_location or 'Main Library')

    @property
    def hours_until_expiry(self) -> float:
        """Hours remaining until pickup deadline. Negative = expired."""
        if not self.expires_at:
            return 0.0
        delta = self.expires_at - timezone.now()
        return delta.total_seconds() / 3600

    # -- Commands ------------------------------------------------------------

    def mark_ready(self, copy):
        """Assign a copy and start the 12 h pickup window."""
        self.status = 'READY'
        self.assigned_copy = copy
        self.ready_at = timezone.now()
        circ_config = getattr(settings, 'CIRCULATION_CONFIG', {})
        pickup_hours = circ_config.get('RESERVATION_PICKUP_HOURS', 12)
        self.expires_at = timezone.now() + timedelta(hours=pickup_hours)
        self.save(update_fields=[
            'status', 'assigned_copy', 'ready_at', 'expires_at', 'updated_at',
        ])
        # Mark the physical copy as RESERVED so nobody else can take it
        copy.mark_reserved()

    def fulfill(self):
        """Called when librarian confirms physical pickup."""
        self.status = 'FULFILLED'
        self.fulfilled_at = timezone.now()
        self.save(update_fields=['status', 'fulfilled_at', 'updated_at'])

    def cancel(self):
        """User-initiated cancellation."""
        if self.assigned_copy and self.status == 'READY':
            self.assigned_copy.mark_returned()  # release the reserved copy
        self.status = 'CANCELLED'
        self.cancelled_at = timezone.now()
        self.save(update_fields=['status', 'cancelled_at', 'updated_at'])

    def expire(self):
        """Auto-expire: pickup deadline passed (no-show)."""
        if self.assigned_copy:
            self.assigned_copy.mark_returned()  # release the reserved copy
        self.status = 'EXPIRED'
        self.save(update_fields=['status', 'updated_at'])


# ---------------------------------------------------------------------------
# ReservationBan — anti-abuse: temporary ban from reserving
# ---------------------------------------------------------------------------

class ReservationBan(UUIDModel):
    """
    Temporary ban from placing reservations.
    Imposed on users who frequently reserve but fail to pick up (no-shows).
    Banned users can still browse, use digital library, etc.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservation_bans',
    )
    reason = models.TextField(default='Excessive no-show reservations.')
    no_show_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of no-show reservations that triggered this ban.',
    )
    banned_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(
        help_text='When the ban lifts automatically.',
    )
    lifted_at = models.DateTimeField(
        null=True, blank=True,
        help_text='If manually lifted early by staff.',
    )
    lifted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='lifted_bans',
    )

    class Meta:
        db_table = 'circulation_reservation_ban'
        ordering = ['-banned_at']
        indexes = [
            models.Index(fields=['user', 'expires_at'], name='idx_ban_user_exp'),
        ]

    def __str__(self):
        return f'Ban {self.user} until {self.expires_at}'

    @property
    def is_active(self) -> bool:
        if self.lifted_at:
            return False
        return timezone.now() < self.expires_at

    def lift(self, lifted_by=None):
        self.lifted_at = timezone.now()
        self.lifted_by = lifted_by
        self.save(update_fields=['lifted_at', 'lifted_by', 'updated_at'])


# ---------------------------------------------------------------------------
# Fine
# ---------------------------------------------------------------------------

class Fine(UUIDModel):
    """
    Financial penalty for overdue returns, lost books, or damage.
    """

    REASON_CHOICES = [
        ('OVERDUE', 'Overdue Return'),
        ('LOST', 'Lost Book'),
        ('DAMAGE', 'Book Damage'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('WAIVED', 'Waived'),
        ('PARTIALLY_PAID', 'Partially Paid'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fines',
    )
    borrow_record = models.ForeignKey(
        BorrowRecord,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='fines',
    )

    reason = models.CharField(max_length=20, choices=REASON_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='LKR')

    description = models.TextField(blank=True, default='')
    issued_at = models.DateTimeField(default=timezone.now)
    paid_at = models.DateTimeField(null=True, blank=True)
    waived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='waived_fines',
    )
    waived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'circulation_fine'
        ordering = ['-issued_at']
        indexes = [
            models.Index(fields=['user', 'status'], name='idx_fine_user_status'),
            models.Index(fields=['status', '-issued_at'], name='idx_fine_status_time'),
        ]

    def __str__(self):
        return f'Fine {self.amount} {self.currency} — {self.user} ({self.status})'

    @property
    def outstanding(self) -> Decimal:
        return self.amount - self.paid_amount

    def pay(self, amount: Decimal = None):
        payment = amount or self.outstanding
        self.paid_amount += payment
        if self.paid_amount >= self.amount:
            self.status = 'PAID'
            self.paid_at = timezone.now()
        else:
            self.status = 'PARTIALLY_PAID'
        self.save(update_fields=['paid_amount', 'status', 'paid_at', 'updated_at'])

    def waive(self, waived_by):
        self.status = 'WAIVED'
        self.waived_by = waived_by
        self.waived_at = timezone.now()
        self.save(update_fields=['status', 'waived_by', 'waived_at', 'updated_at'])
