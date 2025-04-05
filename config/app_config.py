#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
应用程序配置文件
包含STEP/DWG到G代码转换器的所有配置参数
"""

import os

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# 数据路径
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')
SAMPLES_DIR = os.path.join(DATA_DIR, 'samples')
UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')

# 创建所需目录
for directory in [DATA_DIR, OUTPUT_DIR, SAMPLES_DIR, UPLOAD_DIR]:
    os.makedirs(directory, exist_ok=True)

# Web应用配置
WEB_CONFIG = {
    'DEBUG': True,
    'HOST': '0.0.0.0',
    'PORT': 8888,
    'SECRET_KEY': os.urandom(24),
    'MAX_CONTENT_LENGTH': 50 * 1024 * 1024,  # 50MB
    'ALLOWED_EXTENSIONS': {'stp', 'step', 'dwg'},
    'UPLOAD_FOLDER': UPLOAD_DIR,
    'OUTPUT_FOLDER': OUTPUT_DIR,
    'STATIC_FOLDER': os.path.join(PROJECT_ROOT, 'web/static'),
    'TEMPLATE_FOLDER': os.path.join(PROJECT_ROOT, 'web/templates')
}

# 默认加工参数
DEFAULT_MACHINING_PARAMS = {
    'FEED_RATE': 500.0,  # 进给速率 (mm/min)
    'RAPID_FEED_RATE': 5000.0,  # 快速移动速率 (mm/min)
    'SAFETY_HEIGHT': 10.0,  # 安全高度 (mm)
    'CUT_DEPTH': 0.5,  # 切削深度 (mm)
    'TOOL_DIAMETER': 3.0,  # 刀具直径 (mm)
    'SPINDLE_SPEED': 3000  # 主轴转速 (RPM)
}

# 支持的控制器类型
SUPPORTED_CONTROLLERS = [
    {"id": "fanuc", "name": "FANUC (发那科)", "description": "日本发那科公司，最广泛使用的CNC控制器"},
    {"id": "siemens", "name": "Siemens SINUMERIK (西门子)", "description": "德国西门子公司，在欧洲广泛使用"},
    {"id": "heidenhain", "name": "Heidenhain (海德汉)", "description": "德国海德汉公司，用于高精度加工"},
    {"id": "haas", "name": "Haas (哈斯)", "description": "美国哈斯自动化公司，小型加工中心常用"}
]

# 默认控制器
DEFAULT_CONTROLLER = "fanuc"

# 支持的转换器类型
SUPPORTED_CONVERTERS = [
    {"id": "numpy", "name": "NumPy优化版 (推荐)", "description": "使用NumPy优化的转换器，性能最佳"},
    {"id": "no_numpy", "name": "标准版 (无NumPy依赖)", "description": "不依赖NumPy的标准转换器"},
    {"id": "simple", "name": "简化版", "description": "简化版转换器，适用于简单模型"}
]

# 默认转换器
DEFAULT_CONVERTER = "numpy" 