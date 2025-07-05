"""
小红书内容自动化管线 - 执行模块
Xiaohongshu Content Automation Pipeline - Execution Module

这是流水线中技术最核心的阶段，负责将战略蓝图转化为文案和HTML。
采用双重缓存架构，分为"叙事与设计"和"视觉编码"两个可缓存的子阶段。

主要功能：
1. 双重缓存架构：分阶段生成和缓存中间结果
2. 健壮的AI调用：自动处理JSON解析错误并重试
3. 叙事与设计：生成设计规范文档
4. 视觉编码：将设计规范转化为HTML
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import time
from datetime import datetime
from google import genai

# 导入项目配置和工具
from config import (
    GEMINI_API_KEY, MODEL_FOR_EXECUTION, FALLBACK_MODEL,
    MAX_RETRIES, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS,
    CACHE_DIR, OUTPUT_DIR, EXECUTION_SYSTEM_PROMPT,
    DESIGN_SPEC_FILENAME, FINAL_HTML_FILENAME, HTML_BASE_STYLE, XIAOHONGSHU_IMAGE_WIDTH, XIAOHONGSHU_IMAGE_HEIGHT,
    SCREENSHOT_CONFIG
)
from .utils import save_json, load_json, get_logger

# 导入数据模型
from .models import DesignSpecification

# ===================================
# 模块级别配置
# ===================================

logger = get_logger(__name__)

# ===================================
# 核心AI调用函数
# ===================================

def _call_gemini_with_self_correction(
    system_prompt: str,
    user_prompt: str,
    expect_json: bool = True,
    max_retries: int = 3,
    max_tokens: int = 4000,
    use_structured_output: bool = False,
    response_schema = None
) -> Dict[str, Any]:
    """
    调用Gemini API并支持自我修正
    
    Args:
        system_prompt (str): 系统提示词
        user_prompt (str): 用户提示词  
        expect_json (bool): 是否期望JSON响应
        max_retries (int): 最大重试次数
        max_tokens (int): 最大token数量
        use_structured_output (bool): 是否使用结构化输出
        response_schema: 响应的Pydantic模型schema
    
    Returns:
        Dict[str, Any]: 解析后的响应内容
    """
    logger.info(f"开始调用Gemini API，期望JSON: {expect_json}")
    
    # 保存原始用户提示词，用于重试时的错误反馈
    original_user_prompt = user_prompt
    current_user_prompt = user_prompt
    
    for current_attempt in range(max_retries):
        try:
            logger.info(f"第 {current_attempt + 1} 次尝试调用API")
            
            # 创建Gemini客户端
            client = genai.Client()
            
            # 合并system prompt和user prompt
            combined_prompt = f"{system_prompt}\n\n{current_user_prompt}"
            
            # 尝试使用主要模型
            model = MODEL_FOR_EXECUTION
            
            try:
                # 使用官方SDK调用API
                if use_structured_output and response_schema:
                    # 使用结构化输出
                    response = client.models.generate_content(
                        model=model,
                        contents=combined_prompt,
                        config={
                            "response_mime_type": "application/json",
                            "response_schema": response_schema,
                        },
                    )
                else:
                    # 普通调用
                    response = client.models.generate_content(
                        model=model,
                        contents=combined_prompt,
                    )
                
                # 如果使用结构化输出，直接使用解析的结果
                if use_structured_output and response_schema:
                    parsed_result = response.parsed
                    
                    # 检查解析结果并转换为字典
                    if hasattr(parsed_result, 'model_dump'):
                        result_dict = parsed_result.model_dump()  # type: ignore
                        logger.info(f"✓ Gemini API调用成功（结构化输出），使用模型: {model}")
                        return result_dict
                    else:
                        raise ValueError(f"API响应类型不正确: {type(parsed_result)}")
                else:
                    content = response.text
                
            except Exception as model_error:
                # 如果主要模型失败，尝试备用模型
                if model != FALLBACK_MODEL:
                    logger.warning(f"主要模型 {model} 失败，尝试备用模型 {FALLBACK_MODEL}: {model_error}")
                    model = FALLBACK_MODEL
                    
                    # 使用备用模型重新调用
                    if use_structured_output and response_schema:
                        # 使用结构化输出
                        response = client.models.generate_content(
                            model=model,
                            contents=combined_prompt,
                            config={
                                "response_mime_type": "application/json",
                                "response_schema": response_schema,
                            },
                        )
                    else:
                        # 普通调用
                        response = client.models.generate_content(
                            model=model,
                            contents=combined_prompt,
                        )
                    
                    # 如果使用结构化输出，直接使用解析的结果
                    if use_structured_output and response_schema:
                        parsed_result = response.parsed
                        
                        # 检查解析结果并转换为字典
                        if hasattr(parsed_result, 'model_dump'):
                            result_dict = parsed_result.model_dump()  # type: ignore
                            logger.info(f"✓ Gemini API调用成功（结构化输出），使用模型: {model}")
                            return result_dict
                        else:
                            raise ValueError(f"API响应类型不正确: {type(parsed_result)}")
                    else:
                        content = response.text
                else:
                    raise model_error
            
            # 检查响应内容是否为空
            if not content:
                raise Exception("API返回了空的响应内容")
            
            logger.info(f"API调用成功，使用模型: {model}，响应长度: {len(content)}")
            
            # 如果不需要JSON解析，直接返回文本内容
            if not expect_json:
                return {"content": content, "raw_response": content}
            
            # 预处理响应内容，去除可能的代码块包装
            cleaned_content = content.strip()
            
            # 如果内容以```json开头，去除代码块包装
            if cleaned_content.startswith('```json'):
                logger.info("检测到代码块包装，自动去除")
                # 找到第一个换行符后的内容
                start_idx = cleaned_content.find('\n')
                if start_idx != -1:
                    cleaned_content = cleaned_content[start_idx + 1:]
                    
                # 如果以```结尾，去除结尾的```
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]
                
                # 再次去除首尾空格
                cleaned_content = cleaned_content.strip()
            
            # 如果内容以```开头但不是```json，也进行类似处理
            elif cleaned_content.startswith('```'):
                logger.info("检测到代码块包装（非json），自动去除")
                start_idx = cleaned_content.find('\n')
                if start_idx != -1:
                    cleaned_content = cleaned_content[start_idx + 1:]
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()
            
            # 处理可能的特殊字符和转义问题
            # 去除可能存在的BOM字符
            if cleaned_content.startswith('\ufeff'):
                cleaned_content = cleaned_content[1:]
            
            # 确保内容完整性 - 如果是不完整的JSON，尝试修复
            if cleaned_content.startswith('{') and not cleaned_content.endswith('}'):
                logger.warning("检测到JSON可能不完整，内容被截断")
                # 如果是因为response被截断，这里可以添加处理逻辑
                pass
            
            # 尝试修复常见的JSON问题
            cleaned_content = _fix_json_issues(cleaned_content)
            
            # 尝试解析JSON
            try:
                parsed_json = json.loads(cleaned_content)
                logger.info("JSON解析成功")
                return parsed_json
                
            except json.JSONDecodeError as json_error:
                logger.warning(f"JSON解析失败: {json_error}")
                
                # 输出调试信息，显示实际的响应内容
                logger.error(f"原始响应内容（前200字符）: {repr(content[:200])}")
                logger.error(f"清理后内容（前200字符）: {repr(cleaned_content[:200])}")
                logger.error(f"清理后内容长度: {len(cleaned_content)}")
                
                # 如果这是最后一次尝试，抛出异常
                if current_attempt >= max_retries - 1:
                    # 尝试保存失败的JSON到文件用于调试
                    debug_file = f"cache/debug_failed_json_{int(time.time())}.txt"
                    try:
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(f"Original Content:\n{content}\n\n")
                            f.write(f"Cleaned Content:\n{cleaned_content}\n\n")
                            f.write(f"Error: {json_error}\n")
                        logger.info(f"失败的JSON内容已保存到: {debug_file}")
                    except Exception as e:
                        logger.warning(f"无法保存调试文件: {e}")
                    
                    raise Exception(f"达到最大重试次数({max_retries})，JSON解析仍然失败: {json_error}")
                
                # 构造错误反馈提示，让AI自我修正
                error_feedback = f"""
