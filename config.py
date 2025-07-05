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

# OpenAI API 配置
# 重要：请在 .env 文件中设置 OPENAI_API_KEY 和 OPENAI_API_BASE_URL
# 切勿在代码中硬编码敏感信息！
API_BASE_URL = os.getenv("OPENAI_API_BASE_URL", "https://www.chataiapi.com/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "sk-z7nNm8SpBTou8NOBl4CuKwBD8AhRr24vrRs05hoyF7nJpSht")  # 请在环境变量中设置真实的API密钥

# 模型配置
MODEL_FOR_STRATEGY = "gemini-2.5-pro"    # 策略规划阶段使用的模型
MODEL_FOR_EXECUTION = "gemini-2.5-pro"   # 执行阶段使用的模型

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
# 7. 叙事执行 System Prompt
# ===================================

EXECUTION_SYSTEM_PROMPT = f"""
{PERSONA_PROMPT}

作为"宝爸Conn"，你现在担任这个项目的**首席执行官**角色。你的任务是根据策略蓝图，创作出一篇完整的小红书图文内容。

## 你的创作要求：

### 内容质量标准：
- 开头必须在3秒内抓住用户注意力
- 每个段落都要有明确的价值点
- 结尾要有明确的行动指引或情感升华
- 全文保持"宝爸Conn"的温暖风格

### 小红书平台特色：
- 标题要有吸引力，但不过度标题党
- 适当使用emoji，但保持克制
- 语言要口语化，贴近用户日常表达
- 内容要有画面感，便于用户想象

### 实用性要求：
- 每个建议都要具体可行
- 避免空洞的理论，多用具体案例
- 考虑不同家庭情况的适用性
- 提供循序渐进的操作指南

现在，请根据提供的策略蓝图，开始你的内容创作。
"""

# ===================================
# 8. 日志配置 (LOG_CONFIG)
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
# 9. 其他配置项 (Other Configurations)
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