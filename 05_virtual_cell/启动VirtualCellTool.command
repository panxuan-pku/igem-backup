#!/bin/bash
# VirtualCellTool v3.1 启动器
# 单端口 8377 承载全部数据集（数据集在网页里下拉切换，无需多实例）
cd "$(dirname "$0")" || exit 1
VCT="$(pwd)"
PY="$VCT/../.venv/vct/bin/python"

if [ ! -x "$PY" ]; then
  echo "❌ 找不到 Python 环境: $PY"
  echo "   请先在项目根目录运行 bash scripts/setup_envs.sh（Python 3.11）。"
  read -n 1 -s -r -p "按任意键关闭…"
  exit 1
fi

"$PY" "$VCT/src/web_launcher.py"
result=$?
if [ "$result" -ne 0 ]; then
  read -n 1 -s -r -p "按任意键关闭…"
fi
exit "$result"
