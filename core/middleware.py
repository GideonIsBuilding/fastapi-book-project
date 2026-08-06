import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.logger import logger
from core.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION_SECONDS, HTTP_REQUESTS_ERRORS_TOTAL

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log HTTP requests and responses with structured data and metrics."""

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
            duration = time.perf_counter() - start_time
            duration_ms = duration * 1000
            
            # Reconstruct normalized route pattern using path_params to prevent high-cardinality metric labels
            route = request.scope.get("route")
            if not route:
                normalized_path = "not_found"
            else:
                path_segments = request.url.path.split("/")
                param_map = {str(v): k for k, v in request.path_params.items() if v}
                for i, segment in enumerate(path_segments):
                    if segment in param_map:
                        path_segments[i] = f"{{{param_map[segment]}}}"
                normalized_path = "/".join(path_segments)
            status_code = str(response.status_code)
            
            # Record Prometheus metrics
            HTTP_REQUESTS_TOTAL.labels(method=method, path=normalized_path, status_code=status_code).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=normalized_path, status_code=status_code).observe(duration)
            if response.status_code >= 500:
                HTTP_REQUESTS_ERRORS_TOTAL.labels(method=method, path=normalized_path, status_code=status_code).inc()
            
            extra_fields.update({
                "event_status": "success",
                "http_status": response.status_code,
                "duration_ms": round(duration_ms, 2),
            })
            
            is_health_check = path in ("/health", "/ready", "/metrics", "/healthcheck")
            is_success = response.status_code < 400
            
            if not (is_health_check and is_success):
                logger.info(
                    f"Processed {method} {path} - {response.status_code}",
                    extra=extra_fields
                )
            return response

        except Exception as exc:
            duration = time.perf_counter() - start_time
            duration_ms = duration * 1000
            
            route = request.scope.get("route")
            if not route:
                normalized_path = "not_found"
            else:
                path_segments = request.url.path.split("/")
                param_map = {str(v): k for k, v in request.path_params.items() if v}
                for i, segment in enumerate(path_segments):
                    if segment in param_map:
                        path_segments[i] = f"{{{param_map[segment]}}}"
                normalized_path = "/".join(path_segments)
            status_code = "500"
            
            # Record Prometheus metrics for failures
            HTTP_REQUESTS_TOTAL.labels(method=method, path=normalized_path, status_code=status_code).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=normalized_path, status_code=status_code).observe(duration)
            HTTP_REQUESTS_ERRORS_TOTAL.labels(method=method, path=normalized_path, status_code=status_code).inc()
            
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
