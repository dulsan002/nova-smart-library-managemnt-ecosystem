"""
Nova — Shared Type Definitions
================================
Common types and enums used across bounded contexts.
"""

from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = 'SUPER_ADMIN'
    LIBRARIAN = 'LIBRARIAN'
    ASSISTANT = 'ASSISTANT'
    USER = 'USER'


class VerificationStatus(str, Enum):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    MANUAL_REVIEW = 'MANUAL_REVIEW'


class BookCopyCondition(str, Enum):
    NEW = 'NEW'
    GOOD = 'GOOD'
    FAIR = 'FAIR'
    POOR = 'POOR'
    DAMAGED = 'DAMAGED'
    LOST = 'LOST'


class BookCopyStatus(str, Enum):
    AVAILABLE = 'AVAILABLE'
    BORROWED = 'BORROWED'
    RESERVED = 'RESERVED'
    MAINTENANCE = 'MAINTENANCE'
    LOST = 'LOST'


class BorrowStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    RETURNED = 'RETURNED'
    OVERDUE = 'OVERDUE'
    LOST = 'LOST'


class FineStatus(str, Enum):
    PENDING = 'PENDING'
    PARTIALLY_PAID = 'PARTIALLY_PAID'
    PAID = 'PAID'
    WAIVED = 'WAIVED'


class FineReason(str, Enum):
    OVERDUE = 'OVERDUE'
    DAMAGE = 'DAMAGE'
    LOST = 'LOST'


class DigitalAssetType(str, Enum):
    EBOOK_PDF = 'EBOOK_PDF'
    EBOOK_EPUB = 'EBOOK_EPUB'
    AUDIOBOOK = 'AUDIOBOOK'


class SessionStatus(str, Enum):
    ACTIVE = 'ACTIVE'
    PAUSED = 'PAUSED'
    COMPLETED = 'COMPLETED'
    TIMED_OUT = 'TIMED_OUT'


class SessionType(str, Enum):
    READING = 'READING'
    LISTENING = 'LISTENING'
    REVIEWING = 'REVIEWING'
    NOTING = 'NOTING'


class KPDimension(str, Enum):
    READING_TIME = 'READING_TIME'
    COMPLETION = 'COMPLETION'
    CONTENT_CREATION = 'CONTENT_CREATION'
    CONSISTENCY = 'CONSISTENCY'
    DIVERSITY = 'DIVERSITY'
    BONUS = 'BONUS'


class RecommendationStrategy(str, Enum):
    CONTENT_BASED = 'CONTENT_BASED'
    COLLABORATIVE = 'COLLABORATIVE'
    HYBRID = 'HYBRID'
    POPULAR = 'POPULAR'
    COLD_START = 'COLD_START'


class PredictionType(str, Enum):
    OVERDUE_RISK = 'OVERDUE_RISK'
    DEMAND_FORECAST = 'DEMAND_FORECAST'
    USER_SEGMENT = 'USER_SEGMENT'
    ENGAGEMENT_TREND = 'ENGAGEMENT_TREND'


class SecurityEventType(str, Enum):
    LOGIN_FAILED = 'LOGIN_FAILED'
    BRUTE_FORCE_DETECTED = 'BRUTE_FORCE_DETECTED'
    TOKEN_ABUSE = 'TOKEN_ABUSE'
    RATE_LIMIT_HIT = 'RATE_LIMIT_HIT'
    SUSPICIOUS_ENGAGEMENT = 'SUSPICIOUS_ENGAGEMENT'
    FILE_UPLOAD_BLOCKED = 'FILE_UPLOAD_BLOCKED'
    UNAUTHORIZED_ACCESS = 'UNAUTHORIZED_ACCESS'


class SecuritySeverity(str, Enum):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'


class LedgerAction(str, Enum):
    BORROW = 'BORROW'
    RETURN = 'RETURN'
    EXTEND = 'EXTEND'
    FINE_GENERATED = 'FINE_GENERATED'
    FINE_PAID = 'FINE_PAID'
    FINE_WAIVED = 'FINE_WAIVED'
    OVERDUE_FLAGGED = 'OVERDUE_FLAGGED'
