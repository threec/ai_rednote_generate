"""
策略罗盘引擎 V2.0 - 重构版
基于新核心架构，提供战略级内容策略分析

目标：为内容创作提供全面的战略指导，包括目标定位、受众分析、竞争策略等
"""

from typing import Dict, Any
from modules.engines.base_engine_v2 import StrategyEngine
from modules.core.output import ContentType, OutputFormat

class StrategyCompassEngineV2(StrategyEngine):
    """策略罗盘引擎 V2.0"""
    
    def __init__(self, llm, **kwargs):
        super().__init__(llm, **kwargs)
        self.engine_name = "strategy_compass"
    
    def _setup_processing_chain(self):
        """设置策略分析处理链"""
        
        system_prompt = """你是一个资深的内容策略专家和市场分析师。

你的任务是为给定主题制定全面的内容战略方案，确保内容能够在小红书平台上获得最佳传播效果。

**核心能力**：
1. 深度市场分析和竞争态势研究
2. 目标受众细分和用户画像构建
3. 内容策略制定和传播路径规划
4. 平台特征分析和算法适配策略
5. 数据驱动的决策支持

**分析维度**：
- 市场环境分析
- 目标受众研究
- 竞争对手分析
- 内容定位策略
- 传播渠道规划
- 效果预期评估

**输出要求**：
- 采用混合数据格式（结构化数据 + 分析报告）
- 包含可执行的具体策略建议
- 提供量化的目标和指标
- 确保后续引擎能够基于此策略执行

输出格式应包含：
1. 结构化的策略数据（JSON格式）
2. 详细的分析报告（Markdown格式）
3. 可视化的策略地图描述
"""

        user_template = """
请为以下主题制定全面的内容战略方案：

**主题**: {topic}

**现有人格设定**: {persona_info}

**分析要求**:
1. 深入分析该主题在小红书平台的市场机会
2. 构建精准的目标受众画像和需求分析
3. 制定差异化的内容定位和竞争策略
4. 规划最优的内容发布和传播策略
5. 设计可衡量的成功指标和优化路径

请输出包含结构化数据和详细分析的混合格式结果。

**结构化数据要求**（JSON格式）：
```json
{{
  "strategy_overview": {{
    "target_audience": "目标受众描述",
    "content_positioning": "内容定位",
    "differentiation_strategy": "差异化策略",
    "success_metrics": ["指标1", "指标2", "..."]
  }},
  "audience_analysis": {{
    "primary_segments": [
      {{
        "segment_name": "细分群体名称",
        "demographics": "人口统计特征",
        "psychographics": "心理特征",
        "pain_points": ["痛点1", "痛点2"],
        "content_preferences": ["偏好1", "偏好2"]
      }}
    ]
  }},
  "content_strategy": {{
    "topics": ["主题1", "主题2", "..."],
    "formats": ["格式1", "格式2", "..."],
    "posting_schedule": "发布时间策略",
    "engagement_tactics": ["互动策略1", "策略2"]
  }},
  "competitive_analysis": {{
    "key_competitors": ["竞对1", "竞对2"],
    "market_gaps": ["机会点1", "机会点2"],
    "competitive_advantages": ["优势1", "优势2"]
  }}
}}
```

**分析报告要求**（Markdown格式）：
# 内容战略分析报告

## 1. 战略概览
### 1.1 市场机会分析
### 1.2 核心战略定位
### 1.3 成功关键因素

## 2. 目标受众深度分析
### 2.1 受众细分研究
### 2.2 用户需求洞察
### 2.3 内容消费行为

## 3. 竞争环境分析
### 3.1 竞争对手研究
### 3.2 市场空白识别
### 3.3 差异化机会

## 4. 内容策略规划
### 4.1 内容主题策略
### 4.2 内容形式创新
### 4.3 发布节奏优化

## 5. 传播效果预期
### 5.1 目标指标设定
### 5.2 效果评估体系
### 5.3 优化调整机制

请确保策略具有可操作性和可衡量性。
"""

        prompt_template = self._create_prompt_template(system_prompt, user_template)
        self.processing_chain = self._create_processing_chain(prompt_template)
    
    async def _process_content(self, inputs: Dict[str, Any]) -> str:
        """处理内容 - 生成策略分析"""
        topic = inputs.get("topic", "")
        
        # 获取人格设定信息
        persona_info = "未提供人格设定"
        if "persona_core" in inputs:
            persona_data = inputs["persona_core"]
            if isinstance(persona_data, dict) and "content" in persona_data:
                persona_info = persona_data["content"][:500] + "..."
        
        # 准备链输入
        chain_inputs = {
            "topic": topic,
            "persona_info": persona_info
        }
        
        # 执行AI处理
        result = await self._invoke_chain_with_timeout(chain_inputs)
        
        return result
    
    async def _post_process(self, output, inputs: Dict[str, Any]):
        """后处理 - 提取和验证策略数据"""
        content = output.content or ""
        
        # 尝试提取JSON结构化数据
        structured_data = self._extract_strategy_data(content)
        if structured_data:
            output.set_structured_data(structured_data)
        
        # 添加策略相关元数据
        output.set_metadata(
            strategy_extracted=bool(structured_data),
            has_audience_analysis=self._has_section(content, "受众分析"),
            has_competitive_analysis=self._has_section(content, "竞争"),
            has_content_strategy=self._has_section(content, "内容策略"),
            content_quality=self._assess_content_quality(content),
            actionable_items=self._count_actionable_items(content)
        )
    
    def _extract_strategy_data(self, content: str) -> Dict[str, Any]:
        """从分析报告中提取结构化的策略数据"""
        import json
        import re
        
        from datetime import datetime
        structured_data = {
            "extracted_at": datetime.now().isoformat(),
            "extraction_method": "json_parsing"
        }
        
        # 尝试提取JSON数据
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        json_matches = re.findall(json_pattern, content, re.DOTALL)
        
        if json_matches:
            try:
                parsed_json = json.loads(json_matches[0])
                structured_data.update(parsed_json)
                structured_data["json_extraction_success"] = True
            except json.JSONDecodeError:
                structured_data["json_extraction_success"] = False
        else:
            structured_data["json_extraction_success"] = False
        
        # 文本分析提取关键信息
        if "目标受众" in content:
            structured_data["has_target_audience"] = True
        
        if "差异化" in content:
            structured_data["has_differentiation"] = True
        
        if "指标" in content or "KPI" in content:
            structured_data["has_metrics"] = True
        
        # 提取关键策略词汇
        strategy_keywords = []
        for line in content.split('\n'):
            if any(keyword in line for keyword in ["策略", "定位", "目标", "优势"]):
                strategy_keywords.append(line.strip())
        
        if strategy_keywords:
            structured_data["strategy_keywords"] = strategy_keywords[:10]
        
        return structured_data
    
    def _has_section(self, content: str, section_keyword: str) -> bool:
        """检查内容是否包含特定章节"""
        return section_keyword in content
    
    def _assess_content_quality(self, content: str) -> str:
        """评估内容质量"""
        word_count = len(content)
        
        if word_count > 2000 and "##" in content and "```json" in content:
            return "high"
        elif word_count > 1000 and ("##" in content or "策略" in content):
            return "medium"
        else:
            return "low"
    
    def _count_actionable_items(self, content: str) -> int:
        """统计可执行项目数量"""
        actionable_patterns = [
            "建议", "应该", "需要", "推荐", "策略", "方案", "计划"
        ]
        
        count = 0
        for pattern in actionable_patterns:
            count += content.count(pattern)
        
        return min(count, 50)  # 限制最大数量
    
    def get_strategy_summary(self, topic: str) -> Dict[str, Any]:
        """获取策略摘要信息"""
        cached_output = self.load_cache(topic)
        if not cached_output:
            return {"error": "未找到策略分析"}
        
        structured_data = cached_output.structured_data or {}
        content = cached_output.content
        
        summary = {
            "topic": topic,
            "has_json_data": structured_data.get("json_extraction_success", False),
            "has_target_audience": structured_data.get("has_target_audience", False),
            "has_differentiation": structured_data.get("has_differentiation", False),
            "has_metrics": structured_data.get("has_metrics", False),
            "content_quality": structured_data.get("content_quality", "unknown"),
            "actionable_items": structured_data.get("actionable_items", 0),
            "strategy_preview": content[:300] + "..." if len(content) > 300 else content
        }
        
        # 如果有结构化数据，提取关键信息
        if "strategy_overview" in structured_data:
            overview = structured_data["strategy_overview"]
            summary.update({
                "target_audience": overview.get("target_audience", ""),
                "content_positioning": overview.get("content_positioning", ""),
                "success_metrics": overview.get("success_metrics", [])
            })
        
        return summary

# 向后兼容
StrategyCompassEngine = StrategyCompassEngineV2 