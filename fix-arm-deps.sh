#!/bin/bash
# ARM架构依赖修复脚本
set -e

echo "====== 开始修复ARM环境依赖问题 ======"

# 进入Docker容器
docker exec -it step-dwg-to-gcode bash -c "
echo '安装系统依赖...'
apt-get update
apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgl1-mesa-glx \
    curl \
    python3-dev

echo '卸载可能有问题的包...'
pip uninstall -y numpy matplotlib scipy ezdxf networkx

echo '安装ARM兼容的Python依赖...'
pip install --no-cache-dir \
    numpy==1.22.4 \
    matplotlib==3.5.2 \
    scipy==1.8.1 \
    ezdxf==0.17.2 \
    networkx==2.6.3

echo '检查是否存在step_processor_fallback.py...'
if [ ! -f /app/web/step_processor_fallback.py ]; then
    echo 'fallback处理器文件不存在，复制实现...'
    cp /app/step_processor_fallback.py /app/web/ 2>/dev/null || echo '无法找到fallback处理器源文件'
fi

echo '增加权限...'
chmod 777 /app/web/uploads /app/web/output /app/web/static/plots

echo '验证关键模块...'
python3 -c 'import numpy; print(\"NumPy版本:\", numpy.__version__)'
python3 -c 'import matplotlib; print(\"Matplotlib版本:\", matplotlib.__version__)'
python3 -c 'import scipy; print(\"SciPy版本:\", scipy.__version__)'
"

echo "====== ARM环境依赖修复完成 ======"
echo "如果上面显示了正确的版本信息，请重启服务尝试"
echo "重启命令: ./arm-deploy.sh -r" 