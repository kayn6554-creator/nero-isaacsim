#!/usr/bin/env bash
# 推流方式运行 gcf 的 NERO lift 场景，用 Windows 上的 Isaac Sim WebRTC Streaming Client 连接 192.168.1.102 观看。
cd "$(dirname "$0")/.."
source scripts/env.sh
cd isaac_so_arm101
../.venv/bin/zero_agent --task Isaac-Nero-Lift-Cube-v0 --num_envs 1 --enable_cameras --headless --livestream 2 2>&1 \
  | tee /tmp/${USER}_stream_lift.log | grep -i -E "stream|Traceback"
