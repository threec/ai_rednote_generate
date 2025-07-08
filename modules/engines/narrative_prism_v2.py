"""
叙事棱镜引擎 V2.0 - 重构版
基于新核心架构，提供故事化内容创作和叙事结构设计

目标：将策略洞察转化为引人入胜的故事叙述，构建情感连接
"""

from typing import Dict, Any, List
from modules.engines.base_engine_v2 import TextReportEngine
from modules.core.output import ContentType, OutputFormat

class NarrativePrismEngineV2(TextReportEngine):
    """叙事棱镜引擎 V2.0"""
    
    def __init__(self, llm, **kwargs):
        super().__init__(llm, **kwargs)
        self.engine_name = "narrative_prism"
    
    def get_content_type(self) -> ContentType:
        return ContentType.CREATIVE
    
    def get_expected_output_format(self) -> OutputFormat:
        return OutputFormat.TEXT
    
    def _setup_processing_chain(self):
        """设置叙事创作处理链"""
        
        system_prompt = """你是一个专业的故事创作专家和叙事结构设计师。

你的任务是将战略分析和用户洞察转化为引人入胜的故事叙述，创造情感共鸣和价值传递。

**核心能力**：
1. 故事结构设计和叙事节奏控制
2. 情感共鸣点构建和用户代入感创造
3. 场景化描述和生动形象塑造
4. 冲突设置和悬念营造
5. 价值观传递和行为引导
6. 多元化叙事视角和表达方式

**叙事原则**：
- 真实性：基于真实场景和用户体验
- 共鸣性：触达用户内心真实感受
- 实用性：提供具体可行的解决方案
- 趣味性：保持内容的吸引力和可读性
- 教育性：传递有价值的知识和经验

**输出要求**：
- 采用小红书风格的故事化文本
- 结构清晰，节奏紧凑
- 情感真挚，语言生动
- 包含具体的场景和细节
- 确保内容的实用价值

输出格式为连贯的故事化文本，不需要章节标题，直接呈现完整的叙事内容。
"""

        user_template = """
请基于以下分析结果创作一个引人入胜的故事化内容：

**主题**: {topic}

**创作素材**:
- 人格设定: {persona_info}
- 策略分析: {strategy_info}
- 事实依据: {truth_info}
- 用户洞察: {insight_info}

**创作要求**:
1. 采用第一人称或第二人称视角，增强代入感
2. 开头要能立即抓住读者注意力
3. 通过具体场景和细节展现内容价值
4. 融入情感元素，创造共鸣点
5. 结尾要有明确的行动指导或价值总结
6. 保持小红书平台的轻松、亲切风格

**内容结构建议**:
- 开头：场景设置/问题提出
- 发展：经历描述/解决过程
- 高潮：关键发现/重要洞察
- 结尾：总结收获/行动指导

**语言风格**:
- 亲切自然，如朋友分享
- 生动具体，避免抽象说教
- 适当使用网络流行语
- 保持正能量和温暖感

请创作一篇完整的故事化内容，确保既有情感温度又有实用价值。
"""

        prompt_template = self._create_prompt_template(system_prompt, user_template)
        self.processing_chain = self._create_processing_chain(prompt_template)
    
    async def _process_content(self, inputs: Dict[str, Any]) -> str:
        """处理内容 - 生成故事化叙述"""
        topic = inputs.get("topic", "")
        
        # 获取前序分析信息
        persona_info = self._extract_info(inputs, "persona_core", "温暖贴心的分享者")
        strategy_info = self._extract_info(inputs, "strategy_compass", "关注用户需求的策略")
        truth_info = self._extract_info(inputs, "truth_detector", "经过事实验证的内容")
        insight_info = self._extract_info(inputs, "insight_distiller", "深度理解用户痛点")
        
        # 准备链输入
        chain_inputs = {
            "topic": topic,
            "persona_info": persona_info,
            "strategy_info": strategy_info,
            "truth_info": truth_info,
            "insight_info": insight_info
        }
        
        # 执行AI处理
        result = await self._invoke_chain_with_timeout(chain_inputs)
        
        return result
    
    def _extract_info(self, inputs: Dict[str, Any], key: str, default: str) -> str:
        """提取前序分析信息"""
        if key in inputs:
            data = inputs[key]
            if isinstance(data, dict) and "content" in data:
                content = data["content"]
                return content[:400] + "..." if len(content) > 400 else content
        return default
    
    async def _post_process(self, output, inputs: Dict[str, Any]):
        """后处理 - 分析叙事质量"""
        content = output.content or ""
        
        # 分析叙事质量数据
        narrative_data = self._analyze_narrative_quality(content)
        if narrative_data:
            output.set_structured_data(narrative_data)
        
        # 添加叙事相关元数据
        output.set_metadata(
            narrative_created=True,
            story_structure=self._analyze_story_structure(content),
            emotional_tone=self._analyze_emotional_tone(content),
            readability_score=self._assess_readability(content),
            engagement_level=self._assess_engagement(content),
            practical_value=self._assess_practical_value(content),
            xiaohongshu_style=self._check_platform_style(content)
        )
    
    def _analyze_narrative_quality(self, content: str) -> Dict[str, Any]:
        """分析叙事质量"""
        from datetime import datetime
        
        narrative_data = {
            "created_at": datetime.now().isoformat(),
            "analysis_method": "narrative_quality_assessment"
        }
        
        # 分析文本长度和结构
        word_count = len(content)
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        
        narrative_data.update({
            "word_count": word_count,
            "paragraph_count": paragraph_count,
            "avg_paragraph_length": word_count // max(paragraph_count, 1)
        })
        
        # 检查叙事元素
        narrative_elements = {
            "has_opening": self._has_opening(content),
            "has_conflict": self._has_conflict(content),
            "has_resolution": self._has_resolution(content),
            "has_emotional_elements": self._has_emotional_elements(content),
            "has_specific_details": self._has_specific_details(content),
            "has_call_to_action": self._has_call_to_action(content)
        }
        
        narrative_data["narrative_elements"] = narrative_elements
        
        # 计算叙事完整性分数
        completeness_score = sum(narrative_elements.values())
        narrative_data["narrative_completeness"] = completeness_score
        narrative_data["quality_level"] = "high" if completeness_score >= 5 else "medium" if completeness_score >= 3 else "low"
        
        # 提取关键情感词汇
        emotional_words = self._extract_emotional_words(content)
        if emotional_words:
            narrative_data["emotional_words"] = emotional_words[:8]
        
        # 提取行动指导
        action_points = self._extract_action_points(content)
        if action_points:
            narrative_data["action_points"] = action_points[:5]
        
        return narrative_data
    
    def _analyze_story_structure(self, content: str) -> str:
        """分析故事结构"""
        if len(content) < 200:
            return "simple"
        
        has_beginning = any(word in content[:200] for word in ["我", "最近", "今天", "有一次", "前几天"])
        has_middle = "但是" in content or "然后" in content or "后来" in content
        has_end = any(word in content[-200:] for word in ["最后", "现在", "总之", "希望", "分享给"])
        
        if has_beginning and has_middle and has_end:
            return "complete"
        elif (has_beginning and has_middle) or (has_middle and has_end):
            return "partial"
        else:
            return "basic"
    
    def _analyze_emotional_tone(self, content: str) -> str:
        """分析情感基调"""
        positive_words = ["开心", "快乐", "满意", "惊喜", "温暖", "感动", "希望", "美好"]
        negative_words = ["担心", "焦虑", "困扰", "难过", "失望", "害怕", "紧张"]
        neutral_words = ["分享", "经历", "体验", "发现", "学到", "了解"]
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        neutral_count = sum(1 for word in neutral_words if word in content)
        
        if positive_count > negative_count and positive_count > 0:
            return "positive"
        elif negative_count > positive_count and negative_count > 0:
            return "negative"
        else:
            return "neutral"
    
    def _assess_readability(self, content: str) -> int:
        """评估可读性分数（1-10）"""
        # 基于句子长度、段落结构等因素
        sentences = [s for s in content.replace('。', '。\n').split('\n') if s.strip()]
        avg_sentence_length = sum(len(s) for s in sentences) / max(len(sentences), 1)
        
        # 理想句子长度15-25字
        if 15 <= avg_sentence_length <= 25:
            readability = 8
        elif 10 <= avg_sentence_length <= 30:
            readability = 6
        else:
            readability = 4
        
        # 调整分数
        if len(content) > 1000:  # 适当长度加分
            readability += 1
        if '？' in content or '！' in content:  # 有感叹/疑问句加分
            readability += 1
        
        return min(readability, 10)
    
    def _assess_engagement(self, content: str) -> str:
        """评估吸引力水平"""
        engagement_indicators = ["你", "我们", "一起", "分享", "经历", "故事", "发现", "惊喜"]
        engagement_count = sum(1 for indicator in engagement_indicators if indicator in content)
        
        if engagement_count >= 6:
            return "high"
        elif engagement_count >= 3:
            return "medium"
        else:
            return "low"
    
    def _assess_practical_value(self, content: str) -> str:
        """评估实用价值"""
        value_indicators = ["方法", "建议", "技巧", "经验", "步骤", "注意", "推荐", "选择"]
        value_count = sum(1 for indicator in value_indicators if indicator in content)
        
        if value_count >= 4:
            return "high"
        elif value_count >= 2:
            return "medium"
        else:
            return "low"
    
    def _check_platform_style(self, content: str) -> bool:
        """检查是否符合小红书风格"""
        style_indicators = ["分享", "姐妹", "宝宝", "真的", "超级", "建议", "经验", "推荐"]
        style_count = sum(1 for indicator in style_indicators if indicator in content)
        return style_count >= 3
    
    def _has_opening(self, content: str) -> bool:
        """检查是否有吸引人的开头"""
        opening_patterns = ["最近", "今天", "有一次", "说到", "作为", "我发现"]
        return any(pattern in content[:100] for pattern in opening_patterns)
    
    def _has_conflict(self, content: str) -> bool:
        """检查是否有冲突或问题"""
        conflict_patterns = ["但是", "然而", "问题", "困扰", "挑战", "难题", "担心"]
        return any(pattern in content for pattern in conflict_patterns)
    
    def _has_resolution(self, content: str) -> bool:
        """检查是否有解决方案"""
        resolution_patterns = ["解决", "方法", "建议", "经验", "发现", "效果", "改善"]
        return any(pattern in content for pattern in resolution_patterns)
    
    def _has_emotional_elements(self, content: str) -> bool:
        """检查是否有情感元素"""
        emotional_patterns = ["感动", "开心", "担心", "惊喜", "温暖", "感谢", "希望"]
        return any(pattern in content for pattern in emotional_patterns)
    
    def _has_specific_details(self, content: str) -> bool:
        """检查是否有具体细节"""
        detail_patterns = ["天", "点", "分钟", "次", "个", "块", "元", "米", "克"]
        return any(pattern in content for pattern in detail_patterns)
    
    def _has_call_to_action(self, content: str) -> bool:
        """检查是否有行动号召"""
        action_patterns = ["分享", "关注", "试试", "建议", "记得", "一定要", "推荐"]
        return any(pattern in content[-200:] for pattern in action_patterns)
    
    def _extract_emotional_words(self, content: str) -> List[str]:
        """提取情感词汇"""
        emotional_words = ["开心", "快乐", "感动", "温暖", "惊喜", "满意", "担心", "焦虑"]
        found_words = [word for word in emotional_words if word in content]
        return found_words
    
    def _extract_action_points(self, content: str) -> List[str]:
        """提取行动要点"""
        lines = content.split('\n')
        action_points = []
        
        for line in lines:
            if any(word in line for word in ["建议", "推荐", "记得", "注意", "一定要"]):
                action_points.append(line.strip())
        
        return action_points
    
    def get_narrative_summary(self, topic: str) -> Dict[str, Any]:
        """获取叙事摘要信息"""
        cached_output = self.load_cache(topic)
        if not cached_output:
            return {"error": "未找到叙事内容"}
        
        structured_data = cached_output.structured_data or {}
        content = cached_output.content
        
        summary = {
            "topic": topic,
            "quality_level": structured_data.get("quality_level", "unknown"),
            "narrative_completeness": structured_data.get("narrative_completeness", 0),
            "word_count": structured_data.get("word_count", 0),
            "emotional_tone": structured_data.get("emotional_tone", "neutral"),
            "readability_score": structured_data.get("readability_score", 0),
            "engagement_level": structured_data.get("engagement_level", "unknown"),
            "practical_value": structured_data.get("practical_value", "unknown"),
            "xiaohongshu_style": structured_data.get("xiaohongshu_style", False),
            "content_preview": content[:200] + "..." if len(content) > 200 else content
        }
        
        return summary

# 向后兼容
NarrativePrismEngine = NarrativePrismEngineV2 