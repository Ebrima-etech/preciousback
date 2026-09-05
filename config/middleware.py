import logging
import traceback
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class ErrorLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        logger.error(
            f"Unhandled exception on {request.method} {request.path}",
            exc_info=True,
            extra={
                'request_path': request.path,
                'request_method': request.method,
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc(),
            }
        )
        return JsonResponse(
            {'error': str(exception), 'type': type(exception).__name__},
            status=500
        )
