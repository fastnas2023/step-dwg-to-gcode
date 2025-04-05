#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
STEP/DWG到G代码转换服务 - Web界面
此脚本提供基于Flask的Web界面，用于上传和处理STEP/DWG文件
"""

import os
import shutil
import subprocess
import uuid
import datetime
import re
import zipfile
import time
import sys
import json
import platform
from flask import Flask, request, render_template, redirect, url_for, flash, session, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path

# 添加项目根目录到PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
TEMP_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
PLOTS_FOLDER = os.path.join(STATIC_FOLDER, 'plots')
STATIC_PLOTS_FOLDER = os.path.join(STATIC_FOLDER, 'static/plots')
ALLOWED_EXTENSIONS = {'stp', 'step', 'dwg', 'dxf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

# 应用初始化
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER
app.config['STATIC_FOLDER'] = STATIC_FOLDER
app.config['PLOTS_FOLDER'] = PLOTS_FOLDER
app.config['STATIC_PLOTS_FOLDER'] = STATIC_PLOTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.secret_key = os.urandom(24)

# 确保各目录存在
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, TEMP_FOLDER, PLOTS_FOLDER, STATIC_PLOTS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# 辅助函数
def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file_path):
    """获取文件大小的可读表示"""
    size_bytes = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def count_file_lines(file_path):
    """计算文件行数"""
    with open(file_path, 'r') as f:
        return sum(1 for _ in f)

def extract_processing_time(gcode_content):
    """尝试从G代码或控制台输出中提取加工时间估计"""
    time_pattern = r"预计加工时间[：:]\s*([0-9]+\.?[0-9]*)\s*分钟"
    estimated_pattern = r"estimated\s+processing\s+time[：:]\s*([0-9]+\.?[0-9]*)\s*minutes"
    
    match = re.search(time_pattern, gcode_content, re.IGNORECASE)
    if match:
        return f"{match.group(1)} 分钟"
    
    match = re.search(estimated_pattern, gcode_content, re.IGNORECASE)
    if match:
        return f"{match.group(1)} 分钟"
    
    return "未知"

def get_gcode_stats(file_path):
    """获取G代码文件的统计信息"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        stats = {
            'line_count': count_file_lines(file_path),
            'file_size': get_file_size(file_path),
            'estimated_time': extract_processing_time(content)
        }
        return stats
    except Exception as e:
        app.logger.error(f"获取G代码统计信息出错: {str(e)}")
        return {
            'line_count': 0,
            'file_size': "未知",
            'estimated_time': "未知"
        }

def get_gcode_preview(file_path, max_lines=100):
    """获取G代码文件的前N行预览"""
    try:
        with open(file_path, 'r') as f:
            lines = [line.rstrip() for line in f.readlines()[:max_lines]]
        return lines
    except Exception as e:
        app.logger.error(f"获取G代码预览出错: {str(e)}")
        return ["无法读取G代码预览"]

