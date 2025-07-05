"""
小红书内容自动化管线 - 配置中心
Configuration Center for Xiaohongshu Content Automation Pipeline

这是项目的神经中枢，所有其他模块都将从这里获取配置信息。
所有配置项都在此文件中统一管理，确保项目的可维护性和扩展性。
"""

import os
from pathlib import Path

# ===================================
# 1. 核心路径配置 (Core Path Configuration)
# ===================================

# 项目根目录 - 基于当前文件位置动态获取
BASE_DIR = Path(__file__).parent.absolute()

# 基于根目录动态生成各个子目录路径
CACHE_DIR = os.path.join(BASE_DIR, "cache")           # 缓存目录
OUTPUT_DIR = os.path.join(BASE_DIR, "output")         # 输出结果目录
LOGS_DIR = os.path.join(BASE_DIR, "logs")             # 日志目录
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")   # 模板目录

# 确保关键目录存在
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# ===================================
# 2. API & 模型配置 (API & Model Configuration)
# ===================================

import os

# Gemini API 官方SDK配置
GEMINI_API_KEY = "AIzaSyAHJifSef1yBljVkavGYhDeJWFvcW3l3Ks"  # 您提供的API Key

# 设置环境变量（官方SDK从此获取API Key）
os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY

# 兼容性配置（保留原有变量名以减少代码修改）
API_KEY = GEMINI_API_KEY

# 模型配置 - 使用Google官方SDK支持的模型名称
MODEL_FOR_STRATEGY = "gemini-2.5-pro"        # 策略规划阶段使用的模型  
MODEL_FOR_EXECUTION = "gemini-2.5-pro"       # 执行阶段使用的模型

# 备用模型（如果2.5-pro不可用）
FALLBACK_MODEL = "gemini-1.5-pro"

# AI调用参数
DEFAULT_TEMPERATURE = 0.7        # 默认温度参数，控制回答的创造性
DEFAULT_MAX_TOKENS = 4000        # 默认最大token数
MAX_RETRIES = 3                  # 最大重试次数
REQUEST_TIMEOUT = 60             # 请求超时时间（秒）

# ===================================
# 3. 流程控制与文件名 (Process Control & File Names)
# ===================================

# 流程控制开关
FORCE_STRATEGY = False           # 是否强制重新执行策略规划阶段
FORCE_EXECUTION = False          # 是否强制重新执行内容生成阶段

# 标准输出文件名
BLUEPRINT_FILENAME = "blueprint.json"        # 策略蓝图文件名
DESIGN_SPEC_FILENAME = "design_spec.json"   # 设计规格文件名
FINAL_HTML_FILENAME = "final_content.html"  # 最终HTML内容文件名
IMAGES_MANIFEST_FILENAME = "images_manifest.json"  # 图片清单文件名

# 临时文件名
TEMP_STRATEGY_FILENAME = "temp_strategy.json"
TEMP_EXECUTION_FILENAME = "temp_execution.json"

# ===================================
# 4. 人格核心 (Persona Core)
# ===================================

PERSONA_PROMPT = """你是"宝爸Conn"，一位充满智慧和温暖的资深父亲。

## 你的核心特质：
- **温暖陪伴者**：用温和、包容的语调，像和朋友聊天一样自然
- **实用主义者**：分享的每一个建议都经过实际验证，拒绝空泛的理论
- **生活观察家**：善于从日常小事中发现深刻的育儿智慧
- **情感共鸣者**：能准确捕捉并回应父母们的焦虑、困惑和期待

## 你的表达风格：
- 用"咱们"、"我家孩子"等亲近的称呼，营造亲密感
- 经常分享具体的个人经历和案例，让内容更有血肉
- 适度使用emoji，但不过度，保持成熟感
- 语言简洁明了，避免教条式的说教

## 你的专业深度：
- 拥有丰富的育儿实战经验，涵盖0-18岁各个阶段
- 对儿童心理学、教育学有深入理解，但表达通俗易懂
- 紧跟时代发展，了解数字时代的育儿新挑战

记住：你不是在写教科书，而是在和朋友分享你的人生智慧。"""

# ===================================
# 5. 策略罗盘 (Strategy Compass)
# ===================================

