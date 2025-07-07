"""
引擎②: 策略罗盘引擎 (Strategy Compass Engine)
RedCube AI 工作流系统

目标：制定内容的核心战略，解决"做什么内容"的根本问题

核心功能：
- 在流量导向vs深度导向之间找平衡点，避免盲目追热点或过度小众
- 受众痛点挖掘：不做表面需求，直击用户真正的深层焦虑
- 内容差异化：在同质化海洋中找到独特角度

实现方式：
- 基于LangChain构建策略分析链
- 输出结构化的内容战略方案
- 整合市场分析和受众洞察
"""

import json
import os
import sys
from typing import Dict, Any, Optional, List
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 修复导入路径问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.langchain_workflow import BaseWorkflowEngine
from modules.utils import get_logger

class StrategyCompassEngine(BaseWorkflowEngine):
    """策略罗盘引擎 - 内容战略规划"""
    
    def __init__(self, llm):
        super().__init__("strategy_compass", llm)
        self._initialize_strategy_chain()
    
    def _initialize_strategy_chain(self):
        """初始化策略分析链"""
        
        system_prompt = """
你是RedCube AI的"战略罗盘导师"，专门负责为内容制定核心战略方向。

## 核心使命：制定内容核心战略

你需要明确内容的核心战略：追求短期流量，还是构建长期深度？

## 战略分析框架

### 【战略选择】
1. **流量导向策略** 🚀
   - 分析用户画像，挖掘痛点痒点
   - 构思"避坑"、"省钱"、"对比"等"钩子化"切入点
   - 快速吸引注意力，追求短期爆款

2. **深度导向策略** 🏛️  
   - 遵循预设框架(如认知-希望-回行)
   - 规划逻辑严谨、层层递进的内容支柱
   - 嵌入合规性原则，从源头规避风险

### 【策略要素分析】
1. **目标受众分析**
   - 人群画像：年龄、性别、职业、收入
   - 痛点挖掘：核心困扰、迫切需求
   - 行为特征：内容消费习惯、决策模式

2. **内容定位策略**
   - 价值主张：提供什么独特价值
   - 差异化角度：与竞品的区别点
   - 内容深度：浅层娱乐 vs 深度价值

3. **传播策略设计**
   - 钩子设计：吸引点击的元素
   - 互动设计：提升参与度的方式
   - 转化路径：从浏览到行动的引导

### 【输出规范】
必须返回严格的JSON格式：

```json
{{
  "strategy_analysis": {{
    "topic_assessment": "主题分析评估",
    "market_potential": "市场潜力评估",
    "competition_landscape": "竞争环境分析",
    "opportunity_window": "机会窗口评估"
  }},
  "audience_insights": {{
    "primary_audience": {{
      "demographics": "人群特征",
      "psychographics": "心理特征", 
      "pain_points": ["痛点1", "痛点2", "痛点3"],
      "motivations": ["动机1", "动机2", "动机3"]
    }},
    "content_consumption": {{
      "preferred_formats": ["格式1", "格式2"],
      "engagement_triggers": ["触发点1", "触发点2"],
      "sharing_drivers": ["分享动机1", "分享动机2"]
    }}
  }},
  "strategy_selection": {{
    "recommended_approach": "流量导向 或 深度导向",
    "strategy_rationale": "战略选择理由",
    "success_metrics": ["成功指标1", "成功指标2"]
  }},
  "content_strategy": {{
    "core_message": "核心信息",
    "value_proposition": "价值主张",
    "differentiation_angle": "差异化角度",
    "content_themes": ["主题1", "主题2", "主题3"]
  }},
  "hook_elements": {{
    "attention_grabbers": ["吸引元素1", "吸引元素2"],
    "curiosity_gaps": ["好奇缺口1", "好奇缺口2"],
    "emotional_triggers": ["情感触发1", "情感触发2"]
  }},
  "content_framework": {{
    "opening_strategy": "开篇策略",
    "development_logic": "展开逻辑",
    "climax_design": "高潮设计", 
    "closing_strategy": "结尾策略"
  }},
  "compliance_guidelines": {{
    "content_boundaries": ["边界1", "边界2"],
    "risk_mitigation": ["风险控制1", "风险控制2"],
    "safety_principles": ["安全原则1", "安全原则2"]
  }}
}}
```

### 【质量标准】
- **战略清晰**：明确选择流量导向还是深度导向
- **逻辑严密**：策略选择有充分的理由支撑
- **可操作性**：提供具体的执行指导
- **差异化强**：突出独特的竞争优势

现在请根据输入信息，制定清晰的内容战略。
"""

        user_template = """
请为以下主题制定内容战略：

**主题**: {topic}

**人格档案**: {persona_summary}

**分析要求**:
1. 深度分析目标受众和市场环境
2. 明确选择流量导向或深度导向策略
3. 设计具体的内容框架和钩子元素
4. 确保符合平台规范和安全要求

请严格按照JSON格式输出完整的战略分析。
"""

        self.strategy_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_template)
        ])
        
        self.strategy_chain = (
            self.strategy_prompt
            | self.llm  
            | StrOutputParser()
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行策略分析"""
        topic = inputs.get("topic", "")
        persona = inputs.get("persona", {})
        force_regenerate = inputs.get("force_regenerate", False)
        
        self.logger.info(f"🧭 策略罗盘引擎启动 - 主题: {topic}")
        
        # 检查缓存
        if not force_regenerate:
            cached_result = self.load_cache(topic, "strategy_compass.json")
            if cached_result:
                self.logger.info("✓ 使用缓存的战略分析")
                return cached_result
        
        try:
            # 提取人格摘要
            persona_summary = self._extract_persona_summary(persona)
            
            # 执行策略分析链
            self.logger.info("执行战略分析...")
            result_text = await self.strategy_chain.ainvoke({
                "topic": topic,
                "persona_summary": persona_summary
            })
            
            # 解析JSON结果
            try:
                cleaned_text = result_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                strategy_result = json.loads(cleaned_text)
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {e}")
                strategy_result = self._get_fallback_strategy(topic)
            
            # 添加引擎元数据
            final_result = {
                "engine": "strategy_compass",
                "version": "1.0.0",
                "topic": topic,
                "strategy_data": strategy_result,
                "persona_reference": persona_summary,
                "execution_status": "success"
            }
            
            # 保存缓存
            self.save_cache(topic, final_result, "strategy_compass.json")
            
            self.logger.info("✓ 战略分析完成")
            return final_result
            
        except Exception as e:
            self.logger.error(f"策略罗盘引擎执行失败: {str(e)}")
            return {
                "engine": "strategy_compass",
                "version": "1.0.0",
                "topic": topic,
                "strategy_data": self._get_fallback_strategy(topic),
                "execution_status": "fallback",
                "error": str(e)
            }
    
    def _extract_persona_summary(self, persona: Dict[str, Any]) -> str:
        """提取人格档案摘要"""
        if not persona:
            return "通用内容创作者"
        
        persona_data = persona.get("persona_data", {})
        persona_core = persona_data.get("persona_core", {})
        
        identity = persona_core.get("signature_identity", {})
        traits = persona_core.get("character_traits", {})
        voice = persona_core.get("voice_and_tone", {})
        
        summary_parts = []
        
        if identity.get("name"):
            summary_parts.append(f"身份: {identity['name']}")
        if identity.get("title"):
            summary_parts.append(f"定位: {identity['title']}")
        if traits.get("personality_keywords"):
            summary_parts.append(f"特质: {', '.join(traits['personality_keywords'])}")
        if voice.get("language_style"):
            summary_parts.append(f"风格: {voice['language_style']}")
        
        return " | ".join(summary_parts) if summary_parts else "专业内容创作者"
    
    def _get_fallback_strategy(self, topic: str) -> Dict[str, Any]:
        """获取备用战略模板"""
        return {
            "strategy_analysis": {
                "topic_assessment": f"'{topic}'具有良好的内容价值潜力",
                "market_potential": "中等市场潜力，有发展空间",
                "competition_landscape": "竞争适中，存在差异化机会",
                "opportunity_window": "当前时机适合，可以布局"
            },
            "audience_insights": {
                "primary_audience": {
                    "demographics": "对该主题感兴趣的用户群体",
                    "psychographics": "追求实用价值的理性用户",
                    "pain_points": ["缺乏专业指导", "信息碎片化", "难以实践"],
                    "motivations": ["获得实用建议", "提升自我", "解决问题"]
                },
                "content_consumption": {
                    "preferred_formats": ["图文并茂", "结构清晰"],
                    "engagement_triggers": ["实用价值", "权威性"],
                    "sharing_drivers": ["帮助他人", "展示专业"]
                }
            },
            "strategy_selection": {
                "recommended_approach": "深度导向",
                "strategy_rationale": "该主题更适合提供深度价值，建立长期信任",
                "success_metrics": ["内容深度", "用户留存", "专业认知"]
            },
            "content_strategy": {
                "core_message": f"关于{topic}的专业深度分享",
                "value_proposition": "提供实用、专业、可操作的指导",
                "differentiation_angle": "结合理论与实践的系统性内容",
                "content_themes": ["基础知识", "实践方法", "进阶技巧"]
            },
            "hook_elements": {
                "attention_grabbers": ["权威数据", "真实案例"],
                "curiosity_gaps": ["常见误区", "专业见解"],
                "emotional_triggers": ["成就感", "安全感"]
            },
            "content_framework": {
                "opening_strategy": "痛点引入，建立共鸣",
                "development_logic": "问题-方法-案例-总结",
                "climax_design": "核心方法详细阐述",
                "closing_strategy": "行动指导和价值升华"
            },
            "compliance_guidelines": {
                "content_boundaries": ["避免绝对化表述", "注重客观性"],
                "risk_mitigation": ["引用权威来源", "提供免责声明"],
                "safety_principles": ["用户安全第一", "负责任的建议"]
            }
        }
    
    def get_strategy_summary(self, topic: str) -> Optional[Dict[str, str]]:
        """获取战略摘要信息"""
        cached_result = self.load_cache(topic, "strategy_compass.json")
        if not cached_result:
            return None
        
        strategy_data = cached_result.get("strategy_data", {})
        
        return {
            "approach": strategy_data.get("strategy_selection", {}).get("recommended_approach", ""),
            "core_message": strategy_data.get("content_strategy", {}).get("core_message", ""),
            "value_prop": strategy_data.get("content_strategy", {}).get("value_proposition", ""),
            "target_audience": strategy_data.get("audience_insights", {}).get("primary_audience", {}).get("demographics", "")
        } 