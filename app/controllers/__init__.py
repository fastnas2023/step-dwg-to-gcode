#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CNC控制器模块
提供各种CNC控制器的G代码生成能力
"""

import os
import sys
import importlib
from typing import Dict, Type, Any, List

# 当实际移动文件后，取消下面的注释，导入所有控制器类
# from .fanuc_gcode_generator import FanucGcodeGenerator
# from .siemens_gcode_generator import SiemensGcodeGenerator
# from .haas_gcode_generator import HaasGcodeGenerator
# ...

# 控制器类字典，用于通过ID获取控制器类
_CONTROLLER_CLASSES: Dict[str, Type] = {
    # 当实际移动文件后，取消下面的注释，映射控制器ID到类
    # 'fanuc': FanucGcodeGenerator,
    # 'siemens': SiemensGcodeGenerator,
    # 'haas': HaasGcodeGenerator,
    # ...
}

# 导入适配器模块
from app.controllers.adapter import get_adapted_controller

def get_controller_by_id(controller_id: str) -> Type:
    """
    通过控制器ID获取对应的控制器类
    
    Args:
        controller_id: 控制器ID
        
    Returns:
        对应的控制器类
        
    Raises:
        ValueError: 如果控制器ID不存在
    """
    print(f"尝试获取控制器: {controller_id}")
    
    if controller_id in _CONTROLLER_CLASSES:
        controller_class = _CONTROLLER_CLASSES[controller_id]
        return get_adapted_controller(controller_id, controller_class)
    else:
        # 临时解决方案：直接引用原有文件，在项目重构完成后可移除
        from config.app_config import PROJECT_ROOT
        old_file_mapping = {
            'fanuc': 'fanuc_gcode_generator.py',
            'siemens': 'siemens_gcode_generator.py',
            'haas': 'haas_gcode_generator.py',
            'heidenhain': 'heidenhain_gcode_generator.py',
            'generic': 'base_gcode_generator.py',
            'numpy': 'numpy_gcode_generator.py',
        }
        
        print(f"使用临时映射，文件映射: {old_file_mapping.get(controller_id, '未找到')}")
        
        if controller_id in old_file_mapping:
            module_name = os.path.splitext(old_file_mapping[controller_id])[0]
            
            # 使用正确的类名映射
            class_name_mapping = {
                'fanuc_gcode_generator': 'FanucGcodeGenerator',
                'siemens_gcode_generator': 'SiemensGcodeGenerator',
                'haas_gcode_generator': 'HaasGcodeGenerator',
                'heidenhain_gcode_generator': 'HeidenhainGcodeGenerator',
                'base_gcode_generator': 'BaseGcodeGenerator',
                'numpy_gcode_generator': 'NumPyFanucGcodeGenerator',
            }
            
            class_name = class_name_mapping.get(module_name)
            if not class_name:
                # 如果没有特定映射，则使用原来的方式获取类名
                class_name = ''.join(word.capitalize() for word in module_name.split('_'))
            
            print(f"尝试加载模块: {module_name}, 类名: {class_name}")
            
            # 动态导入模块
            sys.path.insert(0, PROJECT_ROOT)
            try:
                module = importlib.import_module(module_name)
                controller_class = getattr(module, class_name)
                print(f"成功加载控制器类: {controller_class.__name__}")
                
                # 使用适配器包装控制器类
                return get_adapted_controller(controller_id, controller_class)
            except (ImportError, AttributeError) as e:
                error_msg = f"无法加载控制器: {controller_id}, 错误: {str(e)}"
                print(f"错误: {error_msg}")
                # 检查模块是否成功导入，如果是，则列出模块中的所有类
                if 'module' in locals():
                    print(f"模块已导入，但找不到类 {class_name}")
                    print(f"模块中的类和函数: {dir(module)}")
                raise ValueError(error_msg)
        else:
            error_msg = f"不支持的控制器ID: {controller_id}"
            print(f"错误: {error_msg}")
            raise ValueError(error_msg)

def list_available_controllers() -> List[Dict[str, Any]]:
    """
    列出所有可用的控制器
    
    Returns:
        控制器信息列表
    """
    from config.app_config import SUPPORTED_CONTROLLERS
    return SUPPORTED_CONTROLLERS

__all__ = ['get_controller_by_id', 'list_available_controllers'] 