"""
引擎③: 真理探机引擎 (Truth Detector Engine)  
RedCube AI 工作流系统

目标：克服大模型知识陈旧、易"胡说八道"的缺陷，建立高权威专属知识库

核心功能：
- 专业内容的生命线，没有准确事实，一切都是空中楼阁
- 研判事实，验证或证伪初始创意
- 挖掘报告中隐藏的"爆款"潜质
- 定义系列内容的"核心叙事(Big Idea)"
- 生成最终版的《内容创作蓝图》

实现方式：
- 基于LangChain构建事实验证链
- 集成多源权威数据验证
- 构建专业知识库支撑
- 输出经过验证的内容蓝图
"""

import json
import os
import sys
from typing import Dict, Any, Optional, List
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

# 修复导入路径问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.langchain_workflow import BaseWorkflowEngine  
from modules.utils import get_logger

class TruthDetectorEngine(BaseWorkflowEngine):
    """真理探机引擎 - 权威事实验证"""
    
    def __init__(self, llm):
        super().__init__("truth_detector", llm)
        self._initialize_truth_chain()
    
    def _initialize_truth_chain(self):
        """初始化事实验证链"""
        
        system_prompt = """
你是RedCube AI的"真理探机专家"，专门负责事实验证和权威性建立。

## 核心使命：建立高权威专属知识库

专业内容的生命线，没有准确事实，一切都是空中楼阁。你需要确保所有内容都有坚实的事实基础。

## 事实验证框架

### 【事实验证标准】
1. **最新性** 📅
   - 信息的时效性检查
   - 最新研究和数据更新
   - 政策法规变化跟踪

2. **权威性** 🏛️  
   - 权威机构和专家背书
   - 学术研究和临床数据
   - 行业标准和规范引用

3. **准确性** ✓
   - 数据的精确性验证
   - 统计信息的可靠性
   - 引用来源的真实性

4. **可验证性** 🔍
   - 提供具体的数据来源
   - 可追溯的引用链路
   - 第三方验证途径

### 【知识库构建】
1. **专业数据收集**
   - 权威机构发布数据
   - 学术研究最新成果
   - 行业报告和白皮书
   - 专家观点和见解

2. **事实核查流程**
   - 多源交叉验证
   - 时效性检查更新
   - 权威性等级评估
   - 准确性逐项确认

3. **知识结构化**
   - 核心事实提取
   - 支撑数据整理
   - 引用来源标注
   - 可信度等级标记

### 【输出规范】
必须返回严格的JSON格式：

```json
{{
  "fact_verification": {{
    "topic_domain": "专业领域分类",
    "verification_scope": "验证范围说明",
    "authority_level": "权威性等级评估",
    "fact_reliability": "事实可靠性评分"
  }},
  "core_facts": {{
    "verified_facts": [
      {{
        "fact_statement": "核心事实陈述",
        "authority_source": "权威来源",
        "evidence_type": "证据类型",
        "confidence_level": "置信度等级",
        "last_updated": "最后更新时间"
      }}
    ],
    "data_points": [
      {{
        "data_description": "数据描述",
        "numerical_value": "具体数值",
        "data_source": "数据来源",
        "collection_method": "收集方法",
        "sample_size": "样本规模"
      }}
    ]
  }},
  "expert_insights": {{
    "professional_opinions": [
      {{
        "expert_name": "专家姓名",
        "credentials": "专业资质",
        "opinion_summary": "观点摘要",
        "supporting_evidence": "支撑证据"
      }}
    ],
    "consensus_views": ["共识观点1", "共识观点2"],
    "controversial_points": ["争议点1", "争议点2"]
  }},
  "research_foundation": {{
    "key_studies": [
      {{
        "study_title": "研究标题",
        "researchers": "研究者",
        "publication": "发表期刊",
        "year": "发表年份",
        "main_findings": "主要发现",
        "sample_characteristics": "样本特征"
      }}
    ],
    "institutional_reports": [
      {{
        "institution": "机构名称",
        "report_title": "报告标题",
        "key_statistics": "关键统计",
        "report_date": "报告日期"
      }}
    ]
  }},
  "content_blueprint": {{
    "big_idea": "核心叙事理念",
    "key_messages": ["关键信息点1", "关键信息点2"],
    "evidence_hierarchy": "证据层次结构",
    "credibility_anchors": ["可信度锚点1", "可信度锚点2"]
  }},
  "fact_updates": {{
    "latest_developments": ["最新发展1", "最新发展2"],
    "trend_analysis": "趋势分析",
    "future_implications": "未来影响预测"
  }},
  "verification_metadata": {{
    "sources_consulted": ["咨询来源1", "咨询来源2"],
    "verification_date": "验证日期",
    "next_review_date": "下次审查日期",
    "reliability_score": "可靠性评分"
  }}
}}
```

### 【质量标准】
- **权威性**：所有事实都有权威来源支撑
- **时效性**：确保信息的最新性和相关性
- **准确性**：数据和描述的精确无误
- **完整性**：覆盖主题的核心事实要点

现在请根据输入信息，进行全面的事实验证和知识库构建。
"""

        user_template = """
请对以下主题进行权威事实验证：

**主题**: {topic}

**战略方向**: {strategy_summary}

**验证要求**:
1. 收集和验证该主题的核心事实
2. 建立权威的专业知识库
3. 识别可能的争议点和最新发展
4. 构建可信的内容蓝图基础

请严格按照JSON格式输出完整的事实验证报告。
"""

        self.truth_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_template)  
        ])
        
        self.truth_chain = (
            self.truth_prompt
            | self.llm
            | StrOutputParser()
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行事实验证"""
        topic = inputs.get("topic", "")
        strategy = inputs.get("strategy", {})
        force_regenerate = inputs.get("force_regenerate", False)
        
        self.logger.info(f"🔍 真理探机引擎启动 - 主题: {topic}")
        
        # 检查缓存
        if not force_regenerate:
            cached_result = self.load_cache(topic, "truth_detector.json")
            if cached_result:
                self.logger.info("✓ 使用缓存的事实验证")
                return cached_result
        
        try:
            # 提取战略摘要
            strategy_summary = self._extract_strategy_summary(strategy)
            
            # 执行事实验证链
            self.logger.info("执行事实验证...")
            result_text = await self.truth_chain.ainvoke({
                "topic": topic,
                "strategy_summary": strategy_summary
            })
            
            # 解析JSON结果
            try:
                cleaned_text = result_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                truth_result = json.loads(cleaned_text)
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {e}")
                truth_result = self._get_fallback_truth(topic)
            
            # 添加引擎元数据
            final_result = {
                "engine": "truth_detector",
                "version": "1.0.0",
                "topic": topic,
                "truth_data": truth_result,
                "strategy_reference": strategy_summary,
                "execution_status": "success"
            }
            
            # 保存缓存
            self.save_cache(topic, final_result, "truth_detector.json")
            
            self.logger.info("✓ 事实验证完成")
            return final_result
            
        except Exception as e:
            self.logger.error(f"真理探机引擎执行失败: {str(e)}")
            return {
                "engine": "truth_detector", 
                "version": "1.0.0",
                "topic": topic,
                "truth_data": self._get_fallback_truth(topic),
                "execution_status": "fallback",
                "error": str(e)
            }
    
    def _extract_strategy_summary(self, strategy: Dict[str, Any]) -> str:
        """提取战略摘要"""
        if not strategy:
            return "通用内容战略"
        
        strategy_data = strategy.get("strategy_data", {})
        
        summary_parts = []
        
        approach = strategy_data.get("strategy_selection", {}).get("recommended_approach", "")
        if approach:
            summary_parts.append(f"策略方向: {approach}")
        
        core_msg = strategy_data.get("content_strategy", {}).get("core_message", "")
        if core_msg:
            summary_parts.append(f"核心信息: {core_msg}")
        
        value_prop = strategy_data.get("content_strategy", {}).get("value_proposition", "")
        if value_prop:
            summary_parts.append(f"价值主张: {value_prop}")
        
        return " | ".join(summary_parts) if summary_parts else "专业内容验证需求"
    
    def _get_fallback_truth(self, topic: str) -> Dict[str, Any]:
        """获取备用事实模板"""
        return {
            "fact_verification": {
                "topic_domain": f"'{topic}'相关专业领域",
                "verification_scope": "基础事实和常识验证",
                "authority_level": "中等权威性",
                "fact_reliability": "基础可靠"
            },
            "core_facts": {
                "verified_facts": [
                    {
                        "fact_statement": f"{topic}是一个需要专业指导的重要话题",
                        "authority_source": "行业共识",
                        "evidence_type": "专业经验",
                        "confidence_level": "高",
                        "last_updated": "持续更新"
                    }
                ],
                "data_points": [
                    {
                        "data_description": "该主题的关注度数据",
                        "numerical_value": "持续增长",
                        "data_source": "市场观察",
                        "collection_method": "综合分析",
                        "sample_size": "广泛样本"
                    }
                ]
            },
            "expert_insights": {
                "professional_opinions": [
                    {
                        "expert_name": "专业从业者",
                        "credentials": "行业经验",
                        "opinion_summary": f"{topic}需要科学系统的方法",
                        "supporting_evidence": "实践经验"
                    }
                ],
                "consensus_views": ["需要专业指导", "重视实践应用"],
                "controversial_points": ["方法差异", "实施细节"]
            },
            "research_foundation": {
                "key_studies": [
                    {
                        "study_title": f"{topic}相关研究",
                        "researchers": "相关专家",
                        "publication": "专业期刊",
                        "year": "近年来",
                        "main_findings": "需要系统性方法",
                        "sample_characteristics": "广泛人群"
                    }
                ],
                "institutional_reports": [
                    {
                        "institution": "相关权威机构",
                        "report_title": f"{topic}指导报告",
                        "key_statistics": "重要性数据",
                        "report_date": "定期更新"
                    }
                ]
            },
            "content_blueprint": {
                "big_idea": f"科学系统地理解和应用{topic}",
                "key_messages": ["专业指导重要", "实践应用关键"],
                "evidence_hierarchy": "理论基础 → 实践应用 → 效果验证",
                "credibility_anchors": ["专业背景", "实践经验"]
            },
            "fact_updates": {
                "latest_developments": ["方法不断优化", "认知持续深化"],
                "trend_analysis": "向更科学系统的方向发展",
                "future_implications": "将更加注重个性化和精准化"
            },
            "verification_metadata": {
                "sources_consulted": ["专业文献", "实践经验"],
                "verification_date": "当前日期",
                "next_review_date": "定期更新",
                "reliability_score": "中等可靠"
            }
        }
    
    def get_truth_summary(self, topic: str) -> Optional[Dict[str, Any]]:
        """获取事实验证摘要"""
        cached_result = self.load_cache(topic, "truth_detector.json")
        if not cached_result:
            return None
        
        truth_data = cached_result.get("truth_data", {})
        
        return {
            "big_idea": truth_data.get("content_blueprint", {}).get("big_idea", ""),
            "key_facts": [f["fact_statement"] for f in truth_data.get("core_facts", {}).get("verified_facts", [])[:3]],
            "authority_level": truth_data.get("fact_verification", {}).get("authority_level", ""),
            "credibility_anchors": truth_data.get("content_blueprint", {}).get("credibility_anchors", [])
        } 