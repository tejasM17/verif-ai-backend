#!/usr/bin/env bash
# Verify script — prints collection counts vs targets.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="venv/Scripts/python.exe"
[ -x "$PY" ] || PY="venv/bin/python"
exec "$PY" -m app.seed verify