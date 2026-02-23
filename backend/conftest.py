"""
Nova — Shared Test Fixtures
================================
Reusable pytest fixtures for the entire test suite.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from django.test import RequestFactory
from django.utils import timezone

from apps.common.permissions import Role


# ---------------------------------------------------------------------------
# Request factory
# ---------------------------------------------------------------------------

@pytest.fixture
def rf():
    """Django RequestFactory."""
    return RequestFactory()


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def make_user(db):
    """
    Factory fixture that creates users with sensible defaults.
    Usage:
        user = make_user(email='test@example.com', role='USER')
    """
    from apps.identity.domain.models import User

    def _make_user(
        email=None,
        password='TestPass123!',
        first_name='Test',
        last_name='User',
        role='USER',
        is_active=True,
        is_verified=True,
        **kwargs,
    ):
        if email is None:
            email = f'user-{uuid.uuid4().hex[:8]}@nova.test'
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            **kwargs,
        )
        user.role = role
        user.is_active = is_active
        user.is_verified = is_verified
        user.verification_status = 'APPROVED' if is_verified else 'PENDING'
        user.save()
        return user

    return _make_user


@pytest.fixture
def user(make_user):
    """A standard active, verified regular user."""
    return make_user(
        email='alice@nova.test',
        first_name='Alice',
        last_name='Reader',
        role='USER',
    )


@pytest.fixture
def librarian(make_user):
    """An active librarian user."""
    return make_user(
        email='librarian@nova.test',
        first_name='Lauren',
        last_name='Librarian',
        role='LIBRARIAN',
    )


@pytest.fixture
def admin_user(make_user):
    """A super-admin user."""
    return make_user(
        email='admin@nova.test',
        first_name='Admin',
        last_name='Nova',
        role='SUPER_ADMIN',
    )


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_context(rf, user):
    """
    Returns a mock GraphQL info.context with an authenticated user.
    """
    request = rf.post('/graphql')
    request.user = user
    request.META['REMOTE_ADDR'] = '127.0.0.1'
    request.META['HTTP_USER_AGENT'] = 'TestRunner/1.0'

    context = MagicMock()
    context.user = user
    context.META = request.META
    return context


@pytest.fixture
def auth_context_for(rf):
    """
    Factory fixture: returns a mock context for any given user.
    Usage:
        ctx = auth_context_for(librarian)
    """
    def _make(target_user):
        request = rf.post('/graphql')
        request.user = target_user
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'TestRunner/1.0'

        context = MagicMock()
        context.user = target_user
        context.META = request.META
        return context

    return _make


# ---------------------------------------------------------------------------
# Catalog fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def make_author(db):
    from apps.catalog.domain.models import Author

    def _make(first_name='Arthur', last_name='Clarke', **kwargs):
        return Author.objects.create(first_name=first_name, last_name=last_name, **kwargs)

    return _make


@pytest.fixture
def make_category(db):
    from apps.catalog.domain.models import Category

    def _make(name='Science Fiction', slug='science-fiction', **kwargs):
        return Category.objects.create(name=name, slug=slug, **kwargs)

    return _make


@pytest.fixture
def make_book(db, make_author, make_category):
    from apps.catalog.domain.models import Book

    def _make(
        title='2001: A Space Odyssey',
        isbn_13='9780451457998',
        **kwargs,
    ):
        authors = kwargs.pop('authors', None)
        categories = kwargs.pop('categories', None)

        book = Book.objects.create(
            title=title,
            isbn_13=isbn_13,
            language='en',
            **kwargs,
        )

        if authors:
            book.authors.set(authors)
        else:
            author = make_author()
            book.authors.add(author)

        if categories:
            book.categories.set(categories)
        else:
            category = make_category()
            book.categories.add(category)

        return book

    return _make


@pytest.fixture
def make_book_copy(db, make_book):
    from apps.catalog.domain.models import BookCopy
    from apps.common.utils import generate_barcode

    def _make(book=None, **kwargs):
        if book is None:
            book = make_book()
        defaults = {
            'barcode': generate_barcode(),
            'condition': 'GOOD',
            'status': 'AVAILABLE',
            'branch': 'Main Library',
            'shelf_location': 'A-01-001',
        }
        defaults.update(kwargs)
        return BookCopy.objects.create(book=book, **defaults)

    return _make


# ---------------------------------------------------------------------------
# Circulation fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def make_borrow(db, user, make_book_copy):
    from apps.circulation.domain.models import BorrowRecord

    def _make(borrower=None, book_copy=None, **kwargs):
        if borrower is None:
            borrower = user
        if book_copy is None:
            book_copy = make_book_copy()
        defaults = {
            'status': 'ACTIVE',
            'due_date': timezone.now().date() + timedelta(days=14),
        }
        defaults.update(kwargs)
        record = BorrowRecord.objects.create(
            user=borrower,
            book_copy=book_copy,
            **defaults,
        )
        book_copy.status = 'BORROWED'
        book_copy.save(update_fields=['status'])
        return record

    return _make


# ---------------------------------------------------------------------------
# Engagement fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def make_engagement(db, user):
    from apps.engagement.domain.models import UserEngagement

    def _make(target_user=None, **kwargs):
        if target_user is None:
            target_user = user
        defaults = {
            'total_kp': 0,
            'level': 1,
            'level_title': 'Newcomer',
        }
        defaults.update(kwargs)
        eng, _ = UserEngagement.objects.get_or_create(
            user=target_user, defaults=defaults,
        )
        return eng

    return _make


# ---------------------------------------------------------------------------
# Event bus isolation
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolate_event_bus():
    """
    Clear all event bus subscribers before each test so that
    cross-context side-effects don't leak between tests.
    """
    from apps.common.event_bus import event_bus
    event_bus.clear()
    yield
    event_bus.clear()
