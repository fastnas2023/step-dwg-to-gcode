import os
import shutil
import subprocess
import uuid
import datetime
import re
import zipfile
from flask import Flask, request, render_template, redirect, url_for, flash, session, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path

# 配置
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output')
PLOTS_FOLDER = os.path.join(os.getcwd(), 'plots')
STATIC_PLOTS_FOLDER = os.path.join(os.getcwd(), 'static/plots')
ALLOWED_EXTENSIONS = {'stp', 'step', 'dwg'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

# 应用初始化
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['PLOTS_FOLDER'] = PLOTS_FOLDER
app.config['STATIC_PLOTS_FOLDER'] = STATIC_PLOTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.secret_key = os.urandom(24)

# 确保各目录存在
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, PLOTS_FOLDER, STATIC_PLOTS_FOLDER]:
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
    """主页 - 文件上传界面"""
    prepare_user_session()
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    print("收到上传请求，表单数据:", request.form)
    print("files对象:", request.files)
    
    if 'file' not in request.files:
        flash('未找到文件', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    print(f"接收到文件: {file.filename}")
    
    if file.filename == '':
        flash('未选择文件', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        session_id = prepare_user_session()
        
        # 保存上传的文件
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        print(f"文件已保存到: {file_path}")
        
        # 在会话中记录文件路径
        session['uploaded_file'] = file_path
        session['original_filename'] = filename
        
        # 根据文件类型决定下一步
        if filename.lower().endswith(('.stp', '.step')):
            return redirect(url_for('step_conversion'))
        elif filename.lower().endswith('.dwg'):
            return redirect(url_for('dwg_conversion'))
    else:
        flash('不支持的文件类型', 'error')
        return redirect(url_for('index'))

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

@app.route('/convert_step', methods=['POST'])
def convert_step():
    """处理STEP文件转G代码转换"""
    if 'uploaded_file' not in session:
        flash('会话已过期，请重新上传文件', 'error')
        return redirect(url_for('index'))
    
    try:
        # 获取参数
        converter_type = request.form.get('converter_type', 'numpy')
        feed_rate = request.form.get('feed_rate', '500')
        safety_height = request.form.get('safety_height', '10')
        cut_depth = request.form.get('cut_depth', '0.5')
        generate_visualization = 'generate_visualization' in request.form
        
        input_file = session['uploaded_file']
        original_filename = session['original_filename']
        output_filename = f"{os.path.splitext(original_filename)[0]}_gcode.nc"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # 根据转换器类型选择脚本
        if converter_type == 'numpy':
            script = 'step_to_fanuc_numpy.py'
        elif converter_type == 'no_numpy':
            script = 'fanuc_stp_to_gcode.py'
        else:
            script = 'fanuc_stp_to_gcode_orig.py'
        
        # 构建命令
        cmd = [
            'python', 
            script, 
            input_file, 
            '-o', output_path,
            '-f', feed_rate,
            '-s', safety_height,
            '-d', cut_depth
        ]
        
        if generate_visualization and converter_type == 'numpy':
            cmd.append('-v')
        
        # 执行转换
        process = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # 检查是否成功
        if process.returncode != 0:
            raise Exception(f"转换过程返回非零状态: {process.stderr}")
        
        # 保存输出文件路径到会话
        session['output_file'] = output_path
        session['output_filename'] = output_filename
        
        # 如果生成了可视化，复制到静态目录
        if generate_visualization and converter_type == 'numpy':
            copy_plots_to_static(app.config['PLOTS_FOLDER'], session['session_id'])
            session['has_visualizations'] = True
        else:
            session['has_visualizations'] = False
        
        # 重定向到结果页面
        return redirect(url_for('show_results'))
    
    except Exception as e:
        app.logger.error(f"STEP转换错误: {str(e)}")
        return render_template('error.html', 
                               error_title="STEP文件转换错误",
                               error_message=str(e),
                               error_code="STEP_CONVERSION_ERROR",
                               timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                               session_id=session.get('session_id', 'unknown'),
                               retry_url=url_for('step_conversion'))

@app.route('/convert_dwg', methods=['POST'])
def convert_dwg():
    """处理DWG文件到STEP转换，然后重定向到STEP转换页面"""
    if 'uploaded_file' not in session:
        flash('会话已过期，请重新上传文件', 'error')
        return redirect(url_for('index'))
    
    try:
        # 获取参数
        part_type = request.form.get('part_type', 'generic')
        
        input_file = session['uploaded_file']
        original_filename = session['original_filename']
        step_filename = f"{os.path.splitext(original_filename)[0]}.stp"
        step_path = os.path.join(app.config['UPLOAD_FOLDER'], step_filename)
        
        # 执行DWG到STEP转换，修改为使用python直接调用脚本
        cmd = [
            'python',
            'advanced_dwg_to_step.py',
            input_file,
            step_path,  # 输出文件作为位置参数
            '--type', part_type
        ]
        
        # 打印命令以便调试
        print(f"执行命令: {' '.join(cmd)}")
        
        # 执行转换
        process = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=False,  # 不使用check=True，以便我们能捕获完整的错误输出
            cwd=os.getcwd()  # 确保在正确的工作目录下执行
        )
        
        # 输出完整的命令执行结果以便调试
        print(f"命令标准输出: {process.stdout}")
        print(f"命令错误输出: {process.stderr}")
        print(f"返回码: {process.returncode}")
        
        # 检查是否成功
        if process.returncode != 0:
            error_message = f"DWG转STEP过程返回非零状态: {process.returncode}\n输出信息:\n{process.stdout}\n错误信息:\n{process.stderr}"
            print(error_message)
            raise Exception(error_message)
        
        # 检查STEP文件是否生成
        if not os.path.exists(step_path):
            print(f"转换未生成STEP文件: {step_path}")
            raise Exception(f"转换未能生成STEP文件: {step_path}")
            
        print(f"STEP文件已生成: {step_path}")
        
        # 更新会话中的文件为生成的STEP文件
        session['uploaded_file'] = step_path
        session['original_filename'] = step_filename
        session['dwg_original'] = original_filename
        session['has_step'] = True
        
        # 重定向到STEP转换页面
        flash('DWG文件已成功转换为STEP格式，请配置G代码生成参数', 'success')
        return redirect(url_for('step_conversion'))
    
    except Exception as e:
        app.logger.error(f"DWG转换错误: {str(e)}")
        return render_template('error.html', 
                               error_title="DWG文件转换错误",
                               error_message=str(e),
                               error_code="DWG_CONVERSION_ERROR",
                               timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                               session_id=session.get('session_id', 'unknown'),
                               retry_url=url_for('dwg_conversion'))

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
    app.run(debug=True, host='0.0.0.0', port=8888) 