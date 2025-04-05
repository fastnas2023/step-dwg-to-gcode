#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
处理INTER BUSBAR REAR-1.STP文件的示例脚本
用于演示如何使用fanuc_stp_to_gcode.py转换特定STP文件为FANUC系统的G代码
"""

import os
import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description='处理INTER BUSBAR REAR-1.STP文件')
    parser.add_argument('-o', '--output-dir', default='output', help='输出目录')
    parser.add_argument('-p', '--program-number', type=int, default=1000, help='FANUC程序编号')
    parser.add_argument('-f', '--feed-rate', type=float, default=400, help='加工进给率 (mm/min)')
    parser.add_argument('-s', '--safety-height', type=float, default=15.0, help='安全高度 (mm)')
    parser.add_argument('-d', '--cut-depth', type=float, default=0.8, help='每次切割深度 (mm)')
    parser.add_argument('-t', '--tool-diameter', type=float, default=4.0, help='刀具直径 (mm)')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    input_file = "INTER BUSBAR REAR-1.STP"
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 '{input_file}' 不存在!")
        return 1
    
    # 创建输出目录（如果不存在）
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"创建输出目录: {args.output_dir}")
    
    # 准备输出文件名
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(args.output_dir, f"{base_name}_P{args.program_number}.nc")
    
    print("=" * 60)
    print(f"处理文件: {input_file}")
    print(f"输出文件: {output_file}")
    print(f"程序编号: O{args.program_number}")
    print(f"进给率: {args.feed_rate} mm/min")
    print(f"切割深度: {args.cut_depth} mm")
    print(f"安全高度: {args.safety_height} mm")
    print(f"刀具直径: {args.tool_diameter} mm")
    print("=" * 60)
    
    # 构建命令
    cmd = [
        sys.executable, 
        "fanuc_stp_to_gcode.py",
        input_file,
        "-o", output_file,
        "-p", str(args.program_number),
        "-f", str(args.feed_rate),
        "-s", str(args.safety_height),
        "-d", str(args.cut_depth),
        "-t", str(args.tool_diameter)
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    print()
    
    # 执行命令
    try:
        process = subprocess.run(cmd, check=True)
        
        if process.returncode == 0:
            print("\n转换成功!")
            print(f"FANUC G代码已生成: {output_file}")
            
            # 显示文件前几行
            if os.path.exists(output_file):
                print("\nG代码预览:")
                with open(output_file, 'r') as f:
                    preview_lines = [line.strip() for line in f.readlines()[:15]]
                    for line in preview_lines:
                        print(f"  {line}")
                    
                    if os.path.getsize(output_file) > 0:
                        print(f"  [...]")
                        print(f"  总行数: {sum(1 for _ in open(output_file))}")
            
            return 0
        else:
            print("\n转换失败!")
            return 1
    
    except subprocess.CalledProcessError as e:
        print(f"\n命令执行出错: {e}")
        return 1
    except Exception as e:
        print(f"\n处理过程中出错: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 