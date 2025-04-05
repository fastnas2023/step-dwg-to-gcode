#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用steputils库的STP文件转G代码转换器
此脚本使用steputils库读取STEP文件并生成G代码
"""

import sys
import os
import argparse
import math
import numpy as np
from time import time
from collections import defaultdict

try:
    import steputils.step as step
    from steputils.geomdl import BSpline
    from steputils.geomdl import utilities as utils
except ImportError:
    print("错误: 需要安装steputils库")
    print("安装命令: pip install steputils")
    sys.exit(1)

class StepToGcode:
    def __init__(self, input_file, output_file=None, feed_rate=500, 
                 rapid_feed_rate=1000, safety_height=5.0, cut_depth=0.5, 
                 tool_diameter=3.0, xy_tolerance=0.01, spline_samples=50):
        """
        初始化STEP到G代码转换器
        
        Args:
            input_file (str): 输入STP文件路径
            output_file (str): 输出G代码文件路径
            feed_rate (float): 加工进给率 (mm/min)
            rapid_feed_rate (float): 快速移动进给率 (mm/min)
            safety_height (float): 安全高度 (mm)
            cut_depth (float): 每次切割深度 (mm)
            tool_diameter (float): 刀具直径 (mm)
            xy_tolerance (float): XY平面公差 (mm)
            spline_samples (int): 样条曲线采样点数
        """
        self.input_file = input_file
        self.output_file = output_file or self._default_output_file()
        self.feed_rate = feed_rate
        self.rapid_feed_rate = rapid_feed_rate
        self.safety_height = safety_height
        self.cut_depth = cut_depth
        self.tool_diameter = tool_diameter
        self.xy_tolerance = xy_tolerance
        self.spline_samples = spline_samples
        
        self.current_z = 0.0
        self.current_x = 0.0
        self.current_y = 0.0
        
        self.gcode_lines = []
        self.points = {}  # 存储STEP文件中的点
        self.curves = []  # 存储STEP文件中的曲线
        self.bounds = None
        
        self.step_file = None
        
    def _default_output_file(self):
        """为输入文件生成默认的输出文件名"""
        base = os.path.splitext(self.input_file)[0]
        return f"{base}.gcode"
    
    def load_step_file(self):
        """加载并解析STEP文件"""
        print(f"正在加载STEP文件: {self.input_file}")
        start_time = time()
        
        try:
            self.step_file = step.readfile(self.input_file)
            print(f"STEP文件加载完成，用时 {time() - start_time:.2f} 秒")
            return True
        except Exception as e:
            print(f"加载STEP文件时出错: {e}")
            return False
    
    def extract_geometry(self):
        """从STEP文件中提取几何信息"""
        if not self.step_file:
            return False
        
        print("正在提取几何信息...")
        start_time = time()
        
        # 收集所有的点
        print("提取点数据...")
        cartesian_points = self.step_file.find_all_entities_by_type('CARTESIAN_POINT')
        for point in cartesian_points:
            try:
                point_id = point.id
                # 坐标可能在XYZ或XY格式
                if len(point.params) >= 3 and isinstance(point.params, list):
                    coords = [float(x) if isinstance(x, (int, float)) else float(x.val) for x in point.params]
                    if len(coords) >= 3:  # 确保有X,Y,Z坐标
                        self.points[point_id] = coords[:3]
            except (ValueError, AttributeError, IndexError) as e:
                # 跳过无法处理的点
                continue
        
        print(f"找到 {len(self.points)} 个点")
        
        # 收集所有的曲线
        print("提取曲线数据...")
        curve_types = ['LINE', 'CIRCLE', 'B_SPLINE_CURVE']
        
        for curve_type in curve_types:
            curves = self.step_file.find_all_entities_by_type(curve_type)
            for curve in curves:
                try:
                    if curve_type == 'LINE':
                        # 直线由起点和方向定义
                        point_id = self._get_referenced_entity_id(curve, 'CARTESIAN_POINT')
                        direction_id = self._get_referenced_entity_id(curve, 'DIRECTION')
                        
                        if point_id in self.points:
                            self.curves.append({
                                'type': 'LINE',
                                'start_point': self.points[point_id],
                                'direction': self._get_direction(direction_id),
                                'id': curve.id
                            })
                    
                    elif curve_type == 'CIRCLE':
                        # 圆由圆心和半径定义
                        placement_id = self._get_referenced_entity_id(curve, 'AXIS2_PLACEMENT_3D')
                        radius = float(curve.params[-1].val) if hasattr(curve.params[-1], 'val') else float(curve.params[-1])
                        
                        if placement_id:
                            center = self._get_placement_location(placement_id)
                            if center:
                                self.curves.append({
                                    'type': 'CIRCLE',
                                    'center': center,
                                    'radius': radius,
                                    'id': curve.id
                                })
                    
                    elif curve_type == 'B_SPLINE_CURVE':
                        # B样条曲线由控制点和度定义
                        degree = int(curve.params[0].val) if hasattr(curve.params[0], 'val') else int(curve.params[0])
                        control_points_refs = []
                        
                        # 找出控制点引用
                        for param in curve.params:
                            if isinstance(param, list):
                                for item in param:
                                    if isinstance(item, step.Entity) and item.type == 'CARTESIAN_POINT':
                                        control_points_refs.append(item.id)
                        
                        control_points = []
                        for ref in control_points_refs:
                            if ref in self.points:
                                control_points.append(self.points[ref])
                        
                        if control_points:
                            self.curves.append({
                                'type': 'B_SPLINE_CURVE',
                                'degree': degree,
                                'control_points': control_points,
                                'id': curve.id
                            })
                except Exception as e:
                    # 跳过无法处理的曲线
                    continue
        
        print(f"找到 {len(self.curves)} 条曲线")
        
        # 计算边界
        if self.points:
            all_points = list(self.points.values())
            x_values = [p[0] for p in all_points]
            y_values = [p[1] for p in all_points]
            z_values = [p[2] for p in all_points]
            
            min_x, max_x = min(x_values), max(x_values)
            min_y, max_y = min(y_values), max(y_values)
            min_z, max_z = min(z_values), max(z_values)
            
            self.bounds = (min_x, min_y, min_z, max_x, max_y, max_z)
            print(f"模型边界: X: {min_x:.2f} to {max_x:.2f}, Y: {min_y:.2f} to {max_y:.2f}, Z: {min_z:.2f} to {max_z:.2f}")
        
        print(f"几何信息提取完成，用时 {time() - start_time:.2f} 秒")
        return True
    
    def _get_referenced_entity_id(self, entity, entity_type):
        """获取实体引用的特定类型的实体ID"""
        for param in entity.params:
            if isinstance(param, step.Entity) and param.type == entity_type:
                return param.id
        return None
    
    def _get_direction(self, direction_id):
        """获取方向向量"""
        if not direction_id:
            return [1, 0, 0]  # 默认X轴方向
        
        direction = self.step_file.find_entity_by_id(direction_id)
        if direction and direction.type == 'DIRECTION':
            try:
                dir_values = []
                for value in direction.params:
                    if isinstance(value, (int, float)):
                        dir_values.append(float(value))
                    elif hasattr(value, 'val'):
                        dir_values.append(float(value.val))
                
                if len(dir_values) >= 3:
                    return dir_values[:3]
            except:
                pass
        
        return [1, 0, 0]  # 默认X轴方向
    
    def _get_placement_location(self, placement_id):
        """获取AXIS2_PLACEMENT_3D的位置"""
        placement = self.step_file.find_entity_by_id(placement_id)
        if placement and placement.type == 'AXIS2_PLACEMENT_3D':
            # 位置通常是第一个参数，是对CARTESIAN_POINT的引用
            point_id = self._get_referenced_entity_id(placement, 'CARTESIAN_POINT')
            if point_id in self.points:
                return self.points[point_id]
        
        return None
    
    def generate_toolpaths(self):
        """生成刀具路径"""
        print("正在生成刀具路径...")
        toolpaths = []
        
        for curve in self.curves:
            if curve['type'] == 'LINE':
                # 生成直线的离散点
                start = curve['start_point']
                direction = curve['direction']
                # 为简化，我们假设直线长度为100，然后生成两个点
                end = [start[i] + direction[i] * 100 for i in range(3)]
                toolpaths.append([start, end])
            
            elif curve['type'] == 'CIRCLE':
                # 生成圆的离散点
                center = curve['center']
                radius = curve['radius']
                
                # 生成一个完整的圆
                points = []
                for angle in np.linspace(0, 2 * np.pi, 36):  # 每10度一个点
                    x = center[0] + radius * np.cos(angle)
                    y = center[1] + radius * np.sin(angle)
                    z = center[2]
                    points.append([x, y, z])
                
                # 闭合圆形
                points.append(points[0])
                toolpaths.append(points)
            
            elif curve['type'] == 'B_SPLINE_CURVE':
                # 使用geomdl库采样B样条曲线
                degree = curve['degree']
                control_points = curve['control_points']
                
                if len(control_points) > degree:
                    try:
                        # 创建曲线对象
                        curve_obj = BSpline.Curve()
                        curve_obj.degree = degree
                        curve_obj.ctrlpts = control_points
                        
                        # 生成均匀节点向量
                        curve_obj.knotvector = utils.generate_knot_vector(curve_obj.degree, len(curve_obj.ctrlpts))
                        
                        # 设置样本点数
                        curve_obj.sample_size = self.spline_samples
                        
                        # 计算曲线点
                        curve_points = curve_obj.evalpts
                        if curve_points:
                            toolpaths.append(curve_points)
                    except Exception as e:
                        print(f"B样条曲线处理出错: {e}")
        
        print(f"生成了 {len(toolpaths)} 条刀具路径")
        return toolpaths
    
    def write_gcode_header(self):
        """写入G代码文件头"""
        self.gcode_lines.extend([
            "(Generated by StepUtils to G-code Converter)",
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
    
    def generate_gcode_from_toolpaths(self, toolpaths, z_cut=0.0):
        """
        从刀具路径生成G代码
        
        Args:
            toolpaths: 刀具路径列表，每个路径是一个点的列表
            z_cut: 切割高度
        """
        for path_idx, path in enumerate(toolpaths):
            if not path or len(path) < 2:
                continue
                
            # 移动到当前路径的起点上方
            first_point = path[0]
            self.gcode_lines.append(f"G0 Z{self.safety_height} ; 提升到安全高度")
            self.gcode_lines.append(f"G0 X{first_point[0]:.4f} Y{first_point[1]:.4f} ; 快速移动到路径 {path_idx+1} 起点")
            self.gcode_lines.append(f"G1 Z{z_cut:.4f} F{self.feed_rate} ; 下降到切割高度")
            
            # 跟踪当前位置
            self.current_x, self.current_y, self.current_z = first_point[0], first_point[1], z_cut
            
            # 沿路径移动
            for point in path[1:]:
                x, y, z = point
                # 保持Z高度不变，使用提供的切割高度
                self.gcode_lines.append(f"G1 X{x:.4f} Y{y:.4f} F{self.feed_rate} ; 路径切割")
                self.current_x, self.current_y = x, y
    
    def convert(self):
        """执行转换过程"""
        try:
            # 加载STEP文件
            if not self.load_step_file():
                return False
            
            # 提取几何信息
            if not self.extract_geometry():
                return False
            
            # 生成刀具路径
            toolpaths = self.generate_toolpaths()
            
            if not toolpaths:
                print("警告: 无法生成刀具路径")
                return False
            
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
                    self.generate_gcode_from_toolpaths(toolpaths, z_cut)
            else:
                # 如果没有边界信息，使用默认切割深度
                self.generate_gcode_from_toolpaths(toolpaths, -self.cut_depth)
            
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
    parser = argparse.ArgumentParser(description='将STEP文件转换为G代码')
    parser.add_argument('input_file', help='输入STEP文件路径')
    parser.add_argument('-o', '--output', help='输出G代码文件路径')
    parser.add_argument('-f', '--feed-rate', type=float, default=500, help='加工进给率 (mm/min)')
    parser.add_argument('-r', '--rapid-feed-rate', type=float, default=1000, help='快速移动进给率 (mm/min)')
    parser.add_argument('-s', '--safety-height', type=float, default=5.0, help='安全高度 (mm)')
    parser.add_argument('-d', '--cut-depth', type=float, default=0.5, help='每次切割深度 (mm)')
    parser.add_argument('-t', '--tool-diameter', type=float, default=3.0, help='刀具直径 (mm)')
    parser.add_argument('-p', '--spline-samples', type=int, default=50, help='样条曲线采样点数')
    
    args = parser.parse_args()
    
    converter = StepToGcode(
        input_file=args.input_file,
        output_file=args.output,
        feed_rate=args.feed_rate,
        rapid_feed_rate=args.rapid_feed_rate,
        safety_height=args.safety_height,
        cut_depth=args.cut_depth,
        tool_diameter=args.tool_diameter,
        spline_samples=args.spline_samples
    )
    
    success = converter.convert()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 