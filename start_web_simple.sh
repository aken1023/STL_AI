#!/bin/bash

echo "🚀 啟動 Web 伺服器（簡化版）"
echo "================================"

# 檢查端口是否被佔用
if lsof -Pi :8082 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 8082 已被佔用，正在清理..."
    lsof -ti:8082 | xargs kill -9 2>/dev/null
    sleep 2
fi

# 啟動伺服器
echo "🌐 啟動 Flask 伺服器..."
echo "📍 訪問: http://localhost:8082"
echo ""

cd "$(dirname "$0")"
export FLASK_ENV=development
export FLASK_DEBUG=0

python3 -u web_interface.py 2>&1
