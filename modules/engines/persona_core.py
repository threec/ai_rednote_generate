"""
引擎①: 人格核心引擎 (Persona Core Engine)
RedCube AI 工作流系统

目标：为内容注入统一的灵魂，定义人格(Persona)、声音(Voice)和基调(Tone)

核心功能：
- 解决AI默认文风中立枯燥的问题，确保内容矩阵风格统一、人设不崩的基石
- 结构化档案：创建包含署名、人设、Slogan、内容策略、用语规范的"风格指南"  
- 强制调用：在后续步骤中强制调用，如同给AI戴上"人格面具"

实现方式：
- 基于LangChain构建人格分析链
- 输出结构化的人格档案
- 建立可复用的人格模板库
"""

import json
import os
import sys
from typing import Dict, Any, Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 修复导入路径问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.langchain_workflow import BaseWorkflowEngine
from modules.utils import get_logger

class PersonaCoreEngine(BaseWorkflowEngine):
    """人格核心引擎 - 建立统一的内容人格"""
    
    def __init__(self, llm):
        super().__init__("persona_core", llm)
        self._initialize_persona_chain()
    
    def _initialize_persona_chain(self):
        """初始化人格分析链"""
        
        # 人格分析系统提示词
        system_prompt = """
你是RedCube AI的"人格核心构建师"，专门负责为内容创作者建立统一、鲜明的人格档案。

## 核心使命：解决AI内容"人格分裂"问题

你的任务是分析用户的内容主题，并构建一个统一、鲜明、可持续的内容人格，确保后续所有内容都能保持一致的风格和调性。

## 人格构建标准

### 【人格核心要素】
1. **署名身份 (Signature Identity)**
   - 具体的职业/身份标签
   - 专业背景和资历
   - 独特的个人标识

2. **人设特征 (Character Traits)**
   - 性格特点（3-5个关键词）
   - 价值观导向
   - 沟通风格偏好

3. **声音调性 (Voice & Tone)**
   - 语言风格（正式/随和/专业/亲切）
   - 情感基调（温暖/理性/激励/幽默）
   - 表达习惯（用词偏好、句式特点）

4. **内容策略 (Content Strategy)**
   - 擅长的内容角度
   - 常用的论证方式
   - 与读者的互动模式

### 【输出规范】
必须返回严格的JSON格式，包含以下结构：

```json
{{
  "persona_analysis": {{
    "topic_category": "内容领域分类",
    "target_audience": "目标受众画像",
    "content_context": "内容背景分析"
  }},
  "persona_core": {{
    "signature_identity": {{
      "name": "署名/昵称",
      "title": "职业/身份标签", 
      "credentials": "专业背景/资历",
      "unique_identifier": "独特标识/slogan"
    }},
    "character_traits": {{
      "personality_keywords": ["关键词1", "关键词2", "关键词3"],
      "value_orientation": "价值观导向描述",
      "communication_style": "沟通风格描述"
    }},
    "voice_and_tone": {{
      "language_style": "语言风格定义",
      "emotional_tone": "情感基调设定", 
      "expression_habits": {{
        "preferred_words": ["常用词1", "常用词2"],
        "sentence_patterns": "句式特点",
        "signature_phrases": ["口头禅1", "口头禅2"]
      }}
    }},
    "content_strategy": {{
      "expertise_angles": ["专长角度1", "专长角度2"],
      "argumentation_style": "论证方式偏好",
      "interaction_mode": "与读者互动模式"
    }}
  }},
  "style_guide": {{
    "do_rules": ["应该做的1", "应该做的2", "应该做的3"],
    "dont_rules": ["不应该做的1", "不应该做的2", "不应该做的3"],
    "language_examples": {{
      "good_examples": ["优秀表达示例1", "优秀表达示例2"],
      "bad_examples": ["需要避免的表达1", "需要避免的表达2"]
    }}
  }},
  "persona_consistency": {{
    "key_mantras": ["核心理念1", "核心理念2"],
    "content_themes": ["内容主题1", "内容主题2"],
    "brand_differentiation": "品牌差异化要点"
  }}
}}
```

### 【质量标准】
- **一致性**：确保人格设定前后一致，不会产生矛盾
- **鲜明性**：人格特征要突出，有辨识度
- **可操作性**：提供具体的执行指导，不是空洞的描述
- **可持续性**：适合长期内容创作，不会审美疲劳

现在请根据用户提供的主题，构建一个专业、鲜明、统一的内容人格档案。
"""

        # 用户输入提示词模板
        user_template = """
请为以下主题构建内容人格档案：

**主题**: {topic}

**分析要求**:
1. 深度分析该主题的内容创作需求
2. 确定最适合的人格设定和声音调性
3. 建立清晰的风格指南和一致性标准
4. 确保人格设定能够支撑长期内容创作

请严格按照JSON格式输出完整的人格档案。
"""

        # 创建提示词模板
        self.persona_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_template)
        ])
        
        # 创建处理链
        self.persona_chain = (
            self.persona_prompt
            | self.llm
            | StrOutputParser()
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """执行人格核心分析"""
        topic = inputs.get("topic", "")
        force_regenerate = inputs.get("force_regenerate", False)
        
        self.logger.info(f"🎭 人格核心引擎启动 - 主题: {topic}")
        
        # 检查缓存
        if not force_regenerate:
            cached_result = self.load_cache(topic, "persona_core.json")
            if cached_result:
                self.logger.info("✓ 使用缓存的人格档案")
                return cached_result
        
        try:
            # 执行人格分析链
            self.logger.info("执行人格分析...")
            result_text = await self.persona_chain.ainvoke({"topic": topic})
            
            # 解析JSON结果
            try:
                # 清理可能的代码块标记
                cleaned_text = result_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                persona_result = json.loads(cleaned_text)
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {e}")
                # 使用备用人格模板
                persona_result = self._get_fallback_persona(topic)
            
            # 添加引擎元数据
            final_result = {
                "engine": "persona_core",
                "version": "1.0.0",
                "timestamp": inputs.get("timestamp", ""),
                "topic": topic,
                "persona_data": persona_result,
                "execution_status": "success"
            }
            
            # 保存缓存
            self.save_cache(topic, final_result, "persona_core.json")
            
            self.logger.info("✓ 人格核心分析完成")
            return final_result
            
        except Exception as e:
            self.logger.error(f"人格核心引擎执行失败: {str(e)}")
            # 返回备用结果
            return {
                "engine": "persona_core",
                "version": "1.0.0", 
                "topic": topic,
                "persona_data": self._get_fallback_persona(topic),
                "execution_status": "fallback",
                "error": str(e)
            }
    
    def _get_fallback_persona(self, topic: str) -> Dict[str, Any]:
        """获取备用人格模板"""
        return {
            "persona_analysis": {
                "topic_category": "通用内容",
                "target_audience": "关注该主题的用户群体",
                "content_context": f"围绕'{topic}'的专业内容分享"
            },
            "persona_core": {
                "signature_identity": {
                    "name": "专业分享者",
                    "title": "内容创作者",
                    "credentials": "丰富的实践经验",
                    "unique_identifier": "用心分享，用爱传递"
                },
                "character_traits": {
                    "personality_keywords": ["专业", "温暖", "实用"],
                    "value_orientation": "帮助他人成长进步",
                    "communication_style": "亲切专业，深入浅出"
                },
                "voice_and_tone": {
                    "language_style": "专业而亲切",
                    "emotional_tone": "温暖励志",
                    "expression_habits": {
                        "preferred_words": ["分享", "实用", "建议"],
                        "sentence_patterns": "多用疑问句引发思考",
                        "signature_phrases": ["我的经验是", "建议大家"]
                    }
                },
                "content_strategy": {
                    "expertise_angles": ["实践经验", "专业知识"],
                    "argumentation_style": "结合理论与实践",
                    "interaction_mode": "引导式分享"
                }
            },
            "style_guide": {
                "do_rules": ["保持专业性", "注重实用性", "语言亲切"],
                "dont_rules": ["避免过于学术", "不要空洞说教", "避免冷漠语调"],
                "language_examples": {
                    "good_examples": ["我在实践中发现...", "建议大家可以尝试..."],
                    "bad_examples": ["众所周知...", "毋庸置疑..."]
                }
            },
            "persona_consistency": {
                "key_mantras": ["实用第一", "温暖分享"],
                "content_themes": ["专业指导", "经验分享"],
                "brand_differentiation": "有温度的专业内容"
            }
        }

    def get_persona_summary(self, topic: str) -> Optional[Dict[str, str]]:
        """获取人格核心摘要信息"""
        cached_result = self.load_cache(topic, "persona_core.json")
        if not cached_result:
            return None
        
        persona_data = cached_result.get("persona_data", {})
        persona_core = persona_data.get("persona_core", {})
        
        return {
            "name": persona_core.get("signature_identity", {}).get("name", ""),
            "title": persona_core.get("signature_identity", {}).get("title", ""),
            "style": persona_core.get("voice_and_tone", {}).get("language_style", ""),
            "tone": persona_core.get("voice_and_tone", {}).get("emotional_tone", "")
        } 