STRATEGY_PROMPT = """## 深度导向策略框架

你的任务是将用户提供的简单主题，转化为一个完整的小红书内容策略。请遵循以下框架：

### 1. 痛点挖掘 (Pain Point Mining)
- 识别目标受众在此主题下的核心痛点和困扰
- 分析痛点背后的深层心理需求
- 找出最具共鸣的情感触发点

### 2. 价值主张定位 (Value Proposition)
- 明确内容能为用户解决什么具体问题
- 确定独特的价值角度和差异化优势
- 设计清晰的行动指引和可操作建议

### 3. 内容架构设计 (Content Architecture)
- 规划开头、中间、结尾的逻辑结构
- 设计引人入胜的故事线或案例
- 确保内容层次清晰，易于理解和记忆

### 4. 视觉呈现规划 (Visual Presentation)
- 设计3-5张图片的主题和风格
- 每张图片都应有明确的功能：吸引注意、解释概念、展示结果等
- 确保图片与文字内容高度匹配

### 5. 互动engagement设计 (Engagement Design)
- 设计引发用户评论和分享的元素
- 包含能激发用户参与的话题或问题
- 考虑用户的使用场景和分享动机

输出格式：请以JSON格式输出完整的策略蓝图。"""

# ===================================
# 6. 战略规划 System Prompt
# ===================================

STRATEGY_SYSTEM_PROMPT = f"""
{PERSONA_PROMPT}

{STRATEGY_PROMPT}

作为"宝爸Conn"，你现在担任这个项目的**总规划师**角色。请结合你的温暖人格和专业深度，为用户提供的主题制定一个完整的内容策略。

请确保你的策略规划：
1. 体现出"宝爸Conn"的温暖和专业
2. 紧扣小红书平台的特点和用户习惯
3. 具有强烈的实用性和可操作性
4. 能够引起目标用户的情感共鸣

现在，请开始你的策略规划工作。
"""

# ===================================
# 7. 叙事执行 System Prompt - 小红书多图内容生成（已整合优化版prompt）
# ===================================

EXECUTION_SYSTEM_PROMPT = f"""
{PERSONA_PROMPT}

你现在是一位经验丰富、细心体贴、乐于分享、观察入微且**具备专业知识搜集、深度分析和模仿优秀案例能力的宝爸**，名叫 **Conn**。你的核心定位是**"有温度的专业主义者"**，像一位可靠的"学霸朋友"，善于将复杂的知识整理得清晰易懂，并在关键之处辅以温暖的经验提醒。

## 💡 核心创作原则：

### 身份定位与创作理念：
作为"宝爸Conn"，你将以专业的知识研究与整理者身份，深入研究小红书爆款笔记的成功要素，特别是：
- **内容框架与信息组织方式**：如何搭建内容结构、划分章节和段落
- **信息覆盖的广度与深度**：核心要点的细节阐述程度
- **用户痛点的切入角度**：如何精准抓住并解决目标用户的核心焦虑

### 【⭐⭐核心语言优化原则：拒绝"假词"与"虚词"，拥抱生活化表达⭐⭐】

#### 1. 拒绝"假词"，用细节建立说服力：
- **【定义】"假词"**：指那些看似华丽，实则空洞、无法给用户提供有效信息的形容词和废话。例如："超好看"、"巨好用"、"性价比绝了"、"很实用"、"高级感"、"神器"、"绝绝子"。
- **【核心方法论】强制替换**：将这些空洞的词语替换为**有说服力的细节**：
  * **具体场景**：它在什么情况下发生？（"开会坐了一下午，站起来时腰完全不酸了"）
  * **可量化数据**：效果可以被量化吗？（"实测充电15分钟，能用3小时"）
  * **生动细节/感官体验**：看起来/听起来/闻起来/摸起来怎么样？（"面料摸上去像云朵一样软糯，贴身穿一点都不扎"）

#### 2. 拒绝"虚词"，用大白话深入生活：
- **【定义】"虚词"**：指那些听起来高大上、华丽但脱离普通人生活、让人看不懂的词汇。例如："赋能"、"矩阵"、"链路"、"抓手"、"重塑"、"升维"、"顶层设计"。
- **【核心方法论】翻译成大白话**：把所有"虚词"都翻译成**接地气、易于理解的家常话**。写作的口吻应该是一个热心的朋友在给另一个朋友分享经验。

### 小红书多图发布要求：
- 生成3-5张独立的图片内容，每张图片都可以单独展示
- 第一张图片：封面图，包含标题和核心吸引点
- 中间图片：详细内容展示，每张图片聚焦一个核心要点
- 最后一张图片：总结和互动引导

### 真实性要求：
- 必须分享具体的个人经历，不能是泛泛而谈
- 要有真实的时间、地点、人物和对话
- 承认自己的错误和不足，展现真实的父亲形象
- 分享失败的尝试和从中学到的教训

### 具体性要求：
- 每个建议都要有详细的实施步骤
- 要有具体的物品推荐、时间安排、地点选择
- 包含真实的效果反馈和孩子的变化
- 避免空洞的理论，用生活中的小故事说明问题

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

### 内容分布策略：
- 图片1：封面 - 吸引眼球的标题 + 核心痛点
- 图片2-4：详细内容 - 每张图片展示一个具体方法或要点
- 图片5：总结 - 核心要点回顾 + 互动引导

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

# 宝爸Conn品牌设计系统 - 统一视觉风格模板
HTML_BASE_STYLE = """
<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    margin: 0;
    padding: 0;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
}

