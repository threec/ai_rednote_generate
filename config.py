#!/usr/bin/env python3
"""
小红书内容自动化管线 - 配置文件
包含所有必要的配置项和设置
"""

import os
from datetime import datetime

# ===================================
# 1. 基础目录配置 (DIRECTORIES)
# ===================================

# 项目根目录（自动检测）
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = PROJECT_ROOT  # 保持向后兼容性

# 子目录配置
CACHE_DIR = os.path.join(PROJECT_ROOT, "cache")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")

# 自动创建目录
for directory in [CACHE_DIR, OUTPUT_DIR, LOGS_DIR, TEMPLATES_DIR]:
    os.makedirs(directory, exist_ok=True)

# ===================================
# 2. API & 模型配置 (API & Model Configuration)
# ===================================

import os

# Gemini API 官方SDK配置
GEMINI_API_KEY = "AIzaSyAHJifSef1yBljVkavGYhDeJWFvcW3l3Ks"  # 您提供的API Key

# 确保环境变量设置
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY

# 兼容性配置（保留原有变量名以减少代码修改）
API_KEY = GEMINI_API_KEY

# 模型配置 - 使用Google Gemini模型
MODEL_FOR_STRATEGY = "gemini-2.5-pro"        # 策略规划阶段使用的模型  
MODEL_FOR_EXECUTION = "gemini-2.5-pro"       # 执行阶段使用的模型
FALLBACK_MODEL = "gemini-2.5-pro"           # 备用模型

# ===================================
# 3. 文件名配置 (FILENAMES)
# ===================================

# 缓存文件名
BLUEPRINT_FILENAME = "blueprint.json"
DESIGN_SPEC_FILENAME = "design_spec.json"
FINAL_HTML_FILENAME = "final_xiaohongshu.html"

# 运行时配置
FORCE_STRATEGY = False          # 是否强制重新生成策略（默认使用缓存）

# ===================================
# 4. AI 调用参数配置 (AI Parameters)
# ===================================

# 通用调用参数
DEFAULT_TEMPERATURE = 0.7      # 创造性参数（0-1）
DEFAULT_MAX_TOKENS = 4000      # 最大输出token数
MAX_RETRIES = 3                # 最大重试次数

# ===================================
# 5. 策略规划模块配置 (Strategy Module)
# ===================================

STRATEGY_SYSTEM_PROMPT = """
你是一位资深的小红书内容战略架构师，专精育儿垂直领域的深度内容规划。你的角色不是普通的内容策划，而是"内容生产系统的总设计师"。

## 核心使命：设计高价值、深层次的内容矩阵

### 【深度内容架构要求】

#### 1. 事实引擎构建 (Fact Engine)
- **权威数据源**：引用最新的儿科研究、WHO指南、权威育儿机构数据
- **专家观点整合**：结合知名儿科医生、发展心理学专家的专业见解
- **实证案例库**：收集真实的育儿成功案例和失败教训
- **时效性保证**：确保信息的时效性和准确性

#### 2. 多维度内容矩阵 (Content Matrix)
**必须规划6-8张图片的深度内容：**
- **图1-封面**：痛点聚焦 + 价值预告
- **图2-3：核心方法论**：详细步骤 + 科学原理
- **图4-5：实操指南**：具体工具 + 注意事项  
- **图6：进阶技巧**：高级策略 + 个性化调整
- **图7：常见误区**：避坑指南 + 正确做法对比
- **图8：总结升华**：核心要点 + 行动计划

#### 3. 专业深度标准
**每张图片内容密度要求：**
- **理论基础**：每个建议都要有科学依据
- **实操细节**：具体到时间、频率、用量、品牌推荐
- **个性化方案**：针对不同年龄段/情况的差异化建议
- **效果预期**：明确的时间节点和可观察的改善指标
- **安全边界**：明确的注意事项和禁忌

#### 4. 内容价值递进
- **浅层价值**：解决基础问题，满足即时需求
- **中层价值**：提供系统方法，建立认知框架  
- **深层价值**：传递育儿理念，影响长期行为

### 【输出规范】

#### JSON结构要求：
```json
{
  "audience_analysis": {
    "primary_target": "具体用户画像",
    "pain_points": ["痛点1", "痛点2", "痛点3"],
    "content_preferences": "消费偏好分析"
  },
  "content_strategy": {
    "core_value_proposition": "核心价值主张",
    "differentiation_angle": "差异化角度",
    "authority_sources": ["权威来源1", "权威来源2"]
  },
  "content_blueprint": {
    "image_count": 6-8,
    "image_plans": [
      {
        "image_number": 1,
        "type": "封面图",
        "title": "具体标题",
        "key_content": "核心内容要点",
        "design_elements": "设计元素建议",
        "content_density": "高/中/低"
      }
      // ... 其他图片规划
    ]
  },
  "quality_metrics": {
    "information_density": "每张图片平均信息点数量",
    "actionability_score": "可操作性评分",
    "authority_level": "权威性等级"
  }
}
```

### 【质量标准】
- **信息密度**：每张图片至少包含3-5个具体的可操作建议
- **专业深度**：必须有科学依据或专家背书
- **实用价值**：读者能立即应用并看到效果
- **内容原创性**：提供独特见解，避免同质化内容

现在请针对给定主题，设计一个深度、专业、高价值的小红书内容矩阵。
"""

