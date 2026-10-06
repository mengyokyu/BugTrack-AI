#!/usr/bin/env bash
set -euo pipefail
. .venv/bin/activate
flask --app run.py db upgrade
