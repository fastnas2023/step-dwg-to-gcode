#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简化版STEP文件处理器（ARM架构兼容版本）
为没有PythonOCC-Core的环境提供基本的STEP文件处理功能
"""

import os
import re
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from time import time
import uuid

class SimpleStepProcessor:
    def __init__(self, input_file):
        """
        初始化STEP文件处理器
        
        Args:
            input_file (str): 输入STP文件路径
        """
        print(f"初始化SimpleStepProcessor，文件: {input_file}")
        self.input_file = input_file
        self.points_array = None  # 存储所有点的NumPy数组
        self.edges_array = None   # 存储所有边的NumPy数组
        self.bounds = None        # 存储边界信息
        self.contours = []        # 存储提取的轮廓
    
    def parse_file(self):
        """解析STEP文件并提取几何信息"""
        print(f"正在解析STEP文件: {self.input_file}")
        start_time = time()
        
        try:
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
                print("尝试使用替代方法构建边...")
                
                # 将点按照X和Y坐标排序
                indices = np.lexsort((self.points_array[:, 1], self.points_array[:, 0]))
                sorted_points = self.points_array[indices]
                
                # 创建边
                edges_list = []
                for i in range(len(sorted_points) - 1):
                    edges_list.append([sorted_points[i], sorted_points[i+1]])
                
                # 形成闭环
                if len(sorted_points) > 2:
                    edges_list.append([sorted_points[-1], sorted_points[0]])
                
                print(f"创建了 {len(edges_list)} 条边")
            
            # 转换为NumPy数组
            if edges_list:
                self.edges_array = np.array(edges_list)
            else:
                print("警告: 未找到有效的边，STEP文件可能格式异常或内容为空")
                return False
            
            # 计算边界
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
            
        except Exception as e:
            print(f"STEP文件解析出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_3d_visualization(self, output_path=None):
        """创建3D可视化图像"""
        if self.edges_array is None or len(self.edges_array) == 0:
            print("无法创建可视化，没有找到足够的边")
            return False
        
        try:
            # 创建3D图形
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            # 绘制边
            for edge in self.edges_array:
                start_point = edge[0]
                end_point = edge[1]
                ax.plot([start_point[0], end_point[0]],
                       [start_point[1], end_point[1]],
                       [start_point[2], end_point[2]], 'b-')
            
            # 设置坐标轴标签
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            
            # 设置坐标轴比例相等
            if self.bounds:
                xmin, ymin, zmin, xmax, ymax, zmax = self.bounds
                max_range = max(xmax-xmin, ymax-ymin, zmax-zmin)
                mid_x = (xmax + xmin) / 2
                mid_y = (ymax + ymin) / 2
                mid_z = (zmax + zmin) / 2
                ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
                ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
                ax.set_zlim(mid_z - max_range/2, mid_z + max_range/2)
            
            # 调整视角
            ax.view_init(elev=30, azim=45)
            
            # 保存图像
            if output_path is None:
                # 生成默认输出路径
                output_dir = os.path.dirname(self.input_file)
                file_name = os.path.splitext(os.path.basename(self.input_file))[0]
                output_path = os.path.join(output_dir, f"{file_name}_visualization.png")
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150)
            plt.close(fig)
            
            print(f"3D可视化已保存至: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"创建3D可视化时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def process(self, preview_only=False, preview_output=None):
        """处理STEP文件并返回结果"""
        # 解析文件
        print(f"开始处理STEP文件: {self.input_file}, preview_only={preview_only}")
        if not self.parse_file():
            print("无法处理STEP文件，解析失败")
            return None, None, None
        
        # 如果只需要预览，生成可视化并返回
        if preview_only:
            if not preview_output:
                # 生成默认预览输出路径
                preview_dir = os.path.join(os.path.dirname(self.input_file), "plots")
                os.makedirs(preview_dir, exist_ok=True)
                preview_output = os.path.join(preview_dir, f"{os.path.splitext(os.path.basename(self.input_file))[0]}_preview.png")
            
            print(f"生成预览图像: {preview_output}")
            visualization_path = self.create_3d_visualization(preview_output)
            
            if visualization_path:
                return True, visualization_path, {"points": len(self.points_array) if self.points_array is not None else 0,
                                                 "edges": len(self.edges_array) if self.edges_array is not None else 0}
            else:
                return False, None, None
        
        # 对于完整处理，简单地返回边数组作为路径
        print("返回边数组作为路径，用于G代码生成")
        
        # 尝试创建一条路径通过所有边
        if self.edges_array is not None and len(self.edges_array) > 0:
            # 提取所有点
            all_points = []
            for edge in self.edges_array:
                all_points.append(edge[0])
                all_points.append(edge[1])
            
            # 去重
            unique_points = []
            for p in all_points:
                if not any(np.array_equal(p, up) for up in unique_points):
                    unique_points.append(p)
            
            # 如果点数量太少，直接返回所有边的点
            if len(unique_points) < 3:
                path = np.array(all_points)
                print(f"点数量太少({len(unique_points)}个)，直接返回所有边的点({len(path)}个)")
                return path, self.bounds, {
                    "points": len(unique_points),
                    "edges": len(self.edges_array),
                    "bounds": self.bounds
                }
            
            # 贪心算法构建路径
            path = [unique_points[0]]
            remaining = unique_points[1:]
            
            while remaining:
                last_point = path[-1]
                closest_idx = 0
                min_dist = float('inf')
                
                for i, p in enumerate(remaining):
                    dist = np.linalg.norm(np.array(last_point) - np.array(p))
                    if dist < min_dist:
                        min_dist = dist
                        closest_idx = i
                
                path.append(remaining[closest_idx])
                del remaining[closest_idx]
            
            # 转换为NumPy数组
            path_array = np.array(path)
            print(f"创建了包含{len(path_array)}个点的路径")
            
            # 统计信息
            stats = {
                "points": len(unique_points),
                "edges": len(self.edges_array),
                "bounds": self.bounds,
                "path_length": len(path_array)
            }
            
            return path_array, self.bounds, stats
        
        # 如果没有有效边，返回None
        return None, self.bounds, {"points": 0, "edges": 0, "bounds": self.bounds}


# 如果直接运行此脚本，执行测试
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python step_processor_fallback.py 输入.step")
        sys.exit(1)
    
    input_file = sys.argv[1]
    processor = SimpleStepProcessor(input_file)
    
    # 测试处理
    path, bounds, stats = processor.process()
    
    if path is not None:
        print("处理成功")
        print(f"生成路径点数: {len(path)}")
        print(f"模型边界: {bounds}")
        print(f"统计信息: {stats}")
    else:
        print("处理失败") 