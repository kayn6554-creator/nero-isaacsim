#!/usr/bin/env bash
# 把 gcf 的 NERO 仿真项目（含未提交的改动）复制到本仓库下，不复制环境/日志/缓存。
# 只读取 gcf 的目录，不会修改它。
set -e
cd "$(dirname "$0")/.."
SRC=/data/gcf/workspace/isaac_so_arm101
rsync -a --info=progress2 \
  --exclude=.venv --exclude=logs --exclude=outputs --exclude=shadercache --exclude=nv_shadercache \
  --exclude=__pycache__ --exclude=camera_samples \
  "$SRC"/ ./isaac_so_arm101/
cd isaac_so_arm101
git add -A && git -c user.name=panhe -c user.email=panhe@local commit -qm "copy from gcf isaac_so_arm101 (local)" || true
git log --oneline | head -3
