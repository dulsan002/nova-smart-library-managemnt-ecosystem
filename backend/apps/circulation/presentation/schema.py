"""
Nova — Circulation GraphQL Schema
=====================================
Reservation-first flow:
  reserveBook  →  confirmPickup  →  renewBorrow  →  returnBook
Queries for borrows, reservations, fines, and bans.
"""

import graphene
from graphene_django import DjangoObjectType

from apps.common.decorators import audit_action, require_authentication, require_roles
from apps.common.pagination import paginate_queryset, PageInfo
from apps.common.permissions import Role

from apps.circulation.application import (
    CancelReservationUseCase,
    ConfirmPickupUseCase,
    LiftBanUseCase,
    PayFineUseCase,
    RenewBorrowUseCase,
    ReserveBookUseCase,
    ReturnBookUseCase,
    WaiveFineUseCase,
)
from apps.circulation.domain.models import (
    BorrowRecord,
    Fine,
    Reservation,
    ReservationBan,
)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class BorrowRecordType(DjangoObjectType):
    is_overdue = graphene.Boolean()
    days_overdue = graphene.Int()
    can_renew = graphene.Boolean()

    class Meta:
        model = BorrowRecord
        fields = (
            'id', 'user', 'book_copy', 'reservation', 'status',
            'borrowed_at', 'due_date', 'returned_at',
            'renewal_count', 'max_renewals',
            'condition_at_borrow', 'condition_at_return',
            'issued_by', 'returned_to', 'notes',
            'created_at', 'updated_at',
        )

    def resolve_is_overdue(self, info):
        return self.is_overdue

    def resolve_days_overdue(self, info):
        return self.days_overdue

    def resolve_can_renew(self, info):
        return self.can_renew


class ReservationType(DjangoObjectType):
    pickup_location = graphene.String()
    hours_until_expiry = graphene.Float()

    class Meta:
        model = Reservation
        fields = (
            'id', 'user', 'book', 'assigned_copy', 'status',
            'reserved_at', 'ready_at', 'expires_at',
            'fulfilled_at', 'cancelled_at',
            'queue_position', 'notification_sent',
            'created_at',
        )

    def resolve_pickup_location(self, info):
        return self.pickup_location

    def resolve_hours_until_expiry(self, info):
        return round(self.hours_until_expiry, 1)


class ReservationBanType(DjangoObjectType):
    is_active = graphene.Boolean()

    class Meta:
        model = ReservationBan
        fields = (
            'id', 'user', 'reason', 'no_show_count',
            'banned_at', 'expires_at', 'lifted_at', 'lifted_by',
            'created_at',
        )

    def resolve_is_active(self, info):
        return self.is_active


class FineType(DjangoObjectType):
    outstanding = graphene.Float()

    class Meta:
        model = Fine
        fields = (
            'id', 'user', 'borrow_record', 'reason', 'status',
            'amount', 'paid_amount', 'currency', 'description',
            'issued_at', 'paid_at', 'waived_by', 'waived_at',
            'created_at',
        )

    def resolve_outstanding(self, info):
        return float(self.outstanding)


class BorrowEdgeType(graphene.ObjectType):
    """Relay-style edge wrapping a BorrowRecordType with a cursor."""
    node = graphene.Field(BorrowRecordType)
    cursor = graphene.String()


class BorrowConnectionType(graphene.ObjectType):
    edges = graphene.List(BorrowEdgeType)
    page_info = graphene.Field('apps.identity.presentation.types.PageInfoType')
    total_count = graphene.Int()


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

class ReserveBook(graphene.Mutation):
    """Reserve a book. If a copy is available it is assigned immediately (12 h pickup)."""

    class Arguments:
        book_id = graphene.UUID(required=True)

    Output = ReservationType

    @require_authentication
    @audit_action(action='RESERVE', resource_type='Reservation')
    def mutate(self, info, book_id):
        use_case = ReserveBookUseCase()
        return use_case.execute(user=info.context.user, book_id=book_id)


