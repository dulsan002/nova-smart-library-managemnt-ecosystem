"""
Nova — Digital Content Admin
"""

from django.contrib import admin

from apps.digital_content.domain.models import (
    Bookmark,
    DigitalAsset,
    Highlight,
    ReadingSession,
    UserLibrary,
)


@admin.register(DigitalAsset)
class DigitalAssetAdmin(admin.ModelAdmin):
    list_display = ('book', 'asset_type', 'file_size_bytes', 'upload_completed', 'created_at')
    list_filter = ('asset_type', 'upload_completed', 'is_drm_protected')
    search_fields = ('book__title', 'narrator')
    readonly_fields = ('id', 'file_hash', 'created_at', 'updated_at')
    raw_id_fields = ('book', 'uploaded_by')


@admin.register(ReadingSession)
class ReadingSessionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'digital_asset', 'session_type', 'status',
        'duration_seconds', 'progress_percent', 'kp_awarded',
        'started_at',
    )
    list_filter = ('session_type', 'status')
    search_fields = ('user__email',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'digital_asset')
    date_hierarchy = 'started_at'


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('user', 'digital_asset', 'title', 'created_at')
    search_fields = ('user__email', 'title')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'digital_asset')


@admin.register(Highlight)
class HighlightAdmin(admin.ModelAdmin):
    list_display = ('user', 'digital_asset', 'color', 'created_at')
    search_fields = ('user__email', 'text')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'digital_asset')


@admin.register(UserLibrary)
class UserLibraryAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'digital_asset', 'overall_progress',
        'total_time_seconds', 'is_finished', 'is_favorite',
        'last_accessed_at',
    )
    list_filter = ('is_finished', 'is_favorite')
    search_fields = ('user__email',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'digital_asset')
