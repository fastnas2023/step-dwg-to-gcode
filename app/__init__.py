#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
STEP/DWG到G代码转换器 - 应用程序核心模块
"""

__version__ = '1.0.0'
__author__ = '华夏传媒'
__email__ = 'huaxumedia@gmail.com'

import os
import sys

# 确保app模块可以被正确导入
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# 定义主要路径
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_ROOT)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')
SAMPLES_DIR = os.path.join(DATA_DIR, 'samples')

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 导入主要模块
from app.controllers import *
from app.processors import *
from app.generators import *
from app.utils import * 