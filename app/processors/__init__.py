#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件处理器模块
提供解析和处理CAD文件的能力
"""

import os
import sys
import importlib
from typing import Dict, Type, Any, List

# 当实际移动文件后，取消下面的注释，导入所有处理器类
# from .numpy_step_processor import NumPyStepProcessor
# from .ezdxf_processor import EzdxfProcessor
# ...

# 处理器类字典，用于通过ID获取处理器类
_PROCESSOR_CLASSES: Dict[str, Type] = {
    # 当实际移动文件后，取消下面的注释，映射处理器ID到类
    # 'numpy': NumPyStepProcessor,
    # 'ezdxf': EzdxfProcessor,
    # ...
}

# 导入适配器模块
from app.processors.adapter import get_adapted_processor

def get_processor_by_id(processor_id: str) -> Type:
    """
    通过处理器ID获取对应的处理器类
    
    Args:
        processor_id: 处理器ID
        
    Returns:
        对应的处理器类
        
    Raises:
        ValueError: 如果处理器ID不存在
    """
    print(f"尝试获取处理器: {processor_id}")
    
    if processor_id in _PROCESSOR_CLASSES:
        processor_class = _PROCESSOR_CLASSES[processor_id]
        return get_adapted_processor(processor_id, processor_class)
    else:
        # 临时解决方案：直接引用原有文件，在项目重构完成后可移除
        from config.app_config import PROJECT_ROOT
        old_file_mapping = {
            'numpy': 'numpy_step_processor.py',
            'step': 'step_file_processor.py',
            'dwg': 'dwg_processor.py'
        }
        
        print(f"使用临时映射，文件映射: {old_file_mapping.get(processor_id, '未找到')}")
        
        if processor_id in old_file_mapping:
            module_name = os.path.splitext(old_file_mapping[processor_id])[0]
            
            # 使用正确的类名 (注意：NumPyStepProcessor 而不是 NumpyStepProcessor)
            class_name_mapping = {
                'numpy_step_processor': 'NumPyStepProcessor',
                'step_file_processor': 'StepFileProcessor',
                'dwg_processor': 'DwgProcessor'
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
                processor_class = getattr(module, class_name)
                print(f"成功加载处理器类: {processor_class.__name__}")
                
                # 使用适配器包装处理器类
                return get_adapted_processor(processor_id, processor_class)
            except (ImportError, AttributeError) as e:
                error_msg = f"无法加载处理器: {processor_id}, 错误: {str(e)}"
                print(f"错误: {error_msg}")
                # 检查模块是否成功导入，如果是，则列出模块中的所有类
                if 'module' in locals():
                    print(f"模块已导入，但找不到类 {class_name}")
                    print(f"模块中的类和函数: {dir(module)}")
                raise ValueError(error_msg)
        else:
            error_msg = f"不支持的处理器ID: {processor_id}"
            print(f"错误: {error_msg}")
            raise ValueError(error_msg)

def list_available_processors() -> List[Dict[str, Any]]:
    """
    列出所有可用的处理器
    
    Returns:
        处理器信息列表
    """
    from config.app_config import SUPPORTED_CONVERTERS
    return SUPPORTED_CONVERTERS

__all__ = ['get_processor_by_id', 'list_available_processors'] 