class ConfirmPickup(graphene.Mutation):
    """Librarian confirms physical pickup → creates BorrowRecord."""

    class Arguments:
        reservation_id = graphene.UUID(required=True)

    Output = BorrowRecordType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    @audit_action(action='CONFIRM_PICKUP', resource_type='BorrowRecord')
    def mutate(self, info, reservation_id):
        use_case = ConfirmPickupUseCase()
        return use_case.execute(
            reservation_id=reservation_id,
            issued_by=info.context.user,
        )


class ReturnBook(graphene.Mutation):
    """Librarian confirms physical return."""

    class Arguments:
        borrow_id = graphene.UUID(required=True)
        condition = graphene.String()

    Output = BorrowRecordType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    @audit_action(action='RETURN', resource_type='BorrowRecord')
    def mutate(self, info, borrow_id, condition=''):
        use_case = ReturnBookUseCase()
        return use_case.execute(
            borrow_id=borrow_id,
            condition=condition,
            returned_to=info.context.user,
        )


class RenewBorrow(graphene.Mutation):
    """User renews a borrow via the app."""

    class Arguments:
        borrow_id = graphene.UUID(required=True)

    Output = BorrowRecordType

    @require_authentication
    @audit_action(action='RENEW', resource_type='BorrowRecord')
    def mutate(self, info, borrow_id):
        use_case = RenewBorrowUseCase()
        return use_case.execute(borrow_id=borrow_id, user=info.context.user)


class CancelReservation(graphene.Mutation):
    class Arguments:
        reservation_id = graphene.UUID(required=True)

    Output = ReservationType

    @require_authentication
    @audit_action(action='DELETE', resource_type='Reservation')
    def mutate(self, info, reservation_id):
        use_case = CancelReservationUseCase()
        return use_case.execute(
            reservation_id=reservation_id,
            user=info.context.user,
        )


class PayFine(graphene.Mutation):
    class Arguments:
        fine_id = graphene.UUID(required=True)
        amount = graphene.Float()

    Output = FineType

    @require_authentication
    @audit_action(action='FINE_PAY', resource_type='Fine')
    def mutate(self, info, fine_id, amount=None):
        from decimal import Decimal
        use_case = PayFineUseCase()
        dec_amount = Decimal(str(amount)) if amount else None
        return use_case.execute(fine_id, dec_amount)


class WaiveFine(graphene.Mutation):
    class Arguments:
        fine_id = graphene.UUID(required=True)

    Output = FineType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='FINE_WAIVE', resource_type='Fine')
    def mutate(self, info, fine_id):
        use_case = WaiveFineUseCase()
        return use_case.execute(fine_id, info.context.user)


class LiftReservationBan(graphene.Mutation):
    """Staff lifts a reservation ban early."""

    class Arguments:
        ban_id = graphene.UUID(required=True)

    Output = ReservationBanType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='LIFT_BAN', resource_type='ReservationBan')
    def mutate(self, info, ban_id):
        use_case = LiftBanUseCase()
        return use_case.execute(ban_id, info.context.user)


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

