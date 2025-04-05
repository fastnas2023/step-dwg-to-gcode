#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
基础G代码生成器抽象类
为不同CNC控制器提供统一接口
"""

from abc import ABC, abstractmethod

class BaseGcodeGenerator(ABC):
    """G代码生成器基类，定义所有控制器通用接口"""
    
    def __init__(self, feed_rate=500, safety_height=10, cut_depth=0.5):
        """
        初始化基础参数
        
        参数:
        feed_rate (float): 进给速度 (mm/min)
        safety_height (float): 安全高度 (mm)
        cut_depth (float): 切削深度 (mm)
        """
        self.feed_rate = float(feed_rate)
        self.safety_height = float(safety_height)
        self.cut_depth = float(cut_depth)
        self.current_position = {"x": 0, "y": 0, "z": 0}
    
    @abstractmethod
    def generate_header(self):
        """生成程序头部，返回字符串列表"""
        pass
    
    @abstractmethod
    def generate_footer(self):
        """生成程序尾部，返回字符串列表"""
        pass
    
    @abstractmethod
    def generate_linear_move(self, x, y, z, feed=None):
        """
        生成直线移动指令
        
        参数:
        x, y, z (float): 目标坐标
        feed (float): 可选的进给速率，默认使用实例进给速率
        
        返回:
        str: G代码指令
        """
        pass
    
    @abstractmethod
    def generate_rapid_move(self, x=None, y=None, z=None):
        """
        生成快速移动指令
        
        参数:
        x, y, z (float): 目标坐标，None表示不移动该轴
        
        返回:
        str: G代码指令
        """
        pass
    
    @abstractmethod
    def set_working_plane(self, plane="xy"):
        """
        设置工作平面
        
        参数:
        plane (str): 工作平面，可选 "xy", "xz", "yz"
        
        返回:
        str: G代码指令
        """
        pass
    
    @abstractmethod
    def set_units(self, units="mm"):
        """
        设置单位
        
        参数:
        units (str): 单位，可选 "mm", "inch"
        
        返回:
        str: G代码指令
        """
        pass
    
    @abstractmethod
    def set_coordinate_system(self, system=1):
        """
        设置坐标系
        
        参数:
        system (int): 坐标系编号
        
        返回:
        str: G代码指令
        """
        pass
    
    def update_position(self, x=None, y=None, z=None):
        """更新当前位置"""
        if x is not None:
            self.current_position["x"] = x
        if y is not None:
            self.current_position["y"] = y
        if z is not None:
            self.current_position["z"] = z
    
    def format_coordinate(self, value):
        """格式化坐标值"""
        if value is None:
            return None
        return "{:.3f}".format(value)
    
    def process_points(self, points):
        """
        处理一系列点并生成相应的G代码
        
        参数:
        points (list): 点坐标列表，每个点是(x,y,z)元组
        
        返回:
        list: G代码指令列表
        """
        gcode = []
        
        # 先移动到安全高度
        gcode.append(self.generate_rapid_move(z=self.safety_height))
        
        if not points:
            return gcode
        
        # 移动到第一个点上方
        first_point = points[0]
        gcode.append(self.generate_rapid_move(x=first_point[0], y=first_point[1]))
        
        # 下降到切削深度
        gcode.append(self.generate_linear_move(
            x=first_point[0], 
            y=first_point[1], 
            z=self.cut_depth
        ))
        
        # 处理其余点
        for point in points[1:]:
            gcode.append(self.generate_linear_move(
                x=point[0], 
                y=point[1], 
                z=self.cut_depth
            ))
        
        # 回到安全高度
        gcode.append(self.generate_rapid_move(z=self.safety_height))
        
        return gcode
    
    def generate_gcode(self, points):
        """
        生成完整G代码
        
        参数:
        points (list): 点坐标列表
        
        返回:
        list: 完整G代码指令列表
        """
        gcode = []
        
        # 添加程序头
        gcode.extend(self.generate_header())
        
        # 处理点
        gcode.extend(self.process_points(points))
        
        # 添加程序尾
        gcode.extend(self.generate_footer())
        
        return gcode 