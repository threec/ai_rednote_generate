"""
引擎④: 洞察提炼器引擎 (Insight Distiller Engine)
RedCube AI 工作流系统

目标：将零散的"研究数据"提炼升华为有中心思想的"核心故事"

核心功能：
- 核心任务：从事实到叙事
- 研判事实，验证或证伪初始创意  
- 挖掘报告中隐藏的"爆款"潜质
- 定义系列内容的"核心叙事(Big Idea)"
- 生成最终版的《内容创作蓝图》

实现方式：
- 基于LangChain构建洞察提炼链
- 多维度价值挖掘分析
- 核心叙事架构设计
- 输出完整的创作蓝图
"""

import json
from typing import Dict, Any, Optional, List
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from ..langchain_workflow import BaseWorkflowEngine
from ..utils import get_logger

class InsightDistillerEngine(BaseWorkflowEngine):
    """洞察提炼器引擎 - 核心价值挖掘"""
    
    def __init__(self, llm):
        super().__init__("insight_distiller", llm)
        self._initialize_insight_chain()
    
    def _initialize_insight_chain(self):
        """初始化洞察提炼链"""
        
        system_prompt = """
你是RedCube AI的"洞察提炼大师"，专门负责将零散数据升华为核心故事。

## 核心使命：从事实到叙事

将零散的"研究数据"提炼升华为有中心思想的"核心故事"，这是内容创作的关键转折点。

## 洞察提炼框架

### 【洞察挖掘维度】
1. **价值发现** 💎
   - 隐藏价值挖掘：发现事实背后的深层价值
   - 痛点洞察：识别用户真正关心的核心问题
   - 机会识别：发现创新角度和差异化机会

2. **叙事构建** 📚
   - 故事线索：将事实串联成有逻辑的故事
   - 情感连接：建立与读者的情感共鸣点
   - 价值升华：从具体事实上升到普遍价值

3. **创意激发** ⚡
   - 爆款潜质：识别具有传播潜力的要素
   - 创新角度：发现独特的切入视角
   - 话题性：构建引发讨论的核心话题

### 【核心叙事设计】
1. **Big Idea构建**
   - 中心思想：一个清晰的核心理念
   - 价值主张：为什么这个话题重要
   - 独特视角：与众不同的观点角度

2. **故事架构**
   - 开篇钩子：吸引注意的强力开场
   - 发展脉络：逻辑清晰的内容展开
   - 高潮设计：核心价值的集中体现
   - 收尾升华：价值的进一步提升

3. **内容蓝图**
   - 内容模块：各部分内容的功能定位
   - 逻辑关系：模块间的逻辑连接
   - 节奏控制：内容展开的节奏安排

### 【输出规范】
必须返回严格的JSON格式：

```json
{
  "insight_analysis": {
    "data_synthesis": "数据综合分析",
    "pattern_recognition": "模式识别结果",
    "value_discovery": "价值发现总结",
    "opportunity_mapping": "机会地图"
  },
  "core_insights": {
    "key_insights": [
      {
        "insight_statement": "核心洞察陈述",
        "supporting_evidence": "支撑证据",
        "value_implication": "价值含义",
        "practical_application": "实际应用"
      }
    ],
    "hidden_gems": [
      {
        "gem_description": "隐藏价值描述",
        "discovery_method": "发现方法",
        "potential_impact": "潜在影响"
      }
    ]
  },
  "big_idea": {
    "central_concept": "核心概念",
    "value_proposition": "价值主张",
    "unique_angle": "独特角度",
    "emotional_hook": "情感钩子",
    "viral_potential": "传播潜力评估"
  },
  "narrative_architecture": {
    "story_spine": {
      "setup": "故事设定",
      "conflict": "冲突张力",
      "resolution": "解决方案",
      "transformation": "转化价值"
    },
    "content_modules": [
      {
        "module_name": "模块名称",
        "module_purpose": "模块目的",
        "key_content": "核心内容",
        "connection_logic": "连接逻辑"
      }
    ]
  },
  "content_blueprint": {
    "content_outline": {
      "opening_hook": "开篇钩子设计",
      "main_sections": [
        {
          "section_title": "章节标题",
          "section_purpose": "章节目的",
          "key_points": ["要点1", "要点2"],
          "evidence_support": "证据支撑"
        }
      ],
      "climax_moment": "高潮时刻设计",
      "closing_impact": "结尾冲击力"
    },
    "engagement_strategy": {
      "attention_grabbers": ["注意力抓手1", "注意力抓手2"],
      "curiosity_builders": ["好奇心构建器1", "好奇心构建器2"],
      "emotional_triggers": ["情感触发器1", "情感触发器2"]
    }
  },
  "creative_elements": {
    "viral_components": ["病毒性元素1", "病毒性元素2"],
    "discussion_starters": ["讨论话题1", "讨论话题2"],
    "shareability_factors": ["分享因子1", "分享因子2"]
  },
  "execution_guidance": {
    "content_priorities": ["优先级1", "优先级2"],
    "tone_guidelines": "语调指导",
    "style_recommendations": "风格建议",
    "quality_checkpoints": ["质量检查点1", "质量检查点2"]
  }
}
```

### 【质量标准】
- **洞察深度**：挖掘出非显而易见的深层价值
- **叙事连贯**：形成清晰流畅的故事线
- **创意新颖**：提供独特的视角和角度
- **实用价值**：确保内容对受众有实际帮助

现在请根据前期分析结果，进行深度洞察提炼。
"""

        user_template = """
请对以下信息进行洞察提炼：

**主题**: {topic}

**人格特征**: {persona_summary}

**战略方向**: {strategy_summary}  

**事实基础**: {truth_summary}

**提炼要求**:
1. 深度挖掘事实背后的价值洞察
2. 构建有吸引力的核心叙事(Big Idea)
3. 设计完整的内容创作蓝图
4. 确保创意的可执行性和传播性

请严格按照JSON格式输出完整的洞察提炼报告。
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
        """执行洞察提炼"""
        topic = inputs.get("topic", "")
        persona = inputs.get("persona", {})
        strategy = inputs.get("strategy", {})
        facts = inputs.get("facts", {})
        force_regenerate = inputs.get("force_regenerate", False)
        
        self.logger.info(f"🔮 洞察提炼器引擎启动 - 主题: {topic}")
        
        # 检查缓存
        if not force_regenerate:
            cached_result = self.load_cache(topic, "insight_distiller.json")
            if cached_result:
                self.logger.info("✓ 使用缓存的洞察提炼")
                return cached_result
        
        try:
            # 提取各模块摘要
            persona_summary = self._extract_persona_summary(persona)
            strategy_summary = self._extract_strategy_summary(strategy)
            truth_summary = self._extract_truth_summary(facts)
            
            # 执行洞察提炼链
            self.logger.info("执行洞察提炼...")
            result_text = await self.insight_chain.ainvoke({
                "topic": topic,
                "persona_summary": persona_summary,
                "strategy_summary": strategy_summary,
                "truth_summary": truth_summary
            })
            
            # 解析JSON结果
            try:
                cleaned_text = result_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                insight_result = json.loads(cleaned_text)
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {e}")
                insight_result = self._get_fallback_insight(topic)
            
            # 添加引擎元数据
            final_result = {
                "engine": "insight_distiller",
                "version": "1.0.0",
                "topic": topic,
                "insight_data": insight_result,
                "input_references": {
                    "persona": persona_summary,
                    "strategy": strategy_summary,
                    "facts": truth_summary
                },
                "execution_status": "success"
            }
            
            # 保存缓存
            self.save_cache(topic, final_result, "insight_distiller.json")
            
            self.logger.info("✓ 洞察提炼完成")
            return final_result
            
        except Exception as e:
            self.logger.error(f"洞察提炼器引擎执行失败: {str(e)}")
            return {
                "engine": "insight_distiller",
                "version": "1.0.0",
                "topic": topic,
                "insight_data": self._get_fallback_insight(topic),
                "execution_status": "fallback",
                "error": str(e)
            }
    
    def _extract_persona_summary(self, persona: Dict[str, Any]) -> str:
        """提取人格摘要"""
        if not persona:
            return "通用内容创作者"
        
        persona_data = persona.get("persona_data", {})
        persona_core = persona_data.get("persona_core", {})
        
        identity = persona_core.get("signature_identity", {})
        traits = persona_core.get("character_traits", {})
        
        return f"{identity.get('name', '创作者')} - {identity.get('title', '专业分享者')} - {', '.join(traits.get('personality_keywords', ['专业']))}"
    
    def _extract_strategy_summary(self, strategy: Dict[str, Any]) -> str:
        """提取战略摘要"""
        if not strategy:
            return "深度价值导向"
        
        strategy_data = strategy.get("strategy_data", {})
        approach = strategy_data.get("strategy_selection", {}).get("recommended_approach", "深度导向")
        core_msg = strategy_data.get("content_strategy", {}).get("core_message", "专业内容分享")
        
        return f"{approach} - {core_msg}"
    
    def _extract_truth_summary(self, facts: Dict[str, Any]) -> str:
        """提取事实摘要"""
        if not facts:
            return "基础事实验证"
        
        truth_data = facts.get("truth_data", {})
        big_idea = truth_data.get("content_blueprint", {}).get("big_idea", "")
        authority = truth_data.get("fact_verification", {}).get("authority_level", "")
        
        verified_facts = truth_data.get("core_facts", {}).get("verified_facts", [])
        fact_count = len(verified_facts)
        
        return f"{big_idea} - {authority} - {fact_count}个核心事实"
    
    def _get_fallback_insight(self, topic: str) -> Dict[str, Any]:
        """获取备用洞察模板"""
        return {
            "insight_analysis": {
                "data_synthesis": f"围绕'{topic}'的综合信息分析",
                "pattern_recognition": "识别出用户需求和解决方案的匹配模式",
                "value_discovery": "发现专业指导和实践应用的核心价值",
                "opportunity_mapping": "系统性内容分享的机会识别"
            },
            "core_insights": {
                "key_insights": [
                    {
                        "insight_statement": f"{topic}需要系统性的专业指导",
                        "supporting_evidence": "用户需求分析和专业实践",
                        "value_implication": "帮助用户建立正确认知和有效实践",
                        "practical_application": "提供可操作的方法和建议"
                    }
                ],
                "hidden_gems": [
                    {
                        "gem_description": "专业知识的平民化表达价值",
                        "discovery_method": "复杂概念简单化处理",
                        "potential_impact": "降低学习门槛，提高实践成功率"
                    }
                ]
            },
            "big_idea": {
                "central_concept": f"科学系统地掌握{topic}",
                "value_proposition": "让复杂专业变得简单实用",
                "unique_angle": "理论与实践相结合的系统性指导",
                "emotional_hook": "从困惑到清晰的成长体验",
                "viral_potential": "实用价值驱动的自然传播"
            },
            "narrative_architecture": {
                "story_spine": {
                    "setup": f"关于{topic}的常见困惑和需求",
                    "conflict": "信息碎片化和实践困难",
                    "resolution": "系统性方法和专业指导",
                    "transformation": "从困惑到掌握的成长价值"
                },
                "content_modules": [
                    {
                        "module_name": "问题识别",
                        "module_purpose": "建立共鸣和需求确认",
                        "key_content": "常见困惑和痛点分析",
                        "connection_logic": "引出解决方案的必要性"
                    },
                    {
                        "module_name": "方法介绍",
                        "module_purpose": "提供系统性解决方案",
                        "key_content": "专业方法和实践步骤",
                        "connection_logic": "从理论到实践的桥梁"
                    },
                    {
                        "module_name": "实践指导",
                        "module_purpose": "确保可操作性",
                        "key_content": "具体操作和注意事项",
                        "connection_logic": "实现价值转化"
                    }
                ]
            },
            "content_blueprint": {
                "content_outline": {
                    "opening_hook": f"你在{topic}上遇到过这些困惑吗？",
                    "main_sections": [
                        {
                            "section_title": "认知基础",
                            "section_purpose": "建立正确理解",
                            "key_points": ["核心概念", "基本原理"],
                            "evidence_support": "专业知识和研究基础"
                        },
                        {
                            "section_title": "实践方法",
                            "section_purpose": "提供操作指导",
                            "key_points": ["具体步骤", "实操技巧"],
                            "evidence_support": "实践经验和案例分析"
                        }
                    ],
                    "climax_moment": "核心方法的深度阐述",
                    "closing_impact": "掌握后的价值升华"
                },
                "engagement_strategy": {
                    "attention_grabbers": ["关键问题", "实用价值"],
                    "curiosity_builders": ["方法揭秘", "效果预期"],
                    "emotional_triggers": ["成就感", "安全感"]
                }
            },
            "creative_elements": {
                "viral_components": ["实用价值", "专业权威"],
                "discussion_starters": ["方法对比", "经验分享"],
                "shareability_factors": ["帮助他人", "专业展示"]
            },
            "execution_guidance": {
                "content_priorities": ["实用性", "专业性", "可操作性"],
                "tone_guidelines": "专业而亲切，权威但不高冷",
                "style_recommendations": "结构清晰，逻辑严密，表达简洁",
                "quality_checkpoints": ["事实准确性", "实践可行性", "价值明确性"]
            }
        }
    
    def get_insight_summary(self, topic: str) -> Optional[Dict[str, Any]]:
        """获取洞察摘要"""
        cached_result = self.load_cache(topic, "insight_distiller.json")
        if not cached_result:
            return None
        
        insight_data = cached_result.get("insight_data", {})
        
        return {
            "big_idea": insight_data.get("big_idea", {}).get("central_concept", ""),
            "value_prop": insight_data.get("big_idea", {}).get("value_proposition", ""),
            "unique_angle": insight_data.get("big_idea", {}).get("unique_angle", ""),
            "blueprint": insight_data.get("content_blueprint", {})
        } 