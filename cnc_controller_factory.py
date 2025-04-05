#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CNC控制器工厂类
用于创建不同CNC控制器的G代码生成器实例
"""

from fanuc_gcode_generator import FanucGcodeGenerator
from siemens_gcode_generator import SiemensGcodeGenerator
from heidenhain_gcode_generator import HeidenhainGcodeGenerator
from haas_gcode_generator import HaasGcodeGenerator

class CncControllerFactory:
    """
    CNC控制器工厂类
    用于创建特定控制器的G代码生成器实例
    """
    
    @staticmethod
    def create_controller(controller_type, **kwargs):
        """
        创建特定类型的CNC控制器实例
        
        参数:
        controller_type (str): 控制器类型，可选值:
            - "fanuc": 发那科控制器
            - "siemens": 西门子控制器
            - "heidenhain": 海德汉控制器
            - "haas": 哈斯控制器
            
        **kwargs: 其他参数，会传递给控制器构造函数，如:
            - feed_rate: 进给速度
            - safety_height: 安全高度
            - cut_depth: 切削深度
            - tool_number: 刀具号
            - spindle_speed: 主轴转速
            
        返回:
        BaseGcodeGenerator的子类实例
        
        异常:
        ValueError: 当指定了不支持的控制器类型时
        """
        controller_type = controller_type.lower()
        
        if controller_type == "fanuc":
            return FanucGcodeGenerator(**kwargs)
        elif controller_type == "siemens":
            return SiemensGcodeGenerator(**kwargs)
        elif controller_type == "heidenhain":
            return HeidenhainGcodeGenerator(**kwargs)
        elif controller_type == "haas":
            return HaasGcodeGenerator(**kwargs)
        else:
            supported_controllers = ["fanuc", "siemens", "heidenhain", "haas"]
            raise ValueError(f"不支持的控制器类型: {controller_type}，支持的类型: {', '.join(supported_controllers)}")
    
    @staticmethod
    def get_supported_controllers():
        """获取所有支持的控制器类型"""
        return [
            {"id": "fanuc", "name": "FANUC (发那科)", "description": "日本发那科公司，最广泛使用的CNC控制器"},
            {"id": "siemens", "name": "Siemens SINUMERIK (西门子)", "description": "德国西门子公司，在欧洲广泛使用"},
            {"id": "heidenhain", "name": "Heidenhain (海德汉)", "description": "德国海德汉公司，用于高精度加工"},
            {"id": "haas", "name": "Haas (哈斯)", "description": "美国哈斯自动化公司，小型加工中心常用"}
        ] 