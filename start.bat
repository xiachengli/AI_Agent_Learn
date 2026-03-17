@echo off
echo ==============================
echo 🚀 AI Agent 启动脚本（Day9）
echo ==============================

set PYTHON_PATH=D:\AI_Agent_Learn\agent-env\Scripts\python.exe

:: 检查Python
%PYTHON_PATH% --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python
    pause
    exit /b 1
)

:: 仅检查依赖是否存在，不安装（适合确认已装完的情况）
echo 📦 检查依赖是否齐全...
%PYTHON_PATH% -c "import streamlit, requests, langchain_community, dotenv" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  缺失依赖，开始安装...
    %PYTHON_PATH% -m pip install -r requirements.txt
) else (
    echo ✅ 所有依赖已安装，跳过安装步骤
)

:: 启动程序
echo 🎯 启动AI Agent...
%PYTHON_PATH% -m streamlit run agent_app_v2.py --server.port 8501 --server.address 0.0.0.0

pause