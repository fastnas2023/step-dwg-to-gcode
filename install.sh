#!/bin/bash

echo "===== STEP/DWG到G代码转换器安装脚本 ====="

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo "错误: 未找到Python，请先安装Python 3.7或更高版本"
    exit 1
fi

echo "使用Python: $($PYTHON --version)"

# 创建并激活虚拟环境
if [ ! -d "gcode_env" ]; then
    echo "创建虚拟环境..."
    $PYTHON -m venv gcode_env
else
    echo "虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source gcode_env/Scripts/activate
else
    # Linux/Mac
    source gcode_env/bin/activate
fi

# 安装依赖
echo "安装依赖项..."
pip install -r requirements.txt

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p uploads output plots templates/static/plots templates/static/img

# 显示完成信息
echo ""
echo "===== 安装完成! ====="
echo "要启动STEP/DWG到G代码转换器，请运行:"
echo "source gcode_env/bin/activate  # 激活虚拟环境 (如果尚未激活)"
echo "python start_converter.py      # 启动Web应用程序"
echo ""
echo "然后在浏览器中访问: http://localhost:8888"
echo "=====================================" 