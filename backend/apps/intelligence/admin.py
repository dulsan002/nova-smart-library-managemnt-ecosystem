"""
Nova — Intelligence Admin Configuration
"""

from django.contrib import admin

from apps.intelligence.domain.models import (
    AIModelVersion,
    AIProviderConfig,
    Recommendation,
    SearchLog,
    TrendingBook,
    UserPreference,
)
from apps.intelligence.infrastructure.notification_engine import (
    UserNotification,
)


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'book', 'strategy', 'score',
        'is_clicked', 'is_dismissed', 'created_at',
    )
    list_filter = ('strategy', 'is_clicked', 'is_dismissed')
    search_fields = ('user__email', 'book__title')
    readonly_fields = (
        'user', 'book', 'strategy', 'score', 'explanation',
        'seed_book', 'is_clicked', 'clicked_at', 'is_dismissed',
        'created_at',
    )
    ordering = ('-created_at',)


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'reading_speed', 'last_computed_at', 'updated_at',
    )
    search_fields = ('user__email',)
    readonly_fields = (
        'preference_vector', 'last_computed_at',
    )


@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = (
        'query_text', 'user', 'results_count',
        'clicked_result_id', 'timestamp',
    )
    list_filter = ('timestamp',)
    search_fields = ('query_text', 'user__email')
    readonly_fields = (
        'user', 'query_text', 'filters_applied',
        'results_count', 'clicked_result_id',
        'session_id', 'ip_address', 'timestamp',
    )
    ordering = ('-timestamp',)


@admin.register(TrendingBook)
class TrendingBookAdmin(admin.ModelAdmin):
    list_display = (
        'book', 'period', 'rank', 'borrow_count',
        'review_count', 'score',
    )
    list_filter = ('period',)
    search_fields = ('book__title',)
    ordering = ('period', 'rank')


@admin.register(AIModelVersion)
class AIModelVersionAdmin(admin.ModelAdmin):
    list_display = (
        'model_type', 'version', 'name', 'is_active', 'created_at',
    )
    list_filter = ('model_type', 'is_active')
    search_fields = ('name', 'version')
    ordering = ('-created_at',)
    actions = ['activate_selected']

    @admin.action(description='Activate selected model version')
    def activate_selected(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request, 'Please select exactly one model version.', 'error',
            )
            return
        version = queryset.first()
        version.activate()
        self.message_user(
            request,
            f'Activated {version.model_type} v{version.version}.',
        )


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'notification_type', 'channel', 'priority',
        'title', 'is_read', 'is_sent', 'created_at',
    )
    list_filter = (
        'notification_type', 'channel', 'priority',
        'is_read', 'is_sent',
    )
    search_fields = ('user__email', 'title', 'body')
    readonly_fields = (
        'user', 'notification_type', 'channel', 'priority',
        'title', 'body', 'data', 'is_read', 'read_at',
        'is_sent', 'sent_at', 'scheduled_for', 'created_at',
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_sent']

    @admin.action(description='Mark selected notifications as read')
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(is_read=False).update(
            is_read=True, read_at=timezone.now(),
        )
        self.message_user(request, f'Marked {count} notifications as read.')

    @admin.action(description='Mark selected notifications as sent')
    def mark_as_sent(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(is_sent=False).update(
            is_sent=True, sent_at=timezone.now(),
        )
        self.message_user(request, f'Marked {count} notifications as sent.')


@admin.register(AIProviderConfig)
class AIProviderConfigAdmin(admin.ModelAdmin):
    list_display = (
        'display_name', 'provider', 'capability', 'model_name',
        'is_active', 'is_healthy', 'last_health_check',
    )
    list_filter = ('provider', 'capability', 'is_active', 'is_healthy')
    search_fields = ('display_name', 'model_name')
    readonly_fields = ('is_healthy', 'last_health_check', 'last_error')
    actions = ['activate_selected']

    @admin.action(description='Activate selected config (deactivates others for same capability)')
    def activate_selected(self, request, queryset):
        for config in queryset:
            config.activate()
        self.message_user(request, f'Activated {queryset.count()} config(s).')
