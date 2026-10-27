#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
case_name="${1:-devkitc1_usb_esd15pf}"
if [[ ! "$case_name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "Invalid case name: $case_name" >&2
    exit 2
fi
exec toolchain/openEMS/bin/AppCSXCAD "models/${case_name}.xml"
