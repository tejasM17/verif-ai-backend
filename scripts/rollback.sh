#!/usr/bin/env bash
# Rollback script — drops all seeded collections and clears the checkpoint.
# Usage:
#   ./scripts/rollback.sh             # prompts for confirmation
#   ./scripts/rollback.sh --yes       # skip confirmation

set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d "venv" ]; then
  echo "no venv; nothing to rollback."
  exit 0
fi

PY="venv/Scripts/python.exe"
[ -x "$PY" ] || PY="venv/bin/python"

exec "$PY" -m app.seed rollback "$@"