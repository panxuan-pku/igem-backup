#!/bin/bash
# VirtualCellTool v3.1 启动器
# 单端口 8377 承载全部数据集（数据集在网页里下拉切换，无需多实例）
cd "$(dirname "$0")" || exit 1
VCT="$(pwd)"
CONDA_BIN="${CONDA_EXE:-conda}"

if ! command -v "$CONDA_BIN" >/dev/null 2>&1; then
  echo "❌ 找不到 Conda。请在能够运行 conda 的终端启动本脚本。"
  echo "   首次使用请在项目根目录运行 conda env create --file environment-vct.yml。"
  read -n 1 -s -r -p "按任意键关闭…"
  exit 1
fi

"$CONDA_BIN" run --no-capture-output -n virtual-cell python "$VCT/src/web_launcher.py"
result=$?
if [ "$result" -ne 0 ]; then
  read -n 1 -s -r -p "按任意键关闭…"
fi
exit "$result"
