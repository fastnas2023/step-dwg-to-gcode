#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试模块 - 单元测试和集成测试
"""

import os
import sys

# 确保app模块可以被正确导入
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from tests.controllers import *
from tests.processors import * 