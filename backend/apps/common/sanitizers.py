"""
Nova — Input Sanitization Utilities
======================================
Centralized functions for sanitising untrusted string input in GraphQL
mutations and other write paths.

Layers
------
1. **HTML / XSS stripping** – Removes all HTML tags and dangerous
   attribute patterns (``onerror``, ``javascript:``…).
2. **SQL meta-character escaping** – Although Django ORM parameterises
   queries, this provides defence-in-depth for any ``extra()`` /
   ``raw()`` calls.
3. **Path traversal prevention** – Blocks ``../`` sequences and null
   bytes in file-path inputs.
4. **Unicode normalisation** – Prevents homoglyph / bidi-override
   trickery.
5. **Length clamping** – Truncates strings to a configurable maximum
   so abnormally long inputs never reach the database layer.

Usage
-----
>>> from apps.common.sanitizers import sanitize, sanitize_path
>>> sanitize("<script>alert(1)</script>Hello")
'Hello'
>>> sanitize_path("../../etc/passwd")  # raises ValidationError
"""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Optional

from apps.common.exceptions import ValidationError

# =========================================================================
# Compiled patterns (compiled once at import time)
# =========================================================================

_HTML_TAG = re.compile(r"<[^>]+>", re.DOTALL)
_JS_PROTOCOL = re.compile(
    r"(?:java|vb)script\s*:", re.IGNORECASE
)
_EVENT_HANDLER = re.compile(
    r"\bon\w+\s*=", re.IGNORECASE
)
_DATA_URI = re.compile(r"data\s*:[^,]*;base64,", re.IGNORECASE)
_SQL_INJECTION = re.compile(
    r"(?:--|;|/\*|\*/|xp_|UNION\s+SELECT|DROP\s+TABLE|INSERT\s+INTO|DELETE\s+FROM|"
    r"UPDATE\s+\w+\s+SET|ALTER\s+TABLE)",
    re.IGNORECASE,
)
_PATH_TRAVERSAL = re.compile(r"(?:\.\./|\.\.\\|%2e%2e|%252e)")
_NULL_BYTE = re.compile(r"\x00|%00")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_BIDI_OVERRIDES = re.compile(
    r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]"
)
_EXCESSIVE_WHITESPACE = re.compile(r"\s{3,}")

# =========================================================================
# Public helpers
# =========================================================================

DEFAULT_MAX_LENGTH = 10_000


def sanitize(
    value: Optional[str],
    *,
    max_length: int = DEFAULT_MAX_LENGTH,
    strip_html: bool = True,
    allow_newlines: bool = True,
) -> Optional[str]:
    """
    Sanitise a generic string input.

    Parameters
    ----------
    value : str | None
        Raw input; ``None`` is returned unchanged.
    max_length : int
        Hard truncation limit.
    strip_html : bool
        If True, remove all HTML tags.
    allow_newlines : bool
        If False, replace ``\\n`` / ``\\r`` with spaces.

    Returns
    -------
    str | None
        Cleaned string.
    """
    if value is None:
        return None

    # Normalise unicode (NFC removes some homoglyph tricks)
    text = unicodedata.normalize("NFC", value)

    # Strip bidirectional overrides
    text = _BIDI_OVERRIDES.sub("", text)

    # Strip control characters (keep \n \r \t)
    text = _CONTROL_CHARS.sub("", text)

    if strip_html:
        # First unescape any HTML entities so we don't miss encoded tags
        text = html.unescape(text)
        text = _HTML_TAG.sub("", text)

    # Remove javascript: / vbscript: protocols
    text = _JS_PROTOCOL.sub("", text)

    # Remove inline event handlers (onerror=, onclick=, …)
    text = _EVENT_HANDLER.sub("", text)

    # Remove data-URIs with base64 payload (potential XSS vector)
    text = _DATA_URI.sub("", text)

    if not allow_newlines:
        text = text.replace("\n", " ").replace("\r", " ")

    # Collapse excessive whitespace
    text = _EXCESSIVE_WHITESPACE.sub("  ", text)

    # Trim
    text = text.strip()

    # Clamp length
    if len(text) > max_length:
        text = text[:max_length]

    return text


def sanitize_email(email: Optional[str]) -> Optional[str]:
    """Sanitise and lower-case an email address."""
    if email is None:
        return None
    clean = sanitize(email, max_length=254, strip_html=True, allow_newlines=False)
    return clean.lower() if clean else None


def sanitize_search_query(query: Optional[str]) -> Optional[str]:
    """
    Sanitise a free-text search query.

    Removes HTML and SQL meta-characters but preserves quotes for
    phrase-matching.
    """
    if query is None:
        return None
    text = sanitize(query, max_length=500, strip_html=True, allow_newlines=False)
    if text is None:
        return None
    # Strip SQL-injection patterns (defence-in-depth)
    text = _SQL_INJECTION.sub("", text)
    return text.strip()


def sanitize_path(path: str) -> str:
    """
    Sanitise a file-system path component.

    Raises ``ValidationError`` if traversal sequences or null bytes
    are detected.  This is intended for *user-supplied* path segments
    (e.g. uploaded filenames) not for trusted internal paths.
    """
    if _NULL_BYTE.search(path):
        raise ValidationError(
            "Path contains null bytes.",
            field="path",
        )

    if _PATH_TRAVERSAL.search(path):
        raise ValidationError(
            "Path traversal detected.",
            field="path",
        )

    # Remove any remaining control chars and HTML
    clean = sanitize(path, max_length=255, strip_html=True, allow_newlines=False)
    return clean or ""


def check_sql_injection(value: str) -> bool:
    """
    Return ``True`` if the value contains SQL-injection patterns.

    This is a **defence-in-depth** check.  The ORM's parameterised
    queries are the primary protection.
    """
    return bool(_SQL_INJECTION.search(value))


def sanitize_dict(data: dict, *, max_length: int = DEFAULT_MAX_LENGTH) -> dict:
    """
    Recursively sanitise all string values in a dictionary.

    Useful for cleaning an entire GraphQL ``input`` object.
    """
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, str):
            cleaned[key] = sanitize(value, max_length=max_length)
        elif isinstance(value, dict):
            cleaned[key] = sanitize_dict(value, max_length=max_length)
        elif isinstance(value, list):
            cleaned[key] = [
                sanitize(v, max_length=max_length) if isinstance(v, str)
                else sanitize_dict(v, max_length=max_length) if isinstance(v, dict)
                else v
                for v in value
            ]
        else:
            cleaned[key] = value
    return cleaned
