# STEP/DWG 到 G-code 转换器 Web 应用

这个目录包含 STEP/DWG 到 G-code 转换器的 Web 应用程序，经过组织和精简，方便部署到生产环境。

## 目录结构

```
web/
├── templates/             # 网页模板
├── static/                # 静态资源（CSS、JS、图片等）
│   ├── css/
│   ├── js/
│   ├── img/
│   └── plots/             # 可视化图表输出
├── uploads/               # 上传文件存储
├── output/                # 生成的 G-code 输出
├── web_interface.py       # Web 应用核心代码
├── run_web.py             # 简化的启动脚本
├── step_to_fanuc_numpy.py # STEP 处理核心代码
├── fanuc_stp_to_gcode.py  # 不使用 NumPy 的转换器
├── dwg_to_step_converter.py # DWG 处理代码
├── *.gcode_generator.py   # 各 CNC 控制器的 G-code 生成器
├── cnc_controller_factory.py # 控制器工厂类
└── requirements.txt       # 依赖包列表
```

## 部署步骤

### 1. 使用 Python 虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动应用程序

```bash
python run_web.py
```

默认情况下，应用将在 http://localhost:9000 上运行。

### 3. 生产环境部署

#### 使用 Gunicorn（Linux/macOS）

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:9000 'web_interface:app'
```

#### 使用 Waitress（Windows）

```bash
pip install waitress
waitress-serve --port=9000 web_interface:app
```

#### 使用 Docker 部署（适用于所有平台）

创建 Dockerfile：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 9000

CMD ["python", "run_web.py"]
```

构建和运行 Docker 容器：

```bash
docker build -t step-dwg-gcode-web .
docker run -p 9000:9000 step-dwg-gcode-web
```

### 4. 环境变量配置

应用支持以下环境变量：

- `PORT`: 应用监听端口（默认：9000）
- `HOST`: 监听地址（默认：0.0.0.0）
- `DEBUG`: 调试模式（默认：true，生产环境应设为 false）

例如：
```bash
PORT=8888 DEBUG=false python run_web.py
```

## 注意事项

1. 确保 `uploads`、`output` 和 `static/plots` 目录具有适当的写入权限
2. 在生产环境中，建议配置 Nginx 或 Apache 作为反向代理，并使用 HTTPS
3. 对于高访问量的部署，可以考虑使用 Redis 进行会话存储
4. 生产环境中请关闭调试模式（`DEBUG=false`）
5. 默认端口为 9000，避免与 macOS AirPlay 接收器服务（5000）和其他常用服务的端口冲突 