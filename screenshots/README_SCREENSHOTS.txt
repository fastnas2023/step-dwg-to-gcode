截图添加指南
==========

目前GitHub仓库中的截图是临时占位图片（1x1像素），需要替换为实际的Web界面截图。

请按照以下步骤操作：

1. 下载之前提供的四张屏幕截图到本地

2. 将这些截图文件重命名为：
   - main_page.png    - 主页界面截图（第一张图）
   - dwg_settings.png - DWG文件转换设置页面截图（第二张图）
   - results.png      - 转换结果页面截图（第三张图）
   - screenshot4.png  - 额外的第四张截图（如有需要）

3. 将重命名后的截图文件放到项目的screenshots目录中，替换现有的占位图片

4. 运行以下Git命令上传截图：
   ```bash
   cd /path/to/your/project
   git add screenshots/*.png
   git commit -m "添加：Web界面实际截图"
   git push
   ```

5. 刷新GitHub仓库页面，确认README.md中现在可以正确显示截图

上传正确的截图后，GitHub上的README.md文件中将显示完整的Web界面预览。

补充说明：
- 项目中已经设置了截图引用路径，只需替换图片文件即可
- 请确保图片格式为PNG，并且文件名与上述完全一致
- 如果您已手机拍摄了Web界面截图，可以发送到自己的电子邮箱，然后在电脑上下载并保存 