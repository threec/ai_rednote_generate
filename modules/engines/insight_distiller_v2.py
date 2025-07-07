"""
洞察提炼器引擎 V2.0 - 改进版
采用文本分析报告+结构化元数据的混合输出模式

核心改进：
1. 主要分析内容用文本形式输出，便于阅读和理解
2. 关键数据和结论用结构化格式存储
3. 避免复杂的JSON转义问题
4. 更符合人类思维的输出方式

目标：将零散数据升华为核心故事，挖掘爆款潜质
"""

import json
import os
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

# 修复导入路径问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.langchain_workflow import BaseWorkflowEngine
from modules.utils import get_logger

class InsightDistillerEngineV2(BaseWorkflowEngine):
    """洞察提炼器引擎V2 - 混合输出模式"""
    
    def __init__(self, llm):
        super().__init__(llm)
        self.engine_name = "insight_distiller_v2"
        self._initialize_insight_chain()
    
    def _initialize_insight_chain(self):
        """初始化洞察分析链"""
        
        # 系统提示词 - 要求输出分析报告格式
        system_prompt = """你是一个专业的内容策略分析师和洞察挖掘专家。

你的任务是基于事实验证结果，深度分析并提炼出核心洞察，形成一份专业的洞察分析报告。

**你的核心能力**：
1. 从海量信息中提炼核心价值点
2. 识别内容的爆款潜质和传播要素
3. 将复杂数据转化为有故事性的洞察
4. 预测内容的用户反响和传播效果

**报告要求**：
- 以分析报告的形式输出，逻辑清晰，见解深刻
- 重点突出Big Idea和核心价值主张
- 包含具体的内容建议和执行要点
- 语言专业但充满洞察力

**报告结构**：
# 洞察提炼分析报告

## 1. 核心洞察摘要
- 最重要的3个关键洞察
- Big Idea核心理念
- 目标用户的核心痛点

## 2. 深度价值分析
- 内容的独特价值主张
- 与竞争内容的差异化优势
- 用户获得感和共鸣点

## 3. 爆款潜质评估
- 传播要素分析
- 用户分享动机
- 病毒传播可能性

## 4. 故事化包装建议
- 核心故事线设计
- 情感共鸣点挖掘
- 具体的表达建议

## 5. 内容执行要点
- 关键信息层次
- 重点突出策略
- 互动设计建议

## 6. 预期效果评估
- 目标用户反响预测
- 传播效果评估
- 潜在风险点提示

请确保分析深入、洞察精准，为后续内容创作提供有力的指导。
"""

        user_template = """
请基于以下信息进行深度洞察分析：

**主题**: {topic}

**人格档案**: {persona_summary}

**策略方向**: {strategy_summary}

**事实基础**: {truth_summary}

**分析要求**:
1. 深度挖掘该主题的核心价值和独特洞察
2. 识别内容的爆款潜质和传播要素
3. 提炼出能够引起用户共鸣的Big Idea
4. 给出具体的内容包装和执行建议
5. 评估内容的预期效果和传播潜力

请输出一份完整的洞察分析报告。
"""

        self.insight_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_template)
        ])
        
        self.insight_chain = (
            self.insight_prompt
            | self.llm
            | StrOutputParser()
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行洞察分析"""
        topic = inputs.get("topic", "")
        persona = inputs.get("persona", {})
        strategy = inputs.get("strategy", {})
        truth = inputs.get("truth", {})
        force_regenerate = inputs.get("force_regenerate", False)
        
        self.logger.info(f"💡 洞察提炼器引擎V2启动 - 主题: {topic}")
        
        # 检查缓存
        if not force_regenerate:
            cached_result = self.load_flexible_cache(topic)
            if cached_result:
                self.logger.info("✓ 使用缓存的洞察分析报告")
                return cached_result
        
        try:
            # 提取各引擎的摘要信息
            persona_summary = self._extract_persona_summary(persona)
            strategy_summary = self._extract_strategy_summary(strategy)
            truth_summary = self._extract_truth_summary(truth)
            
            # 执行洞察分析链
            self.logger.info("执行洞察深度分析...")
            report_text = await self.insight_chain.ainvoke({
                "topic": topic,
                "persona_summary": persona_summary,
                "strategy_summary": strategy_summary,
                "truth_summary": truth_summary
            })
            
            # 创建灵活输出
            output = self.create_output(topic)
            
            # 设置文本内容
            output.set_content(report_text, "text")
            
            # 设置元数据
            output.set_metadata(
                engine_version="2.0",
                topic=topic,
                analysis_type="insight_distillation",
                word_count=len(report_text.split()),
                execution_status="success",
                insight_quality="high",
                viral_potential="evaluated",
                big_idea_extracted=True,
                dependencies={
                    "persona": bool(persona),
                    "strategy": bool(strategy),
                    "truth": bool(truth)
                }
            )
            
            # 转换为结果
            result = output.to_result()
            
            # 保存缓存
            self.save_cache(topic, result, "insight_distiller_v2.json")
            
            self.logger.info("✓ 洞察分析报告完成")
            return result
            
        except Exception as e:
            self.logger.error(f"洞察提炼器引擎V2执行失败: {str(e)}")
            
            # 创建错误输出
            output = self.create_output(topic)
            output.set_content(self._get_fallback_report(topic), "text")
            output.set_metadata(
                execution_status="fallback",
                error=str(e),
                topic=topic
            )
            
            return output.to_result()
    
    def _extract_persona_summary(self, persona: Dict[str, Any]) -> str:
        """提取人格档案摘要"""
        if not persona:
            return "通用内容人格"
        
        persona_data = persona.get("persona_data", {})
        persona_core = persona_data.get("persona_core", {})
        
        name = persona_core.get("signature_identity", {}).get("name", "内容创作者")
        style = persona_core.get("voice_and_tone", {}).get("language_style", "专业亲切")
        
        return f"人格: {name}, 风格: {style}"
    
    def _extract_strategy_summary(self, strategy: Dict[str, Any]) -> str:
        """提取策略摘要"""
        if not strategy:
            return "通用内容战略"
        
        strategy_data = strategy.get("strategy_data", {})
        approach = strategy_data.get("strategy_selection", {}).get("recommended_approach", "")
        core_msg = strategy_data.get("content_strategy", {}).get("core_message", "")
        
        return f"策略: {approach}, 核心信息: {core_msg}"
    
    def _extract_truth_summary(self, truth: Dict[str, Any]) -> str:
        """提取事实摘要"""
        if not truth:
            return "基础事实验证"
        
        # 如果是V2版本的文本格式
        if "content" in truth:
            content = truth["content"]
            # 提取报告的关键信息
            lines = content.split('\n')
            key_facts = []
            for line in lines:
                if line.strip() and ('核心事实' in line or '权威数据' in line or '专家观点' in line):
                    key_facts.append(line.strip())
            return " | ".join(key_facts[:3]) if key_facts else "已完成基础事实验证"
        
        # 传统JSON格式
        truth_data = truth.get("truth_data", {})
        authority = truth_data.get("verification_summary", {}).get("authority_level", "中等")
        
        return f"事实验证: {authority}权威性"
    
    def _get_fallback_report(self, topic: str) -> str:
        """获取备用报告"""
        return f"""# {topic} - 洞察分析报告

## 1. 核心洞察摘要
- 该主题具有良好的内容创作潜力
- 目标用户对此类内容有明确需求
- 可以通过专业角度提供独特价值

## 2. 深度价值分析
- 内容价值：为用户提供实用的指导和建议
- 差异化优势：结合个人经验和专业知识
- 用户获得感：解决实际问题，提升认知水平

## 3. 爆款潜质评估
- 传播要素：实用性强，有明确的目标群体
- 分享动机：用户愿意分享有价值的内容
- 病毒传播：中等潜力，需要精心设计传播点

## 4. 故事化包装建议
- 核心故事线：以问题-解决方案为主线
- 情感共鸣点：关注用户的实际困难和需求
- 表达建议：结合具体案例和实践经验

## 5. 内容执行要点
- 关键信息层次：重点突出核心观点
- 重点突出策略：使用数据和案例支撑
- 互动设计：鼓励用户分享经验和问题

## 6. 预期效果评估
- 目标用户反响：积极正面，有实用价值
- 传播效果：稳定增长，目标群体精准
- 潜在风险：注意信息的准确性和时效性

**注意**: 这是一个备用分析报告，建议根据实际情况进行调整和优化。
"""

    def get_big_idea(self, topic: str) -> Optional[str]:
        """获取核心Big Idea"""
        cached_result = self.load_flexible_cache(topic)
        if not cached_result:
            return None
        
        content = cached_result.get("content", "")
        if content:
            # 从报告中提取Big Idea
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'Big Idea' in line or '核心理念' in line:
                    # 返回该行和下一行的内容
                    if i + 1 < len(lines):
                        return f"{line.strip()} {lines[i+1].strip()}"
                    return line.strip()
        
        return None 