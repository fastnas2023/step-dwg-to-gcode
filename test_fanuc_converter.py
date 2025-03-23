#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FANUC G代码转换器测试脚本
该脚本测试STEP文件到G代码的转换功能，包括标准版本和无NumPy依赖版本
"""

import os
import sys
import subprocess
import tempfile
import shutil
import time
import re

# 测试文件和输出目录
TEST_FILE = "INTER BUSBAR REAR-1.STP"
TEST_OUTPUT_DIR = "test_output"

# 测试结果计数
tests_passed = 0
tests_failed = 0
tests_skipped = 0

def print_header(text):
    """打印格式化的标题"""
    print("\n" + "=" * 70)
    print(f" {text} ".center(70, "="))
    print("=" * 70)

def print_result(name, passed, message=""):
    """打印测试结果"""
    global tests_passed, tests_failed
    
    if passed:
        result = "\033[92m通过\033[0m"  # 绿色
        tests_passed += 1
    else:
        result = "\033[91m失败\033[0m"  # 红色
        tests_failed += 1
        
    print(f"[{result}] {name}")
    if message:
        print(f"      {message}")

def check_file_exists(file_path):
    """检查文件是否存在"""
    exists = os.path.isfile(file_path)
    return exists

def check_gcode_content(file_path, patterns):
    """检查G代码内容是否包含预期模式"""
    if not check_file_exists(file_path):
        return False, f"文件不存在: {file_path}"
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        for pattern, expected in patterns:
            matches = re.search(pattern, content)
            if expected and not matches:
                return False, f"未找到预期模式: {pattern}"
            elif not expected and matches:
                return False, f"发现不应存在的模式: {pattern}"
        
        return True, "内容验证通过"
    except Exception as e:
        return False, f"检查内容时出错: {e}"

def run_command(cmd, name):
    """运行命令并返回结果"""
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        success = result.returncode == 0
        message = result.stdout if success else result.stderr
        return success, message, result.returncode
    except Exception as e:
        return False, str(e), -1

def setup_test_environment():
    """设置测试环境"""
    print_header("设置测试环境")
    
    # 检查测试文件
    test_file_exists = check_file_exists(TEST_FILE)
    print_result("检查测试文件存在", test_file_exists)
    if not test_file_exists:
        print(f"错误: 找不到测试文件 {TEST_FILE}")
        print("请确保测试文件位于当前目录中")
        return False
    
    # 创建输出目录
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)
    os.makedirs(TEST_OUTPUT_DIR)
    print_result("创建输出目录", True)
    
    return True

def test_fanuc_basic_functionality():
    """测试标准FANUC转换器的基本功能"""
    print_header("测试标准FANUC转换器基本功能")
    
    # 输出文件
    output_file = os.path.join(TEST_OUTPUT_DIR, "test_basic_fanuc.nc")
    
    # 运行转换命令
    cmd = [
        "python", "fanuc_stp_to_gcode.py",
        TEST_FILE,
        "-o", output_file,
        "-p", "2000"
    ]
    success, message, _ = run_command(cmd, "执行基本FANUC转换")
    print_result("命令执行", success)
    
    if not success:
        return False
    
    # 检查输出文件是否存在
    file_exists = check_file_exists(output_file)
    print_result("检查输出文件存在", file_exists)
    
    if not file_exists:
        return False
    
    # 检查内容
    patterns = [
        (r"O2000", True),  # 应包含程序号
        (r"G0 G17 G40 G49 G80 G90", True),  # 应包含标准FANUC初始化代码
        (r"G91 G28 Z0", True),  # 应包含参考点返回
        (r"M30", True),  # 应包含程序结束
        (r"%", True)  # 应包含FANUC文件结束符
    ]
    
    content_valid, message = check_gcode_content(output_file, patterns)
    print_result("检查G代码内容", content_valid, message)
    
    return content_valid

def test_no_numpy_basic_functionality():
    """测试无NumPy依赖版本的基本功能"""
    print_header("测试无NumPy依赖版本基本功能")
    
    # 输出文件
    output_file = os.path.join(TEST_OUTPUT_DIR, "test_basic_no_numpy.nc")
    
    # 运行转换命令
    cmd = [
        "python", "fanuc_stp_to_gcode_no_numpy.py",
        TEST_FILE,
        "-o", output_file,
        "-p", "3000"
    ]
    success, message, _ = run_command(cmd, "执行无NumPy依赖版本转换")
    print_result("命令执行", success)
    
    if not success:
        return False
    
    # 检查输出文件是否存在
    file_exists = check_file_exists(output_file)
    print_result("检查输出文件存在", file_exists)
    
    if not file_exists:
        return False
    
    # 检查内容
    patterns = [
        (r"O3000", True),  # 应包含程序号
        (r"G0 G17 G40 G49 G80 G90", True),  # 应包含标准FANUC初始化代码
        (r"G91 G28 Z0", True),  # 应包含参考点返回
        (r"M30", True),  # 应包含程序结束
        (r"%", True)  # 应包含FANUC文件结束符
    ]
    
    content_valid, message = check_gcode_content(output_file, patterns)
    print_result("检查G代码内容", content_valid, message)
    
    return content_valid

def test_parameter_customization():
    """测试参数定制功能"""
    print_header("测试参数定制")
    
    # 输出文件
    output_file = os.path.join(TEST_OUTPUT_DIR, "test_params.nc")
    
    # 运行转换命令
    cmd = [
        "python", "fanuc_stp_to_gcode.py",
        TEST_FILE,
        "-o", output_file,
        "-p", "4000",  # 程序号
        "-f", "600",   # 进给率
        "-s", "20",    # 安全高度
        "-d", "1.0"    # 切割深度
    ]
    success, message, _ = run_command(cmd, "执行带自定义参数的转换")
    print_result("命令执行", success)
    
    if not success:
        return False
    
    # 检查内容
    patterns = [
        (r"O4000", True),  # 应包含自定义程序号
        (r"F600", True),   # 应包含自定义进给率
        (r"Z20", True)     # 应包含自定义安全高度
    ]
    
    content_valid, message = check_gcode_content(output_file, patterns)
    print_result("检查自定义参数应用", content_valid, message)
    
    return content_valid

def test_no_numpy_parameter_customization():
    """测试无NumPy版本的参数定制功能"""
    print_header("测试无NumPy版本参数定制")
    
    # 输出文件
    output_file = os.path.join(TEST_OUTPUT_DIR, "test_no_numpy_params.nc")
    
    # 运行转换命令
    cmd = [
        "python", "fanuc_stp_to_gcode_no_numpy.py",
        TEST_FILE,
        "-o", output_file,
        "-p", "5000",  # 程序号
        "-f", "800",   # 进给率
        "-s", "25",    # 安全高度
        "-d", "1.5"    # 切割深度
    ]
    success, message, _ = run_command(cmd, "执行带自定义参数的无NumPy版本转换")
    print_result("命令执行", success)
    
    if not success:
        return False
    
    # 检查内容
    patterns = [
        (r"O5000", True),  # 应包含自定义程序号
        (r"F800", True),   # 应包含自定义进给率
        (r"Z25", True)     # 应包含自定义安全高度
    ]
    
    content_valid, message = check_gcode_content(output_file, patterns)
    print_result("检查自定义参数应用", content_valid, message)
    
    return content_valid

def test_example_script():
    """测试示例脚本"""
    print_header("测试示例脚本")
    
    # 预期的输出文件
    output_file = os.path.join("output", f"INTER BUSBAR REAR-1_P1000.nc")
    
    # 如果输出目录已存在，先删除
    if os.path.exists("output"):
        shutil.rmtree("output")
    
    # 运行示例脚本
    cmd = ["python", "process_inter_busbar.py"]
    success, message, _ = run_command(cmd, "执行示例脚本")
    print_result("命令执行", success)
    
    if not success:
        return False
    
    # 检查输出文件是否存在
    file_exists = check_file_exists(output_file)
    print_result("检查输出文件存在", file_exists)
    
    return file_exists

def test_no_numpy_example_script():
    """测试无NumPy版本示例脚本"""
    print_header("测试无NumPy版本示例脚本")
    
    # 预期的输出文件
    output_file = os.path.join("output", f"INTER BUSBAR REAR-1_P1000.nc")
    
    # 如果输出目录已存在，先删除
    if os.path.exists("output"):
        shutil.rmtree("output")
    
    # 运行示例脚本
    cmd = ["python", "process_inter_busbar_no_numpy.py"]
    success, message, _ = run_command(cmd, "执行无NumPy版本示例脚本")
    print_result("命令执行", success)
    
    if not success:
        return False
    
    # 检查输出文件是否存在
    file_exists = check_file_exists(output_file)
    print_result("检查输出文件存在", file_exists)
    
    return file_exists

def test_numpy_import():
    """测试NumPy导入"""
    print_header("测试NumPy导入")
    
    cmd = [sys.executable, "-c", "import numpy; print('成功导入NumPy')"]
    success, message, _ = run_command(cmd, "导入NumPy")
    print_result("NumPy可用性", success)
    
    return success

def main():
    """主函数"""
    global tests_passed, tests_failed, tests_skipped
    
    print_header("FANUC G代码转换器测试")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print(f"测试文件: {TEST_FILE}")
    
    # 设置测试环境
    if not setup_test_environment():
        print("测试环境设置失败，终止测试")
        return 1
    
    # 检查NumPy是否可用
    numpy_available = test_numpy_import()
    
    # 测试标准版本
    if numpy_available:
        fanuc_basic_passed = test_fanuc_basic_functionality()
        param_custom_passed = test_parameter_customization()
        example_passed = test_example_script()
    else:
        print("\n警告: NumPy不可用，跳过标准版本测试")
        tests_skipped += 3
        fanuc_basic_passed = False
        param_custom_passed = False
        example_passed = False
    
    # 测试无NumPy版本
    no_numpy_basic_passed = test_no_numpy_basic_functionality()
    no_numpy_param_passed = test_no_numpy_parameter_customization()
    no_numpy_example_passed = test_no_numpy_example_script()
    
    # 输出测试摘要
    print_header("测试摘要")
    print(f"测试通过: {tests_passed}")
    print(f"测试失败: {tests_failed}")
    print(f"测试跳过: {tests_skipped}")
    print(f"总计测试: {tests_passed + tests_failed + tests_skipped}")
    
    # 输出测试结果表
    print("\n测试结果:")
    if numpy_available:
        print(f"标准FANUC转换器基本功能: {'通过' if fanuc_basic_passed else '失败'}")
        print(f"标准版本参数定制: {'通过' if param_custom_passed else '失败'}")
        print(f"标准版本示例脚本: {'通过' if example_passed else '失败'}")
    else:
        print("标准FANUC转换器测试: 已跳过 (NumPy不可用)")
    
    print(f"无NumPy版本基本功能: {'通过' if no_numpy_basic_passed else '失败'}")
    print(f"无NumPy版本参数定制: {'通过' if no_numpy_param_passed else '失败'}")
    print(f"无NumPy版本示例脚本: {'通过' if no_numpy_example_passed else '失败'}")
    
    # 输出结论
    if tests_failed == 0:
        print("\n结论: 所有测试通过!")
        return 0
    else:
        print(f"\n结论: 有 {tests_failed} 个测试失败!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 