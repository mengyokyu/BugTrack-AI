#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env || true
echo 'Environment ready. Run: source .venv/bin/activate && pytest -q'
