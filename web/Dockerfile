FROM python:3.9-slim

WORKDIR /app

# 复制依赖列表并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads output static/plots
RUN chmod 777 uploads output static/plots

# 设置环境变量
ENV PORT=9000
ENV HOST=0.0.0.0
ENV DEBUG=false

# 暴露端口
EXPOSE 9000

# 运行应用
CMD ["python", "run_web.py"] 