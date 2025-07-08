"""
洞察提炼器引擎 V2.0 - 重构版
基于新核心架构，提供深度洞察分析和用户需求挖掘

目标：从数据中提炼出有价值的洞察，发现用户真实需求和痛点
"""

from typing import Dict, Any, Optional, List
from modules.engines.base_engine_v2 import AnalysisEngine
from modules.core.output import ContentType, OutputFormat

class InsightDistillerEngineV2(AnalysisEngine):
    """洞察提炼器引擎 V2.0"""
    
    def __init__(self, llm, **kwargs):
        super().__init__(llm, **kwargs)
        self.engine_name = "insight_distiller"
    
    def _setup_processing_chain(self):
        """设置洞察分析处理链"""
        
        system_prompt = """你是一个资深的用户研究专家和数据洞察分析师。

你的任务是从复杂的信息中提炼出深层的用户洞察，发现隐藏的需求模式和行为动机。

**核心能力**：
1. 用户行为模式识别和分析
2. 深层心理需求挖掘
3. 痛点和机会点识别
4. 情感驱动因素分析
5. 用户决策路径解构
6. 潜在需求预测

**分析维度**：
- 用户行为洞察
- 情感需求分析
- 痛点深度挖掘
- 决策影响因素
- 使用场景分析
- 潜在机会识别

**输出要求**：
- 采用深度分析报告格式
- 包含具体的洞察要点
- 提供可执行的建议
- 结合心理学和行为学原理
- 确保洞察的可操作性

输出格式：
# 用户洞察深度分析报告

## 1. 核心洞察概览
### 1.1 关键发现摘要
### 1.2 洞察价值评估
### 1.3 影响力分析

## 2. 用户行为洞察
### 2.1 行为模式识别
### 2.2 使用场景分析
### 2.3 决策路径解构

## 3. 深层需求挖掘
### 3.1 显性需求分析
### 3.2 隐性需求发现
### 3.3 情感驱动因素

## 4. 痛点与机会分析
### 4.1 核心痛点识别
### 4.2 痛点程度评估
### 4.3 解决方案机会

## 5. 心理动机分析
### 5.1 动机层次解构
### 5.2 情感触发点
### 5.3 心理预期管理

## 6. 可执行洞察
### 6.1 内容策略指导
### 6.2 用户体验优化
### 6.3 价值主张调整
"""

        user_template = """
请对以下主题进行深度的用户洞察分析：

**主题**: {topic}

**已有分析背景**:
- 人格设定: {persona_info}
- 策略分析: {strategy_info}
- 事实核查: {truth_info}

**分析要求**:
1. 深入分析该主题下用户的真实需求和痛点
2. 挖掘用户的深层心理动机和情感驱动因素
3. 识别用户行为模式和决策影响因素
4. 发现潜在的机会点和价值创造空间
5. 提供具体可执行的洞察指导

**特别关注**:
- 用户在该领域的困惑和焦虑点
- 信息获取和理解的障碍
- 实际行动的阻碍因素
- 情感支持和认同需求
- 社交分享和互动动机

请输出完整的用户洞察分析报告，确保洞察的深度性和可操作性。
"""

        prompt_template = self._create_prompt_template(system_prompt, user_template)
        self.processing_chain = self._create_processing_chain(prompt_template)
    
    async def _process_content(self, inputs: Dict[str, Any]) -> str:
        """处理内容 - 生成洞察分析"""
        topic = inputs.get("topic", "")
        
        # 获取前序分析信息
        persona_info = self._extract_info(inputs, "persona_core", "未提供人格设定")
        strategy_info = self._extract_info(inputs, "strategy_compass", "未提供策略分析")
        truth_info = self._extract_info(inputs, "truth_detector", "未提供事实核查")
        
        # 准备链输入
        chain_inputs = {
            "topic": topic,
            "persona_info": persona_info,
            "strategy_info": strategy_info,
            "truth_info": truth_info
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
                return content[:500] + "..." if len(content) > 500 else content
        return default
    
    async def _post_process(self, output, inputs: Dict[str, Any]):
        """后处理 - 提取洞察数据"""
        content = output.content or ""
        
        # 提取结构化的洞察数据
        insight_data = self._extract_insight_data(content)
        if insight_data:
            output.set_structured_data(insight_data)
        
        # 添加洞察相关元数据
        output.set_metadata(
            insight_analysis_completed=True,
            has_behavior_insights=self._has_section(content, "行为洞察"),
            has_need_analysis=self._has_section(content, "需求挖掘"),
            has_pain_points=self._has_section(content, "痛点"),
            has_psychological_analysis=self._has_section(content, "心理动机"),
            has_actionable_insights=self._has_section(content, "可执行洞察"),
            insight_depth=self._assess_insight_depth(content),
            actionability_score=self._assess_actionability(content)
        )
    
    def _extract_insight_data(self, content: str) -> Dict[str, Any]:
        """从分析报告中提取结构化的洞察数据"""
        from datetime import datetime
        
        insight_data = {
            "analyzed_at": datetime.now().isoformat(),
            "analysis_method": "deep_insight_analysis"
        }
        
        # 提取关键洞察点
        key_insights = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # 查找洞察要点
            if any(keyword in line for keyword in ["洞察", "发现", "关键", "核心"]):
                if line.strip() and not line.startswith('#'):
                    key_insights.append(line.strip())
        
        if key_insights:
            insight_data["key_insights"] = key_insights[:8]  # 限制数量
        
        # 提取痛点信息
        pain_points = []
        for line in lines:
            if any(keyword in line for keyword in ["痛点", "困难", "挑战", "障碍", "问题"]):
                if line.strip() and not line.startswith('#'):
                    pain_points.append(line.strip())
        
        if pain_points:
            insight_data["pain_points"] = pain_points[:5]
        
        # 提取用户需求
        user_needs = []
        for line in lines:
            if any(keyword in line for keyword in ["需求", "期望", "希望", "想要", "渴望"]):
                if line.strip() and not line.startswith('#'):
                    user_needs.append(line.strip())
        
        if user_needs:
            insight_data["user_needs"] = user_needs[:5]
        
        # 提取行为模式
        behavior_patterns = []
        for line in lines:
            if any(keyword in line for keyword in ["行为", "模式", "习惯", "倾向", "偏好"]):
                if line.strip() and not line.startswith('#'):
                    behavior_patterns.append(line.strip())
        
        if behavior_patterns:
            insight_data["behavior_patterns"] = behavior_patterns[:5]
        
        # 提取可执行建议
        actionable_suggestions = []
        for line in lines:
            if any(keyword in line for keyword in ["建议", "策略", "方案", "措施", "优化"]):
                if line.strip() and not line.startswith('#'):
                    actionable_suggestions.append(line.strip())
        
        if actionable_suggestions:
            insight_data["actionable_suggestions"] = actionable_suggestions[:6]
        
        # 检查分析完整性
        completeness_score = 0
        if insight_data.get("key_insights"):
            completeness_score += 2
        if insight_data.get("pain_points"):
            completeness_score += 2
        if insight_data.get("user_needs"):
            completeness_score += 2
        if insight_data.get("behavior_patterns"):
            completeness_score += 2
        if insight_data.get("actionable_suggestions"):
            completeness_score += 2
        
        insight_data["completeness_score"] = completeness_score
        insight_data["analysis_quality"] = "high" if completeness_score >= 8 else "medium" if completeness_score >= 6 else "low"
        
        return insight_data
    
    def _has_section(self, content: str, section_keyword: str) -> bool:
        """检查内容是否包含特定章节"""
        return section_keyword in content
    
    def _assess_insight_depth(self, content: str) -> str:
        """评估洞察深度"""
        depth_indicators = ["心理", "动机", "深层", "根本", "本质", "潜在"]
        depth_count = sum(1 for indicator in depth_indicators if indicator in content)
        
        if depth_count >= 4:
            return "deep"
        elif depth_count >= 2:
            return "medium"
        else:
            return "shallow"
    
    def _assess_actionability(self, content: str) -> int:
        """评估可执行性评分（1-10）"""
        actionable_indicators = ["建议", "策略", "方案", "实施", "操作", "执行", "具体", "步骤"]
        actionability_count = sum(1 for indicator in actionable_indicators if indicator in content)
        
        # 基于可执行指标数量评分
        score = min(actionability_count, 10)
        return max(score, 1)  # 确保最低1分
    
    def get_insight_summary(self, topic: str) -> Dict[str, Any]:
        """获取洞察摘要信息"""
        cached_output = self.load_cache(topic)
        if not cached_output:
            return {"error": "未找到洞察分析"}
        
        structured_data = cached_output.structured_data or {}
        content = cached_output.content
        
        summary = {
            "topic": topic,
            "analysis_quality": structured_data.get("analysis_quality", "unknown"),
            "completeness_score": structured_data.get("completeness_score", 0),
            "insight_depth": structured_data.get("insight_depth", "unknown"),
            "actionability_score": structured_data.get("actionability_score", 0),
            "key_insights_count": len(structured_data.get("key_insights", [])),
            "pain_points_count": len(structured_data.get("pain_points", [])),
            "user_needs_count": len(structured_data.get("user_needs", [])),
            "actionable_suggestions_count": len(structured_data.get("actionable_suggestions", [])),
            "content_preview": content[:300] + "..." if len(content) > 300 else content
        }
        
        # 添加洞察亮点
        if structured_data.get("key_insights"):
            summary["top_insights"] = structured_data["key_insights"][:3]
        
        if structured_data.get("pain_points"):
            summary["main_pain_points"] = structured_data["pain_points"][:3]
        
        return summary
    
    def get_actionable_recommendations(self, topic: str) -> List[str]:
        """获取可执行建议列表"""
        summary = self.get_insight_summary(topic)
        if "error" in summary:
            return []
        
        cached_output = self.load_cache(topic)
        structured_data = cached_output.structured_data or {}
        
        return structured_data.get("actionable_suggestions", [])

# 向后兼容
InsightDistillerEngine = InsightDistillerEngineV2 