.page-container {
    width: 100%;
    max-width: 420px;
    background: #ffffff;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    position: relative;
    height: 560px;
    overflow: hidden;
    border-radius: 20px;
}

/* 宝爸Conn品牌水印 */
.brand-watermark {
    position: absolute;
    bottom: 15px;
    right: 20px;
    font-size: 11px;
    color: rgba(0, 0, 0, 0.4);
    font-weight: 500;
    z-index: 999;
    pointer-events: none;
    letter-spacing: 0.5px;
}

/* 统一内容模块 */
.content-module {
    width: 100%;
    height: 560px;
    padding: 30px 25px;
    position: relative;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* 封面图样式 */
.cover-module {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
    justify-content: center;
    align-items: center;
}

.cover-module .main-title {
    font-size: 28px;
    font-weight: 900;
    line-height: 1.2;
    margin-bottom: 20px;
    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.cover-module .subtitle {
    font-size: 14px;
    opacity: 0.9;
    line-height: 1.4;
    margin-bottom: 30px;
}

.cover-module .highlight-box {
    background: rgba(255, 255, 255, 0.15);
    padding: 15px 20px;
    border-radius: 12px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

/* 内容图样式 */
.content-module {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    color: #333;
}

.content-module .section-title {
    font-size: 24px;
    font-weight: 800;
    color: #2c3e50;
    margin-bottom: 20px;
    text-align: center;
}

.content-module .method-card {
    background: rgba(255, 255, 255, 0.9);
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 15px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    border-left: 4px solid #f39c12;
}

.content-module .method-title {
    font-size: 16px;
    font-weight: 700;
    color: #e74c3c;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
}

.content-module .method-title::before {
    content: "●";
    color: #f39c12;
    font-size: 12px;
    margin-right: 8px;
}

.content-module .method-desc {
    font-size: 13px;
    line-height: 1.5;
    color: #555;
}

.content-module .step-list {
    margin-top: 15px;
}

.content-module .step-item {
    display: flex;
    align-items: flex-start;
    margin-bottom: 10px;
    font-size: 12px;
    line-height: 1.4;
}

.content-module .step-number {
    background: #3498db;
    color: white;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 600;
    margin-right: 10px;
    flex-shrink: 0;
}

/* 第三张图 - 温馨绿色系 */
.content-module.green-theme {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
}

.content-module.green-theme .method-card {
    border-left-color: #27ae60;
}

.content-module.green-theme .method-title {
    color: #27ae60;
}

.content-module.green-theme .step-number {
    background: #27ae60;
}

/* 总结图样式 */
.summary-module {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    color: #333;
    padding: 25px;
}

.summary-module .summary-title {
    font-size: 22px;
    font-weight: 800;
    color: #2c3e50;
    text-align: center;
    margin-bottom: 25px;
}

.summary-module .key-points {
    background: rgba(255, 255, 255, 0.9);
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.summary-module .point-item {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    font-size: 14px;
    line-height: 1.4;
}

.summary-module .point-item::before {
    content: "✓";
    color: #27ae60;
    font-weight: 900;
    margin-right: 10px;
    font-size: 16px;
}

.summary-module .cta-box {
    background: #3498db;
    color: white;
    padding: 15px 20px;
    border-radius: 12px;
    text-align: center;
    margin-top: 20px;
}

.summary-module .cta-text {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 5px;
}

.summary-module .cta-action {
    font-size: 12px;
    opacity: 0.9;
}

/* 响应式和通用样式 */
.highlight-text {
    background: linear-gradient(90deg, #f39c12, #e74c3c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700;
}

.warm-tip {
    background: rgba(255, 183, 77, 0.1);
    border-left: 3px solid #f39c12;
    padding: 12px 15px;
    border-radius: 0 8px 8px 0;
    margin: 15px 0;
    font-size: 12px;
    line-height: 1.4;
    color: #856404;
}

.icon-circle {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin: 0 10px 10px 0;
    font-size: 20px;
    color: white;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.icon-orange { background: linear-gradient(45deg, #ff6b6b, #feca57); }
.icon-blue { background: linear-gradient(45deg, #48dbfb, #0abde3); }
.icon-green { background: linear-gradient(45deg, #1dd1a1, #10ac84); }
.icon-purple { background: linear-gradient(45deg, #a55eea, #8854d0); }
</style>"""

# ===================================
# 9. 日志配置 (LOG_CONFIG)
# ===================================

LOG_CONFIG = {
    font-size: 44px;
    font-weight: 900;
    color: #1a1a1a;
    text-align: center;
    margin-bottom: 20px;
    line-height: 1.2;
}

.section-title h2 {
    font-size: 22px;
    font-weight: 700;
    color: #333;
    background: rgba(255, 248, 220, 0.8);
    padding: 8px 12px;
    border-radius: 8px;
    margin-bottom: 15px;
}

/* 高密度干货样式 */
.high-density {
    font-size: 13px;
    line-height: 1.6;
}

.high-density h2 {
    font-size: 20px;
    margin-bottom: 12px;
}

.high-density h3 {
    font-size: 16px;
    margin-bottom: 10px;
}

/* 舒适阅读样式 */
.comfortable-reading {
    font-size: 15px;
    line-height: 1.8;
}

.comfortable-reading h2 {
    font-size: 24px;
    margin-bottom: 16px;
}

.comfortable-reading h3 {
    font-size: 18px;
    margin-bottom: 12px;
}

/* 键值对列表 */
.key-value-list {
    list-style: none;
    padding: 0;
}

.key-value-list li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #f0f0f0;
}

.key-value-list li:last-child {
    border-bottom: none;
}

.key-value-list .key {
    font-weight: 600;
    color: #333;
    display: flex;
    align-items: center;
}

.key-value-list .value {
    color: #666;
    text-align: right;
    flex: 1;
    margin-left: 10px;
}

/* 高亮信息框 */
.highlight-box {
    background: linear-gradient(135deg, #fff5e6 0%, #ffe6cc 100%);
    border-left: 4px solid #ff6b35;
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
}

.highlight-box.info {
    background: linear-gradient(135deg, #e6f3ff 0%, #cce7ff 100%);
    border-left-color: #2196f3;
}

.highlight-box.success {
    background: linear-gradient(135deg, #e8f5e8 0%, #d4edd4 100%);
    border-left-color: #4caf50;
}

.highlight-box.warning {
    background: linear-gradient(135deg, #fff3e0 0%, #ffe0b3 100%);
    border-left-color: #ff9800;
}

/* 最终页面模块 */
.final-page-module {
    width: 100%;
    height: 560px;
    padding: 60px 25px;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    background: linear-gradient(135deg, #f8f9ff 0%, #e8f4fd 100%);
}

.final-greeting {
    font-size: 24px;
    font-weight: 700;
    color: #333;
    margin-bottom: 30px;
}

.cta-box {
    background: rgba(255, 255, 255, 0.9);
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.final-brand {
    font-size: 16px;
    color: #666;
    font-weight: 500;
    margin-top: 20px;
}

/* Emoji样式 */
.emoji {
    font-size: 20px;
    margin-right: 5px;
}

/* 响应式调整 */
@media (max-width: 480px) {
    .page-container {
        max-width: 100%;
        margin: 0;
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

# 验证配置
VALIDATION_CONFIG = {
    "check_api_key": True,      # 是否检查API密钥
    "check_directories": True,  # 是否检查目录结构
    "check_dependencies": True  # 是否检查依赖项
}

# ===================================
# 配置验证函数 (Configuration Validation)
# ===================================

def validate_config():
    """验证配置的有效性"""
    errors = []
    
    if not API_KEY:
        errors.append("API_KEY 未设置，请在环境变量中设置 OPENAI_API_KEY")
    
    if not os.path.exists(CACHE_DIR):
        errors.append(f"缓存目录不存在: {CACHE_DIR}")
    
    if not os.path.exists(OUTPUT_DIR):
        errors.append(f"输出目录不存在: {OUTPUT_DIR}")
    
    if errors:
        print("配置验证失败：")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("配置验证通过")
    return True

# 在导入时自动验证配置
if __name__ == "__main__":
    validate_config()