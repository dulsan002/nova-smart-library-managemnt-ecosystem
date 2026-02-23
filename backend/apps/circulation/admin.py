"""
Nova — Circulation Admin
"""

from django.contrib import admin

from apps.circulation.domain.models import BorrowRecord, Fine, Reservation


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'book_copy', 'status',
        'borrowed_at', 'due_date', 'returned_at',
        'renewal_count',
    )
    list_filter = ('status',)
    search_fields = ('user__email', 'book_copy__barcode', 'book_copy__book__title')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'book_copy', 'issued_by', 'returned_to')
    date_hierarchy = 'borrowed_at'


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'book', 'status',
        'queue_position', 'reserved_at', 'expires_at',
    )
    list_filter = ('status',)
    search_fields = ('user__email', 'book__title')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'book', 'assigned_copy')


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'reason', 'status',
        'amount', 'paid_amount', 'currency', 'issued_at',
    )
    list_filter = ('reason', 'status')
    search_fields = ('user__email',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'borrow_record', 'waived_by')
    date_hierarchy = 'issued_at'