前一次的回复无法解析为有效的JSON格式。

错误信息：{json_error}

你的回复内容开头是：{cleaned_content[:200]}

请检查你的回复格式，确保：
1. 回复必须是纯JSON格式，不要包含任何解释文字
2. 不要使用```json```代码块包装
3. 使用正确的JSON语法
4. 所有字符串都用双引号包围
5. 所有括号和大括号都正确配对
6. 避免使用JSON不支持的字符（如单引号、注释等）
7. 确保所有字符串都正确闭合，没有遗漏结束的双引号
8. 避免在字符串中使用未转义的特殊字符

请简化内容并重新生成符合JSON格式的回复，直接输出JSON内容，不要任何其他文字。

原始请求：
{original_user_prompt}
"""
                
                # 更新用户提示词用于下次重试
                current_user_prompt = error_feedback
                logger.info("准备重试，将错误反馈给AI进行自我修正")
                
        except Exception as api_error:
            logger.error(f"API调用失败: {api_error}")
            
            # 如果这是最后一次尝试，抛出异常
            if current_attempt >= max_retries - 1:
                raise Exception(f"达到最大重试次数({max_retries})，API调用失败: {api_error}")
            
            # 等待后重试
            time.sleep(2)
            logger.info(f"等待2秒后重试...")
    
    # 如果所有重试都失败了，抛出异常
    raise Exception(f"达到最大重试次数({max_retries})，API调用失败")

# 为保持向后兼容性，保留原有函数名
def _call_openai_with_self_correction(
    system_prompt: str,
    user_prompt: str,
    expect_json: bool = True,
    max_retries: int = 3,
    max_tokens: int = 4000
) -> Dict[str, Any]:
    """
    兼容性函数，实际调用Gemini API
    """
    return _call_gemini_with_self_correction(
        system_prompt, user_prompt, expect_json, max_retries, max_tokens
    )

def _fix_json_issues(json_str: str) -> str:
    """
    修复常见的JSON格式问题
    
    Args:
        json_str (str): 可能有问题的JSON字符串
        
    Returns:
        str: 修复后的JSON字符串
    """
    # 去除首尾空白
    json_str = json_str.strip()
    
    # 确保JSON以{开头，}结尾
    if not json_str.startswith('{'):
        # 查找第一个{
        start_idx = json_str.find('{')
        if start_idx != -1:
            json_str = json_str[start_idx:]
    
    if not json_str.endswith('}'):
        # 查找最后一个}
        end_idx = json_str.rfind('}')
        if end_idx != -1:
            json_str = json_str[:end_idx + 1]
    
    # 处理常见的字符串问题
    # 替换可能导致问题的字符
    json_str = json_str.replace('\n', '\\n')  # 换行符
    json_str = json_str.replace('\r', '\\r')  # 回车符
    json_str = json_str.replace('\t', '\\t')  # 制表符
    
    # 尝试修复未闭合的字符串（简单处理）
    # 这是一个基本的修复，可能需要更复杂的逻辑
    if json_str.count('"') % 2 != 0:
        # 字符串引号数量为奇数，可能有未闭合的字符串
        logger.warning("检测到可能的未闭合字符串，尝试修复")
        # 简单的修复：在末尾添加引号和闭合括号
        if not json_str.endswith('"') and not json_str.endswith('}'):
            json_str += '"}'
    
    return json_str

# ===================================
# 叙事与设计阶段
# ===================================

def _generate_design_specification(blueprint: Dict[str, Any], theme: str) -> Dict[str, Any]:
    """
    生成设计规范，为小红书多图内容提供详细的创作指南
    
    Args:
        blueprint (Dict[str, Any]): 来自策略模块的创作蓝图
        theme (str): 内容主题
        
    Returns:
        Dict[str, Any]: 包含多图内容创作规范的设计文档
    """
    logger.info("开始生成小红书多图内容设计规范")
    
    # 构建设计规范生成提示词（已整合优化版prompt）
    design_prompt = f"""
