#!/bin/bash

# 在使用此脚本前，请确保您已经登录GitHub CLI (gh)
# 如果没有登录，请运行: gh auth login

echo "===== 开始更新GitHub仓库 ====="

# 确保移动二维码图片到正确位置
if [ -f "qrcode-alipay-small.png" ]; then
  echo "移动支付宝二维码到templates/static/img目录"
  cp qrcode-alipay-small.png templates/static/img/
fi

if [ -f "qrcode-wechat-small.png" ]; then
  echo "移动微信支付二维码到templates/static/img目录"
  cp qrcode-wechat-small.png templates/static/img/
fi

# 检查GitHub CLI是否已安装
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) 未安装，请先安装"
    echo "可以访问 https://cli.github.com/ 了解安装方法"
    exit 1
fi

# 仓库信息
REPO="fastnas2023/step-dwg-to-gcode"

# 检查是否已克隆仓库
if [ ! -d ".git" ]; then
    echo "初始化Git仓库..."
    git init
    git remote add origin "https://github.com/$REPO.git"
else
    echo "Git仓库已存在，检查远程URL..."
    CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
    if [[ "$CURRENT_REMOTE" != *"$REPO"* ]]; then
        echo "设置正确的远程URL..."
        git remote remove origin
        git remote add origin "https://github.com/$REPO.git"
    fi
fi

# 添加所有文件到暂存区
echo "添加文件到Git..."
git add .

# 创建提交
echo "创建提交..."
git commit -m "更新STEP/DWG到G代码转换器，添加打赏支持"

# 强制推送到GitHub（这将覆盖远程仓库上的所有内容）
echo "推送到GitHub（这将覆盖远程内容）..."
echo "是否继续? (y/n)"
read confirm

if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
    git push -f origin master || git push -f origin main
    echo "推送完成！"
else
    echo "操作已取消"
fi

echo "===== 脚本执行完毕 =====" 