FROM python:3.8-slim

WORKDIR /app

# 设置 Python 环境
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 创建上传、临时和结果目录
RUN mkdir -p /app/web/uploads /app/web/temp /app/web/static/plots

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 使上传目录可写
RUN chmod 777 /app/web/uploads /app/web/temp /app/web/static/plots

# 设置环境变量
ENV FLASK_APP=web/web_interface.py
ENV FLASK_ENV=production

# 开放端口
EXPOSE 5000

# 启动命令
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"] 