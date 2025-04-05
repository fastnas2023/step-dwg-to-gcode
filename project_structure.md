# STEP/DWG到G代码转换器 - 项目结构

## 项目重构方案

为了使项目更易于部署和维护，我们将按照以下结构重新组织：

```
step-dwg-to-gcode/
├── app/                           # 应用程序核心模块
│   ├── __init__.py                # 主模块初始化
│   ├── controllers/               # 控制器代码
│   │   ├── __init__.py
│   │   ├── base_controller.py     # 基础控制器类
│   │   ├── fanuc_controller.py    # FANUC控制器
│   │   ├── siemens_controller.py  # 西门子控制器
│   │   ├── heidenhain_controller.py # 海德汉控制器
│   │   ├── haas_controller.py     # 哈斯控制器
│   │   └── controller_factory.py  # 控制器工厂类
│   ├── processors/                # 文件处理器
│   │   ├── __init__.py
│   │   ├── step_processor.py      # STEP文件处理基类
│   │   ├── numpy_step_processor.py # NumPy优化的STEP处理器
│   │   └── dwg_processor.py       # DWG文件处理器
│   ├── generators/                # G代码生成器
│   │   ├── __init__.py
│   │   ├── base_generator.py      # 基础G代码生成器
│   │   ├── fanuc_generator.py     # FANUC G代码生成器
│   │   ├── numpy_generator.py     # NumPy优化的生成器
│   │   └── legacy_generator.py    # 旧版生成器
│   └── utils/                     # 通用工具函数
│       ├── __init__.py
│       ├── file_utils.py          # 文件操作工具
│       └── geometry_utils.py      # 几何计算工具
├── web/                           # Web界面
│   ├── __init__.py
│   ├── web_interface.py           # Flask Web应用
│   ├── static/                    # 静态资源
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/                 # HTML模板
├── cli/                           # 命令行界面
│   ├── __init__.py
│   └── cli_interface.py           # 命令行工具
├── tests/                         # 测试代码
│   ├── __init__.py
│   ├── test_controllers.py        # 控制器测试
│   └── test_processors.py         # 处理器测试
├── data/                          # 数据目录
│   ├── samples/                   # 示例文件
│   └── output/                    # 输出文件夹
├── docs/                          # 文档
│   ├── user_manual.md             # 用户手册
│   └── images/                    # 文档图片
├── config/                        # 配置文件
│   └── app_config.py              # 应用配置
├── bin/                           # 执行脚本
│   ├── start_app.py               # 启动应用
│   └── install.py                 # 安装依赖
├── .cursor/                       # Cursor AI配置
│   └── ai-rules.txt               # AI规则
├── .gitignore                     # Git忽略文件
├── README.md                      # 项目说明
├── requirements.txt               # 依赖列表
└── setup.py                       # 安装脚本
```

## 文件类型归类

### 控制器文件
- 所有CNC控制器逻辑移动到 `app/controllers/` 目录
- 基础控制器类和控制器工厂放在同一目录

### 处理器文件
- STEP和DWG处理逻辑移动到 `app/processors/` 目录 
- NumPy优化版本的处理器也放在该目录

### 生成器文件
- G代码生成逻辑移动到 `app/generators/` 目录
- 不同的生成器实现（FANUC、优化版等）保持在同目录

### Web界面
- Web相关代码移动到 `web/` 目录
- 静态资源和模板也放在 `web/` 目录下

### 命令行界面
- 命令行工具移动到 `cli/` 目录

### 数据文件
- 示例文件移动到 `data/samples/` 目录
- 输出文件夹位于 `data/output/` 

## 迁移优势

1. **模块化组织**: 功能相关代码集中在同一目录，易于理解和维护
2. **明确依赖**: 模块间依赖关系更加清晰
3. **便于扩展**: 添加新控制器或处理器只需在相应目录添加新文件
4. **简化部署**: 遵循标准Python包结构，便于打包和分发
5. **配置集中**: 所有配置参数集中在config目录，易于管理
6. **测试友好**: 专门的测试目录，便于执行自动化测试

## 迁移步骤

1. 创建新的目录结构
2. 将文件按功能分类复制到相应目录
3. 调整导入路径
4. 更新配置和启动脚本
5. 测试功能完整性 