from prometheus_client import Counter, Histogram, Gauge

# Metric name: http_requests_total
# Purpose: Shows how much traffic the service is receiving.
# Labels: method, path, status_code
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests processed",
    ["method", "path", "status_code"]
)

# Metric name: http_request_duration_seconds
# Purpose: Shows request latency (supports p95/p99 via bucket aggregation).
# Labels: method, path, status_code
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path", "status_code"]
)

# Metric name: http_requests_errors_total
# Purpose: Shows the number of failed HTTP requests (5xx server errors).
# Labels: method, path, status_code
HTTP_REQUESTS_ERRORS_TOTAL = Counter(
    "http_requests_errors_total",
    "Total number of HTTP requests resulting in 5xx errors",
    ["method", "path", "status_code"]
)

# Metric name: application_ready
# Purpose: Shows readiness status of the application (1 = ready, 0 = not ready).
# Labels: None
APPLICATION_READY = Gauge(
    "application_ready",
    "Readiness status of the application (1 = ready, 0 = not ready)"
)
