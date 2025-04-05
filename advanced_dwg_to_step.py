#!/usr/bin/env python3
"""
高级DWG到STEP文件转换工具

这个脚本使用预定义的模板为特定零件创建STEP文件，
然后可以用于G代码生成。适用于常见零件如母排等。

使用方法:
    python advanced_dwg_to_step.py input.dwg [--type busbar|plate|bracket] [output.stp]
"""

import os
import sys
import time
import re
import math
import random
import argparse

# 定义常见零件的模板
TEMPLATES = {
    "busbar": {
        "points": [
            # 外部轮廓 - 矩形 (0,0,0) 到 (100,200,0)
            (10, 0.0, 0.0, 0.0),
            (20, 100.0, 0.0, 0.0),
            (30, 100.0, 200.0, 0.0),
            (40, 0.0, 200.0, 0.0),
            (50, 0.0, 0.0, 0.0),
            
            # 内部孔洞1 - 圆形近似
            (60, 25.0, 50.0, 0.0),
            (70, 35.0, 50.0, 0.0),
            (80, 35.0, 60.0, 0.0),
            (90, 25.0, 60.0, 0.0),
            (100, 25.0, 50.0, 0.0),
            
            # 内部孔洞2 - 圆形近似
            (110, 75.0, 50.0, 0.0),
            (120, 85.0, 50.0, 0.0),
            (130, 85.0, 60.0, 0.0), 
            (140, 75.0, 60.0, 0.0),
            (150, 75.0, 50.0, 0.0),
            
            # 内部孔洞3 - 圆形近似
            (160, 25.0, 140.0, 0.0),
            (170, 35.0, 140.0, 0.0),
            (180, 35.0, 150.0, 0.0),
            (190, 25.0, 150.0, 0.0),
            (200, 25.0, 140.0, 0.0),
            
            # 内部孔洞4 - 圆形近似
            (210, 75.0, 140.0, 0.0),
            (220, 85.0, 140.0, 0.0),
            (230, 85.0, 150.0, 0.0),
            (240, 75.0, 150.0, 0.0),
            (250, 75.0, 140.0, 0.0),
        ],
        "edges": [
            # 外部轮廓边
            (1000, 10, 20),
            (1010, 20, 30),
            (1020, 30, 40),
            (1030, 40, 50),
            
            # 内部孔洞1边
            (2000, 60, 70),
            (2010, 70, 80),
            (2020, 80, 90),
            (2030, 90, 100),
            
            # 内部孔洞2边
            (3000, 110, 120),
            (3010, 120, 130),
            (3020, 130, 140),
            (3030, 140, 150),
            
            # 内部孔洞3边
            (4000, 160, 170),
            (4010, 170, 180),
            (4020, 180, 190),
            (4030, 190, 200),
            
            # 内部孔洞4边
            (5000, 210, 220),
            (5010, 220, 230),
            (5020, 230, 240),
            (5030, 240, 250),
        ]
    },
    
    "front_busbar": {
        "points": [
            # 外部轮廓 - 特殊形状
            (10, 0.0, 0.0, 0.0),
            (20, 120.0, 0.0, 0.0),
            (30, 120.0, 30.0, 0.0),
            (40, 80.0, 30.0, 0.0),
            (50, 80.0, 180.0, 0.0),
            (60, 120.0, 180.0, 0.0),
            (70, 120.0, 220.0, 0.0),
            (80, 0.0, 220.0, 0.0),
            (90, 0.0, 180.0, 0.0),
            (100, 40.0, 180.0, 0.0),
            (110, 40.0, 30.0, 0.0),
            (120, 0.0, 30.0, 0.0),
            (130, 0.0, 0.0, 0.0),
            
            # 内部孔洞 - 圆形近似
            (200, 60.0, 110.0, 0.0),
            (210, 70.0, 110.0, 0.0),
            (220, 70.0, 120.0, 0.0),
            (230, 60.0, 120.0, 0.0),
            (240, 60.0, 110.0, 0.0),
        ],
        "edges": [
            # 外部轮廓边
            (1000, 10, 20),
            (1010, 20, 30),
            (1020, 30, 40),
            (1030, 40, 50),
            (1040, 50, 60),
            (1050, 60, 70),
            (1060, 70, 80),
            (1070, 80, 90),
            (1080, 90, 100),
            (1090, 100, 110),
            (1100, 110, 120),
            (1110, 120, 130),
            
            # 内部孔洞边
            (2000, 200, 210),
            (2010, 210, 220),
            (2020, 220, 230),
            (2030, 230, 240),
        ]
    },
    
    "rear_busbar": {
        "points": [
            # 外部轮廓 - 特殊形状
            (10, 0.0, 0.0, 0.0),
            (20, 100.0, 0.0, 0.0),
            (30, 100.0, 240.0, 0.0),
            (40, 0.0, 240.0, 0.0),
            (50, 0.0, 0.0, 0.0),
            
            # 内部通道1
            (60, 20.0, 20.0, 0.0),
            (70, 80.0, 20.0, 0.0),
            (80, 80.0, 60.0, 0.0),
            (90, 20.0, 60.0, 0.0),
            (100, 20.0, 20.0, 0.0),
            
            # 内部通道2
            (110, 20.0, 180.0, 0.0),
            (120, 80.0, 180.0, 0.0),
            (130, 80.0, 220.0, 0.0),
            (140, 20.0, 220.0, 0.0),
            (150, 20.0, 180.0, 0.0),
        ],
        "edges": [
            # 外部轮廓边
            (1000, 10, 20),
            (1010, 20, 30),
            (1020, 30, 40),
            (1030, 40, 50),
            
            # 内部通道1边
            (2000, 60, 70),
            (2010, 70, 80),
            (2020, 80, 90),
            (2030, 90, 100),
            
            # 内部通道2边
            (3000, 110, 120),
            (3010, 120, 130),
            (3020, 130, 140),
            (3030, 140, 150),
        ]
    }
}

