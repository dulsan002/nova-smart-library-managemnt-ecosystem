"""
Nova — Catalog GraphQL Types
================================
"""

import graphene
from graphene_django import DjangoObjectType

from apps.catalog.domain.models import Author, Book, BookCopy, BookReview, Category


class AuthorType(DjangoObjectType):
    full_name = graphene.String()

    class Meta:
        model = Author
        fields = (
            'id', 'first_name', 'last_name', 'biography',
            'birth_date', 'death_date', 'nationality', 'photo_url',
            'created_at',
        )

    def resolve_full_name(self, info):
        return self.full_name


class CategoryType(DjangoObjectType):
    is_root = graphene.Boolean()

    class Meta:
        model = Category
        fields = (
            'id', 'name', 'slug', 'description', 'parent',
            'children', 'icon', 'sort_order',
        )

    def resolve_is_root(self, info):
        return self.is_root


class BookCopyType(DjangoObjectType):
    class Meta:
        model = BookCopy
        fields = (
            'id', 'book', 'barcode', 'condition', 'status',
            'floor_number', 'shelf_number', 'shelf_location', 'branch',
            'acquisition_date', 'notes', 'created_at',
        )


class BookReviewType(DjangoObjectType):
    class Meta:
        model = BookReview
        fields = (
            'id', 'book', 'user', 'rating', 'title', 'content',
            'is_approved', 'created_at',
        )


class BookType(DjangoObjectType):
    author_names = graphene.String()
    is_available = graphene.Boolean()
    has_ebook = graphene.Boolean()
    has_audiobook = graphene.Boolean()
    copies = graphene.List(BookCopyType)
    reviews = graphene.List(BookReviewType, limit=graphene.Int(default_value=10))

    class Meta:
        model = Book
        fields = (
            'id', 'title', 'subtitle', 'isbn_10', 'isbn_13',
            'authors', 'categories', 'publisher', 'publication_date',
            'edition', 'language', 'page_count', 'description',
            'table_of_contents', 'cover_image_url', 'tags',
            'dewey_decimal', 'lcc_number',
            'total_copies', 'available_copies', 'total_borrows',
            'average_rating', 'rating_count',
            'added_by', 'created_at', 'updated_at',
        )

    def resolve_author_names(self, info):
        return self.author_names

    def resolve_is_available(self, info):
        return self.is_available

    def resolve_has_ebook(self, info):
        return self.digital_assets.filter(
            asset_type__in=['EBOOK_EPUB', 'EBOOK_PDF'],
            deleted_at__isnull=True,
        ).exists()

    def resolve_has_audiobook(self, info):
        return self.digital_assets.filter(
            asset_type='AUDIOBOOK',
            deleted_at__isnull=True,
        ).exists()

    def resolve_copies(self, info):
        return self.copies.filter(deleted_at__isnull=True)

    def resolve_reviews(self, info, limit=10):
        return self.reviews.filter(is_approved=True).order_by('-created_at')[:limit]


class BookEdgeType(graphene.ObjectType):
    """Relay-style edge wrapping a BookType with a cursor."""
    node = graphene.Field(BookType)
    cursor = graphene.String()


class BookConnectionType(graphene.ObjectType):
    edges = graphene.List(BookEdgeType)
    page_info = graphene.Field('apps.identity.presentation.types.PageInfoType')
    total_count = graphene.Int()
