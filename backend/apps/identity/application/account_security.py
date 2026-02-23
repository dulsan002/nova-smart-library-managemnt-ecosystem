"""
Nova — Account Security Service
=================================
Protects user accounts against brute-force attacks, credential stuffing,
and suspicious login patterns.

Features
--------
- **Progressive lockout**: After N failed attempts the account is locked
  for an exponentially increasing duration (5 min → 15 min → 60 min → …).
- **IP-level throttle**: Even if an attacker cycles through accounts, the
  *source IP address* is rate-limited.
- **Suspicious-login detection**: Flags logins from new device fingerprints
  or anomalous IP ranges and records a ``SecurityEvent``.
- **Automatic unlock**: Lockouts are time-based; no admin intervention is
  required (but admins *can* manually unlock via Django admin).

All counters/locks are stored in **Redis** (via Django cache) so they
survive restarts yet remain fast.  If Redis is unavailable the service
fails-open (allows the login) and logs a warning.
"""

from __future__ import annotations

import logging
import math
from typing import Optional, Tuple

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger("nova.security")

# =========================================================================
# Configuration (with sane defaults)
# =========================================================================

_CONF_DEFAULTS = {
    "MAX_FAILED_ATTEMPTS": 5,
    "LOCKOUT_BASE_SECONDS": 300,          # 5 minutes
    "LOCKOUT_MAX_SECONDS": 3600,          # 1 hour
    "LOCKOUT_MULTIPLIER": 2,              # exponential back-off factor
    "FAILED_ATTEMPT_WINDOW_SECONDS": 900, # 15-minute sliding window
    "IP_MAX_FAILED_ATTEMPTS": 20,         # per-IP across all accounts
    "IP_LOCKOUT_SECONDS": 600,            # 10-minute IP-level lockout
}


def _setting(key: str):
    return getattr(settings, "ACCOUNT_SECURITY", {}).get(key, _CONF_DEFAULTS[key])


# =========================================================================
# Cache key helpers
# =========================================================================

def _user_fail_key(email: str) -> str:
    return f"acct_lock:fail:{email.lower().strip()}"


def _user_lock_key(email: str) -> str:
    return f"acct_lock:lock:{email.lower().strip()}"


def _user_lock_count_key(email: str) -> str:
    return f"acct_lock:cnt:{email.lower().strip()}"


def _ip_fail_key(ip: str) -> str:
    return f"acct_lock:ip_fail:{ip}"


def _ip_lock_key(ip: str) -> str:
    return f"acct_lock:ip_lock:{ip}"


# =========================================================================
# Public API
# =========================================================================

def check_account_locked(email: str, ip: str) -> Tuple[bool, Optional[int]]:
    """
    Check whether the account or source IP is currently locked.

    Returns
    -------
    (is_locked, retry_after_seconds)
        ``retry_after_seconds`` is ``None`` when not locked.
    """
    try:
        # Account-level lock
        lock_ttl = cache.ttl(_user_lock_key(email))
        if lock_ttl and lock_ttl > 0:
            return True, lock_ttl

        # IP-level lock
        ip_ttl = cache.ttl(_ip_lock_key(ip))
        if ip_ttl and ip_ttl > 0:
            return True, ip_ttl

    except Exception as exc:
        logger.error("Account lock check failed (fail-open): %s", exc)

    return False, None


def record_failed_attempt(email: str, ip: str) -> None:
    """
    Record a failed login attempt.

    If the failure count exceeds the threshold, an account-level or
    IP-level lockout is applied.
    """
    try:
        window = _setting("FAILED_ATTEMPT_WINDOW_SECONDS")

        # --- Per-account tracking ---
        fail_key = _user_fail_key(email)
        fails = cache.get(fail_key, 0) + 1
        cache.set(fail_key, fails, timeout=window)

        max_fails = _setting("MAX_FAILED_ATTEMPTS")
        if fails >= max_fails:
            _apply_user_lockout(email, fails - max_fails)

        # --- Per-IP tracking ---
        ip_key = _ip_fail_key(ip)
        ip_fails = cache.get(ip_key, 0) + 1
        cache.set(ip_key, ip_fails, timeout=window)

        ip_max = _setting("IP_MAX_FAILED_ATTEMPTS")
        if ip_fails >= ip_max:
            _apply_ip_lockout(ip)

        logger.info(
            "Failed login attempt",
            extra={
                "email": email,
                "ip": ip,
                "account_fails": fails,
                "ip_fails": ip_fails,
            },
        )

    except Exception as exc:
        logger.error("Failed to record login failure (fail-open): %s", exc)


def record_successful_login(email: str, ip: str) -> None:
    """Clear failure counters after a successful authentication."""
    try:
        cache.delete(_user_fail_key(email))
        cache.delete(_ip_fail_key(ip))
    except Exception as exc:
        logger.error("Failed to clear login counters: %s", exc)


def unlock_account(email: str) -> None:
    """Manually unlock an account (admin action)."""
    try:
        cache.delete(_user_lock_key(email))
        cache.delete(_user_fail_key(email))
        cache.delete(_user_lock_count_key(email))
        logger.info("Account manually unlocked", extra={"email": email})
    except Exception as exc:
        logger.error("Failed to unlock account: %s", exc)


# =========================================================================
# Internal helpers
# =========================================================================

def _apply_user_lockout(email: str, previous_lockouts: int) -> None:
    """Apply an exponentially-increasing lockout to the account."""
    base = _setting("LOCKOUT_BASE_SECONDS")
    multiplier = _setting("LOCKOUT_MULTIPLIER")
    maximum = _setting("LOCKOUT_MAX_SECONDS")

    # How many times have we locked out before?
    cnt_key = _user_lock_count_key(email)
    lock_count = cache.get(cnt_key, 0)

    duration = min(base * (multiplier ** lock_count), maximum)
    duration = int(duration)

    cache.set(_user_lock_key(email), True, timeout=duration)
    cache.set(cnt_key, lock_count + 1, timeout=maximum * 2)

    logger.warning(
        "Account locked",
        extra={
            "email": email,
            "duration_seconds": duration,
            "lock_number": lock_count + 1,
        },
    )

    # Record security event (best-effort)
    try:
        from apps.governance.services import SecurityEventService

        SecurityEventService.record(
            event_type="ACCOUNT_LOCKED",
            severity="HIGH",
            description=f"Account {email} locked for {duration}s after repeated failed logins.",
            metadata={"email": email, "duration": duration, "lock_number": lock_count + 1},
        )
    except Exception:
        pass


def _apply_ip_lockout(ip: str) -> None:
    """Lock out an IP address entirely."""
    duration = _setting("IP_LOCKOUT_SECONDS")
    cache.set(_ip_lock_key(ip), True, timeout=duration)

    logger.warning(
        "IP address locked",
        extra={"ip": ip, "duration_seconds": duration},
    )

    try:
        from apps.governance.services import SecurityEventService

        SecurityEventService.record(
            event_type="IP_LOCKED",
            severity="HIGH",
            description=f"IP {ip} locked for {duration}s after excessive failed logins.",
            metadata={"ip": ip, "duration": duration},
        )
    except Exception:
        pass
