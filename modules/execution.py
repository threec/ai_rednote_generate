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
import openai
from openai import OpenAI

# 导入项目配置和工具
from config import (
    API_BASE_URL, API_KEY, MODEL_FOR_EXECUTION, 
    MAX_RETRIES, REQUEST_TIMEOUT, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS,
    CACHE_DIR, OUTPUT_DIR, EXECUTION_SYSTEM_PROMPT,
    DESIGN_SPEC_FILENAME, FINAL_HTML_FILENAME
)
from .utils import save_json, load_json, get_logger

# ===================================
# 模块级别配置
# ===================================

logger = get_logger(__name__)

# 初始化OpenAI客户端
client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL,
    timeout=REQUEST_TIMEOUT
)

# ===================================
# 核心AI调用函数
# ===================================

def _call_openai_with_self_correction(
    system_prompt: str,
    user_prompt: str,
    expect_json: bool = True,
    max_retries: int = MAX_RETRIES,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> Dict[str, Any]:
    """
    健壮的OpenAI API调用函数，具备自我修正能力
    
    这个函数是执行模块的核心，它能够：
    1. 调用OpenAI API获取回复
    2. 当expect_json=True时，自动解析JSON格式
    3. 处理JSON解析错误，将错误信息反馈给AI进行自我修正
    4. 根据MAX_RETRIES配置进行重试
    
    Args:
        system_prompt (str): 系统提示词，定义AI的角色和任务
        user_prompt (str): 用户提示词，包含具体的输入内容
        expect_json (bool): 是否期望返回JSON格式的响应
        max_retries (int): 最大重试次数
        temperature (float): 温度参数，控制回答的创造性
        max_tokens (int): 最大token数量
    
    Returns:
        Dict[str, Any]: 解析后的响应数据
    
    Raises:
        Exception: 当达到最大重试次数仍未成功时抛出异常
    """
    logger.info(f"开始调用OpenAI API，期望JSON: {expect_json}")
    
    # 记录原始用户提示词，用于重试时的错误反馈
    original_user_prompt = user_prompt
    current_attempt = 0
    
    while current_attempt < max_retries:
        try:
            logger.info(f"第 {current_attempt + 1} 次尝试调用API")
            
            # 调用OpenAI API
            response = client.chat.completions.create(
                model=MODEL_FOR_EXECUTION,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 提取响应内容
            content = response.choices[0].message.content
            logger.info(f"API调用成功，响应长度: {len(content) if content else 0}")
            
            # 检查响应内容是否为空
            if not content:
                raise Exception("API返回了空的响应内容")
            
            # 如果不需要JSON解析，直接返回文本内容
            if not expect_json:
                return {"content": content, "raw_response": content}
            
            # 尝试解析JSON
            try:
                parsed_json = json.loads(content)
                logger.info("JSON解析成功")
                return parsed_json
                
            except json.JSONDecodeError as json_error:
                logger.warning(f"JSON解析失败: {json_error}")
                
                # 输出调试信息，显示实际的响应内容
                logger.error(f"无法解析的响应内容（前500字符）: {repr(content[:500])}")
                logger.error(f"响应内容长度: {len(content)}")
                
                # 如果这是最后一次尝试，抛出异常
                if current_attempt >= max_retries - 1:
                    raise Exception(f"达到最大重试次数({max_retries})，JSON解析仍然失败: {json_error}")
                
                # 构造错误反馈提示，让AI自我修正
                error_feedback = f"""
前一次的回复无法解析为有效的JSON格式。

错误信息：{json_error}

你的回复内容开头是：{content[:200]}

请检查你的回复格式，确保：
1. 回复必须是纯JSON格式，不要包含任何解释文字
2. 不要使用```json```代码块包装
3. 使用正确的JSON语法
4. 所有字符串都用双引号包围
5. 所有括号和大括号都正确配对
6. 避免使用JSON不支持的字符（如单引号、注释等）

请重新生成符合JSON格式的回复，直接输出JSON内容，不要任何其他文字。

原始请求：
{original_user_prompt}
"""
                
                user_prompt = error_feedback
                current_attempt += 1
                logger.info(f"准备重试，将错误反馈给AI进行自我修正")
                continue
                
        except Exception as api_error:
            logger.error(f"API调用失败: {api_error}")
            
            # 如果这是最后一次尝试，抛出异常
            if current_attempt >= max_retries - 1:
                raise Exception(f"达到最大重试次数({max_retries})，API调用失败: {api_error}")
            
            current_attempt += 1
            logger.info(f"API调用失败，准备第 {current_attempt + 1} 次重试")
            continue
    
    # 这里不应该被执行到，但作为安全措施
    raise Exception("未知错误：超出了预期的重试逻辑")

# ===================================
# 叙事与设计阶段
# ===================================

def _generate_design_spec(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成设计规范文档
    
    这是双重缓存架构的第一阶段：叙事与设计
    根据策略蓝图生成详细的设计规范，包括：
    - 文案结构和内容要点
    - 视觉设计规范
    - 交互元素设计
    - 图片和布局要求
    
    Args:
        blueprint (Dict[str, Any]): 策略蓝图，包含内容策略和方向
    
    Returns:
        Dict[str, Any]: 设计规范文档
    """
    logger.info("开始生成设计规范文档")
    
    # 构建叙事与设计的提示词
    design_prompt = f"""
基于以下策略蓝图，请生成详细的设计规范文档。

策略蓝图：
{json.dumps(blueprint, ensure_ascii=False, indent=2)}

重要：请直接输出JSON格式的响应，不要包含任何解释文字，不要使用```json```代码块包装。

请按照以下JSON格式输出设计规范：

{{
    "content_structure": {{
        "title": "引人入胜的标题",
        "opening": "开场白，3秒内抓住注意力",
        "main_points": [
            "要点1：具体可行的建议",
            "要点2：结合实际案例",
            "要点3：情感共鸣点"
        ],
        "conclusion": "总结和行动指引"
    }},
    "visual_design": {{
        "layout_type": "卡片式/列表式/故事式",
        "color_scheme": "主色调和辅助色",
        "typography": "字体风格和大小层次",
        "spacing": "间距和留白设计"
    }},
    "images_plan": [
        {{
            "sequence": 1,
            "purpose": "吸引注意/解释概念/展示结果",
            "description": "图片内容描述",
            "style": "插画/照片/图表"
        }}
    ],
    "interactive_elements": {{
        "call_to_action": "明确的行动指引",
        "engagement_hooks": ["互动元素1", "互动元素2"],
        "sharing_triggers": "促进分享的设计"
    }},
    "persona_integration": {{
        "tone": "温暖、专业、亲近",
        "voice_examples": ["具体的语言表达方式"],
        "emotional_connection": "情感连接策略"
    }}
}}

只返回JSON内容，不要任何其他文字。
"""
    
    # 调用AI生成设计规范
    design_spec = _call_openai_with_self_correction(
        system_prompt=EXECUTION_SYSTEM_PROMPT,
        user_prompt=design_prompt,
        expect_json=True
    )
    
    logger.info("设计规范文档生成完成")
    return design_spec

def _generate_final_html(design_spec: Dict[str, Any]) -> str:
    """
    生成最终HTML内容
    
    这是双重缓存架构的第二阶段：视觉编码
    根据设计规范生成可截图的HTML页面，包括：
    - 完整的HTML结构
    - 内联CSS样式
    - 响应式设计
    - 小红书风格的视觉呈现
    
    Args:
        design_spec (Dict[str, Any]): 设计规范文档
    
    Returns:
        str: 完整的HTML内容
    """
    logger.info("开始生成最终HTML内容")
    
    # 构建HTML生成的提示词
    html_prompt = f"""
基于以下设计规范，请生成一个完整的HTML页面，用于小红书内容展示。

设计规范：
{json.dumps(design_spec, ensure_ascii=False, indent=2)}

要求：
1. 生成完整的HTML页面，包含DOCTYPE和完整的文档结构
2. 所有CSS样式必须内联在HTML中，不要使用外部样式表
3. 使用现代、简洁的设计风格，符合小红书的视觉风格
4. 支持移动端响应式设计
5. 包含适当的字体、颜色、间距和布局
6. 确保内容清晰易读，视觉层次分明
7. 添加适当的视觉元素（如图标、分割线等）
8. 考虑截图效果，确保页面在800x600尺寸下完整展示

请直接输出HTML代码，不要用JSON格式包装。
"""
    
    # 调用AI生成HTML
    html_response = _call_openai_with_self_correction(
        system_prompt=EXECUTION_SYSTEM_PROMPT,
        user_prompt=html_prompt,
        expect_json=False  # 这里期望纯HTML文本
    )
    
    # 提取HTML内容
    html_content = html_response.get("content", "")
    
    logger.info(f"HTML内容生成完成，长度: {len(html_content)}")
    return html_content

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

def run_narrative_and_visual(
    blueprint: Dict[str, Any],
    force_regenerate: bool = False,
    force_html_only: bool = False
) -> Tuple[Dict[str, Any], str]:
    """
    运行叙事与视觉生成流程
    
    这是execution模块的主入口函数，负责协调整个双重缓存架构的流程：
    1. 检查并加载缓存的设计规范
    2. 如果需要，生成新的设计规范
    3. 检查并加载缓存的HTML内容
    4. 如果需要，生成新的HTML内容
    5. 保存结果到输出目录
    
    Args:
        blueprint (Dict[str, Any]): 策略蓝图，由strategy模块生成
        force_regenerate (bool): 是否强制重新生成所有内容
        force_html_only (bool): 是否只重新生成HTML（保留设计规范）
    
    Returns:
        Tuple[Dict[str, Any], str]: (设计规范文档, HTML内容)
    
    Raises:
        Exception: 当生成过程中发生不可恢复的错误时
    """
    logger.info("开始执行叙事与视觉生成流程")
    logger.info(f"参数: force_regenerate={force_regenerate}, force_html_only={force_html_only}")
    
    design_spec = None
    html_content = None
    
    try:
        # ===================================
        # 阶段1：叙事与设计
        # ===================================
        
        if not force_html_only:
            if not force_regenerate:
                # 尝试加载缓存的设计规范
                logger.info("尝试加载缓存的设计规范")
                design_spec = _load_cached_design_spec()
                
                if design_spec:
                    logger.info("成功加载缓存的设计规范")
                else:
                    logger.info("未找到缓存的设计规范，将重新生成")
            
            # 如果没有缓存或强制重新生成，则生成新的设计规范
            if not design_spec:
                logger.info("开始生成新的设计规范")
                design_spec = _generate_design_spec(blueprint)
                
                # 保存到缓存
                if _save_design_spec_cache(design_spec):
                    logger.info("设计规范已保存到缓存")
                else:
                    logger.warning("设计规范缓存保存失败")
        else:
            # 如果只重新生成HTML，则必须加载现有的设计规范
            logger.info("force_html_only=True，加载现有的设计规范")
            design_spec = _load_cached_design_spec()
            
            if not design_spec:
                raise Exception("无法加载现有的设计规范，请先运行完整的生成流程")
        
        # ===================================
        # 阶段2：视觉编码
        # ===================================
        
        if not force_regenerate and not force_html_only:
            # 尝试加载缓存的HTML内容
            logger.info("尝试加载缓存的HTML内容")
            html_content = _load_cached_html()
            
            if html_content:
                logger.info("成功加载缓存的HTML内容")
            else:
                logger.info("未找到缓存的HTML内容，将重新生成")
        
        # 如果没有缓存或需要重新生成，则生成新的HTML内容
        if not html_content:
            logger.info("开始生成新的HTML内容")
            html_content = _generate_final_html(design_spec)
            
            # 保存到缓存
            if _save_html_cache(html_content):
                logger.info("HTML内容已保存到缓存")
            else:
                logger.warning("HTML内容缓存保存失败")
        
        # ===================================
        # 保存最终结果
        # ===================================
        
        # 保存设计规范到输出目录
        output_design_path = os.path.join(OUTPUT_DIR, DESIGN_SPEC_FILENAME)
        if save_json(design_spec, output_design_path):
            logger.info(f"设计规范已保存到输出目录: {output_design_path}")
        else:
            logger.warning("设计规范输出保存失败")
        
        # 保存HTML内容到输出目录
        output_html_path = os.path.join(OUTPUT_DIR, FINAL_HTML_FILENAME)
        try:
            with open(output_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML内容已保存到输出目录: {output_html_path}")
        except Exception as e:
            logger.error(f"HTML内容输出保存失败: {e}")
        
        logger.info("叙事与视觉生成流程完成")
        return design_spec, html_content
        
    except Exception as e:
        logger.error(f"叙事与视觉生成流程失败: {e}")
        raise

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
    
    # 检查OpenAI API配置
    if not API_KEY:
        logger.error("OpenAI API密钥未配置")
        return False
    
    # 检查必要的目录
    for directory in [CACHE_DIR, OUTPUT_DIR]:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"创建目录: {directory}")
            except Exception as e:
                logger.error(f"创建目录失败: {directory} - {e}")
                return False
    
    # 测试OpenAI API连接
    try:
        logger.info("测试OpenAI API连接")
        response = client.chat.completions.create(
            model=MODEL_FOR_EXECUTION,
            messages=[{"role": "user", "content": "测试连接"}],
            max_tokens=10
        )
        logger.info("OpenAI API连接测试成功")
    except Exception as e:
        logger.error(f"OpenAI API连接测试失败: {e}")
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
