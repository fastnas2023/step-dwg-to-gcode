#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
STEP文件到FANUC G代码转换工具 (NumPy版本)
这个工具使用优化的NumPy处理器处理STEP文件并生成FANUC CNC控制器的G代码
"""

import os
import sys
import argparse
import time
import platform
import importlib.util
import traceback

# 检测系统平台
system_platform = platform.machine().lower()

# 添加项目根目录到PATH，以便引入其他模块
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.append(root_dir)
sys.path.append(script_dir)

print(f"当前系统平台: {system_platform}")
print(f"脚本目录: {script_dir}")
print(f"根目录: {root_dir}")

# 检查是否在ARM架构上运行
if system_platform in ('aarch64', 'arm64'):
    # ARM架构使用简化版处理器
    print("检测到ARM架构，使用简化版STEP处理器")
    
    # 首先检查使用相对路径的step_processor_fallback.py
    fallback_module_path = os.path.join(script_dir, 'step_processor_fallback.py')
    if os.path.exists(fallback_module_path):
        print(f"使用当前目录的step_processor_fallback.py: {fallback_module_path}")
        from step_processor_fallback import SimpleStepProcessor as StepProcessor
    else:
        # 然后检查根目录
        root_fallback_path = os.path.join(root_dir, 'step_processor_fallback.py')
        if os.path.exists(root_fallback_path):
            print(f"使用根目录的step_processor_fallback.py: {root_fallback_path}")
            sys.path.append(root_dir)  # 确保可以导入根目录的模块
            from step_processor_fallback import SimpleStepProcessor as StepProcessor
        else:
            raise ImportError("在ARM架构上需要step_processor_fallback.py，但无法找到该文件")
else:
    try:
        # 非ARM架构优先使用NumPy处理器
        print("在x86/x64架构上使用标准NumPy处理器")
        
        # 优先尝试导入numpy_step_processor
        numpy_processor_path = os.path.join(script_dir, 'numpy_step_processor.py')
        if os.path.exists(numpy_processor_path):
            print(f"使用当前目录的numpy_step_processor.py: {numpy_processor_path}")
            from numpy_step_processor import NumPyStepProcessor as StepProcessor
        else:
            # 如果找不到，尝试使用备用的fallback处理器
            fallback_module_path = os.path.join(script_dir, 'step_processor_fallback.py') 
            if os.path.exists(fallback_module_path):
                print(f"标准处理器未找到，使用fallback处理器: {fallback_module_path}")
                from step_processor_fallback import SimpleStepProcessor as StepProcessor
            else:
                root_fallback_path = os.path.join(root_dir, 'step_processor_fallback.py')
                if os.path.exists(root_fallback_path):
                    print(f"使用根目录的step_processor_fallback.py: {root_fallback_path}")
                    sys.path.append(root_dir)
                    from step_processor_fallback import SimpleStepProcessor as StepProcessor
                else:
                    raise ImportError("无法找到任何可用的STEP处理器模块")
    except ImportError as e:
        print(f"导入NumPy处理器出错，尝试使用备用处理器: {str(e)}")
        try:
            # 尝试使用备用的fallback处理器
            from step_processor_fallback import SimpleStepProcessor as StepProcessor
        except ImportError:
            print("备用处理器也不可用，无法继续")
            raise

# 导入G代码生成器
try:
    from numpy_gcode_generator import NumPyGCodeGenerator
except ImportError as e:
    print(f"导入G代码生成器时出错: {str(e)}")
    sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='将STEP文件转换为FANUC G代码')
    parser.add_argument('input_file', help='输入的STEP文件路径')
    parser.add_argument('-o', '--output', help='输出的G代码文件路径')
    parser.add_argument('-f', '--feed-rate', type=float, default=500.0, help='进给速率(mm/min)')
    parser.add_argument('-r', '--rapid-height', type=float, default=10.0, help='快速移动高度(mm)')
    parser.add_argument('-d', '--cut-depth', type=float, default=0.5, help='切削深度(mm)')
    parser.add_argument('-t', '--tool-diameter', type=float, default=3.0, help='刀具直径(mm)')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细输出')
    parser.add_argument('--preview-only', action='store_true', help='仅生成预览，不生成G代码')
    parser.add_argument('--preview-output', help='预览图像的输出路径')
    
    args = parser.parse_args()
    
    # 确认输入文件存在
    if not os.path.exists(args.input_file):
        print(f"错误: 输入文件不存在 - {args.input_file}")
        return 1
    
    # 设置默认输出文件
    if not args.output and not args.preview_only:
        args.output = os.path.splitext(args.input_file)[0] + '.nc'
    
    start_time = time.time()
    
    # 初始化STEP处理器
    try:
        processor = StepProcessor(args.input_file)
    except Exception as e:
        print(f"初始化STEP处理器时出错: {str(e)}")
        traceback.print_exc()
        return 1
    
    # 处理STEP文件
    if args.preview_only:
        # 只生成预览
        success, preview_path, stats = processor.process(preview_only=True, preview_output=args.preview_output)
        if success:
            print(f"预览生成成功: {preview_path}")
            print(f"模型统计: 点: {stats['points']}, 边: {stats['edges']}")
            print(f"处理用时: {time.time() - start_time:.2f} 秒")
            return 0
        else:
            print("预览生成失败")
            return 1
    
    # 完整处理流程
    try:
        print(f"处理STEP文件: {args.input_file}")
        path_array, bounds, stats = processor.process()
        
        if path_array is None:
            print("处理STEP文件失败")
            return 1
        
        print(f"STEP文件处理完成，边数量: {stats['edges']}")
        print(f"模型边界: X: {bounds[0]:.3f} 到 {bounds[3]:.3f}, " + 
              f"Y: {bounds[1]:.3f} 到 {bounds[4]:.3f}, " + 
              f"Z: {bounds[2]:.3f} 到 {bounds[5]:.3f}")
        
        # 生成G代码
        print(f"生成G代码: {args.output}")
        
        # 获取Z坐标中值作为切削平面
        cut_z = 0.0
        if bounds is not None:
            cut_z = bounds[2]  # 使用最小Z值作为切削平面
        
        # 创建G代码生成器
        gcode_gen = NumPyGCodeGenerator(
            filename=args.output,
            feed_rate=args.feed_rate,
            rapid_height=args.rapid_height,
            cut_depth=args.cut_depth,
            tool_diameter=args.tool_diameter,
            cut_z=cut_z
        )
        
        # 从路径生成G代码
        gcode_gen.generate_from_path(path_array)
        
        print(f"G代码生成成功: {args.output}")
        print(f"预计加工时间: {gcode_gen.get_estimated_time():.2f} 分钟")
        print(f"总处理用时: {time.time() - start_time:.2f} 秒")
        
        return 0
    
    except Exception as e:
        print(f"生成G代码时出错: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main()) 