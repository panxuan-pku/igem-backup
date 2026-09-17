#!/bin/bash
# VirtualCellTool v3.1 启动器
# 单端口 8377 承载全部数据集（数据集在网页里下拉切换，无需多实例）
cd "$(dirname "$0")" || exit 1
VCT="$(pwd)"
PY="$VCT/../../.venv/vct/bin/python"
PORT="${VCT_PORT:-8377}"

if [ ! -x "$PY" ]; then
  echo "❌ 找不到 Python 环境: $PY"
  echo "   请先在项目根目录运行 bash scripts/setup_envs.sh（Python 3.11）。"
  read -n 1 -s -r -p "按任意键关闭…"
  exit 1
fi

if curl -s --max-time 2 "http://127.0.0.1:$PORT/api/cipher_status" > /dev/null; then
  echo "✅ 服务已在运行（端口 $PORT）"
else
  echo "🚀 启动 VirtualCellTool（默认 PBMC 数据集，约 15 秒）…"
  # 日志留在项目内，便于排查
  nohup "$PY" web/app.py > "$VCT/vct_server.log" 2>&1 &
  for i in $(seq 1 60); do
    curl -s --max-time 2 "http://127.0.0.1:$PORT/api/cipher_status" > /dev/null && break
    sleep 2
  done
  if ! curl -s --max-time 2 "http://127.0.0.1:$PORT/api/cipher_status" > /dev/null; then
    echo "❌ 启动超时，最后 20 行日志："
    tail -20 "$VCT/vct_server.log"
    read -n 1 -s -r -p "按任意键关闭…"
    exit 1
  fi
fi

echo "🌐 打开 http://127.0.0.1:$PORT"
open "http://127.0.0.1:$PORT"
echo ""
echo "提示：数据集在网页顶部下拉切换（PBMC / MS / Williams）。"
echo "     停止服务：pkill -f 'web/app.py'"
