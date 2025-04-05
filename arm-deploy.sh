#!/bin/bash
# ARM服务器部署脚本
set -e

# 显示帮助信息
show_help() {
  echo "STEP/DWG 到 G-code 转换服务 ARM 部署脚本"
  echo ""
  echo "用法: ./arm-deploy.sh [选项]"
  echo ""
  echo "选项:"
  echo "  -h, --help        显示此帮助信息"
  echo "  -r, --restart     重启服务"
  echo "  -u, --update      更新服务（拉取最新代码并重建）"
  echo "  -c, --clean       清理无用镜像和容器"
  echo ""
}

# 检查Docker和Docker Compose是否已安装
check_requirements() {
  echo "正在检查环境要求..."
  
  if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker"
    exit 1
  fi
  
  if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
  fi
  
  # 检查当前平台架构是否为 ARM
  ARCH=$(uname -m)
  if [[ "$ARCH" != "arm"* ]] && [[ "$ARCH" != "aarch"* ]]; then
    echo "警告: 当前系统架构不是 ARM ($ARCH)，这个脚本专为 ARM 服务器设计"
    read -p "是否继续? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      exit 1
    fi
  fi
  
  echo "环境检查通过"
}

# 创建必要的目录
create_directories() {
  echo "创建必要的目录结构..."
  mkdir -p data/uploads
  mkdir -p data/output
  mkdir -p data/plots
  touch data/uploads/.gitkeep
  touch data/output/.gitkeep
  touch data/plots/.gitkeep
  chmod -R 777 data
  echo "目录创建完成"
}

# 启动或重启服务
start_service() {
  echo "启动服务..."
  docker-compose up -d
  echo "服务已启动，可通过以下地址访问:"
  echo "http://$(hostname -I | awk '{print $1}'):5000"
}

# 重启服务
restart_service() {
  echo "重启服务..."
  docker-compose restart
  echo "服务已重启"
}

# 更新服务
update_service() {
  echo "更新服务..."
  docker-compose down
  docker-compose pull
  docker-compose up -d --build
  echo "服务已更新"
}

# 清理无用的镜像和容器
clean_docker() {
  echo "清理无用的 Docker 资源..."
  # 删除停止的容器
  docker container prune -f
  # 删除未使用的镜像
  docker image prune -a -f
  # 删除未使用的数据卷
  docker volume prune -f
  # 删除构建缓存
  docker builder prune -f
  echo "清理完成"
}

# 主函数
main() {
  # 如果没有参数，显示帮助
  if [ $# -eq 0 ]; then
    check_requirements
    create_directories
    start_service
    exit 0
  fi
  
  # 处理参数
  while [ "$1" != "" ]; do
    case $1 in
      -h | --help)
        show_help
        exit 0
        ;;
      -r | --restart)
        restart_service
        exit 0
        ;;
      -u | --update)
        update_service
        exit 0
        ;;
      -c | --clean)
        clean_docker
        exit 0
        ;;
      *)
        echo "未知选项: $1"
        show_help
        exit 1
        ;;
    esac
    shift
  done
}

# 执行主函数
main "$@" 