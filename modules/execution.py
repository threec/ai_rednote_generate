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
    SCREENSHOT_CONFIG, COVER_PAGE_TEMPLATE, CONTENT_PAGE_TEMPLATE, COMPARISON_PAGE_TEMPLATE, FINAL_PAGE_TEMPLATE
)
from modules.utils import save_json, load_json, get_logger

# 导入数据模型
from modules.models import DesignSpecification

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
    根据策略蓝图生成详细的设计规范
    确保与小红书生态完美适配
    """
    logger.info("开始生成设计规范...")
    
    # 从策略蓝图中提取图片数量 - 完全依据策略规划
    visual_plan = blueprint.get("visual_plan", {})
    planned_image_count = visual_plan.get("image_count")  # 不设默认值，强制AI明确决定
    planned_images = visual_plan.get("images", [])
    
    # 如果AI没有明确指定图片数量，则要求重新生成策略
    if not planned_image_count:
        logger.error("策略蓝图中缺少明确的图片数量规划，需要重新生成策略")
        raise ValueError("策略蓝图必须明确指定图片数量")
    
    # 确保图片数量为整数（如果AI返回了字符串描述）
    if isinstance(planned_image_count, str):
        # 尝试从字符串中提取数字
        import re
        numbers = re.findall(r'\d+', planned_image_count)
        if numbers:
            planned_image_count = int(numbers[0])
        else:
            logger.error(f"无法从图片数量描述中提取数字: {planned_image_count}")
            raise ValueError("图片数量必须是明确的数字")
    
    # 确保在系统限制范围内（4-18张）
    planned_image_count = max(4, min(18, int(planned_image_count)))
    
    logger.info(f"策略蓝图明确规划图片数量: {planned_image_count}张")
    
    design_prompt = f"""
根据以下策略蓝图，生成详细的设计规范，严格按照策略蓝图中规划的 {planned_image_count} 张图片执行。

**策略蓝图内容**：
{json.dumps(blueprint, ensure_ascii=False, indent=2)}

**主题**：{theme}

**设计要求**：
1. 必须生成 {planned_image_count} 张图片的设计规范
2. 严格按照策略蓝图中的visual_plan执行
3. 每张图片的功能定位和内容描述要与策略蓝图保持一致
4. 图片数量完全由策略蓝图决定，不做任何修改

请生成如下格式的设计规范JSON：

{{
    "content_overview": {{
        "theme": "{theme}",
        "total_images": {planned_image_count},
        "content_strategy_summary": "根据策略蓝图的内容策略总结",
        "visual_narrative_flow": "视觉叙事流程描述"
    }},
    "design_principles": {{
        "visual_style": "现代简约风格，温暖色调",
        "color_palette": "主色调：温暖橙色 #FF6B35，辅助色：柔和蓝色 #4A90E2，点缀色：清新绿色 #7ED321",
        "typography": "主标题：44px 粗体，副标题：24px 中等，正文：18px 常规",
        "layout_principles": "清晰层次，重点突出，信息密度适中",
        "brand_elements": "宝爸Conn品牌标识，温暖人设体现"
    }},
    "page_specifications": [
        // 这里根据策略蓝图的planned_images生成对应数量的页面规范
    ]
}}

**重要要求**：
1. page_specifications数组必须包含 {planned_image_count} 个页面规范
2. 每个页面规范必须包含完整的设计细节
3. 严格遵循策略蓝图中每张图片的purpose和description
4. 确保所有图片形成完整的内容逻辑链条
5. 高度控制在560px以内，宽度375px，符合小红书规范