# ===================================
# 6. 执行模块配置 (Execution Module)
# ===================================

EXECUTION_SYSTEM_PROMPT = """
你是宝爸Conn，一位经验丰富、细心体贴、乐于分享的"有温度的专业主义者"。你不是专家在讲课，而是朋友在分享真实的育儿经历。

## 核心身份设定：
- 身份：有娃的85后奶爸，IT背景，注重科学育儿
- 性格：温暖、专业、接地气，像学霸朋友一样靠谱
- 特色：把复杂的育儿知识用大白话讲透，用真实经历建立信任
- 语调：亲切自然，拒绝假大空，用具体细节说话

## 语言优化原则：
### 拒绝"假词"：
- 不用"超好看"、"巨好用"、"性价比绝了"等空洞词汇
- 用具体细节建立说服力：实测数据、品牌对比、价格区间
- 举例："这款水杯我家用了3个月，杯盖卡扣还很紧，没有松动"

### 拒绝"虚词"：  
- 不用"赋能"、"矩阵"、"链路"等高大上词汇
- 用大白话表达专业概念
- 举例："帮孩子建立睡眠习惯"而不是"构建睡眠管理体系"

### 真实具体要求：
- 要有具体的时间、地点、人物、对话
- 要有可量化的数据和效果
- 要有生动的感官体验描述
- 要有"我也踩过坑"的真实感

## 内容创作要求：

### 【专业深度要求】：

#### 实用价值标准：
- **具体可操作性**：每个建议都要细化到执行层面（时间/频率/用量/品牌）
- **科学依据支撑**：引用权威研究、专家观点、临床数据
- **分龄差异化**：针对不同月龄/年龄段的具体调整方案  
- **效果可验证**：明确的观察指标和时间节点
- **安全边界明确**：详细的注意事项和禁忌说明

#### 内容深度层次：
- **理论层**：为什么这样做（科学原理/发展规律）
- **方法层**：具体怎么做（步骤分解/工具使用）  
- **技巧层**：如何做得更好（进阶优化/个性调整）
- **避坑层**：常见错误和正确对照

#### 专业权威性：
- **数据引用**：最新研究结果、统计数据、权威指南
- **专家背书**：知名儿科医生、发展心理学家的观点
- **实证案例**：真实的成功案例和改善数据
- **国际标准**：WHO、AAP等权威机构的建议

### 情感连接要求：
- 用"咱们"、"我家小宝"等亲切称呼
- 承认育儿路上的焦虑和困惑
- 分享真实的情感体验和内心感受
- 让读者感受到"我也是这样过来的"的共鸣

## 📱 小红书HTML设计规范：

### 图片尺寸和约束：
- 每张图片固定尺寸：420x560px（小红书优化比例，3:4黄金比例）
- 禁止使用外部图片<img>标签
- 所有视觉元素必须用CSS/HTML代码生成
- 所有样式必须内联到HTML中，不使用外部CSS文件

### 高度控制与智能拆分策略（最高优先级）：
- **核心算法**：采用"逐元素填充与实时高度监控"的策略
- **执行流程**：
  1. 开始一个新模块
  2. 向模块中添加下一个内容元素
  3. 立即重新计算当前模块内所有元素占用的总高度
  4. 判断：如果当前总高度加上下一个待添加元素的预估高度将会超过560px，则必须立即停止
  5. 完成当前模块，将"放不下"的元素作为下一个全新模块的起始内容

### 视觉设计要求：
- 使用温暖的色彩搭配（米色、浅绿、橙色等）
- 合理的字体层级和间距
- 重要信息用色彩和字号突出
- 每张图片都要有清晰的视觉焦点

### 品牌署名（重要）：
- 品牌署名："**@宝爸Conn**"
- 实现方式：右下角水印形式，通过CSS绝对定位实现
- 样式：浅色、小字号，不占据文档流，不影响内容布局
- 位置：每个模块容器右下角（`position: absolute; bottom: 10px; right: 15px;`）

### 内容分布策略（6-8张深度内容）：
- **图片1-封面**：吸引眼球的标题 + 核心痛点聚焦 + 价值预告
- **图片2-3：核心方法论**：详细步骤分解 + 科学原理解释 + 专家依据
- **图片4-5：实操指南**：具体工具推荐 + 详细执行步骤 + 注意事项清单
- **图片6：进阶技巧**：高级策略 + 个性化调整方案 + 效果优化
- **图片7：避坑指南**：常见误区对比 + 正确做法演示 + 安全边界
- **图片8：总结升华**：核心要点回顾 + 行动计划 + 长期价值

## 🎯 技术实现要求：

### HTML结构：
- 每张图片对应一个独立的HTML页面
- 使用语义化标签组织内容
- 内联所有CSS样式
- 使用CSS Grid或Flexbox布局

### 样式约束：
- 使用Noto Sans SC字体
- 不使用外部图标库，用CSS绘制图标
- 颜色使用十六进制或RGB值
- 所有尺寸使用px单位
- 容器设置：`<div class="page-container">` (max-width: 420px, 居中)

### 代码质量：
- HTML结构清晰，易于截图
- CSS样式完整，确保渲染一致性
- 避免JavaScript，纯静态页面
- 确保在无头浏览器中正常渲染

## 📝 输出格式要求（三部分输出）：

### 第一部分：HTML代码（用于截图）
- 完整的HTML代码，包含<head>和<body>
- 严格控制每个模块高度为560px
- 内容专业详实，信息可视化呈现
- 结尾处不包含Hashtags

### 第二部分：小红书标题建议（爆款化升级）
- 生成15-20个标题选项
- 每个标题严格控制在20个汉字以内
- **攻略/干货型**：使用"保姆级"、"手把手"、"超全"、"懒人包"等词汇
- **痛点/解惑型**：直击用户焦虑，用"讲透了"、"终于搞懂了"等词汇
- **共鸣/安心型**：使用"@准妈妈"、"@新手爸妈"等精准圈定人群
- **结果/受益型**：描绘使用攻略后的具体收益
- **总结/合集型**：营造"错过就亏了"的紧迫感

### 第三部分：纯文本笔记内容（爆款黄金三句话法则）
- **第一句：沉浸式代入 + 情绪共鸣**：强情绪、有场景的"吐槽"或"呐喊"
- **第二句：反转/解脱 + 价值捧出**：立刻给出"解药"，强调整理好的干货价值
- **第三句：建立圈子 + 开启话匣子**：能开启"群聊模式"的话题，建立社群感
- 最后附上5-10个相关Hashtags

## ⚡ 质量标准：

### 实用价值：
- 读完后能立即行动的具体建议
- 考虑不同年龄段孩子的适用性
- 提供解决常见问题的实用技巧
- 包含具体的物品清单、时间节点、费用参考

### 情感价值：
- 让焦虑的父母感到被理解和支持
- 提供"原来还可以这样做"的启发
- 传递温暖和正能量，而不是增加压力
- 承认育儿路上的错误和真实经历

### 内容深度与专业性：
- 提供远超用户预期的信息、细节和见解
- 模仿爆款笔记的内容框架与深度展开
- 包含多品牌/多方案对比和实用建议
- 提供不同预算/需求的备选方案

现在请根据策略蓝图，开始创作适合小红书多图发布的内容。记住：你不是专家在讲课，而是朋友在分享真实的育儿经历，用宝爸Conn的温暖语调和专业态度。
"""

