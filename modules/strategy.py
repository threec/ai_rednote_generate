"""
小红书内容自动化管线 - 战略与规划模块
Xiaohongshu Content Automation Pipeline - Strategy and Planning Module

这个模块是内容创作流水线的起点，负责将原始主题转化为结构化的《内容创作蓝图》。
它通过AI分析，将简单的主题深度挖掘为完整的内容策略，包括：
- 目标受众分析
- 痛点挖掘
- 价值主张定位
- 内容架构设计
- 视觉呈现规划
- 互动设计策略

核心功能：
1. 智能缓存机制，避免重复AI调用
2. 基于"宝爸Conn"人格的深度策略分析
3. 输出结构化的创作蓝图，为后续执行阶段提供指导
"""

import os
import re
import json
import requests
from typing import Dict, Any, Optional
from pathlib import Path

# ===================================
# 配置和工具导入
# ===================================

# 导入Google官方SDK
from google import genai

# 导入配置信息
try:
    from config import (
        GEMINI_API_KEY, MODEL_FOR_STRATEGY, FALLBACK_MODEL,
        STRATEGY_SYSTEM_PROMPT, BLUEPRINT_FILENAME, 
        CACHE_DIR, FORCE_STRATEGY, DEFAULT_TEMPERATURE,
        DEFAULT_MAX_TOKENS, MAX_RETRIES
    )
except ImportError:
    # 如果直接导入失败，尝试从父目录导入
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config import (
        GEMINI_API_KEY, MODEL_FOR_STRATEGY, FALLBACK_MODEL,
        STRATEGY_SYSTEM_PROMPT, BLUEPRINT_FILENAME, 
        CACHE_DIR, FORCE_STRATEGY, DEFAULT_TEMPERATURE,
        DEFAULT_MAX_TOKENS, MAX_RETRIES
    )

# 导入工具函数
from .utils import load_json, save_json, get_logger, clean_filename

# 导入数据模型
from .models import StrategyBlueprint

# ===================================
# 模块配置
# ===================================

# 获取模块专用的日志记录器
logger = get_logger(__name__)

# ===================================
# 辅助函数
# ===================================

def _generate_cache_path(topic: str) -> str:
    """
    根据主题生成唯一的缓存文件路径
    
    Args:
        topic (str): 用户输入的主题
        
    Returns:
        str: 缓存文件的完整路径
    """
    # 清理主题字符串，生成安全的目录名
    safe_topic = clean_filename(topic)
    
    # 如果主题过长，截断并添加哈希值确保唯一性
    if len(safe_topic) > 50:
        import hashlib
        topic_hash = hashlib.md5(topic.encode('utf-8')).hexdigest()[:8]
        safe_topic = safe_topic[:42] + f"_{topic_hash}"
    
    # 创建主题专用的缓存目录
    topic_cache_dir = os.path.join(CACHE_DIR, f"strategy_{safe_topic}")
    os.makedirs(topic_cache_dir, exist_ok=True)
    
    # 返回蓝图文件的完整路径
    return os.path.join(topic_cache_dir, BLUEPRINT_FILENAME)

