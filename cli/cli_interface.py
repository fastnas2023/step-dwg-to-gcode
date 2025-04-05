#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
命令行界面模块
提供命令行工具来转换STEP/DWG文件到G代码
"""

import os
import sys
import argparse
from datetime import datetime

# 添加项目根目录到系统路径
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 导入应用模块
from app import OUTPUT_DIR, SAMPLES_DIR
from config.app_config import DEFAULT_MACHINING_PARAMS, SUPPORTED_CONTROLLERS, SUPPORTED_CONVERTERS, DEFAULT_CONTROLLER, DEFAULT_CONVERTER
from app.controllers import get_controller_by_id
from app.processors import get_processor_by_id

def print_banner():
    """打印程序横幅"""
    banner = """
    =====================================================
     STEP/DWG 到 G代码转换器 | STEP/DWG to G-code Converter
    =====================================================
    """
    print(banner)

def list_supported_controllers():
    """列出支持的控制器"""
    print("\n支持的控制器类型:")
    for controller in SUPPORTED_CONTROLLERS:
        print(f"  - {controller['id']}: {controller['name']} - {controller['description']}")

def list_supported_converters():
    """列出支持的转换器"""
    print("\n支持的转换器类型:")
    for converter in SUPPORTED_CONVERTERS:
        print(f"  - {converter['id']}: {converter['name']} - {converter['description']}")

def list_samples():
    """列出样例文件"""
    print("\n可用的样例文件:")
    samples = []
    for filename in os.listdir(SAMPLES_DIR):
        if filename.lower().endswith(('.stp', '.step', '.dwg', '.dxf')):
            file_path = os.path.join(SAMPLES_DIR, filename)
            file_size = os.path.getsize(file_path) / 1024  # KB
            samples.append((filename, file_size))
    
    # 排序并打印
    for i, (filename, size) in enumerate(sorted(samples, key=lambda x: x[0])):
        print(f"  {i+1}. {filename} ({size:.1f} KB)")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='STEP/DWG到G代码转换器命令行工具')
    
    # 基本参数
    parser.add_argument('-i', '--input', help='输入文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-c', '--controller', default=DEFAULT_CONTROLLER, 
                        help=f'CNC控制器类型，默认: {DEFAULT_CONTROLLER}')
    parser.add_argument('-p', '--processor', default=DEFAULT_CONVERTER, 
                        help=f'文件处理器类型，默认: {DEFAULT_CONVERTER}')
    
    # 加工参数
    parser.add_argument('--feed-rate', type=float, default=DEFAULT_MACHINING_PARAMS['FEED_RATE'],
                        help=f'进给速率 (mm/min)，默认: {DEFAULT_MACHINING_PARAMS["FEED_RATE"]}')
    parser.add_argument('--rapid-feed-rate', type=float, default=DEFAULT_MACHINING_PARAMS['RAPID_FEED_RATE'],
                        help=f'快速进给速率 (mm/min)，默认: {DEFAULT_MACHINING_PARAMS["RAPID_FEED_RATE"]}')
    parser.add_argument('--safety-height', type=float, default=DEFAULT_MACHINING_PARAMS['SAFETY_HEIGHT'],
                        help=f'安全高度 (mm)，默认: {DEFAULT_MACHINING_PARAMS["SAFETY_HEIGHT"]}')
    parser.add_argument('--cut-depth', type=float, default=DEFAULT_MACHINING_PARAMS['CUT_DEPTH'],
                        help=f'切削深度 (mm)，默认: {DEFAULT_MACHINING_PARAMS["CUT_DEPTH"]}')
    parser.add_argument('--tool-diameter', type=float, default=DEFAULT_MACHINING_PARAMS['TOOL_DIAMETER'],
                        help=f'刀具直径 (mm)，默认: {DEFAULT_MACHINING_PARAMS["TOOL_DIAMETER"]}')
    parser.add_argument('--spindle-speed', type=int, default=DEFAULT_MACHINING_PARAMS['SPINDLE_SPEED'],
                        help=f'主轴转速 (RPM)，默认: {DEFAULT_MACHINING_PARAMS["SPINDLE_SPEED"]}')
    
    # 信息相关参数
    parser.add_argument('--list-controllers', action='store_true', help='列出所有支持的控制器')
    parser.add_argument('--list-processors', action='store_true', help='列出所有支持的处理器')
    parser.add_argument('--list-samples', action='store_true', help='列出所有样例文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细输出')
    
    # 交互模式
    parser.add_argument('--interactive', '-I', action='store_true', help='启动交互模式')
    
    return parser.parse_args()

def interactive_mode():
    """交互式命令行模式"""
    print_banner()
    print("\n欢迎使用交互模式! 请按照提示进行操作:\n")
    
    # 选择输入文件
    print("请选择输入文件:")
    print("1. 使用样例文件")
    print("2. 输入文件路径")
    choice = input("\n请选择 [1/2]: ").strip()
    
    if choice == '1':
        list_samples()
        sample_choice = input("\n请输入样例文件编号: ").strip()
        try:
            sample_idx = int(sample_choice) - 1
            samples = sorted([f for f in os.listdir(SAMPLES_DIR) 
                              if f.lower().endswith(('.stp', '.step', '.dwg', '.dxf'))])
            input_file = os.path.join(SAMPLES_DIR, samples[sample_idx])
        except (ValueError, IndexError):
            print("无效选择，退出程序。")
            return 1
    else:
        input_path = input("\n请输入文件路径: ").strip()
        if not os.path.exists(input_path):
            print(f"错误: 文件'{input_path}'不存在，退出程序。")
            return 1
        input_file = input_path
    
    # 选择控制器类型
    list_supported_controllers()
    controller_id = input(f"\n请选择控制器类型 [默认: {DEFAULT_CONTROLLER}]: ").strip()
    if not controller_id:
        controller_id = DEFAULT_CONTROLLER
    
    controller_ids = [c['id'] for c in SUPPORTED_CONTROLLERS]
    if controller_id not in controller_ids:
        print(f"错误: 控制器类型'{controller_id}'不支持，退出程序。")
        return 1
    
    # 选择处理器类型
    list_supported_converters()
    processor_id = input(f"\n请选择处理器类型 [默认: {DEFAULT_CONVERTER}]: ").strip()
    if not processor_id:
        processor_id = DEFAULT_CONVERTER
    
    processor_ids = [p['id'] for p in SUPPORTED_CONVERTERS]
    if processor_id not in processor_ids:
        print(f"错误: 处理器类型'{processor_id}'不支持，退出程序。")
        return 1
    
    # 输出文件路径
    default_output = os.path.join(
        OUTPUT_DIR, 
        f"{os.path.splitext(os.path.basename(input_file))[0]}_{controller_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.nc"
    )
    output_file = input(f"\n请输入输出文件路径 [默认: {default_output}]: ").strip()
    if not output_file:
        output_file = default_output
    
    # 加工参数
    print("\n加工参数设置 (直接回车使用默认值):")
    
    params = {}
    for key, default in DEFAULT_MACHINING_PARAMS.items():
        try:
            value = input(f"  {key} [{default}]: ").strip()
            if value:
                if isinstance(default, (int, float)):
                    params[key] = float(value) if isinstance(default, float) else int(value)
                else:
                    params[key] = value
            else:
                params[key] = default
        except ValueError:
            print(f"  无效值，使用默认值 {default}")
            params[key] = default
    
    # 确认信息
    print("\n将使用以下设置:")
    print(f"  输入文件: {input_file}")
    print(f"  输出文件: {output_file}")
    print(f"  控制器类型: {controller_id}")
    print(f"  处理器类型: {processor_id}")
    print("  加工参数:")
    for key, value in params.items():
        print(f"    - {key}: {value}")
    
    confirm = input("\n确认开始转换? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("操作已取消，退出程序。")
        return 0
    
    # 执行转换
    return convert_file(input_file, output_file, controller_id, processor_id, params, verbose=True)

def convert_file(input_file, output_file, controller_id, processor_id, params, verbose=False):
    """转换文件"""
    try:
        if verbose:
            print(f"\n开始转换文件 '{input_file}'...")
        
        # 获取处理器和控制器
        processor_class = get_processor_by_id(processor_id)
        controller_class = get_controller_by_id(controller_id)
        
        if verbose:
            print(f"使用处理器: {processor_class.__name__}")
            print(f"使用控制器: {controller_class.__name__}")
            print("解析文件中...")
        
        # 创建处理器实例并解析文件
        processor = processor_class()
        processor.parse_file(input_file)
        
        if verbose:
            print("提取几何边缘...")
        
        # 提取边缘
        edges = processor.extract_edges()
        
        if verbose:
            print(f"创建G代码生成器 (控制器: {controller_id})...")
        
        # 创建控制器实例
        controller = controller_class(params)
        
        if verbose:
            print("生成G代码...")
        
        # 生成G代码
        gcode = controller.generate_gcode(edges)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # 写入输出文件
        with open(output_file, 'w') as f:
            f.write(gcode)
        
        if verbose:
            print(f"\nG代码已成功生成并保存到 '{output_file}'")
            print(f"文件大小: {os.path.getsize(output_file) / 1024:.1f} KB")
        
        return 0
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1

def main():
    """主函数"""
    args = parse_arguments()
    
    # 处理信息相关参数
    if args.list_controllers:
        print_banner()
        list_supported_controllers()
        return 0
    
    if args.list_processors:
        print_banner()
        list_supported_converters()
        return 0
    
    if args.list_samples:
        print_banner()
        list_samples()
        return 0
    
    # 进入交互模式
    if args.interactive:
        return interactive_mode()
    
    # 非交互模式，检查必要参数
    if not args.input:
        print("错误: 必须提供输入文件路径 (使用 -i 或 --input)")
        return 1
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件 '{args.input}' 不存在")
        return 1
    
    # 确定输出文件路径
    if not args.output:
        args.output = os.path.join(
            OUTPUT_DIR, 
            f"{os.path.splitext(os.path.basename(args.input))[0]}_{args.controller}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.nc"
        )
    
    # 整理加工参数
    params = {
        'FEED_RATE': args.feed_rate,
        'RAPID_FEED_RATE': args.rapid_feed_rate,
        'SAFETY_HEIGHT': args.safety_height,
        'CUT_DEPTH': args.cut_depth,
        'TOOL_DIAMETER': args.tool_diameter,
        'SPINDLE_SPEED': args.spindle_speed
    }
    
    # 执行转换
    return convert_file(args.input, args.output, args.controller, args.processor, params, args.verbose)

if __name__ == "__main__":
    sys.exit(main()) 