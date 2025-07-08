"""
小红书内容自动化管线 - 数据模型定义
使用Pydantic定义结构化输出的数据模型，用于Google Genai API的结构化响应
"""

import os
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# ===================================
# LangChain相关函数
# ===================================

def get_api_key() -> Optional[str]:
    """获取API密钥"""
    return os.environ.get("GOOGLE_API_KEY")

def get_langchain_model(api_key: Optional[str] = None, model_name: Optional[str] = None):
    """获取LangChain模型实例"""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        if not api_key:
            api_key = get_api_key()
        
        if not api_key:
            raise ValueError("未提供API密钥，请设置GOOGLE_API_KEY环境变量")
        
        if not model_name:
            model_name = "gemini-pro"
        
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7,
            max_tokens=2048,
            timeout=30
        )
    except ImportError:
        raise ImportError("LangChain Google GenAI未安装，请运行: pip install langchain-google-genai")

# ===================================
# 策略规划模块的数据模型
# ===================================

class TargetAudience(BaseModel):
    """目标受众分析"""
    primary_audience: str = Field(description="主要目标受众描述")
    demographics: str = Field(description="人群特征分析")
    pain_points: List[str] = Field(description="痛点列表")
    emotional_triggers: List[str] = Field(description="情感触发点")
    content_preferences: str = Field(description="内容偏好分析")

class MarketAnalysis(BaseModel):
    """市场分析"""
    competition_landscape: str = Field(description="竞争环境分析")
    content_gaps: str = Field(description="内容空白点")
    opportunity_assessment: str = Field(description="机会评估")
    trending_elements: List[str] = Field(description="热门元素")

class Insights(BaseModel):
    """洞察分析"""
    key_findings: List[str] = Field(description="关键发现")
    strategic_recommendations: List[str] = Field(description="策略建议")
    content_angles: List[str] = Field(description="内容角度")

class ResearchReport(BaseModel):
    """研究报告"""
    target_audience: TargetAudience
    market_analysis: MarketAnalysis
    insights: Insights

class ContentStrategy(BaseModel):
    """内容策略"""
    core_message: str = Field(description="核心信息")
    value_proposition: str = Field(description="价值主张")
    unique_angle: str = Field(description="独特角度")
    call_to_action: str = Field(description="行动号召")

class MainBodySection(BaseModel):
    """主体内容章节"""
    section_1: str = Field(description="第一部分内容要点")
    section_2: str = Field(description="第二部分内容要点")
    section_3: str = Field(description="第三部分内容要点")

class ContentStructure(BaseModel):
    """内容结构"""
    opening_hook: str = Field(description="开头吸引点设计")
    main_body: MainBodySection
    closing: str = Field(description="结尾设计")

class VisualImage(BaseModel):
    """视觉图片"""
    position: int = Field(description="图片位置")
    purpose: str = Field(description="图片作用")
    description: str = Field(description="图片详细描述")
    style: str = Field(description="图片风格要求")

class VisualPlan(BaseModel):
    """视觉计划"""
    image_count: int = Field(description="图片数量")
    images: List[VisualImage] = Field(description="图片列表")

class EngagementDesign(BaseModel):
    """互动设计"""
    interactive_elements: List[str] = Field(description="互动元素")
    discussion_starters: List[str] = Field(description="讨论话题")
    shareability_factors: List[str] = Field(description="分享因素")

class ContentTone(BaseModel):
    """内容语调"""
    personality: str = Field(description="内容人格特征")
    voice_style: str = Field(description="语调风格")
    emotional_tone: str = Field(description="情感基调")
    language_level: str = Field(description="语言难度层次")

class CreativeBlueprint(BaseModel):
    """创意蓝图"""
    content_strategy: ContentStrategy
    content_structure: ContentStructure
    visual_plan: VisualPlan
    engagement_design: EngagementDesign
    content_tone: ContentTone

class StrategyBlueprint(BaseModel):
    """策略蓝图（完整的策略分析结果）"""
    research_report: ResearchReport
    creative_blueprint: CreativeBlueprint

# ===================================
# 执行模块的数据模型
# ===================================

class ContentOverview(BaseModel):
    """内容概述"""
    theme: str = Field(description="主题")
    total_images: int = Field(description="总图片数")
    target_audience: str = Field(description="目标受众")
    content_style: str = Field(description="内容风格")
    persona_voice: str = Field(description="人格语调")

class ImageContent(BaseModel):
    """图片内容"""
    image_number: int = Field(description="图片编号")
    type: str = Field(description="图片类型")
    title: str = Field(description="图片标题")
    main_content: str = Field(description="主要内容")
    visual_elements: List[str] = Field(description="视觉元素")
    color_scheme: str = Field(description="色彩方案")
    layout: str = Field(description="布局方式")
    height_constraint: str = Field(description="高度约束")

class DesignPrinciples(BaseModel):
    """设计原则"""
    size_constraint: str = Field(description="尺寸约束")
    font_hierarchy: str = Field(description="字体层次")
    color_palette: List[str] = Field(description="色彩调色板")
    spacing: str = Field(description="间距设置")
    visual_consistency: str = Field(description="视觉一致性")

class DesignSpecification(BaseModel):
    """设计规范（执行阶段的输出）"""
    content_overview: ContentOverview
    xiaohongshu_titles: List[str] = Field(description="小红书标题列表")
    xiaohongshu_content: str = Field(description="小红书正文内容")
    image_contents: List[ImageContent] = Field(description="图片内容列表")
    design_principles: DesignPrinciples 