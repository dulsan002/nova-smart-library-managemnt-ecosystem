"""
Nova — Catalog GraphQL Queries & Mutations
==============================================
"""

import graphene

from apps.common.decorators import audit_action, require_authentication, require_roles
from apps.common.pagination import paginate_queryset, PageInfo
from apps.common.permissions import Role

from apps.catalog.application import (
    AddBookCopyDTO,
    CreateBookDTO,
    CreateReviewDTO,
    SearchBooksUseCase,
    UpdateBookDTO,
    CreateBookUseCase,
    UpdateBookUseCase,
    AddBookCopyUseCase,
    SubmitBookReviewUseCase,
)
from apps.catalog.domain.models import Author, Book, BookCopy, Category
from apps.catalog.presentation.types import (
    AuthorType,
    BookConnectionType,
    BookCopyType,
    BookReviewType,
    BookType,
    CategoryType,
)


# ---------------------------------------------------------------------------
# Input types
# ---------------------------------------------------------------------------

class CreateBookInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    isbn_13 = graphene.String(required=True)
    isbn_10 = graphene.String()
    subtitle = graphene.String()
    publisher = graphene.String()
    publication_date = graphene.Date()
    edition = graphene.String()
    language = graphene.String(default_value='en')
    page_count = graphene.Int()
    description = graphene.String()
    cover_image_url = graphene.String()
    dewey_decimal = graphene.String()
    lcc_number = graphene.String()
    tags = graphene.List(graphene.String)
    author_ids = graphene.List(graphene.UUID)
    category_ids = graphene.List(graphene.UUID)


class UpdateBookInput(graphene.InputObjectType):
    title = graphene.String()
    subtitle = graphene.String()
    publisher = graphene.String()
    publication_date = graphene.Date()
    edition = graphene.String()
    language = graphene.String()
    page_count = graphene.Int()
    description = graphene.String()
    cover_image_url = graphene.String()
    dewey_decimal = graphene.String()
    lcc_number = graphene.String()
    tags = graphene.List(graphene.String)
    author_ids = graphene.List(graphene.UUID)
    category_ids = graphene.List(graphene.UUID)


class AddBookCopyInput(graphene.InputObjectType):
    book_id = graphene.UUID(required=True)
    barcode = graphene.String()
    condition = graphene.String(default_value='NEW')
    shelf_location = graphene.String()
    branch = graphene.String(default_value='main')
    acquisition_date = graphene.Date()
    acquisition_price = graphene.Float()
    supplier = graphene.String()


class CreateAuthorInput(graphene.InputObjectType):
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    biography = graphene.String()
    birth_date = graphene.Date()
    death_date = graphene.Date()
    nationality = graphene.String()
    photo_url = graphene.String()


class UpdateAuthorInput(graphene.InputObjectType):
    first_name = graphene.String()
    last_name = graphene.String()
    biography = graphene.String()
    birth_date = graphene.Date()
    death_date = graphene.Date()
    nationality = graphene.String()
    photo_url = graphene.String()


class CreateCategoryInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    slug = graphene.String(required=True)
    description = graphene.String()
    parent_id = graphene.UUID()
    icon = graphene.String()
    sort_order = graphene.Int(default_value=0)


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

class CreateBook(graphene.Mutation):
    class Arguments:
        input = CreateBookInput(required=True)

    Output = BookType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    @audit_action(action='CREATE', resource_type='Book')
    def mutate(self, info, input):
        use_case = CreateBookUseCase()
        dto = CreateBookDTO(
            title=input.title,
            isbn_13=input.isbn_13,
            isbn_10=input.isbn_10 or '',
            subtitle=input.subtitle or '',
            publisher=input.publisher or '',
            publication_date=input.publication_date,
            edition=input.edition or '',
            language=input.language,
            page_count=input.page_count,
            description=input.description or '',
            cover_image_url=input.cover_image_url or '',
            dewey_decimal=input.dewey_decimal or '',
            lcc_number=input.lcc_number or '',
            tags=input.tags or [],
            author_ids=input.author_ids or [],
            category_ids=input.category_ids or [],
        )
        return use_case.execute(dto, added_by=info.context.user)


