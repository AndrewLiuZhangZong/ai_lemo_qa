#!/bin/bash

# AI智能客服问答系统 - 重启脚本

echo "======================================"
echo "  AI智能客服问答系统 - 重启中..."
echo "======================================"

# 获取项目根目录
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

# 停止服务
echo "🛑 停止现有服务..."
./stop.sh

echo ""
echo "⏳ 等待2秒..."
sleep 2

# 启动服务
echo ""
./start.sh

