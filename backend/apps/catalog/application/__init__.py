"""
Nova — Catalog Application Services
=======================================
Use cases for book management operations.
"""

import logging
from typing import Optional
from uuid import UUID

from django.db import transaction
from django.db.models import Q

from apps.common.event_bus import DomainEvent, EventBus, EventTypes
from apps.common.exceptions import ConflictError, NotFoundError, ValidationError
from apps.common.utils import generate_barcode
from apps.common.validators import validate_isbn

from apps.catalog.domain.models import Author, Book, BookCopy, BookReview, Category

logger = logging.getLogger('nova.catalog')


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class CreateBookDTO:
    title: str
    isbn_13: str
    isbn_10: str = ''
    subtitle: str = ''
    publisher: str = ''
    publication_date: Optional[date] = None
    edition: str = ''
    language: str = 'en'
    page_count: Optional[int] = None
    description: str = ''
    cover_image_url: str = ''
    dewey_decimal: str = ''
    lcc_number: str = ''
    tags: list = field(default_factory=list)
    author_ids: list = field(default_factory=list)
    category_ids: list = field(default_factory=list)


@dataclass(frozen=True)
class UpdateBookDTO:
    title: Optional[str] = None
    subtitle: Optional[str] = None
    publisher: Optional[str] = None
    publication_date: Optional[date] = None
    edition: Optional[str] = None
    language: Optional[str] = None
    page_count: Optional[int] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    dewey_decimal: Optional[str] = None
    lcc_number: Optional[str] = None
    tags: Optional[list] = None
    author_ids: Optional[list] = None
    category_ids: Optional[list] = None


@dataclass(frozen=True)
class AddBookCopyDTO:
    book_id: UUID
    barcode: str = ''
    condition: str = 'NEW'
    shelf_location: str = ''
    branch: str = 'main'
    acquisition_date: Optional[date] = None
    acquisition_price: Optional[Decimal] = None
    supplier: str = ''


@dataclass(frozen=True)
class CreateReviewDTO:
    book_id: UUID
    rating: int
    title: str = ''
    content: str = ''


# ---------------------------------------------------------------------------
# Use Cases
# ---------------------------------------------------------------------------

class CreateBookUseCase:
    """Creates a new book in the catalog."""

    @transaction.atomic
    def execute(self, dto: CreateBookDTO, added_by=None) -> Book:
        validate_isbn(dto.isbn_13)

        if Book.objects.filter(isbn_13=dto.isbn_13).exists():
            raise ConflictError(
                message=f'A book with ISBN {dto.isbn_13} already exists.',
                code='DUPLICATE_ISBN',
            )

        book = Book.objects.create(
            title=dto.title,
            subtitle=dto.subtitle,
            isbn_13=dto.isbn_13,
            isbn_10=dto.isbn_10,
            publisher=dto.publisher,
            publication_date=dto.publication_date,
            edition=dto.edition,
            language=dto.language,
            page_count=dto.page_count,
            description=dto.description,
            cover_image_url=dto.cover_image_url,
            dewey_decimal=dto.dewey_decimal,
            lcc_number=dto.lcc_number,
            tags=dto.tags,
            added_by=added_by,
        )

        if dto.author_ids:
            book.authors.set(Author.objects.filter(pk__in=dto.author_ids))
        if dto.category_ids:
            book.categories.set(Category.objects.filter(pk__in=dto.category_ids))

        EventBus.publish(DomainEvent(
            event_type=EventTypes.BOOK_ADDED,
            payload={'title': book.title, 'isbn': book.isbn_13},
            metadata={'aggregate_id': str(book.id)},
        ))
        logger.info('Book created', extra={'book_id': str(book.id), 'isbn': book.isbn_13})
        return book


class UpdateBookUseCase:
    """Updates book metadata."""

    @transaction.atomic
    def execute(self, book_id: UUID, dto: UpdateBookDTO) -> Book:
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            raise NotFoundError(message='Book not found.', code='BOOK_NOT_FOUND')

        for field_name in (
            'title', 'subtitle', 'publisher', 'publication_date',
            'edition', 'language', 'page_count', 'description',
            'cover_image_url', 'dewey_decimal', 'lcc_number', 'tags',
        ):
            value = getattr(dto, field_name, None)
            if value is not None:
                setattr(book, field_name, value)

        book.save()

        if dto.author_ids is not None:
            book.authors.set(Author.objects.filter(pk__in=dto.author_ids))
        if dto.category_ids is not None:
            book.categories.set(Category.objects.filter(pk__in=dto.category_ids))

        EventBus.publish(DomainEvent(
            event_type=EventTypes.BOOK_UPDATED,
            payload={'title': book.title},
            metadata={'aggregate_id': str(book.id)},
        ))
        return book


