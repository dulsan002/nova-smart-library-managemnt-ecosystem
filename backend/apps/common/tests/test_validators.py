"""
Tests for apps.common.validators
=================================
Pure-function tests — no database or Django ORM required.
"""

import pytest
from apps.common.validators import (
    validate_isbn_10,
    validate_isbn_13,
    validate_isbn,
    isbn_10_to_13,
    validate_email_format,
    validate_password_strength,
    compute_file_hash,
    validate_file_extension,
    sanitize_string,
)


# ─── ISBN-10 ─────────────────────────────────────────────────────────

class TestValidateISBN10:
    """Tests for validate_isbn_10."""

    def test_valid_isbn10(self):
        assert validate_isbn_10("0201633612") is True   # Design Patterns

    def test_valid_isbn10_with_x(self):
        assert validate_isbn_10("007462542X") is True

    def test_valid_isbn10_with_dashes(self):
        assert validate_isbn_10("0-201-63361-2") is True

    def test_valid_isbn10_with_spaces(self):
        assert validate_isbn_10("0 201 63361 2") is True

    def test_invalid_isbn10_wrong_checksum(self):
        assert validate_isbn_10("0201633613") is False

    def test_invalid_isbn10_too_short(self):
        assert validate_isbn_10("020163361") is False

    def test_invalid_isbn10_too_long(self):
        assert validate_isbn_10("02016336123") is False

    def test_invalid_isbn10_letters(self):
        assert validate_isbn_10("ABCDEFGHIJ") is False

    def test_empty_string(self):
        assert validate_isbn_10("") is False


# ─── ISBN-13 ─────────────────────────────────────────────────────────

class TestValidateISBN13:
    """Tests for validate_isbn_13."""

    def test_valid_isbn13(self):
        assert validate_isbn_13("9780132350884") is True   # Clean Code

    def test_valid_isbn13_979_prefix(self):
        assert validate_isbn_13("9791032305690") is True

    def test_valid_isbn13_with_dashes(self):
        assert validate_isbn_13("978-0-13-235088-4") is True

    def test_invalid_isbn13_wrong_checksum(self):
        assert validate_isbn_13("9780132350885") is False

    def test_invalid_isbn13_bad_prefix(self):
        assert validate_isbn_13("9770132350884") is False

    def test_invalid_isbn13_too_short(self):
        assert validate_isbn_13("978013235088") is False

    def test_invalid_isbn13_non_digit(self):
        assert validate_isbn_13("978013235088X") is False

    def test_empty_string(self):
        assert validate_isbn_13("") is False


# ─── validate_isbn (unified) ────────────────────────────────────────

class TestValidateISBN:

    def test_returns_isbn13_when_valid(self):
        assert validate_isbn("9780132350884") == "9780132350884"

    def test_returns_isbn10_when_valid(self):
        assert validate_isbn("0201633612") == "0201633612"

    def test_returns_none_when_invalid(self):
        assert validate_isbn("1234567890123") is None

    def test_strips_dashes(self):
        result = validate_isbn("978-0-13-235088-4")
        assert result == "9780132350884"


# ─── isbn_10_to_13 ──────────────────────────────────────────────────

class TestISBN10to13:

    def test_conversion(self):
        result = isbn_10_to_13("0132350882")
        assert result == "9780132350884"

    def test_conversion_with_x_check(self):
        # 007462542X → 978-0074625422
        result = isbn_10_to_13("007462542X")
        assert result is not None
        assert result.startswith("978")
        assert len(result) == 13

    def test_invalid_isbn10_returns_none(self):
        assert isbn_10_to_13("0000000001") is None


# ─── Email ───────────────────────────────────────────────────────────

class TestValidateEmailFormat:

    def test_valid_email(self):
        assert validate_email_format("user@example.com") is True

    def test_valid_email_subdomain(self):
        assert validate_email_format("user@mail.example.co.uk") is True

    def test_valid_email_plus_tag(self):
        assert validate_email_format("user+tag@example.com") is True

    def test_invalid_no_at(self):
        assert validate_email_format("userexample.com") is False

    def test_invalid_no_domain(self):
        assert validate_email_format("user@") is False

    def test_invalid_no_tld(self):
        assert validate_email_format("user@example") is False

    def test_empty_string(self):
        assert validate_email_format("") is False


# ─── Password Strength ──────────────────────────────────────────────

class TestValidatePasswordStrength:

    def test_strong_password(self):
        result = validate_password_strength("MyS3cureP@ss")
        assert result["is_valid"] is True
        assert result["score"] >= 5
        assert result["issues"] == []

    def test_short_password(self):
        result = validate_password_strength("Ab1!")
        assert result["is_valid"] is False
        assert any("10 characters" in i for i in result["issues"])

    def test_no_uppercase(self):
        result = validate_password_strength("mysecurep@ss1")
        assert result["is_valid"] is False
        assert any("uppercase" in i for i in result["issues"])

    def test_no_digit(self):
        result = validate_password_strength("MySecureP@ss")
        assert result["is_valid"] is False
        assert any("digit" in i for i in result["issues"])

    def test_no_special_char(self):
        result = validate_password_strength("MySecurePass1")
        assert result["is_valid"] is False
        assert any("special" in i for i in result["issues"])

    def test_extra_long_password_gets_bonus(self):
        result = validate_password_strength("MyV3ryL0ng&S3cure!")
        assert result["score"] == 6  # 14+ chars = bonus point

    def test_minimum_valid(self):
        result = validate_password_strength("Abcdefgh1!")
        assert result["is_valid"] is True


# ─── File Hash ───────────────────────────────────────────────────────

class TestComputeFileHash:

    def test_known_hash(self):
        # SHA-256 of empty byte string
        assert compute_file_hash(b"") == (
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

    def test_deterministic(self):
        content = b"hello world"
        assert compute_file_hash(content) == compute_file_hash(content)

    def test_different_content_different_hash(self):
        assert compute_file_hash(b"a") != compute_file_hash(b"b")


# ─── File Extension ──────────────────────────────────────────────────

class TestValidateFileExtension:

    @pytest.fixture
    def allowed(self):
        return [".pdf", ".epub", ".mp3"]

    def test_valid_extension(self, allowed):
        assert validate_file_extension("book.pdf", allowed) is True

    def test_case_insensitive(self, allowed):
        assert validate_file_extension("book.PDF", allowed) is True

    def test_invalid_extension(self, allowed):
        assert validate_file_extension("book.exe", allowed) is False

    def test_no_extension(self, allowed):
        assert validate_file_extension("README", allowed) is False

    def test_empty_filename(self, allowed):
        assert validate_file_extension("", allowed) is False


# ─── String Sanitization ────────────────────────────────────────────

class TestSanitizeString:

    def test_removes_null_bytes(self):
        assert "\x00" not in sanitize_string("hello\x00world")

    def test_removes_control_chars(self):
        result = sanitize_string("hello\x01\x02\x03world")
        assert result == "helloworld"

    def test_preserves_newlines_and_tabs(self):
        assert sanitize_string("hello\n\tworld") == "hello\n\tworld"

    def test_strips_whitespace(self):
        assert sanitize_string("  hello  ") == "hello"

    def test_none_passthrough(self):
        assert sanitize_string(None) is None

    def test_empty_string(self):
        assert sanitize_string("") == ""
