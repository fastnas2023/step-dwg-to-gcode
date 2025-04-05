#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
STEP/DWG到G代码转换器启动脚本
自动启动Web服务器并打开浏览器
"""

import os
import sys
import time
import webbrowser
import subprocess
import threading
import platform

# 配置参数
PORT = 8888
HOST = "0.0.0.0"
WELCOME_URL = f"http://localhost:{PORT}"

def open_browser():
    """在延迟后打开浏览器"""
    print("正在启动浏览器...\nStarting browser...")
    time.sleep(1.5)  # 给服务器一些启动时间
    webbrowser.open(WELCOME_URL)

def print_welcome():
    """打印欢迎信息"""
    welcome_text = """
    =====================================================
     STEP/DWG 到 G代码转换器 | STEP/DWG to G-code Converter
    =====================================================
    
    正在启动Web服务...
    Starting Web server...
    
    请在浏览器中访问:
    Please visit in your browser:
    
        http://localhost:{}
    
    按Ctrl+C退出服务
    Press Ctrl+C to exit
    
    =====================================================
    """.format(PORT)
    print(welcome_text)

def is_flask_installed():
    """检查Flask是否已安装"""
    try:
        import flask
        return True
    except ImportError:
        return False

def install_flask():
    """安装Flask依赖"""
    print("未检测到Flask, 正在安装...\nFlask not detected, installing...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
        print("Flask安装成功!\nFlask installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("安装Flask失败，请手动安装: pip install flask\nFailed to install Flask. Please install manually: pip install flask")
        return False

def check_dependencies():
    """检查并安装依赖"""
    if not is_flask_installed():
        if not install_flask():
            return False
    return True

def print_footer():
    """打印程序信息"""
    print("\n")
    print("=" * 60)
    print("STEP/DWG到G代码转换器")
    print("版本: 1.0")
    print("联系方式: 微信/QQ: 350400138 | 邮箱: huaxumedia@gmail.com")
    print("感谢使用！")
    print("=" * 60)
    print("\n")

def main():
    """主函数"""
    print_welcome()
    
    # 检查依赖
    if not check_dependencies():
        input("按回车键退出...\nPress Enter to exit...")
        return
    
    # 创建欢迎页面如果不存在
    if not os.path.exists("welcome.html"):
        with open("welcome.html", "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html><head><meta http-equiv="refresh" content="0;url=http://localhost:{}"></head>
<body><p>正在重定向到Web界面... Redirecting to Web interface...</p></body></html>
""".format(PORT))
    
    # 确保路径存在
    for directory in ["uploads", "output", "plots", "templates/static/plots"]:
        os.makedirs(directory, exist_ok=True)
    
    # 打开浏览器线程
    threading.Thread(target=open_browser).start()
    
    # 启动Flask应用
    os.system(f"{sys.executable} web_interface.py")
    
    # 打印程序信息
    print_footer()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n服务已停止。\nServer stopped.")
    except Exception as e:
        print(f"\n发生错误: {e}\nAn error occurred: {e}")
        input("按回车键退出...\nPress Enter to exit...") 