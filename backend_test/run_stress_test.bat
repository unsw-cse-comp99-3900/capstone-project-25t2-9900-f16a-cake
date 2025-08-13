@echo off
chcp 65001 >nul
echo ========================================
echo 压力测试启动脚本 - Windows版本
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 检查虚拟环境是否存在
if exist "venv\Scripts\activate.bat" (
    echo 🔧 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  警告: 未找到虚拟环境，将使用系统Python
    echo 建议创建虚拟环境: python -m venv venv
    echo.
)

:: 检查配置文件
if not exist "test_config_clean.json" (
    echo ❌ 错误: 未找到配置文件 test_config_clean.json
    pause
    exit /b 1
)

:: 检查依赖
echo 🔍 检查依赖包...
python -c "import aiohttp, psutil" >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 缺少必要的依赖包
    echo 正在安装依赖...
    pip install aiohttp psutil
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo 🚀 开始压力测试...
echo ⏱️  测试时长: 5分钟
echo 👥 并发用户: 50
echo 🔍 测试接口: 21个可用接口
echo.

:: 运行压力测试
python clean_stress_test.py

echo.
echo ========================================
echo 测试完成！
echo ========================================
echo 📁 结果文件: clean_stress_test_results.json
echo 📊 详细报告已生成
echo.

pause
