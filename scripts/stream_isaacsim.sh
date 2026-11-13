#!/usr/bin/env bash
# 推流方式启动完整的 Isaac Sim 界面（不经过 IsaacLab），用于手动打开 USD、鼠标交互、录演示视频。
cd "$(dirname "$0")/.."
source scripts/env.sh
.venv/bin/isaacsim isaacsim.exp.full.streaming --no-window 2>&1 \
  | tee /tmp/${USER}_isaacsim.log | grep -i -E "app ready|stream|Traceback|error:"
