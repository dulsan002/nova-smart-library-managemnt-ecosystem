"""
Tests for apps.common.pagination
==================================
"""

import pytest
from apps.common.pagination import encode_cursor, decode_cursor


class TestEncodeCursor:

    def test_roundtrip(self):
        for val in [0, 42, 999]:
            assert decode_cursor(encode_cursor(val)) == str(val)

    def test_string_cursor(self):
        encoded = encode_cursor("abc")
        assert decode_cursor(encoded) == "abc"


class TestDecodeCursor:

    def test_invalid_base64_returns_empty(self):
        assert decode_cursor("!!!not-base64!!!") == ""

    def test_empty_string(self):
        # Empty base64 decodes to empty string
        assert decode_cursor("") == ""
