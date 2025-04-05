#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
处理器适配器模块
通过适配模式，使旧版处理器适配新的应用架构
"""

import sys
import os
from typing import Any, List, Type, Tuple

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class ProcessorAdapter:
    """
    处理器适配器基类
    用于将旧版处理器接口适配到新版应用架构
    """
    
    def __init__(self, processor_class: Type):
        """
        初始化适配器
        
        Args:
            processor_class: 要适配的处理器类
        """
        self.processor_class = processor_class
    
    def __call__(self, input_file: str) -> Any:
        """
        创建处理器实例
        
        Args:
            input_file: 输入文件路径
            
        Returns:
            适配后的处理器实例
        """
        print(f"创建处理器适配器: {self.processor_class.__name__}")
        return self.create_adapted_instance(input_file)
    
    def create_adapted_instance(self, input_file: str) -> Any:
        """
        创建适配后的处理器实例，由子类实现
        
        Args:
            input_file: 输入文件路径
            
        Returns:
            适配后的处理器实例
        """
        raise NotImplementedError("子类必须实现此方法")

class NumPyStepProcessorAdapter(ProcessorAdapter):
    """NumPyStepProcessor适配器"""
    
    def create_adapted_instance(self, input_file: str) -> Any:
        """
        创建NumPyStepProcessor适配后的实例
        
        Args:
            input_file: 输入文件路径
            
        Returns:
            适配后的NumPyStepProcessor实例
        """
        # 直接创建原始处理器
        processor = self.processor_class(input_file)
        return processor

# 旧处理器ID到适配器类的映射
PROCESSOR_ADAPTERS = {
    'numpy': NumPyStepProcessorAdapter,
    # 可以添加更多处理器适配器
}

def get_adapted_processor(processor_id: str, processor_class: Type) -> Type:
    """
    获取适配后的处理器类
    
    Args:
        processor_id: 处理器ID
        processor_class: 原始处理器类
        
    Returns:
        适配后的处理器类实例
    """
    adapter_class = PROCESSOR_ADAPTERS.get(processor_id)
    if adapter_class:
        return adapter_class(processor_class)
    else:
        # 如果没有特定的适配器，使用默认适配器
        return ProcessorAdapter(processor_class) 