请根据以下策略蓝图，以宝爸Conn的身份为小红书多图内容生成详细的设计规范。

**主题**: {theme}

**策略蓝图**: {json.dumps(blueprint, ensure_ascii=False, indent=2)}

## 重要身份设定：
你是宝爸Conn，一位经验丰富、细心体贴、乐于分享的"有温度的专业主义者"。你不是专家在讲课，而是朋友在分享真实的育儿经历。

## 核心语言优化原则：
1. **拒绝"假词"**：不用"超好看"、"巨好用"、"性价比绝了"等空洞词汇，用具体细节建立说服力
2. **拒绝"虚词"**：不用"赋能"、"矩阵"、"链路"等高大上词汇，用大白话表达
3. **具体场景**：要有具体的时间、地点、人物和对话
4. **可量化数据**：用实测数据证明效果
5. **生动细节**：用感官体验描述

请生成一个包含以下结构的JSON对象：

{{
    "content_overview": {{
        "theme": "{theme}",
        "total_images": 4,
        "target_audience": "年轻父母群体",
        "content_style": "宝爸Conn的温暖实用分享",
        "persona_voice": "有温度的专业主义者，像学霸朋友一样"
    }},
    "xiaohongshu_titles": [
        "爆款标题1 - 攻略/干货型（保姆级、手把手）",
        "爆款标题2 - 痛点/解惑型（讲透了、终于搞懂）",
        "爆款标题3 - 共鸣/安心型（@新手爸妈、别焦虑）",
        "爆款标题4 - 结果/受益型（省钱、省时、避坑）",
        "爆款标题5 - 总结/合集型（吐血整理、必看）"
    ],
    "xiaohongshu_content": "完整的小红书正文内容，严格按照爆款黄金三句话法则：第一句沉浸式代入+情绪共鸣，第二句反转解脱+价值捧出，第三句建立圈子+开启话匣子。必须包含真实的个人经历、具体的实施步骤、温暖的情感表达，用宝爸Conn的语调写作，最后附上hashtags。",
    "image_contents": [
        {{
            "image_number": 1,
            "type": "封面图",
            "title": "吸引眼球的标题（图文插画型内容封面）",
            "main_content": "核心痛点或吸引点，包含第一个核心内容章节",
            "visual_elements": ["巨大标题44px", "第一章节内容", "温暖色调"],
            "color_scheme": "温暖橙色系",
            "layout": "图文插画型内容封面",
            "height_constraint": "严格控制在560px以内"
        }},
        {{
            "image_number": 2,
            "type": "内容图",
            "title": "第一个核心要点",
            "main_content": "具体的方法或经验分享，包含真实案例",
            "visual_elements": ["步骤编号", "重点文字", "个人经历"],
            "color_scheme": "清新绿色系",
            "layout": "上下结构布局",
            "height_constraint": "严格控制在560px以内"
        }},
        {{
            "image_number": 3,
            "type": "内容图",
            "title": "第二个核心要点",
            "main_content": "具体的方法或经验分享，包含可量化数据",
            "visual_elements": ["对比数据", "重点文字", "感官体验"],
            "color_scheme": "温馨蓝色系",
            "layout": "左右对比布局",
            "height_constraint": "严格控制在560px以内"
        }},
        {{
            "image_number": 4,
            "type": "总结图",
            "title": "核心要点总结",
            "main_content": "总结要点和行动指引，互动引导",
            "visual_elements": ["要点列表", "互动引导", "结尾互动"],
            "color_scheme": "渐变紫色系",
            "layout": "列表式布局",
            "height_constraint": "严格控制在560px以内"
        }}
    ],
    "design_principles": {{
        "size_constraint": "420x560px（3:4黄金比例）",
        "font_hierarchy": "主标题44px，章节标题22px，正文13px（高密度）",
        "color_palette": ["#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1"],
        "spacing": "内边距25px 15px，元素间距适中",
        "visual_consistency": "统一的圆角风格，一致的阴影效果",
        "brand_signature": "@宝爸Conn右下角水印，不占文档流"
    }},
    "engagement_elements": {{
        "call_to_action": "建立圈子，开启话匣子的具体文案",
        "hashtags": ["#育儿经验", "#宝爸日常", "#实用技巧", "#新手爸妈"],
        "emotional_triggers": ["真实经历共鸣", "具体效果证明", "温暖陪伴感"]
    }}
}}

