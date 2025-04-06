FROM python:3.8-slim

WORKDIR /app

# 设置 Python 环境
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgl1-mesa-glx \
    curl \
    wget \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 检测ARM架构并设置环境变量
RUN if [ "$(uname -m)" = "aarch64" ] || [ "$(uname -m)" = "arm64" ]; then \
      echo "Detected ARM architecture, using compatible dependencies" \
      && export IS_ARM=true; \
    else \
      echo "Detected x86/x64 architecture, using standard dependencies" \
      && export IS_ARM=false; \
    fi

# 复制项目文件
COPY . /app/

# 创建上传、临时和结果目录
RUN mkdir -p /app/web/uploads /app/web/temp /app/web/static/plots /app/web/output

# 针对ARM架构修改requirements.txt
RUN if [ "$(uname -m)" = "aarch64" ] || [ "$(uname -m)" = "arm64" ]; then \
      echo "Creating ARM-compatible requirements..." \
      && sed -i 's/numpy==1.23.5/numpy==1.22.4 # ARM架构兼容版本/g' requirements.txt \
      && sed -i 's/matplotlib==3.5.3/matplotlib==3.5.2 # ARM架构兼容版本/g' requirements.txt \
      && sed -i 's/scipy==1.9.3/scipy==1.8.1 # ARM架构兼容版本/g' requirements.txt \
      && sed -i 's/ezdxf==1.0.1/ezdxf==0.17.2 # ARM架构兼容版本/g' requirements.txt \
      && sed -i 's/networkx==2.8.8/networkx==2.6.3 # ARM架构兼容版本/g' requirements.txt \
      && cat requirements.txt; \
    fi

# 安装pip和setuptools的固定版本
RUN pip install --no-cache-dir --upgrade pip==23.3.1 setuptools==68.2.2 wheel==0.41.2

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 确认关键依赖安装成功
RUN python -c "import numpy; print('NumPy版本:', numpy.__version__)" \
    && python -c "import matplotlib; print('Matplotlib版本:', matplotlib.__version__)" \
    && python -c "import scipy; print('SciPy版本:', scipy.__version__)"

# 确保fallback处理器可用
RUN if [ ! -f /app/web/step_processor_fallback.py ]; then \
      cp /app/step_processor_fallback.py /app/web/ 2>/dev/null || echo "warning: fallback processor not found"; \
    fi

# 使目录可写
RUN chmod -R 777 /app/web/uploads /app/web/temp /app/web/static/plots /app/web/output

# 设置环境变量
ENV FLASK_APP=web/web_interface.py
ENV FLASK_DEBUG=1
ENV DEBUG=true

# 开放端口
EXPOSE 5000

# 启动命令
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"] 