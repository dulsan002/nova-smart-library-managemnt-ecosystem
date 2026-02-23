"""
Tests for the Catalog bounded context
=======================================
Covers: Author, Category, Book (aggregate root), BookCopy, BookReview.
"""

import pytest
from decimal import Decimal
from django.db import IntegrityError

from apps.catalog.domain.models import Author, Category, Book, BookCopy, BookReview


# ─── Author ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAuthor:

    def test_create_author(self):
        author = Author.objects.create(
            first_name="Robert",
            last_name="Martin",
            nationality="American",
        )
        assert author.full_name == "Robert Martin"
        assert str(author) == "Robert Martin"

    def test_author_ordering(self):
        Author.objects.create(first_name="Zara", last_name="Zeta")
        Author.objects.create(first_name="Alice", last_name="Alpha")
        names = list(Author.objects.values_list("last_name", flat=True))
        assert names == ["Alpha", "Zeta"]


# ─── Category ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCategory:

    def test_create_root_category(self):
        cat = Category.objects.create(name="Science", slug="science")
        assert cat.is_root is True
        assert str(cat) == "Science"

    def test_create_child_category(self):
        parent = Category.objects.create(name="Fiction", slug="fiction")
        child = Category.objects.create(name="Sci-Fi", slug="sci-fi", parent=parent)
        assert child.is_root is False
        assert child.parent == parent

    def test_get_ancestors(self):
        root = Category.objects.create(name="Root", slug="root")
        mid = Category.objects.create(name="Mid", slug="mid", parent=root)
        leaf = Category.objects.create(name="Leaf", slug="leaf", parent=mid)
        ancestors = leaf.get_ancestors()
        assert ancestors == [root, mid]

    def test_unique_slug(self):
        Category.objects.create(name="Test", slug="test")
        with pytest.raises(IntegrityError):
            Category.objects.create(name="Test2", slug="test")


# ─── Book ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBook:

    def test_create_book(self, make_book):
        book = make_book(title="Test Book", isbn_13="9780451457998")
        assert book.title == "Test Book"
        assert book.isbn_13 == "9780451457998"

    def test_unique_isbn13(self, make_book):
        make_book(isbn_13="9780132350884")
        with pytest.raises(IntegrityError):
            Book.objects.create(title="Dup", isbn_13="9780132350884", language="en")

    def test_book_m2m_authors(self, make_author, make_book):
        a1 = make_author(first_name="Author", last_name="One")
        a2 = make_author(first_name="Author", last_name="Two")
        book = make_book(isbn_13="9780000000001", authors=[a1, a2])
        assert book.authors.count() == 2

    def test_book_m2m_categories(self, make_category, make_book):
        c1 = make_category(name="Cat A", slug="cat-a")
        c2 = make_category(name="Cat B", slug="cat-b")
        book = make_book(isbn_13="9780000000002", categories=[c1, c2])
        assert book.categories.count() == 2

    def test_update_copy_counts(self, make_book, make_book_copy):
        book = make_book(isbn_13="9780000000003")
        make_book_copy(book=book, status="AVAILABLE")
        make_book_copy(book=book, status="BORROWED")
        make_book_copy(book=book, status="AVAILABLE")
        book.update_copy_counts()
        book.refresh_from_db()
        assert book.total_copies == 3
        assert book.available_copies == 2

    def test_increment_borrow_count(self, make_book):
        book = make_book(isbn_13="9780000000004")
        assert book.total_borrows == 0
        book.increment_borrow_count()
        book.refresh_from_db()
        assert book.total_borrows == 1

    def test_update_rating(self, make_book):
        book = make_book(isbn_13="9780000000005")
        book.update_rating(4.0)
        book.refresh_from_db()
        assert book.rating_count == 1
        assert book.average_rating == Decimal("4.00")

        book.update_rating(2.0)
        book.refresh_from_db()
        assert book.rating_count == 2
        assert book.average_rating == Decimal("3.00")

    def test_is_available_property(self, make_book):
        book = make_book(isbn_13="9780000000006")
        assert book.is_available is False  # no copies
        book.available_copies = 1
        book.save()
        assert book.is_available is True

    def test_soft_deletion(self, make_book):
        book = make_book(isbn_13="9780000000007")
        book.soft_delete()
        assert Book.objects.filter(isbn_13="9780000000007").count() == 0


# ─── BookCopy ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBookCopy:

    def test_create_book_copy(self, make_book_copy):
        copy = make_book_copy()
        assert copy.status == "AVAILABLE"
        assert copy.condition == "GOOD"

    def test_mark_borrowed(self, make_book_copy):
        copy = make_book_copy()
        copy.mark_borrowed()
        copy.refresh_from_db()
        assert copy.status == "BORROWED"

    def test_mark_returned(self, make_book_copy):
        copy = make_book_copy(status="BORROWED")
        copy.mark_returned()
        copy.refresh_from_db()
        assert copy.status == "AVAILABLE"

    def test_mark_reserved(self, make_book_copy):
        copy = make_book_copy()
        copy.mark_reserved()
        copy.refresh_from_db()
        assert copy.status == "RESERVED"

    def test_mark_lost(self, make_book_copy):
        copy = make_book_copy()
        copy.mark_lost()
        copy.refresh_from_db()
        assert copy.status == "LOST"

    def test_retire(self, make_book_copy):
        copy = make_book_copy()
        copy.retire()
        copy.refresh_from_db()
        assert copy.status == "RETIRED"

    def test_unique_barcode(self, make_book_copy, make_book):
        book = make_book(isbn_13="9780000000010")
        make_book_copy(book=book, barcode="UNIQUE-001")
        with pytest.raises(IntegrityError):
            BookCopy.objects.create(
                book=book, barcode="UNIQUE-001", status="AVAILABLE", condition="NEW"
            )

    def test_str(self, make_book_copy, make_book):
        book = make_book(title="My Book", isbn_13="9780000000011")
        copy = make_book_copy(book=book, barcode="BC-001")
        assert "My Book" in str(copy)
        assert "BC-001" in str(copy)


# ─── BookReview ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBookReview:

    def test_create_review(self, make_book, user):
        book = make_book(isbn_13="9780000000020")
        review = BookReview.objects.create(
            book=book, user=user, rating=4, title="Great!", content="Loved it."
        )
        assert review.rating == 4
        assert review.is_approved is True

    def test_rating_clamp_low(self, make_book, user):
        book = make_book(isbn_13="9780000000021")
        review = BookReview(book=book, user=user, rating=0)
        review.save()
        assert review.rating == 1

    def test_rating_clamp_high(self, make_book, user):
        book = make_book(isbn_13="9780000000022")
        review = BookReview(book=book, user=user, rating=10)
        review.save()
        assert review.rating == 5

    def test_unique_per_user_per_book(self, make_book, user):
        book = make_book(isbn_13="9780000000023")
        BookReview.objects.create(book=book, user=user, rating=3)
        with pytest.raises(IntegrityError):
            BookReview.objects.create(book=book, user=user, rating=5)
