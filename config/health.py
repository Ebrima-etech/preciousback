from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    # Check cache
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        cache_status = "healthy"
    except Exception as e:
        logger.warning(f"Cache health check failed: {e}")
        cache_status = "degraded"

    # Overall status
    status = "healthy" if db_status == "healthy" else "unhealthy"

    return JsonResponse({
        "status": status,
        "database": db_status,
        "cache": cache_status,
    })
