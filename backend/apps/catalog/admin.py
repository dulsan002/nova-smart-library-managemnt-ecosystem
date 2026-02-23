"""
Nova — Catalog Admin Configuration
"""

from django.contrib import admin

from apps.catalog.domain.models import Author, Book, BookCopy, BookReview, Category


class BookCopyInline(admin.TabularInline):
    model = BookCopy
    extra = 0
    readonly_fields = ('id', 'barcode', 'created_at')
    fields = ('barcode', 'condition', 'status', 'shelf_location', 'branch')


class BookReviewInline(admin.TabularInline):
    model = BookReview
    extra = 0
    readonly_fields = ('id', 'user', 'rating', 'created_at')
    fields = ('user', 'rating', 'title', 'is_approved')


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'nationality', 'birth_date', 'created_at')
    search_fields = ('first_name', 'last_name')
    readonly_fields = ('id', 'created_at', 'updated_at')

    def full_name(self, obj):
        return obj.full_name


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'sort_order')
    list_filter = ('parent',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'isbn_13', 'publisher', 'language',
        'total_copies', 'available_copies', 'average_rating',
        'created_at',
    )
    list_filter = ('language', 'categories')
    search_fields = ('title', 'isbn_13', 'isbn_10', 'publisher')
    filter_horizontal = ('authors', 'categories')
    readonly_fields = (
        'id', 'total_copies', 'available_copies', 'total_borrows',
        'average_rating', 'rating_count', 'created_at', 'updated_at',
    )
    inlines = [BookCopyInline, BookReviewInline]
    date_hierarchy = 'created_at'


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'book', 'condition', 'status', 'branch', 'shelf_location')
    list_filter = ('status', 'condition', 'branch')
    search_fields = ('barcode', 'book__title')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('book',)


@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved')
    search_fields = ('book__title', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('book', 'user')
