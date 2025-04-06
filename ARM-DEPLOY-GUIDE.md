# ARM 平台部署问题排查与修复指南

本文档提供了在 ARM 架构服务器上部署 STEP/DWG 到 G-code 转换服务时遇到的常见问题及其解决方案，特别是针对 `500 Internal Server Error` 问题。

## 500 错误的常见原因

在 ARM 平台上，500 错误通常由以下几个原因引起：

1. **不兼容的依赖版本**：部分 Python 库在 ARM 架构上需要使用特定版本
2. **缺少处理器文件**：ARM 上无法使用 PythonOCC-Core，需要 fallback 处理器
3. **文件路径问题**：Docker 容器内的文件路径可能与预期不符
4. **权限问题**：目录权限设置不正确导致无法写入文件

## 解决方案

### 1. 使用修复脚本

我们提供了一个自动修复脚本，可以解决大多数 ARM 平台的兼容性问题：

```bash
# 确保脚本有执行权限
chmod +x fix-arm-deps.sh

# 运行修复脚本
./fix-arm-deps.sh
```

修复脚本会：
- 安装必要的系统依赖
- 卸载有问题的 Python 库并安装兼容版本
- 确保 fallback 处理器文件存在
- 设置正确的目录权限

### 2. 手动修复步骤

如果自动修复脚本不起作用，您可以按照以下步骤手动修复：

#### 2.1 开启调试模式

修改 docker-compose.yml 文件，添加调试环境变量：

```yaml
environment:
  - FLASK_ENV=development
  - DEBUG=true
  - FLASK_DEBUG=1
```

#### 2.2 安装兼容版本的依赖

进入 Docker 容器并更新依赖：

```bash
# 进入容器
docker exec -it step-dwg-to-gcode bash

# 在容器内执行
pip uninstall -y numpy matplotlib scipy ezdxf networkx
pip install --no-cache-dir \
    numpy==1.22.4 \
    matplotlib==3.5.2 \
    scipy==1.8.1 \
    ezdxf==0.17.2 \
    networkx==2.6.3
```

#### 2.3 确保处理器文件存在

```bash
# 在容器内执行
if [ ! -f /app/web/step_processor_fallback.py ]; then
  cp /app/step_processor_fallback.py /app/web/ 2>/dev/null || echo "fallback处理器未找到"
fi
```

#### 2.4 设置目录权限

```bash
# 在容器内执行
chmod -R 777 /app/web/uploads /app/web/temp /app/web/static/plots /app/web/output
```

### 3. 重建容器

如果修改了配置文件或 Dockerfile，需要重建容器：

```bash
docker-compose down
docker-compose up -d --build
```

### 4. 检查日志

查看容器日志可以确定具体问题：

```bash
docker logs step-dwg-to-gcode
```

## 常见错误及解决方案

### 依赖导入错误

错误信息：`ImportError: No module named 'numpy'` 或类似错误。

解决方案：确保安装了兼容 ARM 架构的 numpy 版本。

### 处理器模块错误

错误信息：`ImportError: No module named 'step_processor_fallback'`。

解决方案：确保 step_processor_fallback.py 文件存在于 /app/web/ 目录中。

### 文件写入权限错误

错误信息：`PermissionError: [Errno 13] Permission denied`。

解决方案：确保相关目录有写入权限，使用 `chmod -R 777` 命令。

## 其他优化建议

1. 调整 Docker 资源限制，为容器分配足够的内存和 CPU：
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```

2. 对于大型文件处理，增加超时设置：
   ```yaml
   environment:
     - DOCKER_CLIENT_TIMEOUT=600
     - COMPOSE_HTTP_TIMEOUT=600
   ```

## 如有问题

如果以上解决方案不能解决您的问题，请提供以下信息以便我们进一步排查：

1. Docker 容器的完整日志
2. 服务器的 ARM 具体架构（可使用 `uname -a` 命令查看）
3. 具体使用场景和重现步骤

请将问题报告提交到 GitHub Issues 或联系项目维护者。 