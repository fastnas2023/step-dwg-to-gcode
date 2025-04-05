import matplotlib.pyplot as plt
import numpy as np
import os

# 确保plots目录存在
if not os.path.exists('plots'):
    os.makedirs('plots')

# 数据
versions = ['Original', 'NumPy Optimized']
execution_time = [0.698, 1.886]  # 秒
file_size = [4.4, 1.8]  # MB
gcode_lines = [183283, 72792]  # 行数
contours = [1, 121]  # 轮廓数量

# 创建图表
fig, axs = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('STEP to G-code Converter Comparison', fontsize=16)

# 执行时间比较
axs[0, 0].bar(versions, execution_time, color=['#5DA5DA', '#FAA43A'])
axs[0, 0].set_title('Execution Time (seconds)')
axs[0, 0].set_ylabel('Time (s)')
for i, v in enumerate(execution_time):
    axs[0, 0].text(i, v + 0.05, f"{v:.3f}s", ha='center')

# 文件大小比较
axs[0, 1].bar(versions, file_size, color=['#5DA5DA', '#FAA43A'])
axs[0, 1].set_title('Output File Size (MB)')
axs[0, 1].set_ylabel('Size (MB)')
for i, v in enumerate(file_size):
    axs[0, 1].text(i, v + 0.1, f"{v}MB", ha='center')

# G代码行数比较
axs[1, 0].bar(versions, gcode_lines, color=['#5DA5DA', '#FAA43A'])
axs[1, 0].set_title('G-code Lines (lower is better)')
axs[1, 0].set_ylabel('Number of Lines')
for i, v in enumerate(gcode_lines):
    axs[1, 0].text(i, v + 5000, f"{v:,}", ha='center')

# 轮廓数量比较
axs[1, 1].bar(versions, contours, color=['#5DA5DA', '#FAA43A'])
axs[1, 1].set_title('Number of Contours (higher is better)')
axs[1, 1].set_ylabel('Contours')
for i, v in enumerate(contours):
    axs[1, 1].text(i, v + 5, f"{v}", ha='center')

# 调整布局
plt.tight_layout(rect=[0, 0, 1, 0.95])

# 保存图表
plt.savefig('plots/converter_comparison.png', dpi=300)
print("Comparison chart saved to 'plots/converter_comparison.png'")

# 功能比较雷达图
plt.figure(figsize=(10, 8))

# 功能类别
categories = ['Speed', 'File Size Efficiency', 'Contour Detection', 
              'Path Optimization', 'Feature Richness', 
              'Visualization', 'Statistical Analysis']

# 评分 (0-100)
original_scores = [90, 40, 20, 30, 20, 0, 10]
numpy_scores = [70, 90, 95, 90, 95, 100, 95]

# 计算角度
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]  # 闭合图形

# 调整数据为闭合图形
original_scores += original_scores[:1]
numpy_scores += numpy_scores[:1]

# 绘制雷达图
ax = plt.subplot(111, polar=True)

# 绘制外部圆和网格线
plt.xticks(angles[:-1], categories, size=12)
ax.set_rlabel_position(0)
plt.yticks([20, 40, 60, 80, 100], ["20", "40", "60", "80", "100"], color="grey", size=10)
plt.ylim(0, 100)

# 绘制数据
ax.plot(angles, original_scores, 'b-', linewidth=2, label='Original')
ax.fill(angles, original_scores, 'b', alpha=0.1)
ax.plot(angles, numpy_scores, 'r-', linewidth=2, label='NumPy Optimized')
ax.fill(angles, numpy_scores, 'r', alpha=0.1)

# 添加图例
plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
plt.title('Feature Comparison', size=15)

# 保存雷达图
plt.tight_layout()
plt.savefig('plots/feature_radar.png', dpi=300)
print("Feature radar chart saved to 'plots/feature_radar.png'")

plt.close('all') 