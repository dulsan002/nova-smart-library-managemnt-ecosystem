"""
Nova — Common Utilities
========================
Helper functions used across the application.
"""

import secrets
import string
from datetime import datetime, date
from typing import Optional
from decimal import Decimal

from django.utils import timezone


def generate_token(length: int = 64) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def generate_barcode(prefix: str = 'NOVA') -> str:
    """
    Generate a unique barcode string for book copies.

    Format: NOVA-XXXXXXXX where X is alphanumeric.
    """
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(8))
    return f'{prefix}-{random_part}'


def calculate_overdue_days(due_date: datetime, return_date: Optional[datetime] = None) -> int:
    """
    Calculate the number of overdue days.

    Args:
        due_date: When the book was due.
        return_date: When the book was returned (None = not yet returned).

    Returns:
        Number of overdue days (0 if not overdue).
    """
    comparison_date = return_date or timezone.now()

    if comparison_date <= due_date:
        return 0

    delta = comparison_date - due_date
    return delta.days


def calculate_fine_amount(
    overdue_days: int,
    base_rate: Decimal,
    escalation_tiers: dict,
) -> Decimal:
    """
    Calculate fine amount with escalation tiers.

    Args:
        overdue_days: Number of days overdue.
        base_rate: Base fine rate per day.
        escalation_tiers: Dict mapping day thresholds to multipliers.
            Example: {7: 1.0, 30: 1.5, 999: 2.0}

    Returns:
        Total fine amount.
    """
    if overdue_days <= 0:
        return Decimal('0.00')

    total = Decimal('0.00')
    remaining_days = overdue_days
    previous_threshold = 0

    for threshold, multiplier in sorted(escalation_tiers.items()):
        tier_days = min(remaining_days, threshold - previous_threshold)
        if tier_days <= 0:
            break

        total += base_rate * Decimal(str(multiplier)) * tier_days
        remaining_days -= tier_days
        previous_threshold = threshold

        if remaining_days <= 0:
            break

    return total.quantize(Decimal('0.01'))


def get_client_ip(request) -> str:
    """
    Extract the client's IP address from the request.
    Handles proxied requests (X-Forwarded-For).

    Args:
        request: Django HttpRequest object.

    Returns:
        Client IP address string.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


def get_user_agent(request) -> str:
    """Extract User-Agent string from request."""
    return request.META.get('HTTP_USER_AGENT', '')[:500]


def truncate_string(value: str, max_length: int = 200) -> str:
    """Truncate a string to max_length, adding ellipsis if truncated."""
    if not value or len(value) <= max_length:
        return value
    return value[:max_length - 3] + '...'
