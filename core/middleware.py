import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.logger import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log HTTP requests and responses with structured data."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path
        
        extra_fields = {
            "event_name": "http_request",
            "http_method": method,
            "path": path,
        }

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            extra_fields.update({
                "event_status": "success",
                "http_status": response.status_code,
                "duration_ms": round(duration_ms, 2),
            })
            
            logger.info(
                f"Processed {method} {path} - {response.status_code}",
                extra=extra_fields
            )
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            extra_fields.update({
                "event_status": "failure",
                "http_status": 500,
                "duration_ms": round(duration_ms, 2),
                "error_message": str(exc),
            })
            
            logger.exception(
                f"Failed {method} {path} - Error: {exc}",
                extra=extra_fields
            )
            raise exc
