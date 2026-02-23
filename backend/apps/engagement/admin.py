"""
Nova — Engagement Admin Configuration
"""

from django.contrib import admin
from apps.engagement.domain.models import (
    Achievement,
    DailyActivity,
    UserAchievement,
    UserEngagement,
)


@admin.register(UserEngagement)
class UserEngagementAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'total_kp', 'level', 'level_title',
        'current_streak', 'rank', 'updated_at',
    )
    list_filter = ('level',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = (
        'total_kp', 'level', 'level_title',
        'explorer_kp', 'scholar_kp', 'connector_kp',
        'achiever_kp', 'dedicated_kp',
        'current_streak', 'longest_streak', 'last_activity_date',
        'kp_earned_today', 'rank', 'rank_percentile',
        'created_at', 'updated_at',
    )
    ordering = ('-total_kp',)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'name', 'category', 'rarity',
        'kp_reward', 'is_active', 'sort_order',
    )
    list_filter = ('category', 'rarity', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('sort_order', 'name')


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'achievement', 'earned_at', 'kp_awarded', 'notified',
    )
    list_filter = ('notified', 'achievement__category')
    search_fields = ('user__email', 'achievement__name')
    readonly_fields = ('earned_at',)
    ordering = ('-earned_at',)


@admin.register(DailyActivity)
class DailyActivityAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'date', 'kp_earned', 'books_borrowed',
        'books_returned', 'reading_minutes', 'reviews_written',
    )
    list_filter = ('date',)
    search_fields = ('user__email',)
    readonly_fields = (
        'user', 'date', 'kp_earned', 'books_borrowed',
        'books_returned', 'reading_minutes', 'pages_read',
        'reviews_written', 'sessions_completed',
    )
    ordering = ('-date',)