def _build_strategy_prompt(topic: str) -> str:
    """
    构建发送给AI的策略分析提示词
    
    Args:
        topic (str): 用户输入的主题
        
    Returns:
        str: 完整的用户提示词
    """
    return f"""
请作为"宝爸Conn"，担任这个小红书内容项目的**总规划师**角色。

**用户输入的主题：** {topic}

**你的任务：**
请为这个主题制定一个完整的内容策略，输出一个包含以下结构的JSON对象：

```json
{{
    "research_report": {{
        "target_audience": {{
            "primary_audience": "主要目标受众描述",
            "demographics": "人群特征分析",
            "pain_points": ["痛点1", "痛点2", "痛点3"],
            "emotional_triggers": ["情感触发点1", "情感触发点2"],
            "content_preferences": "内容偏好分析"
        }},
        "market_analysis": {{
            "competition_landscape": "竞争环境分析",
            "content_gaps": "内容空白点",
            "opportunity_assessment": "机会评估",
            "trending_elements": ["热门元素1", "热门元素2"]
        }},
        "insights": {{
            "key_findings": ["关键发现1", "关键发现2"],
            "strategic_recommendations": ["策略建议1", "策略建议2"],
            "content_angles": ["内容角度1", "内容角度2", "内容角度3"]
        }}
    }},
    "creative_blueprint": {{
        "content_strategy": {{
            "core_message": "核心信息",
            "value_proposition": "价值主张",
            "unique_angle": "独特角度",
            "call_to_action": "行动号召"
        }},
        "content_structure": {{
            "opening_hook": "开头吸引点设计",
            "main_body": {{
                "section_1": "第一部分内容要点",
                "section_2": "第二部分内容要点",
                "section_3": "第三部分内容要点"
            }},
            "closing": "结尾设计"
        }},
        "visual_plan": {{
            "image_count": 4,
            "images": [
                {{
                    "position": 1,
                    "purpose": "图片1的作用",
                    "description": "图片1的详细描述",
                    "style": "图片1的风格要求"
                }},
                {{
                    "position": 2,
                    "purpose": "图片2的作用",
                    "description": "图片2的详细描述",
                    "style": "图片2的风格要求"
                }},
                {{
                    "position": 3,
                    "purpose": "图片3的作用",
                    "description": "图片3的详细描述",
                    "style": "图片3的风格要求"
                }},
                {{
                    "position": 4,
                    "purpose": "图片4的作用",
                    "description": "图片4的详细描述",
                    "style": "图片4的风格要求"
                }}
            ]
        }},
        "engagement_design": {{
            "interactive_elements": ["互动元素1", "互动元素2"],
            "discussion_starters": ["讨论话题1", "讨论话题2"],
            "shareability_factors": ["分享因素1", "分享因素2"]
        }},
        "content_tone": {{
            "personality": "内容人格特征",
            "voice_style": "语调风格",
            "emotional_tone": "情感基调",
            "language_level": "语言难度层次"
        }}
    }}
}}
```

**重要要求：**
1. 必须严格按照上述JSON结构输出
2. 每个字段都要有具体、实用的内容，不要使用占位符
3. 体现"宝爸Conn"的温暖、专业和实用的特质
4. 确保策略具有强烈的可操作性和针对性
5. 图片规划要与内容紧密配合，每张图片都有明确的功能定位

请现在开始你的策略规划工作。
"""

