#!/bin/bash
# x86服务器部署脚本
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
  echo -e "${BLUE}STEP/DWG 到 G-code 转换服务 x86 部署脚本${NC}"
  echo ""
  echo "用法: ./x86-deploy.sh [选项]"
  echo ""
  echo "选项:"
  echo "  -h, --help        显示此帮助信息"
  echo "  -r, --restart     重启服务"
  echo "  -u, --update      更新服务（拉取最新代码并重建）"
  echo "  -c, --clean       清理无用镜像和容器"
  echo "  -s, --scale N     设置应用实例数为N"
  echo "  -m, --monitoring  启用监控服务（Prometheus和Grafana）"
  echo "  -p, --production  配置生产环境（包括Nginx和HTTPS）"
  echo ""
}

# 检查Docker和Docker Compose是否已安装
check_requirements() {
  echo -e "${BLUE}正在检查环境要求...${NC}"
  
  if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装，请先安装 Docker${NC}"
    exit 1
  fi
  
  if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装，请先安装 Docker Compose${NC}"
    exit 1
  fi
  
  # 检查当前平台架构是否为 x86
  ARCH=$(uname -m)
  if [[ "$ARCH" != "x86_64" ]] && [[ "$ARCH" != "amd64" ]]; then
    echo -e "${YELLOW}警告: 当前系统架构不是 x86_64 ($ARCH)，这个脚本专为 x86 服务器设计${NC}"
    read -p "是否继续? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      exit 1
    fi
  fi
  
  echo -e "${GREEN}环境检查通过${NC}"
}

# 创建必要的目录
create_directories() {
  echo -e "${BLUE}创建必要的目录结构...${NC}"
  mkdir -p data/uploads
  mkdir -p data/output
  mkdir -p data/plots
  mkdir -p nginx/conf
  mkdir -p nginx/ssl
  mkdir -p nginx/logs
  mkdir -p prometheus
  
  # 创建 Nginx 默认配置
  if [ ! -f nginx/conf/default.conf ]; then
    cat > nginx/conf/default.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://step-dwg-to-gcode:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        
        # 文件上传设置
        client_max_body_size 100M;
    }
}
EOF
  fi
  
  # 创建 Prometheus 配置
  if [ ! -f prometheus/prometheus.yml ]; then
    cat > prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'step-dwg-app'
    static_configs:
      - targets: ['step-dwg-to-gcode:5000']
EOF
  fi
  
  # 权限配置
  touch data/uploads/.gitkeep
  touch data/output/.gitkeep
  touch data/plots/.gitkeep
  chmod -R 777 data
  
  echo -e "${GREEN}目录创建完成${NC}"
}

# 启动服务
start_service() {
  local monitoring=$1
  local production=$2
  
  echo -e "${BLUE}启动服务...${NC}"
  
  if [ "$monitoring" = true ]; then
    # 启动带监控的服务
    docker-compose -f docker-compose.x86.yml --profile monitoring up -d
    echo -e "${GREEN}服务已启动（包含监控服务）${NC}"
    echo -e "应用访问地址: ${YELLOW}http://$(hostname -I | awk '{print $1}'):5000${NC}"
    echo -e "Prometheus: ${YELLOW}http://$(hostname -I | awk '{print $1}'):9090${NC}"
    echo -e "Grafana: ${YELLOW}http://$(hostname -I | awk '{print $1}'):3000${NC} (默认用户名/密码: admin/admin)"
  else
    # 启动标准服务
    docker-compose -f docker-compose.x86.yml up -d
    echo -e "${GREEN}服务已启动${NC}"
    
    if [ "$production" = true ]; then
      echo -e "应用访问地址: ${YELLOW}http://$(hostname -I | awk '{print $1}')${NC} (通过Nginx)"
    else
      echo -e "应用访问地址: ${YELLOW}http://$(hostname -I | awk '{print $1}'):5000${NC}"
    fi
  fi
}

# 重启服务
restart_service() {
  echo -e "${BLUE}重启服务...${NC}"
  docker-compose -f docker-compose.x86.yml restart
  echo -e "${GREEN}服务已重启${NC}"
}

# 更新服务
update_service() {
  echo -e "${BLUE}更新服务...${NC}"
  docker-compose -f docker-compose.x86.yml down
  git pull
  docker-compose -f docker-compose.x86.yml up -d --build
  echo -e "${GREEN}服务已更新${NC}"
}

# 清理无用的镜像和容器
clean_docker() {
  echo -e "${BLUE}清理无用的 Docker 资源...${NC}"
  # 删除停止的容器
  docker container prune -f
  # 删除未使用的镜像
  docker image prune -a -f
  # 删除未使用的数据卷
  docker volume prune -f
  # 删除构建缓存
  docker builder prune -f
  echo -e "${GREEN}清理完成${NC}"
}

# 设置应用实例数量
scale_service() {
  local instances=$1
  echo -e "${BLUE}设置应用实例数量为 $instances...${NC}"
  docker-compose -f docker-compose.x86.yml up -d --scale step-dwg-to-gcode=$instances
  echo -e "${GREEN}应用实例数量已设置为 $instances${NC}"
}

# 配置生产环境
setup_production() {
  echo -e "${BLUE}配置生产环境...${NC}"
  
  # 检查是否已有SSL证书
  if [ ! -f nginx/ssl/cert.pem ] || [ ! -f nginx/ssl/key.pem ]; then
    echo -e "${YELLOW}未找到SSL证书，生成自签名证书...${NC}"
    mkdir -p nginx/ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem \
      -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
    
    # 生成带SSL的Nginx配置
    cat > nginx/conf/default.conf << 'EOF'
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name _;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://step-dwg-to-gcode:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        
        # 文件上传设置
        client_max_body_size 100M;
    }
}
EOF
  fi
  
  # 启动服务
  docker-compose -f docker-compose.x86.yml up -d
  echo -e "${GREEN}生产环境配置完成${NC}"
  echo -e "应用访问地址: ${YELLOW}https://$(hostname -I | awk '{print $1}')${NC} (通过Nginx，使用HTTPS)"
}

# 主函数
main() {
  local MONITORING=false
  local PRODUCTION=false
  local SCALE=0
  
  # 如果没有参数，显示帮助
  if [ $# -eq 0 ]; then
    check_requirements
    create_directories
    start_service $MONITORING $PRODUCTION
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
      -s | --scale)
        shift
        SCALE=$1
        scale_service $SCALE
        exit 0
        ;;
      -m | --monitoring)
        MONITORING=true
        ;;
      -p | --production)
        PRODUCTION=true
        ;;
      *)
        echo -e "${RED}未知选项: $1${NC}"
        show_help
        exit 1
        ;;
    esac
    shift
  done
  
  # 执行其余操作
  check_requirements
  create_directories
  
  if [ "$PRODUCTION" = true ]; then
    setup_production
  else
    start_service $MONITORING $PRODUCTION
  fi
}

# 执行主函数
main "$@" 