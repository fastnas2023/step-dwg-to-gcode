#!/bin/bash
# 将代码推送到GitHub仓库的脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}STEP/DWG 到 G-code 转换服务 GitHub 推送脚本${NC}"
echo

# 检查命令行参数
if [ "$#" -ne 1 ]; then
    echo -e "${RED}错误: 请提供你的GitHub仓库URL${NC}"
    echo -e "用法: $0 <GitHub仓库URL>"
    echo -e "例如: $0 https://github.com/your-username/step-dwg-to-gcode.git"
    exit 1
fi

REPO_URL=$1

# 验证 URL 格式
if [[ ! $REPO_URL =~ ^https://github.com/.+/.+\.git$ ]]; then
    echo -e "${YELLOW}警告: 仓库URL格式可能不正确，应该类似于: https://github.com/username/repo.git${NC}"
    read -p "是否继续? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 确保当前目录是项目根目录
if [ ! -f "requirements.txt" ] || [ ! -d "web" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 创建 .gitignore 文件
echo -e "${BLUE}创建 .gitignore 文件...${NC}"
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
venv/
.venv/

# 项目特定文件
web/uploads/*
!web/uploads/.gitkeep
web/output/*
!web/output/.gitkeep
web/static/plots/*
!web/static/plots/.gitkeep
data/

# IDE 和编辑器
.vscode/
.idea/
*.swp
*.swo
*~

# 日志和临时文件
*.log
*.tmp
.DS_Store

# Docker
.dockerignore

# 大型二进制文件
*.zip
*.stp
*.step
*.dwg
*.dxf
*.nc
EOF

# 检查是否已经初始化了 Git 仓库
if [ ! -d ".git" ]; then
    echo -e "${BLUE}初始化 Git 仓库...${NC}"
    git init
else
    echo -e "${YELLOW}Git 仓库已存在${NC}"
fi

# 确保上传目录存在并保留
mkdir -p web/uploads web/output web/static/plots
touch web/uploads/.gitkeep web/output/.gitkeep web/static/plots/.gitkeep

# 添加文件到 Git
echo -e "${BLUE}添加文件到仓库...${NC}"
git add .

# 提交变更
echo -e "${BLUE}提交变更...${NC}"
git commit -m "初始化STEP/DWG到G-code转换服务"

# 设置远程仓库
echo -e "${BLUE}设置远程仓库...${NC}"
# 检查是否已有远程仓库
if git remote -v | grep -q "origin"; then
    echo -e "${YELLOW}更新远程仓库 origin${NC}"
    git remote set-url origin $REPO_URL
else
    echo -e "${GREEN}添加远程仓库 origin${NC}"
    git remote add origin $REPO_URL
fi

# 推送到远程仓库
echo -e "${BLUE}推送到远程仓库...${NC}"
echo -e "${YELLOW}注意: 这一步可能需要你输入GitHub凭据${NC}"
echo
echo -e "${GREEN}准备推送! 按任意键继续，或Ctrl+C取消${NC}"
read -n 1 -s

# 推送代码
git push -u origin master

# 完成提示
if [ $? -eq 0 ]; then
    echo
    echo -e "${GREEN}成功! 代码已推送到 $REPO_URL${NC}"
    echo -e "你可以在GitHub上查看你的代码了!"
else
    echo
    echo -e "${RED}推送失败，请检查错误信息${NC}"
fi 