#!/usr/bin/env sh
set -e
cd "$(dirname "$0")"
PY=$(command -v python3 || command -v python)
"$PY" scripts/install.py
