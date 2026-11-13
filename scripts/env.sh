# 每次开新终端先执行：source scripts/env.sh
# 作用：退出 conda、把 uv 加进 PATH、把 uv 的缓存和 Python 放到 /data 下（避免撑满家目录）
conda deactivate 2>/dev/null; conda deactivate 2>/dev/null
export PATH="$HOME/.local/bin:$PATH"
export UV_CACHE_DIR=/data/${USER}/.uv_cache
export UV_PYTHON_INSTALL_DIR=/data/${USER}/.uv_python
export UV_HTTP_TIMEOUT=300
export NERO_SIM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