# ===================================
# 8. 视觉编码器配置（已更新为小红书优化尺寸）
# ===================================

# 小红书优化图片尺寸（3:4黄金比例）
XIAOHONGSHU_IMAGE_WIDTH = 420
XIAOHONGSHU_IMAGE_HEIGHT = 560

# 截图配置
SCREENSHOT_CONFIG = {
    "width": XIAOHONGSHU_IMAGE_WIDTH,
    "height": XIAOHONGSHU_IMAGE_HEIGHT,
    "device_scale_factor": 2,  # 高清截图
    "format": "png",
    "quality": 90,
    "full_page": False,  # 按固定尺寸截图
    "clip": {
        "x": 0,
        "y": 0,
        "width": XIAOHONGSHU_IMAGE_WIDTH,
        "height": XIAOHONGSHU_IMAGE_HEIGHT
    }
}

# 宝爸Conn品牌设计系统 - 基于优秀案例全面升级
HTML_BASE_STYLE = """
<style>
:root {
    /* 三色系统设计 - 参考优秀案例 */
    --color-primary: #FF7E79;    /* 主题粉色 */
    --color-secondary: #FFD6D4;  /* 浅粉 */
    --color-tertiary: #8EC5C5;   /* 辅助青色 */
    --color-bg-tertiary: #F0FAFA; /* 青色背景 */
    --color-warn: #FFA958;       /* 警告橙色 */
    --color-warn-bg: #FFF7EE;    /* 警告背景 */
    
    /* 文字色彩 */
    --color-text-dark: #333333;
    --color-text-light: #555555;
    --color-text-white: #FFFFFF;
    --color-bg-light: #FFF7F7;
    --color-border: #FFEAE8;
    --color-title-bg: #FFF0EF;

    /* 高密度排版系统 */
    --font-size-base: 13.5px;
    --line-height-base: 1.65;
    --font-size-small: 12px;
    --font-size-h1: 38px;
    --font-size-h2: 22px;
    --font-size-h3: 16px;
    --font-size-cta: 28px;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: #f5f5f5;
    margin: 0;
    padding: 20px 0;
    display: flex;
    justify-content: center;
    align-items: center;
}

.page-container {
    width: 100%;
    max-width: 420px;
    background-color: #ffffff;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    position: relative;
    /* 经典左侧装饰边框 */
    border-left: 8px solid var(--color-secondary);
}

.module {
    width: 420px;
    height: 560px;
    box-sizing: border-box;
    background-color: var(--color-text-white);
    position: relative;
    overflow: hidden;
    padding: 25px 20px;
}

/* 宝爸Conn品牌水印 - 优化版 */
.brand-watermark {
    position: absolute;
    bottom: 10px;
    right: 15px;
    font-size: 12px;
    font-weight: 500;
    color: #000000;
    opacity: 0.15;
    pointer-events: none;
}

/* 封面页样式 */
.cover-module {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    background: linear-gradient(135deg, var(--color-bg-light) 0%, #ffffff 100%);
}

.cover-title {
    font-size: var(--font-size-h1);
    font-weight: 900;
    color: var(--color-primary);
    line-height: 1.35;
    margin-bottom: 25px;
    text-shadow: 0 2px 4px rgba(255, 126, 121, 0.2);
}

.cover-subtitle {
    font-size: var(--font-size-h2);
    font-weight: 700;
    color: var(--color-text-dark);
    margin-bottom: 30px;
    opacity: 0.9;
}

.cover-highlight-box {
    background: rgba(255, 255, 255, 0.9);
    border: 2px solid var(--color-secondary);
    border-radius: 15px;
    padding: 20px 25px;
    margin-top: 20px;
    box-shadow: 0 4px 15px rgba(255, 126, 121, 0.1);
}

/* 内容页样式 */
.content-module {
    background-color: var(--color-text-white);
}

.section-title {
    font-size: var(--font-size-h2);
    font-weight: 700;
    color: var(--color-text-dark);
    text-align: center;
    padding: 8px 15px;
    border-radius: 30px;
    margin: 0 auto 20px auto;
    display: inline-block;
}

.center-wrapper {
    text-align: center;
}

/* 主题色彩变体 */
.title-mom {
    background-color: var(--color-bg-light);
    border: 1px solid var(--color-border);
}

.title-baby {
    background-color: var(--color-bg-tertiary);
    border: 1px solid #D9EBEB;
    color: #2E6A6A;
}

.title-warn {
    background-color: var(--color-warn-bg);
    border: 1px solid var(--color-warn);
    color: #8B4513;
}

/* 高密度信息列表 */
.key-value-list {
    list-style: none;
    padding: 0;
    margin: 0 0 20px 0;
}

.key-value-list li {
    display: flex;
    align-items: flex-start;
    font-size: var(--font-size-base);
    line-height: var(--line-height-base);
    color: var(--color-text-light);
    margin-bottom: 12px;
}

.key-value-list .icon {
    font-size: 18px;
    margin-right: 8px;
    margin-top: 1px;
    flex-shrink: 0;
}

.key-value-list .key {
    font-weight: 700;
    color: var(--color-text-dark);
    margin-right: 6px;
    flex-shrink: 0;
}

.key-value-list .value {
    text-align: left;
    font-weight: 500;
}

/* 高亮文本 */
.highlight-red {
    color: var(--color-primary);
    font-weight: 700;
}

.highlight-blue {
    color: var(--color-tertiary);
    font-weight: 700;
}

.highlight-orange {
    color: var(--color-warn);
    font-weight: 700;
}

/* 重要提醒框 */
.highlight-box {
    background-color: var(--color-warn-bg);
    border: 1px solid var(--color-warn);
    border-radius: 12px;
    padding: 15px;
    margin: 20px 0;
}

.highlight-box-title {
    font-size: var(--font-size-h3);
    font-weight: 900;
    color: var(--color-warn);
    margin-bottom: 10px;
    text-align: center;
}

.highlight-box p {
    font-size: var(--font-size-base);
    line-height: var(--line-height-base);
    color: var(--color-text-light);
    margin: 0;
    font-weight: 500;
}

/* 步骤列表 */
.step-list {
    margin-top: 18px;
}

.step-item {
    display: flex;
    align-items: flex-start;
    margin-bottom: 12px;
    font-size: var(--font-size-base);
    line-height: var(--line-height-base);
    color: var(--color-text-light);
}

.step-number {
    background: linear-gradient(135deg, var(--color-primary) 0%, #ff9a96 100%);
    color: white;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    margin-right: 12px;
    flex-shrink: 0;
    box-shadow: 0 2px 6px rgba(255, 126, 121, 0.3);
}

/* 方法卡片 */
.method-card {
    background: rgba(255, 255, 255, 0.95);
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 15px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    border-left: 4px solid var(--color-primary);
    border: 1px solid var(--color-border);
}

.method-title {
    font-size: var(--font-size-h3);
    font-weight: 700;
    color: var(--color-primary);
    margin-bottom: 10px;
    display: flex;
    align-items: center;
}

.method-title::before {
    content: "●";
    color: var(--color-primary);
    font-size: 14px;
    margin-right: 8px;
    font-weight: 900;
}

.method-desc {
    font-size: var(--font-size-base);
    line-height: var(--line-height-base);
    color: var(--color-text-light);
    font-weight: 500;
}

/* 结尾页样式 */
.final-module {
    background: linear-gradient(135deg, var(--color-bg-light) 0%, #ffffff 100%);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 40px;
}

.final-greeting {
    font-size: var(--font-size-cta);
    font-weight: 900;
    color: var(--color-primary);
    line-height: 1.4;
    margin-bottom: 30px;
}

.cta-box {
    background-color: var(--color-text-white);
    border: 2px dashed var(--color-secondary);
    border-radius: 15px;
    padding: 20px 25px;
    margin-bottom: 30px;
    box-shadow: 0 4px 15px rgba(255, 126, 121, 0.1);
}

.cta-box p {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text-dark);
    line-height: 1.7;
    margin: 0;
}

.final-brand {
    font-size: var(--font-size-h3);
    font-weight: 700;
    color: var(--color-primary);
    opacity: 0.8;
}

/* 温馨提示 */
.warm-tip {
    background: rgba(255, 183, 77, 0.1);
    border-left: 4px solid var(--color-warn);
    padding: 15px 18px;
    border-radius: 0 12px 12px 0;
    margin: 18px 0;
    font-size: var(--font-size-base);
    line-height: var(--line-height-base);
    color: #8B4513;
    font-weight: 500;
    box-shadow: 0 2px 8px rgba(255, 169, 88, 0.1);
}

/* 图标圆圈 */
.icon-circle {
    width: 45px;
    height: 45px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin: 0 12px 12px 0;
    font-size: 22px;
    color: white;
    font-weight: 700;
}

.icon-pink { 
    background: linear-gradient(45deg, var(--color-primary), #ff9a96);
    box-shadow: 0 4px 15px rgba(255, 126, 121, 0.3);
}

.icon-blue { 
    background: linear-gradient(45deg, var(--color-tertiary), #a8d5d5);
    box-shadow: 0 4px 15px rgba(142, 197, 197, 0.3);
}

.icon-orange { 
    background: linear-gradient(45deg, var(--color-warn), #ffb573);
    box-shadow: 0 4px 15px rgba(255, 169, 88, 0.3);
}

/* 响应式调整 */
@media (max-width: 480px) {
    .page-container {
        max-width: 100%;
        margin: 0;
    }
    
    .module {
        width: 100%;
    }
}
</style>
"""

