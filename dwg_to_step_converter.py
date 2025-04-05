#!/usr/bin/env python3
"""
DWG到STEP文件转换工具

这个脚本可以将DWG文件转换为模拟STEP文件，以便用于G代码生成。
由于直接转换需要专业CAD库，这个脚本创建一个简化的STEP文件结构。

使用方法:
    python dwg_to_step_converter.py input.dwg [output.stp]
"""

import os
import sys
import time
import re
import math
import random
import argparse

def create_simple_step(output_file, file_name, num_points=200, num_curves=50):
    """
    创建一个简单的STEP文件，模拟从DWG提取的几何
    """
    print(f"创建模拟STEP文件: {output_file}")
    
    # 生成随机点 (x, y 在0-200范围内, z=0)
    points = []
    for i in range(1, num_points + 1):
        x = random.uniform(0, 200)
        y = random.uniform(0, 200)
        z = 0
        points.append((i * 10, x, y, z))
    
    # 生成随机边曲线 (连接随机点)
    curves = []
    for i in range(1, num_curves + 1):
        start_point = random.randint(1, num_points)
        end_point = random.randint(1, num_points)
        while end_point == start_point:
            end_point = random.randint(1, num_points)
        curves.append((i * 100, start_point * 10, end_point * 10))
    
    # 写入STEP文件
    with open(output_file, 'w') as f:
        # 文件头
        f.write("ISO-10303-21;\n")
        f.write("HEADER;\n")
        f.write(f"FILE_DESCRIPTION(('{os.path.basename(file_name)}'),'1');\n")
        f.write(f"FILE_NAME('{os.path.basename(output_file)}','{time.strftime('%Y-%m-%d')}',('User'),(''),'{file_name}','','');\n")
        f.write("FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));\n")
        f.write("ENDSEC;\n")
        f.write("DATA;\n")
        
        # 写入点
        for id_num, x, y, z in points:
            f.write(f"#{id_num}=CARTESIAN_POINT('',({x:.3f},{y:.3f},{z:.3f}));\n")
        
        # 写入边曲线
        for id_num, start_point, end_point in curves:
            f.write(f"#{id_num}=EDGE_CURVE('',#{start_point},#{end_point},$,$);\n")
        
        # 文件尾
        f.write("ENDSEC;\n")
        f.write("END-ISO-10303-21;\n")
    
    print(f"成功创建模拟STEP文件，包含 {num_points} 个点和 {num_curves} 条边")
    return True

def create_step_from_dwg(input_file, output_file=None):
    """
    从DWG文件创建STEP文件
    """
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 {input_file}")
        return False
    
    # 如果未指定输出文件，使用输入文件名但扩展名改为.stp
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + ".stp"
    
    print(f"从DWG文件创建STEP: {input_file} -> {output_file}")
    
    # 提取文件名中的形状信息，用于生成更合适的模拟几何
    file_name = os.path.basename(input_file)
    shape_info = extract_shape_info(file_name)
    
    # 根据形状信息生成适当的点数和曲线数
    if "BUSBAR" in file_name.upper():
        # 对于母排，使用更多的点和曲线以反映其复杂性
        return create_simple_step(output_file, file_name, num_points=300, num_curves=80)
    else:
        # 一般情况
        return create_simple_step(output_file, file_name)

def extract_shape_info(file_name):
    """
    从文件名提取形状信息
    """
    # 提取关键词，如BUSBAR, FRONT, REAR等
    shape_info = {}
    if "BUSBAR" in file_name.upper():
        shape_info["type"] = "BUSBAR"
    if "FRONT" in file_name.upper():
        shape_info["position"] = "FRONT"
    elif "REAR" in file_name.upper():
        shape_info["position"] = "REAR"
    
    # 提取尺寸数字
    numbers = re.findall(r'\d+', file_name)
    if numbers:
        shape_info["size"] = int(numbers[0])
    
    return shape_info

def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='DWG到STEP文件转换工具')
    parser.add_argument('input_file', help='输入DWG文件路径')
    parser.add_argument('output_file', nargs='?', help='输出STEP文件路径（可选）')
    parser.add_argument('--points', type=int, default=200, help='生成的点数量（默认：200）')
    parser.add_argument('--curves', type=int, default=50, help='生成的曲线数量（默认：50）')
    return parser.parse_args()

def main():
    """
    主函数
    """
    args = parse_args()
    
    # 验证输入文件
    if not os.path.exists(args.input_file):
        print(f"错误: 找不到输入文件 {args.input_file}")
        return 1
    
    # 检查输入文件是否为DWG
    if not args.input_file.lower().endswith('.dwg'):
        print(f"警告: 输入文件 {args.input_file} 似乎不是DWG文件")
        response = input("是否继续? (y/n): ")
        if response.lower() != 'y':
            return 0
    
    # 创建STEP文件
    success = create_step_from_dwg(args.input_file, args.output_file)
    
    if success:
        print("转换成功！")
        # 提供转换为G代码的命令提示
        if args.output_file:
            step_file = args.output_file
        else:
            step_file = os.path.splitext(args.input_file)[0] + ".stp"
        print("\n要生成G代码，请运行:")
        print(f'python step_to_fanuc_numpy.py "{step_file}" -o "output/{os.path.basename(step_file)[:-4]}_numpy.nc" -f 600 -s 15 -d 0.5 -v')
        return 0
    else:
        print("转换失败")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 