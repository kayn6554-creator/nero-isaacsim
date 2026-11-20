#!/usr/bin/env bash
# Start one persistent Isaac Sim process: scene + WebRTC + localhost TCP control.
set -uo pipefail
cd "$(dirname "$0")/.."

# env.sh intentionally deactivates Conda; keep errexit disabled while sourcing it.
source scripts/env.sh
set -e

if [[ ! -x .venv/bin/python ]]; then
  echo "[ERROR] .venv/bin/python not found." >&2
  exit 1
fi
if [[ ! -d isaac_so_arm101 ]]; then
  echo "[ERROR] isaac_so_arm101 is missing." >&2
  exit 1
fi

LOG="/tmp/$USER_fire_scene_control_server.log"
echo "[INFO] Full log: $LOG"
.venv/bin/python scripts/fire_scene_control_server.py --headless --livestream 2 "$@" 2>&1 | tee "$LOG"
