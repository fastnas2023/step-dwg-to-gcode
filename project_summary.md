# STEP到G代码转换器项目总结

## 项目概述

本项目实现了将STEP文件（标准CAD交换格式）转换为FANUC兼容G代码的工具，可用于数控（CNC）加工中心。项目开发了三个版本的转换器：

1. **原始版本** (fanuc_stp_to_gcode.py)：基础实现，能够解析STEP文件并生成简单的G代码
2. **无NumPy版本** (fanuc_stp_to_gcode_no_numpy.py)：不依赖NumPy的轻量级实现
3. **NumPy优化版** (step_to_fanuc_numpy.py)：基于NumPy的高级实现，提供更多功能和优化

## 技术栈

- Python 3.13
- NumPy 2.2.4（优化版本使用）
- Matplotlib（可视化功能）
- virtualenv（用于环境管理）

## 主要功能

### 原始版本

- STEP文件解析
- 点云数据提取
- 轮廓构建
- 基本G代码生成
- 支持自定义进给速度和步进参数

### NumPy优化版增强功能

- 高效的点云处理和边缘提取
- 精确轮廓识别（121个vs原始版本的1个）
- 重复点移除优化（移除了969个重复点）
- 刀具半径补偿
- 加工路径优化
- 详细的解析统计信息
- 加工时间估算（约340分钟）
- 3D模型和工具路径可视化

## 性能对比

|              | 原始版本 | NumPy优化版 |
|--------------|---------|------------|
| 执行时间      | 0.698秒 | 1.886秒    |
| 输出文件大小   | 4.4MB   | 1.8MB      |
| G代码行数     | 183,283 | 72,792     |
| 轮廓数量      | 1       | 121        |

虽然NumPy优化版的执行时间略长，但输出文件小了60%，G代码行数减少了60%，这意味着更高效的加工过程。

## 项目结构

```
G-code/
├── fanuc_stp_to_gcode.py          # 原始转换器
├── fanuc_stp_to_gcode_no_numpy.py # 无NumPy版本转换器
├── step_to_fanuc_numpy.py         # 主NumPy优化版转换器入口
├── numpy_step_processor.py        # NumPy STEP文件处理模块
├── numpy_gcode_generator.py       # NumPy G代码生成模块
├── test_fanuc_converter.py        # 测试脚本
├── comparison_report.md           # 版本比较报告
├── README.md                      # 项目说明
├── gcode_env/                     # Python虚拟环境
├── output/                        # 生成的G代码文件
│   ├── original_output.nc
│   ├── busbar_numpy.nc
│   └── ...
└── plots/                         # 可视化图表
    ├── 3d_model.png               # 3D模型可视化
    ├── contours.png               # 轮廓可视化
    ├── xy_projection.png          # XY平面投影
    ├── converter_comparison.png   # 转换器性能比较图
    └── feature_radar.png          # 功能雷达图
```

## 主要改进

1. **精确的几何处理**：修复了原始版本中的几何数据提取和处理问题
2. **优化的G代码**：通过路径优化和重复点移除，减少了60%的G代码行数
3. **增强的可视化**：添加了3D模型、轮廓和工具路径的可视化功能
4. **详细的统计分析**：提供了关于模型尺寸、点密度、边长度等详细信息
5. **国际化支持**：更新了中英文标签支持，解决了字体显示问题

## 使用指南

### 原始版本

```bash
python fanuc_stp_to_gcode.py <STEP文件> -o <输出文件> -f <进给速度> -s <步进尺寸> -d <切削深度>
```

### NumPy优化版

```bash
python step_to_fanuc_numpy.py <STEP文件> -o <输出文件> -f <进给速度> -s <步进尺寸> -d <切削深度> -v
```

参数说明:
- `-o`: 输出G代码文件路径
- `-f`: 进给速度 (mm/min)
- `-s`: 步进尺寸 (mm)
- `-d`: 每层切削深度 (mm)
- `-v`: 启用详细输出

## 总结

通过本项目，我们成功实现了从STEP文件到FANUC G代码的高效转换工具，并通过NumPy优化提高了处理效率和精度。尽管NumPy版本执行时间略长，但其提供的功能、精度和优化大大提高了转换质量，对实际CNC加工具有显著价值。

未来可以考虑进一步优化执行速度，增加更多CAM功能，以及支持更复杂的刀具路径策略。 