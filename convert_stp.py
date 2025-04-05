#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
STEP文件到G代码转换器启动脚本
该脚本让用户选择使用哪个转换器版本
"""

import os
import sys
import argparse
import importlib.util
import subprocess

def check_module(module_name):
    """检查模块是否已安装"""
    return importlib.util.find_spec(module_name) is not None

def main():
    parser = argparse.ArgumentParser(description='STEP文件到G代码转换器')
    parser.add_argument('input_file', help='输入STEP文件路径')
    parser.add_argument('-o', '--output', help='输出G代码文件路径')
    parser.add_argument('-f', '--feed-rate', type=float, default=500, help='加工进给率 (mm/min)')
    parser.add_argument('-r', '--rapid-feed-rate', type=float, default=1000, help='快速移动进给率 (mm/min)')
    parser.add_argument('-s', '--safety-height', type=float, default=5.0, help='安全高度 (mm)')
    parser.add_argument('-d', '--cut-depth', type=float, default=0.5, help='每次切割深度 (mm)')
    parser.add_argument('-t', '--tool-diameter', type=float, default=3.0, help='刀具直径 (mm)')
    parser.add_argument('-m', '--mode', choices=['auto', 'simple', 'steputils', 'pythonocc'], 
                       default='auto', help='指定使用哪个转换器')
    parser.add_argument('-p', '--spline-samples', type=int, default=50, help='样条曲线采样点数（仅用于steputils版本）')
    
    args = parser.parse_args()
    
    # 验证输入文件是否存在
    if not os.path.exists(args.input_file):
        print(f"错误: 输入文件 '{args.input_file}' 不存在")
        return 1
    
    # 确定使用哪个转换器
    converter_script = None
    
    if args.mode == 'auto':
        # 自动选择最佳可用转换器
        if check_module('OCC'):
            print("检测到PythonOCC库，使用功能全面版本...")
            converter_script = 'stp_to_gcode.py'
        elif check_module('steputils'):
            print("检测到steputils库，使用中等复杂度版本...")
            converter_script = 'steputils_to_gcode.py'
        else:
            print("未检测到专用库，使用简易版本...")
            converter_script = 'simple_stp_to_gcode.py'
    else:
        # 用户指定的转换器
        if args.mode == 'simple':
            converter_script = 'simple_stp_to_gcode.py'
        elif args.mode == 'steputils':
            if not check_module('steputils'):
                print("警告: 未检测到steputils库，可能无法正常运行")
            converter_script = 'steputils_to_gcode.py'
        elif args.mode == 'pythonocc':
            if not check_module('OCC'):
                print("警告: 未检测到PythonOCC库，可能无法正常运行")
            converter_script = 'stp_to_gcode.py'
    
    # 构建命令行参数
    cmd = [sys.executable, converter_script, args.input_file]
    
    if args.output:
        cmd.extend(['-o', args.output])
    
    cmd.extend(['-f', str(args.feed_rate)])
    cmd.extend(['-r', str(args.rapid_feed_rate)])
    cmd.extend(['-s', str(args.safety_height)])
    cmd.extend(['-d', str(args.cut_depth)])
    cmd.extend(['-t', str(args.tool_diameter)])
    
    # 仅在使用steputils版本时添加样条曲线采样参数
    if converter_script == 'steputils_to_gcode.py':
        cmd.extend(['-p', str(args.spline_samples)])
    
    print(f"执行命令: {' '.join(cmd)}")
    
    # 执行选定的转换器脚本
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except Exception as e:
        print(f"执行过程中出错: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 