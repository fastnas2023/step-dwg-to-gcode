# ARM 服务器 Docker 部署说明

本文档提供在 ARM 架构服务器上使用 Docker 部署 STEP/DWG 到 G-code 转换服务的详细说明。

## 系统要求

- ARM 架构服务器（如树莓派、AWS Graviton、华为鲲鹏等）
- Docker Engine 19.03 或更高版本
- Docker Compose v2.0 或更高版本
- 至少 2GB RAM
- 至少 10GB 磁盘空间

## 快速开始

### 1. 克隆代码仓库

```bash
git clone https://your-repo-url/step-dwg-to-gcode.git
cd step-dwg-to-gcode
```

### 2. 使用部署脚本

为部署脚本添加执行权限：

```bash
chmod +x arm-deploy.sh
```

执行部署脚本：

```bash
./arm-deploy.sh
```

这将自动：
- 检查环境要求
- 创建必要的目录结构
- 构建并启动 Docker 容器

### 3. 访问服务

部署成功后，可以通过以下地址访问服务：

```
http://your-server-ip:5000
```

## 部署脚本选项

部署脚本支持以下选项：

- `-h, --help`：显示帮助信息
- `-r, --restart`：重启服务
- `-u, --update`：更新服务（拉取最新代码并重建）
- `-c, --clean`：清理无用的 Docker 镜像和容器

例如，更新服务：

```bash
./arm-deploy.sh -u
```

## 目录结构

部署后，将创建以下目录结构：

```
step-dwg-to-gcode/
├── data/
│   ├── uploads/   # 上传文件存储目录
│   ├── output/    # 转换后的输出文件目录
│   └── plots/     # 可视化图表存储目录
├── Dockerfile
├── docker-compose.yml
└── ...
```

## 手动部署

如果不想使用部署脚本，可以按照以下步骤手动部署：

1. 创建目录结构：

```bash
mkdir -p data/uploads data/output data/plots
chmod -R 777 data
```

2. 构建并启动服务：

```bash
docker-compose up -d
```

## 故障排除

### 服务无法启动

检查 Docker 日志：

```bash
docker-compose logs
```

### ARM 兼容性问题

确认使用的是兼容 ARM 架构的 Python 库版本：

```bash
docker-compose exec step-dwg-to-gcode python -c "import numpy; print(numpy.__version__)"
```

## 性能优化

### 调整 Docker 资源限制

在 `docker-compose.yml` 中，可以根据服务器性能调整资源限制：

```yaml
services:
  step-dwg-to-gcode:
    # ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### 处理大文件

处理大型 STEP/DWG 文件时，可能需要调整超时设置：

```bash
export DOCKER_CLIENT_TIMEOUT=300
export COMPOSE_HTTP_TIMEOUT=300
```

## 安全注意事项

- 默认配置未启用 HTTPS，生产环境应配置 SSL 证书或使用反向代理
- 服务默认监听所有接口，生产环境应限制访问范围
- 文件上传大小限制应根据实际需求调整

## 更新和维护

定期更新镜像和依赖：

```bash
./arm-deploy.sh -u
```

清理未使用的资源：

```bash
./arm-deploy.sh -c
``` 