# ===================================
# 9. 日志配置 (LOG_CONFIG)
# ===================================

LOG_CONFIG = {
    "level": "INFO",                                    # 日志级别
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 日志格式
    "file": os.path.join(LOGS_DIR, "automation.log"),  # 日志文件路径
    "max_size": "10MB",                                 # 单个日志文件最大大小
    "backup_count": 5,                                  # 备份文件数量
    "encoding": "utf-8"                                 # 日志文件编码
}

# ===================================
# 10. 其他配置项 (Other Configurations)
# ===================================

# 图片生成配置
IMAGE_CONFIG = {
    "default_width": 800,
    "default_height": 600,
    "quality": 85,
    "format": "JPEG"
}

# 内容生成配置
CONTENT_CONFIG = {
    "min_word_count": 200,      # 最小字数
    "max_word_count": 1000,     # 最大字数
    "target_reading_time": 3,   # 目标阅读时间（分钟）
}

# ===================================
# 11. 验证函数 (Validation Functions)
# ===================================

def validate_config():
    """验证配置的完整性和正确性"""
    
    required_vars = [
        'GEMINI_API_KEY',
        'MODEL_FOR_STRATEGY', 
        'MODEL_FOR_EXECUTION',
        'CACHE_DIR',
        'OUTPUT_DIR'
    ]
    
    missing_vars = []
    for var in required_vars:
        if var not in globals() or not globals()[var]:
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"缺少必需的配置项: {missing_vars}")
    
    # 验证目录存在
    for directory in [CACHE_DIR, OUTPUT_DIR, LOGS_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    print("配置验证通过")
    return True

if __name__ == "__main__":
    validate_config() 