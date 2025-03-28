@echo off
echo ===== STEP/DWG到G代码转换器安装脚本 =====

REM 检查Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python，请先安装Python 3.7或更高版本
    pause
    exit /b 1
)

echo 使用Python:
python --version

REM 创建虚拟环境
if not exist gcode_env (
    echo 创建虚拟环境...
    python -m venv gcode_env
) else (
    echo 虚拟环境已存在，跳过创建
)

REM 激活虚拟环境
echo 激活虚拟环境...
call gcode_env\Scripts\activate.bat

REM 安装依赖
echo 安装依赖项...
pip install -r requirements.txt

REM 创建必要的目录
echo 创建必要的目录...
mkdir uploads output plots static\plots static\img templates\static\img 2>nul

REM 确保二维码图片在正确的位置
if exist qrcode-alipay-small.png (
    echo 复制支付宝二维码到静态目录...
    copy qrcode-alipay-small.png static\img\
    copy qrcode-alipay-small.png templates\static\img\
)

if exist qrcode-wechat-small.png (
    echo 复制微信二维码到静态目录...
    copy qrcode-wechat-small.png static\img\
    copy qrcode-wechat-small.png templates\static\img\
)

REM 显示完成信息
echo.
echo ===== 安装完成! =====
echo 要启动STEP/DWG到G代码转换器，请运行:
echo call gcode_env\Scripts\activate.bat  REM 激活虚拟环境 (如果尚未激活)
echo python start_converter.py            REM 启动Web应用程序
echo.
echo 然后在浏览器中访问: http://localhost:8888
echo =====================================

pause 