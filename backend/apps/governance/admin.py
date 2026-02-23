"""
Nova — Governance Admin Configuration
"""

from django.contrib import admin

from apps.governance.domain.models import AuditLog, KPLedger, SecurityEvent


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        'action', 'resource_type', 'resource_id',
        'actor_email', 'ip_address', 'created_at',
    )
    list_filter = ('action', 'resource_type')
    search_fields = ('actor_email', 'resource_id', 'description')
    readonly_fields = (
        'id', 'actor_id', 'actor_email', 'actor_role', 'action',
        'resource_type', 'resource_id', 'description', 'ip_address',
        'user_agent', 'request_id', 'old_value', 'new_value',
        'metadata', 'created_at',
    )
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = (
        'event_type', 'severity', 'user_id',
        'ip_address', 'resolved', 'created_at',
    )
    list_filter = ('event_type', 'severity', 'resolved')
    search_fields = ('description', 'ip_address')
    readonly_fields = (
        'id', 'event_type', 'severity', 'user_id',
        'ip_address', 'user_agent', 'description', 'metadata', 'created_at',
    )
    date_hierarchy = 'created_at'


@admin.register(KPLedger)
class KPLedgerAdmin(admin.ModelAdmin):
    list_display = (
        'user_id', 'action', 'points', 'balance_after',
        'source_type', 'dimension', 'created_at',
    )
    list_filter = ('action', 'dimension', 'source_type')
    search_fields = ('user_id', 'description')
    readonly_fields = (
        'id', 'user_id', 'action', 'points', 'balance_after',
        'source_type', 'source_id', 'dimension', 'description',
        'metadata', 'created_at',
    )
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
