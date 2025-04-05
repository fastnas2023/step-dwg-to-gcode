@echo off
echo ===== STEP/DWG到G代码转换器 - 截图更新工具 =====
echo.

REM 检查截图目录
if not exist screenshots (
  echo 错误：找不到截图目录。请确保您在项目根目录中运行此脚本。
  exit /b 1
)

REM 检查截图文件
echo 检查截图文件...
set missing_files=0

if not exist screenshots\main_page.png (
  echo 警告：main_page.png 文件不存在
  set /a missing_files+=1
) else (
  echo √ main_page.png 已找到
)

if not exist screenshots\dwg_settings.png (
  echo 警告：dwg_settings.png 文件不存在
  set /a missing_files+=1
) else (
  echo √ dwg_settings.png 已找到
)

if not exist screenshots\results.png (
  echo 警告：results.png 文件不存在
  set /a missing_files+=1
) else (
  echo √ results.png 已找到
)

if %missing_files% gtr 0 (
  echo.
  echo 有 %missing_files% 个截图文件缺失。
  echo 请按照 screenshots\README_SCREENSHOTS.txt 中的说明替换截图文件。
  echo.
  set /p continue_upload=是否继续上传现有文件？(y/n): 
  if not "%continue_upload%"=="y" if not "%continue_upload%"=="Y" (
    echo 已取消上传。
    exit /b 1
  )
)

REM 提交更改
echo.
echo 添加截图文件到Git...
git add screenshots\*.png

echo 提交更改...
git commit -m "添加：Web界面实际截图"

echo 推送到GitHub仓库...
git push

echo.
echo ===== 截图更新完成 =====
echo 请访问GitHub仓库查看README.md中的截图是否正确显示。
echo 如果截图仍然没有显示，请确保您的截图文件是有效的PNG文件，
echo 并且已经正确地上传到了GitHub仓库。 