现在请生成完整的设计规范。
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
        
        # 验证图片数量是否正确
        page_specs = result.get("image_contents", [])
        if len(page_specs) != planned_image_count:
            logger.warning(f"AI生成的页面规范数量({len(page_specs)})与策略规划({planned_image_count})不符")
            # 如果数量不对，使用fallback方案，传入明确的图片数量
            fallback_spec = _get_fallback_design_spec(theme, planned_image_count)
            # 调整fallback方案的图片数量为策略规划的数量
            fallback_spec = _adjust_fallback_spec_for_count(fallback_spec, planned_image_count)
            return fallback_spec
        
        logger.info(f"✅ 设计规范生成成功！包含 {len(page_specs)} 张图片")
        return result
        
    except Exception as e:
        logger.error(f"设计规范生成失败: {e}")
        # 使用fallback方案，传入明确的图片数量
        fallback_spec = _get_fallback_design_spec(theme, planned_image_count)
        # 调整fallback方案的图片数量为策略规划的数量
        fallback_spec = _adjust_fallback_spec_for_count(fallback_spec, planned_image_count)
        return fallback_spec

def _generate_html_pages(design_spec: Dict[str, Any]) -> Dict[str, str]:
    """
    使用专业模板系统生成多个HTML页面，每个页面对应一张小红书图片
    
    Args:
        design_spec (Dict[str, Any]): 设计规范文档
        
    Returns:
        Dict[str, str]: 页面名称到HTML内容的映射
    """
    logger.info("开始生成小红书多图HTML页面（使用专业模板系统）")
    
    html_pages = {}
    
    # 获取图片内容列表
    image_contents = design_spec.get("image_contents", [])
    
    for img_content in image_contents:
        img_num = img_content["image_number"]
        img_type = img_content["type"]
        
        try:
            # 智能选择模板并填充数据
            html_content = _generate_page_with_template(img_content, design_spec)
            
            page_name = f"page_{img_num}_{img_type}"
            html_pages[page_name] = html_content
            
            logger.info(f"✓ HTML页面生成成功: {page_name} (使用专业模板)")
            
        except Exception as e:
            logger.warning(f"模板生成失败: {e}, 使用备用方案")
            
            # 备用：简化版本
            html_content = _generate_fallback_page(img_content)
            
            page_name = f"page_{img_num}_{img_type}"
            html_pages[page_name] = html_content
            
            logger.info(f"✓ HTML页面生成成功: {page_name} (使用备用方案)")
    
    logger.info(f"所有HTML页面生成完成，共{len(html_pages)}个页面")
    return html_pages


def _generate_page_with_template(img_content: Dict[str, Any], design_spec: Dict[str, Any]) -> str:
    """
    使用专业模板系统生成单个页面
    
    Args:
        img_content (Dict[str, Any]): 图片内容信息
        design_spec (Dict[str, Any]): 设计规范
        
    Returns:
        str: 生成的HTML内容
    """
    img_num = img_content["image_number"]
    img_type = img_content["type"]
    title = img_content.get("title", "")
    main_content = img_content.get("main_content", "")
    
    # 根据图片类型和编号智能选择模板
    if img_num == 1 or "封面" in img_type or "cover" in img_type.lower():
        # 封面页：使用封面模板
        return _fill_cover_template(img_content, design_spec)
    elif img_num == len(design_spec.get("image_contents", [])) or "总结" in img_type or "final" in img_type.lower():
        # 结尾页：使用结尾模板
        return _fill_final_template(img_content, design_spec)
    elif "对比" in title or "错误" in main_content or "正确" in main_content:
        # 对比页：使用对比模板
        return _fill_comparison_template(img_content, design_spec)
    else:
        # 内容页：使用内容模板
        return _fill_content_template(img_content, design_spec)


def _fill_cover_template(img_content: Dict[str, Any], design_spec: Dict[str, Any]) -> str:
    """填充封面页模板"""
    title = img_content.get("title", "育儿攻略")
    main_content = img_content.get("main_content", "")
    
    # 提取核心问题
    core_problem = main_content[:80] + "..." if len(main_content) > 80 else main_content
    
    # 生成解决方案预览列表
    solution_preview = ""
    points = ["快速识别关键信号", "科学有效的处理方法", "避免常见错误做法"]
    for point in points:
        solution_preview += f'<li><span class="bullet"></span>{point}</li>\n                    '
    
    return COVER_PAGE_TEMPLATE.format(
        title=title,
        style=HTML_BASE_STYLE,
        core_problem=core_problem,
        solution_preview=solution_preview
    )


