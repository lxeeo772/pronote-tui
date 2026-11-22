#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$(dirname "$DIR"):$PYTHONPATH"
exec "$DIR/.venv/bin/python" -m pronoterm.app "$@"
