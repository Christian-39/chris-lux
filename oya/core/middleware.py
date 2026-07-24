"""
Custom middleware for OYA.
"""
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .exceptions import (
    OYAException, ValidationError, PermissionDeniedError,
    AuthenticationError, DuplicateRecordError, DatabaseError, FileUploadError
)

logger = logging.getLogger("oya")


class AuditLogMiddleware(MiddlewareMixin):
    """Middleware to capture request data for audit logging."""

    def process_request(self, request):
        """Attach client IP to request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            request.client_ip = x_forwarded_for.split(",")[0].strip()
        else:
            request.client_ip = request.META.get("REMOTE_ADDR", "")
        return None


class ExceptionHandlerMiddleware(MiddlewareMixin):
    """Global exception handler middleware."""

    def process_exception(self, request, exception):
        """Handle custom exceptions and return standardized responses."""
        if isinstance(exception, ValidationError):
            return self._error_response(str(exception), 400)
        elif isinstance(exception, PermissionDeniedError):
            return self._error_response(str(exception), 403)
        elif isinstance(exception, AuthenticationError):
            return self._error_response(str(exception), 401)
        elif isinstance(exception, DuplicateRecordError):
            return self._error_response(str(exception), 409)
        elif isinstance(exception, DatabaseError):
            return self._error_response(str(exception), 500)
        elif isinstance(exception, FileUploadError):
            return self._error_response(str(exception), 400)
        elif isinstance(exception, OYAException):
            return self._error_response(str(exception), 400)

        # Log unhandled exceptions
        logger.error(f"Unhandled exception: {exception}", exc_info=True)
        return None

    def _error_response(self, message, status_code):
        if self._is_api_request():
            return JsonResponse({
                "success": False,
                "message": message
            }, status=status_code)
        return None

    def _is_api_request(self):
        return True
