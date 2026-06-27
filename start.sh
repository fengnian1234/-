#!/usr/bin/env bash
# 跨设备通用启动脚本 — 自动检测嵌入式 Python 路径
set -e

cd "$(dirname "$0")"

# 自动检测 Python：优先使用 ~/python-embed，fallback 到系统 python
if [ -f "$HOME/python-embed/python.exe" ]; then
    PYTHON="$HOME/python-embed/python.exe"
elif [ -f "$HOME/python-embed/python" ]; then
    PYTHON="$HOME/python-embed/python"
elif command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "错误: 找不到 Python。请将嵌入式 Python 放到 ~/python-embed/ 或安装系统 Python。"
    exit 1
fi

echo "使用 Python: $PYTHON"
export PYTHONUTF8=1

# 安装依赖（如需要）
if [ "$1" = "install" ]; then
    "$PYTHON" -m pip install -r requirements.txt
    echo "依赖安装完成。"
    exit 0
fi

# 启动服务器
exec "$PYTHON" run.py
