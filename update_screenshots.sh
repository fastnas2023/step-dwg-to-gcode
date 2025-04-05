#!/bin/bash

echo "===== STEP/DWG到G代码转换器 - 截图更新工具 ====="
echo ""

# 检查截图目录
if [ ! -d "screenshots" ]; then
  echo "错误：找不到截图目录。请确保您在项目根目录中运行此脚本。"
  exit 1
fi

# 检查截图文件
echo "检查截图文件..."
missing_files=0

check_file() {
  if [ ! -s "screenshots/$1" ]; then
    echo "警告：$1 文件不存在或为空文件"
    missing_files=$((missing_files+1))
    return 1
  else
    file_type=$(file "screenshots/$1")
    if [[ $file_type != *"PNG image data"* ]]; then
      echo "警告：$1 不是有效的PNG图片文件"
      missing_files=$((missing_files+1))
      return 1
    fi
    echo "√ $1 已找到并验证为PNG图片文件"
    return 0
  fi
}

check_file "main_page.png"
check_file "dwg_settings.png"
check_file "results.png"

if [ $missing_files -gt 0 ]; then
  echo ""
  echo "有 $missing_files 个截图文件缺失或无效。"
  echo "请按照 screenshots/README_SCREENSHOTS.txt 中的说明替换截图文件。"
  echo ""
  read -p "是否继续上传现有文件？(y/n): " continue_upload
  if [[ $continue_upload != "y" && $continue_upload != "Y" ]]; then
    echo "已取消上传。"
    exit 1
  fi
fi

# 提交更改
echo ""
echo "添加截图文件到Git..."
git add screenshots/*.png

echo "提交更改..."
git commit -m "添加：Web界面实际截图"

echo "推送到GitHub仓库..."
git push

echo ""
echo "===== 截图更新完成 ====="
echo "请访问GitHub仓库查看README.md中的截图是否正确显示。"
echo "如果截图仍然没有显示，请确保您的截图文件是有效的PNG文件，"
echo "并且已经正确地上传到了GitHub仓库。" 