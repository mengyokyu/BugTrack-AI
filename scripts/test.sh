#!/usr/bin/env bash
set -euo pipefail
. .venv/bin/activate
ruff check app tests run.py
python -m pytest -q --cov=app
