from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    "nestora_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_DURATION = Histogram(
    "nestora_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)
