#!/usr/bin/env bash
# Stream the passive fire-cabinet lid baseline; never command cabinet joint positions.
set -o pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh
.venv/bin/python scripts/fire_lid_passive_test.py --headless --livestream 2 "$@" 2>&1 \
  | tee /tmp/panhe_fire_lid_passive.log \
  | grep -E "\[BASELINE\]|\[INFO\]|t=|Traceback"
