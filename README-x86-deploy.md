# x86 服务器 Docker 部署说明

本文档提供在 x86 架构服务器上使用 Docker 部署 STEP/DWG 到 G-code 转换服务的详细说明。

## 系统要求

- x86_64/amd64 架构服务器
- Docker Engine 20.10 或更高版本
- Docker Compose v2.0 或更高版本
- 至少 4GB RAM（推荐8GB以上）
- 至少 20GB 可用磁盘空间

## 快速开始

### 1. 克隆代码仓库

```bash
git clone https://your-repo-url/step-dwg-to-gcode.git
cd step-dwg-to-gcode
```

### 2. 使用部署脚本

为部署脚本添加执行权限：

```bash
chmod +x x86-deploy.sh
```

执行部署脚本：

```bash
./x86-deploy.sh
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

## 高级部署选项

### 生产环境部署

对于生产环境，建议启用 Nginx 反向代理和 HTTPS：

```bash
./x86-deploy.sh --production
```

这将：
- 生成自签名 SSL 证书（可以在生产环境中替换为真实证书）
- 配置 Nginx 作为反向代理
- 启用 HTTP 到 HTTPS 的自动重定向

### 启用监控

对于需要监控的环境：

```bash
./x86-deploy.sh --monitoring
```

这将额外部署：
- Prometheus 监控系统（访问地址：http://your-server-ip:9090）
- Grafana 仪表盘（访问地址：http://your-server-ip:3000，默认用户名/密码：admin/admin）

### 服务扩展

对于高负载环境，可以启动多个应用实例：

```bash
./x86-deploy.sh --scale 3
```

这将启动 3 个应用实例，并通过 Nginx 进行负载均衡。

## 部署脚本选项

部署脚本支持以下选项：

- `-h, --help`：显示帮助信息
- `-r, --restart`：重启服务
- `-u, --update`：更新服务（拉取最新代码并重建）
- `-c, --clean`：清理无用的 Docker 镜像和容器
- `-s, --scale N`：设置应用实例数为 N
- `-m, --monitoring`：启用监控服务
- `-p, --production`：配置生产环境

可以组合使用这些选项，例如：

```bash
./x86-deploy.sh --production --monitoring
```

## 目录结构

部署后，将创建以下目录结构：

```
step-dwg-to-gcode/
├── data/
│   ├── uploads/   # 上传文件存储目录
│   ├── output/    # 转换后的输出文件目录
│   └── plots/     # 可视化图表存储目录
├── nginx/
│   ├── conf/      # Nginx 配置文件
│   ├── logs/      # Nginx 日志
│   └── ssl/       # SSL 证书
├── prometheus/    # Prometheus 配置
├── Dockerfile.x86
├── docker-compose.x86.yml
└── ...
```

## 性能优化

### 硬件推荐

- **CPU**：4+ 核心（每个实例至少 2 核心）
- **内存**：8GB+（每个实例至少 2GB）
- **磁盘**：SSD 存储推荐用于数据目录
- **网络**：至少 100Mbps 带宽

### Docker 资源限制调整

在 `docker-compose.x86.yml` 中，可以根据服务器性能调整资源限制：

```yaml
services:
  step-dwg-to-gcode:
    # ...
    deploy:
      resources:
        limits:
          cpus: '4'  # 调整为匹配CPU核心数
          memory: 4G # 调整为匹配可用内存
```

### 处理大文件

对于大型 STEP/DWG 文件，建议调整以下设置：

1. **Nginx 客户端大小限制**：修改 `nginx/conf/default.conf` 中的 `client_max_body_size`
2. **应用超时设置**：修改 `docker-compose.x86.yml` 中的应用环境变量
3. **Docker 超时设置**：

```bash
export DOCKER_CLIENT_TIMEOUT=300
export COMPOSE_HTTP_TIMEOUT=300
```

## 备份和恢复

### 数据备份

备份数据目录：

```bash
tar -czvf step-dwg-backup-$(date +%Y%m%d).tar.gz data
```

### 数据恢复

恢复数据目录：

```bash
tar -xzvf step-dwg-backup-20231001.tar.gz
```

## 故障排除

### 服务无法启动

检查 Docker 日志：

```bash
docker-compose -f docker-compose.x86.yml logs
```

### 文件上传问题

检查文件权限和大小限制：

```bash
ls -la data/uploads
grep client_max_body_size nginx/conf/default.conf
```

### 性能问题

检查资源使用情况：

```bash
docker stats
```

## 安全注意事项

- 默认的自签名证书仅适用于测试环境，生产环境应使用有效的 SSL 证书
- Docker 容器之间使用内部网络通信，减少暴露的端口数量
- 所有的环境变量都在 `docker-compose.x86.yml` 中定义，避免敏感信息泄露

## 更新和维护

### 更新应用

```bash
./x86-deploy.sh --update
```

### 定期清理

```bash
./x86-deploy.sh --clean
```

### 日志管理

Docker 日志默认配置了轮转策略（最大 50MB，保留 10 个文件）。可以查看日志：

```bash
docker-compose -f docker-compose.x86.yml logs -f
``` 