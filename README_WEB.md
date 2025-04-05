# STEP/DWG 到 G代码转换器 - Web界面

这是一个将STEP和DWG文件转换为FANUC兼容G代码的Web应用程序，提供直观的用户界面和强大的转换功能。

## 功能特点

- **多格式支持**: 支持STEP和DWG文件格式
- **多种转换器**: 提供标准版、无NumPy版和NumPy优化版三种转换器
- **3D可视化**: 生成模型和路径的3D可视化图表
- **灵活参数**: 可自定义进给速度、安全高度、切削深度等加工参数
- **结果分析**: 提供详细的转换结果、预览和统计信息
- **双语支持**: 中文和英文界面

## 快速启动

1. 确保已安装Python 3.7或更高版本
2. 运行启动脚本:

```bash
python start_converter.py
```

启动脚本会自动:
- 检查并安装必要的依赖
- 创建所需的目录结构
- 启动Web服务器
- 打开浏览器访问应用

## 手动启动

如果需要手动启动，请按以下步骤:

1. 安装Flask (如果尚未安装):

```bash
pip install flask
```

2. 启动Web服务器:

```bash
python web_interface.py
```

3. 在浏览器中访问:

```
http://localhost:8888
```

## 使用方法

1. 上传STEP或DWG文件
2. 根据文件类型设置转换参数
3. 点击"开始转换"按钮
4. 等待处理完成
5. 查看和下载转换结果

## 目录结构

- `web_interface.py`: Web应用程序主文件
- `templates/`: HTML模板
- `templates/static/`: 静态资源(CSS, JS)
- `uploads/`: 上传文件临时存储
- `output/`: 生成的G代码输出
- `plots/`: 生成的可视化图表

## 系统要求

- Python 3.7+
- Flask
- NumPy (对于NumPy优化版转换器)
- Matplotlib (用于可视化)

---

# STEP/DWG to G-code Converter - Web Interface

This is a web application for converting STEP and DWG files to FANUC-compatible G-code, providing an intuitive user interface and powerful conversion capabilities.

## Features

- **Multi-format Support**: Support for STEP and DWG file formats
- **Multiple Converters**: Standard, No-NumPy, and NumPy-optimized converter options
- **3D Visualization**: Generate 3D visualizations of models and toolpaths
- **Flexible Parameters**: Customize feed rate, safety height, cut depth, and other machining parameters
- **Result Analysis**: Detailed conversion results, previews, and statistics
- **Bilingual Support**: Chinese and English interfaces

## Quick Start

1. Ensure Python 3.7 or higher is installed
2. Run the starter script:

```bash
python start_converter.py
```

The starter script will automatically:
- Check and install necessary dependencies
- Create required directory structure
- Start the web server
- Open your browser to access the application

## Manual Start

If you need to start manually, follow these steps:

1. Install Flask (if not already installed):

```bash
pip install flask
```

2. Start the web server:

```bash
python web_interface.py
```

3. Visit in your browser:

```
http://localhost:8888
```

## Usage

1. Upload a STEP or DWG file
2. Set conversion parameters based on file type
3. Click the "Start Conversion" button
4. Wait for processing to complete
5. View and download conversion results

## Directory Structure

- `web_interface.py`: Main web application file
- `templates/`: HTML templates
- `templates/static/`: Static resources (CSS, JS)
- `uploads/`: Temporary storage for uploaded files
- `output/`: Generated G-code output
- `plots/`: Generated visualization charts

## System Requirements

- Python 3.7+
- Flask
- NumPy (for NumPy-optimized converter)
- Matplotlib (for visualization) 