#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$(dirname "$DIR"):$PYTHONPATH"
exec "$DIR/.venv/bin/python" "$DIR/diag.py" "$@"
