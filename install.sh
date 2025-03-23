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

# 创建虚拟环境
echo "创建虚拟环境..."
$PYTHON -m venv gcode_env

# 激活虚拟环境
echo "激活虚拟环境..."
source gcode_env/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 创建输出和上传目录
echo "创建必要的目录..."
mkdir -p uploads output plots static/plots static/img templates/static/img

# 确保二维码图片在正确的位置
if [ -f "qrcode-alipay-small.png" ]; then
  echo "复制支付宝二维码到静态目录..."
  cp qrcode-alipay-small.png static/img/
  cp qrcode-alipay-small.png templates/static/img/
fi

if [ -f "qrcode-wechat-small.png" ]; then
  echo "复制微信二维码到静态目录..."
  cp qrcode-wechat-small.png static/img/
  cp qrcode-wechat-small.png templates/static/img/
fi

# 设置权限
chmod -R 755 static uploads output plots

# 显示完成信息
echo ""
echo "===== 安装完成! ====="
echo "要启动STEP/DWG到G代码转换器，请运行:"
echo "source gcode_env/bin/activate  # 激活虚拟环境 (如果尚未激活)"
echo "python start_converter.py      # 启动Web应用程序"
echo ""
echo "然后在浏览器中访问: http://localhost:8888"
echo "=====================================" 