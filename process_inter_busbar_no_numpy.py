#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
处理INTER BUSBAR REAR-1.STP文件的示例脚本（无NumPy依赖版本）
此脚本演示如何使用无NumPy依赖的FANUC G代码转换器处理STEP文件
"""

import os
import sys
import argparse
import subprocess

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='处理INTER BUSBAR REAR-1.STP文件并生成FANUC G代码（无NumPy依赖版本）')
    parser.add_argument('-o', '--output-dir', default='output', help='输出目录路径')
    parser.add_argument('-p', '--program-number', type=int, default=1000, help='FANUC程序编号')
    parser.add_argument('-f', '--feed-rate', type=float, default=400, help='加工进给率 (mm/min)')
    parser.add_argument('-s', '--safety-height', type=float, default=15.0, help='安全高度 (mm)')
    parser.add_argument('-d', '--cut-depth', type=float, default=0.8, help='每次切割深度 (mm)')
    parser.add_argument('-t', '--tool-diameter', type=float, default=4.0, help='刀具直径 (mm)')
    
    args = parser.parse_args()
    
    # 输入文件
    input_file = "INTER BUSBAR REAR-1.STP"
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 '{input_file}'")
        return 1
    
    # 创建输出目录（如果不存在）
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"创建输出目录: {args.output_dir}")
    
    # 构建输出文件名
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(args.output_dir, f"{base_name}_P{args.program_number}.nc")
    
    # 输出处理信息
    print("=" * 50)
    print("无NumPy依赖版本 - FANUC G代码生成器")
    print("=" * 50)
    print(f"输入文件:        {input_file}")
    print(f"输出文件:        {output_file}")
    print(f"程序编号:        O{args.program_number}")
    print(f"进给率:          {args.feed_rate} mm/min")
    print(f"切割深度:        {args.cut_depth} mm")
    print(f"安全高度:        {args.safety_height} mm")
    print(f"刀具直径:        {args.tool_diameter} mm")
    print("=" * 50)
    
    # 构建命令
    cmd = [
        "python", "fanuc_stp_to_gcode_no_numpy.py", 
        input_file,
        "-o", output_file,
        "-p", str(args.program_number),
        "-f", str(args.feed_rate),
        "-s", str(args.safety_height),
        "-d", str(args.cut_depth),
        "-t", str(args.tool_diameter)
    ]
    
    # 输出将要执行的命令
    print("执行命令:")
    print(" ".join(cmd))
    print("-" * 50)
    
    # 执行命令
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        
        # 检查输出文件是否已生成
        if os.path.exists(output_file):
            print("-" * 50)
            print(f"成功生成G代码文件: {output_file}")
            
            # 显示文件的前15行
            try:
                with open(output_file, 'r') as f:
                    lines = f.readlines()
                    print("\n预览生成的G代码 (前15行):")
                    print("".join(lines[:15]))
                    print(f"... (共 {len(lines)} 行)")
            except Exception as e:
                print(f"无法预览文件内容: {e}")
            
            return 0
        else:
            print(f"错误: 未能生成输出文件 {output_file}")
            return 1
            
    except subprocess.CalledProcessError as e:
        print(f"错误: 命令执行失败")
        print(f"退出代码: {e.returncode}")
        print(f"错误输出: {e.stderr}")
        return e.returncode
    except Exception as e:
        print(f"错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 