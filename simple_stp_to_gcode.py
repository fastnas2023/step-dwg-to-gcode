#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简易STP文件转G代码转换器
此脚本使用更基本的方法读取STEP文件并生成简单的G代码轮廓
"""

import sys
import os
import argparse
import re
import math
import numpy as np
from time import time

class SimpleStepToGcode:
    def __init__(self, input_file, output_file=None, feed_rate=500, 
                 rapid_feed_rate=1000, safety_height=5.0, cut_depth=0.5, 
                 tool_diameter=3.0):
        """
        初始化简易STEP到G代码转换器
        
        Args:
            input_file (str): 输入STP文件路径
            output_file (str): 输出G代码文件路径
            feed_rate (float): 加工进给率 (mm/min)
            rapid_feed_rate (float): 快速移动进给率 (mm/min)
            safety_height (float): 安全高度 (mm)
            cut_depth (float): 每次切割深度 (mm)
            tool_diameter (float): 刀具直径 (mm)
        """
        self.input_file = input_file
        self.output_file = output_file or self._default_output_file()
        self.feed_rate = feed_rate
        self.rapid_feed_rate = rapid_feed_rate
        self.safety_height = safety_height
        self.cut_depth = cut_depth
        self.tool_diameter = tool_diameter
        
        self.current_z = 0.0
        self.current_x = 0.0
        self.current_y = 0.0
        
        self.gcode_lines = []
        self.vertices = []  # 存储所有顶点坐标
        self.edges = []     # 存储所有边
        self.bounds = None  # 存储边界信息
        
    def _default_output_file(self):
        """为输入文件生成默认的输出文件名"""
        base = os.path.splitext(self.input_file)[0]
        return f"{base}.gcode"
    
    def parse_step_file(self):
        """
        解析STEP文件中的基本几何信息
        
        简化处理，仅提取顶点和简单边
        """
        print(f"正在解析STEP文件: {self.input_file}")
        start_time = time()
        
        # 读取文件内容
        with open(self.input_file, 'r', errors='ignore') as f:
            content = f.read()
        
        # 提取顶点信息 (CARTESIAN_POINT)
        cartesian_point_pattern = r'#(\d+)=CARTESIAN_POINT\(\'.*?\',\((.*?)\)\);'
        point_matches = re.finditer(cartesian_point_pattern, content)
        
        points_dict = {}  # 使用ID作为键存储点
        for match in point_matches:
            point_id = int(match.group(1))
            coords_str = match.group(2)
            # 去除可能的空格，分割坐标
            coords = [float(x.strip()) for x in coords_str.split(',')]
            if len(coords) == 3:  # 确保是3D点
                points_dict[point_id] = coords
                self.vertices.append(coords)
        
        print(f"找到 {len(points_dict)} 个点")
        
        # 提取直线信息 (B_SPLINE_CURVE_WITH_KNOTS 简化为直线)
        line_pattern = r'#\d+=EDGE_CURVE\(\'.*?\',#(\d+),#(\d+),.*?\);'
        line_matches = re.finditer(line_pattern, content)
        
        for match in line_matches:
            start_id = int(match.group(1))
            end_id = int(match.group(2))
            if start_id in points_dict and end_id in points_dict:
                start_point = points_dict[start_id]
                end_point = points_dict[end_id]
                self.edges.append((start_point, end_point))
        
        print(f"找到 {len(self.edges)} 条边")
        
        # 计算边界
        if self.vertices:
            min_x = min(v[0] for v in self.vertices)
            max_x = max(v[0] for v in self.vertices)
            min_y = min(v[1] for v in self.vertices)
            max_y = max(v[1] for v in self.vertices)
            min_z = min(v[2] for v in self.vertices)
            max_z = max(v[2] for v in self.vertices)
            
            self.bounds = (min_x, min_y, min_z, max_x, max_y, max_z)
            print(f"模型边界: X: {min_x:.2f} to {max_x:.2f}, Y: {min_y:.2f} to {max_y:.2f}, Z: {min_z:.2f} to {max_z:.2f}")
        
        print(f"STEP文件解析完成，用时 {time() - start_time:.2f} 秒")

    def extract_contours(self):
        """
        从边中提取轮廓
        简化版本，只是对边进行排序，尝试形成连续路径
        """
        if not self.edges:
            print("警告: 没有找到可处理的边")
            return []
        
        print("正在构建轮廓...")
        start_time = time()
        
        # 创建点到相邻边的映射
        point_to_edges = {}
        for i, (start, end) in enumerate(self.edges):
            # 使用元组作为字典键
            start_tuple = tuple(start)
            end_tuple = tuple(end)
            
            if start_tuple not in point_to_edges:
                point_to_edges[start_tuple] = []
            if end_tuple not in point_to_edges:
                point_to_edges[end_tuple] = []
            
            point_to_edges[start_tuple].append((i, True))  # True表示这是边的起点
            point_to_edges[end_tuple].append((i, False))   # False表示这是边的终点
        
        # 构建轮廓
        contours = []
        used_edges = set()
        
        # 对于每条未使用的边，尝试构建轮廓
        for i in range(len(self.edges)):
            if i in used_edges:
                continue
            
            contour = []
            current_edge_idx = i
            current_point = tuple(self.edges[i][1])  # 从第一条边的终点开始
            contour.append(self.edges[i][0])  # 添加起点
            contour.append(self.edges[i][1])  # 添加终点
            used_edges.add(i)
            
            # 尝试找到连续的边
            found_next = True
            while found_next:
                found_next = False
                if current_point in point_to_edges:
                    for edge_idx, is_start in point_to_edges[current_point]:
                        if edge_idx not in used_edges:
                            used_edges.add(edge_idx)
                            
                            if is_start:
                                # 当前点是下一条边的起点
                                next_point = tuple(self.edges[edge_idx][1])
                                contour.append(self.edges[edge_idx][1])
                            else:
                                # 当前点是下一条边的终点
                                next_point = tuple(self.edges[edge_idx][0])
                                contour.append(self.edges[edge_idx][0])
                            
                            current_point = next_point
                            found_next = True
                            break
            
            if len(contour) > 2:  # 至少需要两个点才能形成有效轮廓
                contours.append(contour)
        
        print(f"构建了 {len(contours)} 个轮廓，用时 {time() - start_time:.2f} 秒")
        return contours

    def write_gcode_header(self):
        """写入G代码文件头"""
        self.gcode_lines.extend([
            "(Generated by Simple STP to G-code Converter)",
            f"(Input file: {self.input_file})",
            f"(Date: {time()})",
            "",
            "G90 ; 绝对坐标模式",
            "G21 ; 使用毫米",
            "G17 ; XY平面选择",
            f"G0 Z{self.safety_height} ; 提升到安全高度",
            "G0 X0 Y0 ; 移动到起始位置",
            ""
        ])

    def write_gcode_footer(self):
        """写入G代码文件尾"""
        self.gcode_lines.extend([
            "",
            f"G0 Z{self.safety_height} ; 提升到安全高度",
            "G0 X0 Y0 ; 返回起始位置",
            "M5 ; 关闭主轴",
            "M30 ; 程序结束"
        ])
    
    def generate_gcode_from_contours(self, contours, z_cut=0.0):
        """
        从轮廓生成G代码
        
        Args:
            contours: 轮廓列表，每个轮廓是一个点的列表
            z_cut: 切割高度
        """
        for contour_idx, contour in enumerate(contours):
            if not contour:
                continue
                
            # 移动到当前轮廓的起点上方
            first_point = contour[0]
            self.gcode_lines.append(f"G0 Z{self.safety_height} ; 提升到安全高度")
            self.gcode_lines.append(f"G0 X{first_point[0]:.4f} Y{first_point[1]:.4f} ; 快速移动到轮廓 {contour_idx+1} 起点")
            self.gcode_lines.append(f"G1 Z{z_cut:.4f} F{self.feed_rate} ; 下降到切割高度")
            
            # 跟踪当前位置
            self.current_x, self.current_y, self.current_z = first_point[0], first_point[1], z_cut
            
            # 沿轮廓移动
            for point in contour[1:]:
                x, y, z = point
                # 简化处理：保持Z高度不变
                self.gcode_lines.append(f"G1 X{x:.4f} Y{y:.4f} F{self.feed_rate} ; 轮廓切割")
                self.current_x, self.current_y = x, y
                
    def convert(self):
        """执行转换过程"""
        try:
            # 解析STEP文件
            self.parse_step_file()
            
            # 如果没有找到顶点或边，则退出
            if not self.vertices or not self.edges:
                print("错误: 无法在STEP文件中找到足够的几何信息")
                return False
            
            # 提取轮廓
            contours = self.extract_contours()
            
            if not contours:
                print("警告: 无法构建有效轮廓")
                # 尝试使用边直接生成路径
                contours = [[edge[0], edge[1]] for edge in self.edges]
            
            # 写入G代码头部
            self.write_gcode_header()
            
            # 为每个切割深度生成G代码
            if self.bounds:
                min_z = self.bounds[2]  # 最小Z值
                max_z = self.bounds[5]  # 最大Z值
                
                # 计算切割层数
                total_depth = max_z - min_z
                num_layers = max(1, math.ceil(total_depth / self.cut_depth))
                
                for layer in range(num_layers):
                    z_cut = max_z - (layer + 1) * self.cut_depth
                    z_cut = max(z_cut, min_z)  # 确保不低于模型底部
                    
                    self.gcode_lines.append(f"(Layer {layer+1}/{num_layers}, Z = {z_cut:.4f})")
                    self.generate_gcode_from_contours(contours, z_cut)
            else:
                # 如果没有边界信息，使用默认切割深度
                self.generate_gcode_from_contours(contours, -self.cut_depth)
            
            # 写入G代码尾部
            self.write_gcode_footer()
            
            # 保存G代码到文件
            with open(self.output_file, 'w') as f:
                f.write('\n'.join(self.gcode_lines))
            
            print(f"G代码已生成并保存到: {self.output_file}")
            print(f"共生成 {len(self.gcode_lines)} 行G代码")
            
            return True
            
        except Exception as e:
            print(f"转换过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    parser = argparse.ArgumentParser(description='将STEP文件转换为G代码（简易版）')
    parser.add_argument('input_file', help='输入STEP文件路径')
    parser.add_argument('-o', '--output', help='输出G代码文件路径')
    parser.add_argument('-f', '--feed-rate', type=float, default=500, help='加工进给率 (mm/min)')
    parser.add_argument('-r', '--rapid-feed-rate', type=float, default=1000, help='快速移动进给率 (mm/min)')
    parser.add_argument('-s', '--safety-height', type=float, default=5.0, help='安全高度 (mm)')
    parser.add_argument('-d', '--cut-depth', type=float, default=0.5, help='每次切割深度 (mm)')
    parser.add_argument('-t', '--tool-diameter', type=float, default=3.0, help='刀具直径 (mm)')
    
    args = parser.parse_args()
    
    converter = SimpleStepToGcode(
        input_file=args.input_file,
        output_file=args.output,
        feed_rate=args.feed_rate,
        rapid_feed_rate=args.rapid_feed_rate,
        safety_height=args.safety_height,
        cut_depth=args.cut_depth,
        tool_diameter=args.tool_diameter
    )
    
    success = converter.convert()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 