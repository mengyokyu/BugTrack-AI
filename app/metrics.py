from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import Response
REQUESTS = Counter("bugtrack_http_requests_total", "HTTP requests", ["method", "endpoint", "status"])
LATENCY = Histogram("bugtrack_http_request_latency_seconds", "HTTP request latency", ["endpoint"])
HEALTH = Gauge("bugtrack_application_health", "Application health")
HEALTH.set(1)
def metrics_response(): return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
