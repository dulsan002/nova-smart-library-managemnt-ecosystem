"""
Tests for the Circulation bounded context
==========================================
Covers: BorrowRecord, Reservation, Fine — model methods and lifecycle.
"""

import pytest
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from apps.circulation.domain.models import BorrowRecord, Reservation, Fine


# ─── BorrowRecord ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestBorrowRecord:

    def test_create_borrow(self, make_borrow):
        borrow = make_borrow()
        assert borrow.status == "ACTIVE"
        assert borrow.renewal_count == 0

    def test_is_overdue_false_within_period(self, make_borrow):
        borrow = make_borrow(due_date=timezone.now() + timedelta(days=7))
        assert borrow.is_overdue is False
        assert borrow.days_overdue == 0

    def test_is_overdue_true_past_due(self, make_borrow):
        borrow = make_borrow(due_date=timezone.now() - timedelta(days=3))
        assert borrow.is_overdue is True
        assert borrow.days_overdue >= 3

    def test_is_overdue_false_if_returned(self, make_borrow):
        borrow = make_borrow(
            due_date=timezone.now() - timedelta(days=5),
            status="RETURNED",
        )
        assert borrow.is_overdue is False

    def test_can_renew(self, make_borrow):
        borrow = make_borrow(due_date=timezone.now() + timedelta(days=7))
        assert borrow.can_renew is True

    def test_cannot_renew_if_overdue(self, make_borrow):
        borrow = make_borrow(due_date=timezone.now() - timedelta(days=1))
        assert borrow.can_renew is False

    def test_cannot_renew_max_reached(self, make_borrow):
        borrow = make_borrow(
            due_date=timezone.now() + timedelta(days=7),
            renewal_count=2,
            max_renewals=2,
        )
        assert borrow.can_renew is False

    def test_renew_extends_due_date(self, make_borrow):
        old_due = timezone.now() + timedelta(days=7)
        borrow = make_borrow(due_date=old_due)
        borrow.renew()
        borrow.refresh_from_db()
        assert borrow.renewal_count == 1
        assert borrow.due_date > old_due

    def test_renew_fails_when_not_allowed(self, make_borrow):
        borrow = make_borrow(
            due_date=timezone.now() - timedelta(days=1),
        )
        from apps.common.exceptions import BorrowingError
        with pytest.raises(BorrowingError):
            borrow.renew()

    def test_mark_returned(self, make_borrow, librarian):
        borrow = make_borrow()
        borrow.mark_returned(condition="GOOD", returned_to=librarian)
        borrow.refresh_from_db()
        assert borrow.status == "RETURNED"
        assert borrow.returned_at is not None
        assert borrow.condition_at_return == "GOOD"
        assert borrow.returned_to == librarian

    def test_mark_lost(self, make_borrow):
        borrow = make_borrow()
        borrow.mark_lost()
        borrow.refresh_from_db()
        assert borrow.status == "LOST"

    def test_mark_overdue(self, make_borrow):
        borrow = make_borrow()
        borrow.mark_overdue()
        borrow.refresh_from_db()
        assert borrow.status == "OVERDUE"

    def test_mark_overdue_only_from_active(self, make_borrow):
        borrow = make_borrow(status="RETURNED")
        borrow.mark_overdue()
        borrow.refresh_from_db()
        assert borrow.status == "RETURNED"  # unchanged


# ─── Reservation ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReservation:

    def test_create_reservation(self, user, make_book):
        book = make_book(isbn_13="9780000001000")
        res = Reservation.objects.create(user=user, book=book)
        assert res.status == "PENDING"

    def test_mark_ready(self, user, make_book, make_book_copy):
        book = make_book(isbn_13="9780000001001")
        copy = make_book_copy(book=book)
        res = Reservation.objects.create(user=user, book=book)
        res.mark_ready(copy)
        res.refresh_from_db()
        assert res.status == "READY"
        assert res.assigned_copy == copy
        assert res.ready_at is not None
        assert res.expires_at is not None

    def test_fulfill(self, user, make_book):
        book = make_book(isbn_13="9780000001002")
        res = Reservation.objects.create(user=user, book=book, status="READY")
        res.fulfill()
        res.refresh_from_db()
        assert res.status == "FULFILLED"
        assert res.fulfilled_at is not None

    def test_cancel(self, user, make_book):
        book = make_book(isbn_13="9780000001003")
        res = Reservation.objects.create(user=user, book=book)
        res.cancel()
        res.refresh_from_db()
        assert res.status == "CANCELLED"
        assert res.cancelled_at is not None

    def test_expire(self, user, make_book):
        book = make_book(isbn_13="9780000001004")
        res = Reservation.objects.create(user=user, book=book)
        res.expire()
        res.refresh_from_db()
        assert res.status == "EXPIRED"


# ─── Fine ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestFine:

    def test_create_fine(self, user, make_borrow):
        borrow = make_borrow()
        fine = Fine.objects.create(
            user=user,
            borrow_record=borrow,
            reason="OVERDUE",
            amount=Decimal("5.00"),
        )
        assert fine.status == "PENDING"
        assert fine.outstanding == Decimal("5.00")

    def test_pay_full(self, user, make_borrow):
        borrow = make_borrow()
        fine = Fine.objects.create(
            user=user, borrow_record=borrow,
            reason="OVERDUE", amount=Decimal("10.00"),
        )
        fine.pay()
        fine.refresh_from_db()
        assert fine.status == "PAID"
        assert fine.paid_amount == Decimal("10.00")
        assert fine.paid_at is not None

    def test_pay_partial(self, user, make_borrow):
        borrow = make_borrow()
        fine = Fine.objects.create(
            user=user, borrow_record=borrow,
            reason="OVERDUE", amount=Decimal("10.00"),
        )
        fine.pay(amount=Decimal("4.00"))
        fine.refresh_from_db()
        assert fine.status == "PARTIALLY_PAID"
        assert fine.outstanding == Decimal("6.00")

    def test_waive(self, user, librarian, make_borrow):
        borrow = make_borrow()
        fine = Fine.objects.create(
            user=user, borrow_record=borrow,
            reason="OVERDUE", amount=Decimal("5.00"),
        )
        fine.waive(waived_by=librarian)
        fine.refresh_from_db()
        assert fine.status == "WAIVED"
        assert fine.waived_by == librarian
        assert fine.waived_at is not None

    def test_str(self, user, make_borrow):
        borrow = make_borrow()
        fine = Fine.objects.create(
            user=user, borrow_record=borrow,
            reason="OVERDUE", amount=Decimal("7.50"),
        )
        s = str(fine)
        assert "7.50" in s