def prepare_user_session():
    """准备用户会话，生成唯一会话ID"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # 创建会话特定的目录
    session_plots_dir = os.path.join(app.config['STATIC_PLOTS_FOLDER'], session['session_id'])
    os.makedirs(session_plots_dir, exist_ok=True)
    
    return session['session_id']

def copy_plots_to_static(source_dir, session_id):
    """复制生成的可视化图表到静态目录"""
    session_plots_dir = os.path.join(app.config['STATIC_PLOTS_FOLDER'], session_id)
    os.makedirs(session_plots_dir, exist_ok=True)
    
    # 查找所有PNG文件
    for png_file in Path(source_dir).glob('*.png'):
        shutil.copy(png_file, session_plots_dir)
    
    return True

# 页面路由
@app.route('/')
def index():
    """主页"""
    # 生成会话ID用于区分不同用户的文件
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型，请上传STEP、STP、DWG或DXF文件'}), 400
    
    # 使用用户会话ID创建唯一目录
    user_dir = os.path.join(UPLOAD_FOLDER, session.get('user_id', 'default'))
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    
    # 保存文件
    filename = file.filename
    file_path = os.path.join(user_dir, filename)
    file.save(file_path)
    
    # 重定向到预览页面
    return jsonify({
        'success': True,
        'message': '文件上传成功',
        'filename': filename,
        'redirect': url_for('file_preview', filename=filename)
    })

@app.route('/file_preview')
def file_preview():
    """文件预览页面"""
    filename = request.args.get('filename')
    if not filename:
        return redirect(url_for('index'))
    
    user_dir = os.path.join(UPLOAD_FOLDER, session.get('user_id', 'default'))
    file_path = os.path.join(user_dir, filename)
    
    if not os.path.exists(file_path):
        return render_template('error.html', message=f"文件 {filename} 不存在")
    
    # 获取文件信息
    file_size = os.path.getsize(file_path)
    file_size_formatted = f"{file_size / 1024:.2f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.2f} MB"
    
    file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
    file_type = 'step' if file_ext in ['stp', 'step'] else 'dwg' if file_ext in ['dwg', 'dxf'] else 'unknown'
    
    creation_time = datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
    modification_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
    
    # 读取文件内容预览（前100行）
    file_content = ""
    try:
        with open(file_path, 'r', errors='ignore') as f:
            lines = f.readlines()
            file_content = ''.join(lines[:100])
    except:
        file_content = "无法读取文件内容（可能是二进制文件）"
    
    # 对于STEP文件，尝试生成可视化
    has_visualization = False
    visualization_path = ""
    
    if file_type == 'step':
        try:
            # 创建唯一的可视化目录
            visualization_dir = os.path.join(PLOTS_FOLDER, session.get('user_id', 'default'))
            if not os.path.exists(visualization_dir):
                os.makedirs(visualization_dir)
            
            visualization_path = os.path.join(visualization_dir, f"{os.path.splitext(filename)[0]}_preview.png")
            relative_path = os.path.join('static', 'plots', session.get('user_id', 'default'), f"{os.path.splitext(filename)[0]}_preview.png")
            
            # 确定当前平台
            system_platform = platform.machine().lower()
            
            if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'step_processor_fallback.py')):
                processor_module = 'step_processor_fallback' if system_platform in ('aarch64', 'arm64') else 'numpy_step_processor'
                script_path = 'step_to_fanuc_numpy.py' 
            else:
                script_path = os.path.join('web', 'step_to_fanuc_numpy.py')
            
            # 调用处理脚本生成可视化
            cmd = [
                sys.executable,
                script_path,
                file_path,
                '--preview-only',
                '--preview-output', visualization_path
            ]
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 检查结果
            if result.returncode == 0 and os.path.exists(visualization_path):
                has_visualization = True
            else:
                print(f"可视化生成失败: {result.stderr}")
        except Exception as e:
            print(f"生成可视化时出错: {str(e)}")
    
    return render_template('file_preview.html', 
                         filename=filename,
                         file_size=file_size_formatted,
                         file_type=file_type,
                         preview_type=file_type,
                         creation_time=creation_time,
                         modification_time=modification_time,
                         file_content=file_content,
                         has_visualization=has_visualization,
                         visualization_path=relative_path if has_visualization else "")

@app.route('/proceed_to_conversion')
def proceed_to_conversion():
    """继续到相应的转换页面"""
    if 'uploaded_file' not in session:
        flash('请先上传文件', 'error')
        return redirect(url_for('index'))
    
    filename = session.get('original_filename', '')
    
    # 根据文件类型决定下一步
    if filename.lower().endswith(('.stp', '.step')):
        return redirect(url_for('step_conversion'))
    elif filename.lower().endswith('.dwg'):
        return redirect(url_for('dwg_conversion'))
    else:
        flash('不支持的文件类型', 'error')
        return redirect(url_for('index'))

@app.route('/analyze_step_file')
def analyze_step():
    """分析STEP文件并展示结果"""
    if 'uploaded_file' not in session:
        flash('请先上传文件', 'error')
        return redirect(url_for('index'))
    
    filename = session.get('original_filename', '')
    
    # 检查是否为STEP文件
    if not filename.lower().endswith(('.stp', '.step')):
        flash('只能分析STEP/STP文件', 'error')
        return redirect(url_for('file_preview'))
    
    try:
        file_path = session.get('uploaded_file', '')
        
        # 分析文件
        analysis_results = analyze_step_file(file_path)
        
        return render_template(
            'step_analysis.html',
            filename=filename,
            results=analysis_results
        )
    except Exception as e:
        app.logger.error(f"STEP文件分析错误: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        flash(f'文件分析过程中出错: {str(e)}', 'error')
        return redirect(url_for('file_preview'))

@app.route('/step_conversion')
def step_conversion():
    """STEP文件转换参数页面"""
    if 'uploaded_file' not in session:
        flash('请先上传文件', 'error')
        return redirect(url_for('index'))
    
    filename = session.get('original_filename', '未知文件')
    return render_template('step_conversion.html', filename=filename)

@app.route('/dwg_conversion')
def dwg_conversion():
    """DWG文件转换参数页面"""
    if 'uploaded_file' not in session:
        flash('请先上传文件', 'error')
        return redirect(url_for('index'))
    
    filename = session.get('original_filename', '未知文件')
    return render_template('dwg_conversion.html', filename=filename)

@app.route('/convert', methods=['POST'])
def convert_file():
    """转换文件为G代码"""
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': '没有指定文件名'}), 400
    
    # 转换参数
    params = data.get('params', {})
    feed_rate = params.get('feed_rate', 500)
    rapid_height = params.get('rapid_height', 10.0)
    cut_depth = params.get('cut_depth', 5.0)
    tool_diameter = params.get('tool_diameter', 3.0)
    
    user_dir = os.path.join(UPLOAD_FOLDER, session.get('user_id', 'default'))
    user_output_dir = os.path.join(OUTPUT_FOLDER, session.get('user_id', 'default'))
    
    # 确保输出目录存在
    if not os.path.exists(user_output_dir):
        os.makedirs(user_output_dir)
    
    file_path = os.path.join(user_dir, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': f"文件 {filename} 不存在"}), 404
    
    # 确定文件类型
    file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
    output_filename = f"{os.path.splitext(filename)[0]}.nc"
    output_path = os.path.join(user_output_dir, output_filename)
    
    try:
        # 根据文件类型选择转换方法
        if file_ext in ['stp', 'step']:
            # 确定当前平台
            system_platform = platform.machine().lower()
            
            if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'step_processor_fallback.py')):
                script_path = 'step_to_fanuc_numpy.py'
            else:
                script_path = os.path.join('web', 'step_to_fanuc_numpy.py')
            
            # 调用STEP转换脚本
            cmd = [
                sys.executable,
                script_path,
                file_path,
                '-o', output_path,
                '-f', str(feed_rate),
                '-r', str(rapid_height),
                '-d', str(cut_depth),
                '-t', str(tool_diameter),
                '-v'  # 显示详细输出
            ]
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return jsonify({
                    'error': f"转换失败: {result.stderr}",
                    'details': result.stdout
                }), 500
            
        elif file_ext in ['dwg', 'dxf']:
            # 创建临时STEP文件
            step_filename = f"{os.path.splitext(filename)[0]}.stp"
            step_path = os.path.join(user_dir, step_filename)
            
            # 调用DWG/DXF转STEP脚本
            dwg_to_step_path = os.path.join('web', 'dwg_to_step.py')
            
            # 检查脚本是否存在
            if not os.path.exists(dwg_to_step_path):
                # 如果脚本不存在，创建一个基本的实现
                create_basic_dwg_to_step_script()
                dwg_to_step_path = 'dwg_to_step.py'
            
            # 执行DWG到STEP的转换
            dwg_cmd = [
                sys.executable,
                dwg_to_step_path,
                file_path,
                step_path
            ]
            
            # 执行DWG到STEP转换
            dwg_result = subprocess.run(dwg_cmd, capture_output=True, text=True)
            
            if dwg_result.returncode != 0:
                return jsonify({
                    'error': f"DWG到STEP转换失败: {dwg_result.stderr}",
                    'details': dwg_result.stdout
                }), 500
            
            if not os.path.exists(step_path):
                return jsonify({
                    'error': f"DWG到STEP转换未生成STEP文件",
                    'details': "请检查转换脚本实现"
                }), 500
            
            # 使用转换后的STEP文件生成G代码
            if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'step_processor_fallback.py')):
                script_path = 'step_to_fanuc_numpy.py'
            else:
                script_path = os.path.join('web', 'step_to_fanuc_numpy.py')
            
            # 调用STEP转换脚本
            cmd = [
                sys.executable,
                script_path,
                step_path,
                '-o', output_path,
                '-f', str(feed_rate),
                '-r', str(rapid_height),
                '-d', str(cut_depth),
                '-t', str(tool_diameter),
                '-v'  # 显示详细输出
            ]
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return jsonify({
                    'error': f"转换失败: {result.stderr}",
                    'details': result.stdout
                }), 500
        else:
            return jsonify({'error': '不支持的文件类型'}), 400
        
        # 转换成功
        return jsonify({
            'success': True,
            'message': '文件转换成功',
            'output_filename': output_filename,
            'download_url': url_for('download_file', filename=output_filename)
        })
    
    except Exception as e:
        return jsonify({'error': f"转换过程中出错: {str(e)}"}), 500

def create_basic_dwg_to_step_script():
    """创建基本的DWG到STEP转换脚本"""
    script_content = """#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