class CirculationQuery(graphene.ObjectType):
    # User queries
    my_borrows = graphene.List(
        BorrowRecordType,
        status=graphene.String(),
        limit=graphene.Int(default_value=20),
    )
    my_reservations = graphene.List(ReservationType)
    my_fines = graphene.List(FineType, status=graphene.String())
    my_reservation_ban = graphene.Field(ReservationBanType)

    # Admin queries
    borrow_record = graphene.Field(BorrowRecordType, id=graphene.UUID(required=True))
    all_borrows = graphene.Field(
        BorrowConnectionType,
        first=graphene.Int(default_value=25),
        after=graphene.String(),
        status=graphene.String(),
        user_id=graphene.UUID(),
    )
    overdue_borrows = graphene.List(
        BorrowRecordType,
        limit=graphene.Int(default_value=50),
    )
    pending_pickups = graphene.List(
        ReservationType,
        limit=graphene.Int(default_value=50),
        description='Reservations in READY status awaiting physical pickup.',
    )

    # Admin: view any user's borrows / fines / reservations
    user_borrows = graphene.List(
        BorrowRecordType,
        user_id=graphene.UUID(required=True),
        status=graphene.String(),
        limit=graphene.Int(default_value=50),
        description='All borrows for a specific user (admin only).',
    )
    user_fines = graphene.List(
        FineType,
        user_id=graphene.UUID(required=True),
        status=graphene.String(),
        description='All fines for a specific user (admin only).',
    )
    user_reservations = graphene.List(
        ReservationType,
        user_id=graphene.UUID(required=True),
        description='All reservations for a specific user (admin only).',
    )

    @require_authentication
    def resolve_my_borrows(self, info, status=None, limit=20):
        qs = BorrowRecord.objects.filter(
            user=info.context.user,
        ).select_related('book_copy', 'book_copy__book')
        if status:
            qs = qs.filter(status=status)
        return qs[:limit]

    @require_authentication
    def resolve_my_reservations(self, info):
        return Reservation.objects.filter(
            user=info.context.user,
            status__in=['PENDING', 'READY'],
        ).select_related('book', 'assigned_copy')

    @require_authentication
    def resolve_my_fines(self, info, status=None):
        qs = Fine.objects.filter(user=info.context.user)
        if status:
            qs = qs.filter(status=status)
        return qs

    @require_authentication
    def resolve_my_reservation_ban(self, info):
        from django.utils import timezone
        return ReservationBan.objects.filter(
            user=info.context.user,
            expires_at__gt=timezone.now(),
            lifted_at__isnull=True,
        ).first()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    def resolve_borrow_record(self, info, id):
        try:
            return BorrowRecord.objects.get(pk=id)
        except BorrowRecord.DoesNotExist:
            return None

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    def resolve_all_borrows(self, info, first=25, after=None, status=None, user_id=None):
        qs = BorrowRecord.objects.all()
        if status:
            qs = qs.filter(status=status)
        if user_id:
            qs = qs.filter(user_id=user_id)
        page = paginate_queryset(qs, first=first, after=after)
        return BorrowConnectionType(
            edges=page['edges'],
            page_info=PageInfo(
                has_next_page=page['has_next_page'],
                has_previous_page=page['has_previous_page'],
                start_cursor=page['start_cursor'],
                end_cursor=page['end_cursor'],
            ),
            total_count=page['total_count'],
        )

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    def resolve_overdue_borrows(self, info, limit=50):
        return BorrowRecord.objects.filter(status='OVERDUE').order_by('due_date')[:limit]

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    def resolve_pending_pickups(self, info, limit=50):
        return Reservation.objects.filter(
            status='READY',
        ).select_related('user', 'book', 'assigned_copy').order_by('expires_at')[:limit]

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_user_borrows(self, info, user_id, status=None, limit=50):
        qs = BorrowRecord.objects.filter(user_id=user_id).select_related(
            'book_copy', 'book_copy__book',
        ).order_by('-borrowed_at')
        if status:
            qs = qs.filter(status=status)
        return qs[:limit]

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_user_fines(self, info, user_id, status=None):
        qs = Fine.objects.filter(user_id=user_id).select_related(
            'borrow_record', 'borrow_record__book_copy__book',
        ).order_by('-created_at')
        if status:
            qs = qs.filter(status=status)
        return qs

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    def resolve_user_reservations(self, info, user_id):
        return Reservation.objects.filter(
            user_id=user_id,
        ).select_related('book', 'assigned_copy').order_by('-reserved_at')


# ---------------------------------------------------------------------------
# Mutation root
# ---------------------------------------------------------------------------

class CirculationMutation(graphene.ObjectType):
    reserve_book = ReserveBook.Field()
    confirm_pickup = ConfirmPickup.Field()
    return_book = ReturnBook.Field()
    renew_borrow = RenewBorrow.Field()
    cancel_reservation = CancelReservation.Field()
    pay_fine = PayFine.Field()
    waive_fine = WaiveFine.Field()
    lift_reservation_ban = LiftReservationBan.Field()
