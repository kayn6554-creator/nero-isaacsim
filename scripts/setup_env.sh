#!/usr/bin/env bash
# 一次性安装：Python 3.11 + Isaac Sim 5.1.0 + IsaacLab 2.3.0 + torch 2.7.0(cu128)
# 不需要 root。下载约 15~20 GB，建议在 tmux 里运行：
#   tmux new -s isaac_install
#   bash scripts/setup_env.sh
set -e
cd "$(dirname "$0")/.."
source scripts/env.sh

# 1. 装 uv（已装会跳过）
command -v uv >/dev/null || python3 -m pip install --user -i https://pypi.tuna.tsinghua.edu.cn/simple uv
uv --version

# 2. 建虚拟环境
[ -d .venv ] || uv venv --python 3.11 .venv

# 3. flatdict 4.0.1 构建时需要 pkg_resources，setuptools>=81 已删掉它，所以限制版本
echo "setuptools<81" > build-constraints.txt

# 4. warp-lang 先从清华源单独装（NVIDIA 源下载这个大包经常超时），版本和 gcf 的环境一致
uv pip install --python .venv/bin/python -i https://pypi.tuna.tsinghua.edu.cn/simple warp-lang==1.10.1

# 5. 主安装（中途超时就重跑这个脚本，已下载的包在缓存里）
uv pip install --python .venv/bin/python --index-strategy unsafe-best-match \
  --build-constraints build-constraints.txt \
  --extra-index-url https://pypi.nvidia.com \
  --extra-index-url https://download.pytorch.org/whl/cu128 \
  "isaaclab[all,isaacsim]==2.3.0" torch==2.7.0 torchvision==0.22.0 warp-lang==1.10.1 2>&1 | tee install.log

# 6. 把 NERO 任务项目（从 gcf 复制来的 isaac_so_arm101）装进环境
if [ -d isaac_so_arm101 ]; then
  uv pip install --python .venv/bin/python --build-constraints build-constraints.txt --no-deps -e ./isaac_so_arm101
else
  echo "[提示] 还没有 isaac_so_arm101 目录，先按 KANBAN.md 第 6 步复制，再重跑本脚本"
fi

# 7. 检查（第一次会问是否接受 NVIDIA Omniverse EULA，输入 yes）
.venv/bin/python -c "import torch, isaaclab, warp; print('torch', torch.__version__, torch.cuda.is_available()); print('warp', warp.__version__)"