def _fill_content_template(img_content: Dict[str, Any], design_spec: Dict[str, Any]) -> str:
    """填充内容页模板"""
    title = img_content.get("title", "实用技巧")
    main_content = img_content.get("main_content", "")
    img_num = img_content.get("image_number", 2)
    
    # 生成内容章节
    content_sections = f"""
            <div class="info-card blue">
                <div style="font-weight: 600; font-size: 16px; margin-bottom: 12px;">
                    💡 核心要点
                </div>
                <p style="font-size: 14px; line-height: 1.5; margin: 0;">
                    {main_content}
                </p>
            </div>
    """
    
    # 提取关键提醒
    key_reminder = "记住这个关键要点，能让你事半功倍！"
    
    return CONTENT_PAGE_TEMPLATE.format(
        title=title,
        style=HTML_BASE_STYLE,
        step_number=img_num,
        content_sections=content_sections,
        key_reminder=key_reminder
    )


def _fill_comparison_template(img_content: Dict[str, Any], design_spec: Dict[str, Any]) -> str:
    """填充对比页模板"""
    title = img_content.get("title", "正确做法对比")
    main_content = img_content.get("main_content", "")
    img_num = img_content.get("image_number", 2)
    
    # 简化的对比内容
    wrong_approach = "常见错误：急于处理，可能加重问题"
    right_approach = "正确做法：冷静观察，科学应对"
    explanation = "科学的方法能确保安全有效，避免二次伤害"
    
    # 生成步骤列表
    detailed_steps = ""
    steps = ["先观察评估情况", "采取适当的应对措施", "持续关注后续变化"]
    for step in steps:
        detailed_steps += f'<li><span class="bullet"></span>{step}</li>\n                    '
    
    return COMPARISON_PAGE_TEMPLATE.format(
        title=title,
        style=HTML_BASE_STYLE,
        step_number=img_num,
        wrong_approach=wrong_approach,
        right_approach=right_approach,
        explanation=explanation,
        detailed_steps=detailed_steps
    )


def _fill_final_template(img_content: Dict[str, Any], design_spec: Dict[str, Any]) -> str:
    """填充结尾页模板"""
    title = img_content.get("title", "总结回顾")
    main_content = img_content.get("main_content", "")
    
    # 生成核心要点列表
    key_points = ""
    points = ["掌握科学的判断方法", "学会正确的处理步骤", "建立长期的预防意识"]
    for point in points:
        key_points += f'<li><span class="bullet"></span>{point}</li>\n                    '
    
    important_reminder = "每个宝宝都有个体差异，实际操作时要因人而异，安全第一！"
    cta_message = "关注@宝爸Conn，获取更多科学育儿攻略和实用技巧分享"
    
    return FINAL_PAGE_TEMPLATE.format(
        title=title,
        style=HTML_BASE_STYLE,
        key_points=key_points,
        important_reminder=important_reminder,
        cta_message=cta_message
    )


def _generate_fallback_page(img_content: Dict[str, Any]) -> str:
    """生成备用页面"""
    title = img_content.get("title", "内容页面")
    main_content = img_content.get("main_content", "")
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {HTML_BASE_STYLE}
</head>
<body>
    <div class="page-container">
        <div class="module">
            <div class="main-title">{title}</div>
            <div class="info-card blue">
                <p style="font-size: 14px; line-height: 1.5; margin: 0;">
                    {main_content}
                </p>
            </div>
        </div>
        <div class="brand-watermark">宝爸Conn</div>
    </div>