class AddBookCopyUseCase:
    """Adds a physical copy to a book."""

    @transaction.atomic
    def execute(self, dto: AddBookCopyDTO) -> BookCopy:
        try:
            book = Book.objects.get(pk=dto.book_id)
        except Book.DoesNotExist:
            raise NotFoundError(message='Book not found.', code='BOOK_NOT_FOUND')

        barcode = dto.barcode or generate_barcode()

        if BookCopy.objects.filter(barcode=barcode).exists():
            raise ConflictError(
                message=f'Barcode {barcode} already exists.',
                code='DUPLICATE_BARCODE',
            )

        copy = BookCopy.objects.create(
            book=book,
            barcode=barcode,
            condition=dto.condition,
            shelf_location=dto.shelf_location,
            branch=dto.branch,
            acquisition_date=dto.acquisition_date,
            acquisition_price=dto.acquisition_price,
            supplier=dto.supplier,
        )

        book.update_copy_counts()

        EventBus.publish(DomainEvent(
            event_type=EventTypes.COPY_ADDED,
            payload={'copy_id': str(copy.id), 'barcode': barcode},
            metadata={'aggregate_id': str(book.id)},
        ))
        logger.info('Book copy added', extra={
            'book_id': str(book.id), 'copy_id': str(copy.id),
        })
        return copy


class SearchBooksUseCase:
    """Full-text + filtered book search."""

    def execute(
        self,
        query: str = '',
        category_id: UUID = None,
        author_id: UUID = None,
        language: str = None,
        available_only: bool = False,
        order_by: str = '-created_at',
    ):
        qs = Book.objects.all()

        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(subtitle__icontains=query) |
                Q(isbn_13__icontains=query) |
                Q(isbn_10__icontains=query) |
                Q(description__icontains=query) |
                Q(authors__first_name__icontains=query) |
                Q(authors__last_name__icontains=query)
            ).distinct()

        if category_id:
            qs = qs.filter(categories__id=category_id)
        if author_id:
            qs = qs.filter(authors__id=author_id)
        if language:
            qs = qs.filter(language=language)
        if available_only:
            qs = qs.filter(available_copies__gt=0)

        allowed_orders = {
            '-created_at', 'created_at', 'title', '-title',
            '-total_borrows', '-average_rating', 'publication_date',
        }
        if order_by not in allowed_orders:
            order_by = '-created_at'

        return qs.order_by(order_by)


class SubmitBookReviewUseCase:
    """Submit or update a book review."""

    @transaction.atomic
    def execute(self, user, dto: CreateReviewDTO) -> BookReview:
        try:
            book = Book.objects.get(pk=dto.book_id)
        except Book.DoesNotExist:
            raise NotFoundError(message='Book not found.', code='BOOK_NOT_FOUND')

        if dto.rating < 1 or dto.rating > 5:
            raise ValidationError(
                message='Rating must be between 1 and 5.',
                code='INVALID_RATING',
            )

        review, created = BookReview.objects.update_or_create(
            book=book,
            user=user,
            defaults={
                'rating': dto.rating,
                'title': dto.title,
                'content': dto.content,
            },
        )

        # Recalculate average rating
        from django.db.models import Avg
        avg = BookReview.objects.filter(book=book).aggregate(avg=Avg('rating'))['avg'] or 0
        count = BookReview.objects.filter(book=book).count()
        book.average_rating = round(avg, 2)
        book.rating_count = count
        book.save(update_fields=['average_rating', 'rating_count', 'updated_at'])

        EventBus.publish(DomainEvent(
            event_type=EventTypes.BOOK_REVIEWED,
            payload={'user_id': str(user.id), 'rating': dto.rating},
            metadata={'aggregate_id': str(book.id)},
        ))
        return review