def _call_gemini_api(prompt: str, retries: int = 0) -> Dict[str, Any]:
    """
    使用Google官方SDK调用Gemini API获取策略分析结果，使用结构化输出
    
    Args:
        prompt (str): 发送给AI的提示词
        retries (int): 当前重试次数
        
    Returns:
        Dict[str, Any]: AI返回的策略分析结果
        
    Raises:
        Exception: 当API调用失败或响应格式不正确时抛出异常
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            logger.info(f"正在调用Gemini API (尝试 {attempt + 1}/{MAX_RETRIES + 1})...")
            
            # 创建Gemini客户端
            client = genai.Client()
            
            # 合并system prompt和user prompt
            combined_prompt = f"{STRATEGY_SYSTEM_PROMPT}\n\n{prompt}"
            
            # 尝试使用主要模型
            model = MODEL_FOR_STRATEGY
            try:
                # 使用官方SDK调用API，启用结构化输出
                response = client.models.generate_content(
                    model=model,
                    contents=combined_prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": StrategyBlueprint,
                    },
                )
                
                # 使用解析好的对象
                parsed_result = response.parsed
                
                # 检查解析结果类型
                if not isinstance(parsed_result, StrategyBlueprint):
                    raise ValueError(f"API响应类型不正确: {type(parsed_result)}")
                
                # 转换为字典格式以保持兼容性
                result_dict = parsed_result.model_dump()
                
                logger.info(f"✓ Gemini API调用成功，使用模型: {model}")
                return result_dict
                
            except Exception as model_error:
                # 如果主要模型失败，尝试备用模型
                if model != FALLBACK_MODEL:
                    logger.warning(f"主要模型 {model} 失败，尝试备用模型 {FALLBACK_MODEL}: {model_error}")
                    model = FALLBACK_MODEL
                    
                    response = client.models.generate_content(
                        model=model,
                        contents=combined_prompt,
                        config={
                            "response_mime_type": "application/json",
                            "response_schema": StrategyBlueprint,
                        },
                    )
                    
                    parsed_result = response.parsed
                    
                    # 检查解析结果类型
                    if not isinstance(parsed_result, StrategyBlueprint):
                        raise ValueError(f"API响应类型不正确: {type(parsed_result)}")
                    
                    result_dict = parsed_result.model_dump()
                    
                    logger.info(f"✓ Gemini API调用成功，使用模型: {model}")
                    return result_dict
                else:
                    raise model_error
                    
        except Exception as e:
            logger.error(f"API调用过程中发生错误: {e}")
            if attempt < MAX_RETRIES:
                logger.info(f"正在重试... ({attempt + 1}/{MAX_RETRIES})")
                continue
            else:
                raise Exception(f"API调用失败，已达到最大重试次数: {e}")
    
    # 这里不应该被执行到，但作为安全措施
    raise Exception("未知错误：超出了预期的重试逻辑")

# 为保持向后兼容性，保留原有函数名
def _call_openai_api(prompt: str, retries: int = 0) -> Dict[str, Any]:
    """
    兼容性函数，实际调用Gemini API
    """
    return _call_gemini_api(prompt, retries)

# ===================================
# 核心功能函数
# ===================================

def run_strategy_and_planning(topic: str) -> Dict[str, Any]:
    """
    执行战略规划，将原始主题转化为结构化的内容创作蓝图
    
    这是strategy模块的唯一入口函数，负责整个策略分析流程：
    1. 检查缓存，避免重复AI调用
    2. 如果需要，调用AI进行深度策略分析
    3. 保存结果到缓存，供后续使用
    4. 返回完整的创作蓝图
    
    Args:
        topic (str): 用户输入的原始主题
        
    Returns:
        Dict[str, Any]: 包含research_report和creative_blueprint的完整策略分析结果
        
    Raises:
        ValueError: 当输入主题为空或无效时
        Exception: 当AI调用失败或文件操作失败时
        
    Example:
        >>> blueprint = run_strategy_and_planning("如何培养孩子的阅读兴趣")
        >>> print(blueprint["creative_blueprint"]["content_strategy"]["core_message"])
    """
    
    # ===================================
    # 1. 输入验证和日志记录
    # ===================================
    
    logger.info("=" * 60)
    logger.info("🚀 启动战略规划阶段")
    logger.info(f"📝 输入主题: {topic}")
    logger.info("=" * 60)
    
    # 验证输入
    if not topic or not isinstance(topic, str):
        error_msg = "输入主题不能为空且必须是字符串"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    topic = topic.strip()
    if not topic:
        error_msg = "输入主题不能为空字符串"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"✓ 输入验证通过: {topic}")
    
    # ===================================
    # 2. 缓存逻辑处理
    # ===================================
    
    # 生成缓存文件路径
    cache_file_path = _generate_cache_path(topic)
    logger.info(f"📁 缓存文件路径: {cache_file_path}")
    
    # 检查缓存
    if os.path.exists(cache_file_path) and not FORCE_STRATEGY:
        logger.info("📋 发现现有缓存文件")
        
        # 尝试加载缓存
        cached_data = load_json(cache_file_path)
        if cached_data and isinstance(cached_data, dict):
            logger.info("✓ 缓存加载成功，跳过AI策略规划")
            logger.info("🎯 使用缓存的策略蓝图")
            logger.info("=" * 60)
            return cached_data
        else:
            logger.warning("⚠️ 缓存文件损坏，将重新生成")
    
    if FORCE_STRATEGY:
        logger.info("🔄 强制策略模式已启用，将重新生成策略")
    
    # ===================================
    # 3. AI策略分析
    # ===================================
    
    try:
        logger.info("🤖 准备调用AI进行策略分析...")
        
        # 构建提示词
        user_prompt = _build_strategy_prompt(topic)
        logger.info("📝 策略分析提示词已构建")
        
        # 调用AI API
        logger.info("🔍 开始深度策略分析...")
        strategy_result = _call_openai_api(user_prompt)
        
        # 添加元数据
        from datetime import datetime
        strategy_result["meta"] = {
            "topic": topic,
            "model": MODEL_FOR_STRATEGY,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        logger.info("✓ 策略分析完成")
        logger.info(f"🎯 生成了 {len(strategy_result.get('creative_blueprint', {}).get('visual_plan', {}).get('images', []))} 张图片的规划")
        
    except Exception as e:
        error_msg = f"AI策略分析失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    # ===================================
    # 4. 结果保存和返回
    # ===================================
    
    try:
        # 保存到缓存
        logger.info("💾 正在保存策略蓝图到缓存...")
        save_success = save_json(strategy_result, cache_file_path)
        
        if save_success:
            logger.info(f"✓ 策略蓝图已保存: {cache_file_path}")
        else:
            logger.warning("⚠️ 策略蓝图保存失败，但不影响返回结果")
        
        # 记录完成日志
        logger.info("🎉 战略规划阶段完成!")
        logger.info(f"📊 策略报告包含 {len(strategy_result.get('research_report', {}))} 个研究维度")
        logger.info(f"🎨 创作蓝图包含 {len(strategy_result.get('creative_blueprint', {}))} 个设计维度")
        logger.info("=" * 60)
        
        return strategy_result
        
    except Exception as e:
        error_msg = f"策略结果保存失败: {str(e)}"
        logger.error(error_msg)
        # 即使保存失败，也返回结果，不影响流程
        logger.warning("⚠️ 保存失败但仍返回策略结果")
        return strategy_result

# ===================================
# 辅助查询函数
# ===================================

def get_cached_strategy(topic: str) -> Optional[Dict[str, Any]]:
    """
    获取指定主题的缓存策略（如果存在）
    
    Args:
        topic (str): 主题名称
        
    Returns:
        Optional[Dict[str, Any]]: 缓存的策略数据，如果不存在则返回None
    """
    cache_file_path = _generate_cache_path(topic)
    
    if os.path.exists(cache_file_path):
        result = load_json(cache_file_path)
        if result is None or isinstance(result, list):
            return None
        return result
    
    return None

def list_cached_strategies() -> list:
    """
    列出所有缓存的策略主题
    
    Returns:
        list: 包含所有缓存策略主题的列表
    """
    cached_topics = []
    
    if not os.path.exists(CACHE_DIR):
        return cached_topics
    
    for item in os.listdir(CACHE_DIR):
        item_path = os.path.join(CACHE_DIR, item)
        if os.path.isdir(item_path) and item.startswith("strategy_"):
            blueprint_file = os.path.join(item_path, BLUEPRINT_FILENAME)
            if os.path.exists(blueprint_file):
                # 从目录名提取主题（去掉前缀）
                topic = item[9:]  # 移除 "strategy_" 前缀
                cached_topics.append(topic)
    
    return cached_topics

def clear_strategy_cache(topic: Optional[str] = None) -> bool:
    """
    清除策略缓存
    
    Args:
        topic (str, optional): 特定主题的缓存。如果为None，清除所有缓存
        
    Returns:
        bool: 清除成功返回True，失败返回False
    """
    try:
        if topic is not None:
            # 清除特定主题的缓存
            cache_file_path = _generate_cache_path(topic)
            cache_dir = os.path.dirname(cache_file_path)
            
            if os.path.exists(cache_dir):
                import shutil
                shutil.rmtree(cache_dir)
                logger.info(f"✓ 已清除主题 '{topic}' 的策略缓存")
            else:
                logger.info(f"主题 '{topic}' 没有缓存文件")
        else:
            # 清除所有策略缓存
            strategy_dirs = [d for d in os.listdir(CACHE_DIR) 
                           if os.path.isdir(os.path.join(CACHE_DIR, d)) 
                           and d.startswith("strategy_")]
            
            for strategy_dir in strategy_dirs:
                import shutil
                shutil.rmtree(os.path.join(CACHE_DIR, strategy_dir))
            
            logger.info(f"✓ 已清除所有策略缓存 ({len(strategy_dirs)} 个)")
        
        return True
        
    except Exception as e:
        logger.error(f"清除策略缓存失败: {e}")
        return False

# ===================================
# 模块测试函数
# ===================================

def test_strategy_module():
    """
    测试策略模块的核心功能
    """
    logger.info("开始测试策略模块...")
    
    test_topic = "如何培养孩子的专注力"
    
    try:
        # 测试策略规划
        result = run_strategy_and_planning(test_topic)
        
        # 验证结果结构
        assert "research_report" in result
        assert "creative_blueprint" in result
        
        logger.info("✓ 策略模块测试通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 策略模块测试失败: {e}")
        return False

# ===================================
# 模块入口点
# ===================================

if __name__ == "__main__":
    # 当模块被直接运行时，执行测试
    print("=" * 60)
    print("🧪 策略模块独立测试")
    print("=" * 60)
    
    # 设置日志
    from .utils import setup_logging
    setup_logging(verbose=True)
    
    # 执行测试
    test_success = test_strategy_module()
    
    if test_success:
        print("✓ 所有测试通过")
    else:
        print("✗ 测试失败")
        exit(1)
    
    print("=" * 60)