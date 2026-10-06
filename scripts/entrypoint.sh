#!/usr/bin/env sh
set -eu
flask --app run.py db upgrade
exec gunicorn --bind 0.0.0.0:5000 --workers "${WEB_CONCURRENCY:-2}" --access-logfile - --error-logfile - run:app