</body>
</html>"""

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
            design_spec = _get_fallback_design_spec(theme, len(design_spec.get("image_contents", [])))
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
    
    # 从设计规范中获取图片数量，必须由设计规范明确指定
    total_images = design_spec.get("content_overview", {}).get("total_images")
    
    if not total_images:
        logger.error("设计规范中缺少明确的图片数量")
        raise ValueError("设计规范必须明确指定图片数量")
    
    # 生成对应数量的基础页面
    for i in range(1, total_images + 1):
        page_name = f"page_{i}_备用页面"
        
        # 根据页面位置选择不同的背景颜色
        gradients = [
            '#667eea, #764ba2',  # 封面页 - 蓝紫渐变
            '#f093fb, #f5576c',  # 内容页1 - 粉红渐变
            '#4facfe, #00f2fe',  # 内容页2 - 蓝色渐变
            '#43e97b, #38f9d7',  # 内容页3 - 绿色渐变
            '#fa709a, #fee140',  # 内容页4 - 橙粉渐变
            '#a8edea, #fed6e3',  # 内容页5 - 青粉渐变
            '#ffecd2, #fcb69f',  # 总结页 - 橙色渐变
            '#667eea, #764ba2'   # 额外页面 - 重复使用
        ]
        
        gradient = gradients[(i-1) % len(gradients)]
        
        # 根据页面类型设置不同的内容
        if i == 1:
            page_type = "封面页"
            page_content = f"宝爸Conn为您分享{theme}的专业攻略"
        elif i == total_images:
            page_type = "总结页"
            page_content = "总结要点，开启你的育儿新篇章"
        else:
            page_type = f"内容页{i-1}"
            page_content = f"第{i-1}部分：实用育儿经验分享"
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{theme} - 第{i}页</title>
    {HTML_BASE_STYLE}
    <style>
    .page-{i} {{
        background: linear-gradient(135deg, {gradient});
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
    .page-type {{
        position: absolute;
        top: 10px;
        left: 10px;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 5px 12px;
        font-size: 12px;
        font-weight: 500;
    }}
    </style>
</head>
<body class="page-{i}">
    <div class="container">
        <div class="page-number">{i}</div>
        <div class="page-type">{page_type}</div>
        <div class="title">{theme}</div>
        <div class="content">
            <div class="content-box">
                <p>{page_content}</p>
                <p>系统正在为您生成更详细的内容...</p>
            </div>
        </div>
        <div style="position: absolute; bottom: 15px; right: 20px; font-size: 10px; opacity: 0.7;">
            @宝爸Conn
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

def _get_fallback_design_spec(theme: str, image_count: int = None) -> Dict[str, Any]:
    """
    获取fallback设计规范，用于AI生成失败时的备用方案
    
    Args:
        theme (str): 主题
        image_count (int): 明确的图片数量，必须指定
    """
    if image_count is None:
        logger.error("Fallback设计规范必须指定明确的图片数量")
        raise ValueError("必须明确指定图片数量，不能使用默认值")
    
    # 确保图片数量在合理范围内
    image_count = max(4, min(18, int(image_count)))
    
    # 生成对应数量的图片内容
    image_contents = []
    
    for i in range(1, image_count + 1):
        if i == 1:
            # 封面图
            image_content = {
                "image_number": 1,
                "type": "封面图",
                "title": f"宝爸Conn分享：{theme}",
                "main_content": f"【第一次当爸妈必看】{theme}完整攻略，让你少走弯路！",
                "visual_elements": ["巨大标题44px", "核心要点概览", "温暖色调"],
                "color_scheme": "温暖橙色系",
                "layout": "图文插画型内容封面",
                "height_constraint": "严格控制在560px以内"
            }
        elif i == image_count:
            # 总结图
            image_content = {
                "image_number": i,
                "type": "总结图",
                "title": "核心要点总结",
                "main_content": "总结所有要点，互动引导和下期预告",
                "visual_elements": ["要点列表", "互动引导", "结尾互动"],
                "color_scheme": "渐变紫色系",
                "layout": "列表式布局",
                "height_constraint": "严格控制在560px以内"
            }
        else:
            # 内容图
            content_titles = [
                "核心方法详解",
                "关键要点解析", 
                "实践技巧分享",
                "进阶技巧库",
                "避坑指南"
            ]
            
            color_schemes = [
                "清新绿色系",
                "温馨蓝色系", 
                "活力橙色系",
                "专业紫色系",
                "警示红色系"
            ]
            
            layouts = [
                "上下结构布局",
                "左右对比布局",
                "卡片式布局",
                "流程图布局",
                "网格式布局"
            ]
            
            content_index = (i - 2) % len(content_titles)
            
            image_content = {
                "image_number": i,
                "type": "内容图", 
                "title": content_titles[content_index],
                "main_content": f"具体的{content_titles[content_index]}，包含真实的经验分享和注意事项",
                "visual_elements": ["步骤编号", "重点文字", "个人经历"],
                "color_scheme": color_schemes[content_index],
                "layout": layouts[content_index],
                "height_constraint": "严格控制在560px以内"
            }
        
        image_contents.append(image_content)
    
    return {
        "content_overview": {
            "theme": theme,
            "total_images": image_count,
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
        "image_contents": image_contents,
        "design_principles": {
            "size_constraint": "420x560px（3:4黄金比例）",
            "font_hierarchy": "主标题44px，章节标题22px，正文13px（高密度）",
            "color_palette": ["#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1", "#5758bb", "#ff9ff3"],
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

def _adjust_fallback_spec_for_count(fallback_spec: Dict[str, Any], count: int) -> Dict[str, Any]:
    """
    调整fallback设计规范的图片数量
    
    Args:
        fallback_spec (Dict[str, Any]): 原始的fallback设计规范
        count (int): 目标图片数量
        
    Returns:
        Dict[str, Any]: 调整后的设计规范
    """
    import copy
    
    # 深拷贝原始规范，避免修改原对象
    adjusted_spec = copy.deepcopy(fallback_spec)
    
    # 获取原始图片内容
    original_images = adjusted_spec.get("image_contents", [])
    
    # 如果目标数量小于等于原始数量，直接截取
    if count <= len(original_images):
        adjusted_spec["image_contents"] = original_images[:count]
        adjusted_spec["content_overview"]["total_images"] = count
        return adjusted_spec
    
    # 如果需要增加图片，智能生成额外内容
    new_images = original_images.copy()
    
    # 额外图片的功能类型
    additional_types = [
        {"type": "实用工具", "title": "实用工具清单", "content": "核心工具和资源汇总"},
        {"type": "进阶技巧", "title": "进阶应用方法", "content": "高级策略和深度应用"},
        {"type": "案例分析", "title": "真实案例分享", "content": "成功案例和效果展示"},
        {"type": "避坑指南", "title": "常见误区对比", "content": "错误示范vs正确方法"},
        {"type": "扩展阅读", "title": "相关知识拓展", "content": "延伸学习和深度理解"},
        {"type": "行动计划", "title": "具体行动步骤", "content": "可执行的完整计划"},
        {"type": "效果评估", "title": "效果检验方法", "content": "如何判断和评估效果"},
        {"type": "资源推荐", "title": "推荐资源汇总", "content": "有用的书籍、工具、网站等"}
    ]
    
    # 为额外的图片生成内容
    for i in range(len(original_images), count):
        # 选择一个额外类型
        extra_type = additional_types[(i - len(original_images)) % len(additional_types)]
        
        # 创建新的图片内容
        new_image = {
            "image_number": i + 1,
            "type": extra_type["type"],
            "title": extra_type["title"],
            "main_content": extra_type["content"],
            "visual_elements": ["清晰标题", "核心要点", "实用信息"],
            "color_scheme": f"配色方案{(i % 5) + 1}",
            "layout": "简洁实用布局",
            "height_constraint": "严格控制在560px以内"
        }
        
        new_images.append(new_image)
    
    # 更新设计规范
    adjusted_spec["image_contents"] = new_images
    adjusted_spec["content_overview"]["total_images"] = count
    
    logger.info(f"✅ 已调整fallback设计规范，图片数量: {len(original_images)} → {count}")
    
    return adjusted_spec
