"""
Tests for apps.common.sanitizers
==================================
Tests for XSS stripping, SQL-injection detection, path traversal, and dict sanitisation.
"""

import pytest
from apps.common.sanitizers import (
    sanitize,
    sanitize_email,
    sanitize_search_query,
    sanitize_path,
    check_sql_injection,
    sanitize_dict,
)
from apps.common.exceptions import ValidationError


# ─── sanitize() ──────────────────────────────────────────────────────

class TestSanitize:

    def test_returns_none_for_none(self):
        assert sanitize(None) is None

    def test_strips_html_tags(self):
        assert sanitize("<b>bold</b>") == "bold"

    def test_strips_script_tag(self):
        result = sanitize('<script>alert("xss")</script>Hello')
        assert "<script>" not in result
        assert "Hello" in result

    def test_strips_javascript_protocol(self):
        result = sanitize('javascript:alert(1)')
        assert "javascript:" not in result

    def test_strips_event_handlers(self):
        result = sanitize('<img onerror="alert(1)" src="x">')
        assert "onerror" not in result

    def test_strips_data_uri(self):
        result = sanitize('data:text/html;base64,PHNjcmlwdD4=')
        assert "data:" not in result or "base64" not in result

    def test_strips_bidi_overrides(self):
        result = sanitize("hello\u200eworld\u202a")
        assert "\u200e" not in result
        assert "\u202a" not in result

    def test_strips_control_chars(self):
        result = sanitize("hello\x01\x02world")
        assert "\x01" not in result
        assert "\x02" not in result

    def test_max_length_clamp(self):
        result = sanitize("x" * 200, max_length=100)
        assert len(result) == 100

    def test_preserves_newlines_by_default(self):
        result = sanitize("line1\nline2")
        assert "\n" in result

    def test_removes_newlines_when_disabled(self):
        result = sanitize("line1\nline2", allow_newlines=False)
        assert "\n" not in result

    def test_collapses_excessive_whitespace(self):
        result = sanitize("hello     world")
        assert "     " not in result

    def test_html_entity_bypass(self):
        """Encoded HTML entities should be unescaped then stripped."""
        result = sanitize("&lt;script&gt;alert(1)&lt;/script&gt;")
        assert "<script>" not in result
        assert "alert" in result  # text content is kept

    def test_preserves_normal_text(self):
        text = "A perfectly normal sentence with some numbers 123."
        assert sanitize(text) == text


# ─── sanitize_email() ───────────────────────────────────────────────

class TestSanitizeEmail:

    def test_lowercases(self):
        assert sanitize_email("Admin@NOVA.local") == "admin@nova.local"

    def test_strips_html(self):
        result = sanitize_email("<b>admin</b>@nova.local")
        assert "<b>" not in result

    def test_none_returns_none(self):
        assert sanitize_email(None) is None

    def test_max_length_254(self):
        # RFC limit for email
        result = sanitize_email("a" * 300 + "@test.com")
        assert len(result) <= 254


# ─── sanitize_search_query() ────────────────────────────────────────

class TestSanitizeSearchQuery:

    def test_removes_sql_injection(self):
        result = sanitize_search_query("books; DROP TABLE users;--")
        assert "DROP TABLE" not in result
        assert "--" not in result

    def test_preserves_normal_query(self):
        assert sanitize_search_query("clean code") == "clean code"

    def test_none_returns_none(self):
        assert sanitize_search_query(None) is None


# ─── sanitize_path() ────────────────────────────────────────────────

class TestSanitizePath:

    def test_raises_on_path_traversal(self):
        with pytest.raises(ValidationError, match="Path traversal"):
            sanitize_path("../../etc/passwd")

    def test_raises_on_null_bytes(self):
        with pytest.raises(ValidationError, match="null bytes"):
            sanitize_path("file\x00.pdf")

    def test_raises_on_encoded_traversal(self):
        with pytest.raises(ValidationError, match="Path traversal"):
            sanitize_path("%2e%2e/etc/passwd")

    def test_allows_normal_path(self):
        assert sanitize_path("uploads/document.pdf") == "uploads/document.pdf"


# ─── check_sql_injection() ──────────────────────────────────────────

class TestCheckSQLInjection:

    @pytest.mark.parametrize("payload", [
        "1 UNION SELECT * FROM users",
        "1; DROP TABLE books;--",
        "admin'/*",
        "INSERT INTO logs VALUES (1)",
        "DELETE FROM users WHERE 1=1",
        "UPDATE users SET role='admin'",
        "ALTER TABLE users DROP COLUMN password",
    ])
    def test_detects_injection(self, payload):
        assert check_sql_injection(payload) is True

    def test_safe_string(self):
        assert check_sql_injection("clean code") is False

    def test_safe_string_with_quotes(self):
        assert check_sql_injection("it's a valid book") is False


# ─── sanitize_dict() ────────────────────────────────────────────────

class TestSanitizeDict:

    def test_sanitizes_string_values(self):
        result = sanitize_dict({"name": "<b>Evil</b>"})
        assert result["name"] == "Evil"

    def test_leaves_non_strings_alone(self):
        result = sanitize_dict({"count": 42, "flag": True})
        assert result == {"count": 42, "flag": True}

    def test_nested_dict(self):
        result = sanitize_dict({"user": {"name": "<script>x</script>"}})
        assert "<script>" not in result["user"]["name"]

    def test_list_of_strings(self):
        result = sanitize_dict({"tags": ["<b>a</b>", "normal"]})
        assert result["tags"][0] == "a"
        assert result["tags"][1] == "normal"

    def test_empty_dict(self):
        assert sanitize_dict({}) == {}
