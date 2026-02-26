"""
System Settings — Domain Model
================================
Key-value store for admin-configurable application settings.
Non-technical admins can change these through the UI instead of editing base.py.
"""

import uuid
import json

from django.db import models

from apps.common.base_models import TimeStampedModel


class SystemSetting(TimeStampedModel):
    """
    Key-value setting that can be modified by admin at runtime.
    Overrides the static values in django settings when present.
    """

    class Category(models.TextChoices):
        CIRCULATION = 'CIRCULATION', 'Circulation'
        ENGAGEMENT = 'ENGAGEMENT', 'Engagement'
        SECURITY = 'SECURITY', 'Security'
        GENERAL = 'GENERAL', 'General'
        NOTIFICATIONS = 'NOTIFICATIONS', 'Notifications'
        EMAIL = 'EMAIL', 'Email / SMTP'

    class ValueType(models.TextChoices):
        STRING = 'STRING', 'Text'
        INTEGER = 'INTEGER', 'Whole Number'
        FLOAT = 'FLOAT', 'Decimal Number'
        BOOLEAN = 'BOOLEAN', 'Yes / No'
        JSON = 'JSON', 'Advanced (JSON)'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField(default='')
    value_type = models.CharField(max_length=10, choices=ValueType.choices, default=ValueType.STRING)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)

    label = models.CharField(max_length=200, help_text='Human-readable name shown in admin UI')
    description = models.TextField(blank=True, default='', help_text='Explanation shown to admin')
    is_sensitive = models.BooleanField(default=False, help_text='Mask value in UI')

    updated_by = models.ForeignKey(
        'identity.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='setting_changes',
    )

    class Meta:
        db_table = 'common_system_settings'
        ordering = ['category', 'key']

    def __str__(self):
        return f'{self.key} = {self.value}'

    @property
    def typed_value(self):
        """Return value cast to its declared type."""
        if self.value_type == 'INTEGER':
            return int(self.value)
        elif self.value_type == 'FLOAT':
            return float(self.value)
        elif self.value_type == 'BOOLEAN':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.value_type == 'JSON':
            return json.loads(self.value)
        return self.value

    @classmethod
    def get(cls, key: str, default=None):
        """Get a setting value by key, with fallback to default."""
        try:
            setting = cls.objects.get(key=key)
            return setting.typed_value
        except cls.DoesNotExist:
            return default

    @classmethod
    def sync_defaults(cls):
        """
        Seed default settings from Django settings.
        Only creates settings that don't already exist (won't overwrite admin changes).
        """
        from django.conf import settings as django_settings

        defaults = [
            # Circulation
            ('circulation.default_borrow_days', '14', 'INTEGER', 'CIRCULATION',
             'Default Borrow Period (Days)', 'How many days a patron can borrow a book'),
            ('circulation.max_extensions', '2', 'INTEGER', 'CIRCULATION',
             'Maximum Extensions', 'How many times a borrow can be extended'),
            ('circulation.max_concurrent_borrows', '5', 'INTEGER', 'CIRCULATION',
             'Maximum Concurrent Borrows', 'Maximum books a patron can have at once'),
            ('circulation.reservation_pickup_hours', '12', 'INTEGER', 'CIRCULATION',
             'Reservation Pickup Deadline (Hours)', 'Hours before an uncollected reservation expires'),
            ('circulation.fine_base_rate', '0.50', 'FLOAT', 'CIRCULATION',
             'Daily Fine Rate ($)', 'Base fine charged per overdue day'),
            ('circulation.max_unpaid_fine', '25.00', 'FLOAT', 'CIRCULATION',
             'Maximum Unpaid Fine ($)', 'Patrons with fines above this cannot reserve'),
            ('circulation.abuse_max_no_shows', '3', 'INTEGER', 'CIRCULATION',
             'Max No-Shows Before Ban', 'Number of missed pickups before temporary ban'),
            ('circulation.abuse_ban_days', '7', 'INTEGER', 'CIRCULATION',
             'No-Show Ban Duration (Days)', 'How long a patron is banned after too many no-shows'),

            # Engagement
            ('engagement.daily_kp_cap', '200', 'INTEGER', 'ENGAGEMENT',
             'Daily Knowledge Points Cap', 'Maximum KP a user can earn per day'),
            ('engagement.min_session_duration', '120', 'INTEGER', 'ENGAGEMENT',
             'Minimum Session Duration (Seconds)', 'Minimum reading time to earn KP'),
            ('engagement.streak_min_minutes', '15', 'INTEGER', 'ENGAGEMENT',
             'Streak Minimum Active Minutes', 'Minimum active minutes per day to maintain streak'),

            # General
            ('general.library_name', 'Nova Digital Library', 'STRING', 'GENERAL',
             'Library Name', 'Name displayed in headers and emails'),
            ('general.library_email', 'admin@nova-library.org', 'STRING', 'GENERAL',
             'Library Contact Email', 'Main contact email address'),
            ('general.maintenance_mode', 'false', 'BOOLEAN', 'GENERAL',
             'Maintenance Mode', 'When enabled, only admins can access the system'),

            # Notifications
            ('notifications.email_enabled', 'true', 'BOOLEAN', 'NOTIFICATIONS',
             'Email Notifications', 'Enable or disable email notifications'),
            ('notifications.overdue_reminder_days', '[3, 1, 0, -1, -3, -7]', 'JSON', 'NOTIFICATIONS',
             'Overdue Reminder Schedule', 'Days before/after due date to send reminders (negative = after)'),

            # Security
            ('security.max_login_attempts', '10', 'INTEGER', 'SECURITY',
             'Max Login Attempts', 'Failed login attempts before account lockout'),
            ('security.lockout_seconds', '600', 'INTEGER', 'SECURITY',
             'Account Lockout Duration (Seconds)', 'How long an account stays locked'),

            # Email / SMTP
            ('smtp.host', '', 'STRING', 'EMAIL',
             'SMTP Server Host',
             'The SMTP server address. Examples: smtp.gmail.com (Gmail), smtp.office365.com (Outlook/Microsoft 365), smtp-mail.outlook.com (Hotmail), smtp.zoho.com (Zoho Mail).'),
            ('smtp.port', '587', 'INTEGER', 'EMAIL',
             'SMTP Server Port',
             'The port your SMTP server listens on. Use 587 for TLS (recommended), 465 for SSL, or 25 for unencrypted (not recommended).'),
            ('smtp.username', '', 'STRING', 'EMAIL',
             'SMTP Username',
             'Usually your full email address, e.g. library@gmail.com. This is the account used to authenticate with the mail server.'),
            ('smtp.password', '', 'STRING', 'EMAIL',
             'SMTP Password / App Password',
             'For Gmail: Go to myaccount.google.com → Security → 2-Step Verification → App passwords → Generate a 16-character app password. For Outlook: Use your account password or generate an app password under Security settings. Never use your main password if 2FA is enabled.',
             True),
            ('smtp.from_email', '', 'STRING', 'EMAIL',
             'Sender Email Address',
             'The "From" address recipients will see, e.g. noreply@yourlibrary.org. Must be an address your SMTP server allows you to send from.'),
            ('smtp.from_name', 'Nova Smart Library', 'STRING', 'EMAIL',
             'Sender Display Name',
             'The friendly name shown in the "From" field, e.g. "Nova Smart Library". Recipients will see this next to the sender email.'),
            ('smtp.use_tls', 'true', 'BOOLEAN', 'EMAIL',
             'Use TLS Encryption',
             'Enable TLS encryption for the SMTP connection. Recommended: Yes (port 587). Set to No only if your mail server does not support TLS.'),
        ]

        created = 0
        for item in defaults:
            key, value, vtype, category, label, desc = item[:6]
            sensitive = item[6] if len(item) > 6 else False
            _, was_created = cls.objects.get_or_create(
                key=key,
                defaults={
                    'value': value,
                    'value_type': vtype,
                    'category': category,
                    'label': label,
                    'description': desc,
                    'is_sensitive': sensitive,
                },
            )
            if was_created:
                created += 1
        return created
