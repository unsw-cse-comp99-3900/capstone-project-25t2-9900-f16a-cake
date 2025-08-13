#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}压力测试启动脚本 - MAC/Linux版本${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: 未找到Python3，请先安装Python 3.7+${NC}"
    echo "macOS安装命令: brew install python3"
    echo "Ubuntu安装命令: sudo apt-get install python3 python3-pip"
    echo "CentOS安装命令: sudo yum install python3 python3-pip"
    exit 1
fi

# 检查Python版本
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✅ Python版本: ${PYTHON_VERSION}${NC}"

# 检查虚拟环境是否存在
if [ -f "venv/bin/activate" ]; then
    echo -e "${BLUE}🔧 激活虚拟环境...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  警告: 未找到虚拟环境，将使用系统Python${NC}"
    echo "建议创建虚拟环境: python3 -m venv venv"
    echo
fi

# 检查配置文件
if [ ! -f "test_config_clean.json" ]; then
    echo -e "${RED}❌ 错误: 未找到配置文件 test_config_clean.json${NC}"
    exit 1
fi

# 检查依赖
echo -e "${BLUE}🔍 检查依赖包...${NC}"
if ! python3 -c "import aiohttp, psutil" &> /dev/null; then
    echo -e "${RED}❌ 错误: 缺少必要的依赖包${NC}"
    echo "正在安装依赖..."
    pip3 install aiohttp psutil
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 依赖安装失败${NC}"
        exit 1
    fi
fi

echo
echo -e "${GREEN}🚀 开始压力测试...${NC}"
echo -e "${BLUE}⏱️  测试时长: 5分钟${NC}"
echo -e "${BLUE}👥 并发用户: 50${NC}"
echo -e "${BLUE}🔍 测试接口: 21个可用接口${NC}"
echo

# 运行压力测试
python3 clean_stress_test.py

echo
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}测试完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}📁 结果文件: clean_stress_test_results.json${NC}"
echo -e "${BLUE}📊 详细报告已生成${NC}"
echo

# 显示结果文件信息
if [ -f "clean_stress_test_results.json" ]; then
    echo -e "${GREEN}✅ 结果文件已生成${NC}"
    ls -lh clean_stress_test_results.json
else
    echo -e "${YELLOW}⚠️  结果文件未生成${NC}"
fi