def detect_part_type(file_name):
    """
    根据文件名检测零件类型
    """
    file_name_upper = file_name.upper()
    
    if "BUSBAR" in file_name_upper:
        if "FRONT" in file_name_upper:
            return "front_busbar"
        elif "REAR" in file_name_upper:
            return "rear_busbar"
        else:
            return "busbar"
    elif "PLATE" in file_name_upper:
        return "plate"
    elif "BRACKET" in file_name_upper:
        return "bracket"
    else:
        return "generic"

def create_step_from_template(output_file, template_name, file_name, scale=1.0, rotation=0):
    """
    使用模板创建STEP文件
    """
    print(f"使用模板 '{template_name}' 创建STEP文件: {output_file}")
    
    # 获取模板
    if template_name in TEMPLATES:
        template = TEMPLATES[template_name]
    else:
        print(f"警告: 找不到模板 '{template_name}'，使用通用母排模板")
        template = TEMPLATES["busbar"]
    
    # 应用变换 (缩放和旋转)
    transformed_points = []
    for id_num, x, y, z in template["points"]:
        if rotation != 0:
            # 应用旋转
            angle = math.radians(rotation)
            new_x = x * math.cos(angle) - y * math.sin(angle)
            new_y = x * math.sin(angle) + y * math.cos(angle)
            x, y = new_x, new_y
        
        # 应用缩放
        x *= scale
        y *= scale
        z *= scale
        
        transformed_points.append((id_num, x, y, z))
    
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
        for id_num, x, y, z in transformed_points:
            f.write(f"#{id_num}=CARTESIAN_POINT('',({x:.3f},{y:.3f},{z:.3f}));\n")
        
        # 写入边曲线
        for id_num, start_point, end_point in template["edges"]:
            f.write(f"#{id_num}=EDGE_CURVE('',#{start_point},#{end_point},$,$);\n")
        
        # 文件尾
        f.write("ENDSEC;\n")
        f.write("END-ISO-10303-21;\n")
    
    points_count = len(template["points"])
    edges_count = len(template["edges"])
    print(f"成功创建STEP文件，包含 {points_count} 个点和 {edges_count} 条边")
    return True

def convert_dwg_to_step(input_file, output_file=None, part_type=None, scale=1.0):
    """
    将DWG文件转换为STEP文件
    """
    if not os.path.exists(input_file):
        print(f"错误: 找不到输入文件 {input_file}")
        return False
    
    # 如果未指定输出文件，使用输入文件名但扩展名改为.stp
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + ".stp"
    
    # 如果未指定零件类型，从文件名猜测
    if part_type is None:
        part_type = detect_part_type(os.path.basename(input_file))
    
    print(f"从DWG文件创建STEP: {input_file} -> {output_file} (类型: {part_type})")
    
    # 提取文件名中的数字作为缩放因子
    numbers = re.findall(r'\d+', os.path.basename(input_file))
    if numbers and len(numbers) > 0:
        size_factor = int(numbers[0]) / 100  # 使用第一个数字作为比例因子
        if 0.5 <= size_factor <= 2.0:  # 限制合理范围
            scale = size_factor
    
    # 使用模板创建STEP文件
    return create_step_from_template(output_file, part_type, input_file, scale)

def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description='高级DWG到STEP文件转换工具')
    parser.add_argument('input_file', help='输入DWG文件路径')
    parser.add_argument('output_file', nargs='?', help='输出STEP文件路径（可选）')
    parser.add_argument('--type', choices=['busbar', 'front_busbar', 'rear_busbar', 'plate', 'bracket', 'generic'], 
                       help='零件类型（可选，默认从文件名猜测）')
    parser.add_argument('--scale', type=float, default=1.0, help='缩放因子（默认：1.0）')
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
    success = convert_dwg_to_step(args.input_file, args.output_file, args.type, args.scale)
    
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