class UpdateBook(graphene.Mutation):
    class Arguments:
        book_id = graphene.UUID(required=True)
        input = UpdateBookInput(required=True)

    Output = BookType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    @audit_action(action='UPDATE', resource_type='Book')
    def mutate(self, info, book_id, input):
        use_case = UpdateBookUseCase()
        dto = UpdateBookDTO(
            title=input.title,
            subtitle=input.subtitle,
            publisher=input.publisher,
            publication_date=input.publication_date,
            edition=input.edition,
            language=input.language,
            page_count=input.page_count,
            description=input.description,
            cover_image_url=input.cover_image_url,
            dewey_decimal=input.dewey_decimal,
            lcc_number=input.lcc_number,
            tags=input.tags,
            author_ids=input.author_ids,
            category_ids=input.category_ids,
        )
        return use_case.execute(book_id, dto)


class AddBookCopy(graphene.Mutation):
    class Arguments:
        input = AddBookCopyInput(required=True)

    Output = BookCopyType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    @audit_action(action='CREATE', resource_type='BookCopy')
    def mutate(self, info, input):
        use_case = AddBookCopyUseCase()
        from decimal import Decimal
        dto = AddBookCopyDTO(
            book_id=input.book_id,
            barcode=input.barcode or '',
            condition=input.condition,
            shelf_location=input.shelf_location or '',
            branch=input.branch,
            acquisition_date=input.acquisition_date,
            acquisition_price=Decimal(str(input.acquisition_price)) if input.acquisition_price else None,
            supplier=input.supplier or '',
        )
        return use_case.execute(dto)


class CreateAuthor(graphene.Mutation):
    class Arguments:
        input = CreateAuthorInput(required=True)

    Output = AuthorType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    @audit_action(action='CREATE', resource_type='Author')
    def mutate(self, info, input):
        return Author.objects.create(
            first_name=input.first_name,
            last_name=input.last_name,
            biography=input.biography or '',
            birth_date=input.birth_date,
            death_date=input.death_date,
            nationality=input.nationality or '',
            photo_url=input.photo_url or '',
        )


class UpdateAuthor(graphene.Mutation):
    class Arguments:
        author_id = graphene.UUID(required=True)
        input = UpdateAuthorInput(required=True)

    Output = AuthorType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN, Role.ASSISTANT])
    @audit_action(action='UPDATE', resource_type='Author')
    def mutate(self, info, author_id, input):
        try:
            author = Author.objects.get(pk=author_id)
        except Author.DoesNotExist:
            raise Exception('Author not found.')

        updatable = [
            'first_name', 'last_name', 'biography',
            'birth_date', 'death_date', 'nationality', 'photo_url',
        ]
        for field in updatable:
            val = getattr(input, field, None)
            if val is not None:
                setattr(author, field, val)
        author.save()
        return author


class DeleteAuthor(graphene.Mutation):
    class Arguments:
        author_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='DELETE', resource_type='Author')
    def mutate(self, info, author_id):
        try:
            author = Author.objects.get(pk=author_id)
        except Author.DoesNotExist:
            raise Exception('Author not found.')
        # Check if author has books
        if author.books.exists():
            raise Exception(
                f'Cannot delete author with {author.books.count()} associated book(s). '
                'Remove the author from all books first.'
            )
        author.delete()
        return DeleteAuthor(ok=True)


class DeleteBook(graphene.Mutation):
    """Soft-delete a book. Blocked if active borrows exist."""

    class Arguments:
        book_id = graphene.UUID(required=True)

    ok = graphene.Boolean()

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='DELETE', resource_type='Book')
    def mutate(self, info, book_id):
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            raise Exception('Book not found.')

        # Block if there are active borrows
        from apps.circulation.domain.models import BorrowRecord
        active_borrows = BorrowRecord.objects.filter(
            book_copy__book=book,
            status__in=['ACTIVE', 'OVERDUE'],
        ).count()
        if active_borrows:
            raise Exception(
                f'Cannot delete book with {active_borrows} active borrow(s). '
                'Return all copies first.'
            )

        book.soft_delete()
        return DeleteBook(ok=True)


class CreateCategory(graphene.Mutation):
    class Arguments:
        input = CreateCategoryInput(required=True)

    Output = CategoryType

    @require_authentication
    @require_roles([Role.SUPER_ADMIN, Role.LIBRARIAN])
    @audit_action(action='CREATE', resource_type='Category')
    def mutate(self, info, input):
        parent = None
        if input.parent_id:
            parent = Category.objects.filter(pk=input.parent_id).first()
        return Category.objects.create(
            name=input.name,
            slug=input.slug,
            description=input.description or '',
            parent=parent,
            icon=input.icon or '',
            sort_order=input.sort_order,
        )


