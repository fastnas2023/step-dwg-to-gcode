#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
STEP到FANUC G代码转换器 (NumPy优化版)
此脚本将STEP文件转换为FANUC CNC控制器兼容的G代码
"""

import os
import sys
import argparse
import time
import platform
import traceback

# 根据平台决定使用哪个处理器
system_platform = platform.machine().lower()

try:
    if system_platform in ('aarch64', 'arm64'):
        # ARM架构使用简化版处理器
        print("检测到ARM架构，使用简化版STEP处理器")
        from step_processor_fallback import SimpleStepProcessor as StepProcessor
    else:
        # x86架构使用完整版处理器
        from numpy_step_processor import NumPyStepProcessor as StepProcessor
except ImportError as e:
    # 如果导入失败，总是回退到简化版处理器
    print(f"导入处理器失败: {e}")
    print("回退到简化版STEP处理器")
    from step_processor_fallback import SimpleStepProcessor as StepProcessor

def convert_step_to_gcode(input_file, output_file=None, 
                        feed_rate=500, rapid_height=10.0, 
                        cut_depth=5.0, tool_diameter=0,
                        preview_only=False, preview_output=None,
                        verbose=False):
    """
    将STEP文件转换为G代码
    
    Args:
        input_file (str): 输入STEP文件路径
        output_file (str): 输出G代码文件路径
        feed_rate (float): 进给速率 (毫米/分钟)
        rapid_height (float): 快速移动高度 (毫米)
        cut_depth (float): 切削深度 (毫米)
        tool_diameter (float): 刀具直径 (毫米)
        preview_only (bool): 是否仅生成预览图
        preview_output (str): 预览图输出路径
        verbose (bool): 是否显示详细输出
    
    Returns:
        bool: 操作是否成功
    """
    start_time = time.time()
    
    if verbose:
        print(f"正在处理STEP文件: {input_file}")
        
    # 默认输出文件名
    if output_file is None and not preview_only:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.nc"
    
    try:
        # 初始化处理器
        processor = StepProcessor(input_file)
        
        # 进行处理
        if preview_only:
            result, preview_path, stats = processor.process(preview_only=True, preview_output=preview_output)
            if result:
                if verbose:
                    print(f"预览图已生成: {preview_path}")
                    print(f"模型信息: {stats['points']} 个点, {stats['edges']} 条边")
                return True
            else:
                print("生成预览图失败")
                return False
        else:
            # 完整处理流程，生成G代码
            path, bounds, stats = processor.process()
            
            if path is None or bounds is None:
                print("处理STEP文件失败，无法生成G代码")
                return False
            
            # 生成G代码
            if verbose:
                print(f"正在生成G代码到: {output_file}")
            
            with open(output_file, 'w') as f:
                # G代码头部
                f.write("%\n")
                f.write("O1000 (STEP to FANUC G-code)\n")
                f.write(f"(Generated from {os.path.basename(input_file)})\n")
                f.write(f"(Date: {time.strftime('%Y-%m-%d %H:%M:%S')})\n")
                f.write(f"(Points: {stats['points']}, Edges: {stats['edges']})\n")
                f.write(f"(Bounds: X{bounds[0]:.3f} to {bounds[3]:.3f}, Y{bounds[1]:.3f} to {bounds[4]:.3f}, Z{bounds[2]:.3f} to {bounds[5]:.3f})\n")
                f.write("\n")
                
                # 设置
                f.write("G21 G90 G40\n")  # 毫米单位，绝对坐标，取消刀具补偿
                f.write("G17\n")          # XY平面
                f.write(f"F{feed_rate}\n")# 设置进给速率
                f.write("G54\n")          # 工件坐标系
                f.write("\n")
                
                # 程序主体
                f.write("(--- 程序开始 ---)\n")
                f.write("M3 S1000\n")     # 主轴开启，速度1000
                f.write(f"G0 Z{rapid_height:.3f}\n") # 快速移动到安全高度
                
                # 计算Z轴工作高度
                z_work = bounds[2] - cut_depth if bounds[2] > cut_depth else -cut_depth
                
                # 写入轮廓路径
                first_point = True
                
                # 使用点集生成路径
                for i, point in enumerate(path):
                    x, y = point[0], point[1]
                    
                    if first_point:
                        # 对于第一个点，快速移动到位置，然后下降到工作高度
                        f.write(f"G0 X{x:.3f} Y{y:.3f}\n")
                        f.write(f"G1 Z{z_work:.3f}\n")
                        first_point = False
                    else:
                        # 沿轮廓线性移动
                        f.write(f"G1 X{x:.3f} Y{y:.3f}\n")
                
                # 程序结束
                f.write(f"G0 Z{rapid_height:.3f}\n") # 快速移动到安全高度
                f.write("M5\n")         # 主轴关闭
                f.write("M30\n")        # 程序结束
                f.write("%\n")          # 文件结束
            
            elapsed_time = time.time() - start_time
            if verbose:
                print(f"G代码生成完成，用时 {elapsed_time:.2f} 秒")
                print(f"输出文件: {output_file}")
            
            return True
            
    except Exception as e:
        print(f"错误: {str(e)}")
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='将STEP文件转换为FANUC G代码')
    parser.add_argument('input_file', help='输入STEP文件路径')
    parser.add_argument('-o', '--output', help='输出G代码文件路径')
    parser.add_argument('-f', '--feed-rate', type=float, default=500, help='进给速率 (mm/min)')
    parser.add_argument('-r', '--rapid-height', type=float, default=10.0, help='快速移动高度 (mm)')
    parser.add_argument('-d', '--cut-depth', type=float, default=5.0, help='切削深度 (mm)')
    parser.add_argument('-t', '--tool-diameter', type=float, default=0, help='刀具直径 (mm)')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细输出')
    parser.add_argument('--preview-only', action='store_true', help='仅生成预览图，不生成G代码')
    parser.add_argument('--preview-output', help='预览图输出路径')
    
    args = parser.parse_args()
    
    result = convert_step_to_gcode(
        input_file=args.input_file,
        output_file=args.output,
        feed_rate=args.feed_rate,
        rapid_height=args.rapid_height,
        cut_depth=args.cut_depth,
        tool_diameter=args.tool_diameter,
        preview_only=args.preview_only,
        preview_output=args.preview_output,
        verbose=args.verbose
    )
    
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    main() 