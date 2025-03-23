/**
 * STEP/DWG到G代码转换器web界面
 * 主要JavaScript功能
 */

document.addEventListener('DOMContentLoaded', function() {
    // 文件上传区域的拖放功能
    initFileUpload();
    
    // 转换参数表单的交互功能
    initConversionForm();
    
    // 可视化图表标签页切换
    initVisualizationTabs();
    
    // 初始化工具提示
    initTooltips();
});

/**
 * 初始化文件上传功能
 */
function initFileUpload() {
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.getElementById('file');
    const fileNameDisplay = document.querySelector('.file-name');
    
    // 如果页面上存在上传区域
    if (uploadArea && fileInput) {
        // 点击上传区域触发文件选择
        uploadArea.addEventListener('click', function() {
            fileInput.click();
        });
        
        // 文件选择变更时
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                const file = this.files[0];
                displaySelectedFile(file, fileNameDisplay);
                validateFileType(file);
            }
        });
        
        // 拖放事件 - 拖入
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add('dragover');
        });
        
        // 拖放事件 - 离开
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('dragover');
        });
        
        // 拖放事件 - 放下
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('dragover');
            
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                const file = e.dataTransfer.files[0];
                displaySelectedFile(file, fileNameDisplay);
                validateFileType(file);
            }
        });
    }
}

/**
 * 显示选择的文件名
 */
function displaySelectedFile(file, displayElement) {
    if (displayElement) {
        displayElement.textContent = file.name;
        displayElement.parentElement.classList.remove('d-none');
    }
}

/**
 * 验证文件类型
 */
function validateFileType(file) {
    const allowedTypes = ['.stp', '.step', '.dwg'];
    const fileName = file.name.toLowerCase();
    let valid = false;
    
    for (let type of allowedTypes) {
        if (fileName.endsWith(type)) {
            valid = true;
            break;
        }
    }
    
    const submitButton = document.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = !valid;
    }
    
    if (!valid) {
        alert('请选择有效的文件类型：.stp, .step 或 .dwg');
    }
}

/**
 * 初始化转换参数表单的交互功能
 */
function initConversionForm() {
    // 处理NumPy转换器选择与可视化选项的关联
    const converterSelect = document.getElementById('converter_type');
    const visualizationCheck = document.getElementById('generate_visualization');
    
    if (converterSelect && visualizationCheck) {
        converterSelect.addEventListener('change', function() {
            // 仅当选择NumPy优化版时启用可视化
            visualizationCheck.disabled = this.value !== 'numpy';
            if (this.value !== 'numpy') {
                visualizationCheck.checked = false;
            }
        });
    }
    
    // 范围滑块与数值输入同步
    const rangeInputs = document.querySelectorAll('input[type="range"]');
    
    rangeInputs.forEach(rangeInput => {
        const valueDisplay = document.getElementById(`${rangeInput.id}_value`);
        if (valueDisplay) {
            // 初始化显示值
            valueDisplay.textContent = rangeInput.value;
            
            // 滑块值变更时更新显示
            rangeInput.addEventListener('input', function() {
                valueDisplay.textContent = this.value;
                
                // 如果有关联的数值输入框，也更新它
                const numberInput = document.getElementById(this.id.replace('_range', ''));
                if (numberInput) {
                    numberInput.value = this.value;
                }
            });
        }
        
        // 如果有关联的数值输入框，处理其变更事件
        const numberInputId = rangeInput.id.replace('_range', '');
        const numberInput = document.getElementById(numberInputId);
        
        if (numberInput) {
            numberInput.addEventListener('input', function() {
                rangeInput.value = this.value;
                if (valueDisplay) {
                    valueDisplay.textContent = this.value;
                }
            });
        }
    });
}

/**
 * 初始化可视化图表标签页切换
 */
function initVisualizationTabs() {
    const tabLinks = document.querySelectorAll('.visualization-tabs .nav-link');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 移除所有标签页的active类
            tabLinks.forEach(tab => tab.classList.remove('active'));
            
            // 隐藏所有内容面板
            const tabPanes = document.querySelectorAll('.tab-pane');
            tabPanes.forEach(pane => {
                pane.classList.remove('show', 'active');
            });
            
            // 激活当前标签页
            this.classList.add('active');
            
            // 显示相应内容
            const targetId = this.getAttribute('data-bs-target').substring(1);
            const targetPane = document.getElementById(targetId);
            if (targetPane) {
                targetPane.classList.add('show', 'active');
            }
        });
    });
}

/**
 * 初始化工具提示
 */
function initTooltips() {
    // 如果使用Bootstrap的工具提示
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * 零件类型选择卡片交互（DWG转换页面）
 */
function initPartTypeCards() {
    const partTypeCards = document.querySelectorAll('.part-type-card');
    const partTypeInput = document.getElementById('part_type');
    
    if (partTypeCards.length && partTypeInput) {
        partTypeCards.forEach(card => {
            card.addEventListener('click', function() {
                // 移除所有卡片的选中状态
                partTypeCards.forEach(c => c.classList.remove('selected'));
                
                // 为当前卡片添加选中状态
                this.classList.add('selected');
                
                // 更新隐藏字段的值
                partTypeInput.value = this.dataset.value;
            });
        });
    }
}

// 在页面加载完成后调用零件类型卡片初始化
document.addEventListener('DOMContentLoaded', function() {
    initPartTypeCards();
}); 