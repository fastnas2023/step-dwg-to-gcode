#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
STEP文件到FANUC G代码转换器 (NumPy优化版本)
此脚本集成了优化的STEP解析和G代码生成，利用NumPy提高效率
"""

import os
import sys
import argparse
import numpy as np
from time import time
import json
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from numpy_step_processor import NumPyStepProcessor
from numpy_gcode_generator import NumPyFanucGcodeGenerator

def convert_step_to_gcode(input_file, output_file=None, feed_rate=500, 
                         rapid_feed_rate=5000, safety_height=10.0, cut_depth=0.5, 
                         tool_diameter=3.0, program_number=1000, 
                         optimize=True, compensation=True, visualize=False):
    """
    转换STEP文件为FANUC G代码
    
    Args:
        input_file (str): 输入STEP文件路径
        output_file (str): 输出G代码文件路径
        feed_rate (float): 加工进给率 (mm/min)
        rapid_feed_rate (float): 快速移动进给率 (mm/min)
        safety_height (float): 安全高度 (mm)
        cut_depth (float): 每次切割深度 (mm)
        tool_diameter (float): 刀具直径 (mm)
        program_number (int): FANUC程序编号
        optimize (bool): 是否优化路径
        compensation (bool): 是否应用刀具补偿
        visualize (bool): 是否可视化处理结果
    
    Returns:
        bool: 转换是否成功
    """
    # 设置默认输出文件
    if output_file is None:
        base = os.path.splitext(input_file)[0]
        output_file = f"{base}_fanuc_numpy.nc"
    
    # 创建中间结果目录
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    print(f"=============== NumPy优化版STEP到FANUC G代码转换器 ===============")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print(f"=====================================================\n")
    
    # 1. 解析STEP文件
    print("开始步骤 1: 解析STEP文件")
    processor = NumPyStepProcessor(input_file)
    path, bounds, stats = processor.process()
    
    if path is None:
        print("错误: STEP文件解析失败")
        return False
    
    # 保存解析结果
    np.save(f"{results_dir}/path.npy", path)
    with open(f"{results_dir}/stats.json", 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("\n解析统计信息:")
    for category, values in stats.items():
        print(f"  {category}:")
        for key, value in values.items():
            print(f"    {key}: {value}")
    
    # 2. 生成G代码
    print("\n开始步骤 2: 生成G代码")
    generator = NumPyFanucGcodeGenerator(
        output_file=output_file,
        feed_rate=feed_rate,
        rapid_feed_rate=rapid_feed_rate,
        safety_height=safety_height,
        cut_depth=cut_depth,
        tool_diameter=tool_diameter,
        program_number=program_number
    )
    
    # 设置路径
    generator.set_path(path, bounds)
    
    # 优化路径
    if optimize:
        generator.optimize_path()
        # 保存优化后的路径
        np.save(f"{results_dir}/optimized_path.npy", generator.path)
    
    # 应用刀具补偿
    if compensation:
        generator.apply_tool_compensation()
        # 保存补偿后的路径
        np.save(f"{results_dir}/compensated_path.npy", generator.path)
    
    # 生成G代码
    success = generator.generate_gcode()
    
    if success:
        # 估算加工时间
        machining_time = generator.estimate_machining_time()
        
        # 保存加工时间估算
        with open(f"{results_dir}/machining_info.json", 'w') as f:
            json.dump({
                'input_file': input_file,
                'output_file': output_file,
                'machining_time_minutes': machining_time,
                'machining_time_seconds': machining_time * 60,
                'feed_rate': feed_rate,
                'points_count': len(generator.path),
                'gcode_lines': len(generator.gcode_lines)
            }, f, indent=2)
    
    # 可视化结果
    if visualize and success:
        visualize_results(processor, generator.path, bounds)
    
    return success

def visualize_results(processor, final_path, bounds):
    """可视化解析和处理结果"""
    try:
        print("\n生成可视化图表...")
        
        # 创建图表文件夹
        plots_dir = "plots"
        if not os.path.exists(plots_dir):
            os.makedirs(plots_dir)
        
        # 1. 绘制3D视图
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # 绘制原始点
        if processor.points_array is not None:
            ax.scatter(processor.points_array[:, 0], processor.points_array[:, 1], 
                      processor.points_array[:, 2], c='blue', marker='.', alpha=0.3, label='Points')
        
        # 绘制边
        if processor.edges_array is not None:
            for edge in processor.edges_array:
                ax.plot([edge[0][0], edge[1][0]], [edge[0][1], edge[1][1]], 
                        [edge[0][2], edge[1][2]], 'green', linewidth=1, alpha=0.5)
        
        # 绘制最终路径
        if final_path is not None:
            ax.plot(final_path[:, 0], final_path[:, 1], final_path[:, 2], 
                   'red', linewidth=2, label='Toolpath')
        
        # 绘制边界盒
        if bounds:
            min_x, min_y, min_z, max_x, max_y, max_z = bounds
            vertices = [
                [min_x, min_y, min_z], [max_x, min_y, min_z], [max_x, max_y, min_z], [min_x, max_y, min_z],
                [min_x, min_y, max_z], [max_x, min_y, max_z], [max_x, max_y, max_z], [min_x, max_y, max_z]
            ]
            edges = [
                [0, 1], [1, 2], [2, 3], [3, 0],  # 底面
                [4, 5], [5, 6], [6, 7], [7, 4],  # 顶面
                [0, 4], [1, 5], [2, 6], [3, 7]   # 连接边
            ]
            for edge in edges:
                v1, v2 = vertices[edge[0]], vertices[edge[1]]
                ax.plot([v1[0], v2[0]], [v1[1], v2[1]], [v1[2], v2[2]], 
                       'black', linewidth=1, linestyle=':', alpha=0.5)
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('3D Model and Toolpath')
        ax.legend()
        plt.tight_layout()
        plt.savefig(f"plots/3d_model.png", dpi=300)
        
        # 2. 绘制2D XY平面视图
        plt.figure(figsize=(10, 8))
        
        # 绘制原始点
        if processor.points_array is not None:
            plt.scatter(processor.points_array[:, 0], processor.points_array[:, 1], 
                      c='blue', marker='.', alpha=0.3, label='Points')
        
        # 绘制边
        if processor.edges_array is not None:
            for edge in processor.edges_array:
                plt.plot([edge[0][0], edge[1][0]], [edge[0][1], edge[1][1]], 
                        'green', linewidth=1, alpha=0.5)
        
        # 绘制最终路径
        if final_path is not None:
            plt.plot(final_path[:, 0], final_path[:, 1], 'red', linewidth=2, label='Toolpath')
            # 标记起点和终点
            plt.scatter(final_path[0, 0], final_path[0, 1], color='magenta', s=100, label='Start')
            plt.scatter(final_path[-1, 0], final_path[-1, 1], color='purple', s=100, label='End')
        
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.title('XY Plane Projection')
        plt.grid(True)
        plt.legend()
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(f"plots/xy_projection.png", dpi=300)
        
        # 3. 绘制轮廓
        plt.figure(figsize=(10, 8))
        
        # 为每个轮廓使用不同颜色
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive']
        
        for i, contour in enumerate(processor.contours):
            color = colors[i % len(colors)]
            plt.plot(contour[:, 0], contour[:, 1], color=color, linewidth=2, 
                    label=f'Contour {i+1}' if i < 8 else None)  # 只显示前8个轮廓标签
            
            # 标记轮廓起点
            plt.scatter(contour[0, 0], contour[0, 1], color=color, s=100, marker='o')
        
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.title('Extracted Contours')
        plt.grid(True)
        plt.legend()
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(f"plots/contours.png", dpi=300)
        
        print(f"可视化图表已保存到 {plots_dir}/ 目录")
        
    except Exception as e:
        print(f"可视化生成过程中出错: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='将STEP文件转换为FANUC G代码 (NumPy优化版本)')
    parser.add_argument('input_file', help='输入STEP文件路径')
    parser.add_argument('-o', '--output', help='输出G代码文件路径')
    parser.add_argument('-f', '--feed-rate', type=float, default=500, help='加工进给率 (mm/min)')
    parser.add_argument('-r', '--rapid-feed-rate', type=float, default=5000, help='快速移动进给率 (mm/min)')
    parser.add_argument('-s', '--safety-height', type=float, default=10.0, help='安全高度 (mm)')
    parser.add_argument('-d', '--cut-depth', type=float, default=0.5, help='每次切割深度 (mm)')
    parser.add_argument('-t', '--tool-diameter', type=float, default=3.0, help='刀具直径 (mm)')
    parser.add_argument('-p', '--program-number', type=int, default=1000, help='FANUC程序编号')
    parser.add_argument('--no-optimize', action='store_true', help='禁用路径优化')
    parser.add_argument('--no-compensation', action='store_true', help='禁用刀具补偿')
    parser.add_argument('-v', '--visualize', action='store_true', help='可视化处理结果')
    
    args = parser.parse_args()
    
    success = convert_step_to_gcode(
        input_file=args.input_file,
        output_file=args.output,
        feed_rate=args.feed_rate,
        rapid_feed_rate=args.rapid_feed_rate,
        safety_height=args.safety_height,
        cut_depth=args.cut_depth,
        tool_diameter=args.tool_diameter,
        program_number=args.program_number,
        optimize=not args.no_optimize,
        compensation=not args.no_compensation,
        visualize=args.visualize
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 