请确保：
1. 内容真实具体，体现宝爸Conn的个人经历和温暖语调
2. 每张图片都有独立完整的信息，严格控制在560px高度内
3. 视觉设计简洁美观，适合小红书平台
4. 文案拒绝假词虚词，用具体细节和大白话
5. 包含可操作的具体建议和真实案例
6. 品牌署名使用@宝爸Conn右下角水印
"""
    
    try:
        # 调用AI生成设计规范
        result = _call_gemini_with_self_correction(
            system_prompt=EXECUTION_SYSTEM_PROMPT,
            user_prompt=design_prompt,
            expect_json=True,
            max_retries=3,
            max_tokens=6000,
            use_structured_output=True,
            response_schema=DesignSpecification
        )
        
        logger.info("✓ 设计规范生成成功")
        return result
        
    except Exception as e:
        logger.error(f"设计规范生成失败：{str(e)}")
        raise Exception(f"设计规范生成失败：{str(e)}")

def _generate_html_pages(design_spec: Dict[str, Any]) -> Dict[str, str]:
    """
    根据设计规范生成多个HTML页面，每个页面对应一张小红书图片
    
    Args:
        design_spec (Dict[str, Any]): 设计规范文档
        
    Returns:
        Dict[str, str]: 页面名称到HTML内容的映射
    """
    logger.info("开始生成小红书多图HTML页面")
    
    html_pages = {}
    
    # 获取图片内容列表
    image_contents = design_spec.get("image_contents", [])
    
    for img_content in image_contents:
        img_num = img_content["image_number"]
        img_type = img_content["type"]
        
        # 生成HTML内容（使用新的设计系统）
        html_prompt = f"""
请根据以下设计规范生成一个HTML页面，用于小红书图片截图。

**页面信息**:
- 图片编号: {img_num}
- 图片类型: {img_type}
- 标题: {img_content["title"]}
- 主要内容: {img_content["main_content"]}
- 视觉元素: {img_content["visual_elements"]}
- 配色方案: {img_content["color_scheme"]}
- 布局风格: {img_content["layout"]}

**严格技术要求**:
- 页面尺寸: {XIAOHONGSHU_IMAGE_WIDTH}x{XIAOHONGSHU_IMAGE_HEIGHT}px（3:4黄金比例）
- 高度控制：严格控制在560px以内，使用逐元素填充与实时高度监控
- 所有样式必须内联到HTML中
- 不使用外部图片，用CSS绘制图标
- 使用Noto Sans SC字体
- 确保在无头浏览器中正常渲染

**宝爸Conn品牌设计系统（必须使用）**:
使用以下CSS变量和样式类：

```css
:root {{
    --color-primary: #FF7E79;    /* 主题粉色 */
    --color-secondary: #FFD6D4;  /* 浅粉 */
    --color-tertiary: #8EC5C5;   /* 辅助青色 */
    --color-bg-tertiary: #F0FAFA; /* 青色背景 */
    --color-warn: #FFA958;       /* 警告橙色 */
    --color-warn-bg: #FFF7EE;    /* 警告背景 */
    --color-text-dark: #333333;
    --color-text-light: #555555;
    --color-text-white: #FFFFFF;
    --color-bg-light: #FFF7F7;
    --color-border: #FFEAE8;
    --font-size-base: 13.5px;
    --line-height-base: 1.65;
    --font-size-h1: 38px;
    --font-size-h2: 22px;
    --font-size-h3: 16px;
}}
```

**必须使用的样式类**:
- `.page-container` - 主容器，包含左边框装饰
- `.module` - 页面模块，420x560px
- `.brand-watermark` - 品牌水印
- `.cover-title` - 封面标题（38px，粉色）
- `.section-title` - 章节标题（22px，居中圆角）
- `.title-mom` - 妈妈主题（粉色背景）
- `.title-baby` - 宝宝主题（青色背景）
- `.title-warn` - 警告主题（橙色背景）
- `.key-value-list` - 信息列表
- `.highlight-red` - 粉色高亮
- `.highlight-blue` - 青色高亮
- `.highlight-orange` - 橙色高亮
- `.highlight-box` - 重要提醒框
- `.center-wrapper` - 居中包装器

**基本HTML结构**:
```html
<div class="page-container">
    <div class="module">
        <!-- 根据图片类型选择相应的内容结构 -->
        <div class="brand-watermark">@宝爸Conn</div>
    </div>
</div>
```

**内容要求**:
- 体现宝爸Conn的温暖语调和专业态度
- 拒绝假词虚词，用具体细节和大白话
- 包含真实的个人经历或具体案例
- 重要信息使用高亮色彩突出
- 使用emoji图标增强可读性

**设计规范**:
{json.dumps(design_spec.get("design_principles", {}), ensure_ascii=False, indent=2)}

请生成完整的HTML页面代码，包含所有必要的样式和内容。HTML结构要清晰，样式要完整。
确保使用新的设计系统的CSS变量和样式类。

格式要求：直接输出HTML代码，不要用代码块包装。
"""
        
        try:
            # 调用AI生成HTML（使用新的设计系统）
            result = _call_gemini_with_self_correction(
                system_prompt="""
你是宝爸Conn团队的"原子设计师" - 专门将创意转化为精确可执行代码的系统架构师。

## 🎯 核心理念："AI的母语是逻辑和代码，不是抽象审美"

### 【原子设计师职责】：
- **精确指令生成**：将设计意图转化为100%可执行的HTML/CSS代码
- **系统化视觉架构**：不是"画图"，而是"编程视觉逻辑"  
- **技术性美学**：通过代码结构实现视觉层次和品牌一致性

## 🎨 宝爸Conn设计系统（基于优秀案例升级）

