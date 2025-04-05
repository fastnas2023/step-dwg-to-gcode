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

# 添加自定义 JSON 编码器，用于处理 NumPy 数据类型
class NumpyEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理NumPy数据类型"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def ensure_json_serializable(obj):
    """确保对象是JSON可序列化的"""
    if isinstance(obj, dict):
        return {k: ensure_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [ensure_json_serializable(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return ensure_json_serializable(obj.tolist())
    else:
        return obj

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
    try:
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
        
        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            print(f"错误: 输入文件不存在 - {input_file}")
            return False
        
        # 1. 解析STEP文件
        print("开始步骤 1: 解析STEP文件")
        processor = NumPyStepProcessor(input_file)
        path, bounds, stats = processor.process()
        
        if path is None:
            print("错误: STEP文件解析失败")
            return False
        
        # 检查路径是否有足够的点
        if len(path) < 2:
            print("错误: 生成的路径点数不足，无法进行加工")
            return False
        
        # 保存解析结果
        np.save(f"{results_dir}/path.npy", path)
        with open(f"{results_dir}/stats.json", 'w') as f:
            # 使用自定义编码器处理NumPy类型
            json.dump(ensure_json_serializable(stats), f, indent=2, cls=NumpyEncoder)
        
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
                    'machining_time_minutes': float(machining_time),
                    'machining_time_seconds': float(machining_time * 60),
                    'feed_rate': float(feed_rate),
                    'points_count': int(len(generator.path)),
                    'gcode_lines': int(len(generator.gcode_lines))
                }, f, indent=2, cls=NumpyEncoder)
        
        # 可视化结果
        if visualize and success:
            visualize_results(processor, generator.path, bounds)
        
        return success
    except Exception as e:
        print(f"STEP转换过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

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
        if processor.points_array is not None and len(processor.points_array) > 0:
            ax.scatter(processor.points_array[:, 0], processor.points_array[:, 1], 
                      processor.points_array[:, 2], c='blue', marker='.', alpha=0.3, label='Points')
        
        # 绘制边
        if processor.edges_array is not None and len(processor.edges_array) > 0:
            for edge in processor.edges_array:
                try:
                    ax.plot([edge[0][0], edge[1][0]], [edge[0][1], edge[1][1]], 
                            [edge[0][2], edge[1][2]], 'green', linewidth=1, alpha=0.5)
                except IndexError:
                    print(f"警告: 跳过无效的边")
                    continue
        
        # 绘制最终路径
        if final_path is not None and len(final_path) > 0:
            ax.plot(final_path[:, 0], final_path[:, 1], final_path[:, 2], 
                   'red', linewidth=2, label='Toolpath')
        
        # 绘制边界盒
        if bounds:
            try:
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
            except (ValueError, TypeError) as e:
                print(f"警告: 无法绘制边界盒 - {str(e)}")
        
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
        if processor.points_array is not None and len(processor.points_array) > 0:
            plt.scatter(processor.points_array[:, 0], processor.points_array[:, 1], 
                      c='blue', marker='.', alpha=0.3, label='Points')
        
        # 绘制边
        if processor.edges_array is not None and len(processor.edges_array) > 0:
            for edge in processor.edges_array:
                try:
                    plt.plot([edge[0][0], edge[1][0]], [edge[0][1], edge[1][1]], 
                            'green', linewidth=1, alpha=0.5)
                except IndexError:
                    continue
        
        # 绘制最终路径
        if final_path is not None and len(final_path) > 0:
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
        
        if processor.contours and len(processor.contours) > 0:
            for i, contour in enumerate(processor.contours):
                try:
                    color = colors[i % len(colors)]
                    plt.plot(contour[:, 0], contour[:, 1], color=color, linewidth=2, 
                            label=f'Contour {i+1}' if i < 8 else None)  # 只显示前8个轮廓标签
                    
                    # 标记轮廓起点
                    plt.scatter(contour[0, 0], contour[0, 1], color=color, s=100, marker='o')
                except (IndexError, ValueError) as e:
                    print(f"警告: 无法绘制轮廓 {i+1} - {str(e)}")
                    continue
        else:
            plt.text(0.5, 0.5, "未找到轮廓", horizontalalignment='center', 
                    verticalalignment='center', transform=plt.gca().transAxes, fontsize=14)
        
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

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='STEP文件到FANUC G代码转换工具 (NumPy优化版)')
    parser.add_argument('input_file', help='输入STEP文件')
    parser.add_argument('-o', '--output-file', help='输出G代码文件')
    parser.add_argument('-f', '--feed-rate', type=float, default=500, help='加工进给率 (mm/min)')
    parser.add_argument('-s', '--safety-height', type=float, default=10.0, help='安全高度 (mm)')
    parser.add_argument('-d', '--cut-depth', type=float, default=0.5, help='每次切削深度 (mm)')
    parser.add_argument('-t', '--tool-diameter', type=float, default=3.0, help='刀具直径 (mm)')
    parser.add_argument('-p', '--program-number', type=int, default=1000, help='程序编号')
    parser.add_argument('-c', '--controller', default='fanuc', choices=['fanuc', 'siemens', 'heidenhain', 'haas'], help='控制器类型')
    parser.add_argument('--no-optimize', action='store_true', help='禁用路径优化')
    parser.add_argument('--no-compensation', action='store_true', help='禁用刀具补偿')
    parser.add_argument('-v', '--visualize', action='store_true', help='生成可视化图表')
    parser.add_argument('--preview-only', action='store_true', help='只生成预览图像，不生成G代码')
    parser.add_argument('--preview-output', help='预览图像的输出路径')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_arguments()
    
    start_time = time()
    
    # 预览模式 - 只生成可视化，不生成G代码
    if args.preview_only:
        try:
            print(f"预览模式: 只生成可视化图表...")
            
            # 解析STEP文件
            processor = NumPyStepProcessor(args.input_file)
            path, bounds, stats = processor.process()
            
            if path is None:
                print("错误: STEP文件解析失败，无法生成预览图像")
                return 1
            
            # 创建图表目录
            output_dir = os.path.dirname(args.preview_output) if args.preview_output else "plots"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 生成预览图像
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            # 绘制原始点
            if processor.points_array is not None and len(processor.points_array) > 0:
                ax.scatter(processor.points_array[:, 0], processor.points_array[:, 1], 
                          processor.points_array[:, 2], c='blue', marker='.', alpha=0.3)
            
            # 绘制边
            if processor.edges_array is not None and len(processor.edges_array) > 0:
                for edge in processor.edges_array:
                    try:
                        ax.plot([edge[0][0], edge[1][0]], [edge[0][1], edge[1][1]], 
                                [edge[0][2], edge[1][2]], 'green', linewidth=1, alpha=0.5)
                    except IndexError:
                        print(f"警告: 跳过无效的边")
                        continue
            
            # 设置图表样式
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            ax.set_title('STEP模型预览')
            
            # 保存预览图片
            output_path = args.preview_output if args.preview_output else "plots/step_preview.png"
            plt.tight_layout()
            plt.savefig(output_path, dpi=300)
            print(f"已生成预览图像: {output_path}")
            
            return 0
        except Exception as e:
            print(f"生成预览图像时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1
    
    # 正常模式 - 完整的转换流程
    success = convert_step_to_gcode(
        input_file=args.input_file,
        output_file=args.output_file,
        feed_rate=args.feed_rate,
        safety_height=args.safety_height,
        cut_depth=args.cut_depth,
        tool_diameter=args.tool_diameter,
        program_number=args.program_number,
        optimize=not args.no_optimize,
        compensation=not args.no_compensation,
        visualize=args.visualize
    )
    
    end_time = time()
    print(f"\n总处理时间: {end_time - start_time:.2f} 秒")
    
    if success:
        print("转换成功完成!")
        return 0
    else:
        print("转换失败!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 