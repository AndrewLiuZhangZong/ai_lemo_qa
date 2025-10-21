#!/bin/bash

# AI智能客服问答系统 - 启动脚本

echo "======================================"
echo "  AI智能客服问答系统 - 启动中..."
echo "======================================"

# 获取项目根目录
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

# 停止现有服务
echo "🛑 停止现有服务..."
lsof -ti:8080 | xargs kill -9 2>/dev/null
sleep 2

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ 错误：未找到虚拟环境，请先运行 python -m venv venv"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
python -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 错误：缺少依赖，请运行 pip install -r requirements.txt"
    exit 1
fi

# 启动后端服务
echo "🚀 启动后端服务（端口 8080）..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload > /dev/null 2>&1 &
BACKEND_PID=$!

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 8

# 检查服务状态
if lsof -ti:8080 > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功！"
    echo ""
    echo "======================================"
    echo "  服务信息"
    echo "======================================"
    echo "后端API:  http://localhost:8080"
    echo "API文档:  http://localhost:8080/docs"
    echo "健康检查: http://localhost:8080/health"
    echo "前端界面: http://localhost:3000 (需单独启动)"
    echo ""
    echo "日志文件: logs/app_$(date +%Y-%m-%d).log"
    echo "进程PID:  $(lsof -ti:8080)"
    echo ""
    echo "======================================"
    echo "💡 提示："
    echo "  - 查看日志: tail -f logs/app_$(date +%Y-%m-%d).log"
    echo "  - 停止服务: ./stop.sh"
    echo "  - 重启服务: ./restart.sh"
    echo "======================================"
else
    echo "❌ 后端服务启动失败！"
    echo "请查看日志: tail -50 logs/app_$(date +%Y-%m-%d).log"
    exit 1
fi

