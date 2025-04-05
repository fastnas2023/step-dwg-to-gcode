#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
STEP/DWG到G代码转换器启动脚本
"""

import os
import sys
import webbrowser
import subprocess
import time
from threading import Thread

def main():
    """主函数"""
    # 配置基本路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查Python环境
    print("检查Python环境...")
    python_exe = sys.executable
    
    # 检查并创建虚拟环境
    venv_dir = os.path.join(current_dir, "venv")
    if not os.path.exists(venv_dir):
        try:
            print("创建虚拟环境...")
            subprocess.check_call([python_exe, "-m", "venv", venv_dir])
        except subprocess.CalledProcessError:
            print("创建虚拟环境失败！")
            return 1
    
    # 获取正确的Python解释器和pip
    if sys.platform == 'win32':
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
        venv_pip = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python")
        venv_pip = os.path.join(venv_dir, "bin", "pip")
    
    # 检查并安装依赖
    print("检查并安装依赖...")
    requirements_file = os.path.join(current_dir, "requirements.txt")
    if os.path.exists(requirements_file):
        try:
            subprocess.check_call([venv_pip, "install", "-r", requirements_file])
        except subprocess.CalledProcessError:
            print("安装依赖失败！")
            return 1
    
    # 确保静态资源目录存在
    static_dir = os.path.join(current_dir, "web", "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # 启动Web服务器
    print("启动Web服务器...")
    start_app_script = os.path.join(current_dir, "bin", "start_app.py")
    
    # 在新线程中打开浏览器
    def open_browser():
        time.sleep(2)  # 等待服务器启动
        webbrowser.open("http://localhost:8888")
    
    browser_thread = Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 启动应用
    try:
        subprocess.check_call([venv_python, start_app_script, "--web"])
    except KeyboardInterrupt:
        print("\n服务已停止")
    except subprocess.CalledProcessError:
        print("启动应用失败！")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 