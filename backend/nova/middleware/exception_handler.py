"""
Nova — Centralized Exception Handler Middleware
==================================================
Catches all unhandled exceptions and returns standardized error responses.
Prevents leaking stack traces or internal details to clients.
"""

import logging
import traceback

from django.conf import settings
from django.http import JsonResponse

from apps.common.exceptions import (
    NovaBaseException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    RateLimitExceededError,
)

logger = logging.getLogger('nova')


class ExceptionHandlerMiddleware:
    """
    Catches exceptions from view/resolver processing and returns
    standardized JSON error responses.

    Maps domain exceptions to HTTP status codes:
    - AuthenticationError → 401
    - AuthorizationError → 403
    - NotFoundError → 404
    - ValidationError → 400
    - RateLimitExceededError → 429
    - NovaBaseException → 400
    - Unhandled Exception → 500
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as exc:
            return self._handle_exception(exc, request)

    def process_exception(self, request, exception):
        """Django middleware hook for unhandled exceptions."""
        return self._handle_exception(exception, request)

    def _handle_exception(self, exc, request):
        """Map exceptions to appropriate HTTP responses."""

        if isinstance(exc, AuthenticationError):
            return self._error_response(exc, 401)

        elif isinstance(exc, AuthorizationError):
            return self._error_response(exc, 403)

        elif isinstance(exc, NotFoundError):
            return self._error_response(exc, 404)

        elif isinstance(exc, RateLimitExceededError):
            response = self._error_response(exc, 429)
            retry_after = exc.details.get('retry_after', 60)
            response['Retry-After'] = str(retry_after)
            return response

        elif isinstance(exc, ValidationError):
            return self._error_response(exc, 400)

        elif isinstance(exc, NovaBaseException):
            return self._error_response(exc, 400)

        else:
            # Unhandled exception — log full traceback
            logger.error(
                f'Unhandled exception: {type(exc).__name__}: {exc}',
                exc_info=True,
                extra={
                    'path': request.path,
                    'method': request.method,
                }
            )

            # In production, hide internal details
            if not settings.DEBUG:
                return JsonResponse(
                    {
                        'errors': [{
                            'message': 'An unexpected error occurred. Please try again later.',
                            'extensions': {
                                'code': 'INTERNAL_ERROR',
                            }
                        }]
                    },
                    status=500,
                )
            else:
                # In development, show details
                return JsonResponse(
                    {
                        'errors': [{
                            'message': str(exc),
                            'extensions': {
                                'code': 'INTERNAL_ERROR',
                                'type': type(exc).__name__,
                                'traceback': traceback.format_exc(),
                            }
                        }]
                    },
                    status=500,
                )

    @staticmethod
    def _error_response(exc: NovaBaseException, status_code: int) -> JsonResponse:
        """Build a standardized error response from a NovaBaseException."""
        error_body = {
            'errors': [{
                'message': exc.message,
                'extensions': {
                    'code': exc.code,
                }
            }]
        }

        if exc.details:
            error_body['errors'][0]['extensions']['details'] = exc.details

        return JsonResponse(error_body, status=status_code)
