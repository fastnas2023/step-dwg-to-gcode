#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试不同CNC控制器的G代码生成器
"""

import os
import time
from cnc_controller_factory import CncControllerFactory

def create_test_points():
    """创建测试点集"""
    # 创建一个简单的方形轮廓
    points = []
    
    # 方形边长
    size = 50.0
    
    # 定义顶点(顺时针)
    points.append((0, 0, 0))
    points.append((size, 0, 0))
    points.append((size, size, 0))
    points.append((0, size, 0))
    points.append((0, 0, 0))  # 回到起点完成闭环
    
    return points

def test_controller(controller_type, output_dir="test_output"):
    """
    测试特定控制器的G代码生成
    
    参数:
    controller_type (str): 控制器类型
    output_dir (str): 输出目录
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 设置参数
    params = {
        "feed_rate": 500,
        "safety_height": 10,
        "cut_depth": -2,
        "tool_number": 1,
        "spindle_speed": 1000
    }
    
    # 创建控制器
    try:
        controller = CncControllerFactory.create_controller(controller_type, **params)
    except ValueError as e:
        print(f"错误: {e}")
        return
    
    # 创建测试点
    points = create_test_points()
    
    # 生成G代码
    gcode = controller.generate_gcode(points)
    
    # 创建输出文件名
    output_file = os.path.join(output_dir, f"{controller_type}_test.nc")
    
    # 写入G代码
    with open(output_file, 'w') as f:
        for line in gcode:
            f.write(line + "\n")
    
    print(f"G代码已生成: {output_file}")
    
    # 打印部分G代码以供预览
    print(f"\n{controller_type.upper()} 控制器G代码预览:")
    print("-" * 50)
    
    # 打印前10行和最后5行
    preview_lines = 10
    for i, line in enumerate(gcode):
        if i < preview_lines or i >= len(gcode) - 5:
            print(line)
        elif i == preview_lines:
            print("... (省略部分内容) ...")
    
    print("-" * 50 + "\n")

def main():
    """主函数"""
    print("CNC控制器G代码生成测试")
    print("=" * 50)
    
    # 获取支持的控制器列表
    controllers = CncControllerFactory.get_supported_controllers()
    
    print("支持的控制器:")
    for i, controller in enumerate(controllers):
        print(f"{i+1}. {controller['name']} - {controller['description']}")
    
    print("\n生成所有控制器的测试G代码...")
    
    # 为每种控制器生成测试G代码
    for controller in controllers:
        test_controller(controller["id"])
    
    print("\n测试完成！")

if __name__ == "__main__":
    main() 