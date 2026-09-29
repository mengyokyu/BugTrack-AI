import logging
import time
from flask import Flask, jsonify, request
from .config import Config
from .extensions import db
from .metrics import REQUESTS, LATENCY

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config: app.config.update(test_config)
    db.init_app(app)
    from .routes import bp
    app.register_blueprint(bp)
    with app.app_context(): db.create_all()
    @app.before_request
    def start_timer(): request._started_at = time.perf_counter()
    @app.after_request
    def record(response):
        elapsed = time.perf_counter() - getattr(request, "_started_at", time.perf_counter())
        endpoint = request.endpoint or "unknown"
        REQUESTS.labels(request.method, endpoint, response.status_code).inc()
        LATENCY.labels(endpoint).observe(elapsed)
        app.logger.info("request method=%s endpoint=%s status=%s", request.method, endpoint, response.status_code)
        return response
    @app.errorhandler(Exception)
    def handle_error(error):
        code = getattr(error, "code", 500)
        return jsonify(error="request_failed", message="The request could not be completed", status=code), code
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return app
