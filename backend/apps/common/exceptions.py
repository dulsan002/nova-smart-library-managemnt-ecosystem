"""
Nova — Domain Exceptions
==========================
Centralized exception hierarchy for the entire application.
All domain-specific exceptions inherit from NovaBaseException.
"""


class NovaBaseException(Exception):
    """Base exception for all Nova domain errors."""

    def __init__(self, message: str, code: str = 'INTERNAL_ERROR', details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# =============================================================================
# Authentication & Authorization Exceptions
# =============================================================================

class AuthenticationError(NovaBaseException):
    """Raised when authentication fails."""

    def __init__(self, message: str = 'Authentication failed.', code: str = 'AUTHENTICATION_ERROR',
                 details: dict = None):
        super().__init__(message, code=code, details=details)


class AuthorizationError(NovaBaseException):
    """Raised when a user lacks permission for an action."""

    def __init__(self, message: str = 'You do not have permission to perform this action.',
                 code: str = 'AUTHORIZATION_ERROR', details: dict = None):
        super().__init__(message, code=code, details=details)


class TokenError(NovaBaseException):
    """Raised for JWT token issues (expired, invalid, revoked)."""

    def __init__(self, message: str = 'Token is invalid or expired.', details: dict = None):
        super().__init__(message, code='TOKEN_ERROR', details=details)


# =============================================================================
# Validation Exceptions
# =============================================================================

class ValidationError(NovaBaseException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = None, details: dict = None):
        self.field = field
        _details = details or {}
        if field:
            _details['field'] = field
        super().__init__(message, code='VALIDATION_ERROR', details=_details)


class ISBNValidationError(ValidationError):
    """Raised when ISBN validation fails."""

    def __init__(self, isbn: str, message: str = None):
        msg = message or f'Invalid ISBN: {isbn}'
        super().__init__(msg, field='isbn', details={'isbn': isbn})


# =============================================================================
# Resource Exceptions
# =============================================================================

class NotFoundError(NovaBaseException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str = None,
                 details: dict = None):
        msg = f'{resource_type} not found.'
        if resource_id:
            msg = f'{resource_type} with ID {resource_id} not found.'
        _details = details or {}
        _details['resource_type'] = resource_type
        if resource_id:
            _details['resource_id'] = str(resource_id)
        super().__init__(msg, code='NOT_FOUND', details=_details)


class ConflictError(NovaBaseException):
    """Raised when an operation conflicts with current state."""

    def __init__(self, message: str, code: str = 'CONFLICT', details: dict = None):
        super().__init__(message, code=code, details=details)


class ConcurrencyError(NovaBaseException):
    """Raised when optimistic concurrency control detects a conflict."""

    def __init__(self, message: str = 'Resource was modified by another process.',
                 details: dict = None):
        super().__init__(message, code='CONCURRENCY_CONFLICT', details=details)


# =============================================================================
# Circulation Exceptions
# =============================================================================

class BorrowingError(NovaBaseException):
    """Raised when a borrowing operation fails."""

    def __init__(self, message: str, code: str = 'BORROWING_ERROR', details: dict = None):
        super().__init__(message, code=code, details=details)


class BookUnavailableError(BorrowingError):
    """Raised when a book is not available for borrowing."""

    def __init__(self, book_id: str = None, details: dict = None):
        msg = 'This book is currently unavailable for borrowing.'
        _details = details or {}
        if book_id:
            _details['book_id'] = str(book_id)
        super().__init__(msg, details=_details)


class BorrowLimitExceededError(BorrowingError):
    """Raised when user has reached maximum concurrent borrows."""

    def __init__(self, max_borrows: int, details: dict = None):
        msg = f'You have reached the maximum of {max_borrows} concurrent borrows.'
        _details = details or {}
        _details['max_borrows'] = max_borrows
        super().__init__(msg, details=_details)


class UnpaidFinesError(BorrowingError):
    """Raised when user has unpaid fines above threshold."""

    def __init__(self, amount: float, threshold: float, details: dict = None):
        msg = (f'You have ${amount:.2f} in unpaid fines. '
               f'Please pay outstanding fines (threshold: ${threshold:.2f}) before borrowing.')
        _details = details or {}
        _details['unpaid_amount'] = float(amount)
        _details['threshold'] = float(threshold)
        super().__init__(msg, details=_details)


# =============================================================================
# Digital Content Exceptions
# =============================================================================

class SessionError(NovaBaseException):
    """Raised for reading/listening session errors."""

    def __init__(self, message: str, code: str = 'SESSION_ERROR', details: dict = None):
        super().__init__(message, code=code, details=details)


class ActiveSessionExistsError(SessionError):
    """Raised when user already has an active session for this asset."""

    def __init__(self, asset_id: str = None, details: dict = None):
        msg = 'You already have an active session for this content.'
        _details = details or {}
        if asset_id:
            _details['asset_id'] = str(asset_id)
        super().__init__(msg, details=_details)


# =============================================================================
# Engagement Exceptions
# =============================================================================

class EngagementError(NovaBaseException):
    """Raised for engagement/KP system errors."""

    def __init__(self, message: str, code: str = 'ENGAGEMENT_ERROR', details: dict = None):
        super().__init__(message, code=code, details=details)


class DailyKPCapReachedError(EngagementError):
    """Raised when daily KP cap is reached."""

    def __init__(self, cap: int, details: dict = None):
        msg = f'Daily Knowledge Points cap of {cap} reached. Great work today!'
        _details = details or {}
        _details['daily_cap'] = cap
        super().__init__(msg, details=_details)


# =============================================================================
# Verification Exceptions
# =============================================================================

class VerificationError(NovaBaseException):
    """Raised for ID verification errors."""

    def __init__(self, message: str, code: str = 'VERIFICATION_ERROR', details: dict = None):
        super().__init__(message, code=code, details=details)


# =============================================================================
# Rate Limiting
# =============================================================================

class RateLimitExceededError(NovaBaseException):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int = 60, details: dict = None):
        msg = f'Rate limit exceeded. Please try again in {retry_after} seconds.'
        _details = details or {}
        _details['retry_after'] = retry_after
        super().__init__(msg, code='RATE_LIMITED', details=_details)


# =============================================================================
# File Upload Exceptions
# =============================================================================

class FileUploadError(NovaBaseException):
    """Raised for file upload validation errors."""

    def __init__(self, message: str, code: str = 'FILE_UPLOAD_ERROR', details: dict = None):
        super().__init__(message, code=code, details=details)
