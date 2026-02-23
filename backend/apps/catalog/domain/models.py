"""
Nova — Catalog Domain Models
================================
Core entities: Author, Category, Book (aggregate root), BookCopy.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.base_models import SoftDeletableManager, SoftDeletableModel, UUIDModel, VersionedModel


class Author(UUIDModel):
    """A book author or contributor."""

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    biography = models.TextField(blank=True, default='')
    birth_date = models.DateField(null=True, blank=True)
    death_date = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=100, blank=True, default='')
    photo_url = models.URLField(max_length=500, blank=True, default='')

    class Meta:
        db_table = 'catalog_author'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name'], name='idx_author_name'),
        ]

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'.strip()

    def __str__(self):
        return self.full_name


class Category(UUIDModel):
    """
    Hierarchical book category (supports tree via parent FK).
    """

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, default='')
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
    )
    icon = models.CharField(max_length=50, blank=True, default='',
                            help_text='Icon identifier for the UI.')
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'catalog_category'
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    @property
    def is_root(self) -> bool:
        return self.parent is None

    def get_ancestors(self):
        """Return ancestor chain from root to self (excluding self)."""
        ancestors = []
        current = self.parent
        while current is not None:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors


class Book(UUIDModel, SoftDeletableModel, VersionedModel):
    """
    Aggregate root for the catalog context.
    Represents a bibliographic title (not a physical copy).
    """

    title = models.CharField(max_length=500)
    subtitle = models.CharField(max_length=500, blank=True, default='')
    isbn_10 = models.CharField(max_length=10, blank=True, default='', db_index=True)
    isbn_13 = models.CharField(max_length=13, unique=True, db_index=True)

    # Relationships
    authors = models.ManyToManyField(Author, related_name='books', blank=True)
    categories = models.ManyToManyField(Category, related_name='books', blank=True)

    # Publishing info
    publisher = models.CharField(max_length=300, blank=True, default='')
    publication_date = models.DateField(null=True, blank=True)
    edition = models.CharField(max_length=50, blank=True, default='')
    language = models.CharField(max_length=10, default='en')
    page_count = models.PositiveIntegerField(null=True, blank=True)

    # Description & metadata
    description = models.TextField(blank=True, default='')
    table_of_contents = models.TextField(blank=True, default='')
    cover_image_url = models.URLField(max_length=500, blank=True, default='')
    tags = models.JSONField(default=list, blank=True)

    # Managers
    objects = SoftDeletableManager()
    all_objects = models.Manager()

    # Dewey Decimal / Library of Congress classification
    dewey_decimal = models.CharField(max_length=20, blank=True, default='')
    lcc_number = models.CharField(max_length=50, blank=True, default='')

    # Stats (denormalized for performance)
    total_copies = models.PositiveIntegerField(default=0)
    available_copies = models.PositiveIntegerField(default=0)
    total_borrows = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)

    # AI
    embedding_vector = models.JSONField(
        null=True, blank=True,
        help_text='Semantic embedding for AI recommendations.',
    )

    # Added by
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='added_books',
    )

    class Meta:
        db_table = 'catalog_book'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title'], name='idx_book_title'),
            models.Index(fields=['isbn_13'], name='idx_book_isbn13'),
            models.Index(fields=['isbn_10'], name='idx_book_isbn10'),
            models.Index(fields=['publisher'], name='idx_book_publisher'),
            models.Index(fields=['language'], name='idx_book_language'),
            models.Index(fields=['-total_borrows'], name='idx_book_popularity'),
            models.Index(fields=['-average_rating'], name='idx_book_rating'),
            models.Index(fields=['-created_at'], name='idx_book_created'),
        ]

    def __str__(self):
        return self.title

    def update_copy_counts(self):
        """Recalculate denormalized copy counts from BookCopy records."""
        copies = self.copies.filter(deleted_at__isnull=True)
        self.total_copies = copies.count()
        self.available_copies = copies.filter(status='AVAILABLE').count()
        self.save(update_fields=['total_copies', 'available_copies', 'updated_at'])

    def update_rating(self, new_rating: float):
        """Incrementally update average rating."""
        from decimal import Decimal
        total = self.average_rating * self.rating_count + Decimal(str(new_rating))
        self.rating_count += 1
        self.average_rating = round(total / self.rating_count, 2)
        self.save(update_fields=['average_rating', 'rating_count', 'updated_at'])

    def increment_borrow_count(self):
        self.total_borrows += 1
        self.save(update_fields=['total_borrows', 'updated_at'])

    @property
    def is_available(self) -> bool:
        return self.available_copies > 0

    @property
    def author_names(self) -> str:
        return ', '.join(a.full_name for a in self.authors.all())


class BookCopy(UUIDModel, SoftDeletableModel):
    """
    A physical copy of a book.
    Each copy has a unique barcode and tracks condition + status.
    """

    CONDITION_CHOICES = [
        ('NEW', 'New'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('WORN', 'Worn'),
        ('DAMAGED', 'Damaged'),
    ]

    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('BORROWED', 'Borrowed'),
        ('RESERVED', 'Reserved'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('LOST', 'Lost'),
        ('RETIRED', 'Retired'),
    ]

    # Managers
    objects = SoftDeletableManager()
    all_objects = models.Manager()

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    barcode = models.CharField(max_length=50, unique=True, db_index=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='NEW')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')

    # Location
    floor_number = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='Floor number where this copy is shelved.',
    )
    shelf_number = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Shelf identifier, e.g. A3, B12.',
    )
    shelf_location = models.CharField(max_length=100, blank=True, default='',
                                      help_text='Legacy free-text location field.')
    branch = models.CharField(max_length=100, blank=True, default='main',
                              help_text='Library branch identifier.')

    # Acquisition
    acquisition_date = models.DateField(null=True, blank=True)
    acquisition_price = models.DecimalField(max_digits=10, decimal_places=2,
                                            null=True, blank=True)
    supplier = models.CharField(max_length=200, blank=True, default='')

    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'catalog_book_copy'
        ordering = ['barcode']
        verbose_name_plural = 'Book Copies'
        indexes = [
            models.Index(fields=['barcode'], name='idx_copy_barcode'),
            models.Index(fields=['book', 'status'], name='idx_copy_book_status'),
            models.Index(fields=['status'], name='idx_copy_status'),
            models.Index(fields=['branch'], name='idx_copy_branch'),
        ]

    def __str__(self):
        return f'{self.book.title} [{self.barcode}]'

    def mark_borrowed(self):
        self.status = 'BORROWED'
        self.save(update_fields=['status', 'updated_at'])
        self.book.update_copy_counts()

    def mark_returned(self):
        self.status = 'AVAILABLE'
        self.save(update_fields=['status', 'updated_at'])
        self.book.update_copy_counts()

    def mark_reserved(self):
        self.status = 'RESERVED'
        self.save(update_fields=['status', 'updated_at'])
        self.book.update_copy_counts()

    def mark_lost(self):
        self.status = 'LOST'
        self.save(update_fields=['status', 'updated_at'])
        self.book.update_copy_counts()

    def retire(self):
        self.status = 'RETIRED'
        self.save(update_fields=['status', 'updated_at'])
        self.book.update_copy_counts()


class BookReview(UUIDModel):
    """User review / rating for a book."""

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='book_reviews',
    )
    rating = models.PositiveSmallIntegerField(
        help_text='Rating 1-5',
    )
    title = models.CharField(max_length=200, blank=True, default='')
    content = models.TextField(blank=True, default='')
    is_approved = models.BooleanField(default=True)

    class Meta:
        db_table = 'catalog_book_review'
        ordering = ['-created_at']
        unique_together = [('book', 'user')]
        indexes = [
            models.Index(fields=['book', '-created_at'], name='idx_review_book_time'),
        ]

    def __str__(self):
        return f'{self.user} → {self.book.title} ({self.rating}★)'

    def save(self, *args, **kwargs):
        # Clamp rating
        if self.rating < 1:
            self.rating = 1
        elif self.rating > 5:
            self.rating = 5
        super().save(*args, **kwargs)
