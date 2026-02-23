"""
Nova — Identity Admin Configuration
=======================================
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.identity.domain.models import RefreshToken, User, VerificationRequest


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = (
        'email', 'first_name', 'last_name', 'role',
        'is_active', 'is_verified', 'verification_status',
        'login_count', 'created_at',
    )
    list_filter = ('role', 'is_active', 'is_verified', 'verification_status')
    search_fields = ('email', 'first_name', 'last_name', 'institution_id')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_login_at', 'login_count')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'phone_number',
                'date_of_birth', 'institution_id', 'avatar_url',
            ),
        }),
        ('Status', {
            'fields': (
                'role', 'is_active', 'is_staff', 'is_superuser',
                'is_verified', 'verification_status',
            ),
        }),
        ('Activity', {
            'fields': ('last_login_at', 'login_count'),
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2',
                'first_name', 'last_name', 'role',
            ),
        }),
    )


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'status', 'ocr_confidence',
        'face_match_score', 'attempt_number', 'created_at',
    )
    list_filter = ('status',)
    search_fields = ('user__email', 'extracted_name', 'extracted_id_number')
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'ocr_confidence',
        'face_match_score', 'extracted_name', 'extracted_id_number',
    )
    raw_id_fields = ('user', 'reviewed_by')


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'is_revoked', 'issued_at', 'expires_at')
    list_filter = ('is_revoked',)
    search_fields = ('user__email',)
    readonly_fields = ('id', 'token_hash', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'rotated_from')
