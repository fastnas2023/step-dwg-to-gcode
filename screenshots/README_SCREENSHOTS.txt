截图添加指南
==========

1. 将您提供的四张屏幕截图保存到以下对应文件名：

   - main_page.png    - 主页界面截图（第一张图）
   - dwg_settings.png - DWG文件转换设置页面截图（第二张图）
   - results.png      - 转换结果页面截图（第三张图）
   - screenshot4.png  - 额外的第四张截图（如有需要）

2. 您可以使用以下方法添加截图：

   - 方法一：直接将图片文件复制到screenshots目录下，替换占位文件
   - 方法二：右键点击对应的占位文件，选择"替换"或"编辑"，然后选择实际的截图文件

3. 替换完成后运行以下命令提交更改：

   ```bash
   git add screenshots/*.png
   git commit -m "添加：Web界面截图"
   git push
   ```

截图说明：
- main_page.png：展示了Web界面的首页，包含文件上传区域和功能介绍
- dwg_settings.png：展示DWG文件转换设置页面，包含不同零件类型选择和转换选项
- results.png：展示转换结果页面，包含G代码预览和下载选项
- screenshot4.png：（根据需要描述第四张截图） 