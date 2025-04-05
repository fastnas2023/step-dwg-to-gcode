#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
控制器适配器模块
通过适配模式，使旧版控制器适配新的应用架构
"""

import sys
import os
import inspect
from typing import Any, Dict, Type

# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class ControllerAdapter:
    """
    控制器适配器基类
    用于将旧版控制器接口适配到新版应用架构
    """
    
    def __init__(self, controller_class: Type):
        """
        初始化适配器
        
        Args:
            controller_class: 要适配的控制器类
        """
        self.controller_class = controller_class
    
    def __call__(self, **params: Dict[str, Any]) -> Any:
        """
        创建控制器实例
        
        Args:
            **params: 控制器参数
            
        Returns:
            适配后的控制器实例
        """
        print(f"创建控制器适配器: {self.controller_class.__name__}")
        return self.create_adapted_instance(**params)
    
    def create_adapted_instance(self, **params: Dict[str, Any]) -> Any:
        """
        创建适配后的控制器实例，由子类实现
        
        Args:
            **params: 控制器参数
            
        Returns:
            适配后的控制器实例
        """
        raise NotImplementedError("子类必须实现此方法")

class GcodeGeneratorAdapter(ControllerAdapter):
    """G代码生成器适配器"""
    
    def create_adapted_instance(self, **params) -> Any:
        """
        创建G代码生成器适配后的实例
        
        Args:
            **params: 控制器参数
            
        Returns:
            适配后的G代码生成器实例
        """
        # 获取控制器类的__init__方法签名
        sig = inspect.signature(self.controller_class.__init__)
        valid_params = {}
        
        # 调试日志
        print(f"控制器类 {self.controller_class.__name__} 接受的参数: {list(sig.parameters.keys())}")
        print(f"传入的参数: {params}")
        
        # 过滤参数，只保留控制器类支持的参数
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            if param_name in params and params[param_name] is not None:
                valid_params[param_name] = params[param_name]
                print(f"使用参数: {param_name}={params[param_name]}")
            elif param.default is not param.empty:
                # 如果参数有默认值且未提供，保留默认值
                print(f"使用默认参数: {param_name}={param.default}")
        
        # 如果rapid_feed_rate在参数中但不被控制器支持，则记录日志
        if 'rapid_feed_rate' in params and 'rapid_feed_rate' not in sig.parameters:
            print(f"警告: 控制器 {self.controller_class.__name__} 不支持 rapid_feed_rate 参数，已忽略该参数")
            
        print(f"最终使用的有效参数: {valid_params}")
        # 创建控制器实例
        return self.controller_class(**valid_params)

# 旧控制器ID到适配器类的映射
CONTROLLER_ADAPTERS = {
    'fanuc': GcodeGeneratorAdapter,
    'siemens': GcodeGeneratorAdapter,
    'haas': GcodeGeneratorAdapter,
    'heidenhain': GcodeGeneratorAdapter,
    'generic': GcodeGeneratorAdapter,
    'numpy': GcodeGeneratorAdapter,
    # 可以添加更多控制器适配器
}

def get_adapted_controller(controller_id: str, controller_class: Type) -> Type:
    """
    获取适配后的控制器类
    
    Args:
        controller_id: 控制器ID
        controller_class: 原始控制器类
        
    Returns:
        适配后的控制器类实例
    """
    adapter_class = CONTROLLER_ADAPTERS.get(controller_id)
    if adapter_class:
        return adapter_class(controller_class)
    else:
        # 如果没有特定的适配器，使用默认适配器
        return ControllerAdapter(controller_class) 