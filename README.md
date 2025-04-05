# STEP/DWG 到 G-code 转换服务

这是一个用于将 STEP 和 DWG 文件转换为 CNC 机床可用的 G-code 的 Web 服务。该服务支持在 ARM 和 x86 架构服务器上运行，并提供了易于使用的 Docker 部署方式。

## 特性

- **文件格式支持**
  - STEP (.stp, .step) 文件转换为 G-code
  - DWG 文件转换为 G-code（通过 STEP 中间格式）

- **3D 可视化**
  - STEP 文件的 3D 预览
  - 生成的工具路径可视化

- **多平台支持**
  - ARM 架构服务器部署
  - x86 架构服务器部署
  - Docker 容器化部署

- **友好的用户界面**
  - 简单直观的 Web 界面
  - 转换进度实时显示
  - 参数自定义配置

## 部署方法

### ARM 服务器部署

1. **准备工作**
   ```bash
   # 克隆代码仓库
   git clone https://github.com/fastnas2023/step-dwg-to-gcode.git
   cd step-dwg-to-gcode
   
   # 给部署脚本添加执行权限
   chmod +x arm-deploy.sh
   ```

2. **执行部署脚本**
   ```bash
   ./arm-deploy.sh
   ```

3. **访问应用**
   ```
   http://服务器IP:5000
   ```

详细说明请参考 [ARM 部署文档](README-arm-deploy.md)。

### x86 服务器部署

1. **标准部署**
   ```bash
   # 克隆仓库
   git clone https://github.com/fastnas2023/step-dwg-to-gcode.git
   cd step-dwg-to-gcode
   
   # 授予脚本执行权限
   chmod +x x86-deploy.sh
   
   # 执行部署
   ./x86-deploy.sh
   ```

2. **高级部署选项**
   ```bash
   # 生产环境部署 (Nginx + HTTPS)
   ./x86-deploy.sh --production
   
   # 启用监控 (Prometheus + Grafana)
   ./x86-deploy.sh --monitoring
   
   # 多实例部署
   ./x86-deploy.sh --scale 3
   ```

详细说明请参考 [x86 部署文档](README-x86-deploy.md)。

## 使用指南

1. 通过 Web 浏览器访问服务
2. 上传 STEP 或 DWG 文件
3. 配置转换参数
4. 启动转换
5. 下载生成的 G-code 文件

## 系统要求

### ARM 服务器
- Docker Engine 19.03+
- Docker Compose v2.0+
- 至少 2GB RAM
- 至少 10GB 磁盘空间

### x86 服务器
- Docker Engine 20.10+
- Docker Compose v2.0+
- 至少 4GB RAM（推荐 8GB+）
- 至少 20GB 磁盘空间

## 技术栈

- **后端**: Python, Flask
- **数据处理**: NumPy, SciPy
- **可视化**: Matplotlib
- **容器化**: Docker
- **Web 服务器**: Nginx (x86 生产环境)
- **监控**: Prometheus, Grafana (x86 高级部署)

## 贡献指南

欢迎贡献！请参考以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 联系方式

如有问题，请通过 GitHub Issues 联系我们。