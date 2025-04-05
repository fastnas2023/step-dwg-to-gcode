#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行 Web 应用程序的简化脚本
用法: python run_web.py
"""

import os
import sys

# 确保路径设置正确，可以找到所需的模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)  # 优先查找当前目录中的模块

from web_interface import app

# 确保各目录存在
for folder in ['uploads', 'output', 'static/plots']:
    os.makedirs(folder, exist_ok=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'true').lower() == 'true'
    
    print(f"启动服务器: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    app.run(host=host, port=port, debug=debug) 