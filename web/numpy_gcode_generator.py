#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基于NumPy的FANUC G代码生成器
此脚本将输入的点路径转换为高效的FANUC G代码，利用NumPy进行优化计算
"""

import os
import sys
import argparse
import math
import re
import numpy as np
from time import time

class NumPyFanucGcodeGenerator:
    def __init__(self, output_file=None, feed_rate=500, 
                 rapid_feed_rate=5000, safety_height=10.0, cut_depth=0.5, 
                 tool_diameter=3.0, program_number=1000):
        """
        初始化FANUC G代码生成器
        
        Args:
            output_file (str): 输出G代码文件路径
            feed_rate (float): 加工进给率 (mm/min)
            rapid_feed_rate (float): 快速移动进给率 (mm/min)
            safety_height (float): 安全高度 (mm)
            cut_depth (float): 每次切割深度 (mm)
            tool_diameter (float): 刀具直径 (mm)
            program_number (int): FANUC程序编号
        """
        self.output_file = output_file
        self.feed_rate = feed_rate
        self.rapid_feed_rate = rapid_feed_rate
        self.safety_height = safety_height
        self.cut_depth = cut_depth
        self.tool_diameter = tool_diameter
        self.program_number = program_number
        
        self.current_z = 0.0
        self.current_x = 0.0
        self.current_y = 0.0
        
        self.gcode_lines = []
        self.path = None
        self.bounds = None
    
    def set_path(self, path, bounds=None):
        """
        设置加工路径
        
        Args:
            path (numpy.ndarray): 包含加工路径点的NumPy数组
            bounds (tuple): 可选，模型边界 (min_x, min_y, min_z, max_x, max_y, max_z)
        """
        self.path = path
        self.bounds = bounds
    
    def optimize_path(self):
        """
        优化加工路径以减少加工时间
        
        通过调整路径顺序、合并相邻点等方式优化
        """
        if self.path is None or len(self.path) < 3:
            print("警告: 无法优化路径，点数不足")
            return
        
        print("优化加工路径...")
        start_time = time()
        
        # 1. 移除重复点
        unique_points, unique_indices = np.unique(self.path.round(decimals=3), axis=0, return_index=True)
        if len(unique_points) < len(self.path):
            print(f"移除了 {len(self.path) - len(unique_points)} 个重复点")
            # 保持原始顺序
            sorted_indices = np.sort(unique_indices)
            self.path = self.path[sorted_indices]
        
        # 2. 针对大型路径的优化
        if len(self.path) > 1000:
            # 将路径分割成相邻点块进行处理
            block_size = 500  # 每个块的大小
            num_blocks = math.ceil(len(self.path) / block_size)
            new_path = []
            
            for i in range(num_blocks):
                start_idx = i * block_size
                end_idx = min((i + 1) * block_size, len(self.path))
                block = self.path[start_idx:end_idx]
                
                # 如果不是第一个块，确保与前一个块连接
                if i > 0 and len(new_path) > 0:
                    # 寻找块中距离前一块最后一点最近的点
                    last_point = new_path[-1]
                    distances = np.sum((block - last_point) ** 2, axis=1)
                    nearest_idx = np.argmin(distances)
                    
                    # 重新排序块中的点，从最近点开始
                    new_block = np.vstack([block[nearest_idx:], block[:nearest_idx]])
                    new_path.append(new_block)
                else:
                    new_path.append(block)
            
            # 合并所有块
            self.path = np.vstack(new_path)
        
        print(f"路径优化完成，用时 {time() - start_time:.2f} 秒")
    
    def apply_tool_compensation(self):
        """
        应用刀具半径补偿
        
        根据刀具直径计算实际加工路径
        """
        if self.path is None or len(self.path) < 3:
            print("警告: 无法应用刀具补偿，点数不足")
            return
        
        if self.tool_diameter <= 0:
            return  # 不需要补偿
        
        print("应用刀具半径补偿...")
        start_time = time()
        
        # 刀具半径
        radius = self.tool_diameter / 2.0
        
        # 创建新路径数组
        compensated_path = np.zeros_like(self.path)
        
        # 对每个点计算法向量并应用补偿
        for i in range(len(self.path)):
            prev_i = (i - 1) % len(self.path)
            next_i = (i + 1) % len(self.path)
            
            # 计算前后向量
            prev_vec = self.path[i] - self.path[prev_i]
            next_vec = self.path[next_i] - self.path[i]
            
            # 检查向量是否为零向量
            prev_vec_mag = np.linalg.norm(prev_vec)
            next_vec_mag = np.linalg.norm(next_vec)
            
            # 防止除以零，如果向量太小，使用默认值
            if prev_vec_mag < 1e-6 or next_vec_mag < 1e-6:
                # 复制原始点
                compensated_path[i] = self.path[i]
                continue
            
            # 归一化
            prev_vec_norm = prev_vec / prev_vec_mag
            next_vec_norm = next_vec / next_vec_mag
            
            # 计算法向量 (2D平面内，假设Z轴不变)
            prev_normal = np.array([-prev_vec_norm[1], prev_vec_norm[0], 0])
            next_normal = np.array([-next_vec_norm[1], next_vec_norm[0], 0])
            
            # 平均法向量
            avg_normal = (prev_normal + next_normal) / 2
            avg_normal_mag = np.linalg.norm(avg_normal)
            
            # 防止除以零
            if avg_normal_mag < 1e-6:
                # 使用其中一个法向量
                if np.linalg.norm(prev_normal) > 1e-6:
                    avg_normal = prev_normal
                elif np.linalg.norm(next_normal) > 1e-6:
                    avg_normal = next_normal
                else:
                    # 如果无法计算法向量，保持原点不变
                    compensated_path[i] = self.path[i]
                    continue
                
                avg_normal_mag = np.linalg.norm(avg_normal)
                if avg_normal_mag < 1e-6:
                    # 仍然是零向量，保持原点不变
                    compensated_path[i] = self.path[i]
                    continue
            
            # 归一化平均法向量
            avg_normal = avg_normal / avg_normal_mag
            
            # 应用补偿 (向外偏移)
            compensated_path[i] = self.path[i] + radius * avg_normal
        
        # 检查并清理NaN值
        nan_mask = np.isnan(compensated_path).any(axis=1)
        if np.any(nan_mask):
            print(f"警告: 发现 {np.sum(nan_mask)} 个无效点，使用原始点代替")
            compensated_path[nan_mask] = self.path[nan_mask]
        
        self.path = compensated_path
        print(f"刀具补偿完成，用时 {time() - start_time:.2f} 秒")
    
    def write_fanuc_header(self):
        """写入FANUC G代码文件头"""
        self.gcode_lines.extend([
            f"O{self.program_number}",
            "(FANUC G-CODE GENERATED BY NUMPY PROCESSOR)",
            f"(DATE: {time()})",
            "",
            "G0 G17 G40 G49 G80 G90",  # 标准FANUC启动行
            "G21",  # 毫米单位
            "G91 G28 Z0",  # 回参考点
            "G91 G28 X0 Y0",  # 回参考点
            "G90",  # 绝对坐标
            "M6 T1",  # 换刀
            "M3 S3000",  # 启动主轴 3000转
            f"G0 X0 Y0 Z{self.safety_height}",  # 移动到起点上方
            ""
        ])

    def write_fanuc_footer(self):
        """写入FANUC G代码文件尾"""
        self.gcode_lines.extend([
            "",
            f"G0 Z{self.safety_height}",  # 提升到安全高度
            "G91 G28 Z0",  # Z轴回参考点
            "G91 G28 X0 Y0",  # XY轴回参考点
            "G90",  # 绝对坐标
            "M5",  # 停止主轴
            "M30",  # 程序结束
            "%"  # FANUC程序尾
        ])
    
    def generate_gcode(self):
        """生成G代码"""
        if self.path is None or len(self.path) == 0:
            print("错误: 无法生成G代码，未设置路径")
            return False
        
        print("生成FANUC G代码...")
        start_time = time()
        
        # 写入G代码头部
        self.write_fanuc_header()
        
        # 计算Z轴切削深度
        if self.bounds:
            min_z = self.bounds[2]  # 模型最小Z值
            max_z = self.bounds[5]  # 模型最大Z值
            
            # 计算切割层数
            total_depth = max_z - min_z
            num_layers = max(1, math.ceil(total_depth / self.cut_depth))
            
            # 使用NumPy向量化处理每一层
            for layer in range(num_layers):
                z_cut = max_z - (layer + 1) * self.cut_depth
                z_cut = max(z_cut, min_z)  # 确保不低于模型底部
                
                self.gcode_lines.append(f"(LAYER {layer+1}/{num_layers}, Z = {z_cut:.3f})")
                self.gcode_lines.append(f"G0 Z{self.safety_height}")
                
                # 移动到第一个点
                first_point = self.path[0]
                self.gcode_lines.append(f"G0 X{first_point[0]:.3f} Y{first_point[1]:.3f}")
                self.gcode_lines.append(f"G1 Z{z_cut:.3f} F{self.feed_rate}")
                
                # 优化：使用NumPy批量生成G代码行
                # 每100点生成一批，以平衡内存使用和效率
                batch_size = 100
                for i in range(0, len(self.path), batch_size):
                    batch = self.path[i:i+batch_size]
                    # 格式化为G代码行
                    gcode_batch = [f"G1 X{p[0]:.3f} Y{p[1]:.3f} F{self.feed_rate}" for p in batch]
                    self.gcode_lines.extend(gcode_batch)
        else:
            # 如果没有边界信息，使用默认切割深度
            z_cut = -self.cut_depth
            self.gcode_lines.append(f"G0 Z{self.safety_height}")
            
            # 移动到第一个点
            first_point = self.path[0]
            self.gcode_lines.append(f"G0 X{first_point[0]:.3f} Y{first_point[1]:.3f}")
            self.gcode_lines.append(f"G1 Z{z_cut:.3f} F{self.feed_rate}")
            
            # 生成加工路径的G代码
            for point in self.path[1:]:
                self.gcode_lines.append(f"G1 X{point[0]:.3f} Y{point[1]:.3f} F{self.feed_rate}")
        
        # 写入G代码尾部
        self.write_fanuc_footer()
        
        # 保存G代码到文件
        if self.output_file:
            with open(self.output_file, 'w') as f:
                f.write('\n'.join(self.gcode_lines))
            
            print(f"FANUC G代码已生成并保存到: {self.output_file}")
        
        print(f"共生成 {len(self.gcode_lines)} 行G代码，用时 {time() - start_time:.2f} 秒")
        return True
    
    def estimate_machining_time(self):
        """估算加工时间"""
        if not self.gcode_lines:
            print("警告: 无法估算加工时间，G代码未生成")
            return 0
        
        print("估算加工时间...")
        
        total_distance = 0.0
        rapid_distance = 0.0
        cutting_distance = 0.0
        
        current_pos = np.array([0.0, 0.0, 0.0])
        current_feed = self.rapid_feed_rate
        
        for line in self.gcode_lines:
            # 提取坐标和进给率
            x, y, z = current_pos
            f = current_feed
            
            # 解析G代码行
            if "G0" in line or "G1" in line:
                # 提取坐标
                if "X" in line:
                    x_match = re.search(r'X([-+]?\d*\.?\d+)', line)
                    if x_match:
                        x = float(x_match.group(1))
                
                if "Y" in line:
                    y_match = re.search(r'Y([-+]?\d*\.?\d+)', line)
                    if y_match:
                        y = float(y_match.group(1))
                
                if "Z" in line:
                    z_match = re.search(r'Z([-+]?\d*\.?\d+)', line)
                    if z_match:
                        z = float(z_match.group(1))
                
                if "F" in line:
                    f_match = re.search(r'F([-+]?\d*\.?\d+)', line)
                    if f_match:
                        f = float(f_match.group(1))
                
                # 计算移动距离
                new_pos = np.array([x, y, z])
                distance = np.linalg.norm(new_pos - current_pos)
                
                # 更新总距离
                if "G0" in line:
                    rapid_distance += distance
                    current_feed = self.rapid_feed_rate
                else:  # G1
                    cutting_distance += distance
                    current_feed = f
                
                total_distance += distance
                current_pos = new_pos
        
        # 估算加工时间（分钟）
        rapid_time = rapid_distance / self.rapid_feed_rate
        cutting_time = cutting_distance / self.feed_rate
        total_time = rapid_time + cutting_time
        
        print(f"估算结果:")
        print(f"  总距离: {total_distance:.2f} mm")
        print(f"  快速移动距离: {rapid_distance:.2f} mm")
        print(f"  切削距离: {cutting_distance:.2f} mm")
        print(f"  快速移动时间: {rapid_time*60:.1f} 秒")
        print(f"  切削时间: {cutting_time*60:.1f} 秒")
        print(f"  总加工时间: {total_time*60:.1f} 秒 (约 {total_time:.2f} 分钟)")
        
        return total_time

def main():
    parser = argparse.ArgumentParser(description='使用NumPy生成FANUC G代码')
    parser.add_argument('input_file', help='输入JSON或NumPy数组文件')
    parser.add_argument('-o', '--output', help='输出G代码文件路径')
    parser.add_argument('-f', '--feed-rate', type=float, default=500, help='加工进给率 (mm/min)')
    parser.add_argument('-r', '--rapid-feed-rate', type=float, default=5000, help='快速移动进给率 (mm/min)')
    parser.add_argument('-s', '--safety-height', type=float, default=10.0, help='安全高度 (mm)')
    parser.add_argument('-d', '--cut-depth', type=float, default=0.5, help='每次切割深度 (mm)')
    parser.add_argument('-t', '--tool-diameter', type=float, default=3.0, help='刀具直径 (mm)')
    parser.add_argument('-p', '--program-number', type=int, default=1000, help='FANUC程序编号')
    parser.add_argument('--no-optimize', action='store_true', help='禁用路径优化')
    parser.add_argument('--no-compensation', action='store_true', help='禁用刀具补偿')
    
    args = parser.parse_args()
    
    # 加载输入数据
    input_file = args.input_file
    if input_file.endswith('.json'):
        import json
        with open(input_file, 'r') as f:
            data = json.load(f)
        # 将路径数据转换为NumPy数组
        if 'path' in data:
            path = np.array(data['path'])
        else:
            print("错误: JSON文件中缺少路径数据")
            return 1
        
        bounds = None
        if 'bounds' in data:
            b = data['bounds']
            bounds = (b['min_x'], b['min_y'], b['min_z'], b['max_x'], b['max_y'], b['max_z'])
    elif input_file.endswith('.npy'):
        # 直接加载NumPy数组
        path = np.load(input_file)
        bounds = None
    else:
        print(f"错误: 不支持的输入文件格式: {input_file}")
        return 1
    
    # 检查路径数据
    if path is None or len(path) < 2:
        print("错误: 无效的路径数据")
        return 1
    
    # 创建G代码生成器
    generator = NumPyFanucGcodeGenerator(
        output_file=args.output,
        feed_rate=args.feed_rate,
        rapid_feed_rate=args.rapid_feed_rate,
        safety_height=args.safety_height,
        cut_depth=args.cut_depth,
        tool_diameter=args.tool_diameter,
        program_number=args.program_number
    )
    
    # 设置路径
    generator.set_path(path, bounds)
    
    # 优化路径（如果需要）
    if not args.no_optimize:
        generator.optimize_path()
    
    # 应用刀具补偿（如果需要）
    if not args.no_compensation:
        generator.apply_tool_compensation()
    
    # 生成G代码
    success = generator.generate_gcode()
    
    if success:
        # 估算加工时间
        generator.estimate_machining_time()
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main()) 