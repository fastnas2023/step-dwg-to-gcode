#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
STEP/DWG到G代码转换器启动脚本
自动启动Web服务器或命令行界面
"""

import os
import sys
import time
import webbrowser
import argparse
import threading

# 添加项目根目录到系统路径
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 导入配置
from config.app_config import WEB_CONFIG

def check_dependencies():
    """检查并安装必要的依赖"""
    try:
        import flask
        return True
    except ImportError:
        print("Flask未安装，正在尝试安装...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
            print("Flask安装成功!")
            return True
        except Exception as e:
            print(f"安装依赖时出错: {e}")
            print("请手动安装依赖: pip install -r requirements.txt")
            return False

def print_welcome(mode="web", port=None):
    """打印欢迎信息"""
    welcome_text = f"""
    =====================================================
     STEP/DWG 到 G代码转换器 | STEP/DWG to G-code Converter
    =====================================================
    
    正在启动{mode}服务...
    Starting {mode} service...
    """
    
    if mode == "web" and port:
        welcome_text += f"""
    请在浏览器中访问:
    Please visit in your browser:
    
        http://localhost:{port}
    
    按Ctrl+C退出服务
    Press Ctrl+C to exit
    """
    
    welcome_text += """
    =====================================================
    """
    print(welcome_text)

def open_browser(port):
    """在延迟后打开浏览器"""
    time.sleep(1.5)  # 给服务器一些启动时间
    webbrowser.open(f"http://localhost:{port}")

def start_web_interface(open_browser_tab=True):
    """启动Web界面"""
    # 导入Web界面模块
    from web.web_interface import app
    
    port = WEB_CONFIG['PORT']
    host = WEB_CONFIG['HOST']
    debug = WEB_CONFIG['DEBUG']
    
    print_welcome("web", port)
    
    # 打开浏览器
    if open_browser_tab:
        threading.Thread(target=open_browser, args=(port,)).start()
    
    # 启动Web服务器
    app.run(host=host, port=port, debug=debug)

def start_cli():
    """启动命令行界面"""
    print_welcome("命令行")
    
    # 导入CLI模块
    from cli.cli_interface import main as cli_main
    
    # 调用CLI主函数
    cli_main()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="STEP/DWG到G代码转换器")
    
    # 定义命令行参数
    parser.add_argument("--cli", action="store_true", help="启动命令行界面")
    parser.add_argument("--web", action="store_true", help="启动Web界面")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    
    args = parser.parse_args()
    
    # 检查依赖
    if not check_dependencies():
        return 1
    
    # 决定启动模式
    if args.cli:
        start_cli()
    else:
        # 默认使用Web界面
        start_web_interface(not args.no_browser)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n服务已停止")
        sys.exit(0) 