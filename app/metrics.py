from flask import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

REQUESTS = Counter("bugtrack_http_requests_total", "HTTP requests", ["method", "endpoint", "status"])
LATENCY = Histogram("bugtrack_http_request_latency_seconds", "HTTP request latency", ["endpoint"])
BUG_EVENTS = Counter("bugtrack_events_total", "Bug lifecycle events", ["event"])
HEALTH = Gauge("bugtrack_application_health", "Application health")
DATABASE = Gauge("bugtrack_database_health", "Database connectivity health")
HEALTH.set(1)
DATABASE.set(1)


def metrics_response():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
