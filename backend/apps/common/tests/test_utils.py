"""
Tests for apps.common.utils
=============================
"""

import pytest
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from django.utils import timezone

from apps.common.utils import (
    generate_token,
    generate_barcode,
    calculate_overdue_days,
    calculate_fine_amount,
    get_client_ip,
    get_user_agent,
    truncate_string,
)


# ─── generate_token ─────────────────────────────────────────────────

class TestGenerateToken:

    def test_default_length_is_reasonable(self):
        token = generate_token()
        assert len(token) > 40  # urlsafe_b64 for 64 bytes is ~86 chars

    def test_custom_length(self):
        short = generate_token(8)
        long = generate_token(128)
        assert len(short) < len(long)

    def test_uniqueness(self):
        tokens = {generate_token() for _ in range(50)}
        assert len(tokens) == 50  # all unique


# ─── generate_barcode ───────────────────────────────────────────────

class TestGenerateBarcode:

    def test_default_prefix(self):
        bc = generate_barcode()
        assert bc.startswith("NOVA-")

    def test_custom_prefix(self):
        bc = generate_barcode(prefix="LIB")
        assert bc.startswith("LIB-")

    def test_random_part_length(self):
        bc = generate_barcode()
        random_part = bc.split("-", 1)[1]
        assert len(random_part) == 8

    def test_uniqueness(self):
        barcodes = {generate_barcode() for _ in range(50)}
        assert len(barcodes) == 50


# ─── calculate_overdue_days ─────────────────────────────────────────

class TestCalculateOverdueDays:

    def test_not_overdue(self):
        due = timezone.now() + timedelta(days=5)
        assert calculate_overdue_days(due) == 0

    def test_overdue_3_days(self):
        due = timezone.now() - timedelta(days=3)
        assert calculate_overdue_days(due) == 3

    def test_returned_before_due(self):
        due = timezone.now()
        returned = due - timedelta(days=2)
        assert calculate_overdue_days(due, returned) == 0

    def test_returned_after_due(self):
        due = timezone.now() - timedelta(days=10)
        returned = due + timedelta(days=5)
        assert calculate_overdue_days(due, returned) == 5

    def test_exact_due_date(self):
        now = timezone.now()
        assert calculate_overdue_days(now, now) == 0


# ─── calculate_fine_amount ──────────────────────────────────────────

class TestCalculateFineAmount:

    @pytest.fixture
    def tiers(self):
        return {7: 1.0, 30: 1.5, 999: 2.0}

    def test_zero_days(self, tiers):
        assert calculate_fine_amount(0, Decimal("0.50"), tiers) == Decimal("0.00")

    def test_negative_days(self, tiers):
        assert calculate_fine_amount(-5, Decimal("0.50"), tiers) == Decimal("0.00")

    def test_first_tier_only(self, tiers):
        # 5 days at 1.0x * $0.50 = $2.50
        assert calculate_fine_amount(5, Decimal("0.50"), tiers) == Decimal("2.50")

    def test_spans_two_tiers(self, tiers):
        # 10 days: 7 at 1.0x + 3 at 1.5x = $3.50 + $2.25 = $5.75
        result = calculate_fine_amount(10, Decimal("0.50"), tiers)
        assert result == Decimal("5.75")

    def test_spans_all_tiers(self, tiers):
        # 35 days: 7@1.0 + 23@1.5 + 5@2.0
        # = 3.50 + 17.25 + 5.00 = 25.75
        result = calculate_fine_amount(35, Decimal("0.50"), tiers)
        assert result == Decimal("25.75")


# ─── get_client_ip ──────────────────────────────────────────────────

class TestGetClientIP:

    def test_direct_request(self):
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "192.168.1.1"}
        assert get_client_ip(request) == "192.168.1.1"

    def test_proxied_request(self):
        request = MagicMock()
        request.META = {
            "HTTP_X_FORWARDED_FOR": "10.0.0.1, 172.16.0.1",
            "REMOTE_ADDR": "127.0.0.1",
        }
        assert get_client_ip(request) == "10.0.0.1"

    def test_fallback_when_no_addr(self):
        request = MagicMock()
        request.META = {}
        assert get_client_ip(request) == "0.0.0.0"


# ─── get_user_agent ─────────────────────────────────────────────────

class TestGetUserAgent:

    def test_normal_ua(self):
        request = MagicMock()
        request.META = {"HTTP_USER_AGENT": "Mozilla/5.0"}
        assert get_user_agent(request) == "Mozilla/5.0"

    def test_truncated_ua(self):
        request = MagicMock()
        request.META = {"HTTP_USER_AGENT": "x" * 600}
        assert len(get_user_agent(request)) == 500

    def test_missing_ua(self):
        request = MagicMock()
        request.META = {}
        assert get_user_agent(request) == ""


# ─── truncate_string ────────────────────────────────────────────────

class TestTruncateString:

    def test_short_string_unchanged(self):
        assert truncate_string("hello") == "hello"

    def test_exactly_at_limit(self):
        text = "x" * 200
        assert truncate_string(text) == text

    def test_over_limit(self):
        text = "x" * 250
        result = truncate_string(text, max_length=200)
        assert len(result) == 200
        assert result.endswith("...")

    def test_none_and_empty(self):
        assert truncate_string(None) is None
        assert truncate_string("") == ""
