"""
Nova — Rate Limiting Middleware
=================================
Token bucket rate limiting using Redis.
Applied per-IP and per-user for different endpoint categories.
"""

import time
import logging
import hashlib
import json

from django.conf import settings
from django.http import JsonResponse

logger = logging.getLogger('nova.security')


class RateLimitingMiddleware:
    """
    Multi-tier rate limiting middleware using Redis-backed token bucket.

    Tiers:
    - Auth endpoints: strict (prevents brute force)
    - Mutations: moderate
    - Queries: relaxed
    - Heartbeat: high-frequency allowed
    - Uploads: strict
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip rate limiting if disabled (dev/test)
        if not getattr(settings, 'RATE_LIMIT_ENABLED', False):
            return self.get_response(request)

        # Only rate limit GraphQL endpoint
        if not request.path.startswith('/graphql'):
            return self.get_response(request)

        # Determine rate limit tier from request
        tier = self._determine_tier(request)
        limit_config = self._get_limit_config(tier)

        # Generate rate limit key
        key = self._generate_key(request, tier)

        # Check rate limit
        is_allowed, remaining, retry_after = self._check_rate_limit(
            key, limit_config['requests'], limit_config['window']
        )

        if not is_allowed:
            logger.warning(
                f'Rate limit exceeded',
                extra={
                    'ip': self._get_client_ip(request),
                    'user_id': str(getattr(request.user, 'id', None)),
                    'tier': tier,
                    'retry_after': retry_after,
                }
            )

            return JsonResponse(
                {
                    'errors': [{
                        'message': f'Rate limit exceeded. Please try again in {retry_after} seconds.',
                        'extensions': {
                            'code': 'RATE_LIMITED',
                            'retryAfter': retry_after,
                        }
                    }]
                },
                status=429,
                headers={
                    'Retry-After': str(retry_after),
                    'X-RateLimit-Remaining': '0',
                }
            )

        # Process request
        response = self.get_response(request)

        # Add rate limit headers
        response['X-RateLimit-Remaining'] = str(remaining)

        return response

    def _determine_tier(self, request) -> str:
        """Determine rate limit tier from request content."""
        if request.method != 'POST':
            return 'QUERY'

        try:
            body = json.loads(request.body)
            query = body.get('query', '')

            if 'mutation' in query.lower():
                if any(kw in query.lower() for kw in ['login', 'register', 'refreshtoken']):
                    return 'AUTH'
                if any(kw in query.lower() for kw in ['upload', 'uploaddigitalasset']):
                    return 'UPLOAD'
                if 'heartbeat' in query.lower():
                    return 'HEARTBEAT'
                return 'MUTATION'
        except (json.JSONDecodeError, AttributeError):
            pass

        return 'QUERY'

    def _get_limit_config(self, tier: str) -> dict:
        """Get rate limit configuration for a tier."""
        configs = {
            'AUTH': {'requests': 5, 'window': 60},
            'MUTATION': {'requests': 30, 'window': 60},
            'QUERY': {'requests': 120, 'window': 60},
            'HEARTBEAT': {'requests': 60, 'window': 60},
            'UPLOAD': {'requests': 10, 'window': 3600},
        }
        return configs.get(tier, configs['QUERY'])

    def _generate_key(self, request, tier: str) -> str:
        """Generate a cache key for rate limiting."""
        ip = self._get_client_ip(request)

        # Use user ID if authenticated, otherwise IP
        if hasattr(request, 'user') and request.user.is_authenticated:
            identifier = f'user:{request.user.id}'
        else:
            identifier = f'ip:{ip}'

        return f'rl:{identifier}:{tier}'

    def _check_rate_limit(self, key: str, max_requests: int, window: int):
        """
        Check if request is within rate limit using Redis.

        Returns:
            Tuple of (is_allowed, remaining_requests, retry_after_seconds)
        """
        try:
            from django.core.cache import cache

            # Get current count
            current = cache.get(key, 0)

            if current >= max_requests:
                # Get TTL for retry-after
                ttl = cache.ttl(key) if hasattr(cache, 'ttl') else window
                return False, 0, max(ttl, 1)

            # Increment counter
            if current == 0:
                cache.set(key, 1, timeout=window)
            else:
                try:
                    cache.incr(key)
                except ValueError:
                    cache.set(key, 1, timeout=window)

            remaining = max_requests - current - 1
            return True, remaining, 0

        except Exception as e:
            # If Redis is down, allow the request (fail-open)
            logger.error(f'Rate limiting error: {e}')
            return True, max_requests, 0

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
