#!/usr/bin/env bash
set -euo pipefail
. .venv/bin/activate
ruff check app tests run.py --ignore E701,E702
python -m pytest -q --cov=app
