"""
Nova — Governance Domain Models
===================================
Audit trail, security events, and KP ledger.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.base_models import UUIDModel


class AuditLog(UUIDModel):
    """
    Immutable audit trail for every significant action in the system.
    Stored in the governance schema.
    """

    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('REGISTER', 'Register'),
        ('BORROW', 'Borrow'),
        ('RETURN', 'Return'),
        ('RENEW', 'Renew'),
        ('RESERVE', 'Reserve'),
        ('VERIFY', 'Verify'),
        ('KP_AWARD', 'KP Award'),
        ('KP_DEDUCT', 'KP Deduct'),
        ('FINE_ISSUE', 'Fine Issue'),
        ('FINE_PAY', 'Fine Pay'),
        ('SESSION_START', 'Session Start'),
        ('SESSION_END', 'Session End'),
        ('ROLE_CHANGE', 'Role Change'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('CONFIRM_PICKUP', 'Confirm Pickup'),
        ('REGISTER_WITH_NIC', 'Register with NIC'),
        ('UPDATE_ROLE_CONFIG', 'Update Role Config'),
        ('CREATE_ROLE_CONFIG', 'Create Role Config'),
        ('DELETE_ROLE_CONFIG', 'Delete Role Config'),
        ('SYSTEM', 'System'),
    ]

    # Who
    actor_id = models.UUIDField(null=True, blank=True, db_index=True,
                                help_text='User who performed the action.')
    actor_email = models.CharField(max_length=255, blank=True, default='')
    actor_role = models.CharField(max_length=30, blank=True, default='')

    # What
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True,
                                     help_text='e.g. User, Book, BorrowRecord')
    resource_id = models.CharField(max_length=255, blank=True, default='',
                                   help_text='ID of the affected resource.')
    description = models.TextField(blank=True, default='')

    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    request_id = models.CharField(max_length=64, blank=True, default='')

    # Payload (JSON diff or snapshot)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'governance_audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at'], name='idx_audit_action_time'),
            models.Index(fields=['actor_id', 'created_at'], name='idx_audit_actor_time'),
            models.Index(fields=['resource_type', 'resource_id'], name='idx_audit_resource'),
            models.Index(fields=['-created_at'], name='idx_audit_created'),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        return f'[{self.action}] {self.resource_type}({self.resource_id}) by {self.actor_email}'


class SecurityEvent(UUIDModel):
    """
    Tracks security-relevant events — failed logins, suspicious activity, etc.
    """

    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    EVENT_TYPE_CHOICES = [
        ('FAILED_LOGIN', 'Failed Login'),
        ('BRUTE_FORCE', 'Brute Force Detected'),
        ('TOKEN_REUSE', 'Refresh Token Reuse'),
        ('RATE_LIMIT', 'Rate Limit Exceeded'),
        ('SUSPICIOUS_ACTIVITY', 'Suspicious Activity'),
        ('PRIVILEGE_ESCALATION', 'Privilege Escalation Attempt'),
        ('DATA_EXPORT', 'Bulk Data Export'),
        ('ACCOUNT_LOCKED', 'Account Locked'),
        ('PASSWORD_RESET', 'Password Reset'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, db_index=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, db_index=True)

    user_id = models.UUIDField(null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')

    description = models.TextField(blank=True, default='')
    metadata = models.JSONField(null=True, blank=True)

    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='resolved_security_events',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'governance_security_event'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', '-created_at'], name='idx_sec_type_time'),
            models.Index(fields=['severity', '-created_at'], name='idx_sec_severity_time'),
            models.Index(fields=['user_id', '-created_at'], name='idx_sec_user_time'),
            models.Index(fields=['ip_address'], name='idx_sec_ip'),
        ]
        verbose_name = 'Security Event'
        verbose_name_plural = 'Security Events'

    def resolve(self, user):
        self.resolved = True
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save(update_fields=['resolved', 'resolved_by', 'resolved_at', 'updated_at'])

    def __str__(self):
        return f'[{self.severity}] {self.event_type} — {self.description[:60]}'


class KPLedger(UUIDModel):
    """
    Immutable knowledge-point transaction ledger.
    Every KP gain or deduction is recorded here for auditability.
    """

    LEDGER_ACTION_CHOICES = [
        ('AWARD', 'Award'),
        ('DEDUCT', 'Deduct'),
        ('BONUS', 'Bonus'),
        ('PENALTY', 'Penalty'),
        ('EXPIRE', 'Expire'),
        ('ADMIN_ADJUST', 'Admin Adjustment'),
    ]

    user_id = models.UUIDField(db_index=True)
    action = models.CharField(max_length=20, choices=LEDGER_ACTION_CHOICES)
    points = models.IntegerField(help_text='Positive for award, negative for deduction.')
    balance_after = models.IntegerField(help_text='KP balance after this transaction.')

    source_type = models.CharField(
        max_length=50, blank=True, default='',
        help_text='e.g. BORROW_RETURN, READING_SESSION, LOGIN_STREAK',
    )
    source_id = models.CharField(max_length=255, blank=True, default='')
    dimension = models.CharField(
        max_length=30, blank=True, default='',
        help_text='KP dimension: EXPLORER, SCHOLAR, etc.',
    )

    description = models.TextField(blank=True, default='')
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'governance_kp_ledger'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', '-created_at'], name='idx_kp_user_time'),
            models.Index(fields=['action', '-created_at'], name='idx_kp_action_time'),
            models.Index(fields=['source_type'], name='idx_kp_source'),
            models.Index(fields=['dimension'], name='idx_kp_dimension'),
        ]
        verbose_name = 'KP Ledger Entry'
        verbose_name_plural = 'KP Ledger Entries'

    def __str__(self):
        sign = '+' if self.points >= 0 else ''
        return f'KP {sign}{self.points} → {self.balance_after} ({self.action})'
