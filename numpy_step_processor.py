#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
STEP文件处理器 (基于NumPy优化版本)
此脚本提供了高效的STEP格式CAD文件处理功能，利用NumPy进行高性能计算
"""

import os
import re
import numpy as np
from time import time

class NumPyStepProcessor:
    def __init__(self, input_file):
        """
        初始化STEP文件处理器
        
        Args:
            input_file (str): 输入STP文件路径
        """
        self.input_file = input_file
        self.points_array = None  # 存储所有点的NumPy数组
        self.edges_array = None   # 存储所有边的NumPy数组
        self.bounds = None        # 存储边界信息
        self.contours = []        # 存储提取的轮廓
    
    def parse_file(self):
        """解析STEP文件并提取几何信息"""
        print(f"正在解析STEP文件: {self.input_file}")
        start_time = time()
        
        # 读取文件内容
        with open(self.input_file, 'r', errors='ignore') as f:
            content = f.read()
        
        # 提取顶点信息 (CARTESIAN_POINT)
        cartesian_point_pattern = r'#(\d+)=CARTESIAN_POINT\(\'.*?\',\((.*?)\)\);'
        point_matches = re.finditer(cartesian_point_pattern, content)
        
        points_dict = {}  # 使用ID作为键存储点
        points_list = []  # 临时列表存储所有点
        
        for match in point_matches:
            point_id = int(match.group(1))
            coords_str = match.group(2)
            # 去除可能的空格，分割坐标
            coords = [float(x.strip()) for x in coords_str.split(',')]
            if len(coords) == 3:  # 确保是3D点
                points_dict[point_id] = coords
                points_list.append(coords)
        
        # 转换为NumPy数组以提高性能
        if points_list:
            self.points_array = np.array(points_list)
        
        print(f"找到 {len(points_dict)} 个点")
        
        # 提取边的信息
        # 首先找到所有EDGE_CURVE实体
        edge_curve_pattern = r'#(\d+)=EDGE_CURVE\(\'.*?\',#(\d+),#(\d+),#(\d+).*?\);'
        edge_matches = re.finditer(edge_curve_pattern, content)
        
        edge_ids = {}  # 存储边ID与对应的起点终点ID
        for match in edge_matches:
            edge_id = int(match.group(1))
            start_id = int(match.group(2))
            end_id = int(match.group(3))
            edge_ids[edge_id] = (start_id, end_id)
        
        print(f"找到 {len(edge_ids)} 个EDGE_CURVE实体")
        
        # 然后找所有ORIENTED_EDGE实体，它们引用了EDGE_CURVE
        oriented_edge_pattern = r'#\d+=ORIENTED_EDGE\(\'.*?\',\*,\*,#(\d+),.*?\);'
        oriented_matches = re.finditer(oriented_edge_pattern, content)
        
        edges_list = []  # 临时列表存储所有边
        used_edges = set()
        
        for match in oriented_matches:
            edge_ref_id = int(match.group(1))
            if edge_ref_id in edge_ids and edge_ref_id not in used_edges:
                start_id, end_id = edge_ids[edge_ref_id]
                if start_id in points_dict and end_id in points_dict:
                    edges_list.append([points_dict[start_id], points_dict[end_id]])
                    used_edges.add(edge_ref_id)
        
        # 如果找到的边不足，使用替代方法
        if len(edges_list) < 10 and self.points_array is not None:
            print("尝试使用基于NumPy的高效方法构建边...")
            
            # 将点按照X和Y坐标排序
            indices = np.lexsort((self.points_array[:, 1], self.points_array[:, 0]))
            sorted_points = self.points_array[indices]
            
            # 使用向量化操作创建边
            edges_list = []
            for i in range(len(sorted_points) - 1):
                edges_list.append([sorted_points[i], sorted_points[i+1]])
            
            # 形成闭环
            if len(sorted_points) > 2:
                edges_list.append([sorted_points[-1], sorted_points[0]])
            
            print(f"通过NumPy向量化操作创建了 {len(edges_list)} 条边")
        
        # 转换为NumPy数组
        if edges_list:
            self.edges_array = np.array(edges_list)
        
        # 计算边界（使用NumPy高效计算）
        if self.points_array is not None:
            min_coords = np.min(self.points_array, axis=0)
            max_coords = np.max(self.points_array, axis=0)
            self.bounds = (min_coords[0], min_coords[1], min_coords[2],
                          max_coords[0], max_coords[1], max_coords[2])
            
            print(f"模型边界: X: {min_coords[0]:.3f} 到 {max_coords[0]:.3f}, " +
                  f"Y: {min_coords[1]:.3f} 到 {max_coords[1]:.3f}, " +
                  f"Z: {min_coords[2]:.3f} 到 {max_coords[2]:.3f}")
        
        print(f"STEP文件解析完成，用时 {time() - start_time:.2f} 秒")
        return len(edges_list) > 0
    
    def extract_contours(self):
        """使用NumPy高效提取轮廓"""
        if self.edges_array is None or len(self.edges_array) == 0:
            print("警告: 无法提取轮廓，没有找到足够的边")
            return False
        
        print("正在使用NumPy高效构建轮廓...")
        start_time = time()
        
        # 将边展平为点集
        edge_starts = self.edges_array[:, 0, :]  # 所有边的起点
        edge_ends = self.edges_array[:, 1, :]    # 所有边的终点
        
        # 使用NumPy计算所有点之间的距离矩阵
        # 这种方法对于大型模型非常高效
        num_edges = len(self.edges_array)
        used_edges = np.zeros(num_edges, dtype=bool)
        
        # 构建轮廓
        contour_index = 0
        while not np.all(used_edges):
            # 找到第一个未使用的边
            start_edge_idx = np.where(~used_edges)[0][0]
            used_edges[start_edge_idx] = True
            
            # 开始一个新的轮廓
            current_contour = [edge_starts[start_edge_idx], edge_ends[start_edge_idx]]
            current_point = edge_ends[start_edge_idx]
            
            # 持续寻找连接的边
            found_next = True
            while found_next:
                found_next = False
                
                # 计算所有未使用边的起点与当前点之间的距离
                start_distances = np.sum((edge_starts[~used_edges] - current_point) ** 2, axis=1)
                end_distances = np.sum((edge_ends[~used_edges] - current_point) ** 2, axis=1)
                
                # 找到最近的边
                if len(start_distances) > 0:
                    min_start_idx = np.argmin(start_distances)
                    min_start_dist = start_distances[min_start_idx]
                    
                    min_end_idx = np.argmin(end_distances)
                    min_end_dist = end_distances[min_end_idx]
                    
                    # 查找未使用的边索引
                    unused_indices = np.where(~used_edges)[0]
                    
                    # 选择距离最小的连接方式
                    if min_start_dist < min_end_dist and min_start_dist < 1e-6:
                        # 连接到起点
                        next_edge_idx = unused_indices[min_start_idx]
                        current_point = edge_ends[next_edge_idx]
                        current_contour.append(current_point)
                        used_edges[next_edge_idx] = True
                        found_next = True
                    elif min_end_dist < 1e-6:
                        # 连接到终点
                        next_edge_idx = unused_indices[min_end_idx]
                        current_point = edge_starts[next_edge_idx]
                        current_contour.append(current_point)
                        used_edges[next_edge_idx] = True
                        found_next = True
            
            # 保存轮廓（至少3个点）
            if len(current_contour) > 2:
                self.contours.append(np.array(current_contour))
                contour_index += 1
        
        print(f"使用NumPy高效构建了 {len(self.contours)} 个轮廓，用时 {time() - start_time:.2f} 秒")
        return len(self.contours) > 0
    
    def get_optimized_path(self):
        """使用NumPy计算优化的加工路径"""
        if not self.contours:
            if self.edges_array is not None:
                # 如果没有轮廓但有边，直接使用边
                print("使用边直接构建路径...")
                return self.edges_array.reshape(-1, 3)  # 将边展平为点序列
            return None
        
        # 对于多个轮廓，使用贪婪算法优化访问顺序
        if len(self.contours) > 1:
            print("优化多轮廓访问顺序...")
            start_time = time()
            
            # 计算每个轮廓的中心点
            centers = np.array([np.mean(contour, axis=0) for contour in self.contours])
            
            # 优化访问顺序（使用贪婪最近邻算法）
            visited = np.zeros(len(self.contours), dtype=bool)
            current_idx = 0  # 从第一个轮廓开始
            visited[current_idx] = True
            path_order = [current_idx]
            
            for _ in range(len(self.contours) - 1):
                # 计算当前轮廓到所有未访问轮廓的距离
                distances = np.sum((centers[~visited] - centers[current_idx]) ** 2, axis=1)
                next_idx = np.where(~visited)[0][np.argmin(distances)]
                path_order.append(next_idx)
                visited[next_idx] = True
                current_idx = next_idx
            
            # 按优化顺序重新排列轮廓
            self.contours = [self.contours[i] for i in path_order]
            print(f"轮廓顺序优化完成，用时 {time() - start_time:.2f} 秒")
        
        # 合并所有轮廓为一个路径数组
        total_points = sum(len(contour) for contour in self.contours)
        path = np.zeros((total_points, 3))
        
        idx = 0
        for contour in self.contours:
            path_len = len(contour)
            path[idx:idx+path_len] = contour
            idx += path_len
        
        return path
    
    def analyze_geometry(self):
        """分析模型几何特性并返回统计信息"""
        if self.points_array is None:
            return {}
        
        stats = {}
        # 基本尺寸信息
        if self.bounds:
            stats['dimensions'] = {
                'width': self.bounds[3] - self.bounds[0],
                'height': self.bounds[4] - self.bounds[1],
                'depth': self.bounds[5] - self.bounds[2]
            }
        
        # 点分布统计
        stats['points'] = {
            'count': len(self.points_array),
            'mean_x': np.mean(self.points_array[:, 0]),
            'mean_y': np.mean(self.points_array[:, 1]),
            'mean_z': np.mean(self.points_array[:, 2]),
            'std_x': np.std(self.points_array[:, 0]),
            'std_y': np.std(self.points_array[:, 1]),
            'std_z': np.std(self.points_array[:, 2])
        }
        
        # 边信息
        if self.edges_array is not None:
            # 计算边长度
            edge_lengths = np.sqrt(np.sum((self.edges_array[:, 1, :] - self.edges_array[:, 0, :]) ** 2, axis=1))
            stats['edges'] = {
                'count': len(self.edges_array),
                'mean_length': np.mean(edge_lengths),
                'min_length': np.min(edge_lengths),
                'max_length': np.max(edge_lengths),
                'total_length': np.sum(edge_lengths)
            }
        
        # 轮廓信息
        if self.contours:
            contour_lengths = []
            contour_areas = []
            
            for contour in self.contours:
                # 计算轮廓长度
                contour_length = 0
                for i in range(len(contour)):
                    next_i = (i + 1) % len(contour)
                    segment_length = np.sqrt(np.sum((contour[next_i] - contour[i]) ** 2))
                    contour_length += segment_length
                contour_lengths.append(contour_length)
                
                # 估算轮廓面积（仅适用于平面轮廓）
                # 使用鞋带公式计算面积
                if len(contour) > 2:
                    x = contour[:, 0]
                    y = contour[:, 1]
                    area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
                    contour_areas.append(area)
            
            stats['contours'] = {
                'count': len(self.contours),
                'mean_length': np.mean(contour_lengths),
                'total_length': np.sum(contour_lengths)
            }
            
            if contour_areas:
                stats['contours']['mean_area'] = np.mean(contour_areas)
                stats['contours']['total_area'] = np.sum(contour_areas)
        
        return stats

    def process(self):
        """处理STEP文件并返回结果"""
        success = self.parse_file()
        if not success:
            print("错误: 无法解析STEP文件或未找到足够的几何信息")
            return None, None, None
        
        self.extract_contours()
        path = self.get_optimized_path()
        stats = self.analyze_geometry()
        
        return path, self.bounds, stats

def main():
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='使用NumPy高效处理STEP文件')
    parser.add_argument('input_file', help='输入STEP文件路径')
    parser.add_argument('-o', '--output', help='输出JSON文件路径')
    parser.add_argument('-s', '--stats', action='store_true', help='输出几何统计信息')
    
    args = parser.parse_args()
    
    processor = NumPyStepProcessor(args.input_file)
    path, bounds, stats = processor.process()
    
    if path is None:
        print("处理失败.")
        return 1
    
    output_data = {
        'file': os.path.basename(args.input_file),
        'points_count': len(path),
        'bounds': {
            'min_x': bounds[0], 'min_y': bounds[1], 'min_z': bounds[2],
            'max_x': bounds[3], 'max_y': bounds[4], 'max_z': bounds[5]
        }
    }
    
    if args.stats and stats:
        output_data['statistics'] = stats
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"结果已保存到: {args.output}")
    else:
        print(json.dumps(output_data, indent=2))
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 