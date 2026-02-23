"""
Nova — Security Headers Middleware
=====================================
Adds comprehensive security-related HTTP headers to all responses.

Headers set unconditionally:
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 0 (modern best-practice; rely on CSP instead)
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: restrictive browser-feature allow-list
- X-DNS-Prefetch-Control: off
- Cross-Origin-Opener-Policy
- Cross-Origin-Resource-Policy

Production-only:
- Content-Security-Policy (strict)
- X-Frame-Options: DENY
- Cross-Origin-Embedder-Policy: require-corp (if no embedding needed)
"""

import hashlib
import os
from typing import Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse


class SecurityHeadersMiddleware:
    """
    Adds security headers to every response.

    In production the CSP is strict-dynamic with a per-request nonce that
    can be consumed in templates via ``request.csp_nonce``.  For API-only
    responses (GraphQL) the nonce is irrelevant but the header still
    provides defence-in-depth.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Generate a per-request CSP nonce (32 hex chars)
        nonce = hashlib.sha256(os.urandom(32)).hexdigest()[:32]
        request.csp_nonce = nonce  # accessible in templates as {{ request.csp_nonce }}

        response = self.get_response(request)

        # ----- Universal headers -----
        response['X-Content-Type-Options'] = 'nosniff'
        # X-XSS-Protection: 0 is the modern recommendation
        # (Chrome removed legacy auditor; the old "1; mode=block" can
        # introduce XSS in some edge-cases).
        response['X-XSS-Protection'] = '0'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['X-DNS-Prefetch-Control'] = 'off'

        # Permissions-Policy: disallow all sensitive browser APIs
        response['Permissions-Policy'] = (
            'accelerometer=(), ambient-light-sensor=(), autoplay=(), '
            'battery=(), camera=(), cross-origin-isolated=(), display-capture=(), '
            'document-domain=(), encrypted-media=(), execution-while-not-rendered=(), '
            'execution-while-out-of-viewport=(), fullscreen=(self), '
            'geolocation=(), gyroscope=(), keyboard-map=(), magnetometer=(), '
            'microphone=(), midi=(), navigation-override=(), payment=(), '
            'picture-in-picture=(), publickey-credentials-get=(), '
            'screen-wake-lock=(), sync-xhr=(), usb=(), web-share=(), '
            'xr-spatial-tracking=()'
        )

        # Cross-Origin policies
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Resource-Policy'] = 'same-origin'

        # ----- Production-only headers -----
        if not settings.DEBUG:
            response['X-Frame-Options'] = 'DENY'

            # Strict Content-Security-Policy with nonce
            if 'Content-Security-Policy' not in response:
                csp_directives = [
                    "default-src 'self'",
                    f"script-src 'self' 'nonce-{nonce}' 'strict-dynamic'",
                    "style-src 'self' 'unsafe-inline'",
                    "img-src 'self' data: blob: https:",
                    "font-src 'self' data:",
                    "connect-src 'self'",
                    "media-src 'self' blob:",
                    "object-src 'none'",
                    "base-uri 'self'",
                    "form-action 'self'",
                    "frame-ancestors 'none'",
                    "upgrade-insecure-requests",
                ]
                response['Content-Security-Policy'] = '; '.join(csp_directives)

            # Cross-Origin-Embedder-Policy (API-only; SPA served from CDN/Nginx)
            response['Cross-Origin-Embedder-Policy'] = 'require-corp'

        # ----- No-cache for GraphQL -----
        if request.path.startswith('/graphql'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma'] = 'no-cache'

        # ----- Remove Server header (best-effort; usually set by web server) -----
        response.headers.pop('Server', None)

        return response