class SubmitBookReview(graphene.Mutation):
    class Arguments:
        book_id = graphene.UUID(required=True)
        rating = graphene.Int(required=True)
        title = graphene.String()
        content = graphene.String()

    Output = BookReviewType

    @require_authentication
    @audit_action(action='CREATE', resource_type='BookReview')
    def mutate(self, info, book_id, rating, title='', content=''):
        use_case = SubmitBookReviewUseCase()
        dto = CreateReviewDTO(
            book_id=book_id,
            rating=rating,
            title=title,
            content=content,
        )
        return use_case.execute(info.context.user, dto)


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

class CatalogQuery(graphene.ObjectType):
    book = graphene.Field(BookType, id=graphene.UUID(required=True))
    book_by_isbn = graphene.Field(BookType, isbn=graphene.String(required=True))

    books = graphene.Field(
        BookConnectionType,
        first=graphene.Int(default_value=25),
        after=graphene.String(),
        query=graphene.String(),
        category_id=graphene.UUID(),
        author_id=graphene.UUID(),
        language=graphene.String(),
        available_only=graphene.Boolean(default_value=False),
        order_by=graphene.String(default_value='-created_at'),
    )

    authors = graphene.List(
        AuthorType,
        search=graphene.String(),
        limit=graphene.Int(default_value=50),
    )
    author = graphene.Field(AuthorType, id=graphene.UUID(required=True))

    categories = graphene.List(CategoryType, root_only=graphene.Boolean(default_value=False))
    category = graphene.Field(CategoryType, id=graphene.UUID())

    book_copies = graphene.List(
        BookCopyType,
        book_id=graphene.UUID(required=True),
        status=graphene.String(),
    )

    def resolve_book(self, info, id):
        try:
            return Book.objects.get(pk=id)
        except Book.DoesNotExist:
            return None

    def resolve_book_by_isbn(self, info, isbn):
        try:
            return Book.objects.get(isbn_13=isbn)
        except Book.DoesNotExist:
            try:
                return Book.objects.get(isbn_10=isbn)
            except Book.DoesNotExist:
                return None

    def resolve_books(self, info, first=25, after=None, query='',
                      category_id=None, author_id=None, language=None,
                      available_only=False, order_by='-created_at'):
        use_case = SearchBooksUseCase()
        qs = use_case.execute(
            query=query,
            category_id=category_id,
            author_id=author_id,
            language=language,
            available_only=available_only,
            order_by=order_by,
        )
        page = paginate_queryset(qs, first=first, after=after)
        from apps.common.pagination import PageInfo
        return BookConnectionType(
            edges=page['edges'],
            page_info=PageInfo(
                has_next_page=page['has_next_page'],
                has_previous_page=page['has_previous_page'],
                start_cursor=page['start_cursor'],
                end_cursor=page['end_cursor'],
            ),
            total_count=page['total_count'],
        )

    def resolve_authors(self, info, search=None, limit=50):
        qs = Author.objects.all()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )
        return qs[:limit]

    def resolve_author(self, info, id):
        try:
            return Author.objects.get(pk=id)
        except Author.DoesNotExist:
            return None

    def resolve_categories(self, info, root_only=False):
        qs = Category.objects.all()
        if root_only:
            qs = qs.filter(parent__isnull=True)
        return qs

    def resolve_category(self, info, id=None):
        if id:
            try:
                return Category.objects.get(pk=id)
            except Category.DoesNotExist:
                return None
        return None

    def resolve_book_copies(self, info, book_id, status=None):
        qs = BookCopy.objects.filter(book_id=book_id, deleted_at__isnull=True)
        if status:
            qs = qs.filter(status=status)
        return qs


# ---------------------------------------------------------------------------
# Mutation Root
# ---------------------------------------------------------------------------

class CatalogMutation(graphene.ObjectType):
    create_book = CreateBook.Field()
    update_book = UpdateBook.Field()
    delete_book = DeleteBook.Field()
    add_book_copy = AddBookCopy.Field()
    create_author = CreateAuthor.Field()
    update_author = UpdateAuthor.Field()
    delete_author = DeleteAuthor.Field()
    create_category = CreateCategory.Field()
    submit_book_review = SubmitBookReview.Field()
