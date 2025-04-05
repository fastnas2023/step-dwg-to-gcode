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
            else:
                print("警告: 未找到有效的边，STEP文件可能格式异常或内容为空")
                return False
            
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
            
        except Exception as e:
            print(f"STEP文件解析出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_contours(self):
        """使用NumPy高效提取轮廓"""
        try:
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
                iterations = 0
                max_iterations = num_edges * 2  # 防止无限循环
                
                while found_next and iterations < max_iterations:
                    iterations += 1
                    found_next = False
                    
                    # 计算所有未使用边的起点与当前点之间的距离
                    if np.any(~used_edges):  # 确保还有未使用的边
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
                
                # 检查轮廓是否闭合
                if len(current_contour) > 3:
                    start_point = current_contour[0]
                    end_point = current_contour[-1]
                    distance = np.sum((end_point - start_point) ** 2)
                    if distance < 1e-6:  # 如果起点和终点足够接近，认为轮廓闭合
                        print(f"轮廓 {contour_index+1} 已闭合")
                    else:
                        print(f"轮廓 {contour_index+1} 未闭合，起点和终点距离: {np.sqrt(distance):.6f}")
                
                # 保存轮廓（至少3个点）
                if len(current_contour) > 2:
                    try:
                        contour_array = np.array(current_contour)
                        self.contours.append(contour_array)
                        contour_index += 1
                        print(f"添加轮廓 {contour_index}，包含 {len(current_contour)} 个点")
                    except Exception as e:
                        print(f"添加轮廓时出错: {str(e)}")
            
            print(f"使用NumPy高效构建了 {len(self.contours)} 个轮廓，用时 {time() - start_time:.2f} 秒")
            return len(self.contours) > 0
            
        except Exception as e:
            print(f"提取轮廓过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()
            # 轮廓提取失败不应该导致整个处理失败
            # 可以在后续步骤中直接使用边来构建路径
            self.contours = []
            return False
    
    def get_optimized_path(self):
        """使用NumPy计算优化的加工路径"""
        try:
            if not self.contours:
                if self.edges_array is not None:
                    # 如果没有轮廓但有边，直接使用边
                    print("使用边直接构建路径...")
                    return self.edges_array.reshape(-1, 3)  # 将边展平为点序列
                print("错误: 找不到有效的轮廓或边")
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
            
        except Exception as e:
            print(f"生成优化路径出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def analyze_geometry(self):
        """分析几何特征并返回统计信息"""
        stats = {
            "points": {},
            "edges": {},
            "contours": {},
            "bounds": {}
        }
        
        if self.points_array is not None:
            points_count = len(self.points_array)
            stats["points"]["count"] = int(points_count)  # 转换为Python原生int
        else:
            stats["points"]["count"] = 0
        
        if self.edges_array is not None:
            edges_count = len(self.edges_array)
            stats["edges"]["count"] = int(edges_count)  # 转换为Python原生int
            
            # 计算总边长
            dx = self.edges_array[:, 1, 0] - self.edges_array[:, 0, 0]
            dy = self.edges_array[:, 1, 1] - self.edges_array[:, 0, 1]
            dz = self.edges_array[:, 1, 2] - self.edges_array[:, 0, 2]
            edge_lengths = np.sqrt(dx**2 + dy**2 + dz**2)
            
            stats["edges"]["total_length"] = float(np.sum(edge_lengths))
            stats["edges"]["avg_length"] = float(np.mean(edge_lengths))
            stats["edges"]["min_length"] = float(np.min(edge_lengths))
            stats["edges"]["max_length"] = float(np.max(edge_lengths))
        else:
            stats["edges"]["count"] = 0
        
        if self.contours:
            stats["contours"]["count"] = int(len(self.contours))  # 转换为Python原生int
            contour_lengths = []
            
            for contour in self.contours:
                points = contour.shape[0]
                contour_lengths.append(int(points))  # 转换为Python原生int
            
            if contour_lengths:
                stats["contours"]["avg_points"] = float(np.mean(contour_lengths))
                stats["contours"]["min_points"] = int(np.min(contour_lengths))
                stats["contours"]["max_points"] = int(np.max(contour_lengths))
            else:
                stats["contours"]["avg_points"] = 0
                stats["contours"]["min_points"] = 0
                stats["contours"]["max_points"] = 0
        else:
            stats["contours"]["count"] = 0
        
        if self.bounds:
            min_x, min_y, min_z, max_x, max_y, max_z = self.bounds
            stats["bounds"]["width"] = float(max_x - min_x)
            stats["bounds"]["depth"] = float(max_y - min_y)
            stats["bounds"]["height"] = float(max_z - min_z)
            stats["bounds"]["volume"] = float((max_x - min_x) * (max_y - min_y) * (max_z - min_z))
            stats["bounds"]["min_x"] = float(min_x)
            stats["bounds"]["min_y"] = float(min_y)
            stats["bounds"]["min_z"] = float(min_z)
            stats["bounds"]["max_x"] = float(max_x)
            stats["bounds"]["max_y"] = float(max_y)
            stats["bounds"]["max_z"] = float(max_z)
        
        # 确保所有值都是JSON可序列化的
        return self._ensure_json_serializable(stats)
    
    def _ensure_json_serializable(self, obj):
        """
        递归地确保对象中的所有值都是JSON可序列化的
        将NumPy类型转换为Python原生类型
        """
        if isinstance(obj, dict):
            return {k: self._ensure_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._ensure_json_serializable(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return self._ensure_json_serializable(obj.tolist())
        else:
            return obj
    
    def extract_edges(self):
        """提取边缘，用于兼容已有代码"""
        if self.edges_array is None:
            # 如果还没有解析文件，先解析
            if not self.parse_file():
                return []
        
        # 将NumPy数组转换为列表格式，格式为简单的(x,y,z)点元组列表
        if self.edges_array is not None:
            # 创建所有点的列表
            points_list = []
            
            # 第一种方法：使用轮廓（如果可用）
            if len(self.contours) > 0:
                for contour in self.contours:
                    for point in contour:
                        # 确保每个点是元组格式
                        points_list.append(tuple(point.tolist()))
                return points_list
            
            # 第二种方法：如果没有轮廓，从边中提取点
            used_points = set()  # 用于去重
            for edge in self.edges_array:
                start_tuple = tuple(edge[0].tolist())
                end_tuple = tuple(edge[1].tolist())
                
                # 避免重复点
                if start_tuple not in used_points:
                    points_list.append(start_tuple)
                    used_points.add(start_tuple)
                
                if end_tuple not in used_points:
                    points_list.append(end_tuple)
                    used_points.add(end_tuple)
            
            return points_list
        return []
    
    def process(self):
        """处理STEP文件并返回加工路径"""
        try:
            if not self.parse_file():
                print("错误: 无法从STEP文件中解析有效数据")
                return None, None, None
            
            if not self.extract_contours():
                print("警告: 无法提取轮廓，将尝试直接使用边")
            
            path = self.get_optimized_path()
            if path is None:
                print("错误: 无法生成加工路径")
                return None, None, None
                
            stats = self.analyze_geometry()
            
            return path, self.bounds, stats
            
        except Exception as e:
            print(f"STEP处理过程出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None, None

def main():
    """测试主函数"""
    if len(sys.argv) < 2:
        print("用法: python numpy_step_processor.py <input_file.stp>")
        return 1
    
    input_file = sys.argv[1]
    processor = NumPyStepProcessor(input_file)
    
    path, bounds, stats = processor.process()
    
    if path is None:
        print("STEP文件处理失败")
        return 1
    
    print("\n处理结果统计:")
    for category, items in stats.items():
        print(f"  {category.upper()}:")
        for key, value in items.items():
            print(f"    {key}: {value}")
    
    return 0

def analyze_step_file(file_path):
    """
    分析STEP文件并输出详细信息，帮助诊断潜在问题
    
    Args:
        file_path: STEP文件路径
    
    Returns:
        dict: 包含分析结果的字典
    """
    results = {
        "file_info": {},
        "entities": {},
        "geometry": {},
        "validation": {},
        "issues": []
    }
    
    try:
        # 文件基本信息
        file_size = os.path.getsize(file_path) / (1024*1024)  # MB
        results["file_info"]["path"] = file_path
        results["file_info"]["size"] = f"{file_size:.2f} MB"
        results["file_info"]["exists"] = os.path.exists(file_path)
        
        if not os.path.exists(file_path):
            results["issues"].append("文件不存在")
            return results
        
        if file_size > 50:
            results["issues"].append(f"文件较大 ({file_size:.2f} MB)，可能处理较慢")
        
        # 读取文件内容
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read()
        
        # 检查文件格式
        results["file_info"]["is_step"] = "ISO-10303-21" in content[:1000]
        if not results["file_info"]["is_step"]:
            results["issues"].append("文件可能不是有效的STEP格式")
        
        # 分析实体数量
        entity_counts = {}
        for entity_type in ["CARTESIAN_POINT", "LINE", "EDGE_CURVE", "ORIENTED_EDGE", 
                           "FACE_OUTER_BOUND", "ADVANCED_FACE", "CLOSED_SHELL", "MANIFOLD_SOLID_BREP"]:
            count = content.count(f"={entity_type}(")
            entity_counts[entity_type] = count
        
        results["entities"] = entity_counts
        
        # 检查是否有足够的实体
        if entity_counts["CARTESIAN_POINT"] < 10:
            results["issues"].append(f"点数量不足: {entity_counts['CARTESIAN_POINT']}，模型可能过于简单或损坏")
        
        if entity_counts["EDGE_CURVE"] < 5:
            results["issues"].append(f"边数量不足: {entity_counts['EDGE_CURVE']}，模型可能过于简单或损坏")
        
        # 尝试提取几何信息
        processor = NumPyStepProcessor(file_path)
        
        # 只解析文件，不执行完整处理
        parse_success = processor.parse_file()
        
        if parse_success:
            if processor.points_array is not None:
                results["geometry"]["points_count"] = len(processor.points_array)
            else:
                results["geometry"]["points_count"] = 0
                results["issues"].append("未能提取有效的点集")
            
            if processor.edges_array is not None:
                results["geometry"]["edges_count"] = len(processor.edges_array)
            else:
                results["geometry"]["edges_count"] = 0
                results["issues"].append("未能提取有效的边")
            
            if processor.bounds:
                min_x, min_y, min_z, max_x, max_y, max_z = processor.bounds
                results["geometry"]["dimensions"] = {
                    "x_range": f"{min_x:.3f} 到 {max_x:.3f} ({max_x-min_x:.3f})",
                    "y_range": f"{min_y:.3f} 到 {max_y:.3f} ({max_y-min_y:.3f})",
                    "z_range": f"{min_z:.3f} 到 {max_z:.3f} ({max_z-min_z:.3f})"
                }
                
                # 检查模型尺寸是否过大或过小
                x_size = max_x - min_x
                y_size = max_y - min_y
                z_size = max_z - min_z
                
                if max(x_size, y_size, z_size) > 1000:
                    results["issues"].append(f"模型尺寸过大: {max(x_size, y_size, z_size):.1f} 单位，可能超出加工范围")
                
                if max(x_size, y_size, z_size) < 0.01:
                    results["issues"].append(f"模型尺寸过小: {max(x_size, y_size, z_size):.6f} 单位，可能低于精度要求")
                
                # 检测是否有单位缩放问题
                if max(x_size, y_size, z_size) > 500 and max(x_size, y_size, z_size) < 10000:
                    results["issues"].append("模型尺寸异常大，可能是英寸到毫米的单位转换问题")
            else:
                results["issues"].append("未能计算模型边界")
            
            # 尝试提取轮廓
            contour_extract_success = processor.extract_contours()
            if contour_extract_success:
                results["geometry"]["contours_count"] = len(processor.contours)
            else:
                results["geometry"]["contours_count"] = 0
                results["issues"].append("未能提取有效的轮廓，可能需要手动处理")
            
            # 加工路径生成测试
            try:
                path = processor.get_optimized_path()
                if path is not None:
                    results["geometry"]["path_points"] = len(path)
                    results["validation"]["path_generation"] = "成功"
                else:
                    results["validation"]["path_generation"] = "失败"
                    results["issues"].append("无法生成加工路径，模型可能存在拓扑问题")
            except Exception as e:
                results["validation"]["path_generation"] = f"出错: {str(e)}"
                results["issues"].append(f"生成路径时出错: {str(e)}")
            
        else:
            results["validation"]["parse_success"] = False
            results["issues"].append("STEP文件解析失败，可能格式不兼容或数据损坏")
        
        # 添加诊断建议
        if not results["issues"]:
            results["diagnosis"] = "文件正常，没有发现明显问题"
        else:
            results["diagnosis"] = "文件存在潜在问题，请查看issues列表"
        
    except Exception as e:
        results["validation"]["analysis_success"] = False
        results["issues"].append(f"分析过程中出错: {str(e)}")
        import traceback
        results["error_traceback"] = traceback.format_exc()
    
    return results

if __name__ == "__main__":
    sys.exit(main()) 