#!/usr/bin/env bash
# 推流方式运行消防箱关节体测试（NERO + 消防箱 + 2 个灭火器，脚本自动开关门）。
cd "$(dirname "$0")/.."
source scripts/env.sh
.venv/bin/python scripts/fire_cabinet_test.py --headless --livestream 2 "$@" 2>&1 \
  | tee /tmp/${USER}_fire.log | grep -E "\[INFO\] cab|PHASE|physx|t=|Traceback"
