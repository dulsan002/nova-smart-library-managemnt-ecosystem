"""
Nova — Shared Validators
==========================
Reusable validation functions used across bounded contexts.
"""

import re
import hashlib
from typing import Optional


def validate_isbn_10(isbn: str) -> bool:
    """
    Validate an ISBN-10 number using the check digit algorithm.

    ISBN-10 check: Sum of (digit × position) for positions 1-10 must be divisible by 11.
    The last digit can be 'X' representing 10.

    Args:
        isbn: String of 10 characters (digits + optional trailing 'X').

    Returns:
        True if the ISBN-10 checksum is valid.
    """
    isbn = isbn.replace('-', '').replace(' ', '').upper()

    if len(isbn) != 10:
        return False

    if not re.match(r'^\d{9}[\dX]$', isbn):
        return False

    total = 0
    for i, char in enumerate(isbn):
        if char == 'X':
            value = 10
        else:
            value = int(char)
        total += value * (10 - i)

    return total % 11 == 0


def validate_isbn_13(isbn: str) -> bool:
    """
    Validate an ISBN-13 number using the check digit algorithm.

    ISBN-13 check: Alternating multiply by 1 and 3, sum must be divisible by 10.

    Args:
        isbn: String of 13 digits.

    Returns:
        True if the ISBN-13 checksum is valid.
    """
    isbn = isbn.replace('-', '').replace(' ', '')

    if len(isbn) != 13:
        return False

    if not isbn.isdigit():
        return False

    if not isbn.startswith(('978', '979')):
        return False

    total = 0
    for i, char in enumerate(isbn):
        digit = int(char)
        if i % 2 == 0:
            total += digit
        else:
            total += digit * 3

    return total % 10 == 0


def validate_isbn(isbn: str) -> Optional[str]:
    """
    Validate an ISBN (10 or 13) and return the normalized form.

    Args:
        isbn: ISBN string to validate.

    Returns:
        Normalized ISBN string if valid, None if invalid.
    """
    cleaned = isbn.replace('-', '').replace(' ', '').upper()

    if len(cleaned) == 13 and validate_isbn_13(cleaned):
        return cleaned
    elif len(cleaned) == 10 and validate_isbn_10(cleaned):
        return cleaned

    return None


def isbn_10_to_13(isbn_10: str) -> Optional[str]:
    """
    Convert an ISBN-10 to ISBN-13.

    Args:
        isbn_10: Valid ISBN-10 string.

    Returns:
        ISBN-13 string, or None if input is invalid.
    """
    isbn_10 = isbn_10.replace('-', '').replace(' ', '')

    if not validate_isbn_10(isbn_10):
        return None

    # Remove check digit, prepend 978
    base = '978' + isbn_10[:9]

    # Calculate ISBN-13 check digit
    total = 0
    for i, char in enumerate(base):
        digit = int(char)
        if i % 2 == 0:
            total += digit
        else:
            total += digit * 3

    check_digit = (10 - (total % 10)) % 10
    return base + str(check_digit)


def validate_email_format(email: str) -> bool:
    """
    Validate email format using a comprehensive regex.

    Args:
        email: Email address to validate.

    Returns:
        True if the email format is valid.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> dict:
    """
    Check password strength and return detailed results.

    Args:
        password: Password to check.

    Returns:
        Dictionary with 'is_valid', 'score', and 'issues' keys.
    """
    issues = []
    score = 0

    if len(password) >= 10:
        score += 1
    else:
        issues.append('Password must be at least 10 characters long.')

    if len(password) >= 14:
        score += 1

    if re.search(r'[A-Z]', password):
        score += 1
    else:
        issues.append('Password must contain at least one uppercase letter.')

    if re.search(r'[a-z]', password):
        score += 1
    else:
        issues.append('Password must contain at least one lowercase letter.')

    if re.search(r'\d', password):
        score += 1
    else:
        issues.append('Password must contain at least one digit.')

    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        issues.append('Password must contain at least one special character.')

    return {
        'is_valid': len(issues) == 0,
        'score': score,
        'issues': issues,
    }


def compute_file_hash(file_content: bytes) -> str:
    """
    Compute SHA-256 hash of file content.

    Args:
        file_content: Raw bytes of the file.

    Returns:
        Hex digest of the SHA-256 hash.
    """
    return hashlib.sha256(file_content).hexdigest()


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """
    Check if a file has an allowed extension.

    Args:
        filename: Name of the file.
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.epub']).

    Returns:
        True if the extension is allowed.
    """
    if not filename or '.' not in filename:
        return False

    ext = '.' + filename.rsplit('.', 1)[-1].lower()
    return ext in [e.lower() for e in allowed_extensions]


def sanitize_string(value: str) -> str:
    """
    Sanitize a string by removing potentially dangerous characters.

    Args:
        value: Input string.

    Returns:
        Sanitized string.
    """
    if not value:
        return value

    # Remove null bytes
    value = value.replace('\x00', '')

    # Remove control characters except newlines and tabs
    value = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)

    return value.strip()