基本的DWG/DXF到STEP转换脚本
注意：这是一个基本实现，仅用于示例
实际应用中，推荐使用专业CAD库如ODA或FreeCAD进行转换
'''

import sys
import os
import re
import numpy as np
from time import time

def parse_dxf_file(input_file):
    '''简单解析DXF文件，提取点和线'''
    print(f"解析DXF/DWG文件: {input_file}")
    try:
        # 尝试使用ezdxf库解析
        try:
            import ezdxf
            dwg = ezdxf.readfile(input_file)
            msp = dwg.modelspace()
            
            # 提取实体
            points = []
            lines = []
            
            # 提取LINE实体
            for line in msp.query('LINE'):
                start = line.dxf.start
                end = line.dxf.end
                lines.append((start, end))
                points.append(start)
                points.append(end)
            
            # 提取CIRCLE实体
            for circle in msp.query('CIRCLE'):
                center = circle.dxf.center
                radius = circle.dxf.radius
                # 转换圆为多段线
                for i in range(32):
                    angle = i * 2 * np.pi / 32
                    next_angle = (i + 1) * 2 * np.pi / 32
                    p1 = (center[0] + radius * np.cos(angle), 
                          center[1] + radius * np.sin(angle), 
                          center[2])
                    p2 = (center[0] + radius * np.cos(next_angle), 
                          center[1] + radius * np.sin(next_angle), 
                          center[2])
                    lines.append((p1, p2))
                    points.append(p1)
                    points.append(p2)
            
            # 提取ARC实体
            for arc in msp.query('ARC'):
                center = arc.dxf.center
                radius = arc.dxf.radius
                start_angle = arc.dxf.start_angle * np.pi / 180
                end_angle = arc.dxf.end_angle * np.pi / 180
                
                # 转换弧为多段线
                if end_angle < start_angle:
                    end_angle += 2 * np.pi
                
                num_segments = 16
                angle_step = (end_angle - start_angle) / num_segments
                
                for i in range(num_segments):
                    angle = start_angle + i * angle_step
                    next_angle = start_angle + (i + 1) * angle_step
                    p1 = (center[0] + radius * np.cos(angle), 
                          center[1] + radius * np.sin(angle), 
                          center[2])
                    p2 = (center[0] + radius * np.cos(next_angle), 
                          center[1] + radius * np.sin(next_angle), 
                          center[2])
                    lines.append((p1, p2))
                    points.append(p1)
                    points.append(p2)
            
            print(f"从DXF文件中提取了 {len(points)} 个点和 {len(lines)} 条线")
            return points, lines
            
        except ImportError:
            print("警告: ezdxf库未安装，使用简单文本处理方法解析DXF")
            
            with open(input_file, 'r', errors='ignore') as f:
                content = f.read()
            
            # 简单提取POLYLINE和LINE实体
            # 注意：这是非常基础的实现，仅适用于简单DXF文件
            points = []
            lines = []
            
            # 查找所有点（10,20,30表示X,Y,Z坐标）
            point_pattern = r'POINT\\n.*?10\\n(.*?)\\n.*?20\\n(.*?)\\n.*?30\\n(.*?)\\n'
            for match in re.finditer(point_pattern, content, re.DOTALL):
                x = float(match.group(1))
                y = float(match.group(2))
                z = float(match.group(3))
                points.append((x, y, z))
            
            # 查找所有线（从点到点）
            line_start_pattern = r'LINE\\n.*?10\\n(.*?)\\n.*?20\\n(.*?)\\n.*?30\\n(.*?)\\n'
            line_end_pattern = r'.*?11\\n(.*?)\\n.*?21\\n(.*?)\\n.*?31\\n(.*?)\\n'
            
            for i, match in enumerate(re.finditer(line_start_pattern, content, re.DOTALL)):
                start_x = float(match.group(1))
                start_y = float(match.group(2))
                start_z = float(match.group(3))
                
                # 找到对应的终点
                end_match = re.search(line_end_pattern, content[match.end():], re.DOTALL)
                if end_match:
                    end_x = float(end_match.group(1))
                    end_y = float(end_match.group(2))
                    end_z = float(end_match.group(3))
                    
                    start_point = (start_x, start_y, start_z)
                    end_point = (end_x, end_y, end_z)
                    points.append(start_point)
                    points.append(end_point)
                    lines.append((start_point, end_point))
            
            print(f"从DXF文件中提取了 {len(points)} 个点和 {len(lines)} 条线")
            return points, lines
    
    except Exception as e:
        print(f"解析DXF/DWG文件出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return [], []

def generate_step_file(points, lines, output_file):
    '''生成简单的STEP文件'''
    print(f"生成STEP文件: {output_file}")
    try:
        with open(output_file, 'w') as f:
            # STEP文件头
            f.write("ISO-10303-21;\n")
            f.write("HEADER;\n")
            f.write("FILE_DESCRIPTION(('CAD'),'2;1');\n")
            f.write(f"FILE_NAME('{os.path.basename(output_file)}','Generated by dwg_to_step.py',('AUTHOR'),('ORGANIZATION'),'','','');\n")
            f.write("FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));\n")
            f.write("ENDSEC;\n")
            f.write("DATA;\n")
            
            # 添加顶级实体
            f.write("#1=APPLICATION_CONTEXT('automotive design');\n")
            f.write("#2=APPLICATION_PROTOCOL_DEFINITION('Draft International Standard','automotive_design',2000,#1);\n")
            f.write("#3=PRODUCT_DEFINITION_CONTEXT('design',#1,'design');\n")
            f.write("#4=PRODUCT_CONTEXT('AUTOMOTIVE_DESIGN',#1,'');\n")
            f.write("#5=PRODUCT('CONVERTER_GENERATED_GEOMETRY','CONVERTER_GENERATED_GEOMETRY','',(#4));\n")
            f.write("#6=PRODUCT_DEFINITION_FORMATION('','',#5);\n")
            f.write("#7=PRODUCT_DEFINITION('design','',#6,#3);\n")
            f.write("#8=PRODUCT_DEFINITION_SHAPE('','',#7);\n")
            
            # 添加SHAPE_DEFINITION_REPRESENTATION
            f.write("#9=SHAPE_DEFINITION_REPRESENTATION(#8,#10);\n")
            f.write("#10=SHAPE_REPRESENTATION('',(#11),#12);\n")
            f.write("#11=AXIS2_PLACEMENT_3D('',#13,#14,#15);\n")
            f.write("#12=GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#16)) GLOBAL_UNIT_ASSIGNED_CONTEXT((#17,#18,#19));\n")
            f.write("#13=CARTESIAN_POINT('',(0.0,0.0,0.0));\n")
            f.write("#14=DIRECTION('',(0.0,0.0,1.0));\n")
            f.write("#15=DIRECTION('',(1.0,0.0,0.0));\n")
            f.write("#16=UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.0e-06),#17,'','');\n")
            f.write("#17=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.0),#20);\n")
            f.write("#18=PLANE_ANGLE_MEASURE_WITH_UNIT(PLANE_ANGLE_MEASURE(0.017453293),#21);\n")
            f.write("#19=SOLID_ANGLE_MEASURE_WITH_UNIT(SOLID_ANGLE_MEASURE(0.000290888),#22);\n")
            f.write("#20=(CONVERSION_BASED_UNIT('MILLIMETRE',#23)LENGTH_UNIT());\n")
            f.write("#21=(NAMED_UNIT(*))PLANE_ANGLE_UNIT();\n")
            f.write("#22=(NAMED_UNIT(*))SOLID_ANGLE_UNIT();\n")
            f.write("#23=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(1000.0),#24);\n")
            f.write("#24=(NAMED_UNIT(*))SI_UNIT(MILLI,METRE);\n")
            
            # 添加点和线
            entity_id = 25
            manifest = []
            
            # 定义点
            point_ids = {}
            for i, point in enumerate(points):
                x, y, z = point
                f.write(f"#{entity_id}=CARTESIAN_POINT('POINT{i+1}',(${x:.6f},${y:.6f},${z:.6f}));\n".replace('$', ''))
                point_ids[i] = entity_id
                entity_id += 1
            
            # 定义方向向量
            f.write(f"#{entity_id}=DIRECTION('DIRECTION',(0.0,0.0,1.0));\n")
            z_dir_id = entity_id
            entity_id += 1
            
            # 定义线
            line_ids = []
            for i, line in enumerate(lines):
                start_idx = points.index(line[0])
                end_idx = points.index(line[1])
                
                # VERTEX_POINT for start
                f.write(f"#{entity_id}=VERTEX_POINT('VERTEX{i+1}_START',#{point_ids[start_idx]});\n")
                start_vertex_id = entity_id
                entity_id += 1
                
                # VERTEX_POINT for end
                f.write(f"#{entity_id}=VERTEX_POINT('VERTEX{i+1}_END',#{point_ids[end_idx]});\n")
                end_vertex_id = entity_id
                entity_id += 1
                
                # 方向向量
                start_x, start_y, start_z = line[0]
                end_x, end_y, end_z = line[1]
                dx = end_x - start_x
                dy = end_y - start_y
                dz = end_z - start_z
                length = np.sqrt(dx*dx + dy*dy + dz*dz)
                
                if length > 0:
                    dx /= length
                    dy /= length
                    dz /= length
                else:
                    dx, dy, dz = 1, 0, 0
                
                f.write(f"#{entity_id}=DIRECTION('LINE{i+1}_DIRECTION',(${dx:.6f},${dy:.6f},${dz:.6f}));\n".replace('$', ''))
                dir_id = entity_id
                entity_id += 1
                
                # VECTOR
                f.write(f"#{entity_id}=VECTOR('LINE{i+1}_VECTOR',#{dir_id},${length:.6f});\n".replace('$', ''))
                vector_id = entity_id
                entity_id += 1
                
                # LINE
                f.write(f"#{entity_id}=LINE('LINE{i+1}',#{point_ids[start_idx]},#{vector_id});\n")
                line_id = entity_id
                entity_id += 1
                
                # EDGE_CURVE
                f.write(f"#{entity_id}=EDGE_CURVE('EDGE{i+1}',#{start_vertex_id},#{end_vertex_id},#{line_id},.T.);\n")
                edge_curve_id = entity_id
                entity_id += 1
                
                # ORIENTED_EDGE
                f.write(f"#{entity_id}=ORIENTED_EDGE('',*,*,#{edge_curve_id},.T.);\n")
                oriented_edge_id = entity_id
                entity_id += 1
                
                line_ids.append(oriented_edge_id)
                manifest.append(oriented_edge_id)
            
            # 添加到SHAPE_REPRESENTATION
            manifest_str = ','.join([f'#{id}' for id in manifest])
            f.write(f"#10=SHAPE_REPRESENTATION('',(#11,{manifest_str}),#12);\n")
            
            # 结束STEP文件
            f.write("ENDSEC;\n")
            f.write("END-ISO-10303-21;\n")
            
            return True
    
    except Exception as e:
        print(f"生成STEP文件出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    '''主函数'''
    if len(sys.argv) < 3:
        print("用法: python dwg_to_step.py 输入文件.dwg/dxf 输出文件.stp")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在 - {input_file}")
        sys.exit(1)
    
    start_time = time()
    
    # 解析DXF/DWG文件
    points, lines = parse_dxf_file(input_file)
    
    if not points or not lines:
        print("错误: 未能从DXF/DWG文件中提取几何信息")
        sys.exit(1)
    
    # 去除重复点
    unique_points = []
    for point in points:
        if point not in unique_points:
            unique_points.append(point)
    
    # 生成STEP文件
    if generate_step_file(unique_points, lines, output_file):
        print(f"成功生成STEP文件: {output_file}")
        print(f"转换用时: {time() - start_time:.2f} 秒")
        sys.exit(0)
    else:
        print("生成STEP文件失败")
        sys.exit(1)

if __name__ == "__main__":
    main()

@app.route('/results')
def show_results():
    """显示转换结果页面"""
    if 'output_file' not in session:
        flash('没有可用的转换结果', 'error')
        return redirect(url_for('index'))
    
    output_file = session['output_file']
    if not os.path.exists(output_file):
        flash('转换结果文件不存在', 'error')
        return redirect(url_for('index'))
    
    # 获取结果信息
    gcode_preview = get_gcode_preview(output_file)
    stats = get_gcode_stats(output_file)
    
    return render_template(
        'results.html',
        original_filename=session.get('original_filename', '未知文件'),
        output_filename=session.get('output_filename', '未知文件'),
        step_filename=session.get('original_filename') if session.get('has_step', False) else None,
        has_step=session.get('has_step', False),
        has_visualizations=session.get('has_visualizations', False),
        session_id=session.get('session_id', 'unknown'),
        gcode_preview=gcode_preview,
        stats=stats
    )

@app.route('/download/<filename>')
def download(filename):
    """下载生成的文件"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

@app.route('/download_source')
def download_source():
    """下载源文件"""
    if 'uploaded_file' not in session:
        flash('无法找到源文件', 'error')
        return redirect(url_for('index'))
    
    original_filename = session.get('original_filename', 'unknown.stp')
    return send_from_directory(app.config['UPLOAD_FOLDER'], original_filename, as_attachment=True)

@app.route('/view_gcode/<filename>')
def view_gcode(filename):
    """查看G代码文件内容"""
    if 'output_file' not in session:
        flash('无法找到转换结果', 'error')
        return redirect(url_for('index'))
    
    output_file = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if not os.path.exists(output_file):
        flash('文件不存在', 'error')
        return redirect(url_for('index'))
    
    try:
        with open(output_file, 'r') as f:
            content = f.read()
        
        file_stats = os.stat(output_file)
        file_info = {
            'name': filename,
            'size': get_file_size(output_file),
            'line_count': content.count('\n') + 1,
            'created': time.strftime('%Y-%m-%d %H:%M:%S', 
                                   time.localtime(file_stats.st_ctime)),
            'modified': time.strftime('%Y-%m-%d %H:%M:%S', 
                                    time.localtime(file_stats.st_mtime))
        }
        
        # 获取G代码的统计信息
        stats = get_gcode_stats(output_file)
        
        return render_template('view_gcode.html',
                              filename=filename,
                              file_info=file_info,
                              content=content.splitlines(),
                              stats=stats)
        
    except Exception as e:
        flash(f'查看文件时出错: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download_plot/<filename>')
def download_plot(filename):
    """下载单个可视化图表"""
    session_id = session.get('session_id', 'unknown')
    session_plots_dir = os.path.join(app.config['STATIC_PLOTS_FOLDER'], session_id)
    return send_from_directory(session_plots_dir, filename, as_attachment=True)

@app.route('/download_all_plots')
def download_all_plots():
    """将所有可视化图表打包下载"""
    session_id = session.get('session_id', 'unknown')
    session_plots_dir = os.path.join(app.config['STATIC_PLOTS_FOLDER'], session_id)
    
    # 创建ZIP文件
    zip_filename = f"plots_{session_id}.zip"
    zip_path = os.path.join(app.config['OUTPUT_FOLDER'], zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for plot_file in os.listdir(session_plots_dir):
            if plot_file.endswith('.png'):
                zipf.write(
                    os.path.join(session_plots_dir, plot_file),
                    arcname=plot_file
                )
    
    return send_from_directory(app.config['OUTPUT_FOLDER'], zip_filename, as_attachment=True)

@app.errorhandler(413)
def too_large(e):
    """处理文件过大错误"""
    flash(f'文件太大，最大允许大小为 {MAX_CONTENT_LENGTH/1024/1024:.0f}MB', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def server_error(e):
    """处理服务器错误"""
    return render_template('error.html', 
                           error_title="服务器错误",
                           error_message=str(e),
                           error_code="SERVER_ERROR",
                           timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           session_id=session.get('session_id', 'unknown'))

@app.errorhandler(404)
def not_found(e):
    """处理页面未找到错误"""
    return render_template('error.html', 
                           error_title="页面未找到",
                           error_message="请求的页面不存在",
                           error_code="NOT_FOUND",
                           timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                           session_id=session.get('session_id', 'unknown'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 