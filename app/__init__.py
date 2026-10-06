import logging
import secrets
import time
import uuid

from flask import Flask, g, jsonify, request, session
from werkzeug.exceptions import HTTPException

from .config import Config
from .extensions import db, limiter, migrate
from .metrics import LATENCY, REQUESTS


STATE_CHANGING = {"POST", "PUT", "PATCH", "DELETE"}


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY") and not app.config.get("TESTING"):
        raise RuntimeError("SECRET_KEY must be configured outside tests")
    if app.config.get("TESTING") and not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = secrets.token_urlsafe(32)

    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    from .routes import bp
    app.register_blueprint(bp)

    @app.before_request
    def request_context():
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))[:64]
        request._started_at = time.perf_counter()
        if request.method in STATE_CHANGING and not app.config.get("TESTING"):
            if request.endpoint not in {"main.register", "main.login"}:
                token = request.headers.get("X-CSRFToken") or request.form.get("csrf_token")
                if not token or token != session.get("csrf_token"):
                    return jsonify(error="csrf_validation_failed"), 400

    @app.after_request
    def record(response):
        elapsed = time.perf_counter() - getattr(request, "_started_at", time.perf_counter())
        endpoint = request.endpoint or "unknown"
        REQUESTS.labels(request.method, endpoint, response.status_code).inc()
        LATENCY.labels(endpoint).observe(elapsed)
        response.headers["X-Request-ID"] = g.get("request_id", "")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'"
        app.logger.info("request_id=%s method=%s endpoint=%s status=%s", g.get("request_id"), request.method, endpoint, response.status_code)
        return response

    @app.errorhandler(Exception)
    def handle_error(error):
        if isinstance(error, HTTPException):
            return jsonify(error="request_failed", message=error.description, status=error.code), error.code
        app.logger.exception("request_id=%s unhandled application error", g.get("request_id"))
        return jsonify(error="internal_server_error", message="The request could not be completed", status=500), 500

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return app
