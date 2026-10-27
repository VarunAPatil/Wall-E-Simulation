#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec toolchain/openEMS/venv/bin/python scripts/run_microstrip.py "$@"
