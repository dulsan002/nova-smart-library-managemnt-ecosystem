"""
Nova — Request Logging Middleware
===================================
Logs all incoming requests with timing, user context, and response status.
"""

import time
import logging
import uuid

from django.conf import settings

logger = logging.getLogger('nova')


class RequestLoggingMiddleware:
    """
    Middleware that logs every request with:
    - Request ID (for tracing)
    - Method and path
    - User ID (if authenticated)
    - Response status code
    - Response time in milliseconds
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        request.request_id = request_id

        # Start timer
        start_time = time.monotonic()

        # Process request
        response = self.get_response(request)

        # Calculate duration
        duration_ms = (time.monotonic() - start_time) * 1000

        # Extract user info
        user_id = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = str(request.user.id)

        # Log the request
        log_data = {
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'duration_ms': round(duration_ms, 2),
            'user_id': user_id,
            'ip': self._get_client_ip(request),
        }

        # Choose log level based on status code
        if response.status_code >= 500:
            logger.error('Request completed', extra=log_data)
        elif response.status_code >= 400:
            logger.warning('Request completed', extra=log_data)
        else:
            logger.info('Request completed', extra=log_data)

        # Add request ID to response headers
        response['X-Request-ID'] = request_id

        return response

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
