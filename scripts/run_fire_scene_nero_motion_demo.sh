#!/usr/bin/env bash
# Stream the NERO joint-motion demo in the passive fire-cabinet scene.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh

if [[ ! -x .venv/bin/python ]]; then
  echo "[ERROR] .venv/bin/python not found. Follow KANBAN.md Steps 3-4 first." >&2
  exit 1
fi
if [[ ! -d isaac_so_arm101 ]]; then
  echo "[ERROR] isaac_so_arm101 is missing. Follow KANBAN.md Step 3 first." >&2
  exit 1
fi

.venv/bin/python scripts/fire_scene_nero_motion_demo.py --headless --livestream 2 "$@" 2>&1 \
  | tee "/tmp/$USER"_fire_scene_nero_motion_demo.log \
  | grep -E "\[DEMO\]|\[INFO\]|\[MOVE\]|\[WARN\]|\[ERROR\]|Traceback"
