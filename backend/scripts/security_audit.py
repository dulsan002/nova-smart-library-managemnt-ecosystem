#!/usr/bin/env python3
"""
Nova — Automated Security Audit Script
==========================================
Run this script to verify that the production security posture is correct.

Usage
-----
    cd backend/
    python scripts/security_audit.py

Exit codes
----------
    0 — All checks passed.
    1 — At least one CRITICAL or HIGH finding.
    2 — At least one MEDIUM finding (warnings only).

The script imports Django settings, so ``DJANGO_SETTINGS_MODULE`` must be set.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Bootstrap Django
# ---------------------------------------------------------------------------

# Assume we're running from backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nova.settings.production")

try:
    import django
    django.setup()
except Exception as e:
    print(f"⚠  Could not initialise Django ({e}). Running in static-only mode.\n")

# ---------------------------------------------------------------------------
# Severity constants
# ---------------------------------------------------------------------------

CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
INFO = "INFO"
PASS = "PASS"

ICONS = {
    CRITICAL: "🔴 CRITICAL",
    HIGH: "🟠 HIGH    ",
    MEDIUM: "🟡 MEDIUM  ",
    LOW: "🔵 LOW     ",
    INFO: "ℹ️  INFO    ",
    PASS: "✅ PASS    ",
}

findings: List[Tuple[str, str, str]] = []


def finding(severity: str, check: str, detail: str = ""):
    findings.append((severity, check, detail))
    print(f"  {ICONS[severity]}  {check}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_secret_key():
    """Verify SECRET_KEY is strong and not the development default."""
    try:
        from django.conf import settings

        key = settings.SECRET_KEY
        if "insecure" in key or key == "insecure-dev-key-change-in-production":
            finding(CRITICAL, "SECRET_KEY", "Still using the insecure development default!")
        elif len(key) < 50:
            finding(HIGH, "SECRET_KEY", f"Key length {len(key)} < 50 chars.")
        else:
            finding(PASS, "SECRET_KEY", f"Length {len(key)}, not default.")
    except Exception:
        finding(MEDIUM, "SECRET_KEY", "Could not load settings.")


def check_debug():
    """Ensure DEBUG is False in production."""
    try:
        from django.conf import settings

        if settings.DEBUG:
            finding(CRITICAL, "DEBUG", "DEBUG=True in production!")
        else:
            finding(PASS, "DEBUG", "DEBUG=False")
    except Exception:
        finding(MEDIUM, "DEBUG", "Could not load settings.")


def check_allowed_hosts():
    """ALLOWED_HOSTS must not contain '*'."""
    try:
        from django.conf import settings

        hosts = settings.ALLOWED_HOSTS
        if "*" in hosts:
            finding(CRITICAL, "ALLOWED_HOSTS", "Wildcard '*' allows any host!")
        elif not hosts:
            finding(HIGH, "ALLOWED_HOSTS", "Empty — no hosts allowed (server will 400).")
        else:
            finding(PASS, "ALLOWED_HOSTS", f"{hosts}")
    except Exception:
        finding(MEDIUM, "ALLOWED_HOSTS", "Could not load settings.")


def check_https_settings():
    """HSTS, SSL redirect, secure cookies."""
    try:
        from django.conf import settings

        checks = {
            "SECURE_SSL_REDIRECT": getattr(settings, "SECURE_SSL_REDIRECT", False),
            "SECURE_HSTS_SECONDS": getattr(settings, "SECURE_HSTS_SECONDS", 0) >= 31536000,
            "SECURE_HSTS_INCLUDE_SUBDOMAINS": getattr(settings, "SECURE_HSTS_INCLUDE_SUBDOMAINS", False),
            "SESSION_COOKIE_SECURE": getattr(settings, "SESSION_COOKIE_SECURE", False),
            "CSRF_COOKIE_SECURE": getattr(settings, "CSRF_COOKIE_SECURE", False),
        }
        for name, ok in checks.items():
            if ok:
                finding(PASS, name)
            else:
                finding(HIGH, name, "Not enabled!")
    except Exception:
        finding(MEDIUM, "HTTPS settings", "Could not load settings.")


def check_cors():
    """CORS must not allow all origins in production."""
    try:
        from django.conf import settings

        if getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False):
            finding(HIGH, "CORS_ALLOW_ALL_ORIGINS", "True — allows any origin!")
        else:
            origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
            finding(PASS, "CORS", f"Restricted to {len(origins)} origin(s).")
    except Exception:
        finding(MEDIUM, "CORS", "Could not load settings.")


def check_rate_limiting():
    """Rate limiting must be enabled."""
    try:
        from django.conf import settings

        if getattr(settings, "RATE_LIMIT_ENABLED", False):
            finding(PASS, "RATE_LIMITING", "Enabled.")
        else:
            finding(HIGH, "RATE_LIMITING", "Disabled!")
    except Exception:
        finding(MEDIUM, "RATE_LIMITING", "Could not load settings.")


def check_graphql_security():
    """GraphQL depth/complexity/introspection settings."""
    try:
        from django.conf import settings

        gql = getattr(settings, "GRAPHQL_SECURITY", {})
        if not gql:
            finding(HIGH, "GRAPHQL_SECURITY", "Not configured!")
            return

        intro = gql.get("INTROSPECTION_ENABLED", None)
        if intro is True:
            finding(MEDIUM, "GQL Introspection", "Enabled in production.")
        elif intro is False:
            finding(PASS, "GQL Introspection", "Disabled.")
        else:
            # Follows DEBUG
            if not settings.DEBUG:
                finding(PASS, "GQL Introspection", "Follows DEBUG=False → disabled.")
            else:
                finding(MEDIUM, "GQL Introspection", "Follows DEBUG=True → enabled.")

        depth = gql.get("MAX_DEPTH", 99)
        if depth > 12:
            finding(MEDIUM, "GQL Max Depth", f"{depth} — consider ≤ 10.")
        else:
            finding(PASS, "GQL Max Depth", str(depth))

    except Exception:
        finding(MEDIUM, "GRAPHQL_SECURITY", "Could not load settings.")


def check_password_validators():
    """Ensure password validators are configured."""
    try:
        from django.conf import settings

        validators = getattr(settings, "AUTH_PASSWORD_VALIDATORS", [])
        if len(validators) < 3:
            finding(MEDIUM, "PASSWORD_VALIDATORS", f"Only {len(validators)} validator(s).")
        else:
            finding(PASS, "PASSWORD_VALIDATORS", f"{len(validators)} validators.")
    except Exception:
        finding(MEDIUM, "PASSWORD_VALIDATORS", "Could not load settings.")


def check_password_hashers():
    """Argon2 should be first."""
    try:
        from django.conf import settings

        hashers = getattr(settings, "PASSWORD_HASHERS", [])
        if hashers and "Argon2" in hashers[0]:
            finding(PASS, "PASSWORD_HASHERS", "Argon2 is primary.")
        else:
            finding(MEDIUM, "PASSWORD_HASHERS", f"Primary: {hashers[0] if hashers else 'none'}.")
    except Exception:
        finding(MEDIUM, "PASSWORD_HASHERS", "Could not load settings.")


def check_session_security():
    """Session engine and cookie settings."""
    try:
        from django.conf import settings

        engine = getattr(settings, "SESSION_ENGINE", "")
        if "cache" in engine or "redis" in engine:
            finding(PASS, "SESSION_ENGINE", engine)
        else:
            finding(LOW, "SESSION_ENGINE", f"{engine} — consider cache-backed sessions.")

        httponly = getattr(settings, "SESSION_COOKIE_HTTPONLY", True)
        samesite = getattr(settings, "SESSION_COOKIE_SAMESITE", "Lax")
        if httponly and samesite in ("Lax", "Strict"):
            finding(PASS, "SESSION_COOKIE", f"HttpOnly={httponly}, SameSite={samesite}")
        else:
            finding(MEDIUM, "SESSION_COOKIE", f"HttpOnly={httponly}, SameSite={samesite}")
    except Exception:
        finding(MEDIUM, "SESSION_SECURITY", "Could not load settings.")


def check_middleware_stack():
    """Verify security middleware is present."""
    try:
        from django.conf import settings

        mw = settings.MIDDLEWARE
        required = [
            "SecurityMiddleware",
            "CorsMiddleware",
            "SecurityHeadersMiddleware",
            "GraphQLSecurityMiddleware",
            "RateLimitingMiddleware",
            "ExceptionHandlerMiddleware",
        ]
        for name in required:
            present = any(name in m for m in mw)
            if present:
                finding(PASS, f"MW: {name}")
            else:
                finding(HIGH, f"MW: {name}", "Missing from MIDDLEWARE!")
    except Exception:
        finding(MEDIUM, "MIDDLEWARE", "Could not load settings.")


def check_admin_url():
    """Django admin should not be at /admin/."""
    try:
        admin_url = os.environ.get("DJANGO_ADMIN_URL", "admin/")
        if admin_url in ("admin/", "admin"):
            finding(MEDIUM, "ADMIN_URL", f"Default path '{admin_url}' — easy to guess.")
        else:
            finding(PASS, "ADMIN_URL", f"Custom path: {admin_url}")
    except Exception:
        finding(LOW, "ADMIN_URL", "Could not determine.")


def check_raw_sql():
    """Scan Python files for raw SQL queries."""
    count = 0
    for py_file in BACKEND_DIR.rglob("*.py"):
        if "migrations" in str(py_file) or "venv" in str(py_file):
            continue
        try:
            content = py_file.read_text(errors="ignore")
            if re.search(r"\.raw\s*\(|\.extra\s*\(|cursor\.execute", content):
                count += 1
        except Exception:
            pass

    if count == 0:
        finding(PASS, "RAW_SQL", "No raw()/extra()/cursor.execute() found.")
    else:
        finding(MEDIUM, "RAW_SQL", f"{count} file(s) use raw SQL — review for injection risks.")


def check_env_file():
    """Ensure .env is not committed (check .gitignore)."""
    gitignore = BACKEND_DIR / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if ".env" in content:
            finding(PASS, ".env in .gitignore")
        else:
            finding(HIGH, ".env NOT in .gitignore", "Secrets may be committed!")
    else:
        # Check parent
        parent_gi = BACKEND_DIR.parent / ".gitignore"
        if parent_gi.exists() and ".env" in parent_gi.read_text():
            finding(PASS, ".env in .gitignore (parent)")
        else:
            finding(MEDIUM, ".gitignore", "Not found — ensure .env is excluded.")


def check_dependencies():
    """Check for known-insecure patterns in requirements."""
    req_file = BACKEND_DIR / "requirements" / "base.txt"
    if not req_file.exists():
        finding(INFO, "DEPENDENCIES", "requirements/base.txt not found.")
        return

    content = req_file.read_text()
    # Check for pinned versions (good) vs unpinned (risky)
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
    unpinned = [l for l in lines if ">=" not in l and "==" not in l and "<" not in l]
    if unpinned:
        finding(LOW, "DEPENDENCIES", f"{len(unpinned)} unpinned package(s): {unpinned[:3]}…")
    else:
        finding(PASS, "DEPENDENCIES", "All packages have version constraints.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("  Nova Security Audit")
    print("=" * 70)
    print()

    checks = [
        ("Secret Key", check_secret_key),
        ("Debug Mode", check_debug),
        ("Allowed Hosts", check_allowed_hosts),
        ("HTTPS / Transport", check_https_settings),
        ("CORS Policy", check_cors),
        ("Rate Limiting", check_rate_limiting),
        ("GraphQL Security", check_graphql_security),
        ("Password Validators", check_password_validators),
        ("Password Hashers", check_password_hashers),
        ("Session Security", check_session_security),
        ("Middleware Stack", check_middleware_stack),
        ("Admin URL", check_admin_url),
        ("Raw SQL Usage", check_raw_sql),
        (".env Protection", check_env_file),
        ("Dependencies", check_dependencies),
    ]

    for label, fn in checks:
        print(f"\n── {label} ──")
        try:
            fn()
        except Exception as e:
            finding(MEDIUM, label, f"Check failed: {e}")

    # Summary
    print("\n" + "=" * 70)
    crits = sum(1 for s, _, _ in findings if s == CRITICAL)
    highs = sum(1 for s, _, _ in findings if s == HIGH)
    meds = sum(1 for s, _, _ in findings if s == MEDIUM)
    lows = sum(1 for s, _, _ in findings if s == LOW)
    passes = sum(1 for s, _, _ in findings if s == PASS)

    print(
        f"  Results: {passes} PASS  |  {crits} CRITICAL  |  {highs} HIGH  "
        f"|  {meds} MEDIUM  |  {lows} LOW"
    )
    print("=" * 70)

    if crits or highs:
        print("\n❌ FAIL — Critical or High findings must be resolved before deployment.\n")
        return 1
    elif meds:
        print("\n⚠️  WARN — Medium findings should be reviewed.\n")
        return 2
    else:
        print("\n✅ ALL CHECKS PASSED.\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
