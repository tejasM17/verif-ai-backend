#!/usr/bin/env bash
# Seed script — runs the full recruiter seeding pipeline against MongoDB Atlas + Firebase Auth.
# Usage:
#   ./scripts/seed.sh                 # full run with defaults
#   ./scripts/seed.sh --workers 4     # override worker count
#   ./scripts/seed.sh --skip-firebase # skip Firebase auth (Mongo only)
#   ./scripts/seed.sh --stage jobs    # run only one stage

set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d "venv" ]; then
  echo "creating virtualenv..."
  python -m venv venv
fi

PY="venv/Scripts/python.exe"
[ -x "$PY" ] || PY="venv/bin/python"

"$PY" -m pip install -q -r requirements.txt

exec "$PY" -m app.seed run "$@"