### 新设计系统的核心特点：
1. **三色系统**：主题粉色(#FF7E79)、辅助青色(#8EC5C5)、警告橙色(#FFA958)
2. **高密度排版**：字体13.5px，行高1.65，信息密度高但可读性强
3. **左侧装饰边框**：8px粉色边框，增强品牌识别度
4. **模块化主题**：妈妈篇(粉色)、宝宝篇(青色)、提醒框(橙色)

### 页面基本结构：
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&display=swap" rel="stylesheet">
    <style>
        [内联CSS样式 - 基于新设计系统]
    </style>
</head>
<body>
    <div class="page-container">
        <div class="module">
            [具体内容]
            <div class="brand-watermark">@宝爸Conn</div>
        </div>
    </div>
</body>
</html>
```

### 必须使用的样式类：

#### 1. 封面页面：
- 主容器：`<div class="page-container">`
- 页面模块：`<div class="module">`
- 封面标题：`<h1 class="cover-title">`（38px，粉色）
- 副标题：`<div class="cover-subtitle">`
- 高亮框：`<div class="cover-highlight-box">`

#### 2. 内容页面：
- 主容器：`<div class="page-container">`
- 页面模块：`<div class="module">`
- 章节标题：`<div class="section-title title-mom/title-baby/title-warn">`
- 居中包装：`<div class="center-wrapper">`
- 信息列表：`<ul class="key-value-list">`
- 列表项：`<li>`，包含`<span class="icon">📱</span>`、`<span class="key">标题：</span>`、`<span class="value">内容</span>`
- 重要提醒：`<div class="highlight-box">`

#### 3. 高亮文本：
- 粉色高亮：`<span class="highlight-red">重要内容</span>`
- 青色高亮：`<span class="highlight-blue">重要内容</span>`
- 橙色高亮：`<span class="highlight-orange">重要内容</span>`

#### 4. 结尾页面：
- 页面模块：`<div class="module final-module">`
- 结尾问候：`<div class="final-greeting">`
- 行动框：`<div class="cta-box">`
- 品牌标识：`<div class="final-brand">`

### CSS变量系统（必须使用）：
```css
:root {
    --color-primary: #FF7E79;    /* 主题粉色 */
    --color-secondary: #FFD6D4;  /* 浅粉 */
    --color-tertiary: #8EC5C5;   /* 辅助青色 */
    --color-bg-tertiary: #F0FAFA; /* 青色背景 */
    --color-warn: #FFA958;       /* 警告橙色 */
    --color-warn-bg: #FFF7EE;    /* 警告背景 */
    --color-text-dark: #333333;
    --color-text-light: #555555;
    --color-text-white: #FFFFFF;
    --color-bg-light: #FFF7F7;
    --color-border: #FFEAE8;
    --font-size-base: 13.5px;
    --line-height-base: 1.65;
    --font-size-h1: 38px;
    --font-size-h2: 22px;
    --font-size-h3: 16px;
    --font-size-cta: 28px;
}
```

### 极简内容结构要求：
1. **高密度文字信息**：每页5-8个实用要点
2. **仅用emoji图标**：简单emoji，不要CSS绘制图形
3. **key-value列表**：标题+具体内容，清晰实用
4. **可操作性**：具体数值、时间、方法、品牌推荐

### 技术要求（极简化）：
- 页面尺寸：420x560px
- 左侧边框：8px solid var(--color-secondary)
- 品牌水印：右下角，opacity: 0.15
- 字体：Noto Sans SC，13.5px高密度排版
- **禁止**：CSS绘制图形、复杂装饰、多余视觉元素
- **专注**：文字内容、信息密度、实用性

### 生成要求（极简风格）：
1. **禁止CSS绘制装饰图形** - 只用emoji图标
2. **高密度文字内容** - 每页5-8个要点，信息量大
3. **简洁列表结构** - 使用key-value列表，清晰易读
4. **三色系统** - 仅用颜色区分主题，不添加装饰
5. **精确尺寸控制** - 420x560px，左侧8px装饰边框

参考用户提供的优秀案例风格：简洁、信息密度高、emoji图标、列表式排版。

请作为"原子设计师"，生成简洁实用的HTML，专注内容而非装饰。
""",
                user_prompt=html_prompt,
                expect_json=False,
                max_retries=2,
                max_tokens=3000
            )
            
            html_content = result.get("content", "")
            
            # 如果HTML内容不包含基础样式，则添加（极简风格）
            if "<style>" not in html_content:
                html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小红书图片{img_num}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&display=swap" rel="stylesheet">
    {HTML_BASE_STYLE}
</head>
<body>
    <div class="page-container">
        <div class="module">
            <div class="center-wrapper">
                <div class="section-title title-mom">{img_content["title"]}</div>
            </div>
            <ul class="key-value-list">
                <li>
                    <span class="icon">📝</span>
                    <div>
                        <span class="key">要点：</span>
                        <span class="value">{img_content["main_content"]}</span>
                    </div>
                </li>
            </ul>
            <div class="brand-watermark">@宝爸Conn</div>
        </div>
    </div>
</body>
</html>"""
            
            # 确保HTML包含必要的标签
            if not html_content.startswith("<!DOCTYPE html>"):
                html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小红书图片{img_num}</title>
</head>
<body>
{html_content}
</body>
</html>"""
            
            page_name = f"page_{img_num}_{img_type}"
            html_pages[page_name] = html_content
            
            logger.info(f"✓ HTML页面生成成功: {page_name}")
            
        except Exception as e:
            logger.warning(f"AI生成HTML失败: {e}, 使用备用模板")
            
            # 使用备用模板（优化版样式）
            fallback_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小红书图片{img_num}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&display=swap" rel="stylesheet">
    {HTML_BASE_STYLE}
    <style>
    .page-{img_num} {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }}
    .content-box {{
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        backdrop-filter: blur(10px);
    }}
    </style>
</head>
<body class="page-{img_num}">
    <div class="page-container">
        <div class="illustrated-content-module high-density">
            <h1 class="icm-title">{img_content["title"]}</h1>
            <div class="content-section">
                <div class="content-box">
                    <p>{img_content["main_content"]}</p>
                </div>
            </div>
            <div class="brand-watermark">@宝爸Conn</div>
        </div>
    </div>
</body>
</html>"""
            
            page_name = f"page_{img_num}_{img_type}"
            html_pages[page_name] = fallback_html
            
            logger.info(f"✓ 备用HTML页面生成成功: {page_name}")
    
    logger.info(f"所有HTML页面生成完成，共{len(html_pages)}个页面")
    return html_pages

def _generate_final_html(design_spec: Dict[str, Any]) -> str:
    """
    生成最终的HTML内容（兼容性函数，实际生成多个页面）
    
    Args:
        design_spec (Dict[str, Any]): 设计规范文档
        
    Returns:
        str: 主HTML内容（第一个页面）
    """
    logger.info("开始生成最终HTML内容")
    
    # 生成所有HTML页面
    html_pages = _generate_html_pages(design_spec)
    
    # 返回第一个页面作为主HTML（保持兼容性）
    if html_pages:
        first_page = list(html_pages.values())[0]
        logger.info("✓ 主HTML页面生成成功")
        return first_page
    else:
        logger.warning("未生成任何HTML页面，使用备用方案")
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小红书内容</title>
    <style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
        width: 448px;
        height: 597px;
        margin: 0;
        padding: 20px;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
    }
    .title {
        font-size: 24px;
        font-weight: bold;
        color: #333;
        margin-bottom: 20px;
    }
    .content {
        font-size: 16px;
        color: #666;
        line-height: 1.6;
    }
    </style>
</head>
<body>
    <div class="title">小红书内容生成中</div>
    <div class="content">正在为您准备精彩的内容...</div>
</body>
</html>"""

# ===================================
# 缓存管理函数
# ===================================

def _get_cache_path(filename: str) -> str:
    """获取缓存文件的完整路径"""
    return os.path.join(CACHE_DIR, filename)

def _load_cached_design_spec() -> Optional[Dict[str, Any]]:
    """加载缓存的设计规范"""
    cache_path = _get_cache_path(DESIGN_SPEC_FILENAME)
    result = load_json(cache_path)
    if result is None or isinstance(result, list):
        return None
    return result

def _save_design_spec_cache(design_spec: Dict[str, Any]) -> bool:
    """保存设计规范到缓存"""
    cache_path = _get_cache_path(DESIGN_SPEC_FILENAME)
    return save_json(design_spec, cache_path)

def _load_cached_html() -> Optional[str]:
    """加载缓存的HTML内容"""
    cache_path = _get_cache_path(FINAL_HTML_FILENAME)
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        logger.error(f"加载HTML缓存失败: {e}")
        return None

def _save_html_cache(html_content: str) -> bool:
    """保存HTML内容到缓存"""
    cache_path = _get_cache_path(FINAL_HTML_FILENAME)
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML缓存已保存: {cache_path}")
        return True
    except Exception as e:
        logger.error(f"保存HTML缓存失败: {e}")
        return False

# ===================================
# 主入口函数
# ===================================

def execute_narrative_pipeline(blueprint: Dict[str, Any], theme: str, output_dir: str = "output") -> Dict[str, Any]:
    """
    执行叙事管道，生成小红书多图内容
    
    Args:
        blueprint (Dict[str, Any]): 策略蓝图
        theme (str): 内容主题
        output_dir (str): 输出目录
        
    Returns:
        Dict[str, Any]: 执行结果
    """
    logger.info("=" * 80)
    logger.info("🎬 启动小红书多图内容生成管道")
    logger.info(f"📝 主题: {theme}")
    logger.info("=" * 80)
    
    try:
        # 创建时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建主题专用输出目录
        theme_output_dir = os.path.join(output_dir, f"{theme}_{timestamp}")
        os.makedirs(theme_output_dir, exist_ok=True)
        logger.info(f"创建主题文件夹：{theme_output_dir}")
        
        # 1. 叙事设计阶段：生成设计规范
        logger.info("第1阶段：叙事设计 - 生成小红书多图设计规范")
        try:
            design_spec = _generate_design_specification(blueprint, theme)
        except Exception as e:
            logger.warning(f"AI生成设计规范失败，使用备用方案: {e}")
            design_spec = _get_fallback_design_spec(theme)
            logger.info("已启用备用设计规范")
        
        # 保存设计规范到主题文件夹
        design_spec_path = os.path.join(theme_output_dir, "design_spec.json")
        with open(design_spec_path, 'w', encoding='utf-8') as f:
            json.dump(design_spec, f, ensure_ascii=False, indent=2)
        logger.info(f"设计规范已保存：{design_spec_path}")
        
        # 2. 视觉编码阶段：生成多个HTML页面
        logger.info("第2阶段：视觉编码 - 生成小红书多图HTML页面")
        try:
            html_pages = _generate_html_pages(design_spec)
        except Exception as e:
            logger.warning(f"生成HTML页面失败，使用备用方案: {e}")
            html_pages = _generate_fallback_html_pages(design_spec, theme)
        
        # 保存所有HTML页面到主题文件夹
        html_files = []
        for page_name, html_content in html_pages.items():
            html_path = os.path.join(theme_output_dir, f"{page_name}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            html_files.append(html_path)
            logger.info(f"HTML页面已保存：{html_path}")
        
        # 3. 保存小红书内容文件
        logger.info("第3阶段：保存小红书发布内容")
        
        # 保存标题选项
        titles = design_spec.get("xiaohongshu_titles", [])
        titles_path = os.path.join(theme_output_dir, "xiaohongshu_titles.txt")
        with open(titles_path, 'w', encoding='utf-8') as f:
            for i, title in enumerate(titles, 1):
                f.write(f"{i}. {title}\n")
        logger.info(f"标题选项已保存：{titles_path}")
        
        # 保存正文内容
        content = design_spec.get("xiaohongshu_content", "")
        content_path = os.path.join(theme_output_dir, "xiaohongshu_content.txt")
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"正文内容已保存：{content_path}")
        
        # 4. 生成截图配置文件
        logger.info("第4阶段：生成截图配置文件")
        
        screenshot_config = {
            "config": SCREENSHOT_CONFIG,
            "html_files": html_files,
            "output_directory": theme_output_dir,
            "image_names": [f"image_{i+1}.png" for i in range(len(html_files))]
        }
        
        screenshot_config_path = os.path.join(theme_output_dir, "screenshot_config.json")
        with open(screenshot_config_path, 'w', encoding='utf-8') as f:
            json.dump(screenshot_config, f, ensure_ascii=False, indent=2)
        logger.info(f"截图配置已保存：{screenshot_config_path}")
        
        # 5. 保存策略蓝图到主题文件夹（便于追溯）
        blueprint_path = os.path.join(theme_output_dir, "creative_blueprint.json")
        with open(blueprint_path, 'w', encoding='utf-8') as f:
            json.dump(blueprint, f, ensure_ascii=False, indent=2)
        logger.info(f"策略蓝图已保存：{blueprint_path}")
        
        # 6. 生成README文件
        readme_content = f"""# 小红书多图内容 - {theme}

## 生成时间
{datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}

## 内容概述
- 主题：{theme}
- 图片数量：{len(html_files)}张
- 目标受众：{design_spec.get('content_overview', {}).get('target_audience', '年轻父母群体')}

## 文件说明
- `xiaohongshu_titles.txt` - 标题选项（共{len(titles)}个）
- `xiaohongshu_content.txt` - 小红书正文内容
- `design_spec.json` - 设计规范文档
- `screenshot_config.json` - 截图配置文件
- `creative_blueprint.json` - 策略蓝图
- `page_*.html` - HTML页面文件（{len(html_files)}个）

## 使用说明
1. 查看 `xiaohongshu_titles.txt` 选择合适的标题
2. 复制 `xiaohongshu_content.txt` 的内容作为小红书正文
3. 使用HTML页面生成对应的图片
4. 在小红书发布时，选择生成的多张图片

## 截图说明
- 每张图片尺寸：448x597px
- 适合小红书平台发布
- 所有样式已内联，无需外部资源

## 技术信息
- 生成工具：小红书内容自动化管线
- 设计风格：温暖实用的育儿分享
- 配色方案：{design_spec.get('design_principles', {}).get('color_palette', [])}
"""
        
        readme_path = os.path.join(theme_output_dir, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        logger.info(f"README文件已保存：{readme_path}")
        
        # 生成会话摘要
        session_summary = {
            "theme": theme,
            "timestamp": timestamp,
            "output_directory": theme_output_dir,
            "total_images": len(html_files),
            "files_generated": [
                "design_spec.json",
                "screenshot_config.json",
                "xiaohongshu_titles.txt",
                "xiaohongshu_content.txt",
                "creative_blueprint.json",
                "README.md"
            ] + [os.path.basename(f) for f in html_files],
            "pipeline_stages": [
                "叙事设计 - 小红书多图设计规范生成",
                "视觉编码 - 多个HTML页面生成",
                "内容保存 - 小红书发布内容保存",
                "截图配置 - 截图参数配置",
                "文档生成 - README和说明文档"
            ],
            "next_steps": [
                "使用Playwright或其他工具对HTML页面进行截图",
                "将生成的图片导入小红书",
                "复制正文内容进行发布"
            ]
        }
        
        # 保存会话摘要到主题文件夹
        summary_path = os.path.join(theme_output_dir, "session_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(session_summary, f, ensure_ascii=False, indent=2)
        logger.info(f"会话摘要已保存：{summary_path}")
        
        logger.info("=" * 80)
        logger.info("🎉 小红书多图内容生成管道执行完成")
        logger.info(f"📁 输出目录: {theme_output_dir}")
        logger.info(f"🖼️ 生成图片数量: {len(html_files)}")
        logger.info("=" * 80)
        
        # 返回执行结果
        return {
            "status": "success",
            "theme": theme,
            "output_directory": theme_output_dir,
            "html_files": html_files,
            "design_spec_path": design_spec_path,
            "screenshot_config_path": screenshot_config_path,
            "session_summary": session_summary,
            "total_images": len(html_files)
        }
        
    except Exception as e:
        logger.error(f"小红书多图内容生成管道执行失败：{str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "theme": theme
        }

def _generate_fallback_html_pages(design_spec: Dict[str, Any], theme: str) -> Dict[str, str]:
    """
    生成备用HTML页面，当AI生成失败时使用
    """
    from config import HTML_BASE_STYLE
    
    html_pages = {}
    
    # 生成4个基础页面
    for i in range(1, 5):
        page_name = f"page_{i}_备用页面"
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{theme} - 第{i}页</title>
    {HTML_BASE_STYLE}
    <style>
    .page-{i} {{
        background: linear-gradient(135deg, 
            {['#667eea, #764ba2', '#f093fb, #f5576c', '#4facfe, #00f2fe', '#43e97b, #38f9d7'][i-1]});
        color: white;
    }}
    .content-box {{
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    .page-number {{
        position: absolute;
        top: 10px;
        right: 10px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
    }}
    </style>
</head>
<body class="page-{i}">
    <div class="container">
        <div class="page-number">{i}</div>
        <div class="title">{theme}</div>
        <div class="content">
            <div class="content-box">
                <p>这是第{i}页内容</p>
                <p>宝爸Conn为您准备的实用育儿经验分享</p>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        html_pages[page_name] = html_content
    
    return html_pages

# ===================================
# 模块初始化
# ===================================

def initialize_execution_module() -> bool:
    """
    初始化执行模块
    
    检查必要的配置和依赖项，确保模块能够正常运行。
    
    Returns:
        bool: 初始化是否成功
    """
    logger.info("初始化执行模块")
    
    # 检查必要的目录
    for directory in [CACHE_DIR, OUTPUT_DIR]:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"创建目录: {directory}")
            except Exception as e:
                logger.error(f"创建目录失败: {directory} - {e}")
                return False
    
    logger.info("执行模块初始化完成")
    return True

# ===================================
# 模块级别的自动初始化
# ===================================

if __name__ == "__main__":
    # 当直接运行此模块时，执行初始化检查
    if initialize_execution_module():
        print("✓ 执行模块初始化成功")
    else:
        print("✗ 执行模块初始化失败")

def _get_fallback_design_spec(theme: str) -> Dict[str, Any]:
    """
    获取fallback设计规范，用于AI生成失败时的备用方案（已整合优化版prompt）
    """
    return {
        "content_overview": {
            "theme": theme,
            "total_images": 4,
            "target_audience": "年轻父母群体",
            "content_style": "宝爸Conn的温暖实用分享",
            "persona_voice": "有温度的专业主义者，像学霸朋友一样"
        },
        "xiaohongshu_titles": [
            f"【宝爸亲测】{theme}保姆级攻略！@准爸爸 抄作业",
            f"家人们谁懂啊！{theme}超全攻略来了",
            f"@新手爸妈，{theme}的坑别再踩了！",
            f"听劝！{theme}这么做能省一大笔钱💰",
            f"吐血整理！{theme}必看清单📋码住收藏"
        ],
        "xiaohongshu_content": f"""家人们谁懂啊！老婆怀孕后每天都在研究{theme}，感觉自己像个无头苍蝇😭 明明都是第一次当爸妈，怎么别人都这么淡定？

别慌！我熬夜把过来人的经验全整理了，{theme}的所有关键点和避坑技巧都在图片里了📸 从怎么开始到注意事项，保姆级攻略一次性给你！

准爸爸们，你们现在进行到哪一步了？评论区一起交流经验呀！咱们抱团取暖，互相支持💪

#育儿经验 #宝爸日常 #实用技巧 #新手爸妈 #准爸爸必看""",
        "image_contents": [
            {
                "image_number": 1,
                "type": "封面图",
                "title": f"宝爸Conn分享：{theme}",
                "main_content": f"【第一次当爸妈必看】{theme}完整攻略，让你少走弯路！",
                "visual_elements": ["巨大标题44px", "核心要点概览", "温暖色调"],
                "color_scheme": "温暖橙色系",
                "layout": "图文插画型内容封面",
                "height_constraint": "严格控制在560px以内"
            },
            {
                "image_number": 2,
                "type": "内容图", 
                "title": "关键要点详解",
                "main_content": "具体的方法和步骤说明，包含真实的经验分享和注意事项",
                "visual_elements": ["步骤编号", "重点文字", "个人经历"],
                "color_scheme": "清新绿色系",
                "layout": "上下结构布局",
                "height_constraint": "严格控制在560px以内"
            },
            {
                "image_number": 3,
                "type": "内容图",
                "title": "避坑指南",
                "main_content": "常见问题和解决方案，用实际案例说明",
                "visual_elements": ["对比数据", "重点提醒", "感官体验"],
                "color_scheme": "温馨蓝色系",
                "layout": "左右对比布局",
                "height_constraint": "严格控制在560px以内"
            },
            {
                "image_number": 4,
                "type": "总结图",
                "title": "核心要点总结",
                "main_content": "总结所有要点，互动引导和下期预告",
                "visual_elements": ["要点列表", "互动引导", "结尾互动"],
                "color_scheme": "渐变紫色系",
                "layout": "列表式布局",
                "height_constraint": "严格控制在560px以内"
            }
        ],
        "design_principles": {
            "size_constraint": "420x560px（3:4黄金比例）",
            "font_hierarchy": "主标题44px，章节标题22px，正文13px（高密度）",
            "color_palette": ["#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1"],
            "spacing": "内边距25px 15px，元素间距适中",
            "visual_consistency": "统一的圆角风格，一致的阴影效果",
            "brand_signature": "@宝爸Conn右下角水印，不占文档流"
        },
        "engagement_elements": {
            "call_to_action": "准爸妈们，你们现在进行到哪一步了？评论区一起交流经验呀！",
            "hashtags": ["#育儿经验", "#宝爸日常", "#实用技巧", "#新手爸妈"],
            "emotional_triggers": ["真实经历共鸣", "具体效果证明", "温暖陪伴感"]
        }
    }
