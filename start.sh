#!/bin/bash
echo "=============================="
echo "🚀 AI Agent 启动脚本（Day9）"
echo "=============================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 未安装Python，请先安装Python 3.8+"
    exit 1
fi

# 安装依赖
echo "📦 安装/更新依赖..."
pip3 install -r requirements.txt --upgrade

# 启动Streamlit（局域网可访问，端口8501）
echo "🎯 启动AI Agent..."
streamlit run agent_app_v2.py --server.port 8501 --server.address 0.0.0.0